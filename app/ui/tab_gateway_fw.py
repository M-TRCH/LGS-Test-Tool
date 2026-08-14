"""Gateway firmware update and first-time QSPI provisioning.

Split out of tab_gateway: it shares nothing with the settings machinery
except the port check and the log pane. It is also the one action on that
page that can leave the whole bus without a bridge, so it keeps its own
red-bordered confirm.

Update and provision are the same job with one extra step, so they are one
function with the differing words looked up by a flag — they drifted apart
as twins once already.
"""
from __future__ import annotations

from typing import Callable

from nicegui import ui

from .. import firmware_bundle as fb
from ..gw_net_update import GwNetUpdateConfig
from ..i18n import t
from ..opta_update import OptaConfig
from ..ota import Done, Line, Progress
from . import Ctx, bundled_picker, confirm, helps


def build(ctx: Ctx, usable: Callable[[], tuple],
          get_log: Callable[[], ui.log]) -> None:
    """`usable` is the tab's transport check; `get_log` returns the shared
    log pane, late-bound because it is created after this card in layout
    order and only ever dereferenced inside handlers."""
    worker = ctx.worker
    state: dict = {"seq": 0, "image": b"", "name": ""}

    with ui.card().classes("p-3 w-full border border-orange-400 q-mt-sm"):
        helps(ui.label(t("gw.fw_card")).classes("font-bold text-orange"),
              t("gw.fw_hint"))

        def arm(data: bytes, name: str) -> None:
            state["image"], state["name"] = data, name
            fw_label.set_text(t("gw.fw_chosen", name=name, size=f"{len(data):,}"))

        def on_fw_upload(e) -> None:
            arm(e.content.read(), e.name)

        bundled_picker(fb.KIND_GATEWAY, lambda data, name, img: arm(data, name))
        ui.label(t("fw.or_upload")).classes("text-xs text-grey")
        ui.upload(on_upload=on_fw_upload, auto_upload=True, max_files=1) \
            .props('accept=".bin" flat dense').classes("w-full")
        fw_label = ui.label(t("gw.fw_none")).classes("text-sm")
        with ui.row().classes("items-center gap-3 q-mt-sm"):
            fw_btn = ui.button(t("gw.fw_run"), color="red").props("outline")
            prov_btn = helps(
                ui.button(t("gw.prov_run"), color="red").props("outline"),
                t("gw.prov_hint"))
            ui.button(t("btn.cancel"),
                      on_click=lambda: worker.cancel_commission()).props("flat")
            progress = ui.linear_progress(value=0.0, show_value=False) \
                .classes("w-48")
            badge = ui.badge("—").props("color=grey")

    async def run_job(provision: bool) -> None:
        ok, why = usable()
        if not ok:
            ui.notify(why, type="negative")
            return
        if not state["image"]:
            ui.notify(t("gw.fw_need_image"), type="warning")
            return

        # Over TCP the update travels the network (fw >= 1.12.0): staged on
        # the gateway's QSPI, CRC-checked there, applied by its bootloader.
        # Provisioning stays USB-only — dfu-util IS the provisioning tool.
        net = ctx.transport() == "tcp"
        if net and provision:
            ui.notify(t("gw.prov_usb_only"), type="negative")
            return

        if provision:
            title, ok_label = t("gw.prov_confirm_title"), t("gw.prov_run")
            body = t("gw.prov_confirm_body", port=ctx.port(), name=state["name"])
        elif net:
            title, ok_label = t("gw.fw_confirm_title"), t("gw.fw_run")
            body = t("gw.fw_net_confirm_body", name=state["name"])
        else:
            title, ok_label = t("gw.fw_confirm_title"), t("gw.fw_run")
            body = t("gw.fw_confirm_body", name=state["name"], port=ctx.port())
        if not await confirm(title, body, ok_label, danger_border=True):
            return

        get_log().clear()
        progress.set_value(0.0)
        badge.set_text(t("res.running"))
        badge.props("color=blue")
        if net:
            started = worker.start_gw_net_update(
                GwNetUpdateConfig(image=state["image"], filename=state["name"]))
        else:
            cfg = OptaConfig(image=state["image"], filename=state["name"],
                             port=ctx.port())
            started = (worker.start_opta_provision(cfg) if provision
                       else worker.start_opta_update(cfg))
        if not started:
            ui.notify(t("msg.worker_busy"), type="negative")
            badge.set_text("—")
            badge.props("color=grey")

    fw_btn.on_click(lambda: run_job(False))
    prov_btn.on_click(lambda: run_job(True))

    def drain() -> None:
        state["seq"], events = worker.drain_commission_events(state["seq"])
        for ev in events:
            if isinstance(ev, Line):
                get_log().push(ev.text)
            elif isinstance(ev, Progress):
                progress.set_value(ev.done / max(1, ev.total))
            elif isinstance(ev, Done):
                progress.set_value(1.0)
                badge.set_text(t("res.pass") if ev.ok else t("res.fail"))
                badge.props("color=green" if ev.ok else "color=red")
                ui.notify(ev.summary,
                          type="positive" if ev.ok else "negative", timeout=9000)

    ui.timer(0.2, drain)
