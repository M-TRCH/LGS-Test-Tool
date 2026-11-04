# 1.9.6 release notes (DRAFT)

Not released. When it ships: bump `app/version.py`, move these notes into
`app/changelog.py` as one `Release("1.9.6", ...)` entry, build the exe
(`build_exe.ps1` already bundles `app/v2/static`), then publish.

Everything below is committed on branch `v1.9.6-wip`. Verification status is
stated honestly per item.

## For the person using the tool

- **Web password.** The page was open to anyone on the network, Danger and
  firmware updates included. Gateway tab > "Web password" sets one (stored only
  as a hash in `data/auth.json`); until you set it, nothing changes. From a
  console: `LGS-Test-Tool.exe --set-password` / `--clear-password` (a running
  server picks the change up by itself). Five wrong tries lock that address for a
  minute. Docker: `LGS_TT_PASSWORD` seeds it once.
- **The tool no longer sets an unset gateway clock by itself.** It used to do it
  silently on every read, and setting the clock is what arms the gateway's
  scheduled reset (03:00 cuts the shelf's power), so looking at a cabinet changed
  when it would lose power. It now asks, and a "no" is remembered while the page
  stays open.
- **Soak: the gateway's own repair counters.** A run that reports zero failed
  reads can still have had the gateway repair its bus all night. The fleet soak
  now reads `rtu.*` at the start, every 10 minutes and at the end, keeps the
  difference, and the verdict calls a cabinet **not clean** on a final timeout, a
  failed repair or a bad CRC, and warns above 30 repaired misses per hour.
  Needs gateway firmware 1.13 or later; older ones show "not available".
- **Soak ends on time.** Two overnight runs kept polling 31 and 49 minutes past
  their deadline. Each soak thread now checks the deadline itself as well as the
  fleet clock. *The cause of those overruns is not established*; a `deadline` row
  in a soak CSV that says it fired more than a second late would be the first
  evidence of what it was.
- **Soak: "another master" guard** no longer refuses a run started through a
  router or VPN, where the tool's own connection looks like a stranger's.
- **Event collector** (off by default; Gateway tab > "Gateway event collector"):
  pulls each fleet gateway's event log into `data/events/<name>/events-DATE.jsonl`
  every 5 minutes, kept 90 days, with a resumable cursor and an explicit marker
  when events were lost or the board was replaced. Needs gateway firmware 1.14.0.
  Its own visits are logged by the gateway (3 records per visit), which is why the
  default is 5 minutes and not 1.
- A link back to the new pages (bottom right) on the classic page.

## New: the v2 pages at `/v2` (preview; classic UI unchanged at `/`)

Same server, port, login and data folder. Plain HTML/JS, fonts bundled (works
offline), Thai/English, phone layout. Pages: Cabinets (health check), Gateway
(read, staged edit with a diff, all-or-nothing save, clock, RESYNC/EXC, reboot,
factory defaults with the cabinet name typed, config JSON export/import,
cabinet-shape check), Module (monitor, presets, quick commands, display number,
with the classic safety rules enforced on the server), Soak (start, start at a
time, live table, stop, verdict, history, CSV download), Firmware (module OTA
across cabinets; one gateway's network update, name typed to confirm), Labels
(.lbx), Sites (name <-> address list saved on the server, CSV import/export,
duplicate-address warning), Events.

Since then v2 also has: Commission (ST-Link flash of a blank module, one or a
whole lot), the module test sweep, the ID scan, installation check and pick
walkthrough, set slave id and software reset, the gateway site-report PDF, an
NTP server on the PC, the web password in Settings, a themed login page that
lands on `/v2`, and basic/advanced modes (basic = Cabinets, Module, Events).

Not in v2 yet: USB/COM cabinets.

### Module page (reviewed with the user, passed 2026-11-03)

Top to bottom: module details, quick commands, full module test (advanced),
installation check, scan, module management (advanced, last).

- **Module details** fold into one box, closed by default; its summary line has
  id, type, firmware and a health chip. Decoded values only; statistics always
  read (32-bit counters from module fw 3.3.0, legacy 16-bit before).
- **Quick commands** in groups Light / Latch / Display / Other. Light commands
  ask for the colour in a popup; Unlock asks Safe or Force; Write number asks
  for the number (0-9999, a popup refuses anything else). Only what the read
  module carries is shown (the STANDARD mask board has no display and no latch);
  "show all" brings the rest back. Preset 8 is drawn white, as on the module.
- **Scan**: "scan the cabinet layout" (the cabinet's slots, eight to a row) or
  "scan every id" (1-247, ten to a row; amber = outside the layout, red = a
  layout slot that is silent). Cancel turns into Clear once a result is shown.
- **Installation check** as four numbered steps: check type, modules (the slot
  grid is the picker and the result map), settings, run. General check runs a
  sequence light -> latch -> identify, each step skippable, with a delay between
  steps. Pick walkthrough: colour, number, latch, light goes out on button /
  button then drawer shut / **drawer shut** (for cabinets without buttons such as
  Nar-01), slots at a time, wait per batch, batching by hub channel / id order /
  **random**. Results newest first in a five-row box.
- **Module management**: Change id asks for the new id in a popup (1-245 or 247,
  refused if another module answers there) and then a yes/no; Software reset
  asks for the id to be typed (grey example in the field).

### Events page (reviewed with the user, passed 2026-11-04)

- **Dashboard** over the chosen filters: six counters, lights and problems charts (per hour for a window of two days or
  less, otherwise per day, hover for the number) and one row per gateway. `GET /api/v2/events/summary`.
- **Filters in the manner of a parametric part search**: tick lists with counts for gateway, event type, client and
  module (several ticks in a group = any of them, groups combine, each count leaves out its own group), a date range and
  a time-of-day window (applies on every chosen day, wraps past midnight). Wide screens: one row of drop-downs; phones:
  stacked, collapsible groups. Selected values show as chips with "clear all" beside them. The dashboard follows every
  filter except the event type.
- **Calendar popup** for the date range with Today / 7 / 30 day shortcuts; the choice is held until the popup is
  closed and then applied once. Only days the collector still keeps can be picked.
- **List** paged 10 / 20 / 50 / 100 at a time (the choice is remembered), **Export CSV** of every row matching the
  filters (UTF-8 with BOM, cells starting `= + - @` defused).
- **Collector settings moved to Settings** (on/off and days kept: 30 / 90 / 180 / 365); the events page keeps a status
  chip and a notice when the collector is off. Fixed: switching the collector off and on while a poll was running left
  it dead with the setting on.

## Verification

- `tools/soak_fleet_selftest.py` 27/27 and `tools/v2_selftest.py` 12/12.
- Live: a 30-minute soak on Chest-Std-11 through v2 (clean, gateway counters
  read); gateway 1.14.0-rc1 flashed on Std-11 with identical settings afterwards;
  gateway page read/edit round trip, module monitor and coil writes, label
  preview and download, all on Std-11.
- Gateway network update from the v2 Firmware page: Chest-Std-11 re-flashed with
  1.14.0-rc1 (47 s, uploaded .bin, name typed to confirm), settings identical
  before and after. The reboot also power-cycles the cabinet's modules.
- Simulated only: module OTA from the v2 page (run against a local fake: it ends
  "incomplete, did not enter OTA" as designed). The classic engine it drives is
  unchanged and proven on the bench, but the v2 page has not updated a real module.
- **Event collector, 2-hour run on Chest-Std-11 (2026-11-03).** A simulated
  Modbus TCP client lit and cleared coil 1001 on modules 11-14 (1 s on, 2 s off,
  reconnecting every 10 minutes): 4,458 writes, all acknowledged; the gateway
  logged 4,458 `coil` records; the collector kept all 4,458, no duplicates, no
  `coil_dropped`, gap flag 0, every connect/close with its client address. At
  ~0.6 writes/s this does not reach the firmware's 10/s coil-log limit.
- Live on Std-11 module 11: installation check lit and cleared it, the colour
  popup sent the right preset, set slave id 11 -> 99 -> 11 and software reset
  (boot counter 49 -> 50); site report PDF 56/56 and 40/40 modules.
- Pick walkthrough "drawer shut" tested against a fake bus only (locked -> open
  -> locked = pass), not yet on Nar-01.
- `tools/v2_selftest.py` 14/14.
- Not tested: a phone (only a 375 px emulation), the exe build, Docker, the
  events CSV download in a browser, the full module test, the NTP server
  switched on, a web password set from the v2 page.

## Review status (page by page with the user)

Passed: Commission, Labels, Sites, Cabinets, Gateway, Module, Events. To do: Soak (needs another
round), Firmware.
