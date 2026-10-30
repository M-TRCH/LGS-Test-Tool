"""A picture of a .lbx for the Labels page.

Drawn from the very label.xml that gets downloaded, so what is shown is the
geometry and text that will be printed. Two honest limits: the QR is a
placeholder block at the right size (the printer software generates the real
symbol and this tool carries no QR encoder), and the font is whatever the
browser has, not Brother's rendering.
"""
import io
import zipfile
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

_NS = {"pt": "http://schemas.brother.info/ptouch/2007/lbx/main",
       "style": "http://schemas.brother.info/ptouch/2007/lbx/style",
       "text": "http://schemas.brother.info/ptouch/2007/lbx/text",
       "draw": "http://schemas.brother.info/ptouch/2007/lbx/draw",
       "barcode": "http://schemas.brother.info/ptouch/2007/lbx/barcode"}


def _pt(v: str) -> float:
    return float(str(v).replace("pt", "") or 0)


def _box(style) -> tuple:
    return _pt(style.get("x")), _pt(style.get("y")), _pt(style.get("width")), _pt(style.get("height"))


def _qr_block(x: float, y: float, w: float, h: float) -> str:
    """Finder-pattern look-alike so it reads as a QR without pretending to be one."""
    n, cell = 25, w / 25
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#bbb" stroke-width=".4" stroke-dasharray="2 1.5"/>']
    for fx, fy in ((0, 0), (n - 7, 0), (0, n - 7)):
        X, Y = x + fx * cell, y + fy * cell
        out.append(f'<rect x="{X:.2f}" y="{Y:.2f}" width="{7 * cell:.2f}" height="{7 * cell:.2f}" fill="#111"/>'
                   f'<rect x="{X + cell:.2f}" y="{Y + cell:.2f}" width="{5 * cell:.2f}" height="{5 * cell:.2f}" fill="#fff"/>'
                   f'<rect x="{X + 2 * cell:.2f}" y="{Y + 2 * cell:.2f}" width="{3 * cell:.2f}" height="{3 * cell:.2f}" fill="#111"/>')
    seed = 7
    for r in range(n):
        for c in range(n):
            if (r < 8 and (c < 8 or c >= n - 8)) or (r >= n - 8 and c < 8):
                continue
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            if seed & 0x10000:
                out.append(f'<rect x="{x + c * cell:.2f}" y="{y + r * cell:.2f}" width="{cell:.2f}" height="{cell:.2f}" fill="#111"/>')
    return "".join(out)


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
            parts.append(_qr_block(x, y, w, h))
        elif tag == "text":
            data = el.find("pt:data", _NS)
            fx = el.find("text:ptFontInfo/text:fontExt", _NS)
            lf = el.find("text:ptFontInfo/text:logFont", _NS)
            al = el.find("text:textAlign", _NS)
            size = _pt(fx.get("size")) if fx is not None else 9
            bold = lf is not None and int(lf.get("weight", "400")) >= 600
            ha = (al.get("horizontalAlignment") if al is not None else "LEFT")
            anchor, tx = {"CENTER": ("middle", x + w / 2), "RIGHT": ("end", x + w)}.get(ha, ("start", x))
            lines = (data.text or "").split("\n")
            for i, ln in enumerate(lines):
                parts.append(f'<text x="{tx:.1f}" y="{y + size * (0.85 + 1.15 * i):.1f}" font-size="{size}" text-anchor="{anchor}" '
                             f'font-weight="{700 if bold else 400}" font-family="IBM Plex Sans Thai,IBM Plex Sans,Arial,sans-serif" '
                             f'fill="#111" textLength="{min(w, max(1, len(ln) * size * 0.62)):.1f}" lengthAdjust="spacingAndGlyphs">{escape(ln)}</text>'
                             if len(ln) * size * 0.62 > w else
                             f'<text x="{tx:.1f}" y="{y + size * (0.85 + 1.15 * i):.1f}" font-size="{size}" text-anchor="{anchor}" '
                             f'font-weight="{700 if bold else 400}" font-family="IBM Plex Sans Thai,IBM Plex Sans,Arial,sans-serif" fill="#111">{escape(ln)}</text>')
    parts.append("</svg>")
    return "".join(parts)
