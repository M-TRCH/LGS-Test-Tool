"""Gateway event collector: pulls each gateway's event log into dated files.

The gateway keeps its own ring of events (boots, link drops, clients coming and
going, coil writes, bus silence...). That ring is ~98k records and survives
power cuts, but nobody reads it unless somebody asks. This module asks, on a
timer, from the server the Test Tool runs on, and appends what is new to
data/events/<gateway>/events-YYYY-MM-DD.jsonl -- one JSON object per line, so
a month of a ward is greppable and a spreadsheet can read it.

Pull, not push, on purpose: the gateway answers the same console it already
has (`LOG SINCE <seq>`, firmware >= 1.14.0, over unit 255 / FC 0x41 on port
502), nothing new has to be reachable from the gateway side, and a collector
that was off for a week simply catches up from the ring. `next=` in the
answer is the cursor; it is kept in state.json beside the files. If the ring
overwrote events before the collector came (`gap=1`) or the board was
replaced (`gap=2`) a marker record says so instead of the file pretending
nothing was lost.

Cost to the gateway: one short TCP connection per gateway per interval, and
the gateway accepts only two clients (a soak holds one). A refused or failed
connection is skipped and retried next interval -- the collector never holds
a slot between polls. OFF by default (config `events_enabled`).
"""
from __future__ import annotations

import json
import re
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterable, Optional

from . import applog, config_store

PAGE = 100                 # records per LOG SINCE (the firmware's cap)
MAX_PAGES = 20             # per gateway per poll: 2,000 records, then next interval
FIRST_BACKLOG = 1000       # first contact: start this far back, not at seq 1
FILE_RE = re.compile(r"^events-(\d{4}-\d{2}-\d{2})\.jsonl$")


def events_root() -> Path:
    d = config_store.data_dir() / "events"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _stem(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._") or "gateway"


def describe(rec: dict, client_ip: Optional[str] = None) -> str:
    """One human line for a record. `client_ip` is the full address when the
    accept/refused record had its tcp_peer companion."""
    ev, a, p = rec.get("ev", ""), int(rec.get("a", 0)), int(rec.get("p", 0))
    if ev == "coil":
        addr, on, noreply = p & 0x3FFF, bool(p & 0x8000), bool(p & 0x4000)
        who = "broadcast" if a == 0 else f"unit {a}"
        return (f"{who} coil {addr} {'ON' if on else 'OFF'}"
                + (" (no reply from the module)" if noreply else ""))
    if ev == "tcp_accept":
        return f"client {client_ip or '?.?.?.' + str(p)} connected (slot {a})"
    if ev == "tcp_refused":
        return f"client {client_ip or '?.?.?.' + str(p)} refused (both slots busy)"
    if ev == "tcp_close":
        return f"client disconnected (slot {a})"
    if ev == "tcp_peer":
        return f"client address prefix {p >> 8}.{p & 0xFF}.{a}"
    if ev == "coil_dropped":
        return f"{p} coil events not recorded (rate limit)"
    if ev == "rtu_heal":
        return f"gateway repaired {p} missed RS485 replies" + (f", {a} repairs failed" if a else "")
    if ev == "bus_quiet":
        return "RS485 bus went silent" if a == 1 else f"RS485 bus back after {p} s"
    if ev == "boot":
        return f"gateway booted (reset code {a}, attempt {p})"
    if ev == "link_up":
        return "Ethernet link up"
    if ev == "link_down":
        return "Ethernet link down"
    if ev == "cfg_saved":
        return "settings saved"
    if ev == "sched_reset":
        return "scheduled reset fired"
    if ev == "panel_sweep":
        return f"panel button {p} pressed (action {a})"
    if ev == "clock_set":
        return f"clock set (source {a})"
    if ev == "out_fixed":
        return f"output {a} re-asserted to {p}"
    if ev == "fw_update":
        return f"firmware update (stage {a}, {p} KB)"
    if ev == "store_erased":
        return "settings store erased"
    return ev or "unknown"


def _day(rec: dict, fallback: datetime) -> str:
    t = rec.get("t", "-")
    if isinstance(t, str) and len(t) >= 10 and t[4] == "-":
        return t[:10]
    return f"{fallback:%Y-%m-%d}"


def _default_open(host: str, port: int):
    """-> (link, close). Imported lazily: pymodbus is heavy and the collector
    is off on most machines."""
    from .gateway_tcp import GatewayTcpLink, register_pdu
    from .transports import TcpSettings, make_client
    client = make_client(TcpSettings(host=host, port=port, timeout_s=4.0), retries=0)
    if not client.connect():
        raise ConnectionError(f"cannot reach {host}:{port}")
    register_pdu(client)
    return GatewayTcpLink(client), client.close


class Collector:
    def __init__(self, roster: Callable[[], Iterable[tuple]], *,
                 root: Optional[Path] = None, retention_days: int = 90,
                 opener: Callable = _default_open) -> None:
        self._roster = roster                  # -> (name, host, port) tuples
        self._root = root
        self.retention_days = retention_days
        self._open = opener
        self.status: dict[str, dict] = {}      # per gateway, for a status line
        self._last_purge = 0.0
        self._lock = threading.Lock()

    # ── storage ─────────────────────────────────────────────────────────────
    def _dir(self, name: str) -> Path:
        d = (self._root or events_root()) / _stem(name)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _state(self, name: str) -> dict:
        try:
            return json.loads((self._dir(name) / "state.json").read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self, name: str, st: dict) -> None:
        p = self._dir(name) / "state.json"
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
        tmp.replace(p)

    def _append(self, name: str, host: str, recs: list[dict]) -> None:
        now = datetime.now()
        by_day: dict[str, list[str]] = {}
        for r in recs:
            by_day.setdefault(_day(r, now), []).append(json.dumps(r, ensure_ascii=False))
        for day, lines in by_day.items():
            with open(self._dir(name) / f"events-{day}.jsonl", "a", encoding="utf-8",
                      newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")

    def purge(self, now: Optional[datetime] = None) -> int:
        """Delete day files older than the retention. Returns files removed."""
        cutoff = (now or datetime.now()) - timedelta(days=self.retention_days)
        gone = 0
        base = self._root or events_root()
        for d in base.iterdir() if base.exists() else ():
            if not d.is_dir():
                continue
            for f in d.iterdir():
                m = FILE_RE.match(f.name)
                if m and datetime.strptime(m.group(1), "%Y-%m-%d") < cutoff:
                    try:
                        f.unlink()
                        gone += 1
                    except OSError:
                        pass
        return gone

    # ── one gateway ─────────────────────────────────────────────────────────
    def poll_gateway(self, name: str, host: str, port: int = 502) -> dict:
        out = {"name": name, "host": host, "ok": False, "new": 0, "error": "",
               "at": datetime.now().isoformat(timespec="seconds")}
        try:
            link, close = self._open(host, port)
        except Exception as exc:                                 # noqa: BLE001
            out["error"] = f"{type(exc).__name__}: {exc}"[:100]
            return out
        try:
            st = self._state(name)
            last = st.get("last_seq")
            collected = datetime.now().isoformat(timespec="seconds")
            batch: list[dict] = []
            if last is None:
                first = link.command("LOG 1")
                if not first.ok:
                    out["error"] = (first.error_text or first.err or "LOG refused")[:100]
                    return out
                total = int(first.data.get("total", 0))
                last = max(0, total - FIRST_BACKLOG)
                batch.append({"gw": name, "host": host, "seq": 0, "ev": "collector_start",
                              "text": f"collector started; taking the last "
                                      f"{min(total, FIRST_BACKLOG)} of {total} events",
                              "collected": collected})
            for _ in range(MAX_PAGES):
                res = link.command(f"LOG SINCE {last} {PAGE}")
                if not res.ok:
                    out["error"] = (res.error_text or res.err or "LOG SINCE refused")[:100]
                    break
                if "next" not in res.data:
                    # Firmware before 1.14.0 reads "LOG SINCE 5" as "LOG" with a
                    # junk count and answers with its newest record, which would
                    # be stored again on every poll.
                    out["error"] = "gateway firmware too old for LOG SINCE (needs 1.14.0)"
                    batch = []
                    break
                gap = str(res.data.get("gap", "0"))
                total = int(res.data.get("total", 0))
                if gap == "2":                       # a seq this board never reached
                    batch.append({"gw": name, "host": host, "seq": 0, "ev": "collector_gap",
                                  "text": f"gateway log restarted (had seq {last}, "
                                          f"gateway is at {total}): board replaced or log erased",
                                  "collected": collected})
                    last = total
                    continue
                if gap == "1":
                    batch.append({"gw": name, "host": host, "seq": 0, "ev": "collector_gap",
                                  "text": f"events lost before seq {res.rows[0]['i'] if res.rows else '?'}:"
                                          f" the gateway's ring overwrote them",
                                  "collected": collected})
                rows = list(res.rows)
                consumed_to = last
                for i, row in enumerate(rows):
                    seq = int(row["i"])
                    rec = {"gw": name, "host": host, "seq": seq, "t": row.get("t", "-"),
                           "up": int(row.get("up", 0)), "ev": row.get("ev", ""),
                           "a": int(row.get("a", 0)), "p": int(row.get("p", 0)),
                           "collected": collected}
                    ip = None
                    if rec["ev"] in ("tcp_accept", "tcp_refused"):
                        nxt = rows[i + 1] if i + 1 < len(rows) else None
                        if nxt and nxt.get("ev") == "tcp_peer" and int(nxt["i"]) == seq + 1:
                            pa, pp = int(nxt["a"]), int(nxt["p"])
                            ip = f"{pp >> 8}.{pp & 0xFF}.{pa}.{rec['p']}"
                        elif i + 1 == len(rows) and seq == total:
                            break           # the peer record is not written yet: next poll
                    if (rec["ev"] == "tcp_peer" and i > 0 and int(rows[i - 1]["i"]) == seq - 1
                            and rows[i - 1].get("ev") in ("tcp_accept", "tcp_refused")):
                        consumed_to = seq       # folded into the row before it
                        continue
                    rec["text"] = describe(rec, ip)
                    if ip:
                        rec["client"] = ip
                    batch.append(rec)
                    consumed_to = seq
                last = consumed_to
                if len(rows) < PAGE or consumed_to < int(res.data.get("next", consumed_to)):
                    break
            if batch:
                self._append(name, host, batch)          # files first, cursor second:
            st.update({"last_seq": last, "host": host,   # a crash repeats, never loses
                       "updated": out["at"]})
            self._save_state(name, st)
            out["new"] = sum(1 for r in batch if r.get("seq"))
            out["ok"] = not out["error"]
            return out
        except Exception as exc:                                 # noqa: BLE001
            out["error"] = f"{type(exc).__name__}: {exc}"[:100]
            return out
        finally:
            try:
                close()
            except Exception:                                    # noqa: BLE001
                pass

    # ── all gateways ────────────────────────────────────────────────────────
    def poll_all(self) -> list[dict]:
        results = []
        for entry in list(self._roster()):
            name, host = entry[0], entry[1]
            port = entry[2] if len(entry) > 2 else 502
            r = self.poll_gateway(name, host, port)
            with self._lock:
                self.status[name] = r
            results.append(r)
        if time.monotonic() - self._last_purge > 3600:
            self._last_purge = time.monotonic()
            n = self.purge()
            if n:
                applog.note(f"event collector: removed {n} day files past retention")
        return results

    def run(self, stop: threading.Event, interval_s: float = 60.0) -> None:
        """Blocking loop for a daemon thread. Never raises."""
        while not stop.is_set():
            try:
                self.poll_all()
            except Exception as exc:                             # noqa: BLE001
                applog.note(f"event collector: {type(exc).__name__}: {exc}")
            stop.wait(interval_s)


# ── the server's one collector ───────────────────────────────────────────────
_collector: Optional[Collector] = None
_thread: Optional[threading.Thread] = None
_stop: Optional[threading.Event] = None


def _roster_from(cfg) -> list[tuple]:
    """The saved sites (v2 sites.json) when there are any, else the fleet
    roster ("name|host|cabinet" strings), as (name, host, port)."""
    try:
        from .v2 import sites
        saved = sites.load()
        if saved:
            return [(s["name"], s["host"], s["port"]) for s in saved]
    except Exception:  # noqa: BLE001
        pass
    out = []
    for row in getattr(cfg, "fleet", []) or []:
        parts = str(row).split("|")
        if len(parts) >= 2 and parts[1].strip():
            out.append((parts[0].strip() or parts[1].strip(), parts[1].strip(), 502))
    return out


def status() -> dict:
    """Last poll result per gateway ({} while off)."""
    return dict(_collector.status) if _collector else {}


def apply(cfg) -> None:
    """Start or stop the background collector to match `cfg.events_enabled`.
    Idempotent; safe to call on every change of the setting."""
    global _collector, _thread, _stop
    want = bool(getattr(cfg, "events_enabled", False))
    running = _thread is not None and _thread.is_alive()
    if want and not running:
        _collector = Collector(lambda: _roster_from(cfg),
                               retention_days=int(getattr(cfg, "events_retention_days", 90)))
        _stop = threading.Event()
        _thread = threading.Thread(target=_collector.run,
                                   args=(_stop, float(getattr(cfg, "events_interval_s", 60))),
                                   name="event-collector", daemon=True)
        _thread.start()
        applog.note("event collector started")
    elif not want and running:
        _stop.set()
        applog.note("event collector stopped")
    elif want and _collector:
        _collector.retention_days = int(getattr(cfg, "events_retention_days", 90))
