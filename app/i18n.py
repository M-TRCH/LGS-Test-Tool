"""UI translations (English / Thai).

Only prose is translated. Protocol identifiers stay in English in both
languages — coil and register numbers, function codes (FC03/FC05), device
field names from the control table, the transaction log and its hex dumps —
because they must match `LGS-Control-Table.md` and the firmware sources.

`t(key)` reads the language set by `set_language()` at page-build time; the
language button saves the choice and reloads the page, so the whole tree is
rebuilt in the new language.
"""
from __future__ import annotations

LANGUAGES = {"en": "English", "th": "ไทย"}
DEFAULT_LANG = "en"

_lang = DEFAULT_LANG


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in LANGUAGES else DEFAULT_LANG


def current() -> str:
    return _lang


def t(key: str, **fmt) -> str:
    entry = TEXTS.get(key)
    if entry is None:
        return key                                    # missing key is visible, not silent
    text = entry.get(_lang) or entry[DEFAULT_LANG]
    return text.format(**fmt) if fmt else text


TEXTS: dict[str, dict[str, str]] = {
    # ── header / connection ────────────────────────────────────────────────
    "hdr.transport.rtu": {"en": "RTU (COM)", "th": "RTU (COM)"},
    "hdr.transport.tcp": {"en": "TCP", "th": "TCP"},
    "hdr.com_port": {"en": "COM port", "th": "พอร์ต COM"},
    "hdr.baud": {"en": "baud", "th": "baud"},
    "hdr.host": {"en": "Host", "th": "Host"},
    "hdr.port": {"en": "Port", "th": "Port"},
    "hdr.single_client": {"en": "gateway: single client",
                          "th": "gateway: ต่อได้ทีละเครื่อง"},
    "hdr.slave_id": {"en": "Slave ID", "th": "Slave ID"},
    "hdr.quit": {"en": "Quit the app", "th": "ปิดโปรแกรม"},
    "hdr.quit_title": {"en": "Quit LGS Test Tool?", "th": "ปิด LGS Test Tool?"},
    "hdr.quit_body": {"en": "Stops the server for every open tab and closes "
                            "the terminal window. Settings are saved first.",
                      "th": "หยุดเซิร์ฟเวอร์ของทุกแท็บที่เปิดอยู่และปิดหน้าต่าง"
                            "เทอร์มินัลให้เอง ค่าตั้งถูกบันทึกก่อนปิด"},
    "hdr.cabinet": {"en": "Cabinet", "th": "รุ่นตู้"},
    "hdr.cabinet_tip": {"en": "Which cabinet this tool is working on. Every "
                              "whole-cabinet action — installation check, "
                              "firmware survey, the gateway's sweep size — "
                              "follows this one choice, and it is remembered. "
                              "Custom lets you describe your own shape: how "
                              "many rows, and how many slots on each.",
                        "th": "เครื่องมือกำลังทำงานกับตู้รุ่นไหน ปุ่ม \"ทั้งตู้\" ทุกหน้า "
                              "และขนาดตู้ฝั่ง gateway อ้างอิงค่านี้ค่าเดียว "
                              "และจำไว้ให้ข้ามการเปิดโปรแกรม เลือก \"กำหนดเอง\" "
                              "เพื่อระบุทรงตู้เอง: กี่ชั้น และชั้นละกี่ช่อง"},
    "hdr.cabinet_custom": {"en": "Custom…", "th": "กำหนดเอง…"},
    "hdr.custom_title": {"en": "Custom cabinet shape", "th": "ทรงตู้กำหนดเอง"},
    "hdr.custom_body": {"en": "Slots per row, top row first. A dash means the "
                              "row has no modules on the bus.",
                        "th": "จำนวนช่องของแต่ละชั้น เริ่มจากชั้นบนสุด "
                              "ขีดหมายถึงชั้นนั้นไม่มีโมดูลบนบัส"},
    "hdr.custom_count": {"en": "{n} modules", "th": "{n} โมดูล"},
    "hdr.custom_empty": {"en": "At least one row needs at least one slot.",
                         "th": "ต้องมีอย่างน้อยหนึ่งช่องในสักชั้นหนึ่ง"},
    "hdr.custom_ok": {"en": "Use this shape", "th": "ใช้ทรงนี้"},
    "hdr.custom_edit_tip": {"en": "Edit the custom cabinet's shape.",
                            "th": "แก้ไขทรงตู้ที่กำหนดเอง"},
    # Short labels for the header controls, which carry no icons.
    "hdr.rescan": {"en": "Rescan", "th": "ค้นพอร์ต"},
    "hdr.grid": {"en": "Grid", "th": "ผัง"},
    "hdr.theme": {"en": "Theme", "th": "ธีม"},
    "hdr.about": {"en": "About", "th": "เกี่ยวกับ"},
    "hdr.language": {"en": "Language", "th": "ภาษา"},
    "hdr.advanced": {"en": "Advanced", "th": "ขั้นสูง"},
    "hdr.advanced_tip": {
        "en": "Show the installation and maintenance pages — Firmware, "
              "New module, Gateway and Danger. Off, only the four everyday "
              "pages are shown.",
        "th": "แสดงหน้าสำหรับติดตั้งและซ่อมบำรุง — อัปเดตเฟิร์มแวร์ "
              "ติดตั้งโมดูลใหม่ เกตเวย์ และคำสั่งอันตราย "
              "ปิดไว้จะเหลือเฉพาะหน้าใช้งานประจำ 4 หน้า",
    },
    "hdr.reference": {"en": "Control table", "th": "ตารางคำสั่ง"},
    "ref.title": {"en": "LGS control table", "th": "ตารางคำสั่ง LGS"},
    "ref.search": {"en": "Find a register, coil or name",
                   "th": "ค้นหา register, coil หรือชื่อ"},
    "ref.hits": {"en": "{n} row(s)", "th": "{n} รายการ"},
    "ref.source": {"en": "Shipped with the tool — works offline. Source: {url}",
                   "th": "แนบมากับโปรแกรม ใช้ออฟไลน์ได้ · ต้นฉบับ: {url}"},
    "hdr.more_tooltip": {"en": "language, theme and about",
                         "th": "ภาษา ธีม และเกี่ยวกับโปรแกรม"},
    "hdr.grid_tooltip": {"en": "pick a slave ID from the grid (row x 10 + col)",
                         "th": "เลือก Slave ID จากผัง (แถว x 10 + ช่อง)"},
    "hdr.grid_title": {"en": "Grid IDs — row x 10 + col",
                       "th": "รหัสตามผัง — แถว x 10 + ช่อง"},
    "hdr.id_setid": {"en": "{id} (SET_ID mode)", "th": "{id} (โหมด SET_ID)"},
    "hdr.id_factory": {"en": "{id} (factory)", "th": "{id} (ค่าโรงงาน)"},
    "hdr.scan": {"en": "Scan", "th": "สแกน"},
    "hdr.scan.quick": {"en": "Quick (grid 11-108 + 246/247)",
                       "th": "เร็ว (ผัง 11-108 + 246/247)"},
    "hdr.scan.full": {"en": "Full (1-247)", "th": "ทั้งหมด (1-247)"},
    "hdr.connect": {"en": "Connect", "th": "เชื่อมต่อ"},
    "hdr.disconnect": {"en": "Disconnect", "th": "ตัดการเชื่อมต่อ"},
    "hdr.status.idle": {"en": "idle", "th": "ว่าง"},
    "hdr.status.scanning": {"en": "scanning...", "th": "กำลังสแกน..."},
    "hdr.status.module_test": {"en": "MODULE TEST RUNNING", "th": "กำลังทดสอบโมดูล"},
    "hdr.status.install_check": {"en": "INSTALLATION CHECK RUNNING",
                                 "th": "กำลังตรวจการติดตั้ง"},
    "hdr.status.ota": {"en": "FIRMWARE UPDATE RUNNING", "th": "กำลังอัปเดตเฟิร์มแวร์"},
    "hdr.status.connected": {"en": "{desc} — id {id}", "th": "{desc} — id {id}"},

    # notifications
    "msg.no_com": {"en": "no COM port selected", "th": "ยังไม่ได้เลือกพอร์ต COM"},
    "msg.ports_found": {"en": "{n} port(s) found", "th": "พบพอร์ต {n} รายการ"},
    "msg.connected": {"en": "connected: {desc}", "th": "เชื่อมต่อแล้ว: {desc}"},
    "msg.connect_failed": {"en": "connect failed", "th": "เชื่อมต่อไม่สำเร็จ"},
    "msg.id_reserved": {"en": "ID {id} is reserved for SET_ID mode — a module only "
                              "answers there while its switch is in that mode",
                        "th": "ID {id} สงวนไว้สำหรับโหมด SET_ID — โมดูลจะตอบที่ ID นี้ "
                              "เฉพาะตอนสวิตช์อยู่ในโหมดนั้น"},
    "msg.worker_busy": {"en": "worker busy — cannot start now",
                        "th": "ระบบกำลังทำงานอื่น — เริ่มตอนนี้ไม่ได้"},
    "msg.not_connected": {"en": "not connected", "th": "ยังไม่ได้เชื่อมต่อ"},
    "msg.scan_found": {"en": "scan complete — using ID {id}",
                       "th": "สแกนเสร็จ — ใช้ ID {id}"},
    "msg.scan_none": {"en": "scan complete — no device answered",
                      "th": "สแกนเสร็จ — ไม่มีอุปกรณ์ตอบกลับ"},
    "msg.saved": {"en": "saved {name}", "th": "บันทึก {name} แล้ว"},
    "msg.no_result": {"en": "no completed run yet", "th": "ยังไม่มีผลการทดสอบ"},

    # scan dialog
    "scan.title": {"en": "Scanning for slave IDs", "th": "กำลังค้นหา Slave ID"},
    "scan.probing": {"en": "probing {n}/{total} (id {id})",
                     "th": "ทดสอบ {n}/{total} (id {id})"},
    "scan.done": {"en": "done — probed {n}/{total}", "th": "เสร็จ — ทดสอบไป {n}/{total}"},
    "scan.found": {"en": "found: {ids}", "th": "พบ: {ids}"},
    "scan.none": {"en": "none", "th": "ไม่พบ"},

    "btn.cancel": {"en": "Cancel", "th": "ยกเลิก"},
    "btn.close": {"en": "Close", "th": "ปิด"},
    "btn.clear": {"en": "Clear", "th": "ล้าง"},
    "btn.export_csv": {"en": "Export CSV", "th": "บันทึก CSV"},

    # ── tabs ───────────────────────────────────────────────────────────────
    "tab.control": {"en": "Control", "th": "ควบคุม"},
    "tab.monitor": {"en": "Monitor", "th": "สถานะ"},
    "tab.install": {"en": "Installation Check", "th": "ตรวจการติดตั้ง"},
    "tab.module": {"en": "Module Test", "th": "ทดสอบโมดูล"},
    "tab.danger": {"en": "Danger", "th": "คำสั่งอันตราย"},
    "tab.soak": {"en": "Soak", "th": "ทดสอบยาว"},

    # ── soak tab ───────────────────────────────────────────────────────────
    "soak.card": {"en": "Bus soak", "th": "ทดสอบเดินยาว (soak)"},
    "soak.hint": {"en": "Polls every module of the cabinet, hour after hour, the way "
                        "a hospital server does — and watches each module's BOOT "
                        "counter, because a module that hangs and reboots answers "
                        "again within a second and no read ever fails. That is how "
                        "the hub-crossing fault of 13 Aug hid for months. Leave it "
                        "running overnight; anomalies also go to a CSV in "
                        "data/exports, so nobody has to sit and watch.",
                  "th": "ไล่อ่านทุกโมดูลในตู้ต่อเนื่องเป็นชั่วโมง เหมือนที่เซิร์ฟเวอร์"
                        "โรงพยาบาลทำ พร้อมเฝ้าตัวนับ 'จำนวนครั้งที่บูต' ของแต่ละโมดูล "
                        "เพราะโมดูลที่ค้างแล้วรีบูตจะกลับมาตอบภายในวินาทีเดียว — "
                        "ไม่มี read ไหน fail เลย นั่นคือเหตุผลที่บั๊กการข้าม channel "
                        "ซ่อนตัวได้นาน เปิดทิ้งไว้ข้ามคืนได้ ความผิดปกติจะถูกบันทึกลง "
                        "CSV ใน data/exports ด้วย ไม่ต้องมีคนนั่งเฝ้า"},
    "soak.gap": {"en": "Pause per pass (s)", "th": "พักต่อรอบ (วินาที)"},
    "soak.gap_tip": {"en": "Breather between full cabinet passes. Larger is gentler on "
                           "a bus that is also carrying real traffic.",
                     "th": "เวลาพักระหว่างรอบกวาดทั้งตู้ ตั้งมากขึ้น = เบามือกับบัส"
                           "ที่มีงานจริงวิ่งอยู่ด้วย"},
    "soak.counter_every": {"en": "Check counters every N passes",
                           "th": "ตรวจตัวนับทุก N รอบ"},
    "soak.counter_every_tip": {"en": "How often to re-read every module's boot and "
                                     "watchdog counters — the reboot detector. Costs "
                                     "one extra read per module.",
                               "th": "ความถี่ในการอ่านตัวนับบูต/watchdog ของทุกโมดูล "
                                     "ซึ่งคือตัวจับการรีบูต เสียเวลาเพิ่มโมดูลละ 1 การอ่าน"},
    "soak.slow": {"en": "Slow reply (ms)", "th": "ตอบช้ากว่า (ms)"},
    "soak.slow_tip": {"en": "A reply slower than this is logged. On a healthy 9600 "
                            "bus a read lands in well under 100 ms.",
                      "th": "ถ้าตอบช้ากว่านี้จะถูกบันทึก บัส 9600 ที่ปกติจะตอบต่ำกว่า "
                            "100 ms อย่างสบาย"},
    "soak.start": {"en": "Start soak", "th": "เริ่มทดสอบ"},
    "soak.stop": {"en": "Stop", "th": "หยุด"},
    "soak.idle": {"en": "not running", "th": "ยังไม่ได้เริ่ม"},
    "soak.running": {"en": "running — {n} modules per pass", "th": "กำลังวิ่ง — รอบละ {n} โมดูล"},
    "soak.stopping": {"en": "stopping after this pass…", "th": "จะหยุดเมื่อจบรอบนี้…"},
    "soak.busy": {"en": "The bus is busy with another sweep, or not connected.",
                  "th": "บัสกำลังถูกใช้โดยงานอื่น หรือยังไม่ได้เชื่อมต่อ"},
    "soak.totals": {"en": "Running totals", "th": "ยอดสะสม"},
    "soak.elapsed": {"en": "elapsed {v}", "th": "เวลา {v}"},
    "soak.passes": {"en": "passes {v}", "th": "รอบ {v}"},
    "soak.txns": {"en": "reads {v}", "th": "อ่าน {v}"},
    "soak.fails": {"en": "failed {v}", "th": "ล้มเหลว {v}"},
    "soak.reboots": {"en": "reboots {v}", "th": "รีบูต {v}"},
    "soak.watchdogs": {"en": "watchdog {v}", "th": "watchdog {v}"},
    "soak.worst": {"en": "worst {v} ms", "th": "ช้าสุด {v} ms"},
    "soak.crossings": {"en": "hub crossings {n} (worst {v} ms — expected)",
                       "th": "ข้าม channel {n} ครั้ง (ช้าสุด {v} ms — ปกติ)"},
    "soak.awake_on": {"en": "This PC is held awake while a run is in progress",
                      "th": "กันเครื่องนี้หลับระหว่างที่กำลังทดสอบ"},
    "soak.awake_off": {"en": "Sleep cannot be held off on this platform — turn "
                             "sleep off in the power settings before leaving a "
                             "run unattended",
                       "th": "กันเครื่องหลับอัตโนมัติไม่ได้บนแพลตฟอร์มนี้ — "
                             "ปิด sleep ในตั้งค่าพลังงานก่อนปล่อยทดสอบทิ้งไว้"},
    "soak.applog": {"en": "app log: {v}", "th": "ล็อกโปรแกรม: {v}"},
    "soak.anomalies": {"en": "Anomalies", "th": "ความผิดปกติ"},
    "soak.anomalies_tip": {"en": "Every no-reply, reboot, watchdog reset and slow "
                                 "answer, as it happens. An empty list after a long "
                                 "run is the result you want.",
                           "th": "ทุกครั้งที่ไม่ตอบ รีบูต โดน watchdog หรือตอบช้า "
                                 "จะขึ้นที่นี่ทันที ถ้าวิ่งยาวแล้วว่างเปล่า = ผลที่ต้องการ"},

    # ── control tab ────────────────────────────────────────────────────────
    "ctl.presets": {"en": "Presets (single shared ring — enabling one auto-clears the others)",
                    "th": "พรีเซ็ตสี (ไฟวงเดียวกัน — เปิดอันใหม่ อันเก่าจะดับเอง)"},
    "ctl.preset_n": {"en": "Preset {n}", "th": "พรีเซ็ต {n}"},
    "ctl.active": {"en": "ACTIVE", "th": "ทำงานอยู่"},
    "ctl.light": {"en": "Light ({addr})", "th": "เปิดไฟ ({addr})"},
    "ctl.light_disp": {"en": "Light+Disp ({addr})", "th": "ไฟ+จอ ({addr})"},
    "ctl.unlock": {"en": "Unlock ({addr})", "th": "ปลดล็อก ({addr})"},
    "ctl.unlock_disp": {"en": "Unlock+Disp ({addr})", "th": "ปลดล็อก+จอ ({addr})"},
    "ctl.display": {"en": "Display (OLED)", "th": "จอแสดงผล (OLED)"},
    "ctl.number": {"en": "number", "th": "ตัวเลข"},
    "ctl.number_hint": {"en": "(0-99; >99 clamps to 99)", "th": "(0-99; เกิน 99 จะถูกตัดเหลือ 99)"},
    "ctl.write_reg60": {"en": "Write reg 60", "th": "เขียน reg 60"},
    "ctl.display_power": {"en": "Display power (1010)", "th": "เปิดจอ (1010)"},
    "ctl.quick_ops": {"en": "Quick ops", "th": "คำสั่งลัด"},
    "ctl.identify": {"en": "Identify (509)", "th": "ระบุตัวตน (509)"},
    "ctl.all_off": {"en": "All Off (511)", "th": "ปิดทั้งหมด (511)"},
    "ctl.latch_safety": {"en": "Latch Safety (1020)", "th": "ปลดล็อกแบบปลอดภัย (1020)"},
    "ctl.latch_force": {"en": "Latch Force (1019)", "th": "ปลดล็อกแบบบังคับ (1019)"},
    "ctl.latch_ready": {"en": "latch ready", "th": "พร้อมปลดล็อก"},
    "ctl.cooldown": {"en": "cooldown {s}s", "th": "รอ {s} วิ"},
    "ctl.generic_reg": {"en": "Generic register", "th": "อ่าน/เขียน register"},
    "ctl.generic_coil": {"en": "Generic coil", "th": "อ่าน/เขียน coil"},
    "ctl.addr": {"en": "addr", "th": "แอดเดรส"},
    "ctl.count": {"en": "count", "th": "จำนวน"},
    "ctl.value": {"en": "value", "th": "ค่า"},
    "ctl.on": {"en": "ON", "th": "เปิด"},
    "ctl.off": {"en": "OFF", "th": "ปิด"},

    # ── monitor tab ────────────────────────────────────────────────────────
    "mon.polling": {"en": "Polling", "th": "อ่านค่าต่อเนื่อง"},
    "mon.interval": {"en": "interval (s)", "th": "ทุกกี่วินาที"},
    "mon.stats_note": {"en": "statistics read every 5th poll",
                       "th": "อ่านสถิติทุกรอบที่ 5"},
    "mon.last_poll": {"en": "last poll: {time}", "th": "อ่านล่าสุด: {time}"},
    "mon.card.device": {"en": "Device", "th": "อุปกรณ์"},
    "mon.card.runtime": {"en": "Runtime", "th": "การทำงาน"},
    "mon.card.health": {"en": "Health (reg 9)", "th": "สุขภาพระบบ (reg 9)"},
    "mon.card.reset": {"en": "Reset cause (reg 8)", "th": "สาเหตุการรีเซ็ต (reg 8)"},
    "mon.card.temp": {"en": "Temperatures", "th": "อุณหภูมิ"},
    "mon.card.latch": {"en": "Latch / Display", "th": "กลอน / จอ"},
    "mon.card.stats": {"en": "Statistics", "th": "สถิติ"},
    "mon.reset_note": {"en": "clear-on-read — this tool's polling consumes it; "
                             "last nonzero is kept",
                       "th": "ค่านี้ถูกล้างเมื่ออ่าน — การอ่านของโปรแกรมจะกินค่าไป "
                             "จึงเก็บค่าล่าสุดที่ไม่ใช่ศูนย์ไว้แสดง"},
    "mon.type": {"en": "Type: {v}", "th": "ชนิด: {v}"},
    "mon.fw": {"en": "FW: {v}", "th": "เฟิร์มแวร์: {v}"},
    "mon.hw": {"en": "HW: {v}", "th": "ฮาร์ดแวร์: {v}"},
    "mon.baud_id": {"en": "Baud: {baud} · ID: {id}", "th": "Baud: {baud} · ID: {id}"},
    "mon.uid": {"en": "Serial: {v}", "th": "หมายเลขชิป: {v}"},
    "mon.current": {"en": "Input current: {v}", "th": "กระแสขาเข้า: {v}"},
    "mon.button": {"en": "Confirm presses: {n}", "th": "กดยืนยันแล้ว: {n} ครั้ง"},
    "mon.button_held": {"en": " (held now)", "th": " (กำลังกดค้าง)"},
    "mon.uptime": {"en": "Uptime: {v}", "th": "เปิดมาแล้ว: {v}"},
    "mon.boots": {"en": "Boots: {v}", "th": "จำนวนครั้งที่บูต: {v}"},
    "mon.mode": {"en": "Mode: {v}", "th": "โหมด: {v}"},
    "mon.active_preset": {"en": "Active preset: {v}", "th": "พรีเซ็ตที่ใช้อยู่: {v}"},
    "mon.room": {"en": "Room: {v}", "th": "ในห้อง: {v}"},
    "mon.board": {"en": "Board: {v}", "th": "บนบอร์ด: {v}"},
    "mon.latch_state": {"en": "Latch: {v}", "th": "กลอน: {v}"},
    "mon.locked": {"en": "LOCKED", "th": "ล็อกอยู่"},
    "mon.unlocked": {"en": "UNLOCKED", "th": "ปลดล็อก"},
    "mon.unlocked_ago": {"en": "Unlocked {s} s ago", "th": "ปลดล็อกเมื่อ {s} วินาทีก่อน"},
    "mon.no_unlock": {"en": "No unlock since boot", "th": "ยังไม่เคยปลดล็อกตั้งแต่บูต"},
    "mon.display_num": {"en": "Display number (reg 60): {v}", "th": "เลขบนจอ (reg 60): {v}"},
    "mon.total": {"en": "Total: {c} fires · {s} s", "th": "รวม: {c} ครั้ง · {s} วินาที"},
    "mon.col.preset": {"en": "preset", "th": "พรีเซ็ต"},
    "mon.col.count": {"en": "on count", "th": "จำนวนครั้ง"},
    "mon.col.runtime": {"en": "runtime s", "th": "เวลารวม (วิ)"},
    "mon.seen_at": {"en": "(seen {time})", "th": "(พบเมื่อ {time})"},

    # ── module test tab ────────────────────────────────────────────────────
    "mt.what": {"en": "What to test", "th": "จะทดสอบอะไรบ้าง"},
    "mt.always": {"en": "Always included — read every register and coil, "
                        "write / verify / restore the safe settings, and check "
                        "the firmware's value limits.",
                  "th": "ทำทุกครั้ง — อ่าน register และ coil ทั้งหมด, "
                        "เขียน/ตรวจ/คืนค่าการตั้งค่าที่ปลอดภัย และตรวจว่า firmware "
                        "จำกัดค่าตามสเปคจริง"},
    "mt.lights": {"en": "Lights & display", "th": "ไฟและจอแสดงผล"},
    "mt.lights_tip": {"en": "Colour presets 1-8 (coils 1001-1008), OLED number "
                            "(reg 60 + coil 1010), ring on/off",
                      "th": "พรีเซ็ตสี 1-8 (coil 1001-1008), เลขบนจอ "
                            "(reg 60 + coil 1010), เปิด/ปิดไฟวง"},
    "mt.repeat": {"en": "Repeat", "th": "ทำซ้ำ"},
    "mt.unlock_card": {"en": "Unlock test — moves the physical latch",
                       "th": "ทดสอบปลดล็อก — กลอนจะทำงานจริง"},
    "mt.include_unlock": {"en": "Include the unlock test", "th": "รวมการทดสอบปลดล็อก"},
    "mt.unlocks_per_round": {"en": "Unlocks per round", "th": "ปลดล็อกกี่ครั้งต่อรอบ"},
    "mt.always_safety": {"en": "Always fires: normal unlock (1020) — opens only "
                               "when the latch reads locked",
                         "th": "ยิงเสมอ: ปลดล็อกปกติ (1020) — ทำงานเฉพาะตอนกลอนล็อกอยู่"},
    "mt.also_force": {"en": "Also force unlock (1019) — opens even if the lock "
                            "sensor disagrees",
                      "th": "เพิ่ม: ปลดล็อกแบบบังคับ (1019) — ทำงานแม้เซนเซอร์บอกว่าไม่ได้ล็อก"},
    "mt.also_combo": {"en": "Also light + unlock (1022) and light + number + unlock (1031)",
                      "th": "เพิ่ม: ไฟ + ปลดล็อก (1022) และ ไฟ + เลข + ปลดล็อก (1031)"},
    "mt.also_1021": {"en": "Also light 1 + unlock (1021)", "th": "เพิ่ม: ไฟ 1 + ปลดล็อก (1021)"},
    "mt.warn_unlock": {"en": "this run will unlock the door {n} time(s)",
                       "th": "รอบนี้จะปลดล็อก {n} ครั้ง"},
    "mt.run": {"en": "Run Sweep", "th": "เริ่มทดสอบ"},
    "mt.idle": {"en": "idle", "th": "ว่าง"},
    "mt.done_steps": {"en": "done — {n} steps", "th": "เสร็จ — {n} ขั้น"},
    "mt.table_note": {"en": "(table shows the last {n} steps — the CSV export has everything)",
                      "th": "(ตารางแสดง {n} ขั้นล่าสุด — ไฟล์ CSV มีครบทั้งหมด)"},
    "mt.phase": {"en": "{name} ({i}/{total})", "th": "{name} ({i}/{total})"},

    "phase.READ": {"en": "Read all", "th": "อ่านทั้งหมด"},
    "phase.WRITE": {"en": "Write/restore", "th": "เขียน/คืนค่า"},
    "phase.VALIDATE": {"en": "Value limits", "th": "ขีดจำกัดค่า"},
    "phase.PRESET": {"en": "Colour presets", "th": "พรีเซ็ตสี"},
    "phase.DISPLAY": {"en": "Display", "th": "จอแสดงผล"},
    "phase.LED": {"en": "Light ring", "th": "ไฟวง"},
    "phase.LATCH": {"en": "Unlock", "th": "ปลดล็อก"},

    "res.running": {"en": "RUNNING", "th": "กำลังทำงาน"},
    "res.pass": {"en": "PASS", "th": "ผ่าน"},
    "res.fail": {"en": "FAIL", "th": "ไม่ผ่าน"},
    "res.cancelled": {"en": "CANCELLED", "th": "ยกเลิกแล้ว"},

    "col.time": {"en": "time", "th": "เวลา"},
    "col.phase": {"en": "phase", "th": "ขั้นตอน"},
    "col.addr": {"en": "addr", "th": "แอดเดรส"},
    "col.name": {"en": "name", "th": "ชื่อ"},
    "col.op": {"en": "op", "th": "การทำงาน"},
    "col.value": {"en": "value/check", "th": "ค่า/ผลตรวจ"},
    "col.result": {"en": "result", "th": "ผล"},
    "col.id": {"en": "ID", "th": "ID"},
    "col.type": {"en": "type", "th": "ชนิด"},
    "col.detail": {"en": "detail", "th": "รายละเอียด"},

    # ── installation check tab ─────────────────────────────────────────────
    "ins.modules": {"en": "Modules to check", "th": "โมดูลที่จะตรวจ"},
    "ins.select_all": {"en": "Select all", "th": "เลือกทั้งหมด"},
    "ins.from_scan": {"en": "From last scan", "th": "จากผลสแกนล่าสุด"},
    "ins.selected": {"en": "{n} selected", "th": "เลือกแล้ว {n}"},
    "ins.whole_cabinet": {"en": "Whole cabinet", "th": "ทั้งตู้"},
    "ins.whole_cabinet_tip": {"en": "Select every slot of the cabinet type picked "
                                    "in the header.",
                              "th": "เลือกทุกช่องของตู้รุ่นที่เลือกไว้ที่แถบด้านบน"},
    "ins.hint": {"en": "'Whole cabinet' selects every slot of the type picked in the "
                       "header, or click cells to include them one by one "
                       "(the row button toggles a whole row). Cells turn green when the "
                       "module passes, red when it does not answer.",
                 "th": "\"ทั้งตู้\" เลือกทุกช่องของรุ่นที่ตั้งไว้ที่แถบด้านบน "
                       "หรือคลิกทีละช่อง (ปุ่มหน้าแถวเลือกทั้งแถว) "
                       "ช่องจะเป็นสีเขียวเมื่อผ่าน และสีแดงเมื่อไม่ตอบสนอง"},
    "ins.no_scan": {"en": "no scan result yet — run Scan in the header first",
                    "th": "ยังไม่มีผลสแกน — กดสแกนที่แถบด้านบนก่อน"},
    "ins.from_scan_ok": {"en": "selected {n} module(s) found by the last scan",
                         "th": "เลือก {n} โมดูลที่พบจากการสแกนล่าสุด"},
    "ins.cabinet_ok": {"en": "{label} — {n} modules selected",
                       "th": "{label} — เลือก {n} โมดูล"},
    "ins.what": {"en": "What to do on each module", "th": "จะทำอะไรกับแต่ละโมดูล"},
    "ins.always": {"en": "Always included — check that the module answers on the bus "
                         "(reads its device type).",
                   "th": "ทำทุกครั้ง — ตรวจว่าโมดูลตอบสนองบนบัส (อ่านชนิดอุปกรณ์)"},
    "ins.act.skip": {"en": "skip", "th": "ข้าม"},
    "ins.act.light": {"en": "light", "th": "เปิดไฟ"},
    "ins.act.light_display": {"en": "light + display", "th": "เปิดไฟ+จอ"},
    "ins.act_hint": {
        "en": "One command per module, the same combinations the firmware "
              "offers: 1001 lights the ring, 1011 lights it and shows the "
              "module's number. Adding the latch below upgrades whichever is "
              "chosen to 1021 or 1031. The display shows the slave ID; IDs "
              "above 99 show the column number, because it holds two digits.",
        "th": "หนึ่งคำสั่งต่อโมดูล ใช้ชุดเดียวกับที่เฟิร์มแวร์มีให้: 1001 เปิดไฟวงแหวน, "
              "1011 เปิดไฟพร้อมโชว์เลขประจำช่อง ถ้าติ๊กกลอนด้านล่างจะยกระดับเป็น "
              "1021 หรือ 1031 จอแสดง Slave ID ถ้าเกิน 99 จะแสดงเลขช่องแทน "
              "เพราะจอรองรับสองหลัก"},
    "ins.act_coil": {"en": "will send coil {coil} ({what})",
                     "th": "จะส่ง coil {coil} ({what})"},
    "ins.do_identify": {"en": "Identify — blink white ~5 s (509)",
                        "th": "ระบุตัวตน — กะพริบสีขาว ~5 วิ (509)"},
    "ins.hold": {"en": "Hold each step (s)", "th": "ค้างแต่ละขั้น (วินาที)"},
    "ins.pick_card": {"en": "Pick walkthrough", "th": "ทดสอบลำดับหยิบยา"},
    "ins.pick_hint": {
        "en": "The dispensing flow as a rehearsal: a batch of slots lights up "
              "together, just as a prescription lights them, and someone at "
              "the cabinet picks them in any order — each light goes out as "
              "its front button is pressed. When the batch is done the next "
              "one lights. Proves lights, buttons and the confirm loop in one "
              "walk. Needs module firmware v3.2.0.",
        "th": "ซ้อมขั้นตอนจ่ายยาจริง: ไฟติดพร้อมกันเป็นชุด เหมือนตอนใบสั่งยาสั่งงานจริง "
              "คนที่หน้าตู้หยิบช่องไหนก่อนก็ได้ ไฟแต่ละช่องจะดับเมื่อกดปุ่มหน้าช่องนั้น "
              "ครบชุดแล้วชุดถัดไปจะติดต่อ — พิสูจน์ไฟ ปุ่ม และวงจรยืนยันครบในรอบเดียว "
              "ต้องใช้เฟิร์มแวร์โมดูล v3.2.0"},
    "ins.pick_preset": {"en": "Preset", "th": "Preset สี"},
    "ins.pick_batch": {"en": "Light together", "th": "จุดพร้อมกัน (ช่อง)"},
    "ins.pick_batch_tip": {
        "en": "How many slots light at once. A batch never spans rows: the "
              "cabinet's RS485 hub needs about two seconds of silence to "
              "change channel, so watching two rows at once adds seconds "
              "before a press is noticed, while extra slots in one row cost "
              "milliseconds. 0 lights everything selected at once — honest to "
              "the real system, but slow to confirm across rows.",
        "th": "จำนวนช่องที่ไฟติดพร้อมกัน หนึ่งชุดจะอยู่ในแถวเดียวเสมอ เพราะฮับ RS485 "
              "ต้องเงียบราว 2 วินาทีเพื่อสลับช่อง การเฝ้าสองแถวพร้อมกันจึงหน่วงหลายวินาที"
              "กว่าจะเห็นการกด ขณะที่เพิ่มช่องในแถวเดียวกันแทบไม่มีค่าใช้จ่าย "
              "ใส่ 0 = จุดทุกช่องที่เลือกพร้อมกัน ตรงกับระบบจริงแต่ยืนยันช้าเมื่อข้ามแถว"},
    "ins.pick_display": {"en": "Show the slot number", "th": "โชว์เลขช่องบนจอ"},
    "ins.pick_display_tip": {"en": "Uses the coil that lights the ring and the "
                                   "display together, with the slot's own ID on it.",
                             "th": "ใช้ coil ที่เปิดไฟพร้อมจอในคำสั่งเดียว "
                                   "และแสดงเลขประจำช่องนั้น"},
    "ins.pick_unlock": {"en": "Release the latch", "th": "ปลดกลอน"},
    "ins.pick_unlock_tip": {"en": "What a real pick does. A latch that is already "
                                  "open cannot be pulsed, but on its own that only "
                                  "means the pulse changed nothing — the light, the "
                                  "display and the button are still tested. Tick "
                                  "'wait for the drawer to close' to make the drawer "
                                  "part of the result.",
                            "th": "เหมือนการหยิบยาจริง กลอนที่เปิดอยู่แล้วจะปล่อยพัลส์"
                                  "ไม่ได้ แต่ลำพังเรื่องนี้แปลว่าพัลส์นั้นไม่ได้เปลี่ยนอะไร "
                                  "ไฟ จอ และปุ่มยังทดสอบได้ตามปกติ ถ้าต้องการให้สถานะ"
                                  "ลิ้นชักมีผลกับการตัดสิน ให้ติ๊ก 'รอปิดลิ้นชักก่อนดับไฟ'"},
    "ins.pick_closed": {"en": "Wait for the drawer to close",
                        "th": "รอปิดลิ้นชักก่อนดับไฟ"},
    "ins.pick_closed_tip": {"en": "The pick is not over when the button is pressed — "
                                  "it is over when the drawer is shut again. With "
                                  "this on, the slot must start closed and the light "
                                  "stays on until the module reports its latch "
                                  "locked, so a slot left open cannot pass.",
                            "th": "การหยิบยายังไม่จบตอนกดปุ่ม แต่จบเมื่อปิดลิ้นชักแล้ว "
                                  "เปิดตัวเลือกนี้ ช่องนั้นต้องปิดอยู่ก่อนเริ่ม และไฟจะติดค้าง"
                                  "จนโมดูลรายงานว่ากลอนล็อก ช่องที่เปิดค้างไว้จึงผ่านไม่ได้"},
    "ins.pick_closing": {"en": "{n} waiting to be closed, {lit} still lit",
                         "th": "รอปิดลิ้นชัก {n} ช่อง, ไฟยังติดอีก {lit} ช่อง"},
    "ins.pick_same_channel": {"en": "Keep a batch on one hub channel",
                              "th": "หนึ่งชุดอยู่ช่องฮับเดียว"},
    "ins.pick_same_channel_tip": {
        "en": "On: slots either side of a channel boundary light one batch "
              "after the other, which keeps confirmation under a second. Off: "
              "the batch holds as many slots as you asked for wherever they "
              "are, the way a real prescription lights them — but watching two "
              "channels costs about two seconds per sweep, so the light takes "
              "that much longer to go out.",
        "th": "เปิด: ช่องที่อยู่คนละช่องฮับจะติดเป็นคนละชุดต่อกันไป ทำให้ยืนยันได้"
              "ภายในไม่ถึงวินาที / ปิด: หนึ่งชุดจะจุดครบตามจำนวนที่ตั้งไม่ว่าอยู่ช่องใด "
              "เหมือนใบสั่งยาจริง แต่การเฝ้าสองช่องเสียเวลาราว 2 วินาทีต่อรอบ "
              "ไฟจึงดับช้าลงเท่านั้น"},
    "ins.pick_timeout": {"en": "Timeout/batch (s)", "th": "รอสูงสุด/ชุด (วิ)"},
    "ins.pick_timeout_tip": {"en": "Per batch, from when its lights come on. "
                                   "0 = wait until cancelled.",
                             "th": "นับต่อหนึ่งชุด เริ่มจับเวลาตอนไฟชุดนั้นติด "
                                   "ใส่ 0 = รอจนกว่าจะกดยกเลิก"},
    "ins.pick_run": {"en": "Start walkthrough", "th": "เริ่มเดินทดสอบ"},
    "ins.pick_preparing": {
        "en": "lighting slot {id}  ({i}/{total})",
        "th": "กำลังเปิดไฟช่อง {id}  ({i}/{total})"},
    "ins.pick_waiting": {
        "en": "{n} slots lit — press each slot's button, in any order",
        "th": "ไฟติด {n} ช่อง — กดปุ่มหน้าช่อง หยิบช่องไหนก่อนก็ได้"},
    "ins.unlock_card": {"en": "Unlock — moves the physical latch",
                        "th": "ปลดล็อก — กลอนจะทำงานจริง"},
    "ins.do_unlock": {"en": "Also throw the latch (1021 / 1031)",
                      "th": "ปลดกลอนด้วย (1021 / 1031)"},
    "ins.warn_unlock": {"en": "this run will unlock {n} module(s)",
                        "th": "รอบนี้จะปลดล็อก {n} โมดูล"},
    "ins.cooldown_note": {"en": "Each module keeps its own 2 s cooldown, so a sweep "
                                "across different modules is not slowed down.",
                          "th": "แต่ละโมดูลมีเวลาพัก 2 วินาทีของตัวเอง "
                                "การไล่ทดสอบข้ามโมดูลจึงไม่ถูกหน่วง"},
    "ins.run": {"en": "Run check", "th": "เริ่มตรวจ"},
    "ins.select_one": {"en": "select at least one module", "th": "เลือกอย่างน้อยหนึ่งโมดูล"},
    "ins.module_progress": {"en": "module {id} ({i}/{total})", "th": "โมดูล {id} ({i}/{total})"},
    "ins.done": {"en": "done — {n} module(s)", "th": "เสร็จ — {n} โมดูล"},
    "ins.all_pass": {"en": "ALL PASS", "th": "ผ่านทั้งหมด"},
    "ins.issues": {"en": "ISSUES FOUND", "th": "พบปัญหา"},
    "ins.answered": {"en": "answered {n}/{total}", "th": "ตอบสนอง {n}/{total}"},
    "ins.no_answer": {"en": "no answer: {ids}", "th": "ไม่ตอบสนอง: {ids}"},
    "ins.step_failed": {"en": "failed a step: {ids}", "th": "ทำบางขั้นไม่ผ่าน: {ids}"},
    "ins.res.pass": {"en": "✓ pass", "th": "✓ ผ่าน"},
    "ins.res.no_answer": {"en": "✗ no answer", "th": "✗ ไม่ตอบสนอง"},
    "ins.res.fail": {"en": "✗ fail", "th": "✗ ไม่ผ่าน"},

    # ── Gateway tab ────────────────────────────────────────────────────────
    "tab.gateway": {"en": "Gateway", "th": "เกตเวย์"},
    "gw.intro": {"en": "Settings live in the Opta itself and travel as text commands "
                       "over the same USB port — the gateway is not a device on the "
                       "Modbus bus.",
                 "th": "ค่าตั้งอยู่ในตัว Opta เอง และคุยผ่านคำสั่งข้อความบนสาย USB เส้นเดียวกัน "
                       "— gateway ไม่ได้เป็นอุปกรณ์บนบัส Modbus"},
    "gw.usb_only": {"en": "Gateway settings are reachable over USB only. Switch the "
                          "header to RTU (COM) and pick the Opta's port.",
                    "th": "ตั้งค่า gateway ได้เฉพาะทาง USB — สลับแถบบนเป็น RTU (COM) "
                          "แล้วเลือกพอร์ตของ Opta"},
    "gw.detect": {"en": "Detect", "th": "ค้นหา"},
    "gw.reload": {"en": "Reload", "th": "อ่านใหม่"},
    "gw.detected": {"en": "gateway fw {fw} · up {up} s", "th": "พบ gateway fw {fw} · เปิดมา {up} วิ"},
    "gw.not_found": {"en": "no gateway on {port} — a plain USB-RS485 dongle, or "
                           "firmware without the console",
                     "th": "ไม่พบ gateway ที่ {port} — อาจเป็น dongle USB-RS485 ธรรมดา "
                           "หรือเฟิร์มแวร์ที่ยังไม่มี console"},
    "gw.no_port": {"en": "no COM port selected", "th": "ยังไม่ได้เลือกพอร์ต COM"},
    "gw.card.device": {"en": "Device", "th": "อุปกรณ์"},
    "gw.card.health": {"en": "Health", "th": "สถานะระบบ"},
    "gw.card.rs485": {"en": "RS485 bus", "th": "บัส RS485"},
    "gw.card.usb": {"en": "USB bridge", "th": "USB bridge"},
    "gw.card.identity": {"en": "System", "th": "ระบบ"},
    "gw.card.net": {"en": "Network", "th": "เครือข่าย"},
    "gw.card.counters": {"en": "Counters", "th": "ตัวนับ"},
    "gw.net_hint": {"en": "Address changes take effect after a reboot; the port moves "
                          "immediately.",
                    "th": "การแก้ที่อยู่ต้องรีบูตก่อนจึงมีผล ส่วนพอร์ตเปลี่ยนทันที"},
    "gw.card.link": {"en": "Link", "th": "การเชื่อมต่อ"},
    "gw.link.up": {"en": "up", "th": "เชื่อมต่อแล้ว"},
    "gw.link.nolink": {"en": "no cable", "th": "ยังไม่ขึ้น"},
    "gw.link.disabled": {"en": "off", "th": "ปิดอยู่"},
    "gw.link.safe": {"en": "skipped (safe mode)", "th": "ข้ามไว้ (safe mode)"},
    "gw.link.client": {"en": "a TCP client is connected", "th": "มี TCP client ต่ออยู่"},
    "gw.link.noclient": {"en": "no TCP client", "th": "ยังไม่มี TCP client"},
    "gw.link.serving": {"en": "Point this tool at {ip}:{port} over TCP to reach the "
                              "same modules without USB.",
                        "th": "ตั้ง Test Tool เป็น TCP ที่ {ip}:{port} เพื่อคุยกับโมดูลชุดเดียวกันโดยไม่ต้องใช้ USB"},
    "gw.link.off_hint": {"en": "Switch net.enabled on below, set the address, then Save "
                               "and reboot.",
                         "th": "เปิด net.enabled ด้านล่าง ตั้งที่อยู่ แล้วกดบันทึกและรีบูต"},
    "gw.link.nolink_hint": {"en": "Configured, but the interface is not up yet. Plug the "
                                  "cable in — it is picked up within a few seconds, no "
                                  "reboot needed.",
                            "th": "ตั้งค่าไว้แล้วแต่ยังไม่ขึ้น เสียบสาย LAN ได้เลย "
                                  "ระบบจะจับได้ในไม่กี่วินาทีโดยไม่ต้องรีบูต"},
    "gw.mac_placeholder": {"en": "placeholder MAC — this board's OTP holds no address",
                           "th": "MAC เป็นค่าสำรอง — OTP ของบอร์ดนี้ไม่มีที่อยู่"},
    # Plain-language names for the settings. The console key (rs485.t1_ms and
    # friends) is kept only as a tooltip — an installer should never need it.
    "gwf.sys.name": {"en": "Gateway name", "th": "ชื่อ gateway"},
    "gwf.sys.name.hint": {"en": "A label for you, so several gateways are easy to tell "
                                "apart.",
                          "th": "ป้ายชื่อไว้ให้คุณเอง เวลามีหลายตัวจะได้แยกออก"},
    "gwf.rs485.baud": {"en": "Bus speed (baud)", "th": "ความเร็วบัส (baud)"},
    "gwf.rs485.baud.hint": {"en": "Must match the modules. LGS R5.0 modules use 9600.",
                            "th": "ต้องตรงกับโมดูล — LGS R5.0 ใช้ 9600"},
    "gwf.rs485.predelay_us": {"en": "Pause before sending (µs)", "th": "หน่วงก่อนส่ง (µs)"},
    "gwf.rs485.predelay_us.hint": {"en": "Lets the bus settle before the gateway starts "
                                         "transmitting.",
                                   "th": "ให้บัสนิ่งก่อน gateway เริ่มส่ง"},
    "gwf.rs485.postdelay_us": {"en": "Pause after sending (µs)", "th": "หน่วงหลังส่ง (µs)"},
    "gwf.rs485.postdelay_us.hint": {"en": "Holds the line briefly after the last byte "
                                          "goes out.",
                                    "th": "ค้างสายไว้ครู่หนึ่งหลังส่งไบต์สุดท้าย"},
    "gwf.rs485.t1_ms": {"en": "Wait for a module to answer (ms)", "th": "รอโมดูลตอบ (ms)"},
    "gwf.rs485.t1_ms.hint": {"en": "Raise this if modules on a long bus keep timing out.",
                             "th": "ถ้าบัสยาวแล้วโมดูล timeout บ่อย ให้เพิ่มค่านี้"},
    "gwf.rs485.t2_ms": {"en": "Silence that ends an answer (ms)",
                        "th": "ความเงียบที่ถือว่าจบคำตอบ (ms)"},
    "gwf.rs485.t2_ms.hint": {"en": "Must stay below the waiting time above.",
                             "th": "ต้องน้อยกว่าเวลารอด้านบน"},
    "gwf.usb.gap_ms": {"en": "Silence that ends a command (ms)",
                       "th": "ความเงียบที่ถือว่าจบคำสั่ง (ms)"},
    "gwf.usb.gap_ms.hint": {"en": "Raise this if the PC sends commands in pieces and "
                                  "they get dropped.",
                            "th": "ถ้าคอมส่งคำสั่งขาดเป็นท่อนแล้วถูกทิ้ง ให้เพิ่มค่านี้"},
    "gwf.usb.max_ms": {"en": "Longest single command (ms)", "th": "คำสั่งเดียวยาวสุด (ms)"},
    "gwf.usb.max_ms.hint": {"en": "A safety cap. Must stay above the value above.",
                            "th": "ตัวกันค้าง ต้องมากกว่าค่าด้านบน"},
    "gwf.net.enabled": {"en": "Use the LAN port", "th": "ใช้พอร์ต LAN"},
    "gwf.net.enabled.hint": {"en": "On for LGS cabinets, where a server sends commands "
                                   "over the network. Off for SMT carts, which use USB.",
                             "th": "เปิดสำหรับตู้ LGS ที่เซิร์ฟเวอร์ส่งคำสั่งมาทางเครือข่าย "
                                   "ปิดสำหรับรถ SMT ที่ใช้ USB"},
    "gwf.net.dhcp": {"en": "Get the address automatically (DHCP)",
                     "th": "รับที่อยู่อัตโนมัติ (DHCP)"},
    "gwf.net.dhcp.hint": {"en": "Best left off — the server needs a fixed address it can "
                                "count on.",
                          "th": "ควรปิดไว้ — เซิร์ฟเวอร์ต้องการที่อยู่คงที่ที่เรียกได้แน่นอน"},
    "gwf.net.ip": {"en": "Address of this gateway", "th": "ที่อยู่ของ gateway ตัวนี้"},
    "gwf.net.ip.hint": {"en": "The address the server connects to.",
                        "th": "ที่อยู่ที่เซิร์ฟเวอร์จะเชื่อมเข้ามา"},
    "gwf.net.mask": {"en": "Subnet mask", "th": "Subnet mask"},
    "gwf.net.mask.hint": {"en": "Almost always 255.255.255.0.",
                          "th": "ปกติใช้ 255.255.255.0"},
    "gwf.net.gw": {"en": "Router address", "th": "ที่อยู่เราเตอร์"},
    "gwf.net.gw.hint": {"en": "Must be on the same network as the address above.",
                        "th": "ต้องอยู่วงเดียวกับที่อยู่ด้านบน"},
    "gwf.net.dns": {"en": "DNS server", "th": "เซิร์ฟเวอร์ DNS"},
    "gwf.net.dns.hint": {"en": "Modbus does not use it; the router's address is fine.",
                         "th": "Modbus ไม่ได้ใช้ ใส่ที่อยู่เราเตอร์ก็พอ"},
    "gwf.net.port": {"en": "Port", "th": "พอร์ต"},
    "gwf.net.port.hint": {"en": "502 is the Modbus standard. This one changes "
                                "immediately, without a reboot.",
                          "th": "502 คือค่ามาตรฐานของ Modbus ค่านี้เปลี่ยนแล้วมีผลทันทีไม่ต้องรีบูต"},
    "gwf.net.link_timeout_ms": {"en": "Wait for the cable at startup (ms)",
                                "th": "รอสาย LAN ตอนเปิดเครื่อง (ms)"},
    "gwf.net.link_timeout_ms.hint": {"en": "Only makes startup slower. A cable plugged "
                                           "in later is picked up on its own.",
                                     "th": "แค่ทำให้เปิดเครื่องช้าลง ถ้าเสียบทีหลังระบบก็จับได้เอง"},
    "gwf.net.mac": {"en": "Hardware address (MAC)", "th": "ที่อยู่ฮาร์ดแวร์ (MAC)"},
    "gwf.net.ntp": {"en": "NTP time server (IP)", "th": "เซิร์ฟเวอร์เวลา NTP (IP)"},
    "gwf.net.ntp.hint": {"en": "After a power cut the gateway asks this server for the "
                               "time by itself, so the schedule recovers with no visit. "
                               "0.0.0.0 = off (the tool still sets the clock on connect). "
                               "An IP, not a name — and the NTP server card below can "
                               "make THIS computer the server.",
                         "th": "หลังไฟดับ gateway จะถามเวลาจากเซิร์ฟเวอร์นี้เอง "
                               "ตารางรีเซ็ตจึงกลับมาทำงานโดยไม่ต้องมีคนไป 0.0.0.0 = ปิด "
                               "(เครื่องมือยังตั้งเวลาให้ตอนเชื่อมต่อเหมือนเดิม) ใส่เป็น IP เท่านั้น — "
                               "และการ์ด NTP server ด้านล่างทำให้คอมเครื่องนี้เป็นเซิร์ฟเวอร์ได้เลย"},
    "gwf.net.ntp_port": {"en": "NTP port", "th": "พอร์ต NTP"},
    "gwf.net.ntp_port.hint": {"en": "123 is standard. Change it only if the server "
                                    "serves on another port (Windows' own w32time can "
                                    "hold 123).",
                              "th": "มาตรฐานคือ 123 เปลี่ยนเฉพาะเมื่อเซิร์ฟเวอร์เปิดพอร์ตอื่น "
                                    "(w32time ของ Windows อาจยึด 123 อยู่)"},
    "gwf.time.tz_min": {"en": "Timezone (minutes east of UTC)",
                        "th": "โซนเวลา (นาที นับจาก UTC)"},
    "gwf.time.tz_min.hint": {"en": "Thailand = 420. Only the NTP answer is shifted by "
                                   "this — the clock itself keeps wall time, and Sync "
                                   "from this tool sends wall time already.",
                             "th": "ประเทศไทย = 420 ใช้แปลงเฉพาะคำตอบจาก NTP — "
                                   "นาฬิกาเก็บเวลาท้องถิ่นอยู่แล้ว และปุ่ม Sync ของเครื่องมือ"
                                   "ก็ส่งเวลาท้องถิ่นตรงๆ เหมือนเดิม"},
    "sch.ntp": {"en": "NTP: {s}", "th": "NTP: {s}"},

    "ntp.card": {"en": "NTP server (this computer)", "th": "NTP server (คอมเครื่องนี้)"},
    "ntp.hint": {"en": "Serve time to gateways from this computer's clock. Meant for "
                       "the site's server, where this tool is left running: the "
                       "gateway's net.ntp points here and its clock survives every "
                       "power cut without a visit. Standard NTP — any other client "
                       "may use it too.",
                 "th": "แจกเวลาให้ gateway จากนาฬิกาของคอมเครื่องนี้ ตั้งใจไว้สำหรับ"
                       "เซิร์ฟเวอร์ของไซต์ที่เปิดเครื่องมือนี้ทิ้งไว้: ชี้ net.ntp ของ gateway "
                       "มาที่นี่ แล้วนาฬิกาจะรอดทุกครั้งที่ไฟดับโดยไม่ต้องมีคนไป "
                       "เป็น NTP มาตรฐาน อุปกรณ์อื่นใช้ด้วยได้"},
    "ntp.enable": {"en": "Serve NTP", "th": "เปิด NTP server"},
    "ntp.enable_tip": {"en": "Remembered — the server comes back on when the tool "
                             "restarts.",
                       "th": "จำค่าไว้ — เปิดเครื่องมือใหม่เซิร์ฟเวอร์ก็กลับมาเอง"},
    "ntp.port": {"en": "Port", "th": "พอร์ต"},
    "ntp.port_tip": {"en": "123 is the NTP standard. If Windows' w32time holds it, "
                           "either stop that service or serve here on another port "
                           "and set the gateway's net.ntp_port to match.",
                     "th": "มาตรฐาน NTP คือ 123 ถ้า w32time ของ Windows ยึดอยู่ "
                           "ให้หยุดเซอร์วิสนั้น หรือเปิดพอร์ตอื่นแล้วตั้ง net.ntp_port "
                           "ฝั่ง gateway ให้ตรงกัน"},
    "ntp.serving": {"en": "serving on {ip}:{port} · answered {n} queries",
                    "th": "กำลังแจกเวลาที่ {ip}:{port} · ตอบไปแล้ว {n} ครั้ง"},
    "ntp.off": {"en": "off", "th": "ปิดอยู่"},
    "ntp.err": {"en": "could not open the port: {e}",
                "th": "เปิดพอร์ตไม่ได้: {e}"},
    "ntp.port_busy_hint": {"en": "port taken? stop Windows Time (w32time) or pick "
                                 "another port",
                           "th": "พอร์ตถูกใช้อยู่? หยุด Windows Time (w32time) "
                                 "หรือเปลี่ยนพอร์ต"},
    "ntp.no_ip": {"en": "could not determine this computer's address",
                  "th": "หาที่อยู่ของคอมเครื่องนี้ไม่ได้"},
    "ntp.use_pc": {"en": "Use this computer as the gateway's NTP",
                   "th": "ใช้เครื่องนี้เป็น NTP ของ gateway"},
    "ntp.use_pc_tip": {"en": "Fills net.ntp above with this computer's address — the "
                             "change still goes through the normal Save review.",
                       "th": "เติมที่อยู่ของคอมเครื่องนี้ลงช่อง net.ntp ด้านบน — "
                             "ยังต้องกดบันทึกผ่านหน้าตรวจทานตามปกติ"},
    "ntp.staged": {"en": "net.ntp = {ip} staged — review and Save",
                   "th": "ใส่ net.ntp = {ip} แล้ว — ตรวจแล้วกดบันทึก"},
    "ntp.no_key": {"en": "read the gateway first (needs firmware 1.11.0 or newer)",
                   "th": "อ่านค่า gateway ก่อน (ต้องเป็นเฟิร์มแวร์ 1.11.0 ขึ้นไป)"},

    "evl.card": {"en": "Gateway event log", "th": "บันทึกเหตุการณ์ของ gateway"},
    "evl.hint": {"en": "What happened at the cabinet, kept on the gateway itself: "
                       "every boot and its cause (power cut / watchdog / commanded), "
                       "link drops, clock sets, config saves, scheduled resets, "
                       "panel presses, TCP clients. Read-only; the newest 30 lines "
                       "also ride into the site report. Needs gateway firmware "
                       "1.11.0 or newer.",
                 "th": "เกิดอะไรขึ้นที่ตู้ เก็บไว้ในตัว gateway เอง: ทุกการบูตพร้อมสาเหตุ "
                       "(ไฟดับ / watchdog / สั่งรีเซ็ต), ลิงก์หลุด, ตั้งเวลา, บันทึกค่า, "
                       "รีเซ็ตตามตาราง, กดปุ่มหน้าตู้, ไคลเอนต์ TCP อ่านอย่างเดียว "
                       "30 บรรทัดล่าสุดแนบไปกับ site report ด้วย "
                       "ต้องเป็นเฟิร์มแวร์ 1.11.0 ขึ้นไป"},
    "evl.read": {"en": "Read latest events", "th": "อ่านเหตุการณ์ล่าสุด"},
    "evl.read_tip": {"en": "Fetch the newest 30 records over the USB console.",
                     "th": "ดึง 30 รายการล่าสุดผ่านสาย USB"},
    "evl.failed": {"en": "could not read the log: {e}", "th": "อ่านบันทึกไม่ได้: {e}"},
    "evl.empty": {"en": "(no events recorded yet)", "th": "(ยังไม่มีเหตุการณ์บันทึกไว้)"},

    "fws.card": {"en": "Cabinet firmware", "th": "เฟิร์มแวร์ทั้งตู้"},
    "fws.hint": {"en": "Reads every module's firmware version — nothing is written. "
                       "Run it before an update to see who still needs it, and after "
                       "one to confirm they all took it.",
                 "th": "อ่านเวอร์ชันเฟิร์มแวร์ของทุกโมดูล ไม่มีการเขียนใดๆ ใช้ก่อนอัปเดต"
                       "เพื่อดูว่าเหลือตัวไหน และใช้หลังอัปเดตเพื่อยืนยันว่าขึ้นครบทุกตัว"},
    "fws.whole_cabinet": {"en": "Whole cabinet", "th": "ทั้งตู้"},
    "fws.whole_cabinet_tip": {"en": "Survey every slot of the cabinet type picked "
                                    "in the header.",
                              "th": "สำรวจทุกช่องของตู้รุ่นที่เลือกไว้ที่แถบด้านบน"},
    "fws.selected": {"en": "the targets above", "th": "ตามรายการเป้าหมายด้านบน"},
    "fws.selected_tip": {"en": "Survey exactly the IDs in the target box",
                         "th": "สำรวจเฉพาะไอดีในช่องเป้าหมาย"},
    "fws.running": {"en": "reading {done}/{total}", "th": "กำลังอ่าน {done}/{total}"},
    "fws.done": {"en": "{n}/{total} answered — {summary}",
                 "th": "ตอบ {n}/{total} — {summary}"},
    "fws.groups": {"en": "versions found:", "th": "เวอร์ชันที่พบ:"},
    "fws.group_tip": {"en": "Make the modules on {v} the update targets",
                      "th": "ตั้งโมดูลที่รัน {v} เป็นเป้าหมายอัปเดต"},
    "fws.targets_set": {"en": "{n} modules on {v} set as targets",
                        "th": "ตั้งเป้าหมาย {n} โมดูลที่รัน {v} แล้ว"},
    "fws.cell_tip": {"en": "firmware {v}", "th": "เฟิร์มแวร์ {v}"},
    "fws.silent_tip": {"en": "These did not answer. Find out why before updating "
                             "anything — firmware is not sent to a module that "
                             "cannot be read.",
                       "th": "กลุ่มนี้ไม่ตอบ ควรหาสาเหตุก่อนอัปเดต ระบบจะไม่ส่งเฟิร์มแวร์"
                             "ไปยังโมดูลที่อ่านค่าไม่ได้"},

    "fw.use": {"en": "USE THIS", "th": "ใช้ไฟล์นี้"},
    "fw.or_upload": {"en": "or upload your own file:", "th": "หรืออัปโหลดไฟล์เอง:"},
    "fw.bundled_hint": {"en": "Released firmware shipped inside this tool, so a "
                              "site visit needs no download. The tool checks each "
                              "one against the released file before using it.",
                        "th": "เฟิร์มแวร์ที่ปล่อยแล้วและติดมากับเครื่องมือ ออกหน้างานได้"
                              "โดยไม่ต้องโหลดไฟล์ ระบบตรวจสอบความถูกต้องกับไฟล์ที่ปล่อยจริง"
                              "ก่อนใช้งานทุกครั้ง"},

    "gw.card.hub": {"en": "RS485 switch hub", "th": "ฮับสลับ RS485"},
    "gw.hub_hint": {"en": "For cabinets whose RS485 runs through a channel-switching "
                          "hub (LGS-64). The hub swallows the first frame after every "
                          "channel change and stays deaf for about two seconds; the "
                          "gateway repairs this by holding the next request until the "
                          "hub is ready. The server must retry once, or wait longer "
                          "than the settle time.",
                    "th": "สำหรับตู้ที่บัส RS485 วิ่งผ่านฮับสลับช่อง (LGS-64) ฮับจะกลืนเฟรมแรก"
                          "หลังสลับช่องและเงียบไป ~2 วินาที เกตเวย์ซ่อมโดยหน่วงคำขอถัดไป"
                          "จนฮับพร้อม ฝั่งเซิร์ฟเวอร์ต้อง retry อย่างน้อย 1 ครั้ง "
                          "หรือรอนานกว่าเวลาฮับพร้อม"},
    "sch.card": {"en": "Clock and scheduled reset",
                 "th": "นาฬิกาและการรีเซตตามเวลา"},
    "sch.hint": {"en": "The Opta has no battery for its clock, so the time is "
                       "lost on every power cut — the very thing a scheduled "
                       "reset exists to recover from. This tool sets it whenever "
                       "it reads a gateway whose clock is unset, and nothing is "
                       "ever scheduled while it is unset. The clock keeps the "
                       "time on the wall, not UTC: 03:00 means 03:00 here.",
                 "th": "Opta ไม่มีแบตเตอรี่เลี้ยงนาฬิกา เวลาจึงหายทุกครั้งที่ไฟดับ "
                       "ซึ่งเป็นเหตุการณ์ที่การรีเซตตามเวลามีไว้รองรับพอดี "
                       "เครื่องมือนี้จะตั้งเวลาให้ทุกครั้งที่พบว่าเกตเวย์ยังไม่มีเวลา "
                       "และจะไม่มีการตั้งเวลาใดทำงานจนกว่านาฬิกาจะถูกตั้ง "
                       "นาฬิกาเก็บเวลาท้องถิ่น ไม่ใช่ UTC ดังนั้น 03:00 คือตีสามที่นี่"},
    "sch.now": {"en": "gateway clock: {now}", "th": "นาฬิกาเกตเวย์: {now}"},
    "sch.sync": {"en": "SET FROM THIS PC", "th": "ตั้งจากเครื่องนี้"},
    "sch.sync_hint": {"en": "Sends this PC's wall clock. Done automatically "
                            "whenever the gateway's clock is unset.",
                      "th": "ส่งเวลาของเครื่องนี้ไปให้ ระบบจะตั้งให้เองทุกครั้ง"
                            "ที่พบว่าเกตเวย์ยังไม่มีเวลา"},
    "sch.synced": {"en": "gateway clock set from this PC",
                   "th": "ตั้งนาฬิกาเกตเวย์จากเครื่องนี้แล้ว"},
    "sch.last": {"en": "last scheduled reset: {when}",
                 "th": "รีเซตตามเวลาครั้งล่าสุด: {when}"},
    "sch.days": {"en": "days", "th": "วัน"},
    "sch.days_hint": {"en": "Leave every day ticked to run daily.",
                      "th": "ติ๊กครบทุกวัน = ทำทุกวัน"},
    "sch.sun": {"en": "Sun", "th": "อา"},
    "sch.mon": {"en": "Mon", "th": "จ"},
    "sch.tue": {"en": "Tue", "th": "อ"},
    "sch.wed": {"en": "Wed", "th": "พ"},
    "sch.thu": {"en": "Thu", "th": "พฤ"},
    "sch.fri": {"en": "Fri", "th": "ศ"},
    "sch.sat": {"en": "Sat", "th": "ส"},
    "gwf.sched.reset_enabled": {"en": "Reset the shelf on a schedule",
                                "th": "รีเซตชั้นวางตามเวลา"},
    "gwf.sched.reset_enabled.hint": {
        "en": "Off by default — a cabinet that power-cycles itself at an hour "
              "nobody chose is a fault, not a feature. It does the same thing "
              "the white button does.",
        "th": "ปิดไว้เป็นค่าเริ่มต้น ตู้ที่ตัดไฟตัวเองในเวลาที่ไม่มีใครกำหนด"
              "คือความผิดปกติ ไม่ใช่คุณสมบัติ การทำงานเหมือนกดปุ่มขาว"},
    "gwf.sched.reset_hhmm": {"en": "Time of day (HHMM)", "th": "เวลา (HHMM)"},
    "gwf.sched.reset_hhmm.hint": {
        "en": "As a clock reading: 300 is 03:00, 1430 is 14:30. Wall time at "
              "the cabinet, not UTC.",
        "th": "อ่านแบบหน้าปัด: 300 คือ 03:00, 1430 คือ 14:30 "
              "เป็นเวลาท้องถิ่นที่ตู้ ไม่ใช่ UTC"},
    "sch.slots": {"en": "times", "th": "ช่วงเวลา"},
    "sch.slot_n": {"en": "slot {n}", "th": "ช่วงที่ {n}"},
    "sch.slot_hint": {
        "en": "Up to four resets a day. Tick only the ones you want — an "
              "unticked slot keeps its time and never fires, so turning it "
              "back on later does not mean typing the hour again.",
        "th": "รีเซตได้สูงสุดวันละ 4 ครั้ง ติ๊กเฉพาะช่วงที่ต้องการ "
              "ช่วงที่ไม่ติ๊กจะเก็บเวลาไว้และไม่ทำงาน "
              "เปิดใช้ทีหลังจึงไม่ต้องพิมพ์เวลาใหม่"},
    "sch.no_slots": {"en": "Scheduling is on but no time is ticked — nothing will "
                           "run.",
                     "th": "เปิดใช้ตารางแล้วแต่ยังไม่ได้ติ๊กช่วงเวลาใด จะไม่มีอะไรทำงาน"},
    "sch.off_note": {"en": "Turn the switch on to set these.",
                     "th": "เปิดสวิตช์ด้านบนก่อนจึงจะตั้งค่าส่วนนี้ได้"},
    "gwf.sys.wdt_ms": {"en": "Watchdog (ms)", "th": "Watchdog (มิลลิวินาที)"},
    "gwf.sys.wdt_ms.hint": {
        "en": "The board resets itself if the firmware stops running for this "
              "long — the cure for a hang nobody is there to see. 8000 is well "
              "clear of the longest normal stall (a cross-channel RS485 hold, "
              "about 2.2 s). Too short and a slow boot restarts forever, so it "
              "must also outlast the wait for an Ethernet link. Takes effect on "
              "the next restart.",
        "th": "บอร์ดจะรีเซตตัวเองถ้าเฟิร์มแวร์หยุดทำงานนานเท่านี้ "
              "เป็นทางแก้อาการค้างตอนที่ไม่มีใครอยู่ 8000 ห่างจากการหน่วงปกติที่นานที่สุด "
              "(การรอ hub ข้ามช่อง ~2.2 วิ) พอสมควร ถ้าสั้นเกินไปบอร์ดที่บูตช้าจะรีสตาร์ทวนไม่จบ "
              "จึงต้องนานกว่าเวลารอลิงก์ Ethernet ด้วย มีผลเมื่อรีสตาร์ทครั้งถัดไป"},
    "gw.wdt_running": {"en": "watchdog {ms} ms", "th": "watchdog {ms} มิลลิวินาที"},
    "gw.wdt_off": {"en": "watchdog not running", "th": "watchdog ไม่ทำงาน"},
    "gw.reset_by_wdt": {
        "en": "The last restart was the watchdog — the firmware had stopped "
              "running and the board recovered itself.",
        "th": "การรีสตาร์ทครั้งล่าสุดมาจาก watchdog เฟิร์มแวร์หยุดทำงานและบอร์ดกู้ตัวเองกลับมา"},
    "pnl.card": {"en": "Front-panel buttons", "th": "ปุ่มหน้าตู้"},
    "pnl.hint": {"en": "Five buttons wired to the Opta's inputs 1-5, so the cabinet "
                       "can be exercised at the cabinet with no PC and no network. "
                       "Each one runs its job across the whole cabinet, slot by "
                       "slot; pressing another button replaces whatever is running.",
                 "th": "ปุ่ม 5 ตัวต่อกับอินพุต 1-5 ของ Opta ใช้ทดสอบตู้ที่หน้าตู้ได้เลย "
                       "ไม่ต้องมีคอมพิวเตอร์และไม่ต้องมีเครือข่าย แต่ละปุ่มจะทำงานไล่ทั้งตู้"
                       "ทีละช่อง กดปุ่มอื่นระหว่างทำงานจะแทนที่งานเดิม"},
    "pnl.input": {"en": "Opta input {n} ({name})", "th": "อินพุต {n} ของ Opta ({name})"},
    # Button caps (fixed wiring): a different word set from the lamp colours
    # below — yellow here, amber there — so the two families stay separate.
    "pnl.btn_colour.red": {"en": "Red", "th": "แดง"},
    "pnl.btn_colour.green": {"en": "Green", "th": "เขียว"},
    "pnl.btn_colour.blue": {"en": "Blue", "th": "น้ำเงิน"},
    "pnl.btn_colour.yellow": {"en": "Yellow", "th": "เหลือง"},
    "pnl.btn_colour.white": {"en": "White", "th": "ขาว"},
    "pnl.act.none": {"en": "— unassigned", "th": "— ยังไม่กำหนด"},
    "pnl.act.all_on": {"en": "Light + number, whole cabinet",
                       "th": "เปิดไฟ+จอ ทั้งตู้"},
    "pnl.act.all_off": {"en": "Everything off", "th": "ดับทั้งหมด"},
    "pnl.act.all_unlock": {"en": "Light + number + latch, whole cabinet",
                           "th": "เปิดไฟ+จอ+กลอน ทั้งตู้"},
    "pnl.act.reset": {"en": "Power-cycle the shelf (relays)",
                      "th": "สับรีเลย์ตัดไฟชั้นวาง (hardware reset)"},
    "pnl.act.lamp_test": {"en": "Test the status lamps (one by one)",
                          "th": "ทดสอบหลอดสถานะ (ทีละดวง)"},

    "pnl.lamp_card": {"en": "Relay outputs", "th": "เอาต์พุตรีเลย์"},
    "pnl.lamp_hint": {"en": "Each relay follows one thing. Ready, busy and fault are "
                            "three faces of one state, so putting those on three "
                            "outputs gives a traffic light — exactly one lit, worst "
                            "news first. The colour is your note about which lamp is "
                            "wired there; the gateway neither knows nor needs it.",
                      "th": "รีเลย์แต่ละตัวตามสถานะที่เลือกไว้หนึ่งอย่าง "
                            "โดย ready/busy/fault เป็นสามหน้าของสถานะเดียวกัน "
                            "จับสามอย่างนี้ลงสามเอาต์พุตจึงได้ไฟจราจร — ติดทีละดวง "
                            "เรียงตามความร้ายแรง ส่วนสีคือบันทึกของเราเองว่าเอาต์พุตนั้น "
                            "ต่อหลอดสีอะไร เกตเวย์ไม่รู้และไม่จำเป็นต้องรู้"},
    "pnl.lamp_colour.green": {"en": "green", "th": "เขียว"},
    "pnl.lamp_colour.amber": {"en": "amber", "th": "เหลือง"},
    "pnl.lamp_colour.red": {"en": "red", "th": "แดง"},
    "pnl.lamp_colour.blue": {"en": "blue", "th": "น้ำเงิน"},
    "pnl.lamp_colour.white": {"en": "white", "th": "ขาว"},
    "pnl.lamp_colour.none": {"en": "no lamp", "th": "ไม่มีไฟ"},
    "pnl.lamp_colour_hint": {"en": "Which lamp is actually fitted to this output. The gateway "
                              "drives outputs, not colours, so this is only how this "
                              "page draws the panel — it is saved here and never sent "
                              "to the gateway. Set it to match the panel in front of "
                              "you and the dots read like the real thing.",
                        "th": "เอาต์พุตนี้ติดไฟสีอะไรจริง เกตเวย์สั่งงานเป็นเอาต์พุต "
                              "ไม่รู้จักสี ค่านี้จึงใช้วาดหน้านี้เท่านั้น เก็บไว้ที่นี่ "
                              "ไม่ได้ส่งไปที่เกตเวย์ ตั้งให้ตรงกับตู้จริงแล้วจุดสี"
                              "จะอ่านได้เหมือนดูของจริง"},
    "pnl.out_n": {"en": "output {n}", "th": "เอาต์พุต {n}"},
    "pnl.out_hint": {"en": "What this output follows ({name}). Ready, busy and "
                           "fault are three faces of one state, so mapping those "
                           "to three outputs gives a traffic light — exactly one "
                           "lit. The others are plain facts and can be lit "
                           "alongside anything. The dot is lit for an output that "
                           "was on when this page was read.",
                     "th": "เอาต์พุตนี้ติดตามเงื่อนไขไหน ({name}) พร้อม / "
                           "กำลังสื่อสาร / ไม่พร้อม เป็นสามหน้าของสถานะเดียวกัน "
                           "จับสามอย่างนี้ลงสามเอาต์พุตจะได้ไฟจราจรที่ติดทีละดวง "
                           "ส่วนเงื่อนไขอื่นติดพร้อมอย่างอื่นได้ "
                           "จุดจะสว่างถ้าเอาต์พุตนั้นติดอยู่ตอนอ่านค่า"},
    "pnl.src.none": {"en": "— off", "th": "— ไม่ใช้"},
    "pnl.src.ready": {"en": "ready", "th": "พร้อมใช้งาน"},
    "pnl.src.busy": {"en": "busy — talking to the cabinet",
                     "th": "กำลังสื่อสารกับตู้"},
    "pnl.src.fault": {"en": "fault — not usable", "th": "ไม่พร้อมใช้งาน"},
    "pnl.src.link": {"en": "LAN is up", "th": "เครือข่ายเชื่อมต่อแล้ว"},
    "pnl.src.client": {"en": "a server is connected",
                       "th": "มีเซิร์ฟเวอร์เชื่อมต่ออยู่"},
    "pnl.src.sweep": {"en": "a panel sweep is running",
                      "th": "กำลังรันคำสั่งจากปุ่มหน้าตู้"},
    "pnl.src.shelf": {"en": "shelf power (hardware reset drops it)",
                      "th": "ไฟเลี้ยงชั้นวาง (รีเซตคือการตัดตัวนี้)"},
    "pnl.src.reset": {"en": "power is dropped (reset)",
                      "th": "กำลังตัดไฟ (รีเซต)"},
    "gwf.panel.lamps": {"en": "Drive the status lamps", "th": "เปิดใช้ไฟสถานะ"},
    "gwf.panel.lamps.hint": {"en": "Off leaves outputs 2-4 exactly as they are — for "
                                   "a cabinet with no lamps fitted, or while "
                                   "something else is using those outputs.",
                             "th": "ปิดแล้วเอาต์พุต 2-4 จะถูกปล่อยไว้เฉยๆ "
                                   "สำหรับตู้ที่ไม่ได้ติดไฟสถานะ หรือตอนที่เอาต์พุตนั้น"
                                   "ถูกใช้ทำอย่างอื่นอยู่"},
    "gwf.panel.lamp_hold_ms": {"en": "Busy holds for (ms)",
                               "th": "สถานะ busy ค้างนาน (ms)"},
    "gwf.panel.lamp_hold_ms.hint": {
        "en": "How long one Modbus transaction keeps the gateway counting as "
              "busy — whichever output follows busy holds for that window. "
              "These are mechanical relays, so traffic holds the lamp rather "
              "than flashing it; under steady polling it simply stays on. "
              "Shorter makes "
              "the lamp twitchier and works the relay harder.",
        "th": "ทรานแซกชัน Modbus หนึ่งครั้งทำให้เกตเวย์นับเป็น busy นานเท่าไร — "
              "เอาต์พุตที่ตามสถานะ busy จะติดค้างตามช่วงนี้ รีเลย์เป็นกลไก "
              "จึงใช้วิธีค้างไฟแทนการกระพริบ ถ้า poll ต่อเนื่องไฟจะติดนิ่ง "
              "ตั้งสั้นไปไฟจะกระตุกและรีเลย์ทำงานหนักขึ้น"},
    "gwf.panel.lamp_dwell_ms": {"en": "Minimum time on a lamp (ms)",
                                "th": "ไฟค้างสถานะเดิมอย่างน้อย (ms)"},
    "gwf.panel.lamp_dwell_ms.hint": {
        "en": "No lamp output may switch faster than this, whatever it is "
              "mapped to. It is what keeps the relays from chattering when "
              "the gateway flips between states. The shelf's power is exempt.",
        "th": "เอาต์พุตไฟห้ามสับเร็วกว่านี้ไม่ว่าจะ map กับสถานะไหน "
              "เป็นตัวกันรีเลย์สับรัวเวลาเกตเวย์สลับสถานะไปมา "
              "ไฟเลี้ยงชั้นวางไม่ติดข้อจำกัดนี้"},
    "gwf.panel.lamp_dead": {"en": "Timeouts before fault",
                            "th": "เงียบกี่ครั้งจึงนับเป็น fault"},
    "gwf.panel.lamp_dead.hint": {
        "en": "Consecutive RS485 timeouts before the gateway counts as fault "
              "— whichever output follows fault then lights. A hub channel "
              "change costs one timeout and then answers, so keep this well "
              "above the noise of normal operation.",
        "th": "จำนวนครั้งที่บัส RS485 เงียบติดกันก่อนเกตเวย์นับเป็น fault — "
              "เอาต์พุตที่ตามสถานะ fault จะติดขึ้น การสลับช่องฮับเสียหนึ่งครั้ง"
              "แล้วตอบได้ ดังนั้นควรตั้งสูงกว่าค่าปกติของการใช้งานพอสมควร"},

    "gwf.panel.enabled": {"en": "Use the panel buttons", "th": "เปิดใช้ปุ่มหน้าตู้"},
    "gwf.panel.enabled.hint": {"en": "Off on a bench, where nothing is wired to the "
                                     "inputs and a stray voltage must not sweep a "
                                     "cabinet.",
                               "th": "ปิดไว้ตอนทดสอบบนโต๊ะ เพราะไม่มีอะไรต่อที่อินพุต "
                                     "และไฟรั่วเข้ามาต้องไม่ทำให้ตู้ทำงานเอง"},
    "pnl.preset_n": {"en": "Preset {n}", "th": "พรีเซ็ต {n}"},
    "gwf.panel.preset": {"en": "Sweep preset", "th": "พรีเซ็ตที่ปุ่มใช้"},
    "gwf.panel.preset.hint": {
        "en": "Which module preset the buttons light (1-8). Brightness and "
              "colour are that preset's own per-module settings — a panel too "
              "bright at night is fixed by pointing it at a dimmer preset.",
        "th": "ปุ่มหน้าตู้จุดไฟด้วยพรีเซ็ตไหน (1-8) ความสว่างและสีเป็นค่าของ"
              "พรีเซ็ตนั้นในตัวโมดูลแต่ละตัว — ตู้สว่างเกินไปตอนกลางคืน "
              "แก้โดยชี้ไปพรีเซ็ตที่หรี่กว่า"},
    "gwf.panel.step_on_ms": {"en": "Pause per slot — light (ms)",
                             "th": "หน่วงต่อช่อง — เปิดไฟ (ms)"},
    "gwf.panel.step_on_ms.hint": {
        "en": "How long the all-on sweep waits between slots. 0 walks as fast "
              "as the bus allows; a few hundred ms turns it into a visible "
              "wave.",
        "th": "การกวาดเปิดไฟรอระหว่างช่องนานเท่าไร 0 = เร็วสุดเท่าที่บัสไหว "
              "ตั้งสักสองสามร้อย ms จะเห็นไฟไล่เป็นคลื่น"},
    "gwf.panel.step_off_ms": {"en": "Pause per slot — clear (ms)",
                              "th": "หน่วงต่อช่อง — ปิดไฟ (ms)"},
    "gwf.panel.step_off_ms.hint": {
        "en": "How long the all-off sweep waits between slots. Usually 0 — "
              "clearing has nothing to show off.",
        "th": "การกวาดปิดไฟรอระหว่างช่องนานเท่าไร ปกติ 0 — การดับไฟไม่มีอะไรต้องโชว์"},
    "gwf.panel.step_unlock_ms": {"en": "Pause per slot — light + latch (ms)",
                                 "th": "หน่วงต่อช่อง — เปิดไฟ+กลอน (ms)"},
    "gwf.panel.step_unlock_ms.hint": {
        "en": "How long the unlock sweep waits between slots. This one is a "
              "power budget: each slot fires a solenoid, and the pause keeps "
              "a whole-cabinet unlock from asking the supply for many latches "
              "at once.",
        "th": "การกวาดเปิดไฟ+กลอนรอระหว่างช่องนานเท่าไร ตัวนี้คืองบไฟ: "
              "แต่ละช่องยิงโซลินอยด์ การหน่วงช่วยไม่ให้ปลดล็อกทั้งตู้"
              "กระชากไฟหลายกลอนพร้อมกัน"},
    "gwf.panel.bright": {"en": "Test brightness (%)",
                         "th": "ความสว่างทดสอบ (%)"},
    "gwf.panel.bright.hint": {
        "en": "0 = each module's own preset brightness. 1-100 forces this "
              "brightness while a button sweep lights the cabinet — written "
              "to the modules' volatile global brightness, so a power cycle "
              "restores the configured look and nothing is stored. Adds one "
              "write per slot, so the sweep is a little slower while set.",
        "th": "0 = ใช้ความสว่างตามพรีเซ็ตของแต่ละโมดูล 1-100 = บังคับความสว่างนี้"
              "ตอนปุ่มหน้าตู้จุดไฟ เขียนลงค่าความสว่างชั่วคราวของโมดูล "
              "ดับไฟแล้วกลับเป็นค่าที่ตั้งไว้เดิม ไม่มีอะไรถูกบันทึกถาวร "
              "มีผลให้กวาดช้าลงเล็กน้อยเพราะเขียนเพิ่มช่องละหนึ่งครั้ง"},
    "gwf.panel.cabinet": {"en": "Cabinet size", "th": "ขนาดตู้"},
    "gwf.panel.cabinet.hint": {"en": "40, 64 or 80 — decides which slots a sweep "
                                     "walks and in what order. Checked against "
                                     "the header's cabinet picker.",
                               "th": "40, 64 หรือ 80 — กำหนดว่าจะไล่ช่องไหนบ้างและ"
                                     "เรียงลำดับอย่างไร ตรวจเทียบกับรุ่นตู้"
                                     "ที่เลือกไว้ที่แถบด้านบน"},
    "gw.cab.mismatch": {"en": "Cabinet mismatch — the gateway is set for a "
                              "type {gw} cabinet, but this tool is set to {tool}.",
                        "th": "ขนาดตู้ไม่ตรงกัน — เกตเวย์ตั้งเป็นตู้ {gw} "
                              "แต่เครื่องมือเลือก {tool} ไว้"},
    "gw.cab.fix": {"en": "Set {code}", "th": "ตั้งเป็น {code}"},
    "gw.cab.fix_tip": {"en": "Stages panel.cabinet = {code} as an ordinary edit — "
                             "review and Save to apply.",
                       "th": "ใส่ค่า panel.cabinet = {code} เป็นรายการแก้ไขปกติ "
                             "ตรวจแล้วกดบันทึกเพื่อให้มีผล"},
    "gw.cab.no_code": {"en": "Tool is set to {label} — this firmware knows only "
                             "40, 64 and 80 (panel.shape needs gateway 1.9.0).",
                       "th": "เครื่องมือเลือก {label} — เฟิร์มแวร์รุ่นนี้รู้จักเฉพาะ "
                             "40, 64, 80 (ทรงอิสระต้องใช้ gateway 1.9.0 ขึ้นไป)"},
    "gw.cab.shape_mismatch": {"en": "Sweep shape mismatch — this tool is set to "
                                    "{tool}, which is {want} per row.",
                              "th": "ทรงกวาดไม่ตรงกัน — เครื่องมือเลือก {tool} "
                                    "ซึ่งเป็นชั้นละ {want}"},
    "gw.cab.stray_shape": {"en": "The gateway follows a custom sweep shape, but "
                                 "this tool is set to {tool}.",
                           "th": "เกตเวย์กำลังใช้ทรงกวาดแบบกำหนดเอง "
                                 "แต่เครื่องมือเลือก {tool} ไว้"},
    "gw.cab.set_shape": {"en": "Set shape", "th": "ตั้งทรงนี้"},
    "gw.cab.shape_active": {"en": "Sweep shape {shape} is set — it overrides "
                                  "the size above.",
                            "th": "กำลังใช้ทรงกวาด {shape} — มีผลแทนขนาดด้านบน"},
    "gwf.panel.step_ms": {"en": "Pause between slots (ms)", "th": "หน่วงระหว่างช่อง (ms)"},
    "gwf.panel.step_ms.hint": {"en": "Extra breathing room on top of the bus, which "
                                     "already costs about 100 ms a slot. 0 runs as "
                                     "fast as the bus allows.",
                               "th": "หน่วงเพิ่มจากเวลาบัสซึ่งกินราว 100 ms ต่อช่องอยู่แล้ว "
                                     "ใส่ 0 = เร็วที่สุดเท่าที่บัสไหว"},
    "gwf.panel.reset_ms": {"en": "Power off for (ms)", "th": "ตัดไฟนาน (ms)"},
    "gwf.panel.reset_ms.hint": {"en": "How long both relays drop on a reset press — "
                                      "long enough for the modules' rails to "
                                      "actually collapse.",
                                "th": "ระยะเวลาที่รีเลย์ทั้งสองตัวตัดไฟตอนกดปุ่มรีเซ็ต "
                                      "ต้องนานพอให้ไฟในโมดูลตกจริง"},

    "gw.hub_rows": {"en": "Rows", "th": "จำนวนชั้น"},
    "gw.hub_rows_tip": {"en": "How many rows this cabinet has. Not every LGS is "
                              "ten rows tall, and rows it does not have should "
                              "not appear in the wiring. When the map is empty "
                              "this follows the header's cabinet.",
                        "th": "ตู้นี้มีกี่ชั้น ตู้ LGS ไม่ได้มี 10 ชั้นทุกรุ่น "
                              "ชั้นที่ไม่มีอยู่จริงไม่ควรโผล่ในผังสาย "
                              "ถ้าผังยังว่างจะตั้งต้นตามรุ่นตู้ที่แถบด้านบน"},
    "gw.hub.per_row": {"en": "one channel per row", "th": "ช่องละชั้น"},
    "gw.hub.per_row_tip": {"en": "Row 1 to channel 1, row 2 to channel 2, and so "
                                 "on — the straightforward wiring.",
                           "th": "ชั้น 1 เข้าช่อง 1, ชั้น 2 เข้าช่อง 2 ไล่ไปตามลำดับ "
                                 "คือการเดินสายแบบตรงไปตรงมา"},
    "gw.hub.one_channel": {"en": "all one channel", "th": "รวมช่องเดียว"},
    "gw.hub.one_channel_tip": {"en": "Every row on channel 1. Nothing ever has to "
                                     "switch, so confirmations stay fast.",
                               "th": "ทุกชั้นอยู่ช่อง 1 ไม่มีการสลับช่องเลย "
                                     "การยืนยันจึงไวที่สุด"},
    "gw.hub.nohub": {"en": "no hub", "th": "ไม่มีฮับ"},
    "gw.hub.nohub_tip": {"en": "The bus is wired straight to the modules — turns "
                               "the hub handling off entirely.",
                         "th": "บัสต่อตรงเข้าโมดูล ปิดการจัดการฮับทั้งหมด"},
    "gw.hub_map_adopted": {
        "en": "Cabinet wiring updated from the gateway: {map}. The tool now "
              "groups slots by these channels.",
        "th": "อัปเดตผังสายจากเกตเวย์แล้ว: {map} เครื่องมือจะจัดกลุ่มช่องตามนี้"},
    "gw.cfg_card": {"en": "Config file", "th": "ไฟล์ค่าตั้ง"},
    "gw.cfg_hint": {"en": "Back up the gateway's settings to a file, or stage a "
                          "file's settings for review. A firmware upgrade whose "
                          "settings struct changed wipes the store — export "
                          "first, flash, import, Save. Import never writes by "
                          "itself: values arrive as unsaved edits.",
                    "th": "สำรองค่าตั้งของ gateway เป็นไฟล์ หรือนำไฟล์กลับเข้ามา "
                          "เป็นรายการแก้ไขรอตรวจ อัปเดตเฟิร์มแวร์ที่โครงสร้างค่าตั้งเปลี่ยน"
                          "จะล้างค่าในบอร์ด — ส่งออกก่อน แฟลช นำเข้า แล้วกดบันทึก "
                          "การนำเข้าไม่เขียนเอง ค่ามาเป็นรายการแก้ไขค้างเสมอ"},
    "gw.cfg_export": {"en": "Export config", "th": "ส่งออกค่าตั้ง"},
    "gw.cfg_export_tip": {"en": "Saves every setting the gateway reported, as it "
                                "is running now — unsaved edits are not included.",
                          "th": "บันทึกทุกค่าตามที่ gateway ใช้งานอยู่จริง "
                                "ค่าที่แก้ค้างยังไม่บันทึกจะไม่ติดไปด้วย"},
    "gw.cfg_import": {"en": "Import config…", "th": "นำเข้าค่าตั้ง…"},
    "gw.cfg_need_read": {"en": "Read the gateway first — Detect, then try again.",
                         "th": "อ่านค่าจาก gateway ก่อน — กดค้นหาแล้วลองใหม่"},
    "gw.cfg_bad_file": {"en": "Not a gateway config file.",
                        "th": "ไม่ใช่ไฟล์ค่าตั้งของ gateway"},
    "gw.cfg_imported": {"en": "{n} change(s) staged — review and Save to apply.",
                        "th": "เตรียมไว้ {n} รายการ — ตรวจแล้วกดบันทึกเพื่อให้มีผล"},
    "gw.cfg_skipped": {"en": "{n} key(s) this firmware does not have were skipped.",
                       "th": "ข้าม {n} คีย์ที่เฟิร์มแวร์รุ่นนี้ไม่มี"},
    "rpt.card": {"en": "Site report (PDF)", "th": "รายงานประจำตู้ (PDF)"},
    "rpt.hint": {"en": "One document that says what is installed: the gateway's "
                       "identity, settings and recent events, the cabinet's shape, "
                       "and every module's chip UID, type, firmware and lifetime "
                       "statistics — read from the modules themselves, one or two "
                       "reads each. Needs a Detect first and a connected bus. A "
                       "copy is kept in data/exports.",
                 "th": "เอกสารเดียวที่บอกว่าติดตั้งอะไรไว้: ข้อมูล ค่าตั้ง และเหตุการณ์ล่าสุด"
                       "ของ gateway ทรงตู้ และ UID / รุ่น / เฟิร์มแวร์ / สถิติสะสมของ"
                       "ทุกโมดูล อ่านจากโมดูลจริงตัวละหนึ่งถึงสองครั้ง "
                       "ต้องกดค้นหา gateway ก่อนและต่อบัสอยู่ สำเนาเก็บไว้ใน data/exports"},
    "rpt.run": {"en": "Create PDF report", "th": "สร้างรายงาน PDF"},
    "rpt.need_connect": {"en": "Connect to the bus first — the module sweep "
                               "runs over Modbus.",
                         "th": "กดเชื่อมต่อบัสก่อน — การไล่อ่านโมดูลวิ่งผ่าน Modbus"},
    "rpt.running": {"en": "reading {n} modules…", "th": "กำลังอ่าน {n} โมดูล…"},
    "rpt.cancelled": {"en": "cancelled", "th": "ยกเลิกแล้ว"},
    "rpt.done": {"en": "{a}/{n} modules answered", "th": "โมดูลตอบ {a}/{n}"},
    "rpt.saved": {"en": "Report saved: {name} (also in data/exports)",
                  "th": "บันทึกรายงานแล้ว: {name} (สำเนาใน data/exports)"},
    "rpt.no_lib": {"en": "PDF library missing — run: pip install fpdf2",
                   "th": "ไม่มีไลบรารี PDF — สั่ง: pip install fpdf2"},
    "gwf.panel.shape": {"en": "Sweep shape (slots per row)",
                        "th": "ทรงกวาด (ช่องต่อชั้น)"},
    "gwf.panel.shape.hint": {"en": "Slots per row from the top, e.g. 8,8,4,4,2. "
                                   "When set, button sweeps walk this instead of "
                                   "the preset size; 0 clears it.",
                             "th": "จำนวนช่องของแต่ละชั้นจากบนลงล่าง เช่น 8,8,4,4,2 "
                                   "ถ้าตั้งไว้ ปุ่มหน้าตู้จะกวาดตามนี้แทนขนาดสำเร็จรูป "
                                   "ใส่ 0 เพื่อล้าง"},
    "gwf.bus.hub_map": {"en": "Row → hub channel", "th": "ผังแถว → ช่องฮับ"},
    "gwf.bus.hub_map.hint": {"en": "One entry per row 1-10, comma-separated. Value = "
                                   "hub channel 1-8; 0 = wired straight, no hub. All "
                                   "zeros turns hub handling off.",
                             "th": "หนึ่งค่าต่อแถว 1-10 คั่นด้วยจุลภาค ค่า = ช่องฮับ 1-8, "
                                   "0 = ต่อตรงไม่ผ่านฮับ ใส่ 0 ทั้งหมด = ปิดการซ่อม"},
    "gwf.bus.hub_settle_ms": {"en": "Hub settle time (ms)", "th": "เวลาฮับพร้อม (ms)"},
    "gwf.bus.hub_settle_ms.hint": {"en": "How long the hub stays deaf after the first "
                                         "frame on a new channel. Measured ~2 s on the "
                                         "LGS-64 hub.",
                                   "th": "ช่วงที่ฮับไม่รับส่งหลังเฟรมแรกบนช่องใหม่ "
                                         "วัดจริงบนตู้ LGS-64 ได้ราว 2 วินาที"},
    "gwf.bus.hub_budget_ms": {"en": "Repair time cap (ms)", "th": "เพดานเวลาซ่อม (ms)"},
    "gwf.bus.hub_budget_ms.hint": {"en": "Ceiling for one transaction including the "
                                         "hold. Keep it under the server's timeout — or "
                                         "raise it past the settle time if the server "
                                         "waits long, and the repair finishes in one "
                                         "transaction.",
                                   "th": "เพดานเวลาต่อหนึ่งทรานแซกชันรวมการหน่วง "
                                         "ต้องต่ำกว่า timeout ของเซิร์ฟเวอร์ — หรือถ้า"
                                         "เซิร์ฟเวอร์รอนาน ตั้งเกินเวลาฮับพร้อมจะซ่อมจบ"
                                         "ในทรานแซกชันเดียว"},
    "gwf.bus.hub_retry": {"en": "Attempts after a channel change",
                          "th": "จำนวนยิงตอนข้ามช่อง"},
    "gwf.bus.hub_retry.hint": {"en": "2 = the trigger frame plus one delayed retry "
                                     "when the time cap allows it.",
                               "th": "2 = เฟรมกระตุ้น + ยิงซ้ำหลังหน่วง เมื่อเพดานเวลาพอ"},
    "gwf.bus.hub_gap_ms": {"en": "Extra margin (ms)", "th": "เผื่อเพิ่ม (ms)"},
    "gwf.bus.hub_gap_ms.hint": {"en": "Added past the settle deadline, for hubs whose "
                                      "timing wanders.",
                                "th": "บวกเพิ่มจากเวลาฮับพร้อม เผื่อฮับที่จังหวะเวลาไม่นิ่ง"},

    "gw.on": {"en": "on", "th": "เปิด"},
    "gw.off": {"en": "off", "th": "ปิด"},

    "gw.source": {"en": "settings source", "th": "ที่มาของค่า"},
    "gw.src.stored": {"en": "stored", "th": "จากหน่วยความจำ"},
    "gw.src.defaults": {"en": "defaults (nothing saved yet)", "th": "ค่าเริ่มต้น (ยังไม่เคยบันทึก)"},
    "gw.src.corrupt": {"en": "stored copy is corrupt — running on defaults",
                       "th": "ข้อมูลที่เก็บไว้เสีย — กำลังใช้ค่าเริ่มต้น"},
    "gw.src.unavailable": {"en": "no storage on this unit — settings will not survive a reboot",
                           "th": "เครื่องนี้ไม่มีที่เก็บ — ค่าจะหายเมื่อรีบูต"},
    "gw.dirty": {"en": "{n} unsaved change(s)", "th": "แก้ไว้ยังไม่บันทึก {n} รายการ"},
    "gw.save": {"en": "Save to gateway", "th": "บันทึกลง gateway"},
    "gw.save_title": {"en": "Write these settings to the gateway?", "th": "เขียนค่าเหล่านี้ลง gateway?"},
    "gw.save_ok": {"en": "saved", "th": "บันทึกแล้ว"},
    "gw.needs_reboot": {"en": "takes effect after a reboot: {keys}",
                        "th": "จะมีผลหลังรีบูต: {keys}"},
    "gw.discard": {"en": "Discard", "th": "ยกเลิกการแก้"},
    "gw.defaults": {"en": "Factory defaults", "th": "ค่าโรงงาน"},
    "gw.defaults_title": {"en": "Load factory defaults?", "th": "โหลดค่าโรงงาน?"},
    "gw.defaults_body": {"en": "The factory values are filled into the fields so you "
                               "can check them first. Nothing is written until you Save.",
                         "th": "ค่าโรงงานจะถูกเติมลงในช่องกรอกให้ตรวจดูก่อน "
                               "ยังไม่เขียนจนกว่าจะกดบันทึก"},
    "gw.defaults_loaded": {"en": "{n} factory value(s) filled in — review them, then Save.",
                           "th": "เติมค่าโรงงาน {n} รายการแล้ว — ตรวจดูก่อนแล้วกดบันทึก"},
    "gw.pending_on_gateway": {"en": "staged on the gateway: {v}",
                              "th": "มีค่ารออยู่ที่ gateway: {v}"},
    "gw.fw_card": {"en": "Gateway firmware", "th": "เฟิร์มแวร์ของ Gateway"},
    "gw.fw_hint": {
        "en": "Updates the Opta's own firmware over its USB cable — no "
              "PlatformIO and no developer laptop. The gateway reboots into "
              "its bootloader, takes the new image and restarts, so the bus "
              "has no bridge for about half a minute. Use the .bin from the "
              "gateway release; a wrong-sized file is refused before "
              "anything is written.",
        "th": "อัปเดตเฟิร์มแวร์ของ Opta ผ่านสาย USB — ไม่ต้องใช้ PlatformIO "
              "หรือเครื่องนักพัฒนา · gateway จะรีบูตเข้า bootloader รับ image "
              "ใหม่แล้วเริ่มใหม่ ระหว่างนั้นบัสจะไม่มีสะพานราวครึ่งนาที · "
              "ใช้ไฟล์ .bin จาก release ของ gateway — ไฟล์ขนาดผิดจะถูกปฏิเสธ"
              "ก่อนเขียนอะไรลงไป"},
    "gw.fw_none": {"en": "no file chosen", "th": "ยังไม่ได้เลือกไฟล์"},
    "gw.fw_chosen": {"en": "{name} — {size} B", "th": "{name} — {size} ไบต์"},
    "gw.fw_run": {"en": "Update firmware", "th": "อัปเดตเฟิร์มแวร์"},
    "gw.fw_need_image": {"en": "Choose a gateway .bin first",
                         "th": "เลือกไฟล์ .bin ของ gateway ก่อน"},
    "gw.fw_confirm_title": {"en": "Update the gateway's firmware?",
                            "th": "อัปเดตเฟิร์มแวร์ของ gateway?"},
    "gw.fw_confirm_body": {
        "en": "{name} will be written to the gateway on {port}. The bus has "
              "no bridge until it restarts. Do not unplug it while this runs.",
        "th": "จะเขียน {name} ลง gateway ที่ {port} · บัสจะไม่มีสะพานจนกว่ามัน"
              "จะเริ่มใหม่ · ห้ามถอดสายระหว่างทำงาน"},
    "gw.prov_run": {"en": "Prepare a new Opta", "th": "เตรียม Opta ใหม่"},
    "gw.prov_hint": {
        "en": "A factory-fresh Opta has no partitions on its QSPI flash, so "
              "the gateway finds no settings store and cannot save anything "
              "(cfg.store=unavailable). This creates them once — WiFi, OTA, "
              "the 1 MB KVStore the gateway needs, and user data — then puts "
              "the gateway firmware back. Erases the QSPI: on a new board "
              "there is nothing to lose, on a working one it wipes every "
              "saved setting.",
        "th": "Opta ที่เพิ่งออกจากโรงงานยังไม่มี partition บน QSPI flash "
              "gateway จึงหาที่เก็บค่าตั้งค่าไม่เจอและบันทึกอะไรไม่ได้เลย "
              "(cfg.store=unavailable) · ปุ่มนี้สร้างให้ครั้งเดียว — WiFi, OTA, "
              "KVStore 1 MB ที่ gateway ต้องใช้ และ user data — แล้วคืนเฟิร์มแวร์ "
              "gateway กลับ · จะล้าง QSPI ทั้งหมด: บอร์ดใหม่ไม่มีอะไรให้เสีย "
              "แต่บอร์ดที่ใช้งานอยู่จะเสียค่าที่บันทึกไว้ทุกตัว"},
    "gw.prov_confirm_title": {"en": "Prepare this Opta from scratch?",
                              "th": "เตรียม Opta ตัวนี้ใหม่ทั้งหมด?"},
    "gw.prov_confirm_body": {
        "en": "Everything on the QSPI flash of the board on {port} is erased "
              "and repartitioned, then {name} is written back. Takes a couple "
              "of minutes; do not unplug it. Only do this on a board that "
              "reports cfg.store=unavailable.",
        "th": "ข้อมูลบน QSPI flash ของบอร์ดที่ {port} จะถูกล้างและแบ่ง partition "
              "ใหม่ทั้งหมด แล้วเขียน {name} กลับ · ใช้เวลาสองสามนาที ห้ามถอดสาย · "
              "ทำเฉพาะบอร์ดที่รายงาน cfg.store=unavailable เท่านั้น"},
    "gw.reboot": {"en": "Reboot", "th": "รีบูต"},
    "gw.reboot_title": {"en": "Reboot the gateway?", "th": "รีบูต gateway?"},
    "gw.reboot_body": {"en": "The COM port disappears for a few seconds and any host "
                             "talking to the bus loses its connection.",
                       "th": "พอร์ต COM จะหายไปไม่กี่วินาที และโปรแกรมที่คุยกับบัสอยู่จะหลุด"},
    "gw.btn_hint": {"en": "on-board button now reads {v} — hold it through boot for "
                          "3 s to start on defaults",
                    "th": "ปุ่มบนบอร์ดอ่านค่าได้ {v} — กดค้างตอนบูต 3 วิ เพื่อเริ่มด้วยค่าเริ่มต้น"},

    # ── Commissioning tab ──────────────────────────────────────────────────
    "tab.commission": {"en": "New module", "th": "ติดตั้งโมดูลใหม่"},
    "cm.banner": {"en": "Erases and rewrites the module's flash over ST-Link. "
                        "The module does not need to be on the RS485 bus.",
                  "th": "ล้างและเขียนแฟลชของโมดูลใหม่ผ่าน ST-Link "
                        "ไม่จำเป็นต้องต่อโมดูลเข้าบัส RS485"},
    "cm.image": {"en": "Firmware image", "th": "ไฟล์เฟิร์มแวร์"},
    "cm.image_hint": {"en": "The combined bootloader + application file "
                            "(*_factory_*.bin), written at 0x08000000.",
                      "th": "ไฟล์รวม bootloader + แอป (*_factory_*.bin) "
                            "เขียนที่ 0x08000000"},
    "cm.no_image": {"en": "no file chosen", "th": "ยังไม่ได้เลือกไฟล์"},
    "cm.image_ok": {"en": "{name} — {size} B — {detail}",
                    "th": "{name} — {size} ไบต์ — {detail}"},
    "cm.identity": {"en": "Identity", "th": "ข้อมูลประจำตัว"},
    "cm.identity_hint": {"en": "The ID goes into the image before it is flashed, so "
                               "the module answers at it the first time it starts.",
                         "th": "ID จะถูกใส่ลงในไฟล์ก่อนเขียน "
                               "โมดูลจึงตอบที่หมายเลขนี้ตั้งแต่บูตครั้งแรก"},
    "cm.slave_id": {"en": "Slave ID", "th": "Slave ID"},
    "cm.grid": {"en": "Grid", "th": "ผัง"},
    "cm.lot": {"en": "Lot", "th": "ล็อตการผลิต"},
    "cm.lot_hint": {"en": "Optional. Recorded in commission_log.csv next to the "
                          "chip's own serial number.",
                    "th": "ใส่หรือไม่ใส่ก็ได้ บันทึกลง commission_log.csv "
                          "คู่กับเลขประจำตัวของชิป"},
    "cm.mode.single": {"en": "One module", "th": "ทีละโมดูล"},
    "cm.mode.batch": {"en": "Continuous", "th": "ต่อเนื่องทั้งล็อต"},
    "cm.batch.pick": {"en": "IDs to assign, in order",
                      "th": "ID ที่จะแจก เรียงตามลำดับ"},
    "cm.batch.pick_hint": {
        "en": "Pick the addresses this lot should get, exactly like the "
              "Installation Check grid. The runner waits for a blank board, "
              "gives it the lowest remaining ID, and moves on when you swap "
              "boards — flash and swap until the queue is empty.",
        "th": "เลือกที่อยู่ที่ล็อตนี้ควรได้ เหมือนผังหน้าตรวจการติดตั้ง "
              "โปรแกรมจะรอบอร์ดเปล่า แจก ID ต่ำสุดที่เหลือ "
              "แล้วไปตัวถัดไปเมื่อสลับบอร์ด — ทำจนหมดคิว"},
    "cm.batch.selected": {"en": "{n} selected", "th": "เลือกแล้ว {n}"},
    "cm.batch.no_overwrite": {
        "en": "Continuous mode never overwrites: a board that already has an "
              "ID keeps it. Renumbering a board stays a one-module act.",
        "th": "โหมดต่อเนื่องไม่เขียนทับ ID เดิม — บอร์ดที่มี ID แล้วจะเก็บของเดิมไว้ "
              "การเปลี่ยนเลขบอร์ดให้ทำแบบทีละโมดูล"},
    "cm.batch.need_ids": {"en": "Pick at least one ID in the grid first",
                          "th": "เลือก ID ในผังอย่างน้อย 1 ช่องก่อน"},
    "cm.batch.confirm_body": {
        "en": "Flash {name} to {n} blank boards, assigning IDs {first}-{last} "
              "in order. Swap boards when told; the queue stops on any failure.",
        "th": "จะ flash {name} ลงบอร์ดเปล่า {n} ตัว แจก ID {first}-{last} "
              "ตามลำดับ สลับบอร์ดตามที่โปรแกรมบอก ถ้าตัวไหนพลาดคิวจะหยุดทันที"},
    "cm.batch.progress": {"en": "module {done}/{total}",
                          "th": "โมดูล {done}/{total}"},
    "cm.overwrite_card": {"en": "Modules that already have an ID",
                          "th": "โมดูลที่มี ID อยู่แล้ว"},
    "cm.overwrite": {"en": "Overwrite an ID already stored on the module",
                     "th": "เขียนทับ ID ที่โมดูลเก็บไว้แล้ว"},
    "cm.overwrite_note": {"en": "Off by default: without this the image can only "
                                "fill in an ID on a module that has none, so it can "
                                "never renumber a cabinet already in service.",
                          "th": "ปิดไว้เป็นค่าเริ่มต้น — ถ้าไม่เปิด ไฟล์จะตั้ง ID ได้เฉพาะ"
                                "โมดูลที่ยังไม่มี ID จึงเปลี่ยนเลขตู้ที่ใช้งานอยู่ไม่ได้เลย"},
    "cm.run": {"en": "Flash and set ID", "th": "เขียนและตั้ง ID"},
    "cm.step": {"en": "step {done}/{total}", "th": "ขั้นที่ {done}/{total}"},
    "cm.need_image": {"en": "Choose a firmware image first",
                      "th": "เลือกไฟล์เฟิร์มแวร์ก่อน"},
    "cm.bad_id": {"en": "ID {id} cannot be assigned — use 1-245",
                  "th": "ตั้ง ID {id} ไม่ได้ — ใช้ได้ 1-245"},
    "cm.confirm_title": {"en": "Flash this module?", "th": "เขียนโมดูลนี้?"},
    "cm.confirm_body": {"en": "{name} will be written to the module connected to the "
                              "ST-Link, and it will answer at ID {id}.",
                        "th": "จะเขียน {name} ลงโมดูลที่ต่อกับ ST-Link อยู่ "
                              "แล้วโมดูลจะตอบที่ ID {id}"},
    "cm.confirm_overwrite": {"en": "Overwrite is on: this replaces the ID the module "
                                   "already has.",
                             "th": "เปิดเขียนทับไว้ — จะแทนที่ ID เดิมของโมดูล"},

    # ── OTA tab ────────────────────────────────────────────────────────────
    "tab.ota": {"en": "Firmware", "th": "อัปเดตเฟิร์มแวร์"},
    "ota.banner": {"en": "Writes firmware over RS485. Keep power on until the "
                         "update finishes — an interrupted apply can leave a module "
                         "needing a cable flash.",
                   "th": "เขียนเฟิร์มแวร์ผ่าน RS485 — ห้ามตัดไฟจนกว่าจะเสร็จ "
                         "ถ้าหยุดกลางคันโมดูลอาจต้องต่อสายแฟลชใหม่"},
    "ota.image": {"en": "Firmware image", "th": "ไฟล์เฟิร์มแวร์"},
    "ota.upload_hint": {"en": "Pick the .bin built for the app slot (flash offset "
                              "0x1000), at most {max} bytes.",
                        "th": "เลือกไฟล์ .bin ที่ build สำหรับ app slot (flash offset "
                              "0x1000) ขนาดไม่เกิน {max} ไบต์"},
    "ota.image_info": {"en": "{name} — {size} B, CRC32 {crc}, {chunks} chunks",
                       "th": "{name} — {size} ไบต์, CRC32 {crc}, {chunks} ชิ้น"},
    "ota.no_image": {"en": "no firmware selected", "th": "ยังไม่ได้เลือกไฟล์เฟิร์มแวร์"},
    "ota.targets": {"en": "Target modules", "th": "โมดูลปลายทาง"},
    "ota.ids_label": {"en": "device IDs (comma separated)", "th": "รหัสอุปกรณ์ (คั่นด้วยจุลภาค)"},
    "ota.use_current": {"en": "Use the header ID", "th": "ใช้ ID จากแถบบน"},
    "ota.use_scan": {"en": "From last scan", "th": "จากผลสแกนล่าสุด"},
    "ota.no_ids": {"en": "no valid device IDs", "th": "ยังไม่มีรหัสอุปกรณ์ที่ถูกต้อง"},
    "ota.targets_note": {"en": "The image itself is broadcast to every module on the "
                               "bus. This list is what gets probed first, repaired "
                               "chunk by chunk, and verified afterwards — so list "
                               "every module you are updating.",
                         "th": "ตัวไฟล์เฟิร์มแวร์ถูกส่งถึงทุกโมดูลบนบัสอยู่แล้ว "
                               "รายการนี้คือตัวที่จะถูกตรวจก่อนเริ่ม ซ่อมข้อมูลที่ขาด "
                               "และยืนยันผลเป็นรายตัว — จึงควรใส่ให้ครบทุกตัวที่กำลังอัปเดต"},
    "ota.broadcast_apply": {"en": "Apply with one broadcast instead of per device",
                            "th": "สั่งใช้งานแบบ broadcast ครั้งเดียวแทนทีละเครื่อง"},
    "ota.broadcast_warn": {"en": "every module on the bus that verified the image "
                                 "will switch to it, including ones not listed above",
                           "th": "ทุกโมดูลบนบัสที่ verify ผ่านจะเปลี่ยนไปใช้เฟิร์มแวร์นี้ "
                                 "รวมถึงตัวที่ไม่ได้อยู่ในรายการด้านบน"},
    "ota.send": {"en": "Send firmware", "th": "ส่งเฟิร์มแวร์"},
    "ota.status": {"en": "Read status", "th": "อ่านสถานะ"},
    "ota.abort": {"en": "Abort session", "th": "ยกเลิกเซสชัน"},
    "ota.abort_sent": {"en": "abort broadcast sent", "th": "ส่งคำสั่งยกเลิกแบบ broadcast แล้ว"},
    "ota.confirm_title": {"en": "Flash firmware?", "th": "เขียนเฟิร์มแวร์?"},
    "ota.confirm_body": {"en": "{size} B to {n} device(s): {ids}. The bus is busy for "
                               "a few minutes and each module reboots at the end.",
                         "th": "{size} ไบต์ ไปยัง {n} เครื่อง: {ids} "
                               "บัสจะไม่ว่างหลายนาทีและทุกโมดูลจะรีบูตตอนจบ"},
    "ota.confirm_btn": {"en": "FLASH", "th": "เขียน"},
    "ota.progress": {"en": "chunk {done}/{total}", "th": "ชิ้นที่ {done}/{total}"},

    # ── danger tab ─────────────────────────────────────────────────────────
    "dng.banner": {"en": "These commands reboot or wipe the module — double-check "
                         "the target ID",
                   "th": "คำสั่งเหล่านี้จะรีบูตหรือล้างค่าโมดูล — ตรวจ ID เป้าหมายให้แน่ใจ"},
    "dng.factory": {"en": "Factory reset", "th": "รีเซ็ตค่าโรงงาน"},
    "dng.keep_id": {"en": "Keep slave ID (500→501)", "th": "คง Slave ID เดิม (500→501)"},
    "dng.wipe_all": {"en": "Wipe everything (500→502)", "th": "ล้างทั้งหมด (500→502)"},
    "dng.arm": {"en": "Arm factory reset…", "th": "เตรียมรีเซ็ตค่าโรงงาน…"},
    "dng.arm_title": {"en": "Arm factory reset", "th": "เตรียมรีเซ็ตค่าโรงงาน"},
    "dng.arm_seq": {"en": "Sequence: coil {apply} (mode) → coil 500 (go) → device "
                          "reboots ~3 s.",
                    "th": "ลำดับ: coil {apply} (เลือกโหมด) → coil 500 (สั่งทำ) → "
                          "อุปกรณ์รีบูต ~3 วิ"},
    "dng.wipe_warn": {"en": "Wipe-all restores ID {id} and baud 9600!",
                      "th": "การล้างทั้งหมดจะคืนค่า ID {id} และ baud 9600!"},
    "dng.type_id": {"en": "Type the slave ID ({id}) to arm",
                    "th": "พิมพ์ Slave ID ({id}) เพื่อยืนยัน"},
    "dng.arm_btn": {"en": "Arm", "th": "เตรียม"},
    "dng.really": {"en": "REALLY apply factory reset?", "th": "ยืนยันรีเซ็ตค่าโรงงานจริงหรือไม่?"},
    "dng.apply": {"en": "APPLY", "th": "ยืนยัน"},
    "dng.confirm": {"en": "CONFIRM", "th": "ยืนยัน"},
    "dng.target": {"en": "Target: slave {id} — continue?", "th": "เป้าหมาย: slave {id} — ทำต่อหรือไม่?"},
    "dng.save": {"en": "Save to EEPROM (503)", "th": "บันทึกลง EEPROM (503)"},
    "dng.save_note": {"en": "Persists R/W(F) registers; reboots ~3 s",
                      "th": "บันทึกค่า R/W(F) ถาวร แล้วรีบูต ~3 วิ"},
    "dng.save_btn": {"en": "Save…", "th": "บันทึก…"},
    "dng.save_title": {"en": "Persist config to EEPROM + reboot",
                       "th": "บันทึกค่าลง EEPROM แล้วรีบูต"},
    "dng.soft": {"en": "Software reset (504)", "th": "รีเซ็ตซอฟต์แวร์ (504)"},
    "dng.soft_note": {"en": "Reboots the module ~3 s", "th": "รีบูตโมดูล ~3 วิ"},
    "dng.soft_btn": {"en": "Reset…", "th": "รีเซ็ต…"},
    "dng.soft_title": {"en": "Software reset the module", "th": "รีเซ็ตซอฟต์แวร์ของโมดูล"},
    "dng.stats": {"en": "Clear statistics (510)", "th": "ล้างสถิติ (510)"},
    "dng.stats_note": {"en": "Zeroes regs 200-281 (persisted)",
                       "th": "ล้างค่า reg 200-281 ให้เป็นศูนย์ (มีผลถาวร)"},
    "dng.stats_btn": {"en": "Clear…", "th": "ล้าง…"},
    "dng.stats_title": {"en": "Clear all statistics counters", "th": "ล้างตัวนับสถิติทั้งหมด"},
    "dng.setid": {"en": "Set Slave ID (reg 4 → persist 503)",
                  "th": "ตั้ง Slave ID (reg 4 → บันทึก 503)"},
    "dng.setid_note": {"en": "Grid convention: row x 10 + col (11-108) · factory {factory} "
                             "· {forbidden} is the SET_ID temporary ID",
                       "th": "รูปแบบผัง: แถว x 10 + ช่อง (11-108) · ค่าโรงงาน {factory} "
                             "· {forbidden} คือ ID ชั่วคราวของโหมด SET_ID"},
    "dng.new_id": {"en": "new ID", "th": "ID ใหม่"},
    "dng.setid_btn": {"en": "Set ID…", "th": "ตั้ง ID…"},
    "dng.setid_title": {"en": "Change slave ID?", "th": "เปลี่ยน Slave ID?"},
    "dng.setid_body": {"en": "Device {cur} → new ID {new}. Writes reg 4, persists to "
                             "EEPROM (coil 503) and reboots ~3 s, then verifies at the new ID.",
                       "th": "อุปกรณ์ {cur} → ID ใหม่ {new} จะเขียน reg 4, บันทึกลง EEPROM "
                             "(coil 503), รีบูต ~3 วิ แล้วตรวจสอบที่ ID ใหม่"},
    "dng.setid_same": {"en": "new ID equals the current ID", "th": "ID ใหม่ตรงกับ ID เดิม"},
    "dng.setid_change": {"en": "CHANGE ID", "th": "เปลี่ยน ID"},
    "dng.factory_restored": {"en": "slave ID reset to factory default {id} (baud back to "
                                   "9600 — reconnect if you were on another baud)",
                             "th": "Slave ID ถูกคืนเป็นค่าโรงงาน {id} (baud กลับเป็น 9600 "
                                   "— ถ้าเดิมใช้ baud อื่นต้องเชื่อมต่อใหม่)"},
    "dng.success": {"en": "SUCCESS", "th": "สำเร็จ"},
    "dng.failed": {"en": "FAILED", "th": "ไม่สำเร็จ"},

    # ── log pane ───────────────────────────────────────────────────────────
    "log.title": {"en": "Transaction log", "th": "บันทึกการสื่อสาร"},
    "log.pause": {"en": "pause", "th": "หยุดชั่วคราว"},
    "log.filter": {"en": "filter", "th": "กรอง"},
    "log.all": {"en": "all", "th": "ทั้งหมด"},

    # ── about dialog ───────────────────────────────────────────────────────
    "about.desc": {"en": "Test tool for LGS R5.0 modules over Modbus RTU (COM port) "
                         "or Modbus TCP (LGS gateway).",
                   "th": "เครื่องมือทดสอบโมดูล LGS R5.0 ผ่าน Modbus RTU (พอร์ต COM) "
                         "หรือ Modbus TCP (LGS gateway)"},
    "about.data": {"en": "Data and CSV exports: {path}", "th": "ที่เก็บข้อมูลและไฟล์ CSV: {path}"},
    "about.notes": {"en": "Release notes", "th": "บันทึกการเปลี่ยนแปลงแต่ละรุ่น"},

    # ── themes ─────────────────────────────────────────────────────────────
    "theme.light": {"en": "Light", "th": "สว่าง"},
    "theme.dark": {"en": "Dark", "th": "มืด"},
    "theme.midnight": {"en": "Midnight", "th": "น้ำเงินเข้ม"},
    "theme.workshop": {"en": "Workshop (high contrast)", "th": "หน้างาน (คอนทราสต์สูง)"},
    "theme.solar": {"en": "Solar (warm)", "th": "โทนอุ่น"},
    "theme.lab": {"en": "Lab (green)", "th": "โทนเขียว"},
}
