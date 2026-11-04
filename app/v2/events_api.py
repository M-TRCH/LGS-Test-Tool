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


def window(days: int = 1, start: str = "", end: str = "") -> tuple:
    """(since, until) as YYYY-MM-DD, both inclusive. A calendar range (`start`, optional `end`) wins over
    `days`; both are clamped to the last 366 days and today, and swapped if given the wrong way round."""
    today = datetime.now().date()
    oldest = today - timedelta(days=366)

    def day(text, default):
        try:
            d = datetime.strptime(str(text)[:10], "%Y-%m-%d").date()
        except ValueError:
            return default
        return min(max(d, oldest), today)

    if start:
        a, b = day(start, today), day(end, today) if end else today
    else:
        a, b = today - timedelta(days=max(1, min(int(days), 366)) - 1), today
    if a > b:
        a, b = b, a
    return a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")


def time_window(tfrom: str = "", tto: str = ""):
    """(from, to) as "HH:MM", or None when no time filter applies (both empty, malformed, or the whole day)."""
    ok = lambda x: len(x) == 5 and x[2] == ":" and x[:2].isdigit() and x[3:].isdigit() and int(x[:2]) < 24 and int(x[3:]) < 60  # noqa: E731
    a, b = (tfrom or "00:00"), (tto or "23:59")
    if not (ok(a) and ok(b)) or (a, b) == ("00:00", "23:59"):
        return None
    return a, b


def query(gw: str = "", days: int = 1, ev: str = "", q: str = "", limit: int = 500,
          everything: bool = False, start: str = "", end: str = "", offset: int = 0,
          tfrom: str = "", tto: str = "", client: str = "", unit: str = "") -> dict:
    """Newest first. `gw` is a folder name from gateways(); empty = every gateway.
    `everything` lifts the row cap (the screen shows a page; the CSV export wants all);
    `offset` skips that many matches, for paging."""
    root = event_collector.events_root()
    limit = 10 ** 9 if everything else max(1, min(int(limit), 2000))
    offset = max(0, int(offset))
    since, until = window(days, start, end)
    tw = time_window(tfrom, tto)   # a time of day on every chosen day; a later "from" than "to" wraps past midnight
    evs = {e for e in re.split(r"[,\s]+", ev) if e}
    needle = q.strip().lower()
    rows, scanned = [], 0
    dirs = [root / gw] if gw else sorted(p for p in root.iterdir() if p.is_dir())
    for d in dirs:
        if not d.is_dir() or d.resolve().parent != root.resolve():
            continue                                  # no path walking out of the events folder
        for f in sorted(d.glob("events-*.jsonl"), reverse=True):
            if f.name[7:17] > until:
                continue
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
                if client and r.get("client") != client:
                    continue                                  # exact client address, from a tcp_accept / tcp_refused record
                if unit != "" and (r.get("ev") != "coil" or str(r.get("a")) != str(unit)):
                    continue                                  # a module id: its light commands
                if tw:
                    stamp = r.get("t") or ""
                    if len(stamp) < 16 or stamp[0] != "2":
                        continue                              # no gateway time on it, so it cannot be placed in a window
                    hm = stamp[11:16]
                    if not (tw[0] <= hm <= tw[1] if tw[0] <= tw[1] else hm >= tw[0] or hm <= tw[1]):
                        continue
                rows.append(r)
    rows.sort(key=lambda r: (r.get("t") or r.get("collected", ""), r.get("seq", 0)), reverse=True)
    return {"rows": rows[offset:offset + limit], "matched": len(rows), "scanned": scanned, "limit": limit, "offset": offset}


# What the dashboard counts: "problems" are the events that mean something went wrong on the bus or the
# network side; everything else (lights, connects, schedule, config) is activity.
PROBLEM_EVENTS = ("bus_quiet", "rtu_heal", "tcp_refused", "link_down", "boot")
TILE_EVENTS = ("coil", "tcp_accept", "tcp_refused", "bus_quiet", "rtu_heal", "boot")


def summary(gw: str = "", days: int = 1, start: str = "", end: str = "") -> dict:
    """Counts for the dashboard over the same window as the list: totals, one row per gateway, and
    a time series (by hour when the window is two days or less, otherwise by day) of lights and problems.
    Buckets are the gateway's own timestamps (local wall time), so a bucket is the hour on the cabinet's clock."""
    root = event_collector.events_root()
    since, until = window(days, start, end)
    span = (datetime.strptime(until, "%Y-%m-%d") - datetime.strptime(since, "%Y-%m-%d")).days + 1
    hourly = span <= 2
    totals = {k: 0 for k in TILE_EVENTS}
    per, buckets, clients, units = {}, {}, set(), set()
    dirs = [root / gw] if gw else sorted(p for p in root.iterdir() if p.is_dir())
    for d in dirs:
        if not d.is_dir() or d.resolve().parent != root.resolve():
            continue
        row = per.setdefault(d.name, {"gw": d.name, "last": "", **{k: 0 for k in TILE_EVENTS}})
        for f in sorted(d.glob("events-*.jsonl"), reverse=True):
            if f.name[7:17] > until:
                continue
            if f.name[7:17] < since:
                break
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                ev = r.get("ev", "")
                if r.get("client"):
                    clients.add(r["client"])                  # the pick-lists on the page: who connected, which modules were driven
                if ev == "coil":
                    units.add(int(r.get("a", 0)))
                if ev in TILE_EVENTS:
                    totals[ev] += 1
                    row[ev] += 1
                t = r.get("t") or r.get("collected", "")
                if len(t) >= 13 and t[0] == "2":
                    row["last"] = max(row["last"], t)
                    key = t[:13] if hourly else t[:10]
                    if since <= key[:10] <= until:
                        b = buckets.setdefault(key, {"lights": 0, "problems": 0})
                        if ev == "coil":
                            b["lights"] += 1
                        elif ev in PROBLEM_EVENTS:
                            b["problems"] += 1
    series = []
    if buckets:
        if hourly:
            first = datetime.strptime(since + "T00", "%Y-%m-%dT%H")
            last = min(datetime.now().replace(minute=0, second=0, microsecond=0),
                       datetime.strptime(until + "T23", "%Y-%m-%dT%H"))
            step, fmt = timedelta(hours=1), "%Y-%m-%dT%H"
        else:
            first = datetime.strptime(since, "%Y-%m-%d")
            last = datetime.strptime(until, "%Y-%m-%d")
            step, fmt = timedelta(days=1), "%Y-%m-%d"
        cur = first
        while cur <= last:                                        # empty buckets are real zeros, not gaps
            k = cur.strftime(fmt)
            series.append({"t": k, **buckets.get(k, {"lights": 0, "problems": 0})})
            cur += step
    def ip_key(x):
        return tuple(int(p) if p.isdigit() else 0 for p in x.split("."))

    return {"since": since, "until": until, "hourly": hourly, "totals": totals,
            "clients": sorted(clients, key=ip_key), "units": sorted(units),
            "gateways": sorted(per.values(), key=lambda r: r["gw"]), "series": series}


CSV_COLUMNS = ("t", "gw", "ev", "text", "client", "seq", "up", "a", "p", "collected")


def csv_bytes(gw: str = "", days: int = 1, ev: str = "", q: str = "", start: str = "", end: str = "",
              tfrom: str = "", tto: str = "", client: str = "", unit: str = "") -> bytes:
    """The same filter as the screen, every matching row, oldest first. UTF-8 with a BOM so
    Excel reads the Thai text; a leading =,+,-,@ in any cell is defused so a log line can never
    be read back as a formula."""
    import csv
    import io
    rows = query(gw, days, ev, q, everything=True, start=start, end=end, tfrom=tfrom, tto=tto, client=client, unit=unit)["rows"]
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
