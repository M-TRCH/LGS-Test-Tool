"""Check the fleet run's naming and its refusal rules, without a network.

    python tools/soak_fleet_selftest.py

The cabinet name looks like a cosmetic field and is not one: it names the
CSV, and a fleet run writes one file per cabinet at the same instant. Two
cabinets that reduce to the same filename means two threads opening one path
with "w" and interleaving their rows — a file that parses cleanly and
describes a machine that does not exist. That is the worst shape a bug can
take in this project, so the stem rules are pinned here.

The other half is the cardinal rule: one Modbus master per RS485 bus. The
gateway takes two TCP clients and has one bus behind them, so two fleet rows
aimed at one gateway is the same fault the tool refuses from outsiders,
committed by the tool itself.
"""
import logging
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import framer_watch, soak_fleet                          # noqa: E402


def cab(name, host="192.168.0.204"):
    return soak_fleet.FleetCabinet(name=name, host=host, ids=(11, 12))


# ── the stem ───────────────────────────────────────────────────────────────
def case_thai_survives():
    """A Thai name must stay readable.

    The old rule kept isalnum() characters, and Thai vowel/tone marks are
    combining marks rather than alphanumerics: "ตู้ 80" became "ต---80".
    """
    got = soak_fleet.safe_stem("ตู้ 80")
    if got != "ตู้ 80":
        return f"Thai name mangled to {got!r}"
    if soak_fleet.safe_stem("ห้องยา ชั้น 3") != "ห้องยา ชั้น 3":
        return "Thai with a space and a digit was altered"
    return None


def case_illegal_chars_go():
    for raw, want in (('a/b', 'a-b'), ('a:b', 'a-b'), ('a*b?', 'a-b-'),
                      ('a<b>c', 'a-b-c'), ('a|b', 'a-b'), ('a\\b', 'a-b')):
        got = soak_fleet.safe_stem(raw)
        if got != want:
            return f"{raw!r} -> {got!r}, expected {want!r}"
    if soak_fleet.safe_stem("") != "cabinet":
        return "an empty name must fall back to something"
    if soak_fleet.safe_stem("  . ") != "cabinet":
        return "a name of only dots and spaces must fall back"
    return None


def case_trailing_dot_and_space():
    """Windows silently drops a trailing dot or space from a filename, so
    "Chest " and "Chest" would resolve to one file on disk."""
    if soak_fleet.safe_stem("Chest ") != "Chest":
        return "trailing space kept"
    if soak_fleet.safe_stem("Chest.") != "Chest":
        return "trailing dot kept"
    return None


# ── the files ──────────────────────────────────────────────────────────────
def _paths(names, hosts=None, tmp=None):
    """Run the path allocation the way run_fleet does, without threads."""
    import tempfile
    from datetime import datetime
    hosts = hosts or [f"10.0.0.{i}" for i in range(len(names))]
    cabs = [cab(n, h) for n, h in zip(names, hosts)]
    log_dir = Path(tmp or tempfile.mkdtemp())
    stamp = f"{datetime.now():%Y%m%d-%H%M}"
    # mirrors run_fleet's pre-thread allocation
    out, used = [], set()
    for c in cabs:
        stem = soak_fleet.safe_stem(c.name)
        cand = f"soak-{stem}-{stamp}.csv"
        if cand in used:
            stem = f"{stem}-{soak_fleet.safe_stem(c.host)}"
            cand = f"soak-{stem}-{stamp}.csv"
        n = 2
        while cand in used:
            cand = f"soak-{stem}-{n}-{stamp}.csv"
            n += 1
        used.add(cand)
        out.append(cand)
    return out


def case_colliding_names_get_distinct_files():
    """The names differ; the stems do not. The files still must."""
    got = _paths(["Chest Std 02", "Chest-Std-02", "Chest/Std/02"])
    if len(set(got)) != 3:
        return f"three cabinets produced {len(set(got))} distinct files: {got}"
    return None


def case_identical_names_get_distinct_files():
    got = _paths(["Chest", "Chest", "Chest"],
                 ["10.0.0.1", "10.0.0.2", "10.0.0.3"])
    if len(set(got)) != 3:
        return f"same name three times gave {len(set(got))} files: {got}"
    # The tie-break appends the host, which stays legible: a dot is legal in
    # a filename (only a TRAILING one is stripped by Windows), so there is no
    # reason to mangle an address into 10-0-0-2.
    if not any("10.0.0.2" in g for g in got):
        return f"the tie-break should name the host: {got}"
    return None


def case_empty_names_get_distinct_files():
    got = _paths(["", "", ""], ["10.0.0.1", "10.0.0.2", "10.0.0.3"])
    if len(set(got)) != 3:
        return f"three blank names gave {len(set(got))} files: {got}"
    return None


# ── the bus ────────────────────────────────────────────────────────────────
def case_duplicate_gateway_is_named():
    cabs = [cab("A", "192.168.0.204"), cab("B", "192.168.0.204"),
            cab("C", "192.168.0.205")]
    dupes = soak_fleet.duplicate_hosts(cabs)
    if dupes != ["192.168.0.204"]:
        return f"duplicate_hosts returned {dupes}"
    if soak_fleet.duplicate_hosts([cab("A", "1.1.1.1"), cab("B", "2.2.2.2")]):
        return "two distinct gateways were reported as duplicates"
    return None


def case_duplicate_is_host_AND_port():
    """The bus is behind a GATEWAY, not behind an address.

    Two gateways reached at one IP on different ports -- port forwarding, or
    a test harness on loopback -- are two gateways and two buses. Refusing
    them was wrong, and it blocked the 13-cabinet scale test outright.
    """
    same_ip = [soak_fleet.FleetCabinet("A", "127.0.0.1", (11,), port=5021),
               soak_fleet.FleetCabinet("B", "127.0.0.1", (11,), port=5022)]
    if soak_fleet.duplicate_hosts(same_ip):
        return "refused two gateways that differ by port"
    same_both = [soak_fleet.FleetCabinet("A", "10.0.0.1", (11,), port=502),
                 soak_fleet.FleetCabinet("B", "10.0.0.1", (11,), port=502)]
    if not soak_fleet.duplicate_hosts(same_both):
        return "allowed the SAME gateway twice -- two masters on one bus"
    return None


def case_conflict_with_main_connection():
    cabs = [cab("A", "192.168.0.204"), cab("B", "192.168.0.205")]
    if soak_fleet.conflicting_hosts(cabs, "192.168.0.204") != ["A"]:
        return "the cabinet sharing the tool's own connection was not named"
    if soak_fleet.conflicting_hosts(cabs, None):
        return "nothing is connected, so nothing can conflict"
    return None


# ── the two-masters guard ──────────────────────────────────────────────────
class _FakeRes:
    def __init__(self, peers, ok=True):
        self.ok = ok
        self.lines = [f"#DATA net.state=up net.client=1 net.peer={peers}"]


def _guard(peers, mine="192.168.0.10", console=True):
    """Run _other_master against a scripted INFO answer."""
    import app.soak_fleet as F
    import app.gateway_tcp as G

    real_link, real_reg, real_ip = G.GatewayTcpLink, G.register_pdu, F.local_ip_toward

    class Link:
        def __init__(self, _c): pass
        def command(self, _v): return _FakeRes(peers, console)

    G.GatewayTcpLink = Link
    G.register_pdu = lambda _c: None
    F.local_ip_toward = lambda _h: mine
    try:
        return F._other_master(object(), "192.168.0.204")
    finally:
        G.GatewayTcpLink, G.register_pdu, F.local_ip_toward = real_link, real_reg, real_ip


def case_guard_allows_our_own_socket():
    """The connection the question is asked OVER must not be the answer.

    This has been wrong twice. First it compared `net.peer` -- the gateway's
    CLIENT source addresses -- against the GATEWAY's address, which can never
    match. Then it compared against the MAIN connection's host, which is None
    whenever the operator has not pressed Connect, so `mine` was empty and
    every peer survived the filter. On 2026-09-17 that refused BOTH cabinets
    of a fleet run: the guard was seeing its own socket.
    """
    v = _guard("192.168.0.10:9040")
    if v is not None:
        return f"refused a gateway where the only client is us: {v!r}"
    return None


def case_guard_still_catches_a_stranger():
    v = _guard("192.168.0.10:9040,192.168.0.87:52189")
    if v is None:
        return "a second master from another PC was not reported"
    if "192.168.0.87" not in v:
        return f"the stranger was not named: {v!r}"
    if "192.168.0.10" in v:
        return f"our own socket was reported as a stranger: {v!r}"
    return None


def case_guard_catches_a_second_local_client():
    """Two tool instances on one PC are still two masters on one bus, so
    exactly ONE peer matching our address may be dropped -- not all of them."""
    v = _guard("192.168.0.10:9040,192.168.0.10:9099")
    if v is None:
        return "a second client from this same PC was not reported"
    return None


def case_guard_is_quiet_without_a_console():
    if _guard("192.168.0.87:1", console=False) is not None:
        return "a gateway with no console must not produce a verdict"
    if _guard("-") is not None:
        return "an empty peer list must not produce a verdict"
    return None


# ── the saved roster ───────────────────────────────────────────────────────
KNOWN = {"lgs40", "lgs56", "lgs64", "lgs80", "smt"}


def case_roster_round_trips():
    rows = [("Chest-Std-02", "192.168.0.204", "lgs80"),
            ("ตู้ 56", "192.168.0.203", "lgs56"),
            ("", "192.168.0.202", "lgs64")]
    saved = soak_fleet.roster_to_config(rows)
    back = soak_fleet.roster_from_config(saved, KNOWN)
    if back != rows:
        return f"round trip changed the roster: {back}"
    return None


def case_roster_survives_a_mangled_config():
    """Read at page build, so it must never raise: config.json can be
    hand-edited, written by another version, or half-written by a machine
    that lost power. An exception here takes the whole Soak tab with it."""
    junk = ["", "   ", None, 42, [], {"host": "x"},
            "no-pipes-at-all", "A|10.0.0.1", "A|10.0.0.1|lgs999",
            "A|B|lgs80|extra", "|10.0.0.2|lgs64", "name-only||lgs80"]
    try:
        got = soak_fleet.roster_from_config(junk, KNOWN)
    except Exception as exc:                                      # noqa: BLE001
        return f"raised on a mangled config: {type(exc).__name__}: {exc}"
    for name, host, key in got:
        if key not in KNOWN:
            return f"passed through an unknown cabinet key {key!r} -- "                   "ui.select cannot render a value absent from its options"
        if not host:
            return f"kept a row with no gateway: {(name, host, key)!r}"
    if not any(h == "10.0.0.1" for _n, h, _k in got):
        return f"threw away a recoverable row: {got}"
    return None


def case_roster_handles_none():
    if soak_fleet.roster_from_config(None, KNOWN) != []:
        return "a missing roster must read as empty, not raise"
    if soak_fleet.roster_to_config([]) != []:
        return "an empty card must save as an empty roster"
    return None


# ── the verdict ────────────────────────────────────────────────────────────
# A weekend run is read on Tuesday by someone who was not there, so the
# summary IS the product. Two things it has to get right: a cabinet that
# never ran must not be counted clean, and the discarded-frame count must
# reach the text -- that is the number which let the 2026-09-22 run report
# zero failures while the bus lost sync twelve times.
def _tallies():
    ran = soak_fleet.CabinetTally(name="Queen", modules=64, passes=40,
                                  reads=2560)
    dirty = soak_fleet.CabinetTally(name="Chest-Std-04", modules=80, passes=38,
                                    reads=3040, fails=2)
    dirty.silent.add(88)
    never = soak_fleet.CabinetTally(name="Chest-Std-05", modules=80,
                                    note="cannot reach 192.168.0.232:502")
    quiet = soak_fleet.CabinetTally(name="Chest-Std-09", modules=40, passes=5,
                                    reads=200)
    quiet.silent.add(33)
    return ran, dirty, never, quiet


def case_clean_means_ran_and_answered():
    ran, dirty, never, quiet = _tallies()
    if never.ran:
        return "a cabinet with no passes counted as having run"
    for tally, why in ((never, "never ran"), (dirty, "had failures"),
                       (quiet, "had a silent module")):
        if tally.clean:
            return f"{tally.name} counted clean although it {why}"
    if not ran.clean:
        return "a cabinet with no failures and no silence was not clean"
    return None


def case_summary_judges_the_run():
    framer_watch.reset()
    text = soak_fleet.summarise(_tallies(), framer_watch.snapshot(),
                                started="2026-09-25 10:58:56",
                                duration_s=3600.0)
    if "1 of 4 cabinets completely clean" not in text:
        return f"verdict line wrong:{NL}{text}"
    if "did not run" not in text or "192.168.0.232" not in text:
        return "a cabinet that never ran does not say so, with its reason"
    if "88" not in text:
        return "silent ids never reach the table"
    if "discarded as the wrong unit id: none" not in text:
        return "a quiet framer is omitted rather than stated"
    return None


def case_discarded_frames_reach_the_summary():
    """And are filed against the cabinet whose thread saw them.

    run_fleet names one thread per cabinet, which is the only thing tying a
    pymodbus log line -- it carries no cabinet, no host, nothing -- to the
    gateway it came from.
    """
    framer_watch.start()
    framer_watch.reset()
    th = threading.Thread(
        target=lambda: logging.getLogger("pymodbus.logging").error(
            "ERROR: request ask for id=42 but got id=41, Skipping."),
        name=framer_watch.owner_for("Chest-Std-04"))
    th.start()
    th.join()
    ran, dirty, _never, _quiet = _tallies()
    text = soak_fleet.summarise([ran, dirty], framer_watch.snapshot(),
                                started="x", duration_s=60.0)
    framer_watch.reset()
    if "discarded as the wrong unit id: 1" not in text:
        return f"the count never reached the summary:{NL}{text}"
    row = [ln for ln in text.splitlines() if "Chest-Std-04" in ln][0]
    if row.split()[-2] != "1":
        return f"not filed against the right cabinet: {row!r}"
    if [ln for ln in text.splitlines() if ln.startswith("Queen")][0].split()[-2] != "0":
        return "a cabinet that saw none was charged for it"
    return None


CASES = (
    ("thai name survives", case_thai_survives),
    ("illegal chars removed", case_illegal_chars_go),
    ("trailing dot and space", case_trailing_dot_and_space),
    ("colliding names -> files", case_colliding_names_get_distinct_files),
    ("identical names -> files", case_identical_names_get_distinct_files),
    ("blank names -> files", case_empty_names_get_distinct_files),
    ("duplicate gateway named", case_duplicate_gateway_is_named),
    ("duplicate is host+port", case_duplicate_is_host_AND_port),
    ("guard allows our socket", case_guard_allows_our_own_socket),
    ("guard catches a stranger", case_guard_still_catches_a_stranger),
    ("guard catches 2nd local", case_guard_catches_a_second_local_client),
    ("guard quiet w/o console", case_guard_is_quiet_without_a_console),
    ("roster round-trips", case_roster_round_trips),
    ("roster survives junk", case_roster_survives_a_mangled_config),
    ("roster handles None", case_roster_handles_none),
    ("conflict with main conn", case_conflict_with_main_connection),
    ("clean means ran+answered", case_clean_means_ran_and_answered),
    ("the summary judges it", case_summary_judges_the_run),
    ("discarded frames counted", case_discarded_frames_reach_the_summary),
)


def main() -> int:
    failures = 0
    for name, fn in CASES:
        try:
            problem = fn()
        except Exception as exc:                                  # noqa: BLE001
            problem = f"{type(exc).__name__}: {exc}"
        print(f"{name:26} {'FAIL' if problem else 'ok'}")
        if problem:
            print(f"                           - {problem}")
            failures += 1
    print(f"\n{len(CASES) - failures}/{len(CASES)} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
