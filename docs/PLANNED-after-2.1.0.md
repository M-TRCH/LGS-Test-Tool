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

## Also found (lower priority)

- The AP switch confirms the new state by calling `gwRead()` (INFO + GET + HELP) once a second for up to 14 s; `AP`
  (status) alone answers the question and costs far less of a client slot.
- The AP popup needs `AP SHOW` before it enables anything, so against a gateway without that verb even the on/off switch
  is greyed out although `AP ON/OFF` exist there.
- If an imported config's AP part is refused after the key-table part was saved, the edits stay staged and the next
  Apply re-sends settings that are already stored.
- Leftovers: `want` in `apPaintButtons()`, and `_ap_action`'s docstring still says the password is never read back.
