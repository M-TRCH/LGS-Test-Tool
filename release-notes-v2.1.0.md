**Gateway v1.15.0 bundled: service Wi-Fi at the cabinet, module update at set times.**

Same install as before: drop the exe beside the old one and run `install-autorun.cmd` (or start it by hand with `--port 8090`). Your `data` folder is read as it is; nothing in it needs converting.

## Firmware
- **Gateway v1.15.0 is bundled** and is the default on the Firmware page. Settings are kept across the update (stored-settings layout unchanged). v1.14.0 stays in the bundle for rollback. Module firmware v3.5.5 is unchanged.

## Service Wi-Fi at the cabinet (gateway 1.15.0, Opta WiFi only)
- **Gateway > AP Service**: the Wi-Fi name, password and how long it stays on with nobody using it ("เปิดค้างไว้", also used by a front-panel button set to action 7), and a switch that turns it on or off and goes green when the gateway confirms.
- A phone on that Wi-Fi opens `http://192.168.27.1:502/`: the gateway's status and network settings, its newest events, and every module with its firmware; light or switch off a module, and give a new board (id 246/247) its id.
- **Config export/import** now carries the AP Service name, password and minutes.
- **Labels**: a "Standard + AP Service" sticker with a second QR code that joins the Wi-Fi (INFO / AP SERVICE under the codes). Opened right in P-touch Editor.

## Module update at set times
- Firmware > "Update at set times": the gateway's background update works only between two times of day, keeps clear of the scheduled shelf reset, and goes on every day until it is done. Start it in the daytime and close the tool. Needs gateway 1.15.0; an older gateway says so.

## Soak, events, report
- Soak: the 03:00 shelf reset is no longer counted against a cabinet (the gateway names its own resets in its event log), and a silent module no longer makes the tool reconnect on every pass.
- Events: an "All" range for the page and the CSV export; "show per page" and the CSV button stay on one line.
- Site report (PDF): English, every fact in a clearer order, the Tool's font, and an optional soak result chosen after the modules are read.
- Module scan: each found module shows its firmware version; a slot that missed one answer is asked again before it is called silent.
- One drop-down and one popup style across the tool.

## Known limits (planned for the next version: docs/PLANNED-after-2.1.0.md)
- Importing one cabinet's config onto another copies its Wi-Fi name: after an import onto a different cabinet, set that cabinet's own name in AP Service (or `default`).
- The front-panel "toggle the AP" action (7) is not offered in the Gateway page's button list; set it over the console (`$LGS SET panel.btnN=7`, `SAVE`).
- Gateway-side limits of 1.15.0 are in its release notes (a phone's dead connection can hold a TCP slot; treat the AP password as a key to the cabinet).

## Not tested
The service page from a phone after its last changes (tested through a LAN proxy), the front-panel AP button, printing the AP sticker (opened in P-touch Editor only), Docker.

## Files
- `LGS-Test-Tool-v2.1.0.exe`: the tool (sha256 `a3e2a648127b273a40513e3a21d271f2567c890c33a89db0c589301ed88fc224`)
- `install-autorun.cmd` / `install-autorun.ps1`: server autorun installer
