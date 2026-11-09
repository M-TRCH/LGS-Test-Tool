# Planned: site-simulation soak mode

Proposed by Teerachot, 2026-09-04. Built since as the fleet soak's
`mode=pharmacy` (v2.0). The first full run, and the fixes it calls for, are in
the last section.

## Why this is the right next test

The commissioning record's §5.4 names the largest remaining gap in a year of
testing: every hour of evidence we hold comes from a soak that polls modules in
ID order at a steady cadence. A hospital server does nothing of the sort. It
lights a slot, waits for a person, reads a latch, and its timing is irregular
by nature.

This mode closes that gap directly. It is not another endurance run — the
86-hour baseline already settled endurance. It exercises **the traffic shape we
have never tested**, and it is the only test that would have caught the
`_hubLastCh` defect (§5.1) as a user-visible symptom rather than as a
statistical curiosity in a CSV.

## What it does

Fire real picks at a realistic rate: **~2,000 slot activations per day**, so
roughly one every 43 seconds, spread so that **every module receives the same
average count per day**.

### Equal counts, not uniform random

Do not draw slots uniformly at random. Over a day that gives Poisson spread —
some modules get 20 activations, others 50 — and any per-module comparison
afterwards is confounded by exposure rather than by health.

Use a **shuffled deck**: take all slot IDs, shuffle, deal the whole deck one
slot at a time, then reshuffle and deal again. The order looks random, the
counts come out exactly equal every full round, and a partial round at the end
is off by at most one. With 64 slots at 2,000/day that is 31.25 rounds a day,
~31 activations per module.

## Open design questions

These need answering before anyone writes code.

1. **Light only, or light + latch?** "Fire the lights for real" is the stated
   scope, but a real pick also fires the latch, and latch endurance currently
   has no number at all (§5.5). Firing latches makes this a far more valuable
   test and puts real mechanical wear on the cabinet — which is a decision, not
   a default.
2. **How does an activation end?** Real pick: light on → person opens the
   drawer → latch reads → light off. With nobody there, either the module's own
   max-on-time expires, or the simulation clears it after a set dwell. The
   second is closer to real traffic and gives a settable "how long a nurse
   takes" parameter.
3. **Does background polling continue underneath?** A real server polls status
   as well as dispensing. Running both is the honest simulation; running picks
   alone isolates them. Probably: both, with the poll rate settable.
4. **What counts as a failure here?** The existing soak's `slow` / `no_reply` /
   `reboot` rows still apply, but this mode adds new ones worth logging: a
   commanded light that did not light, a latch that did not fire, an activation
   whose round trip exceeded the server contract's 4 s.

## Prior art — this has been done once already, on the R4.x fleet

Found 2026-09-04 on the `Above-R4.0` branch of `M-TRCH/LGS-Standard-Module`:
`tools/test_random_single_coil.py`, with four result logs from February 2026.
It is the same idea, already run against the live 33-cabinet site, and it
should be read before anything is written here.

What it does: pick a random cabinet (10 of them by IP — nine type 80, one
type 68), a random unit ID, and a random coil in 1001-1008; write the coil
True, wait 3 s, read register 40, write it False. It pauses itself daily from
01:45 to 02:15 and opens a fresh log at 02:15.

The 2026-02-22 log is the one to look at: **11,770 cycles, 23,540 writes,
23,540 reads, and every single one SUCCESS** — no failures at all in about
23 hours across ten real cabinets. That is a meaningful reliability data
point for the R4.x fleet, and a rate of roughly one activation every 7 s,
about six times more aggressive than the ~2,000/day proposed here.

Three things it does NOT do, which is exactly where this design adds value:

1. **It never fires a latch.** It drives 1001-1008 (light only), not
   1021-1028 (light + latch). Latch endurance stays unmeasured — see the
   commissioning record's §5.5.
2. **It is uniform random**, so per-module exposure is Poisson-spread. This
   is precisely the confound the shuffled deck above removes, and it is why
   Teerachot's "equal average per module" requirement is a real improvement
   rather than a detail.
3. It logs its own event schema, not the soak CSV format, so none of the
   existing analysis (`soak_csv.py`, the site report) can read it.

Worth stealing outright: the daily maintenance pause, and the cabinet list
shape (many cabinets by IP rather than one).

## What to reuse

Almost all of it. The existing soak already owns the run loop, the CSV format,
the counter passes that catch reboots, the reboot/watchdog classification, the
link supervision, and `soak_csv.py` which turns the file back into a verdict.
This mode is a different **selection strategy and action** inside that loop,
not a new program.

Keep the same CSV schema so `soak_csv.py` and the site report keep working, and
add a `kind` for activations rather than inventing a second file format.

## Constraints inherited from the commissioning record

- **Pass gap stays clear of 0.4–0.9 s** (§4.2). At one activation every ~43 s
  the natural gaps are far longer, but any burst mode must respect the band.
- **One master on the bus** (§6.5). This mode is a master; nothing else may
  poll while it runs, except the console-only `gw_bus_watch.py`.
- **The 03:00 scheduled reset will interrupt it.** Expect 64 clean `Power-on`
  reboots a night in the CSV, exactly as the endurance soak sees them.

## First full run: 2026-11-06 21:06 to 11-08 22:13 (49.1 h, 12 cabinets)

File: `soak-20261106-210620-all.csv`. Pharmacy mode, 2,000 picks/day, dwell 20 s,
client timeout 6 s, stopped by hand. Chest-Std-11 ran gateway 1.15.0-dev (service
AP, AP off), the other eleven 1.14.0.

**Eleven cabinets were healthy, and the tool still called every one "not clean".**
Together they made 16.6 M reads and 45,023 picks with 0 failed reads and 0 failed
writes. Everything that was not zero came from the scheduled 03:00 shelf reset,
on both nights:

- `reboots` 80 / 112 / 160 = every module twice, all `cause=Power-on` between
  03:00 and 03:09.
- One `slow` read of ~6.06 s per cabinet per night at 03:00:06, the read in
  flight when the shelf lost power. That is also every cabinet's `worst_ms`.
- The gateway counters went up by one final timeout and (mostly) one failed
  repair per night, read at the first counter sample after 03:00. Std-10 also
  had one `bad_other` per night (noise at power-up).

`clean` in `soak_fleet.py` refuses any `gw_timeouts` or `gw_heal_failed`, so the
expected reset alone fails the cabinet. Also seen, not a fault: three reads of
1.2-1.5 s at 04:03 on 11-07 (Std-02 id 88, Std-07 ids 24 and 104), about an hour
after the modules booted; and Ref-12's gateway repaired 55 first-try misses
(1.1/h, under the 30/h warn line).

**Chest-Std-09 has a real fault: row 4 (ids 41-44) never answered.** It was
`missing at the baseline` on the first pass and silent to the end, and still
silent when read again after the run, while row 3 (same hub channel 2) and row 5 answer in
~130 ms. So the break is in row 4 itself or the cable from row 3 to row 4; it
followed the power-cable tidy-up. The other 36 modules had no failure. The
408 failed writes are the picks the simulator placed on row 4.

The run also showed how a dead row distorts the tool: the gateway sends no
reply for a silent module (`EXC 0`), pymodbus reports `No response`, and the
soak calls that `link_lost`, reconnects and comes back 36-37 s later with
"4 reads lost", on every pass (2,658 times). Std-09 therefore made 2,658 passes
against ~25,000 on the other 40-slot cabinets: its healthy modules were tested
about ten times less, and the pick rate fell to 77 % (`sim_behind`).

### Fixes (1 and 2 done 2026-11-09 on branch soak-reset-and-silent-module, not released)

1. **Done: the scheduled shelf reset no longer fails a cabinet.** Treat a whole-cabinet
   burst of `Power-on` reboots (or the gateway's own `sched_reset` event / its
   `sched.reset_*` times) as the reset, and attribute to it the gateway counter
   increments and the slow read in that window. Report them on their own line
   ("03:00 reset x2, expected") instead of in the verdict. A timeout or failed
   repair outside that window still fails the cabinet.
2. **Done: a silent module is not a lost link.** After `No response`, check whether the
   gateway still answers (unit 255 `PING`, or the next module) before declaring
   `link_lost` and reconnecting; keep `no_reply` for the module. Consider taking
   ids that are missing at the baseline out of the pick deck, still listed as
   silent, so one dead row does not slow the whole cabinet's run.
3. **Chest-Std-09 row 4:** check its power and RS485 harness, then re-run.

How they were done. (1) `soak.run_soak` opens a shelf-reset window when 3 module
reboots are noticed within 60 s and the gateway itself did not restart; the window
reaches back 10 minutes (counters are compared every few minutes, so the stall is
noticed late) and closes 5 minutes after the last reboot. Gateway timeouts, failed
and successful repairs and `bad_other` inside it, and ordinary reads slower than
`slow_ms` inside it, go to `reset_*` fields and a "scheduled shelf reset" block in
the verdict, not to "clean". A bad CRC and anything outside the window still fail
the cabinet. The CSV gets a `shelf_reset` row and `resets=`, `reset_to=`,
`reset_hf=`, `reset_worst_ms=` on the heartbeat. A fault in the ten minutes before a
reset is forgiven with it (the counters cannot say when inside the interval it
happened). (2) `soak_fleet._ClientOps._dead`: pymodbus 3.x raises
`ModbusIOException("No response")` for a silent slave, and the old code treated
every exception as a dead socket. Now silence is a failed read; after 8 in a row the
gateway is asked (unit 255 PING) and only an unanswered PING is a lost link. Other
exceptions are still a dead socket at once. Selftests: `tools/soak_fleet_selftest.py`
(4 new cases, verified to fail on the old code).

Not covered: `soak_csv.py` still judges a CSV written by an older run the old way.

### Follow-up, 2026-11-09 (same branch)

- **The shelf-reset window is now exact when the gateway can name its resets.** `soak_fleet._ClientOps.sched_resets()`
  reads `sched_reset` from the gateway's event log (LOG SINCE) and its own clock (INFO `time.now`), so the window is
  `[event - 5 s, event + 180 s]` in the gateway's time whatever this PC's clock says. The counters are then compared
  every 60 s (INFO and LOG never touch RS485; they used to be every 10 min) and a sample interval that overlaps the
  window is booked with the reset, so at most 60 s of ordinary time before the event is forgiven with it, not 10
  minutes. The reboot-burst guess stays as the fallback for firmware before 1.14.0 or a gateway with no clock; it is
  not used when the gateway names its resets (a reboot burst with no event forgives nothing).
- **Export "All"** on the Events page: the range picker has a fourth shortcut, from the oldest day any gateway has a
  file for to today; the page count and the CSV use the same range.
