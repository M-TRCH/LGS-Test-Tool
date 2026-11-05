"""One-shot gateway health for the Cabinets page.

A probe is one short TCP connection that asks INFO and closes: it never sits
on one of the gateway's two client slots. INFO is answered by the gateway
itself and never reaches the RS485 bus, so probing a cabinet in use costs the
cabinet nothing it measures.
"""
from __future__ import annotations

import time


def _i(kv: dict, key: str, default: int = 0) -> int:
    try:
        return int(float(kv.get(key, default)))
    except (TypeError, ValueError):
        return default


def judge(h: dict) -> tuple[str, list[str]]:
    """-> (state, reasons). state: ok | warn | bad. Pure, so it can be tested
    without a gateway. Safe mode and an unreachable gateway are bad; things
    worth a look (both slots busy, another master, clock unset, NTP down,
    event log off) are warnings. The RS485 repair counters are cumulative
    since the gateway booted, so they are shown but not judged here: a verdict
    on them needs a run's DELTA, which is what the soak computes."""
    if not h.get("reachable"):
        return "bad", [h.get("error") or "unreachable"]
    why_bad, why_warn = [], []
    if h.get("console") is False:
        why_warn.append(h.get("error") or "console refused (firmware older than 1.12 or net.console=0)")
    if h.get("clients", 0) >= 2:
        why_warn.append("both client slots busy")
    if h.get("other_clients"):
        who = (": " + ", ".join(h["other_masters"])) if h.get("other_masters") else ""
        why_warn.append(f"{h['other_clients']} other client(s) connected{who}")
    if h.get("time_set") is False:
        why_warn.append("clock not set (scheduled reset will not run)")
    if h.get("ntp") not in (None, "", "ok", "off"):
        why_warn.append(f"NTP {h['ntp']}")
    if h.get("log_state") not in (None, "", "ok"):
        why_warn.append(f"event log {h['log_state']}")
    if h.get("safe"):
        why_bad.append("gateway is in safe mode")
    return ("bad" if why_bad else "warn" if why_warn else "ok"), why_bad + why_warn


def probe(host: str, port: int = 502, *, timeout_s: float = 3.0, my_ip: str = "") -> dict:
    from ..gateway_tcp import GatewayTcpLink, register_pdu
    from ..transports import TcpSettings, make_client

    h: dict = {"host": host, "port": port, "reachable": False, "error": "",
               "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    client = None
    t0 = time.monotonic()
    try:
        client = make_client(TcpSettings(host=host, port=port, timeout_s=timeout_s), retries=0)
        if not client.connect():
            h["error"] = "cannot connect"
            return _final(h)
        register_pdu(client)
        res = GatewayTcpLink(client, timeout_s=timeout_s).command("INFO")
        h["rtt_ms"] = int((time.monotonic() - t0) * 1000)
        h["reachable"] = True
        if not res.ok:
            h["console"] = False
            h["error"] = (res.error_text or res.err or "INFO refused")[:80]
            return _final(h)

        kv: dict = {}
        for row in res.rows:
            kv.update(row)
        h.update(console=True, fw=kv.get("fw", "?"), name=kv.get("sys.name", ""),
                 up_s=_i(kv, "sys.up"), reset=kv.get("sys.reset", ""), safe=kv.get("sys.safe") == "1",
                 clients=_i(kv, "net.client"), time_set=kv.get("time.set") == "1",
                 time_now=kv.get("time.now", ""), ntp=kv.get("ntp.state", ""),
                 log_state=kv.get("log.state", ""), log_n=_i(kv, "log.n"),
                 sched=kv.get("sched.reset", ""))
        peers = [p for p in kv.get("net.peer", "").split(",") if p and p != "-"]
        # One client is always this probe. Which one: by address when the
        # gateway sees our own IP; behind a router or NAT (the tool reached
        # over a VPN) it does not, so only the COUNT can be trusted.
        others, mine = [], False
        for p in peers:
            if not mine and my_ip and p.split(":")[0] == my_ip:
                mine = True
                continue
            others.append(p)
        h["other_clients"] = max(0, h["clients"] - 1)
        h["other_masters"] = others if (mine and len(others) == h["other_clients"]) else []
        if "rtu.heal" in kv:
            h["rtu"] = {"healed": _i(kv, "rtu.retry_ok"), "heal_failed": _i(kv, "rtu.retry_fail"),
                        "resync": _i(kv, "rtu.resync"), "timeouts": _i(kv, "cnt.rs485_timeout"),
                        "bad_crc": _i(kv, "rtu.bad_crc"), "bad_other": _i(kv, "rtu.bad_other")}
        return _final(h)
    except Exception as exc:                                     # noqa: BLE001
        msg = str(exc)
        # A third client is accepted and closed at once; what the caller sees
        # is a refused tunnel call, which is not a console problem.
        h["error"] = ("connection closed by the gateway (both client slots busy?)"
                      if "refused FC41" in msg or "closed" in msg.lower() else f"{type(exc).__name__}: {msg}"[:90])
        return _final(h)
    finally:
        try:
            if client is not None:
                client.close()
        except Exception:                                        # noqa: BLE001
            pass


def _final(h: dict) -> dict:
    h["state"], h["reasons"] = judge(h)
    return h
