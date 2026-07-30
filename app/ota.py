"""OTA firmware update over RS485 — port of LGS-Standard-Module/tools/ota_sender.py.

Streams a firmware .bin to every selected board at once with Modbus broadcast
FC16 writes (device id 0), repairs whatever each board reports missing, then
verifies and applies per device.

Wire contract mirrors src/svc/modbus_map.h + include/flash_layout.h:
  probe → broadcast metadata + coil 505 (staging erase) → stream 128 B chunks
  → per-device bitmap repair → coil 506 verify → coil 507 apply → confirm reg 1.

The image must be built for the app slot (flash_offset 0x1000) and fit in
MAX_IMAGE_SIZE.
"""
from __future__ import annotations

import threading
import time
import zlib
from dataclasses import dataclass, field
from typing import Callable, Optional, Protocol, Sequence

# ── wire contract ──────────────────────────────────────────────────────────
REG_STATE = 282           # lo = state, hi = error code
REG_CHUNKS_RX = 283
REG_META_FIRST = 284      # size_hi, size_lo, crc_hi, crc_lo, total_chunks
REG_CHUNK_FIRST = 290     # index, len, crc16, data x64, commit  (68 regs)
REG_BITMAP_FIRST = 360
BITMAP_REGS = 30
COIL_ENTER, COIL_FINALIZE, COIL_APPLY, COIL_ABORT = 505, 506, 507, 508
CHUNK_SIZE = 128
MAX_IMAGE_SIZE = 61440

STATE_NAMES = {0: "idle", 1: "receiving", 2: "verified", 3: "failed"}
ERROR_NAMES = {0: "-", 1: "bad size", 2: "bad chunk count", 3: "image CRC32 mismatch",
               4: "session timeout", 5: "flash write error", 6: "apply while not verified",
               7: "latch busy", 8: "chunks incomplete"}


class OtaCancelled(Exception):
    pass


class OtaOps(Protocol):
    """Transactions the runner needs; implemented by the worker."""

    def read_regs(self, device_id: int, addr: int, count: int): ...
    def bcast_regs(self, addr: int, values: list, log: bool = True): ...
    def bcast_coil(self, addr: int): ...
    def write_coil(self, device_id: int, addr: int, value: int): ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class OtaConfig:
    ids: tuple = ()
    image: bytes = b""
    filename: str = ""
    repair_rounds: int = 5
    broadcast_apply: bool = False

    @property
    def total_chunks(self) -> int:
        return (len(self.image) + CHUNK_SIZE - 1) // CHUNK_SIZE

    @property
    def crc32(self) -> int:
        return zlib.crc32(self.image) & 0xFFFFFFFF

    def size_error(self) -> str:
        if not 8 <= len(self.image) <= MAX_IMAGE_SIZE:
            return (f"image is {len(self.image):,} B; the OTA slot holds "
                    f"{MAX_IMAGE_SIZE:,} B")
        return ""


@dataclass
class Line:
    text: str
    level: str = "info"          # info | ok | warn | err
    seq: int = 0


@dataclass
class Progress:
    done: int
    total: int
    seq: int = 0


@dataclass
class Done:
    ok: bool
    summary: str
    seq: int = 0


@dataclass
class OtaReport:
    ok: bool = False
    summary: str = ""
    updated: list = field(default_factory=list)
    lines: list = field(default_factory=list)


def crc16_ccitt(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if (crc & 0x8000) else (crc << 1) & 0xFFFF
    return crc


def _chunk_frame(image: bytes, idx: int, tx_counter: int) -> list:
    offset = idx * CHUNK_SIZE
    payload = image[offset:offset + CHUNK_SIZE]
    padded = payload + b"\xff" * (-len(payload) % 2)
    data_regs = [(padded[i] << 8) | padded[i + 1] for i in range(0, len(padded), 2)]
    data_regs += [0xFFFF] * (64 - len(data_regs))
    return [idx, len(payload), crc16_ccitt(payload)] + data_regs + [tx_counter]


def read_state(ops: OtaOps, device_id: int) -> Optional[dict]:
    res = ops.read_regs(device_id, REG_STATE, 2)
    if not res.ok:
        return None
    regs = res.value if isinstance(res.value, list) else [res.value, 0]
    return {"state": regs[0] & 0xFF, "error": regs[0] >> 8, "chunks": regs[1]}


def describe_state(st: Optional[dict]) -> str:
    if st is None:
        return "no reply"
    text = STATE_NAMES.get(st["state"], "?")
    if st["error"]:
        text += f" (error: {ERROR_NAMES.get(st['error'], st['error'])})"
    return f"{text}, chunks {st['chunks']}"


def run_ota(ops: OtaOps, cfg: OtaConfig, emit: Callable,
            cancel: threading.Event) -> OtaReport:
    report = OtaReport()

    def say(text: str, level: str = "info") -> None:
        report.lines.append(text)
        emit(Line(text, level))

    def finish(ok: bool, summary: str) -> OtaReport:
        report.ok, report.summary = ok, summary
        emit(Done(ok, summary))
        return report

    ids = list(cfg.ids)
    total = cfg.total_chunks
    say(f"image: {cfg.filename} — {len(cfg.image):,} B, CRC32 {cfg.crc32:08X}, "
        f"{total} chunks of {CHUNK_SIZE} B")

    try:
        # 1. probe
        say(f"[1/8] probing devices {ids} ...")
        old_fw: dict[int, int] = {}
        for uid in ids:
            res = ops.read_regs(uid, 0, 5)
            if not res.ok:
                say(f"  id {uid}: NO REPLY — aborting", "err")
                return finish(False, f"device {uid} did not answer")
            regs = res.value
            old_fw[uid] = regs[1]
            say(f"  id {uid}: type {regs[0]}, FW {regs[1]}, HW {regs[2]}")

        # 2+3. metadata + enter
        say("[2/8] broadcasting metadata ...")
        ops.bcast_regs(REG_META_FIRST, [len(cfg.image) >> 16, len(cfg.image) & 0xFFFF,
                                        cfg.crc32 >> 16, cfg.crc32 & 0xFFFF, total])
        say("[3/8] entering OTA mode (staging erase ~1 s) ...")
        ops.bcast_coil(COIL_ENTER)
        ops.sleep(2.0)
        for uid in ids:
            st = read_state(ops, uid)
            if st is None or st["state"] != 1:
                say(f"  id {uid}: did not enter OTA — {describe_state(st)}", "err")
                return finish(False, f"device {uid} did not enter OTA mode")
        say(f"  all {len(ids)} device(s) receiving", "ok")

        # 4. stream
        say(f"[4/8] streaming {total} chunks ...")
        t0 = time.monotonic()
        tx_counter = 0
        for idx in range(total):
            tx_counter = (tx_counter + 1) & 0xFFFF
            ops.bcast_regs(REG_CHUNK_FIRST, _chunk_frame(cfg.image, idx, tx_counter),
                           log=False)          # 480 chunk frames would flood the log
            if idx % 8 == 7 or idx == total - 1:
                emit(Progress(idx + 1, total))
        say(f"  streamed in {time.monotonic() - t0:.0f} s")

        # 5. repair
        say("[5/8] bitmap check + repair ...")
        for round_no in range(1, cfg.repair_rounds + 1):
            union_missing: set = set()
            for uid in ids:
                res = ops.read_regs(uid, REG_BITMAP_FIRST, BITMAP_REGS)
                if not res.ok:
                    say(f"  id {uid}: bitmap read failed", "err")
                    return finish(False, f"bitmap read failed on device {uid}")
                regs = res.value
                miss = [i for i in range(total) if not (regs[i // 16] >> (i % 16)) & 1]
                if miss:
                    say(f"  id {uid}: missing {len(miss)} chunk(s)", "warn")
                union_missing.update(miss)
            if not union_missing:
                say("  all devices report a complete image", "ok")
                break
            say(f"  repair round {round_no}: re-sending {len(union_missing)} chunk(s)")
            for idx in sorted(union_missing):
                tx_counter = (tx_counter + 1) & 0xFFFF
                ops.bcast_regs(REG_CHUNK_FIRST, _chunk_frame(cfg.image, idx, tx_counter),
                               log=False)
        else:
            say("  chunks still missing after all repair rounds", "err")
            return finish(False, "image incomplete after repair rounds")

        # 6. finalize
        say("[6/8] finalize (device-side CRC32) ...")
        ops.bcast_coil(COIL_FINALIZE)
        ops.sleep(1.0)
        verified = []
        for uid in ids:
            st = read_state(ops, uid)
            say(f"  id {uid}: {describe_state(st)}",
                "ok" if st and st["state"] == 2 else "err")
            if st and st["state"] == 2:
                verified.append(uid)
        if not verified:
            return finish(False, "no device verified the image")

        # 7. apply
        say(f"[7/8] applying to {verified} (reboot + bootloader copy ~4 s) ...")
        if cfg.broadcast_apply:
            ops.bcast_coil(COIL_APPLY)
        else:
            for uid in verified:
                ops.write_coil(uid, COIL_APPLY, 1)   # may reset before answering
                ops.sleep(0.1)
        ops.sleep(5.0)

        # 8. confirm
        say("[8/8] confirming new firmware version ...")
        ok_count = 0
        for uid in verified:
            regs = None
            for _ in range(5):
                res = ops.read_regs(uid, 1, 1)
                if res.ok:
                    regs = res.value
                    break
                ops.sleep(1.0)
            if regs is None:
                say(f"  id {uid}: no reply after reboot", "err")
            else:
                changed = regs != old_fw[uid]
                say(f"  id {uid}: FW {old_fw[uid]} → {regs}  "
                    f"[{'UPDATED' if changed else 'same version'}]",
                    "ok" if changed else "warn")
                report.updated.append(uid)
                ok_count += 1
        return finish(ok_count == len(verified),
                      f"{ok_count}/{len(verified)} device(s) running the new image")
    except OtaCancelled:
        say("cancelled — the device session times out by itself (~30 s)", "warn")
        return finish(False, "cancelled")
