# Planned after 2.1.0

Found by the release review of 2026-11-09 (v2.0.0...ap-card-show). **Neither blocks 2.1.0.** The site checkpoint
(Central Chest Institute, 12 cabinets) uses the Tool as tested on the bench; both items are about the new AP Service
features, are easy to work around, and wait for the next version so the tested build stays the released one.

สรุป: สองข้อที่พบตอนตรวจก่อนปล่อย 2.1.0 ไม่บล็อก release มีวิธีเลี่ยงง่าย เก็บไว้แก้ในเวอร์ชันถัดไป

## 1. Importing one cabinet's config onto another copies its Wi-Fi name

The config export (Gateway page, ส่งออก config) writes the AP Service block from `AP SHOW`, and `AP SHOW` reports the name
the AP actually uses. A cabinet that never had a name set reports its default `LGS-<sys.name>` (e.g. `LGS-Chest-Std-11`),
the file carries that literal name, and importing the file onto another cabinet stores it there as a fixed name. Two
cabinets then broadcast the same SSID and a phone can join the wrong one.

- **Until fixed:** after importing a config onto a different cabinet, open AP Service and type that cabinet's own name
  (or `default` for `LGS-<its name>`), then Save. Or delete the `"ap"` block from the file before importing it elsewhere.
- **Fix:** on export, write `"ssid": "default"` when the name equals `LGS-<sys.name>` of the exporting gateway (the import
  then sends `AP SSID default`). Cleaner, with a gateway change: `AP SHOW` adds `ap.ssid_default=1`.
- **Test:** export from a cabinet with the default name, import onto another: the target broadcasts its own
  `LGS-<name>`. A custom name still travels as itself.

## 2. The front-panel "toggle the AP" action (7) is not offered on the Gateway page

Gateway 1.15.0 accepts `panel.btn1..5 = 7` (toggle the service Wi-Fi), but the page's button list (`GWENUM` btn in
app.js) stops at 6, so the action cannot be chosen from the Tool; a button already set to 7 shows as a bare `7`.

- **Until fixed:** set it over the gateway console: `$LGS HELLO tech`, `$LGS SET panel.btn5=7`, `$LGS SAVE`
  (a terminal such as PuTTY on the gateway's USB port at 115200, with nothing else holding that port).
- **Fix:** add `7: ["เปิด/ปิด Wi-Fi หน้างาน (AP)", "Toggle the service Wi-Fi (AP)"]` to the btn list, and the same label
  wherever panel actions are named (i18n `pnl.act.*`, the site report).
- **Test:** choose action 7 for a button, Apply, press it at the cabinet: the AP comes up with the stored minutes; press
  again: off.

## 3. A shelf reset from the front-panel button is booked as unexplained reboots

Found in the 72 h fleet soak of 2026-11-18 18:27 (12 cabinets, `soak-20261118-182701-all.zip`). Chest-Ref-12 came out
"not clean": 274 reboots where 120 were expected, `heal_failed=2 timeouts=4`, worst 6078 ms. All of the excess came from
four presses of its reset button (button 5 = action 4, `PANEL_RESET`) on 2026-11-19 at 16:12:30, 16:15:42, 16:16:21 and
16:17:05; the gateway's own log has each one as `panel_sweep a=4 p=5`, and the 40 modules rebooted 7-11 s after every
press (154 reboots). The gateway counters moved only inside 16:13-16:17. Every other hour of the run, and the other 11
cabinets, were clean.

The soak only asks the gateway for `sched_reset` (`SoakFleet.sched_resets()`, `app/soak_fleet.py`), and once the gateway
has answered, `gw["exact"]` turns off the reboot-burst guess in `app/soak.py`, so a reset nobody scheduled is a fault by
definition. It is not one: the gateway cut the shelf's power because it was told to.

- **Until fixed:** when a cabinet is "not clean" with whole-cabinet reboot bursts, read its log (`LOG SINCE`) for
  `panel_sweep a=4` at those times before calling it a fault.
- **Fix:** in `sched_resets()` also collect `ev == "panel_sweep"` with `a == "4"` (return them tagged, or as a second
  list), and in `learn_resets()` open the same `RESET_BEFORE_S`/`RESET_AFTER_S` window for each. Write a CSV row that
  says what it was (`shelf_reset gateway panel reset (button p) at <stamp>`), so the report still shows that somebody
  pressed it; count it apart from the scheduled resets (`resets=` stays the schedule), since at a site a hand reset is
  worth knowing about even though it is not a fault. `parse_soak_csv()` then books those reboots as explained, and the
  LGS Soak Monitor dashboard follows automatically because the uploader sends that summary.
- **Test:** during a fleet soak press the reset button once: one `shelf_reset ... panel reset` row, the 40 reboots
  explained, the cabinet stays clean; a reboot burst with no press is still a fault.

## Still open, not code (as of 2026-11-10)

- **Installs:** v2.1.0 is on GitHub only. The site server, the .87 notebook (it runs the fleet soak) and the copy
  started on this PC at port 8199 still run older code; replace the exe beside the old one (`install-autorun.cmd` for the
  server). The AP Service button, the AP sticker and the set-times update need gateway 1.15.0 on the cabinet.
- **Checkpoint soak:** the conditions for the long soak at the Central Chest Institute checkpoint are not defined yet;
  the site-simulation notes are in `docs/PLANNED-site-simulation-soak.md`.
- **No button yet** for installing the gateway's Wi-Fi radio file over the network (the gateway supports it; the script
  is the gateway repo's `test/wifi_fw_install.py`).
- **Print and scan** one "Standard + AP Service" sticker on the P-touch before printing it for every cabinet (it was only
  opened in P-touch Editor).

## Also found (lower priority)

- The AP switch confirms the new state by calling `gwRead()` (INFO + GET + HELP) once a second for up to 14 s; `AP`
  (status) alone answers the question and costs far less of a client slot.
- The AP popup needs `AP SHOW` before it enables anything, so against a gateway without that verb even the on/off switch
  is greyed out although `AP ON/OFF` exist there.
- If an imported config's AP part is refused after the key-table part was saved, the edits stay staged and the next
  Apply re-sends settings that are already stored.
- Leftovers: `want` in `apPaintButtons()`, and `_ap_action`'s docstring still says the password is never read back.
