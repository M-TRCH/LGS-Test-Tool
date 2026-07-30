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
import queue
import threading
import time
from concurrent.futures import Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Sequence

from . import fieldcheck, lgs_map, ota, testsuite
from .lgs_map import CoilClass, INTER_TXN_S, LATCH_COOLDOWN_S
from .transports import TransportSettings, make_client, make_scan_probe_client
from .txn_log import TxnLog

_PRIO_MANUAL = 0
_PRIO_LONG = 5
_PRIO_MONITOR = 10


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
    last_error: str = ""

    @property
    def long_job_running(self) -> bool:
        return (self.sweep_running or self.scan_running or self.check_running
                or self.ota_running)


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
        self._ota_running = False
        self._ota_cancel = threading.Event()
        self._ota_events: list = []
        self._ota_lock = threading.Lock()
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

    # ── core transaction (worker thread only) ──────────────────────────────
    def _transact(self, source: str, fc: int, addr: int, device_id: int, op: str,
                  call: Callable, extract: Callable, decoded_fn: Callable) -> TxnResult:
        if self._client is None:
            return TxnResult(False, note="not connected")
        # pacing
        gap = INTER_TXN_S - (time.monotonic() - self._last_txn_t)
        if gap > 0:
            time.sleep(gap)
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
        except Exception as exc:                           # noqa: BLE001
            latency = (time.monotonic() - t0) * 1000.0
            note = f"EXC {type(exc).__name__}: {exc}"
        self._last_txn_t = time.monotonic()
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
        if self._sweep_running or self._check_running or self._ota_running:
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
    MONITOR_GROUPS = ((0, 12), (20, 2), (40, 2), (60, 1))
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
            for uid in ids:
                if self._scan_cancel.is_set():
                    break
                probe = None
                ok, dtype = False, -1
                try:
                    probe = make_scan_probe_client(settings)
                    if probe.connect():
                        rsp = probe.read_holding_registers(0, count=1, device_id=uid)
                        if rsp is not None and not rsp.isError():
                            ok, dtype = True, rsp.registers[0]
                except Exception:                          # noqa: BLE001
                    pass
                finally:
                    if probe is not None:
                        try:
                            probe.close()
                        except Exception:
                            pass
                if ok:
                    found.append(uid)
                    self._log.append("scan", 3, 0, uid, "probe", True, dtype,
                                     lgs_map.dec_device_type(dtype), 0.0)
                self._emit_scan(probed=uid, found=ok, device_type=dtype)
                time.sleep(0.02)                           # let the OS release the port
            self._emit_scan(probed=-1, found=False, done=True, found_ids=tuple(found))
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
        latency = (time.monotonic() - t0) * 1000.0
        self._last_txn_t = time.monotonic()
        if log:
            self._log.append(source, 16 if kind == "regs" else 5, addr, 0, "broadcast",
                             ok, len(payload) if kind == "regs" else 1,
                             "broadcast (no reply expected)", latency, note,
                             self._trace["tx"], "")
        return TxnResult(ok, None, latency, note)

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

        # factory reset sequences: arm 500 then apply 501/502
        if not coil(500):
            return DangerResult(False, tuple(steps), "arm coil 500 failed")
        time.sleep(0.2)
        apply_addr = 501 if action is DangerAction.FACTORY_RESET_KEEP_ID else 502
        coil(apply_addr, tolerate_timeout=True)
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
