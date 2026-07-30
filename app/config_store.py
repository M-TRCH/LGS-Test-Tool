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
