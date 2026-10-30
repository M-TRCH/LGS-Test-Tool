"""Module page backend: read one module's status, drive its coils.

Goes through the cabinet's gateway (Modbus TCP -> RTU) in one short session
per call. The safety rules are the classic tool's, applied on the server so
no page can talk its way around them: OTA coils (505-508) are never written
here, danger coils (reboot / wipe) are not reachable from this API at all, and
an unlock (latch) is refused for LATCH_COOLDOWN_S after the last one on that
module -- the firmware enforces >= 2 s between pulses and a refused pulse
would only look like a dead solenoid.
"""
import threading
import time
from datetime import datetime

from .. import lgs_map
from ..transports import INTERACTIVE_TIMEOUT_S
from . import gateway_api

MONITOR_GROUPS = ((0, 20), (20, 3), (40, 2), (60, 1))   # same blocks as the classic Monitor tab
STATS_GROUP = (200, 82)
DISPLAY_REG = 60
_cool: dict = {}
_cool_lock = threading.Lock()


class _Bus:
    """One client on the cabinet's gateway, serialised with the console
    sessions (gateway_api) so the page never interleaves two of its own."""

    def __init__(self, host: str, port: int) -> None:
        self.host, self.port = host, port
        self._lock = gateway_api._lock(host, port)
        self.client = None

    def __enter__(self):
        from ..transports import TcpSettings, make_client
        self._lock.acquire()
        try:
            self.client = make_client(TcpSettings(host=self.host, port=self.port,
                                                  timeout_s=INTERACTIVE_TIMEOUT_S), retries=0)
            if not self.client.connect():
                raise ConnectionError(f"cannot connect to {self.host}:{self.port}")
            return self.client
        except BaseException:
            self._lock.release()
            raise

    def __exit__(self, *exc) -> None:
        try:
            if self.client is not None:
                self.client.close()
        finally:
            self._lock.release()


def _check_id(device_id: int) -> None:
    if not lgs_map.valid_target_id(int(device_id)):
        raise ValueError(f"invalid module id {device_id} (1-247)")


def _read(client, addr: int, count: int, dev: int) -> list:
    r = client.read_holding_registers(addr, count=count, device_id=dev)
    if r is None or r.isError():
        raise IOError(f"no answer from module {dev} (regs {addr}+{count})")
    return list(r.registers)


def monitor(host: str, port: int, device_id: int, with_stats: bool = False) -> dict:
    _check_id(device_id)
    t0 = time.monotonic()
    regs: dict = {}
    errors: list = []
    with _Bus(host, port) as c:
        for start, count in MONITOR_GROUPS:
            try:
                for i, v in enumerate(_read(c, start, count, device_id)):
                    regs[start + i] = v
            except Exception as exc:                             # noqa: BLE001
                errors.append(str(exc)[:80])
                break                       # module probably absent: do not stack timeouts
        stats = None
        if with_stats and not errors:
            try:
                stats = {STATS_GROUP[0] + i: v
                         for i, v in enumerate(_read(c, *STATS_GROUP, device_id))}
            except Exception as exc:                             # noqa: BLE001
                errors.append("stats: " + str(exc)[:70])
    out = {"ok": bool(regs) and not (errors and 0 not in regs), "device_id": device_id,
           "at": datetime.now().strftime("%H:%M:%S"), "ms": int((time.monotonic() - t0) * 1000),
           "errors": errors, "regs": regs}
    if 0 in regs:
        r = regs
        uid = lgs_map.join_uid([r[i] for i in range(12, 18)]) if 17 in r else ""
        out["device"] = {"type": lgs_map.dec_device_type(r[0]), "fw": lgs_map.dec_fw(r[1]),
                         "hw": lgs_map.dec_hw(r[2]), "baud": lgs_map.dec_baud(r[3]), "id": r[4],
                         "uid": uid if uid.strip("0") else ""}
        out["runtime"] = {"uptime": lgs_map.dec_uptime(r[5], r[6]), "boots": r[7],
                          "mode": lgs_map.dec_mode(r[10]), "preset": lgs_map.dec_preset(r[11]),
                          "button": r.get(18), "held": bool(r.get(19))}
        out["health"] = [{"name": n, "ok": ok} for n, ok in lgs_map.decode_health(r[9], r[0])]
        out["reset"] = (", ".join(lgs_map.decode_reset_cause(r[8])) or f"raw {r[8]}") if r[8] else ""
    if 20 in regs:
        r = regs
        out["temps"] = {"room": lgs_map.dec_temp(r[20]), "board": lgs_map.dec_temp(r[21]),
                        "current": lgs_map.dec_current(r[22]) if 22 in r else "",
                        "fault": r[20] == lgs_map.SENSOR_FAULT or r[21] == lgs_map.SENSOR_FAULT}
    if 40 in regs:
        out["latch"] = {"state": {1: "locked", 0: "unlocked"}.get(regs.get(41)),
                        "unlocked_ago_s": regs[40]}
    if DISPLAY_REG in regs:
        out["display"] = regs[DISPLAY_REG]
    if stats:
        out["stats"] = {"fires": stats.get(200, 0), "seconds": stats.get(201, 0),
                        "presets": [{"p": n, "count": stats.get(lgs_map.stats_count(n), 0),
                                     "seconds": stats.get(lgs_map.stats_time(n), 0)}
                                    for n in range(1, 9)]}
    return out


def presets() -> list:
    return [{"n": n, "enable": lgs_map.coil_enable(n), "display": lgs_map.coil_display(n),
             "latch": lgs_map.coil_latch(n), "latch_display": lgs_map.coil_latch_display(n)}
            for n in range(1, 9)]


def cooldown_left(host: str, port: int, device_id: int) -> float:
    with _cool_lock:
        return max(0.0, _cool.get((host, port, device_id), 0.0) - time.monotonic())


def coil(host: str, port: int, device_id: int, addr: int, value: bool) -> dict:
    _check_id(device_id)
    addr = int(addr)
    cls = lgs_map.classify_coil(addr)
    if cls is lgs_map.CoilClass.FORBIDDEN:
        return {"ok": False, "error": "OTA coils are driven by the firmware-update tools only"}
    if cls is lgs_map.CoilClass.DANGER:
        return {"ok": False, "error": "danger coil: not available on this page"}
    key = (host, port, device_id)
    if cls is lgs_map.CoilClass.LATCH and value:
        left = cooldown_left(host, port, device_id)
        if left > 0:
            return {"ok": False, "error": f"latch cooldown: {left:.1f} s remaining", "cooldown_s": left}
    t0 = time.monotonic()
    with _Bus(host, port) as c:
        r = c.write_coil(addr, bool(value), device_id=device_id)
    if r is None or r.isError():
        return {"ok": False, "error": f"no answer from module {device_id}"}
    if cls is lgs_map.CoilClass.LATCH and value:
        with _cool_lock:
            _cool[key] = time.monotonic() + lgs_map.LATCH_COOLDOWN_S
    return {"ok": True, "ms": int((time.monotonic() - t0) * 1000), "class": cls.value,
            "cooldown_s": lgs_map.LATCH_COOLDOWN_S if (cls is lgs_map.CoilClass.LATCH and value) else 0}


def display_number(host: str, port: int, device_id: int, value: int) -> dict:
    _check_id(device_id)
    value = int(value)
    if not 0 <= value <= 9999:
        raise ValueError("number must be 0-9999")
    with _Bus(host, port) as c:
        r = c.write_register(DISPLAY_REG, value, device_id=device_id)
    if r is None or r.isError():
        return {"ok": False, "error": f"no answer from module {device_id}"}
    return {"ok": True, "value": value}
