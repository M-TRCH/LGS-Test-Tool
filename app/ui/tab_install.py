"""Installation Check tab: run a few real commands across many modules and
show the result as a map of the cabinet."""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..config_store import data_dir
from ..i18n import t
from ..fieldcheck import (CheckConfig, CheckDone, DeviceDone, DeviceStart,
                          PickConfig, PickLit, check_csv_bytes)
from ..lgs_map import CABINET_LAYOUTS, GRID_COLS, GRID_ROWS
from . import Ctx, helps, inline_warning

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
    state = {"seq": 0, "report": None, "testing": None, "waiting": set()}

    def paint(gid: int) -> None:
        # A result outranks "still lit": in the pick walkthrough a slot stays
        # in `waiting` until its light is confirmed off, and the moment it has
        # a result the operator should see that, not the amber.
        if gid in results:
            color = COLOR_PASS if results[gid] else COLOR_FAIL
        elif gid == state["testing"] or gid in state["waiting"]:
            color = COLOR_TESTING
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
            ui.label(t("ins.modules")).classes("font-bold")
            ui.button(t("ins.select_all"), on_click=lambda: set_selection(cells.keys())) \
                .props("flat dense no-caps")
            ui.button(t("btn.clear"), on_click=lambda: set_selection(())) \
                .props("flat dense no-caps")

            def from_scan() -> None:
                if not ctx.last_scan_ids:
                    ui.notify(t("ins.no_scan"),
                              type="warning")
                    return
                set_selection(g for g in ctx.last_scan_ids if g in cells)
                ui.notify(t("ins.from_scan_ok", n=len(selected)), type="positive")

            ui.button(t("ins.from_scan"), on_click=from_scan).props("flat dense no-caps")
            count_label = ui.label("").classes("text-sm text-grey")

        with ui.row().classes("items-center gap-2 flex-wrap"):
            helps(ui.label(t("ins.cabinet")).classes("text-sm text-grey"), t("ins.hint"))
            for layout in CABINET_LAYOUTS:
                def pick(layout=layout) -> None:
                    set_selection(layout.ids)
                    ui.notify(t("ins.cabinet_ok", label=layout.label, n=layout.count),
                              type="positive", timeout=1500)

                ui.button(layout.label, on_click=pick).props("outline dense no-caps") \
                    .tooltip(t("ins.cabinet_detail", rows=layout.rows, cols=layout.cols,
                               n=layout.count, first=layout.ids[0], last=layout.ids[-1]))

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
        count_label.set_text(t("ins.selected", n=len(selected)))

    update_count()

    # ── what to run ────────────────────────────────────────────────────────
    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("ins.what")).classes("font-bold"), t("ins.always"))
            with ui.column().classes("gap-1 q-mt-sm"):
                cb_light = ui.checkbox(t("ins.do_light"), value=True)
                cb_display = ui.checkbox(t("ins.do_display"), value=False) \
                    .tooltip(t("ins.do_display_tip"))
                cb_identify = ui.checkbox(t("ins.do_identify"), value=False)
            hold = ui.number(t("ins.hold"), value=1.0, min=0.2, max=5, step=0.1) \
                .props("dense outlined").classes("w-44 q-mt-sm")

        with ui.card().classes("p-3 grow border border-orange-400"):
            with ui.row().classes("items-center gap-2"):
                ui.label(t("ins.unlock_card")).classes("font-bold text-orange")
            cb_unlock = helps(ui.checkbox(t("ins.do_unlock"), value=False),
                              t("ins.cooldown_note"))
            # Stays on screen: it is a live warning about what will happen.
            unlock_caption = inline_warning("text-red text-sm")

        # ── pick walkthrough: the dispensing flow as a test ────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("ins.pick_card")).classes("font-bold"),
                  t("ins.pick_hint"))
            with ui.row().classes("gap-2 items-center q-mt-sm flex-wrap"):
                pick_preset = ui.select({n: f"Preset {n}" for n in range(1, 9)},
                                        value=1, label=t("ins.pick_preset")) \
                    .props("dense outlined").classes("w-36")
                pick_batch = ui.number(t("ins.pick_batch"), value=4,
                                       min=0, max=16, format="%d") \
                    .props("dense outlined").classes("w-36") \
                    .tooltip(t("ins.pick_batch_tip"))
                pick_timeout = ui.number(t("ins.pick_timeout"), value=60,
                                         min=0, max=600, format="%d") \
                    .props("dense outlined").classes("w-36") \
                    .tooltip(t("ins.pick_timeout_tip"))
            pick_btn = ui.button(t("ins.pick_run"), color="primary") \
                .props("outline").classes("q-mt-sm")

    def make_cfg() -> CheckConfig:
        return CheckConfig(light=bool(cb_light.value), unlock=bool(cb_unlock.value),
                           display=bool(cb_display.value),
                           identify=bool(cb_identify.value), hold_s=float(hold.value))

    def update_caption() -> None:
        n = make_cfg().unlock_count(len(selected))
        unlock_caption.set_text(t("ins.warn_unlock", n=n) if n else "")

    cb_unlock.on_value_change(update_caption)

    # ── run + results ──────────────────────────────────────────────────────
    with ui.row().classes("items-center gap-3 flex-wrap"):
        run_btn = ui.button(t("ins.run"), color="primary")
        ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_field_check()).props("outline")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        progress_label = ui.label(t("mt.idle")).classes("font-mono text-sm")
        banner = ui.badge("—").props("color=grey")

    summary = ui.label("").classes("text-sm")

    table = ui.table(
        columns=[
            {"name": "id", "label": t("col.id"), "field": "id", "align": "left"},
            {"name": "type", "label": t("col.type"), "field": "type", "align": "left"},
            {"name": "result", "label": t("col.result"), "field": "result", "align": "left"},
            {"name": "detail", "label": t("col.detail"), "field": "detail", "align": "left"},
        ],
        rows=[], row_key="id").props("dense flat").classes("w-full text-xs")

    def export() -> None:
        report = state["report"]
        if report is None:
            ui.notify(t("msg.no_result"), type="warning")
            return
        path = data_dir() / "exports"
        path.mkdir(exist_ok=True)
        fn = path / f"install_check_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
        fn.write_bytes(check_csv_bytes(report))
        ui.download(str(fn))
        ui.notify(t("msg.saved", name=fn.name), type="positive")

    ui.button(t("btn.export_csv"), on_click=export).props("flat dense")

    def _reset_run_ui() -> bool:
        if not worker.get_state().connected:
            ui.notify(t("msg.not_connected"), type="negative")
            return False
        if not selected:
            ui.notify(t("ins.select_one"), type="warning")
            return False
        results.clear()
        state["waiting"] = set()
        state["testing"] = None
        repaint_all()
        table.rows = []
        table.update()
        state["report"] = None
        summary.set_text("")
        banner.set_text(t("res.running"))
        banner.props("color=blue")
        progress.set_value(0.0)
        return True

    def start() -> None:
        if not _reset_run_ui():
            return
        state["pick_mode"] = False
        if not worker.start_field_check(make_cfg(), sorted(selected)):
            ui.notify(t("msg.worker_busy"), type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    run_btn.on_click(start)

    def start_pick() -> None:
        if not _reset_run_ui():
            return
        state["pick_mode"] = True
        cfg = PickConfig(preset=int(pick_preset.value or 1),
                         timeout_s=float(pick_timeout.value or 0),
                         batch=int(pick_batch.value or 0))
        if not worker.start_pick_sequence(cfg, sorted(selected)):
            ui.notify(t("msg.worker_busy"), type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    pick_btn.on_click(start_pick)

    def drain() -> None:
        state["seq"], events = worker.drain_field_check_events(state["seq"])
        for ev in events:
            if isinstance(ev, DeviceStart):
                prev, state["testing"] = state["testing"], ev.device_id
                if prev is not None:
                    paint(prev)
                paint(ev.device_id)
                progress.set_value((ev.index - 1) / max(1, ev.total))
                progress_label.set_text(
                    t("ins.pick_preparing", id=ev.device_id, i=ev.index,
                      total=ev.total)
                    if state.get("pick_mode") else
                    t("ins.module_progress", id=ev.device_id, i=ev.index, total=ev.total))
            elif isinstance(ev, PickLit):
                # Every slot in this batch is lit and waiting for its person.
                state["testing"] = None
                state["waiting"] = set(ev.ids)
                state["pick_total"] = ev.total
                repaint_all()
                progress.set_value(len(results) / max(1, ev.total))
                progress_label.set_text(t("ins.pick_waiting", n=len(ev.ids)))
            elif isinstance(ev, DeviceDone):
                r = ev.result
                state["testing"] = None
                state["waiting"].discard(r.device_id)
                results[r.device_id] = r.ok
                paint(r.device_id)
                if state.get("pick_mode") and state["waiting"]:
                    progress.set_value(len(results)
                                       / max(1, state.get("pick_total", 1)))
                    progress_label.set_text(
                        t("ins.pick_waiting", n=len(state["waiting"])))
                detail = "; ".join(f"{s.label}: {'ok' if s.ok else 'FAIL'}"
                                   + (f" ({s.note})" if s.note and not s.ok else "")
                                   for s in r.steps)
                table.rows.append({
                    "id": r.device_id,
                    "type": r.type_name or "—",
                    "result": t("ins.res.pass") if r.ok else (t("ins.res.no_answer") if not r.responded
                                                     else t("ins.res.fail")),
                    "detail": detail,
                })
            elif isinstance(ev, CheckDone):
                state["report"] = ev.report
                state["testing"] = None
                state["waiting"] = set()
                progress.set_value(1.0)
                rep = ev.report
                missing = rep.missing
                failed = rep.failed
                progress_label.set_text(t("ins.done", n=len(rep.results)))
                if rep.cancelled:
                    banner.set_text(t("res.cancelled"))
                    banner.props("color=grey")
                elif rep.passed:
                    banner.set_text(t("ins.all_pass"))
                    banner.props("color=green")
                else:
                    banner.set_text(t("ins.issues"))
                    banner.props("color=red")
                parts = [t("ins.answered", n=len(rep.responded), total=len(rep.results))]
                if missing:
                    parts.append(t("ins.no_answer", ids=", ".join(str(i) for i in missing)))
                if failed:
                    parts.append(t("ins.step_failed", ids=", ".join(str(i) for i in failed)))
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
