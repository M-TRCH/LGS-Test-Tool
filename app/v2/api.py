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
from . import commission_api, events_api, gateway_api, health, install_api, labels_api, module_api, ota_api, sites, soak_api

STATIC = Path(__file__).resolve().parent / "static"
RETENTION_CHOICES = (30, 90, 180, 365)   # days the event collector keeps on this PC; the page offers exactly these
PROBE_PARALLEL = 6            # gateways asked at once; each probe is one short connection


def _mutating(request: Request) -> bool:
    """State changes need a header a cross-site form cannot send. The session
    cookie is SameSite=Lax already; this is the second lock, cheap and
    dependency-free."""
    return request.headers.get("x-lgs") == "1"


def _forbidden() -> JSONResponse:
    return JSONResponse({"error": "missing X-LGS header"}, status_code=403)


def install(app, cfg, worker) -> None:
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
        site = sites.find(str(body.get("id", ""))) or {}
        return await _run(request, gateway_api.read, host, port, site.get("cabinet", ""))

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

    # -- installation check (module page) --------------------------------------
    @app.get("/api/v2/ins/layout")
    async def ins_layout(id: str = ""):
        return install_api.layout(id)

    @app.post("/api/v2/ins/start")
    async def ins_start(request: Request):
        body = await request.json()
        try:
            host, port, name = _target(body)
            ids = install_api._ids(body.get("ids"))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        site = {"host": host, "port": port, "name": name}
        return await _run(request, install_api.run.start, site, str(body.get("mode", "check")), ids, body)

    @app.get("/api/v2/ins/events")
    async def ins_events(since: int = 0):
        return install_api.run.snapshot(since)

    @app.post("/api/v2/ins/cancel")
    async def ins_cancel(request: Request):
        if not _mutating(request):
            return _forbidden()
        install_api.run.cancel()
        return {"ok": True}

    @app.get("/api/v2/ins/file")
    async def ins_file():
        r = install_api.run
        if not r.file_bytes:
            return JSONResponse({"error": "no finished run"}, status_code=404)
        return Response(r.file_bytes, media_type=r.file_type,
                        headers={"Content-Disposition": f'attachment; filename="{r.file_name}"'})

    async def _job(request: Request, fn):
        """Start a long job for the saved cabinet in the body: fn(site, body)."""
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        try:
            host, port, name = _target(body)
            return fn({"host": host, "port": port, "name": name}, body)
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/ins/scan")
    async def ins_scan(request: Request):
        return await _job(request, lambda site, b: install_api.run.start_scan(
            site, install_api.scan_ids(str(b.get("id", "")), bool(b.get("full")))))

    @app.post("/api/v2/ins/report")
    async def ins_report(request: Request):
        return await _job(request, lambda site, b: install_api.run.start_report(site, str(b.get("id", "")), bool(b.get("detail"))))

    # -- module danger actions: the page must send back what was typed --------
    @app.post("/api/v2/mod/setid")
    async def mod_setid(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
            dev, new = int(body.get("device_id", 0)), int(body.get("new_id", 0))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if str(body.get("confirm", "")).strip() != str(new):
            return JSONResponse({"error": "type the new id to confirm"}, status_code=422)
        return await _run(request, module_api.set_slave_id, host, port, dev, new)

    @app.post("/api/v2/mod/reset")
    async def mod_reset(request: Request):
        body = await request.json()
        try:
            host, port, _ = _target(body)
            dev = int(body.get("device_id", 0))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        if str(body.get("confirm", "")).strip() != str(dev):
            return JSONResponse({"error": "type the module id to confirm"}, status_code=422)
        return await _run(request, module_api.soft_reset, host, port, dev)

    # -- this PC as the site's NTP server, and the web password ----------------
    def _ntp_state(toward: str = "") -> dict:
        from .. import ntp_server
        srv = ntp_server.server
        site = sites.find(toward) if toward else None
        try:
            ip = ntp_server.local_ip_toward(site["host"]) if site else ""
        except Exception:                                        # noqa: BLE001
            ip = ""
        return {"enabled": bool(cfg.ntp_enabled), "running": srv.running, "port": int(cfg.ntp_port),
                "served": srv.served, "error": srv.error, "ip": ip or ""}

    @app.get("/api/v2/ntp")
    async def ntp_get(toward: str = ""):
        return _ntp_state(toward)

    @app.post("/api/v2/ntp")
    async def ntp_set(request: Request):
        if not _mutating(request):
            return _forbidden()
        from .. import ntp_server
        body = await request.json()
        try:
            port = int(body.get("port", cfg.ntp_port))
        except (TypeError, ValueError):
            return JSONResponse({"error": "port must be a number"}, status_code=422)
        if not 1 <= port <= 65535:
            return JSONResponse({"error": "port must be 1-65535"}, status_code=422)
        cfg.ntp_enabled, cfg.ntp_port = bool(body.get("enabled")), port
        config_store.save(cfg)
        if cfg.ntp_enabled:
            await ntp_server.server.start(port)
        else:
            await ntp_server.server.stop()
        return _ntp_state()

    @app.post("/api/v2/auth")
    async def auth_set(request: Request):
        """{password} sets it (and signs every browser out, this one too);
        {clear: true} removes it. Once a password is set, both need {current}: a
        signed-in tab left open must not be enough to lock the owner out."""
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        if auth.enabled():
            addr = request.client.host if request.client else "?"
            if auth._locked(addr):
                return JSONResponse({"error": "too many attempts, wait 1 minute"}, status_code=429)
            if not auth.verify(str(body.get("current", ""))):
                auth._note_fail(addr)
                return JSONResponse({"error": "current password is wrong"}, status_code=403)
        if body.get("clear"):
            auth.clear_password()
            return {"ok": True, "auth": False}
        try:
            auth.set_password(str(body.get("password", "")))
        except ValueError:
            return JSONResponse({"error": f"min {auth.MIN_LEN}"}, status_code=422)
        return {"ok": True, "auth": True}

    # ── soak ───────────────────────────────────────────────────────────────
    @app.get("/api/v2/soak/status")
    async def soak_status():
        return soak_api.live.snapshot(worker)

    @app.post("/api/v2/soak/start")
    async def soak_start(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        ids = set(body.get("ids") or [])
        chosen = [s for s in sites.load() if s["id"] in ids]
        try:
            return soak_api.start(worker, chosen, body)
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/soak/estimate")
    async def soak_estimate(request: Request):
        body = await request.json()
        ids = set(body.get("ids") or [])
        chosen = [s for s in sites.load() if s["id"] in ids]
        try:
            return soak_api.estimate(chosen, int(body.get("picks") or 2000), float(body.get("dwell_s") or 20),
                                     max(1, min(8, int(body.get("windows") or 8))))
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/soak/stop")
    async def soak_stop(request: Request):
        if not _mutating(request):
            return _forbidden()
        worker.cancel_fleet()
        return {"ok": True}

    @app.get("/api/v2/soak/runs")
    async def soak_runs():
        return {"runs": await asyncio.to_thread(soak_api.runs)}

    @app.get("/api/v2/soak/export")
    async def soak_export(stamp: str, cabs: str = "", format: str = "csv"):
        try:
            body, name, mime = await asyncio.to_thread(
                soak_api.export, stamp, [c for c in cabs.split(",") if c], "zip" if format == "zip" else "csv")
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        return Response(body, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @app.get("/api/v2/soak/file")
    async def soak_file(name: str, download: int = 0):
        try:
            path, kind = soak_api.read_file(name)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        if kind == "verdict" and not download:
            return Response(path.read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8")
        return FileResponse(path, filename=name, media_type="text/csv" if kind == "csv" else "text/plain")

    # ── labels ─────────────────────────────────────────────────────────────
    @app.get("/api/v2/labels/options")
    async def label_options():
        return labels_api.options()

    async def _label(request: Request):
        body = await request.json()
        host, port, _ = _target(body)
        return await asyncio.to_thread(labels_api.build, host, port, str(body.get("ward", "")),
                                       str(body.get("serial", "")), str(body.get("layout", "")),
                                       str(body.get("plate", "")))

    @app.post("/api/v2/labels/preview")
    async def label_preview(request: Request):
        if not _mutating(request):
            return _forbidden()
        try:
            info, _blob, name = await _label(request)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except Exception as exc:                                 # noqa: BLE001
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"[:200]}, status_code=502)
        return {"info": info, "file": name}

    @app.post("/api/v2/labels/file")
    async def label_file(request: Request):
        if not _mutating(request):
            return _forbidden()
        try:
            _info, blob, name = await _label(request)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)
        except Exception as exc:                                 # noqa: BLE001
            return JSONResponse({"error": f"{type(exc).__name__}: {exc}"[:200]}, status_code=502)
        return Response(blob, media_type="application/octet-stream",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})

    # ── firmware ───────────────────────────────────────────────────────────
    @app.get("/api/v2/fw/images")
    async def fw_images():
        return ota_api.images()

    @app.get("/api/v2/fw/ota/status")
    async def fw_ota_status():
        return ota_api.ota_status(worker)

    @app.post("/api/v2/fw/ota/start")
    async def fw_ota_start(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        ids = set(body.get("ids") or [])
        chosen = [s for s in sites.load() if s["id"] in ids]
        try:
            depot = body.get("depot")                  # {id: cabinet that holds the image, slot: 0-3}
            dsite = None
            if depot:
                dsite = sites.find(str(depot.get("id", "")))
                if not dsite:
                    raise ValueError("unknown cabinet for the depot image")
            return await asyncio.to_thread(ota_api.ota_start, worker, chosen, str(body.get("image", "")),
                                           dsite, int(depot.get("slot", -1)) if depot else -1)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    # ── module images kept on a gateway ────────────────────────────────────
    @app.get("/api/v2/fw/depot")
    async def fw_depot(id: str):
        site = sites.find(id)
        if not site:
            return JSONResponse({"error": "unknown cabinet"}, status_code=422)
        try:
            return await asyncio.to_thread(ota_api.depot_list, site)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=502)

    @app.get("/api/v2/fw/depot/progress")
    async def fw_depot_progress(id: str):
        return ota_api.depot_progress(id)

    @app.post("/api/v2/fw/depot/put")
    async def fw_depot_put(request: Request):
        """JSON {id, image} for a bundled image; or a raw .bin body with ?id=&name= for an uploaded one."""
        if not _mutating(request):
            return _forbidden()
        try:
            if "json" in request.headers.get("content-type", ""):
                body = await request.json()
                site = sites.find(str(body.get("id", "")))
                if not site:
                    raise ValueError("unknown cabinet")
                return await asyncio.to_thread(ota_api.depot_put, site, image_key=str(body.get("image", "")))
            q = request.query_params
            site = sites.find(q.get("id", ""))
            if not site:
                raise ValueError("unknown cabinet")
            data = await request.body()
            if len(data) > 200_000:
                raise ValueError("image larger than 200 KB")
            return await asyncio.to_thread(ota_api.depot_put, site, data=data, filename=q.get("name", "upload.bin")[:80])
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/fw/depot/keep")
    async def fw_depot_keep(request: Request):
        """Read one stored image back out of a gateway and keep it in this tool's own folder."""
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        site = sites.find(str(body.get("id", "")))
        if not site:
            return JSONResponse({"error": "unknown cabinet"}, status_code=422)
        try:
            return await asyncio.to_thread(ota_api.keep_from_depot, site, int(body.get("slot", -1)))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    # ── module OTA run by the gateway itself ───────────────────────────────
    @app.get("/api/v2/fw/gwota/status")
    async def fw_gwota_status(ids: str = ""):
        chosen = [s for s in sites.load() if s["id"] in set(i for i in ids.split(",") if i)]
        return await asyncio.to_thread(ota_api.gwota_status, chosen)

    @app.post("/api/v2/fw/gwota/start")
    async def fw_gwota_start(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        chosen = [s for s in sites.load() if s["id"] in set(body.get("ids") or [])]
        try:
            return await asyncio.to_thread(ota_api.gwota_start, chosen, str(body.get("image", "")), body.get("opts") or {})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/fw/gwota/abort")
    async def fw_gwota_abort(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        chosen = [s for s in sites.load() if s["id"] in set(body.get("ids") or [])]
        return await asyncio.to_thread(ota_api.gwota_abort, chosen)

    @app.get("/api/v2/fw/gwota/result")
    async def fw_gwota_result(id: str, n: int = 0):
        site = sites.find(id)
        if not site:
            return JSONResponse({"error": "unknown cabinet"}, status_code=422)
        try:
            return await asyncio.to_thread(ota_api.gwota_result, site, n)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/fw/kept/delete")
    async def fw_kept_delete(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        try:
            return ota_api.delete_kept(str(body.get("name", "")))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/fw/depot/delete")
    async def fw_depot_delete(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        site = sites.find(str(body.get("id", "")))
        if not site:
            return JSONResponse({"error": "unknown cabinet"}, status_code=422)
        try:
            return await asyncio.to_thread(ota_api.depot_delete, site, int(body.get("slot", -1)))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.post("/api/v2/fw/ota/cancel")
    async def fw_ota_cancel(request: Request):
        if not _mutating(request):
            return _forbidden()
        worker.cancel_fleet_ota()
        return {"ok": True}

    @app.get("/api/v2/fw/gateway/status")
    async def fw_gw_status():
        return ota_api.gw_status()

    @app.post("/api/v2/fw/gateway/start")
    async def fw_gw_start(request: Request):
        """JSON {id, confirm, image} for a bundled image; or a raw .bin body with
        ?id=&confirm=&name= for an uploaded one."""
        if not _mutating(request):
            return _forbidden()
        try:
            if "json" in request.headers.get("content-type", ""):
                body = await request.json()
                site = sites.find(str(body.get("id", "")))
                if not site:
                    raise ValueError("unknown cabinet: choose one from the saved list")
                return ota_api.gw_start(site, str(body.get("confirm", "")), image_key=str(body.get("image", "")))
            q = request.query_params
            site = sites.find(q.get("id", ""))
            if not site:
                raise ValueError("unknown cabinet: choose one from the saved list")
            data = await request.body()
            if len(data) > 1_000_000:
                raise ValueError("image larger than 1 MB")
            return ota_api.gw_start(site, q.get("confirm", ""), data=data, filename=q.get("name", "upload.bin")[:80])
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    # ── commission (ST-Link) ───────────────────────────────────────────────
    @app.get("/api/v2/cm/options")
    async def cm_options():
        return commission_api.options(worker)

    @app.post("/api/v2/cm/probe")
    async def cm_probe(request: Request):
        return await _run(request, commission_api.probe, worker)

    @app.post("/api/v2/cm/start")
    async def cm_start(request: Request):
        """JSON {mode, image, id|ids, lot, device_type, overwrite, confirm, confirmed}; or a raw .bin
        body with the same fields in the query string (uploaded image, ?name=)."""
        if not _mutating(request):
            return _forbidden()
        try:
            if "json" in request.headers.get("content-type", ""):
                return await asyncio.to_thread(commission_api.start, worker, await request.json())
            q = dict(request.query_params)
            q["overwrite"] = q.get("overwrite") == "1"
            q["confirmed"] = q.get("confirmed") == "1"
            data = await request.body()
            if len(data) > 1_000_000:
                raise ValueError("image larger than 1 MB")
            return await asyncio.to_thread(commission_api.start, worker, q, data=data,
                                           filename=q.get("name", "upload.bin")[:80])
        except (ValueError, TypeError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=422)

    @app.get("/api/v2/cm/events")
    async def cm_events(since: int = 0):
        return commission_api.events(worker, since)

    @app.post("/api/v2/cm/cancel")
    async def cm_cancel(request: Request):
        if not _mutating(request):
            return _forbidden()
        worker.cancel_commission()
        return {"ok": True}

    # ── events ─────────────────────────────────────────────────────────────
    @app.get("/api/v2/events/gateways")
    async def event_gateways():
        return {"gateways": events_api.gateways()}

    @app.get("/api/v2/events")
    async def events(gw: str = "", days: int = 1, ev: str = "", q: str = "", limit: int = 500,
                     start: str = "", end: str = "", offset: int = 0, tfrom: str = "", tto: str = "",
                     client: str = "", unit: str = ""):
        return await asyncio.to_thread(events_api.query, gw, days, ev, q, limit, False, start, end, offset, tfrom, tto, client, unit)

    @app.get("/api/v2/events/summary")
    async def events_summary(gw: str = "", days: int = 1, start: str = "", end: str = "", ev: str = "",
                             client: str = "", unit: str = "", tfrom: str = "", tto: str = ""):
        return await asyncio.to_thread(events_api.summary, gw, days, start, end, ev, client, unit, tfrom, tto)

    @app.get("/api/v2/events/csv")
    async def events_csv(gw: str = "", days: int = 1, ev: str = "", q: str = "", start: str = "", end: str = "",
                         tfrom: str = "", tto: str = "", client: str = "", unit: str = ""):
        data = await asyncio.to_thread(events_api.csv_bytes, gw, days, ev, q, start, end, tfrom, tto, client, unit)
        from datetime import datetime
        name = f"events-{(gw or 'all')[:40]}-{datetime.now():%Y%m%d-%H%M}.csv".replace("/", "_").replace("\\", "_")
        return Response(data, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}"'})

    @app.post("/api/v2/collector")
    async def collector(request: Request):
        if not _mutating(request):
            return _forbidden()
        body = await request.json()
        if "enabled" in body:
            cfg.events_enabled = bool(body["enabled"])
        if "retention_days" in body:
            try:
                days = int(body["retention_days"])
            except (TypeError, ValueError):
                days = 0
            if days not in RETENTION_CHOICES:
                return JSONResponse({"error": "retention_days must be one of "
                                     + ", ".join(map(str, RETENTION_CHOICES))}, status_code=422)
            cfg.events_retention_days = days
        config_store.save(cfg)
        event_collector.apply(cfg)
        return {"enabled": cfg.events_enabled, "retention_days": cfg.events_retention_days}
