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
# The Tool's default "ocean" theme (app.css), so a report looks like the page it came from.
ACCENT = (10, 126, 164)         # brand: section marks + table headers
INK = (13, 43, 58)              # text
GROUP_FILL = (217, 235, 243)    # settings group bands, tiles (the theme's surface 2)
ZEBRA = (240, 247, 250)         # every-other-row fill
LINE = (188, 214, 226)
FAIL_RED = (198, 40, 40)
MUTED = (70, 105, 122)
OK_GREEN = (15, 138, 79)
OK_BG = (223, 245, 232)
WARN = (154, 103, 0)
WARN_BG = (255, 241, 204)
BAD_BG = (253, 224, 224)

# Windows ships the first three; the Linux ones are what the Docker image
# installs (fonts-thai-tlwg-ttf), for the hospital-server deployment. The
# first that exists wins. Fallback to the built-in Helvetica loses Thai
# glyphs but never loses the report.
_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "v2", "static", "fonts")
# The Tool's own face first (IBM Plex Sans Thai, merged to one TTF by tools/make_report_fonts.py and shipped with the pages),
# the system fonts only if that file is missing.
_FONT_REGULAR = (os.path.join(_FONT_DIR, "IBMPlexSansThai-Regular.ttf"),
                 r"C:\Windows\Fonts\LeelawUI.ttf",
                 r"C:\Windows\Fonts\leelawad.ttf",
                 r"C:\Windows\Fonts\tahoma.ttf",
                 "/usr/share/fonts/truetype/tlwg/Loma.ttf",
                 "/usr/share/fonts/truetype/tlwg/Garuda.ttf")
_FONT_BOLD = (os.path.join(_FONT_DIR, "IBMPlexSansThai-Bold.ttf"),
              r"C:\Windows\Fonts\LeelaUIb.ttf",
              r"C:\Windows\Fonts\leelawdb.ttf",
              r"C:\Windows\Fonts\tahomabd.ttf",
              "/usr/share/fonts/truetype/tlwg/Loma-Bold.ttf",
              "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf")


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
        self.set_text_color(*MUTED)
        self.cell(0, 5, f"LGS Test Tool  ·  {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(*INK)


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
    pdf.set_text_color(*INK)


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
    pdf.set_text_color(*INK)


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
        # aux mirrors the gateway's TimeSource: 1 tool, 2 NTP, 3 restored
        # from the RTC after a reset (gw fw >= 1.12.2). The restore is the
        # forensic case — "who set the clock at 03:12?" must not answer
        # "Test Tool" when nobody was there.
        src = {2: "NTP", 3: "restored from RTC after a reset"}.get(a, "Test Tool")
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


SOAK_TABLE_ROWS = 15


def _when(at) -> str:
    return f"{at:%m-%d %H:%M:%S}" if at else "—"


def _soak_section(pdf: _Report, soak) -> None:
    """Print a soak_csv.SoakSummary the way the LGS Soak Monitor reads the
    same run, so the PDF and the dashboard never disagree:

      * one verdict first — any failed read, any watchdog reset, any reboot
        no scheduled reset explains — because that is the question the
        reader came with;
      * EVERY scheduled reset listed, one line per night: a three-night run
        footers "reboots=192", and printing that without its explanation
        reads as a cabinet fault;
      * the watchdog from all three witnesses on the reboot rows, so a reset
        whose counter could not be read is still seen;
      * the slowest reading of the run, the slowest outside the reset windows
        (modules booting are slow for a reason) and the slowest hub crossing,
        each with its module — and a table of the modules behind them."""
    shown = list(soak.trouble[:SOAK_TABLE_ROWS])
    for which, outside in (("slow", False), ("slow", True), ("cross", False)):
        best = soak.slowest(which, outside_reset=outside)
        if best and all(t.device_id != best[0] for t in shown):
            shown.append(next(t for t in soak.trouble if t.device_id == best[0]))
    _ensure_room(pdf, 52 + len(shown) * 4.4)
    _section(pdf, "ผล soak (ทดสอบต่อเนื่อง)")
    pdf.font(8)
    dur_h = soak.duration_s / 3600.0
    span = "?"
    if soak.started and soak.ended:
        span = f"{soak.started:%Y-%m-%d %H:%M} - {soak.ended:%Y-%m-%d %H:%M}"

    def line(text: str, *, red: bool = False, bold: bool = False) -> None:
        # multi_cell: a long line wraps instead of running off the page.
        pdf.font(8, bold=bold)
        if red:
            pdf.set_text_color(*FAIL_RED)
        pdf.multi_cell(0, 4.4, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*INK)
        pdf.font(8)

    line(f"{soak.filename or 'soak CSV'} · {span} ({dur_h:.1f} h) · "
         f"{soak.module_count} modules · {soak.passes:,} passes · {soak.reads:,} reads"
         # A pharmacy run also WROTE to the cabinet, and that is the whole
         # point of it. Saying so here is what stops the section reading
         # exactly like a plain poll's.
         + (f" · {soak.writes:,} coil writes, {soak.write_fails} failed "
            f"({soak.picks:,} picks, {soak.dropped} dropped)" if soak.writes else ""))

    # The verdict, in the Monitor's words.
    if soak.problems:
        line(f"Problems found: fails {soak.fails} · watchdog resets "
             f"{soak.watchdog_resets} · unexplained reboots "
             f"{soak.unexplained_reboots}", red=True, bold=True)
    else:
        line("No problems: no failed reads, no watchdog resets and no "
             "unexplained reboots", bold=True)
    line(f"fails {soak.fails} · link losses {soak.link_losses} · "
         f"{soak.crossings:,} hub crossings · tool worst read {soak.worst_ms:,} ms, "
         f"worst crossing {soak.worst_cross_ms:,} ms")

    # Reboots: every scheduled reset, then whatever is left over.
    if soak.reboots == 0:
        line("reboots 0 — no module restarted all run")
    else:
        causes = " · ".join(f"{c}: {n}" for c, n in
                            sorted(soak.reboot_causes.items(), key=lambda kv: -kv[1]))
        if soak.mass_clusters:
            nights = " · ".join(f"{c['start']:%m-%d %H:%M:%S}-{c['end']:%H:%M:%S} ×{c['n']}"
                                for c in soak.mass_clusters)
            k = len(soak.mass_clusters)
            line(f"{k} scheduled gateway reset{'s' if k > 1 else ''}, "
                 f"{soak.mass_reboots} reboots in all: {nights} — watchdog "
                 f"counters unchanged, not a fault")
        if soak.unexplained_reboots:
            line(f"{soak.unexplained_reboots} reboot(s) NOT explained by a "
                 f"scheduled reset", red=True)
        line(f"reboot causes (reg 8): {causes}")
    unread = (f" · counter unreadable on {soak.iwdg_unread_rows} reboot row(s): "
              f"cause unknown" if soak.iwdg_unread_rows else "")
    line(f"watchdog: {soak.watchdogs} by the counter (reg 410) · "
         f"{soak.iwdg_moved_rows} reboot row(s) with the counter moved · "
         f"{soak.iwdg_cause_rows} naming IWDG in reg 8" + unread,
         red=bool(soak.watchdog_resets or soak.iwdg_unread_rows))
    if not soak.finished:
        line("run did not finish (no stop row — PC slept or lost power); "
             "totals above are the last heartbeat's and undercount the tail",
             red=True)

    # The slowest readings, each with its owner.
    overall = soak.slowest("slow")
    if overall:
        dev, ms, at, rst = overall
        line(f"slowest in this run: {ms:,} ms · module {dev} · {_when(at)}"
             + (" (during a scheduled reset)" if rst else ""))
        if rst:
            normal = soak.slowest("slow", outside_reset=True)
            if normal:
                line(f"slowest outside resets: {normal[1]:,} ms · module "
                     f"{normal[0]} · {_when(normal[2])}")
    cross = soak.slowest("cross")
    if cross:
        line(f"slowest hub crossing: {cross[1]:,} ms · module {cross[0]} · "
             f"{_when(cross[2])}" + (" (during a scheduled reset)" if cross[3] else ""))

    if soak.trouble:
        pdf.ln(1)
        pdf.font(7.5)
        fail_style = FontFace(color=FAIL_RED)
        top = overall[0] if overall else None
        hl = FontFace(emphasis="BOLD")
        with pdf.table(col_widths=(10, 12, 18, 30, 26, 14),
                       text_align=("CENTER",) * 6,
                       width=110, **_table_kw()) as table:
            _headings(table, ("ID", "Slow", "Worst ms", "When", "Crossing (max ms)",
                              "No reply"))
            for t in shown:
                style = hl if t.device_id == top else None
                row = table.row()
                row.cell(str(t.device_id), style=style)
                row.cell(str(t.slow), style=style)
                row.cell(f"{t.worst_slow_ms:,}" if t.worst_slow_ms else "—", style=style)
                row.cell(_when(t.worst_slow_at)
                         + (" · reset" if t.worst_slow_in_reset else ""), style=style)
                row.cell(f"{t.cross} ({t.worst_cross_ms:,})" if t.cross else "0",
                         style=style)
                row.cell(str(t.no_reply),
                         style=fail_style if t.no_reply else style)
        rest = len(soak.trouble) - len(shown)
        if rest > 0:
            pdf.font(7.5)
            pdf.cell(0, 4.2, f"… and {rest} more modules with at least one slow "
                             f"or missing reply (all of them are in the CSV)",
                     new_x="LMARGIN", new_y="NEXT")
        _legend(pdf, f"every module that was slow or silent, most first; the "
                     f"run's slowest, slowest-outside-reset and slowest-crossing "
                     f"modules are always listed; bold = owner of the slowest "
                     f"reading · slow = an ordinary read past slow_ms, crossing = a "
                     f"read after a hub-channel change past crossing_slow_ms, "
                     f"counted apart · a reset window is "
                     f"{int(soak_csv_reset_margin())} s either side of a "
                     f"scheduled reset · the retry usually rescued a slow read, so "
                     f"these cost time, not failures · no reply = both attempts lost")


def soak_csv_reset_margin() -> float:
    from .soak_csv import RESET_MARGIN_S
    return RESET_MARGIN_S



def _ranges(ids) -> str:
    """[11, 12, 13, 21] -> "11-13, 21" (an en dash, as a reader writes it)."""
    out, ids = [], sorted(ids)
    i = 0
    while i < len(ids):
        j = i
        while j + 1 < len(ids) and ids[j + 1] == ids[j] + 1:
            j += 1
        out.append(str(ids[i]) if i == j else f"{ids[i]}–{ids[j]}")
        i = j + 1
    return ", ".join(out)


def _tile(pdf: _Report, x: float, y: float, w: float, value: str, label: str, tone=None) -> None:
    """A figure with its label, like the Tool's KPI tiles."""
    fill = {"ok": OK_BG, "warn": WARN_BG, "bad": BAD_BG}.get(tone, GROUP_FILL)
    ink = {"ok": OK_GREEN, "warn": WARN, "bad": FAIL_RED}.get(tone, INK)
    pdf.set_fill_color(*fill)
    pdf.rect(x, y, w, 19, style="F", round_corners=True, corner_radius=2.5)
    pdf.set_xy(x + 3.5, y + 2.2)
    pdf.font(13, bold=True)
    pdf.set_text_color(*ink)
    pdf.cell(w - 7, 8, value)
    pdf.set_xy(x + 3.5, y + 11)
    pdf.font(8)
    pdf.set_text_color(*MUTED)
    pdf.cell(w - 7, 5, label)
    pdf.set_text_color(*INK)


def _summary_page(pdf: _Report, *, app_version: str, generated: datetime, info: dict, settings: dict,
                  cabinet_label: str, cabinet_count: int, widths: Sequence[int], records: Sequence, soak=None) -> None:
    """One page that answers "what is in this cabinet and is anything wrong": the figures, the gateway in a few lines,
    a map of the modules coloured by firmware, and a short list of what deserves a look. The tables are the appendix."""
    left, right = pdf.l_margin, pdf.w - pdf.r_margin
    inner = right - left
    name = settings.get("sys.name", "") or cabinet_label

    # title
    pdf.set_xy(left, pdf.get_y())
    pdf.font(20, bold=True)
    pdf.set_text_color(*INK)
    pdf.cell(0, 10, name, new_x="LMARGIN", new_y="NEXT")
    pdf.font(9)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 5, f"รายงานไซต์  ·  {generated:%Y-%m-%d %H:%M}  ·  LGS Test Tool v{app_version}",
             new_x="LMARGIN", new_y="NEXT")
    y = pdf.get_y() + 2
    pdf.set_draw_color(*ACCENT)
    pdf.set_line_width(0.6)
    pdf.line(left, y, right, y)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(*LINE)          # tables below take their rules from the document's draw colour

    answered = [r for r in records if r.responded]
    silent = [r for r in records if not r.responded]
    versions: dict = {}
    for r in answered:
        versions.setdefault(r.fw_raw, []).append(r)
    top = max(versions) if versions else 0
    mixed = len(versions) > 1

    # tiles
    y = pdf.get_y() + 6
    gap = 4
    w = (inner - 2 * gap) / 3
    _tile(pdf, left, y, w, f"{len(answered)}/{len(records)}", "โมดูลที่ตอบ",
          "ok" if not silent else "bad")
    if versions:
        ver_text = "  ".join(f"{records_fw(v[0])} ×{len(v)}" for _, v in sorted(versions.items(), reverse=True))
    else:
        ver_text = "—"
    _tile(pdf, left + w + gap, y, w, ver_text, "เฟิร์มแวร์โมดูล",
          "warn" if mixed else ("ok" if versions else None))
    _tile(pdf, left + 2 * (w + gap), y, w, str(info.get("fw", "?")), "เกตเวย์")
    pdf.set_y(y + 19)
    if soak is not None:
        pdf.set_y(_soak_tiles(pdf, soak, y + 19 + 3.5))

    # gateway
    _section(pdf, "เกตเวย์")
    rows_text = ",".join(str(x) for x in widths) if widths else "-"
    facts = (
        ("เครือข่าย", f"{info.get('net.ip', '?')}:{info.get('net.port', '?')}  ({info.get('net.state', '?')})"),
        ("เวลาของเกตเวย์", f"{info.get('time.now', 'unset').replace('T', ' ')}  ·  NTP {info.get('ntp.state', '-')}"),
        ("reset ชั้นวาง", str(info.get("sched.reset", "?"))),
        ("ตู้", f"{cabinet_label}  ·  {cabinet_count} โมดูล  ·  แถวละ {rows_text}"),
    )
    pdf.set_x(left)
    for k, v in facts:
        pdf.set_x(left + 3.6)
        pdf.font(8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(36, 5.4, k)
        pdf.set_text_color(*INK)
        pdf.cell(0, 5.4, v, new_x="LMARGIN", new_y="NEXT")

    # module map
    _section(pdf, "แผนผังโมดูล")
    by_id = {r.device_id: r for r in records}
    cols = max(widths) if widths else 8
    cell_w = min(24.0, (inner - 3.6) / max(cols, 1))
    cell_h = 10.5
    x0 = left + 3.6
    y0 = pdf.get_y() + 1.5
    for ri, cnt in enumerate(widths, start=1):
        for ci in range(1, cnt + 1):
            rec = by_id.get(ri * 10 + ci)
            if rec is None:
                continue
            x = x0 + (ci - 1) * cell_w
            yy = y0 + (ri - 1) * (cell_h + 1.2)
            if not rec.responded:
                fill, ink = BAD_BG, FAIL_RED
            elif mixed and rec.fw_raw != top:
                fill, ink = WARN_BG, WARN
            else:
                fill, ink = OK_BG, OK_GREEN
            pdf.set_fill_color(*fill)
            pdf.rect(x, yy, cell_w - 1.2, cell_h, style="F", round_corners=True, corner_radius=1.6)
            pdf.set_xy(x, yy + 1.2)
            pdf.font(9, bold=True)
            pdf.set_text_color(*INK)
            pdf.cell(cell_w - 1.2, 4.4, str(rec.device_id), align="C")
            pdf.set_xy(x, yy + 5.6)
            pdf.font(7)
            pdf.set_text_color(*ink)
            pdf.cell(cell_w - 1.2, 3.6, rec.fw if rec.responded else "ไม่ตอบ", align="C")
    pdf.set_y(y0 + len(widths) * (cell_h + 1.2) + 1)
    # key
    pdf.set_x(x0)
    for fill, ink, text in ((OK_BG, OK_GREEN, "เวอร์ชันสูงสุดในตู้" if mixed else "ตอบปกติ"),
                            *(((WARN_BG, WARN, "เวอร์ชันเก่ากว่า"),) if mixed else ()),
                            (BAD_BG, FAIL_RED, "ไม่ตอบ")):
        pdf.set_fill_color(*fill)
        yk = pdf.get_y()
        pdf.rect(pdf.get_x(), yk + 1, 4.5, 3.4, style="F", round_corners=True, corner_radius=0.8)
        pdf.set_x(pdf.get_x() + 6)
        pdf.font(7.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(pdf.get_string_width(text) + 6, 5.4, text)
    pdf.ln(7)
    pdf.set_text_color(*INK)

    # what deserves a look
    _section(pdf, "ข้อควรดู")
    notes = []
    if silent:
        notes.append(("bad", f"ไม่ตอบ {len(silent)} ตัว: {_ranges([r.device_id for r in silent])}"))
    wrong = [r.device_id for r in answered if r.reported_id != r.device_id]
    if wrong:
        notes.append(("bad", f"รายงาน ID ไม่ตรงกับตำแหน่ง: {_ranges(wrong)}"))
    if mixed:
        parts = [f"{records_fw(v[0])}: {_ranges([r.device_id for r in v])}" for _, v in sorted(versions.items(), reverse=True)]
        notes.append(("warn", "เวอร์ชันไม่เท่ากัน  ·  " + "  ·  ".join(parts)))
    dogs = [r.device_id for r in answered if getattr(r, "stats", None) and r.stats.iwdg_resets > 0]
    if dogs:
        notes.append(("warn", f"watchdog เคยรีเซ็ตโมดูล: {_ranges(dogs)}"))
    if info.get("ntp.state", "ok") not in ("ok", "-"):
        notes.append(("warn", f"NTP: {info.get('ntp.state')}  (เวลาของเกตเวย์อาจเพี้ยน)"))
    if soak is not None:
        notes.append(("bad" if soak.problems or not soak.finished else "ok", "soak: " + soak.headline()))
    if not notes:
        notes.append(("ok", "ไม่พบสิ่งผิดปกติ"))
    for tone, text in notes:
        ink = {"ok": OK_GREEN, "warn": WARN, "bad": FAIL_RED}[tone]
        pdf.set_x(left + 3.6)
        pdf.set_fill_color(*ink)
        pdf.ellipse(pdf.get_x(), pdf.get_y() + 1.9, 2, 2, style="F")
        pdf.set_x(pdf.get_x() + 4.5)
        pdf.font(9)
        pdf.set_text_color(*INK)
        pdf.multi_cell(0, 5.4, text, new_x="LMARGIN", new_y="NEXT")


def records_fw(rec) -> str:
    return rec.fw


def _health_text(rec) -> tuple:
    """(text, ok) for a module's health byte, in words. What counts as a fault is deliberately narrow, because the boards
    in the field report 0x01 and are healthy: bit2 (room sensor) and bit3 (board sensor) are parts a board may simply not
    carry, bit3 reads 0 on every R5.x, and a type 10 STANDARD module has the 8-LED mask instead of an OLED so bit1 is 0 by
    design. A fault is bit0 (the AT24 EEPROM) clear, or bit1 clear on a module that has a display. The raw byte stays in
    the text for anyone who wants it."""
    raw = f"0x{rec.health:02X}"
    if not rec.health & 1:
        return f"AT24 EEPROM ผิดปกติ ({raw})", False
    if not rec.health & 2 and rec.device_type != 10:
        return f"จอ OLED ผิดปกติ ({raw})", False
    return f"ปกติ ({raw})", True


def _kv_block(pdf: _Report, facts, key_w: float = 38) -> None:
    for k, v in facts:
        pdf.set_x(pdf.l_margin + 3.6)
        pdf.font(8.5)
        pdf.set_text_color(*MUTED)
        pdf.cell(key_w, 5.2, k)
        pdf.set_text_color(*INK)
        pdf.cell(0, 5.2, str(v), new_x="LMARGIN", new_y="NEXT")


def _soak_tiles(pdf: _Report, soak, y: float) -> float:
    """A second row of tiles for the summary page when a soak result is attached; returns the new y."""
    left = pdf.l_margin
    inner = pdf.w - pdf.l_margin - pdf.r_margin
    gap = 4
    w = (inner - 2 * gap) / 3
    ok = not soak.problems and soak.finished
    _tile(pdf, left, y, w, "ผ่าน" if ok else ("ไม่ครบรอบ" if not soak.finished and not soak.problems else "มีข้อผิดปกติ"),
          f"ผล soak ล่าสุด ({soak.ended:%Y-%m-%d})" if soak.ended else "ผล soak ล่าสุด", "ok" if ok else "bad")
    _tile(pdf, left + w + gap, y, w, f"{soak.duration_s / 3600.0:.1f} ชม.", "ระยะเวลาที่ทดสอบ")
    _tile(pdf, left + 2 * (w + gap), y, w, f"{soak.reads:,}", f"อ่านทั้งหมด (พลาด {soak.fails:,})", "ok" if not soak.fails else "bad")
    return y + 19


def build_report_pdf(*, app_version: str, generated: datetime,
                     info: dict, settings: dict,
                     cabinet_label: str, cabinet_count: int,
                     widths: Sequence[int], records: Sequence,
                     hub_channel, events: Sequence[str] = (),
                     soak=None, soak_file: str = "") -> bytes:
    """`records` are fw_survey.ModuleRecord; `hub_channel(id)` maps a slave ID to its RS485 hub channel (0 = wired
    straight); `events` are the gateway's newest event-log lines (may be empty: older firmware); `soak` is a
    soak_csv.SoakSummary, the cabinet's latest soak run, when there is one (`soak_file` names the file it came from).

    Every fact the report has ever carried is still here. What changed is the order and the wording: page 1 answers
    "what is in this cabinet and is anything wrong" (figures, the gateway in a few lines, a map of the modules
    coloured by firmware, what deserves a look, and the soak result), and the sections after it hold the detail: the
    soak run, every module's identity and statistics grouped by hub channel with the health byte in words, the
    gateway's identity and settings, and its newest events."""
    pdf = _Report()
    pdf.alias_nb_pages()
    pdf.add_page()
    _summary_page(pdf, app_version=app_version, generated=generated, info=info, settings=settings,
                  cabinet_label=cabinet_label, cabinet_count=cabinet_count, widths=widths, records=records, soak=soak)

    # ── soak — the overnight evidence ─────────────────────────────────────
    if soak is not None:
        pdf.add_page()
        _soak_section(pdf, soak)
        if soak_file:
            _legend(pdf, f"จากไฟล์ {soak_file}")

    # ── modules: identity, grouped by hub channel ─────────────────────────
    pdf.add_page()
    answered = sum(1 for r in records if r.responded)
    _section(pdf, f"โมดูลทั้งหมด (ตอบ {answered}/{len(records)})")
    pdf.font(7.5)
    fail_style = FontFace(color=FAIL_RED, emphasis="BOLD")
    with pdf.table(col_widths=(9, 14, 20, 12, 11, 11, 44, 65),
                   text_align=("CENTER", "CENTER", "LEFT", "CENTER", "CENTER", "RIGHT", "LEFT", "LEFT"),
                   **_table_kw(line_height=4.0, padding=0.45)) as table:
        _headings(table, ("ID", "ช่อง hub", "ชนิด", "FW", "HW", "บูต", "สุขภาพ", "UID / หมายเหตุ"))
        last_ch = None
        for r in records:
            ch = hub_channel(r.device_id)
            if ch != last_ch:
                band = table.row()
                band.cell(f"ฮับช่อง {ch}" if ch else "ต่อตรง (ไม่ผ่านฮับ)", colspan=8,
                          style=FontFace(emphasis="BOLD", color=ACCENT, fill_color=GROUP_FILL))
                last_ch = ch
            row = table.row()
            row.cell(str(r.device_id))
            row.cell(str(ch) if ch else "-")
            if r.responded:
                row.cell(r.type_name)
                row.cell(r.fw)
                row.cell(_hw_name(r.hw_raw))
                row.cell(str(r.boots))
                text, healthy = _health_text(r)
                row.cell(text, style=None if healthy else fail_style)
                mismatch = (r.reported_id != r.device_id)
                row.cell(f"รายงาน id {r.reported_id}! " + r.uid if mismatch else r.uid,
                         style=fail_style if mismatch else None)
            else:
                row.cell("ไม่ตอบ", style=fail_style, colspan=6)
    _legend(pdf, "สุขภาพ: บิตที่ตั้งไว้ = ปกติ  (bit0 = AT24 EEPROM, bit1 = OLED, bit2 = เซนเซอร์ห้อง, bit3 = เซนเซอร์บอร์ด, "
                 "bit4 = สลักล็อกอยู่)  ·  แจ้งผิดปกติเฉพาะ EEPROM (bit0) หรือจอ OLED (bit1) เท่านั้น: เซนเซอร์ห้อง/บอร์ดเป็นชิ้นส่วนที่บอร์ด"
                 "อาจไม่มี (bit3 บน R5.x อ่านเป็น 0 เสมอ) และโมดูลชนิด 10 STANDARD ไม่มี OLED (ใช้ไฟ LED 8 ดวงแทน) จึงไม่นับ bit1  ·  บัสวิ่งที่ "
                 f"{dec_baud(int(settings.get('rs485.baud', 9600) or 9600))}")

    # ── module statistics — how much this cabinet has actually worked ─────
    with_stats = sum(1 for r in records if getattr(r, "stats", None))
    if with_stats:
        _ensure_room(pdf, 20 + (len(records) + 1) * 4.9)
        _section(pdf, f"สถิติของโมดูล ({with_stats}/{len(records)})")
        pdf.font(7)
        muted_style = FontFace(color=MUTED)
        with pdf.table(col_widths=(10, 25, 12, 12, 17, 17, 18, 27, 24, 24),
                       text_align=("CENTER",) + ("RIGHT",) * 9,
                       **_table_kw(line_height=4.0, padding=0.45)) as table:
            _headings(table, ("ID", "ทำงานมาแล้ว", "บูต", "IWDG", "กดปุ่ม",
                              "สลักทำงาน", "ไฟติด (ครั้ง)", "ไฟติด (เวลารวม)",
                              "อุณหภูมิห้อง °C", "กระแสไฟเลี้ยง mA"))
            for r in records:
                row = table.row()
                row.cell(str(r.device_id))
                s = getattr(r, "stats", None) if r.responded else None
                if s is None:
                    # Seven columns belong to the statistics block; one short
                    # and the live readings slide left into them.
                    row.cell("ไม่มีข้อมูล", style=muted_style)
                    for _ in range(6):
                        row.cell("")
                else:
                    row.cell(fmt_dur(s.op_seconds))
                    row.cell(str(r.boots))
                    row.cell(str(s.iwdg_resets), style=FontFace(color=FAIL_RED, emphasis="BOLD") if s.iwdg_resets else None)
                    row.cell(str(s.button_presses))
                    row.cell(str(s.latch_fires))
                    row.cell(f"{s.total_on_count:,}")
                    row.cell(fmt_dur(s.total_on_time_s))
                room = getattr(r, "room_raw", -1)
                if r.responded and 0 <= room != SENSOR_FAULT:
                    row.cell(f"{room / 100:.1f}")
                else:
                    row.cell("—")
                ma = getattr(r, "current_ma", -1)
                row.cell(str(ma) if r.responded and ma >= 0 else "—")
        _legend(pdf, "ยอดสะสมที่เก็บไว้ในตัวโมดูล (เฟิร์มแวร์ v3.3.0 ขึ้นไป; \"ไม่มีข้อมูล\" = เฟิร์มแวร์เก่าหรือไม่ตอบ)  ·  "
                     "ล้างได้ด้วย coil 510 / factory reset (จำนวนบูตไม่หาย)  ·  IWDG = watchdog รีเซ็ตโมดูล  ·  "
                     "อุณหภูมิห้องและกระแสไฟเลี้ยงเป็นค่าสดตอนอ่าน")

    # ── the gateway: identity, then every setting, for the record ─────────
    pdf.add_page()
    _section(pdf, "เกตเวย์")
    rows_text = ",".join(str(w) for w in widths) if widths else "-"
    _kv_block(pdf, (
        ("เฟิร์มแวร์", f"{info.get('fw', '?')}  ·  build {info.get('build', '?')}"),
        ("รหัสเกตเวย์ / MAC", f"{info.get('id', '?')}  ·  {info.get('mac', '?')}"),
        ("เครือข่าย", f"{info.get('net.state', '?')}  ·  {info.get('net.ip', '?')}:{info.get('net.port', '?')}"),
        ("watchdog", f"{info.get('sys.wdt', '?')} ms"),
        ("เวลาของเกตเวย์", f"{info.get('time.now', 'unset').replace('T', ' ')}  ·  NTP {info.get('ntp.state', '-')}"),
        ("reset ชั้นวางตามเวลา", str(info.get("sched.reset", "?"))),
        ("ตู้", f"{cabinet_label}  ·  {cabinet_count} โมดูล  ·  แถวละ {rows_text}  ·  hub map {settings.get('bus.hub_map', '-')}"),
    ))
    _ensure_room(pdf, _settings_height(settings))
    _section(pdf, "การตั้งค่าเกตเวย์")
    _settings_table(pdf, settings)
    _legend(pdf, "ชื่อและค่าดิบของคำสั่งคอนโซลอยู่ในไฟล์ส่งออกค่าตั้ง (หน้าเกตเวย์)  ·  ชื่อที่เห็นตามช่องกรอกของ Tool")

    # ── recent gateway events — what happened here lately ─────────────────
    if events:
        _ensure_room(pdf, len(events) * _SETTINGS_ROW_MM + 20)
        _section(pdf, f"เหตุการณ์ล่าสุดของเกตเวย์ (ใหม่สุดก่อน, {len(events)} รายการ)")
        _events_table(pdf, events)
        _legend(pdf, "เวลา — หมายถึงนาฬิกายังไม่ถูกตั้งตอนบันทึก (หลังไฟดับ)  ·  Uptime ใช้เรียงลำดับเหตุการณ์ในรอบบูตเดียวกัน")

    return bytes(pdf.output())
