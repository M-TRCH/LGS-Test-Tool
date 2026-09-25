"""Count the frames pymodbus throws away, because nothing else does.

When a reply carries a different unit id from the one that was asked for,
pymodbus's framer discards it, logs

    ERROR: request ask for id=42 but got id=41, Skipping.

and retries. The retry usually works, so the read succeeds and every layer
above it -- including our own soak -- records a clean pass. The 2 h fleet
soak of 2026-09-22 reported 41 passes, 21,320 reads and zero failures while
twelve frames went in the bin, in two bursts, every one of them a reply one
address stale.

That is not a cosmetic difference. A reply one address stale is the
signature of a client giving up before the gateway has finished: the
abandoned answer arrives late and gets matched to the NEXT request. It says
the timeout is too short, and it is the only evidence of that which reaches
the surface. A run that cannot see it cannot be used to decide whether the
timeout was fixed.

Attribution is by thread name, which costs nothing because the fleet soak
already names one thread per cabinet -- "soak-Chest-Std-07". Anything on
another thread is filed under its own name rather than guessed at.

ONE KNOWN UNDERCOUNT, and it is in the safe direction: pymodbus collapses
consecutive identical messages into "Repeating....", so a burst of the same
mismatch counts once. `repeats` records how many such lines went by, so a
report can say "at least N" rather than "N" and mean it.
"""
from __future__ import annotations

import logging
import threading
from collections import Counter
from dataclasses import dataclass, field

# The framer's own wording, from pymodbus/framer/base.py. Matching on the
# text is ugly and it is what there is: the framer raises no event, exposes
# no counter, and returns the discard as an ordinary retry.
_MISMATCH = ("but got id=", "but got transaction_id=")
_REPEAT = "Repeating...."

# Log._logger is logging.getLogger("pymodbus.logging"); "pymodbus" is its
# parent, so one handler there catches the framer and anything else the
# library has to say for itself.
_LOGGER_NAME = "pymodbus"

MAX_SAMPLES = 200


@dataclass(frozen=True)
class FramerReport:
    """What was discarded, per thread, since the watch was reset."""
    per_owner: dict = field(default_factory=dict)
    repeats: int = 0
    samples: tuple = ()

    @property
    def total(self) -> int:
        return sum(self.per_owner.values())

    def line(self, owner: str) -> str:
        """One human sentence for a cabinet, or "" if it had none."""
        n = self.per_owner.get(owner, 0)
        if not n:
            return ""
        more = " (at least; repeats are collapsed)" if self.repeats else ""
        return f"{n} reply frames discarded as the wrong unit id{more}"


class _Watch(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.ERROR)
        self._lock = threading.Lock()
        self._per_owner: Counter = Counter()
        self._repeats = 0
        self._samples: list = []

    def emit(self, record: logging.LogRecord) -> None:
        # A logging handler that raises takes the caller with it, and the
        # caller here is a Modbus read in the middle of an overnight run.
        try:
            msg = record.getMessage()
        except Exception:                                        # noqa: BLE001
            return
        try:
            if _REPEAT in msg:
                with self._lock:
                    self._repeats += 1
                return
            if not any(m in msg for m in _MISMATCH):
                return
            owner = threading.current_thread().name
            with self._lock:
                self._per_owner[owner] += 1
                if len(self._samples) < MAX_SAMPLES:
                    self._samples.append((owner, msg))
        except Exception:                                        # noqa: BLE001
            return

    def snapshot(self) -> FramerReport:
        with self._lock:
            return FramerReport(per_owner=dict(self._per_owner),
                                repeats=self._repeats,
                                samples=tuple(self._samples))

    def reset(self) -> None:
        with self._lock:
            self._per_owner.clear()
            self._repeats = 0
            self._samples.clear()


_watch = _Watch()
_attached = False
_attach_lock = threading.Lock()


def start() -> None:
    """Begin counting. Safe to call repeatedly; attaches once."""
    global _attached
    with _attach_lock:
        if _attached:
            return
        log = logging.getLogger(_LOGGER_NAME)
        log.addHandler(_watch)
        # The library leaves its logger at NOTSET, so an ERROR record reaches
        # the root's WARNING threshold and propagates. Say so explicitly
        # rather than depending on a default nobody here controls.
        if log.level == logging.NOTSET or log.level > logging.ERROR:
            log.setLevel(logging.ERROR)
        _attached = True


def reset() -> None:
    """Forget what was counted. Call at the start of a run."""
    _watch.reset()


def snapshot() -> FramerReport:
    """What has been discarded since the last reset."""
    return _watch.snapshot()


def owner_for(cabinet_name: str) -> str:
    """The thread name the fleet soak gives a cabinet's reader."""
    return f"soak-{cabinet_name}"
