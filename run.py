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
_ERROR_ACCESS_DENIED = 5

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
        elif args[i] == "--port":
            print("--port needs a value, e.g. --port 8090")
            raise SystemExit(2)
        else:
            print(f"unknown option: {args[i]}  (known: --port N, --no-browser)")
            raise SystemExit(2)


def _acquire_single_instance() -> bool:
    """True when this is the only copy; False when one is already up."""
    global _instance_mutex
    if os.name != "nt":                       # dev convenience (Docker/CI)
        return True
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    # ctypes defaults restype to c_int (32-bit); a HANDLE is pointer-sized.
    # The handle is never used again, but a truncated one could read as 0
    # and hide a real failure — declare the widths properly.
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int,
                                      ctypes.c_wchar_p)
    _instance_mutex = kernel32.CreateMutexW(None, False, _MUTEX_NAME)
    err = ctypes.get_last_error()
    # ACCESS_DENIED is ALSO "already running": when the scheduled task holds
    # the mutex as SYSTEM, a standard user's CreateMutexW fails with error 5
    # instead of 183 (the mutex exists but its DACL refuses this caller).
    # Treating that as "not running" would boot a second full copy -- two
    # Modbus workers, and one Connect press steals the Opta's single TCP
    # slot from the server copy. Exactly the scenario the mutex exists for.
    return err not in (_ERROR_ALREADY_EXISTS, _ERROR_ACCESS_DENIED)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    _parse_flags()
    if not _acquire_single_instance():
        # For someone double-clicking the exe a second time, "it is already
        # running" is success — point them at it and leave quietly. A second
        # Modbus worker fighting over the COM port / TCP slot is the thing
        # this exit prevents.
        # Best-effort guess at the running copy's port: our flag/env first,
        # then the config file. A scheduled task's --port is stored nowhere
        # we can read, so this can be wrong -- say "probably", not certainty.
        port = os.environ.get("LGS_TT_PORT", "").strip()
        if not port:
            try:
                import json
                base = (os.path.dirname(sys.executable)
                        if getattr(sys, "frozen", False)
                        else os.path.dirname(os.path.abspath(__file__)))
                with open(os.path.join(base, "data", "config.json"),
                          encoding="utf-8-sig") as fh:
                    port = str(json.load(fh).get("web_port", "") or "")
            except Exception:
                port = ""
        url = f"http://localhost:{port or 8080}"
        print(f"LGS Test Tool is already running — probably at {url}")
        if os.environ.get("LGS_TT_NO_BROWSER") != "1":
            import webbrowser
            webbrowser.open(url)
        raise SystemExit(0)
    from app.main import run
    run()
