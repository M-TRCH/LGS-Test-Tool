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
from . import events_api, health, sites

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
