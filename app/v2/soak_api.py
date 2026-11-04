"""Soak page backend: start / stop / watch a fleet soak, and read past runs.

The run itself is the worker's fleet soak (ModbusWorker.start_fleet): it lives
in the server, outlives any browser, holds the keep-awake block, enforces its
own deadline and writes the verdict to data/exports. This module is only the
window onto it. Live numbers come from the worker's event list, folded into
the same CabinetTally the verdict uses, so the screen and the file cannot
disagree about what a cabinet did.
"""
import re
import threading
from collections import deque
from datetime import datetime

from .. import config_store, lgs_map, soak, soak_fleet

STAMP = r"\d{8}-\d{6}"
FLEET_RE = re.compile(rf"^fleet-({STAMP})\.txt$")
CSV_RE = re.compile(rf"^soak-([A-Za-z0-9._-]+)-({STAMP})\.csv$")
MODES = ("poll", "pharmacy")


def exports_dir():
    d = config_store.data_dir() / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


class Live:
    """Folds the worker's fleet events into per-cabinet tallies. One instance
    for the server; `pump()` is cheap and idempotent (it only reads events
    newer than the last it saw)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self.since = 0
        self.tallies: dict = {}
        self.paths: dict = {}
        self.anomalies: deque = deque(maxlen=60)
        self.finished: dict | None = None

    def pump(self, worker) -> None:
        with self._lock:
            self.since, events = worker.drain_fleet_events(self.since)
            for ev in events:
                self._fold(ev)

    def _tally(self, name: str, modules: int = 0):
        t = self.tallies.get(name)
        if t is None:
            t = self.tallies[name] = soak_fleet.CabinetTally(name=name, modules=modules)
        return t

    def _fold(self, ev) -> None:
        if isinstance(ev, soak_fleet.FleetStarted):
            self._tally(ev.cabinet, ev.modules)
            self.paths[ev.cabinet] = ev.path
        elif isinstance(ev, soak_fleet.FleetFailed):
            self._tally(ev.cabinet).note = ev.reason
        elif isinstance(ev, soak_fleet.FleetBusy):
            self._tally(ev.cabinet).note = f"refused, another master: {ev.peers}"
        elif isinstance(ev, soak_fleet.FleetEvent):
            t = self._tally(ev.cabinet)
            t.absorb(ev.inner)
            if isinstance(ev.inner, soak.SoakAnomaly):
                a = ev.inner.item
                self.anomalies.appendleft({"at": f"{a.when:%H:%M:%S}", "cabinet": ev.cabinet,
                                           "id": a.device_id, "kind": a.kind, "detail": a.detail})
        elif isinstance(ev, soak_fleet.FleetFinished):
            self.finished = {"text": ev.text, "path": ev.path, "clock": ev.clock}

    def snapshot(self, worker) -> dict:
        self.pump(worker)
        cabs = []
        with self._lock:
            for name, t in self.tallies.items():
                state = ("did not run" if not t.ran and t.note
                         else "starting" if not t.ran
                         else "not clean" if not t.clean
                         else "warn" if t.gw_warn else "clean")
                cabs.append({"name": name, "modules": t.modules, "passes": t.passes, "reads": t.reads,
                             "fails": t.fails, "reboots": t.reboots, "watchdogs": t.watchdogs,
                             "crossings": t.crossings, "worst_ms": round(t.worst_ms),
                             "silent": sorted(t.silent), "elapsed_s": round(t.elapsed_s),
                             "gw_seen": t.gw_seen, "gw_healed": t.gw_healed,
                             "gw_heal_failed": t.gw_heal_failed, "gw_timeouts": t.gw_timeouts,
                             "gw_bad_crc": t.gw_bad_crc, "heal_per_h": round(t.heal_per_h, 1),
                             "writes": t.writes, "write_fails": t.write_fails, "picks": t.picks, "dropped": t.dropped, "lit": t.lit,
                             "state": state, "note": t.note, "csv": self.paths.get(name, "")})
            anomalies = list(self.anomalies)
            finished = self.finished
        drops = 0
        try:
            drops = soak_fleet.framer_watch.snapshot().total
        except Exception:                                        # noqa: BLE001
            pass
        return {"running": worker.fleet_running(), "starts_in_s": worker.fleet_starts_in_s(),
                "left_s": worker.fleet_left_s(), "count": worker.fleet_count(),
                "cabinets": cabs, "anomalies": anomalies, "finished": finished,
                "frames_discarded": drops}


live = Live()


def estimate(sites_list: list, picks: int, dwell_s: float, windows: int) -> dict:
    """What a pharmacy run would look like before it is started, by the same two functions the classic page uses:
    windows lit at once (picks/day / 86400 x dwell) against the capacity of the SMALLEST chosen cabinet (modules x
    windows), and the share of every day the bus spends on picks alone."""
    caps = []
    for s in sites_list:
        if s.get("cabinet"):
            ids = lgs_map.layout_by_key(s["cabinet"]).ids
            caps.append(soak.estimate_concurrent(ids, windows, picks, dwell_s))
    conc, cap = min(caps, key=lambda c: c[1]) if caps else (soak.estimate_concurrent([0], windows, picks, dwell_s))
    return {"concurrent": conc, "capacity": cap, "duty": soak.pick_bus_duty(picks)}


def start(worker, sites_list: list, opts: dict) -> dict:
    """Validate and start. Raises ValueError with a message the page shows."""
    mode = str(opts.get("mode", "poll"))
    if mode not in MODES:
        raise ValueError("mode must be poll or pharmacy")
    hours = float(opts.get("hours") or 0)
    if not 0 <= hours <= 336:
        raise ValueError("hours must be 0-336 (0 = until stopped)")
    gap = float(opts.get("gap_s") or 2.0)
    if not 0.1 <= gap <= 30:
        raise ValueError("pass gap must be 0.1-30 s")
    start_epoch, bad = soak_fleet.parse_start_at(str(opts.get("start_at") or ""))
    if bad:
        raise ValueError(bad)
    picks = int(opts.get("picks") or 2000)
    if mode == "pharmacy" and not 1 <= picks <= 200000:
        raise ValueError("picks per day must be 1-200000")
    cabs = []
    for s in sites_list:
        if not s.get("cabinet"):
            raise ValueError(f"'{s['name']}': set its cabinet type on the Sites page first")
        layout = lgs_map.layout_by_key(s["cabinet"])
        cabs.append(soak_fleet.FleetCabinet(name=s["name"], host=s["host"],
                                            ids=tuple(layout.ids), port=int(s["port"])))
    if not cabs:
        raise ValueError("choose at least one cabinet")
    dupes = soak_fleet.duplicate_hosts(cabs)
    if dupes:
        raise ValueError("two rows on one gateway: " + ", ".join(dupes))
    every = int(opts.get("counter_every") or 5)
    if not 1 <= every <= 100:
        raise ValueError("counter read must be every 1-100 passes")
    slow = int(opts.get("slow_ms") or 400)
    if not 50 <= slow <= 5000:
        raise ValueError("slow threshold must be 50-5000 ms")
    tmo = float(opts.get("timeout_s") or 0)
    if tmo and not 4 <= tmo <= 30:
        raise ValueError("client timeout must be 4-30 s")
    cfg = soak.SoakConfig(ids=cabs[0].ids, pass_gap_s=gap, counter_every=every, slow_ms=slow, timeout_s=tmo,
                          mode=mode, picks_per_day=picks,
                          dwell_s=float(opts.get("dwell_s") or 20.0),
                          windows=int(opts.get("windows") or 8))
    live.reset()
    if not worker.start_fleet(cabs, cfg, exports_dir(), hours=hours, start_at_epoch=start_epoch):
        raise ValueError("a fleet run is already going, or this tool is connected to one of these gateways")
    warns = []
    if 0.4 <= gap <= 0.9:
        warns.append("a pass gap of 0.4-0.9 s makes the hub lose first reads and creates false 'slow module' findings")
    if tmo and tmo < 6:
        warns.append("a client timeout under 6 s can leave the bus out of step behind a hub")
    if hours == 0:
        warns.append("no end time: it runs until stopped")
    return {"ok": True, "count": len(cabs), "armed": bool(start_epoch), "warnings": warns}


def runs(limit: int = 60) -> list:
    """Past runs, newest first: the verdict file and the per-cabinet CSVs that
    share its stamp."""
    d = exports_dir()
    by: dict = {}
    for f in d.iterdir():
        m = FLEET_RE.match(f.name)
        if m:
            by.setdefault(m.group(1), {"stamp": m.group(1), "verdict": f.name, "csv": []})
            continue
        m = CSV_RE.match(f.name)
        if m:
            # A fleet's CSVs are stamped by the run's second; the verdict file
            # carries the same stamp (soak_fleet uses one stamp for both).
            by.setdefault(m.group(2), {"stamp": m.group(2), "verdict": "", "csv": []})["csv"].append(f.name)
    out = []
    for stamp in sorted(by, reverse=True)[:limit]:
        r = by[stamp]
        try:
            r["started"] = datetime.strptime(stamp, "%Y%m%d-%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            r["started"] = stamp
        r["csv"].sort()
        out.append(r)
    return out


def read_file(name: str) -> tuple:
    """-> (path, kind). Only names this module itself produces, never a path."""
    if "/" in name or "\\" in name or not (FLEET_RE.match(name) or CSV_RE.match(name)):
        raise ValueError("not a soak file")
    p = exports_dir() / name
    if not p.is_file():
        raise ValueError("no such file")
    return p, ("verdict" if FLEET_RE.match(name) else "csv")
