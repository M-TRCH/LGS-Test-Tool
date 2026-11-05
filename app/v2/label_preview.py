"""A picture of a .lbx for the Labels page.

Drawn from the very label.xml that gets downloaded, so what is shown is the
geometry and text that will be printed:

* the QR is the real symbol, encoded here with the version and error
  correction the file asks for (segno), not a stand-in;
* text is placed the way the editor places it: the object's top edge plus the
  font's own ascent, drawn in the font the file names, never squeezed. The
  ascent comes from the font file itself when this machine has it (Windows
  ships Arial and Browallia New);
* what stays approximate: the editor's own renderer and the font on the device
  that views the page. A phone has no Browallia New, so it shows a close
  stand-in at the true position.
"""
import io
import os
import zipfile
from functools import lru_cache
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

_NS = {"pt": "http://schemas.brother.info/ptouch/2007/lbx/main",
       "style": "http://schemas.brother.info/ptouch/2007/lbx/style",
       "text": "http://schemas.brother.info/ptouch/2007/lbx/text",
       "draw": "http://schemas.brother.info/ptouch/2007/lbx/draw",
       "barcode": "http://schemas.brother.info/ptouch/2007/lbx/barcode"}

_ECC = {"7%": "l", "15%": "m", "25%": "q", "30%": "h"}
_FALLBACK = "IBM Plex Sans Thai,IBM Plex Sans,Arial,sans-serif"


def _pt(v: str) -> float:
    return float(str(v).replace("pt", "") or 0)


def _box(style) -> tuple:
    return _pt(style.get("x")), _pt(style.get("y")), _pt(style.get("width")), _pt(style.get("height"))


# ── QR ────────────────────────────────────────────────────────────────────────
def _qr_placeholder(x: float, y: float, w: float, h: float) -> str:
    """Only when the symbol cannot be encoded (segno missing, data too long)."""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#bbb" stroke-width=".4" '
            f'stroke-dasharray="2 1.5"/><text x="{x + w / 2:.1f}" y="{y + h / 2:.1f}" font-size="5" text-anchor="middle" '
            f'fill="#888">QR</text>')


def _qr_symbol(el, x: float, y: float, w: float, h: float) -> str:
    """The real module matrix, one <path>, inside the object's box.

    The file states model, error correction and version, so asking for exactly
    those gives the symbol the editor would draw (same size and density). The
    box includes two modules of quiet zone on each side."""
    try:
        import segno
        data = el.find("pt:data", _NS)
        qs = el.find("barcode:qrcodeStyle", _NS)
        text = (data.text or "") if data is not None else ""
        ecc = _ECC.get(qs.get("eccLevel", "25%"), "q") if qs is not None else "q"
        version = int(qs.get("version")) if qs is not None and qs.get("version") else None
        q = segno.make(text, error=ecc, version=version, boost_error=False, micro=False, encoding="utf-8")
        m = [list(row) for row in q.matrix]
    except Exception:                                            # noqa: BLE001
        return _qr_placeholder(x, y, w, h)
    n = len(m)
    cell = w / (n + 4)
    ox, oy = x + 2 * cell, y + (h - n * cell) / 2
    runs = []
    for r, row in enumerate(m):
        c = 0
        while c < n:
            if row[c]:
                s = c
                while c < n and row[c]:
                    c += 1
                runs.append(f"M{ox + s * cell:.3f} {oy + r * cell:.3f}h{(c - s) * cell:.3f}v{cell:.3f}h-{(c - s) * cell:.3f}z")
            else:
                c += 1
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff"/>'
            f'<path d="{"".join(runs)}" fill="#000" shape-rendering="crispEdges"/>')


# ── text ──────────────────────────────────────────────────────────────────────
@lru_cache(maxsize=None)
def _vmetrics(font: str, weight: int):
    """(unitsPerEm, winAscent, winDescent) of the face on this machine, or None.
    GDI cell height is winAscent + winDescent, which is what the editor lays a
    text object out with."""
    try:
        from .. import labels
        entry = labels._FONT_FILES.get((font, weight)) or labels._FONT_FILES.get((font, 400))
        if not entry:
            return None
        name, index = entry
        path = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name)
        if not os.path.exists(path):
            return None
        from fontTools.ttLib import TTCollection, TTFont
        f = TTCollection(path).fonts[index] if path.lower().endswith(".ttc") else TTFont(path)
        os2 = f["OS/2"]
        return f["head"].unitsPerEm, os2.usWinAscent, os2.usWinDescent
    except Exception:                                            # noqa: BLE001
        return None


def _text_objects(el, x: float, y: float, w: float) -> list:
    data = el.find("pt:data", _NS)
    fx = el.find("text:ptFontInfo/text:fontExt", _NS)
    lf = el.find("text:ptFontInfo/text:logFont", _NS)
    al = el.find("text:textAlign", _NS)
    size = _pt(fx.get("size")) if fx is not None else 9
    face = lf.get("name", "Arial") if lf is not None else "Arial"
    weight = 700 if (lf is not None and int(lf.get("weight", "400")) >= 600) else 400
    ha = al.get("horizontalAlignment") if al is not None else "LEFT"
    anchor, tx = {"CENTER": ("middle", x + w / 2), "RIGHT": ("end", x + w)}.get(ha, ("start", x))
    vm = _vmetrics(face, weight)
    if vm:
        upm, asc, desc = vm
        ascent, pitch = size * asc / upm, size * (asc + desc) / upm
    else:                                                        # no font file here: the old estimate
        ascent, pitch = size * 0.85, size * 1.15
    out = []
    for i, ln in enumerate((data.text or "").split("\n")):
        out.append(f'<text x="{tx:.2f}" y="{y + ascent + i * pitch:.2f}" font-size="{size}" text-anchor="{anchor}" '
                   f'font-weight="{weight}" font-family="{escape(face)},{_FALLBACK}" fill="#000" '
                   f'xml:space="preserve">{escape(ln)}</text>')
    return out


def svg_from_lbx(blob: bytes) -> str:
    root = ET.fromstring(zipfile.ZipFile(io.BytesIO(blob)).read("label.xml"))
    paper = root.find(".//style:paper", _NS)
    tape, length = _pt(paper.get("width")), _pt(paper.get("height"))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {length:.1f} {tape:.1f}" role="img" '
             f'style="width:100%;height:auto;background:#fff;border-radius:4px;display:block">',
             f'<rect width="{length:.1f}" height="{tape:.1f}" fill="#fff"/>']
    objs = root.find(".//pt:objects", _NS)
    for el in objs:
        tag = el.tag.split("}")[1]
        st = el.find("pt:objectStyle", _NS)
        if st is None:
            continue
        x, y, w, h = _box(st)
        if tag == "frame":
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="#111" stroke-width=".7"/>')
        elif tag == "rect":
            pen = _pt(st.find("pt:pen", _NS).get("widthX"))
            parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#111" stroke-width="{pen}"/>')
        elif tag == "poly":
            parts.append(f'<line x1="{x + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y + h}" stroke="#111" stroke-width=".5"/>')
        elif tag == "barcode":
            parts.append(_qr_symbol(el, x, y, w, h))
        elif tag == "text":
            parts.extend(_text_objects(el, x, y, w))
    parts.append("</svg>")
    return "".join(parts)
