"""The gateway console and firmware update over Modbus TCP (fw >= v1.12.0).

On port 502, unit id 255 means "the gateway itself": function code 0x41
tunnels a `$LGS` command line in and pages the reply back out, and carries
the firmware-update subfunctions. Nothing sent to unit 255 ever touches the
RS485 bus. This exists because the Opta has no room for another socket —
lwIP there is compiled for four and the gateway already holds all four.

GatewayTcpLink wraps a CONNECTED pymodbus TCP client that someone else owns
(the worker's); it never opens or closes anything. Call `register_pdu(client)`
once after connect or every 0x41 reply decodes as an error.

Wire format (all big-endian; full layout in the firmware's gw_remote.h):
  0x01 CONSOLE_EXEC  line -> total u16 · off u16 · len u8 · data
  0x02 CONSOLE_READ  off u16 -> same shape
  0x10 FW_BEGIN      size u32 · crc32 u32 -> status u8
  0x11 FW_DATA       offset u32 · data[<=240] -> status u8 · received u32
  0x12 FW_STATUS     -> state u8 · received u32 · size u32 · capable u8 · boot_ver u8
  0x13 FW_APPLY      -> status u8 (answered BEFORE the reset)
  0x14 FW_ABORT      -> status u8

An exception response (0xC1) usually means fw < 1.12.0 or net.console=0.
"""
from __future__ import annotations

import struct
import time
from dataclasses import dataclass
from typing import Optional

from pymodbus.pdu import ModbusPDU

from .gateway_config import (DEFAULT_TIMEOUT_S, GatewayError, GwResponse,
                             GwVerbsMixin, LOG_TIMEOUT_S, parse_response_lines)

GW_SELF_UNIT = 255
GW_REMOTE_FC = 0x41

SUB_CONSOLE_EXEC = 0x01
SUB_CONSOLE_READ = 0x02
SUB_FW_BEGIN = 0x10
SUB_FW_DATA = 0x11
SUB_FW_STATUS = 0x12
SUB_FW_APPLY = 0x13
SUB_FW_ABORT = 0x14

FW_CHUNK = 240                  # request cap is 250 incl. sub + offset

FW_STATUS_TEXT = {
    0: "ok", 1: "locked — HELLO first", 2: "gateway storage error",
    3: "image size refused", 4: "busy", 5: "sequence mismatch",
    6: "no upload in progress", 7: "CRC mismatch on the staged file",
    8: "upload incomplete", 9: "bootloader has no OTA support",
    10: "apply library error",
}

FW_STATE_IDLE, FW_STATE_RECEIVING, FW_STATE_STAGED, FW_STATE_ERROR = 0, 1, 2, 3


class GwRawPDU(ModbusPDU):
    """FC 0x41 both ways: sub byte + opaque payload."""
    function_code = GW_REMOTE_FC
    rtu_byte_count_pos = 0

    def __init__(self, sub: int = 0, payload: bytes = b"",
                 dev_id: int = GW_SELF_UNIT, transaction_id: int = 0) -> None:
        super().__init__(dev_id=dev_id, transaction_id=transaction_id)
        self.sub = sub
        self.payload = bytes(payload)

    def encode(self) -> bytes:
        return bytes([self.sub]) + self.payload

    def decode(self, data: bytes) -> None:
        self.sub = data[0] if data else 0
        self.payload = bytes(data[1:])


def register_pdu(client) -> None:
    """Teach a pymodbus client to decode 0x41 replies. Once per client."""
    client.register(GwRawPDU)


@dataclass(frozen=True)
class FwStatus:
    state: int
    received: int
    size: int
    ota_capable: bool
    boot_ver: int


class GatewayTcpLink(GwVerbsMixin):
    """GwVerbsMixin over the tunnel — same verbs, snapshot, set_many as USB."""

    def __init__(self, client, *, timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        self._client = client
        self._timeout = timeout_s

    # ── raw exchange ───────────────────────────────────────────────────────
    def _execute(self, sub: int, payload: bytes = b"") -> GwRawPDU:
        rsp = self._client.execute(False, GwRawPDU(sub, payload))
        if rsp is None or rsp.isError():
            raise GatewayError(
                f"gateway refused FC41/{sub:02X}: {rsp} — needs fw >= 1.12.0 "
                f"and net.console=1")
        return rsp

    # ── console over the tunnel ────────────────────────────────────────────
    def command(self, line: str, *, timeout_s: Optional[float] = None) -> GwResponse:
        # LOG is the one verb whose full answer (100 lines ≈ 9 KB) needs
        # many READ round trips; everything else fits a handful.
        deadline = time.monotonic() + (timeout_s or max(self._timeout,
                                                        LOG_TIMEOUT_S))
        rsp = self._execute(SUB_CONSOLE_EXEC, line.encode("ascii", "ignore"))
        total, _, ln = struct.unpack(">HHB", rsp.payload[:5])
        text = bytearray(rsp.payload[5:5 + ln])
        while len(text) < total and time.monotonic() < deadline:
            more = self._execute(SUB_CONSOLE_READ,
                                 struct.pack(">H", len(text)))
            _, _, ln = struct.unpack(">HHB", more.payload[:5])
            if ln == 0:
                break
            text += more.payload[5:5 + ln]
        # parse_response_lines reports a cut answer as err=truncated, which
        # is also what a console-buffer overflow on the gateway looks like.
        return parse_response_lines(
            text.decode("ascii", "replace").split("\r\n"))

    # ── firmware update ────────────────────────────────────────────────────
    def fw_status(self) -> FwStatus:
        rsp = self._execute(SUB_FW_STATUS)
        state, received, size, capable, boot_ver = struct.unpack(
            ">BIIBB", rsp.payload[:11])
        return FwStatus(state, received, size, bool(capable), boot_ver)

    def fw_begin(self, size: int, crc32: int) -> int:
        rsp = self._execute(SUB_FW_BEGIN, struct.pack(">II", size, crc32))
        return rsp.payload[0]

    def fw_data(self, offset: int, chunk: bytes) -> tuple:
        """(status, received) — on 5/seq_mismatch, `received` is where the
        gateway wants the stream to resume."""
        rsp = self._execute(SUB_FW_DATA, struct.pack(">I", offset) + chunk)
        return rsp.payload[0], struct.unpack(">I", rsp.payload[1:5])[0]

    def fw_apply(self) -> int:
        rsp = self._execute(SUB_FW_APPLY)
        return rsp.payload[0]

    def fw_abort(self) -> int:
        rsp = self._execute(SUB_FW_ABORT)
        return rsp.payload[0]
