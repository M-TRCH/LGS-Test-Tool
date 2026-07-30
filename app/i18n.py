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
    "hdr.status.connected": {"en": "{desc} — id {id}", "th": "{desc} — id {id}"},
    "hdr.lang_tooltip": {"en": "language", "th": "ภาษา"},
    "hdr.about_tooltip": {"en": "about — v{ver} and release notes",
                          "th": "เกี่ยวกับ — v{ver} และบันทึกรุ่น"},
    "hdr.theme_tooltip": {"en": "theme", "th": "ธีม"},

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
    "mt.warn_unlock": {"en": "⚠ this run will unlock the door {n} time(s)",
                       "th": "⚠ รอบนี้จะปลดล็อก {n} ครั้ง"},
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
    "ins.cabinet": {"en": "Cabinet:", "th": "รุ่นตู้:"},
    "ins.cabinet_detail": {"en": "{rows} rows x {cols} columns — {n} modules ({first}-{last})",
                           "th": "{rows} แถว x {cols} ช่อง — {n} โมดูล ({first}-{last})"},
    "ins.hint": {"en": "Pick a cabinet type, or click cells to include them one by one "
                       "(the row button toggles a whole row). Cells turn green when the "
                       "module passes, red when it does not answer.",
                 "th": "เลือกรุ่นตู้ หรือคลิกทีละช่อง (ปุ่มหน้าแถวเลือกทั้งแถว) "
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
    "ins.do_light": {"en": "Turn the light on, then off (1001)",
                     "th": "เปิดไฟแล้วปิด (1001)"},
    "ins.do_display": {"en": "Show its number on the display (reg 60 + 1010)",
                       "th": "โชว์เลขประจำตัวบนจอ (reg 60 + 1010)"},
    "ins.do_display_tip": {"en": "Shows the slave ID; IDs above 99 show the column "
                                 "number because the display holds two digits",
                           "th": "แสดง Slave ID; ถ้าเกิน 99 จะแสดงเลขช่องแทน "
                                 "เพราะจอรองรับสองหลัก"},
    "ins.do_identify": {"en": "Identify — blink white ~5 s (509)",
                        "th": "ระบุตัวตน — กะพริบสีขาว ~5 วิ (509)"},
    "ins.hold": {"en": "Hold each step (s)", "th": "ค้างแต่ละขั้น (วินาที)"},
    "ins.unlock_card": {"en": "Unlock — moves the physical latch",
                        "th": "ปลดล็อก — กลอนจะทำงานจริง"},
    "ins.do_unlock": {"en": "Light + unlock each module (1021)",
                      "th": "เปิดไฟ + ปลดล็อกทุกโมดูล (1021)"},
    "ins.warn_unlock": {"en": "⚠ this run will unlock {n} module(s)",
                        "th": "⚠ รอบนี้จะปลดล็อก {n} โมดูล"},
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

    # ── danger tab ─────────────────────────────────────────────────────────
    "dng.banner": {"en": "⚠ These commands reboot or wipe the module — double-check "
                         "the target ID",
                   "th": "⚠ คำสั่งเหล่านี้จะรีบูตหรือล้างค่าโมดูล — ตรวจ ID เป้าหมายให้แน่ใจ"},
    "dng.factory": {"en": "Factory reset", "th": "รีเซ็ตค่าโรงงาน"},
    "dng.keep_id": {"en": "Keep slave ID (500→501)", "th": "คง Slave ID เดิม (500→501)"},
    "dng.wipe_all": {"en": "Wipe everything (500→502)", "th": "ล้างทั้งหมด (500→502)"},
    "dng.arm": {"en": "Arm factory reset…", "th": "เตรียมรีเซ็ตค่าโรงงาน…"},
    "dng.arm_title": {"en": "Arm factory reset", "th": "เตรียมรีเซ็ตค่าโรงงาน"},
    "dng.arm_seq": {"en": "Sequence: coil 500 (arm) → coil {apply} (apply) → device "
                          "reboots ~3 s.",
                    "th": "ลำดับ: coil 500 (เตรียม) → coil {apply} (สั่งทำ) → "
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
