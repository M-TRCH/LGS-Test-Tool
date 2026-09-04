# LGS type 64 "Queen-Sirikit" — commissioning record

Closed 2026-09-04. This is the durable account of one cabinet: what it is,
what was wrong with it, what fixed each thing, and what is still open. It
exists so that the next person to touch this cabinet — or to build the next
one — does not have to re-derive any of it from CSVs and chat logs.

Everything below was measured on the bench cabinet, not inferred.

---

## 1. What this cabinet is

| | |
|---|---|
| Product | LGS type 64 — 64 slots, **not** a rectangle |
| Slot IDs | rows 1-3 and 8-10 full width (×8), rows 4-7 half width (×4) |
| Modules | 64 × LGS Standard Module, **device type 20 (NARCOTIC)** — ring + OLED + big button |
| Module firmware | **v3.4.0** on all 64 |
| Gateway | Arduino Opta, **v1.12.2**, `192.168.0.202:502`, MAC `A8:61:0A:50:D3:2B` |
| Bus | Modbus RTU 9600 8N1 over RS485, behind an **8-channel active hub** |
| Hub | 8 × UN3088E transceivers, no termination inside the hub |

A "type" number is the **slot count, not the shape**. The shape cannot be
derived from the count — this cabinet was once misdescribed as a 7×8 block
under the name "LGS 56", which selected sixteen slots that do not exist on it
and missed rows 8-10 entirely. The real LGS type 56 is a different product.

---

## 2. Final configuration — treat as the standard for this cabinet type

### Gateway (`GET` output, verified 2026-09-04)

```
rs485.baud=9600          rs485.t1_ms=300         rs485.t2_ms=20
rs485.predelay_us=10000  rs485.postdelay_us=1000
bus.hub_map=1,2,3,4,4,5,5,6,7,8
bus.hub_retry=2          bus.hub_gap_ms=0
bus.hub_settle_ms=2200   bus.hub_budget_ms=2600
net.dhcp=0  net.ip=192.168.0.202  net.port=502  net.link_timeout_ms=1500
panel.enabled=1  panel.cabinet=64  panel.shape=0
sched.reset_enabled=1  sched.reset_hhmm=300  sched.reset_slots=1
sys.wdt_ms=8000
```

`bus.hub_map` is the row-to-channel map: ten rows onto eight channels, so
**rows 4+5 share channel 4 and rows 6+7 share channel 5**. Row 0 (broadcast)
maps to channel 0 = "not behind the hub", which is why broadcasts never cross
channels.

Only reset slot 1 is armed (`sched.reset_slots=1`), so the nightly reset fires
at 03:00 and the other three configured times are inert.

### RS485 termination — settled 2026-08-24, do not re-litigate

**One 120R at each channel's tail module + bias at the head module + NOTHING
at the hub.** A-B reads ~120 Ω per channel.

This bus cannot afford dual termination. With 120R also at the hub ports
(60 Ω total, correct by the book) modules 96 and 108 went fully garbled and 54
marginal, and it drifted worse over half an hour. Removing the hub-end
resistors restored 96 and 108 from 0/20 to 20/20 instantly. The module-side
3.3 V drivers cannot develop reliable swing into 60 Ω over this cable run; the
failure signature is start-bit-slip corruption in the reply direction only.

---

## 3. Test evidence

| Run | Duration | Reads | fails | Watchdog resets | Verdict |
|---|---|---|---|---|---|
| 2026-08-18/19 | 15 h | 197,440 | 0 | 308 reboots | the sag, pre-rewire |
| 2026-08-20/21 | 14 h | 186,380 | 0 | 441 IWDG | worst night on record |
| 2026-08-26/27 | 22.6 h | 143,049 | 1 | **0** | first clean night, post-rewire |
| 2026-08-28/31 | 63 h | ~555,000 | — | 0 | clean, but polluted by the pass-gap artefact |
| **2026-08-31 → 09-04** | **86 h** | **933,696** | **1** | **14** | **the accepted baseline** |

### The accepted baseline in full

- 10,421 passes, 933,696 reads, `fails=1`, `link_lost=0`
- Gateway counters over the same window: `rs485_ok` +980,367,
  **`rs485_timeout` +9** (1 in 109,000), `hub.skip=0`
- 81 slow rows in the whole run; **64 of them inside one 7-minute window**
- 270 reboots, **every one accounted for**: 4 × 64 = 256 scheduled 03:00 resets
  (Sep 1/2/3/4, cause `Power-on`, IWDG counter unchanged on all 64) + the 14
  described in §5.2
- **Boots-counter chains across all 64 modules have zero gaps** — the soak
  witnessed every reset that happened; nothing hid between samples
- Median pass 24 s

---

## 4. Faults found and closed

### 4.1 The IWDG storm — CLOSED by rewiring

Up to 441 watchdog resets a night, always whole-channel with a nested survivor
set. Ruled out in turn: firmware (a full audit found no path that can reach the
4 s watchdog), mains wiring (the gateway shares the feed and never rebooted
through 441 events), and the hub's channel-switch transient (a 19-minute
crossing storm produced zero events).

Fixed by **rewiring ten rows onto eight channels** (`1,2,3,4,4,5,5,6,7,8`).
Three independent runs since have produced one event in 86 hours.

### 4.2 "Modules 12 and 13 are chronically slow" — CLOSED, it was the tool

For weeks every soak reported modules 12 and 13 slow on ~80% of passes,
~3,578 ms each. Three theories were built on this and all were wrong: the
boards were always healthy.

**Root cause: the soak's own `pass_gap_s = 0.5` default.** The hub falls back
to its home channel (CH1) after about a second of silence. A pause of
**0.4–0.9 s** lands mid-transition, while the gateway still believes the hub is
where it left it, so the first read of the next pass is sent into a hub that is
somewhere else — 300 ms timeout, then a retry that works. 0–0.3 s and ≥ 1.0 s
are both clean.

Proven by two interleaved A/B series (four cycles each, perfect separation): in
reverse scan order modules 12/13 answer in 78 ms, 100% of the time.

Fixed in `a141c05` — default `pass_gap_s` 0.5 → **2.0**, which is also
**faster** (24 s per pass against 30.9 s). Slow rows went from 10,566 in 63
hours to 81 in 86 hours; modules 12/13 from 5,009/5,001 rows to **1 each**.

The methodological lesson, worth more than the fix: four sequential
confirmations of a fault are also consistent with the fault going quiet. Only
an interleaved A/B, with the failing config re-run as a control, separates them.

### 4.3 The CH8 IWDG question — CLOSED

Twenty-nine resets during a fleet OTA on 2026-08-27 looked like bad hardware on
channel 8. It was **broken broadcast pacing in the tool**: frames were paced by
wire time alone, and gateway forwarding jitter merged them. Fixed with a 100 ms
idle hold after every broadcast (`BROADCAST_IDLE_S`, `af7a90c`).

Re-tested at CH8 with corrected pacing: all 8 modules received **470/470
chunks**, and both the boots and IWDG counters were unchanged on every one.

### 4.4 Latches — CLOSED, 64/64 functional

Audited 2026-08-28. Module 104's board was replaced (new board, fw 30400 — its
boots/IWDG counters restart near zero, which matters when reading CH8
baselines) and verified full-cycle: a real 344 ms pulse, reg 41 1→0, reg 40
restarted, fires incremented. Slot 51 was simply an unlatched drawer.

---

## 5. Still open

### 5.1 The gateway trusts `_hubLastCh` across idle — KNOWN DEFECT, not fixed

`src/modbus_rtu.cpp` remembers the last hub channel and skips the settle when
the next request is for the same one. It has **no idle timeout**, so after the
hub has drifted back to its home channel the gateway still believes otherwise.
This is the mechanism behind §4.2.

**Mitigated entirely by the server contract in §6** (timeout ≥ 4 s and retry).
Fix it in firmware only if that contract cannot be guaranteed — and a proper
fix needs a scope on the hub's A/B lines during the 0.3–1.0 s idle window,
which has not been captured.

### 5.2 One unexplained 7-minute event — 2026-08-31 22:05:48 → 22:12:48

Cabinet-wide degradation: 64 of the run's 81 slow rows, its only `no_reply`
(id 64), passes stretched from 24 s to 63/66/78 s, two hub crossings at 5.8 s
and 6.6 s against a normal 2.2 s. It ended with **14 modules IWDG-resetting** —
all 8 of CH3 (31-38) plus 6 of 8 on CH5 (61, 62, 63, 72, 73, 74; **not** 64,
**not** 71) — after which the cabinet ran normally for 84 hours.

**The watchdog did its job**: the cabinet recovered itself inside one counter
pass with nobody touching it.

The gateway's event log excludes the usual suspects. Between `tcp_accept` at
2026-08-31T15:47 (the soak's session, which then stayed open for four days) and
the 03:00 `sched_reset` rows there is **nothing at all** — no
`tcp_accept`/`tcp_refused` (so **not a second master**), no `panel_sweep` (no
button was pressed), no `link_up`/`link_down`, no `bus_quiet`, no `out_fixed`.
The disturbance was real, lived downstream of the gateway on the RS485 side,
and was invisible to it.

If it recurs, run `tools/gw_bus_watch.py` beside the soak so
`cnt.rs485_timeout` and `hub.wait_ms` are timestamped from the gateway's side
too. That is the one piece of evidence still missing.

### 5.3 Lifetime IWDG by channel — historical, not from this run

```
CH1 (11-18)    23-54     CH5 (61-74)    199-377
CH2 (21-28)    26-52     CH6 (81-88)    165-337
CH3 (31-38)    27-50     CH7 (91-98)    151-338
CH4 (41-44)    32-51     CH8 (101-108)  321-342   (104 = 1, replaced board)
    (51-54)   106-116
```

A clean gradient down the cabinet — but boots counters put rows 31-38 at ~208
against 61-74's ~560, so those boards carry roughly 2.7× the powered history.
Normalised, CH5–CH8 still run 2–4× the IWDG rate of CH1–CH4. Worth knowing
before reading too much into any single channel's numbers.

### 5.4 Never tested: the real server's traffic

Every hour of evidence above comes from a soak that polls 64 modules in ID
order at a steady cadence. The hospital server will do something else
entirely — dispense commands, latch fires, irregular timing, bursts. **This has
never been run against this cabinet.** It is the largest remaining gap and the
reason §6 exists.

### 5.5 Latch endurance has no number

The audit proved 64/64 *work*, not how many cycles they last. The modules carry
a `fires` counter (reg 40/41) — read it to find out what history this cabinet
already has.

---

## 6. The server integration contract

Give this to whoever writes the polling software. Without it the cabinet will
look broken on day one while being entirely healthy.

1. **Read timeout ≥ 4 seconds, AND retry on timeout.** A hub crossing costs
   2.2 s of settle before the module is even asked. A 1 s timeout without retry
   will report failures on a perfect bus.
2. **Do not pause 0.4–0.9 s before touching channel 1** (modules 11-18). See
   §4.2 and §5.1. Either stay under 0.3 s or go over 1.0 s.
3. **Register 60 now accepts 0-999**, up from two digits.
4. **Confirm a pick from the latch, not the button.** See the pick PDF.
5. **One master on the RS485 bus at a time.** The gateway accepts two TCP
   clients but there is one physical bus. A second poller corrupts both
   sessions' data and produces `transaction_id` mismatches — demonstrated
   accidentally on 2026-08-28. A console-only reader (`tools/gw_bus_watch.py`)
   is safe as the second client because it never touches RS485.

---

## 7. Reproducing any of this

The soak, from the tool's UI — **visit the Gateway tab and press Read first**,
so the hub map syncs from the gateway, which is the authority on it. Then Soak
tab → all 64 → Start. The defaults are correct; the pass gap is 2.0 s.

The gateway's own account of the bus, safe to run beside a soak because it
never touches RS485:

```bash
python tools/gw_bus_watch.py 192.168.0.202 --every 30
```

To turn a finished soak CSV back into a verdict: Gateway tab → Attach soak
CSV → the site report PDF carries the summary.

The gateway's console (unit 255, FC 0x41) answers `INFO`, `GET` and `LOG <n>`
over the same TCP connection. `LOG` is the QSPI event log and it survives
resets — it is the first thing to read after any surprise.
