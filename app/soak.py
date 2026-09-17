"""Bus soak: poll the whole cabinet for hours and prove nothing wobbles.

A cabinet that answers every read still is not healthy — the modules can be
rebooting between them. That is exactly what happened on 2026-08-13: every
hub channel change wedged the modules on that channel until their watchdog
reset them, a second later they answered again, and the master never saw a
single failed transaction. What gave it away was the BOOT COUNTER moving.

So this watches three things at once:

  * transactions that fail or answer slowly (the obvious layer),
  * the boot counter of every module (a reboot nobody asked for), and
  * the watchdog counter, when the firmware publishes one (fw >= v3.3.0),
    which says the reboot came from a hang rather than from the power.

It is deliberately gentle — one register read per module per pass — so it
can be left running for days beside real traffic. Every pass crosses the
RS485 hub's channels the same way a hospital server polling the cabinet
does, which is the condition the fault needed.

Anomalies stream to the UI as they happen AND to a CSV, because the whole
point of an overnight run is that nobody is watching it.

The CSV also carries `start`, `heartbeat` (one per pass) and `stop` rows on
device 0. They are not anomalies; they are the answer to "when did this
stop, and was it finished?". The first overnight run ended at 00:17 when
Windows put the machine to sleep, and a file of nothing but anomalies could
not tell that from a cabinet that had simply behaved itself until morning.
"""
from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Callable, Optional, Protocol, Sequence

from .fw_survey import FW_MIN_STATS
from .lgs_map import INTER_TXN_S, decode_reset_cause, hub_channel

REG_IDENTITY = 0        # type, fw, hw — the cheap "are you there" read
REG_BOOTS = 7
REG_RESET_CAUSE = 8     # bit0 IWDG, 1 SW, 2 power-on, 3 NRST, 4 WWDG, 5 LP, 6 OBL
REG_STATS2_IWDG = 410   # fw >= v3.3.0


class SoakOps(Protocol):
    def read_regs(self, device_id: int, addr: int, count: int): ...
    def sleep(self, seconds: float) -> None: ...
    # Only the pharmacy simulation writes. A plain poll soak never calls it,
    # so an ops binder that predates the mode still satisfies this.
    def write_coil(self, device_id: int, addr: int, value: bool): ...


@dataclass
class SoakConfig:
    ids: tuple = ()
    # Breather between cabinet passes. NOT a free parameter: measured on the
    # 64-module cabinet 2026-08-31, a pause in the 0.5-0.75 s band makes the
    # first two reads of the next channel lose their first attempt (~3.6 s
    # each), while 0-0.3 s and >=1.0 s are clean. The hub falls back to its
    # home channel after about a second of silence, and a pause inside that
    # band catches it mid-transition while the gateway still believes it is
    # elsewhere. The old default was 0.5 -- dead centre of the bad band --
    # which is why every soak for weeks reported modules 12/13 as "slow on
    # 80% of passes": the tool was manufacturing the fault it was measuring.
    # 2.0 s is clear of the band with margin, and passes are actually FASTER
    # (24.4 s vs 30.9 s) because the re-entry crossing costs 94 ms, not 2.3 s.
    pass_gap_s: float = 2.0
    counter_every: int = 5       # re-read boot/watchdog counters every N passes
    slow_ms: int = 400           # a reply this slow is worth a line
    # The first read after a hub channel change is SUPPOSED to be slow: the
    # gateway holds it until the channel stops being deaf (~2.2 s). Logging
    # that as an anomaly would bury the real ones — so crossings are counted
    # separately and only complained about past their own, larger, threshold.
    crossing_slow_ms: int = 4000

    # ── pharmacy simulation ────────────────────────────────────────────────
    # "poll" is the read-only soak that produced every baseline this project
    # owns; it is untouched and stays the default. "pharmacy" adds picks on
    # top of the same poll: the cabinet is also being USED while it is
    # watched, which is the one traffic shape no soak here has ever applied.
    mode: str = "poll"               # poll | pharmacy
    # Activations per cabinet per day. A ward is not a stress test -- the
    # point is the shape of real use, not the maximum the bus can take.
    picks_per_day: int = 2000
    # How long a lit window stays lit before the simulation clears it, the
    # way a server clears one when the tablet confirm arrives.
    dwell_s: float = 20.0
    # Windows per slot to draw from: 8 on a mask cabinet (window n = person
    # n), and on a ring cabinet the same coils select a colour preset, which
    # is radio -- so only the last one drawn stays lit there. Harmless, and
    # the clear still lands on what was lit.
    windows: int = 8


@dataclass
class Anomaly:
    when: datetime
    device_id: int
    kind: str                    # no_reply | reboot | watchdog | slow |
                                 # link_lost | link_back
    detail: str = ""

    @property
    def text(self) -> str:
        return (f"{self.when:%H:%M:%S}  id {self.device_id}  "
                f"{self.kind}{('  ' + self.detail) if self.detail else ''}")


@dataclass
class SoakTick:
    """One pass finished — the running totals, for the live panel."""
    passes: int = 0
    txns: int = 0
    fails: int = 0
    reboots: int = 0
    watchdogs: int = 0
    worst_ms: float = 0.0        # worst ORDINARY read (crossings excluded)
    crossings: int = 0
    worst_crossing_ms: float = 0.0
    picks: int = 0               # pharmacy mode: windows lit so far
    dropped: int = 0             # picks with no dark window left to use
    lit: int = 0                 # windows lit at this instant
    elapsed_s: float = 0.0
    seq: int = 0


@dataclass
class SoakAnomaly:
    item: Anomaly = None
    seq: int = 0


@dataclass
class SoakDone:
    cancelled: bool = False
    summary: str = ""
    seq: int = 0


@dataclass
class SoakReport:
    started: datetime = None
    anomalies: list = field(default_factory=list)
    tick: SoakTick = field(default_factory=SoakTick)


def _totals(tick: SoakTick) -> str:
    """Running totals as key=value pairs. No commas — the CSV has four
    columns and a detail field that quietly grew a fifth would be worse
    than useless when someone opens it a month later."""
    return (f"pass={tick.passes} reads={tick.txns} fails={tick.fails} "
            f"reboots={tick.reboots} wdt={tick.watchdogs} "
            f"worst_ms={tick.worst_ms:.0f} cross={tick.crossings} "
            f"worst_cross_ms={tick.worst_crossing_ms:.0f} "
            f"picks={tick.picks} dropped={tick.dropped} lit={tick.lit} "
            f"elapsed_s={tick.elapsed_s:.0f}")


def _counters(ops: SoakOps, device_id: int, want_iwdg: bool,
              on_read: Optional[Callable[[int, float], None]] = None):
    """(boots, iwdg, reset_cause) for one module.

    iwdg is None on firmware without the v2 stats block. reset_cause is the
    module's own reg-8 flags for the boot it is currently running, which it
    latches once and clears, so it names the cause of the boot rather than
    being inferred from a counter moving.

    `on_read(addr, took_ms, ok)` fires for every read this makes. The main pass
    has always timed its own reads; these two did not, and that gap hid the
    one fact that would have explained modules 12/13. They lose the FIRST
    attempt of the ordinary read(0, 3) four passes out of five -- 3,578 ms
    is the 3.5 s client timeout plus a retry that always succeeds -- and the
    one pass they behave on is the pass right after this function ran. So
    the read shape, not the cable, is the variable, and the reads that
    "fix" them were the only ones nobody was measuring.
    """
    t = time.monotonic()
    res = ops.read_regs(device_id, REG_IDENTITY, 12)
    if on_read:
        on_read(REG_IDENTITY, (time.monotonic() - t) * 1000.0, res.ok)
    values = res.value if isinstance(res.value, (list, tuple)) else None
    if not (res.ok and values and len(values) >= 12):
        return None
    boots = int(values[REG_BOOTS])
    cause = int(values[REG_RESET_CAUSE])
    iwdg = None
    if want_iwdg and int(values[1]) >= FW_MIN_STATS:
        t = time.monotonic()
        r2 = ops.read_regs(device_id, REG_STATS2_IWDG, 1)
        if on_read:
            on_read(REG_STATS2_IWDG, (time.monotonic() - t) * 1000.0, r2.ok)
        # A one-register read comes back as a bare int, not a list of one.
        # Testing for a list here made every iwdg reading None, so the
        # watchdog comparison below could never fire and a whole night of
        # watchdog resets was reported as wdt=0 — the opposite conclusion
        # (clean power cycles) from the truth. Let the count decide the
        # shape, and compare against None: zero resets is a real answer.
        v2 = r2.value
        if r2.ok and v2 is not None:
            iwdg = int(v2[0] if isinstance(v2, (list, tuple)) else v2)
    return boots, iwdg, cause


class _Pharmacy:
    """Draws which window to light next, and remembers to put it out.

    Windows come off a SHUFFLED DECK of every (module, window) pair rather
    than a uniform draw. Uniform gives Poisson spread -- over a night one
    slot collects twice the activations of another -- and then any per-slot
    comparison afterwards is confounded by exposure instead of by health.
    Dealing a shuffled deck and reshuffling when it runs out gives every
    pair the same count, and still looks nothing like a sweep.

    One write per step(), never a burst: a ward lights a slot every half a
    minute, and the whole value of this mode is that it is the shape of real
    use rather than the maximum the bus will take.

    DWELL AND RATE ARE ONE SETTING, NOT TWO. How many windows are lit at
    once is neither of them alone -- it settles at

        concurrent = picks_per_day / 86400 * dwell_s

    so the defaults (2000/day, 20 s) hold 0.46 windows lit, and the cabinet
    is essentially never showing two at a time. That is a perfectly good
    imitation of a ward and a poor exercise of the v3.5.0 window engine,
    which exists precisely because eight people can share one slot. Dwell is
    the honest knob for reaching that: leaving a window lit for five minutes
    is exactly what happens when a pharmacist is interrupted.

    Push it far enough, though, and the model stops being a model -- when
    concurrent approaches the number of (module, window) pairs the cabinet is
    simply all on, and the deck has nothing left to deal.
    estimate_concurrent() below lets a caller see that coming, and the run
    says so in the CSV rather than quietly dropping the picks it cannot
    place.
    """

    def __init__(self, ids: Sequence[int], windows: int,
                 picks_per_day: int, dwell_s: float, now: float) -> None:
        self._pairs = [(i, w) for i in ids for w in range(1, windows + 1)]
        self._deck: list = []
        self._lit: dict = {}                 # (id, window) -> monotonic expiry
        self._dwell = max(1.0, dwell_s)
        self._interval = 86400.0 / max(1, picks_per_day)
        self._next_at = now + self._interval
        self._rng = random.Random()
        self.picks = 0
        self.skipped = 0            # picks the cabinet had no dark window for

    def _deal(self):
        if not self._deck:
            self._deck = list(self._pairs)
            self._rng.shuffle(self._deck)
        return self._deck.pop()

    def step(self, now: float):
        """The next single bus action, or None when there is nothing due.

        Returns (device_id, coil, on). Clears come first: a window that has
        served its dwell is a promise already made, while the next pick can
        wait for the following step a few hundred milliseconds later.
        """
        due = next((p for p, exp in self._lit.items() if now >= exp), None)
        if due is not None:          # find first, delete after -- never
            del self._lit[due]       # mutate a dict while iterating it
            return due[0], 1000 + due[1], False
        if now < self._next_at:
            return None
        self._next_at = now + self._interval
        held = []
        try:
            for _ in range(len(self._pairs)):
                dev, win = self._deal()
                if (dev, win) not in self._lit:
                    self._lit[(dev, win)] = now + self._dwell
                    self.picks += 1
                    return dev, 1000 + win, True
                held.append((dev, win))
        finally:
            # Pairs passed over because they were already lit go BACK on the
            # deck, at the top, still owed their turn. Dropping them was the
            # subtle cost of a long dwell: the deck is the only reason every
            # slot gets equal exposure, and discarding whatever happened to
            # be lit would have biased exposure towards the windows that
            # clear fastest -- worst exactly when dwell is long, which is
            # when a soak leans on the deck most.
            self._deck.extend(held)
        self.skipped += 1
        return None

    def lit_count(self) -> int:
        return len(self._lit)

    def all_off(self):
        """Every pair still lit, so a run that ends does not leave the
        cabinet decorated."""
        out = [(d, 1000 + w) for (d, w) in self._lit]
        self._lit.clear()
        return out


def estimate_concurrent(ids, windows: int, picks_per_day: int,
                        dwell_s: float):
    """(concurrent, capacity) for a pharmacy run that has not started yet.

    Rate and dwell are the two knobs an operator sets, and neither one says
    what the run will actually look like -- their product does. A caller
    showing this before the start button is pressed saves a night spent
    proving that 0.46 windows lit at a time does not exercise an engine
    built for eight.
    """
    capacity = max(1, len(list(ids)) * max(1, windows))
    concurrent = max(1, picks_per_day) / 86400.0 * max(1.0, dwell_s)
    return concurrent, capacity


def run_soak(ops: SoakOps, cfg: SoakConfig, emit: Callable,
             cancel: threading.Event, log_line: Optional[Callable] = None) -> SoakReport:
    """Poll until cancelled. `log_line(str)` appends CSV rows: one per
    anomaly, plus start / heartbeat / stop rows on device 0."""
    report = SoakReport(started=datetime.now())
    ids = list(cfg.ids)
    t0 = time.monotonic()
    tick = report.tick

    def note(device_id: int, kind: str, detail: str = "") -> None:
        item = Anomaly(datetime.now(), device_id, kind, detail)
        report.anomalies.append(item)
        emit(SoakAnomaly(item=item))
        if log_line:
            log_line(f"{item.when:%Y-%m-%d %H:%M:%S},{device_id},{kind},{detail}")

    def csv(kind: str, detail: str, device_id: int = 0) -> None:
        """A row for the file only — the anomaly list on screen stays a list
        of things that went wrong.

        Pharmacy mode is why this takes a device id. Every pick and clear is
        worth keeping, so a file can be replayed into "what was this cabinet
        asked to show at 03:40", but 4,000 routine writes a day are not
        anomalies: routing them through note() would have pushed the real
        findings out of a 400-line box within a couple of hours and left an
        overnight run looking clean because its evidence had scrolled away.
        """
        if log_line:
            log_line(f"{datetime.now():%Y-%m-%d %H:%M:%S},{device_id},{kind},{detail}")

    start_detail = (f"ids={len(ids)} gap_s={cfg.pass_gap_s} "
                    f"counter_every={cfg.counter_every} slow_ms={cfg.slow_ms} "
                    f"crossing_slow_ms={cfg.crossing_slow_ms} mode={cfg.mode}")
    if cfg.mode == "pharmacy":
        # Record the derived concurrency, not just the two knobs. The whole
        # question a reader brings to a pharmacy-mode file months later is
        # "was the multi-window engine actually under load here", and that
        # is the product of rate and dwell, not either number on its own.
        conc, cap = estimate_concurrent(ids, cfg.windows,
                                        cfg.picks_per_day, cfg.dwell_s)
        start_detail += (f" picks_per_day={cfg.picks_per_day} "
                         f"dwell_s={cfg.dwell_s:.0f} windows={cfg.windows} "
                         f"concurrent={conc:.2f}/{cap}")
    csv("start", start_detail)
    reason = "unknown"
    polled = False
    try:
        polled = _poll(ops, cfg, emit, cancel, report, note, csv, t0)
        reason = "cancelled" if polled else "cancelled_before_baseline"
    except BaseException as exc:                                # noqa: BLE001
        reason = f"error:{type(exc).__name__}"
        raise
    finally:
        # Whatever happened — cancelled, crashed, or the machine pulled the
        # rug — the file ends with a line saying so and what had been seen
        # up to that point.
        tick.elapsed_s = time.monotonic() - t0
        csv("stop", f"reason={reason} " + _totals(tick))

    if not polled:                  # _poll has already said why it gave up
        return report

    hours = tick.elapsed_s / 3600.0
    emit(SoakDone(cancelled=True,
                  summary=(f"{hours:.1f} h · {tick.passes} passes · "
                           f"{tick.txns} reads · {tick.fails} failed · "
                           f"{tick.reboots} reboots · {tick.watchdogs} watchdog · "
                           f"{tick.crossings} hub crossings "
                           f"(worst {tick.worst_crossing_ms:.0f} ms)")))
    return report


def _poll(ops: SoakOps, cfg: SoakConfig, emit: Callable, cancel: threading.Event,
          report: SoakReport, note: Callable, csv: Callable, t0: float) -> bool:
    """The run itself. Split out so run_soak's start/stop bookkeeping wraps
    every exit from it, including the early return on a cancelled baseline.

    False = it never got past the baseline, and has already said so."""
    ids = list(cfg.ids)
    tick = report.tick
    link_state = {"down": False, "since": 0.0, "missed": 0}

    # Baseline: what every module says before we start leaning on the bus.
    baseline: dict = {}
    for device_id in ids:
        if cancel.is_set():
            emit(SoakDone(cancelled=True, summary="cancelled before the baseline"))
            return False
        baseline[device_id] = _counters(ops, device_id, True)
        if baseline[device_id] is None:
            note(device_id, "no_reply", "missing at the baseline")
        ops.sleep(INTER_TXN_S)

    # Pharmacy simulation, when asked for. Built after the baseline so its
    # first pick lands on a cabinet whose counters are already known.
    pharmacy = None
    if cfg.mode == "pharmacy":
        pharmacy = _Pharmacy(ids, cfg.windows, cfg.picks_per_day,
                             cfg.dwell_s, time.monotonic())
        csv("sim_start", f"picks_per_day={cfg.picks_per_day} "
                         f"dwell_s={cfg.dwell_s} windows={cfg.windows} "
                         f"pairs={len(ids) * cfg.windows}")

    saturated: list = []       # one-shot latch for the note above
    behind: list = []          # one-shot latch for the rate shortfall below

    def check_rate() -> None:
        """Say so when the bus cannot deliver the pick rate that was asked for.

        `dropped` only counts picks with nowhere to go. It does NOT catch the
        other way a run quietly stops being the run you configured: the bus
        simply not keeping up. A pick lands on a random module, which drags
        the hub off whatever channel the poll is walking, so the next read
        drags it back -- every pick costs TWO channel crossings, about 4.4 s
        of bus time on the type-80 cabinet. Measured there on 2026-09-17,
        43,200/day asked produced 16,491/day, 38% of it, with dropped=0 and
        nothing on screen suggesting the figure in the config was fiction.

        Judged only once enough picks were due for the number to mean
        anything, and said once, because it will stay true all night.
        """
        if pharmacy is None or behind:
            return
        expected = tick.elapsed_s / 86400.0 * cfg.picks_per_day
        if expected < 20:
            return
        achieved = tick.picks / max(1.0, tick.elapsed_s) * 86400.0
        if achieved >= cfg.picks_per_day * 0.8:
            return
        behind.append(True)
        note(0, "sim_behind",
             f"asked {cfg.picks_per_day}/day got {achieved:.0f}/day "
             f"({achieved / cfg.picks_per_day * 100:.0f}%) -- the bus cannot "
             f"place picks this fast; each one costs two hub crossings")

    # Where the hub is parked, shared by the poll and the simulation. It has
    # to be shared: a pick jumps to wherever the deck sent it and MOVES the
    # hub, so a poll that kept its own idea of the channel would mis-score
    # every crossing after the first pick — undercounting the crossings and
    # then blaming the module that paid for one.
    chan = [None]

    def crossing_to(channel: int) -> bool:
        """True when reaching `channel` means the hub has to move. Updates
        the shared tracker, so callers must only ask once per transaction."""
        moved = channel != 0 and (chan[0] is None or channel != chan[0])
        chan[0] = channel
        return moved

    def pharmacy_step() -> None:
        """At most ONE coil write per call, slipped between module reads.

        Interleaving rather than bursting is the whole point: the cabinet
        has to be carrying real traffic WHILE it is watched, and a ward
        lights a slot every half a minute, not eighty in a row.

        These writes are TIMED, and they are the reason to time anything.
        The poll walks ids in order and crosses the hub about ten times a
        pass; the deck sends a pick anywhere, so nearly every one crosses —
        which makes this the most crossing-heavy traffic the tool produces
        and the closest thing here to how a server actually reaches a
        cabinet. Leaving it unmeasured would have wasted the run it exists
        to justify.
        """
        if pharmacy is None:
            return
        before_skips = pharmacy.skipped
        action = pharmacy.step(time.monotonic())
        tick.lit = pharmacy.lit_count()
        if action is None:
            tick.dropped = pharmacy.skipped
            if pharmacy.skipped != before_skips and not saturated:
                # Every window in the cabinet is already lit, so this pick
                # had nowhere to go. Say it ONCE -- at this dwell it will
                # happen for the rest of the night, and a line per dropped
                # pick would bury the run's real findings. The summary
                # carries the count.
                saturated.append(True)
                note(0, "sim_saturated",
                     f"every window lit (dwell {cfg.dwell_s:.0f} s at "
                     f"{cfg.picks_per_day}/day exceeds "
                     f"{len(ids) * cfg.windows} windows) -- picks now dropped")
            return
        dev, coil, on = action
        crossed = crossing_to(hub_channel(dev))
        t = time.monotonic()
        res = ops.write_coil(dev, coil, on)
        took_ms = (time.monotonic() - t) * 1000.0
        tick.txns += 1
        if crossed:
            tick.crossings += 1
            tick.worst_crossing_ms = max(tick.worst_crossing_ms, took_ms)
        else:
            tick.worst_ms = max(tick.worst_ms, took_ms)
        what = "pick" if on else "clear"
        if not getattr(res, "ok", False):
            tick.fails += 1
            note(dev, "no_reply", f"{what} window {coil - 1000}"
                                  + (" after a hub crossing" if crossed else ""))
            return
        if on:
            tick.picks += 1
        limit = cfg.crossing_slow_ms if crossed else cfg.slow_ms
        if took_ms >= limit:
            note(dev, "slow", f"{took_ms:.0f} ms ({what} window {coil - 1000}"
                              + (" hub crossing" if crossed else "") + ")")
        tick.lit = pharmacy.lit_count()
        csv(what, f"window {coil - 1000}", dev)

    while not cancel.is_set():
        tick.passes += 1
        check_counters = (tick.passes % max(1, cfg.counter_every) == 0)

        for device_id in ids:
            if cancel.is_set():
                break
            # The very first read counts as a crossing too: nobody knows which
            # channel the hub is parked on, and letting that one 2.2 s wait
            # into the ordinary "worst" made the panel look alarming forever.
            crossing = crossing_to(hub_channel(device_id))

            t = time.monotonic()
            res = ops.read_regs(device_id, REG_IDENTITY, 3)
            took_ms = (time.monotonic() - t) * 1000.0
            tick.txns += 1
            if crossing:
                tick.crossings += 1
                tick.worst_crossing_ms = max(tick.worst_crossing_ms, took_ms)
            else:
                tick.worst_ms = max(tick.worst_ms, took_ms)

            limit = cfg.crossing_slow_ms if crossing else cfg.slow_ms
            if getattr(res, "link_down", False):
                # The transport is gone, not this module. Say it ONCE and
                # keep the file readable: a site power cut once wrote 64,689
                # identical rows in 89 minutes and made the app unusable.
                # The worker reconnects underneath; the run simply resumes.
                if not link_state["down"]:
                    link_state["down"] = True
                    link_state["since"] = time.monotonic()
                    link_state["missed"] = 0
                    note(0, "link_lost", (res.note or "transport gone")[:60])
                link_state["missed"] += 1
                tick.fails += 1
            elif not res.ok:
                if link_state["down"]:
                    link_state["down"] = False
                    note(0, "link_back",
                         f"after {time.monotonic() - link_state['since']:.0f} s, "
                         f"{link_state['missed']} reads lost")
                tick.fails += 1
                note(device_id, "no_reply",
                     ("after a hub crossing; " if crossing else "") + (res.note or ""))
            else:
                if link_state["down"]:
                    link_state["down"] = False
                    note(0, "link_back",
                         f"after {time.monotonic() - link_state['since']:.0f} s, "
                         f"{link_state['missed']} reads lost")
                if took_ms >= limit:
                    note(device_id, "slow",
                         f"{took_ms:.0f} ms" + (" (hub crossing)" if crossing else ""))
            ops.sleep(INTER_TXN_S)
            pharmacy_step()

        if check_counters and not cancel.is_set():
            for device_id in ids:
                if cancel.is_set():
                    break
                # This loop walks the same ids in the same order, so it
                # crosses the hub exactly as the main pass does and needs the
                # same allowance -- the channel tracker carries over deliberately.
                counter_crossing = crossing_to(hub_channel(device_id))

                # Only the FIRST read of the pair pays the channel settle;
                # the second one is already on a woken channel, so it is held
                # to the ordinary limit. A one-slot list because a plain flag
                # rebound inside the closure would reset on every call.
                cross_left = [counter_crossing]

                def timed(addr: int, took_ms: float, ok: bool,
                          _dev=device_id) -> None:
                    crossed, cross_left[0] = cross_left[0], False
                    tick.txns += 1
                    if crossed:
                        tick.crossings += 1
                        tick.worst_crossing_ms = max(tick.worst_crossing_ms,
                                                     took_ms)
                    if not ok:
                        # A dead module's counter read burns the whole client
                        # timeout; calling that "slow" would inflate the very
                        # column this investigation reads. Lost is lost.
                        tick.fails += 1
                        note(_dev, "no_reply", f"counter reg {addr}"
                                               + (" after a hub crossing"
                                                  if crossed else ""))
                        return
                    limit = cfg.crossing_slow_ms if crossed else cfg.slow_ms
                    if took_ms >= limit:
                        note(_dev, "slow", f"{took_ms:.0f} ms (counter reg {addr}"
                                           + (" hub crossing" if crossed else "") + ")")

                now = _counters(ops, device_id, True, timed)
                was = baseline.get(device_id)
                if now is None:
                    ops.sleep(INTER_TXN_S)
                    continue
                if was is None:
                    baseline[device_id] = now       # it came back; start counting
                    ops.sleep(INTER_TXN_S)
                    continue
                if now[0] != was[0]:
                    tick.reboots += 1
                    # Say on the reboot row itself what kind of reboot it was.
                    # The absence of a watchdog row below means either "the
                    # counter held still" or "reg 410 could not be read this
                    # pass", and those are opposite conclusions about the
                    # cabinet: a supply sag stops the CPU and the watchdog
                    # rescues it, while a real interruption leaves the watchdog
                    # untouched. Reg 8 is the module's own answer for the boot
                    # it is running, and it costs nothing — it already rides in
                    # the same read as the boot counter.
                    cause = " ".join(decode_reset_cause(now[2])) or f"raw {now[2]}"
                    if now[1] is None or was[1] is None:
                        seen = "iwdg unread"
                    elif now[1] != was[1]:
                        seen = f"iwdg {was[1]} -> {now[1]}"
                    else:
                        seen = f"iwdg {now[1]} unchanged"
                    note(device_id, "reboot",
                         f"boots {was[0]} -> {now[0]} cause={cause} {seen}")
                if now[1] is not None and was[1] is not None and now[1] != was[1]:
                    tick.watchdogs += 1
                    note(device_id, "watchdog", f"iwdg {was[1]} -> {now[1]}")
                baseline[device_id] = now
                ops.sleep(INTER_TXN_S)

        tick.elapsed_s = time.monotonic() - t0
        # A COPY of every field, never a hand-written list of them. The
        # listing here was missing `lit` and `dropped` the day they were
        # added, so the panel showed 0 lit windows through a run that was
        # lighting them correctly — the same silent-zero shape that once had
        # a night of 308 watchdog resets reporting wdt=0. A new field on
        # SoakTick must not depend on someone remembering this line.
        check_rate()
        emit(replace(tick))
        # One line per pass, so the end of the file is a fact rather than an
        # inference: the last heartbeat is the last moment the tool was
        # certainly alive and the cabinet certainly answering.
        csv("heartbeat", _totals(tick))
        ops.sleep(cfg.pass_gap_s)

    if pharmacy is not None:
        # A cancelled run must not leave windows lit across the ward
        # overnight. Best effort: the transport may already be gone.
        for dev, coil in pharmacy.all_off():
            try:
                ops.write_coil(dev, coil, False)
            except Exception:                                   # noqa: BLE001
                break
        csv("sim_stop", f"picks={tick.picks} dropped={tick.dropped}")

    return True
