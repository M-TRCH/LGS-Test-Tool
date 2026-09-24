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
# Tahoma, and only Tahoma. It is the one face the PT-9700PC has actually
# printed with its vowels and tone marks composed correctly. Leelawadee UI
# was tried on 2026-09-24 because it reads better on screen at 10-12 pt, and
# Teerachot got overlapping characters straight away.
#
# TWO things could produce that and only one of them has been eliminated.
# A substituted face that does not position Thai combining marks stacks tone
# marks exactly like this — but so does shrink=true squeezing text into a box
# it does not fit, and the old 108 pt identity box was 1.6 pt NARROWER than
# "รพ.สมเด็จพระนางเจ้าสิริกิติ์" needs in Tahoma at 10 pt. The box is now 130 pt,
# which clears both faces at every size used here, so the layout is fixed
# either way; which of the two was to blame is untested.
#
# Do not swap this for something that only looks better on a screen. A font
# here is a claim about a printer in another room, and the only evidence
# that counts is a sticker off that printer.
THAI_FONT = "Tahoma"
LATIN_FONT = "Arial"


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
    bg_w = round(paper_len_pt - 2 * ACROSS_PT - 1.6, 1)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main" '
        'xmlns:style="http://schemas.brother.info/ptouch/2007/lbx/style" '
        'xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text" '
        'xmlns:barcode="http://schemas.brother.info/ptouch/2007/lbx/barcode" '
        'xmlns:image="http://schemas.brother.info/ptouch/2007/lbx/image" '
        'version="1.9" generator="LGS-Test-Tool">'
        '<pt:body currentSheet="LGS" direction="LTR">'
        '<style:paper media="0" width="' + str(TAPE_PT) + 'pt" height="'
        + str(paper_len_pt) + 'pt" marginLeft="' + str(ACROSS_PT) + 'pt" '
        'marginTop="' + str(EDGE_PT) + 'pt" marginRight="' + str(ACROSS_PT) + 'pt" '
        'marginBottom="' + str(EDGE_PT) + 'pt" orientation="landscape" '
        'autoLength="false" monochromeDisplay="true" printColorDisplay="false" '
        'printColorsID="0" paperColor="#FFFFFF" paperInk="#000000" '
        'split="1" format="0" backgroundTheme="0" printerID="30256" '
        'printerName="Brother PT-9700PC"/>'
        '<style:backGrounds><style:backGround x="' + str(ACROSS_PT + 0.8) + 'pt" '
        'y="' + str(ACROSS_PT) + 'pt" width="' + str(bg_w) + 'pt" '
        'height="' + str(USABLE_ACROSS) + 'pt" brushStyle="NULL" '
        'brushId="0" backColor="#FFFFFF" backPrintColorNumber="0" '
        'brushColor="#000000" brushPrintColorNumber="1"/></style:backGrounds>'
        '<pt:objects>' + body + '</pt:objects></pt:body></pt:document>')


def prop_xml(*, created: str, revision: int = 1) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<meta:properties xmlns:meta="http://schemas.brother.info/ptouch/2007/lbx/meta" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:dcterms="http://purl.org/dc/terms/">'
        '<meta:appName>LGS-Test-Tool</meta:appName>'
        '<dc:title></dc:title><dc:subject></dc:subject><dc:creator></dc:creator>'
        '<meta:keyword></meta:keyword><dc:description></dc:description>'
        '<meta:template></meta:template>'
        '<dcterms:created>' + created + '</dcterms:created>'
        '<dcterms:modified>' + created + '</dcterms:modified>'
        '<meta:lastPrinted>' + created + '</meta:lastPrinted>'
        '<meta:modifiedBy></meta:modifiedBy>'
        '<meta:revision>' + str(revision) + '</meta:revision>'
        '<meta:editTime>0</meta:editTime>'
        '<meta:numberOfPages>1</meta:numberOfPages>'
        '<meta:numberOfWords>0</meta:numberOfWords>'
        '<meta:numberOfChars>0</meta:numberOfChars>'
        '<meta:creatingApplication></meta:creatingApplication>'
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

    lines = [
        (c.ward, id_x, 3.0, IW, 14.0, "10", THAI_FONT, 400),
        (c.name, id_x, 18.0, IW, 14.0, "11", LATIN_FONT, 700),
        (f"S/N {c.serial}" if c.serial else "", id_x, 33.0, IW, 9.0, "7", LATIN_FONT, 400),
        (c.ip, id_x, 43.0, IW, 11.0, "9", LATIN_FONT, 400),
        (c.mac, id_x, 55.0, IW, 8.0, "6", LATIN_FONT, 400),
    ]
    # Row and id range only. The hub channel used to print here, but it is
    # wiring detail nobody reads at the cabinet door, and dropping it buys
    # the two remaining lines room to be larger.
    for i, (row, ids, _ch) in enumerate(rows):
        cx = map_x + (i % ncol) * CW
        yy = 10.0 if i < ncol else 38.0
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
        (c.ward, tx, 10.0, TW, 18.0, "12", THAI_FONT, 400),
        (c.name, tx, 32.0, TW, 24.0, "18", LATIN_FONT, 700),
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
