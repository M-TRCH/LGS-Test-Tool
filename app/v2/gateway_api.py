"""Gateway page backend: read settings, apply edits, a few actions.

Every call is one short console session over the TCP tunnel (unit 255 /
FC 0x41): connect, do the work, BYE, close. Nothing holds a client slot
between calls, and calls to one gateway are serialised here so two browsers
cannot interleave HELLO/SET/SAVE on it.

The write sequence is the one the classic Gateway tab proved on the bench:
HELLO, DISCARD (staged edits left by an interrupted session must not ride this
SAVE), SET, SAVE, BYE.
"""
import threading
import time
from datetime import datetime

from .. import i18n, lgs_map

_locks: dict = {}
_locks_guard = threading.Lock()

# Volatile console switches (not stored settings, reset at every boot).
VOLATILE = ("RESYNC", "EXC")
ACTIONS = ("reboot", "defaults", "discard", "time", "resync", "exc", "ap_on", "ap_off", "ap_ssid", "ap_pass", "ap_show")


def _lock(host: str, port: int) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault((host, port), threading.Lock())


class _Session:
    """with _Session(host, port) as link: ... -- closes the socket on exit."""

    def __init__(self, host: str, port: int, timeout_s: float = 5.0) -> None:
        self.host, self.port, self.timeout_s = host, port, timeout_s
        self.client = None
        self._lock = _lock(host, port)

    def __enter__(self):
        from ..gateway_tcp import GatewayTcpLink, register_pdu
        from ..transports import TcpSettings, make_client
        self._lock.acquire()
        try:
            self.client = make_client(TcpSettings(host=self.host, port=self.port,
                                                  timeout_s=self.timeout_s), retries=0)
            if not self.client.connect():
                raise ConnectionError(f"cannot connect to {self.host}:{self.port}")
            register_pdu(self.client)
            return GatewayTcpLink(self.client, timeout_s=self.timeout_s)
        except BaseException:
            self._release()
            raise

    def _release(self) -> None:
        try:
            if self.client is not None:
                self.client.close()
        finally:
            self.client = None
            self._lock.release()

    def __exit__(self, *exc) -> None:
        self._release()


def wall_epoch() -> int:
    """This PC's wall clock as seconds since 1970, LOCAL (not UTC): the
    gateway keeps the time on the wall in front of the cabinet."""
    now = datetime.now().astimezone()
    return int(now.timestamp() + now.utcoffset().total_seconds())


def _label(key: str) -> dict:
    out = {}
    for lang in ("th", "en"):
        e = i18n.TEXTS.get(f"gwf.{key}")
        h = i18n.TEXTS.get(f"gwf.{key}.hint")
        out[lang] = {"label": (e or {}).get(lang, ""), "hint": (h or {}).get(lang, "")}
    return out


def shape_check(settings: dict, layout_key: str) -> dict:
    """Does the gateway's cabinet setting agree with the cabinet type saved for
    this site? Same rule as the classic Gateway tab: a catalogue cabinet wants
    its `panel.cabinet` code and no `panel.shape`; any other wants its row
    widths as `panel.shape` (gateway >= 1.9.0). `fix` is what to STAGE, never
    something written here."""
    if not layout_key:
        return {}
    layout = lgs_map.layout_by_key(layout_key)
    has_shape = "panel.shape" in settings
    cab = str(settings.get("panel.cabinet", ""))
    shape = str(settings.get("panel.shape", "0"))
    if layout.panel_cabinet:
        agreed = (not has_shape or lgs_map.same_shape(shape, "0")) and cab == layout.panel_cabinet
        fix = {"panel.cabinet": layout.panel_cabinet}
        if has_shape:
            fix["panel.shape"] = "0"
        stray = has_shape and not lgs_map.same_shape(shape, "0")
        why = ("a stray panel.shape overrides the cabinet code" if stray
               else f"gateway has panel.cabinet={cab or '?'}")
    else:
        want = lgs_map.format_custom_widths(lgs_map.layout_widths(layout))
        agreed = has_shape and lgs_map.same_shape(shape, want)
        fix = {"panel.shape": want} if has_shape else {}
        why = f"gateway shape is {shape}, this cabinet needs {want}"
    return {"layout": layout.key, "label": layout.label, "agreed": bool(agreed),
            "fix": fix if not agreed else {}, "fixable": bool(fix), "why": "" if agreed else why}


def read(host: str, port: int = 502, cabinet: str = "") -> dict:
    """Snapshot (INFO + GET) plus per-key flags from HELP and bilingual labels."""
    with _Session(host, port) as link:
        snap = link.snapshot()
        if not snap.ok:
            return {"ok": False, "error": snap.note or "no answer"}
        helped = link.command("HELP")
    flags = {}
    for row in (helped.rows if helped.ok else ()):
        if "key" in row:
            flags[row["key"]] = {"ro": row.get("ro") == "1", "reboot": row.get("reboot") == "1"}
    keys = []
    for k, v in snap.settings.items():
        f = flags.get(k, {})
        keys.append({"key": k, "value": v, "staged": snap.staged.get(k),
                     "ro": bool(f.get("ro")), "reboot": bool(f.get("reboot")),
                     "text": _label(k)})
    return {"ok": True, "info": snap.info, "keys": keys, "shape": shape_check(snap.settings, cabinet),
            "verbs": (helped.rows[0].get("verbs", "") if helped.ok and helped.rows else "")}


def apply(host: str, port: int, changes: dict) -> dict:
    """Write `changes` and save. All or nothing: on any failure the staged set
    is discarded, so the gateway is never left half-edited."""
    steps: list[str] = []
    if not changes:
        return {"ok": True, "steps": ["nothing to change"], "pending_reboot": ""}
    with _Session(host, port) as link:
        hello = link.hello("LGS-Test-Tool v2")
        if not hello.ok:
            return {"ok": False, "error": hello.error_text or "HELLO refused", "steps": steps}
        steps.append("session armed")
        try:
            d = link.discard()
            if not d.ok:
                return {"ok": False, "error": d.error_text, "steps": steps}
            res = link.set_many(changes)
            steps.append(f"SET {len(changes)} key(s): " + ("ok" if res.ok else res.error_text))
            if not res.ok:
                link.discard()
                return {"ok": False, "error": res.error_text, "steps": steps}
            res = link.save()
            if not res.ok:
                link.discard()
                return {"ok": False, "error": res.error_text, "steps": steps}
            applied = res.data.get("applied", "-")
            pending = res.data.get("pending_reboot", "")
            steps.append(f"SAVE applied={applied}" + (f", needs reboot: {pending}" if pending else ""))
            return {"ok": True, "steps": steps, "pending_reboot": pending, "applied": applied}
        finally:
            try:
                link.bye()
            except Exception:                                    # noqa: BLE001
                pass


def _ap_action(link, name: str, value) -> dict:
    """The service Wi-Fi AP verbs (gateway >= 1.15, Opta WiFi). The password is never read back, only written: the
    value is checked here the way the gateway checks it, so a typo is told apart from a refusal."""
    v = "" if value is None else str(value)
    if name == "ap_on":
        try:
            mins = int(v or "30")
        except ValueError:
            return {"ok": False, "error": "minutes must be a number"}
        if not 1 <= mins <= 480:
            return {"ok": False, "error": "minutes must be 1-480"}
        line = f"AP ON min={mins} bridge=0"
    elif name == "ap_off":
        line = "AP OFF"
    elif name == "ap_show":
        line = "AP SHOW"
    elif name in ("ap_ssid", "ap_pass"):
        lo, hi = (1, 31) if name == "ap_ssid" else (8, 31)
        if not lo <= len(v) <= hi or any(c <= " " or c > "~" for c in v):
            return {"ok": False, "error": f"{lo}-{hi} printable characters, no spaces"}
        line = ("AP SSID " if name == "ap_ssid" else "AP PASS ") + v
    else:
        return {"ok": False, "error": "unknown action"}
    h = link.hello("LGS-Test-Tool v2")
    if not h.ok:
        return {"ok": False, "error": h.error_text or "HELLO refused"}
    res = link.command(line)
    try:
        link.bye()
    except Exception:                                            # noqa: BLE001
        pass
    if name == "ap_show":
        row = res.rows[0] if res.ok and res.rows else {}
        pw = row.get("ap.pass", "-")
        return {"ok": res.ok, "error": "" if res.ok else res.error_text, "ssid": row.get("ap.ssid", ""),
                "pass": "" if pw == "-" else pw, "url": row.get("ap.url", "")}
    return {"ok": res.ok, "error": "" if res.ok else res.error_text,
            "detail": "" if name == "ap_pass" else " ".join(res.lines[:1])}


def action(host: str, port: int, name: str, value=None) -> dict:
    if name not in ACTIONS:
        return {"ok": False, "error": f"unknown action '{name}'"}
    with _Session(host, port) as link:
        if name == "time":
            res = link.command(f"TIME {wall_epoch()}")
            return {"ok": res.ok, "error": "" if res.ok else res.error_text,
                    "detail": res.data.get("now", "")}
        if name in ("resync", "exc"):
            v = "1" if str(value) in ("1", "true", "True", "on") else "0"
            h = link.hello("LGS-Test-Tool v2")
            if not h.ok:
                return {"ok": False, "error": h.error_text or "HELLO refused"}
            res = link.command(f"{name.upper()} {v}")
            link.bye()
            return {"ok": res.ok, "error": "" if res.ok else res.error_text, "detail": v}
        if name.startswith("ap_"):
            return _ap_action(link, name, value)
        h = link.hello("LGS-Test-Tool v2")
        if not h.ok:
            return {"ok": False, "error": h.error_text or "HELLO refused"}
        if name == "discard":
            res = link.discard()
        elif name == "defaults":
            res = link.defaults()
        else:                                    # reboot: the answer may not arrive
            try:
                res = link.reboot()
            except Exception:                                    # noqa: BLE001
                return {"ok": True, "detail": "rebooting"}
            time.sleep(0.2)
        try:
            link.bye()
        except Exception:                                        # noqa: BLE001
            pass
        return {"ok": res.ok, "error": "" if res.ok else res.error_text}
