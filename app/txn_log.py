"""Thread-safe transaction log: ring buffer + CSV export."""
from __future__ import annotations

import csv
import io
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TxnRecord:
    seq: int
    ts: datetime
    source: str            # manual | monitor | sweep | scan | danger
    fc: int
    addr: int
    device_id: int
    op: str                # read | write
    ok: bool
    raw: object            # int, list, bool or None
    decoded: str
    latency_ms: float
    note: str
    tx_hex: str = ""
    rx_hex: str = ""

    def line(self) -> str:
        status = "OK " if self.ok else "ERR"
        val = f"{self.decoded}" if self.decoded else f"{self.raw}"
        s = (f"{self.ts.strftime('%H:%M:%S.%f')[:-3]} [{self.source:<7}] "
             f"FC{self.fc:02d} id={self.device_id} addr={self.addr} {self.op} "
             f"-> {status} {val} ({self.latency_ms:.1f} ms)")
        if self.note:
            s += f" | {self.note}"
        if self.tx_hex:
            s += f" | TX {self.tx_hex}"
        if self.rx_hex:
            s += f" | RX {self.rx_hex}"
        return s


CSV_COLUMNS = ["timestamp", "source", "fc", "addr", "device_id", "op",
               "ok", "raw", "decoded", "latency_ms", "note", "tx_hex", "rx_hex"]


@dataclass
class TxnLog:
    maxlen: int = 2000
    _buf: deque = field(default_factory=lambda: deque(maxlen=2000))
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _seq: int = 0

    def append(self, source: str, fc: int, addr: int, device_id: int, op: str,
               ok: bool, raw, decoded: str, latency_ms: float, note: str = "",
               tx_hex: str = "", rx_hex: str = "") -> TxnRecord:
        with self._lock:
            self._seq += 1
            rec = TxnRecord(self._seq, datetime.now(), source, fc, addr, device_id,
                            op, ok, raw, decoded, latency_ms, note, tx_hex, rx_hex)
            self._buf.append(rec)
            return rec

    def since(self, seq: int) -> tuple[int, list[TxnRecord]]:
        """Records newer than seq (for incremental UI drains)."""
        with self._lock:
            fresh = [r for r in self._buf if r.seq > seq]
            return (fresh[-1].seq if fresh else seq), fresh

    def clear(self) -> None:
        with self._lock:
            self._buf.clear()

    def to_csv_bytes(self) -> bytes:
        with self._lock:
            rows = list(self._buf)
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(CSV_COLUMNS)
        for r in rows:
            w.writerow([r.ts.isoformat(timespec="milliseconds"), r.source, r.fc,
                        r.addr, r.device_id, r.op, int(r.ok), r.raw, r.decoded,
                        f"{r.latency_ms:.1f}", r.note, r.tx_hex, r.rx_hex])
        return out.getvalue().encode("utf-8-sig")
