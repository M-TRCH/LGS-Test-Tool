"""LGS Test Tool — entry point.

Run with:  .venv\\Scripts\\python -m app.main   then open http://localhost:8080
"""
import os

from nicegui import app, ui

from . import config_store, i18n
from .modbus_worker import ModbusWorker
from .txn_log import TxnLog
from .ui import (Ctx, connection_bar, log_pane, tab_autotest, tab_control,
                 tab_danger, tab_install, tab_monitor, tab_ota, theme)
from .version import APP_VERSION

# Shared across browsers: one Modbus worker, one log, one settings file — the
# bus and the gateway's single TCP slot cannot be shared anyway.
log = TxnLog()
worker = ModbusWorker(log)
worker.start()
cfg = config_store.load()


@ui.page("/")
def index() -> None:
    """Built per browser session, so switching language just reloads the page."""
    i18n.set_language(cfg.language)
    ctx = Ctx(worker=worker, log=log, cfg=cfg)

    theme.init(cfg.theme)
    connection_bar.build(ctx)

    with ui.tabs().classes("w-full") as tabs:
        t_control = ui.tab("control", i18n.t("tab.control"), icon="tune")
        t_monitor = ui.tab("monitor", i18n.t("tab.monitor"), icon="monitor_heart")
        t_install = ui.tab("install", i18n.t("tab.install"), icon="grid_view")
        t_module = ui.tab("module", i18n.t("tab.module"), icon="checklist")
        t_ota = ui.tab("ota", i18n.t("tab.ota"), icon="system_update")
        t_danger = ui.tab("danger", i18n.t("tab.danger"), icon="warning")

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
