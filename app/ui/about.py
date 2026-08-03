"""About dialog: what the tool is, which version runs, and the release notes."""
from __future__ import annotations

from nicegui import ui

from ..changelog import RELEASES
from ..config_store import data_dir
from ..i18n import t
from ..version import APP_VERSION


def build_dialog():
    """Create the About dialog and hand it back; the caller opens it.

    Built outside the header menu on purpose — a dialog defined inside a menu
    would be torn down with it the moment the item is clicked.
    """
    dialog = ui.dialog()
    with dialog, ui.card().classes("w-[640px] max-w-full"):
        with ui.row().classes("items-center gap-2"):
            ui.label("LGS Test Tool").classes("text-xl font-bold")
            ui.badge(f"v{APP_VERSION}").props("color=primary")
        ui.label(t("about.desc")).classes("text-sm")
        ui.label(t("about.data", path=data_dir())).classes("text-xs text-grey")

        ui.separator()
        ui.label(t("about.notes")).classes("font-bold")
        with ui.scroll_area().classes("w-full h-72"):
            for index, rel in enumerate(RELEASES):
                with ui.expansion(f"v{rel.version} — {rel.date}",
                                  value=(index == 0)).classes("w-full"):
                    with ui.column().classes("gap-1"):
                        for note in rel.notes:
                            with ui.row().classes("items-start gap-2 no-wrap"):
                                ui.label("•").classes("text-primary")
                                ui.label(note).classes("text-sm")

        with ui.row().classes("w-full justify-end"):
            ui.button(t("btn.close"), on_click=dialog.close).props("flat")

    return dialog
