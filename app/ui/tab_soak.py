"""Soak tab — leave the cabinet polling for hours and watch for wobble.

Built for the machine that plays the hospital's server: point the tool at
the gateway over TCP, start the soak, walk away. It answers the question a
plain poll cannot — "did any module reboot while nobody was looking" —
because a module that resets comes back within a second and every read
still succeeds. Boot counters are what give it away.
"""
from __future__ import annotations

import asyncio
import time
from datetime import datetime

from nicegui import ui

from .. import (applog, config_store, framer_watch, keep_awake, soak,
                soak_fleet)
from ..i18n import t
from ..lgs_map import CABINET_LAYOUTS, resolve_cabinet
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

        # Poll stays the default and the proven path. Pharmacy adds picks on
        # top of the same poll — the cabinet is being USED while it is
        # watched, which no soak here has ever done.
        with ui.row().classes("items-center gap-3 flex-wrap q-mt-sm"):
            mode = ui.toggle({"poll": t("soak.mode.poll"),
                              "pharmacy": t("soak.mode.pharmacy")},
                             value="poll").props("dense no-caps")
            helps(mode, t("soak.mode_tip"))
        with ui.row().classes("items-center gap-3 flex-wrap") as sim_row:
            picks = ui.number(t("soak.picks"), value=2000, min=1, max=100000,
                              format="%d").props("dense outlined").classes("w-40")
            helps(picks, t("soak.picks_tip"))
            dwell = ui.number(t("soak.dwell"), value=20, min=1, max=3600,
                              format="%d").props("dense outlined").classes("w-36")
            helps(dwell, t("soak.dwell_tip"))
            wins = ui.number(t("soak.windows"), value=8, min=1, max=8,
                             format="%d").props("dense outlined").classes("w-36")
            helps(wins, t("soak.windows_tip"))
        # Rate and dwell are not two settings — they multiply into the one
        # number that decides whether this run exercises the multi-window
        # engine at all. At the defaults it is 0.46, meaning the cabinet
        # essentially never shows two windows at once, and nobody would guess
        # that from "2000" and "20". So show the product, live, before the
        # night is spent rather than after.
        sim_calc = ui.label().classes("text-xs")
        ui.label(t("soak.sim_note")).classes("text-xs text-grey")
        sim_row.bind_visibility_from(mode, "value", lambda v: v == "pharmacy")
        sim_calc.bind_visibility_from(mode, "value", lambda v: v == "pharmacy")

        shown: dict = {"text": None}

        def recalc() -> None:
            if mode.value != "pharmacy":
                return          # the label is hidden; poll runs pay nothing
            conc, cap = soak.estimate_concurrent(
                ctx.cabinet().ids, int(wins.value or 8),
                int(picks.value or 2000), float(dwell.value or 20))
            if conc >= cap:
                text, tone = t("soak.sim_full", cap=cap), "text-red"
            elif conc >= cap * 0.5:
                text, tone = t("soak.sim_conc", n=f"{conc:.1f}",
                               cap=cap) + " · " + t("soak.sim_crowded"), "text-orange"
            elif conc < 1.0:
                text, tone = t("soak.sim_conc", n=f"{conc:.2f}",
                               cap=cap) + " · " + t("soak.sim_thin"), "text-grey"
            else:
                text, tone = t("soak.sim_conc", n=f"{conc:.1f}", cap=cap), "text-green"
            if text == shown["text"]:
                return
            shown["text"] = text
            sim_calc.set_text(text)
            sim_calc.classes(replace=f"text-xs {tone}")

        # Capacity depends on the cabinet, which is chosen on another card and
        # gives no change event here, so poll for it — with the guards above,
        # an unchanged figure costs a multiply and touches nothing, and poll
        # mode costs a comparison. Switching to pharmacy fills the label at
        # once rather than up to a second later.
        mode.on_value_change(lambda _e: recalc())
        ui.timer(1.0, recalc)
        recalc()

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
            # Pharmacy mode's only proof of life. Everything else on this
            # card is poll traffic and reads identically whether or not a
            # single window was ever lit, and the pick rows deliberately go
            # to the file rather than the anomaly box — so without this the
            # mode looks broken while working perfectly.
            lbl_picks = ui.label("—").classes("text-sm")
            lbl_picks.bind_visibility_from(mode, "value",
                                           lambda v: v == "pharmacy")

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
                    lbl_reboots, lbl_wdt, lbl_worst, lbl_cross, lbl_picks):
            lbl.set_text("—")
        lbl_reboots.classes(replace="text-sm font-bold")
        lbl_wdt.classes(replace="text-sm font-bold")
        lbl_cross.classes(replace="text-sm text-grey")
        lbl_picks.classes(replace="text-sm")

    def _cfg(ids: tuple) -> soak.SoakConfig:
        return soak.SoakConfig(ids=ids,
                               pass_gap_s=float(gap.value or 2.0),
                               counter_every=int(every.value or 5),
                               slow_ms=int(slow.value or 400),
                               mode=str(mode.value or "poll"),
                               picks_per_day=int(picks.value or 2000),
                               dwell_s=float(dwell.value or 20),
                               windows=int(wins.value or 8))

    def do_start() -> None:
        layout = ctx.cabinet()
        path = (config_store.data_dir() / "exports"
                / f"soak-{datetime.now():%Y%m%d-%H%M}.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        cfg = _cfg(tuple(layout.ids))
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
                lbl_picks.set_text(
                    t("soak.picks_live", n=f"{ev.picks:,}", lit=ev.lit)
                    + (" · " + t("soak.picks_dropped", n=ev.dropped)
                       if ev.dropped else ""))
                lbl_picks.classes(replace="text-sm"
                                  + (" text-red" if ev.dropped else ""))
            elif isinstance(ev, soak.SoakAnomaly):
                say(ev.item.text)
            elif isinstance(ev, soak.SoakDone):
                state["running"] = False
                say(f"{datetime.now():%H:%M:%S}  stopped · {ev.summary}")
                status.set_text(ev.summary)
                status.classes(replace="text-sm text-grey")

    # ── fleet: several cabinets at once ───────────────────────────────────
    # Each cabinet here is a separate gateway on a separate bus, so they do
    # not contend — the one-master rule is about a bus, not about the tool.
    # A fleet writes one CSV per cabinet so soak_csv.py and the site report
    # read them exactly as they read a single-cabinet run.
    fleet_rows: list = []
    fleet_state: dict = {"seq": 0, "tally": {}, "deadline": 0.0,
                         "started": "", "t0": 0.0, "early": False}

    with ui.card().classes("p-3 w-full q-mt-md"):
        helps(ui.label(t("fleet.card")).classes("font-bold text-lg"), t("fleet.hint"))
        rows_box = ui.column().classes("gap-1 w-full")

        def save_fleet() -> None:
            """Remember the roster. A weekend soak is set up ONCE, and five
            cabinets is fifteen fields typed by hand -- losing them to a
            restart or a page reload means retyping five IP addresses, and a
            mistyped one points the whole weekend at the wrong gateway."""
            ctx.cfg.fleet = soak_fleet.roster_to_config(
                ((e["name"].value or ""), (e["host"].value or ""),
                 e["cab"].value) for e in fleet_rows)
            try:
                config_store.save(ctx.cfg)
            except Exception:                                     # noqa: BLE001
                pass            # a roster that will not save must not stop a run

        def add_row(name: str = "", host: str = "", cab_key: str = "lgs80") -> None:
            with rows_box:
                with ui.row().classes("items-center gap-2 no-wrap w-full") as row:
                    n = ui.input(t("fleet.name"), value=name)                         .props("dense outlined").classes("w-44")
                    h = ui.input(t("fleet.host"), value=host)                         .props("dense outlined").classes("w-40")
                    c = ui.select({lay.key: lay.label for lay in CABINET_LAYOUTS},
                                  value=cab_key, label=t("fleet.cabinet"))                         .props("dense outlined").classes("w-48")
                    live = ui.label("—").classes("text-xs font-mono grow")
                    entry = {"name": n, "host": h, "cab": c, "live": live,
                             "row": row}
                    for fld in (n, h, c):
                        fld.on_value_change(lambda _e: save_fleet())

                    def drop() -> None:
                        rows_box.remove(row)
                        fleet_rows.remove(entry)
                        save_fleet()
                    # This was a grey "close" cross, and it was invisible in
                    # use: asked for a delete button while six of them were
                    # on screen. A cross is a dismiss, a bin is a delete, and
                    # the colour is what makes it findable at the end of a row
                    # of grey-on-white fields. The tooltip names the cabinet,
                    # because six identical bins in a column is the shape of
                    # deleting the wrong row.
                    kill = ui.button(icon="delete", on_click=drop)                         .props("flat dense round color=negative")
                    kill.tooltip(t("fleet.drop"))
                    fleet_rows.append(entry)

        with ui.row().classes("items-center gap-2 q-mt-sm"):
            # Read every gateway before committing to the run. Cheap, and
            # the answer it gives most often -- "free" -- is the one worth
            # having on a Friday evening.
            async def probe_all() -> None:
                for entry in fleet_rows:
                    target = (entry["host"].value or "").strip()
                    if not target:
                        continue
                    entry["live"].set_text("checking ...")
                    await asyncio.sleep(0)          # let the row repaint
                    entry["live"].set_text(
                        await asyncio.to_thread(soak_fleet.probe_gateway, target))

            ui.button(t("fleet.probe"), icon="travel_explore",
                      on_click=probe_all).props("flat dense")

            def export_roster() -> None:
                text = soak_fleet.roster_to_csv(
                    ((e["name"].value or ""), (e["host"].value or ""),
                     e["cab"].value) for e in fleet_rows)
                ui.download(text.encode("utf-8"), "lgs-fleet.csv")

            def import_roster(event) -> None:
                raw = event.content.read()
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    # Excel on a Thai Windows writes cp874, and a roster is
                    # exactly the file somebody will have opened in Excel.
                    text = raw.decode("cp874", "replace")
                rows, problems = soak_fleet.roster_from_csv(
                    text, {lay.key for lay in CABINET_LAYOUTS})
                for problem in problems:
                    ui.notify(problem, type="warning")
                if not rows:
                    return
                # Swapped only once the file has parsed. Half a new roster
                # and none of the old one is the worst outcome here: the old
                # one was typed by hand and is written down nowhere else.
                for entry in list(fleet_rows):
                    rows_box.remove(entry["row"])
                    fleet_rows.remove(entry)
                for name, host, key in rows:
                    add_row(name, host, key)
                save_fleet()
                ui.notify(t("fleet.imported", n=len(rows)), type="positive")

            ui.button(t("fleet.export"), icon="download",
                      on_click=export_roster).props("flat dense")
            # A plain upload rather than a button hiding one: the hidden
            # variant depends on how Quasar nests its file input and breaks
            # quietly when that changes. This control gets used twice a year,
            # and when it does it has to work.
            # Quasar's uploader prints "0.0B / 0.00%" under its title, which
            # beside three plain buttons reads as a fault rather than a
            # control. Only the SUBTITLE goes: hiding the whole header took
            # the words "Import list" with it and left a control nobody could
            # name. Scoped to this one widget, and the picker is untouched.
            ui.add_css(".fleet-import .q-uploader__subtitle { display: none }")
            ui.upload(label=t("fleet.import"), on_upload=import_roster,
                      auto_upload=True) \
                .props("flat dense accept=.csv,.txt")\
                .classes("fleet-import w-64")
            ui.button(t("fleet.add"), icon="add",
                      on_click=lambda: add_row()).props("flat dense no-caps")
            # WHICH MODE. The fleet inherits the toggle from the
            # single-cabinet card far above, and that card hides its pharmacy
            # fields in poll mode -- so an operator who ran a pharmacy soak
            # earlier, scrolled down here and pressed START would have begun
            # writing coils to N real cabinets with nothing on this card
            # saying so. It is red for pharmacy because that is the one that
            # touches the hardware.
            fleet_mode = ui.label().classes("text-sm")
            fleet_inherits = ui.label().classes("text-xs text-grey")
            fleet_gap_warn = ui.label().classes("text-xs text-orange font-bold")

            def fleet_mode_text() -> None:
                pharm = mode.value == "pharmacy"
                fleet_mode.set_text(t("fleet.will_run_pharmacy")
                                    if pharm else t("fleet.will_run_poll"))
                fleet_mode.classes(replace="text-sm "
                                   + ("text-red" if pharm else "text-grey"))
                # Every field on the Bus soak card drives this run too -- the
                # whole SoakConfig comes from up there and only the id list
                # differs. The mode has been called out since it can write
                # coils; the rest were silent, and the pass gap is the one
                # that cost this project months. Somebody sets 0.5 s for a
                # single-cabinet test, scrolls down, starts a weekend run on
                # ten cabinets, and gets back the phantom "chronically slow
                # modules" that took until 2026-08-31 to explain.
                inherited = t("fleet.inherits",
                              gap=f"{float(gap.value or 2.0):g}",
                              every=int(every.value or 5),
                              slow=int(slow.value or 400))
                if pharm:
                    inherited += t("fleet.inherits_pharmacy",
                                   picks=int(picks.value or 2000),
                                   dwell=f"{float(dwell.value or 20):g}",
                                   wins=int(wins.value or 8))
                fleet_inherits.set_text(inherited)
                bad_gap = 0.4 <= float(gap.value or 2.0) <= 0.9
                fleet_gap_warn.set_text(t("fleet.gap_band") if bad_gap else "")
                fleet_gap_warn.visible = bad_gap

            mode.on_value_change(lambda _e: fleet_mode_text())
            ui.timer(1.0, fleet_mode_text)
            fleet_mode_text()
            # A run without an end is a run somebody has to remember to
            # stop. The ones that matter here are weekends: set up on a
            # Friday, read on a Tuesday, by which time nobody is going to
            # recall which day the polling was supposed to have finished.
            # Zero means "until I press stop", which is what this card did
            # before and is still the right answer for a ten-minute check.
            fleet_hours = ui.number(t("fleet.hours"), value=0, min=0, max=336,
                                    step=0.5, format="%g")                 .props("dense outlined").classes("w-36")
            helps(fleet_hours, t("fleet.hours_tip"))
            fleet_start = ui.button(t("fleet.start"), color="primary")
            fleet_stop = ui.button(t("fleet.stop"), color="red").props("outline")
            fleet_status = ui.label(t("soak.idle")).classes("text-sm")

        fleet_log = ui.log(max_lines=300).classes("w-full h-40 font-mono text-xs q-mt-sm")
        # The log scrolls and is capped at 300 lines; a three-day run throws
        # away everything that happened on the Saturday. The verdict has to
        # live somewhere that does not scroll, and on DISK as well, because
        # the app being closed is the normal end of a weekend run.
        fleet_summary = ui.label("").classes(
            "w-full font-mono text-xs whitespace-pre q-mt-sm")
        fleet_summary.visible = False

    # Restore the saved roster. The single hardcoded row is only what a
    # brand-new install starts from.
    _saved = soak_fleet.roster_from_config(ctx.cfg.fleet,
                                           {lay.key for lay in CABINET_LAYOUTS})
    for _name, _host, _key in _saved:
        add_row(_name, _host, _key)
    if not _saved:
        add_row("Chest-Std-02", "192.168.0.204", "lgs80")

    def do_fleet_start() -> None:
        cabs = []
        for e in fleet_rows:
            host = (e["host"].value or "").strip()
            if not host:
                continue
            layout = resolve_cabinet(e["cab"].value, ctx.cfg.cabinet_custom)
            cabs.append(soak_fleet.FleetCabinet(
                name=(e["name"].value or host).strip(),
                host=host, ids=tuple(layout.ids)))
            e["live"].set_text("…")
        if not cabs:
            ui.notify(t("fleet.none"), type="warning")
            return
        # Two rows on one gateway is the two-masters fault with the tool
        # playing both parts. Refuse here: once the threads are running each
        # one checks the gateway for peers as it arrives, so whichever
        # connects first finds it empty and is let through.
        dupes = soak_fleet.duplicate_hosts(cabs)
        if dupes:
            ui.notify(t("fleet.dupe_host", hosts=", ".join(dupes)),
                      type="negative", timeout=0, close_button=True)
            for e in fleet_rows:
                if (e["host"].value or "").strip() in dupes:
                    e["live"].set_text(t("fleet.dupe_short"))
            return
        log_dir = config_store.data_dir() / "exports"
        if not worker.start_fleet(cabs, _cfg(()), log_dir):
            # start_fleet refuses a host this tool is already connected to:
            # two masters on one bus is the failure that looks like bad
            # hardware for a week.
            ui.notify(t("fleet.busy"), type="warning")
            fleet_status.set_text(t("fleet.busy"))
            fleet_status.classes(replace="text-sm text-orange")
            return
        fleet_log.clear()
        fleet_log.push(f"{datetime.now():%H:%M:%S}  start · {len(cabs)} cabinets")
        # Everything the verdict is built from is reset here rather than at
        # the end, so a second run cannot inherit the first one's numbers.
        fleet_state["tally"] = {c.name: soak_fleet.CabinetTally(
            name=c.name, modules=len(c.ids)) for c in cabs}
        fleet_state["t0"] = time.monotonic()
        fleet_state["started"] = f"{datetime.now():%Y-%m-%d %H:%M:%S}"
        fleet_state["early"] = False
        hours = float(fleet_hours.value or 0)
        fleet_state["deadline"] = (time.monotonic() + hours * 3600.0
                                   if hours > 0 else 0.0)
        framer_watch.start()
        framer_watch.reset()
        fleet_summary.visible = False
        fleet_summary.set_text("")
        fleet_status.set_text(t("fleet.running", n=len(cabs))
                              + (f" - {hours:g} h" if hours > 0 else ""))
        fleet_status.classes(replace="text-sm text-green")

    fleet_start.on_click(do_fleet_start)
    fleet_stop.on_click(lambda: worker.cancel_fleet())

    def finish_fleet() -> None:
        """Write the verdict where a Tuesday morning can find it."""
        tallies = list(fleet_state["tally"].values())
        if not tallies:
            return
        text = soak_fleet.summarise(
            tallies, framer_watch.snapshot(),
            started=fleet_state["started"],
            duration_s=time.monotonic() - fleet_state["t0"],
            stopped_early=bool(fleet_state["early"]))
        fleet_summary.set_text(text)
        fleet_summary.visible = True
        # On disk too. The app being closed is the ordinary end of a weekend
        # run, and a verdict that lives only in a browser tab does not
        # survive it. Beside the CSVs, so the whole run is one folder.
        try:
            stem = (fleet_state["started"].replace(":", "")
                    .replace("-", "").replace(" ", "-"))
            path = config_store.data_dir() / "exports" / f"fleet-{stem}.txt"
            path.write_text(text, encoding="utf-8")
            fleet_log.push(f"{datetime.now():%H:%M:%S}  summary written to "
                           f"{path.name}")
        except OSError as exc:
            # Never let the disk be the reason a finished run reports nothing.
            fleet_log.push(f"{datetime.now():%H:%M:%S}  could not write the "
                           f"summary: {exc}")
        fleet_state["tally"] = {}

    def fleet_drain() -> None:
        running = worker.fleet_running()
        fleet_start.set_enabled(not running)
        fleet_stop.set_enabled(running)
        # The clock. Checked here rather than on a thread of its own, so that
        # stopping is the same code path whoever asks for it.
        if running and fleet_state["deadline"]:
            left = fleet_state["deadline"] - time.monotonic()
            if left <= 0:
                fleet_state["deadline"] = 0.0
                fleet_log.push(f"{datetime.now():%H:%M:%S}  time is up - "
                               f"stopping and clearing every cabinet")
                worker.cancel_fleet()
            else:
                fleet_status.set_text(t("fleet.running_left",
                                        n=len(fleet_state["tally"]),
                                        left=_dur(left)))
        fleet_state["seq"], events = worker.drain_fleet_events(fleet_state["seq"])
        # STRIPPED, to match FleetCabinet.name. Keying on the raw field value
        # meant a name typed with a trailing space never matched its own
        # events: that row's live column sat at "..." all night and its
        # failures never reached it.
        by_name = {(e["name"].value or e["host"].value).strip(): e
                   for e in fleet_rows}
        for ev in events:
            if isinstance(ev, soak_fleet.FleetStarted):
                fleet_log.push(f"{datetime.now():%H:%M:%S}  {ev.cabinet} · "
                               f"{ev.modules} modules · {ev.path.split(chr(92))[-1]}")
            elif isinstance(ev, soak_fleet.FleetBusy):
                fleet_log.push(f"{datetime.now():%H:%M:%S}  {ev.cabinet} · "
                               f"REFUSED — another master: {ev.peers}")
                if ev.cabinet in by_name:
                    by_name[ev.cabinet]["live"].set_text(f"refused · {ev.peers}")
                if ev.cabinet in fleet_state["tally"]:
                    fleet_state["tally"][ev.cabinet].note = (
                        f"refused, another master: {ev.peers}")
            elif isinstance(ev, soak_fleet.FleetFailed):
                fleet_log.push(f"{datetime.now():%H:%M:%S}  {ev.cabinet} · {ev.reason}")
                if ev.cabinet in fleet_state["tally"]:
                    fleet_state["tally"][ev.cabinet].note = ev.reason
                if ev.cabinet in by_name:
                    by_name[ev.cabinet]["live"].set_text(ev.reason)
            elif isinstance(ev, soak_fleet.FleetEvent):
                inner = ev.inner
                tally = fleet_state["tally"].get(ev.cabinet)
                if tally is not None:
                    tally.absorb(inner)
                if isinstance(inner, soak.SoakTick) and ev.cabinet in by_name:
                    by_name[ev.cabinet]["live"].set_text(
                        f"{_dur(inner.elapsed_s)} · {inner.passes} passes · "
                        f"{inner.txns:,} reads · fails {inner.fails} · "
                        f"reboots {inner.reboots} · wdt {inner.watchdogs}"
                        + (f" · picks {inner.picks}" if inner.picks else ""))
                elif isinstance(inner, soak.SoakAnomaly):
                    fleet_log.push(f"{ev.cabinet}  {inner.item.text}")
                elif isinstance(inner, soak.SoakDone):
                    fleet_log.push(f"{datetime.now():%H:%M:%S}  {ev.cabinet} · "
                                   f"stopped · {inner.summary}")
        if not running and fleet_state["tally"]:
            # However it ended - the clock, the stop button, or every cabinet
            # giving up - the run gets judged exactly once.
            fleet_state["early"] = bool(fleet_state["deadline"])
            fleet_state["deadline"] = 0.0
            finish_fleet()
            fleet_status.set_text(t("soak.idle"))
            fleet_status.classes(replace="text-sm")

    ui.timer(0.5, fleet_drain)
    fleet_drain()

    ui.timer(0.5, drain)
    drain()
