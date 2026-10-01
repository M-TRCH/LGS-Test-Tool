"""Firmware update for several cabinets at once.

Every cabinet is its own gateway with its own RS485 bus behind it, so nothing
stops ten of them streaming at the same time — the only thing they share is
this PC's network, and an OTA stream is one 145-byte frame every quarter of a
second. One after another, ten cabinets were ten times ~30 min: five hours,
which nobody can accept for a roll-out (2026-10-01). Side by side they take as
long as the slowest one.

One thread per cabinet, each with its own TCP client — the worker's single
transport is not touched — and each running the same app/ota.run_ota the
Firmware tab uses, resync pauses, keepalive and slow retry included. Like the
fleet soak, the run keeps its own per-cabinet status and writes its own
verdict, so the page that started it is only a window onto it.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import ota
from .lgs_map import INTER_TXN_S, hub_channel, parse_hub_map
from .soak_fleet import (FleetCabinet, _ClientOps, _Txn, _other_master,
                         duplicate_hosts, safe_stem)
from .transports import HUB_SAFE_TIMEOUT_S, TcpSettings

BUS_BAUD = 9600                 # what the worker assumes behind a gateway too
BROADCAST_IDLE_S = 0.100        # same hold as ModbusWorker.BROADCAST_IDLE_S

# Lines worth putting in the run's shared log as well as the cabinet's own
# file. Everything else (probe lines, per-device "missing N", the confirm
# list) stays in the file: ten cabinets at once would bury the line that
# matters under four thousand that do not.
_NOTABLE = ("left the session", "retrying", "NOT updated", "did not answer",
            "did not enter", "NO REPLY", "bitmap read failed", "no device",
            "cancelled", "hub map from the gateway", "kept the session alive")


class _FleetOtaOps(_ClientOps):
    """ota.OtaOps over one cabinet's own TCP client.

    Built on the fleet soak's client so it inherits that one's reconnect: a
    switch that blinks for two seconds (Std-04 does, a dozen times an hour)
    must cost a cabinet a few chunks for the repair round, not its update.
    """

    def __init__(self, settings: TcpSettings, cancel: threading.Event) -> None:
        super().__init__(settings, cancel)
        self._last = 0.0

    def connect(self) -> bool:
        ok = super().connect()
        if ok:
            try:                                 # the console (hub map, peers)
                from .gateway_tcp import register_pdu
                register_pdu(self._client)
            except Exception:                                    # noqa: BLE001
                pass
        return ok

    def _pace(self) -> None:
        gap = INTER_TXN_S - (time.monotonic() - self._last)
        if gap > 0:
            time.sleep(gap)

    def read_regs(self, device_id: int, addr: int, count: int):
        self._pace()
        try:
            return super().read_regs(device_id, addr, count)
        finally:
            self._last = time.monotonic()

    def write_coil(self, device_id: int, addr: int, value):
        self._pace()
        try:
            return super().write_coil(device_id, addr, bool(value))
        finally:
            self._last = time.monotonic()

    def _bcast(self, send: Callable, nbytes: int):
        self._pace()
        ok = False
        if self._client is not None or self._revive():
            try:
                send(self._client)
                ok = True
            except Exception as exc:                             # noqa: BLE001
                self._dead(exc)
        # Hold the line for the frame's wire time whether or not it went out.
        # A stream that raced through its remaining chunks while the link was
        # down would turn a two-second blink into re-sending the whole image.
        time.sleep(nbytes * 10.0 / BUS_BAUD + BROADCAST_IDLE_S)
        self._last = time.monotonic()
        return _Txn(ok, None, "" if ok else "link down", not ok)

    def bcast_regs(self, addr: int, values: list, log: bool = True):
        return self._bcast(lambda c: c.write_registers(addr, values, device_id=0,
                                                       no_response_expected=True),
                           9 + 2 * len(values))

    def bcast_coil(self, addr: int):
        return self._bcast(lambda c: c.write_coil(addr, True, device_id=0,
                                                  no_response_expected=True), 8)

    def hub_map(self) -> Optional[str]:
        if self._client is None:
            return None
        try:
            from .gateway_tcp import GatewayTcpLink
            snap = GatewayTcpLink(self._client).snapshot()
            return snap.settings.get("bus.hub_map") if snap.ok else None
        except Exception:                                        # noqa: BLE001
            return None

    def other_master(self, host: str) -> Optional[str]:
        return _other_master(self._client, host) if self._client is not None else None

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._cancel.is_set():
                raise ota.OtaCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


# ── status the run keeps for itself ─────────────────────────────────────────
@dataclass
class CabStatus:
    name: str
    host: str
    modules: int
    state: str = "waiting"      # waiting | running | done | incomplete |
                                # refused | failed | cancelled
    channel: int = 0            # which hub channel group is being worked, 1-based
    channels: int = 0
    phase: str = ""
    pct: int = 0                # stream progress inside the current group
    updated: int = 0
    left: tuple = ()            # ids not on the new image when it ended
    census: str = ""            # what the cabinet reports afterwards
    note: str = ""
    log_path: str = ""
    t0: float = 0.0
    t1: float = 0.0

    @property
    def minutes(self) -> float:
        if not self.t0:
            return 0.0
        return ((self.t1 or time.monotonic()) - self.t0) / 60.0

    @property
    def fraction(self) -> float:
        """Rough share of the job done: whole groups plus the stream inside
        the current one. Repair, verify and apply are short next to it."""
        if self.state in ("done", "incomplete"):
            return 1.0
        if not self.channels or not self.channel:
            return 0.0
        inside = self.pct / 100.0 if self.phase == "stream" else (
            0.0 if self.phase in ("probe", "enter") else 0.95)
        return min(1.0, ((self.channel - 1) + inside) / self.channels)


class StatusBoard:
    """Per-cabinet status, written by the cabinet threads and read by pages."""

    def __init__(self, cabinets: Sequence[FleetCabinet]) -> None:
        self.lock = threading.Lock()
        self.rows = [CabStatus(c.name, c.host, len(c.ids)) for c in cabinets]

    def snapshot(self) -> list:
        with self.lock:
            return [replace(r) for r in self.rows]


@dataclass
class FleetOtaEvent:
    """A line worth showing in the run's shared log."""
    cabinet: str
    text: str
    level: str = "info"
    seq: int = 0
    # Stamped when it happened, not when a page drew it: a page opened
    # halfway through replays the buffer, and "now" on every replayed line
    # made a half-hour roll-out look like it happened in one second.
    when: str = field(default_factory=lambda: f"{datetime.now():%H:%M:%S}")


@dataclass
class FleetOtaFinished:
    text: str
    path: str = ""
    seq: int = 0


@dataclass
class FleetOtaOutcome:
    text: str
    path: str
    started: str
    duration_s: float
    rows: list                  # CabStatus, final
    cabinets: list              # the FleetCabinet each row ran

    def leftovers(self) -> list:
        """The same cabinets, holding only the ids that are not on the new
        image — including whole cabinets that never got to run."""
        out = []
        for cab, row in zip(self.cabinets, self.rows):
            if row.state in ("refused", "failed") or (row.state == "cancelled"
                                                      and not row.left):
                ids = tuple(cab.ids) if not row.left else row.left
            else:
                ids = row.left
            if ids:
                out.append(FleetCabinet(name=cab.name, host=cab.host,
                                        ids=tuple(ids), port=cab.port))
        return out


def count_channels(ids: Sequence[int], hub_map_text: Optional[str]) -> int:
    """How many sessions run_ota will open: one per hub channel, grouped the
    way it groups them (the gateway's map when it answers, else the tool's)."""
    channel_of = hub_channel
    if hub_map_text:
        try:
            gw = parse_hub_map(hub_map_text)
        except ValueError:
            gw = None
        if gw:
            def channel_of(uid: int, _m=gw) -> int:              # noqa: F811
                row = uid // 10
                return _m[row - 1] if 1 <= row <= len(_m) else 0
    return max(1, len({channel_of(uid) for uid in ids}))


def _census(ops, ids: Sequence[int]) -> str:
    """Every module's firmware version, read back after the run."""
    seen: dict = {}
    for uid in ids:
        res = ops.read_regs(uid, 1, 1)
        key = str(res.value) if res.ok else "no reply"
        seen[key] = seen.get(key, 0) + 1
    return ", ".join(f"{k} x{n}" for k, n in
                     sorted(seen.items(), key=lambda kv: (-kv[1], kv[0])))


def run_fleet_ota(cabinets: Sequence[FleetCabinet], image: bytes, filename: str,
                  emit: Callable, cancel: threading.Event, log_dir: Path, *,
                  board: Optional[StatusBoard] = None,
                  timeout_s: float = HUB_SAFE_TIMEOUT_S,
                  allow_shared: bool = False,
                  repair_rounds: int = 8,
                  ops_factory: Optional[Callable] = None) -> Optional[FleetOtaOutcome]:
    """Update every cabinet at once and block until all of them finish.

    Returns the outcome (its verdict already on disk), or None when the run
    was refused before any socket was opened. `ops_factory(cabinet, cancel)`
    exists for the selftest; the default builds one TCP client per cabinet.
    """
    cfg0 = ota.OtaConfig(image=image, filename=filename)
    if cfg0.size_error():
        emit(FleetOtaEvent("fleet", f"refused: {cfg0.size_error()}", "err"))
        return None
    # Two rows aimed at one gateway are two masters on one bus, and each
    # thread's own peer check cannot see the other in time. Refuse up front.
    dupes = duplicate_hosts(cabinets)
    if dupes:
        emit(FleetOtaEvent("fleet", f"refused: the same gateway is listed twice "
                                    f"({', '.join(dupes)})", "err"))
        return None

    board = board or StatusBoard(cabinets)
    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    def factory(cab: FleetCabinet):
        if ops_factory is not None:
            return ops_factory(cab, cancel)
        return _FleetOtaOps(TcpSettings(host=cab.host, port=cab.port,
                                        timeout_s=timeout_s), cancel)

    def one(cab: FleetCabinet, st: CabStatus) -> None:
        def tell(text: str, level: str = "info") -> None:
            emit(FleetOtaEvent(cab.name, text, level))

        handle = None
        st.t0 = time.monotonic()
        st.state = "running"
        st.phase = "connect"
        ops = None
        try:
            ops = factory(cab)
            if not ops.connect():
                st.state, st.note = "refused", f"cannot reach {cab.host}:{cab.port}"
                tell(st.note, "err")
                return
            busy = None if allow_shared else ops.other_master(cab.host)
            if busy:
                st.state, st.note = "refused", f"another master on the gateway: {busy}"
                tell(st.note, "err")
                return
            st.channels = count_channels(cab.ids, ops.hub_map())
            path = log_dir / f"ota-{safe_stem(cab.name)}-{stamp}.log"
            try:
                handle = path.open("w", encoding="utf-8")
                st.log_path = str(path)
            except OSError:
                handle = None            # a log that will not open must not stop it

            def sub_emit(ev) -> None:
                if isinstance(ev, ota.Line):
                    text = ev.text
                    if handle is not None:
                        try:
                            handle.write(f"{datetime.now():%H:%M:%S}  {text}\n")
                            handle.flush()
                        except OSError:
                            pass
                    if text.startswith("── hub channel"):
                        st.channel += 1
                        st.phase, st.pct = "probe", 0
                    elif st.channel == 0 and text.startswith("image:"):
                        st.channel = 1            # one group: no channel header
                        st.phase, st.pct = "probe", 0
                    elif text.startswith("[3/8]"):
                        st.phase = "enter"
                    elif text.startswith("[4/8]"):
                        st.phase, st.pct = "stream", 0
                    elif text.startswith("[5/8]"):
                        st.phase = "check"
                    elif "repair round" in text:
                        st.phase = "repair"
                    elif text.startswith("[6/8]"):
                        st.phase = "verify"
                    elif text.startswith("[7/8]"):
                        st.phase = "apply"
                    elif text.startswith("[8/8]"):
                        st.phase = "confirm"
                    elif "retrying" in text:
                        st.phase = "slow retry"
                    if "[UPDATED]" in text:
                        st.updated += 1
                    stripped = text.strip()
                    if stripped.startswith("channel ") or any(k in text for k in _NOTABLE):
                        tell(stripped, ev.level)
                elif isinstance(ev, ota.Progress):
                    st.pct = ev.done * 100 // max(1, ev.total)

            cfg = ota.OtaConfig(ids=tuple(cab.ids), image=image, filename=filename,
                                repair_rounds=repair_rounds)
            rep = ota.run_ota(ops, cfg, sub_emit, cancel)
            st.updated = len(set(rep.updated))
            st.left = tuple(sorted(set(cab.ids) - set(rep.updated)))
            if cancel.is_set():
                st.state = "cancelled"
            else:
                st.phase = "read back"
                st.census = _census(ops, cab.ids)
                st.state = "done" if rep.ok and not st.left else "incomplete"
            st.phase = ""
            tell(f"{st.state} · {st.updated}/{st.modules} updated in "
                 f"{st.minutes:.1f} min" + (f" · now {st.census}" if st.census else "")
                 + (f" · left behind {', '.join(map(str, st.left))}" if st.left else ""),
                 "ok" if st.state == "done" else "err")
        except BaseException as exc:                             # noqa: BLE001
            # One cabinet falling over must not take the others with it.
            st.state, st.note = "failed", f"{type(exc).__name__}: {exc}"[:120]
            tell(st.note, "err")
        finally:
            st.t1 = time.monotonic()
            if handle is not None:
                handle.close()
            if ops is not None:
                ops.close()

    started_h = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
    t0 = time.monotonic()
    threads = [threading.Thread(target=one, args=(c, s), name=f"ota-{c.name}", daemon=True)
               for c, s in zip(cabinets, board.rows)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    duration_s = time.monotonic() - t0

    rows = board.snapshot()
    text = summarise(rows, started_h, duration_s, filename, image, cfg0.crc32, stamp)
    path = log_dir / f"ota-fleet-{stamp}.txt"
    try:
        path.write_text(text, encoding="utf-8")
        saved = str(path)
    except OSError:
        saved = ""
    outcome = FleetOtaOutcome(text=text, path=saved, started=started_h,
                              duration_s=duration_s, rows=rows,
                              cabinets=list(cabinets))
    emit(FleetOtaFinished(text=text, path=saved))
    return outcome


def summarise(rows: Sequence[CabStatus], started: str, duration_s: float,
              filename: str, image: bytes, crc32: int, stamp: str) -> str:
    lines = [f"firmware update  {started}",
             f"  image {filename}   {len(image):,} B   CRC32 {crc32:08X}",
             f"  ran for {duration_s / 60:.1f} min -- the cabinets ran side by side, "
             f"so the slowest one sets the time", "",
             f"{'cabinet':18} {'mod':>4} {'updated':>8} {'min':>5}  {'firmware now':22} left behind",
             "-" * 78]
    full = mods = done_mods = 0
    for r in rows:
        mods += r.modules
        if r.state in ("refused", "failed"):
            lines.append(f"{r.name[:18]:18} {r.modules:>4} {'-':>8} {'-':>5}  {r.state}: {r.note}")
            continue
        done_mods += r.updated
        full += r.state == "done"
        left = ", ".join(map(str, r.left)) if r.left else "-"
        if r.state == "cancelled":
            left = "cancelled" + ("" if not r.left else f": {left}")
        lines.append(f"{r.name[:18]:18} {r.modules:>4} {f'{r.updated}/{r.modules}':>8} "
                     f"{r.minutes:5.1f}  {(r.census or '-')[:22]:22} {left}")
    lines += ["", f"{full} of {len(rows)} cabinets fully updated · "
                  f"{done_mods} of {mods} modules",
              f"each cabinet's own log: ota-<cabinet>-{stamp}.log"]
    return "\n".join(lines) + "\n"
