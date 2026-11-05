Same install as before: drop the exe beside the old one and run `install-autorun.cmd` (or start it by hand with `--port 8090`). Your `data` folder is read as it is; nothing in it needs converting.

## The new pages are now the main interface
Opening the tool lands on the new pages (`/v2`). The old page is still there at `/classic` (the "Classic UI" button in advanced mode). Pages: Cabinets, Sites, Gateway, Module, Soak, Events, Firmware, Labels, Commission. Thai or English, phone layout, fonts bundled so it works offline. Ten colour themes (Settings, the gear), default "Ocean".

## Security
- **Web password.** The page was open to anyone on the network. Gateway > "Web password" sets one (stored only as a hash); from a console use `--set-password` / `--clear-password`. Until you set one, nothing changes. Once set, changing or removing it asks for the current one.

## Firmware
- **Gateway v1.14.0 is bundled**: event log, NTP, console and firmware update over the network (port 502, unit 255), a module depot, and a module update that the gateway runs by itself in the background. While that update runs the cabinet's three status lamps stay lit. Bench: on Chest-Std-11 the background update did 40 of 40 modules in 20.8 minutes. Settings are kept across the update (stored-settings layout unchanged).
- **Module depot**: store a module image on a gateway, update from any PC later without the file.
- **Two ways to update modules**: the gateway does it in the background (progress per cabinet, no need to keep the tool open), or the tool drives it over OTA with its result and log shown in the same card.

## Soak and events
- Soak reads the gateway's own repair counters and calls a cabinet "not clean" on a final timeout, a failed repair or a bad CRC; it ends on time; the summary can be saved as an image.
- An event collector (Settings) keeps each gateway's event log on this PC, with filters, charts and CSV export.

## Behaviour changes
- The tool no longer sets an unset gateway clock by itself (that arms the gateway's scheduled reset). It asks first.
- The full module test section was removed from the Module page.

## Not tested
Docker, a phone (only a 375 px emulation), modules older than v3.5.2, 80-module cabinets, a power cut during a depot upload, ABORT of a background module update on a real cabinet, a background update while a server polls the cabinet continuously, the new themes on every page.
