"""Release notes shown in the About dialog.

Newest first. Add an entry when the version in version.py is bumped for a
release — one entry per release, written for the person using the tool.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Release:
    version: str
    date: str            # YYYY-MM-DD
    notes: tuple


RELEASES: tuple = (
    Release("1.9.0", "2026-09-25", (
        "The fleet soak is now fit to be left alone over a long weekend. "
        "Give it a duration in hours and it stops by itself, clearing every "
        "cabinet on the way out, with the time remaining counting down in "
        "the status line; 0 keeps the old run-until-stopped behaviour. When "
        "a run ends — by the clock, the Stop button, or every cabinet "
        "failing — it writes a verdict: one row per cabinet with passes, "
        "reads, failures, reboots, watchdogs, worst read, silent ids, and "
        "how many cabinets were completely clean. The verdict is shown on "
        "the card AND written to exports/fleet-<start>.txt, because closing "
        "the app is the normal end of a weekend run.",
        "The verdict includes a number nothing measured before: reply "
        "frames the Modbus library silently threw away. A reply carrying "
        "the wrong unit id is discarded and retried, so a two-hour run in "
        "September reported zero failures while the bus lost sync twelve "
        "times. These are now counted per cabinet. The client timeout also "
        "rose from 3.5 s to 6 s — the discarded frames were replies "
        "arriving after the tool had given up.",
        "A fleet run now holds the sleep block. It never did: only the "
        "single-cabinet soak was checked, so a laptop that suspends at "
        "midnight ended a weekend fleet run at midnight with nothing in "
        "the CSVs saying why.",
        "Check the gateways: one button fills every roster row with the "
        "gateway's firmware, how many of its two TCP slots are taken, and "
        "any other client connected — before the run starts, not after it "
        "is refused. A gateway whose client vanished without closing (an "
        "IP change, a killed process) holds its slot until reboot, and now "
        "that is visible.",
        "The roster can be exported and imported as CSV — typed once, "
        "carried between machines, reviewable in a spreadsheet. Import "
        "tolerates what Excel produces (BOM, CRLF, quoted commas, Thai "
        "code page) and names every line it cannot use; the old roster is "
        "only replaced once the whole file parses.",
        "The fleet card now says which Bus-soak settings it inherits, and "
        "warns in orange when the pass gap sits in the 0.4–0.9 s band that "
        "makes healthy modules look chronically slow. The remove button is "
        "a red bin with a tooltip instead of a grey cross nobody found.",
        "Labels: the QR now carries the cabinet type spelled out, the "
        "channel map, row widths, the gateway firmware WITH the date it "
        "was read, and — optionally, via a ~22 s survey — what firmware "
        "the modules run (one version if they agree, lowest–highest if "
        "not). The symbol shrank to a 0.8 pt cell, print-proven at full "
        "density, and its version is pinned so the drawn size can never "
        "disagree with the declared box. Frames: the Editor's own rounded "
        "frame or a plain bold border.",
        "Bundled gateway firmware v1.12.4 (panel.cabinet 0 = no preset, "
        "follow the shape) — deployed across the fleet 2026-09-25; v1.12.3 "
        "kept for rollback.",
    )),
    Release("1.8.0", "2026-09-24", (
        "New Labels tab: a Brother P-touch sticker for the front of a "
        "cabinet, saved as a .lbx and printed from P-touch Editor. Press "
        "Read and the short name, the address, the MAC and the row/channel "
        "map come off the gateway live, so a sticker can never describe a "
        "cabinet that no longer exists -- the worst it can be is old, and "
        "reprinting costs nothing. Only two fields are typed and neither is "
        "kept: the ward name, which is printed for people to read, and the "
        "serial, which belongs to the warehouse's database and would only "
        "drift if a second copy lived here.",
        "Three layouts -- minimal, standard and a row map for a cabinet "
        "whose row widths nobody can guess -- and three frames. The QR "
        "carries the whole shape of the cabinet, channels and row widths "
        "included, in 95 bytes of the 134 a 24 mm tape holds; the panel "
        "showing exactly what it encodes is there because a wrong channel "
        "map is invisible until someone is at a cabinet with a scanner.",
        "Soak: several cabinets at once. The roster is remembered, because a "
        "weekend run is set up once and started many times, and cabinets "
        "that share an IP no longer trip the two-masters guard, which had "
        "been refusing every cabinet in a fleet run.",
        "The pharmacy simulation now shows what it is doing and admits when "
        "it cannot keep up. Its pick schedule was drifting and quietly "
        "losing 14% of the requested rate; dwell is tied to the pick rate, "
        "and the writes are timed.",
        "The refrigerated cabinet is a type of its own rather than a "
        "40-slot chest with the wrong row widths.",
        "Bundled gateway firmware is v1.12.3.",
    )),
    Release("1.7.3", "2026-09-09", (
        "A panel action the firmware does not know about no longer takes the "
        "whole card down with it.",
    )),
    Release("1.7.2", "2026-09-08", (
        "The commissioning sweep asks the board what it is before deciding "
        "what to assert. On a type-10 mask board running module v3.5.0, coil "
        "1001 correctly stays lit when 1003 is enabled -- window n is person "
        "n, and one slot can serve several people at once -- so the old "
        "assertion would have reported every module in an 80-slot cabinet as "
        "a hardware fault while it worked exactly as designed.",
        "The global fan-out check now restores the global register too. It "
        "left the test value behind, and because those are CHANGE watches "
        "the next run's identical write was not a change, so nothing fanned "
        "out: the check passed once per board and failed forever after.",
        "Bundled module firmware is v3.5.0.",
    )),
    Release("1.7.1", "2026-08-31", (
        "The Soak tab's pause between passes now defaults to 2 seconds "
        "instead of 0.5. That half-second was not a harmless default: on a "
        "cabinet wired through the RS485 hub it lands exactly where the hub "
        "is falling back to its home channel, and the first two modules read "
        "after the pause then lose their first request and answer in about "
        "3.6 seconds instead of 80 milliseconds. Every soak run was reporting "
        "those two slots as chronically slow, and the hardware was fine all "
        "along. Anything from 0 to 0.3 s, or 1 s upward, is clear of it; "
        "2 s also makes each pass finish sooner, because re-entering the "
        "channel no longer costs a settle.",
        "The field tip on that setting now carries the measured numbers, so "
        "the band to avoid travels with the tool.",
    )),
    Release("1.7.0", "2026-08-28", (
        "Firmware updates over the bus stopped losing chunks: broadcasts now "
        "leave a 100 ms quiet gap for the gateway's forwarding jitter, and a "
        "whole 64-module cabinet updates in about 19 minutes with no repair "
        "rounds. The Firmware tab walks the RS485 hub one channel at a time "
        "by itself, using the wiring map read from the gateway, and a module "
        "that drops out of a session is named with its own error code while "
        "everyone who finished is still updated.",
        "The site report can now carry a soak run: attach the soak's CSV on "
        "the Gateway page and the PDF gains a Soak section with the verdict "
        "worked out — a whole-cabinet reboot at the scheduled reset time is "
        "labelled as such (only when the watchdog counters held still), and "
        "a run that did not finish says so.",
        "Server install: install-autorun.ps1 registers the tool as a "
        "scheduled task that starts at boot with nobody logged in, hardens "
        "the folder's permissions, and the tool itself now refuses to run "
        "twice and takes --port for machines where 8080 is taken.",
        "Bundled firmware refreshed: module v3.4.0 (display shows 0-999) and "
        "gateway v1.12.2 (clock survives a restart), each with the previous "
        "release kept for rollback.",
    )),
    Release("1.6.1", "2026-08-18", (
        "The link no longer dies quietly: if the gateway connection drops "
        "mid-session the tool reconnects by itself and says so, instead of "
        "reporting every module as absent until someone notices.",
    )),
    Release("1.6.0", "2026-08-14", (
        "The Gateway tab works over the network: read and change the "
        "gateway's settings, pull its event log, and update its firmware "
        "through the same TCP connection as everything else — no USB cable "
        "needed at the cabinet.",
        "A Soak tab: leave the whole cabinet polling for hours or days, "
        "with every anomaly streamed to a CSV, heartbeats that prove the "
        "run was alive, and the PC kept awake while it matters.",
        "A built-in NTP server, so the gateway's clock can sync from the "
        "site PC without internet access.",
        "The site report gained the gateway's recent events and a restyle.",
    )),
    Release("1.5.0", "2026-08-11", (
        "The cabinet type is picked once, in the header, and remembered — "
        "LGS 80 / 64 / 56 / 40, SMT type 12, or a Custom shape you describe "
        "yourself: how many rows and how many slots on each. Every "
        "whole-cabinet action follows that one choice, and the Gateway page "
        "warns when the gateway disagrees, with a one-click fix.",
        "Site report PDF from the Gateway page: the gateway's identity and "
        "settings, the cabinet's shape, and one row per module — chip UID, "
        "type, firmware, hardware, boot count, health — read from the "
        "modules themselves. A copy is kept in data/exports.",
        "Gateway settings export and import as a file. A firmware upgrade "
        "that changes the settings layout wipes the gateway's store — the "
        "path is now export, flash, import, Save. Import stages values for "
        "the normal review and skips keys the firmware does not have.",
        "Gateway pages for everything firmware v1.10.0 configures: the five "
        "panel buttons, all four relay outputs, up to four scheduled resets "
        "a day behind one switch, the watchdog period, a sweep shape for "
        "cabinets that are not a 40/64/80, which module preset the buttons "
        "fire, a temporary test brightness, and one pace per sweep kind — "
        "the unlock pace spaces the solenoid firings out. The bundled "
        "gateway image is v1.10.0.",
        "Every section is led by its switch, and a setting whose action or "
        "state is not selected anywhere is disabled until it is — a value "
        "that can be set but can never fire reads as a broken cabinet.",
        "The transaction log opens collapsed (it keeps recording), and the "
        "\"...\" menu gains Quit: settings saved, server down, terminal "
        "window closed.",
        "Firmware survey and whole-cabinet monitoring of every module's "
        "version, with each version group clickable as update targets.",
        "Every write to the gateway now starts from a clean slate, so "
        "values someone staged over a console session and forgot can never "
        "ride along with a save. Long writes are split to fit the console's "
        "line limit.",
        "Module Test moved behind the Advanced switch beside the other "
        "maintenance pages.",
    )),
    Release("1.4.0", "2026-08-06", (
        "Pick walkthrough on the Installation Check page: each selected slot "
        "lights up in turn, the person at the cabinet picks and presses the "
        "slot's front button, the light goes out and the next slot lights — "
        "the real dispensing flow as a rehearsal, proving lights, buttons "
        "and wiring in one walk. Needs module firmware v3.2.0, which counts "
        "button presses so a press can never fall between polls.",
        "New module tab gains a Continuous mode: pick the whole lot's IDs on "
        "a grid like the Installation Check page, then just keep swapping "
        "boards — each blank board is detected, flashed and given the next "
        "ID in the queue. Proven on an 80-board lot at under half a minute a "
        "board. Continuous mode never overwrites an ID a board already has.",
        "Factory-fresh chips no longer need a power cycle after their first "
        "flash. A blank STM32 locks itself onto ST's built-in loader until "
        "power is pulled — boards looked dead on the bench until unplugged. "
        "The flasher now releases that latch itself.",
        "The Monitor tab shows the module's chip serial — the same number "
        "commission_log.csv records — so a board on the bus can be matched "
        "to its commissioning record without opening the cabinet, plus the "
        "module's input current in mA and its confirm-press counter. All "
        "need module firmware v3.2.0; older modules show a dash.",
        "A Basic/Advanced switch in the header: everyday pages only by "
        "default, with Firmware, New module, Gateway and Danger appearing "
        "in advanced mode. The choice is remembered.",
    )),
    Release("1.3.1", "2026-08-04", (
        "Module firmware versions now read as v3.1.0 rather than as a date "
        "code. The firmware used to report the build date in that field, which "
        "meant a newer build could show a smaller number — 4 August came out "
        "below 17 July. Modules still running an older build are labelled as a "
        "legacy date instead of being given a version number that would be "
        "wrong.",
    )),
    Release("1.3.0", "2026-08-04", (
        "New module tab: flash a blank module over ST-Link and give it its "
        "Modbus ID in the same step. The ID goes into the firmware image "
        "before it is written, so the module answers at it the first time it "
        "starts — no second tool, and the module does not even need to be on "
        "the RS485 bus yet. Needs module firmware v3.1.0 or newer.",
        "A module that already has an ID is left alone unless you tick "
        "\"overwrite\", so a flash cannot renumber a cabinet in service. "
        "Re-flashing the same file never reverts an ID you changed afterwards, "
        "and a factory reset still returns the module to unset.",
        "Every module flashed is appended to commission_log.csv with the "
        "chip's own serial number, the ID assigned, the lot and the time.",
        "Fixed: Factory reset in the Danger tab never actually reset anything. "
        "It sent the commands in the wrong order, so the module rejected them "
        "— and worse, left the wipe-all flag set, which meant a later reset "
        "command could erase a module nobody meant to touch.",
    )),
    Release("1.2.0", "2026-08-03", (
        "Gateway tab: read and change the Opta gateway's own settings over its "
        "USB port — bus speed and timings, USB framing, network address and "
        "port — with the link status, its address and the traffic counters in "
        "view. Save, discard, load factory values or reboot from the same page. "
        "Needs gateway firmware v1.1.0 or newer.",
        "The LGS control table now travels inside the tool: open it from the "
        "… menu, search for a register, coil or name, and read it with no "
        "network connection.",
        "Every setting is written in plain language instead of its protocol "
        "name, with the explanation on hover so the page stays readable.",
        "Interface reworked around text: icons removed, the system font in "
        "place of Roboto, and language, theme and about collected into a single "
        "… menu at the right of the header.",
        "Fixed: Factory defaults appeared to do nothing. The gateway staged the "
        "factory values and then discarded them as the session closed, so the "
        "fields never changed. They are now filled in for review before saving.",
    )),
    Release("1.1.0", "2026-07-30", (
        "Installation Check: run light / display / unlock across many modules at "
        "once and read the result as a map of the cabinet. One click picks a whole "
        "cabinet type — LGS 80 / 40 / 56 or SMT.",
        "Module Test (previously 'Auto Test'): options rewritten in plain language; "
        "the latch options stay locked until the unlock test is enabled.",
        "Slave ID grid picker in the header — click 11-108, 246 (SET_ID) or 247 "
        "(factory) instead of typing.",
        "Set Slave ID in the Danger tab: writes, persists and verifies the new ID.",
        "Six selectable themes, remembered between sessions.",
        "Portable one-file Windows build (build_exe.ps1).",
    )),
    Release("1.0.0", "2026-07-29", (
        "First working version: Control, Monitor, Auto Test and Danger tabs over "
        "Modbus RTU (COM port) or Modbus TCP (LGS gateway).",
        "Every transaction runs through a single worker so the RS485 bus and the "
        "gateway's single TCP slot are never contended.",
        "Transaction log with raw TX/RX hex and CSV export.",
    )),
)
