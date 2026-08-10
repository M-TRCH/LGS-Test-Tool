"""Patch a Modbus slave ID into a firmware image before it is flashed.

A blank module has no firmware, so it cannot be told its ID over Modbus — that
is a second tool and a second session after the ST-Link flash. Its settings
live on an external EEPROM that ST-Link cannot reach either. What ST-Link can
write is the image, so the image carries the ID, and the module adopts it the
first time it boots.

The values sit in a block the firmware tags with a magic
(LGS-Standard-Module/include/commission_block.h). Finding it by magic rather
than by recognising the default values is the whole point: the previous
approach had to know every surrounding default and would have started patching
the wrong address the day one of them changed.

Everything here is pure — bytes in, bytes out — so it is testable with no
board, no programmer and no serial port.
"""
from __future__ import annotations

import secrets
import struct
from dataclasses import dataclass

MAGIC = b"LGS-COMMISSION"
# v2 added deviceType. v1 images (ID only) are still read and still patchable,
# because some are already flashed on boards in the field.
LAYOUTS = {1: 32, 2: 36}         # block version -> size in bytes
BLOCK_SIZE = LAYOUTS[2]
BLOCK_VERSION = 2

# Fields after the 16-byte magic, up to (not including) the trailing crc.
_HEAD = "<7H"            # version, size, tokenLo, tokenHi, applyMask, flags, identifier
_FIELDS_AT = 16

APPLY_ID = 0x0001
APPLY_DEVICE_TYPE = 0x0002
FLAG_FORCE = 0x0001

# What reg 0 reports. The factory builds these variants differently — a
# Standard cabinet takes the 8-LED index mask and has no ring, OLED or big
# button — so the type is a commissioning-time fact about the hardware.
DEVICE_TYPES = {10: "STANDARD", 20: "NARCOTIC", 30: "LITE", 40: "DELIVERY"}

# 0 means "nobody patched this image"; all-ones is what erased flash reads as.
TOKEN_NONE = 0x00000000
TOKEN_ERASED = 0xFFFFFFFF

# The firmware refuses anything outside this: 246 is the SET_ID switch mode's
# own address and 247 means "no ID set".
ID_MIN, ID_MAX = 1, 245

FIRMWARE_MIN = "v3.1.0"          # first release carrying the block
FIRMWARE_TYPE_MIN = "v3.3.0"     # first release whose block carries a device type


class ImageError(Exception):
    """The image cannot be commissioned, with a reason worth showing a user."""


@dataclass(frozen=True)
class Block:
    offset: int              # where it sits in the image
    version: int
    size: int
    token: int
    apply_mask: int
    flags: int
    identifier: int
    device_type: int = 0     # 0 = the image does not carry one (v1 block)

    @property
    def patched(self) -> bool:
        return self.token not in (TOKEN_NONE, TOKEN_ERASED)


def crc16_ccitt(data: bytes) -> int:
    """Poly 0x1021, init 0xFFFF — the CRC the firmware uses throughout."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def _candidates(image: bytes) -> list[Block]:
    """Every block in the image that passes version, size and CRC.

    The magic appears more than once by design — the firmware also holds it as
    the string it compares against — so a hit is only a candidate until its
    CRC checks out.
    """
    found: list[Block] = []
    start = 0
    while True:
        i = image.find(MAGIC, start)
        if i < 0:
            return found
        start = i + 1
        head = image[i:i + 20]
        if len(head) < 20:
            continue
        version, size = struct.unpack_from("<2H", head, _FIELDS_AT)
        if LAYOUTS.get(version) != size:
            continue
        raw = image[i:i + size]
        if len(raw) < size:
            continue
        _v, _s, token_lo, token_hi, mask, flags, ident = \
            struct.unpack_from(_HEAD, raw, _FIELDS_AT)
        crc = struct.unpack_from("<H", raw, size - 2)[0]
        if crc16_ccitt(raw[:size - 2]) != crc:
            continue
        dtype = struct.unpack_from("<H", raw, 30)[0] if version >= 2 else 0
        found.append(Block(offset=i, version=version, size=size,
                           token=(token_hi << 16) | token_lo,
                           apply_mask=mask, flags=flags, identifier=ident,
                           device_type=dtype))


# Where the application starts. Everything below it is the bootloader.
APP_BASE = 0x08001000


def check_factory_image(image: bytes) -> None:
    """Refuse an OTA image where a factory image is meant.

    The two look alike to every other check here: the OTA image is a byte
    slice of the factory image starting at the application, so it carries the
    same commissioning block and passes `find_block` happily. Flashing it over
    ST-Link would write the application to 0x08000000, where the bootloader
    belongs — a board that has to be recovered before it will run again.

    They differ in the one place that says where the image expects to live:
    the reset vector. A factory image starts with the bootloader's vector
    table, so its reset handler sits in the first 4 KB; an application linked
    at 0x08001000 points well past it. Checked against every released image
    from v3.0.0 to v3.3.0.
    """
    if len(image) < 8:
        raise ImageError("This file is too small to be a firmware image.")
    reset = struct.unpack_from("<I", image, 4)[0] & ~1
    if reset >= APP_BASE:
        raise ImageError(
            "This is an over-the-air image (application only) — its reset "
            f"vector points to 0x{reset:08X}, past the bootloader. Flashing "
            "it over ST-Link would leave the module without one. Use the "
            "*factory* image here, and this one on the Firmware (OTA) tab.")


def find_block(image: bytes) -> Block:
    """Locate the one commissioning block, or explain why there isn't one."""
    blocks = _candidates(image)
    if not blocks:
        raise ImageError(
            "This firmware image cannot carry a Modbus ID — it was built "
            f"before commissioning support. Use {FIRMWARE_MIN} or newer, or "
            "flash this image as it is and set the ID over Modbus afterwards.")
    if len(blocks) > 1:
        where = ", ".join(f"0x{b.offset:05X}" for b in blocks)
        raise ImageError(
            f"The image carries {len(blocks)} commissioning blocks ({where}). "
            "That is a firmware bug — it must be defined once. Refusing to "
            "guess which one the module reads.")
    return blocks[0]


def mint_token() -> int:
    """A fresh apply-once marker, avoiding both reserved values."""
    while True:
        token = secrets.randbits(32)
        if token not in (TOKEN_NONE, TOKEN_ERASED):
            return token


def patch(image: bytes, *, identifier: int, force: bool = False,
          token: int | None = None,
          device_type: int | None = None) -> tuple[bytes, Block]:
    """Return a copy of `image` carrying `identifier`, and the block written.

    A fresh token each time is what makes the module apply the ID exactly once
    per flash: it records which token it consumed, so re-flashing the same file
    later cannot silently revert an ID somebody changed in the meantime.

    `device_type` is written only when asked for, and only into a v2 block —
    an older image has nowhere to put it, and quietly dropping it would leave
    a board reporting a type nobody chose.
    """
    if not (ID_MIN <= identifier <= ID_MAX):
        raise ImageError(
            f"Slave ID {identifier} is out of range. Use {ID_MIN}-{ID_MAX}; "
            "246 is reserved for a module in SET_ID mode and 247 means no ID "
            "is set.")
    if device_type is not None and device_type not in DEVICE_TYPES:
        raise ImageError(
            f"Device type {device_type} is not one this firmware knows. Use "
            + ", ".join(f"{k} ({v})" for k, v in DEVICE_TYPES.items()) + ".")

    block = find_block(image)
    if device_type is not None and block.version < 2:
        raise ImageError(
            "This image cannot carry a device type — it was built before "
            f"block v2 (this one is v{block.version}). Use module firmware "
            f"{FIRMWARE_TYPE_MIN} or newer, or leave the device type unset.")
    if token is None:
        token = mint_token()

    size = block.size
    flags = FLAG_FORCE if force else 0
    mask = APPLY_ID | (APPLY_DEVICE_TYPE if device_type is not None else 0)
    body = bytearray(image[block.offset:block.offset + size])
    struct.pack_into(_HEAD, body, _FIELDS_AT,
                     block.version, size,
                     token & 0xFFFF, (token >> 16) & 0xFFFF,
                     mask, flags, identifier)
    if block.version >= 2:
        # deviceType then reserved. Keep whatever type the image already
        # carried when the operator did not pick one, so re-flashing is never
        # a silent downgrade to "unspecified".
        struct.pack_into("<2H", body, 30,
                         device_type if device_type is not None
                         else block.device_type, 0)
    struct.pack_into("<H", body, size - 2, crc16_ccitt(bytes(body[:size - 2])))

    out = bytearray(image)
    out[block.offset:block.offset + size] = body
    patched = bytes(out)

    # Read our own output back rather than trusting the write: a wrong offset
    # or a stale CRC would otherwise only surface as a board that ignores the
    # ID, long after the flash.
    written = find_block(patched)
    if (written.identifier != identifier or written.token != token
            or written.offset != block.offset
            or not (written.apply_mask & APPLY_ID)
            or bool(written.flags & FLAG_FORCE) != force):
        raise ImageError("Patched image did not read back as expected — "
                         "refusing to flash it.")
    if device_type is not None and written.device_type != device_type:
        raise ImageError("Patched image did not read back the device type — "
                         "refusing to flash it.")
    if len(patched) != len(image):
        raise ImageError("Patching changed the image length — refusing to flash it.")

    return patched, written


def describe(block: Block) -> str:
    """One line about a block, for logs and the confirm dialog."""
    if not block.patched:
        return f"unpatched image (built-in ID {block.identifier})"
    forced = ", overwrite" if block.flags & FLAG_FORCE else ""
    typed = ""
    if block.apply_mask & APPLY_DEVICE_TYPE:
        name = DEVICE_TYPES.get(block.device_type, "?")
        typed = f", type {block.device_type} ({name})"
    return (f"ID {block.identifier}{typed}, token 0x{block.token:08X}{forced}, "
            f"block at 0x{block.offset:05X}")
