"""Hold the machine awake while an unattended job is running.

The first overnight soak (2026-08-13) died at 00:17 and nobody could say
why. Windows had entered Modern Standby at 22:41; the app went on polling
at full cadence for another hour and a half, and then the process was
simply gone — no traceback, no Windows error report, only the gateway's own
event log showing the TCP socket closing at 00:17:06. Four hours of a
cabinet test were lost to a power plan.

A tool whose purpose is to be left running on the site's server — soaking
the bus overnight, answering NTP for the gateway — must not depend on
somebody remembering to change that setting. So it asks Windows directly.

ONE THREAD ONLY. Windows tracks this per thread: SetThreadExecutionState
with ES_CONTINUOUS holds until the SAME thread changes it, and is dropped
the moment that thread exits. Every call must therefore come from one
long-lived thread — here, the asyncio loop's thread, where main.py's guard
task runs. Calling it from a worker thread would look right and then
release the lock the instant the job that asked for it ended.

ES_SYSTEM_REQUIRED only, never ES_DISPLAY_REQUIRED: the screen is welcome
to sleep, the machine is not.
"""
from __future__ import annotations

import sys

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001

_held = False
_note = ""
_set_state = None

if sys.platform == "win32":
    try:
        import ctypes

        _set_state = ctypes.WinDLL("kernel32", use_last_error=True).SetThreadExecutionState
        _set_state.argtypes = [ctypes.c_uint32]
        _set_state.restype = ctypes.c_uint32
    except Exception as exc:                                    # noqa: BLE001
        _set_state = None
        _note = f"{type(exc).__name__}: {exc}"


def supported() -> bool:
    return _set_state is not None


def held() -> bool:
    return _held


def note() -> str:
    """Why it is not holding, when it should be. "" = nothing to say."""
    return _note


def apply(active: bool) -> bool:
    """Hold (or release) the sleep block. Idempotent — call it as often as
    you like; the Windows call only happens when the answer changes.

    Returns whether the block is in force. Never raises: a machine that
    refuses to stay awake must still run the test.
    """
    global _held, _note
    if _set_state is None or bool(active) == _held:
        return _held
    flags = (ES_CONTINUOUS | ES_SYSTEM_REQUIRED) if active else ES_CONTINUOUS
    try:
        if _set_state(flags) == 0:                  # 0 = the call failed
            _note = "Windows refused the sleep block (SetThreadExecutionState)"
            return _held
    except Exception as exc:                                    # noqa: BLE001
        _note = f"{type(exc).__name__}: {exc}"
        return _held
    _held = bool(active)
    _note = ""
    return _held
