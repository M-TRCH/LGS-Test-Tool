"""The site report: one PDF that says what is installed.

A cabinet leaves commissioning with a gateway full of settings and dozens
of modules whose identity (chip UID above all) exists nowhere on paper.
This renders the record: gateway identity and configuration, the cabinet's
shape, and one row per slot — ID, hub channel, UID, type, firmware,
hardware, boot count, health — so "which board sits in slot 45 of the
cabinet at ward 7" has an answer years later.

Pure: (meta, settings, layout facts, module records) -> PDF bytes. The
sweep that produces the records lives in fw_survey.run_report_survey.

Labels are English on purpose — they match the console keys and the
control table, the same rule the rest of the tool follows — but the font
carries Thai for free-text values such as the gateway's name.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, Sequence

from fpdf import FPDF

from .lgs_map import HEALTH_BITS, dec_baud, dec_hw

# Windows ships these; the first pair that exists wins. Fallback to the
# built-in Helvetica loses Thai glyphs but never loses the report.
_FONT_REGULAR = (r"C:\Windows\Fonts\LeelawUI.ttf",
                 r"C:\Windows\Fonts\leelawad.ttf",
                 r"C:\Windows\Fonts\tahoma.ttf")
_FONT_BOLD = (r"C:\Windows\Fonts\LeelaUIb.ttf",
              r"C:\Windows\Fonts\leelawdb.ttf",
              r"C:\Windows\Fonts\tahomabd.ttf")


def _first_existing(paths: Sequence[str]) -> Optional[str]:
    for p in paths:
        if os.path.isfile(p):
            return p
    return None


class _Report(FPDF):
    def __init__(self) -> None:
        super().__init__(orientation="P", format="A4")
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(True, margin=14)
        regular = _first_existing(_FONT_REGULAR)
        bold = _first_existing(_FONT_BOLD)
        if regular:
            self.add_font("site", "", regular)
            self.add_font("site", "B", bold or regular)
            self._family = "site"
        else:
            self._family = "helvetica"

    def font(self, size: float, bold: bool = False) -> None:
        self.set_font(self._family, "B" if bold else "", size)

    def footer(self) -> None:  # fpdf hook
        self.set_y(-10)
        self.font(7)
        self.set_text_color(120)
        self.cell(0, 5, f"page {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(0)


def _kv_rows(pdf: _Report, pairs: list) -> None:
    """Two key=value pairs per line, the whole settings dump in ~1 column."""
    half = (len(pairs) + 1) // 2
    left, right = pairs[:half], pairs[half:]
    with pdf.table(col_widths=(34, 59, 34, 59), first_row_as_headings=False,
                   line_height=4.6, borders_layout="NONE", padding=0.4) as table:
        for i in range(half):
            row = table.row()
            k1, v1 = left[i]
            row.cell(k1)
            row.cell(str(v1))
            if i < len(right):
                k2, v2 = right[i]
                row.cell(k2)
                row.cell(str(v2))
            else:
                row.cell("")
                row.cell("")


def build_report_pdf(*, app_version: str, generated: datetime,
                     info: dict, settings: dict,
                     cabinet_label: str, cabinet_count: int,
                     widths: Sequence[int], records: Sequence,
                     hub_channel) -> bytes:
    """`records` are fw_survey.ModuleRecord; `hub_channel(id)` maps a slave
    ID to its RS485 hub channel (0 = wired straight)."""
    pdf = _Report()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── title ─────────────────────────────────────────────────────────────
    pdf.font(15, bold=True)
    pdf.cell(0, 8, "LGS Site Report", new_x="LMARGIN", new_y="NEXT")
    pdf.font(8)
    pdf.set_text_color(90)
    name = settings.get("sys.name", "")
    headline = f"{name} · " if name else ""
    pdf.cell(0, 5,
             f"{headline}generated {generated:%Y-%m-%d %H:%M} · "
             f"LGS Test Tool v{app_version}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    pdf.ln(2)

    # ── gateway identity ──────────────────────────────────────────────────
    pdf.font(11, bold=True)
    pdf.cell(0, 6, "Gateway", new_x="LMARGIN", new_y="NEXT")
    pdf.font(8)
    idline = (f"fw {info.get('fw', '?')} · build {info.get('build', '?')} · "
              f"id {info.get('id', '?')} · mac {info.get('mac', '?')}")
    netline = (f"net {info.get('net.state', '?')} · "
               f"{info.get('net.ip', '?')}:{info.get('net.port', '?')} · "
               f"watchdog {info.get('sys.wdt', '?')} ms · "
               f"clock {info.get('time.now', 'unset').replace('T', ' ')} · "
               f"scheduled reset {info.get('sched.reset', '?')}")
    pdf.cell(0, 4.6, idline, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4.6, netline, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── cabinet ───────────────────────────────────────────────────────────
    pdf.font(11, bold=True)
    pdf.cell(0, 6, "Cabinet", new_x="LMARGIN", new_y="NEXT")
    pdf.font(8)
    rows_text = ",".join(str(w) for w in widths) if widths else "-"
    pdf.cell(0, 4.6,
             f"{cabinet_label} · {cabinet_count} modules · "
             f"slots per row (top first): {rows_text} · "
             f"hub map {settings.get('bus.hub_map', '-')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── modules — the reason this report exists ───────────────────────────
    pdf.font(11, bold=True)
    answered = sum(1 for r in records if r.responded)
    pdf.cell(0, 6, f"Modules ({answered}/{len(records)} answered)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.font(7.5)
    with pdf.table(col_widths=(10, 8, 47, 26, 15, 20, 12, 13, 35),
                   line_height=4.4, padding=0.4,
                   text_align=("CENTER", "CENTER", "LEFT", "LEFT", "CENTER",
                               "LEFT", "CENTER", "CENTER", "LEFT")) as table:
        head = table.row()
        for title in ("ID", "CH", "UID", "Type", "FW", "HW",
                      "Boots", "Health", "Note"):
            head.cell(title)
        for r in records:
            row = table.row()
            row.cell(str(r.device_id))
            ch = hub_channel(r.device_id)
            row.cell(str(ch) if ch else "-")
            if r.responded:
                row.cell(r.uid)
                row.cell(r.type_name)
                row.cell(r.fw)
                row.cell(dec_hw(r.hw_raw))
                row.cell(str(r.boots))
                row.cell(f"0x{r.health:02X}")
                mismatch = (r.reported_id != r.device_id)
                row.cell(f"reports id {r.reported_id}!" if mismatch else "")
            else:
                pdf.set_text_color(180, 40, 40)
                row.cell("no answer")
                pdf.set_text_color(0)
                for _ in range(6):
                    row.cell("")
    pdf.font(6.5)
    pdf.set_text_color(90)
    bits = ", ".join(f"bit{i}={n}" for i, n in enumerate(HEALTH_BITS))
    pdf.cell(0, 4, f"health: {bits} (set = OK) · bit4 = latch locked · "
                   f"baud per module config, bus runs "
                   f"{dec_baud(int(settings.get('rs485.baud', 9600) or 9600))}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    pdf.ln(2)

    # ── the full settings dump, for the record ────────────────────────────
    pdf.font(11, bold=True)
    pdf.cell(0, 6, "Gateway settings", new_x="LMARGIN", new_y="NEXT")
    pdf.font(6.8)
    _kv_rows(pdf, sorted(settings.items()))

    return bytes(pdf.output())
