"""Installation check — run a few real commands across many modules.

Breadth, not depth: for every selected slave ID it confirms the module answers
and then exercises the commands an installer actually wants to see (ring on,
number on the display, unlock, identify). The deep single-module sweep lives
in testsuite.py.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Protocol, Sequence

from .lgs_map import DEVICE_TYPES, INTER_TXN_S, hub_channel


class CheckCancelled(Exception):
    pass


class FieldOps(Protocol):
    """Same transactions as the worker facade, with the device id per call."""

    def read_reg(self, device_id: int, addr: int): ...
    def write_reg(self, device_id: int, addr: int, value: int): ...
    def write_coil(self, device_id: int, addr: int, value: int): ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class CheckConfig:
    light: bool = True              # coil 1001 — ring on, hold, off
    unlock: bool = False            # coil 1021 — ring + latch pulse (physical!)
    display: bool = False           # reg 60 + coil 1010 — number on the OLED
    identify: bool = False          # coil 509 — blink white ~5 s, self-restoring
    hold_s: float = 1.0             # how long the light/number stays visible

    def unlock_count(self, device_count: int) -> int:
        return device_count if self.unlock else 0


@dataclass
class StepOutcome:
    label: str
    ok: bool
    note: str = ""


@dataclass
class DeviceResult:
    device_id: int
    responded: bool
    device_type: Optional[int] = None
    steps: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.responded and all(s.ok for s in self.steps)

    @property
    def type_name(self) -> str:
        if self.device_type is None:
            return ""
        return DEVICE_TYPES.get(self.device_type, f"type {self.device_type}")


@dataclass
class DeviceStart:
    device_id: int
    index: int
    total: int
    seq: int = 0


@dataclass
class DeviceDone:
    result: DeviceResult
    seq: int = 0


@dataclass
class PickLit:
    """The pick walkthrough has lit these slots; the operator is now working.

    One event for the whole batch rather than a start per module: in this run
    mode every slot is waiting at once, and the page has to show that.
    """
    ids: tuple
    total: int
    seq: int = 0


@dataclass
class CheckDone:
    report: "CheckReport"
    seq: int = 0


@dataclass
class CheckReport:
    results: list = field(default_factory=list)
    started: Optional[datetime] = None
    finished: Optional[datetime] = None
    cancelled: bool = False

    @property
    def responded(self) -> list:
        return [r for r in self.results if r.responded]

    @property
    def missing(self) -> list:
        return [r.device_id for r in self.results if not r.responded]

    @property
    def failed(self) -> list:
        return [r.device_id for r in self.results if r.responded and not r.ok]

    @property
    def passed(self) -> bool:
        return (not self.cancelled and bool(self.results)
                and all(r.ok for r in self.results))


def _display_value(device_id: int) -> int:
    """What to show on the 2-digit OLED: the ID itself when it fits (11-98),
    otherwise the column number (IDs above 99 cannot be displayed)."""
    return device_id if device_id <= 99 else device_id % 10


def run_check(ops: FieldOps, cfg: CheckConfig, ids: Sequence[int],
              emit: Callable, cancel: threading.Event) -> CheckReport:
    report = CheckReport(started=datetime.now())
    total = len(ids)
    try:
        for index, device_id in enumerate(ids, 1):
            emit(DeviceStart(device_id, index, total))
            result = DeviceResult(device_id=device_id, responded=False)

            probe = ops.read_reg(device_id, 0)
            if not probe.ok:
                result.steps.append(StepOutcome("answers on the bus", False,
                                                probe.note or "no reply"))
                report.results.append(result)
                emit(DeviceDone(result))
                continue
            result.responded = True
            result.device_type = probe.value
            result.steps.append(StepOutcome("answers on the bus", True,
                                            result.type_name))

            if cfg.light:
                on = ops.write_coil(device_id, 1001, 1)
                ops.sleep(cfg.hold_s)
                off = ops.write_coil(device_id, 1001, 0)
                result.steps.append(StepOutcome(
                    "light on/off (1001)", on.ok and off.ok,
                    on.note or off.note))

            if cfg.display:
                value = _display_value(device_id)
                w = ops.write_reg(device_id, 60, value)
                ops.sleep(INTER_TXN_S)
                on = ops.write_coil(device_id, 1010, 1)
                ops.sleep(cfg.hold_s)
                off = ops.write_coil(device_id, 1010, 0)
                ops.write_reg(device_id, 60, 0)
                result.steps.append(StepOutcome(
                    f"display shows {value} (reg 60 + 1010)",
                    w.ok and on.ok and off.ok, w.note or on.note or off.note))

            if cfg.unlock:
                fire = ops.write_coil(device_id, 1021, 1)
                ops.sleep(max(0.6, cfg.hold_s))     # let the pulse resolve
                ops.write_coil(device_id, 1001, 0)  # 1021 leaves the ring lit
                result.steps.append(StepOutcome("light + unlock (1021)",
                                                fire.ok, fire.note))

            if cfg.identify:
                ident = ops.write_coil(device_id, 509, 1)
                result.steps.append(StepOutcome("identify blink (509)",
                                                ident.ok, ident.note))

            report.results.append(result)
            emit(DeviceDone(result))
    except CheckCancelled:
        report.cancelled = True
    report.finished = datetime.now()
    emit(CheckDone(report))
    return report


# ── Pick-sequence walkthrough ──────────────────────────────────────────────
# The dress rehearsal of the real dispensing flow: light one slot, wait for
# the person at the cabinet to press its front button (module firmware
# v3.2.0+ counts presses at reg 18), turn the light off, move on. The tool
# plays the master's role end-to-end, so it proves lights, buttons, wiring
# and the confirm loop in one walk past the cabinet.

MB_REG_FW = 1
MB_REG_BUTTON_PRESSES = 18
FW_MIN_CONFIRM = 30200          # v3.2.0 — first build that counts presses


@dataclass
class PickConfig:
    preset: int = 1              # enable coil 1000+n lights the slot
    timeout_s: float = 60.0      # for the whole run; 0 = wait until cancelled
    poll_s: float = 0.4          # pause between sweeps of the waiting slots


def _poll_order(ids: Sequence[int]) -> list:
    """Waiting slots, grouped by the hub channel they hang off.

    On a cabinet wired through the RS485 switch hub, the first transaction
    after a channel change costs seconds while the hub settles. Sweeping in
    ID order would pay that on nearly every module; sweeping channel by
    channel pays it once per channel. Where there is no hub the order is
    simply by ID and nothing is lost.
    """
    return sorted(ids, key=lambda i: (hub_channel(i), i))


def run_pick_sequence(ops: FieldOps, cfg: PickConfig, ids: Sequence[int],
                      emit: Callable, cancel: threading.Event) -> CheckReport:
    """Light every selected slot at once, then watch for the confirmations.

    This is how a prescription actually arrives: several slots light
    together and the person picks them in whatever order suits them, each
    light going out as its button is pressed.

    Polling many modules is slower than watching one, and on a hubbed
    cabinet a full sweep can take tens of seconds — but a press is never
    missed, because reg 18 is a cumulative counter rather than a live state.
    A slot pressed early simply goes dark on the sweep that reaches it.
    """
    report = CheckReport(started=datetime.now())
    total = len(ids)
    coil = 1000 + max(1, min(8, cfg.preset))
    waiting: dict = {}           # device_id -> (result, baseline count)
    lit: set = set()

    def finish(result: DeviceResult) -> None:
        report.results.append(result)
        emit(DeviceDone(result))

    try:
        # ── prepare each slot, and light the ones that are ready ───────────
        for index, device_id in enumerate(ids, 1):
            emit(DeviceStart(device_id, index, total))
            result = DeviceResult(device_id=device_id, responded=False)

            probe = ops.read_reg(device_id, 0)
            if not probe.ok:
                result.steps.append(StepOutcome("answers on the bus", False,
                                                probe.note or "no reply"))
                finish(result)
                continue
            result.responded = True
            result.device_type = probe.value
            result.steps.append(StepOutcome("answers on the bus", True,
                                            result.type_name))

            fw = ops.read_reg(device_id, MB_REG_FW)
            if not fw.ok or fw.value < FW_MIN_CONFIRM:
                result.steps.append(StepOutcome(
                    "firmware counts presses (reg 18)", False,
                    f"needs v3.2.0+, module reports {fw.value if fw.ok else '?'}"))
                finish(result)
                continue
            result.steps.append(StepOutcome("firmware counts presses (reg 18)",
                                            True))

            base = ops.read_reg(device_id, MB_REG_BUTTON_PRESSES)
            if not base.ok:
                result.steps.append(StepOutcome("read press counter", False,
                                                base.note))
                finish(result)
                continue

            on = ops.write_coil(device_id, coil, 1)
            if not on.ok:
                result.steps.append(StepOutcome(f"light on ({coil})", False,
                                                on.note))
                finish(result)
                continue
            lit.add(device_id)
            waiting[device_id] = (result, base.value)

        emit(PickLit(tuple(sorted(waiting)), total))

        # ── the human is now part of the loop ──────────────────────────────
        started = time.monotonic()
        while waiting:
            elapsed = time.monotonic() - started
            if cfg.timeout_s > 0 and elapsed >= cfg.timeout_s:
                break
            for device_id in _poll_order(list(waiting)):
                now = ops.read_reg(device_id, MB_REG_BUTTON_PRESSES)
                result, base_count = waiting[device_id]
                if now.ok and now.value != base_count:
                    ops.write_coil(device_id, coil, 0)
                    lit.discard(device_id)
                    del waiting[device_id]
                    result.steps.append(StepOutcome(
                        "confirmed by button press", True,
                        f"after {time.monotonic() - started:.1f}s"))
                    finish(result)
                ops.sleep(INTER_TXN_S)
            ops.sleep(cfg.poll_s)

        # Anything still waiting ran out of time (or the run was cancelled,
        # which lands here through CheckCancelled below).
        for device_id in sorted(waiting):
            result, _ = waiting[device_id]
            result.steps.append(StepOutcome(
                "confirmed by button press", False,
                f"no press within {cfg.timeout_s:.0f}s"))
            finish(result)
        waiting.clear()
    except CheckCancelled:
        report.cancelled = True
        for device_id in sorted(waiting):
            result, _ = waiting[device_id]
            result.steps.append(StepOutcome("confirmed by button press", False,
                                            "cancelled"))
            finish(result)
        waiting.clear()
    finally:
        # However this ended, no slot is left lit with nobody working it.
        for device_id in sorted(lit):
            try:
                ops.write_coil(device_id, coil, 0)
            except CheckCancelled:
                pass                    # already cancelled; keep clearing
    report.finished = datetime.now()
    emit(CheckDone(report))
    return report


def check_csv_bytes(report: CheckReport) -> bytes:
    import csv
    import io
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["device_id", "responded", "device_type", "step", "ok", "note"])
    for r in report.results:
        if not r.steps:
            w.writerow([r.device_id, int(r.responded), r.type_name, "", "", ""])
        for s in r.steps:
            w.writerow([r.device_id, int(r.responded), r.type_name,
                        s.label, int(s.ok), s.note])
    return out.getvalue().encode("utf-8-sig")
