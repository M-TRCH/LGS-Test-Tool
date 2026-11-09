"""Labels page backend: a Brother .lbx sticker for the cabinet in front of you.

Everything machine-readable is read live from the gateway when asked (name,
IP, MAC, the row/channel strip), exactly as the classic Labels tab does, so a
sticker cannot describe a cabinet that no longer exists. The two typed fields
(ward, serial) are passed in and never stored: the serial belongs to the
warehouse's database, not to this tool.

labels.use_frame() sets module-level state, so rendering is serialised.
"""
import threading
from datetime import datetime, timezone

from .. import i18n, labels
from . import gateway_api, label_preview

_render_lock = threading.Lock()


def options() -> dict:
    return {"layouts": [{"key": k, "title": v.title} for k, v in labels.LAYOUTS.items()],
            "plates": [{"key": k, "text": {lang: (i18n.TEXTS.get(f"labels.plate_{k}") or {}).get(lang, k)
                                           for lang in ("th", "en")}}
                       for k in labels.FRAME_STYLES],
            "default_layout": "standard", "default_plate": labels.FRAME_STYLE}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build(host: str, port: int, ward: str, serial: str, layout: str, plate: str) -> tuple:
    """-> (info dict, blob bytes, file name). Raises ValueError for a bad
    choice, labels.LabelTooBig-as-ValueError when it does not fit the tape."""
    if layout not in labels.LAYOUTS:
        raise ValueError(f"unknown layout '{layout}'")
    if plate not in labels.FRAME_STYLES:
        raise ValueError(f"unknown plate '{plate}'")
    with gateway_api._Session(host, port) as link:
        snap = link.snapshot()
    if not snap.ok:
        raise ValueError("could not read the gateway: " + (snap.note or "no answer"))
    s, info = snap.settings, snap.info
    cab = labels.CabinetLabel(name=s.get("sys.name") or info.get("sys.name", ""),
                              ip=info.get("net.ip", ""), mac=info.get("mac", ""),
                              rows=labels.rows_from_gateway(s), fw=info.get("fw", ""),
                              built=_now()[:10])
    if layout == "standard_ap":                    # the AP Service settings are not in the key table: ask the gateway
        if info.get("hw.wifi") != "1":
            raise ValueError("this gateway has no Wi-Fi radio, so there is no AP Service to put on a sticker")
        r = gateway_api.action(host, port, "ap_show")
        if not r.get("ok"):
            raise ValueError("could not read the AP Service settings: " + (r.get("error") or "no answer"))
        cab.ap_ssid, cab.ap_pass, cab.ap_url = r.get("ssid", ""), r.get("pass", ""), r.get("url", "")
    cab.ward = (ward or "").strip()[:60]
    cab.serial = (serial or "").strip()[:40]
    with _render_lock:
        labels.use_frame(plate)
        try:
            blob, mm = labels.render(layout, cab, created=_now())
        except labels.LabelTooBig as exc:
            raise ValueError("does not fit the tape: " + str(exc))
        payload = cab.qr_payload()
        # the same limit the sticker used: with the Wi-Fi code beside it, the cabinet code leaves room for a caption
        modules, _side, ecc = labels.fit_qr(payload, limit_pt=labels.FRAME_H - 2 * labels.FRAME_PAD - 10.0 if layout == "standard_ap" else None)
    n = len(payload.encode("utf-8"))
    version = (modules - 17) // 4
    stem = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in (cab.name or "cabinet")).strip("-") or "cabinet"
    return ({"name": cab.name, "ip": cab.ip, "mac": cab.mac, "rows": len(cab.rows), "mm": round(mm),
             "qr_bytes": n, "qr_version": version, "ecc": ecc.upper(), "recover_pct": labels._ECC_PCT[ecc],
             "spare_bytes": labels._QR_BYTES[ecc][version] - n, "size": len(blob), "payload": payload,
             "svg": label_preview.svg_from_lbx(blob)},
            blob, f"{stem}-{layout}.lbx")
