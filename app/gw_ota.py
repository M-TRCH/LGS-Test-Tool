"""The gateway runs the module OTA itself; the Tool starts it and reads it back.

Gateway side: LGS-Gateway-Arduino-Opta docs/design-gateway-ota.md (console verbs OTA START / STATUS / RESULT / ABORT, reached over
the unit 255 tunnel). The image comes from the gateway's own depot (gw_depot), the gateway drives the bus in the gaps between
everybody else's traffic, and it keeps the record of the last two runs. Nothing here moves firmware bytes or touches the bus: once
started, the Tool can be switched off.
"""
from __future__ import annotations

from . import gw_depot
from .gateway_config import GatewayError

STATE_TEXT = {"running", "scheduled", "done_ok", "done_with_failures", "aborted", "interrupted", "none"}
DEFAULTS = {"idle": 5, "group": 8, "apply_idle": 5, "apply_quiet": 300}   # = the gateway's own defaults (ota_runner.cpp)
LIMITS = {"idle": (1, 600), "group": (1, 8), "apply_idle": (1, 3600), "apply_quiet": (0, 86400)}


class OtaError(Exception):
    pass


MAX_NIGHTS = 14


def _hhmm(v, name: str) -> str:
    """"01:00", "1:00" or "0100" -> "0100"; anything else is refused."""
    text = str(v).strip().replace(":", "")
    if not text.isdigit() or len(text) not in (3, 4):
        raise OtaError(f"{name} must be a time like 01:00")
    text = text.zfill(4)
    if int(text[:2]) > 23 or int(text[2:]) > 59:
        raise OtaError(f"{name} must be a time like 01:00")
    return text


def options(raw: dict) -> dict:
    """Validated START options; unknown or out-of-range values are refused, not clamped."""
    out = {}
    for k, (lo, hi) in LIMITS.items():
        v = (raw or {}).get(k, DEFAULTS[k])
        try:
            v = int(v)
        except (TypeError, ValueError):
            raise OtaError(f"{k} must be a whole number")
        if not lo <= v <= hi:
            raise OtaError(f"{k} must be {lo}-{hi}")
        out[k] = v
    # Optional night window (gateway firmware >= 1.15.0): both times or neither. The gateway keeps to it by itself, on its
    # own clock, so the run can be started in the daytime and the Tool switched off.
    at, until = (raw or {}).get("at"), (raw or {}).get("until")
    if at or until:
        if not (at and until):
            raise OtaError("a night window needs both a start and an end time")
        out["at"], out["until"] = _hhmm(at, "start"), _hhmm(until, "end")
        if out["at"] == out["until"]:
            raise OtaError("the start and end of the window must differ")
        try:
            nights = int((raw or {}).get("nights", 1))
        except (TypeError, ValueError):
            raise OtaError("nights must be a whole number")
        if not 1 <= nights <= MAX_NIGHTS:
            raise OtaError(f"nights must be 1-{MAX_NIGHTS}")
        out["nights"] = nights
    return out


def _merge(rows) -> dict:
    d: dict = {}
    for r in rows:
        d.update(r)
    return d


def status(link) -> dict:
    """One gateway's OTA STATUS as a flat dict (state, phase, ch, group, chunk, paused_s, pending, verified, applied, failed...)."""
    try:
        r = link.command("OTA STATUS")
    except (OSError, GatewayError) as exc:
        raise OtaError(str(exc))
    if not r.ok:
        if "unknown_verb" in r.error_text:
            return {"state": "unsupported"}
        raise OtaError(r.error_text)
    return _merge(r.rows)


def status_row(link) -> dict:
    """status(), as the fields the page shows; an old firmware or an unreachable gateway is a row, not an exception."""
    try:
        return {"ota": status(link)}
    except OtaError as exc:
        return {"ota": {"state": "unreachable"}, "error": str(exc)[:160]}


def start(link, image_name: str, raw_opts: dict, ids: str = "") -> dict:
    """Find the depot slot holding `image_name`, arm a session, send OTA START."""
    opts = options(raw_opts)
    slots = gw_depot.slots(link)
    hit = next((s for s in slots if s["state"] == 2 and s["name"] == image_name), None)
    if not hit:
        raise OtaError(f"this gateway's depot holds no complete image named {image_name}")
    hello = link.hello("ota-start")
    if not hello.ok:
        raise OtaError("HELLO refused: " + hello.error_text)
    try:
        line = f"OTA START slot={hit['slot']} idle={opts['idle']} group={opts['group']} " \
               f"apply_idle={opts['apply_idle']} apply_quiet={opts['apply_quiet']}"
        if ids:
            line += f" ids={ids}"
        if "at" in opts:
            line += f" at={opts['at']} until={opts['until']} nights={opts['nights']}"
        r = link.command(line)
        if not r.ok:
            raise OtaError(_explain(r.error_text))
        return {"ok": True, **r.data}
    finally:
        try:
            link.bye()
        except (OSError, GatewayError):
            pass


def _explain(text: str) -> str:
    for key, msg in (("err=busy", "a run is already going on this gateway"),
                     ("err=locked", "the session was not armed"),
                     ("err=clock_unset", "the gateway's clock is not set (set it on the Gateway page)"),
                     ("err=usb_busy", "a PC used this gateway's USB port in the last minute"),
                     ("err=unknown_verb", "this gateway's firmware has no OTA runner"),
                     ("err=no_ids", "the gateway does not know its cabinet layout (set panel.cabinet or panel.shape)"),
                     ("want=at=HHMM", "this gateway's firmware has no night window (needs 1.15.0)")):
        if key in text:
            return msg
    return text


def abort(link) -> None:
    hello = link.hello("ota-abort")
    if not hello.ok:
        raise OtaError("HELLO refused: " + hello.error_text)
    try:
        r = link.command("OTA ABORT")
        if not r.ok:
            raise OtaError(_explain(r.error_text))
    finally:
        try:
            link.bye()
        except (OSError, GatewayError):
            pass


def result(link, n: int = 0) -> dict:
    """RESULT n: {"run": {...}, "modules": [{id, st, err, tries, fw}]}."""
    r = link.command(f"OTA RESULT {int(n)}")
    if not r.ok:
        raise OtaError(_explain(r.error_text) or "no such run")
    run, mods = {}, []
    for row in r.rows:
        if "run" in row:
            run = row
        elif "id" in row:
            mods.append(row)
    return {"run": run, "modules": mods}
