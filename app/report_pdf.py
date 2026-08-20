"""The site report: one PDF that says what is installed.

A cabinet leaves commissioning with a gateway full of settings and dozens
of modules whose identity (chip UID above all) exists nowhere on paper.
This renders the record: gateway identity and configuration, the cabinet's
shape, one row per slot — ID, hub channel, UID, type, firmware, hardware,
boot count, health — the lifetime statistics each module keeps, and the
gateway's own recent event log.

Pure: (meta, settings, layout facts, module records) -> PDF bytes. The
sweep that produces the records lives in fw_survey.run_report_survey.

Language: English throughout, by house rule. Since 2026-08-13 the settings
table borrows the tool's curated English field labels (i18n `gwf.*`, which
carry the units) instead of raw console keys — the export file still holds
the raw keys for machine use, and the label lookup falls back to the raw
key for anything unnamed.
"""
from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Optional, Sequence

from fpdf import FPDF
from fpdf.enums import TableCellFillMode
from fpdf.fonts import FontFace

from .i18n import TEXTS
from .lgs_map import HEALTH_BITS, SENSOR_FAULT, dec_baud, fmt_dur


def _hw_name(raw: int) -> str:
    """510 -> "R5.1". The board revision is what a reader recognises; the
    raw register value belongs in the CSV export, not in a column someone
    has to translate in their head."""
    return f"R{raw // 100}.{(raw // 10) % 10}" if raw > 0 else "—"

# ── palette ────────────────────────────────────────────────────────────────
ACCENT = (38, 84, 124)          # deep blue: section marks + table headers
GROUP_FILL = (222, 232, 241)    # settings group bands
ZEBRA = (240, 244, 249)         # every-other-row fill
FAIL_RED = (180, 40, 40)
MUTED = (130, 130, 130)

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


def _section(pdf: _Report, title: str) -> None:
    """A heading with the accent mark — one look for every section."""
    pdf.ln(1.5)
    y = pdf.get_y()
    pdf.set_fill_color(*ACCENT)
    pdf.rect(pdf.l_margin, y + 0.9, 1.8, 4.6, style="F")
    # Hand the document's fill colour back to white before anything else
    # draws: a table takes its UNFILLED cells' style from the current
    # document state, so a leftover accent here paints every non-zebra row
    # navy — the zebra reads inverted and the report looks broken.
    pdf.set_fill_color(255)
    pdf.set_x(pdf.l_margin + 3.6)
    pdf.font(11, bold=True)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)


def _table_kw(**extra) -> dict:
    """The shared table look: filled header, zebra rows, light borders."""
    kw = dict(
        headings_style=FontFace(emphasis="BOLD", color=255, fill_color=ACCENT),
        cell_fill_color=ZEBRA,
        cell_fill_mode=TableCellFillMode.ROWS,
        borders_layout="MINIMAL",
        line_height=4.4, padding=0.4)
    kw.update(extra)
    return kw


def _legend(pdf: _Report, text: str) -> None:
    """Small print under a table. multi_cell, not cell: these run long and a
    legend that leaves the page carries its meaning off with it."""
    pdf.font(6.5)
    pdf.set_text_color(*MUTED)
    pdf.multi_cell(0, 3.6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)


def _ensure_room(pdf: _Report, needed_mm: float) -> None:
    """Start the next page rather than cut a block in two — but only when
    the block would actually fit on a fresh one, or the break buys nothing
    and costs half a page.

    It matters for the settings: a group that straddles the break leaves
    its second half under no heading at all, and "Cabinet size / Drive the
    status lamps" at the top of a page belongs to nothing the reader can see.
    """
    limit = pdf.h - pdf.b_margin
    if needed_mm <= limit - pdf.t_margin and pdf.get_y() + needed_mm > limit:
        pdf.add_page()


def _headings(table, titles: Sequence[str]) -> None:
    """Column titles, always centred over their column.

    A heading inherits its column's alignment unless told otherwise, so a
    left-aligned column of long text ("UID", "Note") dragged its title out
    to the edge while the narrow numeric ones sat centred — the row read as
    if it had been typeset twice."""
    row = table.row()
    for title in titles:
        row.cell(title, align="CENTER")


# ── gateway settings: friendly names, grouped ──────────────────────────────
_SETTING_GROUPS = (("sys", "System"), ("time", "Clock"),
                   ("rs485", "RS485 bus"), ("usb", "USB bridge"),
                   ("net", "Network"), ("bus", "RS485 hub"),
                   ("panel", "Front panel"), ("sched", "Scheduled reset"))
_BOOL_KEYS = {"net.enabled", "net.dhcp", "panel.enabled", "panel.lamps",
              "sched.reset_enabled"}
# hh:mm keys -> which bit of `sched.reset_slots` arms them
_HHMM_KEYS = {"sched.reset_hhmm": 0, "sched.reset_hhmm2": 1,
              "sched.reset_hhmm3": 2, "sched.reset_hhmm4": 3}

# Keys the tool draws with a custom widget rather than a labelled field, so
# i18n has no `gwf.` entry for them. Named here so the report never falls
# back to a raw console key.
_EXTRA_LABELS = {
    "panel.btn1": "Red button does", "panel.btn2": "Green button does",
    "panel.btn3": "Blue button does", "panel.btn4": "Yellow button does",
    "panel.btn5": "White button does",
    "panel.out1": "Relay output 1 follows", "panel.out2": "Relay output 2 follows",
    "panel.out3": "Relay output 3 follows", "panel.out4": "Relay output 4 follows",
    "sched.reset_hhmm": "Reset time 1", "sched.reset_hhmm2": "Reset time 2",
    "sched.reset_hhmm3": "Reset time 3", "sched.reset_hhmm4": "Reset time 4",
    "sched.reset_slots": "Reset times armed", "sched.reset_days": "Reset days",
}
_PANEL_ACTIONS = {0: "nothing", 1: "light + number, whole cabinet",
                  2: "everything off", 3: "light + number + latch",
                  4: "power-cycle the shelf", 5: "test the status lamps"}
_PANEL_SOURCES = {0: "nothing (off)", 1: "ready", 2: "busy", 3: "fault",
                  4: "LAN is up", 5: "TCP client connected",
                  6: "sweep running", 7: "shelf power dropped",
                  8: "the shelf's power"}
_DAY_NAMES = ("Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat")


def _setting_label(key: str) -> str:
    # The overrides win: the tool's own label for slot 1 ("Time of day")
    # reads oddly beside "Reset time 2/3/4", and a set of four wants one
    # name with four numbers.
    entry = TEXTS.get(f"gwf.{key}")
    label = _EXTRA_LABELS.get(key) or (
        entry["en"] if entry and entry.get("en") else key)
    # The UI's arrow is not in the report font; the glyph would be dropped
    # silently, leaving "Row  hub channel".
    return label.replace("→", "->")


def _is_off(settings: dict, key: str, default: str = "1") -> bool:
    return str(settings.get(key, default)).strip() != "1"


def _no_hub(settings: dict) -> bool:
    text = str(settings.get("bus.hub_map", "") or "").strip()
    return bool(text) and set(text.replace(",", "")) <= {"0"}


def _inert_note(key: str, settings: dict) -> str:
    """Why this setting is not currently doing anything. "" = it is live.

    A stored value is not the same as a value in force, and the report was
    printing the two identically: `sched.reset_hhmm2` reads 09:00 whether
    or not slot 2 is armed, so a disarmed time looked exactly like a
    cabinet that power-cycles itself every morning. Every switch that
    parks another setting is listed here, strongest first.
    """
    def num(k: str, default: int = 0) -> int:
        try:
            return int(str(settings.get(k, default)).strip())
        except (TypeError, ValueError):
            return default

    if key.startswith("sched.") and key != "sched.reset_enabled":
        if _is_off(settings, "sched.reset_enabled"):
            return "scheduler off"
        if key in _HHMM_KEYS:
            slot = _HHMM_KEYS[key]
            if not num("sched.reset_slots", 1) & (1 << slot):
                return "not armed"
    if key.startswith("panel.btn") and _is_off(settings, "panel.enabled"):
        return "buttons off"
    if (key.startswith("panel.out") and _is_off(settings, "panel.lamps")
            and num(key) not in (0, 8)):        # 8 = shelf power, not a lamp
        return "lamps off"
    if key == "panel.cabinet" and str(settings.get("panel.shape", "0")).strip() \
            not in ("", "0"):
        return "the sweep shape wins"
    if key.startswith("net.") and key != "net.enabled" \
            and _is_off(settings, "net.enabled"):
        return "LAN off"
    if key in {"net.ip", "net.mask", "net.gw", "net.dns"} and num("net.dhcp") == 1:
        return "DHCP is on"
    if key == "net.ntp_port" and str(settings.get("net.ntp", "")).strip() \
            in ("", "0.0.0.0"):
        return "no NTP server set"
    if key.startswith("bus.hub_") and key != "bus.hub_map" and _no_hub(settings):
        return "no hub"
    return ""


def _setting_value(key: str, value: str) -> str:
    if key in _BOOL_KEYS:
        return "on" if value == "1" else "off"
    if key in _HHMM_KEYS and value.isdigit():
        v = int(value)
        if v <= 2359:
            return f"{v // 100:02d}:{v % 100:02d}"
    if value.isdigit():
        n = int(value)
        if key.startswith("panel.btn"):
            return _PANEL_ACTIONS.get(n, value)
        if key.startswith("panel.out"):
            return _PANEL_SOURCES.get(n, value)
        if key == "sched.reset_slots":
            armed = [str(i + 1) for i in range(4) if n & (1 << i)]
            return ("times " + ", ".join(armed)) if armed else "none"
        if key == "sched.reset_days":
            if n in (0, 0x7F):
                return "every day"
            days = [_DAY_NAMES[i] for i in range(7) if n & (1 << i)]
            return ", ".join(days) if days else "never"
    return value or "—"


def _settings_column(settings: dict) -> list:
    """Every group as a flat list of slots: ("group", name) / ("kv", k, v)."""
    slots = []
    for prefix, group_name in _SETTING_GROUPS:
        # Sorted by the LABEL, not the console key: the reader is scanning
        # names, and "Reset time 1..4" belong together however their keys
        # happen to spell themselves.
        items = sorted(((k, v) for k, v in settings.items()
                        if k.split(".", 1)[0] == prefix),
                       key=lambda kv: _setting_label(kv[0]).lower())
        if not items:
            continue
        slots.append(("group", group_name))
        slots.extend(("kv", k, v) for k, v in items)
    return slots


def _split_by_group(slots: list) -> tuple:
    """Two columns, cut on a group boundary near the halfway mark.

    The page has room for two pairs of columns and this table wants them —
    but splitting ONE topic down the middle is what made it hard to read:
    "Red button does" ended up bottom left and "Yellow button does" bottom
    right, and the eye had to zigzag through a group to collect it. Each
    side now carries WHOLE topics, so a group is read straight down.
    """
    starts = [i for i, s in enumerate(slots) if s[0] == "group"] + [len(slots)]
    half = len(slots) / 2
    cut = min(starts[1:], key=lambda i: abs(i - half))
    return slots[:cut], slots[cut:]


_SETTINGS_ROW_MM = 5.0          # line_height + padding, near enough to plan with


def _settings_height(settings: dict) -> float:
    left, right = _split_by_group(_settings_column(settings))
    return max(len(left), len(right)) * _SETTINGS_ROW_MM + 12


def _settings_table(pdf: _Report, settings: dict) -> None:
    pdf.font(6.8)
    group_style = FontFace(emphasis="BOLD", color=ACCENT,
                           fill_color=GROUP_FILL)
    inert_style = FontFace(color=MUTED)
    left, right = _split_by_group(_settings_column(settings))

    def put(row, slot) -> None:
        if slot is None:
            row.cell("")
            row.cell("")
        elif slot[0] == "group":
            row.cell(slot[1], colspan=2, style=group_style)
        else:
            key, value = slot[1], str(slot[2])
            note = _inert_note(key, settings)
            row.cell(_setting_label(key))
            # Greyed AND spelled out: the report gets printed in black and
            # white as often as not, and colour alone would carry nothing.
            row.cell(_setting_value(key, value) + (f"  ({note})" if note else ""),
                     style=inert_style if note else None)

    # Values run wide once they read as words ("light + number + latch"),
    # so the value columns get more room than a raw number would need.
    with pdf.table(col_widths=(52, 41, 52, 41), first_row_as_headings=False,
                   **_table_kw(line_height=4.2)) as table:
        for i in range(max(len(left), len(right))):
            row = table.row()
            put(row, left[i] if i < len(left) else None)
            put(row, right[i] if i < len(right) else None)


# ── recent events: parse the console lines into a real table ───────────────
_EV_LINE = re.compile(r"#(\d+)\s+(\S+)\s+up=(\S+?)s?\s+(\S+)"
                      r"(?:\s+a=(\d+)\s+p=(\d+))?$")
_RESET_NAMES = {0: "unknown", 1: "watchdog", 2: "window-watchdog",
                3: "software", 4: "pin", 5: "brownout", 6: "power-on"}
_ACTION_NAMES = {1: "all on", 2: "all off", 3: "all unlock",
                 4: "shelf reset", 5: "lamp test"}


def _event_detail(ev: str, a: int, p: int) -> str:
    if ev == "boot":
        return f"cause: {_RESET_NAMES.get(a, a)}"
    if ev == "clock_set":
        src = "NTP" if a == 2 else "Test Tool"
        jump = f", jumped {p} s" if p else ""
        return f"set by {src}{jump}"
    if ev == "link_up":
        return f"our address ends .{p}"
    if ev == "tcp_accept":
        return f"slot {a}, client ends .{p}"
    if ev == "tcp_close":
        return f"slot {a}"
    if ev == "tcp_refused":
        return f"both slots taken; client ends .{p}"
    if ev == "sched_reset":
        return f"slot time {p // 100:02d}:{p % 100:02d}" if p else ""
    if ev == "panel_sweep":
        return f"{_ACTION_NAMES.get(a, a)} (button {p})"
    if ev == "store_erased":
        return "10 s button hold" if a == 1 else "forced defaults"
    if a or p:
        return f"a={a} p={p}"
    return ""


def _events_table(pdf: _Report, events: Sequence[str]) -> None:
    pdf.font(7)
    with pdf.table(col_widths=(12, 34, 18, 30, 92),
                   text_align=("CENTER", "LEFT", "RIGHT", "LEFT", "LEFT"),
                   **_table_kw()) as table:
        _headings(table, ("#", "Time", "Uptime", "Event", "Detail"))
        for line in events:
            m = _EV_LINE.match(str(line).strip())
            row = table.row()
            if not m:
                row.cell("")
                row.cell(str(line), colspan=4)
                continue
            seq, when, up, ev = m.group(1), m.group(2), m.group(3), m.group(4)
            a = int(m.group(5) or 0)
            p = int(m.group(6) or 0)
            row.cell(seq)
            row.cell("—" if when == "-" else when.replace("T", " "))
            row.cell(fmt_dur(int(up)) if up.isdigit() else up)
            row.cell(ev.replace("_", " "))
            row.cell(_event_detail(ev, a, p))


def build_report_pdf(*, app_version: str, generated: datetime,
                     info: dict, settings: dict,
                     cabinet_label: str, cabinet_count: int,
                     widths: Sequence[int], records: Sequence,
                     hub_channel, events: Sequence[str] = ()) -> bytes:
    """`records` are fw_survey.ModuleRecord; `hub_channel(id)` maps a slave
    ID to its RS485 hub channel (0 = wired straight); `events` are the
    gateway's newest event-log lines (may be empty — older firmware)."""
    pdf = _Report()
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── title ─────────────────────────────────────────────────────────────
    pdf.font(15, bold=True)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, "LGS Site Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)
    pdf.font(8)
    pdf.set_text_color(90)
    name = settings.get("sys.name", "")
    headline = f"{name} · " if name else ""
    pdf.cell(0, 5,
             f"{headline}generated {generated:%Y-%m-%d %H:%M} · "
             f"LGS Test Tool v{app_version}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0)

    # ── gateway identity ──────────────────────────────────────────────────
    _section(pdf, "Gateway")
    pdf.font(8)
    idline = (f"fw {info.get('fw', '?')} · build {info.get('build', '?')} · "
              f"id {info.get('id', '?')} · mac {info.get('mac', '?')}")
    netline = (f"net {info.get('net.state', '?')} · "
               f"{info.get('net.ip', '?')}:{info.get('net.port', '?')} · "
               f"watchdog {info.get('sys.wdt', '?')} ms · "
               f"clock {info.get('time.now', 'unset').replace('T', ' ')} · "
               f"NTP {info.get('ntp.state', '-')} · "
               f"scheduled reset {info.get('sched.reset', '?')}")
    pdf.cell(0, 4.6, idline, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4.6, netline, new_x="LMARGIN", new_y="NEXT")

    # ── cabinet ───────────────────────────────────────────────────────────
    _section(pdf, "Cabinet")
    pdf.font(8)
    rows_text = ",".join(str(w) for w in widths) if widths else "-"
    pdf.cell(0, 4.6,
             f"{cabinet_label} · {cabinet_count} modules · "
             f"slots per row (top first): {rows_text} · "
             f"hub map {settings.get('bus.hub_map', '-')}",
             new_x="LMARGIN", new_y="NEXT")

    # ── modules — the reason this report exists ───────────────────────────
    answered = sum(1 for r in records if r.responded)
    _section(pdf, f"Modules ({answered}/{len(records)} answered)")
    pdf.font(7.5)
    fail_style = FontFace(color=FAIL_RED)
    with pdf.table(col_widths=(10, 8, 47, 26, 15, 14, 12, 13, 41),
                   text_align=("CENTER", "CENTER", "LEFT", "LEFT", "CENTER",
                               "CENTER", "CENTER", "CENTER", "LEFT"),
                   **_table_kw()) as table:
        _headings(table, ("ID", "CH", "UID", "Type", "FW", "HW",
                          "Boots", "Health", "Note"))
        for r in records:
            row = table.row()
            row.cell(str(r.device_id))
            ch = hub_channel(r.device_id)
            row.cell(str(ch) if ch else "-")
            if r.responded:
                row.cell(r.uid)
                row.cell(r.type_name)
                row.cell(r.fw)
                row.cell(_hw_name(r.hw_raw))
                row.cell(str(r.boots))
                row.cell(f"0x{r.health:02X}")
                mismatch = (r.reported_id != r.device_id)
                row.cell(f"reports id {r.reported_id}!" if mismatch else "")
            else:
                row.cell("no answer", style=fail_style)
                for _ in range(6):
                    row.cell("")
    bits = ", ".join(f"bit{i}={n}" for i, n in enumerate(HEALTH_BITS))
    _legend(pdf, f"health: {bits} (set = OK; bit3 reads 0 on every R5.1 — "
                 f"known, harmless; bit1 reads 0 on every type 10 STANDARD "
                 f"module, which has the 8-LED mask instead of an OLED — on a "
                 f"ring type it means a failed display) · bit4 = latch locked "
                 f"· bus runs "
                 f"{dec_baud(int(settings.get('rs485.baud', 9600) or 9600))}")

    # ── module statistics — how much this cabinet has actually worked ─────
    with_stats = sum(1 for r in records if getattr(r, "stats", None))
    if with_stats:
        _section(pdf, f"Module statistics ({with_stats}/{len(records)})")
        pdf.font(7)
        muted_style = FontFace(color=MUTED)
        with pdf.table(col_widths=(10, 24, 12, 12, 18, 18, 18, 28, 24, 22),
                       text_align=("CENTER",) * 10,
                       **_table_kw()) as table:
            _headings(table, ("ID", "Op time", "Boots", "IWDG", "Presses",
                              "Latch fires", "LED on", "LED time",
                              "Room °C", "Supply mA"))
            for r in records:
                row = table.row()
                row.cell(str(r.device_id))
                s = getattr(r, "stats", None) if r.responded else None
                if s is None:
                    # Seven columns belong to the statistics block; one short
                    # and the live readings slide left into them.
                    row.cell("n/a", style=muted_style)
                    for _ in range(6):
                        row.cell("")
                else:
                    row.cell(fmt_dur(s.op_seconds))
                    row.cell(str(r.boots))
                    row.cell(str(s.iwdg_resets))
                    row.cell(str(s.button_presses))
                    row.cell(str(s.latch_fires))
                    row.cell(str(s.total_on_count))
                    row.cell(fmt_dur(s.total_on_time_s))
                room = getattr(r, "room_raw", -1)
                if r.responded and 0 <= room != SENSOR_FAULT:
                    row.cell(f"{room / 100:.1f}")
                else:
                    row.cell("—")
                ma = getattr(r, "current_ma", -1)
                row.cell(str(ma) if r.responded and ma >= 0 else "—")
        _legend(pdf, "lifetime totals persisted on each module (fw >= v3.3.0; "
                     "n/a = older firmware or no answer) · cleared by coil 510 "
                     "/ factory reset — boot count survives · Room °C and "
                     "Supply mA are live readings at survey time")

    # ── the full settings dump, for the record ────────────────────────────
    _ensure_room(pdf, _settings_height(settings))
    _section(pdf, "Gateway settings")
    _settings_table(pdf, settings)
    _legend(pdf, "raw console keys and values travel in the config export "
                 "file (Gateway page); labels here follow the tool's fields")

    # ── recent gateway events — what happened here lately ─────────────────
    if events:
        _ensure_room(pdf, len(events) * _SETTINGS_ROW_MM + 20)
        _section(pdf, f"Recent gateway events (newest first, {len(events)})")
        _events_table(pdf, events)
        _legend(pdf, "Time — means the clock was not yet set when the event "
                     "was written (right after a power cut); Uptime orders "
                     "those events within their boot")

    return bytes(pdf.output())
