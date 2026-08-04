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
    Release("1.3.0", "2026-08-04", (
        "New module tab: flash a blank module over ST-Link and give it its "
        "Modbus ID in the same step. The ID goes into the firmware image "
        "before it is written, so the module answers at it the first time it "
        "starts — no second tool, and the module does not even need to be on "
        "the RS485 bus yet. Needs module firmware v4086 or newer.",
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
