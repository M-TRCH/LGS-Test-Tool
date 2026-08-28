"""Drive run_ota against scripted stub devices and check who gets salvaged.

    python tools/ota_selftest.py

This exists because of a real fleet failure (2026-08-27): seven devices on
one hub channel, and partway through the stream some of them hit their 30 s
session timeout and dropped to "failed" — after which they ignore every
chunk. The repair loop never read the OTA state, so a dropped device printed
as "missing N chunks", the rounds re-sent whole images to devices that were
not listening (five 470-chunk rounds, 545 s), and when the rounds ran out
the run threw away the image of a device that had COMPLETED in round one.

The rules these cases pin down: a device that left the session is named
(with its own error code) and stops costing air time; devices that
completed are finalized and applied anyway; chunks are only re-sent for
devices still listening.
"""
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import ota                                               # noqa: E402


class Reply:
    def __init__(self, value=None, ok=True):
        self.ok, self.value = ok, value
        self.latency_ms, self.note = 1.0, ""


class Device:
    def __init__(self, uid, miss_first=0, drop_after_stream=False):
        self.uid = uid
        self.fw = 30302
        self.state, self.err = 0, 0          # 0 idle, 1 receiving, 2 verified, 3 failed
        self.chunks: set = set()
        self.total = 0
        self.miss_first = miss_first         # chunks to drop during the first stream
        self.drop_after_stream = drop_after_stream
        self.streamed = 0                    # frames seen while receiving


class StubBus:
    """OtaOps over a handful of scripted devices on one 'channel'."""

    def __init__(self, devices, hub=False):
        self.devs = {d.uid: d for d in devices}
        self.meta = [0] * 5
        self.resent: list = []               # chunk idx re-sent after the stream
        self.streaming_done = False
        # hub=True behaves like the real gateway: a broadcast (slave id 0) is
        # NOT a channel switch, so it only reaches whichever channel a unicast
        # last parked the hub on. Without modelling that, the stub cheerfully
        # passed a whole-cabinet OTA that cannot work on the bench.
        self.hub = hub
        self.parked = None

    def _reachable(self):
        if not self.hub:
            return list(self.devs.values())
        return [d for d in self.devs.values() if d.uid // 10 == self.parked]

    # ── OtaOps ─────────────────────────────────────────────────────────
    def read_regs(self, device_id, addr, count):
        d = self.devs[device_id]
        self.parked = device_id // 10        # a unicast parks the hub
        if addr == 0:
            return Reply([20, d.fw, 510][:count])
        if addr == 1:
            return Reply(d.fw)
        if addr == ota.REG_STATE:
            return Reply([d.state | (d.err << 8), len(d.chunks)][:count])
        if addr == ota.REG_BITMAP_FIRST:
            regs = [0] * count
            for i in d.chunks:
                regs[i // 16] |= 1 << (i % 16)
            return Reply(regs)
        return Reply([0] * count)

    def bcast_regs(self, addr, values, log=True):
        if addr == ota.REG_META_FIRST:
            self.meta = list(values)
        elif addr == ota.REG_CHUNK_FIRST:
            idx = values[0]
            if self.streaming_done:
                self.resent.append(idx)
            for d in self._reachable():
                if d.state != 1:
                    continue                  # dropped devices hear nothing
                d.streamed += 1
                if not self.streaming_done and d.miss_first and \
                        idx >= d.total - d.miss_first:
                    continue                  # lose the tail of the stream
                d.chunks.add(idx)
            # end of the first stream = the frame carrying the last index
            if not self.streaming_done and idx == self.meta[4] - 1:
                self.streaming_done = True
                for d in self._reachable():
                    if d.drop_after_stream and d.state == 1:
                        d.state, d.err = 3, 4         # failed: session timeout
        return Reply()

    def bcast_coil(self, addr):
        for d in self._reachable():
            if addr == ota.COIL_ENTER:
                d.state, d.err = 1, 0
                d.chunks.clear()
                d.total = self.meta[4]
            elif addr == ota.COIL_FINALIZE and d.state == 1:
                if len(d.chunks) == d.total:
                    d.state = 2
                else:
                    d.err = 8
        return Reply()

    def write_coil(self, device_id, addr, value):
        d = self.devs[device_id]
        if addr == ota.COIL_APPLY and d.state == 2:
            d.fw, d.state = 30400, 0
        return Reply()

    def sleep(self, seconds):
        pass


def run(devices, hub=False):
    bus = StubBus(devices, hub=hub)
    lines: list = []

    def emit(ev):
        if isinstance(ev, ota.Line):
            lines.append(ev.text)

    image = bytes(range(256)) * 8            # 2,048 B -> 16 chunks
    rep = ota.run_ota(bus, ota.OtaConfig(ids=tuple(d.uid for d in devices),
                                         image=image),
                      emit, threading.Event())
    return bus, rep, lines


def main() -> int:
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
        failures += not cond

    # 1. clean run: everyone updates
    bus, rep, _ = run([Device(11), Device(12)])
    check("clean: both updated", rep.ok and sorted(rep.updated) == [11, 12])

    # 2. one device drops after the stream; the other missed 3 chunks
    a, b = Device(11, miss_first=3), Device(12, drop_after_stream=True)
    bus, rep, lines = run([a, b])
    check("drop: survivor updated", rep.ok and rep.updated == [11],
          f"ok={rep.ok} updated={rep.updated}")
    check("drop: survivor really runs new fw", a.fw == 30400 and b.fw == 30302)
    check("drop: dropped device named with its own error",
          any("left the session" in l and "timeout" in l for l in lines),
          str([l for l in lines if "left" in l]))
    check("drop: retry advice names id 12",
          any("NOT updated this run: 12" in l for l in lines))
    check("drop: only the survivor's chunks were re-sent",
          sorted(set(bus.resent)) == list(range(13, 16)),
          f"resent={sorted(set(bus.resent))}")

    # 3. everyone drops: the run says so and fails
    bus, rep, lines = run([Device(11, drop_after_stream=True),
                           Device(12, drop_after_stream=True)])
    check("all-drop: run fails", not rep.ok)
    check("all-drop: no chunks wasted on the deaf", bus.resent == [],
          f"resent={bus.resent}")

    # 4. two hub channels: one session per channel, or nobody on the far
    #    channel ever hears the ENTER broadcast
    devs = [Device(11), Device(12), Device(21), Device(22)]
    bus, rep, lines = run(devs, hub=True)
    check("hub: every device on both channels updated",
          rep.ok and sorted(rep.updated) == [11, 12, 21, 22],
          f"ok={rep.ok} updated={sorted(rep.updated)}")
    check("hub: all four really run the new fw",
          all(d.fw == 30400 for d in devs),
          str({d.uid: d.fw for d in devs}))
    check("hub: the run names each channel it visits",
          sum("hub channel" in l for l in lines) == 2)

    print(f"\n{'ALL PASS' if not failures else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
