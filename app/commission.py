"""Commissioning a blank module: give it its ID in the same ST-Link session.

Until now a new module took two tools and two sessions — STM32CubeProgrammer
to flash it, then something else to set its Modbus ID, because a board with no
firmware cannot be told its address over Modbus. Patching the ID into the image
before it is written collapses that into one step.

The runner is pure: it takes an ops object and emits events, so it can be
exercised with a fake programmer and no hardware at all. Same shape as
app/ota.py, and it reuses that module's Line/Progress/Done vocabulary so the
UI drains it the same way.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Protocol

from . import commission_image as ci
from .ota import Done, Line, Progress

LOG_NAME = "commission_log.csv"
LOG_HEADER = ("timestamp", "slave_id", "device_uid", "lot", "token",
              "image", "image_bytes", "overwrite", "result")


class CommissionCancelled(Exception):
    pass


class CommissionOps(Protocol):
    """What the runner needs from the outside world."""

    def find_programmer(self) -> object: ...
    def programmer_version(self, cli) -> str: ...
    def list_probes(self, cli) -> list: ...
    def read_uid(self, cli) -> str: ...
    def probe(self, cli) -> object | None: ...
    def flash(self, cli, image_path, on_line, cancel) -> object: ...
    def write_temp(self, data: bytes, name: str) -> Path: ...
    def remove_temp(self, path: Path) -> None: ...
    def sleep(self, seconds: float) -> None: ...


@dataclass
class CommissionConfig:
    image: bytes = b""
    filename: str = ""
    identifier: int = 0
    lot: str = ""
    overwrite: bool = False          # sets the block's FORCE flag
    log_dir: Path | None = None      # where commission_log.csv goes


@dataclass
class BatchConfig:
    """A whole lot in one sitting: swap boards, the runner does the rest.

    Always non-FORCE: a production line flashes factory-blank boards, and a
    board that already carries an ID keeping it is the safety property, not a
    problem. Renumbering stays a deliberate one-board act in single mode.
    """
    image: bytes = b""
    filename: str = ""
    ids: tuple = ()                  # assignment order
    lot: str = ""
    log_dir: Path | None = None


@dataclass
class BoardNext:
    """Batch: waiting for a blank board to give this ID to."""
    identifier: int
    seq: int = 0


@dataclass
class BoardDone:
    """Batch: one board finished (the batch itself may continue)."""
    identifier: int
    ok: bool
    uid: str = ""
    seq: int = 0


@dataclass
class CommissionReport:
    ok: bool = False
    summary: str = ""
    identifier: int = 0
    token: int = 0
    uid: str = ""
    lines: list = field(default_factory=list)


def append_log(log_dir: Path, cfg: CommissionConfig, *, uid: str, token: int,
               ok: bool) -> Path | None:
    """One row per module, so a production run leaves a record.

    This is where the device serial lives. It is the STM32's own unique ID read
    over SWD, not something patched into the image — every board keeps running
    byte-identical firmware, which is what lets one image be OTA'd to a whole
    bus later.
    """
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / LOG_NAME
        new = not path.exists()
        with path.open("a", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(LOG_HEADER)
            w.writerow((datetime.now().isoformat(timespec="seconds"),
                        cfg.identifier, uid, cfg.lot, f"0x{token:08X}",
                        cfg.filename, len(cfg.image),
                        "yes" if cfg.overwrite else "no",
                        "ok" if ok else "failed"))
        return path
    except OSError:
        return None          # a missing production log must not fail a flash


def _find_programmer(ops: CommissionOps, say) -> tuple[object | None, str]:
    """Step [1/5], shared verbatim by single and batch mode."""
    try:
        cli = ops.find_programmer()
    except Exception as exc:                            # noqa: BLE001
        say(str(exc), "err")
        return None, "STM32CubeProgrammer not available"
    say(f"[1/5] STM32CubeProgrammer {ops.programmer_version(cli)}", "ok")

    probes = ops.list_probes(cli)
    if not probes:
        say("No ST-Link is connected.", "err")
        return None, "no ST-Link found"
    say(f"      {probes[0].describe()}")
    if len(probes) > 1:
        say(f"      {len(probes)} probes connected — using the first", "warn")
    return cli, ""


def _flash_one(ops: CommissionOps, cli, cfg: CommissionConfig,
               report: CommissionReport, say, step, cancel) -> tuple[bool, str]:
    """Steps [2/5]-[5/5] for one board: validate, patch, flash, log.

    `step(n)` reports sub-progress (single mode maps it onto the bar; batch
    mode tracks whole boards instead). Returns (ok, failure note); partial
    uid/token land in `report` so a cancellation can still be logged.
    """
    temp: Path | None = None
    try:
        step(1)
        try:
            block = ci.find_block(cfg.image)
        except ci.ImageError as exc:
            say(str(exc), "err")
            return False, "image cannot carry an ID"
        say(f"[2/5] {cfg.filename}: {len(cfg.image):,} B, {ci.describe(block)}", "ok")
        if block.patched:
            say("      this file was already patched once; re-patching it", "warn")

        step(2)
        uid = ops.read_uid(cli)
        report.uid = uid
        say(f"[3/5] device UID {uid}" if uid else
            "[3/5] device UID unavailable — logging without it", "ok" if uid else "warn")

        if cancel.is_set():
            raise CommissionCancelled()

        step(3)
        try:
            patched, written = ci.patch(cfg.image, identifier=cfg.identifier,
                                        force=cfg.overwrite)
        except ci.ImageError as exc:
            say(str(exc), "err")
            return False, "could not patch the image"
        report.token = written.token
        say(f"[4/5] patched to ID {cfg.identifier}"
            f"{' with overwrite' if cfg.overwrite else ''}, "
            f"token 0x{written.token:08X}")

        temp = ops.write_temp(patched, cfg.filename)
        result = ops.flash(cli, temp, lambda ln: say(f"      {ln}"),
                           lambda: cancel.is_set())
        if not result.ok:
            say(result.note, "err")
            return False, result.note
        say(f"      {result.note}", "ok")

        step(4)
        path = append_log(cfg.log_dir, cfg, uid=uid, token=written.token, ok=True) \
            if cfg.log_dir else None
        say(f"[5/5] logged to {path.name}" if path else
            "[5/5] production log not written", "ok" if path else "warn")
        return True, ""
    finally:
        if temp is not None:
            ops.remove_temp(temp)


def run_commission(ops: CommissionOps, cfg: CommissionConfig, emit, cancel
                   ) -> CommissionReport:
    report = CommissionReport(identifier=cfg.identifier)

    def say(text: str, level: str = "info") -> None:
        report.lines.append(text)
        emit(Line(text, level))

    def finish(ok: bool, summary: str) -> CommissionReport:
        report.ok, report.summary = ok, summary
        emit(Done(ok, summary))
        return report

    total = 5
    try:
        emit(Progress(0, total))
        cli, why = _find_programmer(ops, say)
        if cli is None:
            return finish(False, why)

        ok, why = _flash_one(ops, cli, cfg, report, say,
                             lambda n: emit(Progress(n, total)), cancel)
        if not ok:
            return finish(False, why)

        emit(Progress(total, total))
        summary = (f"module commissioned as ID {cfg.identifier}"
                   + (f" (UID {report.uid})" if report.uid else ""))
        if not cfg.overwrite:
            summary += " — it keeps any ID it already had"
        return finish(True, summary)

    except CommissionCancelled:
        if cfg.log_dir:
            append_log(cfg.log_dir, cfg, uid=report.uid, token=report.token, ok=False)
        return finish(False, "cancelled")


_POLL_S = 2.5


def run_batch(ops: CommissionOps, cfg: BatchConfig, emit, cancel) -> None:
    """Assign cfg.ids to blank boards, one swap at a time.

    The bench loop the operator lives in: clip the next factory board on,
    watch it get the next ID from the queue, swap. Detection is 'flash is
    blank' — the board just flashed stops being blank, so it can never be
    taken twice, and a board that already ran is never renumbered by accident.
    One board failing stops the batch: on a production bench a failure means
    hands are needed, and quietly moving on would desynchronise operator and
    queue. Everything already flashed stays flashed and logged.
    """
    total = len(cfg.ids)

    def say(text: str, level: str = "info") -> None:
        emit(Line(text, level))

    def finish(ok: bool, summary: str) -> None:
        emit(Done(ok, summary))

    try:
        emit(Progress(0, total))
        cli, why = _find_programmer(ops, say)
        if cli is None:
            return finish(False, why)
        try:
            ci.find_block(cfg.image)
        except ci.ImageError as exc:
            say(str(exc), "err")
            return finish(False, "image cannot carry an ID")

        done_ids: list = []
        for idx, target in enumerate(cfg.ids):
            emit(Progress(idx, total))
            emit(BoardNext(identifier=target))
            say(f"── module {idx + 1}/{total}: waiting for a blank board "
                f"to become ID {target} ──")

            last_state = ""
            while True:
                if cancel.is_set():
                    raise CommissionCancelled()
                p = ops.probe(cli)
                if p is None:
                    state = "gone"
                    if state != last_state:
                        say("      no board — clip the next one on")
                elif not p.blank:
                    state = "programmed"
                    if state != last_state:
                        say("      a programmed board is connected — "
                            "swap it for a blank one")
                else:
                    say(f"      blank board found, UID {p.uid}", "ok")
                    break
                last_state = state
                ops.sleep(_POLL_S)

            one = CommissionConfig(image=cfg.image, filename=cfg.filename,
                                   identifier=target, lot=cfg.lot,
                                   overwrite=False, log_dir=cfg.log_dir)
            report = CommissionReport(identifier=target)
            ok, why = _flash_one(ops, cli, one, report, say,
                                 lambda n: None, cancel)
            emit(BoardDone(identifier=target, ok=ok, uid=report.uid))
            if not ok:
                emit(Progress(idx, total))
                return finish(False, f"stopped at ID {target}: {why} — "
                                     f"{len(done_ids)} of {total} done")
            done_ids.append(target)
            say(f"      ID {target} done — {len(done_ids)}/{total}", "ok")

        emit(Progress(total, total))
        return finish(True, f"batch complete: {total} modules "
                            f"({cfg.ids[0]}-{cfg.ids[-1]})")

    except CommissionCancelled:
        return finish(False, "cancelled")
