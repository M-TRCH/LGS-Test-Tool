"""Pin the soak-CSV parser's verdicts, especially the one that can lie.

    python tools/soak_csv_selftest.py

The "reboots N (all simultaneous - scheduled reset)" verdict is the single
line a reader trusts instead of 6,000 raw rows, and the first cut earned it
with timestamps alone: a brown-out that IWDG-reset half the cabinet inside
two minutes would have been blessed as the 03:00 schedule. The cluster now
admits only rows whose own text says "iwdg N unchanged" - the distinction
soak.py stamps onto every reboot row precisely so this file can read it.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.soak_csv import SoakCsvError, parse_soak_csv          # noqa: E402

H = "time,device_id,kind,detail\n"


def row(t, dev, kind, detail):
    return f"2026-08-27 {t},{dev},{kind},{detail}\n"


START = row("00:00:00", 0, "start",
            "ids=8 gap_s=0.5 counter_every=5 slow_ms=400 crossing_slow_ms=4000")


def stop(reboots, wdt):
    return row("06:00:00", 0, "stop",
               f"reason=cancelled pass=100 reads=800 fails=0 reboots={reboots} "
               f"wdt={wdt} worst_ms=100 cross=0 worst_cross_ms=0 elapsed_s=21600")


def clean_boot(t, dev):
    return row(t, dev, "reboot",
               f"boots 10 -> 11 cause=Power-on NRST pin iwdg 5 unchanged")


def wdt_boot(t, dev):
    return row(t, dev, "reboot",
               f"boots 10 -> 11 cause=IWDG NRST pin iwdg 5 -> 6")


def main() -> int:
    failures = 0

    def check(name, cond, detail=""):
        nonlocal failures
        print(("ok   " if cond else "FAIL ") + name + ("" if cond else f"  {detail}"))
        failures += not cond

    # 1. the real 03:00 shape: >= half the modules, clean rows, one window
    body = "".join(clean_boot(f"03:00:{i:02d}", 11 + i) for i in range(6))
    s = parse_soak_csv(H + START + body + stop(6, 0))
    check("scheduled reset gets the green verdict",
          s.mass_reboots == 6 and s.unexplained_reboots == 0
          and "scheduled reset" in s.headline(), s.headline())

    # 2. THE LIE THE FIRST CUT WOULD HAVE TOLD: a mass IWDG event inside one
    #    window must NOT be blessed - the rows say the watchdog counter moved
    body = "".join(wdt_boot(f"03:00:{i:02d}", 11 + i) for i in range(6))
    s = parse_soak_csv(H + START + body + stop(6, 6))
    check("mass IWDG cluster is NOT a scheduled reset",
          s.mass_reboots == 0 and s.unexplained_reboots == 6
          and "scheduled reset" not in s.headline(), s.headline())

    # 3. mixed: 5 clean + 1 watchdog in the window -> cluster counts the 5,
    #    the watchdog one stays unexplained
    body = "".join(clean_boot(f"03:00:{i:02d}", 11 + i) for i in range(5))
    body += wdt_boot("03:00:05", 17)
    s = parse_soak_csv(H + START + body + stop(6, 1))
    check("mixed cluster: clean 5 blessed, watchdog 1 unexplained",
          s.mass_reboots == 5 and s.unexplained_reboots == 1, s.headline())

    # 4. mass event AFTER the last heartbeat of an unfinished run: the footer
    #    lags the rows - unexplained must clamp at zero, never print negative
    hb = row("02:00:00", 0, "heartbeat",
             "pass=50 reads=400 fails=0 reboots=0 wdt=0 worst_ms=100 cross=0 "
             "worst_cross_ms=0 elapsed_s=7200")
    body = "".join(clean_boot(f"03:00:{i:02d}", 11 + i) for i in range(6))
    s = parse_soak_csv(H + START + hb + body)
    check("footer lag: reboots trusts the rows, unexplained clamps at 0",
          s.reboots == 6 and s.unexplained_reboots == 0 and not s.finished,
          f"reboots={s.reboots} unexplained={s.unexplained_reboots}")

    # 5. below half the cabinet is never "mass", however clean
    body = "".join(clean_boot(f"03:00:{i:02d}", 11 + i) for i in range(3))
    s = parse_soak_csv(H + START + body + stop(3, 0))
    check("3 of 8 is not a mass event", s.mass_reboots == 0)

    # 6. two clean reboots 130 s apart never share a window
    body = clean_boot("03:00:00", 11) + clean_boot("03:02:10", 12)
    s = parse_soak_csv(H + START + body + stop(2, 0))
    check("spread reboots stay unexplained", s.mass_reboots == 0
          and s.unexplained_reboots == 2)

    # 8. THREE nights: every scheduled reset counts (it used to keep only the
    #    largest cluster, so nights 2 and 3 came out "unexplained")
    def night(day, dev0=11):
        return "".join(f"2026-08-{day} 03:00:{i:02d},{dev0 + i},reboot,boots 10 -> 11 "
                       f"cause=Power-on NRST pin iwdg 5 unchanged\n" for i in range(6))
    s = parse_soak_csv(H + START + night(28) + night(29) + night(30) + stop(18, 0))
    check("three nights = three scheduled resets, nothing unexplained",
          len(s.mass_clusters) == 3 and s.mass_reboots == 18
          and s.unexplained_reboots == 0 and not s.problems
          and "3 scheduled resets" in s.headline(), s.headline())

    # 9. slow reads and hub-crossing reads are counted apart, and a reading
    #    inside a reset window is tagged; the slowest outside it is kept too
    body = night(27)
    body += row("03:00:40", 12, "slow", "6063 ms")                      # in reset
    body += row("05:00:00", 12, "slow", "1500 ms (counter reg 0)")      # normal
    body += row("05:10:00", 12, "slow", "4500 ms (hub crossing)")       # crossing
    body += row("05:20:00", 13, "slow", "2000 ms")
    s = parse_soak_csv(H + START + body + stop(6, 0))
    t12 = next(t for t in s.trouble if t.device_id == 12)
    check("crossing counted apart from slow",
          t12.slow == 2 and t12.cross == 1 and t12.worst_cross_ms == 4500,
          f"slow={t12.slow} cross={t12.cross}")
    check("worst reading inside the reset window is tagged",
          t12.worst_slow_ms == 6063 and t12.worst_slow_in_reset
          and t12.normal_worst_ms == 1500, str(t12))
    over, normal = s.slowest("slow"), s.slowest("slow", outside_reset=True)
    check("slowest overall vs slowest outside resets",
          over[:2] == (12, 6063) and over[3] and normal[:2] == (13, 2000),
          f"{over} {normal}")

    # 10. a watchdog the counter comparison missed is still seen: reg 8 names
    #     IWDG on a row whose counter was unreadable
    body = row("04:00:00", 14, "reboot", "boots 10 -> 11 cause=IWDG iwdg unread")
    s = parse_soak_csv(H + START + body + stop(1, 0))
    check("IWDG cause with unread counter is a watchdog reset",
          s.watchdog_resets == 1 and s.iwdg_unread_rows == 1 and s.problems,
          f"wdt={s.watchdog_resets} unread={s.iwdg_unread_rows}")

    # 7. garbage in, error out (not a traceback)
    try:
        parse_soak_csv("hello\nworld")
        check("garbage raises SoakCsvError", False)
    except SoakCsvError:
        check("garbage raises SoakCsvError", True)

    print(f"\n{'ALL PASS' if not failures else f'{failures} FAILURES'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
