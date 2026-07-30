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


def build_picker(on_select: Callable[[str], None]) -> None:
    """Palette button + theme menu, for the header."""

    @ui.refreshable
    def items() -> None:
        for theme in THEMES.values():
            marker = "●" if theme.key == _state["current"] else "○"
            ui.menu_item(f"{marker}  {t('theme.' + theme.key)}",
                         on_click=lambda th=theme: _choose(th.key))

    def _choose(key: str) -> None:
        apply(key)
        on_select(key)
        items.refresh()

    with ui.button(icon="palette").props("dense flat round").tooltip(t("hdr.theme_tooltip")):
        with ui.menu():
            items()
