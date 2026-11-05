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
        key="gateway_v1.14.0-rc1",
        kind=KIND_GATEWAY,
        version="v1.14.0-rc1",
        blob="gateway_opta_v1.14.0-rc1.bin",
        sha256="62289a406998d96acbb8e96a9b8dc91db83f3fda1d3255c94ebc59a8501e4376",
        source="LGS-Gateway-Arduino-Opta branch gw-1.14-eventlog @ 44251cc (2026-11-05; not tagged)",
        note="release candidate: event log, NTP, TCP console + network update, module depot, background module update, status lamps lit during a module update",
    ),
    BundledImage(
        key="gateway_v1.13.0",
        kind=KIND_GATEWAY,
        version="v1.13.0",
        blob="gateway_opta_v1.13.0.bin",
        sha256="56cd6a58adc137cdadc4c965b48a780cddd8b6351874cd83ee1563991ebc5d8c",
        source="LGS-Gateway-Arduino-Opta release v1.13.0",
        note="re-sync after a missing reply, echo-aware reply window",
    ),
    BundledImage(
        key="gateway_v1.12.4",
        kind=KIND_GATEWAY,
        version="v1.12.4",
        blob="gateway_opta_v1.12.4.bin",
        sha256="4f42f4ff75929221ecaaee8a81481b2b3f6545040e526441f39e890cd86af06c",
        source="LGS-Gateway-Arduino-Opta release v1.12.4",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="gateway_v1.12.3",
        kind=KIND_GATEWAY,
        version="v1.12.3",
        blob="gateway_opta_v1.12.3.bin",
        sha256="cebfc2add0ec892c101b7437820636fdab952b48aa74ed9fbdb4eabf70b5ba1a",
        source="LGS-Gateway-Arduino-Opta release v1.12.3",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="gateway_v1.12.2",
        kind=KIND_GATEWAY,
        version="v1.12.2",
        blob="gateway_opta_v1.12.2.bin",
        sha256="2d95547792ffcc349716a03381edb5fbc907c0d8bc05d5e825dd63c622226b79",
        source="LGS-Gateway-Arduino-Opta release v1.12.2",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.5.5_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.5.5",
        blob="module_g070_v3.5.5_factory.bin",
        sha256="9238b657c7455caea0fae1b06f19a281528ffce5aa14616f8f40b97a5af3723e",
        source="LGS-Standard-Module release v3.5.5 (factory image)",
        note="keeps its place after an unanswered request, for ST-Link",
    ),
    BundledImage(
        key="module_v3.5.5_ota",
        kind=KIND_MODULE_OTA,
        version="v3.5.5",
        blob="module_g070_v3.5.5_ota.bin",
        sha256="20c0c0f83b565bfad99c089f95b7da14089a160ef4a8af89284ec36321a4d966",
        source="LGS-Standard-Module release v3.5.5 (OTA image)",
        note="keeps its place after an unanswered request, over the bus",
    ),
    BundledImage(
        key="module_v3.5.4_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.5.4",
        blob="module_g070_v3.5.4_factory.bin",
        sha256="804ba05807e48b52f73bb9515dc1bc0231617bfe5401963dad2c0a07c4e4dd63",
        source="LGS-Standard-Module release v3.5.4 (factory image)",
        note="previous release, for rollback (factory)",
    ),
    BundledImage(
        key="module_v3.5.4_ota",
        kind=KIND_MODULE_OTA,
        version="v3.5.4",
        blob="module_g070_v3.5.4_ota.bin",
        sha256="a2a5982833507d9b60402b29c6682781159a6d51c1c4f407aac6f489eab35474",
        source="LGS-Standard-Module release v3.5.4 (OTA image)",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.5.0_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.5.0",
        blob="module_g070_v3.5.0_factory.bin",
        sha256="eb2b9dc6c33730e193c3a0b3fa51ada0a46111b108d984d704744b56d256fa15",
        source="LGS-Standard-Module release v3.5.0 (factory image)",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.5.0_ota",
        kind=KIND_MODULE_OTA,
        version="v3.5.0",
        blob="module_g070_v3.5.0_ota.bin",
        sha256="20dcfc9f95cd9ec2203f18b132b902ec8bf6b5457bdd56c4681206090684d9e9",
        source="LGS-Standard-Module release v3.5.0 (OTA image)",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.4.0_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.4.0",
        blob="module_g070_v3.4.0_factory.bin",
        sha256="17b73e0475382fb0094a0aa250b6afe8439e460a5e35fd212f123a12a507fa74",
        source="LGS-Standard-Module release v3.4.0 (factory image)",
        note="bootloader + app, for ST-Link",
    ),
    BundledImage(
        key="module_v3.4.0_ota",
        kind=KIND_MODULE_OTA,
        version="v3.4.0",
        blob="module_g070_v3.4.0_ota.bin",
        sha256="475fea876bd296f57fc8e166b388351537fa1eb5fa7f01d87137c2453e18fae8",
        source="LGS-Standard-Module release v3.4.0 (OTA image)",
        note="display 0-999 + folded v3.3.1/v3.3.2 hardening, over the bus",
    ),
    BundledImage(
        key="gateway_v1.12.0",
        kind=KIND_GATEWAY,
        version="v1.12.0",
        blob="gateway_opta_v1.12.0.bin",
        sha256="1db6cc4d73640e032dbda0a4a1a95c32760ca9c133c8dcafaba53f077d2ef4a0",
        source="LGS-Gateway-Arduino-Opta release v1.12.0",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.3.0_factory",
        kind=KIND_MODULE_FACTORY,
        version="v3.3.0",
        blob="module_g070_v3.3.0_factory.bin",
        sha256="7510b4f88f45f2fbb581422878c3f36b10ca180d2cb10f812f027e3fda421225",
        source="LGS-Standard-Module release v3.3.0 (factory image)",
        note="previous release, for rollback",
    ),
    BundledImage(
        key="module_v3.3.0_ota",
        kind=KIND_MODULE_OTA,
        version="v3.3.0",
        blob="module_g070_v3.3.0_ota.bin",
        sha256="779932105d1c211c404c6202453c4feb77561cca9485c01d2ffe8ff934dfd000",
        source="LGS-Standard-Module release v3.3.0 (OTA image)",
        note="previous release, for rollback",
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
