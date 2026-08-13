"""Built-in SNTP server, so the tool itself can be the site's time source.

The gateway (fw >= v1.11.0) can re-learn its clock after a power cut by
querying an NTP server (`net.ntp`). Any server works — an AD domain
controller, w32time, chrony — but the zero-setup option is this one: the
tool is already running on the site's server for monitoring, so it answers
NTP too. One UDP socket, stateless, standard 48-byte SNTP replies from the
PC's own clock (in UTC, as NTP requires — the gateway applies its
`time.tz_min` itself).

Windows notes, surfaced in the UI when binding fails:
  - w32time holds UDP 123 while it runs; either stop it (`net stop w32time`)
    or serve on another port and set the gateway's `net.ntp_port` to match.
  - Windows Firewall must allow inbound UDP on the port for OTHER machines
    to reach us; the first-run firewall prompt only covered the web page's
    TCP listener.

The singleton lives for the process (like `modbus_worker.worker`); pages
render views over it. Start/stop from `app.on_startup`/`on_shutdown` in
main.py and from the card's toggle.
"""
from __future__ import annotations

import asyncio
import socket
import struct
import time

_NTP_EPOCH_OFFSET = 2208988800          # seconds between 1900 and 1970


def local_ip_toward(peer: str) -> str:
    """The local address the OS would use to reach `peer` — the right NIC's
    address on a multi-homed server. No packet is sent (UDP connect only)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((peer or "8.8.8.8", 1))
        return s.getsockname()[0]
    except OSError:
        return ""
    finally:
        s.close()


def _ts48(t: float) -> bytes:
    """A float epoch (Unix) as an 8-byte NTP timestamp."""
    t += _NTP_EPOCH_OFFSET
    sec = int(t)
    frac = int((t - sec) * (1 << 32))
    return struct.pack("!II", sec & 0xFFFFFFFF, frac & 0xFFFFFFFF)


class _NtpProtocol(asyncio.DatagramProtocol):
    def __init__(self, owner: "NtpServer") -> None:
        self._owner = owner
        self._transport: asyncio.DatagramTransport | None = None

    def connection_made(self, transport) -> None:  # type: ignore[override]
        self._transport = transport

    def datagram_received(self, data: bytes, addr) -> None:
        if len(data) < 48 or self._transport is None:
            return
        # Mode 3 (client) or anything client-ish gets a mode-4 reply carrying
        # the client's own version number back.
        vn = (data[0] >> 3) & 0x07
        now = _ts48(time.time())        # UTC — time.time() is Unix/UTC epoch
        reply = bytearray(48)
        reply[0] = (0 << 6) | (vn << 3) | 4     # LI 0, client's VN, mode 4
        reply[1] = 2                            # stratum 2: "from a real clock"
        reply[2] = data[2] or 6                 # poll interval, echoed
        reply[3] = 0xEC                         # precision ~1 µs, close enough
        reply[12:16] = b"LOCL"                  # reference: the local clock
        reply[16:24] = now                      # reference timestamp
        reply[24:32] = data[40:48]              # originate = client's transmit
        reply[32:40] = now                      # receive
        reply[40:48] = now                      # transmit
        self._transport.sendto(bytes(reply), addr)
        self._owner.served += 1
        self._owner.last_client = str(addr[0])


class NtpServer:
    """Process-wide singleton (see `server` below)."""

    def __init__(self) -> None:
        self._transport: asyncio.DatagramTransport | None = None
        self.port = 0
        self.served = 0
        self.last_client = ""
        self.error = ""                 # human-readable bind failure, "" = fine

    @property
    def running(self) -> bool:
        return self._transport is not None

    async def start(self, port: int) -> bool:
        """Bind and serve. False (with .error set) when the port is taken or
        refused — never raises: a dead NTP card must not cost the app."""
        await self.stop()
        self.error = ""
        try:
            loop = asyncio.get_running_loop()
            self._transport, _ = await loop.create_datagram_endpoint(
                lambda: _NtpProtocol(self), local_addr=("0.0.0.0", int(port)))
        except OSError as exc:
            self.error = str(exc)
            self._transport = None
            return False
        self.port = int(port)
        return True

    async def stop(self) -> None:
        if self._transport is not None:
            self._transport.close()
            self._transport = None


server = NtpServer()
