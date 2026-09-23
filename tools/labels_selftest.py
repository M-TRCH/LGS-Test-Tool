#!/usr/bin/env python3
"""Self-test for app/labels.py — the .lbx sticker generator.

Nothing here needs a printer or a cabinet. What it locks down is the set of
facts that cost a roll of tape each to learn, and that fail SILENTLY: a
clipped label still prints, it just has no first character, and an oversized
QR still prints, it just runs off the edge.

The geometry case compares against the label that was actually printed on the
PT-9700PC and scanned back — if a refactor moves an object, this says so.
"""
import sys
import io
import re
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import labels                                         # noqa: E402

WARD = "ห้องยาผู้ป่วยนอก ชั้น 2"
FAILS = []


def check(name, got, want):
    if got == want:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}\n         got  {got!r}\n         want {want!r}")
        FAILS.append(name)


def check_true(name, cond, note=""):
    check(name + (f" ({note})" if note else ""), bool(cond), True)


def rows_for(cab, shape, hub):
    return labels.rows_from_gateway({"panel.cabinet": cab, "panel.shape": shape,
                                     "bus.hub_map": hub})


def sample(**kw):
    base = dict(name="Chest-Std-02", ward=WARD, serial="LGS-2026-0042",
                ip="192.168.0.229", mac="A8:61:0A:51:5D:9C",
                rows=rows_for("80", "0", "1,2,3,4,5,6,7,8,7,8"))
    base.update(kw)
    return labels.CabinetLabel(**base)


print("rows_from_gateway — the shape overrides the preset, as the gateway does")
check("type 80 is ten rows of eight", rows_for("80", "0", "1,2,3,4,5,6,7,8,7,8")[0],
      (1, "11-18", 1))
check("type 40 is ten rows of FOUR", rows_for("40", "0", "1,2,3,4,5,6,7,8,7,8")[0],
      (1, "11-14", 1))
check("the 64 is not a rectangle", rows_for("64", "0", "1,2,3,4,4,5,5,6,7,8")[3],
      (4, "41-44", 4))
check("rows 9 and 10 share channels 7 and 8",
      [r[2] for r in rows_for("80", "0", "1,2,3,4,5,6,7,8,7,8")[-2:]], [7, 8])
# A shape is the only way to say 7x8 or the 5x8 fridge, which is why
# panel.cabinet gained a "no preset" value.
check("shape wins over a stale preset",
      len(rows_for("64", "8,8,8,8,8,8,8", "1,2,3,4,5,6,7")), 7)
check("the fridge is five rows of eight, not ten of four",
      rows_for("0", "8,8,8,8,8", "1,2,3,4,5")[0], (1, "11-18", 1))

print("\nQR sizing — the ceiling is version 4, because version 5 overflows")
mods, side, ecc = labels.fit_qr("x" * 62)
check("62 bytes still fits at EC-M", (mods, side, ecc), (33, 59.2, "m"))
check("the box is (modules + 4) * cell, quiet zone included", side,
      round((mods + 4) * labels.QR_CELL_PT, 1))
check_true("a version 4 symbol fits a 64 pt tape", side <= labels.USABLE_ACROSS)
_, _, ecc_long = labels.fit_qr("x" * 70)
check("a longer payload drops the error correction rather than the fit",
      ecc_long, "l")
try:
    labels.fit_qr("x" * 200)
    check("200 bytes is refused", "no exception", "LabelTooBig")
except labels.LabelTooBig:
    print("  ok   200 bytes is refused")

print("\ncheck_fits — clipping is silent on the printer, so catch it here")
check("nothing inside the printable area is flagged",
      labels.check_fits([("a", 11.4, 2.0, 10, 10)], 340.2), [])
check_true("an object past the far edge is flagged",
           labels.check_fits([("a", 320.0, 2.0, 20, 10)], 340.2))
check_true("an object before the near edge is flagged",
           labels.check_fits([("a", 2.0, 2.0, 10, 10)], 340.2))
check_true("an object off the side of the tape is flagged",
           labels.check_fits([("a", 20.0, 60.0, 10, 20)], 340.2))

print("\nthe full layout, against the label that was printed and scanned")
blob, mm = labels.render("full", sample(), created="2026-09-23T00:00:00Z")
xml = zipfile.ZipFile(io.BytesIO(blob)).read("label.xml").decode()
check("zip holds exactly label.xml then prop.xml",
      zipfile.ZipFile(io.BytesIO(blob)).namelist(), ["label.xml", "prop.xml"])
# The no-line-breaks rule is about the XML STRUCTURE — P-touch writes each
# document as one line. Data may legitimately contain newlines: the QR
# payload is deliberately multi-line, and the reference label that printed
# and scanned carries three of them, all inside the barcode's pt:data.
structure = re.sub(r'<pt:data>.*?</pt:data>', '<pt:data/>', xml, flags=re.S)
check_true("the XML structure is one line", "\n" not in structure)
check_true("the QR payload keeps its line breaks",
           "\n" in re.search(r'<barcode:barcode>.*?<pt:data>(.*?)</pt:data>',
                             xml, re.S).group(1))
check("the QR sits at x=13 as printed",
      re.search(r'<barcode:barcode><pt:objectStyle x="([\d.]+)pt"', xml).group(1), "13.0")
check("the cell size is the one P-touch itself writes",
      re.search(r'cellSize="([\d.]+)pt"', xml).group(1), "1.6")
check("Thai is set in Tahoma", 'name="Tahoma"' in xml, True)
# LEFT alignment at x=2.8 lost the first character of every line on a real
# print. Check the attribute that governs text, not the bare word: the
# barcode style carries humanReadableAlignment="LEFT" from P-touch itself.
check("every text object is centred",
      set(re.findall(r'horizontalAlignment="(\w+)"', xml)), {"CENTER"})
check("10 rows make a 121 mm label", round(mm), 121)
check("7 rows make a shorter one",
      round(labels.render("full", sample(rows=rows_for("0", "8,8,8,8,8,8,8",
                                                       "1,2,3,4,5,6,7")),
                          created="x")[1]), 112)

print("\ncharLen counts CODE POINTS, so Thai floating vowels survive")
for m in re.finditer(r'<pt:data>(.*?)</pt:data><text:stringItem charLen="(\d+)"', xml):
    if len(m.group(1)) != int(m.group(2)):
        check(f"charLen for {m.group(1)!r}", m.group(2), str(len(m.group(1))))
        break
else:
    print("  ok   every charLen matches its data")

print("\nthe QR carries identity only — the rest is printed beside it")
check("payload is name, serial, ip, mac", sample().qr_payload().split("\n"),
      ["Chest-Std-02", "S/N LGS-2026-0042", "192.168.0.229", "A8:61:0A:51:5D:9C"])
check("a cabinet with no serial simply omits the line",
      len(sample(serial="").qr_payload().split("\n")), 3)

print("\na serial too long to encode is refused before any tape is spent")
try:
    labels.render("full", sample(serial="X" * 40), created="x")
    check("40-character serial", "no exception", "LabelTooBig")
except labels.LabelTooBig:
    print("  ok   40-character serial is refused")

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
    sys.exit(1)
print("ALL PASS")
