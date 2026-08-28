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

# The whole-cabinet reset window. The 2026-08-27 scheduled reset landed all
# 64 reboot rows in 29 seconds; 120 s leaves room for a slower counter pass.
MASS_WINDOW_S = 120.0


@dataclass
class SoakDeviceTrouble:
    device_id: int
    slow: int = 0
    worst_slow_ms: int = 0
    no_reply: int = 0


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
    reboots: int = 0
    watchdogs: int = 0
    worst_ms: int = 0
    crossings: int = 0
    worst_cross_ms: int = 0

    # Reboot rows regrouped: cause text -> count.
    reboot_causes: dict = field(default_factory=dict)
    # Reboots inside a >= half-the-modules simultaneous window (see module
    # docstring) — near-certainly the scheduled reset, not a fault.
    mass_reboots: int = 0
    mass_when: Optional[datetime] = None
    module_count: int = 0           # ids= from the start row

    trouble: list = field(default_factory=list)   # SoakDeviceTrouble, worst first
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

    def headline(self) -> str:
        """One line for the UI label and the report subtitle."""
        h = self.duration_s / 3600.0
        parts = [f"{h:.1f} h", f"{self.reads:,} reads", f"fails {self.fails}",
                 f"wdt {self.watchdogs}"]
        if self.reboots:
            if self.unexplained_reboots == 0:
                parts.append(f"reboots {self.reboots} (all simultaneous — "
                             f"scheduled reset)")
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
            t.slow += 1
            m = re.match(r"(\d+)", detail)
            if m:
                t.worst_slow_ms = max(t.worst_slow_ms, int(m.group(1)))
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

    # Mass-reboot detection: slide a window over the reboot rows whose own
    # iwdg counter held still and take the largest cluster. One cluster is
    # enough — a nightly reset fires once. Watchdog reboots never qualify.
    clean_times = sorted(t for t, unchanged in reboot_times if unchanged)
    if clean_times and out.module_count:
        best, best_at = 0, None
        for i, t0 in enumerate(clean_times):
            k = i
            while (k + 1 < len(clean_times)
                   and (clean_times[k + 1] - t0).total_seconds() <= MASS_WINDOW_S):
                k += 1
            size = k - i + 1
            if size > best:
                best, best_at = size, t0
        if best >= max(2, out.module_count // 2):
            out.mass_reboots = best
            out.mass_when = best_at
    # The footer can lag the rows (unfinished run): trust whichever saw more.
    out.reboots = max(out.reboots, len(reboot_times))

    out.trouble = sorted(trouble.values(),
                         key=lambda t: (t.slow + t.no_reply), reverse=True)
    return out
