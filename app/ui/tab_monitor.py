"""Monitor tab: periodic poll of diagnostics/sensor/statistics with decoding."""
from __future__ import annotations

from nicegui import ui

from ..lgs_map import (SENSOR_FAULT, dec_baud, dec_device_type, dec_fw, dec_hw,
                       dec_mode, dec_preset, dec_temp, dec_uptime,
                       decode_health, decode_reset_cause, stats_count, stats_time)
from . import Ctx


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"cycle": 0, "sticky_cause": "", "sticky_ts": ""}

    with ui.row().classes("items-center gap-3"):
        polling = ui.switch("Polling", value=False)
        interval = ui.select([0.5, 1.0, 2.0], value=ctx.cfg.monitor_interval_s,
                             label="interval (s)").props("dense outlined").classes("w-28")
        ui.label("statistics read every 5th poll").classes("text-xs text-grey")
        last_poll = ui.label("last poll: —").classes("text-xs text-grey")
        errors_label = ui.label("").classes("text-xs text-orange")

    def L(container_label: str) -> ui.label:
        return ui.label("—").classes("text-sm")

    with ui.row().classes("gap-3 flex-wrap items-stretch"):
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Device").classes("font-bold")
            dev_type = L("type")
            dev_fw = L("fw")
            dev_hw = L("hw")
            dev_baud = L("baud")
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Runtime").classes("font-bold")
            rt_uptime = L("uptime")
            rt_boots = L("boots")
            rt_mode = L("mode")
            rt_preset = L("preset")
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label("Health (reg 9)").classes("font-bold")
            health_row = ui.row().classes("gap-1 flex-wrap")
            latch_chip = ui.badge("latch: —").props("color=grey")
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label("Reset cause (reg 8)").classes("font-bold")
            rc_label = L("cause")
            ui.label("clear-on-read — this tool's polling consumes it; last nonzero is kept") \
                .classes("text-xs text-grey")
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label("Temperatures").classes("font-bold")
            t_room = L("room")
            t_board = L("board")
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label("Latch / Display").classes("font-bold")
            ld_latch = L("latch")
            ld_unlock = L("unlock t")
            ld_display = L("display")
        with ui.card().classes("p-3 min-w-[280px]"):
            ui.label("Statistics").classes("font-bold")
            st_total = L("total")
            stats_table = ui.table(
                columns=[{"name": "p", "label": "preset", "field": "p", "align": "left"},
                         {"name": "c", "label": "on count", "field": "c"},
                         {"name": "t", "label": "runtime s", "field": "t"}],
                rows=[], row_key="p").props("dense flat hide-bottom").classes("text-xs")

    async def poll() -> None:
        if not polling.value:
            return
        state["cycle"] += 1
        snap = await worker.poll_monitor(ctx.device_id(),
                                         with_stats=(state["cycle"] % 5 == 1))
        if snap is None:
            return
        ctx.latest_snapshot = snap
        last_poll.set_text(f"last poll: {snap.ts.strftime('%H:%M:%S')}")
        errors_label.set_text("; ".join(snap.errors))
        r = snap.regs
        if not r:
            return
        if 0 in r:
            dev_type.set_text(f"Type: {dec_device_type(r[0])}")
            dev_fw.set_text(f"FW: {dec_fw(r[1])}")
            dev_hw.set_text(f"HW: {dec_hw(r[2])}")
            dev_baud.set_text(f"Baud: {dec_baud(r[3])} · ID: {r[4]}")
            rt_uptime.set_text(f"Uptime: {dec_uptime(r[5], r[6])}")
            rt_boots.set_text(f"Boots: {r[7]}")
            rt_mode.set_text(f"Mode: {dec_mode(r[10])}")
            rt_preset.set_text(f"Active preset: {dec_preset(r[11])}")

            health_row.clear()
            with health_row:
                for name, ok in decode_health(r[9]):
                    ui.badge(name).props(f"color={'green' if ok else 'red'}")
            if r[8]:
                names = ", ".join(decode_reset_cause(r[8])) or f"raw {r[8]}"
                state["sticky_cause"] = names
                state["sticky_ts"] = snap.ts.strftime("%H:%M:%S")
            rc_label.set_text(f"{state['sticky_cause'] or '—'}"
                              + (f"  (seen {state['sticky_ts']})" if state["sticky_ts"] else ""))
        if 20 in r:
            t_room.set_text(f"Room: {dec_temp(r[20])}")
            t_board.set_text(f"Board: {dec_temp(r[21])}")
            fault = r[20] == SENSOR_FAULT or r[21] == SENSOR_FAULT
            for lbl in (t_room, t_board):
                lbl.classes(add="text-red" if fault else "", remove="" if fault else "text-red")
        if 40 in r:
            locked = r.get(41)
            ld_latch.set_text(f"Latch: {'LOCKED' if locked == 1 else 'UNLOCKED' if locked == 0 else '—'}")
            ld_unlock.set_text(f"Unlocked {r[40]} s ago" if r[40] else "No unlock since boot")
        if 60 in r:
            ld_display.set_text(f"Display number (reg 60): {r[60]}")
        latch_chip.set_text(f"latch: {'LOCKED' if r.get(41) == 1 else 'UNLOCKED' if r.get(41) == 0 else '—'}")

        if snap.stats:
            s = snap.stats
            st_total.set_text(f"Total: {s.get(200, 0)} fires · {s.get(201, 0)} s")
            stats_table.rows = [{"p": n, "c": s.get(stats_count(n), 0),
                                 "t": s.get(stats_time(n), 0)} for n in range(1, 9)]
            stats_table.update()

    timer = ui.timer(float(ctx.cfg.monitor_interval_s), poll)

    def set_interval() -> None:
        timer.interval = float(interval.value)
        ctx.cfg.monitor_interval_s = float(interval.value)

    interval.on_value_change(set_interval)
