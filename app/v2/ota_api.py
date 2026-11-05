"""Firmware page backend: module OTA across cabinets, and one gateway's
network update.

Both are the classic engines unchanged (ModbusWorker.start_fleet_ota,
gw_net_update.run_update); this module only validates, confirms and reports.
Only released images that pass their SHA-256 check are offered for modules; a
gateway may also take an uploaded image, which run_update still checks for
size and proves by CRC on the gateway before anything is applied.

Writing firmware is the one operation here that cannot be undone from the page,
so every start takes an explicit confirmation the server verifies (the
cabinet's own name for a gateway) and refuses a second job while one runs.
"""
import threading
import time
from collections import deque

from .. import firmware_bundle, kept_images, lgs_map, soak_fleet
from . import gateway_api, soak_api


def images() -> dict:
    def row(i):
        return {"key": i.key, "version": i.version, "note": i.note, "label": i.label,
                "source": i.source, "sha256": i.sha256[:12]}
    # Images the tool kept after reading them out of a gateway are offered next to the bundled ones, under a "kept:" key.
    kept = [{"key": kept_images.KEY_PREFIX + k["name"], "version": k["name"], "note": "kept from " + k["source"],
             "label": f"{k['name']} — kept from {k['source']}", "source": k["source"], "sha256": k["sha256"][:12],
             "kept": True, "size": k["size"]} for k in kept_images.listing()]
    return {"module": [row(i) for i in firmware_bundle.for_kind(firmware_bundle.KIND_MODULE_OTA)] + kept,
            "gateway": [row(i) for i in firmware_bundle.for_kind(firmware_bundle.KIND_GATEWAY)]}


def keep_from_depot(site: dict, slot: int) -> dict:
    """Read an image back out of a gateway's depot and keep it in this tool's own folder."""
    name, data = depot_fetch(site, slot)
    try:
        meta = kept_images.keep(name, data, site["name"])
    except kept_images.KeptError as exc:
        raise ValueError(str(exc))
    return {"ok": True, "kept": meta, "images": images()}


def delete_kept(name: str) -> dict:
    try:
        kept_images.delete(name)
    except kept_images.KeptError as exc:
        raise ValueError(str(exc))
    return {"ok": True, "images": images()}


def _image_bytes(image_key: str, kind: str) -> tuple:
    """(filename, bytes) of a bundled release, or of a kept image when the key is `kept:<name>`."""
    if image_key.startswith(kept_images.KEY_PREFIX):
        try:
            return kept_images.load(image_key[len(kept_images.KEY_PREFIX):])
        except kept_images.KeptError as exc:
            raise ValueError(str(exc))
    img = firmware_bundle.by_key(image_key)
    if img is None or img.kind != kind:
        raise ValueError("choose a module OTA image" if kind == firmware_bundle.KIND_MODULE_OTA else "choose a gateway image")
    try:
        return img.filename, firmware_bundle.load(img)
    except firmware_bundle.BundleError as exc:
        raise ValueError(str(exc))


# ── module images kept on a gateway ──────────────────────────────────────────
def _depot_link(site: dict):
    """(client, link) to the gateway's tunnel; the caller holds the gateway's lock and closes the client."""
    import socket
    from pymodbus.client import ModbusTcpClient
    from .. import gateway_tcp
    try:      # pymodbus keeps re-trying a dead address for over half a minute; a plain connect tells us in 2 s
        socket.create_connection((site["host"], int(site["port"])), timeout=2.0).close()
    except OSError:
        raise ValueError(f"cannot reach {site['host']}:{site['port']}")
    c = ModbusTcpClient(host=site["host"], port=int(site["port"]), timeout=5.0, retries=0)
    if not c.connect():
        raise ValueError(f"cannot reach {site['host']}:{site['port']}")
    gateway_tcp.register_pdu(c)
    return c, gateway_tcp.GatewayTcpLink(c)


def depot_list(site: dict) -> dict:
    from .. import gw_depot
    from ..gateway_config import GatewayError
    with gateway_api._lock(site["host"], int(site["port"])):
        c, link = _depot_link(site)
        try:
            return {"name": site["name"], "slots": gw_depot.slots(link)}
        except (OSError, GatewayError, gw_depot.DepotError) as exc:
            raise ValueError(str(exc))
        finally:
            c.close()


_depot_prog: dict = {}          # cabinet id -> what a deposit in progress is doing, for the page's progress bar


def depot_progress(site_id: str) -> dict:
    return dict(_depot_prog.get(site_id) or {"state": "idle"})


def depot_put(site: dict, *, image_key: str = "", data: bytes = b"", filename: str = "") -> dict:
    from .. import gw_depot
    from ..gateway_config import GatewayError
    if image_key:
        filename, data = _image_bytes(image_key, firmware_bundle.KIND_MODULE_OTA)
    if not data:
        raise ValueError("no image")
    name = gw_depot.depot_name(filename)
    with gateway_api._lock(site["host"], int(site["port"])):
        c, link = _depot_link(site)
        try:
            _depot_prog[site["id"]] = {"state": "sending", "done": 0, "total": len(data)}

            def note(done: int, total: int) -> None:
                _depot_prog[site["id"]] = {"state": "verifying" if done >= total else "sending", "done": done, "total": total}
            slot = gw_depot.put(link, name, data, progress=note)
            return {"ok": True, "name": name, "slot": slot, "size": len(data), "slots": gw_depot.slots(link)}
        except (OSError, GatewayError, gw_depot.DepotError) as exc:
            raise ValueError(str(exc))
        finally:
            _depot_prog.pop(site["id"], None)
            c.close()


def depot_delete(site: dict, slot: int) -> dict:
    from .. import gw_depot
    from ..gateway_config import GatewayError
    with gateway_api._lock(site["host"], int(site["port"])):
        c, link = _depot_link(site)
        try:
            gw_depot.delete(link, slot)
            return {"ok": True, "slots": gw_depot.slots(link)}
        except (OSError, GatewayError, gw_depot.DepotError) as exc:
            raise ValueError(str(exc))
        finally:
            c.close()


def depot_fetch(site: dict, slot: int) -> tuple:
    """(name, bytes) read back from one gateway and CRC-proven."""
    from .. import gw_depot
    from ..gateway_config import GatewayError
    with gateway_api._lock(site["host"], int(site["port"])):
        c, link = _depot_link(site)
        try:
            def note(done: int, total: int) -> None:
                _depot_prog[site["id"]] = {"state": "reading", "done": done, "total": total}
            return gw_depot.fetch(link, slot, progress=note)
        except (OSError, GatewayError, gw_depot.DepotError) as exc:
            raise ValueError(str(exc))
        finally:
            _depot_prog.pop(site["id"], None)
            c.close()


# ── module OTA run by the gateway itself ────────────────────────────────────
# START / ABORT / RESULT wait this long for a gateway another job is using (a depot upload, a gateway update), then answer
# "busy" instead of hanging the page until that job ends.
LONG_LOCK_WAIT_S = 15.0


def _each_gateway(sites_list: list, fn, lock_wait: float = LONG_LOCK_WAIT_S) -> list:
    """Run fn(link) against every gateway in parallel, one short connection each -> [{id, name, ...} | {id, name, error}]."""
    from concurrent.futures import ThreadPoolExecutor
    from .. import gw_ota
    from ..gateway_config import GatewayError

    def one(site):
        row = {"id": site["id"], "name": site["name"], "host": site["host"]}
        try:
            lock = gateway_api._lock(site["host"], int(site["port"]))
            if not lock.acquire(timeout=lock_wait):      # a status poll must not queue behind a long job on that gateway
                row["error"] = "busy"
                return row
            try:
                c, link = _depot_link(site)
                try:
                    row.update(fn(link))
                finally:
                    c.close()
            finally:
                lock.release()
        except (ValueError, OSError, GatewayError, gw_ota.OtaError, Exception) as exc:      # noqa: BLE001
            row["error"] = str(exc)[:160]
        return row

    with ThreadPoolExecutor(max_workers=min(16, max(1, len(sites_list)))) as pool:
        return list(pool.map(one, sites_list))


def gwota_status(sites_list: list) -> dict:
    from .. import gw_ota
    return {"rows": _each_gateway(sites_list, gw_ota.status_row, lock_wait=3.0)}


def gwota_start(sites_list: list, image_name: str, opts: dict) -> dict:
    from .. import gw_ota
    if not sites_list:
        raise ValueError("choose at least one cabinet")
    try:
        gw_ota.options(opts)
    except gw_ota.OtaError as exc:
        raise ValueError(str(exc))
    return {"rows": _each_gateway(sites_list, lambda link: gw_ota.start(link, image_name, opts), lock_wait=LONG_LOCK_WAIT_S)}


def gwota_abort(sites_list: list) -> dict:
    from .. import gw_ota
    return {"rows": _each_gateway(sites_list, lambda link: (gw_ota.abort(link), {"ok": True})[1], lock_wait=LONG_LOCK_WAIT_S)}


def gwota_result(site: dict, n: int) -> dict:
    from .. import gw_ota
    rows = _each_gateway([site], lambda link: gw_ota.result(link, n), lock_wait=LONG_LOCK_WAIT_S)
    if rows[0].get("error"):
        raise ValueError(rows[0]["error"])
    return rows[0]


# ── module OTA across cabinets ───────────────────────────────────────────────
class _OtaLog:
    def __init__(self) -> None:
        self.since = 0
        self.lines: deque = deque(maxlen=300)
        self.lock = threading.Lock()

    def pump(self, worker) -> None:
        with self.lock:
            self.since, evs = worker.drain_fleet_ota_events(self.since)
            for e in evs:
                if hasattr(e, "text") and hasattr(e, "cabinet"):
                    self.lines.append({"at": e.when, "cabinet": e.cabinet, "level": e.level, "text": e.text})

    def reset(self) -> None:
        with self.lock:
            self.since = 0
            self.lines.clear()


ota_log = _OtaLog()


def ota_status(worker) -> dict:
    ota_log.pump(worker)
    rows = []
    for r in worker.fleet_ota_status():
        rows.append({"name": r.name, "host": r.host, "modules": r.modules, "state": r.state,
                     "channel": r.channel, "channels": r.channels, "phase": r.phase, "pct": r.pct,
                     "left": list(r.left), "census": r.census, "note": r.note,
                     "minutes": round(r.minutes, 1)})
    out = worker.fleet_ota_outcome()
    with ota_log.lock:
        lines = list(ota_log.lines)[-80:]
    return {"running": worker.fleet_ota_running(), "rows": rows, "log": lines,
            "outcome": ({"text": out.text, "path": out.path} if out else None)}


def ota_start(worker, sites_list: list, image_key: str, depot_site: dict = None, depot_slot: int = -1) -> dict:
    """The image is a bundled release (image_key) or one read back out of a gateway's depot (depot_site + depot_slot)."""
    cabs = []
    for s in sites_list:
        if not s.get("cabinet"):
            raise ValueError(f"'{s['name']}': set its cabinet type on the Sites page first")
        cabs.append(soak_fleet.FleetCabinet(name=s["name"], host=s["host"],
                                            ids=tuple(lgs_map.layout_by_key(s["cabinet"]).ids),
                                            port=int(s["port"])))
    if not cabs:
        raise ValueError("choose at least one cabinet")
    dupes = soak_fleet.duplicate_hosts(cabs)
    if dupes:
        raise ValueError("two rows on one gateway: " + ", ".join(dupes))
    if depot_site is not None:
        filename, data = depot_fetch(depot_site, depot_slot)        # CRC-proven against the gateway's own record
        filename = f"{filename} (from {depot_site['name']})"
        from .. import ota
        if not 8 <= len(data) <= ota.MAX_IMAGE_SIZE:
            raise ValueError(f"{len(data):,} bytes is not a module image (the module slot holds {ota.MAX_IMAGE_SIZE:,})")
    else:
        filename, data = _image_bytes(image_key, firmware_bundle.KIND_MODULE_OTA)     # SHA-256 proven here
    ota_log.reset()
    if not worker.start_fleet_ota(cabs, data, filename, soak_api.exports_dir()):
        raise ValueError("an update is already running, or this tool is connected to one of these gateways")
    return {"ok": True, "count": len(cabs), "modules": sum(len(c.ids) for c in cabs),
            "image": filename, "size": len(data)}


# ── one gateway's network update ─────────────────────────────────────────────
class _GwJob:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        self.running = False
        self.cancel = threading.Event()
        self.lines: list = []
        self.pct = 0
        self.done = False
        self.ok = False
        self.summary = ""
        self.name = ""
        self.started = 0.0


gw_job = _GwJob()


def gw_status() -> dict:
    j = gw_job
    with j.lock:
        return {"running": j.running, "name": j.name, "pct": j.pct, "lines": list(j.lines)[-40:],
                "done": j.done, "ok": j.ok, "summary": j.summary,
                "seconds": round(time.monotonic() - j.started) if j.started else 0}


def gw_start(site: dict, confirm: str, *, image_key: str = "", data: bytes = b"", filename: str = "") -> dict:
    if confirm != site["name"]:
        raise ValueError("type the cabinet's name to confirm the update")
    if image_key:
        img = firmware_bundle.by_key(image_key)
        if img is None or img.kind != firmware_bundle.KIND_GATEWAY:
            raise ValueError("choose a gateway image")
        try:
            data, filename = firmware_bundle.load(img), img.filename
        except firmware_bundle.BundleError as exc:
            raise ValueError(str(exc))
    if not data:
        raise ValueError("no image")
    j = gw_job
    with j.lock:
        if j.running:
            raise ValueError("a gateway update is already running")
        j.reset()
        j.running, j.name, j.started = True, site["name"], time.monotonic()
    threading.Thread(target=_gw_run, args=(site, data, filename), name="gw-net-update", daemon=True).start()
    return {"ok": True, "name": site["name"], "size": len(data), "image": filename}


def _gw_run(site: dict, data: bytes, filename: str) -> None:
    from pymodbus.client import ModbusTcpClient
    from .. import gateway_tcp, gw_net_update
    from ..ota import Done, Line, Progress
    j = gw_job

    class Ops:
        def __init__(self):
            self.c = None
            self.connect()

        def connect(self):
            c = ModbusTcpClient(host=site["host"], port=int(site["port"]), timeout=5.0, retries=0)
            ok = c.connect()
            if ok:
                gateway_tcp.register_pdu(c)
                self.c = c
            return ok

        def link(self):
            return gateway_tcp.GatewayTcpLink(self.c)

        def drop_client(self):
            try:
                self.c.close()
            except Exception:                                    # noqa: BLE001
                pass

        def reconnect(self):
            try:
                return self.connect()
            except Exception:                                    # noqa: BLE001
                return False

        def sleep(self, s):
            time.sleep(s)

    def emit(ev):
        with j.lock:
            if isinstance(ev, Line):
                j.lines.append(f"[{ev.level}] {ev.text}")
            elif isinstance(ev, Progress) and ev.total:
                j.pct = int(ev.done * 100 // ev.total)
            elif isinstance(ev, Done):
                j.ok, j.summary = bool(ev.ok), ev.summary

    lock = gateway_api._lock(site["host"], int(site["port"]))
    try:
        with lock:
            gw_net_update.run_update(Ops(), gw_net_update.GwNetUpdateConfig(image=data, filename=filename),
                                     emit, j.cancel)
    except BaseException as exc:                                 # noqa: BLE001
        with j.lock:
            j.ok, j.summary = False, f"{type(exc).__name__}: {exc}"[:200]
            j.lines.append(f"[error] {j.summary}")
    finally:
        with j.lock:
            j.running, j.done = False, True
