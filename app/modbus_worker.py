"""Single worker thread that owns the one pymodbus client.

Every Modbus transaction in the app funnels through this thread's job queue,
which by construction enforces: RS485 half-duplex (one txn at a time), the
Opta gateway's single-TCP-client limit (one socket per process), pymodbus
sync-client thread-unsafety, the 25 ms inter-transaction breather, and the
2.2 s latch cooldown (final authority — the UI merely previews it).

UI side uses the async facade (awaits a Future); the worker never touches UI
elements. Long jobs (scan / sweep) run as one queue job each and publish
progress into drainable event buffers.
"""
from __future__ import annotations

import asyncio
import os
import queue
import tempfile
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import (commission, fieldcheck, fw_survey, gateway_config, lgs_map,
               opta_flash, opta_update, ota, soak, stlink, testsuite)
from .lgs_map import (CoilClass, HUB_WAKE_GAP_S, HUB_WAKE_TRIES,
                      INTER_CH_S, INTER_TXN_S, LATCH_COOLDOWN_S,
                      hub_channel)
from .transports import (RtuSettings, TransportSettings, make_client,
                         make_scan_probe_client)
from .txn_log import TxnLog

_PRIO_MANUAL = 0
_PRIO_LONG = 5
_PRIO_MONITOR = 10

# Speed of the RS485 bus behind a TCP gateway (the tool only knows the TCP leg).
RS485_BUS_BAUD = 9600


@dataclass(frozen=True)
class TxnResult:
    ok: bool
    value: object = None          # int | list[int] | bool | None
    latency_ms: float = 0.0
    note: str = ""


@dataclass(frozen=True)
class WorkerState:
    connected: bool = False
    transport_desc: str = ""
    busy: bool = False
    sweep_running: bool = False
    scan_running: bool = False
    check_running: bool = False
    ota_running: bool = False
    gw_running: bool = False
    commission_running: bool = False
    last_error: str = ""

    @property
    def long_job_running(self) -> bool:
        return (self.sweep_running or self.scan_running or self.check_running
                or self.ota_running or self.gw_running or self.commission_running)


@dataclass(frozen=True)
class MonitorSnapshot:
    ts: datetime
    device_id: int
    regs: dict                    # addr -> raw (core groups)
    stats: Optional[dict]         # addr -> raw (every Nth cycle) or None
    errors: tuple


@dataclass(frozen=True)
class ScanEvent:
    seq: int
    probed: int                   # device id just probed (-1 for "done")
    found: bool
    device_type: int = -1
    done: bool = False
    found_ids: tuple = ()
    error: str = ""               # set when the scan had to give up (e.g. port)


class DangerAction(Enum):
    FACTORY_RESET_KEEP_ID = "factory reset (keep ID)"
    FACTORY_RESET_ALL = "factory reset (all data)"
    SAVE_EEPROM = "save to EEPROM"
    SOFT_RESET = "software reset"
    CLEAR_STATS = "clear statistics"


@dataclass(frozen=True)
class DangerResult:
    ok: bool
    steps: tuple
    note: str


@dataclass(order=True)
class _Job:
    priority: int
    seq: int
    fn: Callable = field(compare=False)
    future: Future = field(compare=False)


class ModbusWorker:
    def __init__(self, log: TxnLog) -> None:
        self._log = log
        # Where STM32CubeProgrammer lives, when it is not where we look by
        # default. Set from AppConfig at startup; "" means auto-detect.
        self.cubeprog_path = ""
        self.dfu_util_path = ""
        self._q: queue.PriorityQueue = queue.PriorityQueue()
        self._seq = 0
        self._seq_lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name="modbus-worker", daemon=True)
        self._stop = threading.Event()

        self._state_lock = threading.Lock()
        self._client = None
        self._settings: Optional[TransportSettings] = None
        self._connected = False
        self._busy = False
        self._last_error = ""
        # latch cooldown is per module: the firmware's 2 s minimum applies to a
        # device, not to the bus, so a multi-device check must not serialise on it
        self._cooldown_until: dict = {}
        self._last_txn_t = 0.0
        self._last_channel = None    # hub channel of the last transaction

        # raw-frame capture (worker serializes txns, so one holder is safe)
        self._trace = {"tx": "", "rx": ""}

        # long-job machinery
        self._sweep_running = False
        self._sweep_cancel = threading.Event()
        self._sweep_events: list = []
        self._sweep_lock = threading.Lock()
        self._scan_running = False
        self._scan_cancel = threading.Event()
        self._scan_events: list[ScanEvent] = []
        self._scan_lock = threading.Lock()
        self._check_running = False
        self._check_cancel = threading.Event()
        self._check_events: list = []
        self._check_lock = threading.Lock()
        self._survey_cancel = threading.Event()
        self._survey_events: list = []
        self._survey_lock = threading.Lock()
        self._soak_running = False
        self._soak_cancel = threading.Event()
        self._soak_events: list = []
        self._soak_lock = threading.Lock()
        self._ota_running = False
        self._ota_cancel = threading.Event()
        self._ota_events: list = []
        self._ota_lock = threading.Lock()
        self._commission_running = False
        self._commission_cancel = threading.Event()
        self._commission_events: list = []
        self._commission_lock = threading.Lock()
        self._gw_running = False
        self._event_seq = 0

    # ── lifecycle ──────────────────────────────────────────────────────────
    def start(self) -> None:
        self._thread.start()

    def shutdown(self) -> None:
        self._sweep_cancel.set()
        self._scan_cancel.set()
        self._stop.set()
        self._submit(_PRIO_MANUAL, lambda: None)          # wake the queue
        self._thread.join(timeout=5)
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass

    def _run(self) -> None:
        while not self._stop.is_set():
            job: _Job = self._q.get()
            if self._stop.is_set():
                job.future.cancel()
                break
            with self._state_lock:
                self._busy = True
            try:
                job.future.set_result(job.fn())
            except Exception as exc:                       # noqa: BLE001
                job.future.set_exception(exc)
            finally:
                with self._state_lock:
                    self._busy = False

    def _submit(self, priority: int, fn: Callable) -> Future:
        fut: Future = Future()
        with self._seq_lock:
            self._seq += 1
            self._q.put(_Job(priority, self._seq, fn, fut))
        return fut

    async def _run_job(self, priority: int, fn: Callable):
        return await asyncio.wrap_future(self._submit(priority, fn))

    # ── state ──────────────────────────────────────────────────────────────
    def get_state(self) -> WorkerState:
        with self._state_lock:
            desc = self._settings.describe() if self._settings else ""
            return WorkerState(self._connected, desc, self._busy,
                               self._sweep_running, self._scan_running,
                               self._check_running, self._ota_running,
                               self._gw_running, self._commission_running,
                               self._last_error)

    def cooldown_remaining(self, device_id: int) -> float:
        """Seconds left before this module will accept another unlock."""
        return max(0.0, self._cooldown_until.get(device_id, 0.0) - time.monotonic())

    @property
    def sweep_running(self) -> bool:
        return self._sweep_running

    # ── connect / disconnect ───────────────────────────────────────────────
    async def connect(self, settings: TransportSettings) -> WorkerState:
        await self._run_job(_PRIO_MANUAL, lambda: self._do_connect(settings))
        return self.get_state()

    async def disconnect(self) -> WorkerState:
        await self._run_job(_PRIO_MANUAL, self._do_disconnect)
        return self.get_state()

    def _trace_hook(self, sending: bool, data: bytes) -> bytes:
        key = "tx" if sending else "rx"
        self._trace[key] = data.hex(" ").upper()
        return data

    def _do_connect(self, settings: TransportSettings) -> None:
        self._do_disconnect()
        try:
            client = make_client(settings, trace_packet=self._trace_hook)
            ok = client.connect()
        except Exception as exc:                           # noqa: BLE001
            with self._state_lock:
                self._last_error = f"{type(exc).__name__}: {exc}"
            return
        with self._state_lock:
            if ok:
                self._client, self._settings = client, settings
                self._connected, self._last_error = True, ""
            else:
                self._last_error = (f"cannot open {settings.describe()} — port in use "
                                    f"or host unreachable")
                try:
                    client.close()
                except Exception:
                    pass

    def _do_disconnect(self) -> None:
        with self._state_lock:
            client, self._client = self._client, None
            self._connected = False
        if client is not None:
            try:
                client.close()
            except Exception:
                pass

    def _explain(self, exc: Exception) -> str:
        """Turn a pymodbus failure into something that names the real cause.

        The library's own wording sends people to the wrong place. A dropped
        TCP socket and a silent module both surface as "no response", but the
        Opta serves exactly one TCP client — so a second copy of this tool, or
        the site's own master, quietly gets its socket closed and every read
        after that looks like a dead cabinet. That has now cost two debugging
        sessions; the tool knows it is on TCP, so it can say so.
        """
        name = type(exc).__name__
        tcp = self._settings is not None and not isinstance(self._settings, RtuSettings)
        text = str(exc)
        if tcp and ("Connection" in name or "closed" in text or "reset" in text.lower()):
            return ("GATEWAY LINK LOST — the Opta closed the connection. It "
                    "serves one TCP client at a time, so another program (or "
                    "another copy of this tool) may hold it, or the gateway "
                    "rebooted. Press Connect again. " + text)
        if "ModbusIOException" in name and tcp:
            return ("No reply through the gateway. If every module looks dead, "
                    "reconnect first — the link may have dropped rather than "
                    "the bus. " + text)
        return f"EXC {name}: {text}"

    # ── core transaction (worker thread only) ──────────────────────────────
    def _transact(self, source: str, fc: int, addr: int, device_id: int, op: str,
                  call: Callable, extract: Callable, decoded_fn: Callable) -> TxnResult:
        if self._client is None:
            return TxnResult(False, note="not connected")
        # Every transaction in the app funnels through here, so the RS485 hub
        # is handled here too — one rule, and no page can forget it.
        #
        # Crossing to another hub channel costs frames, not time: the hub
        # switches to whichever channel it last saw traffic on and eats what
        # arrives mid-switch. So the first transaction after a cross gets
        # several attempts; anywhere else a single failure is a real failure
        # and must stay one, or every genuinely dead module would take six
        # timeouts to report.
        channel = hub_channel(device_id)
        crossed = self._last_channel is not None and channel != self._last_channel
        gap = (max(INTER_TXN_S, INTER_CH_S) if crossed else INTER_TXN_S) \
            - (time.monotonic() - self._last_txn_t)
        if gap > 0:
            time.sleep(gap)
        self._last_channel = channel

        attempts = HUB_WAKE_TRIES if crossed else 1
        for attempt in range(1, attempts + 1):
            self._trace["tx"] = self._trace["rx"] = ""
            t0 = time.monotonic()
            note = ""
            value = None
            ok = False
            try:
                rsp = call(self._client)
                latency = (time.monotonic() - t0) * 1000.0
                if rsp is None or rsp.isError():
                    note = f"ERR {rsp}"
                else:
                    ok, value = True, extract(rsp)
            except Exception as exc:                       # noqa: BLE001
                latency = (time.monotonic() - t0) * 1000.0
                note = self._explain(exc)
            self._last_txn_t = time.monotonic()
            if ok or attempt == attempts:
                if crossed and attempt > 1:
                    # Worth recording: if this creeps towards the ceiling the
                    # hub is degrading, and the log is where that shows first.
                    note = (note + " " if note else "") + f"[hub wake {attempt}]"
                break
            time.sleep(HUB_WAKE_GAP_S)

        decoded = decoded_fn(value) if ok else ""
        self._log.append(source, fc, addr, device_id, op, ok, value, decoded,
                         latency, note, self._trace["tx"], self._trace["rx"])
        return TxnResult(ok, value, latency, note)

    def _do_read_registers(self, addr: int, count: int, device_id: int, source: str) -> TxnResult:
        return self._transact(
            source, 3, addr, device_id, "read",
            lambda c: c.read_holding_registers(addr, count=count, device_id=device_id),
            lambda r: r.registers[0] if count == 1 else list(r.registers),
            lambda v: lgs_map.decode_register(addr, v) if count == 1 else f"block x{count}")

    def _do_read_coils(self, addr: int, count: int, device_id: int, source: str) -> TxnResult:
        return self._transact(
            source, 1, addr, device_id, "read",
            lambda c: c.read_coils(addr, count=count, device_id=device_id),
            lambda r: (1 if r.bits[0] else 0) if count == 1 else [1 if b else 0 for b in r.bits[:count]],
            lambda v: f"coil={v}")

    def _do_write_register(self, addr: int, value: int, device_id: int, source: str) -> TxnResult:
        return self._transact(
            source, 6, addr, device_id, "write",
            lambda c: c.write_register(addr, value, device_id=device_id),
            lambda r: value,
            lambda v: lgs_map.decode_register(addr, v))

    def _do_write_coil(self, addr: int, value: bool, device_id: int, source: str,
                       allow_danger: bool = False, allow_ota: bool = False) -> TxnResult:
        cls = lgs_map.classify_coil(addr)
        if cls is CoilClass.FORBIDDEN and not allow_ota:
            res = TxnResult(False, note="OTA coils are driven by the OTA tab only")
            self._log.append(source, 5, addr, device_id, "write", False, int(value), "",
                             0.0, res.note)
            return res
        if cls is CoilClass.DANGER and not allow_danger:
            res = TxnResult(False, note="danger coil — use the Danger tab")
            self._log.append(source, 5, addr, device_id, "write", False, int(value), "",
                             0.0, res.note)
            return res
        if cls is CoilClass.LATCH and value:
            remaining = self._cooldown_until.get(device_id, 0.0) - time.monotonic()
            if remaining > 0:
                res = TxnResult(False, note=f"latch cooldown — {remaining:.1f}s remaining")
                self._log.append(source, 5, addr, device_id, "write", False, int(value), "",
                                 0.0, res.note)
                return res
        result = self._transact(
            source, 5, addr, device_id, "write",
            lambda c: c.write_coil(addr, bool(value), device_id=device_id),
            lambda r: int(value),
            lambda v: f"coil={'ON' if v else 'OFF'}")
        if result.ok and cls is CoilClass.LATCH and value:
            with self._state_lock:
                self._cooldown_until[device_id] = time.monotonic() + LATCH_COOLDOWN_S
        return result

    # ── async facade (manual ops) ──────────────────────────────────────────
    def _guard(self, device_id: int) -> Optional[TxnResult]:
        if self._sweep_running or self._check_running or self._ota_running \
                or self._gw_running or self._commission_running:
            return TxnResult(False, note="a test is running — wait or cancel it")
        if not self._connected:
            return TxnResult(False, note="not connected")
        if not lgs_map.valid_target_id(device_id):
            return TxnResult(False, note=f"invalid device id {device_id} (1-247; broadcast 0 not supported)")
        return None

    async def read_registers(self, addr: int, count: int, device_id: int, *,
                             source: str = "manual") -> TxnResult:
        return self._guard(device_id) or await self._run_job(
            _PRIO_MANUAL, lambda: self._do_read_registers(addr, count, device_id, source))

    async def read_coils(self, addr: int, count: int, device_id: int, *,
                         source: str = "manual") -> TxnResult:
        return self._guard(device_id) or await self._run_job(
            _PRIO_MANUAL, lambda: self._do_read_coils(addr, count, device_id, source))

    async def write_register(self, addr: int, value: int, device_id: int, *,
                             source: str = "manual") -> TxnResult:
        return self._guard(device_id) or await self._run_job(
            _PRIO_MANUAL, lambda: self._do_write_register(addr, value, device_id, source))

    async def write_coil(self, addr: int, value: bool, device_id: int, *,
                         source: str = "manual", allow_danger: bool = False) -> TxnResult:
        return self._guard(device_id) or await self._run_job(
            _PRIO_MANUAL, lambda: self._do_write_coil(addr, value, device_id, source, allow_danger))

    # ── monitor poll ───────────────────────────────────────────────────────
    # (0,20) spans identity+diagnostics+UID 12-17+button 18/19; (20,3) adds
    # input current. Older firmware answers 0 for regs it never writes.
    MONITOR_GROUPS = ((0, 20), (20, 3), (40, 2), (60, 1))
    STATS_GROUP = (200, 82)

    async def poll_monitor(self, device_id: int, *, with_stats: bool) -> Optional[MonitorSnapshot]:
        st = self.get_state()
        if not st.connected or st.busy or st.long_job_running:
            return None                                    # skip-if-busy: no backlog
        return await self._run_job(
            _PRIO_MONITOR, lambda: self._do_poll_monitor(device_id, with_stats))

    def _do_poll_monitor(self, device_id: int, with_stats: bool) -> MonitorSnapshot:
        regs: dict = {}
        errors: list[str] = []
        for start, count in self.MONITOR_GROUPS:
            res = self._do_read_registers(start, count, device_id, "monitor")
            if res.ok:
                vals = res.value if isinstance(res.value, list) else [res.value]
                for i, v in enumerate(vals):
                    regs[start + i] = v
            else:
                errors.append(f"regs {start}+{count}: {res.note}")
                break                                      # device likely absent — don't stack timeouts
        stats = None
        if with_stats and not errors:
            res = self._do_read_registers(*self.STATS_GROUP, device_id, "monitor")
            if res.ok:
                stats = {self.STATS_GROUP[0] + i: v for i, v in enumerate(res.value)}
            else:
                errors.append(f"stats: {res.note}")
        return MonitorSnapshot(datetime.now(), device_id, regs, stats, tuple(errors))

    # ── ID scan (long job) ─────────────────────────────────────────────────
    def start_scan(self, settings: TransportSettings, ids: Sequence[int]) -> bool:
        if self._scan_running or self._sweep_running:
            return False
        self._scan_cancel.clear()
        with self._scan_lock:
            self._scan_events.clear()
        self._scan_running = True
        self._submit(_PRIO_LONG, lambda: self._do_scan(settings, list(ids)))
        return True

    def cancel_scan(self) -> None:
        self._scan_cancel.set()

    def drain_scan_events(self, since: int) -> tuple[int, list[ScanEvent]]:
        with self._scan_lock:
            fresh = [e for e in self._scan_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _emit_scan(self, **kw) -> None:
        with self._scan_lock:
            self._event_seq += 1
            self._scan_events.append(ScanEvent(seq=self._event_seq, **kw))

    def _do_scan(self, settings: TransportSettings, ids: list) -> None:
        was_connected = self._connected
        prev_settings = self._settings
        try:
            self._do_disconnect()                          # free the COM port / TCP slot
            found: list[int] = []
            fatal = ""
            for uid in ids:
                if self._scan_cancel.is_set():
                    break
                probe = None
                ok, dtype = False, -1
                try:
                    # Opening the port is the only fatal step: if it fails, probing
                    # the remaining ids repeats the same failure and reports "no
                    # devices", hiding the real reason.
                    probe = make_scan_probe_client(settings)
                    opened = probe.connect()
                    if not opened:
                        fatal = (f"cannot open {settings.describe()} — unplugged, "
                                 f"in use by another program, or wrong host")
                except Exception as exc:                   # noqa: BLE001
                    fatal = f"{settings.describe()}: {type(exc).__name__}: {exc}"
                if not fatal:
                    try:
                        rsp = probe.read_holding_registers(0, count=1, device_id=uid)
                        if rsp is not None and not rsp.isError():
                            ok, dtype = True, rsp.registers[0]
                    except Exception:                      # noqa: BLE001
                        pass    # timeout / IO error: this id simply has no device
                if probe is not None:
                    try:
                        probe.close()
                    except Exception:                      # noqa: BLE001
                        pass
                if fatal:
                    self._log.append("scan", 3, 0, uid, "probe", False, None, "",
                                     0.0, fatal)
                    break
                if ok:
                    found.append(uid)
                    self._log.append("scan", 3, 0, uid, "probe", True, dtype,
                                     lgs_map.dec_device_type(dtype), 0.0)
                self._emit_scan(probed=uid, found=ok, device_type=dtype)
                time.sleep(0.02)                           # let the OS release the port
            self._emit_scan(probed=-1, found=False, done=True,
                            found_ids=tuple(found), error=fatal)
        finally:
            if was_connected and prev_settings is not None:
                self._do_connect(prev_settings)
            self._scan_running = False

    # ── sweep (long job) ───────────────────────────────────────────────────
    def start_sweep(self, cfg: "testsuite.SweepConfig", device_id: int) -> bool:
        if self._sweep_running or self._scan_running or not self._connected:
            return False
        self._sweep_cancel.clear()
        with self._sweep_lock:
            self._sweep_events.clear()
        self._sweep_running = True
        self._submit(_PRIO_LONG, lambda: self._do_sweep(cfg, device_id))
        return True

    def cancel_sweep(self) -> None:
        self._sweep_cancel.set()

    def drain_sweep_events(self, since: int) -> tuple[int, list]:
        with self._sweep_lock:
            fresh = [e for e in self._sweep_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_sweep(self, cfg: "testsuite.SweepConfig", device_id: int) -> None:
        def emit(ev) -> None:
            with self._sweep_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._sweep_events.append(ev)

        ops = _WorkerOps(self, device_id)
        try:
            testsuite.run_sweep(ops, cfg, emit, self._sweep_cancel)
        finally:
            self._sweep_running = False

    # ── broadcast (device id 0, no reply expected) ─────────────────────────
    def _broadcast_wire_time(self, kind: str, payload) -> float:
        """How long the frame occupies the RS485 line, in seconds.

        A broadcast gets no reply, so nothing paces the sender: over USB the
        write returns immediately while the bus (or the Opta bridge's queue)
        is still busy. Without this wait the next frame is appended to the
        previous one in the bridge's buffer, the 10 ms gap that delimits a
        frame never appears, and the merged bytes fail CRC and are dropped —
        which is exactly how an OTA session starves and times out.
        """
        nbytes = (9 + len(payload) * 2) if kind == "regs" else 8
        baud = self._settings.baud if isinstance(self._settings, RtuSettings) else RS485_BUS_BAUD
        return nbytes * 10.0 / max(1, baud)

    def _do_broadcast(self, kind: str, addr: int, payload, source: str = "ota",
                      log: bool = True) -> TxnResult:
        if self._client is None:
            return TxnResult(False, note="not connected")
        gap = INTER_TXN_S - (time.monotonic() - self._last_txn_t)
        if gap > 0:
            time.sleep(gap)
        self._trace["tx"] = self._trace["rx"] = ""
        t0 = time.monotonic()
        ok, note = True, ""
        try:
            if kind == "regs":
                self._client.write_registers(addr, payload, device_id=0,
                                             no_response_expected=True)
            else:
                self._client.write_coil(addr, True, device_id=0,
                                        no_response_expected=True)
        except Exception as exc:                           # noqa: BLE001
            ok, note = False, f"EXC {type(exc).__name__}: {exc}"
        if ok:
            time.sleep(self._broadcast_wire_time(kind, payload))
        latency = (time.monotonic() - t0) * 1000.0
        self._last_txn_t = time.monotonic()
        if log:
            self._log.append(source, 16 if kind == "regs" else 5, addr, 0, "broadcast",
                             ok, len(payload) if kind == "regs" else 1,
                             "broadcast (no reply expected)", latency, note,
                             self._trace["tx"], "")
        return TxnResult(ok, None, latency, note)

    # ── Gateway console (borrows the COM port, like the ID scan) ───────────
    def _do_gw_session(self, port: str, body, *, reconnect_delay_s: float = 0.0):
        """Run `body(link)` with the Modbus client stood down.

        The gateway console needs the raw port, and a COM port serves one
        program at a time — so this follows _do_scan exactly: drop the Modbus
        client, do the work, restore the previous connection in `finally`.
        """
        was_connected = self._connected
        prev_settings = self._settings
        self._gw_running = True
        try:
            self._do_disconnect()
            try:
                with gateway_config.GatewayLink(port) as link:
                    return body(link)
            except (OSError, gateway_config.GatewayError) as exc:
                self._log.append("gateway", 0, 0, 0, "session", False, None, "",
                                 0.0, f"{type(exc).__name__}: {exc}")
                return exc
        finally:
            if reconnect_delay_s:
                time.sleep(reconnect_delay_s)
            if was_connected and prev_settings is not None:
                self._do_connect(prev_settings)
            self._gw_running = False

    def _log_gw(self, verb: str, res) -> None:
        self._log.append("gateway", 0, 0, 0, verb, res.ok, None,
                         " ".join(res.lines[-1:]) if res.lines else "",
                         0.0, "" if res.ok else res.error_text)

    async def gw_probe(self, port: str) -> Optional[dict]:
        return await self._run_job(
            _PRIO_MANUAL,
            lambda: self._do_gw_session(port, lambda link: (
                dict(link.ping().data) if link.ping().ok else None)))

    async def gw_read(self, port: str):
        def body(link):
            snap = link.snapshot()
            self._log.append("gateway", 0, 0, 0, "read", snap.ok, None,
                             f"{len(snap.settings)} keys", 0.0, snap.note)
            return snap

        res = await self._run_job(_PRIO_MANUAL, lambda: self._do_gw_session(port, body))
        if isinstance(res, Exception):
            return gateway_config.GwSnapshot(False, note=str(res))
        return res

    async def gw_write(self, port: str, changes: dict, *, save: bool):
        def body(link):
            steps: list[str] = []
            hello = link.hello()
            self._log_gw("HELLO", hello)
            if not hello.ok:
                return gateway_config.GwActionResult(False, tuple(steps),
                                                     hello.error_text or "HELLO failed")
            steps.append("session armed")

            # The gateway keeps staged edits across sessions, so anything a
            # console experiment (or an interrupted write) left behind would
            # ride this SAVE unseen. Start from a clean slate: this SAVE
            # commits exactly what this dialog showed, nothing else.
            res = link.discard()
            self._log_gw("DISCARD", res)
            if not res.ok:
                link.bye()
                return gateway_config.GwActionResult(False, tuple(steps),
                                                     res.error_text)

            if changes:
                res = link.set_many(changes)
                self._log_gw("SET", res)
                steps.append(f"SET {len(changes)} key(s): "
                             + ("ok" if res.ok else res.error_text))
                if not res.ok:
                    link.bye()
                    return gateway_config.GwActionResult(False, tuple(steps), res.error_text)

            if save:
                res = link.save()
                self._log_gw("SAVE", res)
                if not res.ok:
                    link.bye()
                    return gateway_config.GwActionResult(False, tuple(steps), res.error_text)
                applied = res.data.get("applied", "-")
                pending = res.data.get("pending_reboot", "")
                steps.append(f"SAVE applied={applied}"
                             + (f", needs reboot: {pending}" if pending else ""))
                link.bye()
                return gateway_config.GwActionResult(True, tuple(steps), pending)

            link.bye()
            return gateway_config.GwActionResult(True, tuple(steps), "")

        res = await self._run_job(_PRIO_MANUAL, lambda: self._do_gw_session(port, body))
        if isinstance(res, Exception):
            return gateway_config.GwActionResult(False, (), str(res))
        return res

    async def gw_set_time(self, port: str, epoch: int):
        """Set the gateway's wall clock.

        Not part of gw_write: the clock is not a stored setting. The Opta
        cannot keep time through a power cut, so this is sent every time the
        tool meets a gateway whose clock is unset — the schedule is useless
        until somebody does, and nobody should have to remember to.
        """
        def body(link):
            res = link.command(f"TIME {int(epoch)}")
            self._log_gw("TIME", res)
            return gateway_config.GwActionResult(
                res.ok, tuple(res.lines), res.error_text if not res.ok else "")

        res = await self._run_job(_PRIO_MANUAL, lambda: self._do_gw_session(port, body))
        if isinstance(res, Exception):
            return gateway_config.GwActionResult(False, (), str(res))
        return res

    async def gw_read_log(self, port: str, n: int = 30):
        """Newest `n` gateway event-log records (fw >= 1.11.0), formatted one
        per line in `.steps`. Read-only: no HELLO, no DISCARD."""
        def body(link):
            res = link.log(n)
            self._log_gw("LOG", res)
            lines: list[str] = []
            for row in res.rows:
                aux, par = row.get("a", "0"), row.get("p", "0")
                detail = f"  a={aux} p={par}" if (aux != "0" or par != "0") else ""
                lines.append(f"#{row.get('i', '?')}  {row.get('t', '-')}"
                             f"  up={row.get('up', '?')}s"
                             f"  {row.get('ev', '?')}{detail}")
            return gateway_config.GwActionResult(
                res.ok, tuple(lines), res.error_text if not res.ok else "")

        res = await self._run_job(_PRIO_MANUAL, lambda: self._do_gw_session(port, body))
        if isinstance(res, Exception):
            return gateway_config.GwActionResult(False, (), str(res))
        return res

    async def gw_action(self, port: str, action: str):
        """action: discard | defaults | reboot"""
        def body(link):
            steps: list[str] = []
            hello = link.hello()
            self._log_gw("HELLO", hello)
            if not hello.ok:
                return gateway_config.GwActionResult(False, (), hello.error_text)
            values: dict = {}
            if action == "discard":
                res = link.discard()
            elif action == "defaults":
                res = link.defaults()
                # DEFAULTS only *stages* the factory values, and BYE — like the
                # 120 s session timeout — discards anything staged. So read them
                # back while the session is still armed and hand them to the
                # caller as ordinary pending edits.
                if res.ok:
                    values = link.staged_values()
                    steps.append(f"read back {len(values)} factory value(s)")
            elif action == "reboot":
                res = link.reboot()
            else:
                return gateway_config.GwActionResult(False, (), f"unknown action {action}")
            self._log_gw(action.upper(), res)
            steps.append(f"{action}: " + ("ok" if res.ok else res.error_text))
            if action != "reboot":
                link.bye()
            return gateway_config.GwActionResult(res.ok, tuple(steps),
                                                 "" if res.ok else res.error_text,
                                                 values)

        # A reboot re-enumerates the CDC; give Windows time before reconnecting.
        delay = 4.0 if action == "reboot" else 0.0
        res = await self._run_job(
            _PRIO_MANUAL,
            lambda: self._do_gw_session(port, body, reconnect_delay_s=delay))
        if isinstance(res, Exception):
            return gateway_config.GwActionResult(False, (), str(res))
        return res

    # ── OTA (long job) ─────────────────────────────────────────────────────
    def start_ota(self, cfg: "ota.OtaConfig") -> bool:
        if self._ota_running or self._sweep_running or self._scan_running \
                or self._check_running or not self._connected or not cfg.ids:
            return False
        self._ota_cancel.clear()
        with self._ota_lock:
            self._ota_events.clear()
        self._ota_running = True
        self._submit(_PRIO_LONG, lambda: self._do_ota(cfg))
        return True

    def cancel_ota(self) -> None:
        self._ota_cancel.set()

    def drain_ota_events(self, since: int) -> tuple[int, list]:
        with self._ota_lock:
            fresh = [e for e in self._ota_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_ota(self, cfg: "ota.OtaConfig") -> None:
        def emit(ev) -> None:
            with self._ota_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._ota_events.append(ev)

        try:
            ota.run_ota(_OtaOps(self), cfg, emit, self._ota_cancel)
        finally:
            self._ota_running = False

    # ── commissioning (ST-Link; no bus involved) ───────────────────────────
    def start_commission(self, cfg: "commission.CommissionConfig") -> bool:
        """Unlike the other long jobs this does not need a Modbus connection:
        the module is flashed over SWD and may not be on the bus at all."""
        if self._commission_running or self._sweep_running or self._scan_running \
                or self._check_running or self._ota_running or not cfg.image:
            return False
        self._commission_cancel.clear()
        with self._commission_lock:
            self._commission_events.clear()
        self._commission_running = True
        self._submit(_PRIO_LONG, lambda: self._do_commission(cfg))
        return True

    def cancel_commission(self) -> None:
        self._commission_cancel.set()

    def drain_commission_events(self, since: int) -> tuple[int, list]:
        with self._commission_lock:
            fresh = [e for e in self._commission_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_commission(self, cfg: "commission.CommissionConfig") -> None:
        def emit(ev) -> None:
            with self._commission_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._commission_events.append(ev)

        try:
            commission.run_commission(_CommissionOps(self), cfg, emit,
                                      self._commission_cancel)
        finally:
            self._commission_running = False

    def start_opta_update(self, cfg: "opta_update.OptaConfig",
                          provision: bool = False) -> bool:
        """Update the gateway's own firmware over USB.

        Shares the commissioning slot and event stream: both are long jobs
        that take a device away from the bus, and the UI already drains that
        one stream. Unlike commissioning this *does* need the Modbus port —
        it is the gateway's — so it drops the connection first, exactly like
        the gateway console does.
        """
        if self._commission_running or self._sweep_running or self._scan_running \
                or self._check_running or self._ota_running or self._gw_running \
                or not cfg.image or not cfg.port:
            return False
        self._commission_cancel.clear()
        with self._commission_lock:
            self._commission_events.clear()
        self._commission_running = True
        self._submit(_PRIO_LONG, lambda: self._do_opta_update(cfg, provision))
        return True

    def start_opta_provision(self, cfg: "opta_update.OptaConfig") -> bool:
        """Partition a factory-fresh Opta's QSPI, then put the firmware back."""
        return self.start_opta_update(cfg, provision=True)

    def _do_opta_update(self, cfg: "opta_update.OptaConfig",
                        provision: bool = False) -> None:
        def emit(ev) -> None:
            with self._commission_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._commission_events.append(ev)

        was_connected = self._connected
        prev_settings = self._settings
        run = opta_update.run_provision if provision else opta_update.run_update
        try:
            self._do_disconnect()       # the gateway's USB is our Modbus port
            run(_OptaOps(self), cfg, emit, self._commission_cancel)
        finally:
            # Reconnecting is left to the operator: the gateway has just
            # rebooted onto new firmware, and silently restoring a session
            # would hide whether it actually came back.
            if was_connected and prev_settings is not None:
                self._log.append("gateway", 0, 0, 0, "reconnect", True, None,
                                 "left disconnected after a firmware update",
                                 0.0, "")
            self._commission_running = False

    def start_batch_commission(self, cfg: "commission.BatchConfig") -> bool:
        """Same slot as single commissioning — one ST-Link, one job at a time."""
        if self._commission_running or self._sweep_running or self._scan_running \
                or self._check_running or self._ota_running \
                or not cfg.image or not cfg.ids:
            return False
        self._commission_cancel.clear()
        with self._commission_lock:
            self._commission_events.clear()
        self._commission_running = True
        self._submit(_PRIO_LONG, lambda: self._do_batch_commission(cfg))
        return True

    def _do_batch_commission(self, cfg: "commission.BatchConfig") -> None:
        def emit(ev) -> None:
            with self._commission_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._commission_events.append(ev)

        try:
            commission.run_batch(_CommissionOps(self), cfg, emit,
                                 self._commission_cancel)
        finally:
            self._commission_running = False

    async def ota_status(self, ids: Sequence[int]) -> list:
        """[(device_id, description)] — quick read of reg 282/283 per device."""
        if not self._connected:
            return [(uid, "not connected") for uid in ids]
        return await self._run_job(_PRIO_MANUAL, lambda: self._do_ota_status(list(ids)))

    def _do_ota_status(self, ids: list) -> list:
        ops = _OtaOps(self)
        return [(uid, ota.describe_state(ota.read_state(ops, uid))) for uid in ids]

    async def ota_abort(self) -> TxnResult:
        if not self._connected:
            return TxnResult(False, note="not connected")
        return await self._run_job(
            _PRIO_MANUAL, lambda: self._do_broadcast("coil", ota.COIL_ABORT))

    # ── installation check (long job, many devices) ────────────────────────
    def start_field_check(self, cfg: "fieldcheck.CheckConfig",
                          ids: Sequence[int]) -> bool:
        if self._check_running or self._sweep_running or self._scan_running \
                or not self._connected or not ids:
            return False
        self._check_cancel.clear()
        with self._check_lock:
            self._check_events.clear()
        self._check_running = True
        self._submit(_PRIO_LONG, lambda: self._do_field_check(cfg, list(ids)))
        return True

    def cancel_field_check(self) -> None:
        self._check_cancel.set()

    def drain_field_check_events(self, since: int) -> tuple[int, list]:
        with self._check_lock:
            fresh = [e for e in self._check_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_field_check(self, cfg: "fieldcheck.CheckConfig", ids: list) -> None:
        def emit(ev) -> None:
            with self._check_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._check_events.append(ev)

        try:
            fieldcheck.run_check(_FieldOps(self), cfg, ids, emit, self._check_cancel)
        finally:
            self._check_running = False

    def start_pick_sequence(self, cfg: "fieldcheck.PickConfig",
                            ids: Sequence[int]) -> bool:
        """Same slot, cancel and event stream as the installation check —
        the pick walkthrough is that page's other run mode."""
        if self._check_running or self._sweep_running or self._scan_running \
                or not self._connected or not ids:
            return False
        self._check_cancel.clear()
        with self._check_lock:
            self._check_events.clear()
        self._check_running = True
        self._submit(_PRIO_LONG, lambda: self._do_pick_sequence(cfg, list(ids)))
        return True

    def _do_pick_sequence(self, cfg: "fieldcheck.PickConfig", ids: list) -> None:
        def emit(ev) -> None:
            with self._check_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._check_events.append(ev)

        try:
            fieldcheck.run_pick_sequence(_FieldOps(self), cfg, ids, emit,
                                         self._check_cancel)
        finally:
            self._check_running = False

    # ── bus soak (read-only, runs for hours, its own event stream) ─────────
    def start_soak(self, cfg: "soak.SoakConfig", log_path=None) -> bool:
        """Poll the cabinet until cancelled, watching for silent reboots.

        Takes the same long-job slot as the surveys — one bus, one sweep —
        but unlike them it does not end on its own.
        """
        if self._check_running or self._sweep_running or self._scan_running \
                or self._ota_running or not self._connected or not cfg.ids:
            return False
        self._soak_cancel.clear()
        with self._soak_lock:
            self._soak_events.clear()
        self._soak_running = True
        self._check_running = True                # occupies the same slot
        self._submit(_PRIO_LONG, lambda: self._do_soak(cfg, log_path))
        return True

    def cancel_soak(self) -> None:
        self._soak_cancel.set()
        self._check_cancel.set()                  # _SurveyOps.sleep watches this

    def soak_running(self) -> bool:
        return self._soak_running

    def drain_soak_events(self, since: int) -> tuple[int, list]:
        with self._soak_lock:
            fresh = [e for e in self._soak_events if e.seq > since]
            # An overnight run must not grow a list until the process dies.
            if len(self._soak_events) > 2000:
                del self._soak_events[:-500]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_soak(self, cfg: "soak.SoakConfig", log_path) -> None:
        def emit(ev) -> None:
            with self._soak_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._soak_events.append(ev)

        handle = None
        if log_path is not None:
            try:
                handle = open(log_path, "a", encoding="utf-8", buffering=1)
                handle.write("time,device_id,kind,detail\n")
            except OSError:
                handle = None      # the run matters more than its paper trail

        def log_line(text: str) -> None:
            if handle is not None:
                try:
                    handle.write(text + "\n")
                except OSError:
                    pass

        try:
            self._check_cancel.clear()
            soak.run_soak(_SurveyOps(self), cfg, emit, self._soak_cancel, log_line)
        finally:
            self._soak_running = False
            self._check_running = False
            if handle is not None:
                try:
                    handle.close()
                except OSError:
                    pass

    # ── firmware survey (read-only, its own event stream) ──────────────────
    def start_fw_survey(self, ids: Sequence[int]) -> bool:
        """Read every module's firmware version.

        Shares the long-job guard with the installation check: one bus, one
        sweep at a time. Its events go to their own queue so the two pages
        never read each other's.
        """
        if self._check_running or self._sweep_running or self._scan_running \
                or self._ota_running or not self._connected or not ids:
            return False
        self._survey_cancel.clear()
        with self._survey_lock:
            self._survey_events.clear()
        self._check_running = True                # occupies the same slot
        self._submit(_PRIO_LONG, lambda: self._do_fw_survey(list(ids)))
        return True

    def cancel_fw_survey(self) -> None:
        self._survey_cancel.set()
        self._check_cancel.set()                  # _SurveyOps.sleep watches this

    def drain_fw_survey_events(self, since: int) -> tuple[int, list]:
        with self._survey_lock:
            fresh = [e for e in self._survey_events if e.seq > since]
            return (fresh[-1].seq if fresh else since), fresh

    def _do_fw_survey(self, ids: list) -> None:
        def emit(ev) -> None:
            with self._survey_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._survey_events.append(ev)

        try:
            self._check_cancel.clear()
            fw_survey.run_survey(_SurveyOps(self), ids, emit, self._survey_cancel)
        finally:
            self._check_running = False

    # ── site-report sweep (read-only; the survey stream carries it) ────────
    def start_report_survey(self, ids: Sequence[int]) -> bool:
        """Registers 0-17 of every module — the site report's raw material.

        Same slot and same event queue as the firmware survey; pages keep
        their own drain cursor, so the streams do not steal each other's
        events.
        """
        if self._check_running or self._sweep_running or self._scan_running \
                or self._ota_running or not self._connected or not ids:
            return False
        self._survey_cancel.clear()
        with self._survey_lock:
            self._survey_events.clear()
        self._check_running = True
        self._submit(_PRIO_LONG, lambda: self._do_report_survey(list(ids)))
        return True

    def _do_report_survey(self, ids: list) -> None:
        def emit(ev) -> None:
            with self._survey_lock:
                self._event_seq += 1
                ev.seq = self._event_seq
                self._survey_events.append(ev)

        try:
            self._check_cancel.clear()
            fw_survey.run_report_survey(_SurveyOps(self), ids, emit,
                                        self._survey_cancel)
        finally:
            self._check_running = False

    # ── danger actions ─────────────────────────────────────────────────────
    async def danger_action(self, action: DangerAction, device_id: int) -> DangerResult:
        guard = self._guard(device_id)
        if guard is not None:
            return DangerResult(False, (), guard.note)
        return await self._run_job(_PRIO_MANUAL, lambda: self._do_danger(action, device_id))

    def _do_danger(self, action: DangerAction, device_id: int) -> DangerResult:
        steps: list[TxnResult] = []

        def coil(addr: int, tolerate_timeout: bool = False) -> bool:
            res = self._do_write_coil(addr, True, device_id, "danger", allow_danger=True)
            if not res.ok and tolerate_timeout:
                res = TxnResult(True, None, res.latency_ms, "no reply — device rebooting (expected)")
            steps.append(res)
            return res.ok

        def probe(pid: int) -> bool:
            r0 = self._do_read_registers(0, 1, pid, "danger")
            steps.append(r0)
            r7 = self._do_read_registers(7, 1, pid, "danger")
            steps.append(r7)
            return r0.ok

        if action is DangerAction.CLEAR_STATS:
            if not coil(510):
                return DangerResult(False, tuple(steps), "coil 510 write failed")
            time.sleep(0.5)
            r200 = self._do_read_registers(200, 2, device_id, "danger")
            steps.append(r200)
            zeroed = r200.ok and list(r200.value) == [0, 0]
            return DangerResult(zeroed, tuple(steps),
                                "statistics cleared" if zeroed else "readback not zero")

        if action in (DangerAction.SAVE_EEPROM, DangerAction.SOFT_RESET):
            addr = 503 if action is DangerAction.SAVE_EEPROM else 504
            coil(addr, tolerate_timeout=True)
            time.sleep(4.0)
            ok = probe(device_id)
            return DangerResult(ok, tuple(steps),
                                "device back online after reboot" if ok else "device did not come back — check power/bus")

        # Factory reset: pick the mode on 501/502 FIRST, then fire 500.
        #
        # The firmware registers its handler on coil 500 and reads 501/502
        # inside it (LGS-Standard-Module src/app/ops.cpp): 500 is the trigger,
        # 501/502 are the modifier. Writing 500 first ran the handler with no
        # modifier set, so it rejected the command and cleared 500 — and then
        # the 501/502 write just latched a modifier that nothing consumed,
        # leaving the device one stray write-to-500 away from an unasked-for
        # wipe. Clear the modifier on any failure for the same reason.
        mode_addr = 501 if action is DangerAction.FACTORY_RESET_KEEP_ID else 502
        if not coil(mode_addr):
            return DangerResult(False, tuple(steps), f"coil {mode_addr} write failed")
        time.sleep(0.2)
        if not coil(500, tolerate_timeout=True):
            self._do_write_coil(mode_addr, False, device_id, "danger", allow_danger=True)
            return DangerResult(False, tuple(steps), "trigger coil 500 failed")
        time.sleep(4.0)
        probe_id = device_id if action is DangerAction.FACTORY_RESET_KEEP_ID else lgs_map.FACTORY_DEFAULT_ID
        ok = probe(probe_id)
        note = ("device back online after reset" if ok else "device did not answer after reset")
        if action is DangerAction.FACTORY_RESET_ALL:
            note += f" — defaults restored: ID {lgs_map.FACTORY_DEFAULT_ID}, baud 9600"
        return DangerResult(ok, tuple(steps), note)

    # ── set slave ID (write reg 4 → persist via coil 503 → probe new id) ───
    async def set_slave_id(self, current_id: int, new_id: int) -> DangerResult:
        guard = self._guard(current_id)
        if guard is not None:
            return DangerResult(False, (), guard.note)
        if not lgs_map.valid_assignable_id(new_id):
            return DangerResult(False, (),
                                f"invalid new id {new_id} (1-245 or 247; 246 is the SET_ID temp ID)")
        return await self._run_job(_PRIO_MANUAL, lambda: self._do_set_slave_id(current_id, new_id))

    def _do_set_slave_id(self, current_id: int, new_id: int) -> DangerResult:
        steps: list[TxnResult] = []

        r4 = self._do_read_registers(4, 1, current_id, "danger")
        steps.append(r4)
        if not r4.ok:
            return DangerResult(False, tuple(steps), f"device {current_id} is not answering")

        w = self._do_write_register(4, new_id, current_id, "danger")
        steps.append(w)
        if not w.ok:
            return DangerResult(False, tuple(steps), "writing reg 4 failed")

        rb = self._do_read_registers(4, 1, current_id, "danger")
        steps.append(rb)
        if not rb.ok or rb.value != new_id:
            return DangerResult(False, tuple(steps),
                                f"reg 4 readback mismatch (got {rb.value}, expected {new_id})")

        res = self._do_write_coil(503, True, current_id, "danger", allow_danger=True)
        if not res.ok:
            res = TxnResult(True, None, res.latency_ms, "no reply — device rebooting (expected)")
        steps.append(res)
        time.sleep(4.0)

        probe = self._do_read_registers(4, 1, new_id, "danger")
        steps.append(probe)
        ok = probe.ok and probe.value == new_id
        if ok:
            note = f"slave ID changed {current_id} → {new_id} and persisted"
        else:
            # R5.0 validates at persist time; a rejected value reverts to the old ID
            back = self._do_read_registers(4, 1, current_id, "danger")
            steps.append(back)
            note = (f"device still answers at old id {current_id} — new ID rejected at persist"
                    if back.ok else f"device did not answer at new id {new_id} after reboot")
        return DangerResult(ok, tuple(steps), note)


class _OtaOps:
    """ota.OtaOps bound to the worker (runs on the worker thread)."""

    def __init__(self, worker: ModbusWorker) -> None:
        self._w = worker

    def read_regs(self, device_id: int, addr: int, count: int) -> TxnResult:
        return self._w._do_read_registers(addr, count, device_id, "ota")

    def bcast_regs(self, addr: int, values: list, log: bool = True) -> TxnResult:
        return self._w._do_broadcast("regs", addr, values, "ota", log)

    def bcast_coil(self, addr: int) -> TxnResult:
        return self._w._do_broadcast("coil", addr, [1], "ota")

    def write_coil(self, device_id: int, addr: int, value: int) -> TxnResult:
        return self._w._do_write_coil(addr, bool(value), device_id, "ota", allow_ota=True)

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._ota_cancel.is_set():
                raise ota.OtaCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class _FieldOps:
    """fieldcheck.FieldOps — device id per call (runs on the worker thread)."""

    def __init__(self, worker: ModbusWorker) -> None:
        self._w = worker

    def read_reg(self, device_id: int, addr: int) -> TxnResult:
        return self._w._do_read_registers(addr, 1, device_id, "check")

    def write_reg(self, device_id: int, addr: int, value: int) -> TxnResult:
        return self._w._do_write_register(addr, value, device_id, "check")

    def write_coil(self, device_id: int, addr: int, value: int) -> TxnResult:
        return self._w._do_write_coil(addr, bool(value), device_id, "check")

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._check_cancel.is_set():
                raise fieldcheck.CheckCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class _SurveyOps:
    """fw_survey.SurveyOps — read-only, one transaction per module."""

    def __init__(self, worker: ModbusWorker) -> None:
        self._w = worker

    def read_regs(self, device_id: int, addr: int, count: int) -> TxnResult:
        return self._w._do_read_registers(addr, count, device_id, "survey")

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._check_cancel.is_set():
                return              # the loop checks cancel; nothing to unwind
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class _OptaOps:
    """opta_update.OptaOps bound to the worker (runs on the worker thread)."""

    def __init__(self, worker: ModbusWorker) -> None:
        self._w = worker

    def find_tool(self):
        return opta_flash.find_dfu_util(self._w.dfu_util_path)

    def touch(self, port: str) -> None:
        opta_flash.touch_1200(port)

    def wait_for_dfu(self, tool, cancel):
        return opta_flash.wait_for_dfu(tool, cancel=cancel)

    def flash(self, tool, device, image_path, on_line, cancel):
        return opta_flash.flash(tool, device, image_path, on_line=on_line,
                                cancel=cancel)

    def write_temp(self, data: bytes, name: str) -> Path:
        fd, path = tempfile.mkstemp(prefix="lgs_gateway_", suffix=".bin")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return Path(path)

    def remove_temp(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._commission_cancel.is_set():
                return          # a finished flash is not worth cancelling over
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))

    def blob(self, name: str) -> bytes:
        return opta_flash.blob(name)

    def find_port(self, timeout_s: float, cancel) -> str:
        return opta_flash.find_serial_port(timeout_s, cancel)

    def converse(self, port, on_line, answer, done_marker, timeout_s, cancel):
        return opta_flash.converse(port, on_line, answer, done_marker,
                                   timeout_s, cancel)


class _CommissionOps:
    """commission.CommissionOps bound to the worker (runs on the worker thread).

    None of this touches Modbus: commissioning happens entirely over SWD, and
    the module being flashed may not be on the bus at all.
    """

    def __init__(self, worker: ModbusWorker) -> None:
        self._w = worker

    def find_programmer(self):
        return stlink.find_cli(self._w.cubeprog_path)

    def programmer_version(self, cli) -> str:
        return stlink.version(cli)

    def list_probes(self, cli) -> list:
        return stlink.list_probes(cli)

    def read_uid(self, cli) -> str:
        try:
            return stlink.read_uid(cli)
        except stlink.ProgrammerError:
            return ""           # a missing serial is worth noting, not failing

    def probe(self, cli):
        return stlink.probe_board(cli)

    def flash(self, cli, image_path, on_line, cancel):
        return stlink.flash(cli, image_path, on_line=on_line, cancel=cancel)

    def write_temp(self, data: bytes, name: str) -> Path:
        # The patched image is never left on disk under a name someone could
        # re-flash later: one file per board, deleted when the job ends.
        fd, path = tempfile.mkstemp(prefix="lgs_commission_", suffix=".bin")
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        return Path(path)

    def remove_temp(self, path: Path) -> None:
        try:
            path.unlink()
        except OSError:
            pass

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._commission_cancel.is_set():
                raise commission.CommissionCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class _WorkerOps:
    """testsuite.ModbusOps bound to the worker internals (runs on worker thread)."""

    def __init__(self, worker: ModbusWorker, device_id: int) -> None:
        self._w = worker
        self._id = device_id

    def read_reg(self, addr: int) -> TxnResult:
        return self._w._do_read_registers(addr, 1, self._id, "sweep")

    def read_coil(self, addr: int) -> TxnResult:
        return self._w._do_read_coils(addr, 1, self._id, "sweep")

    def write_reg(self, addr: int, value: int) -> TxnResult:
        return self._w._do_write_register(addr, value, self._id, "sweep")

    def write_coil(self, addr: int, value: int) -> TxnResult:
        return self._w._do_write_coil(addr, bool(value), self._id, "sweep")

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._w._sweep_cancel.is_set():
                raise testsuite.SweepCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))
