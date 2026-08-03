"""Control-table reference, opened from the header menu.

A dialog rather than a tab: you look a register up *while* working in Control
or Monitor, and a tab would make you leave the thing you were doing.
"""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..reference import SOURCE_REPO, control_table, filtered


def build_dialog():
    """Create the reference dialog and return it; the caller opens it."""
    markdown = control_table()

    dialog = ui.dialog().props("maximized")
    with dialog, ui.card().classes("w-full h-full flex flex-col"):
        with ui.row().classes("items-center gap-3 w-full no-wrap"):
            ui.label(t("ref.title")).classes("text-lg font-bold")
            search = ui.input(t("ref.search")).props("dense outlined clearable") \
                .classes("w-72")
            hits = ui.label("").classes("text-xs text-grey")
            ui.space()
            ui.button(t("btn.close"), on_click=dialog.close).props("flat no-caps")

        with ui.scroll_area().classes("w-full grow"):
            body = ui.markdown(markdown).classes("w-full")

        ui.label(t("ref.source", url=SOURCE_REPO)).classes("text-xs text-grey")

    def apply_filter() -> None:
        query = (search.value or "").strip()
        text = filtered(markdown, query)
        body.set_content(text)
        # Table rows carry a leading pipe; count those, not headings.
        rows = sum(1 for line in text.splitlines()
                   if line.startswith("|") and not set(line) <= set("|-: "))
        hits.set_text(t("ref.hits", n=max(rows - 1, 0)) if query else "")

    search.on_value_change(apply_filter)
    return dialog
