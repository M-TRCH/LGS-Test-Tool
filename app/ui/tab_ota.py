"""Firmware (OTA) tab — broadcast a firmware image to selected modules.

The image is uploaded through the browser (so it also works when the tool runs
on another machine), then streamed by app/ota.py on the worker thread.
"""
from __future__ import annotations

from nicegui import ui

from .. import firmware_bundle as fb
from ..fw_survey import SurveyDone, SurveyProgress, SurveyRead
from ..i18n import t
from ..lgs_map import CABINET_LAYOUTS, GRID_COLS, GRID_ROWS
from ..ota import Done, Line, MAX_IMAGE_SIZE, OtaConfig, Progress
from . import Ctx, bundled_picker, helps, inline_warning, warning_banner

LEVEL_CLASS = {"info": "", "ok": "text-green", "warn": "text-orange", "err": "text-red"}

# Firmware survey grid. Version groups get their colours in order, so the
# newest firmware in the cabinet is always the first colour — what matters is
# that unlike versions look unlike, not which colour any one version gets.
SURVEY_IDLE = "grey-4"        # slot not part of this survey
SURVEY_QUEUED = "grey-7"      # in the survey, not read yet
SURVEY_READING = "amber"
SURVEY_ANSWERED = "blue-grey"  # answered; recoloured by group when the run ends
SURVEY_SILENT = "negative"    # no answer — a real fault, not an empty slot
SURVEY_COLORS = ("positive", "primary", "purple", "teal", "brown", "indigo")


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"seq": 0, "image": b"", "name": ""}

    warning_banner(t("ota.banner"))

    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        # ── image ──────────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("ota.image")).classes("font-bold"),
                  t("ota.upload_hint", max=f"{MAX_IMAGE_SIZE:,}"))

            def arm(data: bytes, name: str) -> None:
                state["image"], state["name"] = data, name
                cfg = OtaConfig(image=data, filename=name)
                err = cfg.size_error()
                if err:
                    image_label.set_text(err)
                    image_label.classes(add="text-red", remove="text-green")
                    state["image"] = b""
                else:
                    image_label.set_text(t("ota.image_info", name=name, size=f"{len(data):,}",
                                           crc=f"{cfg.crc32:08X}", chunks=cfg.total_chunks))
                    image_label.classes(add="text-green", remove="text-red")

            def on_upload(e) -> None:
                arm(e.content.read(), e.name)

            bundled_picker(fb.KIND_MODULE_OTA,
                           lambda data, name, img: arm(data, name))
            ui.label(t("fw.or_upload")).classes("text-xs text-grey")
            ui.upload(on_upload=on_upload, auto_upload=True, max_files=1) \
                .props('accept=".bin" flat dense').classes("w-full")
            image_label = ui.label(t("ota.no_image")).classes("text-sm")

        # ── targets ────────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("ota.targets")).classes("font-bold"), t("ota.targets_note"))
            ids_input = ui.input(t("ota.ids_label"), value=str(ctx.device_id())) \
                .props("dense outlined").classes("w-full")
            with ui.row().classes("gap-2 flex-wrap"):
                ui.button(t("ota.use_current"),
                          on_click=lambda: ids_input.set_value(str(ctx.device_id()))) \
                    .props("flat dense no-caps")

                def from_scan() -> None:
                    if not ctx.last_scan_ids:
                        ui.notify(t("ins.no_scan"), type="warning")
                        return
                    ids_input.set_value(", ".join(str(i) for i in ctx.last_scan_ids))

                ui.button(t("ota.use_scan"), on_click=from_scan).props("flat dense no-caps")
            cb_broadcast = ui.checkbox(t("ota.broadcast_apply"), value=False)
            broadcast_warn = inline_warning("text-orange text-xs")
            cb_broadcast.on_value_change(
                lambda e: broadcast_warn.set_text(t("ota.broadcast_warn") if e.value else ""))

    def parse_ids() -> list:
        out = []
        for part in str(ids_input.value or "").replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= 247:
                out.append(int(part))
        return sorted(set(out))

    def set_ids(ids) -> None:
        ids_input.set_value(", ".join(str(i) for i in sorted(ids)))

    # ── cabinet firmware ───────────────────────────────────────────────────
    # Read-only, and the reason the rest of this page is safe to use: before
    # an update it says who still needs it, after one whether they all took
    # it. Its groups double as the target picker, so "update the ones still
    # on v3.1.0" is a click rather than a list typed out by hand.
    with ui.card().classes("p-3 w-full"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            helps(ui.label(t("fws.card")).classes("font-bold"), t("fws.hint"))
            for layout in CABINET_LAYOUTS:
                ui.button(layout.label,
                          on_click=lambda layout=layout: survey_start(layout.ids)) \
                    .props("outline dense no-caps") \
                    .tooltip(t("fws.cabinet_tip", n=layout.count))
            ui.button(t("fws.selected"),
                      on_click=lambda: survey_start(parse_ids())) \
                .props("flat dense no-caps").tooltip(t("fws.selected_tip"))
            ui.button(t("btn.cancel"),
                      on_click=lambda: worker.cancel_fw_survey()).props("flat dense")
            survey_progress = ui.linear_progress(value=0.0, show_value=False) \
                .classes("w-40")
            survey_label = ui.label(t("mt.idle")).classes("text-sm font-mono")

        # The whole grid is drawn once; a survey lights the slots it covers
        # and leaves the rest grey, so the cabinet's shape stays readable.
        survey_cells: dict = {}
        with ui.column().classes("gap-1 q-mt-sm"):
            for r in range(1, GRID_ROWS + 1):
                with ui.row().classes("gap-1 flex-nowrap items-center"):
                    ui.label(f"R{r}").classes("w-8 text-xs text-grey font-mono")
                    for gid in (r * 10 + c for c in range(1, GRID_COLS + 1)):
                        survey_cells[gid] = ui.button(str(gid)) \
                            .props(f"unelevated no-caps dense color={SURVEY_IDLE}") \
                            .classes("w-14 min-w-0 font-mono")

        groups_row = ui.row().classes("items-center gap-2 flex-wrap q-mt-sm")

    def survey_paint(gid: int, color: str, tip: str = "") -> None:
        cell = survey_cells.get(gid)
        if cell is None:
            return
        cell.props(f"color={color}")
        if tip:
            cell.tooltip(tip)

    def survey_reset(ids) -> None:
        chosen = set(ids)
        for gid in survey_cells:
            survey_paint(gid, SURVEY_QUEUED if gid in chosen else SURVEY_IDLE)
        groups_row.clear()

    def survey_start(ids) -> None:
        if not worker.get_state().connected:
            ui.notify(t("msg.not_connected"), type="negative")
            return
        ids = [i for i in ids if i in survey_cells]
        if not ids:
            ui.notify(t("ota.no_ids"), type="warning")
            return
        if not worker.start_fw_survey(ids):
            ui.notify(t("msg.worker_busy"), type="negative")
            return
        survey_reset(ids)
        survey_progress.set_value(0.0)
        survey_label.set_text(t("fws.running", done=0, total=len(ids)))

    def survey_show_groups(report) -> None:
        """One chip per version — click it to make that group the targets."""
        groups_row.clear()
        with groups_row:
            ui.label(t("fws.groups")).classes("text-sm text-grey")
            shade = 0
            for group in report.groups():
                if group.silent:
                    colour = SURVEY_SILENT
                else:
                    colour = SURVEY_COLORS[shade % len(SURVEY_COLORS)]
                    shade += 1
                for gid in group.ids:
                    survey_paint(gid, colour, t("fws.cell_tip", v=group.label))
                if group.silent:
                    # Not offered as a target: a module that would not answer a
                    # read is not one to start writing firmware to.
                    ui.badge(f"{group.label} × {group.count}") \
                        .props(f"color={colour}").tooltip(t("fws.silent_tip"))
                    continue

                def target(g=group) -> None:
                    set_ids(g.ids)
                    ui.notify(t("fws.targets_set", n=g.count, v=g.label),
                              type="positive")

                ui.button(f"{group.label} × {group.count}", on_click=target) \
                    .props(f"unelevated dense no-caps color={colour}") \
                    .tooltip(t("fws.group_tip", v=group.label))

    def survey_drain() -> None:
        survey_state["seq"], events = worker.drain_fw_survey_events(
            survey_state["seq"])
        for ev in events:
            if isinstance(ev, SurveyProgress):
                survey_paint(ev.device_id, SURVEY_READING)
                survey_progress.set_value((ev.index - 1) / max(1, ev.total))
                survey_label.set_text(t("fws.running", done=ev.index - 1,
                                        total=ev.total))
            elif isinstance(ev, SurveyRead):
                r = ev.result
                survey_paint(r.device_id,
                             SURVEY_ANSWERED if r.responded else SURVEY_SILENT,
                             r.version or r.note)
            elif isinstance(ev, SurveyDone):
                survey_progress.set_value(1.0)
                survey_show_groups(ev.report)
                survey_label.set_text(
                    t("fws.done", n=ev.report.answered,
                      total=len(ev.report.results), summary=ev.report.summary()))
                say(t("fws.done", n=ev.report.answered,
                      total=len(ev.report.results),
                      summary=ev.report.summary()), "ok")

    survey_state = {"seq": 0}
    ui.timer(0.2, survey_drain)

    # ── actions ────────────────────────────────────────────────────────────
    with ui.row().classes("items-center gap-3 flex-wrap"):
        send_btn = ui.button(t("ota.send"), color="red")
        ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_ota()).props("outline")
        ui.button(t("ota.status"), on_click=lambda: read_status()).props("outline dense")
        ui.button(t("ota.abort"), on_click=lambda: abort()).props("outline dense")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        progress_label = ui.label(t("mt.idle")).classes("font-mono text-sm")
        banner = ui.badge("—").props("color=grey")

    log_box = ui.column().classes("w-full gap-0 font-mono text-xs p-2 rounded "
                                  "border max-h-96 overflow-auto")

    def say(text: str, level: str = "info") -> None:
        with log_box:
            ui.label(text).classes(LEVEL_CLASS.get(level, ""))

    async def read_status() -> None:
        ids = parse_ids()
        if not ids:
            ui.notify(t("ota.no_ids"), type="warning")
            return
        for uid, desc in await worker.ota_status(ids):
            say(f"  id {uid}: {desc}")

    async def abort() -> None:
        res = await worker.ota_abort()
        say(t("ota.abort_sent") if res.ok else f"abort failed: {res.note}",
            "warn" if res.ok else "err")
        ui.notify(t("ota.abort_sent") if res.ok else res.note,
                  type="warning" if res.ok else "negative")

    async def start() -> None:
        if not worker.get_state().connected:
            ui.notify(t("msg.not_connected"), type="negative")
            return
        if not state["image"]:
            ui.notify(t("ota.no_image"), type="warning")
            return
        ids = parse_ids()
        if not ids:
            ui.notify(t("ota.no_ids"), type="warning")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("ota.confirm_title")).classes("font-bold text-red")
            ui.label(t("ota.confirm_body", size=f"{len(state['image']):,}",
                       n=len(ids), ids=", ".join(str(i) for i in ids)))
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("ota.confirm_btn"), color="red", on_click=lambda: d.submit(True))
        if not await d:
            return

        log_box.clear()
        progress.set_value(0.0)
        banner.set_text(t("res.running"))
        banner.props("color=blue")
        cfg = OtaConfig(ids=tuple(ids), image=state["image"], filename=state["name"],
                        broadcast_apply=bool(cb_broadcast.value))
        if not worker.start_ota(cfg):
            ui.notify(t("msg.worker_busy"), type="negative")
            banner.set_text("—")
            banner.props("color=grey")

    send_btn.on_click(start)

    def drain() -> None:
        state["seq"], events = worker.drain_ota_events(state["seq"])
        for ev in events:
            if isinstance(ev, Line):
                say(ev.text, ev.level)
            elif isinstance(ev, Progress):
                progress.set_value(ev.done / max(1, ev.total))
                progress_label.set_text(t("ota.progress", done=ev.done, total=ev.total))
            elif isinstance(ev, Done):
                progress.set_value(1.0)
                progress_label.set_text(ev.summary)
                banner.set_text(t("res.pass") if ev.ok else t("res.fail"))
                banner.props("color=green" if ev.ok else "color=red")
                ui.notify(ev.summary, type="positive" if ev.ok else "negative", timeout=8000)

    ui.timer(0.2, drain)
