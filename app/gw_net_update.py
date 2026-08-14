"""Update the Opta gateway's firmware over the network — no USB, no DFU.

The image streams through the FC 0x41 tunnel (gateway_tcp) into UPDATE.BIN
on the gateway's QSPI, is CRC-verified there by reading it back, and only
then does the gateway write the bootloader's apply-magic and reboot itself.
A dropped socket or power cut mid-upload leaves a file nothing ever applies;
re-running starts clean.

Mirrors opta_update.run_update in shape (steps, ota.Line/Progress/Done
events, ops indirection) so the UI drains it with the code it already has.
Unlike the USB path it RECONNECTS at the end and reads the version back —
no cable means nobody is watching a boot banner, so the proof has to come
over the wire. Measured on the bench: 297 KB uploads in ~24 s, the
bootloader copies it in ~3 s, back on the network ~8 s after APPLY.
"""
from __future__ import annotations

import time
import zlib
from dataclasses import dataclass
from typing import Callable

from . import gateway_tcp
from .gateway_config import GatewayError
from .ota import Done, Line, Progress

MIN_IMAGE_B = 50_000
MAX_IMAGE_B = 786_432           # boards/opta.json upload.maximum_size
RECONNECT_WAIT_S = 90.0         # APPLY -> bootloader copy -> boot -> link
RECONNECT_POLL_S = 2.0


@dataclass
class GwNetUpdateConfig:
    image: bytes = b""
    filename: str = ""


class GwNetOps:
    """What the runner needs from the worker (all on the worker thread)."""

    def link(self) -> gateway_tcp.GatewayTcpLink: ...
    def drop_client(self) -> None: ...
    def reconnect(self) -> bool: ...
    def sleep(self, seconds: float) -> None: ...


def run_update(ops, cfg: GwNetUpdateConfig, emit: Callable, cancel) -> bool:
    def say(text: str, level: str = "info") -> None:
        emit(Line(text, level))

    def fail(text: str) -> bool:
        emit(Done(ok=False, summary=text))
        return False

    image = cfg.image
    if not (MIN_IMAGE_B <= len(image) <= MAX_IMAGE_B):
        return fail(f"{cfg.filename or 'image'}: {len(image):,} bytes is not "
                    f"a plausible gateway image")
    crc = zlib.crc32(image) & 0xFFFFFFFF

    try:
        link = ops.link()

        # ── 1/5 capability ────────────────────────────────────────────────
        say("1/5 asking the gateway about its bootloader")
        st = link.fw_status()
        if not st.ota_capable:
            return fail(f"the gateway's bootloader (v{st.boot_ver}) cannot "
                        f"apply updates from QSPI — update over USB instead")
        old = link.ping()
        old_fw = old.data.get("fw", "?") if old.ok else "?"
        say(f"gateway fw {old_fw}, bootloader ok")

        # ── 2/5 arm + clean slate ─────────────────────────────────────────
        say("2/5 arming a session")
        hello = link.hello("net-update")
        if not hello.ok:
            return fail("HELLO refused: " + hello.error_text)
        link.fw_abort()

        status = link.fw_begin(len(image), crc)
        if status != 0:
            return fail("FW_BEGIN: "
                        + gateway_tcp.FW_STATUS_TEXT.get(status, str(status)))

        # ── 3/5 upload ────────────────────────────────────────────────────
        say(f"3/5 uploading {len(image):,} bytes")
        off = 0
        resynced = False
        while off < len(image):
            if cancel.is_set():
                link.fw_abort()
                return fail("cancelled — nothing was applied")
            chunk = image[off:off + gateway_tcp.FW_CHUNK]
            status, received = link.fw_data(off, chunk)
            if status == 5 and not resynced:        # seq_mismatch: resume once
                say(f"stream resync at {received:,}", "warn")
                off, resynced = received, True
                continue
            if status != 0:
                link.fw_abort()
                return fail("FW_DATA: "
                            + gateway_tcp.FW_STATUS_TEXT.get(status, str(status)))
            off += len(chunk)
            emit(Progress(off, len(image)))

        st = link.fw_status()
        if st.state != gateway_tcp.FW_STATE_STAGED or st.received != len(image):
            return fail(f"staging incomplete: state={st.state} "
                        f"received={st.received:,}/{len(image):,}")

        # ── 4/5 verify + apply ────────────────────────────────────────────
        say("4/5 gateway is CRC-checking the staged file")
        status = link.fw_apply()
        if status != 0:
            return fail("FW_APPLY: "
                        + gateway_tcp.FW_STATUS_TEXT.get(status, str(status)))
        say("applied — the gateway is rebooting onto the new image", "ok")
    except (OSError, GatewayError) as exc:
        return fail(f"{type(exc).__name__}: {exc}")

    # ── 5/5 reconnect + prove it ──────────────────────────────────────────
    say("5/5 waiting for the gateway to come back")
    ops.drop_client()
    deadline = time.monotonic() + RECONNECT_WAIT_S
    ops.sleep(6.0)                          # reset + copy window, no point knocking
    while time.monotonic() < deadline:
        if cancel.is_set():
            return fail("cancelled while waiting — check the gateway yourself")
        if ops.reconnect():
            try:
                res = ops.link().ping()
            except (OSError, GatewayError):
                res = None
            if res is not None and res.ok:
                new_fw = res.data.get("fw", "?")
                ok = new_fw != "?" and (new_fw != old_fw or old_fw == "?")
                # Same-version re-flash is legitimate (recovery); say what
                # happened and let the operator judge.
                emit(Done(ok=True, summary=(
                    f"gateway back on fw {new_fw}"
                    + ("" if ok else f" (was {old_fw} — same version)"))))
                return True
        ops.sleep(RECONNECT_POLL_S)
    return fail(f"the gateway did not come back within "
                f"{int(RECONNECT_WAIT_S)} s — check it over USB")
