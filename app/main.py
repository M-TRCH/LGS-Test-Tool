"""LGS Test Tool — entry point.

Run with:  .venv\\Scripts\\python -m app.main   then open http://localhost:8080
"""
import os

from nicegui import app, ui

from . import config_store
from .modbus_worker import ModbusWorker
from .txn_log import TxnLog
from .ui import (Ctx, connection_bar, log_pane, tab_autotest, tab_control,
                 tab_danger, tab_install, tab_monitor, theme)
from .version import APP_VERSION

log = TxnLog()
worker = ModbusWorker(log)
worker.start()
cfg = config_store.load()
ctx = Ctx(worker=worker, log=log, cfg=cfg)


def build_ui() -> None:
    theme.init(ctx.cfg.theme)
    connection_bar.build(ctx)

    with ui.tabs().classes("w-full") as tabs:
        t_control = ui.tab("Control", icon="tune")
        t_monitor = ui.tab("Monitor", icon="monitor_heart")
        t_install = ui.tab("Installation Check", icon="grid_view")
        t_module = ui.tab("Module Test", icon="checklist")
        t_danger = ui.tab("Danger", icon="warning")

    with ui.tab_panels(tabs, value=t_control).classes("w-full"):
        with ui.tab_panel(t_control):
            tab_control.build(ctx)
        with ui.tab_panel(t_monitor):
            tab_monitor.build(ctx)
        with ui.tab_panel(t_install):
            tab_install.build(ctx)
        with ui.tab_panel(t_module):
            tab_autotest.build(ctx)
        with ui.tab_panel(t_danger):
            tab_danger.build(ctx)

    log_pane.build(ctx)


build_ui()
app.on_shutdown(lambda: (config_store.save(ctx.cfg), worker.shutdown()))


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
