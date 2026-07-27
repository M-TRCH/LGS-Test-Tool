"""Transport settings and pymodbus client construction (RTU serial / TCP).

Everything pymodbus-version-sensitive is isolated here: the `device_id=` kwarg
is used by the worker (pymodbus >= 3.9), and the raw-frame trace hook degrades
gracefully if the installed version does not accept `trace_packet`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Union

from pymodbus.client import ModbusSerialClient, ModbusTcpClient
from serial.tools import list_ports

OPTA_VID = 0x2341
OPTA_PID = 0x0164

DEFAULT_TCP_HOST = "192.168.0.178"   # Opta gateway static IP (single client only!)
DEFAULT_TCP_PORT = 502


@dataclass
class RtuSettings:
    port: str
    baud: int = 9600
    timeout_s: float = 1.0            # framing fixed 8N1

    def describe(self) -> str:
        return f"RTU {self.port} @{self.baud} 8N1"


@dataclass
class TcpSettings:
    host: str = DEFAULT_TCP_HOST
    port: int = DEFAULT_TCP_PORT
    timeout_s: float = 1.0

    def describe(self) -> str:
        return f"TCP {self.host}:{self.port}"


TransportSettings = Union[RtuSettings, TcpSettings]


@dataclass(frozen=True)
class PortInfo:
    device: str
    description: str
    is_opta: bool

    @property
    def label(self) -> str:
        tag = " — Arduino Opta (USB-RS485 bridge)" if self.is_opta else ""
        return f"{self.device} — {self.description}{tag}" if not self.is_opta else f"{self.device}{tag}"


def list_com_ports() -> list[PortInfo]:
    out = []
    for p in list_ports.comports():
        out.append(PortInfo(p.device, p.description or "?",
                            p.vid == OPTA_VID and p.pid == OPTA_PID))
    out.sort(key=lambda p: (not p.is_opta, p.device))
    return out


def find_opta_port() -> Optional[str]:
    for p in list_com_ports():
        if p.is_opta:
            return p.device
    return None


def make_client(s: TransportSettings, *,
                trace_packet: Optional[Callable[[bool, bytes], bytes]] = None,
                timeout_s: Optional[float] = None,
                retries: int = 1):
    """Build a sync pymodbus client. trace_packet(sending, data) captures raw
    frames when the installed pymodbus supports it; silently dropped otherwise."""
    timeout = timeout_s if timeout_s is not None else s.timeout_s
    kwargs = dict(timeout=timeout, retries=retries)
    if trace_packet is not None:
        kwargs["trace_packet"] = trace_packet
    try:
        return _construct(s, kwargs)
    except TypeError:
        # older/newer pymodbus without trace_packet — degrade to no hex capture
        kwargs.pop("trace_packet", None)
        return _construct(s, kwargs)


def _construct(s: TransportSettings, kwargs: dict):
    if isinstance(s, RtuSettings):
        return ModbusSerialClient(port=s.port, baudrate=s.baud,
                                  bytesize=8, parity="N", stopbits=1, **kwargs)
    return ModbusTcpClient(host=s.host, port=s.port, **kwargs)


def make_scan_probe_client(s: TransportSettings):
    """Short-timeout, no-retry client for ID scanning. RTU probes use a FRESH
    client per ID (a persistent serial client wedges after a no-response)."""
    if isinstance(s, RtuSettings):
        return make_client(RtuSettings(s.port, s.baud, timeout_s=0.25), retries=0)
    # via the Opta gateway a missing slave costs its 300 ms first-byte timeout
    return make_client(TcpSettings(s.host, s.port, timeout_s=0.6), retries=0)
