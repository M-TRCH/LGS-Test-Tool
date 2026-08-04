"""Commissioning tab: flash a new module and give it its Modbus ID at once.

Everything here runs over ST-Link, not the bus — the module usually is not
wired to RS485 yet. That is also why nothing on this page needs a connection.
"""
from __future__ import annotations

from pathlib import Path

from nicegui import ui

from .. import commission_image as ci
from ..commission import CommissionConfig
from ..config_store import data_dir
from ..i18n import t
from ..lgs_map import GRID_COLS, GRID_ROWS, valid_assignable_id
from ..ota import Done, Line, Progress
from . import Ctx, helps, warning_banner

LEVEL_CLASS = {"info": "", "ok": "text-green", "warn": "text-orange", "err": "text-red"}


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state: dict = {"seq": 0, "image": b"", "name": ""}

    warning_banner(t("cm.banner"))

    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        # ── the image ──────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("cm.image")).classes("font-bold"), t("cm.image_hint"))

            def on_upload(e) -> None:
                data = e.content.read()
                state["image"], state["name"] = data, e.name
                try:
                    block = ci.find_block(data)
                except ci.ImageError as exc:
                    state["image"] = b""
                    image_label.set_text(str(exc))
                    image_label.classes(add="text-red", remove="text-green")
                    return
                image_label.set_text(t("cm.image_ok", name=e.name,
                                       size=f"{len(data):,}",
                                       detail=ci.describe(block)))
                image_label.classes(add="text-green", remove="text-red")

            ui.upload(on_upload=on_upload, auto_upload=True, max_files=1) \
                .props('accept=".bin" flat dense').classes("w-full")
            image_label = ui.label(t("cm.no_image")).classes("text-sm")

        # ── the identity to give it ────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("cm.identity")).classes("font-bold"), t("cm.identity_hint"))
            id_input = ui.number(t("cm.slave_id"), value=ctx.device_id(),
                                 min=1, max=245, format="%d") \
                .props("dense outlined").classes("w-40")

            with ui.button(t("cm.grid")).props("dense flat no-caps") \
                    .classes("q-mt-sm"):
                with ui.menu() as grid_menu:
                    with ui.column().classes("gap-1 p-3"):
                        for r in range(1, GRID_ROWS + 1):
                            with ui.row().classes("gap-1 flex-nowrap"):
                                for c in range(1, GRID_COLS + 1):
                                    gid = r * 10 + c

                                    def pick(g=gid) -> None:
                                        id_input.set_value(g)
                                        grid_menu.close()

                                    ui.button(str(gid), on_click=pick) \
                                        .props("unelevated dense no-caps") \
                                        .classes("w-12 min-w-0 font-mono")

            lot_input = helps(
                ui.input(t("cm.lot")).props("dense outlined").classes("w-40 q-mt-sm"),
                t("cm.lot_hint"))

        # ── overwriting a module that already has an ID ────────────────────
        with ui.card().classes("p-3 grow border border-orange-400"):
            ui.label(t("cm.overwrite_card")).classes("font-bold text-orange")
            cb_overwrite = ui.checkbox(t("cm.overwrite"), value=False)
            ui.label(t("cm.overwrite_note")).classes("text-xs text-grey")

    # ── run ────────────────────────────────────────────────────────────────
    with ui.row().classes("items-center gap-3 flex-wrap"):
        run_btn = ui.button(t("cm.run"), color="primary")
        ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_commission()) \
            .props("outline")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        progress_label = ui.label("").classes("font-mono text-sm")
        banner = ui.badge("—").props("color=grey")

    log_box = ui.column().classes("w-full gap-0 font-mono text-xs p-2 rounded "
                                  "border max-h-96 overflow-auto")

    def say(text: str, level: str = "info") -> None:
        with log_box:
            ui.label(text).classes(LEVEL_CLASS.get(level, ""))

    async def start() -> None:
        if not state["image"]:
            ui.notify(t("cm.need_image"), type="warning")
            return
        target = int(id_input.value or 0)
        if not valid_assignable_id(target) or target > 245:
            ui.notify(t("cm.bad_id", id=target), type="negative")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("cm.confirm_title")).classes("font-bold text-red")
            ui.label(t("cm.confirm_body", name=state["name"], id=target))
            if cb_overwrite.value:
                ui.label(t("cm.confirm_overwrite")).classes("text-red font-bold")
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("cm.run"), color="red", on_click=lambda: d.submit(True))
        if not await d:
            return

        log_box.clear()
        progress.set_value(0.0)
        progress_label.set_text("")
        banner.set_text(t("res.running"))
        banner.props("color=blue")

        cfg = CommissionConfig(image=state["image"], filename=state["name"],
                               identifier=target, lot=str(lot_input.value or ""),
                               overwrite=bool(cb_overwrite.value),
                               log_dir=Path(data_dir()) / "exports")
        if not worker.start_commission(cfg):
            ui.notify(t("msg.worker_busy"), type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    run_btn.on_click(start)

    def drain() -> None:
        state["seq"], events = worker.drain_commission_events(state["seq"])
        for ev in events:
            if isinstance(ev, Line):
                say(ev.text, ev.level)
            elif isinstance(ev, Progress):
                progress.set_value(ev.done / max(1, ev.total))
                progress_label.set_text(t("cm.step", done=ev.done, total=ev.total))
            elif isinstance(ev, Done):
                progress.set_value(1.0)
                progress_label.set_text("")
                banner.set_text(t("res.pass") if ev.ok else t("res.fail"))
                banner.props("color=green" if ev.ok else "color=red")
                ui.notify(ev.summary, type="positive" if ev.ok else "negative",
                          timeout=8000)
                if ev.ok:
                    # The next board almost always gets the next address.
                    nxt = int(id_input.value or 0) + 1
                    if valid_assignable_id(nxt) and nxt <= 245:
                        id_input.set_value(nxt)

    ui.timer(0.2, drain)
