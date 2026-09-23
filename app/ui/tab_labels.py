"""Labels tab — a Brother `.lbx` sticker for the cabinet in front of you.

Everything machine-readable is read LIVE from the gateway when the button is
pressed: the short name, the IP, the MAC, and the row/channel strip that no
one has written down on site. So a sticker cannot describe a cabinet that no
longer exists — the worst it can be is old, and reprinting is free.

Two fields are typed, and neither is stored. The ward name is printed for
people to read. The **serial belongs to the warehouse's database**, not to
this tool: keeping a copy here could only ever drift out of step with the
one system that is actually authoritative about it. Replace an Opta and you
print a new sticker with the same serial and the new MAC, read live.
"""
from __future__ import annotations

from datetime import datetime, timezone

from nicegui import ui

from .. import labels
from ..i18n import t
from . import Ctx, helps


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state: dict = {"cab": None, "settings": {}}

    with ui.card().classes("p-3 w-full"):
        helps(ui.label(t("labels.card")).classes("font-bold text-lg"),
              t("labels.hint"))

        read_btn = ui.button(t("labels.read"))
        who = ui.label(t("labels.not_read")).classes("text-sm")

        with ui.row().classes("items-start gap-3 flex-wrap"):
            ward = ui.input(t("labels.ward")).props("dense outlined").classes("w-72")
            serial = ui.input(t("labels.serial")).props("dense outlined").classes("w-56")
        helps(serial, t("labels.serial_tip"))

        layout_sel = ui.select(
            {k: v.title for k, v in labels.LAYOUTS.items()},
            value="full", label=t("labels.layout")).props("dense outlined").classes("w-96")

        status = ui.label("").classes("text-sm")
        save_btn = ui.button(t("labels.save"))
        save_btn.disable()

        def describe() -> None:
            """Say what would be produced, before any tape is spent."""
            cab = state["cab"]
            if cab is None:
                status.set_text("")
                save_btn.disable()
                return
            cab.ward = (ward.value or "").strip()
            cab.serial = (serial.value or "").strip()
            try:
                blob, mm = labels.render(layout_sel.value, cab,
                                         created=_now())
            except labels.LabelTooBig as exc:
                status.set_text(t("labels.too_big", why=str(exc)))
                status.classes(replace="text-sm text-negative")
                save_btn.disable()
                return
            payload = cab.qr_payload()
            n = len(payload.encode("utf-8"))
            status.set_text(t("labels.ready", mm=f"{mm:.0f}", rows=len(cab.rows),
                              qr=n, spare=labels.QR_MAX_BYTES - n,
                              size=f"{len(blob):,}"))
            status.classes(replace="text-sm text-positive")
            save_btn.enable()

        async def do_read() -> None:
            read_btn.disable()
            who.set_text(t("labels.reading"))
            try:
                snap = await worker.gw_read(ctx.port())
            finally:
                read_btn.enable()
            if not snap.ok:
                who.set_text(t("labels.read_failed", why=snap.note or "?"))
                who.classes(replace="text-sm text-negative")
                state["cab"] = None
                describe()
                return
            s = snap.settings
            info = snap.info
            state["settings"] = s
            # INFO's own key names, checked against a live gateway: the
            # address is `net.ip` (there is no bare `ip`) and the name
            # appears in both halves. Getting these wrong prints a wrong
            # address onto a sticker that then outlives the mistake.
            state["cab"] = labels.CabinetLabel(
                name=s.get("sys.name") or info.get("sys.name", ""),
                ip=info.get("net.ip", ""),
                mac=info.get("mac", ""),
                rows=labels.rows_from_gateway(s),
            )
            cab = state["cab"]
            who.set_text(t("labels.read_ok", name=cab.name, ip=cab.ip,
                           mac=cab.mac, rows=len(cab.rows)))
            who.classes(replace="text-sm")
            describe()

        def do_save() -> None:
            cab = state["cab"]
            if cab is None:
                return
            cab.ward = (ward.value or "").strip()
            cab.serial = (serial.value or "").strip()
            blob, _mm = labels.render(layout_sel.value, cab, created=_now())
            stem = "".join(ch if ch.isalnum() or ch in "-_" else "-"
                           for ch in (cab.name or "cabinet")).strip("-") or "cabinet"
            ui.download(blob, f"{stem}-{layout_sel.value}.lbx")

        read_btn.on_click(do_read)
        save_btn.on_click(do_save)
        for widget in (ward, serial):
            widget.on("blur", lambda _e: describe())
        layout_sel.on("update:model-value", lambda _e: describe())

    with ui.card().classes("p-3 w-full"):
        ui.label(t("labels.print_card")).classes("font-bold")
        ui.label(t("labels.print_hint")).classes("text-sm")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
