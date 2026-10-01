"""Drive ota_fleet.run_fleet_ota against stub cabinets.

    python tools/ota_fleet_selftest.py

The point of the fleet OTA is wall time: ten cabinets at ~30 min each were
five hours one after another (2026-10-01). So the first case measures it --
three cabinets must take about as long as one, not three times as long --
and the rest pin down what a roll-out has to survive: a cabinet that cannot
be reached, one with another master on it, one that loses a module, the same
gateway listed twice, and Stop.
"""
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import ota, ota_fleet                                    # noqa: E402
from app.soak_fleet import FleetCabinet                           # noqa: E402
from ota_selftest import Device, StubBus                          # noqa: E402

OP_S = 0.004          # every stub transaction costs real time, so walls are measurable
SLEEP_SCALE = 0.01    # the runner's own holds (2 s after ENTER, 5 s apply...) shrunk


class StubCabinet(StubBus):
    """One cabinet's OtaOps, plus the lifecycle the fleet runner asks for."""

    def __init__(self, devices, reachable=True, busy=None):
        super().__init__(devices)
        self.reachable, self.busy = reachable, busy
        self.cancel = None

    def connect(self):
        return self.reachable

    def close(self):
        pass

    def other_master(self, host):
        return self.busy

    def read_regs(self, device_id, addr, count):
        time.sleep(OP_S)
        return super().read_regs(device_id, addr, count)

    def bcast_regs(self, addr, values, log=True):
        time.sleep(OP_S)
        return super().bcast_regs(addr, values, log)

    def sleep(self, seconds):
        end = time.monotonic() + seconds * SLEEP_SCALE
        while time.monotonic() < end:
            if self.cancel is not None and self.cancel.is_set():
                raise ota.OtaCancelled()
            time.sleep(0.001)


IMAGE = bytes(range(256)) * 8            # 2,048 B -> 16 chunks


def fleet(specs, cancel_after=None):
    """specs: name -> StubCabinet. Returns (outcome, events, wall seconds)."""
    cabs = [FleetCabinet(name=n, host=f"10.0.0.{i + 1}",
                         ids=tuple(sorted(s.devs))) for i, (n, s) in enumerate(specs.items())]
    events, cancel = [], threading.Event()
    for s in specs.values():
        s.cancel = cancel
    if cancel_after is not None:
        threading.Timer(cancel_after, cancel.set).start()
    with tempfile.TemporaryDirectory() as tmp:
        t0 = time.monotonic()
        out = ota_fleet.run_fleet_ota(cabs, IMAGE, "fw.bin", events.append, cancel,
                                      Path(tmp), ops_factory=lambda cab, _c: specs[cab.name])
        wall = time.monotonic() - t0
        files = sorted(p.name for p in Path(tmp).iterdir())
        verdict_on_disk = bool(out) and Path(out.path).is_file() and \
            Path(out.path).read_text(encoding="utf-8") == out.text
    return out, events, wall, files, verdict_on_disk


def main() -> int:
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
        failures += not cond

    # 1. wall time: one cabinet, then three at once
    one, _, wall1, _, _ = fleet({"A": StubCabinet([Device(11), Device(12)])})
    check("single cabinet updates", one is not None and one.rows[0].state == "done",
          one.rows[0].state if one else "no outcome")
    devs = {n: [Device(11), Device(12)] for n in ("A", "B", "C")}
    out, events, wall3, files, on_disk = fleet({n: StubCabinet(d) for n, d in devs.items()})
    check("three cabinets: all done", all(r.state == "done" for r in out.rows),
          str([(r.name, r.state) for r in out.rows]))
    check("three cabinets: every module really runs the new fw",
          all(d.fw == 30400 for ds in devs.values() for d in ds))
    check(f"three cabinets side by side: {wall3:.2f} s against {wall1:.2f} s for one",
          wall3 < 1.8 * wall1, f"wall3={wall3:.2f} wall1={wall1:.2f}")
    check("the verdict is on disk and says 3 of 3",
          on_disk and "3 of 3 cabinets fully updated" in out.text, out.text)
    check("each cabinet wrote its own log",
          sum(f.startswith("ota-") and f.endswith(".log") for f in files) == 3, str(files))
    check("census read back after the run", all(r.census == "30400 x2" for r in out.rows),
          str([r.census for r in out.rows]))
    check("nothing left behind", out.leftovers() == [], str(out.leftovers()))
    lines = [e for e in events if isinstance(e, ota_fleet.FleetOtaEvent)]
    check("log lines carry the time they happened",
          lines and all(len(e.when) == 8 and e.when[2] == ":" for e in lines),
          str([e.when for e in lines][:3]))
    check("exactly one FleetOtaFinished, last",
          sum(isinstance(e, ota_fleet.FleetOtaFinished) for e in events) == 1
          and isinstance(events[-1], ota_fleet.FleetOtaFinished))

    # 2. the same gateway twice: refused before any socket opens
    s = StubCabinet([Device(11)])
    cabs = [FleetCabinet("X", "10.0.0.9", (11,)), FleetCabinet("Y", "10.0.0.9", (11,))]
    ev = []
    res = ota_fleet.run_fleet_ota(cabs, IMAGE, "fw.bin", ev.append, threading.Event(),
                                  Path(tempfile.gettempdir()), ops_factory=lambda c, _x: s)
    check("duplicate gateway: refused up front", res is None and s.devs[11].fw == 30302
          and any("listed twice" in e.text for e in ev), str([e.text for e in ev]))

    # 3. unreachable, busy and a lost module, next to a healthy cabinet
    good = [Device(11), Device(12)]
    lossy = [Device(11), Device(12, drop_after_stream=2)]      # drops on the retry too
    out, events, _, _, _ = fleet({
        "good": StubCabinet(good),
        "dark": StubCabinet([Device(11)], reachable=False),
        "busy": StubCabinet([Device(11)], busy="192.168.0.87:51377"),
        "lossy": StubCabinet(lossy),
    })
    by = {r.name: r for r in out.rows}
    check("a healthy cabinet is not held back by the others", by["good"].state == "done"
          and all(d.fw == 30400 for d in good))
    check("unreachable cabinet: refused, named", by["dark"].state == "refused"
          and "cannot reach" in by["dark"].note, by["dark"].note)
    check("another master: refused with the peer named", by["busy"].state == "refused"
          and "192.168.0.87" in by["busy"].note, by["busy"].note)
    check("lost module: cabinet incomplete, the id named", by["lossy"].state == "incomplete"
          and by["lossy"].left == (12,), f"{by['lossy'].state} {by['lossy'].left}")
    left = {c.name: c.ids for c in out.leftovers()}
    check("re-run list: the lost id, and whole cabinets that never ran",
          left == {"dark": (11,), "busy": (11,), "lossy": (12,)}, str(left))
    check("the verdict counts 1 of 4", "1 of 4 cabinets fully updated" in out.text, out.text)

    # 4. Stop: every cabinet ends, none of them claims to be done
    slow = {n: [Device(11), Device(12)] for n in ("A", "B")}
    out, events, wall, _, _ = fleet({n: StubCabinet(d) for n, d in slow.items()},
                                    cancel_after=0.05)
    check("stop: the run ends and no cabinet says done",
          out is not None and all(r.state == "cancelled" for r in out.rows),
          str([(r.name, r.state) for r in out.rows]) if out else "no outcome")

    # 5. progress bookkeeping a page can draw from
    st = ota_fleet.CabStatus("A", "h", 64, state="running", channel=3, channels=8,
                             phase="stream", pct=50)
    check("progress: 2.5 of 8 groups", abs(st.fraction - 2.5 / 8) < 1e-9, str(st.fraction))
    check("channel count follows the gateway's map",
          ota_fleet.count_channels((11, 21, 41, 51, 61, 71), "1,2,3,4,4,5,5,6,7,8") == 4
          and ota_fleet.count_channels((11, 21), None) == 2)

    print(f"\n{'ALL PASS' if not failures else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
