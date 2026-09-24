"""Brother P-touch `.lbx` label files for LGS cabinets.

A `.lbx` is a zip of exactly two files, `label.xml` then `prop.xml`, both
UTF-8 with **no BOM and no line breaks at all** — each is a single line. The
format was reverse-engineered from a file P-touch Editor saved and proven by
a byte-for-byte round trip: a generator written from scratch reproduced that
file's payload exactly.

What the hardware taught us, none of it guessable from the file:

* **The printable area along the tape is `x = 11.4 .. (length - 11.4)`**, so
  every label loses 8 mm of length to margins whatever its size. A
  calibration label carrying its own coordinates every 10 pt established it.
  Clipping is SILENT — the printer accepts the file and the first characters
  simply are not there — so `check_fits` refuses a layout before the tape is
  spent rather than after.
* **Use `horizontalAlignment="CENTER"`.** The one file that used `LEFT` with
  boxes at x=2.8 lost the first character of every line.
* **Thai must name a face that is installed.** Arial has no Thai glyphs, and
  an unresolvable family name is substituted silently — which ruins combining
  marks and looks like a font bug. Browallia New, Leelawadee UI and Tahoma
  are all print-proven here.
* **`charLen` counts CODE POINTS**, so Thai floating vowels round-trip.
* **`<style:sheet>` wraps everything and `pt:body currentSheet` names it.**
  Leave it out and the label opens completely blank, with no error at all.

The QR is sized, not rendered — P-touch draws it from `<pt:data>`. All this
module needs is the module count, so a measured capacity table replaces a QR
library; the tool ships as an exe with a deliberately short dependency list.
"""
from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

MM = 2.8346                  # points per millimetre

# Geometry, from the real file and the calibration print.
TAPE_PT = 68.0               # 24 mm tape: the full width
ACROSS_PT = 2.0              # marginLeft/Right — unprintable across the tape
EDGE_PT = 11.4               # marginTop/Bottom — unprintable along its LENGTH
USABLE_ACROSS = TAPE_PT - 2 * ACROSS_PT          # 64.0

# How far in from the top and bottom edges the content actually starts.
#
# ACROSS_PT above is copied from a file P-touch wrote; it is what goes in the
# XML, and it is NOT the same thing as what the printer can reach. The margin
# along the tape's LENGTH was measured on a real print at 11.4 pt, three
# times the 2 pt the file declares — the across margin has never been
# measured, and on 2026-09-24 Teerachot reported the top edge clipped.
#
# MEASURED 2026-09-24. A ruler label printed the same digit at 0..8 pt from
# each edge: at the top the first whole digit was 1, at the bottom it was 0.
# So the across margin is about 1 pt at the top and nothing at the bottom —
# SMALLER than the 2 pt the file declares, and nothing like the 11.4 pt the
# length margin turned out to be.
#
# Which means the clipped top edge that prompted this was almost certainly
# another symptom of the broken document shell, like the overlapping Thai:
# content at y=3 clears a 1 pt margin easily. 2 pt keeps a point of slack
# over the measurement and gives back the 4 pt an unmeasured guess had cost.
#
# The tape is sold as 1 in but specified at 0.94 in — 67.7 pt against the
# 68 pt assumed here. A third of a point; the slack covers it.
CONTENT_INSET_PT = 2.0

# 1.2 pt: 0.423 mm, six printer dots per module.
#
# This was 1.6 pt for a long time, on the assumption that 1.6 was the only
# size P-touch offers — because 1.6 is what it wrote in the sample we copied.
# The assumption was never checked and it cost the whole design: at 1.6 pt a
# version 5 symbol overflows the tape, which capped the code at 78 bytes and
# is why the full report was abandoned, why the MAC lost its colons, and why
# a logo was impossible.
#
# A calibration label printed the SAME payload at 0.8, 1.0, 1.2, 1.4 and
# 1.6 pt. All five printed at their declared size and all five scanned, so
# every one of them is real. 1.2 pt is chosen rather than the smallest: six
# dots a module keeps a comfortable margin against the printer, and the extra
# room is spent on stronger error correction instead of a smaller sticker.
QR_CELL_PT = 1.2

# Cap the symbol well inside the 64 pt of usable tape. Without this the
# strongest-EC-that-fits rule would take EC-Q at 63.6 pt and leave 2.2 pt of
# clearance — TIGHTER than the 4.4 pt the old 1.6 pt symbol had. At 58 pt it
# settles on EC-M at 54 pt with 7 pt clear: more data than before, stronger
# error correction than before, and further from the edge than before.
QR_MAX_SIDE_PT = 58.0

# Byte-mode capacity per version and error-correction level, MEASURED against
# a real encoder rather than copied from a table. Versions 1-9 covers every
# symbol that can fit this tape at any cell size now in use.
_QR_BYTES = {
    "h": {1: 7, 2: 14, 3: 24, 4: 34, 5: 44, 6: 58, 7: 64, 8: 84, 9: 98},
    "q": {1: 11, 2: 20, 3: 32, 4: 46, 5: 60, 6: 74, 7: 86, 8: 108, 9: 130},
    "m": {1: 14, 2: 26, 3: 42, 4: 62, 5: 84, 6: 106, 7: 122, 8: 152, 9: 180},
    "l": {1: 17, 2: 32, 3: 53, 4: 78, 5: 106, 6: 134, 7: 154, 8: 192, 9: 230},
}
_ECC_PCT = {"h": "30%", "q": "25%", "m": "15%", "l": "7%"}


def _max_bytes() -> int:
    """The most any payload can be, at the current cell size and box cap."""
    best = 0
    for ecc, caps in _QR_BYTES.items():
        for version, n in caps.items():
            side = (17 + 4 * version + 4) * QR_CELL_PT
            if side <= QR_MAX_SIDE_PT:
                best = max(best, n)
    return best


QR_MAX_BYTES = _max_bytes()

# Arial has no Thai glyphs at all, so Thai text must name its own face.
#
# Leelawadee UI, chosen for a cleaner and more minimal look — and this time
# on evidence. A test strip printed "สิริกิติ์ ชั้น ผู้" in six combinations of
# face and combinedChars on the PT-9700PC, and Teerachot confirmed every line
# came out complete, garan and all. Tahoma also prints correctly and stays a
# safe fallback; it is simply heavier at 10-12 pt.
#
# Leelawadee UI was tried once BEFORE that strip existed, while chasing
# overlapping characters, and it looked guilty for a while. It was not: the
# document shell was broken and P-touch was rendering something else
# entirely. Two rounds of blaming the font, the box width and shrink=true all
# missed it.
#
# The rule that came out of that: a font here is a claim about a printer in
# another room. Change it only with a sticker off that printer in hand.
THAI_FONT = "Browallia New"
# Print-proven on the PT-9700PC, all three, by a test strip that came back
# with every line complete — including "ติ์", a consonant carrying two
# stacked marks. IBM Plex Sans Thai was set briefly and reverted: it does not
# ship with Windows, was not installed on the machine that drives the Editor,
# and an unresolvable family name is substituted silently. Pick from this
# list, or print a strip first.
THAI_FONT_PROVEN = ("Browallia New", "Leelawadee UI", "Tahoma")
LATIN_FONT = "Arial"


# The document shell, transcribed from the file that printed. Every piece of
# it earned its place the hard way:
#
#   * `<style:sheet name=...>` WRAPS the paper, the cut line, the background
#     and the objects, and `pt:body currentSheet` names it. Omit the wrapper
#     and P-touch finds no sheet behind the name it was given: the label
#     opens COMPLETELY BLANK, with no error and nothing wrong-looking in the
#     XML. That is what a rewritten shell cost on 2026-09-24.
#   * The namespace list, `version="1.7"`, the generator string,
#     `format="261"`, `printerID="25136"` and `<style:cutLine>` are all
#     copied rather than chosen. None of them is understood; all of them are
#     in a file that works.
#   * Lengths are written the way P-touch writes them — `68pt`, `2pt` — not
#     `68.0pt`. Whether it cares is unknown and not worth finding out.
_NS = ('xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main" '
       'xmlns:style="http://schemas.brother.info/ptouch/2007/lbx/style" '
       'xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text" '
       'xmlns:draw="http://schemas.brother.info/ptouch/2007/lbx/draw" '
       'xmlns:image="http://schemas.brother.info/ptouch/2007/lbx/image" '
       'xmlns:barcode="http://schemas.brother.info/ptouch/2007/lbx/barcode" '
       'xmlns:database="http://schemas.brother.info/ptouch/2007/lbx/database" '
       'xmlns:table="http://schemas.brother.info/ptouch/2007/lbx/table" '
       'xmlns:cable="http://schemas.brother.info/ptouch/2007/lbx/cable"')
SHEET = "ชีท1"                    # P-touch's own default sheet name


def _pt(v) -> str:
    """68.0 -> '68', 11.4 -> '11.4' — lengths as P-touch writes them."""
    f = float(v)
    return str(int(f)) if f == int(f) else str(round(f, 1))


class LabelTooBig(ValueError):
    """The content cannot be placed inside the printable area."""


def usable(paper_len_pt: float) -> tuple:
    """(x_min, x_max, y_min, y_max) that the printer will actually mark."""
    return EDGE_PT, paper_len_pt - EDGE_PT, ACROSS_PT, TAPE_PT - ACROSS_PT


def check_fits(objects_xywh, paper_len_pt: float) -> list:
    """Names of objects that fall outside the printable area."""
    x0, x1, y0, y1 = usable(paper_len_pt)
    bad = []
    for name, x, y, w, h in objects_xywh:
        if x < x0 - 0.05 or x + w > x1 + 0.05 or y < y0 - 0.05 or y + h > y1 + 0.05:
            bad.append(f"{name} at x {x:.1f}..{x + w:.1f} y {y:.1f}..{y + h:.1f}")
    return bad


def fit_qr(data: str, *, cell_pt: float = QR_CELL_PT,
           limit_pt: float = QR_MAX_SIDE_PT) -> tuple:
    """(modules, side_pt, ecc_key) for the strongest EC that still fits.

    The serial is free text typed at print time and the warehouse has never
    said how long it runs, so the cell size cannot be chosen against an
    assumed payload. Pick the error correction to suit whatever was typed
    instead, strongest first, and raise rather than emit a symbol that
    overflows the tape — that failure is invisible until it is printed.
    """
    n = len(data.encode("utf-8"))
    for ecc in ("h", "q", "m", "l"):
        for version, cap in sorted(_QR_BYTES[ecc].items()):
            if n <= cap:
                modules = 17 + 4 * version
                side = round((modules + 4) * cell_pt, 1)   # +4 = quiet zone
                if side <= limit_pt:
                    return modules, side, ecc
    raise LabelTooBig(
        f"{n} bytes will not fit a QR at {cell_pt} pt even at the weakest "
        f"error correction (max {QR_MAX_BYTES})")


# ── XML pieces ─────────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


# The font block, byte for byte as in the file that printed. It appears
# twice in a text object — once for the box, once inside the stringItem —
# and the two must agree.
_FONT = ('<text:ptFontInfo><text:logFont name="{font}" width="0" italic="false"'
         ' weight="{weight}" charSet="0" pitchAndFamily="34"/>'
         '<text:fontExt effect="NOEFFECT" underline="0" strikeout="0"'
         ' size="{size}pt" orgSize="{orgsize}pt" textColor="#000000"'
         ' textPrintColorNumber="1"/></text:ptFontInfo>')


def text_object(data: str, x, y, w, h, *, name: str, obj_id: int,
                font: str = LATIN_FONT, weight: int = 400, size: str = "10",
                orgsize: str = "12", align: str = "CENTER") -> str:
    """One text box, matching a file P-touch wrote attribute for attribute.

    This is a transcription, not a design. Four attributes were retyped
    differently when this moved out of the scratchpad, and every one of them
    mattered:

    * `shrink="false"` — with shrink ON, P-touch squeezes text that does not
      fit rather than clipping it, and squeezed Thai stacks its vowels and
      tone marks on top of each other. This is what Teerachot kept seeing.
    * `inLineAlignment="BASELINE"` — dropped entirely in the port. Thai hangs
      marks above and below the line, so the baseline is what holds them
      apart.
    * `aspectNormal="false"` — with it true, a squeeze also distorts.
    * `pitchAndFamily="34"` — the font's family class; 2 says something else
      about the face and invites a substitution.

    `orgPoint` is the LAYOUT point size and equals `size`, never `orgSize`.

    `charLen` counts CODE POINTS, not bytes, so Thai floating vowels are one
    each; the file is rejected if the count disagrees with the data.
    """
    f = _FONT.format(font=font, weight=weight, size=size, orgsize=orgsize)
    return (
        '<text:text><pt:objectStyle'
        f' x="{x}pt" y="{y}pt" width="{w}pt" height="{h}pt"'
        ' backColor="#FFFFFF" backPrintColorNumber="0" ropMode="COPYPEN"'
        ' angle="0" anchor="TOPLEFT" flip="NONE">'
        '<pt:pen style="NULL" widthX="0.5pt" widthY="0.5pt" color="#000000"'
        ' printColorNumber="1"/>'
        '<pt:brush style="NULL" color="#000000" printColorNumber="1" id="0"/>'
        f'<pt:expanded objectName="{_esc(name)}" ID="{obj_id}" lock="0"'
        ' templateMergeTarget="LABELLIST" templateMergeType="NONE"'
        ' templateMergeID="0" linkStatus="NONE" linkID="0"/>'
        '</pt:objectStyle>'
        + f +
        '<text:textControl control="FREE" clipFrame="false"'
        ' aspectNormal="false" shrink="false" autoLF="false"'
        ' avoidImage="false"/>'
        f'<text:textAlign horizontalAlignment="{align}" verticalAlignment="TOP"'
        ' inLineAlignment="BASELINE"/>'
        '<text:textStyle vertical="false" nullBlock="false" charSpace="0"'
        f' lineSpace="0" orgPoint="{size}pt" combinedChars="false"/>'
        f'<pt:data>{_esc(data)}</pt:data>'
        f'<text:stringItem charLen="{len(data)}">{f}</text:stringItem>'
        '</text:text>')


def qr_object(data: str, x, y, *, modules: int, cell_pt: float, ecc: str,
              name: str = "barcode1", obj_id: int = 0) -> tuple:
    """The barcode element and its square side in points.

    The object box is `(modules + 4) * cellSize`, not `modules * cellSize` —
    the extra four are the two-module quiet zone `margin="true"` adds at each
    side. Getting that wrong makes a box that disagrees with what prints.
    No `stringItem` and no `charLen` here, unlike a text object.
    """
    side = round((modules + 4) * cell_pt, 1)
    xml = (
        '<barcode:barcode><pt:objectStyle x="' + str(x) + 'pt" y="' + str(y) + 'pt" '
        'width="' + str(side) + 'pt" height="' + str(side) + 'pt" '
        'backColor="#FFFFFF" backPrintColorNumber="0" ropMode="COPYPEN" '
        'angle="0" anchor="TOPLEFT" flip="NONE"><pt:pen style="NULL" '
        'widthX="0.5pt" widthY="0.5pt" color="#000000" printColorNumber="1"/>'
        '<pt:brush style="NULL" color="#000000" printColorNumber="1" id="0"/>'
        '<pt:expanded objectName="' + _esc(name) + '" ID="' + str(obj_id) + '" '
        'lock="0" templateMergeTarget="LABELPRINTER" templateMergeType="NONE" '
        'templateMergeID="0"/></pt:objectStyle>'
        '<barcode:barcodeStyle protocol="QRCODE" lengths="48" zeroFill="false" '
        'barWidth="1.2pt" barRatio="1:3" humanReadable="true" '
        'humanReadableAlignment="LEFT" checkDigit="false" autoLengths="true" '
        'margin="true" sameLengthBar="false" bearerBar="false"/>'
        '<barcode:qrcodeStyle model="2" eccLevel="' + _ECC_PCT[ecc] + '" '
        'cellSize="' + str(cell_pt) + 'pt" mbcs="auto" joint="1" version="auto"/>'
        '<pt:data>' + _esc(data) + '</pt:data></barcode:barcode>')
    return xml, side


def label_xml(objects, *, paper_len_pt: float) -> str:
    body = "".join(objects)

    # Object IDs must start at 0 and run without a gap. A list that begins
    # at 1 opens as a COMPLETELY BLANK label — P-touch reports no error, the
    # printer would happily feed blank tape, and nothing in the file looks
    # wrong. Found on 2026-09-24 when a test strip came out empty. Cheap to
    # check, invisible to debug.
    import re as _re
    ids = [int(n) for n in _re.findall(r'<pt:expanded objectName="[^"]*" ID="(\d+)"',
                                       body)]
    if ids and sorted(ids) != list(range(len(ids))):
        raise LabelTooBig(f"object IDs must be 0..{len(ids) - 1} with no gaps, "
                          f"got {sorted(ids)} — P-touch opens such a file blank")

    bg_w = _pt(paper_len_pt - 2 * ACROSS_PT - 1.6)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<pt:document {_NS} version="1.7"'
        ' generator="P-touch Editor 5.4.011 Windows">'
        f'<pt:body currentSheet="{SHEET}" direction="LTR">'
        f'<style:sheet name="{SHEET}">'
        f'<style:paper media="0" width="{_pt(TAPE_PT)}pt"'
        f' height="{_pt(paper_len_pt)}pt"'
        f' marginLeft="{_pt(ACROSS_PT)}pt" marginTop="{_pt(EDGE_PT)}pt"'
        f' marginRight="{_pt(ACROSS_PT)}pt" marginBottom="{_pt(EDGE_PT)}pt"'
        ' orientation="landscape" autoLength="false"'
        ' monochromeDisplay="true" printColorDisplay="false"'
        ' printColorsID="0" paperColor="#FFFFFF" paperInk="#000000"'
        ' split="1" format="261" backgroundTheme="0" printerID="25136"'
        ' printerName="Brother PT-9700PC"/>'
        '<style:cutLine regularCut="0pt" freeCut=""/>'
        f'<style:backGround x="{_pt(ACROSS_PT + 0.8)}pt" y="{_pt(ACROSS_PT)}pt"'
        f' width="{bg_w}pt" height="{_pt(USABLE_ACROSS)}pt"'
        ' brushStyle="NULL" brushId="0"'
        ' userPattern="NONE" userPatternId="0" color="#000000"'
        ' printColorNumber="1" backColor="#FFFFFF" backPrintColorNumber="0"/>'
        f'<pt:objects>{body}</pt:objects>'
        '</style:sheet></pt:body></pt:document>')


def prop_xml(*, created: str, revision: int = 2) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<meta:properties'
        ' xmlns:meta="http://schemas.brother.info/ptouch/2007/lbx/meta"'
        ' xmlns:dc="http://purl.org/dc/elements/1.1/"'
        ' xmlns:dcterms="http://purl.org/dc/terms/">'
        '<meta:appName>P-touch Editor</meta:appName>'
        '<dc:title></dc:title><dc:subject></dc:subject>'
        '<dc:creator>LGS-Test-Tool</dc:creator>'
        '<meta:keyword></meta:keyword><dc:description></dc:description>'
        '<meta:template></meta:template>'
        f'<dcterms:created>{created}</dcterms:created>'
        f'<dcterms:modified>{created}</dcterms:modified>'
        f'<meta:lastPrinted>{created}</meta:lastPrinted>'
        '<meta:modifiedBy>LGS-Test-Tool</meta:modifiedBy>'
        f'<meta:revision>{revision}</meta:revision>'
        '<meta:editTime>24</meta:editTime>'
        '<meta:numPages>1</meta:numPages><meta:numWords>0</meta:numWords>'
        '<meta:numChars>0</meta:numChars><meta:security>0</meta:security>'
        '</meta:properties>')


def pack(label: str, prop: str) -> bytes:
    """Zip the two documents in the order P-touch writes them."""
    import io
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("label.xml", label.encode("utf-8"))
        z.writestr("prop.xml", prop.encode("utf-8"))
    return buf.getvalue()


# -- Measuring text, so a box is the size of what goes in it ----------------
# The identity column used to be 130 pt wide whatever went in it. That was
# sized by eye against a wider Thai face; Browallia New is much narrower, and
# the widest line on the Queen's label measures 80.8 pt -- so 49 pt of the
# box was empty air. Every line is CENTRE aligned, so half of that air sat
# between the code and the text, and that is the gap Teerachot could see.
# Measure the string instead of guessing at it.
#
# fontTools arrives with fpdf2, which is already a dependency, so this costs
# the build nothing. Summing advance widths is the right answer for Thai: a
# floating vowel or tone mark has zero advance, and shaping moves marks about
# without changing how far the pen travels. Checked against Pillow's shaper
# on all five lines of the real label -- the two agree within 0.2 pt.
#
# When a face cannot be found -- another machine, another OS -- the
# measurement returns None and the caller keeps the old generous box. A label
# that is too roomy still prints; one sized from a guess might not.

_FONT_FILES = {
    ("Browallia New", 400): ("browalia.ttc", 0),
    ("Browallia New", 700): ("browalia.ttc", 1),
    ("Leelawadee UI", 400): ("LeelawUI.ttf", 0),
    ("Leelawadee UI", 700): ("LeelaUIb.ttf", 0),
    ("Tahoma", 400): ("tahoma.ttf", 0),
    ("Tahoma", 700): ("tahomabd.ttf", 0),
    ("Arial", 400): ("arial.ttf", 0),
    ("Arial", 700): ("arialbd.ttf", 0),
}


@lru_cache(maxsize=None)
def _face(font: str, weight: int):
    """(unitsPerEm, cmap, hmtx metrics) for one face, or None if not here."""
    entry = _FONT_FILES.get((font, weight)) or _FONT_FILES.get((font, 400))
    if not entry:
        return None
    name, index = entry
    path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
    if not os.path.exists(path):
        return None
    try:
        from fontTools.ttLib import TTCollection, TTFont
        f = (TTCollection(path).fonts[index] if path.lower().endswith(".ttc")
             else TTFont(path))
        return f["head"].unitsPerEm, f.getBestCmap(), f["hmtx"].metrics
    except Exception:
        return None


def text_width(text: str, *, font: str, weight: int, size_pt: float):
    """How wide the string really prints, or None if it cannot be measured."""
    face = _face(font, weight)
    if face is None:
        return None
    upm, cmap, metrics = face
    total = 0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None or g not in metrics:
            return None                 # a glyph unaccounted for: do not guess
        total += metrics[g][0]
    return total * size_pt / upm


def column_width(lines, *, pad: float, fallback: float) -> float:
    """Width of a column of (text, size, font, weight), plus breathing room."""
    widths = [text_width(t, font=fo, weight=wt, size_pt=float(sz))
              for t, sz, fo, wt in lines if t]
    if not widths or any(w is None for w in widths):
        return fallback
    return round(max(widths) + pad, 1)


# -- Drawn objects ----------------------------------------------------------
# Transcribed from Brother's own template library, which ships beside the
# editor in Ptedit54/LayoutStyle/ -- 144 files, using draw:rect, draw:poly
# and draw:frame. The attribute sets below are theirs, not invented; the last
# time element names were invented here every label opened blank.
#
# One thing is NOT verbatim: the point list of a VERTICAL rule. Every line in
# the library runs horizontally, so the geometry below is their rule turned
# on its side -- same attributes, different coordinates.
#
# The objectStyle wrapper is ours rather than theirs. Their files are older
# (version 1.1) and omit printColorNumber; ours is the one proven to print.

def _draw_style(x, y, w, h, *, name: str, obj_id: int, pen_pt: float) -> str:
    return (
        f'<pt:objectStyle x="{_pt(x)}pt" y="{_pt(y)}pt"'
        f' width="{_pt(w)}pt" height="{_pt(h)}pt"'
        ' backColor="#FFFFFF" backPrintColorNumber="0" ropMode="COPYPEN"'
        ' angle="0" anchor="TOPLEFT" flip="NONE">'
        f'<pt:pen style="INSIDEFRAME" widthX="{_pt(pen_pt)}pt"'
        f' widthY="{_pt(pen_pt)}pt" color="#000000" printColorNumber="1"/>'
        '<pt:brush style="NULL" color="#000000" printColorNumber="1" id="0"/>'
        f'<pt:expanded objectName="{_esc(name)}" ID="{obj_id}" lock="0"'
        ' templateMergeTarget="LABELLIST" templateMergeType="NONE"'
        ' templateMergeID="0" linkStatus="NONE" linkID="0"/>'
        '</pt:objectStyle>')


def rect_object(x, y, w, h, *, name: str, obj_id: int, roundness: float = 0.0,
                pen_pt: float = 0.5) -> str:
    """A rectangle outline, with rounded corners if roundness is given."""
    return ('<draw:rect>'
            + _draw_style(x, y, w, h, name=name, obj_id=obj_id, pen_pt=pen_pt)
            + f'<draw:rectStyle shape="RECTANGLE"'
              f' roundnessX="{_pt(roundness)}pt"'
              f' roundnessY="{_pt(roundness)}pt"/></draw:rect>')


def vline_object(x, y, h, *, name: str, obj_id: int, pen_pt: float = 0.5) -> str:
    """A vertical hairline, to the library's own convention.

    Twelve of the fifty rules in Brother's templates run vertically, so this
    is transcribed rather than deduced. Their box is a tenth of a point wider
    than the pen, and the two points sit on the box's CENTRE line -- half the
    box width in from the left, and half in from each end.
    """
    w = round(pen_pt + 0.1, 1)
    cx, y0, y1 = x + w / 2, y + w / 2, y + h - w / 2
    return ('<draw:poly>'
            + _draw_style(x, y, w, h, name=name, obj_id=obj_id, pen_pt=pen_pt)
            + '<draw:polyStyle shape="LINE" arrowBegin="SQUARE"'
              ' arrowEnd="SQUARE">'
              f'<draw:polyOrgPos x="{_pt(x)}pt" y="{_pt(y)}pt"'
              f' width="{_pt(w)}pt" height="{_pt(h)}pt"/>'
              f'<draw:polyLinePoints points="{_pt(cx)}pt,{_pt(y0)}pt'
              f' {_pt(cx)}pt,{_pt(y1)}pt"/>'
              '</draw:polyStyle></draw:poly>')


# ── The cabinet a label describes ──────────────────────────────────────────

@dataclass
class CabinetLabel:
    """Everything a sticker can say about one cabinet.

    Everything machine-readable is read LIVE from the gateway at print time,
    so a sticker cannot be stale. The two typed fields are the ward name and
    the serial — and the serial is stored NOWHERE: the warehouse owns that
    database, and a second copy here could only ever disagree with it.
    """
    name: str = ""                       # sys.name, the short name
    ward: str = ""                       # typed, Thai, printed only
    serial: str = ""                     # typed, free text, never stored
    ip: str = ""
    mac: str = ""
    rows: tuple = ()                     # ((row, "11-18", channel), ...)

    def qr_payload(self) -> str:
        """Identity, and the whole shape of the cabinet.

        Everything a person would otherwise retype, plus the two lines that
        are NOT printed beside the code on the standard layout and are what
        make the thing worth scanning rather than reading:

            ch 1234455678    hub channel of each row, in row order
            w  8884444888    slots in each row

        Together those give the id of every slot and the channel it hangs
        off — which is the cabinet's whole geometry, and the part nobody has
        written down on site.

        This used to be four cramped lines with the MAC's colons stripped to
        save five bytes, because the cell size was believed to be fixed at
        1.6 pt and the ceiling at 78. Both were wrong; at 1.2 pt there is
        room for all of it at stronger error correction, and the colons are
        back because the MAC is read off a phone screen by a person.
        """
        lines = [self.name]
        if self.serial:
            lines.append(f"S/N {self.serial}")
        if self.ip:
            lines.append(self.ip)
        if self.mac:
            lines.append(self.mac)
        if self.rows:
            lines.append("ch " + "".join(str(ch) for _r, _i, ch in self.rows))
            widths = [int(ids.split("-")[1]) - int(ids.split("-")[0]) + 1
                      for _r, ids, _c in self.rows]
            lines.append("w " + "".join(str(n) for n in widths))
        return "\n".join(lines)


def rows_from_gateway(settings: dict) -> tuple:
    """((row, "11-18", channel), ...) from a gateway snapshot's own settings.

    The gateway is the authority on both halves of this. `panel.shape`
    overrides `panel.cabinet` when it is set, which is the whole reason a
    cabinet the catalogue cannot name still prints a correct strip; and the
    hub map says which channel each row hangs off, which matters because two
    rows can share one and then stall together.
    """
    shape = str(settings.get("panel.shape") or "0")
    cab = str(settings.get("panel.cabinet") or "0")
    if shape and shape != "0":
        widths = [int(w) for w in shape.split(",")]
    else:
        widths = {"80": [8] * 10, "40": [4] * 10,
                  "64": [8, 8, 8, 4, 4, 4, 4, 8, 8, 8]}.get(cab, [])
    widths = [w for w in widths if w]

    hub = []
    for token in str(settings.get("bus.hub_map") or "").split(","):
        token = token.strip()
        if token.isdigit():
            hub.append(int(token))

    out = []
    for i, w in enumerate(widths, start=1):
        ch = hub[i - 1] if i - 1 < len(hub) else i
        out.append((i, f"{i * 10 + 1}-{i * 10 + w}", ch))
    return tuple(out)


# ── Layouts ────────────────────────────────────────────────────────────────
# Each takes a CabinetLabel and returns (label_xml, prop_xml, length_mm).
# Registered below so a new sticker is a function plus one dict entry.

def _detail_label(c: CabinetLabel, *, created: str, with_rows: bool) -> tuple:
    """QR + identity block in a frame, and optionally the row/id strip.

    With `with_rows`, it also carries the part nobody has written down on
    site: a technician moving between an 80 and a 40 cannot guess that one
    is eight slots per row and the other four. Without it, the label is
    shorter and the strip is simply not available at the door.

    Everything horizontal is measured rather than assumed. The columns are
    as wide as the text in them, the frame is as wide as the columns, and
    the tape is as long as the frame -- so the Queen's standard label came
    down from 78 mm to 65 mm without losing a character.
    """
    qr_data = c.qr_payload()
    modules, side, ecc = fit_qr(qr_data)

    # Across the tape: the frame sits 3 pt inside each edge, which is inside
    # the 2 pt the printer can reach and a little further in than the 1 pt
    # where the first whole character appeared on the calibration print. Its
    # inner height then comes to 56 pt, and the code at 54 pt very nearly
    # fills it, which is why the two look deliberate together.
    FR_Y, FR_H, PAD = 3.0, 62.0, 3.5
    top = FR_Y + PAD                             # 6.5
    inner_h = FR_H - 2 * PAD                     # 55.0

    GAP, CW = 5.0, 26.0                          # QR-to-rule, and a map column
    fr_x = EDGE_PT + 1.0                         # 12.4
    qr_x = fr_x + PAD
    rule1_x = qr_x + side + GAP
    id_x = rule1_x + GAP

    idlines = [
        (c.ward, "10", THAI_FONT, 400, 13.0),
        (c.name, "11", LATIN_FONT, 700, 14.0),
        (f"S/N {c.serial}" if c.serial else "", "7", LATIN_FONT, 400, 9.0),
        (c.ip, "9", LATIN_FONT, 400, 11.0),
        (c.mac, "6", LATIN_FONT, 400, 8.0),
    ]
    # 130 pt was the old fixed width and stays as the fallback: if the faces
    # cannot be measured the label is merely roomy, not wrong.
    IW = column_width([(t, sz, fo, wt) for t, sz, fo, wt, _h in idlines],
                      pad=4.0, fallback=130.0)

    rows = c.rows if with_rows else ()
    ncol = max(1, (len(rows) + 1) // 2) if rows else 0   # two banks, always
    rule2_x = id_x + IW + GAP
    map_x = rule2_x + GAP
    right = (map_x + ncol * CW) if rows else (id_x + IW)

    # Round the cut up to a whole millimetre. The tape is continuous so any
    # length prints, but a label whose length is a round number is one a
    # person can check with a ruler and one that reproduces exactly.
    import math
    fr_w = right + PAD - fr_x
    paper = round(math.ceil((fr_x + fr_w + EDGE_PT + 1) / MM) * MM, 1)

    # Five lines stacked inside the frame, summing to exactly its inner
    # height. Each box is about 1.2x its point size, and the Thai line gets
    # the most slack of the five because its marks hang furthest.
    y, lines = top, []
    for txt, sz, fo, wt, h in idlines:
        lines.append((txt, id_x, y, IW, h, sz, fo, wt))
        y += h

    # Row and id range only. The hub channel used to print here, but it is
    # wiring detail nobody reads at the cabinet door, and dropping it buys
    # the two remaining lines room to be larger.
    for i, (row, ids, _ch) in enumerate(rows):
        cx = map_x + (i % ncol) * CW
        yy = top + (0 if i < ncol else 26.0)
        lines += [
            (f"R{row}", cx, yy, CW, 10.0, "7", LATIN_FONT, 700),
            (ids, cx, yy + 11, CW, 10.0, "6.5", LATIN_FONT, 400),
        ]
    lines = [ln for ln in lines if ln[0]]

    rules = [(rule1_x, "rule1")] + ([(rule2_x, "rule2")] if rows else [])
    boxes = [("frame", fr_x, FR_Y, fr_w, FR_H),
             ("qr", qr_x, round((TAPE_PT - side) / 2, 1), side, side)]
    boxes += [(n, x, top, 0.6, inner_h) for x, n in rules]
    boxes += [(str(t)[:10], x, yy, w, h) for t, x, yy, w, h, _, _, _ in lines]
    bad = check_fits(boxes, paper)
    if bad:
        raise LabelTooBig("; ".join(bad))

    objs = [rect_object(fr_x, FR_Y, fr_w, FR_H, name="frame", obj_id=0,
                        roundness=6.0)]
    objs += [vline_object(x, top, inner_h, name=n, obj_id=i + 1)
             for i, (x, n) in enumerate(rules)]
    n0 = len(objs)
    qr_xml, _ = qr_object(qr_data, qr_x, round((TAPE_PT - side) / 2, 1),
                          modules=modules, cell_pt=QR_CELL_PT, ecc=ecc,
                          obj_id=n0)
    objs.append(qr_xml)
    objs += [
        text_object(txt, x, yy, w, h, name=f"o{i}", obj_id=n0 + 1 + i, font=fo,
                    weight=wt, size=sz, orgsize=str(round(float(sz) * 1.2, 1)))
        for i, (txt, x, yy, w, h, sz, fo, wt) in enumerate(lines)]
    return label_xml(objs, paper_len_pt=paper), prop_xml(created=created), paper / MM


def _minimal_label(c: CabinetLabel, *, created: str) -> tuple:
    """Site name, cabinet name, QR. Nothing else printed.

    The serial, the address and the MAC are all in the code already, so
    printing them too only gives a person a second place to misread. What
    this layout gives up is the row/id strip, which the code now carries as
    channels and widths but not as printed text -- if the strip is wanted at
    a glance, that is the row map layout's job.
    """
    qr_data = c.qr_payload()
    modules, side, ecc = fit_qr(qr_data)

    FR_Y, FR_H, PAD, GAP = 3.0, 62.0, 3.5, 5.0
    top = FR_Y + PAD
    inner_h = FR_H - 2 * PAD
    fr_x = EDGE_PT + 1.0
    qr_x = fr_x + PAD
    rule_x = qr_x + side + GAP
    tx = rule_x + GAP

    # Two lines, weighted the way they are read: the site answers "whose
    # cabinet is this" from across a room, the short name answers "which
    # one" and is what every other system calls it.
    txtlines = [(c.ward, "12", THAI_FONT, 400, 18.0),
                (c.name, "18", LATIN_FONT, 700, 26.0)]
    TW = column_width([(t, sz, fo, wt) for t, sz, fo, wt, _h in txtlines],
                      pad=4.0, fallback=150.0)

    import math
    fr_w = tx + TW + PAD - fr_x
    paper = round(math.ceil((fr_x + fr_w + EDGE_PT + 1) / MM) * MM, 1)

    # The pair is centred in the frame rather than hung from its top: with
    # only two lines, the leftover space reads as a mistake anywhere else.
    y = top + (inner_h - sum(h for *_r, h in txtlines)) / 2
    lines = []
    for txt, sz, fo, wt, h in txtlines:
        lines.append((txt, tx, round(y, 1), TW, h, sz, fo, wt))
        y += h
    lines = [ln for ln in lines if ln[0]]

    boxes = [("frame", fr_x, FR_Y, fr_w, FR_H),
             ("qr", qr_x, round((TAPE_PT - side) / 2, 1), side, side),
             ("rule", rule_x, top, 0.6, inner_h)]
    boxes += [(str(t)[:10], x, yy, w, h) for t, x, yy, w, h, _, _, _ in lines]
    bad = check_fits(boxes, paper)
    if bad:
        raise LabelTooBig("; ".join(bad))

    objs = [rect_object(fr_x, FR_Y, fr_w, FR_H, name="frame", obj_id=0,
                        roundness=6.0),
            vline_object(rule_x, top, inner_h, name="rule", obj_id=1)]
    qr_xml, _ = qr_object(qr_data, qr_x, round((TAPE_PT - side) / 2, 1),
                          modules=modules, cell_pt=QR_CELL_PT, ecc=ecc,
                          obj_id=2)
    objs.append(qr_xml)
    objs += [
        text_object(txt, x, yy, w, h, name=f"o{i}", obj_id=3 + i, font=fo,
                    weight=wt, size=sz, orgsize=str(round(float(sz) * 1.2, 1)))
        for i, (txt, x, yy, w, h, sz, fo, wt) in enumerate(lines)]
    return label_xml(objs, paper_len_pt=paper), prop_xml(created=created), paper / MM


@dataclass(frozen=True)
class Layout:
    key: str
    title: str
    build: Callable
    note: str = ""


def _standard_label(c: CabinetLabel, *, created: str) -> tuple:
    return _detail_label(c, created=created, with_rows=False)


def _rowmap_label(c: CabinetLabel, *, created: str) -> tuple:
    return _detail_label(c, created=created, with_rows=True)


LAYOUTS = {
    "minimal": Layout("minimal", "Minimal — site, cabinet name, QR", _minimal_label,
                      "Two lines and the code. Everything else is in the QR."),
    "standard": Layout("standard", "Standard — site, name, serial, address, QR",
                       _standard_label,
                       "The identity a person reads, printed. 78 mm for "
                       "every cabinet but the fridge, 2 mm shorter."),
    "rowmap": Layout("rowmap", "Row map — standard, plus every row and its ids",
                     _rowmap_label,
                     "For the door of a cabinet whose row widths nobody can "
                     "guess. Length follows the row count."),
}


def render(layout_key: str, cabinet: CabinetLabel, *, created: str) -> tuple:
    """(bytes of the .lbx, length in mm) for one cabinet and one layout."""
    layout = LAYOUTS[layout_key]
    label, prop, length_mm = layout.build(cabinet, created=created)
    return pack(label, prop), length_mm
