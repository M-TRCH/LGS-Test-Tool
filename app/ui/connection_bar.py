"""Persistent header: transport selection, slave ID, scan, connect, status chip."""
from __future__ import annotations

from nicegui import ui

from .. import config_store, i18n
from ..i18n import t
from ..lgs_map import (BAUD_WHITELIST, CABINET_LAYOUTS, DEFAULT_CABINET_KEY,
                       FACTORY_DEFAULT_ID, GRID_COLS, GRID_IDS, GRID_ROWS,
                       SETID_TEMP_ID)
from ..transports import RtuSettings, TcpSettings, list_com_ports
from ..version import APP_VERSION
from . import (Ctx, about, helps, reference_dialog as reference_mod,
               theme as theme_mod)


def _port_options() -> dict:
    ports = list_com_ports()
    return {p.device: p.label for p in ports}


def build(ctx: Ctx) -> None:
    cfg = ctx.cfg
    worker = ctx.worker

    # background/text classes come from the active theme (see ui/theme.py)
    with ui.header().classes("items-center gap-3 flex-wrap q-py-xs") \
            .props("bordered") as header:
        theme_mod.register_header(header)
        ui.label("LGS Test Tool").classes("text-lg font-bold text-primary")
        ui.badge(f"v{APP_VERSION}").props("color=primary outline").classes("text-xs")

        transport = ui.radio({"rtu": t("hdr.transport.rtu"), "tcp": t("hdr.transport.tcp")},
                             value=cfg.transport).props("inline dense")

        with ui.row().classes("items-center gap-2") as rtu_row:
            opts = _port_options()
            initial = cfg.com_port if cfg.com_port in opts else (next(iter(opts), None))
            for dev, label in opts.items():                     # prefer the Opta bridge
                if "Opta" in label:
                    initial = cfg.com_port if cfg.com_port in opts else dev
                    break
            com_select = ui.select(opts or {"": "(no ports)"}, value=initial,
                                   label=t("hdr.com_port")) \
                .classes("min-w-[260px]").props("dense outlined")

            def refresh_ports() -> None:
                new = _port_options()
                com_select.set_options(new or {"": "(no ports)"})
                for dev, label in new.items():
                    if "Opta" in label:
                        com_select.set_value(dev)
                        break
                ui.notify(t("msg.ports_found", n=len(new)), type="info")

            ui.button(t("hdr.rescan"), on_click=refresh_ports) \
                .props("flat dense no-caps")
            baud_select = ui.select(list(BAUD_WHITELIST), value=cfg.baud,
                                    label=t("hdr.baud")).props("dense outlined").classes("w-24")
            ui.label("8N1").classes("text-xs text-grey")

        with ui.row().classes("items-center gap-2") as tcp_row:
            host_input = ui.input(t("hdr.host"), value=cfg.tcp_host) \
                .props("dense outlined").classes("w-40")
            port_input = helps(ui.number(t("hdr.port"), value=cfg.tcp_port, min=1,
                                         max=65535, format="%d")
                               .props("dense outlined").classes("w-24"),
                               t("hdr.single_client"))

        def sync_rows() -> None:
            rtu_row.set_visibility(transport.value == "rtu")
            tcp_row.set_visibility(transport.value == "tcp")

        transport.on_value_change(sync_rows)
        sync_rows()

        # Which cabinet the tool is pointed at — the one fact every
        # whole-cabinet action follows, so it lives here with the other
        # "what am I talking to" facts and is saved the moment it changes.
        cabinet_opts = {l.key: l.label for l in CABINET_LAYOUTS}
        cabinet_select = helps(
            ui.select(cabinet_opts,
                      value=cfg.cabinet if cfg.cabinet in cabinet_opts
                      else DEFAULT_CABINET_KEY,
                      label=t("hdr.cabinet"))
            .props("dense outlined").classes("w-36"),
            t("hdr.cabinet_tip"))

        def cabinet_changed(e) -> None:
            cfg.cabinet = str(e.value)
            config_store.save(cfg)

        cabinet_select.on_value_change(cabinet_changed)

        id_input = ui.number(t("hdr.slave_id"), value=cfg.device_id, min=1, max=247,
                             format="%d").props("dense outlined").classes("w-28")

        def id_changed() -> None:
            if int(id_input.value or 0) == SETID_TEMP_ID:
                ui.notify(t("msg.id_reserved", id=SETID_TEMP_ID), type="info")

        id_input.on_value_change(id_changed)
        ctx.device_id_getter = lambda: int(id_input.value or FACTORY_DEFAULT_ID)
        ctx.device_id_setter = lambda v: id_input.set_value(int(v))
        ctx.port_getter = lambda: str(com_select.value or "")
        ctx.transport_getter = lambda: str(transport.value)

        # clickable grid picker (typing in the field still works as before)
        with ui.button(t("hdr.grid")).props("dense flat no-caps") \
                .tooltip(t("hdr.grid_tooltip")):
            with ui.menu() as id_menu:
                with ui.column().classes("gap-1 p-3"):
                    ui.label(t("hdr.grid_title")).classes("text-xs text-grey q-mb-xs")
                    for r in range(1, GRID_ROWS + 1):
                        with ui.row().classes("gap-1 flex-nowrap"):
                            for c in range(1, GRID_COLS + 1):
                                gid = r * 10 + c
                                ui.button(str(gid),
                                          on_click=lambda gid=gid: (id_input.set_value(gid),
                                                                    id_menu.close())) \
                                    .props("flat no-caps") \
                                    .classes("w-14 min-w-0 font-mono text-base")
                    ui.separator().classes("q-my-xs")
                    with ui.row().classes("gap-1 flex-nowrap w-full"):
                        ui.button(t("hdr.id_setid", id=SETID_TEMP_ID),
                                  on_click=lambda: (id_input.set_value(SETID_TEMP_ID),
                                                    id_menu.close())) \
                            .props("flat no-caps").classes("grow min-w-0")
                        ui.button(t("hdr.id_factory", id=FACTORY_DEFAULT_ID),
                                  on_click=lambda: (id_input.set_value(FACTORY_DEFAULT_ID),
                                                    id_menu.close())) \
                            .props("flat no-caps").classes("grow min-w-0")

        # ── scan ───────────────────────────────────────────────────────────
        def current_settings():
            if transport.value == "rtu":
                if not com_select.value:
                    ui.notify(t("msg.no_com"), type="negative")
                    return None
                return RtuSettings(str(com_select.value), int(baud_select.value))
            return TcpSettings(str(host_input.value), int(port_input.value))

        scan_dialog = ui.dialog()
        with scan_dialog, ui.card().classes("min-w-[360px]"):
            ui.label(t("scan.title")).classes("font-bold")
            scan_progress = ui.label("...")
            scan_found = ui.label(t("scan.found", ids="—"))
            scan_error = ui.label("").classes("text-red text-sm")
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_scan()).props("flat")
                ui.button(t("btn.close"), on_click=scan_dialog.close).props("flat")

        scan_state = {"seq": 0, "count": 0, "total": 0, "found": []}

        def drain_scan() -> None:
            scan_state["seq"], events = worker.drain_scan_events(scan_state["seq"])
            for ev in events:
                if ev.done:
                    ctx.last_scan_ids = ev.found_ids
                    ids = ", ".join(str(i) for i in ev.found_ids) or t("scan.none")
                    scan_progress.set_text(t("scan.done", n=scan_state["count"],
                                             total=scan_state["total"]))
                    scan_found.set_text(t("scan.found", ids=ids))
                    scan_error.set_text(ev.error)
                    if ev.error:
                        ui.notify(ev.error, type="negative", timeout=8000)
                    elif ev.found_ids:
                        id_input.set_value(ev.found_ids[0])
                        cfg.device_id = ev.found_ids[0]
                        config_store.save(cfg)
                        ui.notify(t("msg.scan_found", id=ev.found_ids[0]), type="positive")
                    else:
                        ui.notify(t("msg.scan_none"), type="warning")
                else:
                    scan_state["count"] += 1
                    if ev.found:
                        scan_state["found"].append(ev.probed)
                    scan_progress.set_text(t("scan.probing", n=scan_state["count"],
                                             total=scan_state["total"], id=ev.probed))
                    scan_found.set_text(t("scan.found", ids=", ".join(
                        str(i) for i in scan_state["found"]) or "—"))

        ui.timer(0.2, drain_scan)

        def start_scan(full: bool) -> None:
            s = current_settings()
            if s is None:
                return
            ids = ([FACTORY_DEFAULT_ID, SETID_TEMP_ID] + [i for i in range(1, 246)]) if full \
                else [FACTORY_DEFAULT_ID, SETID_TEMP_ID, *GRID_IDS]
            scan_state.update(seq=scan_state["seq"], count=0, total=len(ids), found=[])
            if not worker.start_scan(s, ids):
                ui.notify(t("msg.worker_busy"), type="negative")
                return
            scan_progress.set_text(t("scan.probing", n=0, total=len(ids), id="—"))
            scan_found.set_text(t("scan.found", ids="—"))
            scan_error.set_text("")
            scan_dialog.open()

        with ui.dropdown_button(t("hdr.scan"), auto_close=True).props("dense"):
            ui.item(t("hdr.scan.quick"), on_click=lambda: start_scan(False))
            ui.item(t("hdr.scan.full"), on_click=lambda: start_scan(True))

        # ── connect / status ───────────────────────────────────────────────
        connect_btn = ui.button(t("hdr.connect")).props("unelevated dense")
        status = ui.badge(t("hdr.status.idle")).props("color=grey")

        async def toggle_connect() -> None:
            st = worker.get_state()
            if st.connected:
                await worker.disconnect()
                return
            s = current_settings()
            if s is None:
                return
            st = await worker.connect(s)
            if st.connected:
                cfg.transport = transport.value
                cfg.com_port = str(com_select.value or "")
                cfg.baud = int(baud_select.value)
                cfg.tcp_host = str(host_input.value)
                cfg.tcp_port = int(port_input.value)
                cfg.device_id = ctx.device_id()
                config_store.save(cfg)
                ui.notify(t("msg.connected", desc=st.transport_desc), type="positive")
            else:
                ui.notify(st.last_error or t("msg.connect_failed"), type="negative")

        connect_btn.on_click(toggle_connect)

        def theme_chosen(key: str) -> None:
            cfg.theme = key
            config_store.save(cfg)

        # ── language / theme / about (far right) ───────────────────────────
        def choose_language(lang: str) -> None:
            cfg.language = lang
            config_store.save(cfg)
            ui.navigate.reload()      # the page is rebuilt in the new language

        # Built outside the menu below: a dialog defined inside it would be
        # torn down the moment the item that opens it is clicked.
        about_dialog = about.build_dialog()
        reference_dialog = reference_mod.build_dialog()

        # Language, theme and about are all settings you touch once and forget,
        # so they collapse into a single overflow button instead of spending
        # three slots in the header. ml-auto keeps it at the right edge of
        # whichever line it lands on (ui.space() would strand it on the left
        # after a wrap).
        def submenu(label: str):
            """A menu row that opens its own list, so a group can grow without
            making the top level longer.

            It opens leftward: the button sits at the right edge of the window,
            and a submenu flying out to the right would land off-screen.
            """
            item = ui.menu_item(auto_close=False)
            with item:
                with ui.row().classes("items-center justify-between w-full no-wrap"):
                    ui.label(label)
                    ui.label("›").classes("text-grey")
            return item

        with ui.row().classes("items-center flex-nowrap ml-auto"):
            with ui.button("...").props("flat dense no-caps") \
                    .classes("px-3 tracking-widest") \
                    .tooltip(t("hdr.more_tooltip")):
                with ui.menu().classes("min-w-[180px]") as more_menu:
                    with submenu(t("hdr.language")):
                        with ui.menu().props('anchor="top start" self="top end"') \
                                .classes("min-w-[160px]"):
                            for code, name in i18n.LANGUAGES.items():
                                ui.menu_item(
                                    name,
                                    on_click=lambda c=code: choose_language(c)) \
                                    .classes("text-primary font-bold"
                                             if code == i18n.current() else "")

                    with submenu(t("hdr.theme")):
                        with ui.menu().props('anchor="top start" self="top end"') \
                                .classes("min-w-[200px]") as theme_menu:

                            def pick_theme(key: str) -> None:
                                # Both levels are closed by hand: picking a theme
                                # rebuilds these items to move the current-theme
                                # marker, and leaving the popups open would make
                                # the next click on "..." read as dismiss.
                                theme_chosen(key)
                                theme_menu.close()
                                more_menu.close()

                            theme_mod.build_menu_items(pick_theme)

                    ui.separator()
                    ui.menu_item(t("hdr.reference"), on_click=reference_dialog.open)
                    ui.menu_item(t("hdr.about"), on_click=about_dialog.open)

        def refresh_status() -> None:
            st = worker.get_state()
            if st.sweep_running:
                status.set_text(t("hdr.status.module_test"))
                status.props("color=amber")
            elif st.check_running:
                status.set_text(t("hdr.status.install_check"))
                status.props("color=amber")
            elif st.ota_running:
                status.set_text(t("hdr.status.ota"))
                status.props("color=amber")
            elif st.scan_running:
                status.set_text(t("hdr.status.scanning"))
                status.props("color=amber")
            elif st.connected:
                status.set_text(t("hdr.status.connected", desc=st.transport_desc,
                                  id=ctx.device_id()))
                status.props("color=green")
            elif st.last_error:
                status.set_text(st.last_error[:60])
                status.props("color=red")
            else:
                status.set_text(t("hdr.status.idle"))
                status.props("color=grey")
            connect_btn.set_text(t("hdr.disconnect") if st.connected else t("hdr.connect"))

        ui.timer(0.5, refresh_status)
