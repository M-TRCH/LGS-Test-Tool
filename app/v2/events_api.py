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


def _split(text: str, ws: bool = False) -> set:
    """A comma list from the page ("a,b") as a set; `ws` also splits on spaces (event types never contain one)."""
    return {x.strip() for x in re.split(r"[,\s]+" if ws else r",", text or "") if x.strip()}


class _Filter:
    """Which filters a record fails. The page filters like a parametric part search: tick values in several groups (gateway,
    event type, client, module) and every group narrows the result, with each option's count showing what ticking it WOULD
    leave, so a count is computed with that option's own group left out. `fails()` therefore returns the set of groups a
    record fails rather than one yes/no."""

    def __init__(self, gw="", ev="", client="", unit="", tfrom="", tto="", q=""):
        self.gw, self.ev, self.client, self.unit = _split(gw), _split(ev, True), _split(client), _split(unit)
        self.tw = time_window(tfrom, tto)           # a time of day on every chosen day; "from" later than "to" wraps past midnight
        self.needle = (q or "").strip().lower()

    def fails(self, name: str, r: dict) -> set:
        out = set()
        ev = r.get("ev")
        if self.gw and name not in self.gw:
            out.add("gw")
        if self.ev and ev not in self.ev:
            out.add("ev")
        if self.client and r.get("client") not in self.client:
            out.add("client")                       # the address is only on tcp_accept / tcp_refused records
        if self.unit and not (ev == "coil" and str(r.get("a")) in self.unit):
            out.add("unit")                         # a module id: its light commands
        if self.tw:
            stamp = r.get("t") or ""
            hm = stamp[11:16]
            if len(stamp) < 16 or stamp[0] != "2":
                out.add("time")                     # no gateway time on it, so it cannot be placed in a window
            elif not (self.tw[0] <= hm <= self.tw[1] if self.tw[0] <= self.tw[1] else hm >= self.tw[0] or hm <= self.tw[1]):
                out.add("time")
        if self.needle and self.needle not in (r.get("text", "") + " " + r.get("client", "")).lower():
            out.add("q")
        return out


def _records(since: str, until: str, only=None):
    """Every (gateway folder name, record) in the window; `only` limits it to those gateway folders."""
    root = event_collector.events_root()
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if only and d.name not in only:
            continue
        for f in sorted(d.glob("events-*.jsonl"), reverse=True):
            if f.name[7:17] > until:
                continue
            if f.name[7:17] < since:
                break
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    yield d.name, json.loads(line)
                except ValueError:
                    continue


def query(gw: str = "", days: int = 1, ev: str = "", q: str = "", limit: int = 500,
          everything: bool = False, start: str = "", end: str = "", offset: int = 0,
          tfrom: str = "", tto: str = "", client: str = "", unit: str = "") -> dict:
    """Newest first. `gw`, `ev`, `client` and `unit` are comma lists (several values = any of them); empty = no limit.
    `everything` lifts the row cap (the screen shows a page; the CSV export wants all);
    `offset` skips that many matches, for paging."""
    limit = 10 ** 9 if everything else max(1, min(int(limit), 2000))
    offset = max(0, int(offset))
    since, until = window(days, start, end)
    flt = _Filter(gw, ev, client, unit, tfrom, tto, q)
    rows, scanned = [], 0
    for name, r in _records(since, until, flt.gw or None):
        scanned += 1
        if not flt.fails(name, r):
            rows.append(r)
    rows.sort(key=lambda r: (r.get("t") or r.get("collected", ""), r.get("seq", 0)), reverse=True)
    return {"rows": rows[offset:offset + limit], "matched": len(rows), "scanned": scanned, "limit": limit, "offset": offset}


# What the dashboard counts: "problems" are the events that mean something went wrong on the bus or the
# network side; everything else (lights, connects, schedule, config) is activity.
PROBLEM_EVENTS = ("bus_quiet", "rtu_heal", "tcp_refused", "link_down", "boot")
TILE_EVENTS = ("coil", "tcp_accept", "tcp_refused", "bus_quiet", "rtu_heal", "boot")
HIDDEN_TYPES = ("tcp_peer",)          # folded into the tcp_accept before it, never a row of its own


def summary(gw: str = "", days: int = 1, start: str = "", end: str = "", ev: str = "", client: str = "", unit: str = "",
            tfrom: str = "", tto: str = "") -> dict:
    """One pass over the window for the whole dashboard side of the page: the counters, one row per gateway, a time series
    (by hour when the window is two days or less, otherwise by day) of lights and problems, and the option lists with counts
    for the filter groups. The counters, chart and table follow every filter EXCEPT the event-type one (filtering to one type
    would blank the rest of the dashboard); each option count leaves out its own group (see _Filter).
    Buckets are the gateway's own timestamps (local wall time), so a bucket is the hour on the cabinet's clock."""
    since, until = window(days, start, end)
    span = (datetime.strptime(until, "%Y-%m-%d") - datetime.strptime(since, "%Y-%m-%d")).days + 1
    hourly = span <= 2
    flt = _Filter(gw, ev, client, unit, tfrom, tto)
    totals = {k: 0 for k in TILE_EVENTS}
    per, buckets = {}, {}
    facets = {"gw": {}, "ev": {}, "client": {}, "unit": {}}
    root = event_collector.events_root()
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if not flt.gw or d.name in flt.gw:
            per[d.name] = {"gw": d.name, "last": "", **{k: 0 for k in TILE_EVENTS}}
        facets["gw"].setdefault(d.name, 0)
    for name, r in _records(since, until):
        ev_name = r.get("ev", "")
        f = flt.fails(name, r)
        if "time" in f or "q" in f:
            continue
        if f <= {"gw"}:
            facets["gw"][name] = facets["gw"].get(name, 0) + 1
        if f <= {"ev"} and ev_name not in HIDDEN_TYPES:
            facets["ev"][ev_name] = facets["ev"].get(ev_name, 0) + 1
        if f <= {"client"} and r.get("client"):
            facets["client"][r["client"]] = facets["client"].get(r["client"], 0) + 1
        if f <= {"unit"} and ev_name == "coil":
            u = str(r.get("a", 0))
            facets["unit"][u] = facets["unit"].get(u, 0) + 1
        if not f <= {"ev"}:
            continue
        row = per[name]
        if ev_name in TILE_EVENTS:
            totals[ev_name] += 1
            row[ev_name] += 1
        t = r.get("t") or r.get("collected", "")
        if len(t) >= 13 and t[0] == "2":
            row["last"] = max(row["last"], t)
            key = t[:13] if hourly else t[:10]
            if since <= key[:10] <= until:
                b = buckets.setdefault(key, {"lights": 0, "problems": 0})
                if ev_name == "coil":
                    b["lights"] += 1
                elif ev_name in PROBLEM_EVENTS:
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

    opts = {
        "gw": [{"v": k, "n": n} for k, n in sorted(facets["gw"].items())],
        "ev": [{"v": k, "n": n} for k, n in sorted(facets["ev"].items(), key=lambda kv: (-kv[1], kv[0]))],
        "client": [{"v": k, "n": n} for k, n in sorted(facets["client"].items(), key=lambda kv: ip_key(kv[0]))],
        "unit": [{"v": k, "n": n} for k, n in sorted(facets["unit"].items(), key=lambda kv: int(kv[0]))],
    }
    return {"since": since, "until": until, "hourly": hourly, "totals": totals, "facets": opts,
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
