"""Auto Test tab: run the ported sweep with live progress, results, CSV export."""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..config_store import data_dir
from ..testsuite import Done, PhaseEnd, PhaseStart, Step, SweepConfig, sweep_csv_bytes
from . import Ctx

MAX_TABLE_ROWS = 200


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"seq": 0, "report": None, "rows": 0}

    with ui.row().classes("items-center gap-3 flex-wrap"):
        loops = ui.number("loops", value=1, min=1, max=10, format="%d") \
            .props("dense outlined").classes("w-20")
        cb_led = ui.checkbox("LED phases (PRESET/DISPLAY/LED)", value=True)
        cb_latch = ui.checkbox("Latch phase (fires the solenoid!)", value=False)
        fires = ui.number("fires", value=1, min=1, max=5, format="%d") \
            .props("dense outlined").classes("w-20")
        cb_force = ui.checkbox("force 1019", value=True)
        cb_combos = ui.checkbox("combos 1022/1031", value=False)
        cb_1021 = ui.checkbox("1021", value=False)
    fire_caption = ui.label("").classes("text-red text-sm")

    def make_cfg() -> SweepConfig:
        return SweepConfig(loops=int(loops.value), include_led=bool(cb_led.value),
                           include_latch=bool(cb_latch.value), latch_fires=int(fires.value),
                           include_force=bool(cb_force.value),
                           include_combos=bool(cb_combos.value),
                           include_1021=bool(cb_1021.value))

    def update_caption() -> None:
        total = make_cfg().latch_total_fires()
        fire_caption.set_text(f"⚠ the latch phase will FIRE THE SOLENOID {total} time(s)"
                              if total else "")

    for el in (loops, cb_latch, fires, cb_force, cb_combos, cb_1021):
        el.on_value_change(update_caption)

    with ui.row().classes("items-center gap-3"):
        run_btn = ui.button("Run Sweep", color="primary")
        cancel_btn = ui.button("Cancel", on_click=lambda: worker.cancel_sweep()).props("outline")
        phase_label = ui.label("idle").classes("font-mono")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        b_ok = ui.badge("OK 0").props("color=green")
        b_fail = ui.badge("FAIL 0").props("color=red")
        b_err = ui.badge("ERR 0").props("color=orange")
        banner = ui.badge("—").props("color=grey")

    table = ui.table(
        columns=[
            {"name": "t", "label": "time", "field": "t", "align": "left"},
            {"name": "phase", "label": "phase", "field": "phase", "align": "left"},
            {"name": "fc", "label": "fc", "field": "fc"},
            {"name": "addr", "label": "addr", "field": "addr"},
            {"name": "name", "label": "name", "field": "name", "align": "left"},
            {"name": "op", "label": "op", "field": "op", "align": "left"},
            {"name": "value", "label": "value/check", "field": "value", "align": "left"},
            {"name": "result", "label": "result", "field": "result", "align": "left"},
            {"name": "ms", "label": "ms", "field": "ms"},
        ],
        rows=[], row_key="i").props("dense flat").classes("w-full text-xs")
    ui.label(f"(table shows the last {MAX_TABLE_ROWS} steps — the CSV export has everything)") \
        .classes("text-xs text-grey")

    def export() -> None:
        report = state["report"]
        if report is None:
            ui.notify("no completed sweep yet", type="warning")
            return
        path = data_dir() / "exports"
        path.mkdir(exist_ok=True)
        fn = path / f"sweep_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
        fn.write_bytes(sweep_csv_bytes(report))
        ui.download(str(fn))
        ui.notify(f"saved {fn.name}", type="positive")

    ui.button("Export CSV", on_click=export).props("flat dense")

    def start() -> None:
        cfg = make_cfg()
        st = worker.get_state()
        if not st.connected:
            ui.notify("not connected", type="negative")
            return
        table.rows = []
        table.update()
        state["report"] = None
        state["rows"] = 0
        for b, txt in ((b_ok, "OK 0"), (b_fail, "FAIL 0"), (b_err, "ERR 0")):
            b.set_text(txt)
        banner.set_text("RUNNING")
        banner.props("color=blue")
        progress.set_value(0.0)
        if not worker.start_sweep(cfg, ctx.device_id()):
            ui.notify("worker busy — cannot start sweep", type="negative")
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
                phase_label.set_text(f"{ev.name} ({ev.index}/{ev.total})")
                progress.set_value((ev.index - 1) / max(1, ev.total))
            elif isinstance(ev, Step):
                s = ev.step
                state["rows"] += 1
                table.rows.append({
                    "i": state["rows"],
                    "t": s.ts.strftime("%H:%M:%S"),
                    "phase": s.phase, "fc": s.fc, "addr": s.addr, "name": s.name,
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
                t = ev.report.totals
                if ev.report.cancelled:
                    banner.set_text("CANCELLED")
                    banner.props("color=grey")
                elif ev.report.passed:
                    banner.set_text("PASS")
                    banner.props("color=green")
                else:
                    banner.set_text("FAIL")
                    banner.props("color=red")
                phase_label.set_text(f"done — {t.ok + t.fail + t.err} steps")
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
                t = src.totals
                ok, fail, err = t.ok, t.fail, t.err
            b_ok.set_text(f"OK {ok}")
            b_fail.set_text(f"FAIL {fail}")
            b_err.set_text(f"ERR {err}")
        table.update()

    ui.timer(0.2, drain)
