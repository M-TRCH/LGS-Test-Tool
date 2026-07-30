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
    Release("1.1.0", "2026-07-30", (
        "Installation Check: run light / display / unlock across many modules at "
        "once and read the result as a map of the cabinet.",
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
