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
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Protocol, Sequence

from .fw_survey import FW_MIN_STATS
from .lgs_map import INTER_TXN_S, hub_channel

REG_IDENTITY = 0        # type, fw, hw — the cheap "are you there" read
REG_BOOTS = 7
REG_STATS2_IWDG = 410   # fw >= v3.3.0


class SoakOps(Protocol):
    def read_regs(self, device_id: int, addr: int, count: int): ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class SoakConfig:
    ids: tuple = ()
    pass_gap_s: float = 0.5      # breather between cabinet passes
    counter_every: int = 5       # re-read boot/watchdog counters every N passes
    slow_ms: int = 400           # a reply this slow is worth a line
    # The first read after a hub channel change is SUPPOSED to be slow: the
    # gateway holds it until the channel stops being deaf (~2.2 s). Logging
    # that as an anomaly would bury the real ones — so crossings are counted
    # separately and only complained about past their own, larger, threshold.
    crossing_slow_ms: int = 4000


@dataclass
class Anomaly:
    when: datetime
    device_id: int
    kind: str                    # no_reply | reboot | watchdog | slow
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


def _counters(ops: SoakOps, device_id: int, want_iwdg: bool):
    """(boots, iwdg) — iwdg is None on firmware without the v2 stats block."""
    res = ops.read_regs(device_id, REG_IDENTITY, 12)
    values = res.value if isinstance(res.value, (list, tuple)) else None
    if not (res.ok and values and len(values) >= 12):
        return None
    boots = int(values[REG_BOOTS])
    iwdg = None
    if want_iwdg and int(values[1]) >= FW_MIN_STATS:
        r2 = ops.read_regs(device_id, REG_STATS2_IWDG, 1)
        v2 = r2.value if isinstance(r2.value, (list, tuple)) else None
        if r2.ok and v2:
            iwdg = int(v2[0])
    return boots, iwdg


def run_soak(ops: SoakOps, cfg: SoakConfig, emit: Callable,
             cancel: threading.Event, log_line: Optional[Callable] = None) -> SoakReport:
    """Poll until cancelled. `log_line(str)` appends one CSV row per anomaly."""
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

    # Baseline: what every module says before we start leaning on the bus.
    baseline: dict = {}
    for device_id in ids:
        if cancel.is_set():
            emit(SoakDone(cancelled=True, summary="cancelled before the baseline"))
            return report
        baseline[device_id] = _counters(ops, device_id, True)
        if baseline[device_id] is None:
            note(device_id, "no_reply", "missing at the baseline")
        ops.sleep(INTER_TXN_S)

    prev_channel = None
    while not cancel.is_set():
        tick.passes += 1
        check_counters = (tick.passes % max(1, cfg.counter_every) == 0)

        for device_id in ids:
            if cancel.is_set():
                break
            channel = hub_channel(device_id)
            crossing = (channel != 0 and prev_channel is not None
                        and channel != prev_channel)
            prev_channel = channel

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
            if not res.ok:
                tick.fails += 1
                note(device_id, "no_reply",
                     ("after a hub crossing; " if crossing else "") + (res.note or ""))
            elif took_ms >= limit:
                note(device_id, "slow",
                     f"{took_ms:.0f} ms" + (" (hub crossing)" if crossing else ""))
            ops.sleep(INTER_TXN_S)

        if check_counters and not cancel.is_set():
            for device_id in ids:
                if cancel.is_set():
                    break
                now = _counters(ops, device_id, True)
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
                    note(device_id, "reboot", f"boots {was[0]} -> {now[0]}")
                if now[1] is not None and was[1] is not None and now[1] != was[1]:
                    tick.watchdogs += 1
                    note(device_id, "watchdog", f"iwdg {was[1]} -> {now[1]}")
                baseline[device_id] = now
                ops.sleep(INTER_TXN_S)

        tick.elapsed_s = time.monotonic() - t0
        emit(SoakTick(passes=tick.passes, txns=tick.txns, fails=tick.fails,
                      reboots=tick.reboots, watchdogs=tick.watchdogs,
                      worst_ms=tick.worst_ms, crossings=tick.crossings,
                      worst_crossing_ms=tick.worst_crossing_ms,
                      elapsed_s=tick.elapsed_s))
        ops.sleep(cfg.pass_gap_s)

    hours = tick.elapsed_s / 3600.0
    emit(SoakDone(cancelled=True,
                  summary=(f"{hours:.1f} h · {tick.passes} passes · "
                           f"{tick.txns} reads · {tick.fails} failed · "
                           f"{tick.reboots} reboots · {tick.watchdogs} watchdog · "
                           f"{tick.crossings} hub crossings "
                           f"(worst {tick.worst_crossing_ms:.0f} ms)")))
    return report
