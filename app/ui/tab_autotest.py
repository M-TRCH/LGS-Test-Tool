"""Auto Test tab: run the ported sweep with live progress, results, CSV export."""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..config_store import data_dir
from ..i18n import t
from ..testsuite import Done, PhaseEnd, PhaseStart, Step, SweepConfig, sweep_csv_bytes
from . import Ctx, helps, inline_warning

MAX_TABLE_ROWS = 200

# Phase names are shown through i18n keys "phase.<RAW>"; the raw names
# (READ / WRITE / …) stay in the CSV so exports remain comparable.


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"seq": 0, "report": None, "rows": 0}

    # Options are written in plain language; the raw coil/register numbers stay
    # in parentheses (same convention as the Control tab) for anyone checking
    # against the control table.
    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("mt.what")).classes("font-bold"), t("mt.always"))
            with ui.row().classes("items-center gap-4 flex-wrap q-mt-sm"):
                cb_led = ui.checkbox(t("mt.lights"), value=True).tooltip(t("mt.lights_tip"))
                loops = ui.number(t("mt.repeat"), value=1, min=1, max=10, format="%d") \
                    .props("dense outlined").classes("w-24")

        with ui.card().classes("p-3 grow border border-orange-400"):
            with ui.row().classes("items-center gap-2"):
                ui.label(t("mt.unlock_card")).classes("font-bold text-orange")
            cb_latch = ui.checkbox(t("mt.include_unlock"), value=False)
            with ui.column().classes("gap-1 q-pl-md"):
                fires = helps(ui.number(t("mt.unlocks_per_round"), value=1, min=1, max=5,
                                        format="%d")
                              .props("dense outlined").classes("w-40")
                              .bind_enabled_from(cb_latch, "value"),
                              t("mt.always_safety"))
                cb_force = ui.checkbox(t("mt.also_force"), value=True) \
                    .bind_enabled_from(cb_latch, "value")
                cb_combos = ui.checkbox(t("mt.also_combo"), value=False) \
                    .bind_enabled_from(cb_latch, "value")
                cb_1021 = ui.checkbox(t("mt.also_1021"), value=False) \
                    .bind_enabled_from(cb_latch, "value")
            fire_caption = inline_warning("text-red text-sm")

    def make_cfg() -> SweepConfig:
        return SweepConfig(loops=int(loops.value), include_led=bool(cb_led.value),
                           include_latch=bool(cb_latch.value), latch_fires=int(fires.value),
                           include_force=bool(cb_force.value),
                           include_combos=bool(cb_combos.value),
                           include_1021=bool(cb_1021.value))

    def update_caption() -> None:
        total = make_cfg().latch_total_fires()
        fire_caption.set_text(t("mt.warn_unlock", n=total) if total else "")

    for el in (loops, cb_latch, fires, cb_force, cb_combos, cb_1021):
        el.on_value_change(update_caption)

    with ui.row().classes("items-center gap-3"):
        run_btn = ui.button(t("mt.run"), color="primary")
        cancel_btn = ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_sweep()).props("outline")
        phase_label = ui.label(t("mt.idle")).classes("font-mono")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        b_ok = ui.badge("OK 0").props("color=green")
        b_fail = ui.badge("FAIL 0").props("color=red")
        b_err = ui.badge("ERR 0").props("color=orange")
        banner = ui.badge("—").props("color=grey")

    table = ui.table(
        columns=[
            {"name": "t", "label": t("col.time"), "field": "t", "align": "left"},
            {"name": "phase", "label": t("col.phase"), "field": "phase", "align": "left"},
            {"name": "fc", "label": "fc", "field": "fc"},
            {"name": "addr", "label": t("col.addr"), "field": "addr"},
            {"name": "name", "label": t("col.name"), "field": "name", "align": "left"},
            {"name": "op", "label": t("col.op"), "field": "op", "align": "left"},
            {"name": "value", "label": t("col.value"), "field": "value", "align": "left"},
            {"name": "result", "label": t("col.result"), "field": "result", "align": "left"},
            {"name": "ms", "label": "ms", "field": "ms"},
        ],
        rows=[], row_key="i").props("dense flat").classes("w-full text-xs")
    # Stays on screen: this describes what you are looking at (the table is
    # truncated), not how a control works.
    ui.label(t("mt.table_note", n=MAX_TABLE_ROWS)).classes("text-xs text-grey")

    def export() -> None:
        report = state["report"]
        if report is None:
            ui.notify(t("msg.no_result"), type="warning")
            return
        path = data_dir() / "exports"
        path.mkdir(exist_ok=True)
        fn = path / f"sweep_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
        fn.write_bytes(sweep_csv_bytes(report))
        ui.download(str(fn))
        ui.notify(t("msg.saved", name=fn.name), type="positive")

    ui.button(t("btn.export_csv"), on_click=export).props("flat dense")

    def start() -> None:
        cfg = make_cfg()
        st = worker.get_state()
        if not st.connected:
            ui.notify(t("msg.not_connected"), type="negative")
            return
        table.rows = []
        table.update()
        state["report"] = None
        state["rows"] = 0
        for b, txt in ((b_ok, "OK 0"), (b_fail, "FAIL 0"), (b_err, "ERR 0")):
            b.set_text(txt)
        banner.set_text(t("res.running"))
        banner.props("color=blue")
        progress.set_value(0.0)
        if not worker.start_sweep(cfg, ctx.device_id()):
            ui.notify(t("msg.worker_busy"), type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    run_btn.on_click(start)

    def drain() -> None:
        state["seq"], events = worker.drain_sweep_events(state["seq"])
        if not events:
            return
        totals = None
        for ev in events:
            if isinstance(ev, PhaseStart):
                phase_label.set_text(t("mt.phase", name=t("phase." + ev.name),
                                       i=ev.index, total=ev.total))
                progress.set_value((ev.index - 1) / max(1, ev.total))
            elif isinstance(ev, Step):
                s = ev.step
                state["rows"] += 1
                table.rows.append({
                    "i": state["rows"],
                    "t": s.ts.strftime("%H:%M:%S"),
                    "phase": t("phase." + s.phase),
                    "fc": s.fc, "addr": s.addr, "name": s.name,
                    "op": s.op,
                    "value": (s.decoded or str(s.raw)) + (f" | {s.note}" if s.note else ""),
                    "result": {"OK": "✓ OK", "FAIL": "✗ FAIL"}.get(s.result, "⚠ ERR"),
                    "ms": f"{s.latency_ms:.0f}",
                })
                if len(table.rows) > MAX_TABLE_ROWS:
                    table.rows = table.rows[-MAX_TABLE_ROWS:]
            elif isinstance(ev, PhaseEnd):
                pass
            elif isinstance(ev, Done):
                state["report"] = ev.report
                progress.set_value(1.0)
                tot = ev.report.totals
                if ev.report.cancelled:
                    banner.set_text(t("res.cancelled"))
                    banner.props("color=grey")
                elif ev.report.passed:
                    banner.set_text(t("res.pass"))
                    banner.props("color=green")
                else:
                    banner.set_text(t("res.fail"))
                    banner.props("color=red")
                phase_label.set_text(t("mt.done_steps", n=tot.ok + tot.fail + tot.err))
                # autosave
                try:
                    path = data_dir() / "exports"
                    path.mkdir(exist_ok=True)
                    fn = path / f"sweep_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
                    fn.write_bytes(sweep_csv_bytes(ev.report))
                except OSError:
                    pass
        report = state["report"]
        if events:
            # recompute counters from the live per-phase stats of the current run
            src = report if report is not None else None
            if src is None:
                ok = sum(1 for r in table.rows if "OK" in r["result"])
                fail = sum(1 for r in table.rows if "FAIL" in r["result"])
                err = sum(1 for r in table.rows if "ERR" in r["result"])
            else:
                tot = src.totals
                ok, fail, err = tot.ok, tot.fail, tot.err
            b_ok.set_text(f"OK {ok}")
            b_fail.set_text(f"FAIL {fail}")
            b_err.set_text(f"ERR {err}")
        table.update()

    ui.timer(0.2, drain)
