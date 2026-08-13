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

DEFAULT_TCP_HOST = "192.168.0.178"   # Opta gateway static IP
DEFAULT_TCP_PORT = 502

# A master talking to a cabinet behind the RS485 switch hub has to outlast a
# channel change. The hub swallows the first frame on a new channel and stays
# deaf for ~2.2 s; the gateway repairs that by HOLDING the request until the
# channel opens (up to bus.hub_budget_ms) so the reply merely arrives late.
# A client that gives up before the gateway does gets the worst of both — the
# read fails AND the late answer desynchronises the reads behind it: measured
# on the bench at a 1 s timeout, one crossing took the next three modules with
# it. 3.5 s clears a 2600 ms budget with margin. This is exactly the rule the
# hospital's server has to follow, so the tool had better follow it too.
HUB_SAFE_TIMEOUT_S = 3.5


@dataclass
class RtuSettings:
    port: str
    baud: int = 9600
    timeout_s: float = HUB_SAFE_TIMEOUT_S     # framing fixed 8N1

    def describe(self) -> str:
        return f"RTU {self.port} @{self.baud} 8N1"


@dataclass
class TcpSettings:
    host: str = DEFAULT_TCP_HOST
    port: int = DEFAULT_TCP_PORT
    timeout_s: float = HUB_SAFE_TIMEOUT_S

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


# A probe must outlast the gateway/bridge's own wait for the slave
# (TIMEOUT_FIRST_BYTE_MS = 300 ms in LGS-Gateway-Arduino-Opta). If the PC gives
# up first, the bridge is still holding the line when the next probe starts and
# replies land after their client is gone — devices then read as "not there".
PROBE_TIMEOUT_S = 0.45


def make_scan_probe_client(s: TransportSettings):
    """Short-timeout, no-retry client for ID scanning. RTU probes use a FRESH
    client per ID (a persistent serial client wedges after a no-response)."""
    if isinstance(s, RtuSettings):
        return make_client(RtuSettings(s.port, s.baud, timeout_s=PROBE_TIMEOUT_S), retries=0)
    return make_client(TcpSettings(s.host, s.port, timeout_s=PROBE_TIMEOUT_S), retries=0)
