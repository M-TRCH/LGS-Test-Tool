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
* **Thai needs Tahoma.** Arial has no Thai glyphs; with Tahoma the vowels and
  tone marks compose correctly on glass.
* **`charLen` counts CODE POINTS**, so Thai floating vowels round-trip.

The QR is sized, not rendered — P-touch draws it from `<pt:data>`. All this
module needs is the module count, so a four-row capacity table replaces a QR
library; the tool ships as an exe with a deliberately short dependency list.
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
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

# The cell size P-touch itself writes. A value it does not offer gets rounded
# up and the symbol overflows the tape — which is how the first printed
# sample came out visibly too big. Never invent one.
QR_CELL_PT = 1.6

# Byte-mode capacity per version and error-correction level. Versions 1-4
# only: at 1.6 pt a version 5 symbol is (37+4)*1.6 = 65.6 pt and will not fit
# across a 64 pt tape, so 4 is the ceiling and there is nothing above it to
# tabulate. Measured against a real encoder before being written down.
_QR_BYTES = {
    "h": {1: 7, 2: 14, 3: 24, 4: 34},
    "q": {1: 11, 2: 20, 3: 32, 4: 46},
    "m": {1: 14, 2: 26, 3: 42, 4: 62},
    "l": {1: 17, 2: 32, 3: 53, 4: 78},
}
_ECC_PCT = {"h": "30%", "q": "25%", "m": "15%", "l": "7%"}
QR_MAX_BYTES = _QR_BYTES["l"][4]                 # 78

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
THAI_FONT = "Leelawadee UI"
THAI_FONT_FALLBACK = "Tahoma"       # also print-proven, heavier
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
           limit_pt: float = USABLE_ACROSS) -> tuple:
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
        """What the code carries: identity, and only identity.

        The row map, the type and the slot count are all PRINTED on the same
        label centimetres away, and firmware belongs on no sticker because one
        OTA makes it a lie. What is left is the four things somebody would
        otherwise retype by hand, which is exactly what a scanner is for.
        """
        lines = [self.name]
        if self.serial:
            lines.append(f"S/N {self.serial}")
        if self.ip:
            lines.append(self.ip)
        if self.mac:
            lines.append(self.mac)
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
    """QR + identity block, and optionally the row/id strip.

    With `with_rows`, it also carries the part nobody has written down on
    site: a technician moving between an 80 and a 40 cannot guess that one
    is eight slots per row and the other four. Without it, the label is
    shorter and the strip is simply not available at the door.
    """
    qr_data = c.qr_payload()
    modules, side, ecc = fit_qr(qr_data)

    # 130 pt, not 108: the site name is the widest thing on the label and
    # Thai has no room to give. The old box was 1.6 pt narrower than the
    # hospital's name needs at 10 pt, and P-touch's shrink would have
    # squeezed it — so the box holds the text outright instead.
    GAP, IW, CW = 9.0, 130.0, 26.0
    qr_x = 13.0
    id_x = qr_x + side + GAP
    map_x = id_x + IW + GAP
    rows = c.rows if with_rows else ()
    ncol = max(1, (len(rows) + 1) // 2) if rows else 0   # two banks, always
    # Round the cut up to a whole millimetre. The tape is continuous so any
    # length prints, but a label whose length is a round number is one a
    # person can check with a ruler and one that reproduces exactly.
    import math
    right = (map_x + ncol * CW) if rows else (id_x + IW)
    paper = round(math.ceil((right + EDGE_PT + 2) / MM) * MM, 1)

    # Five lines inside TAPE_PT - 2 * CONTENT_INSET_PT, so both edges keep
    # their clearance whatever the inset is set to.
    t = CONTENT_INSET_PT
    lines = [
        (c.ward, id_x, t, IW, 13.0, "10", THAI_FONT, 400),
        (c.name, id_x, t + 13.0, IW, 14.0, "11", LATIN_FONT, 700),
        (f"S/N {c.serial}" if c.serial else "", id_x, t + 27.0, IW, 9.0, "7",
         LATIN_FONT, 400),
        (c.ip, id_x, t + 36.0, IW, 11.0, "9", LATIN_FONT, 400),
        (c.mac, id_x, t + 47.0, IW, 8.0, "6", LATIN_FONT, 400),
    ]
    # Row and id range only. The hub channel used to print here, but it is
    # wiring detail nobody reads at the cabinet door, and dropping it buys
    # the two remaining lines room to be larger.
    for i, (row, ids, _ch) in enumerate(rows):
        cx = map_x + (i % ncol) * CW
        yy = CONTENT_INSET_PT if i < ncol else CONTENT_INSET_PT + 26.0
        lines += [
            (f"R{row}", cx, yy, CW, 10.0, "7", LATIN_FONT, 700),
            (ids, cx, yy + 11, CW, 10.0, "6.5", LATIN_FONT, 400),
        ]
    lines = [ln for ln in lines if ln[0]]

    boxes = [("qr", qr_x, (TAPE_PT - side) / 2, side, side)]
    boxes += [(str(t)[:10], x, y, w, h) for t, x, y, w, h, _, _, _ in lines]
    bad = check_fits(boxes, paper)
    if bad:
        raise LabelTooBig("; ".join(bad))

    qr_xml, _ = qr_object(qr_data, qr_x, round((TAPE_PT - side) / 2, 1),
                          modules=modules, cell_pt=QR_CELL_PT, ecc=ecc)
    objs = [qr_xml] + [
        text_object(txt, x, y, w, h, name=f"o{i + 1}", obj_id=i + 1, font=fo,
                    weight=wt, size=sz, orgsize=str(round(float(sz) * 1.2, 1)))
        for i, (txt, x, y, w, h, sz, fo, wt) in enumerate(lines)]
    return label_xml(objs, paper_len_pt=paper), prop_xml(created=created), paper / MM


def _minimal_label(c: CabinetLabel, *, created: str) -> tuple:
    """Site name, cabinet name, QR. Nothing else printed.

    The serial, the address and the MAC are all in the code already, so
    printing them too only gives a person a second place to misread. What
    this layout deliberately gives up is the row/channel strip, which is
    NOT in the QR and cannot be: the Thai site name alone is 82 bytes in
    UTF-8 and the whole symbol holds 78, so the code is identity and the
    tape is the name. If the strip is wanted at a glance, that is the full
    layout's job.
    """
    qr_data = c.qr_payload()
    modules, side, ecc = fit_qr(qr_data)

    GAP, TW = 9.0, 150.0
    qr_x = 13.0
    tx = qr_x + side + GAP
    import math
    paper = round(math.ceil((tx + TW + EDGE_PT + 2) / MM) * MM, 1)

    # Two lines, weighted the way they are read: the site answers "whose
    # cabinet is this" from across a room, the short name answers "which
    # one" and is what every other system calls it.
    lines = [
        (c.ward, tx, CONTENT_INSET_PT + 2.0, TW, 16.0, "12", THAI_FONT, 400),
        (c.name, tx, CONTENT_INSET_PT + 20.0, TW, 24.0, "18", LATIN_FONT, 700),
    ]
    lines = [ln for ln in lines if ln[0]]

    boxes = [("qr", qr_x, (TAPE_PT - side) / 2, side, side)]
    boxes += [(str(t)[:10], x, y, w, h) for t, x, y, w, h, _, _, _ in lines]
    bad = check_fits(boxes, paper)
    if bad:
        raise LabelTooBig("; ".join(bad))

    qr_xml, _ = qr_object(qr_data, qr_x, round((TAPE_PT - side) / 2, 1),
                          modules=modules, cell_pt=QR_CELL_PT, ecc=ecc)
    objs = [qr_xml] + [
        text_object(txt, x, y, w, h, name=f"o{i + 1}", obj_id=i + 1, font=fo,
                    weight=wt, size=sz, orgsize=str(round(float(sz) * 1.2, 1)))
        for i, (txt, x, y, w, h, sz, fo, wt) in enumerate(lines)]
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
                       "The identity a person reads, printed. One fixed "
                       "length whatever the cabinet."),
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
