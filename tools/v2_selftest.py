"""Self-test for the v1.9.6 / v2.0 server pieces that need no gateway.

    .venv\\Scripts\\python tools\\v2_selftest.py

Covers: web password (hash, cookie, expiry, rotation, lockout), sites store
(validation, duplicates, Excel CSV incl. Thai and cp874), gateway health
judgement, the event collector against a simulated ring, the events query and
the soak-file name guard. Everything runs against a throwaway data folder.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="lgs_v2_selftest_")
os.environ["LGS_TT_DATA_DIR"] = _tmp
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import auth, event_collector as ec            # noqa: E402
from app.gateway_config import parse_response_lines    # noqa: E402
from app.v2 import events_api, health, sites, soak_api  # noqa: E402

_results: list = []


def case(name):
    def deco(fn):
        try:
            fn()
            _results.append((name, True, ""))
        except Exception as exc:                                  # noqa: BLE001
            _results.append((name, False, f"{type(exc).__name__}: {exc}"))
        return fn
    return deco


def raises(exc_type, fn, *a):
    try:
        fn(*a)
    except exc_type:
        return True
    raise AssertionError(f"expected {exc_type.__name__}")


# ── web password ─────────────────────────────────────────────────────────────
@case("password: off until set, hash verifies, short refused")
def _():
    assert not auth.enabled()
    raises(ValueError, auth.set_password, "abc")
    auth.set_password("secret1")
    assert auth.enabled() and auth.verify("secret1") and not auth.verify("secret2")
    assert "secret1" not in (Path(_tmp) / "auth.json").read_text()


@case("password: cookie valid, tampered, expired, rotated by a new password")
def _():
    tok = auth.make_token(now=1000.0)
    assert auth.token_ok(tok, now=1000.0)
    assert not auth.token_ok(tok[:-3] + "000", now=1000.0)
    assert not auth.token_ok(tok, now=1000.0 + auth.SESSION_S + 1)
    auth.set_password("secret2")
    assert not auth.token_ok(tok, now=1000.0)


@case("password: lockout after 5 wrong, open redirect refused, clear reopens")
def _():
    for _i in range(auth.FAIL_MAX):
        auth._note_fail("9.9.9.9")
    assert auth._locked("9.9.9.9")
    assert not auth._locked("9.9.9.9", now=time.time() + auth.LOCK_S + 1)
    assert auth._safe_next("//evil.example") == "/" and auth._safe_next("https://x") == "/"
    assert auth._safe_next("/v2?a=1") == "/v2?a=1"
    auth.clear_password()
    assert not auth.enabled()


# ── sites ────────────────────────────────────────────────────────────────────
@case("sites: validation names every bad field")
def _():
    s = sites._norm({"name": "", "host": "bad host!", "port": 99999, "cabinet": "zzz"})
    errs = sites.validate(s)
    assert len(errs) == 4, errs
    raises(ValueError, sites.save, [{"name": "", "host": "x"}])


@case("sites: duplicate address and name are warned, not refused")
def _():
    a = sites.save([{"name": "A", "host": "10.0.0.1"}, {"name": "B", "host": "10.0.0.1"},
                    {"name": "a", "host": "10.0.0.2"}])
    w = sites.warnings(a)
    assert len(w) == 2 and any("10.0.0.1:502" in x for x in w) and any("'a'" in x for x in w), w


@case("sites: CSV round trip with Thai, comma and quote; cp874; bad header")
def _():
    rows = [{"name": 'ตู้ ทดสอบ, "ชั้น 1"', "host": "10.0.0.5", "port": 502, "cabinet": "lgs40",
             "site": "รพ.", "note": "x"}]
    text = sites.to_csv([sites._norm(r) for r in rows])
    assert text.startswith("﻿") and "\r\n" in text
    back = sites.from_csv(text.encode("utf-8"))
    assert back[0]["name"] == rows[0]["name"] and back[0]["site"] == "รพ."
    thai = "name,host\r\nตู้ ทดสอบ,10.0.0.6\r\n".encode("cp874")
    assert sites.from_csv(thai)[0]["name"] == "ตู้ ทดสอบ"
    raises(ValueError, sites.from_csv, b"a,b\r\n1,2\r\n")
    raises(ValueError, sites.from_csv, b"")


# ── health judgement ─────────────────────────────────────────────────────────
@case("health: unreachable bad, safe mode bad, clock/other client warn, clean ok")
def _():
    assert health.judge({"reachable": False, "error": "x"})[0] == "bad"
    base = {"reachable": True, "console": True, "clients": 1, "time_set": True, "ntp": "ok",
            "log_state": "ok", "other_clients": 0}
    assert health.judge(base)[0] == "ok"
    assert health.judge({**base, "safe": True})[0] == "bad"
    assert health.judge({**base, "time_set": False})[0] == "warn"
    st, why = health.judge({**base, "clients": 2, "other_clients": 1})
    assert st == "warn" and any("other client" in w for w in why)
    assert health.judge({**base, "console": False})[0] == "warn"


# ── collector + events ───────────────────────────────────────────────────────
class _Ring:
    def __init__(self):
        self.ev, self.oldest = [], 1

    def add(self, ev, a=0, p=0, t="2026-10-30T09:00:00"):
        self.ev.append(dict(i=len(self.ev) + 1, t=t, up=1, ev=ev, a=a, p=p))

    def command(self, line, **kw):
        w, total = line.split(), len(self.ev)
        if w[:2] == ["LOG", "SINCE"]:
            since = int(w[2])
            if since > total:
                return parse_response_lines([f"#OK LOG n=0 total={total} next={total} gap=2 oldest={self.oldest}"])
            start, gap = since + 1, 0
            if self.oldest > start:
                start, gap = self.oldest, 1
            sel = [e for e in self.ev if e["i"] >= start][:100]
            ls = ["#DATA i={i} t={t} up={up} ev={ev} a={a} p={p}".format(**e) for e in sel]
            ls.append(f"#OK LOG n={len(sel)} total={total} next={sel[-1]['i'] if sel else since} gap={gap} oldest={self.oldest}")
            return parse_response_lines(ls)
        return parse_response_lines([f"#OK LOG n=1 total={total}"])


@case("collector: paging, accept+peer join, cursor, deferral, gap, replaced board")
def _():
    g = _Ring()
    g.add("boot", 2, 1)
    for _i in range(130):
        g.add("link_up")
    g.add("tcp_accept", 1, 87)
    g.add("tcp_peer", 99, (192 << 8) | 168)
    g.add("coil", 11, 1011 | 0x8000)
    g.add("tcp_accept", 2, 5)                    # newest: companion not written yet
    root = Path(tempfile.mkdtemp(dir=_tmp))
    col = ec.Collector(lambda: [("G", "h", 502)], root=root, opener=lambda h, p: (g, lambda: None))
    r = col.poll_all()[0]
    assert r["ok"], r
    rows = [json.loads(x) for f in (root / "G").glob("events-*.jsonl") for x in f.read_text(encoding="utf-8").splitlines()]
    texts = [x["text"] for x in rows]
    assert "client 192.168.99.87 connected (slot 1)" in texts and "unit 11 coil 1011 ON" in texts
    assert not any(x["ev"] == "tcp_peer" for x in rows)
    assert not any("slot 2" in x for x in texts), "deferred accept must wait for its peer"
    g.add("tcp_peer", 99, (192 << 8) | 168)
    col.poll_all()
    rows = [json.loads(x) for f in (root / "G").glob("events-*.jsonl") for x in f.read_text(encoding="utf-8").splitlines()]
    seqs = [x["seq"] for x in rows if x["seq"]]
    assert len(seqs) == len(set(seqs)), "duplicates"
    assert any("192.168.99.5 connected (slot 2)" in x["text"] for x in rows)
    for _i in range(10):
        g.add("coil", 12, 1002)
    g.oldest = len(g.ev) - 3
    col.poll_all()
    rows = [json.loads(x) for f in (root / "G").glob("events-*.jsonl") for x in f.read_text(encoding="utf-8").splitlines()]
    assert any(x["ev"] == "collector_gap" and "lost" in x["text"] for x in rows)
    g2 = _Ring()
    g2.add("boot", 2, 1)
    col._open = lambda h, p: (g2, lambda: None)
    col.poll_all()
    rows = [json.loads(x) for f in (root / "G").glob("events-*.jsonl") for x in f.read_text(encoding="utf-8").splitlines()]
    assert any("board replaced" in x["text"] for x in rows)


@case("collector: firmware without LOG SINCE is refused, not re-stored; failures reported")
def _():
    class Old:
        def command(self, line, **kw):
            return parse_response_lines(["#DATA i=5 t=- up=1 ev=boot a=0 p=0", "#OK LOG n=1 total=5"])
    root = Path(tempfile.mkdtemp(dir=_tmp))
    col = ec.Collector(lambda: [("Old", "h", 502)], root=root, opener=lambda h, p: (Old(), lambda: None))
    r = col.poll_all()[0]
    assert not r["ok"] and "too old" in r["error"]
    assert not list((root / "Old").glob("events-*.jsonl"))
    col._open = lambda h, p: (_ for _ in ()).throw(ConnectionError("refused"))
    assert "refused" in col.poll_all()[0]["error"]


@case("collector: retention purges only old day files")
def _():
    root = Path(tempfile.mkdtemp(dir=_tmp))
    d = root / "G"
    d.mkdir()
    (d / "events-2026-01-01.jsonl").write_text("{}\n")
    (d / "events-2099-01-01.jsonl").write_text("{}\n")
    (d / "state.json").write_text("{}")
    col = ec.Collector(lambda: [], root=root, retention_days=90)
    assert col.purge() == 1
    assert not (d / "events-2026-01-01.jsonl").exists() and (d / "events-2099-01-01.jsonl").exists()
    assert (d / "state.json").exists()


@case("events query: filters, newest first, no path walking")
def _():
    root = event_collector_root = ec.events_root()
    d = root / "Q"
    d.mkdir(exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    rows = [{"gw": "Q", "seq": i, "t": f"{today}T10:00:0{i}", "ev": "coil" if i % 2 else "boot", "text": f"row {i}"}
            for i in range(1, 6)]
    (d / f"events-{today}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    r = events_api.query(gw="Q", days=1)
    assert r["matched"] == 5 and r["rows"][0]["seq"] == 5
    assert events_api.query(gw="Q", ev="coil")["matched"] == 3
    assert events_api.query(gw="Q", q="row 2")["matched"] == 1
    assert events_api.query(gw="../..")["matched"] >= 0          # resolves outside -> skipped, no error
    assert all(x["gw"] == "Q" for x in events_api.query(gw="../..")["rows"]) or not events_api.query(gw="../..")["rows"]


@case("soak files: only produced names are readable")
def _():
    ex = soak_api.exports_dir()
    (ex / "fleet-20261030-100000.txt").write_text("v")
    (ex / "soak-Fake-40-20261030-100000.csv").write_text("c")
    runs = soak_api.runs()
    assert runs and runs[0]["verdict"] == "fleet-20261030-100000.txt" and runs[0]["csv"]
    assert soak_api.read_file("fleet-20261030-100000.txt")[1] == "verdict"
    for bad in ("../x.txt", "..\\x.txt", "config.json", "fleet-1.txt", "auth.json"):
        raises(ValueError, soak_api.read_file, bad)


def main() -> int:
    width = max(len(n) for n, _, _ in _results)
    for name, ok, why in _results:
        print(f"{name:<{width}}  {'ok' if ok else 'FAIL  ' + why}")
    bad = sum(1 for _, ok, _ in _results if not ok)
    print(f"\n{len(_results) - bad}/{len(_results)} cases pass")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
