"""Render the 2026-08-20/21 overnight soak findings as a one-brief PDF.

    python tools/make_soak_report_pdf.py [out.pdf]

Same visual language as the site report and the pick-sequence brief. The
numbers are this run's measurements, hardcoded on purpose: the document is a
record of what WAS measured, not a template.
"""
import sys

from fpdf import FPDF
from fpdf.enums import TableCellFillMode
from fpdf.fonts import FontFace

from app.report_pdf import ACCENT, MUTED, ZEBRA, _first_existing, \
    _FONT_BOLD, _FONT_REGULAR

OUT = sys.argv[1] if len(sys.argv) > 1 else "lgs-soak-report-20260821.pdf"


def clean(text: str) -> str:
    return (text.replace("`", "")
                .replace("→", "->").replace("←", "<-")
                .replace("≥", ">=").replace("≤", "<=")
                .replace("⊃", ">").replace("×", "x")
                .replace("≈", "~"))


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


def table(pdf: Doc, widths, aligns, head, rows, size=8.0) -> None:
    pdf.font(size)
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


def para(pdf: Doc, text: str, size=8.0) -> None:
    pdf.font(size)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 4.6, clean(text), markdown=True,
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(0.6)


def bullets(pdf: Doc, items, size=7.5) -> None:
    pdf.ln(0.6)
    pdf.font(size)
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
pdf.cell(0, 9, "LGS — ผล soak ข้ามคืน 20-21 ส.ค. 2569 และผลกระทบการใช้งานจริง",
         new_x="LMARGIN", new_y="NEXT")
pdf.font(9)
pdf.set_text_color(90)
pdf.cell(0, 5, "ตู้ทดสอบ 64 โมดูล · module v3.3.1 · gateway v1.12.1 · Test Tool v1.6.1",
         new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0)

pdf.ln(2)
pdf.set_fill_color(238, 243, 248)
pdf.set_draw_color(*ACCENT)
pdf.set_line_width(0.3)
pdf.font(8)
pdf.set_x(pdf.l_margin)
pdf.multi_cell(0, 4.8, clean(
    "**เงื่อนไขทดสอบ:** Modbus TCP ผ่านเกตเวย์ 192.168.0.202:502 · "
    "poll 64 โมดูลต่อรอบ (คาบจริง ~17.5 วิ) · เช็คตัวนับทุก 5 รอบ\n"
    "**ช่วงเวลา:** 20 ส.ค. 19:53 -> 21 ส.ค. 10:04  (14 ชม. 10 นาที · 2,913 รอบ · 186,380 การอ่าน)\n"
    "**ความสามารถใหม่ของรอบนี้:** ทุกแถว reboot ระบุสาเหตุจาก reg 8 ของโมดูลเอง "
    "(IWDG = ไฟตกจน CPU ค้าง / Power-on = ไฟดับจริง) พร้อมยืนยันไขว้กับตัวนับ IWDG สะสม"),
    fill=True, border=1, markdown=True, new_x="LMARGIN", new_y="NEXT")

# ── ① results ──────────────────────────────────────────────────────────────
section(pdf, 1, "ผลการทดสอบ — รีเซ็ต 441 ครั้ง / 15 เหตุการณ์ / เป็น IWDG ทั้งหมด")

para(pdf,
     "**fails = 0 ตลอด 14 ชั่วโมง** (ไม่มีการอ่านล้มเหลวแม้แต่ครั้งเดียว) ขณะที่โมดูลรีบูตรวม "
     "**441 ครั้ง** — สาเหตุจาก reg 8 เป็น **IWDG ทั้ง 441/441** ไม่มี Power-on แม้แต่ครั้งเดียว "
     "และตรงกับตัวนับ IWDG สะสมทุกรายการ (ไม่ขัดกันสักครั้ง)")

table(pdf,
      (8, 15, 20, 15, 18, 64),
      ("CENTER", "CENTER", "CENTER", "CENTER", "CENTER", "LEFT"),
      ("#", "เวลา", "สาขา", "ล้ม/32", "cause", "หมายเหตุ"),
      [("1", "20:44", "rows 6-10", "32", "IWDG", ""),
       ("2", "21:49", "rows 6-10", "32", "IWDG", ""),
       ("3", "22:30", "rows 6-10", "32", "IWDG", ""),
       ("4", "23:35", "rows 1-5", "**20**", "IWDG", "รอด 12 ตัว"),
       ("5", "00:15", "rows 1-5", "**31**", "IWDG", "รอดตัวเดียว: โมดูล 12"),
       ("6", "01:14", "rows 6-10", "32", "IWDG", ""),
       ("7", "01:55", "rows 6-10", "32", "IWDG", ""),
       ("8", "03:06", "rows 6-10", "32", "IWDG", ""),
       ("9", "03:35", "rows 6-10", "32", "IWDG", ""),
       ("10", "05:57", "rows 6-10", "**15**", "IWDG", "ครั้งเดียวที่แถวหลังล้มไม่ครบ"),
       ("11", "06:26", "rows 1-5", "**23**", "IWDG", "รอด 9 ตัว"),
       ("12", "07:36", "rows 1-5", "32", "IWDG", "แถวหน้าล้มยกสาขาครั้งแรก"),
       ("13", "07:42", "rows 6-10", "32", "IWDG", "ห่างข้อ 12 เพียง 6 นาที"),
       ("14", "09:44", "rows 6-10", "32", "IWDG", ""),
       ("15", "09:50", "rows 6-10", "32", "IWDG", "")],
      size=7.5)

bullets(pdf, [
    "**ทั้งสองสาขาคือความผิดปกติเดียวกัน** — แถวหน้า (rows 1-5) 4 เหตุการณ์ / แถวหลัง (rows 6-10) "
    "11 เหตุการณ์ สาเหตุ IWDG เหมือนกันหมด ต่างเพียงความถี่และความลึก ไม่ต้องตามหาปัญหาสองเรื่อง",
    "**เหตุการณ์ที่ล้มไม่ครบเรียงซ้อนกันสมบูรณ์**: ผู้รอด 12 ตัว > 9 ตัว > 1 ตัว > 0 ตัว "
    "(เซตย่อยของกันทุกชั้น ไม่มีข้อยกเว้น) — ลายเซ็นของ threshold แรงดันประจำบอร์ด "
    "ไม่ใช่จังหวะสุ่มหรือบั๊กซอฟต์แวร์ · **โมดูล 12 ทนสุดในตู้** / แถว 8-10 ล้มทุกครั้ง",
    "**เกิดทั้งคืนถึงสายวันทำงาน** ~ชั่วโมงละครั้ง (20:44 ถึง 09:50) — ไม่ใช่ปัญหาเฉพาะกลางคืน "
    "การไปวัดหน้างานทำได้ในเวลาทำการ",
    "**การทดลองควบคุม (20 ส.ค. 13:16):** ถอดปลั๊กจริงระหว่างทดสอบรอบสั้น -> โมดูลรายงาน "
    "cause=Power-on และตัวนับ IWDG ไม่ขยับ — พิสูจน์ว่าเครื่องมือแยก \"ไฟดับจริง\" ออกจาก "
    "\"ไฟตก\" ได้จริง และ 441 ครั้งของตู้ไม่ใช่ไฟดับ",
    "ประเด็นแยกเรื่อง: **โมดูล 12 กับ 13 อ่านช้า** (timeout+retry ~3.6 วิ) รวม 2,366 จาก 2,419 แถว slow "
    "— เป็นรูปแบบเดิมติดกัน 3 รอบทดสอบ น่าจะเป็นสาย/termination เฉพาะจุด ไม่เกี่ยวกับไฟตก",
])

# ── ② real-use impact ──────────────────────────────────────────────────────
pdf.add_page()
section(pdf, 2, "ผลกระทบเมื่อใช้งานจริง (ยา ~500 รายการ/วัน)")

para(pdf,
     "หนึ่งรอบรีเซ็ตต่อโมดูล = ค้างรอ watchdog **~4.0 วิ** + บูตกลับ **~0.4 วิ** (วัดจริง) "
     "= หายจากระบบ **~4.5 วิ/ครั้ง** — สั้นพอที่ timeout 3.5 วิ + retry 1 ครั้งจะข้ามผ่านได้เสมอ "
     "(นี่คือเหตุที่ fails = 0)")

table(pdf,
      (46, 34, 30, 30),
      ("LEFT", "CENTER", "CENTER", "CENTER"),
      ("สถานะโมดูลขณะเกิดเหตุ", "ที่ผู้ใช้เห็น", "ความถี่", "ระดับผลกระทบ"),
      [("**สแตนด์บาย** (ไฟยังไม่เปิด)", "ไม่เห็นอะไรเลย", "441 ครั้ง/คืน", "แทบเป็นศูนย์"),
       ("**กำลังเปิดไฟรอหยิบยา**\n(30 วิ - 2 นาที/รายการ)", "**ไฟดับคามือ ไม่ติดกลับเอง**",
        "~2-8 รายการ/วัน", "**สูง — เห็นชัด**")],
      size=8.0)

para(pdf,
     "โอกาสที่รายการหนึ่งถูกตัดกลางคัน = อัตราเหตุการณ์ของสาขา x เวลาที่ไฟเปิดรอ "
     "(อัตราวัดจริง: แถวหน้า 0.23 ครั้ง/ชม. · แถวหลัง 0.74 ครั้ง/ชม.):")

table(pdf,
      (40, 35, 35),
      ("CENTER", "CENTER", "CENTER"),
      ("เวลาหยิบต่อรายการ", "ช่องบน rows 1-5", "ช่องบน rows 6-10"),
      [("30 วินาที", "0.2 %", "0.6 %"),
       ("1 นาที", "0.4 %", "1.2 %"),
       ("2 นาที", "0.8 %", "**2.5 %**")])

para(pdf,
     "ที่ **500 รายการ/วัน** (เฉลี่ยรายการละ ~1 นาที กระจายทั้งตู้) คาดว่าจะโดนตัดกลางคัน "
     "**~4 รายการ/วัน (ช่วง 2-8)** — คือเภสัชกรเห็นไฟดับคามือแทบทุกวัน หลายครั้งต่อวัน "
     "และหนักขึ้นถ้ายาหมุนเร็วอยู่แถวหลัง")

bullets(pdf, [
    "**ไฟที่ดับไม่ติดกลับเอง** — โมดูลบูตขึ้นมาแบบทุกช่องดับ ค้างมืดจนกว่าเซิร์ฟเวอร์สั่งซ้ำ "
    "ถ้าไม่มีการเฝ้า ช่องจะมืดถาวรทั้งที่รายการยังเปิด -> เสี่ยงหยิบผิดช่อง",
    "**การกดยืนยันหายได้** — reg 18 นับตั้งแต่บูต รีบูตแล้วกลับเป็น 0 "
    "การกดที่คร่อมจังหวะรีเซ็ตพอดีจะไม่มีใครเห็น รายการค้าง",
    "availability เชิงบัสยังสูง (โมดูลแย่สุด ~99.90%) — ตัวเลขนี้จึงหลอกได้ "
    "ความเสียหายจริงอยู่ที่จังหวะ ไม่ใช่ปริมาณ",
])

# ── ③ remediation ──────────────────────────────────────────────────────────
section(pdf, 3, "แนวทางแก้ไข")

table(pdf,
      (26, 66, 30, 20),
      ("LEFT", "LEFT", "LEFT", "LEFT"),
      ("ระดับ", "สิ่งที่ทำ", "ผลที่ได้", "สถานะ"),
      [("**เซิร์ฟเวอร์**\n(ทำได้ทันที)",
        "ระหว่างรายการเปิดอยู่ ให้ poll **reg 11** (preset ที่ติดอยู่) ทุก 1-2 วิ "
        "เห็น 11 -> 0 ทั้งที่รายการยังไม่จบ = สั่งเปิดไฟ+จอซ้ำทันที",
        "ไฟดับเหลือ ~5-8 วิ แล้วติดกลับเอง จาก \"มืดถาวร\" เป็น \"กะพริบครั้งเดียว\"",
        "อยู่ในเอกสาร Programmer แล้ว — ยกระดับเป็นข้อบังคับ"),
       ("**เฟิร์มแวร์โมดูล**\n(ข้อเสนอ)",
        "IWDG reset ไม่ล้าง SRAM: เก็บสถานะไฟ+จอไว้ใน RAM (noinit, มี CRC) "
        "บูตแล้วถ้า cause=IWDG ให้จุดไฟเดิมคืนเอง (ไม่คืนกลอนเด็ดขาด, เคารพ max-on-time)",
        "ไฟวูบเพียง ~0.4 วิ โดยเซิร์ฟเวอร์ไม่ต้องทำอะไร · OTA ลงทั้งตู้ได้",
        "รอสั่ง"),
       ("**ฮาร์ดแวร์**\n(ต้นเหตุ)",
        "วัดแรงดันสาขา 24V rows 6-10 และ 3.3V บนบอร์ด ด้วย scope/logger จับค่า min "
        "ในเวลาทำการ (รอ ~1 ชม. ก็เจอ) · เทียบคู่: บอร์ดที่ล้มก่อน vs โมดูล 12 (ทนสุด) "
        "· เพิ่ม bulk capacitance / headroom ตามที่วัดได้ · ตรวจสายโมดูล 12,13 (เรื่อง slow แยกต่างหาก)",
        "แก้ที่ตัวปัญหาจริง",
        "งานหน้าตู้"),
       ("**ตัดออกแล้ว**",
        "ยก BOR level ทำไม่ได้ — STM32G070 (value line) ไม่มี BOR แบบตั้งค่าและไม่มี PVD "
        "(ตรวจ CMSIS header แล้ว: G071/G0B1 มีครบ, G070 ไม่มี) · ที่พอทำได้คือย่น IWDG 4 วิ -> 1 วิ "
        "(ต้องพิสูจน์บนโต๊ะก่อน)",
        "-", "-")],
      size=7.2)

para(pdf,
     "**สิ่งที่ติดตั้งไปแล้วและพิสูจน์ตัวเองในรอบนี้:** module v3.3.1 สถิติ 2 ช่อง A/B "
     "(ตัวนับรอดรีเซ็ตจริงทุกครั้ง ไม่มีเป็นศูนย์) · gateway v1.12.1 ย้ำเอาต์พุตทุก 5 วิ + log บัสเงียบ "
     "· Test Tool v1.6.1 ต่อลิงก์คืนเอง (พิสูจน์แล้ว 20 ส.ค.: หลุดแล้วกลับใน 2 วิ ไม่ค้าง) "
     "และจำแนกสาเหตุรีเซ็ตอัตโนมัติ", size=7.5)

# ── ④ conclusion ───────────────────────────────────────────────────────────
section(pdf, 4, "สรุปผล")

bullets(pdf, [
    "ตู้มีความผิดปกติของแหล่งจ่าย **หนึ่งเรื่อง**: แรงดันตกชั่วขณะ (sag) ถึงทั้งสองสาขา "
    "~ชั่วโมงละครั้ง ตลอดวัน — ลึกไม่เท่ากันต่อครั้ง บอร์ดแต่ละตัวมี threshold ของตัวเอง "
    "(หลักฐาน: ผู้รอดซ้อนกันสมบูรณ์ + IWDG ล้วน 441/441 + ไม่เคยเกิดพร้อมกันสองสาขา)",
    "**ไม่ใช่บั๊กเฟิร์มแวร์** (โมดูลที่ล้มกระจายทั่วลำดับ poll ไม่เกาะกลุ่มตามจังหวะเฟรม) "
    "และ **ไม่ใช่ไฟดับ** (ไม่มี Power-on แม้แต่ครั้งเดียว — เทียบกับการถอดปลั๊กจริงที่ขึ้น Power-on ทันที)",
    "ซอฟต์แวร์ทั้ง stack ตอนนี้ **ทนต่อเหตุการณ์และวัดมันได้เอง** — งานที่เหลือเป็นการวัดและแก้ไฟฟ้าหน้าตู้ "
    "ซึ่งทำได้ในเวลาทำการ ไม่ต้องเฝ้ากลางคืน",
    "ผลกระทบผู้ใช้เข้มข้นที่จังหวะเดียว: **ไฟดับคาการหยิบ ~2-8 รายการ/วัน** — ลดเหลือกะพริบเดียวได้ทันที "
    "ด้วยกติกา re-issue ฝั่งเซิร์ฟเวอร์ และลดจนแทบมองไม่เห็นด้วยข้อเสนอเฟิร์มแวร์จุดไฟคืน",
    "ระหว่างยังไม่แก้ไฟ: ตู้ใช้งานได้ โดยต้องมีกติกา re-issue เป็นข้อบังคับฝั่งเซิร์ฟเวอร์",
])

pdf.ln(2)
pdf.font(7)
pdf.set_text_color(*MUTED)
pdf.multi_cell(0, 4.0, clean(
    "ข้อมูล: soak-20260820-1953.csv (441 reboot / 441 watchdog / fails 0 / 186,380 การอ่าน) · "
    "การทดลองควบคุม: soak-20260820-1126.csv · ตัวนับสะสมอ่านจากบอร์ดยืนยันไขว้แล้ว · "
    "สร้างด้วย tools/make_soak_report_pdf.py (LGS-Test-Tool)"),
    new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0)

pdf.output(OUT)
print("wrote", OUT)
