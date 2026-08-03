"""Selectable UI themes (brand colors + light/dark), persisted in the config.

A theme drives three things: Quasar's brand colors (ui.colors), the dark-mode
plugin (which restyles cards/tables/inputs automatically), and the header bar's
own background/text classes — the header needs explicit classes because Quasar's
bg-* utilities are not dark-aware.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from nicegui import ui

from ..i18n import t


@dataclass(frozen=True)
class Theme:
    key: str
    dark: bool
    primary: str
    secondary: str
    accent: str
    header: str          # classes applied to the header bar


THEMES: dict[str, Theme] = {
    "light": Theme("light", False,
                   "#1976d2", "#26a69a", "#9c27b0", "bg-grey-2 text-black"),
    "dark": Theme("dark", True,
                  "#42a5f5", "#26a69a", "#ab47bc", "bg-grey-10 text-white"),
    "midnight": Theme("midnight", True,
                      "#64b5f6", "#4db6ac", "#7986cb", "bg-blue-grey-10 text-white"),
    "workshop": Theme("workshop", True,
                      "#ffd54f", "#4dd0e1", "#ff8a65", "bg-black text-white"),
    "solar": Theme("solar", False,
                   "#b26500", "#00796b", "#8d6e63", "bg-orange-1 text-brown-10"),
    "lab": Theme("lab", False,
                 "#2e7d32", "#00838f", "#6d4c41", "bg-green-1 text-green-10"),
}

DEFAULT_THEME = "light"

# The interface is text-first: no decorative icons anywhere, so what is left is
# only the glyphs Quasar draws to make its own controls work — dropdown arrows,
# checkbox ticks, the sort caret in tables. Those stay, in the thin square-
# cornered face, because a select with no arrow or a checkbox with no tick is
# not minimal, it is broken.
#
# NiceGUI bundles the static 400-weight instance, not the variable font, so
# font-variation-settings would be ignored — the face itself is the change.
_ICON_FACE_CSS = """
.q-icon.material-icons, i.material-icons, .material-icons {
    font-family: 'Material Symbols Sharp' !important;
    font-weight: normal;
}
/* Quasar decorates its empty-table row with a warning glyph — the message
   beside it already says the same thing. The upload button's glyph stays: it
   is the only thing on that button. */
.q-table__bottom--nodata .q-icon { display: none; }
"""

# Roboto is Quasar's default and reads as an Android app. The platform's own UI
# face looks native instead and pulls in the matching Thai face automatically
# (Leelawadee UI on Windows), so mixed EN/TH lines keep one weight and rhythm.
# System fonts need no download, so the portable exe is unaffected.
_FONT_CSS = """
body, .q-menu, .q-dialog, .q-tooltip, input, textarea, select, button {
    font-family: system-ui, -apple-system, "Segoe UI", "Leelawadee UI", Roboto,
                 "Noto Sans Thai", "Helvetica Neue", Arial, sans-serif;
}
"""

_state: dict = {"current": DEFAULT_THEME, "dark_el": None, "header": None,
                "header_classes": ""}


def current() -> Theme:
    return THEMES.get(_state["current"], THEMES[DEFAULT_THEME])


def init(key: str) -> None:
    """Create the dark-mode element and apply the stored theme (call once).

    Uses ui.colors(), which only takes effect while the page is being built —
    later switches go through apply() instead.
    """
    theme = THEMES.get(key, THEMES[DEFAULT_THEME])
    _state["current"] = theme.key
    ui.add_css(_FONT_CSS)
    ui.add_css(_ICON_FACE_CSS)
    _state["dark_el"] = ui.dark_mode(theme.dark)
    ui.colors(primary=theme.primary, secondary=theme.secondary, accent=theme.accent)
    _apply_header(theme)


def register_header(element) -> None:
    """Let the theme own the header bar's background/text classes."""
    _state["header"] = element
    _apply_header(current())


def _apply_header(theme: Theme) -> None:
    header = _state["header"]
    if header is None:
        return
    header.classes(theme.header, remove=_state["header_classes"])
    _state["header_classes"] = theme.header


def apply(key: str) -> None:
    """Switch themes at runtime (from an event handler).

    Brand colors go through Quasar.setCssVar: a second ui.colors() element
    created after the page is built does not re-apply the palette.
    """
    theme = THEMES.get(key, THEMES[DEFAULT_THEME])
    _state["current"] = theme.key
    if _state["dark_el"] is not None:
        _state["dark_el"].value = theme.dark
    ui.run_javascript(
        f"Quasar.setCssVar('primary', '{theme.primary}');"
        f"Quasar.setCssVar('secondary', '{theme.secondary}');"
        f"Quasar.setCssVar('accent', '{theme.accent}');"
    )
    _apply_header(theme)


def build_menu_items(on_select: Callable[[str], None]) -> None:
    """Theme choices as plain menu items.

    The caller owns the button and the menu — the header collects language,
    theme and about into one overflow menu, so this contributes items rather
    than a control of its own.
    """

    @ui.refreshable
    def items() -> None:
        for theme in THEMES.values():
            selected = theme.key == _state["current"]
            # Weight and colour mark the current theme; no glyph needed.
            ui.menu_item(t("theme." + theme.key),
                         on_click=lambda th=theme: _choose(th.key)) \
                .classes("text-primary font-bold" if selected else "")

    def _choose(key: str) -> None:
        apply(key)
        on_select(key)
        items.refresh()

    items()
