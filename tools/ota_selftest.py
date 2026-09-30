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
    def __init__(self, uid, miss_first=0, drop_after_stream=0):
        self.uid = uid
        self.fw = 30302
        self.state, self.err = 0, 0          # 0 idle, 1 receiving, 2 verified, 3 failed
        self.chunks: set = set()
        self.total = 0
        self.miss_first = miss_first         # chunks to drop during the first stream
        # How many streams this device drops out of (session timeout at the
        # end of the stream). 1 = the first only, so the runner's slow retry
        # gets it; 2 = the retry too, so it stays lost.
        self.drop_after_stream = int(drop_after_stream)
        self.streamed = 0                    # frames seen while receiving


class StubBus:
    """OtaOps over a handful of scripted devices on one 'channel'."""

    def __init__(self, devices, hub=False, gateway_map=None):
        self.devs = {d.uid: d for d in devices}
        self.meta = [0] * 5
        self.resent: list = []               # chunk idx re-sent after the stream
        self.streaming_done = False
        self.sleeps: list = []               # every ops.sleep(), for pacing checks
        self.sessions = 0                    # ENTER broadcasts seen
        # hub=True behaves like the real gateway: a broadcast (slave id 0) is
        # NOT a channel switch, so it only reaches whichever channel a unicast
        # last parked the hub on. Without modelling that, the stub cheerfully
        # passed a whole-cabinet OTA that cannot work on the bench.
        self.hub = hub
        self.parked = None
        self.gateway_map = gateway_map       # what the gateway would report

    def _chan(self, uid):
        # Row -> CHANNEL via the map, exactly like the real gateway. The
        # first cut compared rows, which quietly made rows sharing a channel
        # unreachable from each other and forced the gateway-map test to run
        # hubless -- a stub bug shaped just right to hide a grouping bug.
        row = uid // 10
        if self.gateway_map:
            m = [int(x) for x in self.gateway_map.split(",")]
            return m[row - 1] if 1 <= row <= len(m) else 0
        return row

    def _reachable(self):
        if not self.hub:
            return list(self.devs.values())
        return [d for d in self.devs.values()
                if self._chan(d.uid) == self.parked]

    # ── OtaOps ─────────────────────────────────────────────────────────
    def read_regs(self, device_id, addr, count):
        d = self.devs[device_id]
        self.parked = self._chan(device_id)  # a unicast parks the hub
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
                    if d.drop_after_stream > 0 and d.state == 1:
                        d.drop_after_stream -= 1
                        d.state, d.err = 3, 4         # failed: session timeout
        return Reply()

    def bcast_coil(self, addr):
        if addr == ota.COIL_ENTER:
            # A new session: its own stream is a stream, not a repair.
            self.streaming_done = False
            self.sessions += 1
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

    def hub_map(self):
        return self.gateway_map              # None = "cannot ask", as over RTU

    def sleep(self, seconds):
        self.sleeps.append(seconds)


def run(devices, hub=False, gateway_map=None, **cfg):
    bus = StubBus(devices, hub=hub, gateway_map=gateway_map)
    lines: list = []

    dones: list = []

    def emit(ev):
        if isinstance(ev, ota.Line):
            lines.append(ev.text)
        elif isinstance(ev, ota.Done):
            dones.append(ev)

    image = bytes(range(256)) * 8            # 2,048 B -> 16 chunks
    rep = ota.run_ota(bus, ota.OtaConfig(ids=tuple(d.uid for d in devices),
                                         image=image, **cfg),
                      emit, threading.Event())
    return bus, rep, lines, dones


def main() -> int:
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
        failures += not cond

    # 1. clean run: everyone updates
    bus, rep, _, _d = run([Device(11), Device(12)])
    check("clean: both updated", rep.ok and sorted(rep.updated) == [11, 12])

    # 2. one device drops after the stream; the other missed 3 chunks.
    #    Without the automatic retry this is the 2026-08-27 salvage rule.
    a, b = Device(11, miss_first=3), Device(12, drop_after_stream=1)
    bus, rep, lines, dones = run([a, b], retry_dropped=False)
    check("drop: survivor updated", rep.updated == [11],
          f"ok={rep.ok} updated={rep.updated}")
    check("drop: run not ok while a device is left behind", not rep.ok)
    check("drop: survivor really runs new fw", a.fw == 30400 and b.fw == 30302)
    check("drop: dropped device named with its own error",
          any("left the session" in l and "timeout" in l for l in lines),
          str([l for l in lines if "left" in l]))
    check("drop: retry advice names id 12",
          any("NOT updated this run: 12" in l for l in lines))
    check("drop: only the survivor's chunks were re-sent",
          sorted(set(bus.resent)) == list(range(13, 16)),
          f"resent={sorted(set(bus.resent))}")
    check("drop: the report names the dropped device", rep.dropped == [12],
          f"dropped={rep.dropped}")
    check("drop: exactly one Done", len(dones) == 1, f"{len(dones)} Done event(s)")

    # 2b. the same bus with the retry ON (the default): the dropped device is
    #     re-run once with the slow pacing and gets there. This is the Queen
    #     of 2026-09-30 -- five hand-driven rounds -- made automatic.
    a, b = Device(11, miss_first=3), Device(12, drop_after_stream=1)
    bus, rep, lines, dones = run([a, b])
    check("retry: both updated in one run", rep.ok and sorted(rep.updated) == [11, 12],
          f"ok={rep.ok} updated={rep.updated}")
    check("retry: both really run the new fw", a.fw == 30400 and b.fw == 30400)
    check("retry: announced, naming the device",
          any("retrying 1 device(s)" in l and "[12]" in l for l in lines),
          str([l for l in lines if "retry" in l]))
    check("retry: two sessions were opened", bus.sessions == 2, f"sessions={bus.sessions}")
    check("retry: nothing left in the dropped list", rep.dropped == [],
          f"dropped={rep.dropped}")
    check("retry: still exactly one Done", len(dones) == 1 and dones[0].ok,
          f"{len(dones)} Done event(s)")
    # The retry pacing is the point: 16 chunks at "1.0 s every 2" is 8
    # one-second holds; the first stream at "0.6 s every 8" is 2 holds.
    # (Each session also waits 1.0 s once after FINALIZE, hence + sessions.)
    check("retry: slow stream really paused the line",
          bus.sleeps.count(1.0) == 8 + bus.sessions and bus.sleeps.count(0.6) == 2,
          f"sleeps: 1.0 x{bus.sleeps.count(1.0)}, 0.6 x{bus.sleeps.count(0.6)}")

    # 3. everyone drops, on the retry too: the run says so and fails
    bus, rep, lines, dones = run([Device(11, drop_after_stream=2),
                           Device(12, drop_after_stream=2)])
    check("all-drop: run fails", not rep.ok)
    check("all-drop: no chunks wasted on the deaf", bus.resent == [],
          f"resent={bus.resent}")
    check("all-drop: both still named as dropped", sorted(rep.dropped) == [11, 12],
          f"dropped={rep.dropped}")

    # 3b. pauses off: a stream is just a stream (bench scripts, old behaviour)
    bus, rep, lines, dones = run([Device(11)], resync_every=0)
    check("no pacing: no holds at all",
          0.6 not in bus.sleeps and bus.sleeps.count(1.0) == bus.sessions,
          f"sleeps={bus.sleeps}")
    check("no pacing: still updates", rep.ok and rep.updated == [11])

    # 4. two hub channels: one session per channel, or nobody on the far
    #    channel ever hears the ENTER broadcast
    devs = [Device(11), Device(12), Device(21), Device(22)]
    bus, rep, lines, dones = run(devs, hub=True)
    check("hub: every device on both channels updated",
          rep.ok and sorted(rep.updated) == [11, 12, 21, 22],
          f"ok={rep.ok} updated={sorted(rep.updated)}")
    check("hub: all four really run the new fw",
          all(d.fw == 30400 for d in devs),
          str({d.uid: d.fw for d in devs}))
    check("hub: the run names each channel it visits",
          sum("hub channel" in l for l in lines) == 2)
    # Exactly one Done for the whole run. A Done per channel would end the
    # Firmware tab's job after the first one and silently skip the rest of
    # the cabinet -- which is what happened on the bench before this.
    check("hub: exactly one Done for the whole run",
          len(dones) == 1 and dones[0].ok,
          f"{len(dones)} Done event(s)")

    # 5. the gateway's map outranks the tool's. lgs_map's default puts rows
    #    1 and 2 on different channels; make the gateway say they SHARE
    #    channel 1. The device set is identical either way, so only the
    #    session count can tell which map was actually used.
    devs = [Device(11), Device(21)]
    bus, rep, lines_out, dones = run(devs, hub=True, gateway_map="1,1,3,4,5,6,7,8,1,2")
    check("gateway map wins: one shared channel, so one session",
          rep.ok and sum("hub channel" in l for l in lines_out) == 0,
          str([l for l in lines_out if 'channel' in l]))
    check("gateway map wins: both devices updated",
          all(d.fw == 30400 for d in devs))
    check("a map disagreement is announced",
          any("hub map from the gateway" in l for l in lines_out),
          str([l for l in lines_out if 'hub map' in l]))

    print(f"\n{'ALL PASS' if not failures else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
