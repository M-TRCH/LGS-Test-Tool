"""Installation Check tab: run a few real commands across many modules and
show the result as a map of the cabinet."""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..config_store import data_dir
from ..fieldcheck import (CheckConfig, CheckDone, DeviceDone, DeviceStart,
                          check_csv_bytes)
from ..lgs_map import GRID_COLS, GRID_ROWS
from . import Ctx

COLOR_UNSELECTED = "grey-5"
COLOR_SELECTED = "primary"
COLOR_TESTING = "amber"
COLOR_PASS = "positive"
COLOR_FAIL = "negative"


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    cells: dict[int, ui.button] = {}
    selected: set[int] = set()
    results: dict[int, bool] = {}
    state = {"seq": 0, "report": None, "testing": None}

    def paint(gid: int) -> None:
        if gid == state["testing"]:
            color = COLOR_TESTING
        elif gid in results:
            color = COLOR_PASS if results[gid] else COLOR_FAIL
        else:
            color = COLOR_SELECTED if gid in selected else COLOR_UNSELECTED
        cells[gid].props(f"color={color}")

    def repaint_all() -> None:
        for gid in cells:
            paint(gid)

    def toggle(gid: int) -> None:
        selected.discard(gid) if gid in selected else selected.add(gid)
        results.pop(gid, None)
        paint(gid)
        update_count()

    def set_selection(ids) -> None:
        selected.clear()
        selected.update(ids)
        results.clear()
        repaint_all()
        update_count()

    # ── target picker ──────────────────────────────────────────────────────
    with ui.card().classes("p-3 w-full"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            ui.label("Modules to check").classes("font-bold")
            ui.button("Select all", on_click=lambda: set_selection(cells.keys())) \
                .props("flat dense no-caps")
            ui.button("Clear", on_click=lambda: set_selection(())) \
                .props("flat dense no-caps")

            def from_scan() -> None:
                if not ctx.last_scan_ids:
                    ui.notify("no scan result yet — run Scan in the header first",
                              type="warning")
                    return
                set_selection(g for g in ctx.last_scan_ids if g in cells)
                ui.notify(f"selected {len(selected)} module(s) found by the last scan",
                          type="positive")

            ui.button("From last scan", on_click=from_scan).props("flat dense no-caps")
            count_label = ui.label("").classes("text-sm text-grey")

        ui.label("Click a cell to include it; the row button toggles a whole row. "
                 "Cells turn green when the module passes, red when it does not answer.") \
            .classes("text-xs text-grey")

        with ui.column().classes("gap-1 q-mt-sm"):
            for r in range(1, GRID_ROWS + 1):
                with ui.row().classes("gap-1 flex-nowrap items-center"):
                    row_ids = [r * 10 + c for c in range(1, GRID_COLS + 1)]

                    def toggle_row(ids=row_ids) -> None:
                        if all(i in selected for i in ids):
                            for i in ids:
                                selected.discard(i)
                        else:
                            selected.update(ids)
                        for i in ids:
                            results.pop(i, None)
                            paint(i)
                        update_count()

                    ui.button(f"R{r}", on_click=toggle_row) \
                        .props("flat dense no-caps size=sm").classes("w-10 min-w-0 text-grey")
                    for gid in row_ids:
                        cells[gid] = ui.button(
                            str(gid), on_click=lambda gid=gid: toggle(gid)) \
                            .props(f"unelevated no-caps color={COLOR_UNSELECTED}") \
                            .classes("w-14 min-w-0 font-mono")

    def update_count() -> None:
        count_label.set_text(f"{len(selected)} selected")

    update_count()

    # ── what to run ────────────────────────────────────────────────────────
    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        with ui.card().classes("p-3 grow"):
            ui.label("What to do on each module").classes("font-bold")
            ui.label("Always included — check that the module answers on the bus "
                     "(reads its device type).").classes("text-xs text-grey")
            with ui.column().classes("gap-1 q-mt-sm"):
                cb_light = ui.checkbox("Turn the light on, then off (1001)", value=True)
                cb_display = ui.checkbox("Show its number on the display "
                                         "(reg 60 + 1010)", value=False) \
                    .tooltip("Shows the slave ID; IDs above 99 show the column number "
                             "because the display holds two digits")
                cb_identify = ui.checkbox("Identify — blink white ~5 s (509)", value=False)
            hold = ui.number("Hold each step (s)", value=1.0, min=0.2, max=5, step=0.1) \
                .props("dense outlined").classes("w-44 q-mt-sm")

        with ui.card().classes("p-3 grow border border-orange-400"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("lock_open").classes("text-orange")
                ui.label("Unlock — moves the physical latch").classes("font-bold")
            cb_unlock = ui.checkbox("Light + unlock each module (1021)", value=False)
            unlock_caption = ui.label("").classes("text-red text-sm")
            ui.label("Each module keeps its own 2 s cooldown, so a sweep across "
                     "different modules is not slowed down.").classes("text-xs text-grey")

    def make_cfg() -> CheckConfig:
        return CheckConfig(light=bool(cb_light.value), unlock=bool(cb_unlock.value),
                           display=bool(cb_display.value),
                           identify=bool(cb_identify.value), hold_s=float(hold.value))

    def update_caption() -> None:
        n = make_cfg().unlock_count(len(selected))
        unlock_caption.set_text(f"⚠ this run will unlock {n} module(s)" if n else "")

    cb_unlock.on_value_change(update_caption)

    # ── run + results ──────────────────────────────────────────────────────
    with ui.row().classes("items-center gap-3 flex-wrap"):
        run_btn = ui.button("Run check", color="primary")
        ui.button("Cancel", on_click=lambda: worker.cancel_field_check()).props("outline")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        progress_label = ui.label("idle").classes("font-mono text-sm")
        banner = ui.badge("—").props("color=grey")

    summary = ui.label("").classes("text-sm")

    table = ui.table(
        columns=[
            {"name": "id", "label": "ID", "field": "id", "align": "left"},
            {"name": "type", "label": "type", "field": "type", "align": "left"},
            {"name": "result", "label": "result", "field": "result", "align": "left"},
            {"name": "detail", "label": "detail", "field": "detail", "align": "left"},
        ],
        rows=[], row_key="id").props("dense flat").classes("w-full text-xs")

    def export() -> None:
        report = state["report"]
        if report is None:
            ui.notify("no completed check yet", type="warning")
            return
        path = data_dir() / "exports"
        path.mkdir(exist_ok=True)
        fn = path / f"install_check_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
        fn.write_bytes(check_csv_bytes(report))
        ui.download(str(fn))
        ui.notify(f"saved {fn.name}", type="positive")

    ui.button("Export CSV", on_click=export).props("flat dense")

    def start() -> None:
        if not worker.get_state().connected:
            ui.notify("not connected", type="negative")
            return
        if not selected:
            ui.notify("select at least one module", type="warning")
            return
        results.clear()
        repaint_all()
        table.rows = []
        table.update()
        state["report"] = None
        summary.set_text("")
        banner.set_text("RUNNING")
        banner.props("color=blue")
        progress.set_value(0.0)
        ids = sorted(selected)
        if not worker.start_field_check(make_cfg(), ids):
            ui.notify("worker busy — cannot start now", type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    run_btn.on_click(start)

    def drain() -> None:
        state["seq"], events = worker.drain_field_check_events(state["seq"])
        for ev in events:
            if isinstance(ev, DeviceStart):
                prev, state["testing"] = state["testing"], ev.device_id
                if prev is not None:
                    paint(prev)
                paint(ev.device_id)
                progress.set_value((ev.index - 1) / max(1, ev.total))
                progress_label.set_text(f"module {ev.device_id} ({ev.index}/{ev.total})")
            elif isinstance(ev, DeviceDone):
                r = ev.result
                state["testing"] = None
                results[r.device_id] = r.ok
                paint(r.device_id)
                detail = "; ".join(f"{s.label}: {'ok' if s.ok else 'FAIL'}"
                                   + (f" ({s.note})" if s.note and not s.ok else "")
                                   for s in r.steps)
                table.rows.append({
                    "id": r.device_id,
                    "type": r.type_name or "—",
                    "result": "✓ pass" if r.ok else ("✗ no answer" if not r.responded
                                                     else "✗ fail"),
                    "detail": detail,
                })
            elif isinstance(ev, CheckDone):
                state["report"] = ev.report
                state["testing"] = None
                progress.set_value(1.0)
                rep = ev.report
                missing = rep.missing
                failed = rep.failed
                progress_label.set_text(f"done — {len(rep.results)} module(s)")
                if rep.cancelled:
                    banner.set_text("CANCELLED")
                    banner.props("color=grey")
                elif rep.passed:
                    banner.set_text("ALL PASS")
                    banner.props("color=green")
                else:
                    banner.set_text("ISSUES FOUND")
                    banner.props("color=red")
                parts = [f"answered {len(rep.responded)}/{len(rep.results)}"]
                if missing:
                    parts.append("no answer: " + ", ".join(str(i) for i in missing))
                if failed:
                    parts.append("failed a step: " + ", ".join(str(i) for i in failed))
                summary.set_text(" · ".join(parts))
                try:
                    path = data_dir() / "exports"
                    path.mkdir(exist_ok=True)
                    fn = path / f"install_check_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
                    fn.write_bytes(check_csv_bytes(rep))
                except OSError:
                    pass
        if events:
            table.update()

    ui.timer(0.2, drain)
