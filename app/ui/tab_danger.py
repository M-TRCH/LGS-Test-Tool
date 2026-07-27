"""Danger tab: factory reset, EEPROM persist, software reset, clear statistics.

Only this tab calls worker.danger_action() (the only path that sets the
allow_danger flag). Factory reset requires typing the slave ID plus a second
red confirmation.
"""
from __future__ import annotations

from nicegui import ui

from ..lgs_map import FACTORY_DEFAULT_ID
from ..modbus_worker import DangerAction
from . import Ctx


def build(ctx: Ctx) -> None:
    worker = ctx.worker

    ui.badge("⚠ These commands reboot or wipe the module — double-check the target ID") \
        .props("color=red").classes("text-sm p-2")

    result_log = ui.log(max_lines=60).classes("w-full h-40 font-mono text-xs")

    async def run(action: DangerAction) -> None:
        device_id = ctx.device_id()
        result_log.push(f"--- {action.value} @ id {device_id} ---")
        res = await worker.danger_action(action, device_id)
        for i, step in enumerate(res.steps, 1):
            mark = "OK " if step.ok else "ERR"
            result_log.push(f"  step {i}: {mark} {step.note or step.value}")
        result_log.push(f"  => {'SUCCESS' if res.ok else 'FAILED'}: {res.note}")
        ui.notify(res.note, type="positive" if res.ok else "negative", timeout=6000)
        if res.ok and action is DangerAction.FACTORY_RESET_ALL and ctx.device_id_setter:
            ctx.device_id_setter(FACTORY_DEFAULT_ID)
            ui.notify(f"slave ID reset to factory default {FACTORY_DEFAULT_ID} "
                      f"(baud back to 9600 — reconnect if you were on another baud)",
                      type="warning", timeout=8000)

    def simple_confirm(title: str, action: DangerAction):
        async def flow() -> None:
            d = ui.dialog()
            with d, ui.card():
                ui.label(title).classes("font-bold")
                ui.label(f"Target: slave {ctx.device_id()} — continue?")
                with ui.row():
                    ui.button("Cancel", on_click=lambda: d.submit(False)).props("flat")
                    ui.button("CONFIRM", color="red", on_click=lambda: d.submit(True))
            if await d:
                await run(action)
        return flow

    with ui.row().classes("gap-3 flex-wrap items-stretch"):
        with ui.card().classes("p-3 min-w-[340px] border border-red-400"):
            ui.label("Factory reset").classes("font-bold text-red")
            mode = ui.radio({"keep": "Keep slave ID (500→501)",
                             "all": "Wipe everything (500→502)"}, value="keep").props("dense")

            async def arm() -> None:
                device_id = ctx.device_id()
                action = (DangerAction.FACTORY_RESET_KEEP_ID if mode.value == "keep"
                          else DangerAction.FACTORY_RESET_ALL)
                d1 = ui.dialog()
                with d1, ui.card():
                    ui.label("Arm factory reset").classes("font-bold")
                    ui.label(f"Sequence: coil 500 (arm) → coil {'501' if mode.value == 'keep' else '502'}"
                             f" (apply) → device reboots ~3 s.")
                    if mode.value == "all":
                        ui.label(f"Wipe-all restores ID {FACTORY_DEFAULT_ID} and baud 9600!") \
                            .classes("text-red")
                    typed = ui.input(f"Type the slave ID ({device_id}) to arm").props("dense outlined")
                    with ui.row():
                        ui.button("Cancel", on_click=lambda: d1.submit(False)).props("flat")
                        ui.button("Arm", on_click=lambda: d1.submit(typed.value == str(device_id)))
                armed = await d1
                if not armed:
                    if armed is False:
                        pass
                    return
                d2 = ui.dialog()
                with d2, ui.card().classes("border border-red-500"):
                    ui.label("REALLY apply factory reset?").classes("font-bold text-red")
                    ui.label(f"{action.value} @ slave {device_id}")
                    with ui.row():
                        ui.button("Cancel", on_click=lambda: d2.submit(False)).props("flat")
                        ui.button("APPLY", color="red", on_click=lambda: d2.submit(True))
                if await d2:
                    await run(action)

            ui.button("Arm factory reset…", color="red", on_click=arm).props("outline")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Save to EEPROM (503)").classes("font-bold")
            ui.label("Persists R/W(F) registers; reboots ~3 s").classes("text-xs text-grey")
            ui.button("Save…", on_click=simple_confirm("Persist config to EEPROM + reboot",
                                                       DangerAction.SAVE_EEPROM)).props("outline dense")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Software reset (504)").classes("font-bold")
            ui.label("Reboots the module ~3 s").classes("text-xs text-grey")
            ui.button("Reset…", on_click=simple_confirm("Software reset the module",
                                                        DangerAction.SOFT_RESET)).props("outline dense")

        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Clear statistics (510)").classes("font-bold")
            ui.label("Zeroes regs 200-281 (persisted)").classes("text-xs text-grey")
            ui.button("Clear…", on_click=simple_confirm("Clear all statistics counters",
                                                        DangerAction.CLEAR_STATS)).props("outline dense")

        with ui.card().classes("p-3 min-w-[280px]"):
            ui.label("Set Slave ID (reg 4 → persist 503)").classes("font-bold")
            ui.label("Grid convention: row×10+col (11-64) · factory 247 · 246 forbidden") \
                .classes("text-xs text-grey")
            with ui.row().classes("items-center gap-2"):
                new_id_input = ui.number("new ID", value=11, min=1, max=247, format="%d") \
                    .props("dense outlined").classes("w-24")

                async def set_id_flow() -> None:
                    cur = ctx.device_id()
                    target = int(new_id_input.value or 0)
                    d = ui.dialog()
                    with d, ui.card():
                        ui.label("Change slave ID?").classes("font-bold")
                        ui.label(f"Device {cur} → new ID {target}. Writes reg 4, persists to "
                                 f"EEPROM (coil 503) and reboots ~3 s, then verifies at the new ID.")
                        if target == cur:
                            ui.label("new ID equals the current ID").classes("text-orange")
                        with ui.row():
                            ui.button("Cancel", on_click=lambda: d.submit(False)).props("flat")
                            ui.button("CHANGE ID", color="red", on_click=lambda: d.submit(True))
                    if not await d:
                        return
                    result_log.push(f"--- set slave id {cur} -> {target} ---")
                    res = await worker.set_slave_id(cur, target)
                    for i, step in enumerate(res.steps, 1):
                        mark = "OK " if step.ok else "ERR"
                        result_log.push(f"  step {i}: {mark} {step.note or step.value}")
                    result_log.push(f"  => {'SUCCESS' if res.ok else 'FAILED'}: {res.note}")
                    ui.notify(res.note, type="positive" if res.ok else "negative", timeout=6000)
                    if res.ok and ctx.device_id_setter:
                        ctx.device_id_setter(target)

                ui.button("Set ID…", color="red", on_click=set_id_flow).props("outline dense")
