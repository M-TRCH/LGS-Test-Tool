"""Module firmware images kept on a gateway (the depot), and how the Tool puts them there and gets them back.

Why it exists: the Tool installed on a hospital server has no firmware bundle and no way to be sent one. A laptop that has
the images plugs straight into an Opta and leaves one behind (`put`); later the Tool on the server reads it back out of any
one gateway (`fetch`) and runs the ordinary module OTA from memory. The gateway never interprets the bytes.
Gateway side: LGS-Gateway-Arduino-Opta docs/design-module-depot.md, subfunctions 0x20-0x24.
"""
from __future__ import annotations

import re
import zlib
from typing import Callable, Optional

from . import gateway_tcp
from .gateway_config import GatewayError

NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,24}$")
MIN_IMAGE_B = 1024
MAX_IMAGE_B = 128 * 1024          # the gateway's own limit; a module slot is 61,440 B


class DepotError(Exception):
    pass


def depot_name(filename: str) -> str:
    """A bundled file name as the gateway will store it: allowed characters only, at most 24, the tail kept
    (the version is at the end of the name)."""
    stem = re.sub(r"\.bin$", "", filename or "", flags=re.I)
    stem = re.sub(r"[^A-Za-z0-9._-]", "_", stem)
    return stem[-24:] or "image"


def slots(link) -> list:
    try:
        return link.depot_list()
    except GatewayError as exc:
        raise DepotError(f"this gateway has no depot ({exc})") from exc


def put(link, name: str, data: bytes, progress: Optional[Callable[[int, int], None]] = None) -> int:
    """Store `data` as `name`; returns the slot. The gateway CRC-checks the bytes on its flash before marking the
    slot complete, and this reads the list back to prove it."""
    if not NAME_RE.match(name):
        raise DepotError(f"image name {name!r} is not allowed (A-Z a-z 0-9 . _ - , up to 24)")
    if not MIN_IMAGE_B <= len(data) <= MAX_IMAGE_B:
        raise DepotError(f"{len(data):,} bytes is not a plausible module image")
    crc = zlib.crc32(data) & 0xFFFFFFFF
    hello = link.hello("depot-put")
    if not hello.ok:
        raise DepotError("HELLO refused: " + hello.error_text)
    try:
        status, slot = link.depot_begin(name, len(data), crc)
        if status != 0:
            raise DepotError("DEPOT_BEGIN: " + gateway_tcp.DEPOT_STATUS_TEXT.get(status, str(status)))
        off, resynced = 0, False
        while off < len(data):
            chunk = data[off:off + gateway_tcp.FW_CHUNK]
            status, received = link.depot_data(off, chunk)
            if status == 5 and not resynced:
                off, resynced = received, True
                continue
            if status != 0:
                raise DepotError("DEPOT_DATA: " + gateway_tcp.DEPOT_STATUS_TEXT.get(status, str(status)))
            off += len(chunk)
            if progress:
                progress(off, len(data))
        mine = next((s for s in link.depot_list() if s["slot"] == slot), None)
        if not mine or mine["state"] != 2 or mine["crc"] != crc or mine["size"] != len(data):
            raise DepotError("the gateway does not list the image as complete")
        return slot
    finally:
        try:
            link.bye()
        except (OSError, GatewayError):
            pass


def fetch(link, slot: int, progress: Optional[Callable[[int, int], None]] = None) -> tuple:
    """Read one stored image back -> (name, bytes), proven against the CRC-32 the gateway listed."""
    row = next((s for s in slots(link) if s["slot"] == slot), None)
    if not row or row["state"] != 2:
        raise DepotError("that depot slot holds no complete image")
    buf = bytearray()
    while len(buf) < row["size"]:
        status, part = link.depot_read(slot, len(buf))
        if status != 0:
            raise DepotError("DEPOT_READ: " + gateway_tcp.DEPOT_STATUS_TEXT.get(status, str(status)))
        if not part:
            break
        buf += part
        if progress:
            progress(len(buf), row["size"])
    if len(buf) != row["size"] or (zlib.crc32(bytes(buf)) & 0xFFFFFFFF) != row["crc"]:
        raise DepotError("the image read back does not match its CRC — try again, or read it from another gateway")
    return row["name"], bytes(buf)


def delete(link, slot: int) -> None:
    hello = link.hello("depot-delete")
    if not hello.ok:
        raise DepotError("HELLO refused: " + hello.error_text)
    try:
        status = link.depot_delete(slot)
        if status != 0:
            raise DepotError("DEPOT_DELETE: " + gateway_tcp.DEPOT_STATUS_TEXT.get(status, str(status)))
    finally:
        try:
            link.bye()
        except (OSError, GatewayError):
            pass
