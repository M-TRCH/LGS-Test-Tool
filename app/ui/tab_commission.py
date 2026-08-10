"""Commissioning tab: flash a new module and give it its Modbus ID at once.

Everything here runs over ST-Link, not the bus — the module usually is not
wired to RS485 yet. That is also why nothing on this page needs a connection.
"""
from __future__ import annotations

from pathlib import Path

from nicegui import ui

from .. import commission_image as ci
from .. import firmware_bundle as fb
from ..commission import BatchConfig, BoardDone, BoardNext, CommissionConfig
from ..config_store import data_dir
from ..i18n import t
from ..lgs_map import GRID_COLS, GRID_ROWS, valid_assignable_id
from ..ota import Done, Line, Progress
from . import Ctx, bundled_picker, helps, warning_banner

LEVEL_CLASS = {"info": "", "ok": "text-green", "warn": "text-orange", "err": "text-red"}

# Same palette as the Installation Check grid, so the two pages read alike.
COLOR_UNSELECTED = "grey-5"
COLOR_SELECTED = "primary"
COLOR_WAITING = "amber"
COLOR_PASS = "positive"
COLOR_FAIL = "negative"


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state: dict = {"seq": 0, "image": b"", "name": "", "batch": False}

    warning_banner(t("cm.banner"))

    mode = ui.toggle({"single": t("cm.mode.single"), "batch": t("cm.mode.batch")},
                     value="single").props("no-caps dense")

    with ui.row().classes("gap-3 flex-wrap items-stretch w-full"):
        # ── the image ──────────────────────────────────────────────────────
        with ui.card().classes("p-3 grow"):
            helps(ui.label(t("cm.image")).classes("font-bold"), t("cm.image_hint"))

            # A bundled image goes through the very same check as an uploaded
            # one: shipping it with the tool says where it came from, not that
            # it is exempt from carrying a commissioning block.
            def arm(data: bytes, name: str) -> None:
                state["image"], state["name"] = data, name
                try:
                    # Block first: it answers "is this an LGS module image at
                    # all?". Only then is "factory or OTA?" the useful
                    # question — asking it of a foreign binary would explain
                    # the wrong problem.
                    block = ci.find_block(data)
                    ci.check_factory_image(data)
                except ci.ImageError as exc:
                    state["image"] = b""
                    image_label.set_text(str(exc))
                    image_label.classes(add="text-red", remove="text-green")
                    return
                image_label.set_text(t("cm.image_ok", name=name,
                                       size=f"{len(data):,}",
                                       detail=ci.describe(block)))
                image_label.classes(add="text-green", remove="text-red")

            def on_upload(e) -> None:
                arm(e.content.read(), e.name)

            bundled_picker(fb.KIND_MODULE_FACTORY,
                           lambda data, name, img: arm(data, name))
            ui.label(t("fw.or_upload")).classes("text-xs text-grey")
            ui.upload(on_upload=on_upload, auto_upload=True, max_files=1) \
                .props('accept=".bin" flat dense').classes("w-full")
            image_label = ui.label(t("cm.no_image")).classes("text-sm")
            lot_input = helps(
                ui.input(t("cm.lot")).props("dense outlined").classes("w-40 q-mt-sm"),
                t("cm.lot_hint"))

        # ── single mode: the one identity to give it ───────────────────────
        with ui.card().classes("p-3 grow") as single_card:
            helps(ui.label(t("cm.identity")).classes("font-bold"), t("cm.identity_hint"))
            id_input = ui.number(t("cm.slave_id"), value=ctx.device_id(),
                                 min=1, max=245, format="%d") \
                .props("dense outlined").classes("w-40")

            with ui.button(t("cm.grid")).props("dense flat no-caps") \
                    .classes("q-mt-sm"):
                with ui.menu() as grid_menu:
                    with ui.column().classes("gap-1 p-3"):
                        for r in range(1, GRID_ROWS + 1):
                            with ui.row().classes("gap-1 flex-nowrap"):
                                for c in range(1, GRID_COLS + 1):
                                    gid = r * 10 + c

                                    def pick(g=gid) -> None:
                                        id_input.set_value(g)
                                        grid_menu.close()

                                    ui.button(str(gid), on_click=pick) \
                                        .props("unelevated dense no-caps") \
                                        .classes("w-12 min-w-0 font-mono")

        # ── single mode: overwriting a module that already has an ID ───────
        with ui.card().classes("p-3 grow border border-orange-400") as ow_card:
            ui.label(t("cm.overwrite_card")).classes("font-bold text-orange")
            cb_overwrite = ui.checkbox(t("cm.overwrite"), value=False)
            ui.label(t("cm.overwrite_note")).classes("text-xs text-grey")

    # ── batch mode: the queue of IDs, picked exactly like Installation Check ─
    selected: set = set()
    results: dict = {}
    cells: dict = {}
    waiting: dict = {"id": None}

    with ui.card().classes("p-3 w-full") as batch_card:
        with ui.row().classes("items-center gap-2 flex-wrap"):
            helps(ui.label(t("cm.batch.pick")).classes("font-bold"),
                  t("cm.batch.pick_hint"))
            ui.button(t("btn.clear"),
                      on_click=lambda: set_selection(())).props("flat dense no-caps")
            count_label = ui.label("").classes("text-sm text-grey")
        ui.label(t("cm.batch.no_overwrite")).classes("text-xs text-grey")

        with ui.column().classes("gap-1 q-mt-sm"):
            for r in range(1, GRID_ROWS + 1):
                with ui.row().classes("gap-1 flex-nowrap items-center"):
                    row_ids = [r * 10 + c for c in range(1, GRID_COLS + 1)]

                    def toggle_row(ids=row_ids) -> None:
                        if all(i in selected for i in ids):
                            for i in ids:
                                selected.discard(i)
                        else:
                            selected.update(ids)
                        for i in ids:
                            results.pop(i, None)
                            paint(i)
                        update_count()

                    ui.button(f"R{r}", on_click=toggle_row) \
                        .props("flat dense no-caps size=sm") \
                        .classes("w-10 min-w-0 text-grey")
                    for gid in row_ids:
                        cells[gid] = ui.button(
                            str(gid), on_click=lambda gid=gid: toggle(gid)) \
                            .props(f"unelevated no-caps color={COLOR_UNSELECTED}") \
                            .classes("w-14 min-w-0 font-mono")

    def paint(gid: int) -> None:
        if gid == waiting["id"]:
            color = COLOR_WAITING
        elif gid in results:
            color = COLOR_PASS if results[gid] else COLOR_FAIL
        else:
            color = COLOR_SELECTED if gid in selected else COLOR_UNSELECTED
        cells[gid].props(f"color={color}")

    def toggle(gid: int) -> None:
        selected.discard(gid) if gid in selected else selected.add(gid)
        results.pop(gid, None)
        paint(gid)
        update_count()

    def set_selection(ids) -> None:
        selected.clear()
        selected.update(ids)
        results.clear()
        waiting["id"] = None
        for gid in cells:
            paint(gid)
        update_count()

    def update_count() -> None:
        count_label.set_text(t("cm.batch.selected", n=len(selected)))

    update_count()

    def apply_mode() -> None:
        batch = mode.value == "batch"
        single_card.set_visibility(not batch)
        ow_card.set_visibility(batch is False)
        batch_card.set_visibility(batch)

    mode.on_value_change(apply_mode)
    apply_mode()

    # ── run ────────────────────────────────────────────────────────────────
    with ui.row().classes("items-center gap-3 flex-wrap"):
        run_btn = ui.button(t("cm.run"), color="primary")
        ui.button(t("btn.cancel"), on_click=lambda: worker.cancel_commission()) \
            .props("outline")
        progress = ui.linear_progress(value=0.0, show_value=False).classes("w-64")
        progress_label = ui.label("").classes("font-mono text-sm")
        banner = ui.badge("—").props("color=grey")

    log_box = ui.column().classes("w-full gap-0 font-mono text-xs p-2 rounded "
                                  "border max-h-96 overflow-auto")

    def say(text: str, level: str = "info") -> None:
        with log_box:
            ui.label(text).classes(LEVEL_CLASS.get(level, ""))

    def begin_run() -> None:
        log_box.clear()
        progress.set_value(0.0)
        progress_label.set_text("")
        banner.set_text(t("res.running"))
        banner.props("color=blue")

    def busy() -> None:
        ui.notify(t("msg.worker_busy"), type="negative")
        banner.set_text("—")
        banner.props("color=grey")

    async def start_single() -> None:
        target = int(id_input.value or 0)
        if not valid_assignable_id(target) or target > 245:
            ui.notify(t("cm.bad_id", id=target), type="negative")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("cm.confirm_title")).classes("font-bold text-red")
            ui.label(t("cm.confirm_body", name=state["name"], id=target))
            if cb_overwrite.value:
                ui.label(t("cm.confirm_overwrite")).classes("text-red font-bold")
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("cm.run"), color="red", on_click=lambda: d.submit(True))
        if not await d:
            return

        state["batch"] = False
        begin_run()
        cfg = CommissionConfig(image=state["image"], filename=state["name"],
                               identifier=target, lot=str(lot_input.value or ""),
                               overwrite=bool(cb_overwrite.value),
                               log_dir=Path(data_dir()) / "exports")
        if not worker.start_commission(cfg):
            busy()

    async def start_batch() -> None:
        ids = tuple(sorted(selected))
        if not ids:
            ui.notify(t("cm.batch.need_ids"), type="warning")
            return

        d = ui.dialog()
        with d, ui.card().classes("border border-red-500"):
            ui.label(t("cm.confirm_title")).classes("font-bold text-red")
            ui.label(t("cm.batch.confirm_body", n=len(ids), first=ids[0],
                       last=ids[-1], name=state["name"]))
            with ui.row():
                ui.button(t("btn.cancel"), on_click=lambda: d.submit(False)).props("flat")
                ui.button(t("cm.run"), color="red", on_click=lambda: d.submit(True))
        if not await d:
            return

        state["batch"] = True
        results.clear()
        waiting["id"] = None
        for gid in cells:
            paint(gid)
        begin_run()
        cfg = BatchConfig(image=state["image"], filename=state["name"], ids=ids,
                          lot=str(lot_input.value or ""),
                          log_dir=Path(data_dir()) / "exports")
        if not worker.start_batch_commission(cfg):
            busy()

    async def start() -> None:
        if not state["image"]:
            ui.notify(t("cm.need_image"), type="warning")
            return
        if mode.value == "batch":
            await start_batch()
        else:
            await start_single()

    run_btn.on_click(start)

    def drain() -> None:
        state["seq"], events = worker.drain_commission_events(state["seq"])
        for ev in events:
            if isinstance(ev, Line):
                say(ev.text, ev.level)
            elif isinstance(ev, BoardNext):
                waiting["id"] = ev.identifier
                if ev.identifier in cells:
                    paint(ev.identifier)
            elif isinstance(ev, BoardDone):
                waiting["id"] = None
                results[ev.identifier] = ev.ok
                if ev.identifier in cells:
                    paint(ev.identifier)
            elif isinstance(ev, Progress):
                progress.set_value(ev.done / max(1, ev.total))
                progress_label.set_text(
                    t("cm.batch.progress", done=ev.done, total=ev.total)
                    if state["batch"] else
                    t("cm.step", done=ev.done, total=ev.total))
            elif isinstance(ev, Done):
                progress.set_value(1.0)
                progress_label.set_text("")
                banner.set_text(t("res.pass") if ev.ok else t("res.fail"))
                banner.props("color=green" if ev.ok else "color=red")
                ui.notify(ev.summary, type="positive" if ev.ok else "negative",
                          timeout=8000)
                if waiting["id"] is not None:
                    gid, waiting["id"] = waiting["id"], None
                    if gid in cells:
                        paint(gid)
                if ev.ok and not state["batch"]:
                    # The next board almost always gets the next address.
                    nxt = int(id_input.value or 0) + 1
                    if valid_assignable_id(nxt) and nxt <= 245:
                        id_input.set_value(nxt)

    ui.timer(0.2, drain)
