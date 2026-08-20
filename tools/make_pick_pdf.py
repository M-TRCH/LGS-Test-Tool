"""Render the pick-sequence brief as a PDF in the site report's style."""
import sys

from fpdf import FPDF
from fpdf.enums import TableCellFillMode
from fpdf.fonts import FontFace

from app.report_pdf import ACCENT, MUTED, ZEBRA, _first_existing, \
    _FONT_BOLD, _FONT_REGULAR

OUT = sys.argv[1] if len(sys.argv) > 1 else "lgs-pick-sequence.pdf"
GATEWAY = "192.168.0.99:502"
SLOT = 11


def clean(text: str) -> str:
    """Backticks are not markdown fpdf understands, and the report font has
    no arrow glyphs — a dropped glyph would silently eat the meaning."""
    return (text.replace("`", "")
                .replace("→", "->").replace("←", "<-")
                .replace("≥", ">=").replace("≤", "<=")
                .replace("⚠️", "!"))


class Doc(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", format="A4")
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(True, margin=14)
        regular = _first_existing(_FONT_REGULAR)
        bold = _first_existing(_FONT_BOLD)
        self.add_font("site", "", regular)
        self.add_font("site", "B", bold or regular)

    def font(self, size: float, bold: bool = False) -> None:
        self.set_font("site", "B" if bold else "", size)

    def footer(self) -> None:
        self.set_y(-10)
        self.font(7)
        self.set_text_color(120)
        self.cell(0, 5, f"page {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(0)


def section(pdf: Doc, step: int, title: str) -> None:
    """A numbered step. The circled digits (U+2460…) are not in Leelawadee UI —
    a dropped glyph would leave the steps unnumbered, so the badge is drawn."""
    pdf.ln(3.0)
    y = pdf.get_y()
    d = 6.2
    pdf.set_fill_color(*ACCENT)
    pdf.ellipse(pdf.l_margin, y + 0.4, d, d, style="F")
    pdf.set_text_color(255)
    pdf.font(9, bold=True)
    pdf.set_xy(pdf.l_margin, y + 1.6)
    pdf.cell(d, 4, str(step), align="C")
    pdf.set_fill_color(255)
    pdf.set_xy(pdf.l_margin + d + 2.5, y)
    pdf.font(12, bold=True)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 7, clean(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    pdf.ln(0.8)


def table(pdf: Doc, widths, aligns, head, rows) -> None:
    pdf.font(8)
    with pdf.table(col_widths=widths, text_align=aligns, markdown=True,
                   headings_style=FontFace(emphasis="BOLD", color=255,
                                           fill_color=ACCENT),
                   cell_fill_color=ZEBRA, cell_fill_mode=TableCellFillMode.ROWS,
                   borders_layout="MINIMAL", line_height=5.0,
                   padding=1.0) as t:
        row = t.row()
        for title in head:
            row.cell(clean(title), align="CENTER")
        for cells in rows:
            row = t.row()
            for cell in cells:
                row.cell(clean(cell))


def bullets(pdf: Doc, items) -> None:
    pdf.ln(1.0)
    pdf.font(7.5)
    for item in items:
        pdf.set_x(pdf.l_margin + 1.5)
        pdf.multi_cell(0, 4.4, clean("• " + item), markdown=True,
                       new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.4)


pdf = Doc()
pdf.alias_nb_pages()
pdf.add_page()

# ── title ──────────────────────────────────────────────────────────────────
pdf.font(16, bold=True)
pdf.set_text_color(*ACCENT)
pdf.cell(0, 9, "LGS — ลำดับคำสั่งหยิบยา", new_x="LMARGIN", new_y="NEXT")
pdf.font(9)
pdf.set_text_color(90)
pdf.cell(0, 5, "สำหรับทีม Programmer", new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0)

# ── connection box ─────────────────────────────────────────────────────────
pdf.ln(2)
y0 = pdf.get_y()
pdf.set_fill_color(238, 243, 248)
pdf.set_draw_color(*ACCENT)
pdf.set_line_width(0.3)
pdf.font(8)
pdf.set_x(pdf.l_margin)
pdf.multi_cell(0, 4.8, clean(
    "**การเชื่อมต่อ:** Modbus TCP -> เกตเวย์ " + GATEWAY
    + "  ·  **Unit ID = รหัสช่อง** (แถว×10+ช่อง)\n"
    "**Timeout >= 3 วินาที หรือ retry >= 1** — คำขอแรกหลังสลับแถวข้ามช่องฮับ "
    "RS485 ใช้เวลา ~2.6 วิ (เกตเวย์จัดการเอง)\n"
    f"**ตัวอย่างทั้งเอกสาร:** ช่อง **{SLOT}** (แถว 1 ช่อง 1)  ·  หยิบ **5** กล่อง  ·  ไฟ preset 1"),
    markdown=True, fill=True, border=1, new_x="LMARGIN", new_y="NEXT")

# ── 1 ──────────────────────────────────────────────────────────────────────
section(pdf, 1, "สั่งหยิบยา (เลข + จอ + ไฟ + กลอน)")
table(pdf, (13, 43, 19, 51, 60),
      ("CENTER", "LEFT", "CENTER", "LEFT", "LEFT"),
      ("ลำดับ", "คำสั่ง", "Address", "ตัวอย่างจริง", "ความหมาย"),
      [("1", "FC06 Write Register", "60", f"unit={SLOT}, reg 60 <- 5",
        "เลขขึ้นจอ 0-99 (เกินถูก clamp เป็น 99)"),
       ("2", "FC03 Read Register", "18", f"unit={SLOT}, reg 18 -> 41",
        "จด baseline ตัวนับปุ่ม (สมมุติอ่านได้ 41)"),
       ("3", "FC05 Write Coil", "1031", f"unit={SLOT}, coil 1031 <- ON",
        "คำสั่งเดียว: ไฟ preset 1 + จอแสดงเลข + ยิงกลอน")])
bullets(pdf, [
    "สี preset 2-8 -> coil **1032**-**1038**  ·  ไม่เอากลอน -> coil **1011**-**1018** "
    "(ยิงกลอนทีหลังด้วย coil **1020**)",
    "กลอนเป็นแบบ Safety: ยิง**เฉพาะเมื่อกลอนล็อกอยู่** (reg 41 = 1)  ·  "
    "pulse 300-500 ms  ·  ยิงซ้ำต้องห่าง >= 2 วิ",
    "สั่งหลายช่องพร้อมกัน: เว้นจังหวะช่องละ ~800 ms (จำกัดกระแสพีคของโซลินอยด์)",
])

# ── 2 ──────────────────────────────────────────────────────────────────────
section(pdf, 2, "รอเช็คปุ่ม + กลอน (poll ทุก 1-2 วิ)")
table(pdf, (26, 40, 19, 41, 60),
      ("LEFT", "LEFT", "CENTER", "LEFT", "LEFT"),
      ("เฝ้าดู", "คำสั่ง", "Address", "ตัวอย่างจริง", "เงื่อนไขผ่าน"),
      [("ปุ่มยืนยัน", "FC03 Read Register", "18", f"unit={SLOT}, reg 18 -> 42",
        "(42-41) & 0xFFFF >= 1 = กดแล้ว"),
       ("ลิ้นชักเปิด", "FC03 Read Register", "41", f"unit={SLOT}, reg 41 -> 0",
        "1->0 = กลอนปลด/ลิ้นชักเปิด (กำลังหยิบยา)"),
       ("ลิ้นชักปิดกลับ", "FC03 Read Register", "41", f"unit={SLOT}, reg 41 -> 1",
        "0->1 = ปิดเรียบร้อย")])
bullets(pdf, [
    "reg 18 เป็น**ตัวนับ** (การกด ~200 ms สั้นกว่ารอบ poll — ค่าสถานะเฉยๆ จะพลาด)  ·  "
    "นับเฉพาะโหมด RUN",
    "**ทำไมต้องลบด้วย & 0xFFFF:** reg 18 เป็น u16 นับขึ้นแล้ว**วนรอบ** (65535 -> 0)  ·  "
    "ถ้าตัวนับวนพอดีช่วงที่กำลังรอ การลบตรงๆ จะได้ค่าติดลบ เช่น baseline = 65535 "
    "แล้วอ่านใหม่ได้ 1: ผลลบตรงๆ = -65534 (ผิด) แต่ (1 - 65535) & 0xFFFF = 2 "
    "(ถูก คือกด 2 ครั้ง)  ·  สูตรนี้ให้ผลถูกเสมอ ตราบใดที่กดไม่เกิน 65535 ครั้งระหว่างรอบ poll",
    "โมดูลกะพริบแหวนสี preset รับทราบการกดเอง — แต่**ไฟไม่ดับเอง** "
    "การดับคือสัญญาณ “ระบบรับรายการแล้ว” จาก server",
    "เสริม: reg 40 = วินาทีตั้งแต่ปลดล็อก (ใช้เตือน “เปิดค้างนาน”)  ·  "
    "ช่องไม่มีกลอน: ข้ามการรอ reg 41",
])

# ── 3 ──────────────────────────────────────────────────────────────────────
section(pdf, 3, "จบรายการ (ปิดไฟ + จอ)")
table(pdf, (13, 43, 19, 51, 60),
      ("CENTER", "LEFT", "CENTER", "LEFT", "LEFT"),
      ("ลำดับ", "คำสั่ง", "Address", "ตัวอย่างจริง", "ความหมาย"),
      [("1", "FC05 Write Coil", "1011", f"unit={SLOT}, coil 1011 <- OFF",
        "ดับทั้งวงแหวนและจอในคำสั่งเดียว")])
bullets(pdf, [
    "**ข้อควรระวัง — กติกาคู่ mirror:** เปิดด้วย **1031**/**1011** ต้องปิดที่ **1011** — "
    "ปิดด้วย 1001 จอจะค้าง  ·  ใช้ preset n ปิดที่ **101n**",
    "ทางลัดล้างทุกอย่างของช่อง: coil **511** <- ON "
    "(All Off: ไฟ+จอ+เคลียร์ coil preset ทั้งหมด)",
])

# ── 4 ──────────────────────────────────────────────────────────────────────
section(pdf, 4, "กันช่องดับเงียบ (ต้องทำ)")
table(pdf, (34, 40, 19, 33, 60),
      ("LEFT", "LEFT", "CENTER", "LEFT", "LEFT"),
      ("เฝ้าดู", "คำสั่ง", "Address", "ตัวอย่างจริง", "ถ้าพบให้ทำ"),
      [("โมดูลรีบูตหรือยัง", "FC03 Read Register", "7",
        f"unit={SLOT}, reg 7 -> 139", "ค่าเปลี่ยนจากที่จำไว้ = รีบูต"),
       ("ไฟยังติดอยู่ไหม", "FC03 Read Register", "11",
        f"unit={SLOT}, reg 11 -> 0", "เป็น 0 ทั้งที่สั่งให้ติด = ดับแล้ว"),
       ("แก้", "FC06 + FC05", "60 / 1031",
        "เขียนเลข + coil ใหม่", "สั่งซ้ำชุดเดิม ช่องกลับมาสว่าง")])
bullets(pdf, [
    "**ทำไมต้องมี:** ไฟตกที่ตู้ทำให้โมดูลรีบูต วงแหวนกับจอดับและ**ไม่กลับมาเอง** "
    "แต่การอ่านค่ายังสำเร็จทุกครั้ง — ระบบจึงไม่มีทางรู้ว่าช่องมืดไปแล้ว "
    "(วัดจริงที่หน้างาน: คืนเดียว 225 ครั้ง)",
    "reg 7 กับ reg 11 อยู่ในบล็อกเดียวกับที่อ่านอยู่แล้ว (reg 0-11) — "
    "อ่านเพิ่มไม่เสียรอบ poll",
    "ทำครั้งเดียวได้ผลถาวร: ต่อให้ระบบไฟที่ตู้ถูกแก้แล้ว ไฟกระพริบที่หน้างานจริง"
    "ก็ยังเกิดได้เสมอ",
])

# ── footer note ────────────────────────────────────────────────────────────
pdf.ln(3)
pdf.font(6.5)
pdf.set_text_color(*MUTED)
pdf.multi_cell(0, 3.8, clean(
    "อ้างอิง: LGS-Control-Table.md  ·  module fw >= v3.3.0, gateway fw >= v1.12.0  ·  2026-08-14"),
    new_x="LMARGIN", new_y="NEXT")

pdf.output(OUT)
print("wrote", OUT)
