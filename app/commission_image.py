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
BLOCK_SIZE = 32
BLOCK_VERSION = 1
CRC_LEN = BLOCK_SIZE - 2

# Field offsets within the block, after the 16-byte magic.
_FIELDS = "<8H"          # version, size, tokenLo, tokenHi, applyMask, flags, identifier, crc
_FIELDS_AT = 16

APPLY_ID = 0x0001
FLAG_FORCE = 0x0001

# 0 means "nobody patched this image"; all-ones is what erased flash reads as.
TOKEN_NONE = 0x00000000
TOKEN_ERASED = 0xFFFFFFFF

# The firmware refuses anything outside this: 246 is the SET_ID switch mode's
# own address and 247 means "no ID set".
ID_MIN, ID_MAX = 1, 245

FIRMWARE_MIN = "v3.1.0"          # first release carrying the block


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
        raw = image[i:i + BLOCK_SIZE]
        if len(raw) < BLOCK_SIZE:
            continue
        version, size, token_lo, token_hi, mask, flags, ident, crc = \
            struct.unpack_from(_FIELDS, raw, _FIELDS_AT)
        if version != BLOCK_VERSION or size != BLOCK_SIZE:
            continue
        if crc16_ccitt(raw[:CRC_LEN]) != crc:
            continue
        found.append(Block(offset=i, version=version, size=size,
                           token=(token_hi << 16) | token_lo,
                           apply_mask=mask, flags=flags, identifier=ident))


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
          token: int | None = None) -> tuple[bytes, Block]:
    """Return a copy of `image` carrying `identifier`, and the block written.

    A fresh token each time is what makes the module apply the ID exactly once
    per flash: it records which token it consumed, so re-flashing the same file
    later cannot silently revert an ID somebody changed in the meantime.
    """
    if not (ID_MIN <= identifier <= ID_MAX):
        raise ImageError(
            f"Slave ID {identifier} is out of range. Use {ID_MIN}-{ID_MAX}; "
            "246 is reserved for a module in SET_ID mode and 247 means no ID "
            "is set.")

    block = find_block(image)
    if token is None:
        token = mint_token()

    flags = FLAG_FORCE if force else 0
    body = bytearray(image[block.offset:block.offset + BLOCK_SIZE])
    struct.pack_into(_FIELDS, body, _FIELDS_AT,
                     BLOCK_VERSION, BLOCK_SIZE,
                     token & 0xFFFF, (token >> 16) & 0xFFFF,
                     APPLY_ID, flags, identifier, 0)
    struct.pack_into("<H", body, CRC_LEN, crc16_ccitt(bytes(body[:CRC_LEN])))

    out = bytearray(image)
    out[block.offset:block.offset + BLOCK_SIZE] = body
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
    if len(patched) != len(image):
        raise ImageError("Patching changed the image length — refusing to flash it.")

    return patched, written


def describe(block: Block) -> str:
    """One line about a block, for logs and the confirm dialog."""
    if not block.patched:
        return f"unpatched image (built-in ID {block.identifier})"
    forced = ", overwrite" if block.flags & FLAG_FORCE else ""
    return (f"ID {block.identifier}, token 0x{block.token:08X}{forced}, "
            f"block at 0x{block.offset:05X}")
