"""Gateway firmware update, as a runner the worker can drive.

Same shape as commission.py and ota.py: pure logic behind an ops object,
emitting Line/Progress/Done so the UI drains it the way it drains every
other long job. The steps are the operator's mental model, not the tool's —
each one is a thing that can go wrong on a bench and needs naming when it
does.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .ota import Done, Line, Progress

# The gateway app image starts here; below it is Arduino's own bootloader,
# which this never touches — losing that would need an ST-Link to recover.
MIN_IMAGE_B = 50_000
MAX_IMAGE_B = 786_432        # boards/opta.json upload.maximum_size


class OptaCancelled(Exception):
    pass


class OptaOps(Protocol):
    def find_tool(self) -> object: ...
    def touch(self, port: str) -> None: ...
    def wait_for_dfu(self, tool, cancel) -> object: ...
    def flash(self, tool, device, image_path, on_line, cancel) -> object: ...
    def write_temp(self, data: bytes, name: str) -> Path: ...
    def remove_temp(self, path: Path) -> None: ...
    def sleep(self, seconds: float) -> None: ...
    # provisioning only
    def blob(self, name: str) -> bytes: ...
    def find_port(self, timeout_s: float, cancel) -> str: ...
    def converse(self, port: str, on_line, answer, done_marker,
                 timeout_s: float, cancel) -> bool: ...


@dataclass
class OptaConfig:
    image: bytes = b""
    filename: str = ""
    port: str = ""               # the gateway's serial port, before the touch


# QSPIFormat's dialogue. It asks in a fixed order but skips questions that do
# not apply (a partition it did not find has nothing to reformat), so answers
# are matched on the question rather than counted — a positional script would
# answer the wrong question the first time a board differs.
QSPI_ANSWERS = (
    ("restore the wifi firmware", "n"),   # the gateway is Ethernet-only
)
QSPI_DEFAULT_ANSWER = "y"
QSPI_PROMPT = "Y/[n]"
QSPI_DONE = "QSPI Flash formatted"
QSPI_TIMEOUT_S = 240             # a full erase alone can take a minute


def qspi_answer(prompt: str) -> str:
    low = prompt.lower()
    for needle, ans in QSPI_ANSWERS:
        if needle in low:
            return ans
    return QSPI_DEFAULT_ANSWER


@dataclass
class OptaReport:
    ok: bool = False
    summary: str = ""
    lines: list = field(default_factory=list)


def run_provision(ops: OptaOps, cfg: OptaConfig, emit, cancel) -> OptaReport:
    """Give a factory-fresh Opta the QSPI partitions the gateway needs.

    Three flashes in one action, because doing them separately means a
    technician holding a half-provisioned board and a decision to make:

      1. Arduino's QSPIFormat, bundled with this tool
      2. answer its questions — it asks before a late-attaching host can see
         the first one, so the first answer goes out blind
      3. put the gateway firmware back, since step 1 replaced it

    Destructive to the QSPI by definition. That is the point on a new board
    (there is nothing there yet) and the reason the caller must confirm on a
    board that already works.
    """
    report = OptaReport()
    temp: Path | None = None
    total = 6

    def say(text: str, level: str = "info") -> None:
        report.lines.append(text)
        emit(Line(text, level))

    def finish(ok: bool, summary: str) -> OptaReport:
        report.ok, report.summary = ok, summary
        emit(Done(ok, summary))
        return report

    try:
        emit(Progress(0, total))
        try:
            tool = ops.find_tool()
            formatter = ops.blob("qspiformat_opta.bin")
        except Exception as exc:                     # noqa: BLE001
            say(str(exc), "err")
            return finish(False, "cannot start provisioning")
        say(f"[1/6] dfu-util at {tool}; QSPIFormat {len(formatter):,} B", "ok")

        size = len(cfg.image)
        if not (MIN_IMAGE_B <= size <= MAX_IMAGE_B):
            say(f"{cfg.filename} is {size:,} B, outside the {MIN_IMAGE_B:,}-"
                f"{MAX_IMAGE_B:,} B a gateway image occupies — provisioning "
                "would leave the board without firmware to put back.", "err")
            return finish(False, "gateway image is not plausible")
        say(f"[2/6] gateway image to restore afterwards: {cfg.filename} "
            f"({size:,} B)", "ok")

        # [3/6] QSPIFormat on --------------------------------------------
        emit(Progress(2, total))
        say(f"[3/6] rebooting {cfg.port} into its bootloader")
        ops.touch(cfg.port)
        device = ops.wait_for_dfu(tool, lambda: cancel.is_set())
        if cancel.is_set():
            raise OptaCancelled()
        if device is None:
            say("The board never appeared as a DFU device.", "err")
            return finish(False, "board did not enter DFU mode")
        temp = ops.write_temp(formatter, "qspiformat.bin")
        result = ops.flash(tool, device, temp, lambda ln: say(f"      {ln}"),
                           lambda: cancel.is_set())
        ops.remove_temp(temp)
        temp = None
        if not result.ok:
            say(result.note, "err")
            return finish(False, result.note)
        say("      QSPIFormat is running on the board", "ok")

        # [4/6] the dialogue ---------------------------------------------
        emit(Progress(3, total))
        port = ops.find_port(30.0, lambda: cancel.is_set())
        if cancel.is_set():
            raise OptaCancelled()
        if not port:
            say("The board did not come back as a serial port after the "
                "formatter was written.", "err")
            return finish(False, "no serial port after flashing QSPIFormat")
        say(f"[4/6] answering QSPIFormat on {port} "
            f"(WiFi firmware is declined — the gateway uses Ethernet)")
        ok = ops.converse(port, lambda ln: say(f"      {ln}"), qspi_answer,
                          QSPI_DONE, QSPI_TIMEOUT_S, lambda: cancel.is_set())
        if cancel.is_set():
            raise OptaCancelled()
        if not ok:
            say("QSPIFormat never reported success. The QSPI may be half "
                "formatted — run this again before using the board.", "err")
            return finish(False, "QSPIFormat did not finish")
        say("      partitions created (KVStore is partition 3)", "ok")

        # [5/6] gateway firmware back -------------------------------------
        emit(Progress(4, total))
        say("[5/6] putting the gateway firmware back")
        ops.touch(port)
        device = ops.wait_for_dfu(tool, lambda: cancel.is_set())
        if cancel.is_set():
            raise OptaCancelled()
        if device is None:
            say("The board did not re-enter DFU mode. Its QSPI is formatted, "
                "but it is still running the formatter — flash the gateway "
                "firmware with the update card to finish.", "err")
            return finish(False, "could not restore the gateway firmware")
        temp = ops.write_temp(cfg.image, cfg.filename)
        result = ops.flash(tool, device, temp, lambda ln: say(f"      {ln}"),
                           lambda: cancel.is_set())
        if not result.ok:
            say(result.note, "err")
            say("The QSPI is formatted; only the firmware restore failed. "
                "Use the update card to finish.", "warn")
            return finish(False, result.note)

        emit(Progress(5, total))
        ops.sleep(3.0)
        say("[6/6] done — connect and check that the gateway page saves", "ok")
        emit(Progress(total, total))
        return finish(True, "Opta provisioned: QSPI partitioned and gateway "
                            "firmware restored")

    except OptaCancelled:
        return finish(False, "cancelled")
    finally:
        if temp is not None:
            ops.remove_temp(temp)


def run_update(ops: OptaOps, cfg: OptaConfig, emit, cancel) -> OptaReport:
    report = OptaReport()
    temp: Path | None = None
    total = 4

    def say(text: str, level: str = "info") -> None:
        report.lines.append(text)
        emit(Line(text, level))

    def finish(ok: bool, summary: str) -> OptaReport:
        report.ok, report.summary = ok, summary
        emit(Done(ok, summary))
        return report

    try:
        # [1/4] the tool ------------------------------------------------
        emit(Progress(0, total))
        try:
            tool = ops.find_tool()
        except Exception as exc:                     # noqa: BLE001
            say(str(exc), "err")
            return finish(False, "dfu-util not available")
        say(f"[1/4] dfu-util at {tool}", "ok")

        # [2/4] the image -----------------------------------------------
        emit(Progress(1, total))
        size = len(cfg.image)
        if not (MIN_IMAGE_B <= size <= MAX_IMAGE_B):
            # A .hex, a module image or a truncated download all land here.
            say(f"{cfg.filename} is {size:,} B, outside the {MIN_IMAGE_B:,}-"
                f"{MAX_IMAGE_B:,} B a gateway image occupies. This is most "
                "likely the wrong file — a module image, or not a .bin.", "err")
            return finish(False, "image size is not plausible for a gateway")
        say(f"[2/4] {cfg.filename}: {size:,} B", "ok")

        # [3/4] into the bootloader --------------------------------------
        emit(Progress(2, total))
        say(f"[3/4] rebooting {cfg.port} into its bootloader (1200 bps touch)")
        ops.touch(cfg.port)
        device = ops.wait_for_dfu(tool, lambda: cancel.is_set())
        if cancel.is_set():
            raise OptaCancelled()
        if device is None:
            say("The gateway never appeared as a DFU device. Unplug it, hold "
                "nothing, plug it back in and try again — if it still does "
                "not, its bootloader may need the reset button.", "err")
            return finish(False, "gateway did not enter DFU mode")
        say(f"      {device.describe()}", "ok")

        # [4/4] write -----------------------------------------------------
        emit(Progress(3, total))
        temp = ops.write_temp(cfg.image, cfg.filename)
        result = ops.flash(tool, device, temp, lambda ln: say(f"      {ln}"),
                           lambda: cancel.is_set())
        if not result.ok:
            say(result.note, "err")
            return finish(False, result.note)
        say(f"[4/4] {result.note}", "ok")

        # The COM port takes a moment to come back under a new firmware, and
        # reconnecting before it does looks like a failed update.
        ops.sleep(3.0)
        emit(Progress(total, total))
        return finish(True, "gateway updated — reconnect to check its version")

    except OptaCancelled:
        return finish(False, "cancelled")
    finally:
        if temp is not None:
            ops.remove_temp(temp)
