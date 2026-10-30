"""Commission page backend: flash a blank module over ST-Link and give it its ID.

The classic engine unchanged (commission.run_commission / run_batch through the
worker); this module only validates, confirms and reports. Nothing here touches
Modbus, and nothing is flashed without the page's explicit confirmation flag:
writing a board's flash cannot be undone from the page.

A bundled factory image is SHA-256 checked by firmware_bundle.load(); an
uploaded one must still carry a commissioning block and be a factory (not OTA)
image, exactly like the classic page.
"""
from .. import commission_image as ci
from .. import firmware_bundle, lgs_map, stlink
from ..commission import BatchConfig, BoardDone, BoardNext, CommissionConfig
from ..ota import Done, Line, Progress
from . import soak_api


def options(worker) -> dict:
    """Images and device types: no hardware touched."""
    return {"images": [{"key": i.key, "version": i.version, "label": i.label, "note": i.note,
                        "sha256": i.sha256[:12]}
                       for i in firmware_bundle.for_kind(firmware_bundle.KIND_MODULE_FACTORY)],
            "device_types": [{"id": k, "name": v} for k, v in ci.DEVICE_TYPES.items()]}


def probe(worker) -> dict:
    """Is the programmer installed, and is an ST-Link connected? Read only."""
    try:
        cli = stlink.find_cli(worker.cubeprog_path)
    except stlink.ProgrammerError as exc:
        return {"cli": False, "error": str(exc), "probes": []}
    try:
        probes = stlink.list_probes(cli)
        return {"cli": True, "version": stlink.version(cli),
                "probes": [{"serial": p.serial, "firmware": p.firmware} for p in probes]}
    except stlink.ProgrammerError as exc:
        return {"cli": True, "error": str(exc), "probes": []}


def parse_ids(text: str) -> tuple:
    """'11-18, 21' -> (11,...,18,21). Order kept, duplicates refused."""
    out: list = []
    for part in str(text).replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                a, b = (int(x) for x in part.split("-", 1))
                if b < a or b - a > 244:
                    raise ValueError
                out.extend(range(a, b + 1))
            else:
                out.append(int(part))
        except ValueError:
            raise ValueError(f"'{part}' is not an ID or a range like 11-18")
    if len(set(out)) != len(out):
        raise ValueError("an ID is listed twice")
    for i in out:
        if not (lgs_map.valid_assignable_id(i) and i <= ci.ID_MAX):
            raise ValueError(f"ID {i} cannot be assigned: use 1-{ci.ID_MAX}")
    return tuple(out)


def _image(image_key: str, data: bytes, filename: str) -> tuple:
    if image_key:
        img = firmware_bundle.by_key(image_key)
        if img is None or img.kind != firmware_bundle.KIND_MODULE_FACTORY:
            raise ValueError("choose a factory image")
        try:
            data, filename = firmware_bundle.load(img), img.filename
        except firmware_bundle.BundleError as exc:
            raise ValueError(str(exc))
    if not data:
        raise ValueError("no image")
    try:
        ci.find_block(data)                 # is it an LGS module image at all?
        ci.check_factory_image(data)        # and a factory one, not OTA
    except ci.ImageError as exc:
        raise ValueError(str(exc))
    return data, filename


def _type(value) -> "int | None":
    v = int(value or 0)
    if v and v not in ci.DEVICE_TYPES:
        raise ValueError(f"device type {v} is not one this firmware knows")
    return v or None


def start(worker, body: dict, *, data: bytes = b"", filename: str = "") -> dict:
    if body.get("confirmed") is not True:
        raise ValueError("this writes the module's flash: confirm it on the page")
    mode = str(body.get("mode", "single"))
    image, name = _image(str(body.get("image", "")), data, filename)
    lot = str(body.get("lot", ""))[:40]
    dtype = _type(body.get("device_type"))
    log_dir = soak_api.exports_dir()
    if mode == "batch":
        ids = parse_ids(body.get("ids", ""))
        if not ids:
            raise ValueError("list at least one ID, e.g. 11-18")
        ok = worker.start_batch_commission(BatchConfig(image=image, filename=name, ids=ids, lot=lot,
                                                       log_dir=log_dir, device_type=dtype))
        out = {"mode": "batch", "ids": list(ids)}
    else:
        ids = parse_ids(body.get("id", ""))
        if len(ids) != 1:
            raise ValueError("give one ID")
        overwrite = bool(body.get("overwrite"))
        if overwrite and str(body.get("confirm", "")) != str(ids[0]):
            raise ValueError("overwrite replaces the ID the module already has: type its new ID to confirm")
        ok = worker.start_commission(CommissionConfig(image=image, filename=name, identifier=ids[0], lot=lot,
                                                      overwrite=overwrite, log_dir=log_dir,
                                                      device_type=dtype))
        out = {"mode": "single", "id": ids[0], "overwrite": overwrite}
    if not ok:
        raise ValueError("another job is already running on this tool")
    out.update(ok=True, image=name, size=len(image))
    return out


def events(worker, since: int) -> dict:
    seq, evs = worker.drain_commission_events(since)
    out = []
    for e in evs:
        if isinstance(e, Line):
            out.append({"k": "line", "text": e.text, "level": e.level})
        elif isinstance(e, Progress):
            out.append({"k": "progress", "done": e.done, "total": e.total})
        elif isinstance(e, Done):
            out.append({"k": "done", "ok": bool(e.ok), "summary": e.summary})
        elif isinstance(e, BoardNext):
            out.append({"k": "next", "id": e.identifier})
        elif isinstance(e, BoardDone):
            out.append({"k": "board", "id": e.identifier, "ok": bool(e.ok), "uid": e.uid})
    return {"seq": seq, "events": out, "running": bool(worker.get_state().commission_running)}
