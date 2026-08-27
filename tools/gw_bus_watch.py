"""Log the GATEWAY's own account of the bus, to run beside a soak.

    python tools/gw_bus_watch.py 192.168.0.202 [--every 30] [--out FILE.csv]

Why this exists. The soak sees the bus through a client timeout: a read that
takes 3,578 ms is 3.5 s of silence plus a retry that worked, and from the PC
there is no way to tell "the module never answered" from "my request never got
there". On 2026-08-27 the gateway settled it in one read -- `cnt.rs485_timeout`
was 3,820 against the CSV's 3,821 slow rows, so the losses were real RS485
timeouts, the gateway had asked and nothing answered inside its 300 ms window.

That number was only available after the fact, as a running total. Sampled once
a pass it becomes a time series that lines up with the soak's own CSV, and the
questions that took a day of guessing this time get answered by reading two
columns side by side:

  rs485_timeout  climbing while the soak logs slow rows  -> the module is quiet
  tcp_ok         climbing without rs485_ok               -> the gateway is the stall
  cross          climbing faster than the soak's own     -> something else is
                                                            moving the hub
  skip           anything but zero                       -> a crossing gave up
                                                            without asking:
                                                            budget too tight
  wait_ms        rising share of elapsed                 -> settle is eating the
                                                            run; check hub.settle

It is deliberately a separate process from the soak: one FC41 round trip every
30 s, no shared state, and nothing it can do will disturb the run it watches.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymodbus.client import ModbusTcpClient                    # noqa: E402

from app.gateway_tcp import GatewayTcpLink, register_pdu       # noqa: E402

# The gateway prints these as `cnt.rs485_ok=...` etc. Digits inside the key are
# why a plain [a-z_]+ pattern silently drops the two that matter most.
FIELD = re.compile(r"([a-z_]+\.[a-z0-9_]+)=(\S+)")

COLUMNS = ("sys.up", "cnt.tcp_ok", "cnt.rs485_ok", "cnt.rs485_timeout",
           "hub.cross", "hub.extra", "hub.wait_ms", "hub.skip",
           "net.client", "rtt.last_ms", "rtt.max_ms", "rtt.consec_timeout")


def sample(link: GatewayTcpLink) -> dict:
    res = link.command("INFO")
    if not res.ok:
        raise RuntimeError(res.err or "INFO refused")
    out: dict = {}
    for line in res.lines:
        out.update(dict(FIELD.findall(line)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("host")
    ap.add_argument("--port", type=int, default=502)
    ap.add_argument("--every", type=float, default=30.0, help="seconds between samples")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    out = Path(args.out or f"gwbus-{datetime.now():%Y%m%d-%H%M}.csv")
    client = ModbusTcpClient(host=args.host, port=args.port, timeout=5.0, retries=1)
    register_pdu(client)
    if not client.connect():
        print(f"cannot reach {args.host}:{args.port}", file=sys.stderr)
        return 1

    link = GatewayTcpLink(client)
    prev: dict = {}
    # Deltas as well as totals: a total tells you the run's damage, a delta
    # tells you WHEN, and lining the delta up against the soak CSV is the
    # whole point.
    head = ["time"] + list(COLUMNS) + [f"d_{c.split('.')[1]}" for c in COLUMNS
                                       if c != "sys.up"]
    with out.open("w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(head) + "\n")
        fh.flush()
        print(f"writing {out}  (Ctrl-C to stop)")
        try:
            while True:
                try:
                    now = sample(link)
                except Exception as exc:                     # noqa: BLE001
                    # A soak is a long night; one refused INFO must not end the
                    # watch. Say so in the file and keep going.
                    fh.write(f"{datetime.now():%Y-%m-%d %H:%M:%S},"
                             f"ERROR {str(exc)[:60].replace(',', ' ')}\n")
                    fh.flush()
                    time.sleep(args.every)
                    continue
                row = [f"{datetime.now():%Y-%m-%d %H:%M:%S}"]
                row += [now.get(c, "") for c in COLUMNS]
                for c in COLUMNS:
                    if c == "sys.up":
                        continue
                    try:
                        row.append(str(int(now[c]) - int(prev[c])))
                    except (KeyError, ValueError):
                        row.append("")
                fh.write(",".join(row) + "\n")
                fh.flush()
                prev = now
                time.sleep(args.every)
        except KeyboardInterrupt:
            print("\nstopped")
        finally:
            client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
