"""Firmware survey — what version is every module in the cabinet running?

Before an update it answers "who still needs it", and after one "did they all
take it". Both questions used to mean reading one module at a time in the
Monitor tab and writing the answers down.

Deliberately read-only: one FC03 of two registers per module, no coils, no
writes. Running it on a live cabinet must be as harmless as looking at it.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Protocol, Sequence

from .lgs_map import DEVICE_TYPES, INTER_TXN_S, fw_short, join_uid

REG_DEVICE_TYPE = 0
REG_FIRMWARE = 1

# Sorts below every real version, so silent modules land last in the groups.
SILENT = -1


class SurveyOps(Protocol):
    """The worker facade, with the device id per call."""

    def read_regs(self, device_id: int, addr: int, count: int): ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class ModuleFirmware:
    device_id: int
    responded: bool = False
    raw: int = 0
    device_type: int = -1
    note: str = ""

    @property
    def version(self) -> str:
        return fw_short(self.raw) if self.responded else ""

    @property
    def type_name(self) -> str:
        return DEVICE_TYPES.get(self.device_type, "?") if self.responded else ""

    @property
    def sort_key(self) -> int:
        return self.raw if self.responded else SILENT


@dataclass
class VersionGroup:
    """The modules that share one firmware version (or that stayed silent)."""
    label: str
    ids: tuple
    raw: int                      # SILENT for the no-answer group

    @property
    def silent(self) -> bool:
        return self.raw == SILENT

    @property
    def count(self) -> int:
        return len(self.ids)


@dataclass
class SurveyReport:
    started: datetime
    finished: Optional[datetime] = None
    results: list = field(default_factory=list)
    cancelled: bool = False

    def groups(self) -> list:
        """Newest firmware first, silent modules last.

        Grouping by the raw register rather than the printed version keeps two
        builds that merely print alike from merging — the raw value is what
        the module actually reports.
        """
        buckets: dict = {}
        for r in self.results:
            buckets.setdefault(r.sort_key, []).append(r.device_id)
        out = [VersionGroup(label=("no answer" if raw == SILENT else fw_short(raw)),
                            ids=tuple(sorted(ids)), raw=raw)
               for raw, ids in buckets.items()]
        out.sort(key=lambda g: (g.raw == SILENT, -g.raw))
        return out

    @property
    def answered(self) -> int:
        return sum(1 for r in self.results if r.responded)

    def summary(self) -> str:
        parts = [f"{g.label} x{g.count}" for g in self.groups()]
        return " · ".join(parts) if parts else "nothing surveyed"


@dataclass
class SurveyProgress:
    device_id: int
    index: int
    total: int
    seq: int = 0


@dataclass
class SurveyRead:
    result: ModuleFirmware
    seq: int = 0


@dataclass
class SurveyDone:
    report: SurveyReport
    seq: int = 0


@dataclass
class ReportSurveyDone:
    """End of a site-report sweep — carries the records themselves."""
    records: list
    cancelled: bool = False
    seq: int = 0


@dataclass
class ModuleRecord:
    """One module's identity, as the site report prints it.

    Everything comes from ONE FC03 of registers 0-17 — device type, firmware,
    hardware, baud, slave id, boot counter, health, and the chip UID — so a
    64-module cabinet costs 64 transactions, hub crossings included.
    """
    device_id: int
    responded: bool = False
    device_type: int = -1
    fw_raw: int = 0
    hw_raw: int = 0
    baud_raw: int = 0
    reported_id: int = -1
    boots: int = 0
    health: int = 0
    uid: str = ""
    note: str = ""

    @property
    def fw(self) -> str:
        return fw_short(self.fw_raw) if self.responded else ""

    @property
    def type_name(self) -> str:
        return DEVICE_TYPES.get(self.device_type, "?") if self.responded else ""


def read_module_record(ops: SurveyOps, device_id: int) -> ModuleRecord:
    """Registers 0-17 in one transaction; silence leaves a not-responded row."""
    rec = ModuleRecord(device_id=device_id)
    res = ops.read_regs(device_id, 0, 18)
    values = res.value if isinstance(res.value, (list, tuple)) else None
    if res.ok and values and len(values) >= 18:
        rec.responded = True
        rec.device_type = int(values[0])
        rec.fw_raw = int(values[1])
        rec.hw_raw = int(values[2])
        rec.baud_raw = int(values[3])
        rec.reported_id = int(values[4])
        rec.boots = int(values[7])
        rec.health = int(values[9])
        rec.uid = join_uid(values[12:18])
    else:
        rec.note = res.note or "no reply"
    return rec


def run_report_survey(ops: SurveyOps, ids: Sequence[int], emit: Callable,
                      cancel: threading.Event) -> list:
    """The site report's sweep: one ModuleRecord per slot, in slot order.

    Reuses the survey event stream so the page shows the same progress a
    firmware survey does; SurveyRead is not emitted (the records carry more
    than ModuleFirmware and go back as the return value instead).
    """
    records: list = []
    total = len(ids)
    cancelled = False
    for index, device_id in enumerate(ids, 1):
        if cancel.is_set():
            cancelled = True
            break
        emit(SurveyProgress(device_id, index, total))
        records.append(read_module_record(ops, device_id))
        ops.sleep(INTER_TXN_S)
    emit(ReportSurveyDone(records=records, cancelled=cancelled))
    return records


def run_survey(ops: SurveyOps, ids: Sequence[int], emit: Callable,
               cancel: threading.Event) -> SurveyReport:
    report = SurveyReport(started=datetime.now())
    total = len(ids)
    for index, device_id in enumerate(ids, 1):
        if cancel.is_set():
            report.cancelled = True
            break
        emit(SurveyProgress(device_id, index, total))
        entry = ModuleFirmware(device_id=device_id)
        # Type and version are adjacent, so one transaction answers both —
        # worth caring about on a bus where a hub channel change costs
        # seconds, not milliseconds.
        res = ops.read_regs(device_id, REG_DEVICE_TYPE, 2)
        values = res.value if isinstance(res.value, (list, tuple)) else None
        if res.ok and values and len(values) >= 2:
            entry.responded = True
            entry.device_type = int(values[REG_DEVICE_TYPE])
            entry.raw = int(values[REG_FIRMWARE])
        else:
            entry.note = res.note or "no reply"
        report.results.append(entry)
        emit(SurveyRead(entry))
        ops.sleep(INTER_TXN_S)
    report.finished = datetime.now()
    emit(SurveyDone(report))
    return report
