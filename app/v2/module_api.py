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

    def __init__(self, host: str, port: int, wait: float = 8.0, timeout_s: float = None) -> None:
        self.host, self.port, self.wait = host, port, wait
        self.timeout_s = timeout_s or INTERACTIVE_TIMEOUT_S
        self._lock = gateway_api._lock(host, port)
        self.client = None

    def __enter__(self):
        from ..transports import TcpSettings, make_client
        # A long run (the installation check) holds the gateway: say so rather
        # than leave a page request hanging behind it.
        if not self._lock.acquire(timeout=self.wait):
            raise ConnectionError("the cabinet's gateway is busy (a check is running)")
        try:
            self.client = make_client(TcpSettings(host=self.host, port=self.port,
                                                  timeout_s=self.timeout_s), retries=0)
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


# ── danger: set slave ID, software reset ──────────────────────────────────
# The same sequences as the classic Danger tab (ModbusWorker._do_set_slave_id /
# _do_danger), written against one held client. Coils 503/504 are DANGER class,
# which coil() above refuses on purpose: these two functions are the only way
# to them from v2, and each asks the page for a typed confirmation first.
REBOOT_WAIT_S = 4.0


def _probe(c, dev: int):
    try:
        r = c.read_holding_registers(4, count=1, device_id=dev)
        return None if (r is None or r.isError()) else r.registers[0]
    except Exception:                                            # noqa: BLE001
        return None


def set_slave_id(host: str, port: int, current_id: int, new_id: int) -> dict:
    _check_id(current_id)
    current_id, new_id = int(current_id), int(new_id)
    if not lgs_map.valid_assignable_id(new_id):
        raise ValueError(f"invalid new id {new_id} (1-245 or 247; 246 is the SET_ID temp id)")
    if new_id == current_id:
        raise ValueError("the new id is the same as the current one")
    steps = []
    with _Bus(host, port) as c:
        if _probe(c, current_id) is None:
            return {"ok": False, "error": f"module {current_id} is not answering", "steps": steps}
        steps.append(f"module {current_id} answers")
        time.sleep(lgs_map.INTER_TXN_S)
        # Not in the classic sequence: two modules on one address answer on top
        # of each other, and nothing on the bus could tell them apart again.
        if _probe(c, new_id) is not None:
            return {"ok": False, "error": f"id {new_id} is already used by another module", "steps": steps}
        steps.append(f"id {new_id} is free")
        time.sleep(lgs_map.INTER_TXN_S)
        w = c.write_register(4, new_id, device_id=current_id)
        if w is None or w.isError():
            return {"ok": False, "error": "writing reg 4 failed", "steps": steps}
        time.sleep(lgs_map.INTER_TXN_S)
        rb = _probe(c, current_id)
        if rb != new_id:
            return {"ok": False, "error": f"reg 4 readback mismatch (got {rb}, expected {new_id})", "steps": steps}
        steps.append(f"reg 4 = {new_id}")
        time.sleep(lgs_map.INTER_TXN_S)
        try:
            c.write_coil(503, True, device_id=current_id)           # persist + reboot
        except Exception:                                        # noqa: BLE001
            pass                                                 # no reply: rebooting (expected)
        steps.append("saved, module rebooting")
        time.sleep(REBOOT_WAIT_S)
        if _probe(c, new_id) == new_id:
            steps.append(f"answers at {new_id}")
            return {"ok": True, "steps": steps, "new_id": new_id}
        back = _probe(c, current_id)
        err = (f"module still answers at {current_id}: the new id was rejected when saved"
               if back is not None else f"module did not answer at {new_id} after reboot")
        return {"ok": False, "error": err, "steps": steps}


def soft_reset(host: str, port: int, device_id: int) -> dict:
    _check_id(device_id)
    with _Bus(host, port) as c:
        try:
            c.write_coil(504, True, device_id=int(device_id))
        except Exception:                                        # noqa: BLE001
            pass                                                 # no reply: rebooting (expected)
        time.sleep(REBOOT_WAIT_S)
        back = _probe(c, int(device_id)) is not None
    return {"ok": back, "error": "" if back else "module did not come back: check power and bus"}
