"""Drive STM32CubeProgrammer's CLI to flash a module over ST-Link.

CubeProgrammer is a separate ~1 GB install with its own licence, so it cannot
be bundled into the portable exe. This finds it instead, and says so plainly
when it is missing rather than failing somewhere deep in a job.

Output is streamed line by line rather than collected at the end: a flash takes
the better part of a minute, and a progress bar that only appears once it is
over is not a progress bar. That is the one place this departs from the
subprocess conventions in tools/sync_reference.py.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

EXE_NAME = "STM32_Programmer_CLI.exe" if os.name == "nt" else "STM32_Programmer_CLI"

# Where ST's installer puts it. Checked in order, newest layout first.
_SEARCH_DIRS = (
    r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin",
    r"C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin",
    r"C:\ST\STM32CubeIDE\STM32CubeProgrammer\bin",
)

FLASH_ADDRESS = 0x08000000      # bootloader + app, as one factory image
FLASH_TIMEOUT_S = 180


class ProgrammerError(Exception):
    """Something the operator can act on: no CLI, no probe, a failed write."""


@dataclass(frozen=True)
class Probe:
    index: int
    serial: str
    firmware: str

    def describe(self) -> str:
        return f"ST-Link {self.serial} ({self.firmware})"


@dataclass
class FlashResult:
    ok: bool
    note: str = ""
    lines: list = field(default_factory=list)


def find_cli(configured: str = "") -> Path:
    """Locate STM32_Programmer_CLI, or explain how to point at it."""
    if configured:
        p = Path(configured)
        if p.is_dir():
            p = p / EXE_NAME
        if p.exists():
            return p
        raise ProgrammerError(
            f"STM32CubeProgrammer was not found at the configured path "
            f"({configured}). Clear or correct it in the settings.")

    for d in _SEARCH_DIRS:
        p = Path(d) / EXE_NAME
        if p.exists():
            return p

    found = shutil.which(EXE_NAME)
    if found:
        return Path(found)

    raise ProgrammerError(
        "STM32CubeProgrammer is not installed, or not where this tool looked. "
        "Install it from st.com, or set the path to STM32_Programmer_CLI in "
        "the settings. Everything else in the tool works without it.")


def _run(cli: Path, args: list, timeout: int = 60) -> subprocess.CompletedProcess:
    try:
        return subprocess.run([str(cli)] + args, capture_output=True, text=True,
                              timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise ProgrammerError(f"STM32CubeProgrammer did not finish within "
                              f"{timeout} s") from exc
    except OSError as exc:
        raise ProgrammerError(f"Could not run STM32CubeProgrammer: {exc}") from exc


def version(cli: Path) -> str:
    out = _run(cli, ["--version"], timeout=30).stdout
    m = re.search(r"STM32CubeProgrammer version:?\s*([\d.]+)", out)
    return m.group(1) if m else "unknown"


def list_probes(cli: Path) -> list:
    """Every ST-Link the CLI can see."""
    out = _run(cli, ["-l"], timeout=45).stdout
    probes, index = [], 0
    serial = None
    for line in out.splitlines():
        m = re.search(r"ST-LINK SN\s*:\s*(\S+)", line)
        if m:
            serial = m.group(1)
            continue
        m = re.search(r"ST-LINK FW\s*:\s*(\S+)", line)
        if m and serial:
            probes.append(Probe(index=index, serial=serial, firmware=m.group(1)))
            index += 1
            serial = None
    return probes


def read_uid(cli: Path) -> str:
    """The STM32's 96-bit unique ID, as a hex string.

    A real per-device serial that costs nothing to collect and, unlike one
    patched into the image, leaves every board running byte-identical firmware
    — which is what lets a single image be OTA'd to a whole bus.
    """
    out = _run(cli, ["-c", "port=SWD", "mode=UR", "reset=HWrst",
                     "-r32", "0x1FFF7590", "12"], timeout=60).stdout
    words = re.findall(r"0x1FFF75[0-9A-Fa-f]{2}\s*:\s*([0-9A-Fa-f ]+)", out)
    hexes = " ".join(words).split()
    if len(hexes) < 3:
        return ""
    return "".join(h.upper() for h in hexes[:3])


def flash(cli: Path, image: Path, *, address: int = FLASH_ADDRESS,
          on_line: Callable[[str], None] | None = None,
          cancel: Callable[[], bool] | None = None) -> FlashResult:
    """Write `image` at `address`, verify it, and let the board run.

    `mode=UR` (connect under reset) is not optional: the application arms a 4 s
    watchdog that survives a software reset and is never stopped, so a hotplug
    connect risks the board resetting itself in the middle of the write.
    """
    args = ["-c", "port=SWD", "mode=UR", "reset=HWrst",
            "-d", str(image), hex(address), "-v", "-rst"]
    lines: list = []
    try:
        proc = subprocess.Popen([str(cli)] + args, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
    except OSError as exc:
        raise ProgrammerError(f"Could not run STM32CubeProgrammer: {exc}") from exc

    try:
        for raw in proc.stdout:                     # type: ignore[union-attr]
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
                    "Cancelled mid-write. The module's application slot is now "
                    "incomplete and it will not start until it is flashed "
                    "again — nothing else is damaged.", lines)
        proc.wait(timeout=FLASH_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        return FlashResult(False, f"No response for {FLASH_TIMEOUT_S} s — "
                                  "check the ST-Link connection.", lines)
    finally:
        if proc.stdout:
            proc.stdout.close()

    blob = "\n".join(lines)
    # The exit code alone is not trusted: ST's tools have historically returned
    # 0 on partial failures, and the verify result is what actually matters.
    verified = "Download verified successfully" in blob
    if proc.returncode != 0 or not verified:
        why = _first_error(lines) or f"exit code {proc.returncode}"
        return FlashResult(False, f"Flashing failed: {why}", lines)
    return FlashResult(True, "programmed and verified", lines)


def _first_error(lines: Iterable[str]) -> str:
    for line in lines:
        if re.search(r"\berror\b", line, re.IGNORECASE):
            return line.strip()
    return ""


if __name__ == "__main__":                          # quick manual check
    try:
        cli = find_cli()
    except ProgrammerError as exc:
        print(exc)
        sys.exit(2)
    print(f"cli      {cli}")
    print(f"version  {version(cli)}")
    for p in list_probes(cli):
        print(f"probe    {p.describe()}")
