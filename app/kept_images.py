"""Module firmware images the Tool keeps in its own data folder.

An installed Tool has no firmware bundle. An image pulled back out of a gateway's depot (gw_depot.fetch) can be kept here, so the
Tool holds its own copy: it then offers the image like a bundled one for module OTA, and can put it on another gateway.
Each image is `<name>.bin` plus `<name>.json` (size, CRC-32, SHA-256, where it came from, when); the SHA-256 is checked on every
load, so a damaged or swapped file is refused rather than flashed.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import zlib
from pathlib import Path

from . import config_store

NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,24}$")
MIN_B, MAX_B = 1024, 128 * 1024
KEY_PREFIX = "kept:"


class KeptError(Exception):
    pass


def folder() -> Path:
    d = config_store.data_dir() / "firmware"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _paths(name: str):
    if not NAME_RE.match(name or ""):
        raise KeptError(f"image name {name!r} is not allowed")
    d = folder()
    return d / f"{name}.bin", d / f"{name}.json"


def keep(name: str, data: bytes, source: str) -> dict:
    if not MIN_B <= len(data) <= MAX_B:
        raise KeptError(f"{len(data):,} bytes is not a plausible module image")
    binp, jsp = _paths(name)
    meta = {"name": name, "size": len(data), "crc32": zlib.crc32(data) & 0xFFFFFFFF,
            "sha256": hashlib.sha256(data).hexdigest(), "source": source,
            "kept": time.strftime("%Y-%m-%d %H:%M:%S")}
    binp.write_bytes(data)
    jsp.write_text(json.dumps(meta), encoding="utf-8")
    return meta


def listing() -> list:
    out = []
    for js in sorted(folder().glob("*.json")):
        try:
            meta = json.loads(js.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if NAME_RE.match(str(meta.get("name", ""))) and js.with_suffix(".bin").is_file():
            out.append(meta)
    return out


def load(name: str) -> tuple:
    """(name, bytes), proven against the SHA-256 written when it was kept."""
    binp, jsp = _paths(name)
    try:
        meta = json.loads(jsp.read_text(encoding="utf-8"))
        data = binp.read_bytes()
    except (OSError, ValueError) as exc:
        raise KeptError(f"{name} is not kept in this tool ({exc})") from exc
    if hashlib.sha256(data).hexdigest() != meta.get("sha256"):
        raise KeptError(f"{name} does not match the checksum it was kept with — refusing to use it")
    return name, data


def delete(name: str) -> None:
    binp, jsp = _paths(name)
    for p in (binp, jsp):
        try:
            p.unlink()
        except FileNotFoundError:
            pass
