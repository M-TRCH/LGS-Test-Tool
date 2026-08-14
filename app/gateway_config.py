"""Client for the Opta gateway's `$LGS` text console.

The gateway is not a Modbus device — it sits between the PC and the bus — so
its configuration travels as ASCII lines on the same COM port, on bytes the
Modbus bridge rejects. This module speaks that protocol with plain pyserial;
pymodbus is deliberately not involved.

    request  := "$LGS" SP VERB (SP ARG)* CRLF
    response := "#DATA ..."*  then exactly one "#OK ..." or "#ERR ..."

Reading stops at the terminal line, so a response never bleeds into the next
command.

Since gateway fw v1.12.0 the same console also rides Modbus TCP (unit 255 /
FC 0x41 — see gateway_tcp.GatewayTcpLink). The verbs live in GwVerbsMixin so
both links share one protocol implementation; the only thing a link owes the
mixin is `command(line, *, timeout_s) -> GwResponse`.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import serial

GW_PREFIX = "$LGS"
GW_BAUD = 115200

# 1200 baud on an Opta triggers the bootloader (the 1200 bps touch), which
# would drop the running firmware off the bus mid-session.
FORBIDDEN_BAUDS = {1200}

DEFAULT_TIMEOUT_S = 1.0
SAVE_TIMEOUT_S = 3.0
# A LOG dump is up to 100 lines and the firmware feeds its watchdog per
# line, so the wait is bounded by the console itself — but it is well past
# the 1 s default.
LOG_TIMEOUT_S = 3.0


class GatewayError(Exception):
    pass


def _parse_pairs(text: str) -> dict:
    out: dict = {}
    for token in text.split():
        if "=" in token:
            key, _, value = token.partition("=")
            out[key] = value
    return out


@dataclass(frozen=True)
class GwResponse:
    ok: bool
    verb: str = ""
    data: dict = field(default_factory=dict)        # from the #OK / #ERR line
    rows: tuple = ()                                # one dict per #DATA line
    err: str = ""
    lines: tuple = ()                               # raw, for the log pane

    @property
    def error_text(self) -> str:
        if self.ok:
            return ""
        detail = " ".join(f"{k}={v}" for k, v in self.data.items())
        return detail or self.err or "error"


@dataclass(frozen=True)
class GwSnapshot:
    ok: bool
    info: dict = field(default_factory=dict)        # merged INFO fields
    settings: dict = field(default_factory=dict)    # key -> active value
    staged: dict = field(default_factory=dict)      # key -> staged value (differs only)
    note: str = ""


@dataclass(frozen=True)
class GwActionResult:
    ok: bool
    steps: tuple = ()                               # human-readable trace
    note: str = ""
    values: dict = field(default_factory=dict)      # key -> value the caller
                                                    # should now offer to write


def parse_response_lines(lines) -> GwResponse:
    """Console text lines -> GwResponse. Shared by every transport: the
    serial link feeds it as lines arrive, the TCP tunnel after reassembling
    the paged buffer. A missing terminal line means the answer was cut."""
    raw: list[str] = []
    rows: list[dict] = []
    for text in lines:
        text = text.strip()
        if not text:
            continue
        raw.append(text)
        if text.startswith("#DATA"):
            rows.append(_parse_pairs(text[5:]))
        elif text.startswith("#OK") or text.startswith("#ERR"):
            ok = text.startswith("#OK")
            body = text[3:] if ok else text[4:]
            parts = body.split()
            verb = parts[0] if parts and "=" not in parts[0] else ""
            return GwResponse(ok=ok, verb=verb, data=_parse_pairs(body),
                              rows=tuple(rows), lines=tuple(raw))
    return GwResponse(ok=False, err="truncated", rows=tuple(rows), lines=tuple(raw))


class GwVerbsMixin:
    """Every console verb and composite, transport-blind.

    The one contract: `self.command(line, *, timeout_s=None) -> GwResponse`.
    """

    def command(self, line: str, *, timeout_s: Optional[float] = None) -> GwResponse:
        raise NotImplementedError

    # ── verbs ──────────────────────────────────────────────────────────────
    def ping(self) -> GwResponse:
        return self.command("PING")

    def info(self) -> GwResponse:
        return self.command("INFO")

    def get_all(self) -> GwResponse:
        return self.command("GET")

    def get(self, key: str) -> GwResponse:
        return self.command(f"GET {key}")

    def hello(self, who: str = "LGS-Test-Tool") -> GwResponse:
        return self.command(f"HELLO {who}")

    def bye(self) -> GwResponse:
        return self.command("BYE")

    # The console drops any line over ~120 characters WHOLE (the reply is a
    # timeout, not an error), and parses at most 11 key=value pairs per line.
    # So SET is chunked: each line stays under both limits, and one bad chunk
    # aborts the rest — half-applied staging would be worse than none, and
    # DISCARD after a failure is the caller's move.
    _SET_LINE_MAX = 100          # command body budget, margin under 120
    _SET_PAIRS_MAX = 8

    def set_many(self, changes: dict) -> GwResponse:
        chunk: list = []
        length = 0
        responses: list = []

        def flush() -> Optional[GwResponse]:
            nonlocal chunk, length
            if not chunk:
                return None
            res = self.command("SET " + " ".join(chunk))
            chunk, length = [], 0
            return res

        for k, v in changes.items():
            pair = f"{k}={v}"
            if chunk and (len(chunk) >= self._SET_PAIRS_MAX
                          or length + 1 + len(pair) > self._SET_LINE_MAX):
                res = flush()
                if res is not None and not res.ok:
                    return res
                responses.append(res)
            chunk.append(pair)
            length += (1 if length else 0) + len(pair)
        res = flush()
        if res is not None:
            responses.append(res)
        if res is not None and not res.ok:
            return res
        # One summary response so callers keep reading a single result.
        total = sum(int(r.data.get("n", 0) or 0) for r in responses if r)
        last = responses[-1] if responses else None
        if last is None:
            return GwResponse(ok=True, verb="SET", data={"n": "0"})
        return GwResponse(ok=True, verb="SET",
                          data={"n": str(total),
                                "dirty": last.data.get("dirty", "?")},
                          lines=tuple(f"#OK SET n={total} (chunked "
                                      f"x{len(responses)})".split("\n")))

    def save(self) -> GwResponse:
        return self.command("SAVE", timeout_s=SAVE_TIMEOUT_S)

    def discard(self) -> GwResponse:
        return self.command("DISCARD")

    def defaults(self) -> GwResponse:
        return self.command("DEFAULTS", timeout_s=SAVE_TIMEOUT_S)

    def reboot(self) -> GwResponse:
        return self.command("REBOOT")

    def log(self, n: int) -> GwResponse:
        """Newest `n` event-log records (fw >= 1.11.0; older firmware answers
        err=unknown_verb, which arrives as an ordinary failed response)."""
        return self.command(f"LOG {int(n)}", timeout_s=LOG_TIMEOUT_S)

    # ── composites ─────────────────────────────────────────────────────────
    @staticmethod
    def _split_values(res: GwResponse) -> tuple:
        """GET prints `key=<active>` plus `staged=<pending>` when they differ."""
        settings: dict = {}
        staged: dict = {}
        for row in res.rows:
            for key, value in row.items():
                if key == "staged":
                    if settings:
                        staged[list(settings)[-1]] = value
                else:
                    settings[key] = value
        return settings, staged

    def staged_values(self) -> dict:
        """Keys the gateway currently has staged, with their pending values."""
        res = self.get_all()
        return self._split_values(res)[1] if res.ok else {}

    def snapshot(self) -> GwSnapshot:
        """INFO + GET in one session — what the Gateway tab renders."""
        info = self.info()
        if not info.ok:
            return GwSnapshot(False, note=info.error_text or "no reply from the gateway")
        merged: dict = {}
        for row in info.rows:
            merged.update(row)

        values = self.get_all()
        if not values.ok:
            return GwSnapshot(False, info=merged, note=values.error_text)
        settings, staged = self._split_values(values)
        return GwSnapshot(True, info=merged, settings=settings, staged=staged)


class GatewayLink(GwVerbsMixin):
    """One short-lived console session over USB serial. Open, use, close."""

    def __init__(self, port: str, *, baud: int = GW_BAUD,
                 timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
        if baud in FORBIDDEN_BAUDS:
            raise GatewayError(f"baud {baud} would put the Opta into its bootloader")
        self._port = port
        self._baud = baud
        self._timeout = timeout_s
        self._ser: Optional[serial.Serial] = None

    # ── lifecycle ──────────────────────────────────────────────────────────
    def open(self) -> None:
        self._ser = serial.Serial(self._port, self._baud, timeout=0.05)
        self._ser.reset_input_buffer()

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            finally:
                self._ser = None

    def __enter__(self) -> "GatewayLink":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ── transport ──────────────────────────────────────────────────────────
    def command(self, line: str, *, timeout_s: Optional[float] = None) -> GwResponse:
        if self._ser is None:
            raise GatewayError("link is not open")
        deadline = time.monotonic() + (timeout_s or self._timeout)

        self._ser.reset_input_buffer()
        self._ser.write(f"{GW_PREFIX} {line}\r\n".encode("ascii", "ignore"))
        self._ser.flush()

        raw: list[str] = []
        rows: list[dict] = []
        buf = b""
        while time.monotonic() < deadline:
            chunk = self._ser.read(256)
            if chunk:
                buf += chunk
            while b"\n" in buf:
                one, _, buf = buf.partition(b"\n")
                text = one.decode("ascii", "replace").strip()
                if not text:
                    continue
                raw.append(text)
                if text.startswith("#DATA"):
                    rows.append(_parse_pairs(text[5:]))
                elif text.startswith("#OK") or text.startswith("#ERR"):
                    ok = text.startswith("#OK")
                    body = text[3:] if ok else text[4:]
                    parts = body.split()
                    verb = parts[0] if parts and "=" not in parts[0] else ""
                    return GwResponse(ok=ok, verb=verb, data=_parse_pairs(body),
                                      rows=tuple(rows), lines=tuple(raw))
        return GwResponse(ok=False, err="timeout", rows=tuple(rows), lines=tuple(raw))


def probe(port: str, *, timeout_s: float = 0.8) -> Optional[dict]:
    """Return the PING fields when a gateway answers on this port, else None.

    Only ever called on the port the user selected: opening an arbitrary COM
    port can reset whatever Arduino is on the other end.
    """
    try:
        with GatewayLink(port, timeout_s=timeout_s) as link:
            res = link.ping()
            return dict(res.data) if res.ok else None
    except (serial.SerialException, GatewayError, OSError):
        return None
