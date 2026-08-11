"""Gateway tab — read and edit the Opta gateway's own settings.

Talks the `$LGS` text console over USB (see app/gateway_config.py). The
gateway is not a Modbus device, so nothing here goes through pymodbus; the
worker lends the COM port for the duration of each exchange.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from nicegui import ui

from .. import config_store, lgs_map
from ..fw_survey import ReportSurveyDone, SurveyProgress
from ..i18n import t
from ..lgs_map import BAUD_WHITELIST
from ..version import APP_VERSION
from . import Ctx, confirm, helps, tab_gateway_fw

# Which settings each card shows, in display order.
# sys.wdt_ms only exists on gateway >= 1.8.0; field_row skips what the
# firmware did not report.
CARD_IDENTITY = ("sys.name", "sys.wdt_ms")
CARD_RS485 = ("rs485.baud", "rs485.predelay_us", "rs485.postdelay_us",
              "rs485.t1_ms", "rs485.t2_ms")
CARD_USB = ("usb.gap_ms", "usb.max_ms")
CARD_NET = ("net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns",
            "net.port", "net.link_timeout_ms")
# Only rendered when the firmware reports these keys (gateway >= 1.2.0).
# bus.hub_map comes first and is drawn by hub_map_editor, not as a plain field.
CARD_HUB = ("bus.hub_map", "bus.hub_settle_ms", "bus.hub_budget_ms",
            "bus.hub_retry", "bus.hub_gap_ms")

# Front-panel buttons (gateway >= 1.3.0). The colours are how they are wired
# to inputs 1-5; what each one does is what this card sets.
PANEL_KEYS = ("panel.btn1", "panel.btn2", "panel.btn3", "panel.btn4",
              "panel.btn5")
PANEL_COLORS = ("red", "green", "blue", "yellow", "white")
PANEL_SWATCH = {"red": "#e53935", "green": "#43a047", "blue": "#1e88e5",
                "yellow": "#fdd835", "white": "#fafafa"}
PANEL_ACTIONS = {0: "pnl.act.none", 1: "pnl.act.all_on", 2: "pnl.act.all_off",
                 3: "pnl.act.all_unlock", 4: "pnl.act.reset"}
# What each of the gateway's four relay outputs does. Output 1 normally
# carries the shelf's power — which is what a hardware reset drops — but even
# that is a mapping now, so a re-wired panel is a setting, not a build.
LAMP_OUT_KEYS = ("panel.out1", "panel.out2", "panel.out3", "panel.out4")
LAMP_SOURCES = {0: "pnl.src.none", 1: "pnl.src.ready", 2: "pnl.src.busy",
                3: "pnl.src.fault", 4: "pnl.src.link", 5: "pnl.src.client",
                6: "pnl.src.sweep", 7: "pnl.src.reset", 8: "pnl.src.shelf"}
# What colour of lamp is actually fitted to each output. The gateway does not
# know and should not — it drives outputs, not colours — but the person
# reading this page is looking at a panel of coloured lamps, so the tool keeps
# its own note of which is which.
LAMP_COLOURS = ("green", "amber", "red", "blue", "white", "none")
LAMP_COLOUR_DEFAULT = ("none", "green", "amber", "red")
# A lamp's colour shown as the thing itself. The word is still carried in the
# tooltip's legend, so nothing is lost by dropping it from the field — and a
# column of dots is read at a glance, which a column of colour names is not.
LAMP_COLOUR_SYMBOL = {"green": "🟢", "amber": "🟡", "red": "🔴",
                      "blue": "🔵", "white": "⚪", "none": "—"}

BOOL_KEYS = {"net.enabled", "net.dhcp", "panel.enabled", "panel.lamps",
             "sched.reset_enabled"}

# The four scheduled-reset times (gateway >= 1.8.0). Slot 1 keeps the original
# key name — the gateway's key table is append-only, so it could not be
# renamed without moving every key after it.
SCHED_SLOT_KEYS = ("sched.reset_hhmm", "sched.reset_hhmm2",
                   "sched.reset_hhmm3", "sched.reset_hhmm4")


def hhmm_text(value: str) -> str:
    """`"300"` -> `"03:00"`. People set a clock reading, not a four-digit
    number; the console stores the number, so the translation happens here."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return ""
    if not 0 <= v <= 2359 or v % 100 > 59:
        return ""
    return f"{v // 100:02d}:{v % 100:02d}"


def hhmm_value(text: str):
    """`"03:00"` -> `300`, or None while the field is empty or half-typed."""
    parts = (text or "").split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return None
    hour, minute = int(parts[0]), int(parts[1])
    if hour > 23 or minute > 59:
        return None
    return hour * 100 + minute


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
    if key in SCHED_SLOT_KEYS:
        return hhmm_text(value) or value or "—"
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

    # ── config file: export / import ───────────────────────────────────────
    # A settings file is the answer to two recurring days: the firmware whose
    # settings struct changed wipes the store on upgrade, and a replacement
    # unit starts from nothing. Import stages values as ordinary edits — the
    # SAVE review still stands between a file and the gateway.
    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("gw.cfg_card")).classes("font-bold"),
              t("gw.cfg_hint"))
        with ui.row().classes("items-center gap-3 flex-wrap"):
            ui.button(t("gw.cfg_export"),
                      on_click=lambda: do_export()) \
                .props("outline dense no-caps") \
                .tooltip(t("gw.cfg_export_tip"))
            ui.upload(label=t("gw.cfg_import"),
                      on_upload=lambda e: do_import(e),
                      auto_upload=True, max_files=1) \
                .props('accept=".json" flat dense')

    # ── site report ────────────────────────────────────────────────────────
    # The record a cabinet leaves commissioning with: gateway identity and
    # settings, the cabinet's shape, and every module's chip UID — on paper,
    # for the day someone asks what is installed in slot 45.
    with ui.card().classes("p-3 w-full q-mt-sm"):
        helps(ui.label(t("rpt.card")).classes("font-bold"), t("rpt.hint"))
        with ui.row().classes("items-center gap-3 flex-wrap"):
            report_btn = ui.button(t("rpt.run"),
                                   on_click=lambda: do_report()) \
                .props("outline dense no-caps")
            ui.button(t("btn.cancel"),
                      on_click=lambda: worker.cancel_fw_survey()).props("flat")
            report_progress = ui.linear_progress(value=0.0, show_value=False) \
                .classes("w-48")
            report_label = ui.label("").classes("text-sm text-grey")

    def usable() -> tuple:
        """(ok, message) — the console is USB-only and needs a port."""
        if ctx.transport() != "rtu":
            return False, t("gw.usb_only")
        if not ctx.port():
            return False, t("gw.no_port")
        return True, ""

    # Firmware update / QSPI provisioning: its own module — it shares only
    # the port check and the log pane with the settings machinery here.
    # get_log is late-bound because log_box is created just below.
    tab_gateway_fw.build(ctx, usable, lambda: log_box)

    log_box = ui.log(max_lines=40).classes("w-full h-32 font-mono text-xs")

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

    def time_field(key: str, snap):
        """One slot's time, as a clock rather than the four-digit number the
        console stores. Returns the element so the caller can gate it."""
        def changed(e) -> None:
            value = hhmm_value(e.value)
            # Half-typed or cleared: leave the staged value alone rather than
            # stage a time nobody meant.
            if value is not None:
                stage(key, value)

        el = ui.input(value=hhmm_text(snap.settings.get(key, "0")),
                      on_change=changed) \
            .props("dense outlined type=time").classes("w-28")
        # All four slots answer the same question, so they share slot 1's
        # explanation rather than repeating it four times.
        helps(el, f"{hint_of('sched.reset_hhmm')} ({key})")
        fields[key] = el
        return el

    def hub_map_editor(snap) -> None:
        """One channel picker per row, sized to the cabinet in front of you.

        The console value is a comma list, which is fine to read and awful to
        type — and typing ten numbers is plainly wrong for an LGS with five
        rows. So the rows come first: say how many the cabinet has, then set
        each row's channel. The text field stays as the single staged value
        (that is what SAVE sends) and follows whatever the pickers say.
        """
        current = str(snap.settings.get("bus.hub_map", "") or "")
        try:
            channels = lgs_map.parse_hub_map(current)
        except ValueError:
            channels = [0] * lgs_map.HUB_ROWS
        # Default the row count to the last row that is actually wired — the
        # map is the truth about this cabinet. Only an empty map falls back
        # to the header's cabinet type.
        wired = [r for r, ch in enumerate(channels, 1) if ch]
        rows_default = max(wired) if wired else ctx.cabinet().row_count

        # The staged value. Kept visible: it is exactly what the console
        # stores, and it can still be pasted from another cabinet's notes.
        text = ui.input(label_of("bus.hub_map"), value=current,
                        on_change=lambda e: stage("bus.hub_map", e.value)) \
            .props("dense outlined").classes("w-72")
        helps(text, f"{hint_of('bus.hub_map')} (bus.hub_map)")
        fields["bus.hub_map"] = text

        pickers: list = []

        def push() -> None:
            """Rebuild the console value from the pickers."""
            text.set_value(",".join(str(int(p.value or 0)) for p in pickers))

        def build_rows(n: int, *, push_after: bool = True) -> None:
            """push_after=False for the initial render: pushing rewrites the
            text field, whose on_change would stage a normalisation-diff of
            the gateway's own value — a dirty flag with no edit behind it."""
            row_box.clear()
            pickers.clear()
            options = {0: "—"} | {c: str(c) for c in range(1, lgs_map.HUB_CHANNELS + 1)}
            with row_box:
                for r in range(1, int(n) + 1):
                    with ui.column().classes("gap-0 items-center"):
                        ui.label(f"R{r}").classes("text-xs text-grey")
                        sel = ui.select(options,
                                        value=channels[r - 1] if r <= len(channels) else 0,
                                        on_change=lambda _: push()) \
                            .props("dense outlined").classes("w-16")
                        pickers.append(sel)
            if push_after:
                push()

        with ui.row().classes("items-center gap-2 q-mt-sm flex-wrap"):
            rows_input = ui.number(t("gw.hub_rows"), value=rows_default,
                                   min=1, max=lgs_map.HUB_ROWS, format="%d") \
                .props("dense outlined").classes("w-32")
            helps(rows_input, t("gw.hub_rows_tip"))

        row_box = ui.row().classes("gap-1 q-mt-sm flex-wrap items-end")

        with ui.row().classes("gap-2 q-mt-xs"):
            def preset(fn) -> None:
                for i, p in enumerate(pickers, 1):
                    p.set_value(fn(i))
                push()

            ui.button(t("gw.hub.per_row"),
                      on_click=lambda: preset(
                          lambda r: ((r - 1) % lgs_map.HUB_CHANNELS) + 1)) \
                .props("flat dense no-caps").tooltip(t("gw.hub.per_row_tip"))
            ui.button(t("gw.hub.one_channel"),
                      on_click=lambda: preset(lambda r: 1)) \
                .props("flat dense no-caps").tooltip(t("gw.hub.one_channel_tip"))
            ui.button(t("gw.hub.nohub"), on_click=lambda: preset(lambda r: 0)) \
                .props("flat dense no-caps").tooltip(t("gw.hub.nohub_tip"))

        rows_input.on_value_change(
            lambda e: build_rows(max(1, int(e.value or 1))))
        # The initial render must not push: the card opens showing the
        # gateway's value verbatim, with zero staged edits.
        build_rows(rows_default, push_after=False)

    def cabinet_field(snap) -> None:
        """panel.cabinet as a select, checked against the header's cabinet.

        The header is the authority on what cabinet this is; the gateway's
        copy decides which slots its button sweeps walk, so the two must
        agree. The fix button stages the matching values as ordinary
        edits — the normal SAVE review still stands between the click and
        the gateway.

        Two vocabularies, by firmware age. A preset cabinet is the code in
        `panel.cabinet`; a shape the catalogue lacks (SMT, custom) is a
        per-row width list in `panel.shape` (gateway >= 1.9.0), which
        overrides the code when set. Older firmware without `panel.shape`
        can only be told the codes, so a shape there shows a note instead
        of a warning it cannot fix.
        """
        key = "panel.cabinet"
        skey = "panel.shape"
        value = str(snap.settings.get(key, ""))
        has_shape = skey in snap.settings
        tool = ctx.cabinet()                       # read at render time
        options = {"40": "40", "64": "64", "80": "80"}
        # What the header wants on the gateway: a preset wants its code and
        # no shape; a non-catalogue cabinet wants its widths as the shape.
        want_shape = ("0" if tool.panel_cabinet
                      else lgs_map.format_custom_widths(
                          lgs_map.layout_widths(tool)))

        def eff(k: str, dflt: str) -> str:         # a staged edit wins
            return state["edits"].get(k, str(snap.settings.get(k, dflt)))

        def agreed() -> bool:
            if tool.panel_cabinet:
                shape_clear = (not has_shape
                               or lgs_map.same_shape(eff(skey, "0"), "0"))
                return shape_clear and eff(key, "") == tool.panel_cabinet
            return has_shape and lgs_map.same_shape(eff(skey, "0"), want_shape)

        def fix() -> None:
            if tool.panel_cabinet:
                if has_shape:
                    stage(skey, want_shape)        # "0": the preset rules again
                el.set_value(tool.panel_cabinet)   # no-op when already right
                stage(key, tool.panel_cabinet)
            else:
                stage(skey, want_shape)
            refresh()

        def warn_text() -> str:
            if not tool.panel_cabinet:
                return t("gw.cab.shape_mismatch", tool=tool.label,
                         want=want_shape)
            if has_shape and not lgs_map.same_shape(eff(skey, "0"), "0"):
                # The code may even match — the stray shape is what rules.
                return t("gw.cab.stray_shape", tool=tool.label)
            return t("gw.cab.mismatch", gw=eff(key, "") or "?",
                     tool=tool.label)

        def refresh() -> None:
            bad = not agreed()
            warn_row.set_visibility(bad)
            if bad:
                warn_label.set_text(warn_text())

        fixable = bool(tool.panel_cabinet) or has_shape
        fix_label = (t("gw.cab.fix", code=tool.panel_cabinet)
                     if tool.panel_cabinet else t("gw.cab.set_shape"))

        with ui.column().classes("gap-0 w-72 mb-2"):
            el = ui.select(options, value=value if value in options else None,
                           label=label_of(key),
                           on_change=lambda e: (stage(key, e.value), refresh())) \
                .props("dense outlined").classes("w-full")
            hint = hint_of(key)
            helps(el, f"{hint} ({key})" if hint else key)
            pending = snap.staged.get(key)
            if pending is not None:
                ui.label(t("gw.pending_on_gateway", v=shown(key, pending))) \
                    .classes("text-xs text-orange leading-tight mt-1")
            if has_shape and not lgs_map.same_shape(eff(skey, "0"), "0"):
                # The one fact that changes how this select reads: while a
                # shape is set, the sweeps ignore the code above.
                ui.label(t("gw.cab.shape_active", shape=eff(skey, "0"))) \
                    .classes("text-xs text-grey leading-tight mt-1")
            if fixable:
                with ui.row().classes("items-center gap-2 no-wrap mt-1") as warn_row:
                    warn_label = ui.label("").classes("text-xs text-orange")
                    helps(ui.button(fix_label, on_click=fix)
                          .props("dense outline no-caps color=orange"),
                          t("gw.cab.fix_tip", code=want_shape
                            if not tool.panel_cabinet else tool.panel_cabinet))
                refresh()
            else:
                # Old firmware, non-catalogue cabinet: nothing to offer.
                ui.label(t("gw.cab.no_code", label=tool.label)) \
                    .classes("text-xs text-grey leading-tight mt-1")
        fields[key] = el

    def panel_editor(snap) -> None:
        """One row per button, in the colours they are wired in.

        The buttons exist so the cabinet can be exercised at the cabinet with
        no PC, which means the person setting them up is looking at coloured
        caps, not at input numbers — so the colour leads and `panel.btnN` is
        the hover text.
        """
        # The master first. Everything that only matters while the button
        # inputs are read is disabled when they are not — an action that can
        # be set but can never fire reads as a broken cabinet. What stays
        # live: panel.reset_ms (the scheduled reset uses it too), the
        # cabinet identity (a record, and its mismatch fix must stay
        # reachable), and the lamps (their own switch below).
        field_row("panel.enabled", snap)
        master = fields["panel.enabled"]
        gated: list = []

        options = {v: t(k) for v, k in PANEL_ACTIONS.items()}
        for i, key in enumerate(PANEL_KEYS):
            if key not in snap.settings:
                continue
            raw = snap.settings.get(key, "0")
            value = int(raw) if raw.isdigit() else 0
            colour = PANEL_COLORS[i]
            with ui.row().classes("items-center gap-2 no-wrap q-mb-xs"):
                ui.element("div").classes("rounded-full border") \
                    .style(f"width:14px;height:14px;background:{PANEL_SWATCH[colour]}")
                ui.label(t(f"pnl.btn_colour.{colour}")).classes("text-sm w-20")
                el = ui.select(options, value=value,
                               on_change=lambda e, k=key: stage(k, int(e.value))) \
                    .props("dense outlined").classes("grow")
                helps(el, t("pnl.input", n=i + 1, name=key))
                fields[key] = el
                gated.append(el)
        # Which module preset the sweeps fire (gateway >= 1.10.0). A select,
        # because 1-8 typed as text invites a 9; the look itself — brightness,
        # colour — is that preset's per-module config, which the hint says.
        if "panel.preset" in snap.settings:
            raw = snap.settings.get("panel.preset", "1")
            value = int(raw) if raw.isdigit() else 1
            with ui.column().classes("gap-0 w-72 mb-2"):
                el = ui.select({n: t("pnl.preset_n", n=n) for n in range(1, 9)},
                               value=value if 1 <= value <= 8 else 1,
                               label=label_of("panel.preset"),
                               on_change=lambda e: stage("panel.preset",
                                                         int(e.value))) \
                    .props("dense outlined").classes("w-full")
                hint = hint_of("panel.preset")
                helps(el, f"{hint} (panel.preset)" if hint else "panel.preset")
            fields["panel.preset"] = el
            gated.append(el)
        # Temporary test brightness (gateway >= 1.10.0): writes each module's
        # VOLATILE global brightness before lighting it, so a bench test can
        # be dim or blinding without touching what the site configured.
        if "panel.bright" in snap.settings:
            field_row("panel.bright", snap)
            gated.append(fields["panel.bright"])
        if "panel.step_ms" in snap.settings:
            field_row("panel.step_ms", snap)
            gated.append(fields["panel.step_ms"])
        if "panel.reset_ms" in snap.settings:
            field_row("panel.reset_ms", snap)
        if "panel.cabinet" in snap.settings:
            cabinet_field(snap)

        for widget in gated:
            widget.bind_enabled_from(master, "value")
        # Reuses the schedule card's wording — the same rule, said once.
        ui.label(t("sch.off_note")).classes("text-xs text-grey") \
            .bind_visibility_from(master, "value", backward=lambda v: not v)

        # ── status lamps ──────────────────────────────────────────────────
        if "panel.lamps" in snap.settings:
            ui.separator().classes("q-my-sm")
            helps(ui.label(t("pnl.lamp_card")).classes("font-bold"),
                  t("pnl.lamp_hint"))
            # The master first, like every other section: while the lamps are
            # off their mapping and timings are disabled. One nuance the hint
            # carries: an output mapped to the shelf's power keeps running
            # regardless — that switch is about lamps, not about the cabinet.
            field_row("panel.lamps", snap)
            lamps_master = fields["panel.lamps"]
            lamp_gated: list = []
            # What each output follows. Which colour sits on which output is
            # wiring, and what a colour should mean is a site's call — so both
            # are answered here rather than assumed by the firmware.
            #
            # No lit/dark indicator here: this page reads the gateway once, so
            # any such mark is a photograph of a lamp that has moved on since,
            # and a stale one is worse than none. The panel itself is the live
            # view; `$LGS LAMP n` is how a suspect output is proven.
            if "panel.out1" in snap.settings:
                src_options = {v: t(k) for v, k in LAMP_SOURCES.items()}
                colour_options = {c: LAMP_COLOUR_SYMBOL[c] for c in LAMP_COLOURS}
                # The symbols carry no words, so the hint carries the key.
                colour_hint = t("pnl.lamp_colour_hint") + " — " + " · ".join(
                    f"{LAMP_COLOUR_SYMBOL[c]} {t(f'pnl.lamp_colour.{c}')}"
                    for c in LAMP_COLOURS)
                fitted = lamp_colours()
                for i, key in enumerate(LAMP_OUT_KEYS):
                    raw = snap.settings.get(key, "0")
                    value = int(raw) if raw.isdigit() else 0
                    colour = fitted[i]
                    with ui.row().classes("items-center gap-2 no-wrap q-mb-xs"):
                        ui.label(t("pnl.out_n", n=i + 1)).classes("text-sm w-16")
                        # The lamp's colour is the tool's note about the panel
                        # in front of it — the gateway has no idea, and should
                        # not, so this is saved here and not sent anywhere.
                        cel = helps(ui.select(
                            colour_options, value=colour,
                            on_change=lambda e, n=i: set_lamp_colour(n, e.value)) \
                            .props("dense outlined borderless").classes("w-16"),
                            colour_hint)
                        el = ui.select(
                            src_options,
                            value=value if value in src_options else 0,
                            on_change=lambda e, k=key: stage(k, int(e.value))) \
                            .props("dense outlined").classes("grow")
                        helps(el, t("pnl.out_hint", name=key))
                        fields[key] = el
                        lamp_gated.extend((cel, el))
            for key in ("panel.lamp_hold_ms", "panel.lamp_dwell_ms",
                        "panel.lamp_dead"):
                if key in snap.settings:
                    field_row(key, snap)
                    lamp_gated.append(fields[key])
            for widget in lamp_gated:
                widget.bind_enabled_from(lamps_master, "value")
            ui.label(t("sch.off_note")).classes("text-xs text-grey") \
                .bind_visibility_from(lamps_master, "value",
                                      backward=lambda v: not v)

    def sched_editor(snap) -> None:
        """The gateway's clock, and the nightly power cycle it drives."""
        # The gateway sends ISO with a T so it survives the console's
        # whitespace-split; a space reads better here.
        now = snap.info.get("time.now", "unset").replace("T", " ")
        was_set = snap.info.get("time.set") == "1"
        last = snap.info.get("sched.last", "0")

        with ui.row().classes("items-center gap-2 flex-wrap"):
            ui.label(t("sch.now", now=now)).classes(
                "text-sm font-mono" + ("" if was_set else " text-red"))

            async def set_now() -> None:
                res = await worker.gw_set_time(ctx.port(), wall_epoch())
                ui.notify(t("sch.synced") if res.ok else res.note,
                          type="positive" if res.ok else "negative")
                await do_reload()

            helps(ui.button(t("sch.sync"), on_click=set_now)
                  .props("outline dense no-caps"), t("sch.sync_hint"))
        if last and last != "0":
            # sched.last is already wall time, so it must not be shifted
            # again by this PC's timezone.
            when = (datetime(1970, 1, 1) + timedelta(seconds=int(last)))
            ui.label(t("sch.last", when=when.strftime("%Y-%m-%d %H:%M")))                 .classes("text-xs text-grey")

        field_row("sched.reset_enabled", snap)
        master = fields["sched.reset_enabled"]
        # Everything below is the schedule's detail, and detail you cannot act
        # on is worse than absent: it invites someone to set a time and walk
        # away believing the cabinet will reset. So the switch gates it all.
        gated: list = []

        # Four slots, each with its own tick. The times stay editable-looking
        # while their slot is off because the firmware keeps them — untick,
        # retick, and the hour is still there.
        has_slots = "sched.reset_slots" in snap.settings
        if has_slots:
            raw_slots = snap.settings.get("sched.reset_slots", "1")
            slot_mask = int(raw_slots) if raw_slots.isdigit() else 1
            ticks: list = []

            def push_slots() -> None:
                value = 0
                for bit, box in enumerate(ticks):
                    if box.value:
                        value |= 1 << bit
                stage("sched.reset_slots", value)
                none_ticked.set_visibility(value == 0)

            helps(ui.label(t("sch.slots")).classes("text-sm text-grey"),
                  t("sch.slot_hint"))
            for i, key in enumerate(SCHED_SLOT_KEYS):
                if key not in snap.settings:
                    continue
                with ui.row().classes("items-center gap-2 no-wrap q-mb-xs"):
                    box = ui.checkbox(t("sch.slot_n", n=i + 1),
                                      value=bool(slot_mask & (1 << i)),
                                      on_change=lambda _: push_slots()) \
                        .props("dense").classes("text-xs w-24")
                    ticks.append(box)
                    gated.append(box)
                    gated.append(time_field(key, snap))
            none_ticked = ui.label(t("sch.no_slots")) \
                .classes("text-xs text-orange leading-tight")
            none_ticked.set_visibility(slot_mask == 0)
        else:
            # Gateway < 1.8.0: one time, and it is on whenever the switch is.
            field_row("sched.reset_hhmm", snap)
            gated.append(fields["sched.reset_hhmm"])

        # Days as seven checkboxes, because a bitmask is not something anyone
        # should have to add up. All seven clear means every day, which is
        # also what the firmware reads a zero as.
        raw = snap.settings.get("sched.reset_days", "0")
        mask = int(raw) if raw.isdigit() else 0
        boxes: list = []

        def push_days() -> None:
            value = 0
            for bit, box in enumerate(boxes):
                if box.value:
                    value |= 1 << bit
            stage("sched.reset_days", 0 if value == 0x7F else value)

        with ui.row().classes("gap-1 flex-wrap items-center"):
            ui.label(t("sch.days")).classes("text-sm text-grey w-20")
            for bit, name in enumerate(("sch.sun", "sch.mon", "sch.tue", "sch.wed",
                                        "sch.thu", "sch.fri", "sch.sat")):
                box = ui.checkbox(t(name),
                                  value=bool(mask == 0 or (mask & (1 << bit))),
                                  on_change=lambda _: push_days()) \
                    .props("dense").classes("text-xs")
                boxes.append(box)
                gated.append(box)
        helps(ui.label(t("sch.days_hint")).classes("text-xs text-grey"),
              t("sch.days_hint"))

        for widget in gated:
            widget.bind_enabled_from(master, "value")
        ui.label(t("sch.off_note")).classes("text-xs text-grey") \
            .bind_visibility_from(master, "value", backward=lambda v: not v)

    def apply_pending(values: dict) -> None:
        """Drop values into the fields as ordinary unsaved edits.

        A key with no widget of its own (the schedule's masks, panel.shape)
        is staged directly: the SAVE dialog is where such values are seen,
        and skipping them would silently drop part of a defaults load or an
        imported file.
        """
        for key, text in values.items():
            el = fields.get(key)
            if el is None:
                stage(key, text)
                continue
            if key in BOOL_KEYS:
                el.set_value(text == "1")
            elif key == "rs485.baud":
                el.set_value(int(text) if text.isdigit() else text)
            elif key in SCHED_SLOT_KEYS:
                el.set_value(hhmm_text(text))    # the field holds a clock
            else:
                el.set_value(text)

    def do_export() -> None:
        """The gateway's settings as a JSON file — what is RUNNING, not the
        unsaved edits: a backup is a record of the cabinet, not of a half-
        finished thought."""
        snap = state["snapshot"]
        if snap is None or not snap.ok:
            ui.notify(t("gw.cfg_need_read"), type="warning")
            return
        payload = {
            "app": "LGS-Test-Tool",
            "kind": "gateway-config",
            "fw": snap.info.get("fw", "?"),
            "gateway_id": snap.info.get("id", ""),
            "name": snap.settings.get("sys.name", ""),
            "saved": datetime.now().isoformat(timespec="seconds"),
            # net.mac is the board's identity, not a setting — a file that
            # carried it would invite importing one gateway into another.
            "settings": {k: v for k, v in sorted(snap.settings.items())
                         if k != "net.mac"},
        }
        tag = payload["name"] or payload["gateway_id"] or "gateway"
        fname = f"gateway-config-{tag}-{datetime.now():%Y%m%d-%H%M}.json"
        ui.download(json.dumps(payload, indent=2).encode("utf-8"), fname)

    def do_report() -> None:
        """Sweep the cabinet's modules and render the PDF.

        Needs both faces of the tool at once: the console snapshot for the
        gateway half (Detect first) and a connected Modbus link for the
        module half — the sweep is the same read-only kind a firmware
        survey does, one FC03 per module.
        """
        snap = state["snapshot"]
        if snap is None or not snap.ok:
            ui.notify(t("gw.cfg_need_read"), type="warning")
            return
        layout = ctx.cabinet()
        if not worker.start_report_survey(layout.ids):
            ui.notify(t("rpt.need_connect"), type="warning")
            return
        report_state.update(snapshot=snap, layout=layout, waiting=True)
        report_btn.set_enabled(False)
        report_progress.set_value(0.0)
        report_label.set_text(t("rpt.running", n=layout.count))

    def finish_report(records: list, cancelled: bool) -> None:
        report_btn.set_enabled(True)
        report_state["waiting"] = False
        if cancelled:
            report_label.set_text(t("rpt.cancelled"))
            return
        snap = report_state["snapshot"]
        layout = report_state["layout"]
        # Imported here, not at module top: fpdf2 is the one dependency a
        # bare interpreter may lack, and a missing PDF library must cost
        # the report button, never the whole Gateway tab.
        try:
            from .. import report_pdf
        except ImportError:
            ui.notify(t("rpt.no_lib"), type="negative", timeout=9000)
            report_label.set_text("")
            return
        pdf = report_pdf.build_report_pdf(
            app_version=APP_VERSION, generated=datetime.now(),
            info=snap.info, settings=snap.settings,
            cabinet_label=layout.label, cabinet_count=layout.count,
            widths=lgs_map.layout_widths(layout), records=records,
            hub_channel=lgs_map.hub_channel)
        name = snap.settings.get("sys.name", "") or snap.info.get("id", "gw")
        fname = f"lgs-report-{name}-{datetime.now():%Y%m%d-%H%M}.pdf"
        # A copy stays in data/exports — a record someone can find later is
        # the point; the download is merely today's convenience.
        out = config_store.data_dir() / "exports" / fname
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(pdf)
        ui.download(pdf, fname)
        answered = sum(1 for r in records if r.responded)
        report_label.set_text(t("rpt.done", a=answered, n=len(records)))
        ui.notify(t("rpt.saved", name=fname), type="positive", timeout=8000)
        say(f"report: {fname} ({answered}/{len(records)} answered)")

    def drain_report() -> None:
        if not report_state["waiting"]:
            return
        report_state["seq"], events = \
            worker.drain_fw_survey_events(report_state["seq"])
        for ev in events:
            if isinstance(ev, SurveyProgress):
                report_progress.set_value(ev.index / max(1, ev.total))
                report_label.set_text(f"{ev.index}/{ev.total} · id {ev.device_id}")
            elif isinstance(ev, ReportSurveyDone):
                report_progress.set_value(1.0)
                finish_report(ev.records, ev.cancelled)

    report_state: dict = {"seq": 0, "waiting": False,
                          "snapshot": None, "layout": None}
    ui.timer(0.3, drain_report)

    def do_import(e) -> None:
        """Stage a config file's values — never write them. The SAVE review
        stands between any file and the gateway, and keys this firmware
        does not report are skipped and said out loud."""
        snap = state["snapshot"]
        if snap is None or not snap.ok:
            ui.notify(t("gw.cfg_need_read"), type="warning")
            return
        try:
            data = json.loads(e.content.read().decode("utf-8-sig"))
            if data.get("kind") != "gateway-config" \
                    or not isinstance(data.get("settings"), dict):
                raise ValueError("not a gateway config")
        except (ValueError, UnicodeDecodeError):
            ui.notify(t("gw.cfg_bad_file"), type="negative")
            return
        known: dict = {}
        skipped: list = []
        for k, v in data["settings"].items():
            if k == "net.mac":
                continue
            if k in snap.settings:
                known[k] = str(v)
            else:
                skipped.append(k)
        apply_pending(known)
        staged = len(state["edits"])
        msg = t("gw.cfg_imported", n=staged)
        if skipped:
            msg += " " + t("gw.cfg_skipped", n=len(skipped))
        ui.notify(msg, type="warning" if staged else "info", timeout=8000)
        say(f"import: {len(known)} known, {len(skipped)} skipped, "
            f"{staged} staged")

    def render(snap) -> None:
        cards.clear()
        # The elements just went with the cards; a stale reference here would
        # let apply_pending() address the dead render instead of this one.
        fields.clear()
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
                    # A watchdog reset means the firmware stopped running. It
                    # is the one reset reason worth reading twice, so it says
                    # so rather than sitting in a line of diagnostics.
                    if info.get("sys.reset") == "watchdog":
                        ui.label(t("gw.reset_by_wdt")) \
                            .classes("text-xs text-orange leading-tight")

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
                        # Older firmware has fewer of these; an empty field
                        # only invites a SET the console would reject.
                        if key in snap.settings:
                            field_row(key, snap)
                    wdt = info.get("sys.wdt")
                    if wdt is not None:
                        ui.label(t("gw.wdt_running", ms=wdt) if wdt != "0"
                                 else t("gw.wdt_off")) \
                            .classes("text-xs " + ("text-grey" if wdt != "0"
                                                   else "text-orange"))
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
                # Older gateway firmware has no hub keys; showing empty fields
                # would only invite a SET the console must reject.
                if "bus.hub_map" in snap.settings:
                    with ui.card().classes("p-3 grow"):
                        helps(ui.label(t("gw.card.hub")).classes("font-bold"),
                              t("gw.hub_hint"))
                        hub_map_editor(snap)
                        for key in CARD_HUB[1:]:        # hub_map has its own
                            field_row(key, snap)
                # Older firmware has no panel keys; the card stays away rather
                # than offering settings the console would reject.
                if "panel.btn1" in snap.settings:
                    with ui.card().classes("p-3 grow"):
                        helps(ui.label(t("pnl.card")).classes("font-bold"),
                              t("pnl.hint"))
                        panel_editor(snap)
                if "sched.reset_enabled" in snap.settings:
                    with ui.card().classes("p-3 grow"):
                        helps(ui.label(t("sch.card")).classes("font-bold"),
                              t("sch.hint"))
                        sched_editor(snap)

    def say(text: str) -> None:
        log_box.push(text)

    def lamp_colours() -> list:
        """Which colour is fitted to outputs 2, 3 and 4, per this tool's config."""
        parts = [p.strip() for p in str(ctx.cfg.lamp_colours or "").split(",")]
        # A config written before output 1 joined the table holds three
        # colours, for outputs 2-4. Read it as such rather than sliding every
        # lamp one row up.
        if len(parts) == 3:
            parts = ["none"] + parts
        out = list(LAMP_COLOUR_DEFAULT)
        for i in range(len(out)):
            if i < len(parts) and parts[i] in LAMP_COLOURS:
                out[i] = parts[i]
        return out

    def set_lamp_colour(index: int, colour: str) -> None:
        # No re-render: the select already shows the new symbol, and a
        # re-render would clear state["edits"] — a cosmetic click must never
        # cost the operator their unsaved changes.
        current = lamp_colours()
        current[index] = colour
        ctx.cfg.lamp_colours = ",".join(current)
        config_store.save(ctx.cfg)

    def wall_epoch() -> int:
        """This PC's wall clock as seconds since 1970, local — not UTC.

        The gateway keeps the time on the wall in front of the cabinet and
        knows nothing about timezones, so a schedule that says 03:00 means
        the 03:00 a pharmacist would recognise. Sending UTC here would make
        every schedule silently wrong by the offset.
        """
        now = datetime.now().astimezone()
        return int(now.timestamp() + now.utcoffset().total_seconds())

    async def sync_clock(snap) -> None:
        """Set the gateway's clock when it has none.

        The Opta loses the time whenever it loses power — the very event a
        scheduled reset exists to recover from — so the tool sets it on every
        read rather than leaving a schedule that quietly never runs.
        """
        if not snap or not snap.ok:
            return
        if snap.info.get("time.set") == "1":
            return
        res = await worker.gw_set_time(ctx.port(), wall_epoch())
        if res.ok:
            snap.info["time.set"] = "1"
            say(t("sch.synced"))
            ui.notify(t("sch.synced"), type="positive")
        else:
            say(f"clock not set: {res.note}")

    def adopt_hub_map(snap) -> None:
        """Take the cabinet's wiring from the gateway, which owns it.

        The tool uses the row -> channel map to decide which slots can be
        watched together cheaply (pick walkthrough batches, sweep order). A
        stale copy is not a wrong reading, only a slow one — but re-cabling
        happens during commissioning, and nobody should have to remember to
        tell the tool about it twice.
        """
        if not snap or not snap.ok:
            return
        text = snap.settings.get("bus.hub_map")
        if not text or text == lgs_map.format_hub_map():
            return
        try:
            lgs_map.set_hub_map(text)
        except ValueError as exc:
            say(f"hub map from gateway ignored: {exc}")
            return
        ctx.cfg.hub_map = text
        config_store.save(ctx.cfg)
        say(t("gw.hub_map_adopted", map=text))
        ui.notify(t("gw.hub_map_adopted", map=text), type="positive", timeout=5000)

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
        adopt_hub_map(snap)
        await sync_clock(snap)
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
        if await confirm(t("gw.defaults_title"), t("gw.defaults_body"),
                         t("gw.defaults")):
            await run_action("defaults")

    async def confirm_reboot() -> None:
        if await confirm(t("gw.reboot_title"), t("gw.reboot_body"),
                         t("gw.reboot"), danger_border=True):
            await run_action("reboot")

    detect_btn.on_click(do_detect)
    reload_btn.on_click(do_reload)
    save_btn.on_click(do_save)
    save_btn.set_visibility(False)
