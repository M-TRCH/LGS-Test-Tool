"""Long module jobs for the v2 pages: installation check, pick walkthrough,
bus scan and the site report.

Each job is one of the classic tool's transport-independent runners
(fieldcheck, fw_survey, testsuite) handed a small ops object over one Modbus
TCP client on the cabinet's gateway, held for the whole job, with the same hub
handling the classic worker applies to every transaction. The classic pages
drive the very same runners through the worker, so the two cannot disagree
about what a check does.

One job at a time for the whole server. While it holds the gateway, the page's
other calls to that gateway wait their turn (module_api._Bus) instead of
interleaving frames into it.
"""
import threading
import time
from dataclasses import dataclass
from datetime import datetime

from .. import config_store, fieldcheck, fw_survey, lgs_map, testsuite
from ..lgs_map import CoilClass
from ..transports import PROBE_TIMEOUT_S
from ..version import APP_VERSION
from . import gateway_api, module_api, sites

MODES = ("check", "pick")
ACTIONS = ("skip", "light", "light_display")
MAX_IDS = 80
RUN_WAIT_S = 30.0          # how long a job waits for the gateway to be free


@dataclass(frozen=True)
class _Res:
    ok: bool
    value: object = None
    note: str = ""
    latency_ms: float = 0.0


class _TcpOps:
    """The ops every runner asks for, over one held Modbus TCP client:
    fieldcheck.FieldOps, fw_survey.SurveyOps, and (through _OneModule)
    testsuite.ModbusOps."""

    def __init__(self, client, host: str, port: int, cancel: threading.Event, cancel_exc=None) -> None:
        self._c, self._host, self._port, self._cancel = client, host, port, cancel
        self._exc = cancel_exc
        self._last_t = 0.0
        self._last_ch = None

    def _txn(self, device_id: int, call, extract, wake: bool = True) -> _Res:
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
        attempts = lgs_map.HUB_WAKE_TRIES if (crossed and wake) else 1
        note = ""
        for attempt in range(1, attempts + 1):
            if self._cancel.is_set() and self._exc is not None:
                raise self._exc()
            t0 = time.monotonic()
            try:
                rsp = call(self._c)
                if rsp is None or rsp.isError():
                    note = f"ERR {rsp}"
                else:
                    self._last_t = time.monotonic()
                    return _Res(True, extract(rsp), "", (self._last_t - t0) * 1000.0)
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

    def read_regs(self, device_id: int, addr: int, count: int) -> _Res:
        return self._txn(device_id,
                         lambda c: c.read_holding_registers(addr, count=count, device_id=device_id),
                         lambda r: r.registers[0] if count == 1 else list(r.registers))

    def read_coil(self, device_id: int, addr: int) -> _Res:
        return self._txn(device_id,
                         lambda c: c.read_coils(addr, count=1, device_id=device_id),
                         lambda r: 1 if r.bits[0] else 0)

    def write_reg(self, device_id: int, addr: int, value: int) -> _Res:
        return self._txn(device_id,
                         lambda c: c.write_register(addr, int(value), device_id=device_id),
                         lambda r: int(value))

    def write_coil(self, device_id: int, addr: int, value: int) -> _Res:
        # The same gates module_api.coil applies: a job can never reach an OTA
        # or danger coil, and a latch is not pulsed inside its cooldown.
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

    def probe(self, device_id: int) -> _Res:
        """A scan probe: one short try, no hub-wake retries (an absent id
        would otherwise cost six timeouts)."""
        return self._txn(device_id,
                         lambda c: c.read_holding_registers(0, count=1, device_id=device_id),
                         lambda r: r.registers[0], wake=False)

    def sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            if self._cancel.is_set():
                if self._exc is not None:
                    raise self._exc()
                return
            time.sleep(min(0.05, max(0.0, end - time.monotonic())))


class _OneModule:
    """testsuite.ModbusOps: _TcpOps with the device id fixed."""

    def __init__(self, ops: _TcpOps, device_id: int) -> None:
        self._o, self._id = ops, device_id

    def read_reg(self, addr):
        return self._o.read_reg(self._id, addr)

    def read_coil(self, addr):
        return self._o.read_coil(self._id, addr)

    def write_reg(self, addr, value):
        return self._o.write_reg(self._id, addr, value)

    def write_coil(self, addr, value):
        return self._o.write_coil(self._id, addr, value)

    def sleep(self, seconds):
        self._o.sleep(seconds)


# ── validation ────────────────────────────────────────────────────────────
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
                                 by_channel=bool(body.get("by_channel", True)),
                                 shuffle=bool(body.get("shuffle")),
                                 drawer_only=bool(body.get("drawer_only")))


def layout(site_id: str) -> dict:
    """The slots of the saved cabinet type, grouped by row, for the picker."""
    site = sites.find(str(site_id)) or {}
    lay = lgs_map.layout_by_key(site.get("cabinet", ""))
    rows: dict = {}
    for i in lay.ids:
        rows.setdefault(i // 10, []).append(i)
    return {"label": lay.label, "ids": list(lay.ids),
            "rows": [{"r": r, "ids": v} for r, v in sorted(rows.items())]}


def scan_ids(site_id: str, full: bool) -> list:
    """Quick: the cabinet's slots plus the factory and SET_ID addresses, where
    an unconfigured or half-configured module answers. Full: every id."""
    extra = [lgs_map.FACTORY_DEFAULT_ID, lgs_map.SETID_TEMP_ID]
    if full:
        return list(range(1, 246)) + extra
    return list(layout(site_id)["ids"]) + extra


# ── events (JSON for the page) ────────────────────────────────────────────
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
    if isinstance(ev, fw_survey.SurveyProgress):
        return {"t": "start", "id": ev.device_id, "index": ev.index, "total": ev.total}
    if isinstance(ev, fw_survey.ReportSurveyDone):
        return {"t": "end", "cancelled": ev.cancelled, "total": len(ev.records),
                "answered": sum(1 for r in ev.records if r.responded)}
    if isinstance(ev, testsuite.PhaseStart):
        return {"t": "phase", "name": ev.name, "index": ev.index, "total": ev.total}
    if isinstance(ev, testsuite.Step):
        s = ev.step
        return {"t": "step", "phase": s.phase, "name": s.name, "addr": s.addr, "op": s.op,
                "result": s.result, "decoded": str(s.decoded), "expected": str(s.expected), "note": s.note}
    if isinstance(ev, testsuite.PhaseEnd):
        return {"t": "phaseend", "name": ev.name, "ok": ev.stats.ok, "fail": ev.stats.fail, "err": ev.stats.err}
    if isinstance(ev, testsuite.Done):
        rep, tot = ev.report, ev.report.totals
        return {"t": "end", "cancelled": rep.cancelled, "passed": rep.passed,
                "ok": tot.ok, "fail": tot.fail, "err": tot.err}
    if isinstance(ev, dict):
        return ev
    return {"t": "?"}


def soak_choices(name: str) -> list:
    """This cabinet's soak CSVs in the exports folder, newest first, for the report's "which run?" list. A fleet run
    writes soak-<cabinet>-<stamp>.csv per cabinet; other cabinets' files and the combined "-all" exports never match. The
    files are only listed here (name, when, size); one is read when the report is built."""
    from .. import soak_fleet
    from . import soak_api
    stem = soak_fleet.safe_stem(name)
    out = []
    try:
        files = [f for f in soak_api.exports_dir().glob(f"soak-{stem}-*.csv") if "-all" not in f.name]
        for f in sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)[:30]:
            st = f.stat()
            out.append({"name": f.name, "when": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                        "kb": max(1, st.st_size // 1024)})
    except OSError:
        pass
    return out


def _parse_soak(text: str, label: str):
    from .. import soak_csv
    try:
        return soak_csv.parse_soak_csv(text, label)
    except soak_csv.SoakCsvError as exc:
        raise ValueError(f"that is not a usable soak CSV: {exc}")


class Run:
    """The one long job on the server: its events, its cancel flag, its file."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.kind = ""
        self.mode = ""
        self.cabinet = ""
        self.events: list = []
        self.error = ""
        self.file_name = ""
        self.file_bytes = b""
        self.file_type = ""
        self.pending = None            # a report whose modules have been read and whose PDF is not built yet
        self._cancel = threading.Event()

    def _emit(self, ev) -> None:
        d = _event(ev)
        with self._lock:
            d["seq"] = len(self.events) + 1
            self.events.append(d)

    def _begin(self, site: dict, kind: str, mode: str) -> None:
        with self._lock:
            if self.running:
                raise ValueError("another check is already running on this tool")
            self.running = True
            self.kind, self.mode, self.cabinet = kind, mode, site["name"]
            self.events, self.error = [], ""
            self.file_name, self.file_bytes, self.file_type = "", b"", ""
            self.pending = None
            self._cancel.clear()

    def _launch(self, site: dict, work, pre=None, timeout_s: float = 0.0) -> None:
        threading.Thread(target=self._work, args=(site, work, pre, timeout_s), daemon=True,
                         name="v2-module-job").start()

    def _work(self, site: dict, work, pre, timeout_s: float) -> None:
        host, port = site["host"], site["port"]
        try:
            ctx = None
            try:        # the channel each row hangs on decides batching and wake retries
                snap = gateway_api.read(host, port)
                for k in snap.get("keys", []):
                    if k["key"] == "bus.hub_map":
                        lgs_map.set_hub_map(lgs_map.parse_hub_map(k["value"]))
            except Exception:                                    # noqa: BLE001
                snap = None
            if pre is not None:
                ctx = pre(snap)
            with module_api._Bus(host, port, wait=RUN_WAIT_S, timeout_s=timeout_s or None) as client:
                out = work(client, ctx)
            if out:
                name, data, ctype = out
                try:
                    d = config_store.data_dir() / "exports"
                    d.mkdir(exist_ok=True)
                    (d / name).write_bytes(data)
                except OSError:
                    pass
                with self._lock:
                    self.file_name, self.file_bytes, self.file_type = name, data, ctype
        except Exception as exc:                                 # noqa: BLE001
            with self._lock:
                self.error = f"{type(exc).__name__}: {exc}"[:200]
        finally:
            with self._lock:
                self.running = False

    @staticmethod
    def _stamp() -> str:
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # ── the jobs ───────────────────────────────────────────────────────────
    def start(self, site: dict, mode: str, ids: list, body: dict) -> dict:
        """Installation check (mode check) or pick walkthrough (mode pick)."""
        if mode not in MODES:
            raise ValueError("mode must be check or pick")
        cfg = check_config(body) if mode == "check" else pick_config(body)
        self._begin(site, "check", mode)
        host, port = site["host"], site["port"]

        def work(client, _ctx):
            ops = _TcpOps(client, host, port, self._cancel, fieldcheck.CheckCancelled)
            run = fieldcheck.run_check if mode == "check" else fieldcheck.run_pick_sequence
            report = run(ops, cfg, ids, self._emit, self._cancel)
            return (f"install_check_{self._stamp()}.csv", fieldcheck.check_csv_bytes(report), "text/csv")

        self._launch(site, work)
        return {"ok": True}

    def start_scan(self, site: dict, ids: list) -> dict:
        self._begin(site, "scan", "")
        host, port = site["host"], site["port"]

        def work(client, _ctx):
            ops = _TcpOps(client, host, port, self._cancel)
            found = []
            for n, uid in enumerate(ids, 1):
                if self._cancel.is_set():
                    break
                r = ops.probe(uid)
                if r.ok:
                    found.append({"id": uid, "type": lgs_map.dec_device_type(r.value)})
                self._emit({"t": "probe", "id": uid, "found": r.ok, "index": n, "total": len(ids),
                            "type": lgs_map.dec_device_type(r.value) if r.ok else ""})
            self._emit({"t": "end", "cancelled": self._cancel.is_set(), "found": found, "total": len(ids)})
            return None

        self._launch(site, work, timeout_s=PROBE_TIMEOUT_S)
        return {"ok": True}

    def start_report(self, site: dict, site_id: str) -> dict:
        """The site report: gateway snapshot + newest events, then a read-only
        sweep of every slot, rendered to the same PDF the classic tool makes."""
        self._begin(site, "report", "")
        host, port = site["host"], site["port"]
        lay = lgs_map.layout_by_key((sites.find(site_id) or {}).get("cabinet", ""))

        def pre(snap):
            if not snap or not snap.get("ok"):
                raise ConnectionError("cannot read the gateway's settings")
            events = []
            try:
                with gateway_api._Session(host, port) as link:
                    res = link.log(30)
                    for row in (res.rows if res.ok else ()):
                        aux, par = row.get("a", "0"), row.get("p", "0")
                        detail = f"  a={aux} p={par}" if (aux != "0" or par != "0") else ""
                        events.append(f"#{row.get('i', '?')}  {row.get('t', '-')}  up={row.get('up', '?')}s"
                                      f"  {row.get('ev', '?')}{detail}")
            except Exception:                                    # noqa: BLE001
                events = []                 # older firmware: the report simply has no events section
            return {"snap": snap, "events": tuple(events)}

        def work(client, ctx):
            ops = _TcpOps(client, host, port, self._cancel)
            records = fw_survey.run_report_survey(ops, list(lay.ids), self._emit, self._cancel)
            if self._cancel.is_set():
                return None
            snap = ctx["snap"]
            with self._lock:
                self.pending = {"records": records, "snap": snap, "events": ctx["events"], "lay": lay,
                                "settings": {k["key"]: k["value"] for k in snap["keys"]}, "cabinet": site.get("name", "")}
            self._emit({"t": "ready"})
            return None

        self._launch(site, work, pre=pre)
        return {"ok": True}

    def cancel(self) -> None:
        self._cancel.set()

    def pending_soaks(self) -> list:
        with self._lock:
            pend = self.pending
        return soak_choices(pend["cabinet"]) if pend else []

    def build_report(self, soak_name: str = "", soak_text: str = "", soak_label: str = "") -> dict:
        """Step two of the site report: the modules are already read; render the PDF, with the soak run the operator
        picked from the exports folder (`soak_name`) or uploaded (`soak_text`), or without one."""
        from .. import report_pdf
        with self._lock:
            pend, busy = self.pending, self.running
        if busy or not pend:
            raise ValueError("read the modules first")
        soak, soak_file = None, ""
        if soak_text:
            soak, soak_file = _parse_soak(soak_text, soak_label or "uploaded.csv"), soak_label or "uploaded.csv"
        elif soak_name:
            if "/" in soak_name or "\\" in soak_name or not soak_name.startswith("soak-") or not soak_name.endswith(".csv"):
                raise ValueError("choose a soak file from the list")
            from . import soak_api
            path = soak_api.exports_dir() / soak_name
            try:
                soak, soak_file = _parse_soak(path.read_text(encoding="utf-8-sig"), soak_name), soak_name
            except OSError:
                raise ValueError("that soak file is no longer there")
        snap, settings, lay = pend["snap"], pend["settings"], pend["lay"]
        pdf = report_pdf.build_report_pdf(
            app_version=APP_VERSION, generated=datetime.now(), info=snap["info"], settings=settings,
            cabinet_label=lay.label, cabinet_count=lay.count, widths=lgs_map.layout_widths(lay),
            records=pend["records"], hub_channel=lgs_map.hub_channel, events=pend["events"], soak=soak, soak_file=soak_file)
        name = settings.get("sys.name", "") or snap["info"].get("id", "gw")
        fname = f"lgs-report-{name}-{datetime.now():%Y%m%d-%H%M}.pdf"
        data = bytes(pdf)
        try:
            d = config_store.data_dir() / "exports"
            d.mkdir(exist_ok=True)
            (d / fname).write_bytes(data)
        except OSError:
            pass
        with self._lock:
            self.file_name, self.file_bytes, self.file_type = fname, data, "application/pdf"
        return {"ok": True, "file": fname, "soak": soak.headline() if soak else ""}

    def snapshot(self, since: int) -> dict:
        with self._lock:
            return {"running": self.running, "kind": self.kind, "mode": self.mode, "cabinet": self.cabinet,
                    "error": self.error, "csv": bool(self.file_bytes), "file": self.file_name,
                    "seq": len(self.events),
                    "events": [e for e in self.events if e["seq"] > since]}


run = Run()
