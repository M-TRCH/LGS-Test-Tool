# Planned: site-simulation soak mode

Proposed by Teerachot, 2026-09-04. **Not built yet** — this is the design
record so the idea survives until someone picks it up.

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
