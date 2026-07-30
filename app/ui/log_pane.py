"""Global transaction log pane (all sources) with filter + CSV export.

Log lines themselves stay in English in both languages: they mirror the wire
(function codes, addresses, raw hex) and are meant to be pasted into reports.
"""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from ..config_store import data_dir
from ..i18n import t
from . import Ctx


def build(ctx: Ctx) -> None:
    with ui.expansion(t("log.title"), icon="receipt_long", value=True).classes("w-full"):
        with ui.row().classes("items-center gap-2"):
            paused = ui.switch(t("log.pause"), value=False).props("dense")
            source_filter = ui.select({"all": t("log.all"), "manual": "manual",
                                       "monitor": "monitor", "sweep": "sweep",
                                       "check": "check", "scan": "scan", "danger": "danger"},
                                      value="all", label=t("log.filter")) \
                .props("dense outlined").classes("w-32")
            ui.button(t("btn.clear"), on_click=lambda: (ctx.log.clear(), log_view.clear())) \
                .props("flat dense")

            def export() -> None:
                path = data_dir() / "exports"
                path.mkdir(exist_ok=True)
                fn = path / f"txn_log_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.csv"
                fn.write_bytes(ctx.log.to_csv_bytes())
                ui.download(str(fn))
                ui.notify(t("msg.saved", name=fn.name), type="positive")

            ui.button(t("btn.export_csv"), on_click=export).props("flat dense")

        log_view = ui.log(max_lines=400).classes("w-full h-64 font-mono text-xs")

        state = {"seq": 0}

        def drain() -> None:
            state["seq"], fresh = ctx.log.since(state["seq"])
            if paused.value:
                return
            flt = source_filter.value
            for rec in fresh:
                if flt != "all" and rec.source != flt:
                    continue
                log_view.push(rec.line())

        ui.timer(0.2, drain)
