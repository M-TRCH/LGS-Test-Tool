"""Self-test for gw_ota (the gateway-run module OTA, seen from the Tool) against a scripted gateway console. No network.

Run: .venv/Scripts/python tools/gwota_selftest.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import gw_ota  # noqa: E402
from app.gateway_config import parse_response_lines  # noqa: E402


class FakeLink:
    """A console that answers from a table and remembers what it was asked. Depot has one complete image."""

    def __init__(self, answers, slots=None):
        self.answers = answers
        self.asked = []
        self._slots = slots if slots is not None else [
            {"slot": 0, "state": 0, "size": 0, "crc": 0, "name": ""},
            {"slot": 1, "state": 2, "size": 61304, "crc": 1, "name": "module_v3.5.5"},
            {"slot": 2, "state": 0, "size": 0, "crc": 0, "name": ""},
            {"slot": 3, "state": 0, "size": 0, "crc": 0, "name": ""}]

    def depot_list(self):
        return self._slots

    def command(self, line, **kw):
        self.asked.append(line)
        for prefix, text in self.answers.items():
            if line.startswith(prefix):
                return parse_response_lines(text.split("\n"))
        return parse_response_lines(["#ERR X err=unknown_verb"])

    def hello(self, who="x"):
        return self.command("HELLO " + who)

    def bye(self):
        return self.command("BYE")


def main() -> int:
    bad = []

    def check(name, cond):
        print(f"  {'PASS' if cond else 'FAIL'}  {name}")
        if not cond:
            bad.append(name)

    ok_console = {"HELLO": "#OK HELLO", "BYE": "#OK BYE",
                  "OTA START": "#OK OTA START run=3 image=module_v3.5.5 size=61304 modules=40"}
    link = FakeLink(ok_console)
    r = gw_ota.start(link, "module_v3.5.5", {"idle": 3, "group": 4})
    start_line = next(x for x in link.asked if x.startswith("OTA START"))
    check("start finds the slot by name and arms a session first", link.asked[0].startswith("HELLO") and "slot=1" in start_line)
    check("start passes the validated options", "idle=3" in start_line and "group=4" in start_line and "apply_quiet=300" in start_line)
    check("start returns what the gateway said", r["ok"] and r["run"] == "3")
    check("the session is closed afterwards", link.asked[-1] == "BYE")

    try:
        gw_ota.start(FakeLink(ok_console), "no_such_image", {})
        check("an image the depot does not hold is refused", False)
    except gw_ota.OtaError as exc:
        check("an image the depot does not hold is refused", "no complete image named" in str(exc))

    for bad_opts in ({"idle": 0}, {"group": 9}, {"apply_idle": "x"}, {"apply_quiet": -1}):
        try:
            gw_ota.options(bad_opts)
            check(f"options {bad_opts} refused", False)
        except gw_ota.OtaError:
            check(f"options {bad_opts} refused", True)
    check("defaults fill in", gw_ota.options({}) == gw_ota.DEFAULTS)

    for err, word in (("err=busy", "already"), ("err=clock_unset", "clock"), ("err=usb_busy", "USB"), ("err=no_ids", "layout")):
        link = FakeLink({"HELLO": "#OK HELLO", "BYE": "#OK BYE", "OTA START": f"#ERR OTA {err}"})
        try:
            gw_ota.start(link, "module_v3.5.5", {})
            check(f"{err} is explained", False)
        except gw_ota.OtaError as exc:
            check(f"{err} is explained", word in str(exc))

    # night window (gateway firmware >= 1.15.0)
    link = FakeLink(ok_console)
    gw_ota.start(link, "module_v3.5.5", {"at": "1:00", "until": "04:00", "nights": 2})
    start_line = next(x for x in link.asked if x.startswith("OTA START"))
    check("a window is sent as HHMM, with nights when one is given", "at=0100 until=0400 nights=2" in start_line)
    link = FakeLink(ok_console)
    gw_ota.start(link, "module_v3.5.5", {"at": "01:00", "until": "04:00"})
    start_line = next(x for x in link.asked if x.startswith("OTA START"))
    check("without nights none is sent (the gateway goes on until done)", "at=0100 until=0400" in start_line and "nights" not in start_line)
    link = FakeLink(ok_console)
    gw_ota.start(link, "module_v3.5.5", {})
    check("no window, nothing about one is sent", "at=" not in next(x for x in link.asked if x.startswith("OTA START")))
    for bad_win in ({"at": "01:00"}, {"until": "04:00"}, {"at": "25:00", "until": "01:00"}, {"at": "01:00", "until": "01:00"},
                    {"at": "01:00", "until": "04:00", "nights": 0}, {"at": "01:00", "until": "04:00", "nights": 15}, {"at": "abc", "until": "04:00"}):
        try:
            gw_ota.options(bad_win)
            check(f"window {bad_win} refused", False)
        except gw_ota.OtaError:
            check(f"window {bad_win} refused", True)
    sched = FakeLink({"OTA STATUS": "#DATA state=scheduled run=36 phase=pick ch=0 group=0 chunk=0/0\n#DATA window=1335-1435 nights=0/1 gate=reset_hold\n#OK OTA STATUS"})
    st = gw_ota.status(sched)
    check("a waiting window run reads as scheduled with its gate", st["state"] == "scheduled" and st["gate"] == "reset_hold" and st["window"] == "1335-1435")
    check("scheduled is a known state", "scheduled" in gw_ota.STATE_TEXT)

    old = FakeLink({"OTA STATUS": "#ERR OTA STATUS err=unknown_verb"})
    check("an old firmware is 'unsupported', not an error", gw_ota.status(old) == {"state": "unsupported"})
    run = FakeLink({"OTA STATUS": "#DATA state=running run=2 phase=stream ch=1 group=8 chunk=80/479\n#DATA paused_s=4 failed=0\n#OK OTA STATUS"})
    st = gw_ota.status(run)
    check("status merges the DATA lines", st["state"] == "running" and st["chunk"] == "80/479" and st["paused_s"] == "4")
    check("status_row keeps it under ota", gw_ota.status_row(run)["ota"]["phase"] == "stream")

    res = FakeLink({"OTA RESULT": "#DATA run=2 state=done_ok image=m size=61304 crc=79F7532C start=1 end=2 modules=2\n"
                                  "#DATA id=11 st=updated err=0 tries=0 fw=30504>30505\n#DATA id=12 st=gave_up err=102 tries=6 fw=30504>0\n#OK OTA RESULT"})
    out = gw_ota.result(res, 0)
    check("result splits the run from its modules", out["run"]["state"] == "done_ok" and [m["id"] for m in out["modules"]] == ["11", "12"])
    check("abort arms a session and sends OTA ABORT", (gw_ota.abort(FakeLink({"HELLO": "#OK HELLO", "BYE": "#OK BYE", "OTA ABORT": "#OK OTA ABORT"})) is None))
    print("ALL PASS" if not bad else "FAILED: " + ", ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
