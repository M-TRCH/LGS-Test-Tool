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
GRID_ROWS = 10
GRID_COLS = 8
GRID_IDS = tuple(r * 10 + c for r in range(1, GRID_ROWS + 1)
                 for c in range(1, GRID_COLS + 1))          # 11-18, 21-28, ... 101-108


@dataclass(frozen=True)
class CabinetLayout:
    """A product variant's module grid — the number in the LGS names is the
    module count (rows x cols)."""
    key: str
    label: str
    rows: int
    cols: int

    @property
    def ids(self) -> tuple:
        return tuple(r * 10 + c for r in range(1, self.rows + 1)
                     for c in range(1, self.cols + 1))

    @property
    def count(self) -> int:
        return self.rows * self.cols

    @property
    def detail(self) -> str:
        return (f"{self.rows} rows x {self.cols} columns — {self.count} modules "
                f"({self.ids[0]}-{self.ids[self.cols - 1]} … {self.ids[-self.cols]}-{self.ids[-1]})")


CABINET_LAYOUTS = (
    CabinetLayout("lgs80", "LGS type 80", 10, 8),
    CabinetLayout("lgs40", "LGS type 40", 10, 4),
    CabinetLayout("lgs56", "LGS type 56", 7, 8),
    CabinetLayout("smt", "SMT", 3, 4),
)

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

def dec_fw(raw: int, unit: str = "") -> str:
    """major*10000 + minor*100 + patch, so 30100 reads as v3.1.0.

    Firmware before v3.1.0 packed a ddmmy date here instead. Values whose
    minor or patch field is out of range are shown as that older date code, so
    a module still running one is not labelled with a nonsense version.
    """
    major, minor, patch = raw // 10000, (raw // 100) % 100, raw % 100
    if raw >= 10000 and minor < 50 and patch < 50:
        return f"{raw} (v{major}.{minor}.{patch})"
    s = str(raw).zfill(5)                       # legacy ddmmy date code
    return f"{raw} (legacy date {s[0:2]}/{s[2:4]}/*{s[4]})"

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
