"""Danger tab: factory reset, EEPROM persist, software reset, clear statistics,
set slave ID.

Only this tab calls worker.danger_action() / set_slave_id() (the only paths that
set the allow_danger flag). Factory reset requires typing the slave ID plus a
second red confirmation.
"""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..lgs_map import FACTORY_DEFAULT_ID, SETID_TEMP_ID
from ..modbus_worker import DangerAction
from . import Ctx, warning_banner


def build(ctx: Ctx) -> None:
    worker = ctx.worker

    warning_banner(t("dng.banner"))

    result_log = ui.log(max_lines=60).classes("w-full h-40 font-mono text-xs")

    async def run(action: DangerAction) -> None:
        device_id = ctx.device_id()
        result_log.push(f"--- {action.value} @ id {device_id} ---")
        res = await worker.danger_action(action, device_id)
        for i, step in enumerate(res.steps, 1):
            mark = "OK " if step.ok else "ERR"
            result_log.push(f"  step {i}: {mark} {step.note or step.value}")
        result_log.push(f"  => {t('dng.success') if res.ok else t('dng.failed')}: {res.note}")
        ui.notify(res.note, type="positive" if res.ok else "negative", timeout=6000)
        if res.ok and action is DangerAction.FACTORY_RESET_ALL and ctx.device_id_setter:
            ctx.device_id_setter(FACTORY_DEFAULT_ID)
            ui.notify(t("dng.factory_restored", id=FACTORY_DEFAULT_ID),
                      type="warning", timeout=8000)

    def simple_confirm(title: str, action: DangerAction):
        async def flow() -> None:
            d = ui.dialog()
            with d, ui.card():
                ui.label(title).classes("font-bold")
                ui.label(t("dng.target", id=ctx.device_id()))
                with ui.row():
                    ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                    ui.button(t("dng.confirm"), color="red", on_click=lambda: d.submit(True))
            if await d:
                await run(action)
        return flow

    with ui.row().classes("gap-3 flex-wrap items-stretch"):
        with ui.card().classes("p-3 min-w-[340px] border border-red-400"):
            ui.label(t("dng.factory")).classes("font-bold text-red")
            mode = ui.radio({"keep": t("dng.keep_id"), "all": t("dng.wipe_all")},
                            value="keep").props("dense")

            async def arm() -> None:
                device_id = ctx.device_id()
                action = (DangerAction.FACTORY_RESET_KEEP_ID if mode.value == "keep"
                          else DangerAction.FACTORY_RESET_ALL)
                d1 = ui.dialog()
                with d1, ui.card():
                    ui.label(t("dng.arm_title")).classes("font-bold")
                    ui.label(t("dng.arm_seq", apply="501" if mode.value == "keep" else "502"))
                    if mode.value == "all":
                        ui.label(t("dng.wipe_warn", id=FACTORY_DEFAULT_ID)).classes("text-red")
                    typed = ui.input(t("dng.type_id", id=device_id)).props("dense outlined")
                    with ui.row():
                        ui.button(t("btn.cancel"), on_click=lambda: d1.submit(False)).props("flat")
                        ui.button(t("dng.arm_btn"),
                                  on_click=lambda: d1.submit(typed.value == str(device_id)))
                if not await d1:
                    return
                d2 = ui.dialog()
                with d2, ui.card().classes("border border-red-500"):
                    ui.label(t("dng.really")).classes("font-bold text-red")
                    ui.label(f"{action.value} @ slave {device_id}")
                    with ui.row():
                        ui.button(t("btn.cancel"), on_click=lambda: d2.submit(False)).props("flat")
                        ui.button(t("dng.apply"), color="red", on_click=lambda: d2.submit(True))
                if await d2:
                    await run(action)

            ui.button(t("dng.arm"), color="red", on_click=arm).props("outline")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("dng.save")).classes("font-bold")
            ui.label(t("dng.save_note")).classes("text-xs text-grey")
            ui.button(t("dng.save_btn"),
                      on_click=simple_confirm(t("dng.save_title"), DangerAction.SAVE_EEPROM)) \
                .props("outline dense")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("dng.soft")).classes("font-bold")
            ui.label(t("dng.soft_note")).classes("text-xs text-grey")
            ui.button(t("dng.soft_btn"),
                      on_click=simple_confirm(t("dng.soft_title"), DangerAction.SOFT_RESET)) \
                .props("outline dense")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("dng.stats")).classes("font-bold")
            ui.label(t("dng.stats_note")).classes("text-xs text-grey")
            ui.button(t("dng.stats_btn"),
                      on_click=simple_confirm(t("dng.stats_title"), DangerAction.CLEAR_STATS)) \
                .props("outline dense")

        with ui.card().classes("p-3 min-w-[280px]"):
            ui.label(t("dng.setid")).classes("font-bold")
            ui.label(t("dng.setid_note", factory=FACTORY_DEFAULT_ID,
                       forbidden=SETID_TEMP_ID)).classes("text-xs text-grey")
            with ui.row().classes("items-center gap-2"):
                new_id_input = ui.number(t("dng.new_id"), value=11, min=1, max=247, format="%d") \
                    .props("dense outlined").classes("w-24")

                async def set_id_flow() -> None:
                    cur = ctx.device_id()
                    target = int(new_id_input.value or 0)
                    d = ui.dialog()
                    with d, ui.card():
                        ui.label(t("dng.setid_title")).classes("font-bold")
                        ui.label(t("dng.setid_body", cur=cur, new=target))
                        if target == cur:
                            ui.label(t("dng.setid_same")).classes("text-orange")
                        with ui.row():
                            ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                            ui.button(t("dng.setid_change"), color="red",
                                      on_click=lambda: d.submit(True))
                    if not await d:
                        return
                    result_log.push(f"--- set slave id {cur} -> {target} ---")
                    res = await worker.set_slave_id(cur, target)
                    for i, step in enumerate(res.steps, 1):
                        mark = "OK " if step.ok else "ERR"
                        result_log.push(f"  step {i}: {mark} {step.note or step.value}")
                    result_log.push(f"  => {t('dng.success') if res.ok else t('dng.failed')}: "
                                    f"{res.note}")
                    ui.notify(res.note, type="positive" if res.ok else "negative", timeout=6000)
                    if res.ok and ctx.device_id_setter:
                        ctx.device_id_setter(target)

                ui.button(t("dng.setid_btn"), color="red", on_click=set_id_flow) \
                    .props("outline dense")
