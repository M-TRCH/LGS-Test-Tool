"""LGS Test Tool — entry point.

Run with:  .venv\\Scripts\\python -m app.main   then open http://localhost:8080
"""
import os

from nicegui import app, ui

from . import config_store, i18n
from .modbus_worker import ModbusWorker
from .txn_log import TxnLog
from .ui import (Ctx, connection_bar, helps, log_pane, tab_autotest,
                 tab_commission, tab_control, tab_danger, tab_gateway,
                 tab_install, tab_monitor, tab_ota, theme)
from .version import APP_VERSION

# Shared across browsers: one Modbus worker, one log, one settings file — the
# bus and the gateway's single TCP slot cannot be shared anyway.
log = TxnLog()
worker = ModbusWorker(log)
worker.start()
cfg = config_store.load()
worker.cubeprog_path = cfg.cubeprog_path


@ui.page("/")
def index() -> None:
    """Built per browser session, so switching language just reloads the page."""
    i18n.set_language(cfg.language)
    ctx = Ctx(worker=worker, log=log, cfg=cfg)

    theme.init(cfg.theme)
    connection_bar.build(ctx)

    with ui.row(align_items="center").classes("w-full no-wrap"):
        with ui.tabs().classes("grow") as tabs:
            t_control = ui.tab("control", i18n.t("tab.control"))
            t_monitor = ui.tab("monitor", i18n.t("tab.monitor"))
            t_install = ui.tab("install", i18n.t("tab.install"))
            t_module = ui.tab("module", i18n.t("tab.module"))
            t_ota = ui.tab("ota", i18n.t("tab.ota"))
            t_commission = ui.tab("commission", i18n.t("tab.commission"))
            t_gateway = ui.tab("gateway", i18n.t("tab.gateway"))
            t_danger = ui.tab("danger", i18n.t("tab.danger"))

        # Everyday pages stay; the installation / maintenance pages appear
        # only in advanced mode. Hiding Danger from the default view is the
        # point, not a side effect: the people this switch exists for are the
        # ones a stray factory reset would hurt.
        advanced_tabs = (t_ota, t_commission, t_gateway, t_danger)
        adv = helps(ui.switch(i18n.t("hdr.advanced"), value=cfg.advanced_mode)
                    .props("dense").classes("shrink-0 pr-2"),
                    i18n.t("hdr.advanced_tip"))

        def apply_mode() -> None:
            show = bool(adv.value)
            for tab in advanced_tabs:
                tab.set_visibility(show)
            # Leaving someone parked on a page that just vanished would look
            # like a frozen app, so fall back to the first everyday page.
            if not show and str(tabs.value) in {t.props["name"]
                                                for t in advanced_tabs}:
                tabs.set_value(t_control)
            if cfg.advanced_mode != show:
                cfg.advanced_mode = show
                config_store.save(cfg)

        adv.on_value_change(apply_mode)
        apply_mode()

    with ui.tab_panels(tabs, value=t_control).classes("w-full"):
        with ui.tab_panel(t_control):
            tab_control.build(ctx)
        with ui.tab_panel(t_monitor):
            tab_monitor.build(ctx)
        with ui.tab_panel(t_install):
            tab_install.build(ctx)
        with ui.tab_panel(t_module):
            tab_autotest.build(ctx)
        with ui.tab_panel(t_ota):
            tab_ota.build(ctx)
        with ui.tab_panel(t_commission):
            tab_commission.build(ctx)
        with ui.tab_panel(t_gateway):
            tab_gateway.build(ctx)
        with ui.tab_panel(t_danger):
            tab_danger.build(ctx)

    log_pane.build(ctx)


app.on_shutdown(lambda: (config_store.save(cfg), worker.shutdown()))


def run() -> None:
    """Start the server (also the entry point for the packaged .exe)."""
    print(f"LGS Test Tool v{APP_VERSION}")
    show = os.environ.get("LGS_TT_DOCKER") != "1" and os.environ.get("LGS_TT_NO_BROWSER") != "1"
    # reload=False is mandatory: the auto-reloader spawns a second process, which
    # would mean a second Modbus worker fighting over the COM port / TCP slot.
    ui.run(host="0.0.0.0", port=8080, title=f"LGS Test Tool v{APP_VERSION}",
           reload=False, show=show)


if __name__ in {"__main__", "__mp_main__"}:
    run()
