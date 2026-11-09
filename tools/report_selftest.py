"""Site report: the one-page summary, the optional appendix, and the helpers, from synthetic records (no hardware).

    .venv/Scripts/python tools/report_selftest.py
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import fw_survey, lgs_map, report_pdf  # noqa: E402


def records(mixed=False, silent=()):
    out = []
    for r in range(1, 11):
        for c in range(1, 5):
            i = r * 10 + c
            if i in silent:
                out.append(fw_survey.ModuleRecord(device_id=i))
                continue
            out.append(fw_survey.ModuleRecord(device_id=i, responded=True, device_type=10, hw_raw=510, reported_id=i, boots=84,
                                              health=1, uid="004F004B3745501920343159",
                                              fw_raw=30504 if (mixed and r <= 4) else 30505))
    return out


def build(recs, ntp="ok", soak=None):
    info = {"fw": "1.15.0-dev", "net.state": "up", "net.ip": "192.168.99.111", "net.port": "502", "time.now": "2026-11-09T14:54:13",
            "ntp.state": ntp, "sched.reset": "03:00@daily", "sys.wdt": "8000"}
    return report_pdf.build_report_pdf(
        app_version="2.0.0", generated=datetime(2026, 11, 9, 14, 54), info=info,
        settings={"sys.name": "Chest-Std-11", "bus.hub_map": "1,1,2,2,3,4,5,6,7,8", "rs485.baud": "9600"},
        cabinet_label="LGS-40", cabinet_count=40, widths=[4] * 10, records=recs, hub_channel=lgs_map.hub_channel,
        events=("#1  2026-11-09T14:44:24  up=10s  boot a=0 p=0",), soak=soak)


def pages(pdf: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page(?![s])", pdf))


def main() -> int:
    bad = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            bad.append(name)

    check("ranges join consecutive ids", report_pdf._ranges([11, 12, 13, 21, 41, 42]) == "11–13, 21, 41–42")
    check("ranges of nothing is empty", report_pdf._ranges([]) == "")

    clean = build(records())
    check("a clean cabinet is a PDF", clean[:4] == b"%PDF")
    check("nothing is left out: summary, modules, gateway (3 pages for 40 modules without stats)", pages(clean) == 3)
    mixed = build(records(mixed=True, silent=(41, 42)), ntp="failed")
    check("a silent module and mixed versions still render", mixed[:4] == b"%PDF" and pages(mixed) == 3)
    stats = records()
    for r in stats:
        r.stats = fw_survey.ModuleStats(total_on_count=6000, total_on_time_s=170000, op_seconds=3300000)
    check("the statistics table is added when modules report them", pages(build(stats)) == 4)
    from app import soak_csv
    csv = ("time,device_id,kind,detail\n"
           "2026-11-09 13:16:20,0,start,ids=40 gap_s=2.0 counter_every=5 slow_ms=400 crossing_slow_ms=4000 mode=poll\n"
           "2026-11-09 13:16:30,0,heartbeat,pass=1 reads=40 fails=0 reboots=0 wdt=0 worst_ms=63 cross=8 worst_cross_ms=63 writes=0 "
           "write_fails=0 picks=0 dropped=0 lit=0 elapsed_s=10\n"
           "2026-11-09 13:32:30,0,stop,reason=cancelled pass=105 reads=5814 fails=0 reboots=0 wdt=0 worst_ms=891 cross=1001 "
           "worst_cross_ms=735 writes=0 write_fails=0 picks=0 dropped=0 lit=0 elapsed_s=960\n")
    soak = soak_csv.parse_soak_csv(csv, "soak-Chest-Std-11-x.csv")
    with_soak = build(records(), soak=soak)
    check("an attached soak result adds its page", pages(with_soak) == 4)
    check("the report carries the Tool's own font", b"IBMPlexSansThai" in clean)
    check("both weights are bundled", all(os.path.isfile(os.path.join(report_pdf._FONT_DIR, f"IBMPlexSansThai-{w}.ttf")) for w in ("Regular", "Bold")))
    print("ALL PASS" if not bad else "FAILED: " + ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
