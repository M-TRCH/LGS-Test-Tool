"""Read a soak CSV back into a summary the site report can print.

The soak writes an append-only log (`time,device_id,kind,detail`, see
app/soak.py) that is complete but unreadable to anyone who was not there:
6,000 rows in which the single line that matters — "were the reboots the
03:00 scheduled reset, or a fault?" — has to be reconstructed by hand.
This module does that reconstruction once, correctly, so the report can
carry the conclusion instead of the raw file.

Two judgment calls are encoded here because getting them wrong has already
cost real analysis time:

* A run without a `stop` row did not finish — the PC slept or lost power —
  and its totals are the last heartbeat's, which undercounts the tail. The
  summary says so rather than presenting the numbers as final.

* Reboots are grouped by the module's own reg-8 cause AND checked for the
  whole-cabinet-at-once shape: when at least half the polled modules reboot
  inside one two-minute window with their watchdog counters unchanged, that
  is the gateway's scheduled reset doing its job, not a fault. A night with
  "reboots=64" in the footer and zero actual faults looks alarming in
  exactly the way that misled us on 2026-08-27.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

_TS = "%Y-%m-%d %H:%M:%S"
_KV = re.compile(r"(\w+)=(\S+)")
_IWDG_MOVED = re.compile(r"iwdg \d+ -> \d+")

# The whole-cabinet reset window. The 2026-08-27 scheduled reset landed all
# 64 reboot rows in 29 seconds; 120 s leaves room for a slower counter pass.
MASS_WINDOW_S = 120.0
# Slow readings this close to a scheduled reset (either side of its cluster)
# are put down to the reset: modules are booting and the bus is waking up.
# Same rule, same numbers as the LGS Soak Monitor (lgs-monitor/src/worker.js),
# so the PDF and the dashboard tell the same story about the same run.
RESET_MARGIN_S = 120.0


@dataclass
class SoakDeviceTrouble:
    """Every module that was ever slow or silent, as the LGS Soak Monitor's
    module table counts it: ordinary slow reads and hub-crossing reads apart
    (the tool judges them against different limits, slow_ms and
    crossing_slow_ms), each worst reading with its time and whether it fell
    inside a scheduled-reset window."""
    device_id: int
    slow: int = 0                    # slow reads, hub crossings NOT included
    worst_slow_ms: int = 0
    worst_slow_at: Optional[datetime] = None
    worst_slow_in_reset: bool = False
    normal_worst_ms: int = 0         # slowest outside every reset window
    normal_worst_at: Optional[datetime] = None
    cross: int = 0                   # slow reads during a hub crossing
    worst_cross_ms: int = 0
    worst_cross_at: Optional[datetime] = None
    worst_cross_in_reset: bool = False
    no_reply: int = 0

    @property
    def count(self) -> int:
        return self.slow + self.cross + self.no_reply


@dataclass
class SoakSummary:
    filename: str = ""
    started: Optional[datetime] = None
    ended: Optional[datetime] = None
    finished: bool = False          # a stop row was present
    config: str = ""                # the start row's detail, verbatim

    # Totals from the stop row, or the last heartbeat when there is none.
    passes: int = 0
    reads: int = 0
    fails: int = 0
    picks: int = 0                  # pharmacy mode: windows lit during the run
    dropped: int = 0                # picks the cabinet was too full to place
    writes: int = 0                 # coil writes -- NOT part of `reads`
    write_fails: int = 0            # of those, the ones that did not land
    reboots: int = 0
    watchdogs: int = 0
    worst_ms: int = 0
    crossings: int = 0
    worst_cross_ms: int = 0

    # Reboot rows regrouped: cause text -> count.
    reboot_causes: dict = field(default_factory=dict)
    # Every scheduled-reset cluster: {"start", "end", "n"}. A run that spans
    # three nights has three, and each one is the gateway doing its job.
    mass_clusters: list = field(default_factory=list)
    # Reboots inside those clusters (their sum) — near-certainly the scheduled
    # reset, not a fault. mass_when is the first cluster's start.
    mass_reboots: int = 0
    mass_when: Optional[datetime] = None
    module_count: int = 0           # ids= from the start row

    # The watchdog, read three independent ways off the reboot rows, because
    # each can miss what another sees: the counter comparison is lost when
    # reg 410 could not be read that pass ("iwdg unread"), while reg 8's own
    # cause bit is read in the same transaction as the boot counter.
    iwdg_moved_rows: int = 0        # "iwdg A -> B" on the reboot row
    iwdg_cause_rows: int = 0        # reg 8 says IWDG
    iwdg_unread_rows: int = 0       # counter unreadable: cause unknown

    trouble: list = field(default_factory=list)   # SoakDeviceTrouble, most first
    link_losses: int = 0

    @property
    def duration_s(self) -> float:
        if self.started and self.ended:
            return (self.ended - self.started).total_seconds()
        return 0.0

    @property
    def unexplained_reboots(self) -> int:
        # Never negative: a mass event after the last heartbeat of an
        # unfinished run makes the footer's reboot count lag the rows.
        return max(0, self.reboots - self.mass_reboots)

    @property
    def watchdog_resets(self) -> int:
        """The most any one witness saw. The footer's wdt is the soak's
        counter comparison; a reboot row can still name IWDG in reg 8 when
        that comparison was skipped for an unreadable counter."""
        return max(self.watchdogs, self.iwdg_moved_rows, self.iwdg_cause_rows)

    @property
    def problems(self) -> bool:
        """The Soak Monitor's verdict: any failed read, any watchdog reset or
        any reboot no scheduled reset explains."""
        return bool(self.fails or self.watchdog_resets or self.unexplained_reboots)

    def slowest(self, which: str = "slow", outside_reset: bool = False):
        """(device_id, ms, at, in_reset) of the run's slowest reading, from
        the rows themselves — the footer's worst_ms leaves out the counter
        reads. which: "slow" (ordinary reads) or "cross" (hub crossings)."""
        best = None
        for t in self.trouble:
            if which == "cross":
                ms, at, rst = t.worst_cross_ms, t.worst_cross_at, t.worst_cross_in_reset
            elif outside_reset:
                ms, at, rst = t.normal_worst_ms, t.normal_worst_at, False
            else:
                ms, at, rst = t.worst_slow_ms, t.worst_slow_at, t.worst_slow_in_reset
            if ms and (best is None or ms > best[1]):
                best = (t.device_id, ms, at, rst)
        return best

    def headline(self) -> str:
        """One line for the UI label and the report subtitle."""
        h = self.duration_s / 3600.0
        parts = [f"{h:.1f} h", f"{self.reads:,} reads", f"fails {self.fails}",
                 f"wdt {self.watchdog_resets}"]
        if self.reboots:
            k = len(self.mass_clusters)
            if self.unexplained_reboots == 0:
                what = ("all simultaneous — scheduled reset" if k <= 1
                        else f"{k} scheduled resets")
                parts.append(f"reboots {self.reboots} ({what})")
            else:
                parts.append(f"reboots {self.reboots} "
                             f"({self.unexplained_reboots} unexplained)")
        else:
            parts.append("reboots 0")
        if not self.finished:
            parts.append("RUN DID NOT FINISH")
        return " · ".join(parts)


class SoakCsvError(ValueError):
    """The file is not a soak CSV. The message is safe to show in the UI."""


def _kv(detail: str) -> dict:
    return dict(_KV.findall(detail))


def parse_soak_csv(text: str, filename: str = "") -> SoakSummary:
    lines = text.splitlines()
    if not lines or not lines[0].strip().startswith("time,device_id,kind"):
        raise SoakCsvError("not a soak CSV (missing time,device_id,kind header)")

    out = SoakSummary(filename=filename)
    trouble: dict[int, SoakDeviceTrouble] = {}
    # Every slow reading, kept until the reset windows are known: a module's
    # worst reading outside the windows can only be picked afterwards.
    readings: dict[int, list] = {}
    reboot_times: list[datetime] = []
    totals_detail = ""

    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split(",", 3)
        if len(parts) != 4:
            continue                      # a torn tail line from a power cut
        ts_raw, dev_raw, kind, detail = parts
        try:
            when = datetime.strptime(ts_raw, _TS)
            dev = int(dev_raw)
        except ValueError:
            continue
        if out.started is None:
            out.started = when
        out.ended = when

        if kind == "start":
            out.config = detail
            try:
                out.module_count = int(_kv(detail).get("ids", 0))
            except ValueError:
                pass
        elif kind in ("heartbeat", "stop"):
            totals_detail = detail
            if kind == "stop":
                out.finished = True
        elif kind == "slow":
            t = trouble.setdefault(dev, SoakDeviceTrouble(dev))
            m = re.match(r"(\d+)", detail)
            # Crossing reads are allowed longer (crossing_slow_ms) and the
            # footer reports them apart (worst_cross_ms), so they are counted
            # apart here too. A counter read IS an ordinary read: its "(counter
            # reg N)" suffix does not move it out of the slow column.
            crossing = "crossing" in detail
            if crossing:
                t.cross += 1
            else:
                t.slow += 1
            if m:
                readings.setdefault(dev, []).append((int(m.group(1)), when, crossing))
        elif kind == "no_reply":
            trouble.setdefault(dev, SoakDeviceTrouble(dev)).no_reply += 1
        elif kind == "reboot":
            # Only a reboot whose own row says the watchdog counter held
            # still may join a "scheduled reset" cluster. The soak writes
            # "iwdg N unchanged" / "iwdg N -> M" onto every reboot row for
            # exactly this distinction; a brown-out that IWDG-resets half
            # the cabinet inside two minutes must NOT get the green verdict.
            reboot_times.append((when, "unchanged" in detail))
            m = re.search(r"cause=(.*?)\s+iwdg", detail)
            cause = m.group(1) if m else "unknown"
            out.reboot_causes[cause] = out.reboot_causes.get(cause, 0) + 1
            # "iwdg A -> B" only: every reboot row also says "boots A -> B".
            if _IWDG_MOVED.search(detail):
                out.iwdg_moved_rows += 1
            if "iwdg unread" in detail:
                out.iwdg_unread_rows += 1
            if "IWDG" in cause.upper():
                out.iwdg_cause_rows += 1
        elif kind == "link_lost":
            out.link_losses += 1

    if out.started is None:
        raise SoakCsvError("no parseable rows")

    if totals_detail:
        kv = _kv(totals_detail)

        def num(key: str) -> int:
            try:
                return int(float(kv.get(key, 0)))
            except ValueError:
                return 0

        out.passes = num("pass")
        out.reads = num("reads")
        out.fails = num("fails")
        out.reboots = num("reboots")
        out.watchdogs = num("wdt")
        out.worst_ms = num("worst_ms")
        out.crossings = num("cross")
        out.worst_cross_ms = num("worst_cross_ms")
        # Pharmacy mode only; a poll run simply reports zero. Without these
        # a simulated run's report reads exactly like a plain poll's, and
        # the one thing that made it worth running -- that the cabinet was
        # being USED while it was watched -- would be invisible in the
        # summary even though every pick is there in the rows.
        out.picks = num("picks")
        out.dropped = num("dropped")
        out.writes = num("writes")
        out.write_fails = num("write_fails")

    # Mass-reboot detection over the reboot rows whose own iwdg counter held
    # still (watchdog reboots never qualify): a window of MASS_WINDOW_S from
    # the first row, at least half the cabinet inside it. EVERY such cluster
    # counts — this used to keep only the largest ("a nightly reset fires
    # once"), so a run across two nights called the second night's 64
    # scheduled reboots unexplained. Same walk as the LGS Soak Monitor.
    clean_times = sorted(t for t, unchanged in reboot_times if unchanged)
    if clean_times and out.module_count:
        need = max(2, out.module_count // 2)
        i = 0
        while i < len(clean_times):
            k = i
            while (k + 1 < len(clean_times)
                   and (clean_times[k + 1] - clean_times[i]).total_seconds()
                   <= MASS_WINDOW_S):
                k += 1
            size = k - i + 1
            if size >= need:
                out.mass_clusters.append({"start": clean_times[i],
                                          "end": clean_times[k], "n": size})
                i = k + 1
            else:
                i += 1
        out.mass_reboots = sum(c["n"] for c in out.mass_clusters)
        if out.mass_clusters:
            out.mass_when = out.mass_clusters[0]["start"]
    # The footer can lag the rows (unfinished run): trust whichever saw more.
    out.reboots = max(out.reboots, len(reboot_times))

    # Each module's worst readings, now that the reset windows are known.
    windows = [(c["start"].timestamp() - RESET_MARGIN_S,
                c["end"].timestamp() + RESET_MARGIN_S) for c in out.mass_clusters]

    def in_reset(when: datetime) -> bool:
        ts = when.timestamp()
        return any(a <= ts <= b for a, b in windows)

    for dev, rows in readings.items():
        t = trouble[dev]
        for ms, when, crossing in rows:
            if crossing:
                if ms > t.worst_cross_ms:
                    t.worst_cross_ms, t.worst_cross_at = ms, when
                    t.worst_cross_in_reset = in_reset(when)
                continue
            if ms > t.worst_slow_ms:
                t.worst_slow_ms, t.worst_slow_at = ms, when
                t.worst_slow_in_reset = in_reset(when)
            if ms > t.normal_worst_ms and not in_reset(when):
                t.normal_worst_ms, t.normal_worst_at = ms, when

    # Most trouble first, then the slowest, then by id: the Monitor's
    # "by count" order, which is also what a reader scans for first.
    out.trouble = sorted(trouble.values(),
                         key=lambda t: (-t.count, -t.worst_slow_ms, t.device_id))
    return out
