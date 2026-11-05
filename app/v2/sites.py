"""Sites: the saved name <-> address list, shared by every browser.

data/sites.json on the SERVER, not in a browser, so the phone, the laptop and
the PC at the site all see the same list and nobody retypes an IP. One entry
per cabinet; a gateway is one cabinet's controller.
"""
from __future__ import annotations

import csv
import io
import json
import re
import threading
import uuid
from typing import Optional

from .. import config_store, lgs_map

_lock = threading.Lock()
_HOST_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]{0,61}[A-Za-z0-9])?$")
FIELDS = ("name", "host", "port", "cabinet", "site", "note")


def _path():
    return config_store.data_dir() / "sites.json"


def layouts() -> list[str]:
    return [l.key for l in lgs_map.CABINET_LAYOUTS]


def load() -> list[dict]:
    try:
        raw = json.loads(_path().read_text(encoding="utf-8-sig"))
        return [_norm(s, keep_id=True) for s in raw.get("sites", []) if isinstance(s, dict)]
    except Exception:
        return []


def _norm(s: dict, keep_id: bool = False) -> dict:
    out = {k: str(s.get(k, "")).strip() for k in FIELDS if k != "port"}
    try:
        out["port"] = int(str(s.get("port", "") or 502).strip())
    except ValueError:
        out["port"] = 0
    out["id"] = (str(s.get("id", "")) if keep_id and s.get("id") else "") or uuid.uuid4().hex[:8]
    return out


def validate(s: dict) -> list[str]:
    """Problems with one entry (empty = fine). Refusals, not warnings."""
    errs = []
    if not s["name"]:
        errs.append("name is empty")
    if len(s["name"]) > 40:
        errs.append("name longer than 40 characters")
    if not _HOST_RE.match(s["host"]):
        errs.append("address is not an IP or host name")
    if not 1 <= s["port"] <= 65535:
        errs.append("port must be 1-65535")
    if s["cabinet"] and s["cabinet"] not in layouts():
        errs.append(f"unknown cabinet type '{s['cabinet']}' (known: {', '.join(layouts())})")
    return errs


def warnings(sites: list[dict]) -> list[str]:
    """Things worth a look but not worth refusing: two cabinets on one
    address is the mistake that makes a soak read the wrong gateway."""
    out, by_addr, by_name = [], {}, {}
    for s in sites:
        by_addr.setdefault((s["host"], s["port"]), []).append(s["name"])
        by_name.setdefault(s["name"].lower(), []).append(s["host"])
    for (host, port), names in by_addr.items():
        if len(names) > 1:
            out.append(f"{host}:{port} is used by {len(names)} entries: {', '.join(names)}")
    for name, hosts in by_name.items():
        if len(hosts) > 1:
            out.append(f"name '{name}' appears {len(hosts)} times ({', '.join(hosts)})")
    return out


def save(sites: list[dict]) -> list[dict]:
    """Validate all, then replace. All or nothing: a bad row refuses the lot
    and names it, so a half-saved list never reaches a Friday-night soak."""
    clean = [_norm(s, keep_id=True) for s in sites]
    problems = []
    for i, s in enumerate(clean, 1):
        for e in validate(s):
            problems.append(f"row {i} ({s['name'] or '?'}): {e}")
    if problems:
        raise ValueError("; ".join(problems[:8]))
    with _lock:
        p = _path()
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "sites": clean}, indent=1, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(p)
    return clean


def to_csv(sites: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(FIELDS)
    for s in sites:
        w.writerow([s[k] for k in FIELDS])
    return "﻿" + buf.getvalue()          # BOM: Excel opens Thai as UTF-8


def from_csv(data: bytes) -> list[dict]:
    """Excel's CSV: BOM or not, CRLF, quoted commas, and on a Thai Windows
    the legacy code page. A whole-file parse; the caller saves only if it
    all read."""
    for enc in ("utf-8-sig", "cp874"):
        try:
            text = data.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("file is neither UTF-8 nor Thai Windows text")
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        raise ValueError("file is empty")
    head = [h.strip().lower() for h in rows[0]]
    if "name" not in head or "host" not in head:
        raise ValueError("first row must name the columns: name, host (port, cabinet, site, note optional)")
    idx = {h: head.index(h) for h in FIELDS if h in head}
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        out.append(_norm({k: (r[i] if i < len(r) else "") for k, i in idx.items()}))
    return out


def find(site_id: str) -> Optional[dict]:
    return next((s for s in load() if s["id"] == site_id), None)
