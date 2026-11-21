# Plan: soak tests before the site install (Central Chest Institute, 12 cabinets)

Draft 2026-11-10 for Teerachot to decide. Frozen builds under test: gateway **1.15.0**
(`gateway_opta_v1.15.0.bin`, SHA-256 `bfa0e64a…0570`), module firmware **3.5.5**, Test Tool **2.1.0**.
Nothing is changed in code during the plan: a fix means a new version and a restart of the affected condition.

สรุป: แผนแบ่ง 12 ตู้เป็นกลุ่ม "ทนทาน" 9 ตู้ (เงื่อนไขเดียว ไม่แตะ) กับกลุ่ม "ทดสอบกวน" 3 ตู้ (ตัดสาย ดับไฟ เปิด AP
อัปเดตโมดูลระหว่างใช้งาน) ใช้เวลาราว 2 สัปดาห์ มีเกณฑ์ผ่าน/หยุดชัดเจน และมี 4 เรื่องที่ต้องให้คุณตัดสินใจก่อนเริ่ม (ท้ายเอกสาร)

## 1. What we already know, and what we do not

| Evidence | Result |
|---|---|
| 49 h fleet soak, 2026-11-06 to 11-08 (11 cabinets on 1.14.0, Std-11 on a 1.15.0-dev build, AP off) | 16.6 M reads, 0 failed; the 03:00 reset was wrongly called "not clean" (fixed in Tool 2.1.0) |
| 6 h soak 2026-11-10 02:00-08:00, **all 12 on 1.15.0** | ~2.07 M reads, 0 failed, 0 watchdog/gateway reboots, only the 03:00 reset; Std-06 (no radio) clean |
| Std-11 bench: AP cycles, LAN Modbus during AP, windowed module update, depot, radio file | passed (see the gateway repo's design notes) |

**Never run, and the site depends on or can hit it:**
1. More than one night with 1.15.0 on all 12 (only one 03:00 reset seen on this build).
2. The hospital server's real pattern for days: pick rate ~2,000/day, plus **two clients at once** (server + a technician's Tool).
3. A module update by the gateway **while a server polls and picks continuously** (the stated "not tested" item of 1.14/1.15).
4. The service AP **on overnight**, with a phone that comes and goes (the open gateway risk: a dead phone connection can hold a TCP slot).
5. Recovery from the things a hospital does to equipment: LAN cable pulled, switch rebooted, gateway or shelf power cut, clock lost after a power cut.
6. A silent/dead module in the cabinet mid-run (Std-09 showed the tool-side cost; the gateway-side behaviour should be confirmed on 1.15.0).
7. Latch endurance (no number exists; see section 5, decision 1).

## 2. Cabinet groups

Fault injection on a cabinet spoils its endurance numbers, so the 12 are split and each group keeps one condition.

- **Endurance group, 9 cabinets, never touched:** Nar-01 (56), Ref-12 (40), Std-02..05 (80 each), Std-06 (80, **no radio**: the
  site may have such units), Std-07, Std-08 (40 each). Pure C1.
- **Disturbance group, 3 cabinets (40 modules each):** Std-09, Std-10, Std-11. Std-11 is the AP/OTA cabinet (it has all the history);
  Std-09 carries the cable-pull/power tests; Std-10 is the reserve and the control for the OTA run. Keep Std-09's row-4 harness
  as it is now (fixed and clean on 2026-11-09).

## 3. Conditions

Each starts only after the previous gate passes. "Pass" always also means: no gateway reboot except an intended one, `wdt=0`,
INFO `heap.used` flat (within 5 % of the start after any AP use), event log intact (`LOG SINCE` continues, no `gap`), and
`net.client` back to the expected number when a client leaves.

### C1. Realistic endurance (endurance group, 72 h, 3 nights)
- Pharmacy mode at the **site rate**: ~2,000 picks/day, dwell 20 s, client timeout 6 s, gateway counters sampled every 60 s,
  the soak as the one "server" client, the event collector as the second.
- Why: the first run that matches what the server will do, over three 03:00 resets, on the frozen build.
- **Pass:** 0 failed reads/writes outside the 03:00 windows; worst ordinary read < 400 ms; module reboots = modules x nights and
  nothing else; first-try misses < 30/h per cabinet (the existing warn line); the Tool's verdict "clean" for every cabinet.
- **Stop and investigate:** any watchdog reset, any gateway reboot, any failed read outside a window, a module reboot outside 03:00.

### C2. Stress burst (endurance group, 12 h, after C1 passes)
- Pharmacy mode at the maximum the bus allows (the 11-10 run asked 40,000/day and got ~30,000). Not a prediction of the
  site, a margin: if it is clean at 15x the site rate there is room.
- **Pass:** same as C1 except that `sim_behind` is expected and not a failure.

### C3. Service AP on overnight (Std-11 and Std-10 on the disturbance group, 12 h, with C1 traffic running)
- `AP ON min=480` (a technician forgot it), a phone joins at 22:00, opens the page, taps Modules, then is switched off without
  closing the tab; at 01:00 a second phone does the same and is carried out of range; morning: AP off.
- Why: lwIP has four sockets; this is the combination (AP + server + Tool + phone) that can exhaust them.
- **Pass:** LAN reads 0 failed throughout; NTP resumes after the AP stops; `net.client` returns to the expected number within
  its idle time after each phone leaves **or the leak is measured**: if a dead phone connection holds a slot until the gateway
  reboots (the known limit), record how long and decide whether the site procedure ("close the tab, AP off") is enough or the
  fix (docs of the gateway repo, PLANNED-after-1.15.0 item 1) must ship before install.
- Front panel: a button set to action 7 switches the AP on and off, using the stored minutes (needs a person at the cabinet).

### C4. Module update during traffic (Std-10 updates, Std-11 is its control, 2 nights)
- Put two modules per cabinet (or one row) on 3.5.4, deposit the 3.5.5 image, `OTA START ... at=0100 until=0400` while C1
  traffic runs; the 03:00 reset falls inside the window on purpose.
- **Pass:** every module ends on 3.5.5; the run says `scheduled` between windows and `reset_hold` around 03:00; **no failed pick or
  read outside the 03:00 window attributable to the update** (compare Std-10 against the control); a gateway reboot ends the run
  as `interrupted` (never a half-flashed module).
- Needs a decision (below): deliberately downgrading a few bench modules.

### C5. LAN faults (Std-09, one afternoon, with traffic)
Each step: do it, wait, restore, then check the soak recovers by itself and the gateway shows no leaked slot.
1. Pull the gateway's LAN cable for 30 s, then 5 min (server connected). Watch for a stale connection holding a slot after the
   cable returns (the half-open TCP case: the same slot-leak mechanism as C3).
2. Reboot the switch/router the cabinet hangs off.
3. Tool and server both reconnect at once after the outage (two clients racing for two slots).
- **Pass:** traffic resumes within 60 s of the link coming back, `link_down` / `link_up` events in the log, 0 stuck slots.

### C6. Power faults (Std-09, one afternoon, **the 03:00 reset and the clock**)
1. Cut the **gateway** power for 10 s mid-run: it reboots, modules keep their power. Expect `power-on`, clock unset.
   With `net.ntp` reachable the clock must come back by itself; check `time.set=1`, and that the **next 03:00 reset still fires**
   (leave it overnight). Without NTP the reset must **not** fire (by design) and the Tool must ask before setting the clock.
2. Cut the **shelf** power (panel `reset` or a real cut): every module reboots, `bus_quiet` appears in the event log with its time.
3. Cut everything and power up in the wrong order (modules before gateway, gateway before modules).
- **Pass:** the cabinet answers again without anybody touching it; the soak records the break and resumes; no module stuck on a
  wrong id; settings (schema 11) unchanged after each cycle.

### C7. Dead module (Std-09, 1 h)
- Unplug one module's connector (not the row), keep traffic, restore after an hour.
- **Pass:** the other modules keep their 130 ms reads; no `link_lost` loop in the Tool (the 2.1.0 fix); the gateway's re-sync
  keeps the rest of the channel answering; the restored module is picked up again.

### C8. Final soak on the final build (all 12, 7 days)
- Only if everything above passes with no code change, or after the fixes of any failed condition are retested. All 12 cabinets,
  site rate, AP off, one server + one Tool/collector, including at least one weekend and one windowed update on a cabinet at the
  start. This is the number that goes in the commissioning record.
- **Pass:** C1's criteria over 7 nights.

## 4. Order and timing (about two weeks; a gate failure stops the line)

| Days | What | Gate |
|---|---|---|
| 1-3 | C1 on 9 cabinets; **C3 and C5 on the disturbance group** run alongside (they do not touch the endurance group) | C1 clean |
| 4 | C2 (12 h) on the endurance group; C4 starts on Std-10 | C2 clean |
| 5-6 | C4 nights; C6 on Std-09 (afternoon + one night to see the 03:00 reset after a power loss); C7 | C4/C6/C7 pass |
| 7-14 | C8 final soak on all 12 | clean 7 nights |

Daytime tests that need a person at the bench: C3 (phones, front-panel button), C5, C6, C7. The rest runs unattended, and
**must be started from the user's own Tool, not from the Claude app** (a child of the app dies when the app updates itself, as
on 2026-11-04).

## 5. Decisions needed before day 1

1. **Latches in the soak?** Lights-only leaves latch endurance unmeasured (commissioning record §5.5); lights + latch wears the
   cabinets' solenoids. Recommendation: lights + latch on **one** disturbance cabinet only (Std-11), lights-only elsewhere.
2. **Downgrade a few modules to 3.5.4 for C4?** Needed to have something to update. Recommendation: 2 modules per cabinet on
   Std-10 and Std-11, restored by the test itself.
3. **Who is at the bench for the daytime tests**, and is a phone and the cabinet's panel available? C3, C5, C6 and C7 cannot be
   done remotely.
4. **Duration of C8:** 7 days as above, or 72 h if the date is close. Recommendation: do not shorten C1 (3 nights) or C6.

## 6. Results so far (as of 2026-11-21)

The plan was run in a different order from section 4 (the cabinets were rearranged and re-cabled for shipping on
2026-11-13), but the conditions map as below. Builds unchanged throughout: gateway 1.15.0, modules 3.5.5, Tool 2.1.0.

| Condition | Run | Result |
|---|---|---|
| C1 (all 12, not 9) | 48 h, pharmacy 2,000/day, from 2026-11-13 17:23 | clean (Teerachot's reading of the Tool summary) |
| C2 | 12 h, pharmacy 40,000/day, ended 2026-11-15 17:53 | clean |
| C5 LAN | Std-09, 2026-11-16: cable out 30 s, 11 s, 31 s (run 1); 5 min and 15 min (run 2) | **pass**: each time the gateway closed the dead connection itself 1 s before `link_down` and the soak was back 1 s after `link_up`; no `tcp_refused`, no stuck slot, the collector's slot untouched. The slot leak does not happen on a cable pull |
| C6 power | Std-09, 2026-11-16: whole cabinet ~5 min (run 1); hub channels 1+2 only, whole cabinet, hub 1+2 + Opta (run 2) | **pass**: back by itself every time; with the Opta cut every module rebooted once (the shelf relay follows the Opta, so modules can never power up before it); the clock came back from the RTC at boot (`clock_set aux=3`, ~6 min off) and NTP agreed; the **03:00 reset fired that night** on both cabinets |
| C7 dead module | Std-10, 2026-11-16 17:17-18:25: hub channel 8 pulled (ids 101-104, 4 modules, not 1) | **pass with two gateway findings**: only 101-104 failed, the other 36 had 0 fails, no `link_lost` loop, all back after reinsertion. But the gateway logged ~50 false `bus_quiet` (4 dead ids in a row = 6 timeouts in a row), and the cabinet's pass rate fell ~10x (252 -> 27 passes per 30 min). Both go to the gateway's `docs/PLANNED-after-1.15.0.md` item 4 |
| C1 again (all 12) | **72 h, pharmacy 2,000/day, 2026-11-18 18:27 - 11-21 18:27** | **11 of 12 clean; Ref-12 explained**: reboots = modules x 3 nights on every cabinet (Std-02..06 80 x 3 = 240, Nar-01 56 x 3 = 168, the 40-slot ones 120), 0 failed reads, 0 watchdog, 0 gateway reboots, gateway counters 0. Ref-12's 154 extra reboots and 4 timeouts were four presses of its front-panel reset button on 11-19 16:12-16:17 (gateway log `panel_sweep a=4 p=5`), which the Tool books as faults: Tool `PLANNED-after-2.1.0.md` item 3 |

Seen in the 72 h run and not explained by a cabinet: one slow ordinary read (1.1-1.5 s) on several cabinets **in the same
second**, 2026-11-21 16:29:47 (Std-02, Std-06, Std-11) and 16:40:39 (Nar-01, Std-10), with every gateway's counters at 0.
Different gateways at the same instant means the soak PC or the LAN, as with the 12 s read on 2026-11-16 11:45. Over the
400 ms line but not a cabinet fault; worth watching on the hospital's own network.

Not run yet: **C3** (AP overnight with phones), **C4** (module update during traffic), **C8** (7-day final), C5.3 (switch
reboot), C6 with the gateway alone (modules on) and with no NTP, and **a client that vanishes silently while the link stays
up** (a server VM stopped hard or a firewall dropping an idle connection): the case where the gateway's lack of an idle
timeout could hold a slot. Site facts still missing: how the hospital system connects (one persistent connection or one
per request, connections per cabinet), the firewall/NAT idle timeout between server and cabinets, the NTP server's IP.

## 7. Records

Per condition: start/end time, cabinets, the exported CSVs (`soak-...-all.zip`), the Tool's summary image, INFO before and after
(fw, build, heap.used, counters, `net.client`), and the event-log range. Write the verdict per condition into the checkpoint
record, with the image hashes of the firmware under test. Gateway `docs/PLANNED-after-1.15.0.md` and the Tool's
`docs/PLANNED-after-2.1.0.md` hold what is known and deferred.
