"""Flash the Opta gateway's firmware over USB, without PlatformIO.

Updating the gateway has meant a developer machine with PlatformIO and the
project checked out. On site there is neither, so a gateway that needs new
firmware means someone drives back with a laptop. This does the same job the
`pio run -t upload` invocation does, from the tool the technician already has.

The sequence is the board's own, not ours:

  1. open its serial port at 1200 baud and close it again. The Arduino core
     watches for exactly that and reboots into the DFU bootloader — the same
     "1200 bps touch" gateway_config.py already refuses to let a settings
     write trigger by accident.
  2. wait for the DFU device to enumerate. It is a *different* USB device
     from the running gateway, so the COM port disappears while it is up.
  3. dfu-util writes the image at the app offset and `:leave` makes the
     bootloader run it immediately.

Parameters come from the ststm32 platform's own upload logic
(builder/main.py, the `dfu` branch) plus boards/opta.json, so this stays the
same command PlatformIO issues rather than a guess that happens to work.

Nothing here touches Modbus. The caller must close the port first: the
gateway's USB *is* the Modbus bridge, so a live connection would both hold
the port open and vanish underneath itself at step 1.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

# boards/opta.json: upload.offset_address, build.hwids. The bootloader keeps
# the vendor ID; matching on vendor alone also finds it when a board revision
# ships a new product ID, which a hardcoded pair would silently miss.
FLASH_OFFSET = "0x08040000"
ARDUINO_VID = "2341"
TOUCH_BAUD = 1200
DFU_APPEAR_TIMEOUT_S = 20
FLASH_TIMEOUT_S = 180

EXE = "dfu-util.exe" if os.name == "nt" else "dfu-util"

# Where PlatformIO puts the Arduino-flavoured build. Portenta-family boards
# need that one specifically — the generic tool-dfuutil is a different build.
_SEARCH_DIRS = (
    Path.home() / ".platformio" / "packages" / "tool-dfuutil-arduino",
    Path.home() / ".platformio" / "packages" / "tool-dfuutil" / "bin",
)


class FlashError(Exception):
    """Something the operator can act on, phrased for them."""


def blob(name: str) -> bytes:
    """A firmware image shipped inside the tool (see app/blobs/README.md)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS")) / "app" / "blobs"
    else:
        base = Path(__file__).resolve().parent / "blobs"
    try:
        return (base / name).read_bytes()
    except OSError as exc:
        raise FlashError(f"The bundled {name} is missing from this build "
                         f"({exc}).") from exc


@dataclass(frozen=True)
class DfuDevice:
    vid: str
    pid: str
    name: str = ""

    @property
    def spec(self) -> str:
        return f"0x{self.vid}:0x{self.pid}"

    def describe(self) -> str:
        return f"{self.spec}{f' ({self.name})' if self.name else ''}"


@dataclass
class FlashResult:
    ok: bool
    note: str = ""
    lines: list = field(default_factory=list)


def find_dfu_util(configured: str = "") -> Path:
    """Locate dfu-util, or say where to put it."""
    if configured:
        p = Path(configured)
        if p.is_dir():
            p = p / EXE
        if p.exists():
            return p
        raise FlashError(f"dfu-util was not found at the configured path "
                         f"({configured}). Clear or correct it in the settings.")

    if getattr(sys, "frozen", False):        # shipped next to the exe
        beside = Path(sys.executable).parent / EXE
        if beside.exists():
            return beside

    for d in _SEARCH_DIRS:
        if (d / EXE).exists():
            return d / EXE

    import shutil
    found = shutil.which(EXE)
    if found:
        return Path(found)

    raise FlashError(
        "dfu-util was not found. It ships with PlatformIO "
        "(packages/tool-dfuutil-arduino) — copy it next to this tool, or set "
        "its path in the settings. Everything else keeps working without it.")


def _run(dfu: Path, args: list, timeout: int = 30) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([str(dfu)] + args, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise FlashError(f"dfu-util did not answer within {timeout} s.") from exc
    except OSError as exc:
        raise FlashError(f"Could not run dfu-util: {exc}") from exc


def list_dfu(dfu: Path) -> list:
    """Every DFU device dfu-util can see, deduplicated by VID:PID.

    A board exposes several DFU interfaces (internal flash, external QSPI);
    they differ only by alt setting, which we always drive as 0.
    """
    out = _run(dfu, ["-l"]).stdout
    seen, devices = set(), []
    for m in re.finditer(r"\[([0-9A-Fa-f]{4}):([0-9A-Fa-f]{4})\]([^\n]*)", out):
        vid, pid = m.group(1).lower(), m.group(2).lower()
        if (vid, pid) in seen:
            continue
        seen.add((vid, pid))
        name = ""
        nm = re.search(r'name="([^"]*)"', m.group(3))
        if nm:
            name = nm.group(1)
        devices.append(DfuDevice(vid=vid, pid=pid, name=name))
    return devices


def find_gateway_dfu(dfu: Path):
    """The Arduino board in DFU mode, or None."""
    for d in list_dfu(dfu):
        if d.vid == ARDUINO_VID:
            return d
    return None


def touch_1200(port: str) -> None:
    """Reboot the gateway into its bootloader.

    Opening at 1200 baud and closing is the whole signal; the core reboots
    on the close, so the port disappearing here is success, not a failure.
    """
    import serial
    try:
        s = serial.Serial(port, TOUCH_BAUD)
        s.dtr = False
        time.sleep(0.25)
        s.close()
    except serial.SerialException as exc:
        raise FlashError(
            f"Could not open {port} to reboot the gateway ({exc}). Close any "
            "other program using it — including this tool's own connection.")
    time.sleep(0.5)


def wait_for_dfu(dfu: Path, timeout_s: float = DFU_APPEAR_TIMEOUT_S,
                 cancel: Callable[[], bool] | None = None):
    """Poll until the board comes back as a DFU device."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if cancel and cancel():
            return None
        found = find_gateway_dfu(dfu)
        if found:
            return found
        time.sleep(0.5)
    return None


def find_serial_port(timeout_s: float = 30.0,
                     cancel: Callable[[], bool] | None = None) -> str:
    """Wait for an Arduino USB serial port to (re)appear, and name it.

    After a flash the board enumerates fresh, and Windows often hands it a
    different COM number than it had before — so the port the operator
    connected on cannot be reused blindly.
    """
    from serial.tools import list_ports
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if cancel and cancel():
            return ""
        for p in list_ports.comports():
            if p.vid == 0x2341:
                return p.device
        time.sleep(0.5)
    return ""


def converse(port: str, on_line: Callable[[str], None],
             answer: Callable[[str], str], done_marker: str,
             timeout_s: float, cancel: Callable[[], bool] | None = None) -> bool:
    """Answer a sketch's Y/[n] questions until it says it is done.

    The first question is already on the wire before this can open the port —
    the sketch prints and blocks, and a host attaching afterwards never sees
    it. So the opening answer goes out blind, before reading anything.

    Answers are single characters on purpose: the sketch's waitResponse()
    takes *any* stray 'y' or 'n' byte as the reply, so echoing words back
    would answer the next question by accident.
    """
    import serial
    prompt = "Y/[n]"
    try:
        s = serial.Serial(port, 115200, timeout=0.5)
    except serial.SerialException as exc:
        raise FlashError(f"Could not open {port} to answer the formatter "
                         f"({exc}).") from exc
    try:
        time.sleep(1.0)
        s.write(b"y")                       # the question already asked
        buf, deadline = "", time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if cancel and cancel():
                return False
            chunk = s.read(256).decode("ascii", "replace")
            if chunk:
                buf += chunk
                for line in chunk.replace("\r", "").split("\n"):
                    if line.strip():
                        on_line(line.strip())
            while prompt in buf:
                idx = buf.index(prompt)
                start = buf.rfind("\n", 0, idx) + 1
                question = buf[start:idx]
                buf = buf[idx + len(prompt):]
                time.sleep(0.4)             # it is still printing the note
                s.write(answer(question).encode())
            if done_marker in buf:
                return True
        return False
    finally:
        s.close()


def flash(dfu: Path, device: DfuDevice, image: Path,
          on_line: Callable[[str], None] | None = None,
          cancel: Callable[[], bool] | None = None) -> FlashResult:
    """Write `image` at the app offset and let the gateway run it."""
    args = ["-d", device.spec, "-a", "0",
            f"-s", f"{FLASH_OFFSET}:leave", "-D", str(image)]
    lines: list = []
    try:
        proc = subprocess.Popen([str(dfu)] + args, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
    except OSError as exc:
        raise FlashError(f"Could not run dfu-util: {exc}") from exc

    try:
        for raw in proc.stdout:                      # type: ignore[union-attr]
            line = raw.rstrip()
            if not line:
                continue
            lines.append(line)
            if on_line:
                on_line(line)
            if cancel and cancel():
                proc.terminate()
                return FlashResult(
                    False,
                    "Cancelled mid-write. The gateway is still in its "
                    "bootloader with an incomplete image — flash it again to "
                    "recover; nothing else is damaged.", lines)
        proc.wait(timeout=FLASH_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        return FlashResult(False, f"No response for {FLASH_TIMEOUT_S} s — "
                                  "check the USB connection.", lines)
    finally:
        if proc.stdout:
            proc.stdout.close()

    blob = "\n".join(lines)
    # dfu-util's exit code is not trusted on its own: it has historically
    # returned 0 after a failed download, and this line is what actually
    # says the bytes landed.
    wrote = "File downloaded successfully" in blob
    if proc.returncode != 0 or not wrote:
        why = next((ln for ln in lines if re.search(r"\berror\b", ln, re.I)),
                   f"exit code {proc.returncode}")
        return FlashResult(False, f"Flashing failed: {why}", lines)
    return FlashResult(True, "written and restarted", lines)
