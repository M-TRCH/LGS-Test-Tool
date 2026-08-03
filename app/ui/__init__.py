"""Shared UI context passed to every builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..config_store import AppConfig
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
