"""About dialog: what the tool is, which version runs, and the release notes."""
from __future__ import annotations

from nicegui import ui

from ..changelog import RELEASES
from ..config_store import data_dir
from ..version import APP_VERSION


def build_button() -> None:
    dialog = ui.dialog()
    with dialog, ui.card().classes("w-[640px] max-w-full"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("science").classes("text-primary text-2xl")
            ui.label("LGS Test Tool").classes("text-xl font-bold")
            ui.badge(f"v{APP_VERSION}").props("color=primary")
        ui.label("Test tool for LGS R5.0 modules over Modbus RTU (COM port) or "
                 "Modbus TCP (LGS gateway).").classes("text-sm")
        ui.label(f"Data and CSV exports: {data_dir()}").classes("text-xs text-grey")

        ui.separator()
        ui.label("Release notes").classes("font-bold")
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
            ui.button("Close", on_click=dialog.close).props("flat")

    ui.button(icon="info", on_click=dialog.open).props("dense flat round") \
        .tooltip(f"about — v{APP_VERSION} and release notes")
