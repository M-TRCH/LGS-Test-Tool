"""Send live soak results to the LGS Soak Monitor web dashboard.

Runs beside LGS Test Tool on the test server and never touches the tool or
its files beyond reading them: every `interval_s` it looks in the exports
folder for soak-*.csv files written in the last `max_age_hours`, and for each
one posts

  * the summary from app.soak_csv.parse_soak_csv() -- the same reading the
    site report uses, so the dashboard and the PDF can never disagree about
    whether a reboot was the scheduled reset or a fault, and
  * the CSV lines it has not sent yet, numbered by line, so a restart or a
    dropped connection resumes exactly where the server's copy ends.

A run that is still going is posted every pass even when no line was added:
that is how the dashboard tells "quiet cabinet" from "the PC went to sleep".
Only complete lines are sent; the line the tool is half-way through writing
waits for the next pass.

Settings live in soak_uploader.ini in the tool's data folder (next to
config.json). A missing file is created with blanks and the uploader exits,
saying what to fill in:

    [monitor]
    url = https://lgs.teerachot.cc
    token = <INGEST_TOKEN from the Worker>

    [source]
    exports_dir =            ; blank = <data folder>/exports
    interval_s = 30
    max_age_hours = 24

Usage:
    python tools/soak_uploader.py            # run until stopped
    python tools/soak_uploader.py --once     # one pass, then exit (testing)
"""
from __future__ import annotations

import argparse
import configparser
import json
import logging
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from logging.handlers import RotatingFileHandler
from pathlib import Path

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config_store  # noqa: E402  (stdlib-only module)
from app.soak_csv import SoakCsvError, parse_soak_csv  # noqa: E402

VERSION = "1.0.3"
CONFIG_NAME = "soak_uploader.ini"
BATCH_ROWS = 500            # lines per POST; the Worker accepts up to 1000
MAX_BATCHES_PER_PASS = 40   # catch-up cap per file per pass (20,000 lines)
HTTP_TIMEOUT_S = 20
TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{32,128}")

# soak-<cabinet>-<YYYYMMDD-HHMMSS>.csv from a fleet run; the Soak tab's own
# file is soak-<YYYYMMDD-HHMM>.csv and has no cabinet name.
_FLEET_NAME = re.compile(r"^soak-(.+)-(\d{8}-\d{4,6})\.csv$")

log = logging.getLogger("soak_uploader")


# ------------------------------------------------------------------ config

class Settings:
    def __init__(self, path: Path):
        cp = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
        cp.read(path, encoding="utf-8-sig")   # Notepad saves with a BOM
        self.url = cp.get("monitor", "url", fallback="https://lgs.teerachot.cc").rstrip("/")
        self.token = cp.get("monitor", "token", fallback="").strip()
        # A scheduled task running as SYSTEM does not inherit the logged-in
        # user's proxy, so a company proxy has to be named here.
        self.proxy = cp.get("monitor", "proxy", fallback="").strip()
        exports = cp.get("source", "exports_dir", fallback="").strip()
        self.exports = Path(exports) if exports else config_store.data_dir() / "exports"
        self.interval_s = max(5.0, cp.getfloat("source", "interval_s", fallback=30.0))
        self.max_age_s = max(1.0, cp.getfloat("source", "max_age_hours", fallback=24.0)) * 3600


def write_template(path: Path) -> None:
    path.write_text(
        "[monitor]\n"
        "url = https://lgs.teerachot.cc\n"
        "; the INGEST_TOKEN secret of the lgs-monitor Worker\n"
        "token =\n"
        "; company proxy if this PC needs one, e.g. http://proxy.example.local:8080\n"
        "; blank = use the system / environment setting\n"
        "proxy =\n"
        "\n"
        "[source]\n"
        "; blank = the exports folder inside LGS Test Tool's data folder\n"
        "exports_dir =\n"
        "interval_s = 30\n"
        "max_age_hours = 24\n",
        encoding="utf-8",
    )


# ------------------------------------------------------------------ HTTP

class AuthError(RuntimeError):
    pass


class Client:
    def __init__(self, settings: Settings):
        self.s = settings
        self.host = socket.gethostname()
        if settings.proxy:
            proxies = {"http": settings.proxy, "https": settings.proxy}
        else:
            proxies = urllib.request.getproxies()
        self.proxy_desc = ", ".join(f"{k}={v}" for k, v in proxies.items()) or "none (direct)"
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.s.token}",
            "User-Agent": f"lgs-soak-uploader/{VERSION}",
        }
        data = None
        if body is not None:
            data = json.dumps(body, default=str).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.s.url + path, data=data, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=HTTP_TIMEOUT_S) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # Name who answered: "Server: cloudflare" is the monitor itself;
            # anything else (or nothing) is a proxy or firewall on the way.
            server = e.headers.get("Server") or "-"
            via = e.headers.get("Via")
            if e.code == 401 and server.lower() == "cloudflare":
                raise AuthError("server rejected the token (401) - check [monitor] token") from None
            detail = e.read()[:200].decode("utf-8", "replace").strip() or "(empty body)"
            who = f"server={server}" + (f" via={via}" if via else "")
            raise RuntimeError(f"HTTP {e.code} from {path} [{who}, proxy {self.proxy_desc}]: {detail}") from None

    def check(self) -> None:
        """Prove the URL and token work before anything else. Without this a
        pass that finds no soak files sends nothing at all, and a wrong token
        or a blocked network looks exactly like a quiet day."""
        self.cursor("soak-uploader-check.csv")

    def cursor(self, run_id: str) -> int:
        q = urllib.parse.urlencode({"run": run_id})
        return int(self._request("GET", f"/api/ingest/cursor?{q}").get("rows_total", 0))

    def post(self, run: dict, rows: list, rows_through: int, file_age_s: float) -> int:
        res = self._request("POST", "/api/ingest", {
            "uploader": self.host, "file_age_s": round(file_age_s, 1),
            "run": run, "rows": rows, "rows_through": rows_through,
        })
        return int(res.get("rows_total", rows_through))


# ------------------------------------------------------------------ one file

def summary_dict(summary) -> dict:
    d = asdict(summary)
    d["duration_s"] = summary.duration_s
    d["unexplained_reboots"] = summary.unexplained_reboots
    d["headline"] = summary.headline()
    d["trouble"] = d["trouble"][:50]
    return d


def split_row(seq: int, line: str):
    parts = line.rstrip("\r").split(",", 3)
    if len(parts) != 4:
        return None
    ts, dev, kind, detail = parts
    try:
        dev_id = int(dev)
    except ValueError:
        return None
    if len(ts) != 19:
        return None
    return [seq, ts, dev_id, kind, detail]


class Tracker:
    """What has been sent for each file, so finished runs stop costing requests."""

    def __init__(self, client: Client):
        self.client = client
        self.sent: dict[str, int] = {}     # run id -> rows the server has
        self.done: set[str] = set()        # finished and fully sent
        self.last_seen = None              # what the last pass found, for the log

    def pass_file(self, path: Path) -> None:
        run_id = path.name
        if run_id in self.done:
            return
        st = path.stat()
        file_age_s = max(0.0, time.time() - st.st_mtime)
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
            text = fh.read()
        # Only lines that end in a newline are complete; the tool may be
        # half-way through the last one.
        lines = text.split("\n")[:-1]
        if len(lines) < 2:
            return
        try:
            summary = parse_soak_csv("\n".join(lines), filename=run_id)
        except SoakCsvError as e:
            log.debug("%s: skipped (%s)", run_id, e)
            return

        m = _FLEET_NAME.match(run_id)
        run = {
            "id": run_id,
            "cabinet": m.group(1) if m else "",
            "started": summary.started,
            "last_row": summary.ended,
            "finished": summary.finished,
            "config": summary.config,
            "summary": summary_dict(summary),
        }

        if run_id not in self.sent:
            self.sent[run_id] = self.client.cursor(run_id)
            log.info("%s: server has %d of %d lines", run_id, self.sent[run_id], len(lines) - 1)

        last = len(lines) - 1                  # header is line 0
        if self.sent[run_id] >= last:
            if summary.finished:
                self.done.add(run_id)          # the server already has all of it
            else:
                # Nothing new, but still running: say so, so the dashboard
                # can tell a quiet cabinet from a silent uploader.
                self.client.post(run, [], last, file_age_s)
            return

        for _ in range(MAX_BATCHES_PER_PASS):
            start = self.sent[run_id] + 1
            end = min(last, start + BATCH_ROWS - 1)
            rows = [r for r in (split_row(i, lines[i]) for i in range(start, end + 1)) if r]
            self.sent[run_id] = max(end, self.client.post(run, rows, end, file_age_s))
            if self.sent[run_id] >= last:
                break
        if summary.finished and self.sent[run_id] >= last:
            log.info("%s: finished, all %d lines sent", run_id, last)
            self.done.add(run_id)


# ------------------------------------------------------------------ main loop

def candidates(settings: Settings) -> list[Path]:
    if not settings.exports.is_dir():
        return []
    cutoff = time.time() - settings.max_age_s
    files = [p for p in settings.exports.glob("soak-*.csv") if p.stat().st_mtime >= cutoff]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def run_pass(settings: Settings, tracker: Tracker) -> None:
    files = candidates(settings)
    # Say what was found whenever it changes -- the first question when the
    # dashboard is empty is always "is it even looking in the right place?"
    seen = (settings.exports.is_dir(), tuple(p.name for p in files))
    if seen != tracker.last_seen:
        tracker.last_seen = seen
        if not seen[0]:
            log.warning("exports folder does not exist: %s", settings.exports)
        elif not files:
            log.info("no soak-*.csv changed in the last %.0f h in %s", settings.max_age_s / 3600, settings.exports)
        else:
            log.info("%d soak file(s): %s", len(files), ", ".join(seen[1]))
    for path in files:
        try:
            tracker.pass_file(path)
        except AuthError:
            raise
        except (OSError, RuntimeError, ValueError) as e:
            # One bad file or one failed request must not stop the others;
            # the cursor is unchanged, so the next pass retries from there.
            log.warning("%s: %s", path.name, e)


def setup_logging(log_path: Path, verbose: bool) -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    fh = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)
    if sys.stderr is not None:            # a windowless exe has no console
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(sh)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Send live soak results to the LGS Soak Monitor.")
    ap.add_argument("--config", type=Path, help=f"settings file (default: <data folder>/{CONFIG_NAME})")
    ap.add_argument("--once", action="store_true", help="one pass, then exit")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    data = config_store.data_dir()
    cfg_path = args.config or data / CONFIG_NAME
    setup_logging(data / "soak_uploader.log", args.verbose)

    if not cfg_path.exists():
        write_template(cfg_path)
        log.error("created %s - fill in [monitor] token, then start again", cfg_path)
        return 2
    settings = Settings(cfg_path)
    if not settings.token:
        log.error("%s has no [monitor] token", cfg_path)
        return 2
    # The token is URL-safe base64. Anything else -- most often a literal ^V
    # left by Ctrl+V in a hidden PowerShell prompt -- makes Cloudflare answer
    # 400 with an empty body before the request ever reaches the monitor.
    if not TOKEN_RE.fullmatch(settings.token):
        bad = sorted({f"U+{ord(c):04X}" for c in settings.token if not re.fullmatch(r"[A-Za-z0-9_-]", c)})
        log.error("[monitor] token in %s is not valid (length %d, bad characters: %s) - paste it again",
                  cfg_path, len(settings.token), ", ".join(bad) or "none, wrong length")
        return 4

    log.info("soak uploader %s -> %s, watching %s every %.0f s", VERSION, settings.url, settings.exports, settings.interval_s)
    client = Client(settings)
    log.info("proxy: %s", client.proxy_desc)
    while True:
        try:
            client.check()
            log.info("monitor reachable, token accepted")
            break
        except AuthError as e:
            log.error("%s", e)
            if args.once:
                return 1
            time.sleep(300)
        except (OSError, RuntimeError, ValueError) as e:
            # At boot the network may not be up yet; keep trying.
            log.warning("cannot reach %s: %s", settings.url, e)
            if args.once:
                return 3
            time.sleep(settings.interval_s)
    tracker = Tracker(client)
    while True:
        started = time.monotonic()
        try:
            run_pass(settings, tracker)
        except AuthError as e:
            log.error("%s", e)
            if args.once:
                return 1
            time.sleep(300)               # a wrong token will not fix itself in 30 s
            continue
        if args.once:
            return 0
        time.sleep(max(1.0, settings.interval_s - (time.monotonic() - started)))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
