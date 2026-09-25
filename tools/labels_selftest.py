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
import os
import re
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import labels
from app.lgs_map import layout_by_key, layout_widths                                         # noqa: E402

# The real site name, because its length is the whole reason the QR cannot
# carry it: 28 Thai characters are 82 bytes in UTF-8 against a 78-byte code.
WARD = "รพ.สมเด็จพระนางเจ้าสิริกิติ์"
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


# The only numbers here that depend on which plate is fitted. Everything
# else is checked as a relationship, so switching the frame does not mean
# editing the tests.
ROWMAP_MM = {"round": 116, "bold": 116}

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

print("\nQR sizing — the box cap decides now, not the tape")
# The ceiling was version 4 and 78 bytes for a long time, on the belief that
# 1.6 pt was the only cell size P-touch offers. A calibration print put the
# same payload at 0.8, 1.0, 1.2, 1.4 and 1.6: all five printed at the size
# declared and all five scanned. The limit is a choice, and the choice is to
# spend the room on error correction and clearance rather than a small label.
mods, side, ecc = labels.fit_qr("x" * 62)
check("a short payload takes the strongest EC that fits", ecc, "h")
check("the box is (modules + 4) * cell, quiet zone included", side,
      round((mods + 4) * labels.QR_CELL_PT, 1))
check_true("the symbol stays inside the cap", side <= labels.QR_MAX_SIDE_PT,
           f"{side} <= {labels.QR_MAX_SIDE_PT}")
check_true("which clears the tape edge better than the old 1.6 pt symbol",
           (labels.TAPE_PT - side) / 2 > 4.4,
           f"{(labels.TAPE_PT - side) / 2:.1f} pt vs 4.4")
_, _, ecc_long = labels.fit_qr("x" * 120)
check("a longer payload drops the error correction rather than the fit",
      ecc_long, "q")
try:
    labels.fit_qr("x" * 300)
    check("300 bytes is refused", "no exception", "LabelTooBig")
except labels.LabelTooBig:
    print("  ok   300 bytes is refused")

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
blob, mm = labels.render("rowmap", sample(), created="2026-09-23T00:00:00Z")
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
# The code used to start at x=13, hard against the printable edge. It now
# sits inside the frame, which is itself 1 pt inside that edge.
# Derived, not typed: the plate is a one-line switch and the double plate
# pushes everything 1.8 pt further in, so a literal here would have to be
# edited every time the frame changed.
# Compared as the file writes it, not as a float: CONTENT_X is a sum of
# constants and on the double plate it comes to 17.700000000000003, which is
# not equal to 17.7 and is exactly why _pt exists.
check_true("the QR sits inside the frame, not on the paper edge",
           float(re.search(r'<barcode:barcode><pt:objectStyle x="([\d.]+)pt"',
                           xml).group(1)) >= labels.CONTENT_X,
           "the code takes its own gap, never less than the text's")
# A coordinate computed from constants lands on 17.700000000000003 unless
# every one of them goes through _pt. Float noise in a file the printer
# parses is not worth discovering at the printer.
check("no coordinate carries float noise",
      [v for v in re.findall(r'(?:x|y|width|height)="([\d.]+)pt"', xml)
       if len(v.split(".")[-1]) > 1 and "." in v], [])
check("the cell size is one the printer was shown to honour",
      float(re.search(r'cellSize="([\d.]+)pt"', xml).group(1)), labels.QR_CELL_PT)
check_true("and it is one of the five that were print-tested",
           labels.QR_CELL_PT in (0.8, 1.0, 1.2, 1.4, 1.6))
check("Thai names its own face", f'name="{labels.THAI_FONT}"' in xml, True)
check_true("and it is not Arial, which has no Thai glyphs",
           labels.THAI_FONT != labels.LATIN_FONT)
# LEFT alignment at x=2.8 lost the first character of every line on a real
# print. Check the attribute that governs text, not the bare word: the
# barcode style carries humanReadableAlignment="LEFT" from P-touch itself.
check("every text object is centred",
      set(re.findall(r'horizontalAlignment="(\w+)"', xml)), {"CENTER"})
check(f"10 rows make a {ROWMAP_MM[labels.FRAME_STYLE]} mm label with the "
      f"{labels.FRAME_STYLE} plate", round(mm), ROWMAP_MM[labels.FRAME_STYLE])
check("and dropping three rows takes 10 mm off, whatever the plate",
      round(mm) - round(labels.render("rowmap",
                                      sample(rows=rows_for("0", "8,8,8,8,8,8,8",
                                                           "1,2,3,4,5,6,7")),
                                      created="x")[1]), 10)

print("\nboxes are measured, not assumed")
# labels.text_width sums advance widths out of the font's own hmtx table.
# Check it against a real shaper rather than against numbers typed in here:
# Pillow lays the string out properly, applying Thai mark positioning, and
# the two should agree because marks are zero-advance -- shaping moves them
# about without changing how far the pen travels.
from PIL import ImageFont                                       # noqa: E402
for label_, text_, font_, weight_, size_, file_, idx_ in (
        ("Thai site name", WARD, labels.THAI_FONT, 400, 10.0, "browalia.ttc", 0),
        ("cabinet name", "QueenSirikit-01", "Arial", 700, 11.0, "arialbd.ttf", 0),
        ("serial line", "S/N LGS-CSV-1169-001", "Arial", 400, 7.0, "arial.ttf", 0),
        ("the MAC", "A8:61:0A:50:D3:2B", "Arial", 400, 6.0, "arial.ttf", 0)):
    mine = labels.text_width(text_, font=font_, weight=weight_, size_pt=size_)
    try:
        theirs = ImageFont.truetype(file_, int(size_ * 10),
                                    index=idx_).getlength(text_) / 10.0
    except OSError:
        continue
    check_true(f"  {label_} agrees with Pillow's shaper",
               mine is not None and abs(mine - theirs) < 0.3,
               f"{mine:.2f} vs {theirs:.2f} pt")
check("a face that is not installed cannot be measured",
      labels.text_width("x", font="No Such Face", weight=400, size_pt=10), None)
check("so the column keeps the old generous box",
      labels.column_width([("x", "10", "No Such Face", 400)], pad=4.0,
                          fallback=130.0), 130.0)
_iw = labels.column_width([(WARD, "10", labels.THAI_FONT, 400),
                           ("QueenSirikit-01", "11", labels.LATIN_FONT, 700)],
                          pad=4.0, fallback=130.0)
check_true("a measured column is far narrower than that fallback",
           _iw < 90, f"{_iw} pt, not 130")
check_true("but still wider than the widest line in it", _iw > 80.8,
           f"{_iw} pt > 80.8")

print("\nobject IDs — a list that starts at 1 opens as a blank label")
ids = [int(n) for n in re.findall(r'<pt:expanded objectName="[^"]*" ID="(\d+)"', xml)]
check("ids run 0..N with no gaps", sorted(ids), list(range(len(ids))))
for key in labels.LAYOUTS:
    blob_k, _ = labels.render(key, sample(), created="x")
    x_k = zipfile.ZipFile(io.BytesIO(blob_k)).read("label.xml").decode()
    i_k = [int(n) for n in re.findall(r'<pt:expanded objectName="[^"]*" ID="(\d+)"', x_k)]
    check(f"  {key} starts at 0", min(i_k), 0)
try:
    labels.label_xml(['<pt:expanded objectName="a" ID="1"/>'], paper_len_pt=100.0)
    check("a list starting at 1 is refused", "no exception", "LabelTooBig")
except labels.LabelTooBig:
    print("  ok   a list starting at 1 is refused")

print("\nEVERY attribute, against the file that printed and scanned")
# Five attributes were retyped differently when this left the scratchpad --
# shrink, aspectNormal, inLineAlignment, pitchAndFamily and orgPoint -- and
# shrink alone squeezes Thai until its tone marks stack. Two rounds of
# comparison missed them by checking only the fields someone thought to
# name. So compare the whole tag, and let geometry be the only exception.
REF = Path(r"C:\Users\mteer\AppData\Local\Temp\claude\lbx-tests\test5-qr-fitted.lbx")
if REF.exists():
    ref_xml = zipfile.ZipFile(REF).read("label.xml").decode()

    def _thai_object(x):
        for o in re.findall(r'<text:text>.*?</text:text>', x, re.S):
            t = re.search(r'<pt:data>(.*?)</pt:data>', o, re.S).group(1)
            if any('\u0e00' <= ch <= '\u0e7f' for ch in t):
                return o
        return ""

    def _attrs(o):
        d = {}
        for tag in re.findall(r'<[a-z:]+[^>]*/?>', o):
            n = re.match(r'<([a-z:]+)', tag).group(1)
            for k, v in re.findall(r'(\w+)="([^"]*)"', tag):
                d[f"{n}.{k}"] = v
        return d

    # Excluded because they are functions of the content and the layout, or
    # a deliberate choice with its own case above — not values that could
    # silently drift. `name` is the font family: the reference was printed in
    # Tahoma and the generator now sets Leelawadee UI, both print-proven.
    GEOM = {"x", "y", "width", "height", "ID", "objectName", "charLen", "name"}
    A, B = _attrs(_thai_object(ref_xml)), _attrs(_thai_object(xml))
    drift = [(k, A.get(k, "—"), B.get(k, "—")) for k in sorted(set(A) | set(B))
             if A.get(k) != B.get(k) and k.split(".")[-1] not in GEOM]
    check("no attribute drifts from the printed reference", drift, [])
else:
    print("  --   reference label not on this machine, comparison skipped")

print("\nfont attributes, against what P-touch writes for itself")
# The first comparison against the printed reference checked coordinates and
# data and reported 36/36 identical — while orgPoint was 20% wrong on every
# object, because it was never looked at. Compare the whole triple.
triples = set()
for o in re.findall(r'<text:text>.*?</text:text>', xml, re.S):
    sz = re.search(r'size="([\d.]+)pt" orgSize="([\d.]+)pt"', o)
    op = re.search(r'orgPoint="([\d.]+)pt"', o)
    triples.add((sz.group(1), sz.group(2), op.group(1)))
bad_point = [t for t in triples if float(t[2]) != float(t[0])]
check("orgPoint equals size on every object", bad_point, [])
bad_org = [t for t in triples if abs(float(t[1]) - float(t[0]) * 1.2) > 0.05]
check("orgSize is 1.2x size on every object", bad_org, [])

print("\ncharLen counts CODE POINTS, so Thai floating vowels survive")
for m in re.finditer(r'<pt:data>(.*?)</pt:data><text:stringItem charLen="(\d+)"', xml):
    if len(m.group(1)) != int(m.group(2)):
        check(f"charLen for {m.group(1)!r}", m.group(2), str(len(m.group(1))))
        break
else:
    print("  ok   every charLen matches its data")

print("\nthe minimal layout — two lines and the code")
mini, mini_mm = labels.render("minimal", sample(), created="2026-09-24T00:00:00Z")
mx = zipfile.ZipFile(io.BytesIO(mini)).read("label.xml").decode()
check("three objects: the QR and two lines",
      len(re.findall(r'<text:text>|<barcode:barcode>', mx)), 3)
check_true("shorter than the full label", mini_mm < mm, f"{mini_mm:.0f} < {mm:.0f} mm")
check_true("the row strip is NOT on it", "R1" not in mx)
check_true("the full label still has it", "R1" in xml)
# The channel is still carried in the data — another layout may want it —
# it just stopped being printed, being wiring detail nobody reads at a door.
check_true("the channel is no longer printed", "ch1" not in xml)
check("but rows_from_gateway still reports it",
      rows_for("80", "0", "1,2,3,4,5,6,7,8,7,8")[8][2], 7)
check_true("nor the address, which lives in the code", "192.168" not in
           re.sub(r'<barcode:barcode>.*?</barcode:barcode>', '', mx, flags=re.S))
check_true("the site name IS on it, because Thai cannot go in the code",
           WARD in mx)
# It used to be one fixed length whatever the cabinet. Now that the QR
# carries the channel map and the row widths, its payload — and so its
# version, and so its box — grows with the row count, and the label grows
# with it. A couple of millimetres, and the price of the code being worth
# scanning.
# The code carries the channel map, so its payload grows with the row count
# and can tip it into the next version. Whether that shows up in the label's
# length depends entirely on where the cell size puts the version boundary:
# it did at 1.2 pt, it did not at 1.0, and at 0.8 it does again, by a
# millimetre. Check the bound rather than the fact, which keeps moving.
_five = round(labels.render("minimal", sample(rows=rows_for("0", "8,8,8,8,8",
                                                            "1,2,3,4,5")),
                            created="x")[1])
# This one has been true, false, true and is now false again, and each time
# for a different reason. The code carries the channel map, so its payload
# grows with the row count and can tip it into the next version; the printed
# name now carries the type, and "40R" is wider than "80". So the fridge can
# come out LONGER than a ten-row chest even though it holds half as much.
# Check the bound, which is the thing worth guaranteeing: no label strays
# far from its neighbours, whatever drives the difference.
check_true("no cabinet is wildly out of step with another",
           abs(round(mini_mm) - _five) <= 6,
           f"{_five} mm vs {round(mini_mm)} mm")
# 28 Thai characters are 82 bytes in UTF-8, and for a long time that was
# more than the whole code could hold -- which was the reason the site name
# is printed rather than encoded. At 1.0 pt it would now fit alongside
# everything else, so the reason has changed and is worth stating: the name
# is the one field nobody reads live, it is the most likely thing on the
# label to be wrong, and it is already printed in full an inch away.
_together = len(WARD.encode("utf-8")) + len(sample().qr_payload().encode("utf-8")) + 1
check_true("the site name WOULD now fit beside the rest",
           _together <= labels.QR_MAX_BYTES,
           f"{_together} B of {labels.QR_MAX_BYTES}")
check_true("it is left out on purpose, not for want of room",
           "รพ." not in sample().qr_payload())

print("\nthe QR: identity, and the whole shape of the cabinet")
check("payload is name, serial, ip, mac, channels, widths",
      sample().qr_payload().split("\n"),
      ["Chest-Std-02", "S/N LGS-2026-0042", "192.168.0.229", "A8:61:0A:51:5D:9C",
       "ch 1234567878", "w 8888888888"])
check("a cabinet with no serial simply omits the line",
      len(sample(serial="").qr_payload().split("\n")), 5)
# The colons went for five bytes when the ceiling was 78; at 1.2 pt there is
# no need, and a person reads the MAC off a phone screen.
check_true("the MAC keeps its colons", ":" in sample().qr_payload())
check("one channel digit per row, in row order",
      sample().qr_payload().split("\n")[-2],
      "ch " + "".join(str(r[2]) for r in sample().rows))
check("the 64's doubled channels show up as repeats",
      labels.CabinetLabel(rows=rows_for("64", "0", "1,2,3,4,4,5,5,6,7,8"))
      .qr_payload().split("\n")[-2], "ch 1234455678")
check("and its half-width middle rows show in the widths",
      labels.CabinetLabel(rows=rows_for("64", "0", "1,2,3,4,4,5,5,6,7,8"))
      .qr_payload().split("\n")[-1], "w 8884444888")
worst = labels.CabinetLabel(name="QueenSirikit-01", serial="LGS-CSV-1169-001",
                            ip="192.168.0.227", mac="A8:61:0A:50:D3:2B",
                            rows=rows_for("64", "0", "1,2,3,4,4,5,5,6,7,8"))
n = len(worst.qr_payload().encode("utf-8"))
check_true("the longest cabinet in the fleet still fits",
           n <= labels.QR_MAX_BYTES, f"{n} of {labels.QR_MAX_BYTES} bytes")
check_true("with room to spare, unlike the four bytes it had at 1.6 pt",
           labels.QR_MAX_BYTES - n > 20,
           f"{labels.QR_MAX_BYTES - n} bytes spare")


# The firmware version is the one field on the label that stops being true.
# Everything else describes the cabinet for as long as it exists; this one
# changes at the next OTA, which was the reason for leaving it out. It is
# carried with the DATE it was read, so it is a record of what the cabinet
# was running when the sticker was made rather than a claim about today --
# and a record cannot go stale.
_fw = sample(fw="1.12.2", built="2026-09-24").qr_payload()
check("the firmware line is last, and dated",
      _fw.split(chr(10))[-1], "fw 1.12.2 2026-09-24")
check_true("a cabinet whose firmware was not read simply omits it",
           "fw " not in sample().qr_payload())
check("the date is dropped rather than left dangling",
      sample(fw="1.12.2").qr_payload().split(chr(10))[-1], "fw 1.12.2")
_m, _s, _e = labels.fit_qr(_fw)
check_true("it still fits, one level weaker",
           _e == "q" and _s <= labels.QR_MAX_SIDE_PT,
           f"{len(_fw.encode())} B, EC-{_e.upper()} ({labels._ECC_PCT[_e]}), {_s} pt")
check_true("which is still stronger than the label that printed and scanned",
           labels._ECC_PCT[_e] == "25%", labels._ECC_PCT[_e])


# What the MODULES run. The gateway does not know, so it costs a survey --
# one read each, 22 s measured on the Queen's 64 -- which is why the tab
# asks rather than assumes. One version when the cabinet agrees, lowest and
# highest when it does not: a replaced board on a different version is
# exactly the thing worth knowing and exactly the thing one number hides.
check("one version when every module agrees",
      labels.module_version(["v3.4.0"] * 64), "v3.4.0")
check("lowest and highest when they do not",
      labels.module_version(["v3.4.0"] * 63 + ["v3.5.0"]), "v3.4.0-v3.5.0")
check("and nothing at all when none was read", labels.module_version([]), "")
check("the row ranges expand back into module ids",
      labels.ids_from_rows(((1, "11-18", 1), (2, "21-24", 2))),
      (11, 12, 13, 14, 15, 16, 17, 18, 21, 22, 23, 24))
_both = sample(fw="1.12.2", built="2026-09-24", mod="v3.4.0").qr_payload()
check("the module line comes after the gateway's",
      _both.split(chr(10))[-2:], ["fw 1.12.2 2026-09-24", "mod v3.4.0"])
_m2, _s2, _e2 = labels.fit_qr(_both)
check_true("both firmware lines still fit in the same symbol",
           _e2 == "q" and _s2 <= labels.QR_MAX_SIDE_PT,
           f"{len(_both.encode())} B, EC-{_e2.upper()}, {_s2} pt")
_mixed = sample(fw="1.12.2", built="2026-09-24",
                mod="v3.4.0-v3.5.0").qr_payload()
_m3, _s3, _e3 = labels.fit_qr(_mixed)
check_true("and so does a cabinet with two versions in it",
           _s3 <= labels.QR_MAX_SIDE_PT,
           f"{len(_mixed.encode())} B, EC-{_e3.upper()}, {_s3} pt")


# The cabinet type: printed, never encoded. The widths already identify it
# in the code and identify it BETTER -- lgs40 and lgs40r are both forty
# slots and only the widths tell them apart -- so encoding a slot count
# would have spent a level of error correction on a worse answer. Printed,
# it costs 3 mm of tape and saves a person adding up eight digits in their
# head to find out what they are standing in front of.
for _key, _want in (("lgs80", "80"), ("lgs64", "64"), ("lgs56", "56"),
                    ("lgs40", "40"), ("lgs40r", "40R"), ("smt", "SMT")):
    _L = layout_by_key(_key)
    _ids, _rows, _k = list(_L.ids), [], 0
    for _i, _n in enumerate(layout_widths(_L), start=1):
        _rows.append((_i, f"{_ids[_k]}-{_ids[_k + _n - 1]}", 1)); _k += _n
    check(f"  {_key} reads as {_want}", labels.cabinet_type(tuple(_rows)), _want)
check("the two forty-slot cabinets do NOT collide",
      labels.cabinet_type(((1, "11-14", 1), (2, "21-24", 1), (3, "31-34", 1),
                           (4, "41-44", 1), (5, "51-54", 1), (6, "61-64", 1),
                           (7, "71-74", 1), (8, "81-84", 1), (9, "91-94", 1),
                           (10, "101-104", 1))) != "40R", True)
check("a shape matching no preset falls back to its slot count",
      labels.cabinet_type(((1, "11-15", 1), (2, "21-25", 1))), "10")
check("and a cabinet that was never read says nothing",
      labels.cabinet_type(()), "")

_typed, _ = labels.render("standard", sample(), created="x")
_tx = zipfile.ZipFile(io.BytesIO(_typed)).read("label.xml").decode()
check_true("the type is printed beside the name",
           f"Chest-Std-02 · 80" in _tx,
           [d for d in re.findall(r"<pt:data>([^<]*)</pt:data>", _tx)
            if "Chest" in d])
check_true("and is NOT in the code, which already knows the shape",
           "80" not in sample().qr_payload().split(chr(10))[0])

print("\na serial too long to encode is refused before any tape is spent")
# Forty characters used to be refused. At 1.2 pt the code holds 134 bytes
# rather than 78, so it now fits with room over -- the guard is still needed,
# just a good deal further out than it was.
labels.render("rowmap", sample(serial="X" * 40), created="x")
print("  ok   a 40-character serial encodes fine at 1.2 pt")
try:
    labels.render("rowmap", sample(serial="X" * 200), created="x")
    check("200-character serial", "no exception", "LabelTooBig")
except labels.LabelTooBig:
    print("  ok   a 200-character serial is refused")

print("\nthe plate, against Brother's own template library")
PLATE = "draw:frame" if labels.FRAME_KIND == "frame" else "draw:rect"
for key in ("minimal", "standard", "rowmap"):
    b_k, _ = labels.render(key, sample(), created="x")
    x_k = zipfile.ZipFile(io.BytesIO(b_k)).read("label.xml").decode()
    check(f"  {key} carries the {labels.FRAME_STYLE} plate",
          len(re.findall(f"<{PLATE}>", x_k)), 1)
    check_true(f"  {key} has a rule beside the code", "<draw:poly>" in x_k)

# The plate has to stay inside the band the printer can actually mark. A
# calibration print put the first whole character at 1 pt from the top edge,
# so a line at 3 pt has something in hand -- which matters, because one
# sticker came back with its top edge shaved.
fx, fy, fw, fh = [float(v) for v in re.search(
    f'<{PLATE}><pt:objectStyle x="([\d.]+)pt" y="([\d.]+)pt"'
    r' width="([\d.]+)pt" height="([\d.]+)pt"', xml).groups()]
check_true("the plate clears both edges of the tape",
           fy >= labels.ACROSS_PT and fy + fh <= labels.TAPE_PT - labels.ACROSS_PT,
           f"y {fy}..{fy + fh}, band {labels.ACROSS_PT}..{labels.TAPE_PT - labels.ACROSS_PT}")
check_true("and both ends of the label",
           fx >= labels.EDGE_PT and fx + fw <= mm * labels.MM - labels.EDGE_PT,
           f"x {fx}..{fx + fw:.1f}")
check("content starts one pad inside the plate",
      labels._pt(labels.CONTENT_X),
      labels._pt(fx + labels.FRAME_PAD))

if labels.FRAME_KIND == "frame":
    # A rounded corner is art, not geometry: roundnessX is inert, proven by a
    # strip of five rectangles from 0 to 40 pt that came back identical and
    # square. SIMPLE 3 is the Editor's plain rounded rectangle, found by
    # sweeping the style index 0..15 and looking at the result.
    cat, st = labels.FRAME_ART
    check("the plate names the style that is actually round",
          re.search(r'<draw:frameStyle category="(\w+)" style="(\d+)"',
                    xml).groups(), (cat, str(st)))
    check("stretched, so the corner keeps its size at any width",
          re.search(r'stretchCenter="(\w+)"', xml).group(1), "true")
    check("and drawn with the pen every frame in the library uses",
          re.search(r'<draw:frame><pt:objectStyle[^>]*>'
                    r'<pt:pen style="(\w+)" widthX="([\d.]+)pt"',
                    xml).groups(), ("INSIDEFRAME", "0.5"))
# The code overflowed the frame once, on every layout at once, because its
# ceiling was set from a clearance that had been reasoned about rather than
# measured. Check the thing that actually matters -- the gap between the two
# boxes -- on every layout and not just on the one the eye happens to be on.
for key in ("minimal", "standard", "rowmap"):
    b_k, mm_k = labels.render(key, sample(), created="x")
    x_k = zipfile.ZipFile(io.BytesIO(b_k)).read("label.xml").decode()
    pf = [float(v) for v in re.search(
        f'<{PLATE}><pt:objectStyle x="([\d.]+)pt" y="([\d.]+)pt"'
        r' width="([\d.]+)pt" height="([\d.]+)pt"', x_k).groups()]
    pq = [float(v) for v in re.search(
        r'<barcode:barcode><pt:objectStyle x="([\d.]+)pt" y="([\d.]+)pt"'
        r' width="([\d.]+)pt" height="([\d.]+)pt"', x_k).groups()]
    gaps = (pq[0] - pf[0], pq[1] - pf[1],
            (pf[0] + pf[2]) - (pq[0] + pq[2]), (pf[1] + pf[3]) - (pq[1] + pq[3]))
    check_true(f"  {key}: the code clears the plate on all four sides",
               min(gaps) >= labels.FRAME_PAD - 0.05,
               "left %.1f top %.1f right %.1f bottom %.1f, need %.1f"
               % (*gaps, labels.FRAME_PAD))
    # and its LEFT gap equals its vertical one, so it reads as a square cell
    # centred in the frame rather than a code pushed into a corner
    check(f"  {key}: the same gap on the left as above and below",
          (round(gaps[0], 1), round(gaps[1], 1)),
          (round(gaps[3], 1), round(gaps[3], 1)))

# The version is pinned rather than left on "auto". Our capacity table is
# byte mode, and a payload carrying "1234455678" would encode smaller in
# numeric mode -- so on "auto" P-touch could draw a smaller symbol than the
# box computed for it, and every clearance worked out here would be wrong by
# an unknowable amount. Proven to be accepted: a file written with
# version="9" opened, and its symbol sat exactly on the box edges.
check("the version is pinned, not left to the encoder",
      re.search(r'<barcode:qrcodeStyle[^>]*version="([^"]+)"', xml).group(1),
      str((int(re.search(r'<barcode:barcode><pt:objectStyle[^>]*width="([\d.]+)pt"',
                         xml).group(1).split(".")[0]) // 1) and
          (round(float(re.search(r'<barcode:barcode><pt:objectStyle[^>]*width="([\d.]+)pt"',
                                 xml).group(1)) / labels.QR_CELL_PT) - 4 - 17) // 4))

# Whatever the plate, no rectangle may claim a rounded corner. The attribute
# does nothing, and copying Brother's habit of filling it with 25% of the
# shorter side is what sent this the wrong way twice.
check("no rectangle pretends to be rounded",
      set(re.findall(r'roundness[XY]="([\d.]+)pt"', xml)) - {"0"}, set())

# Brother's own vertical rules -- twelve of the fifty in the library -- put
# both points on the box's centre line, half the BOX width in from each end,
# and the box is a tenth of a point wider than the pen. Copied, not deduced.
rule = re.search(r'<draw:poly>.*?</draw:poly>', xml, re.S).group(0)
rx, ry, rw, rh = [float(v) for v in re.search(
    r'x="([\d.]+)pt" y="([\d.]+)pt" width="([\d.]+)pt" height="([\d.]+)pt"',
    rule).groups()]
(px0, py0), (px1, py1) = [tuple(float(v[:-2]) for v in pair.split(","))
                          for pair in re.search(r'points="([^"]+)"',
                                                rule).group(1).split()]
check("the rule's two points share one x", px0, px1)
check("which is the box centre line", round(px0 - rx, 2), round(rw / 2, 2))
check("inset half a box width at the top", round(py0 - ry, 2), round(rw / 2, 2))
check("and at the bottom", round(ry + rh - py1, 2), round(rw / 2, 2))
check("the box is a tenth wider than the pen", rw, 0.6)

BROTHER = (r"C:\Program Files (x86)\Brother\Ptedit54\LayoutStyle\RDRoll"
           r"\Large Shipping Label\Shipping 1.lbx")
if os.path.exists(BROTHER):
    ref = zipfile.ZipFile(BROTHER).read("label.xml").decode("utf-8")
    ref_rule = [m.group(0) for m in re.finditer(r'<draw:poly>.*?</draw:poly>',
                                                ref, re.S)
                if float(re.search(r'height="([\d.]+)pt"', m.group(0)).group(1))
                > float(re.search(r'width="([\d.]+)pt"', m.group(0)).group(1))][0]
    for tag in ("draw:polyStyle", "pt:pen", "pt:brush"):
        want = dict(re.findall(r'(\w+)="([^"]*)"',
                               re.search(rf"<{tag} ([^>]*?)/?>", ref_rule).group(1)))
        got = dict(re.findall(r'(\w+)="([^"]*)"',
                              re.search(rf"<{tag} ([^>]*?)/?>", rule).group(1)))
        drift = {k: (want[k], got.get(k)) for k in want if got.get(k) != want[k]}
        check(f"  {tag} matches Brother's vertical rule", drift, {})
else:
    print("  --   Brother's template library is not on this machine")

print("\nthe barcode object, against one P-touch wrote itself")
# The barcode object had never been diffed against anything -- the check
# above only covers the Thai text object -- and that is how anchor="TOPLEFT"
# survived on it. The right reference is not one of our own files but
# Brother's, whose library contains a QR that P-touch itself wrote.
BQR = (r"C:\\Program Files (x86)\\Brother\\Ptedit54\\LayoutStyle\\RDRoll"
       r"\\Continuous Length Paper and Film Tape\\Continuous 5.lbx")
if os.path.exists(BQR):
    bref = zipfile.ZipFile(BQR).read("label.xml").decode("utf-8")
    ours = re.search(r"<barcode:barcode>.*?</barcode:barcode>", xml, re.S).group(0)
    theirs = re.search(r"<barcode:barcode>.*?</barcode:barcode>", bref, re.S).group(0)
    # Excluded on purpose, on top of geometry and identity: the character
    # set (they encode Shift-JIS, we let P-touch decide), the error
    # correction and cell size, which fit_qr picks per payload, and the
    # check digit, which QR does not have. And `style`: Brother strokes a
    # 0.5 pt border INSIDEFRAME round the barcode box, which is the outer
    # edge of the quiet zone -- our pen is NULL, and a quiet zone with
    # nothing in it is the one thing a scanner is entitled to.
    MINE = {"x", "y", "width", "height", "ID", "objectName", "mbcs",
            "eccLevel", "cellSize", "checkDigit", "templateMergeTarget",
            "templateMergeType", "templateMergeID", "style", "version"}

    def _bat(o):
        d = {}
        for tag in re.findall(r"<[a-z:]+[^>]*/?>", o):
            n = re.match(r"<([a-z:]+)", tag).group(1)
            for k, v in re.findall(r'(\w+)="([^"]*)"', tag):
                if k not in MINE:
                    d[f"{n}.{k}"] = v
        return d
    a, b = _bat(theirs), _bat(ours)
    drift = {k: (a[k], b.get(k)) for k in a if b.get(k) != a[k]}
    check("our QR matches the one P-touch wrote, attribute for attribute",
          drift, {})
else:
    print("  --   Brother's library is not on this machine")

# The anchor says where the content sits inside its box. A barcode is the
# one object whose rendered size P-touch decides for itself, so it is the
# one object that must be CENTER: anything else and the slack all falls on
# one side. Brother does exactly this -- every text and drawn object TOPLEFT,
# both barcodes CENTER.
check("the code is centred inside its box",
      re.search(r'<barcode:barcode><pt:objectStyle[^>]*anchor="(\w+)"',
                xml).group(1), "CENTER")
check("and everything else is anchored top-left",
      set(re.findall(r'<(?:text:text|draw:rect|draw:poly)><pt:objectStyle'
                     r'[^>]*anchor="(\w+)"', xml)), {"TOPLEFT"})

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
    sys.exit(1)
print("ALL PASS")
