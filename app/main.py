"""LGS Test Tool — entry point.

Run with:  .venv\\Scripts\\python -m app.main   then open http://localhost:8080
"""
import os

from nicegui import ui


def build_ui() -> None:
    ui.label("LGS Test Tool — skeleton (scaffold commit)")


build_ui()

if __name__ in {"__main__", "__mp_main__"}:
    show = os.environ.get("LGS_TT_DOCKER") != "1" and os.environ.get("LGS_TT_NO_BROWSER") != "1"
    # reload=False is mandatory: the auto-reloader spawns a second process, which
    # would mean a second Modbus worker fighting over the COM port / TCP slot.
    ui.run(host="0.0.0.0", port=8080, title="LGS Test Tool", reload=False, show=show)
