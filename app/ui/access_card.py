"""Web password card (Gateway tab, beside the NTP card) -- a view over app/auth.py.

Both cards are about running the tool as a server that is left on at a site,
which is why they sit together. The card only ever shows whether a password
is set; the hash never leaves auth.json.
"""
from __future__ import annotations

from nicegui import ui

from .. import auth
from ..i18n import t
from . import Ctx, helps


def build(ctx: Ctx) -> None:
    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("auth.card")).classes("font-bold"), t("auth.hint"))
        status = ui.label().classes("text-sm")
        with ui.row().classes("items-center gap-3 flex-wrap"):
            pw1 = ui.input(t("auth.new"), password=True, password_toggle_button=True) \
                .props("dense outlined").classes("w-48")
            pw2 = ui.input(t("auth.repeat"), password=True) \
                .props("dense outlined").classes("w-48")
            set_btn = ui.button(t("auth.set"))
            off_btn = ui.button(t("auth.remove")).props("flat color=negative")
            out_btn = ui.button(t("auth.logout"),
                                on_click=lambda: ui.navigate.to("/logout")).props("flat")

        def refresh() -> None:
            on = auth.enabled()
            status.set_text(t("auth.on") if on else t("auth.off"))
            status.classes(replace="text-sm " + ("text-positive" if on else "text-warning"))
            off_btn.set_visibility(on)
            out_btn.set_visibility(on)

        def do_set() -> None:
            if pw1.value != pw2.value:
                ui.notify(t("auth.mismatch"), type="warning")
                return
            try:
                auth.set_password(pw1.value or "")
            except ValueError:
                ui.notify(t("auth.short", n=auth.MIN_LEN), type="warning")
                return
            pw1.set_value("")
            pw2.set_value("")
            ui.notify(t("auth.saved"), type="positive")
            # Setting rotates the cookie secret, so this very browser is signed
            # out too: go straight to the form rather than strand the page.
            ui.navigate.to("/login")

        with ui.dialog() as dlg, ui.card():
            ui.label(t("auth.remove_q"))
            with ui.row():
                ui.button(t("auth.cancel"), on_click=dlg.close).props("flat")

                def do_remove() -> None:
                    auth.clear_password()
                    dlg.close()
                    ui.notify(t("auth.removed"), type="info")
                    refresh()

                ui.button(t("auth.remove"), on_click=do_remove).props("color=negative")

        set_btn.on_click(do_set)
        off_btn.on_click(dlg.open)
        refresh()
