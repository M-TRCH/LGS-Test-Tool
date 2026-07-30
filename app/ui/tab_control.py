"""Control tab: preset buttons, display, quick ops, generic register/coil rows."""
from __future__ import annotations

from nicegui import ui

from ..lgs_map import (coil_display, coil_enable, coil_latch, coil_latch_display,
                       decode_register)
from . import Ctx

# default preset palette (config regs 111-113 per preset) — dots on the cards
PRESET_COLORS = {1: "#ff3232", 2: "#32ff32", 3: "#3264ff", 4: "#ffd700",
                 5: "#00e5e5", 6: "#ff32ff", 7: "#ff5a1e", 8: "#fff096"}


def build(ctx: Ctx) -> None:
    worker = ctx.worker

    async def wcoil(addr: int, value: bool, label: str) -> None:
        res = await worker.write_coil(addr, value, ctx.device_id())
        if res.ok:
            ui.notify(f"{label} OK", type="positive", timeout=1200)
        else:
            ui.notify(f"{label}: {res.note}", type="negative")

    latch_buttons: list = []

    # ── presets ────────────────────────────────────────────────────────────
    ui.label("Presets (single shared ring — enabling one auto-clears the others)") \
        .classes("text-sm text-grey")
    active_badges: dict[int, ui.badge] = {}
    with ui.row().classes("gap-2 flex-wrap"):
        for n in range(1, 9):
            with ui.card().classes("p-2 w-44"):
                with ui.row().classes("items-center gap-2"):
                    ui.html(f'<div style="width:14px;height:14px;border-radius:50%;'
                            f'background:{PRESET_COLORS[n]}"></div>')
                    ui.label(f"Preset {n}").classes("font-bold")
                    active_badges[n] = ui.badge("ACTIVE").props("color=green")
                    active_badges[n].set_visibility(False)
                with ui.column().classes("gap-1 w-full"):
                    ui.button(f"Light ({coil_enable(n)})",
                              on_click=lambda n=n: wcoil(coil_enable(n), True, f"P{n} light")) \
                        .props("dense size=sm").classes("w-full")
                    ui.button(f"Light+Disp ({coil_display(n)})",
                              on_click=lambda n=n: wcoil(coil_display(n), True, f"P{n} light+disp")) \
                        .props("dense size=sm").classes("w-full")
                    b1 = ui.button(f"Unlock ({coil_latch(n)})",
                                   on_click=lambda n=n: wcoil(coil_latch(n), True, f"P{n} unlock"),
                                   color="orange").props("dense size=sm").classes("w-full")
                    b2 = ui.button(f"Unlock+Disp ({coil_latch_display(n)})",
                                   on_click=lambda n=n: wcoil(coil_latch_display(n), True,
                                                              f"P{n} unlock+disp"),
                                   color="orange").props("dense size=sm").classes("w-full")
                    latch_buttons += [b1, b2]

    def refresh_active() -> None:
        snap = ctx.latest_snapshot
        ap = snap.regs.get(11) if snap and snap.regs else None
        for n, badge in active_badges.items():
            badge.set_visibility(ap == n)

    ui.timer(1.0, refresh_active)

    ui.separator()

    # ── display + quick ops ────────────────────────────────────────────────
    with ui.row().classes("items-center gap-4 flex-wrap"):
        with ui.card().classes("p-3"):
            ui.label("Display (OLED)").classes("font-bold")
            with ui.row().classes("items-center gap-2"):
                num = ui.number("number", value=45, min=0, max=9999, format="%d") \
                    .props("dense outlined").classes("w-28")
                ui.label("(0-99; >99 clamps to 99)").classes("text-xs text-grey")

                async def write_num() -> None:
                    res = await worker.write_register(60, int(num.value or 0), ctx.device_id())
                    if res.ok:
                        ui.notify(f"reg 60 = {res.value}", type="positive", timeout=1200)
                    else:
                        ui.notify(res.note, type="negative")

                ui.button("Write reg 60", on_click=write_num).props("dense")
                ui.switch("Display power (1010)",
                          on_change=lambda e: wcoil(1010, bool(e.value), "display power"))

        with ui.card().classes("p-3"):
            ui.label("Quick ops").classes("font-bold")
            with ui.row().classes("gap-2"):
                ui.button("Identify (509)", on_click=lambda: wcoil(509, True, "identify")) \
                    .props("dense")
                ui.button("All Off (511)", on_click=lambda: wcoil(511, True, "all off")) \
                    .props("dense")
                lb1 = ui.button("Latch Safety (1020)", color="orange",
                                on_click=lambda: wcoil(1020, True, "latch safety")).props("dense")
                lb2 = ui.button("Latch Force (1019)", color="deep-orange",
                                on_click=lambda: wcoil(1019, True, "latch force")).props("dense")
                latch_buttons += [lb1, lb2]
                cooldown = ui.badge("latch ready").props("color=green")

    def refresh_cooldown() -> None:
        rem = worker.cooldown_remaining(ctx.device_id())
        if rem > 0:
            cooldown.set_text(f"cooldown {rem:.1f}s")
            cooldown.props("color=orange")
            for b in latch_buttons:
                b.disable()
        else:
            cooldown.set_text("latch ready")
            cooldown.props("color=green")
            for b in latch_buttons:
                b.enable()

    ui.timer(0.1, refresh_cooldown)

    ui.separator()

    # ── generic register / coil access ─────────────────────────────────────
    with ui.row().classes("gap-4 flex-wrap"):
        with ui.card().classes("p-3"):
            ui.label("Generic register").classes("font-bold")
            with ui.row().classes("items-center gap-2"):
                r_addr = ui.number("addr", value=0, min=0, max=65535, format="%d") \
                    .props("dense outlined").classes("w-24")
                r_count = ui.number("count", value=1, min=1, max=64, format="%d") \
                    .props("dense outlined").classes("w-20")

                async def read_reg() -> None:
                    res = await worker.read_registers(int(r_addr.value), int(r_count.value),
                                                      ctx.device_id())
                    if res.ok:
                        if isinstance(res.value, list):
                            r_result.set_text(f"= {res.value} ({res.latency_ms:.0f} ms)")
                        else:
                            r_result.set_text(f"= {res.value} → "
                                              f"{decode_register(int(r_addr.value), res.value)}"
                                              f" ({res.latency_ms:.0f} ms)")
                    else:
                        r_result.set_text(f"ERR: {res.note}")

                ui.button("FC03 Read", on_click=read_reg).props("dense")
                w_val = ui.number("value", value=0, min=0, max=65535, format="%d") \
                    .props("dense outlined").classes("w-24")

                async def write_reg() -> None:
                    res = await worker.write_register(int(r_addr.value), int(w_val.value),
                                                      ctx.device_id())
                    r_result.set_text(f"write OK ({res.latency_ms:.0f} ms)" if res.ok
                                      else f"ERR: {res.note}")

                ui.button("FC06 Write", on_click=write_reg).props("dense")
            r_result = ui.label("—").classes("text-sm font-mono")

        with ui.card().classes("p-3"):
            ui.label("Generic coil").classes("font-bold")
            with ui.row().classes("items-center gap-2"):
                c_addr = ui.number("addr", value=1001, min=0, max=65535, format="%d") \
                    .props("dense outlined").classes("w-24")

                async def read_coil() -> None:
                    res = await worker.read_coils(int(c_addr.value), 1, ctx.device_id())
                    c_result.set_text(f"= {res.value} ({res.latency_ms:.0f} ms)" if res.ok
                                      else f"ERR: {res.note}")

                ui.button("FC01 Read", on_click=read_coil).props("dense")
                c_val = ui.radio({1: "ON", 0: "OFF"}, value=1).props("inline dense")

                async def write_coil() -> None:
                    res = await worker.write_coil(int(c_addr.value), bool(c_val.value),
                                                  ctx.device_id())
                    c_result.set_text(f"write OK ({res.latency_ms:.0f} ms)" if res.ok
                                      else f"ERR: {res.note}")
                    if not res.ok and res.note:
                        ui.notify(res.note, type="warning")

                ui.button("FC05 Write", on_click=write_coil).props("dense")
            c_result = ui.label("—").classes("text-sm font-mono")
