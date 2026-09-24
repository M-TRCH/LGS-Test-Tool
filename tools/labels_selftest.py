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
from app import labels                                         # noqa: E402

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
check("a short payload takes the strongest EC that fits", ecc, "q")
check("the box is (modules + 4) * cell, quiet zone included", side,
      round((mods + 4) * labels.QR_CELL_PT, 1))
check_true("the symbol stays inside the cap", side <= labels.QR_MAX_SIDE_PT,
           f"{side} <= {labels.QR_MAX_SIDE_PT}")
check_true("which clears the tape edge better than the old 1.6 pt symbol",
           (labels.TAPE_PT - side) / 2 > 4.4,
           f"{(labels.TAPE_PT - side) / 2:.1f} pt vs 4.4")
_, _, ecc_long = labels.fit_qr("x" * 120)
check("a longer payload drops the error correction rather than the fit",
      ecc_long, "l")
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
check("the QR sits inside the frame, not on the paper edge",
      re.search(r'<barcode:barcode><pt:objectStyle x="([\d.]+)pt"', xml).group(1),
      "15.9")
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
check("10 rows make a 112 mm label", round(mm), 112)
check("7 rows make a shorter one",
      round(labels.render("rowmap", sample(rows=rows_for("0", "8,8,8,8,8,8,8",
                                                       "1,2,3,4,5,6,7")),
                          created="x")[1]), 101)

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
_five = round(labels.render("minimal", sample(rows=rows_for("0", "8,8,8,8,8",
                                                            "1,2,3,4,5")),
                            created="x")[1])
check_true("a five-row cabinet gives a slightly shorter label",
           _five < round(mini_mm), f"{_five} mm vs {round(mini_mm)} mm")
check_true("but only slightly", round(mini_mm) - _five <= 4,
           f"{round(mini_mm) - _five} mm")
# 28 Thai characters are 82 bytes in UTF-8. That used to be more than the
# whole 78-byte code; at 1.2 pt it would fit on its own, but not beside the
# identity and the shape, so the site name is still printed and not encoded.
_together = len(WARD.encode("utf-8")) + len(sample().qr_payload().encode("utf-8")) + 1
check_true("the site name will not fit beside the rest",
           _together > labels.QR_MAX_BYTES,
           f"{_together} B > {labels.QR_MAX_BYTES}")

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

print("\nthe frame and the rule, against Brother's own template library")
for key in ("minimal", "standard", "rowmap"):
    b_k, _ = labels.render(key, sample(), created="x")
    x_k = zipfile.ZipFile(io.BytesIO(b_k)).read("label.xml").decode()
    check(f"  {key} has exactly one frame", len(re.findall(r"<draw:rect>", x_k)), 1)
    check_true(f"  {key} has a rule beside the code", "<draw:poly>" in x_k)

# The frame has to stay inside the band the printer can actually mark. A
# calibration print put the first whole character at 1 pt from the top edge,
# so a line at 3 pt has something in hand -- which matters, because the last
# sticker came back with its top edge shaved.
fx, fy, fw, fh = [float(v) for v in re.search(
    r'<draw:rect><pt:objectStyle x="([\d.]+)pt" y="([\d.]+)pt"'
    r' width="([\d.]+)pt" height="([\d.]+)pt"', xml).groups()]
check_true("the frame clears both edges of the tape",
           fy >= labels.ACROSS_PT and fy + fh <= labels.TAPE_PT - labels.ACROSS_PT,
           f"y {fy}..{fy + fh}, band {labels.ACROSS_PT}..{labels.TAPE_PT - labels.ACROSS_PT}")
check_true("and both ends of the label",
           fx >= labels.EDGE_PT and fx + fw <= mm * labels.MM - labels.EDGE_PT,
           f"x {fx}..{fx + fw:.1f}")

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

print()
if FAILS:
    print(f"{len(FAILS)} FAILED: {', '.join(FAILS)}")
    sys.exit(1)
print("ALL PASS")
