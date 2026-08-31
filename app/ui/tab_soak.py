"""Soak tab — leave the cabinet polling for hours and watch for wobble.

Built for the machine that plays the hospital's server: point the tool at
the gateway over TCP, start the soak, walk away. It answers the question a
plain poll cannot — "did any module reboot while nobody was looking" —
because a module that resets comes back within a second and every read
still succeeds. Boot counters are what give it away.
"""
from __future__ import annotations

from datetime import datetime

from nicegui import ui

from .. import applog, config_store, keep_awake, soak
from ..i18n import t
from . import Ctx, helps


def _dur(seconds: float) -> str:
    s = int(seconds)
    if s >= 3600:
        return f"{s // 3600}h {s % 3600 // 60:02d}m"
    if s >= 60:
        return f"{s // 60}m {s % 60:02d}s"
    return f"{s}s"


def build(ctx: Ctx) -> None:
    worker = ctx.worker
    state: dict = {"seq": 0, "running": False, "path": None}

    with ui.card().classes("p-3 w-full"):
        helps(ui.label(t("soak.card")).classes("font-bold text-lg"), t("soak.hint"))

        with ui.row().classes("items-center gap-3 flex-wrap"):
            gap = ui.number(t("soak.gap"), value=2.0, min=0, max=60, step=0.5,
                            format="%.1f").props("dense outlined").classes("w-32")
            helps(gap, t("soak.gap_tip"))
            every = ui.number(t("soak.counter_every"), value=5, min=1, max=100,
                              format="%d").props("dense outlined").classes("w-40")
            helps(every, t("soak.counter_every_tip"))
            slow = ui.number(t("soak.slow"), value=400, min=50, max=5000,
                             format="%d").props("dense outlined").classes("w-36")
            helps(slow, t("soak.slow_tip"))

        with ui.row().classes("items-center gap-3 flex-wrap q-mt-sm"):
            start_btn = ui.button(t("soak.start"), color="primary")
            stop_btn = ui.button(t("soak.stop"), color="red").props("outline")
            status = ui.label(t("soak.idle")).classes("text-sm")

        # Both halves of "you can walk away now": the machine will not sleep
        # under the run, and if the app dies anyway there is a file that says
        # what happened. The first overnight run had neither.
        marks = [t("soak.awake_on") if keep_awake.supported()
                 else t("soak.awake_off")]
        if applog.path() is not None:
            marks.append(t("soak.applog", v=applog.path().name))
        ui.label(" · ".join(marks)).classes("text-xs text-grey")

    # ── live totals ────────────────────────────────────────────────────────
    with ui.card().classes("p-3 w-full q-mt-sm"):
        ui.label(t("soak.totals")).classes("font-bold")
        with ui.row().classes("gap-6 flex-wrap"):
            lbl_elapsed = ui.label("—").classes("text-sm")
            lbl_passes = ui.label("—").classes("text-sm")
            lbl_txns = ui.label("—").classes("text-sm")
            lbl_fails = ui.label("—").classes("text-sm")
            lbl_reboots = ui.label("—").classes("text-sm font-bold")
            lbl_wdt = ui.label("—").classes("text-sm font-bold")
            lbl_worst = ui.label("—").classes("text-sm")
            lbl_cross = ui.label("—").classes("text-sm text-grey")

    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("soak.anomalies")).classes("font-bold"), t("soak.anomalies_tip"))
        box = ui.log(max_lines=400).classes("w-full h-64 font-mono text-xs")

    def say(text: str) -> None:
        box.push(text)

    def reset_totals() -> None:
        """Blank the panel between runs.

        The first tick of a new run only lands when its first pass finishes —
        twenty seconds during which last run's numbers would sit there
        looking like this one's. A soak is read at a glance; stale totals are
        worse than none.
        """
        for lbl in (lbl_elapsed, lbl_passes, lbl_txns, lbl_fails,
                    lbl_reboots, lbl_wdt, lbl_worst, lbl_cross):
            lbl.set_text("—")
        lbl_reboots.classes(replace="text-sm font-bold")
        lbl_wdt.classes(replace="text-sm font-bold")
        lbl_cross.classes(replace="text-sm text-grey")

    def do_start() -> None:
        layout = ctx.cabinet()
        path = (config_store.data_dir() / "exports"
                / f"soak-{datetime.now():%Y%m%d-%H%M}.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        cfg = soak.SoakConfig(ids=tuple(layout.ids),
                              pass_gap_s=float(gap.value or 2.0),
                              counter_every=int(every.value or 5),
                              slow_ms=int(slow.value or 400))
        if not worker.start_soak(cfg, path):
            # Say it in the status line as well as the toast: a refused start
            # leaves the previous run's totals on screen, and a toast that has
            # faded is no help to someone reading them a minute later.
            ui.notify(t("soak.busy"), type="warning")
            status.set_text(t("soak.busy"))
            status.classes(replace="text-sm text-orange")
            return
        state.update(running=True, path=path)
        box.clear()
        reset_totals()
        say(f"{datetime.now():%H:%M:%S}  start · {layout.label} · "
            f"{layout.count} modules · log {path.name}")
        status.set_text(t("soak.running", n=layout.count))
        status.classes(replace="text-sm text-green")

    def do_stop() -> None:
        worker.cancel_soak()
        status.set_text(t("soak.stopping"))

    start_btn.on_click(do_start)
    stop_btn.on_click(do_stop)

    def drain() -> None:
        running = worker.soak_running()
        start_btn.set_enabled(not running)
        stop_btn.set_enabled(running)
        state["seq"], events = worker.drain_soak_events(state["seq"])
        for ev in events:
            if isinstance(ev, soak.SoakTick):
                lbl_elapsed.set_text(t("soak.elapsed", v=_dur(ev.elapsed_s)))
                lbl_passes.set_text(t("soak.passes", v=ev.passes))
                lbl_txns.set_text(t("soak.txns", v=f"{ev.txns:,}"))
                lbl_fails.set_text(t("soak.fails", v=ev.fails))
                lbl_reboots.set_text(t("soak.reboots", v=ev.reboots))
                lbl_reboots.classes(replace="text-sm font-bold "
                                    + ("text-red" if ev.reboots else "text-green"))
                lbl_wdt.set_text(t("soak.watchdogs", v=ev.watchdogs))
                lbl_wdt.classes(replace="text-sm font-bold "
                                + ("text-red" if ev.watchdogs else "text-green"))
                lbl_worst.set_text(t("soak.worst", v=f"{ev.worst_ms:.0f}"))
                lbl_cross.set_text(t("soak.crossings", n=ev.crossings,
                                     v=f"{ev.worst_crossing_ms:.0f}"))
            elif isinstance(ev, soak.SoakAnomaly):
                say(ev.item.text)
            elif isinstance(ev, soak.SoakDone):
                state["running"] = False
                say(f"{datetime.now():%H:%M:%S}  stopped · {ev.summary}")
                status.set_text(ev.summary)
                status.classes(replace="text-sm text-grey")

    ui.timer(0.5, drain)
    drain()
