"""The LGS control table, shipped inside the tool.

Commissioning happens on site, often with no network, so the register and coil
reference has to travel inside the exe rather than sit behind a GitHub link.

The file under app/docs is a **copy**. Its source of truth is
LGS-Standard-Module/doc/LGS-Control-Table.md (taken from 75fb659, 2026-07-17);
refresh it with tools/sync_reference.py when the module firmware changes what
a register means.
"""
from __future__ import annotations

import sys
from pathlib import Path

DOC_NAME = "LGS-Control-Table.md"
SOURCE_REPO = "https://github.com/M-TRCH/LGS-Standard-Module/blob/main/doc/LGS-Control-Table.md"


def _doc_path() -> Path:
    if getattr(sys, "frozen", False):
        # PyInstaller unpacks --add-data payloads under _MEIPASS
        return Path(getattr(sys, "_MEIPASS")) / "app" / "docs" / DOC_NAME
    return Path(__file__).resolve().parent / "docs" / DOC_NAME


def control_table() -> str:
    """The document as markdown, or an explanatory line if it is missing."""
    try:
        return _doc_path().read_text(encoding="utf-8")
    except OSError as exc:
        return (f"*The reference could not be loaded ({exc.__class__.__name__}).*\n\n"
                f"It is available online at <{SOURCE_REPO}>.")


def filtered(markdown: str, query: str) -> str:
    """Keep only the lines matching `query`, with their section still above them.

    A register lookup is the reason this document is here at all, so the filter
    keeps the heading a row belongs to (otherwise a bare row of numbers says
    nothing) and the table header (otherwise the columns are unlabelled).
    """
    needle = query.strip().lower()
    if not needle:
        return markdown

    out: list[str] = []
    heading = ""
    table_head: list[str] = []
    heading_used = False

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading, heading_used = line, False
            table_head = []
            continue
        if stripped.startswith("|"):
            # A markdown table's first two lines are its header and separator.
            if len(table_head) < 2:
                table_head.append(line)
                continue
            if needle not in line.lower():
                continue
            if not heading_used:
                if heading:
                    out += ["", heading, ""]
                out += table_head
                heading_used = True
            out.append(line)
        elif needle in stripped.lower() and stripped:
            if heading and not heading_used:
                out += ["", heading, ""]
                heading_used = True
            out.append(line)

    return "\n".join(out).strip() or f"*No entry matches “{query}”.*"
