"""Shared UI context passed to every builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..config_store import AppConfig
from ..modbus_worker import ModbusWorker, MonitorSnapshot
from ..txn_log import TxnLog


@dataclass
class Ctx:
    worker: ModbusWorker
    log: TxnLog
    cfg: AppConfig
    device_id_getter: object = None            # set by connection_bar
    device_id_setter: object = None            # set by connection_bar
    port_getter: object = None                 # set by connection_bar
    transport_getter: object = None            # set by connection_bar
    latest_snapshot: Optional[MonitorSnapshot] = None
    last_scan_ids: tuple = ()                  # IDs found by the most recent scan

    def device_id(self) -> int:
        return int(self.device_id_getter()) if self.device_id_getter else self.cfg.device_id

    def port(self) -> str:
        return str(self.port_getter()) if self.port_getter else self.cfg.com_port

    def transport(self) -> str:
        return str(self.transport_getter()) if self.transport_getter else self.cfg.transport
