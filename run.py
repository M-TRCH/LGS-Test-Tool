"""Entry script for the packaged Windows executable (see build_exe.ps1).

PyInstaller cannot use `python -m app.main` as an entry point, and the onefile
bootstrap re-executes the binary, so freeze_support() must run first.

Everything else here runs BEFORE `app.main` is imported, deliberately: that
import already starts the Modbus worker thread and opens the app log, so both
the flag parsing and the single-instance check have to happen while nothing
has been touched yet.

Flags (parsed by hand — the point is to run before any import):
    --port N        listen on N (beats LGS_TT_PORT, which beats config)
    --no-browser    headless: do not open a browser window on start

The single instance is enforced with a named Windows mutex rather than a
lockfile or a port probe: the OS releases a mutex the instant its process
dies (no stale-file logic), and the Global\\ namespace makes it hold across
sessions — a second copy started by a logged-in user is refused even while
the scheduled task runs the first copy as SYSTEM. A port probe was rejected
because it cannot tell "the tool is already up" from "another program took
the port", and those need different messages.
"""
import ctypes
import multiprocessing
import os
import sys

_MUTEX_NAME = "Global\\LGS-Test-Tool"
_ERROR_ALREADY_EXISTS = 183

# Held for the life of the process, released by the OS at exit. The
# reference must survive run() or the mutex would be garbage-collected away.
_instance_mutex = None


def _parse_flags() -> None:
    """Stash the flags into the env vars app.main already understands."""
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--port" and i + 1 < len(args):
            os.environ["LGS_TT_PORT"] = args[i + 1]
            i += 2
        elif args[i].startswith("--port="):
            os.environ["LGS_TT_PORT"] = args[i].split("=", 1)[1]
            i += 1
        elif args[i] == "--no-browser":
            os.environ["LGS_TT_NO_BROWSER"] = "1"
            i += 1
        else:
            print(f"unknown option: {args[i]}  (known: --port N, --no-browser)")
            raise SystemExit(2)


def _acquire_single_instance() -> bool:
    """True when this is the only copy; False when one is already up."""
    global _instance_mutex
    if os.name != "nt":                       # dev convenience (Docker/CI)
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _instance_mutex = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    return ctypes.get_last_error() != _ERROR_ALREADY_EXISTS


if __name__ == "__main__":
    multiprocessing.freeze_support()
    _parse_flags()
    if not _acquire_single_instance():
        # For someone double-clicking the exe a second time, "it is already
        # running" is success — point them at it and leave quietly. A second
        # Modbus worker fighting over the COM port / TCP slot is the thing
        # this exit prevents.
        port = os.environ.get("LGS_TT_PORT", "").strip() or "8080"
        url = f"http://localhost:{port}"
        print(f"LGS Test Tool is already running — {url}")
        if os.environ.get("LGS_TT_NO_BROWSER") != "1":
            import webbrowser
            webbrowser.open(url)
        raise SystemExit(0)
    from app.main import run
    run()
