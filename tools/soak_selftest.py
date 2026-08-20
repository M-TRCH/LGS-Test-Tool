"""Drive run_soak against a scripted stub bus and check what it writes.

    python tools/soak_selftest.py

This exists because of a real failure. `_counters` read the IWDG counter with
a one-register read, which comes back as a bare int rather than a list of one,
and the code tested for a list before taking element 0 -- so the reading was
always None, the watchdog comparison could never fire, and an overnight run
that logged 308 reboots reported `wdt=0`. That reads as "clean power cycles",
the exact opposite of the truth, and it was used to reason about a cabinet's
power fault for a day before anyone checked it against the hardware.

A silent zero in a results column is worse than a crash, and no amount of
staring at the code catches one. So the rule these cases encode is: every
reboot the soak reports must say what kind of reboot it was, and each of the
three answers must be distinguishable from the other two.
"""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import soak                                              # noqa: E402


class Reply:
    """The shape modbus_worker hands back: scalar for count=1, list above."""

    def __init__(self, value, ok=True, note=""):
        self.ok = ok
        self.value = value
        self.latency_ms = 5.0
        self.note = note
        self.link_down = False


class StubBus:
    """One module that reboots once, on command, in a chosen way."""

    def __init__(self, kind: str):
        self.kind = kind            # watchdog | clean | unread
        self.boots = 100
        self.iwdg = 7
        self.cause = 0
        self.rebooted = False

    def read_regs(self, device_id: int, addr: int, count: int):
        if addr == 0:
            regs = [20, 30301, 51] + [0] * 21
            regs[soak.REG_BOOTS] = self.boots
            regs[soak.REG_RESET_CAUSE] = self.cause
            return Reply(regs[:count])
        if addr == soak.REG_STATS2_IWDG:
            if self.kind == "unread" and self.rebooted:
                return Reply(None, ok=False, note="timeout")
            return Reply(self.iwdg)         # count=1: a bare int, not [int]
        return Reply([0] * count)

    def sleep(self, seconds: float) -> None:
        pass

    def reboot(self):
        self.rebooted = True
        self.boots += 1
        if self.kind == "watchdog":
            self.iwdg += 1
            self.cause = 1 << 0             # reg 8 bit0 = IWDG
        else:
            self.cause = 1 << 2             # reg 8 bit2 = power-on


def run(kind: str) -> list[str]:
    bus = StubBus(kind)
    rows: list[str] = []
    cancel = threading.Event()
    seen = {"passes": 0}

    def emit(event):
        if isinstance(event, soak.SoakTick):
            seen["passes"] += 1
            if seen["passes"] == 1:
                bus.reboot()                # between the baseline and pass 2
            else:
                cancel.set()

    soak.run_soak(bus, soak.SoakConfig(ids=(11,), pass_gap_s=0, counter_every=1),
                  emit, cancel, rows.append)
    return [r.split(",", 2)[2] for r in rows if ",reboot," in r or ",watchdog," in r]


CASES = (
    # kind,      must appear in the reboot row,          extra watchdog row?
    ("watchdog", ("cause=IWDG", "iwdg 7 -> 8"), True),
    ("clean",    ("cause=Power-on", "iwdg 7 unchanged"), False),
    ("unread",   ("cause=Power-on", "iwdg unread"), False),
)


def main() -> int:
    failures = 0
    for kind, wanted, want_watchdog_row in CASES:
        lines = run(kind)
        reboot = next((l for l in lines if l.startswith("reboot,")), None)
        watchdog = any(l.startswith("watchdog,") for l in lines)
        problems = []
        if reboot is None:
            problems.append("no reboot row at all")
        else:
            for token in wanted:
                if token not in reboot:
                    problems.append(f"missing {token!r}")
            if "," in reboot.split(",", 1)[1]:
                problems.append("detail contains a comma (breaks the 4-column CSV)")
        if watchdog != want_watchdog_row:
            problems.append(f"watchdog row {'missing' if want_watchdog_row else 'unexpected'}")

        print(f"{kind:9} {'FAIL' if problems else 'ok  '}  {reboot or ''}")
        for p in problems:
            print(f"            - {p}")
        failures += bool(problems)

    print(f"\n{len(CASES) - failures}/{len(CASES)} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
