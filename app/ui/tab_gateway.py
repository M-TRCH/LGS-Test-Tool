"""Gateway tab — read and edit the Opta gateway's own settings.

Talks the `$LGS` text console over USB (see app/gateway_config.py). The
gateway is not a Modbus device, so nothing here goes through pymodbus; the
worker lends the COM port for the duration of each exchange.
"""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..lgs_map import BAUD_WHITELIST
from . import Ctx

# Which settings each card shows, in display order.
CARD_RS485 = ("rs485.baud", "rs485.predelay_us", "rs485.postdelay_us",
              "rs485.t1_ms", "rs485.t2_ms")
CARD_USB = ("usb.gap_ms", "usb.max_ms")
CARD_NET = ("net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns",
            "net.port", "net.link_timeout_ms")

BOOL_KEYS = {"net.enabled", "net.dhcp"}
SOURCE_KEY = {"stored": "gw.src.stored", "defaults": "gw.src.defaults",
              "corrupt": "gw.src.corrupt", "unavailable": "gw.src.unavailable"}


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    # edits[key] = new value as text; only what the user actually changed
    state: dict = {"snapshot": None, "edits": {}}
    fields: dict = {}

    ui.label(t("gw.intro")).classes("text-sm text-grey")

    with ui.row().classes("items-center gap-3 flex-wrap"):
        detect_btn = ui.button(t("gw.detect"), icon="search")
        reload_btn = ui.button(t("gw.reload"), icon="refresh").props("outline")
        status = ui.badge("—").props("color=grey")
        dirty = ui.label("").classes("text-sm text-orange")
    transport_note = ui.label("").classes("text-sm text-red")

    cards = ui.column().classes("w-full gap-3")

    with ui.row().classes("items-center gap-3 flex-wrap"):
        save_btn = ui.button(t("gw.save"), color="primary", icon="save")
        ui.button(t("gw.discard"), icon="undo",
                  on_click=lambda: run_action("discard")).props("outline")
        ui.button(t("gw.defaults"), icon="restart_alt",
                  on_click=lambda: confirm_defaults()).props("outline")
        ui.button(t("gw.reboot"), icon="power_settings_new", color="red",
                  on_click=lambda: confirm_reboot()).props("outline")

    log_box = ui.log(max_lines=40).classes("w-full h-32 font-mono text-xs")

    # ── helpers ────────────────────────────────────────────────────────────
    def usable() -> tuple:
        """(ok, message) — the console is USB-only and needs a port."""
        if ctx.transport() != "rtu":
            return False, t("gw.usb_only")
        if not ctx.port():
            return False, t("gw.no_port")
        return True, ""

    def update_dirty() -> None:
        n = len(state["edits"])
        dirty.set_text(t("gw.dirty", n=n) if n else "")
        save_btn.set_visibility(bool(n))

    def stage(key: str, value) -> None:
        snap = state["snapshot"]
        current = snap.settings.get(key, "") if snap else ""
        text = str(int(value)) if isinstance(value, bool) else str(value)
        if text == current:
            state["edits"].pop(key, None)
        else:
            state["edits"][key] = text
        update_dirty()

    def field_row(key: str, snap) -> None:
        value = snap.settings.get(key, "—")
        if key in BOOL_KEYS:
            el = ui.switch(key, value=(value == "1"),
                           on_change=lambda e, k=key: stage(k, e.value))
        elif key == "rs485.baud":
            el = ui.select(list(BAUD_WHITELIST), value=int(value) if value.isdigit() else 9600,
                           label=key, on_change=lambda e, k=key: stage(k, e.value)) \
                .props("dense outlined").classes("w-56")
        else:
            el = ui.input(key, value=value,
                          on_change=lambda e, k=key: stage(k, e.value)) \
                .props("dense outlined").classes("w-56")
        fields[key] = el

    def render(snap) -> None:
        cards.clear()
        state["edits"].clear()
        update_dirty()
        if snap is None or not snap.ok:
            return
        info = snap.info

        with cards:
            with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.device")).classes("font-bold")
                    ui.label(f"fw {info.get('fw', '?')} · build {info.get('build', '?')}") \
                        .classes("text-sm")
                    ui.label(f"id {info.get('id', '?')} · mac {info.get('mac', '?')}") \
                        .classes("text-sm font-mono")
                    ui.label(f"uptime {info.get('sys.up', '?')} s · "
                             f"reset {info.get('sys.reset', '?')}").classes("text-sm")

                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.health")).classes("font-bold")
                    src = info.get("cfg.source", "?")
                    ui.label(f"{t('gw.source')}: {t(SOURCE_KEY.get(src, 'gw.src.defaults'))}") \
                        .classes("text-sm" + ("" if src == "stored" else " text-orange"))
                    ui.label(f"safe mode {info.get('sys.safe', '?')} · "
                             f"boot attempts {info.get('sys.boots', '?')}").classes("text-sm")
                    ui.label(t("gw.btn_hint", v=info.get("sys.btn", "?"))) \
                        .classes("text-xs text-grey")

                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.counters")).classes("font-bold")
                    ui.label(f"usb ok {info.get('cnt.usb_ok', 0)} · "
                             f"dropped {info.get('cnt.usb_drop', 0)}").classes("text-sm")
                    ui.label(f"rs485 ok {info.get('cnt.rs485_ok', 0)} · "
                             f"timeout {info.get('cnt.rs485_timeout', 0)}").classes("text-sm")
                    ui.label(f"rtt last {info.get('rtt.last_ms', 0)} ms · "
                             f"max {info.get('rtt.max_ms', 0)} ms").classes("text-sm")

            with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.rs485")).classes("font-bold")
                    for key in CARD_RS485:
                        field_row(key, snap)
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.usb")).classes("font-bold")
                    for key in CARD_USB:
                        field_row(key, snap)
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.net")).classes("font-bold")
                    ui.label(t("gw.net_phase1")).classes("text-xs text-grey")
                    for key in CARD_NET:
                        field_row(key, snap)

    def say(text: str) -> None:
        log_box.push(text)

    # ── actions ────────────────────────────────────────────────────────────
    async def do_detect() -> None:
        ok, message = usable()
        transport_note.set_text("" if ok else message)
        if not ok:
            return
        port = ctx.port()
        found = await worker.gw_probe(port)
        if not found:
            status.set_text(t("gw.not_found", port=port))
            status.props("color=red")
            state["snapshot"] = None
            render(None)
            return
        status.set_text(t("gw.detected", fw=found.get("fw", "?"), up=found.get("up", "?")))
        status.props("color=green")
        await do_reload()

    async def do_reload() -> None:
        ok, message = usable()
        transport_note.set_text("" if ok else message)
        if not ok:
            return
        snap = await worker.gw_read(ctx.port())
        state["snapshot"] = snap
        if not snap.ok:
            status.set_text(snap.note or t("gw.not_found", port=ctx.port()))
            status.props("color=red")
            say(f"read failed: {snap.note}")
        render(snap)

    async def run_action(action: str) -> None:
        ok, message = usable()
        if not ok:
            ui.notify(message, type="warning")
            return
        res = await worker.gw_action(ctx.port(), action)
        for step in res.steps:
            say(step)
        ui.notify(res.note or action, type="positive" if res.ok else "negative")
        await do_reload()

    async def do_save() -> None:
        ok, message = usable()
        if not ok:
            ui.notify(message, type="warning")
            return
        changes = dict(state["edits"])
        if not changes:
            return
        d = ui.dialog()
        with d, ui.card():
            ui.label(t("gw.save_title")).classes("font-bold")
            for key, value in changes.items():
                ui.label(f"{key} = {value}").classes("font-mono text-sm")
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("gw.save"), color="primary", on_click=lambda: d.submit(True))
        if not await d:
            return

        res = await worker.gw_write(ctx.port(), changes, save=True)
        for step in res.steps:
            say(step)
        if res.ok:
            ui.notify(t("gw.save_ok"), type="positive")
            if res.note:
                ui.notify(t("gw.needs_reboot", keys=res.note), type="warning", timeout=8000)
        else:
            ui.notify(res.note, type="negative", timeout=8000)
        await do_reload()

    async def confirm_defaults() -> None:
        d = ui.dialog()
        with d, ui.card():
            ui.label(t("gw.defaults_title")).classes("font-bold")
            ui.label(t("gw.defaults_body"))
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("gw.defaults"), color="red", on_click=lambda: d.submit(True))
        if await d:
            await run_action("defaults")

    async def confirm_reboot() -> None:
        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("gw.reboot_title")).classes("font-bold text-red")
            ui.label(t("gw.reboot_body"))
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("gw.reboot"), color="red", on_click=lambda: d.submit(True))
        if await d:
            await run_action("reboot")

    detect_btn.on_click(do_detect)
    reload_btn.on_click(do_reload)
    save_btn.on_click(do_save)
    save_btn.set_visibility(False)
