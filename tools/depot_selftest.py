"""Self-test for gw_depot against an in-memory gateway (no network, no hardware).

The fake link keeps the same rules as the gateway's depot: four slots, CRC checked when the last chunk lands, a started
slot listed as incomplete, BEGIN needs HELLO. Run: .venv/Scripts/python tools/depot_selftest.py
"""
import os
import sys
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import gw_depot  # noqa: E402


class R:
    def __init__(self, ok=True):
        self.ok, self.error_text = ok, "refused"


class FakeLink:
    def __init__(self, corrupt_read=False, drop_chunk_once=False):
        self.slots = [None] * 4
        self.armed = False
        self.w = None
        self.corrupt_read = corrupt_read
        self.drop_chunk_once = drop_chunk_once

    def hello(self, who):
        self.armed = True
        return R()

    def bye(self):
        self.armed = False

    def depot_begin(self, name, size, crc):
        if not self.armed:
            return 1, 0
        slot = next((i for i, s in enumerate(self.slots) if s and s["name"] == name), None)
        if slot is None:
            slot = next((i for i, s in enumerate(self.slots) if s is None), None)
        if slot is None:
            return 11, 0
        self.slots[slot] = {"name": name, "size": size, "crc": crc, "data": bytearray(), "done": False}
        self.w = slot
        return 0, slot

    def depot_data(self, offset, chunk):
        s = self.slots[self.w]
        if self.drop_chunk_once and offset == 480:
            self.drop_chunk_once = False
            return 5, len(s["data"])          # as if a frame was lost: tells the tool where to resume
        if offset != len(s["data"]):
            return 5, len(s["data"])
        s["data"] += chunk
        if len(s["data"]) == s["size"]:
            if zlib.crc32(bytes(s["data"])) & 0xFFFFFFFF != s["crc"]:
                self.slots[self.w] = None
                return 7, 0
            s["done"] = True
        return 0, len(s["data"])

    def depot_list(self):
        out = []
        for i, s in enumerate(self.slots):
            if not s:
                out.append({"slot": i, "state": 0, "size": 0, "crc": 0, "name": ""})
            else:
                out.append({"slot": i, "state": 2 if s["done"] else 1, "size": s["size"], "crc": s["crc"], "name": s["name"]})
        return out

    def depot_read(self, slot, offset):
        s = self.slots[slot]
        if not s or not s["done"]:
            return 14, b""
        part = bytes(s["data"][offset:offset + 200])
        if self.corrupt_read and offset == 0:
            part = bytes([part[0] ^ 1]) + part[1:]
        return 0, part

    def depot_delete(self, slot):
        if not self.armed:
            return 1
        if not self.slots[slot]:
            return 14
        self.slots[slot] = None
        return 0


def main() -> int:
    bad = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            bad.append(name)

    image = os.urandom(61304)
    link = FakeLink()
    slot = gw_depot.put(link, "module_v3_5_5", image)
    check("put returns the slot and the gateway lists it complete", link.slots[slot]["done"])
    name, back = gw_depot.fetch(link, slot)
    check("fetch returns the same name and bytes", name == "module_v3_5_5" and back == image)

    link2 = FakeLink(drop_chunk_once=True)
    s2 = gw_depot.put(link2, "resume", image)
    check("a lost chunk is resumed from where the gateway says", link2.slots[s2]["done"] and bytes(link2.slots[s2]["data"]) == image)

    try:
        gw_depot.fetch(FakeLink(corrupt_read=True) if False else _corrupt(image), 0)
        check("a corrupted read-back is refused", False)
    except gw_depot.DepotError:
        check("a corrupted read-back is refused", True)

    for bad_name in ("has space", "x" * 25, ""):
        try:
            gw_depot.put(FakeLink(), bad_name, image)
            check(f"bad name {bad_name!r} refused", False)
        except gw_depot.DepotError:
            check(f"bad name {bad_name!r} refused", True)
    try:
        gw_depot.put(FakeLink(), "tiny", b"x" * 100)
        check("an implausible size is refused", False)
    except gw_depot.DepotError:
        check("an implausible size is refused", True)

    full = FakeLink()
    for i in range(4):
        gw_depot.put(full, f"img{i}", image[:2000])
    try:
        gw_depot.put(full, "fifth", image[:2000])
        check("a fifth image is refused as full", False)
    except gw_depot.DepotError as exc:
        check("a fifth image is refused as full", "four" in str(exc))
    gw_depot.delete(full, 0)
    gw_depot.put(full, "fifth", image[:2000])
    check("delete frees a slot", True)

    check("the stored name keeps the version at the tail", gw_depot.depot_name("module_g070_v3.5.5_ota.bin") == "module_g070_v3.5.5_ota"
          and gw_depot.depot_name("a" * 30 + "_v3.5.5.bin").endswith("_v3.5.5"))
    print(f"{'ALL PASS' if not bad else 'FAILED: ' + ', '.join(bad)}")
    return 1 if bad else 0


def _corrupt(image):
    l = FakeLink(corrupt_read=True)
    gw_depot.put(l, "c", image)
    return l


if __name__ == "__main__":
    sys.exit(main())
