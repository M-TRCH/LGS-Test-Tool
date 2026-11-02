"""Web UI password (v1.9.6).

Until now the server listened on 0.0.0.0 with no authentication at all: anyone
on the LAN could open the page and press Danger, fire an OTA or change a
gateway. This gate closes that, without costing the double-click story:

* NO password set  -> behaves exactly as before (open). Nothing to configure
  on a bench laptop.
* password set     -> every page, asset, download and WebSocket needs a signed
  session cookie; anything else is sent to /login.

The password lives only as a PBKDF2 hash in data/auth.json -- a separate file
from config.json, so copying a config around never copies the credential.
The same file holds the cookie-signing secret. Setting or removing the
password rotates that secret, which signs every existing browser out.

Core functions here import nothing from NiceGUI so run.py can set a password
from the command line before the app (and its Modbus worker) is touched;
install() does the web wiring and imports lazily.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from html import escape
from urllib.parse import parse_qs, quote, urlsplit

# Module level, not inside install(): FastAPI resolves the route annotations
# by name, and under `from __future__ import annotations` a function-local
# `Request` is invisible to it (every route answered 422).
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from . import config_store

COOKIE = "lgs_tt_session"
SESSION_S = 7 * 24 * 3600
MIN_LEN = 6
_ITERS = 200_000

# Paths that must stay reachable without a session: the login form itself and
# the page guard's "is the server back" probe (page_guard.PROBE_PATH), which
# returns a constant and exposes nothing.
_OPEN_PATHS = ("/login", "/_lgs/alive", "/v2/static/app.css", "/v2/static/fonts.css")
# The login page wears the v2 look, so its stylesheet and fonts load before
# anyone has signed in. Styles and font files only: no script, no data.
_OPEN_PREFIXES = ("/v2/static/fonts/",)

# Brute-force brake: per client address, FAIL_MAX wrong passwords lock it out
# for LOCK_S. In memory on purpose -- a restart is a human at the machine.
FAIL_MAX = 5
LOCK_S = 60
_fails: dict[str, list[float]] = {}

_cache: dict | None = None


def _path():
    return config_store.data_dir() / "auth.json"


_cache_mtime: float | None = None


def _mtime() -> float | None:
    try:
        return _path().stat().st_mtime
    except OSError:
        return None


def _load() -> dict:
    """Cached, but re-read when the file changes: `--set-password` from a
    console must take effect on the running server without a restart."""
    global _cache, _cache_mtime
    m = _mtime()
    if _cache is None or m != _cache_mtime:
        try:
            _cache = json.loads(_path().read_text(encoding="utf-8-sig"))
            if not isinstance(_cache, dict):
                _cache = {}
        except Exception:
            _cache = {}
        _cache_mtime = m
    return _cache


def _store(d: dict) -> None:
    global _cache, _cache_mtime
    p = _path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=2), encoding="utf-8")
    tmp.replace(p)
    _cache, _cache_mtime = d, _mtime()


def enabled() -> bool:
    d = _load()
    return bool(d.get("hash") and d.get("salt") and d.get("secret"))


def _hash(pw: str, salt: bytes, iters: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, iters).hex()


def set_password(pw: str) -> None:
    """Set (or replace) the password. Raises ValueError when it is too short."""
    if len(pw) < MIN_LEN:
        raise ValueError(f"password must be at least {MIN_LEN} characters")
    salt = secrets.token_bytes(16)
    _store({"iters": _ITERS, "salt": salt.hex(), "hash": _hash(pw, salt, _ITERS),
            "secret": secrets.token_hex(32)})


def clear_password() -> None:
    try:
        _path().unlink()
    except FileNotFoundError:
        pass
    except OSError:
        _store({})
    global _cache, _cache_mtime
    _cache, _cache_mtime = None, None


def verify(pw: str) -> bool:
    d = _load()
    if not enabled():
        return False
    try:
        salt = bytes.fromhex(d["salt"])
        want = d["hash"]
        got = _hash(pw, salt, int(d.get("iters", _ITERS)))
    except Exception:
        return False
    return hmac.compare_digest(got, want)


def seed_from_env() -> bool:
    """Docker: LGS_TT_PASSWORD sets the password once, when none is stored yet.

    The variable is only a bootstrap -- the hash is what persists, and a later
    change in the UI is not overwritten by a restart.
    """
    pw = os.environ.get("LGS_TT_PASSWORD", "")
    if pw and not enabled():
        try:
            set_password(pw)
            return True
        except ValueError:
            return False
    return False


# --- session cookie ---------------------------------------------------------

def _sign(payload: str) -> str:
    key = bytes.fromhex(_load()["secret"])
    return hmac.new(key, payload.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(now: float | None = None) -> str:
    exp = int((now if now is not None else time.time()) + SESSION_S)
    p = base64.urlsafe_b64encode(str(exp).encode()).decode().rstrip("=")
    return f"{p}.{_sign(p)}"


def token_ok(token: str, now: float | None = None) -> bool:
    if not enabled() or not token or "." not in token:
        return False
    p, sig = token.rsplit(".", 1)
    try:
        if not hmac.compare_digest(sig, _sign(p)):
            return False
        exp = int(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)).decode())
    except Exception:
        return False
    return exp > (now if now is not None else time.time())


def _cookie_from(headers) -> str:
    for k, v in headers:
        if k == b"cookie":
            for part in v.decode("latin-1").split(";"):
                name, _, val = part.strip().partition("=")
                if name == COOKIE:
                    return val
    return ""


def _locked(addr: str, now: float | None = None) -> bool:
    now = time.time() if now is None else now
    recent = [t for t in _fails.get(addr, []) if now - t < LOCK_S]
    _fails[addr] = recent
    return len(recent) >= FAIL_MAX


def _note_fail(addr: str) -> None:
    _fails.setdefault(addr, []).append(time.time())


# --- ASGI gate --------------------------------------------------------------

class Gate:
    """Pure ASGI middleware: HTTP and WebSocket both, since a page is useless
    without its socket and a socket without its page is still a way in."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket") or not enabled():
            return await self.app(scope, receive, send)
        path = scope.get("path", "")
        if path in _OPEN_PATHS or (path.startswith(_OPEN_PREFIXES) and ".." not in path) \
                or token_ok(_cookie_from(scope.get("headers", []))):
            return await self.app(scope, receive, send)
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1008})
            return
        qs = scope.get("query_string", b"").decode("latin-1")
        nxt = path + ("?" + qs if qs else "")
        loc = "/login" + ("?next=" + quote(nxt, safe="") if nxt else "")
        await send({"type": "http.response.start", "status": 302,
                    "headers": [(b"location", loc.encode("latin-1")),
                                (b"cache-control", b"no-store")]})
        await send({"type": "http.response.body", "body": b""})


# Where a sign-in lands when nothing asked for a particular page: the v2 UI.
# A page that did ask (the classic tool at "/", say) passes ?next= and keeps it.
HOME = "/v2"


def _safe_next(n: str) -> str:
    """Only same-site paths: '//evil.example' or 'http://...' would turn the
    login into an open redirect."""
    n = n or HOME
    if not n.startswith("/") or n.startswith("//") or "\\" in n or urlsplit(n).netloc:
        return HOME
    return n


_PAGE = """<!doctype html><html lang="th"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LGS Test Tool</title>
<link rel="stylesheet" href="/v2/static/fonts.css"><link rel="stylesheet" href="/v2/static/app.css">
<script>try{{var t=localStorage.getItem("lgs.theme");if(t&&t!=="auto")document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<style>
.login{{min-height:100vh;min-height:100dvh;display:grid;place-items:center;padding:16px;box-sizing:border-box}}
.login form{{width:min(100%,380px);display:grid;gap:16px;padding:24px;box-sizing:border-box}}
.login h1{{margin:0;font-size:22px;line-height:1.3}}.login .sub{{margin:2px 0 0;color:var(--muted);font-size:14px}}
.login .btn{{width:100%}}.login .e{{color:var(--bad);background:var(--bad-bg);border-radius:10px;padding:8px 12px;font-size:14px}}
</style></head><body><main class="login"><form class="card" method="post" action="/login">
<div><h1>LGS Test Tool</h1><p class="sub" data-en="Sign in to continue">เข้าสู่ระบบเพื่อใช้งานต่อ</p></div>{err}
<input type="hidden" name="next" value="{nxt}">
<div class="field"><label for="pw" data-en="Password">รหัสผ่าน</label>
<input id="pw" type="password" name="password" autocomplete="current-password" autofocus required></div>
<button class="btn primary" data-en="Sign in">เข้าสู่ระบบ</button></form></main>
<script>try{{if(localStorage.getItem("lgs.lang")==="en"){{document.documentElement.lang="en";document.querySelectorAll("[data-en]").forEach(function(e){{e.textContent=e.dataset.en}})}}}}catch(e){{}}</script>
</body></html>"""


def install(app) -> None:
    """Wire the gate and the /login, /logout routes into the NiceGUI app."""
    seed_from_env()
    app.add_middleware(Gate)

    def page(err: str = "", nxt: str = HOME, status: int = 200) -> HTMLResponse:
        e = f'<div class="e">{escape(err)}</div>' if err else ""
        return HTMLResponse(_PAGE.format(err=e, nxt=escape(nxt, quote=True)),
                            status_code=status,
                            headers={"Cache-Control": "no-store"})

    @app.get("/login")
    async def login_form(request: Request):
        if not enabled() or token_ok(request.cookies.get(COOKIE, "")):
            return RedirectResponse(_safe_next(request.query_params.get("next", HOME)), status_code=302)
        return page(nxt=_safe_next(request.query_params.get("next", HOME)))

    @app.post("/login")
    async def login_submit(request: Request):
        addr = request.client.host if request.client else "?"
        form = parse_qs((await request.body()).decode("utf-8", "replace"))
        nxt = _safe_next((form.get("next") or [HOME])[0])
        if not enabled():
            return RedirectResponse(nxt, status_code=303)
        if _locked(addr):
            return page("พยายามหลายครั้งเกินไป รอ 1 นาที / Too many attempts, wait 1 minute",
                        nxt, 429)
        if not verify((form.get("password") or [""])[0]):
            _note_fail(addr)
            return page("รหัสผ่านไม่ถูกต้อง / Wrong password", nxt, 401)
        _fails.pop(addr, None)
        r = RedirectResponse(nxt, status_code=303)
        r.set_cookie(COOKIE, make_token(), max_age=SESSION_S, httponly=True,
                     samesite="lax", path="/")
        return r

    @app.get("/logout")
    async def logout():
        r = RedirectResponse("/login", status_code=302)
        r.delete_cookie(COOKIE, path="/")
        return r
