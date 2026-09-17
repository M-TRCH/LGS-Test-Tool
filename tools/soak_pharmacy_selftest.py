"""Check what pharmacy mode puts on the bus, without a bus.

    python tools/soak_pharmacy_selftest.py

Pharmacy mode is the first thing in this tool that WRITES during a soak. Every
other feature here reads: a bug costs a wrong number in a report, and the
report can be re-run. A bug in this one lights a cabinet nobody asked to be
lit, or leaves it lit overnight, and on a ward that is not a data-quality
problem. So the guarantees worth a test are mostly about restraint:

  [1] poll mode writes NOTHING. The proven overnight path must be unchanged
      by the existence of this mode -- not "mostly unchanged", zero writes.
  [2] every window that is lit is later cleared, and a cancelled run leaves
      the cabinet dark.
  [3] a slow write is reported. The picks jump around the cabinet, so nearly
      every one crosses a hub channel -- this is the heaviest crossing
      traffic the tool produces, and it went unmeasured in the first cut.
  [4] the poll and the picks share one idea of where the hub is parked. A
      pick MOVES the hub; a poll that kept its own count would score the
      next read as no-crossing and blame the module for the 2.2 s.
  [5] a long dwell does not quietly break the model -- pairs passed over
      because they were already lit stay in the deck (equal exposure is the
      whole reason the deck exists), and picks that cannot be placed are
      counted and reported rather than dropped in silence.
"""
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import soak                                              # noqa: E402
from app.lgs_map import hub_channel                               # noqa: E402


class Reply:
    def __init__(self, value, ok=True, note=""):
        self.ok = ok
        self.value = value
        self.latency_ms = 5.0
        self.note = note
        self.link_down = False


class StubBus:
    """A quiet, healthy cabinet that records every write.

    It spends a little REAL time per transaction, because the simulation is
    driven by the wall clock: dwell is floored at one second and the pick
    interval is derived from picks-per-day, so a stub that answered instantly
    would finish a whole run inside one millisecond and never reach a single
    pick. A few milliseconds a read is enough to make time pass.

    `slow_windows` names windows whose write should take a visible amount of
    time, so the timing path can be checked without waiting for a real hub.
    """

    def __init__(self, ids, slow_windows=(), slow_s=0.0, read_s=0.004):
        self.ids = list(ids)
        self.writes: list = []          # (device_id, coil, value)
        self.slow_windows = set(slow_windows)
        self.slow_s = slow_s
        self.read_s = read_s
        self.channel_seen: list = []    # channel of each bus touch, in order

    def read_regs(self, device_id: int, addr: int, count: int):
        time.sleep(self.read_s)
        self.channel_seen.append(hub_channel(device_id))
        if addr == 0:
            regs = [10, 30500, 510] + [0] * 21
            regs[soak.REG_BOOTS] = 100
            return Reply(regs[:count])
        if addr == soak.REG_STATS2_IWDG:
            return Reply(3)
        return Reply([0] * count)

    def write_coil(self, device_id: int, addr: int, value: bool):
        self.channel_seen.append(hub_channel(device_id))
        if (addr - 1000) in self.slow_windows and value:
            time.sleep(self.slow_s)
        self.writes.append((device_id, addr, bool(value)))
        return Reply(True)

    def sleep(self, seconds: float) -> None:
        pass


def drive(cfg_kw, ids=(11, 12, 21, 22), seconds=3.0, bus=None):
    """Run a soak for `seconds` of wall clock and hand back (bus, rows, report).

    Cancelling on elapsed time rather than pass count is what lets the
    simulation actually run: picks are due on a real-time interval and dwell
    expires on a real-time clock, so a run measured in passes could complete
    without either ever happening.
    """
    bus = bus or StubBus(ids)
    rows: list = []
    cancel = threading.Event()
    deadline = [0.0]

    def emit(event):
        if isinstance(event, soak.SoakTick) and time.monotonic() >= deadline[0]:
            cancel.set()

    def log(row: str) -> None:
        rows.append(row)
        if ",sim_start," in row:
            # The baseline sweep before this row is deliberately NOT counted
            # as crossings by the soak -- the run's own tracker starts here,
            # so the oracle has to start here too.
            bus.channel_seen.clear()
            deadline[0] = time.monotonic() + seconds

    cfg = soak.SoakConfig(ids=tuple(ids), pass_gap_s=0, counter_every=1,
                          **cfg_kw)
    deadline[0] = time.monotonic() + seconds
    report = soak.run_soak(bus, cfg, emit, cancel, log)
    return bus, rows, report


def kinds(rows, kind):
    return [r.split(",", 3)[3] for r in rows if f",{kind}," in r]


# ── [1] poll mode is untouched ─────────────────────────────────────────────
def case_poll_writes_nothing():
    bus, rows, report = drive({"mode": "poll"}, seconds=0.5)
    if bus.writes:
        return f"poll mode wrote {len(bus.writes)} coils -- must be zero"
    if report.tick.picks:
        return f"poll mode counted {report.tick.picks} picks"
    start = next((r for r in rows if ",start," in r), "")
    if "mode=poll" not in start:
        return "start row does not record the mode"
    return None


# ── [2] nothing is left lit ────────────────────────────────────────────────
def case_everything_cleared():
    # 4 picks/s against a 1 s dwell: plenty of lights and plenty of clears.
    bus, rows, report = drive({"mode": "pharmacy", "picks_per_day": 345600,
                               "dwell_s": 1.0, "windows": 8}, seconds=3.0)
    if not bus.writes:
        return "pharmacy mode wrote nothing at all"
    lit = set()
    for dev, coil, on in bus.writes:
        if on:
            lit.add((dev, coil))
        else:
            lit.discard((dev, coil))
    if lit:
        return f"{len(lit)} window(s) still lit when the run ended: {sorted(lit)[:4]}"
    if report.tick.picks < 1:
        return "picks were never counted"
    return None


# ── [3] a slow write is reported, and says it was a pick ───────────────────
def case_slow_write_reported():
    bus = StubBus((11, 12, 21, 22), slow_windows={3}, slow_s=0.25)
    bus, rows, report = drive({"mode": "pharmacy", "picks_per_day": 864000,
                               "dwell_s": 1.0, "windows": 8,
                               "slow_ms": 100, "crossing_slow_ms": 100},
                              seconds=3.0, bus=bus)
    slow = [d for d in kinds(rows, "slow") if "window 3" in d]
    if not slow:
        return "a 250 ms write was never reported as slow"
    if not any("pick" in d for d in slow):
        return f"slow row does not say it was a pick: {slow[0]}"
    if report.tick.txns <= report.tick.passes * len(bus.ids):
        return "writes were not counted as transactions"
    return None


# ── [4] poll and picks share one channel tracker ───────────────────────────
def case_shared_channel_tracker():
    """Crossings counted must equal crossings actually made on the wire.

    The stub records the channel of every touch in order, so the truth is
    computable. Before the tracker was shared, the poll's count drifted below
    it by roughly one per pick.
    """
    bus, rows, report = drive({"mode": "pharmacy", "picks_per_day": 345600,
                               "dwell_s": 1.0, "windows": 8}, seconds=3.0)
    # One counted transaction == one bus touch, in order, so the counted part
    # of the run is exactly the first `txns` touches. What comes after is the
    # all-off teardown, which runs once the totals are already final and is
    # deliberately not counted -- it is housekeeping, not measurement.
    counted = bus.channel_seen[:report.tick.txns]
    if len(counted) != report.tick.txns:
        return (f"{report.tick.txns} transactions counted but only "
                f"{len(bus.channel_seen)} touches reached the bus")
    actual, prev = 0, None
    for ch in counted:
        if ch != 0 and (prev is None or ch != prev):
            actual += 1
        prev = ch
    if report.tick.crossings != actual:
        return (f"counted {report.tick.crossings} crossings, the wire made "
                f"{actual} -- the poll and the picks disagree about the hub")
    return None


# ── [5] long dwell: deck intact, saturation reported ───────────────────────
def case_deck_survives_long_dwell():
    """Pairs skipped for being lit must stay in the cycle.

    Two modules, two windows: four pairs. Light three, then deal -- the deck
    must still be able to produce all four over the next cycle, not just the
    one that was dark.
    """
    ph = soak._Pharmacy([11, 12], 2, 86400, 3600.0, 0.0)   # 1 s interval
    now = 1.0                            # the first pick is due at t=1
    got = set()
    for _ in range(4):                   # four picks, dwell far beyond the run
        action = ph.step(now)
        if action is None:
            break
        dev, coil, on = action
        if on:
            got.add((dev, coil - 1000))
        now += 1.0
    if len(got) != 4:
        return f"only {len(got)} of 4 pairs were ever dealt: {sorted(got)}"
    # the fifth has nowhere to go
    if ph.step(now) is not None:
        return "dealt a fifth pick with every window already lit"
    if ph.skipped != 1:
        return f"saturation not counted (skipped={ph.skipped})"
    return None


def case_saturation_reported_once():
    # Two modules of two windows is four pairs; at 20 picks/s with an hour's
    # dwell the cabinet is full within a second and stays full.
    bus, rows, report = drive({"mode": "pharmacy", "picks_per_day": 1728000,
                               "dwell_s": 3600.0, "windows": 2},
                              ids=(11, 12), seconds=2.0)
    sat = kinds(rows, "sim_saturated")
    if not sat:
        return "a saturated cabinet never said so"
    if len(sat) != 1:
        return f"{len(sat)} saturation rows -- must be one, not one per pick"
    if report.tick.dropped < 1:
        return "dropped picks were not counted"
    if "dwell" not in sat[0] or "every window lit" not in sat[0]:
        return f"saturation row does not explain itself: {sat[0]}"
    return None


# ── [6] routine picks are not anomalies ────────────────────────────────────
def case_picks_are_not_anomalies():
    """The CSV keeps every pick; the anomaly stream keeps none of them.

    The on-screen box holds 400 lines. Two rows per pick would fill it in
    about two hours of a 2,000/day run, so an overnight soak would look
    clean for the worst possible reason -- its findings scrolled off.
    """
    bus, rows, report = drive({"mode": "pharmacy", "picks_per_day": 345600,
                               "dwell_s": 1.0, "windows": 8}, seconds=2.0)
    picks_in_csv = len(kinds(rows, "pick"))
    if picks_in_csv < 1:
        return "picks are not in the CSV -- the run cannot be replayed"
    noise = [a for a in report.anomalies if a.kind in ("pick", "clear")]
    if noise:
        return (f"{len(noise)} routine picks reached the anomaly stream "
                f"(of {picks_in_csv} in the file)")
    return None


# ── [7] the emitted tick carries EVERY field ───────────────────────────────
def case_tick_carries_every_field():
    """Whatever run_soak counts, the panel must receive.

    The tick used to be rebuilt field by field at the emit site, so adding a
    counter to SoakTick silently produced a column that read 0 forever while
    the run counted it correctly. This project has been bitten by that exact
    shape before -- a night of 308 watchdog resets reported wdt=0. The test
    is deliberately generic: it compares the whole dataclass rather than any
    named field, so the NEXT counter added is covered without anyone
    remembering to come back here.
    """
    import dataclasses
    last = {}

    class Grab(dict):
        pass

    bus = StubBus((11, 12, 21, 22))
    rows, cancel = [], __import__("threading").Event()
    deadline = [time.monotonic() + 3.0]

    def emit(ev):
        if isinstance(ev, soak.SoakTick):
            last["tick"] = ev
            if time.monotonic() >= deadline[0]:
                cancel.set()

    def log(row):
        rows.append(row)
        if ",sim_start," in row:
            deadline[0] = time.monotonic() + 3.0

    cfg = soak.SoakConfig(ids=(11, 12, 21, 22), pass_gap_s=0, counter_every=1,
                          mode="pharmacy", picks_per_day=345600, dwell_s=1.0,
                          windows=8)
    report = soak.run_soak(bus, cfg, emit, cancel, log)
    got = last.get("tick")
    if got is None:
        return "no tick was ever emitted"
    internal = dataclasses.asdict(report.tick)
    emitted = dataclasses.asdict(got)
    # `seq` is stamped by the event queue, and elapsed_s advances after the
    # last tick; everything else must have arrived.
    stale = [k for k, v in internal.items()
             if k not in ("seq", "elapsed_s") and emitted.get(k) != v]
    if stale:
        return (f"the panel never received: {stale} "
                f"(internal {[internal[k] for k in stale]}, "
                f"emitted {[emitted.get(k) for k in stale]})")
    if internal["picks"] < 1:
        return "the run lit nothing, so the comparison proved nothing"
    if internal["lit"] < 1 and internal["picks"] > 3:
        return "lit stayed 0 through a run that lit windows"
    return None


# ── [8] the configured rate is actually delivered ──────────────────────────
def case_rate_does_not_drift():
    """Over many intervals the pick rate must not sag.

    A step only happens between module reads and a clear outranks a pick in
    the same step, so picks go out a little late. Rescheduling from the LATE
    moment rather than the DUE moment makes each delay permanent, and the
    losses compound: on the type-80 it produced 1,726 picks/day against
    2,000 configured, with the median gap looking perfectly healthy at 44.0 s.
    A median cannot show this; only the count over a long run can.

    Driven here on a synthetic clock, so it is exact and instant.
    """
    interval = 10.0                       # 8640/day
    # dwell 100 s over 160 pairs holds ~10 lit: far from saturation, and the
    # clears it produces are the point -- a clear outranks a pick in the same
    # step, and that is precisely what makes picks late.
    ph = soak._Pharmacy(range(11, 31), 8, 8640, 100.0, 0.0)
    now, fired = 0.0, 0
    while now < 10000.0:
        now += 0.7                        # a step between module reads
        act = ph.step(now)
        if act is not None and act[2]:    # count picks, not clears
            fired += 1
    expected = 10000.0 / interval
    ratio = fired / expected
    if ratio < 0.97:
        return (f"delivered {fired} picks where {expected:.0f} were due "
                f"({ratio * 100:.0f}%) -- the schedule is drifting")
    if ratio > 1.03:
        return f"delivered {fired} for {expected:.0f} due -- firing too fast"
    return None


def case_far_behind_resyncs_without_bursting():
    """After a long stall it must not fire a catch-up burst.

    Compensating for lost time is right for a few seconds and wrong for a
    few minutes: a cabinet does not owe anyone forty picks because the bus
    was busy. One catch-up at most, then resync.
    """
    ph = soak._Pharmacy(range(11, 31), 8, 8640, 100.0, 0.0)  # 10 s interval
    ph.step(10.0)                          # first pick, on time
    burst = 0
    now = 600.0                            # ten minutes later
    for _ in range(30):                    # hammer step() at the same instant
        act = ph.step(now)
        if act is not None and act[2]:     # picks only; the clears are due
            burst += 1
    if burst > 2:
        return f"fired {burst} picks at one instant catching up -- that is a burst"
    if burst == 0:
        return "fired nothing at all after the stall"
    return None


# ── the arithmetic the UI shows ────────────────────────────────────────────
def case_estimate_matches_reality():
    ids = list(range(11, 19))            # 8 modules
    conc, cap = soak.estimate_concurrent(ids, 8, 2000, 20.0)
    if cap != 64:
        return f"capacity {cap}, expected 64"
    if abs(conc - (2000 / 86400 * 20)) > 1e-9:
        return f"concurrent {conc}, expected picks/86400 x dwell"
    if conc > 1.0:
        return "the documented default should be well under one light at a time"
    # and the figure the docs quote
    if abs(conc - 0.463) > 0.001:
        return f"the 0.46 figure in the docs is now {conc:.3f}"
    return None


CASES = (
    ("poll writes nothing", case_poll_writes_nothing),
    ("everything cleared", case_everything_cleared),
    ("slow write reported", case_slow_write_reported),
    ("shared channel tracker", case_shared_channel_tracker),
    ("deck survives long dwell", case_deck_survives_long_dwell),
    ("saturation reported once", case_saturation_reported_once),
    ("picks are not anomalies", case_picks_are_not_anomalies),
    ("tick carries every field", case_tick_carries_every_field),
    ("rate does not drift", case_rate_does_not_drift),
    ("far behind resyncs", case_far_behind_resyncs_without_bursting),
    ("estimate matches reality", case_estimate_matches_reality),
)


def main() -> int:
    failures = 0
    for name, fn in CASES:
        try:
            problem = fn()
        except Exception as exc:                                  # noqa: BLE001
            problem = f"{type(exc).__name__}: {exc}"
        print(f"{name:26} {'FAIL' if problem else 'ok'}")
        if problem:
            print(f"                           - {problem}")
            failures += 1
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
