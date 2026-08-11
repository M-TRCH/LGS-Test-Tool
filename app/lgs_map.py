"""LGS R5.0 Modbus address map — mirrors LGS-Standard-Module/src/svc/modbus_map.h.

Single source of truth for every address, decoder, and coil safety class used
by the tool. Keep in lock-step with the firmware header; the self-check block
at the bottom freezes the wire contract the same way its static_asserts do.

Run `python -m app.lgs_map` to dump the full table (no hardware needed).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

# ── Constants ──────────────────────────────────────────────────────────────
DEVICE_TYPES = {10: "STANDARD", 20: "NARCOTIC", 30: "LITE", 40: "DELIVERY"}
FUNCTION_MODES = {0: "RUN", 1: "DEMO", 2: "SET_ID", 3: "FACTORY_RESET"}
BAUD_WHITELIST = (9600, 19200, 38400, 57600)
FACTORY_DEFAULT_ID = 247
SETID_TEMP_ID = 246         # temporary ID a module adopts while its switch is in
                            # SET_ID mode — addressable as a target, NEVER assignable
SENSOR_FAULT = 0x8000       # regs 20/21 report this after >=3 failed sensor reads
LATCH_COOLDOWN_S = 2.2      # firmware enforces >=2000 ms between unlock pulses
INTER_TXN_S = 0.025         # RS485 breather between transactions

# ── RS485 switch hub ───────────────────────────────────────────────────────
# The bus can leave the Opta through an 8-channel RS485 switch hub, which
# follows traffic: the first frame on a new channel makes it switch, that
# frame is swallowed, and the channel stays deaf for about two seconds
# (measured on the cabinet). So slots that share a channel can be watched
# together for about 100 ms each, while every extra channel in the set adds
# ~2 s to each sweep. Which slots share a channel is therefore worth knowing.
#
# Which row hangs off which channel is wiring, and the wiring changes — rows
# 1-5 were re-cabled onto a single channel on 2026-08-10. The gateway holds
# the authoritative map at `bus.hub_map`; this is the tool's copy of it, kept
# in step by the Gateway tab whenever it reads the gateway. The default below
# is the original cabinet: rows 1-8 on channels 1-8, rows 9-10 doubled onto
# channels 1-2.
#
# A channel of 0 means "not behind a hub". An all-zero map therefore says
# there is no hub at all, and every slot can be watched together.
HUB_CHANNELS = 8
INTER_CH_S = 0.03           # brief settle; the retries do the real work
HUB_WAKE_TRIES = 6          # attempts allowed on the first txn after a switch
HUB_WAKE_GAP_S = 0.04       # between those attempts
HUB_ROWS = 10               # slave IDs 11-108; same span as GRID_ROWS below

_HUB_MAP = [((r - 1) % HUB_CHANNELS) + 1 for r in range(1, HUB_ROWS + 1)]


def hub_map() -> list:
    """The tool's row -> channel map, row 1 first."""
    return list(_HUB_MAP)


def format_hub_map() -> str:
    return ",".join(str(v) for v in _HUB_MAP)


def parse_hub_map(text: str) -> list:
    """Read a `bus.hub_map` value ("1,1,1,1,1,2,3,4,5,6") into a list.

    Raises ValueError on anything that is not a channel, so a garbled console
    reply can never quietly become a wrong map.
    """
    parts = [p.strip() for p in str(text).replace(";", ",").split(",") if p.strip()]
    if not parts:
        raise ValueError("empty hub map")
    out = []
    for p in parts:
        if not p.isdigit() or int(p) > HUB_CHANNELS:
            raise ValueError(f"{p!r} is not a hub channel (0-{HUB_CHANNELS})")
        out.append(int(p))
    return out[:HUB_ROWS] + [0] * max(0, HUB_ROWS - len(out))


def set_hub_map(values) -> list:
    """Adopt a row -> channel map. Accepts a list or a console string."""
    global _HUB_MAP
    if isinstance(values, str):
        values = parse_hub_map(values)
    values = list(values)[:HUB_ROWS]
    _HUB_MAP = values + [0] * max(0, HUB_ROWS - len(values))
    return list(_HUB_MAP)


def hub_channel(device_id: int) -> int:
    """Which hub channel a module hangs off, or 0 when it is not behind one."""
    row = device_id // 10
    if 1 <= row <= len(_HUB_MAP):
        return _HUB_MAP[row - 1]
    return 0


GRID_ROWS = 10
GRID_COLS = 8
GRID_IDS = tuple(r * 10 + c for r in range(1, GRID_ROWS + 1)
                 for c in range(1, GRID_COLS + 1))          # 11-18, 21-28, ... 101-108


@dataclass(frozen=True)
class CabinetLayout:
    """A product variant's module grid.

    The number in an LGS name is the slot count. Most variants are a plain
    rows x cols block, but LGS 64 is not — its middle rows are half width —
    so a layout may instead carry the exact ID list.
    """
    key: str
    label: str
    rows: int
    cols: int
    ids_override: tuple = ()
    # The gateway's `panel.cabinet` value for this variant, "" when the
    # gateway has no such size (SMT is a bench rig, not a cabinet).
    panel_cabinet: str = ""

    @property
    def ids(self) -> tuple:
        if self.ids_override:
            return self.ids_override
        return tuple(r * 10 + c for r in range(1, self.rows + 1)
                     for c in range(1, self.cols + 1))

    @property
    def count(self) -> int:
        return len(self.ids)

    @property
    def row_count(self) -> int:
        """How many rows this cabinet actually has.

        Read from the IDs, not from `rows`: a layout may carry an explicit ID
        list instead (LGS 64 does), and not every LGS is ten rows tall.
        """
        return max(i // 10 for i in self.ids) if self.ids else 0


# LGS 64: not a rectangle. Rows 1-3 and 8-10 are full width, rows 4-7 carry
# only the first four columns. Early on this cabinet was misdescribed as a
# 7x8 block (11-78) under the name "LGS 56", which selected sixteen slots
# that do not exist on it and missed rows 8-10 entirely — so "select LGS 56"
# on the Installation Check page checked the wrong cabinet. Spelled out per
# row: the shape cannot be derived from a count.
#
# (Today's REAL LGS type 56 below is a different thing: a product that
# genuinely is the plain 7x8 block. The bug was the name on the wrong
# cabinet, not the shape itself.)
_LGS64_IDS = tuple(
    [r * 10 + c for r in (1, 2, 3) for c in range(1, 9)]
    + [r * 10 + c for r in (4, 5, 6, 7) for c in range(1, 5)]
    + [r * 10 + c for r in (8, 9, 10) for c in range(1, 9)]
)

CABINET_LAYOUTS = (
    CabinetLayout("lgs80", "LGS type 80", 10, 8, panel_cabinet="80"),
    CabinetLayout("lgs64", "LGS type 64", 0, 0, ids_override=_LGS64_IDS,
                  panel_cabinet="64"),
    # No gateway code on purpose: the firmware hard-codes only 40/64/80, and
    # panel.shape (gateway >= 1.9.0) exists precisely so a newer variant
    # does not force a firmware release — the tool offers "8,8,8,8,8,8,8".
    CabinetLayout("lgs56", "LGS type 56", 7, 8),
    CabinetLayout("lgs40", "LGS type 40", 10, 4, panel_cabinet="40"),
    # The key stays "smt" — it is what saved configs hold.
    CabinetLayout("smt", "SMT type 12", 3, 4),
)

# The cabinet the tool assumes until somebody picks one (header, persisted in
# AppConfig.cabinet). The full grid: on a smaller cabinet an over-wide
# selection fails loudly — red unanswered slots — where a smaller default
# would skip real modules in silence.
DEFAULT_CABINET_KEY = "lgs80"

# A shape of the operator's own: how many rows, and how many slots each row
# carries — per row, because real cabinets are not rectangles (LGS 64's
# middle rows are half width). Stored in AppConfig.cabinet_custom as a comma
# list of widths, top row first: "8,8,8,4,4,4,4,8,8,8".
CUSTOM_CABINET_KEY = "custom"


def parse_custom_widths(text: str) -> list:
    """`"8,8,4"` -> [8, 8, 4]. Raises ValueError with a reason on anything
    that is not 1-10 rows of 0-8 slots with at least one slot somewhere."""
    parts = [p.strip() for p in str(text or "").replace(";", ",").split(",")
             if p.strip() != ""]
    if not parts or len(parts) > GRID_ROWS:
        raise ValueError(f"1-{GRID_ROWS} rows")
    if not all(p.isdigit() and 0 <= int(p) <= GRID_COLS for p in parts):
        raise ValueError(f"0-{GRID_COLS} slots per row")
    widths = [int(p) for p in parts]
    if not any(widths):
        raise ValueError("at least one slot")
    return widths


def format_custom_widths(widths) -> str:
    return ",".join(str(int(w)) for w in widths)


def custom_layout(widths) -> CabinetLayout:
    """A CabinetLayout for per-row widths. A width of 0 keeps the row's IDs
    out entirely — the row exists in the wall, not on the bus."""
    ids = tuple(r * 10 + c
                for r, w in enumerate(widths, 1)
                for c in range(1, int(w) + 1))
    return CabinetLayout(CUSTOM_CABINET_KEY, f"Custom ({len(ids)})", 0, 0,
                         ids_override=ids)


def layout_by_key(key: str) -> CabinetLayout:
    """The layout for a stored key, falling back to the default so a stale
    or hand-edited config can never leave the tool without a cabinet."""
    for layout in CABINET_LAYOUTS:
        if layout.key == key:
            return layout
    return layout_by_key(DEFAULT_CABINET_KEY)


def layout_widths(layout: CabinetLayout) -> list:
    """Per-row widths derived from the ID list, trailing absent rows dropped.

    Sound for every layout this module builds, because their rows are always
    columns 1..w — which is also the only shape the gateway's `panel.shape`
    can express.
    """
    widths = []
    for r in range(1, GRID_ROWS + 1):
        cols = [i % 10 for i in layout.ids if i // 10 == r]
        widths.append(max(cols) if cols else 0)
    while widths and widths[-1] == 0:
        widths.pop()
    return widths


def same_shape(a_text: str, b_text: str) -> bool:
    """Do two width lists describe the same shape? "0"/blank/garbage all
    read as "no shape", and trailing zeros do not count."""
    def norm(text):
        try:
            w = parse_custom_widths(text)
        except ValueError:
            w = []
        w = list(w)[:GRID_ROWS]
        return w + [0] * (GRID_ROWS - len(w))
    return norm(a_text) == norm(b_text)


def resolve_cabinet(key: str, custom_text: str) -> CabinetLayout:
    """The cabinet the tool is pointed at: a preset by key, or the custom
    shape. An unusable custom string falls back to the default preset —
    never to nothing."""
    if key == CUSTOM_CABINET_KEY:
        try:
            return custom_layout(parse_custom_widths(custom_text))
        except ValueError:
            return layout_by_key(DEFAULT_CABINET_KEY)
    return layout_by_key(key)

HEALTH_BITS = ("AT24 EEPROM", "OLED", "Room sensor", "Board sensor")     # bit0..3, set = OK
HEALTH_LATCH_BIT = 4                                                     # bit4 = latch locked (state, not health)
RESET_CAUSES = ("IWDG", "Software", "Power-on", "NRST pin", "WWDG", "Low-power", "Option-byte")

# ── Address formulas (mirror modbus_map.h helpers) ─────────────────────────
def preset_cfg_base(n: int) -> int:      # +0 brightness +1 R +2 G +3 B +4 max-on
    return 100 + 10 * n

def coil_enable(n: int) -> int:
    return 1000 + n

def coil_display(n: int) -> int:
    return 1010 + n

def coil_latch(n: int) -> int:
    return 1020 + n

def coil_latch_display(n: int) -> int:
    return 1030 + n

def stats_count(n: int) -> int:
    return 200 + 10 * n

def stats_time(n: int) -> int:
    return 201 + 10 * n

# ── Decoders (raw int -> human string) ─────────────────────────────────────
def dec_plain(raw: int, unit: str = "") -> str:
    return f"{raw}{(' ' + unit) if unit else ''}"

def dec_temp(raw: int, unit: str = "") -> str:
    if raw == SENSOR_FAULT:
        return "SENSOR FAULT (0x8000)"
    c = raw - 65536 if raw >= 32768 else raw    # signed int16
    return f"{c / 100.0:.2f} °C"

def dec_device_type(raw: int, unit: str = "") -> str:
    return f"{raw} = {DEVICE_TYPES.get(raw, '?')}"

def fw_short(raw: int) -> str:
    """Just the version, for grouping modules and labelling groups.

    major*10000 + minor*100 + patch, so 30100 reads as v3.1.0. Firmware
    before v3.1.0 packed a ddmmy date here instead; values whose minor or
    patch field is out of range are shown as that older date code, so a
    module still running one is not labelled with a nonsense version.
    """
    major, minor, patch = raw // 10000, (raw // 100) % 100, raw % 100
    if raw >= 10000 and minor < 50 and patch < 50:
        return f"v{major}.{minor}.{patch}"
    s = str(raw).zfill(5)                       # legacy ddmmy date code
    return f"legacy date {s[0:2]}/{s[2:4]}/*{s[4]}"

def dec_fw(raw: int, unit: str = "") -> str:
    return f"{raw} ({fw_short(raw)})"

def dec_hw(raw: int, unit: str = "") -> str:
    return f"{raw} (R{raw // 100}.{(raw // 10) % 10})"

def dec_baud(raw: int, unit: str = "") -> str:
    ok = "" if raw in BAUD_WHITELIST else "  (NOT in whitelist!)"
    return f"{raw} bps{ok}"

def dec_mode(raw: int, unit: str = "") -> str:
    return f"{raw} = {FUNCTION_MODES.get(raw, '?')}"

def dec_preset(raw: int, unit: str = "") -> str:
    return "0 = off" if raw == 0 else f"preset {raw}"

def dec_uptime(hi: int, lo: int) -> str:
    total = (hi << 16) | lo
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m:02d}m {s:02d}s"

def dec_current(raw: int, unit: str = "") -> str:
    """Input current from reg 22 (firmware >= v3.2.0; older modules read 0)."""
    return f"{raw} mA" if raw < 1000 else f"{raw} mA ({raw / 1000:.2f} A)"

def join_uid(words) -> str:
    """Regs 12-17 -> the module's serial, one number everywhere.

    Hex-concatenating the six registers (hi word first per 32-bit UID word)
    reproduces exactly what stlink.read_uid() reads over SWD and what
    commission_log.csv stores in device_uid — so a board on the bus can be
    matched to its commissioning record even after someone changed its ID.
    """
    return "".join(f"{w:04X}" for w in words)

def decode_health(raw: int) -> list[tuple[str, bool]]:
    """[(subsystem, ok)] for bits 0-3. Bit 4 (latch) is a state — use is_latch_locked()."""
    return [(name, bool(raw & (1 << i))) for i, name in enumerate(HEALTH_BITS)]

def is_latch_locked(health_raw: int) -> bool:
    return bool(health_raw & (1 << HEALTH_LATCH_BIT))

def decode_reset_cause(raw: int) -> list[str]:
    return [name for i, name in enumerate(RESET_CAUSES) if raw & (1 << i)]

# ── Register / coil definitions ────────────────────────────────────────────
@dataclass(frozen=True)
class RegDef:
    addr: int
    name: str
    unit: str
    decoder: Callable[[int, str], str]
    writable: bool = False
    persisted: bool = False      # R/W(F): survives via coil 503 (AT24 EEPROM)

class CoilClass(Enum):
    NORMAL = "normal"            # safe momentary/self-clearing command
    STATE = "state"              # holds its value (ring/display enables)
    LATCH = "latch"              # fires the solenoid — cooldown-gated
    DANGER = "danger"            # reboot/wipe — Danger tab only
    FORBIDDEN = "forbidden"      # OTA session coils — this tool never writes them

@dataclass(frozen=True)
class CoilDef:
    addr: int
    name: str
    cls: CoilClass
    self_clearing: bool = False

REGISTERS: list[RegDef] = [
    RegDef(0,   "Device Type",        "",    dec_device_type),
    RegDef(1,   "Firmware Version",   "",    dec_fw),
    RegDef(2,   "Hardware Version",   "",    dec_hw),
    RegDef(3,   "Baud Rate",          "bps", dec_baud, writable=True, persisted=True),
    RegDef(4,   "Slave ID",           "",    dec_plain, writable=True, persisted=True),
    RegDef(5,   "Uptime (hi)",        "",    dec_plain),
    RegDef(6,   "Uptime (lo)",        "s",   dec_plain),
    RegDef(7,   "Boot Counter",       "",    dec_plain),
    RegDef(8,   "Last Reset Cause",   "",    dec_plain),
    RegDef(9,   "Health Bits",        "",    dec_plain),
    RegDef(10,  "Function Mode",      "",    dec_mode),
    RegDef(11,  "Active Preset",      "",    dec_preset),
    RegDef(12,  "UID 1/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(13,  "UID 2/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(14,  "UID 3/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(15,  "UID 4/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(16,  "UID 5/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(17,  "UID 6/6",            "",    lambda raw, unit="": f"0x{raw:04X}"),
    RegDef(18,  "Button Presses",     "",    dec_plain),
    RegDef(19,  "Button Held",        "",    dec_plain),
    RegDef(20,  "Room Temp",          "°C",  dec_temp),
    RegDef(21,  "Board Temp",         "°C",  dec_temp),
    RegDef(22,  "Input Current",      "mA",  dec_current),
    RegDef(40,  "Time After Unlock",  "s",   dec_plain),
    RegDef(41,  "Latch Locked",       "",    dec_plain),
    RegDef(60,  "Display Number",     "",    dec_plain, writable=True),
    RegDef(80,  "Unlock Delay",       "ms",  dec_plain, writable=True, persisted=True),
    RegDef(190, "Global Brightness",  "%",   dec_plain, writable=True),   # fans out to all presets
    RegDef(194, "Global Max On-Time", "s",   dec_plain, writable=True),   # fans out to all presets
    RegDef(200, "Total On Count",     "",    dec_plain),
    RegDef(201, "Total On Time",      "s",   dec_plain),
]

_PRESET_FIELDS = (("Brightness", "%"), ("Red", ""), ("Green", ""), ("Blue", ""), ("Max On-Time", "s"))
for _n in range(1, 9):
    for _k, (_fname, _funit) in enumerate(_PRESET_FIELDS):
        REGISTERS.append(RegDef(preset_cfg_base(_n) + _k, f"Preset {_n} {_fname}", _funit,
                                dec_plain, writable=True, persisted=True))
    REGISTERS.append(RegDef(stats_count(_n), f"Preset {_n} On Count", "", dec_plain))
    REGISTERS.append(RegDef(stats_time(_n), f"Preset {_n} On Time", "s", dec_plain))
REGISTERS.sort(key=lambda r: r.addr)

COILS: list[CoilDef] = [
    CoilDef(500,  "Factory Reset (arm)",       CoilClass.DANGER, self_clearing=True),
    CoilDef(501,  "Apply Reset (keep ID)",     CoilClass.DANGER, self_clearing=True),
    CoilDef(502,  "Apply Reset (all data)",    CoilClass.DANGER, self_clearing=True),
    CoilDef(503,  "Write to EEPROM (+reboot)", CoilClass.DANGER, self_clearing=True),
    CoilDef(504,  "Software Reset",            CoilClass.DANGER, self_clearing=True),
    CoilDef(505,  "OTA Enter",                 CoilClass.FORBIDDEN, self_clearing=True),
    CoilDef(506,  "OTA Finalize",              CoilClass.FORBIDDEN, self_clearing=True),
    CoilDef(507,  "OTA Apply",                 CoilClass.FORBIDDEN, self_clearing=True),
    CoilDef(508,  "OTA Abort",                 CoilClass.FORBIDDEN, self_clearing=True),
    CoilDef(509,  "Identify (blink white 5s)", CoilClass.NORMAL, self_clearing=True),
    CoilDef(510,  "Clear Statistics",          CoilClass.DANGER, self_clearing=True),
    CoilDef(511,  "All Off (ring + display)",  CoilClass.NORMAL, self_clearing=True),
    CoilDef(1010, "Display Enable",            CoilClass.STATE),
    CoilDef(1019, "Latch Force Trigger",       CoilClass.LATCH, self_clearing=True),
    CoilDef(1020, "Latch Trigger (Safety)",    CoilClass.LATCH, self_clearing=True),
]
for _n in range(1, 9):
    COILS.append(CoilDef(coil_enable(_n), f"Enable Preset {_n}", CoilClass.STATE))
    COILS.append(CoilDef(coil_display(_n), f"Preset {_n} + Display", CoilClass.STATE))
    COILS.append(CoilDef(coil_latch(_n), f"Preset {_n} + Latch", CoilClass.LATCH, self_clearing=True))
    COILS.append(CoilDef(coil_latch_display(_n), f"Preset {_n} + Latch + Display",
                         CoilClass.LATCH, self_clearing=True))
COILS.sort(key=lambda c: c.addr)

REG_BY_ADDR: dict[int, RegDef] = {r.addr: r for r in REGISTERS}
COIL_BY_ADDR: dict[int, CoilDef] = {c.addr: c for c in COILS}


def classify_coil(addr: int) -> CoilClass:
    """Safety class for ANY coil address, listed or not (unknown -> NORMAL)."""
    c = COIL_BY_ADDR.get(addr)
    if c is not None:
        return c.cls
    if 505 <= addr <= 508:
        return CoilClass.FORBIDDEN
    if addr in (500, 501, 502, 503, 504, 510):
        return CoilClass.DANGER
    if addr in (1019, 1020) or 1021 <= addr <= 1028 or 1031 <= addr <= 1038:
        return CoilClass.LATCH
    return CoilClass.NORMAL


def is_latch_coil(addr: int) -> bool:
    return classify_coil(addr) is CoilClass.LATCH


def decode_register(addr: int, raw: int) -> str:
    r = REG_BY_ADDR.get(addr)
    return r.decoder(raw, r.unit) if r else str(raw)


def valid_target_id(device_id: int) -> bool:
    """IDs addressable on the bus (246 = a module currently in SET_ID mode)."""
    return 1 <= device_id <= 247


def valid_assignable_id(device_id: int) -> bool:
    """IDs that may be persisted into reg 4 (246 is the SET_ID temp ID — never assign)."""
    return (1 <= device_id <= 245) or device_id == FACTORY_DEFAULT_ID


# ── Wire-contract self-check (mirrors the header's static_asserts) ─────────
assert preset_cfg_base(1) == 110 and preset_cfg_base(8) == 180
assert coil_enable(1) == 1001 and coil_enable(8) == 1008
assert coil_display(1) == 1011 and coil_display(8) == 1018
assert coil_latch(1) == 1021 and coil_latch(8) == 1028
assert coil_latch_display(1) == 1031 and coil_latch_display(8) == 1038
assert stats_count(8) == 280 and stats_time(8) == 281
assert GRID_IDS[0] == 11 and GRID_IDS[-1] == 108 and len(GRID_IDS) == 80
assert all(valid_assignable_id(i) for i in GRID_IDS)
for _layout in CABINET_LAYOUTS:                 # every variant fits inside the full grid
    assert set(_layout.ids) <= set(GRID_IDS) and len(_layout.ids) == _layout.count
    # The gateway code, when a variant has one, IS the slot count — the LGS
    # name and panel.cabinet share their meaning by definition.
    assert not _layout.panel_cabinet or int(_layout.panel_cabinet) == _layout.count
assert layout_by_key(DEFAULT_CABINET_KEY).key == DEFAULT_CABINET_KEY
assert layout_by_key("nonsense").key == DEFAULT_CABINET_KEY   # stale config falls back
# The custom shape: LGS 64 spelled as widths must reproduce the real layout,
# and a broken custom string must fall back to the default, never to nothing.
assert custom_layout(parse_custom_widths("8,8,8,4,4,4,4,8,8,8")).ids == _LGS64_IDS
assert resolve_cabinet(CUSTOM_CABINET_KEY, "3,0,5").ids == (11, 12, 13, 31, 32, 33, 34, 35)
assert resolve_cabinet(CUSTOM_CABINET_KEY, "garbage").key == DEFAULT_CABINET_KEY
assert resolve_cabinet("lgs40", "").count == 40
assert not custom_layout([4] * 3).panel_cabinet          # custom never maps to the gateway
# Widths round-trip: a layout's derived widths rebuild its exact ID list,
# which is what lets the tool hand any layout to the gateway's panel.shape.
for _layout in CABINET_LAYOUTS:
    assert custom_layout(layout_widths(_layout)).ids == _layout.ids
assert same_shape("8,8,4,0,0", "8,8,4") and not same_shape("8,8", "8,8,1")
assert same_shape("0", "") and same_shape("garbage", "0")
# LGS 56 is the plain 7x8 block 11-78 — the shape the old misnamed "LGS 56"
# wrongly claimed for the 64 cabinet. Pin it so the two are never confused.
_l56 = layout_by_key("lgs56")
assert _l56.count == 56 and _l56.ids[0] == 11 and _l56.ids[-1] == 78
assert not _l56.panel_cabinet and layout_widths(_l56) == [8] * 7
assert valid_target_id(SETID_TEMP_ID) and not valid_assignable_id(SETID_TEMP_ID)
assert not valid_target_id(0) and valid_target_id(247)
assert classify_coil(505) is CoilClass.FORBIDDEN
assert classify_coil(503) is CoilClass.DANGER
assert classify_coil(1021) is CoilClass.LATCH
assert classify_coil(1001) is CoilClass.STATE
assert classify_coil(509) is CoilClass.NORMAL
assert len(REGISTERS) == len(REG_BY_ADDR) and len(COILS) == len(COIL_BY_ADDR)  # no dup addrs
assert all(i in REG_BY_ADDR for i in range(12, 20)) and 22 in REG_BY_ADDR  # v3.2.0 regs
# Byte-order contract with the bench: board C's real UID, read both ways.
assert join_uid((0x0058, 0x0033, 0x3135, 0x5103, 0x3135, 0x3730)) \
    == "005800333135510331353730"


if __name__ == "__main__":
    print(f"LGS R5.0 map — {len(REGISTERS)} registers, {len(COILS)} coils\n")
    print("HOLDING REGISTERS (FC03/FC06)")
    for r in REGISTERS:
        flags = ("W" if r.writable else "-") + ("F" if r.persisted else "-")
        print(f"  {r.addr:>5}  [{flags}]  {r.name}")
    print("\nCOILS (FC01/FC05)")
    for c in COILS:
        sc = "self-clear" if c.self_clearing else "state"
        print(f"  {c.addr:>5}  [{c.cls.value:<9}] [{sc:<10}] {c.name}")
    print("\nself-check: all wire-contract asserts passed")
