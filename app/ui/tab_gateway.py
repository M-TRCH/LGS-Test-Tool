"""Gateway tab — read and edit the Opta gateway's own settings.

Talks the `$LGS` text console over USB (see app/gateway_config.py). The
gateway is not a Modbus device, so nothing here goes through pymodbus; the
worker lends the COM port for the duration of each exchange.
"""
from __future__ import annotations

from nicegui import ui

from ..i18n import t
from ..lgs_map import BAUD_WHITELIST
from ..opta_update import OptaConfig
from ..ota import Done, Line, Progress
from . import Ctx, helps

# Which settings each card shows, in display order.
CARD_IDENTITY = ("sys.name",)
CARD_RS485 = ("rs485.baud", "rs485.predelay_us", "rs485.postdelay_us",
              "rs485.t1_ms", "rs485.t2_ms")
CARD_USB = ("usb.gap_ms", "usb.max_ms")
CARD_NET = ("net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns",
            "net.port", "net.link_timeout_ms")

BOOL_KEYS = {"net.enabled", "net.dhcp"}


def label_of(key: str) -> str:
    """Plain-language name for a setting, falling back to the console key."""
    friendly = t(f"gwf.{key}")
    return key if friendly == f"gwf.{key}" else friendly


def hint_of(key: str) -> str:
    text = t(f"gwf.{key}.hint")
    return "" if text == f"gwf.{key}.hint" else text


def shown(key: str, value: str) -> str:
    """A value as a person reads it — "on"/"off" rather than 1/0."""
    if key in BOOL_KEYS:
        return t("gw.on") if value == "1" else t("gw.off")
    return value or "—"


SOURCE_KEY = {"stored": "gw.src.stored", "defaults": "gw.src.defaults",
              "corrupt": "gw.src.corrupt", "unavailable": "gw.src.unavailable"}
LINK_KEY = {"up": "gw.link.up", "nolink": "gw.link.nolink",
            "disabled": "gw.link.disabled", "safe": "gw.link.safe"}
LINK_COLOUR = {"up": "text-green", "nolink": "text-orange",
               "disabled": "text-grey", "safe": "text-orange"}


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    # edits[key] = new value as text; only what the user actually changed
    state: dict = {"snapshot": None, "edits": {}}
    fields: dict = {}

    with ui.row().classes("items-center gap-3 flex-wrap"):
        detect_btn = helps(ui.button(t("gw.detect")), t("gw.intro"))
        reload_btn = ui.button(t("gw.reload")).props("outline")
        status = ui.badge("—").props("color=grey")
        dirty = ui.label("").classes("text-sm text-orange")
    transport_note = ui.label("").classes("text-sm text-red")

    cards = ui.column().classes("w-full gap-3")

    with ui.row().classes("items-center gap-3 flex-wrap"):
        save_btn = ui.button(t("gw.save"), color="primary")
        ui.button(t("gw.discard"),
                  on_click=lambda: run_action("discard")).props("outline")
        ui.button(t("gw.defaults"),
                  on_click=lambda: confirm_defaults()).props("outline")
        ui.button(t("gw.reboot"), color="red",
                  on_click=lambda: confirm_reboot()).props("outline")

    # ── firmware update ────────────────────────────────────────────────────
    # Below the settings and behind its own confirm: this is the one action
    # on this page that can leave the whole bus without a bridge.
    fw_state: dict = {"seq": 0, "image": b"", "name": ""}
    with ui.card().classes("p-3 w-full border border-orange-400 q-mt-sm"):
        helps(ui.label(t("gw.fw_card")).classes("font-bold text-orange"),
              t("gw.fw_hint"))

        def on_fw_upload(e) -> None:
            fw_state["image"], fw_state["name"] = e.content.read(), e.name
            fw_label.set_text(t("gw.fw_chosen", name=e.name,
                                size=f"{len(fw_state['image']):,}"))

        ui.upload(on_upload=on_fw_upload, auto_upload=True, max_files=1) \
            .props('accept=".bin" flat dense').classes("w-full")
        fw_label = ui.label(t("gw.fw_none")).classes("text-sm")
        with ui.row().classes("items-center gap-3 q-mt-sm"):
            fw_btn = ui.button(t("gw.fw_run"), color="red").props("outline")
            prov_btn = helps(
                ui.button(t("gw.prov_run"), color="red").props("outline"),
                t("gw.prov_hint"))
            ui.button(t("btn.cancel"),
                      on_click=lambda: worker.cancel_commission()).props("flat")
            fw_progress = ui.linear_progress(value=0.0, show_value=False) \
                .classes("w-48")
            fw_badge = ui.badge("—").props("color=grey")

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
        name = label_of(key)
        with ui.column().classes("gap-0 w-72 mb-2"):
            if key in BOOL_KEYS:
                el = ui.switch(name, value=(value == "1"),
                               on_change=lambda e, k=key: stage(k, e.value))
            elif key == "rs485.baud":
                el = ui.select(list(BAUD_WHITELIST),
                               value=int(value) if value.isdigit() else 9600,
                               label=name, on_change=lambda e, k=key: stage(k, e.value)) \
                    .props("dense outlined").classes("w-full")
            else:
                el = ui.input(name, value=value,
                              on_change=lambda e, k=key: stage(k, e.value)) \
                    .props("dense outlined").classes("w-full")
            # What the setting is for, plus the console key for support —
            # both on hover, so the card stays a list of settings.
            hint = hint_of(key)
            helps(el, f"{hint} ({key})" if hint else key)
            # Someone may have staged a change from a terminal; say so rather
            # than showing the running value as if nothing were pending.
            pending = snap.staged.get(key)
            if pending is not None:
                ui.label(t("gw.pending_on_gateway", v=shown(key, pending))) \
                    .classes("text-xs text-orange leading-tight mt-1")
        fields[key] = el

    def apply_pending(values: dict) -> None:
        """Drop values into the fields as ordinary unsaved edits."""
        for key, text in values.items():
            el = fields.get(key)
            if el is None:
                continue
            if key in BOOL_KEYS:
                el.set_value(text == "1")
            elif key == "rs485.baud":
                el.set_value(int(text) if text.isdigit() else text)
            else:
                el.set_value(text)

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
                    if info.get("macsrc") == "placeholder":
                        ui.label(t("gw.mac_placeholder")).classes("text-xs text-orange")
                    ui.label(f"uptime {info.get('sys.up', '?')} s · "
                             f"reset {info.get('sys.reset', '?')}").classes("text-sm")

                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.health")).classes("font-bold")
                    src = info.get("cfg.source", "?")
                    ui.label(f"{t('gw.source')}: {t(SOURCE_KEY.get(src, 'gw.src.defaults'))}") \
                        .classes("text-sm" + ("" if src == "stored" else " text-orange"))
                    helps(ui.label(f"safe mode {info.get('sys.safe', '?')} · "
                                   f"boot attempts {info.get('sys.boots', '?')}")
                          .classes("text-sm"),
                          t("gw.btn_hint", v=info.get("sys.btn", "?")))

                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.counters")).classes("font-bold")
                    ui.label(f"usb ok {info.get('cnt.usb_ok', 0)} · "
                             f"dropped {info.get('cnt.usb_drop', 0)}").classes("text-sm")
                    ui.label(f"tcp ok {info.get('cnt.tcp_ok', 0)}").classes("text-sm")
                    ui.label(f"rs485 ok {info.get('cnt.rs485_ok', 0)} · "
                             f"timeout {info.get('cnt.rs485_timeout', 0)}").classes("text-sm")
                    ui.label(f"rtt last {info.get('rtt.last_ms', 0)} ms · "
                             f"max {info.get('rtt.max_ms', 0)} ms").classes("text-sm")

                # The one card that answers "is the LAN side actually working?"
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.link")).classes("font-bold")
                    link = info.get("net.state", "disabled")
                    ip = info.get("net.ip", "0.0.0.0")
                    port = info.get("net.port", "502")
                    # State and address stay on screen — that is the answer to
                    # "is it working?". The advice behind each state hovers.
                    advice = {"up": t("gw.link.serving", ip=ip, port=port),
                              "nolink": t("gw.link.nolink_hint"),
                              "disabled": t("gw.link.off_hint")}.get(link, "")
                    helps(ui.label(t(LINK_KEY.get(link, "gw.link.disabled")))
                          .classes("text-sm font-bold "
                                   + LINK_COLOUR.get(link, "text-grey")), advice)
                    if link == "up":
                        ui.label(f"{ip}:{port}").classes("text-sm font-mono")
                        ui.label(t("gw.link.client") if info.get("net.client") == "1"
                                 else t("gw.link.noclient")).classes("text-xs text-grey")

            with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.identity")).classes("font-bold")
                    for key in CARD_IDENTITY:
                        field_row(key, snap)
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.rs485")).classes("font-bold")
                    for key in CARD_RS485:
                        field_row(key, snap)
                with ui.card().classes("p-3 grow"):
                    ui.label(t("gw.card.usb")).classes("font-bold")
                    for key in CARD_USB:
                        field_row(key, snap)
                with ui.card().classes("p-3 grow"):
                    helps(ui.label(t("gw.card.net")).classes("font-bold"),
                          t("gw.net_hint"))
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
        if res.ok and res.values:
            apply_pending(res.values)
            ui.notify(t("gw.defaults_loaded", n=len(res.values)), type="warning",
                      timeout=7000)

    async def do_save() -> None:
        ok, message = usable()
        if not ok:
            ui.notify(message, type="warning")
            return
        changes = dict(state["edits"])
        if not changes:
            return
        snap = state["snapshot"]
        d = ui.dialog()
        with d, ui.card():
            ui.label(t("gw.save_title")).classes("font-bold")
            for key, value in changes.items():
                was = snap.settings.get(key, "") if snap else ""
                with ui.row().classes("items-baseline gap-2"):
                    ui.label(f"{label_of(key)}:").classes("text-sm")
                    ui.label(shown(key, was)).classes("text-sm text-grey line-through")
                    ui.label("→").classes("text-sm text-grey")
                    ui.label(shown(key, value)).classes("text-sm font-bold")
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
                friendly = ", ".join(label_of(k.strip()) for k in res.note.split(",")
                                     if k.strip())
                ui.notify(t("gw.needs_reboot", keys=friendly), type="warning",
                          timeout=8000)
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

    # ── firmware update: confirm, run, drain ───────────────────────────────
    async def do_fw_update() -> None:
        ok, why = usable()
        if not ok:
            ui.notify(why, type="negative")
            return
        if not fw_state["image"]:
            ui.notify(t("gw.fw_need_image"), type="warning")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("gw.fw_confirm_title")).classes("font-bold text-red")
            ui.label(t("gw.fw_confirm_body", name=fw_state["name"],
                       port=ctx.port()))
            with ui.row():
                ui.button(t("btn.cancel"),
                          on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("gw.fw_run"), color="red",
                          on_click=lambda: d.submit(True))
        if not await d:
            return

        log_box.clear()
        fw_progress.set_value(0.0)
        fw_badge.set_text(t("res.running"))
        fw_badge.props("color=blue")
        cfg = OptaConfig(image=fw_state["image"], filename=fw_state["name"],
                         port=ctx.port())
        if not worker.start_opta_update(cfg):
            ui.notify(t("msg.worker_busy"), type="negative")
            fw_badge.set_text("—")
            fw_badge.props("color=grey")

    fw_btn.on_click(do_fw_update)

    async def do_provision() -> None:
        ok, why = usable()
        if not ok:
            ui.notify(why, type="negative")
            return
        if not fw_state["image"]:
            ui.notify(t("gw.fw_need_image"), type="warning")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("gw.prov_confirm_title")).classes("font-bold text-red")
            ui.label(t("gw.prov_confirm_body", port=ctx.port(),
                       name=fw_state["name"]))
            with ui.row():
                ui.button(t("btn.cancel"),
                          on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("gw.prov_run"), color="red",
                          on_click=lambda: d.submit(True))
        if not await d:
            return

        log_box.clear()
        fw_progress.set_value(0.0)
        fw_badge.set_text(t("res.running"))
        fw_badge.props("color=blue")
        cfg = OptaConfig(image=fw_state["image"], filename=fw_state["name"],
                         port=ctx.port())
        if not worker.start_opta_provision(cfg):
            ui.notify(t("msg.worker_busy"), type="negative")
            fw_badge.set_text("—")
            fw_badge.props("color=grey")

    prov_btn.on_click(do_provision)

    def drain_fw() -> None:
        fw_state["seq"], events = worker.drain_commission_events(fw_state["seq"])
        for ev in events:
            if isinstance(ev, Line):
                log_box.push(ev.text)
            elif isinstance(ev, Progress):
                fw_progress.set_value(ev.done / max(1, ev.total))
            elif isinstance(ev, Done):
                fw_progress.set_value(1.0)
                fw_badge.set_text(t("res.pass") if ev.ok else t("res.fail"))
                fw_badge.props("color=green" if ev.ok else "color=red")
                ui.notify(ev.summary,
                          type="positive" if ev.ok else "negative", timeout=9000)

    ui.timer(0.2, drain_fw)
