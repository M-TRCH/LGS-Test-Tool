"""Firmware images shipped inside the tool.

On site there is no PlatformIO, no GitHub and often no network, so the three
jobs that need a binary — commissioning a blank module over ST-Link, updating
a module over the air, updating the gateway over DFU — each ship with the
released image they normally want. Uploading a file still works and still
wins; this only removes the hunt for it.

Only **released** images belong here. A work-in-progress build in this list
is a build someone will flash into a cabinet by accident.

Every entry carries the SHA-256 of the release asset it was copied from, and
`load()` refuses an image that does not match: a bundled binary that has been
swapped or truncated must fail loudly, not flash quietly.
"""
from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

# What a bundled image is for. The three consumers each filter on one of
# these, so an OTA image can never be offered where a factory image is meant.
KIND_MODULE_FACTORY = "module_factory"   # ST-Link, boot + app, carries the ID block
KIND_MODULE_OTA = "module_ota"           # over Modbus, app only, linked at 0x1000
KIND_GATEWAY = "gateway"                 # Opta, over DFU


@dataclass(frozen=True)
class BundledImage:
    key: str            # stable id used by the UI
    kind: str
    version: str
    blob: str           # file name under app/blobs/
    sha256: str         # of the release asset
    source: str         # where it came from, for the operator and for us
    note: str = ""      # shown next to the choice

    @property
    def label(self) -> str:
        return f"{self.version} — {self.note}" if self.note else self.version

    @property
    def filename(self) -> str:
        """The name this image is recorded under (commission log, dialogs)."""
        return self.blob


# Newest first: the UI offers the first entry of a kind as its default.
IMAGES: tuple = (
    BundledImage(
        key="gateway_v1.9.0",
        kind=KIND_GATEWAY,
        version="v1.9.0",
        blob="gateway_opta_v1.9.0.bin",
        sha256="19ae8721632e158f19330a00a9d2ab47fbb8fd84c3027c3fc622306cb627eec8",
        source="LGS-Gateway-Arduino-Opta release v1.9.0",
        note="panel buttons/lamps, 4 scheduled resets, any sweep shape",
    ),
    BundledImage(
        key="module_v3.2.0_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.2.0",
        blob="module_g070_v3.2.0_factory.bin",
        sha256="7972a50a1d3c4764e939140fbe5bdf3095138b3ebb50efa3d11d0b926ac2bb4d",
        source="LGS-Standard-Module release v3.2.0 (factory image)",
        note="bootloader + app, for ST-Link",
    ),
    BundledImage(
        key="module_v3.2.0_ota",
        kind=KIND_MODULE_OTA,
        version="v3.2.0",
        blob="module_g070_v3.2.0_ota.bin",
        sha256="d0a27512ea944b386df460c7560a752a90cab915d4d9c53d01d1e0294b4ce307",
        source="LGS-Standard-Module release v3.2.0 (OTA image)",
        note="app only, over the bus",
    ),
)


class BundleError(Exception):
    """A bundled image is missing or is not the image it claims to be."""


def _blobs_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS")) / "app" / "blobs"
    return Path(__file__).resolve().parent / "blobs"


def for_kind(kind: str) -> list:
    return [img for img in IMAGES if img.kind == kind]


def by_key(key: str):
    for img in IMAGES:
        if img.key == key:
            return img
    return None


def load(image: BundledImage) -> bytes:
    """The image's bytes, proven to be the ones that were released."""
    path = _blobs_dir() / image.blob
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise BundleError(f"{image.blob} is missing from this build ({exc}). "
                          f"Upload the image instead.") from exc
    digest = hashlib.sha256(data).hexdigest()
    if digest != image.sha256:
        raise BundleError(
            f"{image.blob} does not match the released {image.version} image "
            f"(sha256 {digest[:12]}… instead of {image.sha256[:12]}…). "
            f"Refusing to flash it — upload the image instead.")
    return data
