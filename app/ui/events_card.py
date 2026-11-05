"""Event collector card (Gateway tab) -- a view over app/event_collector.py.

Switch it on and the server pulls every fleet gateway's event log into
data/events/ on a timer. The card only shows the last result per gateway;
reading the files is what the Events page of v2.0 is for.
"""
from __future__ import annotations

from nicegui import ui

from .. import config_store, event_collector
from ..i18n import t
from . import Ctx, helps


def build(ctx: Ctx) -> None:
    cfg = ctx.cfg
    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("evc.card")).classes("font-bold"), t("evc.hint"))
        lines = ui.column().classes("gap-0")

        def refresh() -> None:
            lines.clear()
            with lines:
                if not cfg.events_enabled:
                    ui.label(t("evc.off")).classes("text-sm text-grey")
                    return
                st = event_collector.status()
                if not st:
                    ui.label(t("evc.waiting")).classes("text-sm text-grey")
                for name, r in sorted(st.items()):
                    ok = r.get("ok")
                    txt = (t("evc.ok", name=name, n=r.get("new", 0), at=r.get("at", "")[11:])
                           if ok else t("evc.err", name=name, e=r.get("error", "")))
                    ui.label(txt).classes("text-sm " + ("text-positive" if ok else "text-negative"))

        def toggle(e) -> None:
            cfg.events_enabled = bool(e.value)
            config_store.save(cfg)
            event_collector.apply(cfg)
            refresh()

        with ui.row().classes("items-center gap-3 flex-wrap"):
            helps(ui.switch(t("evc.enable"), value=cfg.events_enabled, on_change=toggle)
                  .props("dense"), t("evc.enable_tip"))
            ui.label(t("evc.where", path=str(event_collector.events_root()))) \
                .classes("text-xs text-grey")
        refresh()
        ui.timer(15.0, refresh)
