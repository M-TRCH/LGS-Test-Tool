"""Monitor tab: periodic poll of diagnostics/sensor/statistics with decoding."""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..lgs_map import (SENSOR_FAULT, dec_baud, dec_device_type, dec_fw, dec_hw,
                       dec_mode, dec_preset, dec_temp, dec_uptime,
                       decode_health, decode_reset_cause, stats_count, stats_time)
from . import Ctx


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"cycle": 0, "sticky_cause": "", "sticky_ts": ""}

    with ui.row().classes("items-center gap-3"):
        polling = ui.switch(t("mon.polling"), value=False)
        interval = ui.select([0.5, 1.0, 2.0], value=ctx.cfg.monitor_interval_s,
                             label=t("mon.interval")).props("dense outlined").classes("w-32")
        ui.label(t("mon.stats_note")).classes("text-xs text-grey")
        last_poll = ui.label(t("mon.last_poll", time="—")).classes("text-xs text-grey")
        errors_label = ui.label("").classes("text-xs text-orange")

    def L() -> ui.label:
        return ui.label("—").classes("text-sm")

    with ui.row().classes("gap-3 flex-wrap items-stretch"):
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("mon.card.device")).classes("font-bold")
            dev_type, dev_fw, dev_hw, dev_baud = L(), L(), L(), L()
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("mon.card.runtime")).classes("font-bold")
            rt_uptime, rt_boots, rt_mode, rt_preset = L(), L(), L(), L()
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label(t("mon.card.health")).classes("font-bold")
            health_row = ui.row().classes("gap-1 flex-wrap")
            latch_chip = ui.badge("—").props("color=grey")
        with ui.card().classes("p-3 min-w-[220px]"):
            ui.label(t("mon.card.reset")).classes("font-bold")
            rc_label = L()
            ui.label(t("mon.reset_note")).classes("text-xs text-grey")
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label(t("mon.card.temp")).classes("font-bold")
            t_room, t_board = L(), L()
        with ui.card().classes("p-3 min-w-[240px]"):
            ui.label(t("mon.card.latch")).classes("font-bold")
            ld_latch, ld_unlock, ld_display = L(), L(), L()
        with ui.card().classes("p-3 min-w-[280px]"):
            ui.label(t("mon.card.stats")).classes("font-bold")
            st_total = L()
            stats_table = ui.table(
                columns=[{"name": "p", "label": t("mon.col.preset"), "field": "p", "align": "left"},
                         {"name": "c", "label": t("mon.col.count"), "field": "c"},
                         {"name": "t", "label": t("mon.col.runtime"), "field": "t"}],
                rows=[], row_key="p").props("dense flat hide-bottom").classes("text-xs")

    def latch_text(raw) -> str:
        return t("mon.locked") if raw == 1 else (t("mon.unlocked") if raw == 0 else "—")

    async def poll() -> None:
        if not polling.value:
            return
        state["cycle"] += 1
        snap = await worker.poll_monitor(ctx.device_id(),
                                         with_stats=(state["cycle"] % 5 == 1))
        if snap is None:
            return
        ctx.latest_snapshot = snap
        last_poll.set_text(t("mon.last_poll", time=snap.ts.strftime("%H:%M:%S")))
        errors_label.set_text("; ".join(snap.errors))
        r = snap.regs
        if not r:
            return
        if 0 in r:
            dev_type.set_text(t("mon.type", v=dec_device_type(r[0])))
            dev_fw.set_text(t("mon.fw", v=dec_fw(r[1])))
            dev_hw.set_text(t("mon.hw", v=dec_hw(r[2])))
            dev_baud.set_text(t("mon.baud_id", baud=dec_baud(r[3]), id=r[4]))
            rt_uptime.set_text(t("mon.uptime", v=dec_uptime(r[5], r[6])))
            rt_boots.set_text(t("mon.boots", v=r[7]))
            rt_mode.set_text(t("mon.mode", v=dec_mode(r[10])))
            rt_preset.set_text(t("mon.active_preset", v=dec_preset(r[11])))

            health_row.clear()
            with health_row:
                for name, ok in decode_health(r[9]):
                    ui.badge(name).props(f"color={'green' if ok else 'red'}")
            if r[8]:
                names = ", ".join(decode_reset_cause(r[8])) or f"raw {r[8]}"
                state["sticky_cause"] = names
                state["sticky_ts"] = snap.ts.strftime("%H:%M:%S")
            rc_label.set_text(f"{state['sticky_cause'] or '—'}"
                              + (f"  {t('mon.seen_at', time=state['sticky_ts'])}"
                                 if state["sticky_ts"] else ""))
        if 20 in r:
            t_room.set_text(t("mon.room", v=dec_temp(r[20])))
            t_board.set_text(t("mon.board", v=dec_temp(r[21])))
            fault = r[20] == SENSOR_FAULT or r[21] == SENSOR_FAULT
            for lbl in (t_room, t_board):
                lbl.classes(add="text-red" if fault else "", remove="" if fault else "text-red")
        if 40 in r:
            ld_latch.set_text(t("mon.latch_state", v=latch_text(r.get(41))))
            ld_unlock.set_text(t("mon.unlocked_ago", s=r[40]) if r[40] else t("mon.no_unlock"))
        if 60 in r:
            ld_display.set_text(t("mon.display_num", v=r[60]))
        latch_chip.set_text(t("mon.latch_state", v=latch_text(r.get(41))))

        if snap.stats:
            s = snap.stats
            st_total.set_text(t("mon.total", c=s.get(200, 0), s=s.get(201, 0)))
            stats_table.rows = [{"p": n, "c": s.get(stats_count(n), 0),
                                 "t": s.get(stats_time(n), 0)} for n in range(1, 9)]
            stats_table.update()

    timer = ui.timer(float(ctx.cfg.monitor_interval_s), poll)

    def set_interval() -> None:
        timer.interval = float(interval.value)
        ctx.cfg.monitor_interval_s = float(interval.value)

    interval.on_value_change(set_interval)
