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

Not in v2 yet: module test sweep, ID scan, commissioning/ST-Link, USB/COM
cabinets, the danger zone, the gateway site-report PDF.

## Verification

- `tools/soak_fleet_selftest.py` 27/27 and `tools/v2_selftest.py` 12/12.
- Live: a 30-minute soak on Chest-Std-11 through v2 (clean, gateway counters
  read); gateway 1.14.0-rc1 flashed on Std-11 with identical settings afterwards;
  gateway page read/edit round trip, module monitor and coil writes, label
  preview and download, all on Std-11.
- Simulated only: module OTA and the gateway network update from the v2 page
  (run against a local fake that cannot take firmware: they fail or stop cleanly
  as designed). The classic engines they drive are unchanged and proven on the
  bench, but the v2 pages have not flashed anything yet.
- Not tested: a phone (only a 375 px emulation), the exe build, Docker.
