"""Everything the app prints, kept on disk — so "it died overnight" has an answer.

When the 2026-08-13 soak stopped at 00:17 the only evidence was an absence:
no CSV rows, no Windows error report, no console window left to read. The
diagnosis had to come from the GATEWAY's event log, which is a fine place
to learn that a socket closed and a poor one to learn why a Python process
went away.

So the tool now writes its own black box. One file per launch under
`data/logs/`, carrying stdout, stderr, unhandled exceptions on ANY thread,
asyncio's own complaints, and a final line at exit. The last line of that
file answers "did it crash, was it killed, or did it exit cleanly" — the
question that cost a night's data.

Nothing here may raise. A log that breaks the app it is documenting is
worse than no log: every write and every rotation failure is swallowed.
"""
from __future__ import annotations

import atexit
import sys
import threading
import traceback
from datetime import datetime
from pathlib import Path

KEEP_FILES = 20                 # launches kept; older logs are deleted

_file = None                    # the open handle, or None if we never got one
_path: Path | None = None
_lock = threading.Lock()


def path() -> Path | None:
    return _path


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _write(text: str) -> None:
    if _file is None:
        return
    try:
        with _lock:
            _file.write(text)
    except Exception:                                           # noqa: BLE001
        pass


def note(text: str) -> None:
    """One timestamped line, to the log and to the console.

    Straight to the REAL stdout, not through the tee — otherwise every
    noted line lands in the file twice, once stamped by each of us.
    """
    line = f"[{_stamp()}] {text}"
    _write(line + "\n")
    try:
        if sys.__stdout__ is not None:
            print(line, file=sys.__stdout__, flush=True)
    except Exception:                                           # noqa: BLE001
        pass


class _Tee:
    """A stream that writes to the real one and to the log file.

    Timestamps only at the START of a line, so progress printed with
    `end=""` does not come out shredded.
    """

    def __init__(self, original, tag: str) -> None:
        self._original = original
        self._tag = tag
        self._at_line_start = True

    def write(self, text: str) -> int:
        try:
            if self._original is not None:
                self._original.write(text)
        except Exception:                                       # noqa: BLE001
            pass
        if text:
            out = []
            for part in text.splitlines(keepends=True):
                if self._at_line_start:
                    out.append(f"[{_stamp()}] {self._tag} ")
                out.append(part)
                self._at_line_start = part.endswith(("\n", "\r"))
            _write("".join(out))
        return len(text)

    def flush(self) -> None:
        try:
            if self._original is not None:
                self._original.flush()
        except Exception:                                       # noqa: BLE001
            pass

    def isatty(self) -> bool:
        try:
            return bool(self._original is not None and self._original.isatty())
        except Exception:                                       # noqa: BLE001
            return False

    def fileno(self) -> int:
        if self._original is None:
            raise OSError("no console")
        return self._original.fileno()

    def __getattr__(self, name):
        # Anything else (encoding, buffer, …) belongs to the real stream.
        return getattr(self._original, name)


def _prune(directory: Path) -> None:
    try:
        files = sorted(directory.glob("app-*.log"))
        for old in files[:-KEEP_FILES]:
            old.unlink(missing_ok=True)
    except Exception:                                           # noqa: BLE001
        pass


def begin(directory: Path | None = None) -> Path | None:
    """Open this launch's log and start capturing. Safe to call twice."""
    global _file, _path
    if _file is not None:
        return _path
    if directory is None:
        from . import config_store          # local: config_store imports nothing
        directory = config_store.data_dir() / "logs"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        _path = directory / f"app-{datetime.now():%Y%m%d-%H%M%S}.log"
        _file = open(_path, "a", encoding="utf-8", errors="replace", buffering=1)
    except OSError:
        _file, _path = None, None
        return None
    _prune(directory)

    sys.stdout = _Tee(sys.stdout, "out")
    sys.stderr = _Tee(sys.stderr, "ERR")

    def on_exception(exc_type, exc, tb) -> None:
        _write(f"[{_stamp()}] UNHANDLED in main thread\n"
               + "".join(traceback.format_exception(exc_type, exc, tb)))
        sys.__excepthook__(exc_type, exc, tb)

    def on_thread_exception(args) -> None:
        # The one that matters here: the Modbus worker runs a soak for hours
        # on its own thread, and a thread dying takes the job with it while
        # the window stays up looking fine.
        name = getattr(args.thread, "name", "?")
        _write(f"[{_stamp()}] UNHANDLED in thread {name}\n"
               + "".join(traceback.format_exception(
                   args.exc_type, args.exc_value, args.exc_traceback)))

    sys.excepthook = on_exception
    if hasattr(threading, "excepthook"):
        threading.excepthook = on_thread_exception
    atexit.register(lambda: note("process exiting"))

    note(f"log opened: {_path}")
    return _path


def asyncio_handler(loop, context: dict) -> None:
    """`loop.set_exception_handler` — asyncio swallows these into a logger
    that a frozen exe may not be showing anywhere."""
    message = context.get("message", "?")
    exc = context.get("exception")
    _write(f"[{_stamp()}] ASYNCIO {message}\n")
    if exc is not None:
        _write("".join(traceback.format_exception(
            type(exc), exc, exc.__traceback__)))
    try:
        loop.default_exception_handler(context)
    except Exception:                                           # noqa: BLE001
        pass
