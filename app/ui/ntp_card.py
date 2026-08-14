"""NTP server card (Gateway tab) — a view over app/ntp_server.py's singleton.

The gateway's clock recovery (`net.ntp`, fw >= v1.11.0) needs an NTP server
on the LAN; this card makes the tool itself be one. It lives on the Gateway
tab because that is where `net.ntp` is configured — the "use this PC"
button closes the loop by staging this machine's address into that field.
"""
from __future__ import annotations

from typing import Callable

from nicegui import ui

from .. import config_store, keep_awake, ntp_server
from ..i18n import t
from . import Ctx, helps


def build(ctx: Ctx, gateway_ip: Callable[[], str],
          set_ntp: Callable[[str], bool]) -> None:
    cfg = ctx.cfg
    srv = ntp_server.server

    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("ntp.card")).classes("font-bold"), t("ntp.hint"))
        with ui.row().classes("items-center gap-3 flex-wrap"):
            async def toggle(e) -> None:
                cfg.ntp_enabled = bool(e.value)
                config_store.save(cfg)
                if cfg.ntp_enabled:
                    if not await srv.start(cfg.ntp_port):
                        ui.notify(t("ntp.err", e=srv.error), type="warning")
                else:
                    await srv.stop()

            sw = ui.switch(t("ntp.enable"), value=cfg.ntp_enabled,
                           on_change=toggle).props("dense")
            helps(sw, t("ntp.enable_tip"))

            async def port_changed(e) -> None:
                try:
                    port = int(e.value)
                except (TypeError, ValueError):
                    return
                if not 1 <= port <= 65535 or port == cfg.ntp_port:
                    return
                cfg.ntp_port = port
                config_store.save(cfg)
                if srv.running or cfg.ntp_enabled:
                    if not await srv.start(port):
                        ui.notify(t("ntp.err", e=srv.error), type="warning")

            port_el = ui.number(t("ntp.port"), value=cfg.ntp_port, min=1,
                                max=65535, format="%d",
                                on_change=port_changed) \
                .props("dense outlined").classes("w-28")
            helps(port_el, t("ntp.port_tip"))

            def use_pc() -> None:
                ip = ntp_server.local_ip_toward(gateway_ip())
                if not ip:
                    ui.notify(t("ntp.no_ip"), type="warning")
                    return
                if set_ntp(ip):
                    ui.notify(t("ntp.staged", ip=ip), type="positive")
                else:
                    ui.notify(t("ntp.no_key"), type="warning")

            ui.button(t("ntp.use_pc"), on_click=use_pc) \
                .props("outline dense no-caps") \
                .tooltip(t("ntp.use_pc_tip"))

        status = ui.label("").classes("text-sm")
        # A time source that sleeps is not a time source: the same guard that
        # protects an overnight soak holds the machine awake for this too.
        ui.label(t("soak.awake_on") if keep_awake.supported()
                 else t("soak.awake_off")).classes("text-xs text-grey")

        def refresh() -> None:
            if srv.running:
                ip = ntp_server.local_ip_toward(gateway_ip()) or "0.0.0.0"
                status.set_text(t("ntp.serving", ip=ip, port=srv.port,
                                  n=srv.served))
                status.classes(replace="text-sm text-green")
            elif cfg.ntp_enabled and srv.error:
                status.set_text(t("ntp.err", e=srv.error) + " · "
                                + t("ntp.port_busy_hint"))
                status.classes(replace="text-sm text-red")
            else:
                status.set_text(t("ntp.off"))
                status.classes(replace="text-sm text-grey")

        ui.timer(1.0, refresh)
        refresh()
