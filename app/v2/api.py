"""v2 JSON API and the static front end, mounted on the NiceGUI app.

No `from __future__ import annotations` here on purpose: FastAPI resolves
route annotations by name, and a postponed Request would be invisible to it
(the lesson app/auth.py already paid for).
"""
import asyncio
from pathlib import Path

from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response

from .. import auth, config_store, event_collector
from ..version import APP_VERSION
from . import events_api, gateway_api, health, module_api, sites

STATIC = Path(__file__).resolve().parent / "static"
PROBE_PARALLEL = 6            # gateways asked at once; each probe is one short connection


def _mutating(request: Request) -> bool:
    """State changes need a header a cross-site form cannot send. The session
    cookie is SameSite=Lax already; this is the second lock, cheap and
    dependency-free."""
    return request.headers.get("x-lgs") == "1"


def _forbidden() -> JSONResponse:
    return JSONResponse({"error": "missing X-LGS header"}, status_code=403)


def install(app, cfg) -> None:
    @app.get("/v2")
    async def v2_index():
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})

    @app.get("/v2/static/{path:path}")
    async def v2_static(path: str):
        f = (STATIC / path).resolve()
        if STATIC.resolve() not in f.parents or not f.is_file():
            return Response(status_code=404)
        # Fonts and libraries never change under one version; the page itself
        # (index.html) is revalidated, so a new build shows up on reload.
        cache = "public, max-age=86400" if f.suffix in (".woff2", ".woff") else "no-cache"
        mt = "font/woff2" if f.suffix == ".woff2" else None
        return FileResponse(f, media_type=mt, headers={"Cache-Control": cache})

    @app.get("/api/v2/me")
    async def me():
        return {"version": APP_VERSION, "auth": auth.enabled(), "language": cfg.language,
                "collector": {"enabled": bool(cfg.events_enabled),
                              "interval_s": cfg.events_interval_s,
                              "retention_days": cfg.events_retention_days,
                              "status": event_collector.status()}}

    # ── sites ──────────────────────────────────────────────────────────────
    @app.get("/api/v2/sites")
    async def get_sites():
        s = sites.load()
        return {"sites": s, "warnings": sites.warnings(s), "layouts": sites.layouts()}

    @app.put("/api/v2/sites")
    async def put_sites(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        try:
            s = sites.save(body.get("sites", []))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return {"sites": s, "warnings": sites.warnings(s), "layouts": sites.layouts()}

    @app.get("/api/v2/sites.csv")
    async def sites_csv():
        return Response(sites.to_csv(sites.load()).encode("utf-8"),
                        media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="lgs-sites.csv"'})

    @app.post("/api/v2/sites/import")
    async def import_sites(request: Request, mode: str = "merge"):
        """Whole file or nothing. merge: add rows whose name+address is new;
        replace: the file becomes the list."""
        if not _mutating(request):
            return _forbidden()
        try:
            incoming = sites.from_csv(await request.body())
            current = sites.load()
            if mode == "replace":
                merged = incoming
            else:
                have = {(c["name"].lower(), c["host"], c["port"]) for c in current}
                merged = current + [i for i in incoming
                                    if (i["name"].lower(), i["host"], i["port"]) not in have]
            s = sites.save(merged)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return {"sites": s, "warnings": sites.warnings(s), "imported": len(incoming)}

    # ── health ─────────────────────────────────────────────────────────────
    @app.post("/api/v2/health")
    async def get_health(request: Request):
        """Probe the given site ids (all when none). Results by id."""
        if not _mutating(request):
            return _forbidden()
        try:
            want = set((await request.json()).get("ids") or [])
        except ValueError:
            want = set()
        todo = [s for s in sites.load() if not want or s["id"] in want]
        gate = asyncio.Semaphore(PROBE_PARALLEL)
        # One probe per ADDRESS: two rows on one gateway would otherwise ask it
        # at the same time and the second sees the first as "another client".
        by_addr: dict = {}
        for s in todo:
            by_addr.setdefault((s["host"], s["port"]), []).append(s["id"])

        async def one(addr, ids):
            async with gate:
                from ..ntp_server import local_ip_toward
                try:
                    mine = local_ip_toward(addr[0]) or ""
                except Exception:                                # noqa: BLE001
                    mine = ""
                res = await asyncio.to_thread(health.probe, addr[0], addr[1], my_ip=mine)
                return {i: res for i in ids}

        merged: dict = {}
        for part in await asyncio.gather(*(one(a, i) for a, i in by_addr.items())):
            merged.update(part)
        return {"results": merged}

    # ── gateway page ───────────────────────────────────────────────────────
    def _target(body):
        """(host, port) for a saved site id, else a raw host given by the page.
        Only addresses on the saved list are accepted: this API writes to
        gateways, so it must not be a way to reach arbitrary hosts."""
        s = sites.find(str(body.get("id", "")))
        if not s:
            raise ValueError("unknown cabinet: choose one from the saved list")
        return s["host"], s["port"], s["name"]

    async def _run(request: Request, fn, *args):
        if not _mutating(request):
            return _forbidden()
        try:
            return await asyncio.to_thread(fn, *args)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except Exception as exc:                                 # noqa: BLE001
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"[:200]}, status_code=502)

    @app.post("/api/v2/gw/read")
    async def gw_read(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return await _run(request, gateway_api.read, host, port)

    @app.post("/api/v2/gw/apply")
    async def gw_apply(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        changes = {str(k): str(v) for k, v in (body.get("changes") or {}).items()}
        if any((" " in k) or ("=" in k) or (" " in v) for k, v in changes.items()):
            return JSONResponse({"error": "keys and values may not contain spaces or '='"},
                                status_code=422)
        return await _run(request, gateway_api.apply, host, port, changes)

    @app.post("/api/v2/gw/action")
    async def gw_action(request: Request):
        body = await request.json()
        try:
            host, port, name = _target(body)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        act = str(body.get("action", ""))
        if act == "defaults" and str(body.get("confirm", "")) != name:
            return JSONResponse({"error": "type the cabinet's name to confirm DEFAULTS"},
                                status_code=422)
        return await _run(request, gateway_api.action, host, port, act, body.get("value"))

    # ── module page ────────────────────────────────────────────────────────
    @app.get("/api/v2/mod/presets")
    async def mod_presets():
        return {"presets": module_api.presets()}

    @app.post("/api/v2/mod/monitor")
    async def mod_monitor(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
            dev = int(body.get("device_id", 0))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return await _run(request, module_api.monitor, host, port, dev, bool(body.get("stats")))

    @app.post("/api/v2/mod/coil")
    async def mod_coil(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
            dev, addr = int(body.get("device_id", 0)), int(body.get("addr", -1))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return await _run(request, module_api.coil, host, port, dev, addr, bool(body.get("value")))

    @app.post("/api/v2/mod/number")
    async def mod_number(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
            dev, val = int(body.get("device_id", 0)), int(body.get("value", -1))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        return await _run(request, module_api.display_number, host, port, dev, val)

    # ── events ─────────────────────────────────────────────────────────────
    @app.get("/api/v2/events/gateways")
    async def event_gateways():
        return {"gateways": events_api.gateways()}

    @app.get("/api/v2/events")
    async def events(gw: str = "", days: int = 1, ev: str = "", q: str = "", limit: int = 500):
        return await asyncio.to_thread(events_api.query, gw, days, ev, q, limit)

    @app.post("/api/v2/collector")
    async def collector(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        if "enabled" in body:
            cfg.events_enabled = bool(body["enabled"])
        config_store.save(cfg)
        event_collector.apply(cfg)
        return {"enabled": cfg.events_enabled}
