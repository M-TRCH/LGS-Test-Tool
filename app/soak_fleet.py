"""Soak several cabinets at once — one thread, one socket, one file each.

The single-cabinet soak runs on the worker's one transport, because the
worker exists to keep exactly one master on exactly one RS485 bus. That rule
is about a BUS, not about the tool: two cabinets are two gateways, two
sockets and two entirely separate buses, and polling both at once is no more
contentious than two people watching two cabinets.

So a fleet run is N independent soaks. Each gets:

  * its own pymodbus client, so one cabinet's link dropping cannot stall
    another's pass,
  * its own thread, so a 25 s pass on an 80-slot cabinet does not pace a
    40-slot one,
  * its own CSV in the soak schema, so `soak_csv.py` and the site report
    read a fleet file exactly as they read a single-cabinet one, and a
    cabinet can be compared against its own history rather than against a
    merged file nothing can slice.

What it deliberately does NOT do is share anything between cabinets. There
is no combined pass counter, no barrier, no "wait for the slowest". A fleet
of five is five soaks that happen to have been started together, and any one
of them can be cancelled or die without touching the rest.

THE ONE RULE: never point a fleet run at a gateway the tool is already
connected to on the main Connect. The gateway accepts two TCP clients, but
there is still one physical bus behind it, and two masters on one bus
corrupts both sides' data — it cost a soak's last four rows on 2026-08-28.
`conflicting_hosts()` is here so a caller can refuse before it starts.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import soak
from .transports import HUB_SAFE_TIMEOUT_S, TcpSettings, make_client


@dataclass(frozen=True)
class FleetCabinet:
    """One cabinet in a fleet run."""
    name: str                    # what the operator calls it; names the CSV
    host: str
    ids: tuple
    port: int = 502

    @property
    def label(self) -> str:
        return f"{self.name} ({self.host})"


@dataclass
class FleetEvent:
    """A cabinet's event, tagged. The UI shows one row per cabinet, so every
    event has to say which one it belongs to before anything else."""
    cabinet: str
    inner: object                # soak.SoakTick | SoakAnomaly | SoakDone
    seq: int = 0


@dataclass
class FleetStarted:
    cabinet: str
    path: str
    modules: int
    seq: int = 0


@dataclass
class FleetFailed:
    """A cabinet that never got going — a bad host, a refused socket. The
    others carry on; this says which one dropped out and why."""
    cabinet: str
    reason: str
    seq: int = 0


class _ClientOps:
    """soak.SoakOps over one pymodbus client, with its own reconnect.

    The worker's binder cannot be reused: it routes through a single shared
    transport and a single cancel flag. This one owns its client outright so
    a fleet member is genuinely independent.

    Reconnection matters more here than in a single run. A fleet is left
    overnight, and a switch that blinks takes out every cabinet at once; a
    member that gave up on the first dropped socket would turn one blink
    into a lost night for all of them.
    """

    RECONNECT_EVERY_S = 5.0

    def __init__(self, settings: TcpSettings, cancel: threading.Event) -> None:
        self._settings = settings
        self._cancel = cancel
        self._client = None
        self._next_retry = 0.0

    # ── lifecycle ──────────────────────────────────────────────────────────
    def connect(self) -> bool:
        try:
            self._client = make_client(self._settings, timeout_s=self._settings.timeout_s)
            return bool(self._client.connect())
        except Exception:                                        # noqa: BLE001
            self._client = None
            return False

    def close(self) -> None:
        try:
            if self._client is not None:
                self._client.close()
        except Exception:                                        # noqa: BLE001
            pass
        self._client = None

    def _revive(self) -> bool:
        """Try to get the socket back, but not more than once every few
        seconds: a cabinet that is switched off would otherwise spend the
        night hammering connect() instead of sleeping between passes."""
        now = time.monotonic()
        if now < self._next_retry:
            return False
        self._next_retry = now + self.RECONNECT_EVERY_S
        self.close()
        return self.connect()

    # ── SoakOps ────────────────────────────────────────────────────────────
    def read_regs(self, device_id: int, addr: int, count: int):
        if self._client is None and not self._revive():
            return _Txn(False, None, "link down", True)
        try:
            r = self._client.read_holding_registers(addr, count=count,
                                                    device_id=device_id)
        except TypeError:        # pymodbus < 3.7 spells it differently
            try:
                r = self._client.read_holding_registers(addr, count=count,
                                                        slave=device_id)
            except Exception as exc:                             # noqa: BLE001
                return self._dead(exc)
        except Exception as exc:                                 # noqa: BLE001
            return self._dead(exc)
        if r.isError():
            return _Txn(False, None, str(r)[:60])
        regs = r.registers
        return _Txn(True, regs if count > 1 else regs[0])

    def write_coil(self, device_id: int, addr: int, value: bool):
        if self._client is None and not self._revive():
            return _Txn(False, None, "link down", True)
        try:
            r = self._client.write_coil(addr, bool(value), device_id=device_id)
        except TypeError:
            try:
                r = self._client.write_coil(addr, bool(value), slave=device_id)
            except Exception as exc:                             # noqa: BLE001
                return self._dead(exc)
        except Exception as exc:                                 # noqa: BLE001
            return self._dead(exc)
        if r.isError():
            return _Txn(False, None, str(r)[:60])
        return _Txn(True, value)

    def _dead(self, exc: BaseException):
        """A raised exception is the transport, not the module — pymodbus
        answers a silent slave with an error object, not by throwing."""
        self.close()
        return _Txn(False, None, f"{type(exc).__name__}: {exc}"[:60], True)

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._cancel.is_set():
                return
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


@dataclass
class _Txn:
    ok: bool
    value: object = None
    note: str = ""
    link_down: bool = False
    latency_ms: float = 0.0


def conflicting_hosts(cabinets: Sequence[FleetCabinet],
                      connected_host: Optional[str]) -> list:
    """Cabinets that share a gateway with the tool's own live connection.

    Two TCP clients are allowed by the gateway and fatal to the data: there
    is one RS485 bus behind it. A caller should refuse to start rather than
    produce a file it will later have to distrust.
    """
    if not connected_host:
        return []
    return [c.name for c in cabinets if c.host == connected_host]


@dataclass
class FleetBusy:
    """The gateway already had another master when we arrived."""
    cabinet: str
    peers: str
    seq: int = 0


def _other_master(client, our_host: Optional[str]) -> Optional[str]:
    """Names the peers on this gateway other than us, or None if we are alone.

    Checking `conflicting_hosts` only catches the tool arguing with itself.
    The costly case is somebody ELSE — a server, a colleague's laptop, last
    week's soak nobody closed. The gateway accepts two TCP clients and has
    one RS485 bus behind them, so a second master does not fail loudly; it
    quietly corrupts both sides' reads. On 2026-09-17 the type-80 gateway
    was still being polled from .87 days after that soak was cancelled, and
    nothing on either side said so.

    So ask the gateway who is on it. We are already one of the clients by
    the time this runs, which is why it looks for a peer that is not us.
    """
    try:
        from .gateway_tcp import GatewayTcpLink, register_pdu
        register_pdu(client)
        res = GatewayTcpLink(client).command("INFO")
        if not res.ok:
            return None                  # no console: nothing to go on
        for line in res.lines:
            if "net.peer=" not in line:
                continue
            peers = line.split("net.peer=", 1)[1].split()[0]
            if peers in ("-", ""):
                return None
            others = [p for p in peers.split(",")
                      if not (our_host and p.startswith(our_host + ":"))]
            return ", ".join(others) if others else None
    except Exception:                                            # noqa: BLE001
        return None                      # never let the guard break the run
    return None


def run_fleet(cabinets: Sequence[FleetCabinet], cfg: soak.SoakConfig,
              emit: Callable, cancel: threading.Event,
              log_dir: Path,
              timeout_s: float = HUB_SAFE_TIMEOUT_S,
              our_host: Optional[str] = None,
              allow_shared: bool = False) -> dict:
    """Start one soak per cabinet and block until all of them finish.

    Returns {cabinet name: soak.SoakReport} for those that ran. Cabinets that
    could not be reached are reported through FleetFailed and simply absent.
    """
    stamp = f"{datetime.now():%Y%m%d-%H%M}"
    log_dir.mkdir(parents=True, exist_ok=True)
    reports: dict = {}
    lock = threading.Lock()

    def one(cab: FleetCabinet) -> None:
        settings = TcpSettings(host=cab.host, port=cab.port,
                               timeout_s=timeout_s)
        ops = _ClientOps(settings, cancel)
        if not ops.connect():
            emit(FleetFailed(cabinet=cab.name,
                             reason=f"cannot reach {cab.host}:{cab.port}"))
            return
        busy = None if allow_shared else _other_master(ops._client, our_host)
        if busy:
            # Refuse rather than produce a file that has to be distrusted
            # later. allow_shared exists for the case where the operator
            # knows the other client is read-only (gw_bus_watch).
            emit(FleetBusy(cabinet=cab.name, peers=busy))
            ops.close()
            return
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "-"
                       for ch in cab.name) or "cabinet"
        path = log_dir / f"soak-{safe}-{stamp}.csv"
        handle = path.open("w", encoding="utf-8", newline="")
        handle.write("time,device_id,kind,detail\n")
        handle.flush()
        emit(FleetStarted(cabinet=cab.name, path=str(path), modules=len(cab.ids)))

        def log_line(line: str) -> None:
            handle.write(line + "\n")
            handle.flush()          # an overnight run is read after a crash

        try:
            report = soak.run_soak(
                ops,
                soak.SoakConfig(ids=tuple(cab.ids), pass_gap_s=cfg.pass_gap_s,
                                counter_every=cfg.counter_every,
                                slow_ms=cfg.slow_ms,
                                crossing_slow_ms=cfg.crossing_slow_ms,
                                mode=cfg.mode, picks_per_day=cfg.picks_per_day,
                                dwell_s=cfg.dwell_s, windows=cfg.windows),
                lambda ev, _n=cab.name: emit(FleetEvent(cabinet=_n, inner=ev)),
                cancel, log_line)
            with lock:
                reports[cab.name] = report
        except BaseException as exc:                             # noqa: BLE001
            # One cabinet falling over must not take the fleet with it. Its
            # own CSV already carries a stop row saying why.
            emit(FleetFailed(cabinet=cab.name,
                             reason=f"{type(exc).__name__}: {exc}"[:80]))
        finally:
            handle.close()
            ops.close()

    threads = [threading.Thread(target=one, args=(c,), name=f"soak-{c.name}",
                                daemon=True) for c in cabinets]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    return reports
