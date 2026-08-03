"""Refresh the bundled control table from LGS-Standard-Module.

The tool ships its own copy so it works offline, which means the copy can go
stale the moment the module firmware changes what a register does. Run this
after any such change:

    .venv/Scripts/python tools/sync_reference.py

Prints what moved, so a sync shows up in review as a real diff rather than a
silent overwrite.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DEST = HERE / "app" / "docs" / "LGS-Control-Table.md"
SOURCE = HERE.parent / "LGS-Standard-Module" / "doc" / "LGS-Control-Table.md"


def provenance(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%h %ad", "--date=short", "--", path.name],
            cwd=path.parent, capture_output=True, text=True, timeout=15)
        return out.stdout.strip() or "(no git history)"
    except (OSError, subprocess.SubprocessError):
        return "(git unavailable)"


def main() -> int:
    if not SOURCE.exists():
        print(f"source not found: {SOURCE}")
        print("Clone LGS-Standard-Module next to this repo, or copy the file by hand.")
        return 2

    new = SOURCE.read_text(encoding="utf-8")
    old = DEST.read_text(encoding="utf-8") if DEST.exists() else ""

    if new == old:
        print(f"already up to date ({len(new.splitlines())} lines)")
        print(f"source is at {provenance(SOURCE)}")
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(new, encoding="utf-8")
    print(f"updated {DEST.relative_to(HERE)}")
    print(f"  {len(old.splitlines())} -> {len(new.splitlines())} lines")
    print(f"  source is at {provenance(SOURCE)}")
    print("Update the commit noted in app/reference.py, then rebuild the exe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
