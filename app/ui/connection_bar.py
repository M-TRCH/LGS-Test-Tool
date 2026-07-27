"""Persistent header: transport selection, slave ID, scan, connect, status chip."""
from __future__ import annotations

from nicegui import ui

from .. import config_store
from ..lgs_map import BAUD_WHITELIST, FACTORY_DEFAULT_ID, FORBIDDEN_ID, GRID_IDS
from ..transports import RtuSettings, TcpSettings, list_com_ports
from ..version import APP_VERSION
from . import Ctx


def _port_options() -> dict:
    ports = list_com_ports()
    return {p.device: p.label for p in ports}


def build(ctx: Ctx) -> None:
    cfg = ctx.cfg
    worker = ctx.worker

    # light background so the default dark text of Quasar fields stays readable
    with ui.header().classes("items-center gap-3 flex-wrap bg-grey-2 text-black q-py-xs") \
            .props("bordered"):
        ui.label("LGS Test Tool").classes("text-lg font-bold text-primary")
        ui.badge(f"v{APP_VERSION}").props("color=primary outline").classes("text-xs")

        transport = ui.radio({"rtu": "RTU (COM)", "tcp": "TCP"}, value=cfg.transport) \
            .props("inline dense")

        with ui.row().classes("items-center gap-2") as rtu_row:
            opts = _port_options()
            initial = cfg.com_port if cfg.com_port in opts else (next(iter(opts), None))
            for dev, label in opts.items():                     # prefer the Opta bridge
                if "Opta" in label:
                    initial = cfg.com_port if cfg.com_port in opts else dev
                    break
            com_select = ui.select(opts or {"": "(no ports)"}, value=initial,
                                   label="COM port").classes("min-w-[260px]").props("dense outlined")

            def refresh_ports() -> None:
                new = _port_options()
                com_select.set_options(new or {"": "(no ports)"})
                for dev, label in new.items():
                    if "Opta" in label:
                        com_select.set_value(dev)
                        break
                ui.notify(f"{len(new)} port(s) found", type="info")

            ui.button(icon="refresh", on_click=refresh_ports).props("flat dense round")
            baud_select = ui.select(list(BAUD_WHITELIST), value=cfg.baud, label="baud") \
                .props("dense outlined").classes("w-24")
            ui.label("8N1").classes("text-xs text-grey")

        with ui.row().classes("items-center gap-2") as tcp_row:
            host_input = ui.input("Host", value=cfg.tcp_host).props("dense outlined").classes("w-40")
            port_input = ui.number("Port", value=cfg.tcp_port, min=1, max=65535, format="%d") \
                .props("dense outlined").classes("w-24")
            ui.label("gateway: single client").classes("text-xs text-grey")

        def sync_rows() -> None:
            rtu_row.set_visibility(transport.value == "rtu")
            tcp_row.set_visibility(transport.value == "tcp")

        transport.on_value_change(sync_rows)
        sync_rows()

        id_input = ui.number("Slave ID", value=cfg.device_id, min=1, max=247, format="%d") \
            .props("dense outlined").classes("w-28")

        def id_changed() -> None:
            if int(id_input.value or 0) == FORBIDDEN_ID:
                ui.notify("ID 246 is reserved (SET_ID mode) — not usable", type="warning")

        id_input.on_value_change(id_changed)
        ctx.device_id_getter = lambda: int(id_input.value or FACTORY_DEFAULT_ID)
        ctx.device_id_setter = lambda v: id_input.set_value(int(v))

        # ── scan ───────────────────────────────────────────────────────────
        def current_settings():
            if transport.value == "rtu":
                if not com_select.value:
                    ui.notify("no COM port selected", type="negative")
                    return None
                return RtuSettings(str(com_select.value), int(baud_select.value))
            return TcpSettings(str(host_input.value), int(port_input.value))

        scan_dialog = ui.dialog()
        with scan_dialog, ui.card().classes("min-w-[360px]"):
            ui.label("Scanning for slave IDs").classes("font-bold")
            scan_progress = ui.label("...")
            scan_found = ui.label("found: —")
            with ui.row():
                ui.button("Cancel", on_click=lambda: worker.cancel_scan()).props("flat")
                ui.button("Close", on_click=scan_dialog.close).props("flat")

        scan_state = {"seq": 0, "count": 0, "total": 0, "found": []}

        def drain_scan() -> None:
            scan_state["seq"], events = worker.drain_scan_events(scan_state["seq"])
            for ev in events:
                if ev.done:
                    ids = ", ".join(str(i) for i in ev.found_ids) or "none"
                    scan_progress.set_text(f"done — probed {scan_state['count']}/{scan_state['total']}")
                    scan_found.set_text(f"found: {ids}")
                    if ev.found_ids:
                        id_input.set_value(ev.found_ids[0])
                        cfg.device_id = ev.found_ids[0]
                        config_store.save(cfg)
                        ui.notify(f"scan complete — using ID {ev.found_ids[0]}", type="positive")
                    else:
                        ui.notify("scan complete — no device answered", type="warning")
                else:
                    scan_state["count"] += 1
                    if ev.found:
                        scan_state["found"].append(ev.probed)
                    scan_progress.set_text(f"probing {scan_state['count']}/{scan_state['total']}"
                                           f" (id {ev.probed})")
                    scan_found.set_text("found: " +
                                        (", ".join(str(i) for i in scan_state["found"]) or "—"))

        ui.timer(0.2, drain_scan)

        def start_scan(full: bool) -> None:
            s = current_settings()
            if s is None:
                return
            ids = ([FACTORY_DEFAULT_ID] + [i for i in range(1, 246)]) if full \
                else [FACTORY_DEFAULT_ID, *GRID_IDS]
            scan_state.update(seq=scan_state["seq"], count=0, total=len(ids), found=[])
            if not worker.start_scan(s, ids):
                ui.notify("worker busy — cannot scan now", type="negative")
                return
            scan_progress.set_text(f"probing 0/{len(ids)}")
            scan_found.set_text("found: —")
            scan_dialog.open()

        with ui.dropdown_button("Scan", auto_close=True).props("dense"):
            ui.item("Quick (grid 11-64 + 247)", on_click=lambda: start_scan(False))
            ui.item("Full (1-245 + 247)", on_click=lambda: start_scan(True))

        # ── connect / status ───────────────────────────────────────────────
        connect_btn = ui.button("Connect").props("unelevated dense")
        status = ui.badge("idle").props("color=grey")

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
                ui.notify(f"connected: {st.transport_desc}", type="positive")
            else:
                ui.notify(st.last_error or "connect failed", type="negative")

        connect_btn.on_click(toggle_connect)

        def refresh_status() -> None:
            st = worker.get_state()
            if st.sweep_running:
                status.set_text("SWEEP RUNNING")
                status.props("color=amber")
            elif st.scan_running:
                status.set_text("scanning...")
                status.props("color=amber")
            elif st.connected:
                status.set_text(f"{st.transport_desc} — id {ctx.device_id()}")
                status.props("color=green")
            elif st.last_error:
                status.set_text(st.last_error[:60])
                status.props("color=red")
            else:
                status.set_text("idle")
                status.props("color=grey")
            connect_btn.set_text("Disconnect" if st.connected else "Connect")

        ui.timer(0.5, refresh_status)
