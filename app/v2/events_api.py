"""Read side of the event collector: the dated files under data/events/."""
from __future__ import annotations

import codecs
import json
import re
from datetime import datetime, timedelta

from .. import event_collector


def gateways() -> list[dict]:
    root = event_collector.events_root()
    out = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        files = sorted(d.glob("events-*.jsonl"))
        try:
            st = json.loads((d / "state.json").read_text(encoding="utf-8"))
        except Exception:
            st = {}
        out.append({"gw": d.name, "files": len(files),
                    "first": files[0].name[7:17] if files else "",
                    "last": files[-1].name[7:17] if files else "",
                    "last_seq": st.get("last_seq"), "updated": st.get("updated", "")})
    return out


def query(gw: str = "", days: int = 1, ev: str = "", q: str = "", limit: int = 500,
          everything: bool = False) -> dict:
    """Newest first. `gw` is a folder name from gateways(); empty = every gateway.
    `everything` lifts the row cap (the screen shows a page; the CSV export wants all)."""
    root = event_collector.events_root()
    days = max(1, min(int(days), 366))   # the longest retention the page offers, plus today
    limit = 10 ** 9 if everything else max(1, min(int(limit), 2000))
    since = (datetime.now() - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    evs = {e for e in re.split(r"[,\s]+", ev) if e}
    needle = q.strip().lower()
    rows, scanned = [], 0
    dirs = [root / gw] if gw else sorted(p for p in root.iterdir() if p.is_dir())
    for d in dirs:
        if not d.is_dir() or d.resolve().parent != root.resolve():
            continue                                  # no path walking out of the events folder
        for f in sorted(d.glob("events-*.jsonl"), reverse=True):
            if f.name[7:17] < since:
                break
            for line in f.read_text(encoding="utf-8").splitlines():
                scanned += 1
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if evs and r.get("ev") not in evs:
                    continue
                if needle and needle not in (r.get("text", "") + " " + r.get("client", "")).lower():
                    continue
                rows.append(r)
    rows.sort(key=lambda r: (r.get("t") or r.get("collected", ""), r.get("seq", 0)), reverse=True)
    return {"rows": rows[:limit], "matched": len(rows), "scanned": scanned, "limit": limit}


CSV_COLUMNS = ("t", "gw", "ev", "text", "client", "seq", "up", "a", "p", "collected")


def csv_bytes(gw: str = "", days: int = 1, ev: str = "", q: str = "") -> bytes:
    """The same filter as the screen, every matching row, oldest first. UTF-8 with a BOM so
    Excel reads the Thai text; a leading =,+,-,@ in any cell is defused so a log line can never
    be read back as a formula."""
    import csv
    import io
    rows = query(gw, days, ev, q, everything=True)["rows"]
    rows.reverse()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(CSV_COLUMNS)
    for r in rows:
        cells = []
        for c in CSV_COLUMNS:
            v = str(r.get(c, "") if r.get(c) is not None else "")
            cells.append("'" + v if v[:1] in ("=", "+", "-", "@") and c in ("text", "client", "gw") else v)
        w.writerow(cells)
    return codecs.BOM_UTF8 + out.getvalue().encode("utf-8")
