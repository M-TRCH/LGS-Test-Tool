"""Firmware (OTA) tab — broadcast a firmware image to selected modules.

The image is uploaded through the browser (so it also works when the tool runs
on another machine), then streamed by app/ota.py on the worker thread.
"""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..ota import Done, Line, MAX_IMAGE_SIZE, OtaConfig, Progress
from . import Ctx

LEVEL_CLASS = {"info": "", "ok": "text-green", "warn": "text-orange", "err": "text-red"}


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state = {"seq": 0, "image": b"", "name": ""}

    ui.badge(t("ota.banner")).props("color=red").classes("text-sm p-2")

    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        # ── image ──────────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            ui.label(t("ota.image")).classes("font-bold")
            ui.label(t("ota.upload_hint", max=f"{MAX_IMAGE_SIZE:,}")).classes("text-xs text-grey")

            def on_upload(e) -> None:
                data = e.content.read()
                state["image"], state["name"] = data, e.name
                cfg = OtaConfig(image=data, filename=e.name)
                err = cfg.size_error()
                if err:
                    image_label.set_text(err)
                    image_label.classes(add="text-red", remove="text-green")
                    state["image"] = b""
                else:
                    image_label.set_text(t("ota.image_info", name=e.name, size=f"{len(data):,}",
                                           crc=f"{cfg.crc32:08X}", chunks=cfg.total_chunks))
                    image_label.classes(add="text-green", remove="text-red")

            ui.upload(on_upload=on_upload, auto_upload=True, max_files=1) \
                .props('accept=".bin" flat dense').classes("w-full")
            image_label = ui.label(t("ota.no_image")).classes("text-sm")

        # ── targets ────────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            ui.label(t("ota.targets")).classes("font-bold")
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
            ui.label(t("ota.targets_note")).classes("text-xs text-grey")
            cb_broadcast = ui.checkbox(t("ota.broadcast_apply"), value=False)
            broadcast_warn = ui.label("").classes("text-orange text-xs")
            cb_broadcast.on_value_change(
                lambda e: broadcast_warn.set_text(t("ota.broadcast_warn") if e.value else ""))

    def parse_ids() -> list:
        out = []
        for part in str(ids_input.value or "").replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit() and 1 <= int(part) <= 247:
                out.append(int(part))
        return sorted(set(out))

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
