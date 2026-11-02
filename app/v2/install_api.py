"""Installation check on the module page: backend.

The runs themselves are fieldcheck.run_check (breadth: does every selected
module answer, then light / display / unlock it) and fieldcheck.run_pick_sequence
(the dispensing flow as a rehearsal). Both are written against the small
FieldOps protocol, so this module only supplies the transport: one client on
the cabinet's gateway, held for the whole run, with the same hub handling the
classic worker applies to every transaction.

One run at a time for the whole server. While it holds the gateway, the page's
other calls to that gateway wait their turn (module_api._Bus) instead of
interleaving frames into the run.
"""
import threading
import time
from dataclasses import dataclass
from datetime import datetime

from .. import config_store, fieldcheck, lgs_map
from ..lgs_map import CoilClass
from . import gateway_api, module_api, sites

MODES = ("check", "pick")
ACTIONS = ("skip", "light", "light_display")
MAX_IDS = 80
RUN_WAIT_S = 30.0          # how long a run waits for the gateway to be free


@dataclass(frozen=True)
class _Res:
    ok: bool
    value: object = None
    note: str = ""


class _TcpOps:
    """fieldcheck.FieldOps over one held Modbus TCP client."""

    def __init__(self, client, host: str, port: int, cancel: threading.Event) -> None:
        self._c, self._host, self._port, self._cancel = client, host, port, cancel
        self._last_t = 0.0
        self._last_ch = None

    def _txn(self, device_id: int, call, extract) -> _Res:
        # Crossing to another hub channel loses the first frames, so the first
        # transaction after a cross gets several attempts (and a longer breath);
        # anywhere else one failure is a real failure.
        channel = lgs_map.hub_channel(device_id)
        crossed = self._last_ch is not None and channel != self._last_ch
        gap = (max(lgs_map.INTER_TXN_S, lgs_map.INTER_CH_S) if crossed else lgs_map.INTER_TXN_S) \
            - (time.monotonic() - self._last_t)
        if gap > 0:
            time.sleep(gap)
        self._last_ch = channel
        attempts = lgs_map.HUB_WAKE_TRIES if crossed else 1
        note = ""
        for attempt in range(1, attempts + 1):
            if self._cancel.is_set():
                raise fieldcheck.CheckCancelled()
            try:
                rsp = call(self._c)
                if rsp is None or rsp.isError():
                    note = f"ERR {rsp}"
                else:
                    self._last_t = time.monotonic()
                    return _Res(True, extract(rsp), "")
            except Exception as exc:                             # noqa: BLE001
                note = f"{type(exc).__name__}: {exc}"[:80]
            self._last_t = time.monotonic()
            if attempt < attempts:
                time.sleep(lgs_map.HUB_WAKE_GAP_S)
        return _Res(False, None, note)

    def read_reg(self, device_id: int, addr: int) -> _Res:
        return self._txn(device_id,
                         lambda c: c.read_holding_registers(addr, count=1, device_id=device_id),
                         lambda r: r.registers[0])

    def write_reg(self, device_id: int, addr: int, value: int) -> _Res:
        return self._txn(device_id,
                         lambda c: c.write_register(addr, int(value), device_id=device_id),
                         lambda r: int(value))

    def write_coil(self, device_id: int, addr: int, value: int) -> _Res:
        # The same gates module_api.coil applies: the check can never reach an
        # OTA or danger coil, and a latch is not pulsed inside its cooldown.
        cls = lgs_map.classify_coil(int(addr))
        if cls is CoilClass.FORBIDDEN:
            return _Res(False, None, "OTA coils are driven by the firmware-update tools only")
        if cls is CoilClass.DANGER:
            return _Res(False, None, "danger coil: not available here")
        key = (self._host, self._port, device_id)
        latch_on = cls is CoilClass.LATCH and bool(value)
        if latch_on:
            left = module_api.cooldown_left(self._host, self._port, device_id)
            if left > 0:
                return _Res(False, None, f"latch cooldown: {left:.1f} s remaining")
        res = self._txn(device_id,
                        lambda c: c.write_coil(int(addr), bool(value), device_id=device_id),
                        lambda r: int(bool(value)))
        if res.ok and latch_on:
            with module_api._cool_lock:
                module_api._cool[key] = time.monotonic() + lgs_map.LATCH_COOLDOWN_S
        return res

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._cancel.is_set():
                raise fieldcheck.CheckCancelled()
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


def _ids(raw) -> list:
    try:
        ids = sorted({int(x) for x in (raw or [])})
    except (TypeError, ValueError):
        raise ValueError("ids must be a list of module ids")
    if not ids:
        raise ValueError("select at least one module")
    if len(ids) > MAX_IDS:
        raise ValueError(f"at most {MAX_IDS} modules per run")
    for i in ids:
        if not lgs_map.valid_target_id(i):
            raise ValueError(f"invalid module id {i}")
    return ids


def _num(body: dict, key: str, lo: float, hi: float, default: float) -> float:
    try:
        v = float(body.get(key, default))
    except (TypeError, ValueError):
        raise ValueError(f"{key} must be a number")
    if not lo <= v <= hi:
        raise ValueError(f"{key} must be {lo:g}-{hi:g}")
    return v


def check_config(body: dict) -> fieldcheck.CheckConfig:
    action = str(body.get("action", "light"))
    if action not in ACTIONS:
        raise ValueError("action must be skip, light or light_display")
    return fieldcheck.CheckConfig(light=action != "skip", unlock=bool(body.get("unlock")),
                                  display=action == "light_display",
                                  identify=bool(body.get("identify")),
                                  hold_s=_num(body, "hold_s", 0.2, 5, 1.0))


def pick_config(body: dict) -> fieldcheck.PickConfig:
    return fieldcheck.PickConfig(preset=int(_num(body, "preset", 1, 8, 1)),
                                 display=bool(body.get("display", True)),
                                 unlock=bool(body.get("unlock", True)),
                                 require_locked=bool(body.get("require_locked", True)),
                                 timeout_s=_num(body, "timeout_s", 0, 600, 60),
                                 batch=int(_num(body, "batch", 0, 16, 4)),
                                 by_channel=bool(body.get("by_channel", True)))


def layout(site_id: str) -> dict:
    """The slots of the saved cabinet type, grouped by row, for the picker."""
    site = sites.find(str(site_id)) or {}
    lay = lgs_map.layout_by_key(site.get("cabinet", ""))
    rows: dict = {}
    for i in lay.ids:
        rows.setdefault(i // 10, []).append(i)
    return {"label": lay.label, "ids": list(lay.ids),
            "rows": [{"r": r, "ids": v} for r, v in sorted(rows.items())]}


def _event(ev) -> dict:
    if isinstance(ev, fieldcheck.DeviceStart):
        return {"t": "start", "id": ev.device_id, "index": ev.index, "total": ev.total}
    if isinstance(ev, fieldcheck.DeviceDone):
        r = ev.result
        return {"t": "done", "id": r.device_id, "ok": r.ok, "responded": r.responded,
                "type": r.type_name,
                "steps": [{"label": s.label, "ok": s.ok, "note": s.note} for s in r.steps]}
    if isinstance(ev, fieldcheck.PickLit):
        return {"t": "lit", "ids": list(ev.ids), "total": ev.total}
    if isinstance(ev, fieldcheck.PickPressed):
        return {"t": "pressed", "id": ev.device_id}
    if isinstance(ev, fieldcheck.CheckDone):
        rep = ev.report
        return {"t": "end", "cancelled": rep.cancelled, "passed": rep.passed,
                "answered": len(rep.responded), "total": len(rep.results),
                "missing": rep.missing, "failed": rep.failed}
    return {"t": "?"}


class Run:
    """The one check on the server: its events, its cancel flag, its CSV."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.mode = ""
        self.cabinet = ""
        self.events: list = []
        self.error = ""
        self.csv_name = ""
        self.csv_bytes = b""
        self._cancel = threading.Event()

    def _emit(self, ev) -> None:
        d = _event(ev)
        with self._lock:
            d["seq"] = len(self.events) + 1
            self.events.append(d)

    def start(self, site: dict, mode: str, ids: list, body: dict) -> dict:
        if mode not in MODES:
            raise ValueError("mode must be check or pick")
        cfg = check_config(body) if mode == "check" else pick_config(body)
        with self._lock:
            if self.running:
                raise ValueError("a check is already running")
            self.running = True
            self.mode, self.cabinet = mode, site["name"]
            self.events, self.error, self.csv_name, self.csv_bytes = [], "", "", b""
            self._cancel.clear()
        threading.Thread(target=self._work, args=(site, mode, cfg, ids), daemon=True,
                         name="v2-install-check").start()
        return {"ok": True}

    def _work(self, site: dict, mode: str, cfg, ids: list) -> None:
        host, port = site["host"], site["port"]
        report = None
        try:
            try:        # the channel each row hangs on decides how the pick batches are cut
                for k in gateway_api.read(host, port).get("keys", []):
                    if k["key"] == "bus.hub_map":
                        lgs_map.set_hub_map(lgs_map.parse_hub_map(k["value"]))
            except Exception:                                    # noqa: BLE001
                pass
            with module_api._Bus(host, port, wait=RUN_WAIT_S) as client:
                ops = _TcpOps(client, host, port, self._cancel)
                run = fieldcheck.run_check if mode == "check" else fieldcheck.run_pick_sequence
                report = run(ops, cfg, ids, self._emit, self._cancel)
        except Exception as exc:                                 # noqa: BLE001
            with self._lock:
                self.error = f"{type(exc).__name__}: {exc}"[:200]
        finally:
            if report is not None:
                try:
                    name = f"install_check_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
                    data = fieldcheck.check_csv_bytes(report)
                    d = config_store.data_dir() / "exports"
                    d.mkdir(exist_ok=True)
                    (d / name).write_bytes(data)
                    with self._lock:
                        self.csv_name, self.csv_bytes = name, data
                except OSError:
                    pass
            with self._lock:
                self.running = False

    def cancel(self) -> None:
        self._cancel.set()

    def snapshot(self, since: int) -> dict:
        with self._lock:
            return {"running": self.running, "mode": self.mode, "cabinet": self.cabinet,
                    "error": self.error, "csv": bool(self.csv_bytes),
                    "seq": len(self.events),
                    "events": [e for e in self.events if e["seq"] > since]}


run = Run()
