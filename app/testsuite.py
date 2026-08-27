"""Automated R5.0 test sweep — library port of LGS-Standard-Module
tools/test_modbus_rtu.py, driven through a ModbusOps binder with progress
events and cooperative cancel.

Deliberate differences from the CLI original:
- Danger coils (500-504, 510) never appear: the persist/reboot validation
  checks and the coil-500 canary are dropped (VALIDATE keeps only the
  non-reboot guards).
- The latch phase is opt-in via SweepConfig (the GUI shows the fire count).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional, Protocol

from .lgs_map import (INTER_TXN_S, LATCH_COOLDOWN_S, coil_enable, dec_plain,
                      preset_cfg_base, REGISTERS, COILS, CoilClass)


class SweepCancelled(Exception):
    pass


class ModbusOps(Protocol):
    def read_reg(self, addr: int): ...
    def read_coil(self, addr: int): ...
    def write_reg(self, addr: int, value: int): ...
    def write_coil(self, addr: int, value: int): ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class SweepConfig:
    loops: int = 1
    include_led: bool = True          # PRESET + DISPLAY + LED phases
    include_latch: bool = False       # physical solenoid!
    latch_fires: int = 1
    include_force: bool = True        # coil 1019
    include_combos: bool = False      # coils 1022 + 1031
    include_1021: bool = False        # coil 1021

    def latch_total_fires(self) -> int:
        if not self.include_latch:
            return 0
        per_loop = self.latch_fires + (1 if self.include_force else 0) \
            + (2 if self.include_combos else 0) + (1 if self.include_1021 else 0)
        return per_loop * self.loops

    def phase_names(self) -> list[str]:
        names = ["READ", "WRITE", "VALIDATE"]
        if self.include_led:
            names += ["PRESET", "DISPLAY", "LED"]
        if self.include_latch:
            names.append("LATCH")
        return names


@dataclass
class StepResult:
    ts: datetime
    phase: str
    fc: int
    addr: int
    name: str
    op: str
    raw: object
    decoded: str
    expected: object
    result: str                       # OK | FAIL | ERR
    latency_ms: float
    note: str = ""


@dataclass
class PhaseStats:
    ok: int = 0
    fail: int = 0
    err: int = 0

    def add(self, result: str) -> None:
        if result == "OK":
            self.ok += 1
        elif result == "FAIL":
            self.fail += 1
        else:
            self.err += 1


@dataclass
class PhaseStart:
    name: str
    index: int
    total: int
    seq: int = 0


@dataclass
class Step:
    step: StepResult
    seq: int = 0


@dataclass
class PhaseEnd:
    name: str
    stats: PhaseStats
    seq: int = 0


@dataclass
class Done:
    report: "SweepReport"
    seq: int = 0


@dataclass
class SweepReport:
    steps: list = field(default_factory=list)
    per_phase: dict = field(default_factory=dict)
    started: Optional[datetime] = None
    finished: Optional[datetime] = None
    cancelled: bool = False

    @property
    def totals(self) -> PhaseStats:
        t = PhaseStats()
        for s in self.per_phase.values():
            t.ok += s.ok
            t.fail += s.fail
            t.err += s.err
        return t

    @property
    def passed(self) -> bool:
        t = self.totals
        return not self.cancelled and t.fail == 0 and t.err == 0


# Safe register write tests: (addr, name, test_value, verify_addr). Globals
# 190/194 are excluded here (they fan out) — PRESET tests them with snapshots.
WRITE_TESTS = (
    (60,  "Display Number",   45,   60),
    (80,  "Unlock Delay",     250,  80),
    (110, "Preset 1 Brightness", 50, 110),
    (111, "Preset 1 Red",     11,  111),
    (112, "Preset 1 Green",   22,  112),
    (113, "Preset 1 Blue",    33,  113),
    (114, "Preset 1 Max On",  1800, 114),
)

STATE_COILS = (
    (1001, "Enable Preset 1"),
    (1010, "Display Enable"),
    (1011, "Preset 1 + Display"),
)


class _Runner:
    def __init__(self, ops: ModbusOps, cfg: SweepConfig,
                 emit: Callable, cancel: threading.Event) -> None:
        self.ops = ops
        self.cfg = cfg
        self.emit = emit
        self.cancel = cancel
        self.report = SweepReport(started=datetime.now())
        self.phase = ""

    # ── helpers ────────────────────────────────────────────────────────────
    def _record(self, fc: int, addr: int, name: str, op: str, raw, decoded: str,
                expected, result: str, latency: float, note: str = "") -> None:
        step = StepResult(datetime.now(), self.phase, fc, addr, name, op, raw,
                          decoded, expected, result, latency, note)
        self.report.steps.append(step)
        self.report.per_phase.setdefault(self.phase, PhaseStats()).add(result)
        self.emit(Step(step))

    def _check(self, cond: bool, label: str, fc: int, addr: int, name: str,
               raw, expected) -> None:
        self._record(fc, addr, name, "check", raw, label, expected,
                     "OK" if cond else "FAIL", 0.0)

    def _pace(self) -> None:
        self.ops.sleep(INTER_TXN_S)

    def _reg(self, addr: int):
        res = self.ops.read_reg(addr)
        return res.value if res.ok else None

    # ── phases ─────────────────────────────────────────────────────────────
    def phase_read(self) -> None:
        for r in REGISTERS:
            res = self.ops.read_reg(r.addr)
            if res.ok:
                self._record(3, r.addr, r.name, "read", res.value,
                             r.decoder(res.value, r.unit), "", "OK", res.latency_ms)
            else:
                self._record(3, r.addr, r.name, "read", None, "", "", "ERR",
                             res.latency_ms, res.note)
            self._pace()
        for c in COILS:
            if c.cls is CoilClass.FORBIDDEN:
                continue                                   # skip OTA coils even for reads
            res = self.ops.read_coil(c.addr)
            if res.ok:
                self._record(1, c.addr, c.name, "read", res.value,
                             f"coil={res.value}", "", "OK", res.latency_ms)
            else:
                self._record(1, c.addr, c.name, "read", None, "", "", "ERR",
                             res.latency_ms, res.note)
            self._pace()

    def phase_write(self) -> None:
        targets = sorted({v for *_x, v in WRITE_TESTS} | {a for a, *_x in WRITE_TESTS})
        original = {a: self._reg(a) for a in targets}
        for addr, name, test_val, vaddr in WRITE_TESTS:
            w = self.ops.write_reg(addr, test_val)
            if not w.ok:
                self._record(6, addr, name, "write", test_val, "", test_val, "ERR",
                             w.latency_ms, w.note)
                self._pace()
                continue
            self._pace()
            r = self.ops.read_reg(vaddr)
            if not r.ok:
                self._record(3, vaddr, name, "verify", None, "", test_val, "ERR",
                             r.latency_ms, r.note)
            elif r.value == test_val:
                self._record(3, vaddr, name, "verify", r.value, "echo", test_val,
                             "OK", r.latency_ms)
            else:
                self._record(3, vaddr, name, "verify", r.value, "mismatch", test_val,
                             "FAIL", r.latency_ms)
            self._pace()
        for a in targets:
            if original[a] is not None:
                self.ops.write_reg(a, original[a])
                self._pace()

        for addr, name in STATE_COILS:
            r0 = self.ops.read_coil(addr)
            orig = r0.value if r0.ok else None
            target = 0 if orig == 1 else 1
            w = self.ops.write_coil(addr, target)
            self._pace()
            r = self.ops.read_coil(addr)
            if w.ok and r.ok and r.value == target:
                self._record(1, addr, name, "coil-verify", r.value, f"coil={r.value}",
                             target, "OK", r.latency_ms)
            elif not w.ok:
                self._record(5, addr, name, "coil", target, "", target, "ERR",
                             w.latency_ms, w.note)
            else:
                self._record(1, addr, name, "coil-verify", r.value, "mismatch",
                             target, "FAIL", r.latency_ms, r.note)
            if orig is not None:
                self.ops.write_coil(addr, orig)
                self._pace()

    def phase_validate(self) -> None:
        """Non-reboot range guards only (persist/reboot checks are GUI-excluded)."""
        orig80 = self._reg(80)
        self.ops.write_reg(80, 9000)
        self.ops.sleep(0.1)
        rb = self._reg(80)
        self._check(rb == 8000, f"reg 80 = 9000 clamps to 8000 (readback {rb})",
                    3, 80, "Unlock Delay", rb, 8000)
        if orig80 is not None:
            self.ops.write_reg(80, orig80)
        self._pace()

        origb = {n: self._reg(preset_cfg_base(n)) for n in range(1, 9)}
        self.ops.write_reg(190, 150)
        self.ops.sleep(0.1)
        rb190, rb110 = self._reg(190), self._reg(110)
        self._check(rb190 == 100 and rb110 == 100,
                    f"reg 190 = 150 clamps to 100 + fans out (190={rb190}, 110={rb110})",
                    3, 190, "Global Brightness", rb190, 100)
        for n in range(1, 9):
            if origb[n] is not None:
                self.ops.write_reg(preset_cfg_base(n), origb[n])
                self._pace()

        self.ops.write_coil(1003, 1)
        self._pace()
        self.ops.write_coil(1010, 1)
        self._pace()
        self.ops.write_coil(511, 1)
        self.ops.sleep(0.3)
        c1003 = self.ops.read_coil(1003).value
        c1010 = self.ops.read_coil(1010).value
        self._check(c1003 == 0 and c1010 == 0,
                    f"coil 511 All Off cleared ring+display (1003={c1003}, 1010={c1010})",
                    1, 511, "All Off", c1003, 0)

        self.ops.write_coil(509, 1)
        self.ops.sleep(0.3)
        c509 = self.ops.read_coil(509).value
        self._check(c509 == 0, "coil 509 Identify accepted + self-cleared (blinks white ~5s)",
                    1, 509, "Identify", c509, 0)

    def phase_preset(self) -> None:
        self.ops.write_coil(1001, 1)
        self._pace()
        c1 = self.ops.read_coil(1001).value
        self._check(c1 == 1, "enable 1001 -> ring red", 1, 1001, "Enable Preset 1", c1, 1)
        self.ops.sleep(0.8)

        self.ops.write_coil(1003, 1)
        self._pace()
        c3 = self.ops.read_coil(1003).value
        c1 = self.ops.read_coil(1001).value
        self._check(c3 == 1, "enable 1003 -> ring blue", 1, 1003, "Enable Preset 3", c3, 1)
        self._check(c1 == 0, "radio: coil 1001 auto-cleared after enabling 1003",
                    1, 1001, "Enable Preset 1", c1, 0)
        self.ops.sleep(0.8)

        for gaddr, gname, offset, test_val in ((190, "Global Brightness", 0, 37),
                                               (194, "Global Max On-Time", 4, 2400)):
            orig = {}
            for n in range(1, 9):
                orig[n] = self._reg(preset_cfg_base(n) + offset)
                self._pace()
            self.ops.write_reg(gaddr, test_val)
            self._pace()
            fanout_ok = True
            for n in range(1, 9):
                if self._reg(preset_cfg_base(n) + offset) != test_val:
                    fanout_ok = False
                self._pace()
            self._check(fanout_ok, f"reg {gaddr} = {test_val} fanned out to all 8 presets",
                        3, gaddr, gname, test_val if fanout_ok else -1, test_val)
            for n in range(1, 9):
                if orig[n] is not None:
                    self.ops.write_reg(preset_cfg_base(n) + offset, orig[n])
                    self._pace()

        self.ops.write_coil(1003, 0)
        self._pace()
        c3 = self.ops.read_coil(1003).value
        self._check(c3 == 0, "disable 1003 -> ring off", 1, 1003, "Enable Preset 3", c3, 0)

    def phase_display(self) -> None:
        self.ops.write_reg(60, 45)
        self._pace()
        self.ops.write_coil(1010, 1)
        self._pace()
        c = self.ops.read_coil(1010).value
        self._check(c == 1, "coil 1010 on -> OLED shows '45'", 1, 1010, "Display Enable", c, 1)
        self.ops.sleep(1.5)

        self.ops.write_reg(60, 7)
        self.ops.sleep(1.2)                                # visible re-render '07'

        self.ops.write_reg(60, 1234)
        self.ops.sleep(0.1)
        rb = self._reg(60)
        # fw >= v3.4.0 renders three digits and clamps at 999; earlier
        # firmware clamps at 99. Ask the module which contract it carries so
        # the same suite passes on a mixed bench.
        fw = self._reg(1)
        cap = 999 if (fw or 0) >= 30400 else 99
        self._check(rb == cap, f"reg 60 = 1234 clamps (readback {rb}, OLED '{cap}')",
                    3, 60, "Display Number", rb, cap)
        self.ops.sleep(1.2)

        self.ops.write_coil(1010, 0)
        self._pace()
        c = self.ops.read_coil(1010).value
        self._check(c == 0, "coil 1010 off -> OLED blank", 1, 1010, "Display Enable", c, 0)
        self.ops.write_reg(60, 0)
        self._pace()

    def phase_led(self) -> None:
        orig = {a: self._reg(a) for a in (110, 111, 112, 113)}
        r_en = self.ops.read_coil(1001)
        orig_en = r_en.value if r_en.ok else None

        self.ops.write_coil(1001, 0)
        self._pace()
        for addr, val in ((110, 60), (111, 0), (112, 0), (113, 255)):
            self.ops.write_reg(addr, val)
            self._pace()

        w = self.ops.write_coil(1001, 1)
        self._pace()
        r = self.ops.read_coil(1001)
        if w.ok and r.ok and r.value == 1:
            self._record(1, 1001, "Enable Preset 1", "on", r.value, "ring BLUE", 1,
                         "OK", r.latency_ms)
        else:
            self._record(1, 1001, "Enable Preset 1", "on", r.value, "", 1, "FAIL",
                         r.latency_ms, w.note or r.note)
        self.ops.sleep(1.5)

        self.ops.write_coil(1001, 0)
        self._pace()
        for a, v in orig.items():
            if v is not None:
                self.ops.write_reg(a, v)
                self._pace()
        if orig_en:
            self.ops.write_coil(1001, orig_en)
            self._pace()

    def _fire_latch(self, coil: int, name: str) -> None:
        t40_before = self._reg(40)
        w = self.ops.write_coil(coil, 1)
        if not w.ok:
            self._record(5, coil, name, "fire", 1, "", "", "ERR", w.latency_ms, w.note)
            return
        t0 = time.monotonic()
        cleared_ms = None
        last = 1
        while time.monotonic() - t0 < 1.5:
            r = self.ops.read_coil(coil)
            if r.ok:
                last = r.value
                if r.value == 0:
                    cleared_ms = (time.monotonic() - t0) * 1000.0
                    break
            self.ops.sleep(0.02)
        t40_after = self._reg(40)
        if cleared_ms is not None:
            hint = ("pulsed" if cleared_ms > 150
                    else "accepted; no pulse (sense guard: latch not locked)")
            self._record(1, coil, name, "fire", 0, f"cleared {cleared_ms:.0f}ms — {hint}",
                         "self-clear", "OK", w.latency_ms,
                         f"reg40 {t40_before}->{t40_after}")
        else:
            self._record(1, coil, name, "fire", last, "no self-clear", "self-clear",
                         "FAIL", w.latency_ms)

    def phase_latch(self) -> None:
        cfg = self.cfg
        for n in range(cfg.latch_fires):
            self._fire_latch(1020, "Safety Trigger")
            more = (n < cfg.latch_fires - 1 or cfg.include_force
                    or cfg.include_combos or cfg.include_1021)
            if more:
                self.ops.sleep(LATCH_COOLDOWN_S)
        if cfg.include_force:
            self._fire_latch(1019, "Force Trigger")
            if cfg.include_combos or cfg.include_1021:
                self.ops.sleep(LATCH_COOLDOWN_S)
        if cfg.include_combos:
            self._fire_latch(1022, "Preset 2 + Latch")
            self.ops.sleep(0.3)
            c = self.ops.read_coil(coil_enable(2)).value
            self._check(c == 1, "enable coil 1002 synced after 1022 resolved",
                        1, 1002, "Enable Preset 2", c, 1)
            self.ops.write_coil(coil_enable(2), 0)
            self.ops.sleep(LATCH_COOLDOWN_S)

            self._fire_latch(1031, "Preset 1 + Latch + Display")
            self.ops.sleep(0.3)
            d = self.ops.read_coil(1010).value
            e = self.ops.read_coil(1001).value
            m = self.ops.read_coil(1011).value
            self._check(d == 1, "display coil 1010 turned on by 1031 combo",
                        1, 1010, "Display Enable", d, 1)
            self._check(e == 1, "enable coil 1001 synced after 1031 resolved",
                        1, 1001, "Enable Preset 1", e, 1)
            self._check(m == 1, "state combo 1011 mirrored by 1031",
                        1, 1011, "Preset 1 + Display", m, 1)
            self.ops.sleep(1.0)
            self.ops.write_coil(1011, 0)
            self.ops.sleep(0.3)
            e = self.ops.read_coil(1001).value
            d = self.ops.read_coil(1010).value
            self._check(e == 0 and d == 0,
                        f"single 1011=0 shut ring AND display (1001={e}, 1010={d})",
                        1, 1011, "Preset 1 + Display", e, 0)
            if cfg.include_1021:
                self.ops.sleep(LATCH_COOLDOWN_S)
        if cfg.include_1021:
            self._fire_latch(1021, "Preset 1 + Latch")
            self.ops.sleep(0.2)
            self.ops.write_coil(1001, 0)                   # 1021 leaves the ring on

    # ── run ────────────────────────────────────────────────────────────────
    def run(self) -> SweepReport:
        phase_fns = {"READ": self.phase_read, "WRITE": self.phase_write,
                     "VALIDATE": self.phase_validate, "PRESET": self.phase_preset,
                     "DISPLAY": self.phase_display, "LED": self.phase_led,
                     "LATCH": self.phase_latch}
        names = self.cfg.phase_names()
        try:
            for loop in range(self.cfg.loops):
                for i, name in enumerate(names):
                    self.phase = name
                    self.emit(PhaseStart(name, loop * len(names) + i + 1,
                                         len(names) * self.cfg.loops))
                    phase_fns[name]()
                    self.emit(PhaseEnd(name, self.report.per_phase.get(name, PhaseStats())))
        except SweepCancelled:
            self.report.cancelled = True
            self._epilogue()
        self.report.finished = datetime.now()
        self.emit(Done(self.report))
        return self.report

    def _epilogue(self) -> None:
        """Best-effort: leave the device dark after a cancel."""
        try:
            for addr in (1001, 1010):
                self.ops.write_coil(addr, 0)
        except Exception:                                  # noqa: BLE001
            pass


def run_sweep(ops: ModbusOps, cfg: SweepConfig, emit: Callable,
              cancel: threading.Event) -> SweepReport:
    return _Runner(ops, cfg, emit, cancel).run()


def sweep_csv_bytes(report: SweepReport) -> bytes:
    import csv
    import io
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["timestamp", "phase", "fc", "addr", "name", "op", "raw",
                "decoded", "expected", "result", "latency_ms", "note"])
    for s in report.steps:
        w.writerow([s.ts.isoformat(timespec="milliseconds"), s.phase, s.fc, s.addr,
                    s.name, s.op, s.raw, s.decoded, s.expected, s.result,
                    f"{s.latency_ms:.1f}", s.note])
    return out.getvalue().encode("utf-8-sig")
