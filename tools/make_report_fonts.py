"""Build the TTFs the site report uses from the Tool's own web fonts.

    .venv/Scripts/python tools/make_report_fonts.py        (needs `pip install brotli`, once, to read woff2)

The Tool's pages use IBM Plex Sans Thai, shipped as woff2 split into a Thai and a Latin subset
(app/v2/static/fonts). fpdf2 wants a TTF with both in ONE file, so this merges each weight's two subsets and writes
IBMPlexSansThai-Regular.ttf and -Bold.ttf next to the woff2 files (which are already bundled into the exe as data, so the
report finds them in the same place on every install). The font is SIL OFL 1.1 (fonts/OFL.txt); the merged files are
the same glyphs, not a modified design. Re-run only if the woff2 files change; the TTFs are committed.
"""
from pathlib import Path

from fontTools.merge import Merger
from fontTools.ttLib import TTFont

FONTS = Path(__file__).resolve().parent.parent / "app" / "v2" / "static" / "fonts"
WEIGHTS = {400: "Regular", 700: "Bold"}


def build(weight: int, name: str) -> Path:
    parts = []
    for subset in ("latin", "thai"):                  # Latin first: its .notdef, metrics and name table win the merge
        font = TTFont(FONTS / f"ibm-plex-sans-thai-{subset}-{weight}.woff2")
        font.flavor = None
        tmp = FONTS / f"_{subset}-{weight}.ttf"
        font.save(tmp)
        parts.append(tmp)
    merged = Merger().merge([str(p) for p in parts])
    out = FONTS / f"IBMPlexSansThai-{name}.ttf"
    merged.save(out)
    for p in parts:
        p.unlink()
    return out


if __name__ == "__main__":
    for w, n in WEIGHTS.items():
        out = build(w, n)
        print(out.name, out.stat().st_size, "bytes")
