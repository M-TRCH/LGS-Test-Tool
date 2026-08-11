"""Shared UI context passed to every builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..config_store import AppConfig
from ..lgs_map import CabinetLayout, layout_by_key
from ..modbus_worker import ModbusWorker, MonitorSnapshot
from ..txn_log import TxnLog


def warning_banner(text: str):
    """A page-level caution strip.

    The interface carries no icons, so colour and placement do the signalling:
    Quasar's banner keeps its own padding and rounding and stays legible on
    every theme, unlike a hand-rolled coloured div.
    """
    from nicegui import ui
    with ui.element("q-banner").props("dense rounded") \
            .classes("bg-red text-white text-sm w-full") as banner:
        ui.label(text)
    return banner


def inline_warning(classes: str = "text-red text-sm"):
    """A label that hides itself while it is empty.

    Returns the label, so callers keep using set_text() and the row follows.
    """
    from nicegui import ui
    with ui.row().classes("items-center gap-1 no-wrap") as row:
        label = ui.label("").classes(classes)
    row.bind_visibility_from(label, "text", backward=bool)
    return label


def helps(element, text: str):
    """Attach explanatory text as a hover tooltip instead of on-screen text.

    Explanations belong on the control they explain, not stacked under it —
    a page of captions is harder to scan than the settings themselves. The
    help cursor is the only visible sign, so nothing is hidden without a hint
    that it is there.

    Anything the operator must see *without* hovering — live status, warnings,
    the consequences of a destructive button — stays a real label.
    """
    if text:
        element.tooltip(text)
        element.classes("cursor-help")
    return element


async def confirm(title: str, body: str, ok_label: str, *,
                  color: str = "red", danger_border: bool = False) -> bool:
    """One question, Cancel or OK — the shape every destructive action uses.

    Deliberately dumb: no callbacks, no extra widgets. A dialog whose body
    needs to be built (like SAVE's change list) stays bespoke at its caller.
    """
    from nicegui import ui

    from ..i18n import t

    d = ui.dialog()
    card_classes = "border border-red-500" if danger_border else ""
    with d, ui.card().classes(card_classes):
        title_classes = "font-bold" + (" text-red" if color == "red" else "")
        ui.label(title).classes(title_classes)
        ui.label(body)
        with ui.row():
            ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
            ui.button(ok_label, color=color, on_click=lambda: d.submit(True))
    return bool(await d)


def bundled_picker(kind: str, on_pick) -> None:
    """Offer the released images that ship inside the tool, for one job.

    `on_pick(data, filename, image)` gets the same things an upload produces,
    so each caller keeps one code path for validating and arming an image.
    Picking is a deliberate click rather than a pre-armed default: an image
    that armed itself when a tab opened would sit one stray click away from
    being flashed into a cabinet.
    """
    from nicegui import ui

    from .. import firmware_bundle as fb
    from ..i18n import t

    images = fb.for_kind(kind)
    if not images:
        return
    options = {img.key: img.label for img in images}
    with ui.row().classes("items-center gap-2 w-full no-wrap"):
        select = helps(
            ui.select(options, value=images[0].key)
              .props("dense outlined").classes("grow"),
            t("fw.bundled_hint"))

        def use() -> None:
            image = fb.by_key(select.value)
            if image is None:
                return
            try:
                data = fb.load(image)
            except fb.BundleError as exc:
                ui.notify(str(exc), type="negative", timeout=9000)
                return
            on_pick(data, image.filename, image)

        ui.button(t("fw.use"), on_click=use).props("outline dense no-caps")


@dataclass
class Ctx:
    worker: ModbusWorker
    log: TxnLog
    cfg: AppConfig
    device_id_getter: object = None            # set by connection_bar
    device_id_setter: object = None            # set by connection_bar
    port_getter: object = None                 # set by connection_bar
    transport_getter: object = None            # set by connection_bar
    latest_snapshot: Optional[MonitorSnapshot] = None
    last_scan_ids: tuple = ()                  # IDs found by the most recent scan

    def device_id(self) -> int:
        return int(self.device_id_getter()) if self.device_id_getter else self.cfg.device_id

    def port(self) -> str:
        return str(self.port_getter()) if self.port_getter else self.cfg.com_port

    def transport(self) -> str:
        return str(self.transport_getter()) if self.transport_getter else self.cfg.transport

    def cabinet(self) -> CabinetLayout:
        """The cabinet this tool is pointed at — header-picked, persisted.

        Read fresh every call: cfg is the one shared object, so a header
        change reaches every tab without any wiring.
        """
        return layout_by_key(self.cfg.cabinet)
