"""Small persisted app config (last transport/port/ip/id) in data/config.json.

`LGS_TT_DATA_DIR` overrides the data directory (used by the Docker image,
where /app/data is the volume mount).
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, fields
from pathlib import Path


@dataclass
class AppConfig:
    transport: str = "rtu"               # "rtu" | "tcp"
    com_port: str = ""                   # "" = auto (prefer the Opta bridge)
    baud: int = 9600
    tcp_host: str = "192.168.0.178"
    tcp_port: int = 502
    device_id: int = 11
    monitor_interval_s: float = 1.0
    theme: str = "light"
    language: str = "en"                 # "en" | "th"
    cubeprog_path: str = ""              # "" = look in the usual install dirs
    dfu_util_path: str = ""              # "" = beside the exe, then PlatformIO
    advanced_mode: bool = False          # False = everyday pages only
    # Which cabinet variant the tool is pointed at — a key of
    # lgs_map.CABINET_LAYOUTS or "custom", picked in the header. Every
    # whole-cabinet action (installation check, firmware survey, gateway
    # sweep size) follows it. A literal rather than an import: this module
    # deliberately imports nothing from the app, and lgs_map falls back to
    # its default for a key it does not know.
    cabinet: str = "lgs80"
    # The custom shape, as slots per row from the top: "8,8,8,4,4,4,4,8,8,8".
    # Only read while cabinet == "custom"; kept when switching away, so
    # coming back does not mean building the shape again.
    cabinet_custom: str = ""
    # Row -> RS485 hub channel as the gateway reports it ("1,1,1,1,1,2,3,4,5,6").
    # "" = the built-in default. Stored so a re-cabled cabinet stays correct
    # across restarts; the Gateway tab refreshes it whenever it reads the
    # gateway, which is the authority on the wiring.
    hub_map: str = ""
    # Which colour of lamp is fitted to gateway outputs 1-4 ("none" for an
    # output carrying something other than a lamp, such as the shelf's
    # power). The gateway drives outputs and knows nothing about colours;
    # this is the tool's own note so the Gateway tab draws the panel as it
    # looks.
    lamp_colours: str = "none,green,amber,red"
    # Built-in SNTP server (app/ntp_server.py): serve time to gateways from
    # this PC. Off by default — a bench laptop should not answer NTP; the
    # site's server, where the tool is left running, turns it on once.
    # 123 is the standard port; w32time may hold it on Windows, in which
    # case pick another and set the gateway's net.ntp_port to match.
    ntp_enabled: bool = False
    ntp_port: int = 123


def data_dir() -> Path:
    env = os.environ.get("LGS_TT_DATA_DIR")
    if env:
        d = Path(env)
    elif getattr(sys, "frozen", False):
        # packaged .exe: __file__ points into PyInstaller's temp extraction dir,
        # so keep data next to the executable instead
        d = Path(sys.executable).resolve().parent / "data"
    else:
        d = Path(__file__).resolve().parent.parent / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _config_path() -> Path:
    return data_dir() / "config.json"


def load() -> AppConfig:
    try:
        raw = json.loads(_config_path().read_text(encoding="utf-8"))
        known = {f.name for f in fields(AppConfig)}
        return AppConfig(**{k: v for k, v in raw.items() if k in known})
    except Exception:
        return AppConfig()


def save(cfg: AppConfig) -> None:
    path = _config_path()
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        pass  # config persistence is best-effort
