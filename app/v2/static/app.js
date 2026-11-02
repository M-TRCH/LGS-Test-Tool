/* LGS Test Tool v2 front end, stage 1: Cabinets, Sites, Events. Plain JS, no libraries. */
"use strict";

const TXT = {
  th: {
    stage: "v2 ขั้นแรก", classic: "แบบเดิม", cabinets: "ตู้", sites: "รายการตู้", events: "เหตุการณ์",
    checkAll: "ตรวจทุกตู้", checking: "กำลังตรวจ...", checkedAt: "ตรวจล่าสุด {at}", notChecked: "ยังไม่ได้ตรวจ",
    noSites: "ยังไม่มีตู้ในรายการ เพิ่มได้ที่หน้า รายการตู้", ok: "ปกติ", warn: "ควรดู", bad: "ผิดปกติ",
    fw: "เฟิร์มแวร์", uptime: "เปิดมาแล้ว", clients: "client", clock: "นาฬิกา", rtu: "ซ่อม RS485 (สะสม)",
    clockUnset: "ยังไม่ตั้ง", repaired: "ซ่อมได้ {n}", failed: "ซ่อมไม่ได้ {n}", badcrc: "CRC เสีย {n}",
    add: "เพิ่มตู้", save: "บันทึก", saved: "บันทึกแล้ว", del: "ลบ", name: "ชื่อตู้", host: "ไอพี / โฮสต์", port: "พอร์ต",
    cabinet: "ชนิดตู้", site: "ไซต์", note: "หมายเหตุ", exportCsv: "ส่งออก CSV", importCsv: "นำเข้า CSV",
    importMerge: "เพิ่มเฉพาะที่ยังไม่มี", importReplace: "แทนที่ทั้งรายการ", imported: "นำเข้า {n} แถว",
    dupWarn: "ไอพีซ้ำกับแถวอื่น", unsaved: "มีการแก้ที่ยังไม่บันทึก", gateway: "เกตเวย์", days: "ย้อนหลัง", day1: "วันนี้", day7: "7 วัน", day30: "30 วัน", day90: "90 วัน", all: "ทั้งหมด",
    search: "ค้นหา (ชื่อ, ไอพี)", noEvents: "ไม่มีเหตุการณ์ในช่วงนี้", noEventsOff: "ยังไม่มีข้อมูล เพราะยังไม่ได้เปิด \"เก็บเหตุการณ์อัตโนมัติ\" ด้านบน (เปิดแล้วรอประมาณ 5 นาทีให้ดึงรอบแรก) ตู้ที่ใช้เฟิร์มแวร์ต่ำกว่า 1.14.0 จะไม่มีข้อมูล", collect: "เก็บเหตุการณ์อัตโนมัติ",
    collectHint: "ดึงบันทึกจากเกตเวย์ทุกตู้ในรายการตู้ทุก 5 นาที เก็บ 90 วัน ต้องใช้เฟิร์มแวร์เกตเวย์ 1.14.0 ขึ้นไป",
    gateway_page: "เกตเวย์", pick: "เลือกตู้", read: "อ่านค่า", reading: "กำลังอ่าน...",
    setClock: "ซิงค์เวลาจากเครื่องนี้", hubRow: "แถว {n}", hubDirect: "ต่อตรง", hubCh: "ช่อง {n}",
    resyncInfo: "เมื่อโมดูลไม่ตอบ เกตเวย์ส่งสัญญาณปรับจังหวะให้โมดูลทั้งบัสแล้วลองถามซ้ำอีกครั้ง เป็นการตั้งค่าชั่วคราวจะกลับมาเปิดเองหลังรีบูต",
    excInfo: "เมื่อบัส RS485 ไม่ตอบ ให้ตอบไคลเอนต์ด้วย exception 0x0B ทันที แทนที่จะปล่อยให้หมดเวลา เป็นการตั้งค่าชั่วคราวจะกลับมาปิดเองหลังรีบูต", clockWarn: "การตั้งนาฬิกาเป็นการเปิดใช้การรีเซ็ตตามเวลา (เช่น 03:00) ซึ่งตัดไฟชั้นวาง ตั้งเมื่อตั้งใจเท่านั้น",
    clockSet: "ตั้งนาฬิกาแล้ว", resync: "ซ่อมจังหวะหลังไม่มีคำตอบ (RESYNC)", exc: "ตอบ exception 0x0B ทันทีเมื่อบัสไม่ตอบ (EXC)",
    volatileNote: "ชั่วคราว: กลับค่าเดิมเมื่อเกตเวย์รีบูต", reboot: "รีบูตเกตเวย์", rebootQ: "รีบูตเกตเวย์ {n}? จะตัดการสื่อสารสักครู่",
    defaults: "คืนค่าโรงงาน", defaultsQ: "คืนค่าโรงงานของ {n}? Ethernet จะปิดและ hub map หาย ต้องตั้งใหม่ พิมพ์ชื่อตู้เพื่อยืนยัน",
    discard: "ทิ้งค่าที่ค้างอยู่", danger: "จัดการเกตเวย์", changes: "{n} ค่าที่แก้", apply: "บันทึกลงเกตเวย์", applyQ: "บันทึก {n} ค่าลง {g}?",
    applied: "บันทึกแล้ว", needReboot: "ต้องรีบูตจึงมีผล: {k}", reset: "ล้างที่แก้", ro: "อ่านอย่างเดียว", rebootKey: "ต้องรีบูต",
    doneOk: "สำเร็จ", noPassword: "ยังไม่ตั้งรหัสผ่านหน้าเว็บ ทุกคนในเครือข่ายแก้ค่าเกตเวย์ได้",
    module_page: "โมดูล", devId: "รหัสโมดูล (ID)", withStats: "รวมสถิติ", auto: "อ่านอัตโนมัติทุก 2 วินาที", modNotRead: "เลือกตู้ ใส่ ID โมดูล แล้วกดอ่านค่า",
    cDevice: "อุปกรณ์", cRuntime: "การทำงาน", cHealth: "สุขภาพระบบ", cReset: "สาเหตุรีเซ็ตล่าสุด", cTemp: "อุณหภูมิ", cLatch: "กลอน / จอ", cStats: "สถิติ",
    mType: "ชนิด", mFw: "เฟิร์มแวร์", mHw: "ฮาร์ดแวร์", mBaud: "Baud", mUid: "หมายเลขชิป", mUptime: "เปิดมาแล้ว", mBoots: "จำนวนครั้งที่บูต", mMode: "โหมด",
    mPreset: "พรีเซ็ตที่ใช้อยู่", mButton: "กดยืนยันแล้ว", mRoom: "ในห้อง", mBoard: "บนบอร์ด", mCurrent: "กระแสขาเข้า", mLatch: "กลอน", mLocked: "ล็อก", mUnlocked: "ปลดแล้ว",
    mUnlockedAgo: "ปลดล่าสุด {s} วินาทีก่อน", mDisplay: "ตัวเลขบนจอ", na: "ไม่มี", presets: "พรีเซ็ตสี", pLight: "ไฟ", pLightDisp: "ไฟ + เลข", pUnlock: "ปลดกลอน", pUnlockDisp: "ปลดกลอน + เลข",
    quick: "คำสั่งด่วน", identify: "ระบุตำแหน่ง (กะพริบ)", allOff: "ดับทั้งหมด", latchSafety: "ปลดกลอน (ปลอดภัย)", latchForce: "ปลดกลอน (บังคับ)", dispPower: "เปิดจอ",
    number: "ตัวเลข (0-9999)", writeNumber: "เขียนตัวเลข", cooldownNote: "กลอนต้องเว้น 2.2 วินาทีระหว่างการปลด", sent: "ส่งแล้ว", fires: "ยิงกลอน {c} ครั้ง · {s} วินาที", count: "ครั้ง", seconds: "วินาที",
    soak_page: "ทดสอบต่อเนื่อง", sPick: "เลือกตู้ที่จะทดสอบ", sAll: "ทั้งหมด", sMode: "โหมด", sPoll: "อ่านอย่างเดียว", sPharm: "จำลองการจ่ายยา",
    sPicks: "จำนวนครั้งที่จ่ายต่อวัน", sHours: "ชั่วโมง (0 = จนกว่าจะหยุด)", sStartAt: "เริ่มเวลา (เช่น 21:00 เว้นว่าง = ทันที)", sStart: "เริ่มทดสอบ",
    sStop: "หยุด", sStopQ: "หยุดการทดสอบที่กำลังรัน? ข้อมูลถึงตอนนี้ถูกเก็บไว้", sRunning: "กำลังรัน", sArmed: "ตั้งเวลาไว้ เริ่มในอีก {t}", sLeft: "เหลือ {t}",
    sNoEnd: "ไม่มีเวลาจบ", sCab: "ตู้", sState: "สถานะ", sPass: "รอบ", sReads: "อ่าน", sFails: "พลาด", sRbt: "รีบูต", sWdt: "วอตช์ด็อก", sWorst: "ช้าสุด (ms)", sHeal: "เกตเวย์ซ่อมบัส",
    sClean: "สะอาด", sWarn: "ควรดู", sNotClean: "ไม่สะอาด", sDidNot: "ไม่ได้รัน", sStarting: "กำลังเริ่ม", sAnoms: "เหตุผิดปกติล่าสุด", sNone: "ไม่มี",
    sVerdict: "สรุปผลรอบล่าสุด", sHistory: "รอบที่ผ่านมา", sView: "ดูสรุป", sNoRuns: "ยังไม่มีรอบที่ผ่านมา", sFrames: "เฟรมที่ถูกทิ้ง: {n}",
    sNeedType: "ตู้ที่ไม่ได้กำหนดชนิดจะเริ่มไม่ได้ ตั้งที่หน้า รายการตู้", sStarted: "เริ่มแล้ว {n} ตู้", sCsv: "ไฟล์ CSV", sLongNote: "รันบนเซิร์ฟเวอร์ ปิดหน้านี้ได้ ผลเก็บใน data/exports",
    labels_page: "ป้าย", firmware_page: "เฟิร์มแวร์", lbWard: "ชื่อวอร์ด (พิมพ์บนป้าย)", lbSerial: "ซีเรียลจากคลัง (ไม่เก็บ)", lbLayout: "แบบป้าย", lbPlate: "กรอบ",
    lbPreview: "ดูตัวอย่างข้อมูล", lbDownload: "ดาวน์โหลด .lbx", expCfg: "ส่งออก config (JSON)", impCfg: "นำเข้า config (JSON)", impDone: "นำเข้า {n} ค่า (ยังไม่บันทึก ตรวจแล้วกดบันทึกลงเกตเวย์)", impNone: "ไม่มีค่าที่ต่างจากเกตเวย์",
    shapeBad: "ชนิดตู้ใน รายการตู้ ({l}) ไม่ตรงกับเกตเวย์: {w}", shapeFix: "ตั้งค่าที่ตรงให้ (ยังไม่บันทึก)", shapeNoFix: "เกตเวย์รุ่นนี้แก้เองไม่ได้ (ไม่มี panel.shape)",
    fwOta: "อัปเดตโมดูลผ่าน OTA (หลายตู้)", fwImage: "อิมเมจ", fwStart: "เริ่มอัปเดต", fwCancel: "ยกเลิก", fwCancelQ: "ยกเลิกการอัปเดต? โมดูลที่ค้างอยู่ในเซสชันอาจต้องอัปเดตซ้ำ",
    fwStartQ: "อัปเดตเฟิร์มแวร์โมดูลทุกตัวใน {n} ตู้ด้วย {i}? ทำย้อนจากหน้านี้ไม่ได้ ตู้ที่ใช้งานอยู่จะใช้ไม่ได้ระหว่างอัปเดต", fwRun: "กำลังอัปเดต", fwNoOta: "ยังไม่มีอิมเมจ OTA ในโปรแกรมนี้",
    fwGw: "อัปเดตเกตเวย์ผ่านเครือข่าย (ทีละตู้)", fwGwNote: "เกตเวย์รีบูตตอนจบ และตัดไฟชั้นวางชั่วครู่ (โมดูลทุกตัวรีบูตด้วย) พิมพ์ชื่อตู้เพื่อยืนยัน", fwUpload: "หรือเลือกไฟล์ .bin เอง", fwConfirm: "พิมพ์ชื่อตู้เพื่อยืนยัน",
    fwGwStart: "อัปเดตเกตเวย์", fwGwRun: "กำลังอัปเดตเกตเวย์", fwDone: "เสร็จ", fwFail: "ไม่สำเร็จ", fwLog: "บันทึกการทำงาน", fwNone: "—", fwCensus: "ผลตรวจ", fwLeft: "ยังไม่ใช่รุ่นใหม่", fwPhase: "ขั้น",
    explain: "อธิบาย",
    basic: "พื้นฐาน", advanced: "ขั้นสูง", modeLocked: "หน้านี้อยู่ในโหมดขั้นสูง", mode: "โหมด", settings: "ตั้งค่า", language: "ภาษา", noKeys: "ไม่มีค่าในกลุ่มนี้",
    commission_page: "ลงโมดูลใหม่", cmProbe: "ตรวจ ST-Link", cmProbing: "กำลังตรวจ...", cmNoCli: "ยังไม่พบ STM32CubeProgrammer บนเครื่องที่รันโปรแกรมนี้", cmNoProbe: "ไม่พบ ST-Link ตรวจสาย USB และปิดโปรแกรมอื่นที่จับ ST-Link อยู่ (เช่น CubeProgrammer, CubeIDE)",
    cmProbeOk: "พบ ST-Link {n} ตัว", cmCli: "CubeProgrammer", cmSingle: "ทีละตัว", cmBatch: "ต่อเนื่อง",
    cmImage: "ไฟล์เฟิร์มแวร์", cmChoose: "เลือกไฟล์", cmWhat: "รายละเอียดไฟล์นี้", cmNoteLbl: "หมายเหตุ", cmShaLbl: "SHA-256 (12 ตัวแรก)", cmVerLbl: "เวอร์ชัน", cmNoFile: "ยังไม่ได้เลือกไฟล์", cmUpload: "หรืออัปโหลดไฟล์ .bin", cmType: "ชนิดตู้", cmTypeAuto: "ให้บอร์ดตัดสินเอง", cmLot: "ล็อต (ไม่บังคับ)",
    cmId: "ไอดีของโมดูล", cmIdBad: "ID ต้องเป็นตัวเลข 1-245 เท่านั้น", cmIdNeed: "ใส่ไอดีของโมดูลก่อน", cmIds: "ID ที่จะแจก เรียงตามลำดับ เช่น 11-18, 21", cmOverwrite: "เขียนทับ ID ที่โมดูลเก็บไว้แล้ว", cmOverwriteConfirm: "พิมพ์ ID ใหม่เพื่อยืนยันการเขียนทับ",
    cmStart: "เขียนโมดูล", cmCancel: "ยกเลิก", cmRunning: "กำลังเขียน", cmNeedImage: "เลือกไฟล์ factory ก่อน", cmLog: "ความคืบหน้า", cmResultOk: "สำเร็จ", cmResultFail: "ไม่สำเร็จ", cmNone: "ยังไม่มีการเขียน",
    askOk: "ตกลง", askNo: "ยกเลิก",
    cmGrid: "ไอดีของโมดูล", cmClear: "ล้างที่เลือก", cmPreset: "กำหนดเอง", cmSelected: "เลือกแล้ว {n} ช่อง", cmPickFirst: "เลือก ID อย่างน้อย 1 ช่องก่อน",
    lbIName: "ตู้", lbIIp: "ไอพี", lbIMac: "MAC", lbIRows: "จำนวนแถว", lbIRowsV: "{n} แถว", lbILen: "ความยาวป้าย", lbILenV: "{mm} มม.", lbIFile: "ขนาดไฟล์", lbIBytesV: "{n} ไบต์", lbIQrData: "ข้อมูลใน QR", lbIQrDataV: "{n} ไบต์ เหลืออีก {spare} ไบต์", lbIQrKind: "ชนิด QR", lbIQrKindV: "เวอร์ชัน {v} ระดับ {ecc} กู้ได้ {rec}", lbIPayload: "ข้อมูลใน QR Code", lbIHead: "ข้อมูลป้าย",
    g_sys: "ทั่วไป", g_rs485: "บัส RS485", g_usb: "พอร์ต USB", g_net: "เครือข่าย", g_time: "เวลา", g_bus: "ฮับ RS485", g_panel: "ปุ่มและไฟหน้าตู้", g_sched: "รีเซตตามเวลา",
    theme: "ธีม", th_auto: "ตามเครื่อง", th_light: "สว่าง", th_dark: "มืด", th_ocean: "ทะเล", th_forest: "ป่า", th_sand: "ทราย", th_midnight: "เที่ยงคืน", th_contrast: "คอนทราสต์สูง",
    lbPicture: "ตัวอย่างป้าย", lbPicNote: "ภาพจากไฟล์ .lbx จริง QR เป็นตัวจริง ฟอนต์ตรงกับไฟล์เมื่อเครื่องที่เปิดมีฟอนต์ Arial และ Browallia New",
    sCsvFiles: "ไฟล์ข้อมูล", sColLegend: "คอลัมน์: mod = โมดูล · pass = รอบ · reads = อ่าน · fail = พลาด · rbt = รีบูต · wdt = วอตช์ด็อก · cross = ข้ามช่องฮับ · worst = ช้าสุด (ms) · drop = ตกหล่น · silent = เงียบ",
    close: "ปิด", noExplain: "ยังไม่มีคำอธิบายสำหรับค่านี้", curValue: "ค่าปัจจุบัน", newValue: "ค่าที่กำลังแก้",
    matched: "พบ {n} รายการ", loginAgain: "ต้องเข้าสู่ระบบอีกครั้ง", error: "ผิดพลาด: {e}", d: "วัน", h: "ชม.",
  },
  en: {
    stage: "v2 stage 1", classic: "Classic UI", cabinets: "Cabinets", sites: "Sites", events: "Events",
    checkAll: "Check all", checking: "Checking...", checkedAt: "Last checked {at}", notChecked: "Not checked yet",
    noSites: "No cabinets saved yet. Add them on the Sites page.", ok: "OK", warn: "Look", bad: "Fault",
    fw: "Firmware", uptime: "Up for", clients: "Clients", clock: "Clock", rtu: "RS485 repairs (total)",
    clockUnset: "not set", repaired: "{n} repaired", failed: "{n} failed", badcrc: "{n} bad CRC",
    add: "Add cabinet", save: "Save", saved: "Saved", del: "Delete", name: "Name", host: "IP / host", port: "Port",
    cabinet: "Cabinet type", site: "Site", note: "Note", exportCsv: "Export CSV", importCsv: "Import CSV",
    importMerge: "Add only new rows", importReplace: "Replace the list", imported: "Imported {n} rows",
    dupWarn: "same address as another row", unsaved: "Unsaved changes", gateway: "Gateway", days: "Range", day1: "Today", day7: "7 days", day30: "30 days", day90: "90 days", all: "All",
    search: "Search (name, IP)", noEvents: "No events in this range", noEventsOff: "No data yet because \"Collect events automatically\" above is off (turn it on and wait about 5 minutes for the first pull). Cabinets below firmware 1.14.0 have no events.", collect: "Collect events automatically",
    collectHint: "Pulls every saved cabinet's gateway log every 5 minutes, kept 90 days. Needs gateway firmware 1.14.0 or newer.",
    gateway_page: "Gateway", pick: "Choose cabinet", read: "Read", reading: "Reading...",
    setClock: "Sync time from this PC", hubRow: "Row {n}", hubDirect: "Direct", hubCh: "Channel {n}",
    resyncInfo: "After a missing reply the gateway re-syncs every module on the bus and retries once. Temporary: returns to on when the gateway reboots.",
    excInfo: "When the RS485 bus does not answer, reply to the client with exception 0x0B at once instead of letting it time out. Temporary: returns to off when the gateway reboots.", clockWarn: "Setting the clock also arms the scheduled reset (e.g. 03:00), which cuts the shelf's power. Do it on purpose only.",
    clockSet: "Clock set", resync: "Re-sync after a missing reply (RESYNC)", exc: "Answer a bus timeout with exception 0x0B at once (EXC)",
    volatileNote: "Temporary: reverts when the gateway reboots", reboot: "Reboot gateway", rebootQ: "Reboot gateway {n}? It will be unreachable for a moment.",
    defaults: "Factory defaults", defaultsQ: "Reset {n} to factory defaults? Ethernet goes off and the hub map is lost; both must be set again. Type the cabinet's name to confirm.",
    discard: "Discard staged edits", danger: "Gateway actions", changes: "{n} changed", apply: "Save to gateway", applyQ: "Save {n} value(s) to {g}?",
    applied: "Saved", needReboot: "Needs a reboot to take effect: {k}", reset: "Clear edits", ro: "read-only", rebootKey: "needs reboot",
    doneOk: "Done", noPassword: "No web password set: anyone on the network can edit the gateway.",
    module_page: "Module", devId: "Module ID", withStats: "Include statistics", auto: "Read automatically every 2 s", modNotRead: "Choose a cabinet, enter a module ID, press Read",
    cDevice: "Device", cRuntime: "Runtime", cHealth: "Health", cReset: "Last reset cause", cTemp: "Temperatures", cLatch: "Latch / display", cStats: "Statistics",
    mType: "Type", mFw: "Firmware", mHw: "Hardware", mBaud: "Baud", mUid: "Chip serial", mUptime: "Uptime", mBoots: "Boots", mMode: "Mode",
    mPreset: "Active preset", mButton: "Confirm presses", mRoom: "Room", mBoard: "Board", mCurrent: "Input current", mLatch: "Latch", mLocked: "locked", mUnlocked: "unlocked",
    mUnlockedAgo: "last unlock {s} s ago", mDisplay: "Display number", na: "n/a", presets: "Colour presets", pLight: "Light", pLightDisp: "Light + number", pUnlock: "Unlock", pUnlockDisp: "Unlock + number",
    quick: "Quick commands", identify: "Identify (blink)", allOff: "All off", latchSafety: "Unlock (safe)", latchForce: "Unlock (force)", dispPower: "Display on",
    number: "Number (0-9999)", writeNumber: "Write number", cooldownNote: "A latch needs 2.2 s between unlocks", sent: "Sent", fires: "{c} fires · {s} s", count: "count", seconds: "seconds",
    soak_page: "Soak", sPick: "Choose the cabinets to test", sAll: "All", sMode: "Mode", sPoll: "Read only", sPharm: "Pharmacy simulation",
    sPicks: "Picks per day", sHours: "Hours (0 = until stopped)", sStartAt: "Start at (e.g. 21:00, empty = now)", sStart: "Start soak",
    sStop: "Stop", sStopQ: "Stop the running soak? Data up to now is kept.", sRunning: "Running", sArmed: "Armed, starts in {t}", sLeft: "{t} left",
    sNoEnd: "no end time", sCab: "Cabinet", sState: "State", sPass: "Passes", sReads: "Reads", sFails: "Fails", sRbt: "Reboots", sWdt: "WDT", sWorst: "Worst ms", sHeal: "Gateway repairs",
    sClean: "clean", sWarn: "look", sNotClean: "not clean", sDidNot: "did not run", sStarting: "starting", sAnoms: "Latest anomalies", sNone: "none",
    sVerdict: "Latest run verdict", sHistory: "Past runs", sView: "View verdict", sNoRuns: "No past runs yet", sFrames: "Frames pymodbus discarded: {n}",
    sNeedType: "A cabinet with no type cannot start. Set it on the Sites page.", sStarted: "Started {n} cabinets", sCsv: "CSV files", sLongNote: "Runs on the server: you can close this page. Results go to data/exports.",
    labels_page: "Labels", firmware_page: "Firmware", lbWard: "Ward name (printed)", lbSerial: "Serial from the warehouse (not stored)", lbLayout: "Label layout", lbPlate: "Frame",
    lbPreview: "Preview data", lbDownload: "Download .lbx", expCfg: "Export config (JSON)", impCfg: "Import config (JSON)", impDone: "Imported {n} values (not saved yet: review, then Save to gateway)", impNone: "Nothing differs from the gateway",
    shapeBad: "The cabinet type on the Sites page ({l}) does not match the gateway: {w}", shapeFix: "Stage the matching values (not saved yet)", shapeNoFix: "This firmware cannot be told (no panel.shape)",
    fwOta: "Module update over OTA (several cabinets)", fwImage: "Image", fwStart: "Start update", fwCancel: "Cancel", fwCancelQ: "Cancel the update? Modules left in a session may need updating again.",
    fwStartQ: "Update the firmware of every module in {n} cabinets with {i}? This cannot be undone from this page, and cabinets in use are unusable during the update.", fwRun: "Updating", fwNoOta: "No OTA image is bundled in this build",
    fwGw: "Gateway update over the network (one at a time)", fwGwNote: "The gateway reboots at the end and cuts the shelf's power for a moment (every module reboots too). Type the cabinet's name to confirm.", fwUpload: "or choose a .bin file", fwConfirm: "Type the cabinet's name to confirm",
    fwGwStart: "Update gateway", fwGwRun: "Updating gateway", fwDone: "Done", fwFail: "Failed", fwLog: "Log", fwNone: "—", fwCensus: "Result", fwLeft: "not on the new image", fwPhase: "Phase",
    explain: "info",
    basic: "Basic", advanced: "Advanced", modeLocked: "That page is in Advanced mode", mode: "Mode", settings: "Settings", language: "Language", noKeys: "No values in this group",
    commission_page: "Commission", cmProbe: "Check ST-Link", cmProbing: "Checking...", cmNoCli: "STM32CubeProgrammer was not found on the machine running this tool", cmNoProbe: "No ST-Link found. Check the USB cable and close other programs that hold the ST-Link (CubeProgrammer, CubeIDE).",
    cmProbeOk: "{n} ST-Link found", cmCli: "CubeProgrammer", cmSingle: "One module", cmBatch: "Continuous",
    cmImage: "Firmware file", cmChoose: "Choose file", cmWhat: "About this file", cmNoteLbl: "Note", cmShaLbl: "SHA-256 (first 12)", cmVerLbl: "Version", cmNoFile: "No file chosen", cmUpload: "Or upload a .bin", cmType: "Cabinet type", cmTypeAuto: "Let the board decide", cmLot: "Lot (optional)",
    cmId: "Module ID", cmIdBad: "The ID must be a number from 1 to 245", cmIdNeed: "Enter the module ID first", cmIds: "IDs to assign, in order, e.g. 11-18, 21", cmOverwrite: "Overwrite an ID the module already stores", cmOverwriteConfirm: "Type the new ID to confirm the overwrite",
    cmStart: "Flash module", cmCancel: "Cancel", cmRunning: "Flashing", cmNeedImage: "Choose a factory image first", cmLog: "Progress", cmResultOk: "Done", cmResultFail: "Failed", cmNone: "Nothing flashed yet",
    askOk: "Confirm", askNo: "Cancel",
    cmGrid: "Module ID", cmClear: "Clear", cmPreset: "Custom", cmSelected: "{n} selected", cmPickFirst: "Pick at least one ID first",
    lbIName: "Cabinet", lbIIp: "IP address", lbIMac: "MAC", lbIRows: "Rows", lbIRowsV: "{n} rows", lbILen: "Label length", lbILenV: "{mm} mm", lbIFile: "File size", lbIBytesV: "{n} bytes", lbIQrData: "QR data", lbIQrDataV: "{n} bytes, {spare} bytes spare", lbIQrKind: "QR type", lbIQrKindV: "Version {v}, level {ecc}, recovers {rec}", lbIPayload: "QR Code data", lbIHead: "Label details",
    g_sys: "General", g_rs485: "RS485 bus", g_usb: "USB port", g_net: "Network", g_time: "Time", g_bus: "RS485 hub", g_panel: "Panel buttons and lamps", g_sched: "Scheduled reset",
    theme: "Theme", th_auto: "Follow device", th_light: "Light", th_dark: "Dark", th_ocean: "Ocean", th_forest: "Forest", th_sand: "Sand", th_midnight: "Midnight", th_contrast: "High contrast",
    lbPicture: "Label preview", lbPicNote: "Drawn from the real .lbx with the real QR. Fonts match the file when this device has Arial and Browallia New.",
    sCsvFiles: "Data files", sColLegend: "",
    close: "Close", noExplain: "No explanation for this setting yet", curValue: "Current value", newValue: "Value being edited",
    matched: "{n} found", loginAgain: "Sign in again", error: "Error: {e}", d: "d", h: "h",
  },
};
let lang = (localStorage.getItem("lgs.lang") || "th");
const t = (k, p) => { let s = (TXT[lang] && TXT[lang][k]) || TXT.en[k] || k; for (const a in (p || {})) s = s.replace("{" + a + "}", p[a]); return s; };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: "", days: 1, q: "", types: new Set() }, gw: { id: "", data: null, edits: {}, busy: false }, lab: { id: "", ward: "", serial: "", layout: "", plate: "", opts: null, info: null, busy: false }, fw: { images: null, sel: new Set(), image: "", ota: null, gwId: "", gwImage: "", gwConfirm: "", gwFile: null, gwFileName: "", gw: null, timer: null }, soak: { sel: new Set(), mode: "pharmacy", picks: 2000, hours: 12, startAt: "", status: null, runs: [], verdict: "", timer: null, was: false }, mod: { id: "", dev: 11, data: null, busy: false, auto: false, stats: false, presets: [], lockUntil: 0 } };
let page = (location.hash || "#/cabinets").slice(2) || "cabinets";

/* In-page confirmation: window.confirm() is silently answered "no" when the browser has been told to stop a page's dialogs, which made a write button look dead. */
/* Which way a CSV is brought in, asked when the button is pressed. Resolves "merge", "replace" or null (cancelled). */
function pickImportMode() {
  return new Promise((resolve) => {
    const d = $("#pick"); $("#picktitle").textContent = t("importCsv");
    $("#pickmerge").textContent = t("importMerge"); $("#pickreplace").textContent = t("importReplace"); $("#pickno").textContent = t("askNo");
    const done = (v) => { d.onclose = null; if (d.open) d.close(); resolve(v); };
    $("#pickmerge").onclick = () => done("merge"); $("#pickreplace").onclick = () => done("replace"); $("#pickno").onclick = () => done(null); d.onclose = () => resolve(null);
    if (d.showModal) d.showModal(); else d.setAttribute("open", "");
  });
}
/* ask(text) -> true/false; ask(text, true) is an alert; ask(text, false, true) also wants something typed and resolves with it, or null if cancelled. */
function ask(text, alertOnly, typed) {
  return new Promise((resolve) => {
    const d = $("#ask"), inp = $("#askin"); inp.hidden = !typed; inp.value = ""; $("#asktext").textContent = text; $("#askok").textContent = t("askOk"); $("#askno").textContent = t("askNo"); $("#askno").hidden = !!alertOnly;
    const none = typed ? null : false;
    const done = (v) => { d.onclose = null; if (d.open) d.close(); resolve(v); };
    $("#askok").onclick = () => done(typed ? inp.value : true); $("#askno").onclick = () => done(none); d.onclose = () => resolve(none);
    if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    if (typed) inp.focus();
  });
}
async function api(method, url, body, raw) {
  const opt = { method, headers: { "X-LGS": "1" }, credentials: "same-origin" };
  if (body !== undefined) { opt.body = raw ? body : JSON.stringify(body); if (!raw) opt.headers["Content-Type"] = "application/json"; }
  const r = await fetch(url, opt);
  if (r.redirected && /\/login/.test(r.url)) { location.href = "/login?next=" + encodeURIComponent(location.pathname); throw new Error(t("loginAgain")); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
function toast(msg) { const el = $("#toast"); el.textContent = msg; el.classList.add("show"); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove("show"), 3200); }
const fail = (e) => toast(t("error", { e: e.message || e }));

function fmtUp(s) { const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600); return d ? `${d} ${t("d")} ${h} ${t("h")}` : `${h} ${t("h")} ${Math.floor((s % 3600) / 60)} m`; }

/* ---------- pages ---------- */
/* The cabinet check's reasons are written by the server in English; the page language decides what is shown. A text it does not know is shown as it came. */
const REASONS_TH = [
  [/^cannot connect$/, () => "เชื่อมต่อไม่ได้"],
  [/^unreachable$/, () => "ติดต่อไม่ได้"],
  [/^console refused.*$/, () => "เกตเวย์ไม่ยอมรับคอนโซล เฟิร์มแวร์เก่ากว่า 1.12 หรือปิด net.console"],
  [/^INFO refused$/, () => "เกตเวย์ไม่ตอบคำสั่ง INFO"],
  [/^both client slots busy$/, () => "ช่อง client เต็มทั้ง 2 ช่อง"],
  [/^connection closed by the gateway.*$/, () => "เกตเวย์ตัดการเชื่อมต่อ ช่อง client อาจเต็มทั้ง 2 ช่อง"],
  [/^(\d+) other client\(s\) connected(?:: (.*))?$/, (m) => `มี client อื่นเชื่อมต่ออยู่ ${m[1]} ราย${m[2] ? ": " + m[2] : ""}`],
  [/^clock not set.*$/, () => "ยังไม่ได้ตั้งเวลา การรีเซ็ตตามกำหนดจะไม่ทำงาน"],
  [/^NTP (.+)$/, (m) => "NTP: " + m[1]],
  [/^event log (.+)$/, (m) => "บันทึกเหตุการณ์: " + m[1]],
  [/^gateway is in safe mode$/, () => "เกตเวย์อยู่ในโหมดปลอดภัย"],
];
function reasonText(r) {
  if (lang !== "th") return r;
  for (const [re, f] of REASONS_TH) { const m = String(r).match(re); if (m) return f(m); }
  return r;
}
function viewCabinets() {
  const cards = S.sites.map((s) => {
    const h = S.health[s.id];
    const state = h ? h.state : "off";
    const chip = h ? t(state) : t("notChecked");
    let body = "";
    if (h && h.reachable && h.console !== false) {
      const r = h.rtu;
      body = `<dl class="kv"><dt>${t("fw")}</dt><dd class="mono">${esc(h.fw)}</dd>
        <dt>${t("uptime")}</dt><dd>${esc(fmtUp(h.up_s))} (${esc(h.reset)})</dd>
        <dt>${t("clients")}</dt><dd>${h.clients}/2${h.other_masters && h.other_masters.length ? " · " + esc(h.other_masters.join(", ")) : ""}</dd>
        <dt>${t("clock")}</dt><dd>${h.time_set ? esc(h.time_now.replace("T", " ")) : t("clockUnset")}</dd>
        ${r ? `<dt>${t("rtu")}</dt><dd>${t("repaired", { n: r.healed })}${r.heal_failed ? " · " + t("failed", { n: r.heal_failed }) : ""}${r.bad_crc ? " · " + t("badcrc", { n: r.bad_crc }) : ""}</dd>` : ""}</dl>`;
    }
    const why = h && h.reasons && h.reasons.length ? `<div class="notice ${state === "bad" ? "bad" : ""}">${h.reasons.map((x) => esc(reasonText(x))).join("<br>")}</div>` : "";
    return `<section class="card cab"><h3><span>${esc(s.name)}</span><span class="chip ${state === "off" ? "off" : state}"><i class="dot"></i>${esc(chip)}</span></h3>
      <div class="small muted mono">${esc(s.host)}:${s.port}${s.cabinet ? " · " + esc(s.cabinet) : ""}${s.site ? " · " + esc(s.site) : ""}</div>${body}${why}</section>`;
  }).join("");
  return `<div class="row between"><h1>${t("cabinets")}</h1><div class="row"><span class="small muted">${S.checkedAt ? t("checkedAt", { at: esc(S.checkedAt) }) : ""}</span>
    <button class="btn primary" data-act="check">${t("checkAll")}</button></div></div>
    ${S.sites.length ? `<div class="cabs">${cards}</div>` : `<div class="notice info">${t("noSites")}</div>`}`;
}

function siteRow(s, i) {
  const dup = S.sites.some((o, j) => j !== i && o.host && o.host === s.host && Number(o.port) === Number(s.port));
  const opts = ["", ...S.layouts].map((l) => `<option value="${esc(l)}"${l === s.cabinet ? " selected" : ""}>${esc(l || "—")}</option>`).join("");
  return `<div class="sitesrow${dup ? " dup" : ""}" data-i="${i}">
    <input data-f="name" value="${esc(s.name)}" placeholder="${t("name")}" aria-label="${t("name")}">
    <input data-f="host" value="${esc(s.host)}" placeholder="192.168.x.x" aria-label="${t("host")}" inputmode="decimal">
    <input data-f="port" value="${esc(s.port)}" aria-label="${t("port")}" inputmode="numeric">
    <select data-f="cabinet" aria-label="${t("cabinet")}">${opts}</select>
    <input data-f="site" value="${esc(s.site)}" placeholder="${t("site")}" aria-label="${t("site")}">
    <input data-f="note" value="${esc(s.note)}" placeholder="${t("note")}" aria-label="${t("note")}">
    <button class="btn" data-act="del" data-i="${i}">${t("del")}</button>${dup ? `<div class="tiny" style="color:var(--warn)">${t("dupWarn")}</div>` : ""}</div>`;
}
function viewSites() {
  return `<div class="row between" style="margin-bottom:14px"><h1>${t("sites")}</h1><div class="row">
      <details class="menu"><summary class="btn">CSV</summary><div class="menupanel">
        <a class="menuitem" href="/api/v2/sites.csv" download>${t("exportCsv")}</a>
        <button class="menuitem" type="button" data-act="csv-import">${t("importCsv")}</button>
        <input type="file" id="csvfile" accept=".csv,text/csv" hidden></div></details>
      <button class="btn" data-act="add">${t("add")}</button><button class="btn primary" data-act="save">${t("save")}</button></div></div>
    ${S.dirty ? `<div class="notice">${t("unsaved")}</div>` : ""}
    ${S.warnings.map((w) => `<div class="notice">${esc(w)}</div>`).join("")}
    <section class="card" id="sitelist">${S.sites.length ? `<div class="sitesrow siteshead tiny muted"><span>${t("name")}</span><span>${t("host")}</span><span>${t("port")}</span><span>${t("cabinet")}</span><span>${t("site")}</span><span>${t("note")}</span><span></span></div>` : ""}${S.sites.map(siteRow).join("") || `<p class="muted">${t("noSites")}</p>`}</section>`;
}

function viewEvents() {
  const c = (S.me && S.me.collector) || {};
  const st = Object.values(c.status || {}).map((r) => `<div class="small ${r.ok ? "" : "muted"}">${esc(r.name)}: ${r.ok ? "+" + r.new : esc(r.error)}</div>`).join("");
  const types = ["coil", "tcp_accept", "tcp_close", "tcp_refused", "bus_quiet", "rtu_heal", "boot", "link_down", "cfg_saved", "sched_reset"];
  return `<h1>${t("events")}</h1>
    <section class="card stack"><div class="switch"><div><b>${t("collect")}</b><div class="small muted">${t("collectHint")}</div></div>
      <button class="sw" role="switch" aria-checked="${!!c.enabled}" data-act="collector"></button></div>${st}</section>
    <section class="card stack" style="margin-top:12px"><div class="row">
      <div class="field"><label>${t("gateway")}</label><select id="evgw"><option value="">${t("all")}</option>${(S.evGw || []).map((g) => `<option value="${esc(g.gw)}"${g.gw === S.ev.gw ? " selected" : ""}>${esc(g.gw)} (${g.last || "-"})</option>`).join("")}</select></div>
      <div class="field"><label>${t("days")}</label><select id="evdays">${[[1, "day1"], [7, "day7"], [30, "day30"], [90, "day90"]].map(([d, k]) => `<option value="${d}"${d === S.ev.days ? " selected" : ""}>${t(k)}</option>`).join("")}</select></div>
      <div class="field"><label>${t("search")}</label><input id="evq" value="${esc(S.ev.q)}"></div></div>
      <div class="seg">${types.map((x) => `<button data-type="${x}" aria-pressed="${S.ev.types.has(x)}">${x}</button>`).join("")}</div>
      <div class="small muted" id="evcount"></div><div id="evlist"></div></section>`;
}


/* The order a gateway is really set up in: name, network (to be reachable at all), clock, the RS485 bus and its hub, USB, then the cabinet's panel and its schedule.
   Fields follow the same order inside a group; the firmware's own table is append-only history, not a sensible reading order. */
const GWGROUPS = ["sys", "net", "time", "rs485", "bus", "usb", "panel", "sched"];
const GWORDER = ["sys.name", "sys.wdt_ms",
  "net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns", "net.port", "net.mac", "net.ntp", "net.ntp_port", "net.link_timeout_ms", "net.console",
  "time.tz_min",
  "rs485.baud", "rs485.predelay_us", "rs485.postdelay_us", "rs485.t1_ms", "rs485.t2_ms",
  "bus.hub_map", "bus.hub_retry", "bus.hub_gap_ms", "bus.hub_settle_ms", "bus.hub_budget_ms",
  "usb.gap_ms", "usb.max_ms",
  "panel.enabled", "panel.cabinet", "panel.shape", "panel.preset", "panel.bright", "panel.btn1", "panel.btn2", "panel.btn3", "panel.btn4", "panel.btn5",
  "panel.out1", "panel.out2", "panel.out3", "panel.out4", "panel.lamps", "panel.lamp_hold_ms", "panel.lamp_dwell_ms", "panel.lamp_dead",
  "panel.step_on_ms", "panel.step_off_ms", "panel.step_unlock_ms", "panel.reset_ms",
  "sched.reset_enabled", "sched.reset_days", "sched.reset_slots", "sched.reset_hhmm", "sched.reset_hhmm2", "sched.reset_hhmm3", "sched.reset_hhmm4"];
const gwRank = (key) => { const i = GWORDER.indexOf(key); return i < 0 ? 999 : i; };
/* Settings that pick one of a few meanings (panel.h, gw_config.cpp): a list, not a number. value -> [th, en]. */
const GWENUM = (() => {
  const btn = { 0: ["ไม่ทำอะไร", "Does nothing"], 1: ["เปิดไฟทุกช่อง", "Light every slot"], 2: ["ปิดไฟทั้งหมด", "Everything off"], 3: ["ปลดล็อกทุกช่อง", "Unlock every slot"],
    4: ["รีเซ็ตไฟชั้นวาง", "Reset the shelf power"], 5: ["ทดสอบไฟสถานะ", "Test the status lamps"], 6: ["เปิดทุกหน้าต่างทุกช่อง (ตู้ 80)", "Every window of every slot (type 80)"] };
  const out = { 0: ["ไม่ใช้", "Not used"], 1: ["พร้อมใช้งาน", "Ready"], 2: ["กำลังทำงาน", "Busy"], 3: ["ผิดปกติ", "Fault"], 4: ["สาย LAN เชื่อมอยู่", "LAN up"],
    5: ["มีไคลเอนต์เชื่อมอยู่", "A client is connected"], 6: ["กำลังไล่ช่อง", "A sweep is running"], 7: ["กำลังตัดไฟชั้นวาง", "Shelf power is dropped"], 8: ["ไฟเลี้ยงชั้นวาง", "Shelf power"] };
  const m = { "panel.cabinet": { 0: ["ตามค่ารูปทรง (panel.shape)", "Follow the shape (panel.shape)"], 40: ["40 ช่อง", "40 slots"], 64: ["64 ช่อง", "64 slots"], 80: ["80 ช่อง", "80 slots"] },
    "rs485.baud": { 9600: ["9600", "9600"], 19200: ["19200", "19200"], 38400: ["38400", "38400"], 57600: ["57600", "57600"] },
    "panel.preset": Object.fromEntries([1, 2, 3, 4, 5, 6, 7, 8].map((n) => [n, ["พรีเซ็ต " + n, "Preset " + n]])) };
  /* KIND_BOOL keys in gw_config.cpp */
  for (const k of ["net.enabled", "net.dhcp", "panel.enabled", "panel.lamps", "sched.reset_enabled", "net.console"]) m[k] = { 0: ["ปิด", "Off"], 1: ["เปิด", "On"] };
  /* Offsets people actually live at, in minutes east of UTC (what time.tz_min stores). */
  const tz = {}, fmt = (min) => { const a = Math.abs(min), h = Math.floor(a / 60), mm = a % 60; return "UTC" + (min < 0 ? "-" : "+") + h + (mm ? ":" + String(mm).padStart(2, "0") : ""); };
  const named = { 420: ["ไทย", "Thailand"], 480: ["สิงคโปร์ / จีน", "Singapore / China"], 540: ["ญี่ปุ่น", "Japan"], 0: ["ลอนดอน (ฤดูหนาว)", "London (winter)"], 330: ["อินเดีย", "India"], 390: ["เมียนมา", "Myanmar"] };
  [-720, -660, -600, -540, -480, -420, -360, -300, -240, -210, -180, -120, -60, 0, 60, 120, 180, 210, 240, 270, 300, 330, 345, 360, 390, 420, 480, 525, 540, 570, 600, 660, 720, 765, 780, 840]
    .forEach((min) => { const n = named[min]; tz[min] = [fmt(min) + (n ? " (" + n[0] + ")" : ""), fmt(min) + (n ? " (" + n[1] + ")" : "")]; });
  m["time.tz_min"] = tz;
  for (let n = 1; n <= 5; n++) m["panel.btn" + n] = btn;
  for (let n = 1; n <= 4; n++) m["panel.out" + n] = out;
  return m;
})();
function gwChanged() { return Object.keys(S.gw.edits).length; }
/* Keys the gateway names but i18n has no label for (the Classic tool draws them with a custom widget). Same wording as the PDF report. */
const GWNAMES = {
  "panel.btn1": ["ปุ่มสีแดงทำอะไร", "Red button does"], "panel.btn2": ["ปุ่มสีเขียวทำอะไร", "Green button does"], "panel.btn3": ["ปุ่มสีน้ำเงินทำอะไร", "Blue button does"],
  "panel.btn4": ["ปุ่มสีเหลืองทำอะไร", "Yellow button does"], "panel.btn5": ["ปุ่มสีขาวทำอะไร", "White button does"],
  "panel.out1": ["รีเลย์เอาต์พุต 1 ทำอะไร?", "Relay output 1 follows"], "panel.out2": ["รีเลย์เอาต์พุต 2 ทำอะไร?", "Relay output 2 follows"],
  "panel.out3": ["รีเลย์เอาต์พุต 3 ทำอะไร?", "Relay output 3 follows"], "panel.out4": ["รีเลย์เอาต์พุต 4 ทำอะไร?", "Relay output 4 follows"],
  "sched.reset_days": ["วันที่รีเซ็ต", "Reset days"], "sched.reset_slots": ["ช่วงเวลาที่เปิดใช้", "Reset times armed"],
  "sched.reset_hhmm2": ["เวลารีเซ็ต 2", "Reset time 2"], "sched.reset_hhmm3": ["เวลารีเซ็ต 3", "Reset time 3"], "sched.reset_hhmm4": ["เวลารีเซ็ต 4", "Reset time 4"],
  "net.console": ["เปิดช่องคอนโซลผ่านเครือข่าย", "Console over the network"],
};
/* Thai wording for this page that differs from the shared i18n table the Classic tool also reads. */
const GWTH = { "sys.name": "ชื่อเกตเวย์", "sys.wdt_ms": "Watchdog (ms)", "net.ip": "ไอพีเกตเวย์", "net.ntp": "ไอพีเซิร์ฟเวอร์เวลา NTP", "time.tz_min": "โซนเวลา (UTC)",
  "rs485.t2_ms": "เวลาเงียบที่ถือว่าจบคำตอบ (ms)", "usb.gap_ms": "เวลาเงียบที่ถือว่าจบคำสั่ง (ms)", "panel.preset": "พรีเซ็ตสีที่ปุ่มใช้", "bus.hub_map": "แผนที่ช่อง", "bus.hub_retry": "จำนวนยิงกระตุ้นเมื่อข้ามช่อง", "bus.hub_gap_ms": "เผื่อเวลาเพิ่ม (ms)" };
/* bus.hub_map is ten numbers, one per row (slave IDs 11-108): which hub channel the row hangs on, 0 = wired straight. */
const hubRows = (str) => { const a = String(str || "").split(",").map((x) => parseInt(x, 10) || 0); while (a.length < 10) a.push(0); return a.slice(0, 10); };
/* The "?" button, only where there is something to say: no button when the name says it all, or when there is no explanation text. */
const GWNOINFO = new Set(["sys.name", "net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns", "net.port", "net.ntp", "net.ntp_port", "time.tz_min", "rs485.baud", "panel.enabled", "sched.reset_enabled"]);
function whyBtn(k) {
  const tx = k.text && k.text[lang];
  if (k.ro || GWNOINFO.has(k.key) || !(tx && tx.hint)) return "";
  return `<button class="why" data-act="hint" data-key="${esc(k.key)}" type="button" aria-label="${t("explain")}">?</button>`;
}
/* Shorter Thai explanations for this page than the shared i18n table has. */
const GWTHHINT = { "bus.hub_retry": "จำนวนครั้งที่ส่งคำสั่งเมื่อต้องเปลี่ยนไปคุยกับช่องฮับอื่น", "bus.hub_settle_ms": "เวลาที่ฮับใช้สลับช่อง รอโดยไม่มีการรับส่งข้อมูล", "bus.hub_budget_ms": "เวลามากสุดต่อหนึ่งคำสั่ง รวมเวลารอฮับสลับช่อง ต้องน้อยกว่าเวลารอคำตอบของฝั่งที่สั่ง (เซิร์ฟเวอร์) ไม่อย่างนั้นฝั่งนั้นจะหมดเวลาก่อน", "bus.hub_map": "เลือกว่าแต่ละแถวของตู้ต่ออยู่กับช่องไหนของฮับ RS485 ตั้งแต่ช่อง 1–8 ถ้าเลือกต่อตรง คือแถวที่ไม่ผ่านฮับ และตั้งต่อตรงทั้ง 10 แถว เกตเวย์จะปิดการจัดการฮับ", "sys.wdt_ms": "บอร์ดรีเซ็ตตัวเองถ้าเฟิร์มแวร์หยุดทำงานนานเท่านี้ ต้องนานกว่าเวลารอสาย LAN ตอนเปิดเครื่อง ไม่อย่างนั้นบอร์ดจะรีสตาร์ทวนไม่จบ มีผลหลังรีบูต" };
function gwLabel(k) { if (lang === "th" && GWTH[k.key]) return GWTH[k.key]; const tx = k.text && k.text[lang]; return (tx && tx.label) || (GWNAMES[k.key] && GWNAMES[k.key][lang === "th" ? 0 : 1]) || k.key; }

function showInfo(key) {
  const k = S.gw.data && S.gw.data.keys.find((x) => x.key === key); if (!k) return;
  const tx = (k.text && k.text[lang]) || {};
  const flags = [k.reboot ? t("rebootKey") : "", k.ro ? t("ro") : ""].filter(Boolean).map((f) => `<span class="chip ${f === t("ro") ? "off" : "warn"}">${esc(f)}</span>`).join(" ");
  $("#infobody").innerHTML = `<h2>${esc(gwLabel(k))}</h2><div class="mono small muted" style="margin:2px 0 10px">${esc(k.key)}</div>
    <p style="margin:0 0 12px;white-space:pre-line">${esc((lang === "th" && GWTHHINT[k.key]) || tx.hint || t("noExplain"))}</p>
    <dl class="kv"><dt>${t("curValue")}</dt><dd class="mono">${esc(k.value)}</dd>${k.key in S.gw.edits ? `<dt>${t("newValue")}</dt><dd class="mono">${esc(S.gw.edits[k.key])}</dd>` : ""}</dl>${flags ? `<div class="row" style="margin-top:10px">${flags}</div>` : ""}`;
  const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
}

function viewGateway() {
  const g = S.gw, d = g.data;
  const opts = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === g.id ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  let body = "";
  if (d && d.ok) {
    const i = d.info;
    const groups = {};
    d.keys.forEach((k) => { const p = k.key.split(".")[0]; (groups[p] = groups[p] || []).push(k); });
    Object.values(groups).forEach((g) => g.sort((a, b) => gwRank(a.key) - gwRank(b.key)));
    const order = [...GWGROUPS.filter((x) => groups[x]), ...Object.keys(groups).filter((x) => !GWGROUPS.includes(x))];
    const sw = (name, on, act, info, locked) => `<div class="switch"><div><b>${t(name)}</b><button class="why" data-act="sw-info" data-info="${info}" type="button" aria-label="${t("explain")}">?</button></div><button class="sw" role="switch" aria-checked="${on}" data-act="${act || "gw-vol"}" data-name="${name}"${locked ? " disabled" : ""}></button></div>`;
    const field = (k) => {
      const ed = k.key in g.edits, val = ed ? g.edits[k.key] : k.value;
      if (k.key === "bus.hub_map") {
        const cur = hubRows(val), saved = hubRows(k.value);
        const cells = cur.map((v, i) => `<div class="hubcell"><span>${t("hubRow", { n: i + 1 })}</span><select data-hubrow="${i}"${v !== saved[i] ? ' style="border-color:var(--brand)"' : ""}>`
          + `<option value="0"${v === 0 ? " selected" : ""}>${t("hubDirect")}</option>` + [1, 2, 3, 4, 5, 6, 7, 8].map((c) => `<option value="${c}"${v === c ? " selected" : ""}>${t("hubCh", { n: c })}</option>`).join("") + `</select></div>`).join("");
        return `<div class="field" style="grid-column:1/-1"><label>${esc(gwLabel(k))}${whyBtn(k)}</label><div class="hubgrid">${cells}</div></div>`;
      }
      if (GWENUM[k.key] && !k.ro) {
        const L = GWENUM[k.key], i18 = lang === "th" ? 0 : 1, vals = Object.keys(L).sort((x, y) => x - y), cur = String(val);
        const opts = vals.map((v) => `<option value="${v}"${v === cur ? " selected" : ""}>${esc(L[v][i18])}</option>`).join("") + (vals.includes(cur) ? "" : `<option value="${esc(cur)}" selected>${esc(cur)}</option>`);
        return `<div class="field"><label>${esc(gwLabel(k))}${whyBtn(k)}</label>
          <select data-key="${esc(k.key)}"${ed ? ' style="border-color:var(--brand)"' : ""}>${opts}</select></div>`;
      }
      return `<div class="field"><label>${esc(gwLabel(k))}${whyBtn(k)}</label>
        <input data-key="${esc(k.key)}" value="${esc(val)}" ${k.ro ? 'disabled class="ro"' : ""} ${ed ? 'style="border-color:var(--brand)"' : ""}></div>`;
    };
    const sh = d.shape && d.shape.layout && !d.shape.agreed ? `<div class="notice">${t("shapeBad", { l: esc(d.shape.label), w: esc(d.shape.why) })}<div class="row" style="margin-top:8px">${d.shape.fixable ? `<button class="btn" data-act="gw-shape">${t("shapeFix")}</button>` : `<span class="small">${t("shapeNoFix")}</span>`}</div></div>` : "";
    body = sh + `<section class="card"><dl class="kv"><dt>${t("fw")}</dt><dd class="mono">${esc(i.fw)}</dd><dt>${t("uptime")}</dt><dd>${fmtUp(+i["sys.up"] || 0)} (${esc(i["sys.reset"] || "")})</dd>
        <dt>${t("clients")}</dt><dd>${esc(i["net.client"] || "?")}/2</dd><dt>${t("clock")}</dt><dd>${i["time.set"] === "1" ? esc((i["time.now"] || "").replace("T", " ")) : t("clockUnset")}</dd></dl></section>
      <section class="card stack">${order.map((grp) => `<details><summary><b>${esc(TXT[lang]["g_" + grp] || grp)}</b> <span class="small muted">${groups[grp].length}</span></summary><div class="fgrid" style="margin-top:8px">${groups[grp].map(field).join("")}</div></details>`).join("") || `<p class="muted">${t("noKeys")}</p>`}</section>
      <section class="card stack">${sw("resync", i["rtu.heal"] === "1", "", "resyncInfo")}${sw("exc", i["tcp.exc"] === "1", "", "excInfo")}</section>
      <section class="card stack"><div class="row"><button class="btn" data-act="gw-export">${t("expCfg")}</button><label class="btn">${t("impCfg")}<input type="file" id="gwimport" accept=".json,application/json" hidden></label></div></section>
      <section class="card stack"><h3>${t("danger")}</h3><div class="row"><button class="btn" data-act="gw-time">${t("setClock")}</button><button class="btn" data-act="gw-discard">${t("discard")}</button><button class="btn" data-act="gw-reboot">${t("reboot")}</button><button class="btn" data-act="gw-defaults" style="color:var(--bad)">${t("defaults")}</button></div></section>`;
  } else if (d && !d.ok) body = `<div class="notice bad">${esc(d.error)}</div>`;
  return `<div class="row between"><h1>${t("gateway_page")}</h1></div>
    <section class="card stack"><div class="row" style="align-items:flex-end"><div class="field" style="min-width:0;flex:1"><label>${t("pick")}</label><select id="gwsel"><option value="">—</option>${opts}</select></div>
      <button class="btn primary" data-act="gw-read" style="flex:none;min-width:112px;white-space:nowrap">${g.busy ? t("reading") : t("read")}</button></div></section>
    <div class="stack" style="margin-top:12px">${body}</div><div id="gwbar"></div>`;
}
function gwBar() {
  const n = gwChanged(), el = $("#gwbar"); if (!el) return;
  if (!n) { el.innerHTML = ""; return; }
  const shown = (k, v) => { const e = GWENUM[k] && GWENUM[k][v]; return e ? e[lang === "th" ? 0 : 1] : v; };
  const diffs = Object.entries(S.gw.edits).map(([k, v]) => { const kk = S.gw.data.keys.find((x) => x.key === k); return `<div class="small">${esc(gwLabel(kk))}: ${esc(shown(k, kk.value))} → <b>${esc(shown(k, v))}</b></div>`; }).join("");
  el.innerHTML = `<section class="card stack" style="position:sticky;bottom:calc(var(--navh) + 8px);margin-top:12px;border-color:var(--brand)"><b>${t("changes", { n })}</b>${diffs}
    <div class="row"><button class="btn primary" data-act="gw-apply">${t("apply")}</button><button class="btn" data-act="gw-clear">${t("reset")}</button></div></section>`;
}


const PCOL = { 1: "#ff3232", 2: "#32ff32", 3: "#3264ff", 4: "#ffd700", 5: "#00e5e5", 6: "#ff32ff", 7: "#ff5a1e", 8: "#fff096" };
function viewModule() {
  const m = S.mod, d = m.data;
  const opts = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === m.id ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const kv = (rows) => `<dl class="kv">${rows.filter(Boolean).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;
  let cards = `<div class="notice info">${t("modNotRead")}</div>`;
  if (d && d.ok === false && !d.device) cards = `<div class="notice bad">${esc((d.errors || [d.error || ""]).join(" · "))}</div>`;
  else if (d && d.device) {
    const dv = d.device, rt = d.runtime, tp = d.temps, lt = d.latch;
    const hc = (d.health || []).map((h) => `<span class="chip ${h.ok === null ? "off" : h.ok ? "ok" : "bad"}"><i class="dot"></i>${esc(h.name)}${h.ok === null ? " " + t("na") : ""}</span>`).join(" ");
    const st = d.stats ? `<section class="card stack"><h3>${t("cStats")}</h3><div class="small">${t("fires", { c: d.stats.fires, s: d.stats.seconds })}</div>
      <table><tr><th>#</th><th>${t("count")}</th><th>${t("seconds")}</th></tr>${d.stats.presets.map((p) => `<tr><td>${p.p}</td><td>${p.count}</td><td>${p.seconds}</td></tr>`).join("")}</table></section>` : "";
    cards = `<div class="cabs">
      <section class="card stack"><h3>${t("cDevice")}</h3>${kv([[t("mType"), esc(dv.type)], [t("mFw"), esc(dv.fw)], [t("mHw"), esc(dv.hw)], [t("mBaud"), esc(dv.baud) + " · ID " + dv.id], dv.uid ? [t("mUid"), `<span class="mono">${esc(dv.uid)}</span>`] : null])}</section>
      <section class="card stack"><h3>${t("cRuntime")}</h3>${kv([[t("mUptime"), esc(rt.uptime)], [t("mBoots"), rt.boots], [t("mMode"), esc(rt.mode)], [t("mPreset"), esc(rt.preset)], rt.button !== undefined && rt.button !== null ? [t("mButton"), rt.button + (rt.held ? " ●" : "")] : null])}</section>
      <section class="card stack"><h3>${t("cHealth")}</h3><div class="row">${hc}</div>${d.reset ? `<div class="small muted">${t("cReset")}: ${esc(d.reset)}</div>` : ""}</section>
      ${tp ? `<section class="card stack"><h3>${t("cTemp")}</h3>${kv([[t("mRoom"), `<span style="${tp.fault ? "color:var(--bad)" : ""}">${esc(tp.room)}</span>`], [t("mBoard"), `<span style="${tp.fault ? "color:var(--bad)" : ""}">${esc(tp.board)}</span>`], tp.current ? [t("mCurrent"), esc(tp.current)] : null])}</section>` : ""}
      ${lt ? `<section class="card stack"><h3>${t("cLatch")}</h3>${kv([[t("mLatch"), lt.state ? t(lt.state === "locked" ? "mLocked" : "mUnlocked") : "—"], [t("mUnlockedAgo", { s: lt.unlocked_ago_s }), ""], d.display !== undefined ? [t("mDisplay"), d.display] : null].map((r) => (r && r[1] === "" ? [r[0], ""] : r)))}</section>` : ""}
      ${st}</div>
      <p class="small muted">${t("checkedAt", { at: esc(d.at) })} · ${d.ms} ms</p>`;
  }
  const lb = (addr, label, cls) => `<button class="btn ${cls || ""}" data-act="mod-coil" data-addr="${addr}" data-val="1"${cls === "latch" ? " data-latch=1" : ""}>${label}</button>`;
  const presets = (m.presets || []).map((p) => `<section class="card stack"><div class="row"><i class="dot" style="color:${PCOL[p.n]};width:14px;height:14px"></i><b>${t("presets")} ${p.n}</b></div>
      <div class="stack tight">${lb(p.enable, t("pLight"))}${lb(p.display, t("pLightDisp"))}${lb(p.latch, t("pUnlock"), "latch")}${lb(p.latch_display, t("pUnlockDisp"), "latch")}</div></section>`).join("");
  return `<h1>${t("module_page")}</h1>
    <section class="card stack"><div class="row"><div class="field" style="min-width:220px;flex:1"><label>${t("pick")}</label><select id="modsel"><option value="">—</option>${opts}</select></div>
      <div class="field" style="width:140px"><label>${t("devId")}</label><input id="moddev" type="number" min="1" max="247" value="${m.dev}"></div>
      <button class="btn primary" data-act="mod-read">${m.busy ? t("reading") : t("read")}</button></div>
      <div class="row"><label class="row"><input type="checkbox" id="modstats"${m.stats ? " checked" : ""}> ${t("withStats")}</label>
      <label class="row"><input type="checkbox" id="modauto"${m.auto ? " checked" : ""}> ${t("auto")}</label></div></section>
    <div class="stack" style="margin-top:12px">${cards}
      <h2>${t("quick")}</h2><section class="card stack"><div class="row">${lb(509, t("identify"))}${lb(511, t("allOff"))}${lb(1020, t("latchSafety"), "latch")}${lb(1019, t("latchForce"), "latch")}
        <button class="btn" data-act="mod-coil" data-addr="1010" data-val="1">${t("dispPower")}</button><button class="btn" data-act="mod-coil" data-addr="1010" data-val="0">OFF</button></div>
        <div class="row"><div class="field" style="width:160px"><label>${t("number")}</label><input id="modnum" type="number" min="0" max="9999" value="45"></div><button class="btn" data-act="mod-number">${t("writeNumber")}</button></div>
        <p class="small muted">${t("cooldownNote")}</p></section>
      <h2>${t("presets")}</h2><div class="cabs">${presets}</div></div>`;
}
let modTimer = null;
async function modRead() {
  const m = S.mod; if (!m.id || !(m.dev >= 1)) return;
  if (m.busy) return;
  m.busy = true;
  try { m.data = await api("POST", "/api/v2/mod/monitor", { id: m.id, device_id: m.dev, stats: m.stats }); }
  catch (e) { m.data = { ok: false, error: e.message }; }
  m.busy = false; if (page === "module") renderKeep();
}
/* re-render without losing a typed value or the scroll position */
function renderKeep() { const y = window.scrollY, num = $("#modnum") && $("#modnum").value; render(); if ($("#modnum") && num) $("#modnum").value = num; window.scrollTo(0, y); }
function modAutoSync() {
  clearInterval(modTimer); modTimer = null;
  if (S.mod.auto && page === "module") modTimer = setInterval(() => { if (!document.hidden && page === "module") modRead(); }, 2000);
}


const fmtDur = (sec) => { sec = Math.max(0, Math.round(sec)); const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60); return h ? `${h} ${t("h")} ${m} m` : `${m} m ${sec % 60} s`; };
/* The verdict is a plain-text report written by the engine (and kept as a file for the classic tool), so it stays English on disk; in Thai mode the prose lines are translated here and the fixed-width table is left alone. */
function verdictText(txt) {
  if (lang !== "th") return txt;
  const map = [[/^fleet soak /, "ทดสอบต่อเนื่องทุกตู้ "], [/ran for ([\d.]+) h/, "รันนาน $1 ชม."], [/client timeout/, "timeout ฝั่ง client"],
    [/^(\d+) of (\d+) cabinets completely clean/, "สะอาดสมบูรณ์ $1 จาก $2 ตู้"],
    [/^gateway RS485 counters over the run.*$/, "ตัวนับ RS485 ของเกตเวย์ตลอดรอบ (พลาดครั้งแรกที่ซ่อมได้ และที่ซ่อมไม่ได้):"],
    [/repair failed/, "ซ่อมไม่ได้"], [/repaired/, "ซ่อมได้"], [/final timeouts/, "timeout สุดท้าย"], [/bad crc/, "CRC เสีย"], [/other /, "อื่นๆ "],
    [/^reply frames discarded as the wrong unit id: none/, "เฟรมตอบที่ถูกทิ้งเพราะ unit id ผิด: ไม่มี"], [/^reply frames discarded as the wrong unit id:/, "เฟรมตอบที่ถูกทิ้งเพราะ unit id ผิด:"]];
  const out = txt.split("\n").map((ln) => { if (/^\s*(cabinet|-{5,})/.test(ln)) return ln; let o = ln; for (const [re, to] of map) o = o.replace(re, to); return o; });
  const i = out.findIndex((l) => /^cabinet\s/.test(l));
  if (i >= 0) out.splice(i, 0, t("sColLegend"), "");
  return out.join("\n");
}
function viewSoak() {
  const k = S.soak, st = k.status || {};
  const running = !!st.running;
  const chip = (state) => { const cls = { clean: "ok", warn: "warn", "not clean": "bad", "did not run": "bad", starting: "info" }[state] || "info"; const key = { clean: "sClean", warn: "sWarn", "not clean": "sNotClean", "did not run": "sDidNot", starting: "sStarting" }[state]; return `<span class="chip ${cls}"><i class="dot"></i>${t(key)}</span>`; };
  let head = "";
  if (running) {
    const when = st.starts_in_s != null ? t("sArmed", { t: fmtDur(st.starts_in_s) }) : (st.left_s != null ? t("sLeft", { t: fmtDur(st.left_s) }) : t("sNoEnd"));
    head = `<section class="card stack"><div class="row between"><div><b>${t("sRunning")}</b> · ${st.count} · ${esc(when)}</div><button class="btn" style="color:var(--bad)" data-act="soak-stop">${t("sStop")}</button></div>
      <div class="small muted">${t("sLongNote")}${st.frames_discarded ? " · " + t("sFrames", { n: st.frames_discarded }) : ""}</div></section>`;
  } else {
    const rows = S.sites.map((x) => `<label class="row" style="min-height:40px"><input type="checkbox" data-pick="${esc(x.id)}"${k.sel.has(x.id) ? " checked" : ""}> <span>${esc(x.name)}</span> <span class="small muted mono">${esc(x.host)} · ${esc(x.cabinet || "?")}</span></label>`).join("");
    head = `<section class="card stack"><b>${t("sPick")}</b><div class="row"><button class="btn" data-act="soak-all">${t("sAll")}</button></div>${rows || `<p class="muted">${t("noSites")}</p>`}<p class="small muted">${t("sNeedType")}</p></section>
      <section class="card stack"><div class="fgrid">
        <div class="field"><label>${t("sMode")}</label><select id="soakmode"><option value="pharmacy"${k.mode === "pharmacy" ? " selected" : ""}>${t("sPharm")}</option><option value="poll"${k.mode === "poll" ? " selected" : ""}>${t("sPoll")}</option></select></div>
        <div class="field"><label>${t("sPicks")}</label><input id="soakpicks" type="number" min="1" value="${k.picks}"></div>
        <div class="field"><label>${t("sHours")}</label><input id="soakhours" type="number" min="0" max="336" step="0.5" value="${k.hours}"></div>
        <div class="field"><label>${t("sStartAt")}</label><input id="soakat" value="${esc(k.startAt)}" placeholder="21:00"></div></div>
        <div class="row"><button class="btn primary" data-act="soak-start">${t("sStart")}</button></div></section>`;
  }
  const cabs = (st.cabinets || []).length ? `<section class="card" style="overflow-x:auto"><table><tr><th>${t("sCab")}</th><th>${t("sState")}</th><th>${t("sPass")}</th><th>${t("sReads")}</th><th>${t("sFails")}</th><th>${t("sRbt")}</th><th>${t("sWdt")}</th><th>${t("sWorst")}</th><th>${t("sHeal")}</th></tr>
    ${st.cabinets.map((c) => `<tr><td><b>${esc(c.name)}</b>${c.note ? `<div class="tiny" style="color:var(--bad)">${esc(c.note)}</div>` : ""}</td><td>${chip(c.state)}</td><td>${c.passes}</td><td>${c.reads.toLocaleString()}</td><td>${c.fails}</td><td>${c.reboots}</td><td>${c.watchdogs}</td><td>${c.worst_ms}</td>
      <td>${c.gw_seen ? `${c.gw_healed} (${c.heal_per_h}/h)${c.gw_heal_failed ? ` · ✗${c.gw_heal_failed}` : ""}${c.gw_timeouts ? ` · ⏱${c.gw_timeouts}` : ""}${c.gw_bad_crc ? ` · CRC ${c.gw_bad_crc}` : ""}` : "—"}</td></tr>`).join("")}</table></section>` : "";
  const an = (st.anomalies || []).length ? `<section class="card stack"><h3>${t("sAnoms")}</h3>${st.anomalies.slice(0, 15).map((a) => `<div class="evrow"><span class="when">${esc(a.at)}</span><span><b>${esc(a.cabinet)}</b> ${a.id ? "id " + a.id + " " : ""}${esc(a.kind)} ${esc(a.detail)}</span></div>`).join("")}</section>` : "";
  const fin = st.finished && !running ? `<section class="card stack"><h3>${t("sVerdict")}</h3><pre class="mono small" style="white-space:pre-wrap;overflow-x:auto;margin:0">${esc(verdictText(st.finished.text))}</pre></section>` : "";
  const hist = `<section class="card stack"><h3>${t("sHistory")}</h3>${(k.runs || []).length ? k.runs.map((r) => `<div class="stack tight" style="padding:8px 0;border-bottom:1px solid var(--line)"><div class="row between"><b>${esc(r.started)}</b>
      ${r.verdict ? `<button class="btn" data-act="soak-view" data-name="${esc(r.verdict)}">${t("sView")}</button>` : ""}</div>
      <div class="small">${r.csv.length ? t("sCsvFiles") + ": " : ""}${r.csv.map((c) => `<a href="/api/v2/soak/file?name=${encodeURIComponent(c)}&download=1">${esc(c.replace(/^soak-/, "").replace(/-\d{8}-\d{6}\.csv$/, ""))}</a>`).join(" · ")}</div></div>`).join("") : `<p class="muted">${t("sNoRuns")}</p>`}
      ${k.verdict ? `<pre class="mono small" style="white-space:pre-wrap;overflow-x:auto;margin:0">${esc(verdictText(k.verdict))}</pre>` : ""}</section>`;
  return `<h1>${t("soak_page")}${lang === "th" ? " (Soak)" : ""}</h1><div class="stack">${head}${cabs}${an}${fin}${hist}</div>`;
}
async function soakRefresh() {
  try {
    S.soak.status = await api("GET", "/api/v2/soak/status");
    const running = !!S.soak.status.running;
    if (S.soak.was && !running) S.soak.runs = (await api("GET", "/api/v2/soak/runs")).runs;
    S.soak.was = running;
    if (page === "soak" && !document.activeElement.closest(".fgrid")) { const y = window.scrollY; render(); window.scrollTo(0, y); }
  } catch (e) { /* transient: next tick */ }
}
function soakSync() {
  clearInterval(S.soak.timer); S.soak.timer = null;
  if (page === "soak") { soakRefresh(); S.soak.timer = setInterval(() => { if (!document.hidden && page === "soak") soakRefresh(); }, 3000); }
}


function viewLabels() {
  const l = S.lab, o = l.opts;
  const opts = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === l.id ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const fmt = (n) => Number(n).toLocaleString(lang === "th" ? "th-TH" : "en-US");
  const row = (k, v, mono) => `<dt>${t(k)}</dt><dd${mono ? ' class="mono"' : ""}>${v}</dd>`;
  const info = l.info ? `<div class="stack" style="margin-top:6px;padding-top:12px;border-top:1px solid var(--line)"><h3>${t("lbIHead")}</h3><dl class="kv left">`
    + row("lbIName", esc(l.info.name)) + row("lbIIp", esc(l.info.ip), true) + row("lbIMac", esc(l.info.mac), true)
    + row("lbIRows", t("lbIRowsV", { n: l.info.rows })) + row("lbILen", t("lbILenV", { mm: l.info.mm })) + row("lbIFile", t("lbIBytesV", { n: fmt(l.info.size) }))
    + row("lbIQrData", t("lbIQrDataV", { n: l.info.qr_bytes, spare: l.info.spare_bytes }))
    + row("lbIQrKind", t("lbIQrKindV", { v: l.info.qr_version, ecc: esc(l.info.ecc), rec: esc(l.info.recover_pct) }))
    + `</dl><details><summary class="small">${t("lbIPayload")}</summary><pre class="mono small" style="white-space:pre-wrap;margin:8px 0 0;padding:10px;border-radius:8px;background:var(--surface2)">${esc(l.info.payload)}</pre></details></div>` : "";
  const pic = l.info && l.info.svg ? `<section class="card stack"><h3>${t("lbPicture")}</h3><div style="border:1px solid var(--line);border-radius:8px;background:#fff;padding:6px">${l.info.svg}</div><p class="small muted">${t("lbPicNote")}</p></section>` : "";
  return `<h1>${t("labels_page")}</h1>
    <section class="card stack"><div class="fgrid">
      <div class="field"><label>${t("pick")}</label><select id="lbsel"><option value="">—</option>${opts}</select></div>
      <div class="field"><label>${t("lbWard")}</label><input id="lbward" value="${esc(l.ward)}"></div>
      <div class="field"><label>${t("lbSerial")}</label><input id="lbserial" value="${esc(l.serial)}"></div>
      <div class="field"><label>${t("lbLayout")}</label><select id="lblayout">${o ? o.layouts.map((x) => `<option value="${esc(x.key)}"${x.key === l.layout ? " selected" : ""}>${esc(x.title)}</option>`).join("") : ""}</select></div>
      <div class="field"><label>${t("lbPlate")}</label><select id="lbplate">${o ? o.plates.map((x) => `<option value="${esc(x.key)}"${x.key === l.plate ? " selected" : ""}>${esc(x.text[lang] || x.key)}</option>`).join("") : ""}</select></div></div>
      <div class="row"><button class="btn" data-act="lb-preview">${l.busy ? t("reading") : t("lbPreview")}</button><button class="btn primary" data-act="lb-file">${t("lbDownload")}</button></div>${info}</section>${pic}`;
}

function fwRows(rows) {
  return rows.length ? `<section class="card" style="overflow-x:auto"><table><tr><th>${t("sCab")}</th><th>${t("sState")}</th><th>${t("fwPhase")}</th><th>%</th><th>${t("fwLeft")}</th><th>${t("fwCensus")}</th></tr>
    ${rows.map((r) => `<tr><td><b>${esc(r.name)}</b> <span class="tiny muted">${r.modules}</span></td><td>${esc(r.state)}${r.channels ? ` <span class="tiny muted">${r.channel}/${r.channels}</span>` : ""}</td><td>${esc(r.phase)}</td><td>${r.pct}</td><td>${r.left.length ? esc(r.left.join(",")) : t("fwNone")}</td><td class="small">${esc(r.census || r.note)}</td></tr>`).join("")}</table></section>` : "";
}
function viewFirmware() {
  const f = S.fw, im = f.images, ota = f.ota || {}, gw = f.gw || {};
  const sitesRows = S.sites.map((x) => `<label class="row" style="min-height:40px"><input type="checkbox" data-fwpick="${esc(x.id)}"${f.sel.has(x.id) ? " checked" : ""}> <span>${esc(x.name)}</span> <span class="small muted mono">${esc(x.host)} · ${esc(x.cabinet || "?")}</span></label>`).join("");
  const modImgs = im ? im.module.map((i) => `<option value="${esc(i.key)}"${i.key === f.image ? " selected" : ""}>${esc(i.label)}</option>`).join("") : "";
  const gwImgs = im ? im.gateway.map((i) => `<option value="${esc(i.key)}"${i.key === f.gwImage ? " selected" : ""}>${esc(i.label)}</option>`).join("") : "";
  const gsite = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === f.gwId ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const otaBlock = ota.running
    ? `<section class="card stack"><div class="row between"><b>${t("fwRun")}</b><button class="btn" style="color:var(--bad)" data-act="fw-cancel">${t("fwCancel")}</button></div></section>`
    : `<section class="card stack"><b>${t("fwOta")}</b>${sitesRows || `<p class="muted">${t("noSites")}</p>`}
        <div class="field"><label>${t("fwImage")}</label><select id="fwimage">${modImgs || `<option value="">${t("fwNoOta")}</option>`}</select></div>
        <div class="row"><button class="btn primary" data-act="fw-start">${t("fwStart")}</button></div></section>`;
  const log = (ota.log || []).length ? `<section class="card stack"><h3>${t("fwLog")}</h3><div style="max-height:260px;overflow:auto">${ota.log.slice(-60).map((l) => `<div class="evrow"><span class="when">${esc(l.at)}</span><span><b>${esc(l.cabinet)}</b> ${esc(l.text)}</span></div>`).join("")}</div></section>` : "";
  const outcome = ota.outcome && !ota.running ? `<section class="card stack"><pre class="mono small" style="white-space:pre-wrap;overflow-x:auto;margin:0">${esc(ota.outcome.text)}</pre></section>` : "";
  const gwStat = gw.name ? `<div class="notice ${gw.done ? (gw.ok ? "info" : "bad") : ""}">${gw.running ? t("fwGwRun") + " " + gw.pct + "%" : gw.done ? (gw.ok ? t("fwDone") : t("fwFail")) + " · " + esc(gw.summary) : ""}
      <div class="mono tiny" style="white-space:pre-wrap;margin-top:6px">${esc((gw.lines || []).join("\n"))}</div></div>` : "";
  return `<h1>${t("firmware_page")}</h1><div class="stack">${otaBlock}${fwRows(ota.rows || [])}${log}${outcome}
    <section class="card stack"><b>${t("fwGw")}</b><p class="small muted">${t("fwGwNote")}</p><div class="fgrid">
      <div class="field"><label>${t("pick")}</label><select id="fwgwsel"><option value="">—</option>${gsite}</select></div>
      <div class="field"><label>${t("fwImage")}</label><select id="fwgwimage"><option value="">—</option>${gwImgs}</select></div>
      <div class="field"><label>${t("fwUpload")}</label>${fileBox("fwgwfile", f.gwFileName)}</div>
      <div class="field"><label>${t("fwConfirm")}</label><input id="fwgwconfirm" value="${esc(f.gwConfirm)}" autocomplete="off"></div></div>
      <div class="row"><button class="btn" style="color:var(--bad)" data-act="fw-gwstart"${gw.running ? " disabled" : ""}>${t("fwGwStart")}</button></div>${gwStat}</section></div>`;
}
async function fwRefresh() {
  try {
    S.fw.ota = await api("GET", "/api/v2/fw/ota/status");
    S.fw.gw = await api("GET", "/api/v2/fw/gateway/status");
    if (page === "firmware" && !document.activeElement.matches("input,select")) { const y = window.scrollY; render(); window.scrollTo(0, y); }
  } catch (e) { /* next tick */ }
}
function fwSync() {
  clearInterval(S.fw.timer); S.fw.timer = null;
  if (page === "firmware") { fwRefresh(); S.fw.timer = setInterval(() => { if (!document.hidden && page === "firmware") fwRefresh(); }, 3000); }
}

/* ---------- commission (ST-Link) ---------- */
S.cm = { opts: null, probe: null, probing: false, mode: "single", image: "", file: null, fileName: "", id: "", ids: "", lot: "", type: "10", overwrite: false, confirm: "", since: 0, lines: [], running: false, prog: null, boards: {}, done: null, timer: null, sel: new Set(), gridOpen: false };
function cmLog() { return S.cm.lines.length ? S.cm.lines.map((l) => `<div style="${l.level === "err" ? "color:var(--bad)" : l.level === "ok" ? "color:var(--ok)" : l.level === "warn" ? "color:var(--warn)" : ""}">${esc(l.text)}</div>`).join("") : `<span class="muted" style="font-family:var(--sans)">${t("cmNone")}</span>`; }
function cmStatus() {
  const c = S.cm, parts = [];
  if (c.running) parts.push(`<span class="chip warn"><i class="dot"></i>${t("cmRunning")}${c.prog ? " " + c.prog.done + "/" + c.prog.total : ""}</span>`);
  else if (c.done) parts.push(`<span class="chip ${c.done.ok ? "ok" : "bad"}"><i class="dot"></i>${t(c.done.ok ? "cmResultOk" : "cmResultFail")}</span> <span class="small">${esc(c.done.summary)}</span>`);
  Object.keys(c.boards).forEach((id) => { const b = c.boards[id]; parts.push(`<span class="chip ${b === "next" ? "warn" : b === "ok" ? "ok" : "bad"}">${esc(id)}</span>`); });
  return parts.join(" ");
}
/* "LGS 80 ช่อง" / "LGS 80 slots": the count is the slot count, so it is not repeated. */
function layoutName(l) {
  const n = l.ids.length, fridge = /^lgs\d+r$/.test(l.key), fam = /^lgs\d+r?$/.test(l.key) ? "LGS" : /^smt/.test(l.key) ? "SMT" : "";
  if (!fam) return l.label;
  return lang === "th" ? `${fam} ${n} ช่อง${fridge ? " (ตู้เย็น)" : ""}` : `${fam} ${n} slots${fridge ? " (fridge)" : ""}`;
}
function cmIdsText() { return [...S.cm.sel].sort((a, b) => a - b).join(","); }
function cmGridHtml() {
  const c = S.cm, g = (c.opts && c.opts.grid) || { rows: 10, cols: 8 }, batch = c.mode === "batch";
  let h = `<div class="cmgrid" style="grid-template-columns:auto repeat(${g.cols},minmax(0,1fr))">`;
  for (let r = 1; r <= g.rows; r++) {
    h += batch ? `<button class="cmrow" data-cmrow="${r}" aria-label="R${r}">R${r}</button>` : `<span class="cmrow tiny muted">R${r}</span>`;
    for (let k = 1; k <= g.cols; k++) {
      const id = r * 10 + k, st = c.boards[id], on = batch ? c.sel.has(id) : String(c.id) === String(id);
      h += `<button class="cmcell${on ? " on" : ""}${st ? " " + st : ""}" data-cmcell="${id}" aria-pressed="${on}">${id}</button>`;
    }
  }
  return h + "</div>";
}
/* One look for every file picker: the browser's own widget draws its button and label differently in each engine, which is what never lined up with the other fields. */
/* What each bundled module firmware changed, written from the module repo's own version notes (doc/FIRMWARE_VERSION_NOTE.md). Shown by the "i" button on the Commission page in the page language; a version not listed falls back to the short English note that ships with the image. Keep the facts to what that note states. */
const FW_NOTES = {
  "v3.5.5": {
    th: { date: "26 ต.ค. 2569 (FW 30505)", head: "โมดูลไม่ล็อกเฟสหลังมีคำขอที่ไม่มีใครตอบ", items: [
      "แก้: เมื่อมีคำขอที่ไม่มีใครตอบบนบัส (ID ที่ไม่มีอยู่, โมดูลที่ตอบช้า, เฟรมที่ฮับตัดครึ่งทาง) โมดูลอื่นบนช่องเดียวกันจะเลื่อนเฟสและทิ้งคำขอของตัวเอง ทำให้ \"ครั้งแรกพลาด ครั้งที่สองผ่าน\" ค้างอยู่จนกว่าจะมี CRC error หรือตัดไฟ ตอนนี้โมดูลล้างแฟล็กของไลบรารี Modbus ทุกรอบ จึงไม่ล็อกเฟส",
      "ยังไม่แก้: โมดูลที่หน่วงจริงตอนเขียนสถิติรายชั่วโมงลง AT24 (25-60 ms) ยังตอบช้า (ฝั่งเกตเวย์รับด้วย rs485.t2_ms) และปัญหาทางไฟฟ้าของโมดูลแถวที่ 2 ของตู้ Ref-12",
      "ความเข้ากันได้: ไม่เปลี่ยน register map และ settings อัปเดตผ่านบัสจาก v3.4.x / v3.5.x ได้ทั้งบัส",
      "ขนาด: ไฟล์ factory 65,400 B (ใช้ลงผ่าน ST-Link ครั้งแรก)"] },
    en: { date: "26 Oct 2026 (FW 30505)", head: "Modules no longer lose frame phase after an unanswered request", items: [
      "Fixed: when a request on the bus goes unanswered (an ID that does not exist, a slow module, a frame cut by the hub) the other modules on that channel shift phase and discard their own requests: \"first poll missed, second passes\", until a CRC error or a power cut changes the phase. The module now clears the Modbus library's flag after every poll, so it keeps its phase.",
      "Not fixed: a module that really is slow while writing its hourly stats to the AT24 (25-60 ms) still answers late (the gateway absorbs it with rs485.t2_ms), and the electrical problem on row 2 of the Ref-12 cabinet.",
      "Compatibility: no register map or settings change. Over-the-bus update from v3.4.x / v3.5.x is safe for the whole bus.",
      "Size: factory image 65,400 B (the one for the first ST-Link flash)."] } },
  "v3.5.4": {
    th: { date: "2 ต.ค. 2569 (FW 30504)", head: "ครบ max-on-time แล้วดับทั้งไฟและจอ (รวม v3.5.1-v3.5.3)", items: [
      "บอร์ดวงแหวน (type 20): เมื่อไฟติดครบเวลา max-on-time ตอนนี้ดับทั้งวงแหวนและตัวเลขบนจอ OLED (เดิมดับแค่วงแหวน ตัวเลขยังค้าง)",
      "รวมจาก v3.5.3: เวลา max-on นับจากตอนที่ไฟติดจริง ไม่ใช่จากรอบบันทึกสถิติ ไฟที่ไม่มีใครสั่งดับจึงดับเองจริงเมื่อครบ (ค่าเริ่มต้น 3600 วินาที, 0 = ไม่จำกัด) ระบบที่เคยพึ่งให้ไฟค้างนานกว่านั้นต้องตั้งค่าให้ยาวขึ้น",
      "รวมจาก v3.5.2 และ v3.5.1: session อัปเดตผ่านบัสอยู่ได้ 90 วินาที (เดิม 30) และจำกัดเวลารอภายในไลบรารี Modbus ไม่ให้โมดูลค้างจนวอตช์ด็อกรีเซ็ตเมื่อเฟรมถูกตัดหรือมีไบต์ขยะ",
      "บอร์ด mask (type 10) ไม่มีจอ OLED พฤติกรรมเดิม ความเข้ากันได้: ไม่เปลี่ยน register map และ settings อัปเดตผ่านบัสจาก v3.4.x / v3.5.x ได้"] },
    en: { date: "2 Oct 2026 (FW 30504)", head: "Max-on-time puts out both the light and the display (includes v3.5.1-v3.5.3)", items: [
      "Ring boards (type 20): when a light reaches its max-on-time it now puts out the ring and the number on the OLED (it used to put out only the ring, leaving the number lit).",
      "From v3.5.3: max-on is counted from when the light really went on, not from the stats flush, so a light nobody switches off does go out when the time is up (default 3600 s, 0 = no limit). A server that relied on lights staying on longer must set it higher.",
      "From v3.5.2 and v3.5.1: an over-the-bus update session lives 90 s (was 30), and the Modbus library's own waits are bounded so a module no longer hangs into a watchdog reset on a cut frame or stray bytes.",
      "Mask boards (type 10) have no OLED: behaviour unchanged. Compatibility: no register map or settings change; over-the-bus update from v3.4.x / v3.5.x is safe."] } },
  "v3.5.0": {
    th: { date: "8 ก.ย. 2569 (แท็ก v3.5.0, FW 30500)", head: "บอร์ด mask (type 10) ใช้หน้าต่างอิสระ", items: [
      "บอร์ด mask 8 ช่อง (type 10 STANDARD): coil แต่ละตัวคุมหน้าต่างของตัวเองเท่านั้น จึงติดพร้อมกันได้หลายช่อง (v3.4.0 และก่อนหน้าทำงานแบบ \"radio\" คือติดได้ครั้งละหน้าต่างเดียว)",
      "register 61 ใหม่ (เดิมเป็นช่องสำรอง): bit n-1 = หน้าต่างที่ n กำลังติดอยู่",
      "บอร์ดวงแหวน (type 20) ไม่เปลี่ยนพฤติกรรม (มีชุดทดสอบ regression ยืนยัน)",
      "หมายเหตุ: รุ่นนี้ไม่มีหัวข้อของตัวเองในไฟล์บันทึกเวอร์ชัน รายละเอียดอ้างจากเอกสารตารางควบคุมและประวัติ commit"] },
    en: { date: "8 Sep 2026 (tag v3.5.0, FW 30500)", head: "Mask boards (type 10) use independent windows", items: [
      "8-LED mask boards (type 10 STANDARD): each coil drives only its own window, so several can be lit at once (v3.4.0 and earlier behave as a \"radio\": one window at a time).",
      "New register 61 (previously reserved): bit n-1 = window n is lit.",
      "Ring boards (type 20) behave as before (a regression test confirms it).",
      "Note: this release has no section of its own in the version note; the details come from the control table document and the commit history."] } },
  "v3.4.0": {
    th: { date: "27 ส.ค. 2569 (FW 30400)", head: "จอเลขใหญ่แสดง 3 หลัก (0-999)", items: [
      "จอเลขใหญ่แสดง 0-999 (เดิม 0-99) ค่าต่ำกว่า 100 ยังแสดง 2 หลักหน้าตาเดิม เกิน 99 จึงงอกหลักที่สาม",
      "สัญญาของ register 60 เปลี่ยน: ค่าสูงสุดที่รับขยับจาก 99 เป็น 999 เอกสารฝั่งเซิร์ฟเวอร์ที่ระบุ 0-99 ต้องแจ้งพร้อมกันตอนติดตั้ง",
      "โหมด DEMO นับ 0-999 และเริ่มจาก ID เต็มค่า (ID 108 แสดง 108)",
      "ฟอนต์เลขใหญ่ลดจากสูง 54 เป็น 51 px เพื่อให้เลข 3 หลักพ้นขอบเบเซลของจอ",
      "ความเข้ากันได้: ไม่เปลี่ยน settings/stats schema อัปเดตผ่านบัสจาก v3.3.x ได้"] },
    en: { date: "27 Aug 2026 (FW 30400)", head: "Big display face shows 3 digits (0-999)", items: [
      "The big number face shows 0-999 (was 0-99). Values below 100 keep the two-digit look; above 99 a third digit appears.",
      "The register 60 contract changed: the accepted maximum moves from 99 to 999. Server-side documents that say 0-99 must be updated at the same time.",
      "DEMO counts 0-999 and starts from the full ID (ID 108 shows 108).",
      "The big-number font is 51 px tall (was 54) so three digits clear the display bezel.",
      "Compatibility: no settings/stats schema change; over-the-bus update from v3.3.x is safe."] } },
  "v3.3.0": {
    th: { date: "13 ส.ค. 2569 (FW 30300)", head: "สถิติ v2, framing, หน้าปัดหน้าเครื่อง", items: [
      "สถิติ v2 (register 400-451): จำนวนครั้งและเวลาที่ไฟติดรายพรีเซ็ต, จำนวนครั้งที่กลอนทำงาน, จำนวนครั้งที่กดปุ่มยืนยัน, วินาทีที่ทำงานสะสม, จำนวน IWDG reset อ่านค่า blob v1 เดิมเข้ามาให้ ตัวนับที่สะสมไว้ในสนามจึงไม่หายตอนอัปเกรด",
      "หน้าปัดหน้าเครื่อง: SET_ID ตั้งได้ถึง 108 กดค้างเพื่อไล่เลข บันทึกเองเมื่อปล่อยครบเวลา ตัวเลขขยายเต็มกรอบ และมีหน้าจอ OTA ของตัวเอง",
      "device type ตอน commissioning (เลือกชนิดตู้ตอนลงไฟล์) และ LED-8 mask สำหรับ type 10",
      "แก้ framing RTU: รอความเงียบก่อนส่งบัฟเฟอร์ให้ไลบรารี เดิมฮับตัดเฟรมครึ่งทางตอนสลับแชนแนลแล้วโมดูลค้างจนวอตช์ด็อกรีเซ็ต (วัดได้ประมาณ 0.6 ครั้งต่อโมดูลต่อรอบที่มีการข้ามแชนแนล)"] },
    en: { date: "13 Aug 2026 (FW 30300)", head: "Stats v2, framing, front-panel dial", items: [
      "Statistics v2 (registers 400-451): per-preset on-count and on-time, latch operations, confirm-button presses, accumulated run seconds, IWDG resets. The old v1 blob is read in, so counters collected in the field survive the upgrade.",
      "Front-panel dial: SET_ID goes up to 108, hold to scroll through numbers, saves itself when left for the set time, bigger digits fill the frame, and OTA has its own screen.",
      "Device type at commissioning (the cabinet type chosen when the file is flashed) and the LED-8 mask for type 10.",
      "RTU framing fix: wait for bus silence before handing the buffer to the library. Before, a hub cutting a frame at a channel change left a module hung until the watchdog reset it (about 0.6 resets per module per run with channel crossings)."] } },
};
function fwNoteHtml(im) {
  const n = FW_NOTES[im.version] && FW_NOTES[im.version][lang];
  if (!n) return `<h2>${esc(im.version)}</h2><p style="margin:8px 0 12px">${esc(im.note || "—")}</p>`;
  return `<h2>${esc(im.version)}</h2><div class="small muted" style="margin:2px 0 8px">${esc(n.date)}</div><p style="margin:0 0 8px;font-weight:600">${esc(n.head)}</p><ul style="margin:0 0 12px;padding-left:18px;display:grid;gap:6px;font-size:14px">${n.items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
}
function fileBox(id, name) {
  return `<div class="filebox"><label class="btn">${t("cmChoose")}<input type="file" id="${id}" accept=".bin" hidden></label><span class="small ${name ? "" : "muted"}">${esc(name || t("cmNoFile"))}</span></div>`;
}
function viewCommission() {
  const c = S.cm, o = c.opts, pr = c.probe;
  const imgs = o ? o.images.map((i) => `<option value="${esc(i.key)}"${i.key === c.image ? " selected" : ""}>${esc(i.version)}</option>`).join("") : "";
  const types = o ? o.device_types.map((d) => `<option value="${d.id}"${String(d.id) === c.type ? " selected" : ""}>${d.id} — ${esc(d.name)}</option>`).join("") : "";
  let probe = "";
  if (pr) probe = !pr.cli ? `<div class="notice bad">${t("cmNoCli")}</div>` : pr.probes.length ? `<div class="notice info">${t("cmProbeOk", { n: pr.probes.length })} · ${pr.probes.map((p) => esc(p.serial)).join(", ")} · ${t("cmCli")} ${esc(pr.version || "")}</div>` : `<div class="notice bad">${t("cmNoProbe")}</div>`;
  const same = o ? o.layouts.find((l) => l.ids.length === c.sel.size && l.ids.every((i) => c.sel.has(i))) : null;
  const presets = o ? o.layouts.map((l) => `<option value="${esc(l.key)}"${same && same.key === l.key ? " selected" : ""}>${esc(layoutName(l))}</option>`).join("") : "";
  const idField = c.mode === "batch"
    ? `<div class="field" style="grid-column:1/-1"><label>${t("cmGrid")}</label>
        <div class="row"><select id="cmpreset"><option value="">${t("cmPreset")}</option>${presets}</select><button class="btn" data-act="cm-clear">${t("cmClear")}</button><span class="small muted">${t("cmSelected", { n: c.sel.size })}</span></div>${cmGridHtml()}</div>`
    : `<div class="field" style="grid-column:1/-1"><label>${t("cmId")}</label><input id="cmid" value="${esc(c.id)}" inputmode="numeric" autocomplete="off" style="max-width:140px"></div>`;
  const ow = c.mode === "batch" ? "" : `<label class="row" style="min-height:40px"><input type="checkbox" id="cmow"${c.overwrite ? " checked" : ""}> <span>${t("cmOverwrite")}</span></label>`;
  return `<h1>${t("commission_page")}</h1><div class="stack">${c.err ? `<div class="notice bad">${esc(c.err)}</div>` : ""}
    <section class="card stack"><div class="row"><button class="btn" data-act="cm-probe"${c.probing ? " disabled" : ""}>${c.probing ? t("cmProbing") : t("cmProbe")}</button></div>${probe}</section>
    <section class="card stack"><div class="seg"><button data-cmmode="single" aria-pressed="${c.mode === "single"}">${t("cmSingle")}</button><button data-cmmode="batch" aria-pressed="${c.mode === "batch"}">${t("cmBatch")}</button></div><div class="fgrid">
      <div class="field"><label>${t("cmImage")}<button class="why" type="button" data-act="cm-info" aria-label="${t("cmWhat")}" title="${t("cmWhat")}">i</button></label><select id="cmimage"><option value="">—</option>${imgs}</select></div>
      <div class="field"><label>${t("cmUpload")}</label>${fileBox("cmfile", c.fileName)}</div>
      <div class="field"><label>${t("cmType")}</label><select id="cmtype">${types}</select></div>
      <div class="field"><label>${t("cmLot")}</label><input id="cmlot" value="${esc(c.lot)}" autocomplete="off"></div>${idField}</div>${ow}
      <div class="row"><button class="btn primary" data-act="cm-start"${c.running ? " disabled" : ""}>${t("cmStart")}</button>${c.running ? `<button class="btn" style="color:var(--bad)" data-act="cm-cancel">${t("cmCancel")}</button>` : ""}</div></section>
    <section class="card stack"><h3>${t("cmLog")}</h3><div id="cmstat" class="row">${cmStatus()}</div>${c.prog && c.running ? `<progress value="${c.prog.done}" max="${c.prog.total || 1}" style="width:100%"></progress>` : ""}
      <div id="cmlog" class="mono small" style="max-height:320px;overflow:auto;white-space:pre-wrap">${cmLog()}</div></section></div>`;
}
async function cmPoll() {
  const c = S.cm;
  try {
    const r = await api("GET", "/api/v2/cm/events?since=" + c.since);
    const was = c.running; c.since = r.seq; c.running = r.running;
    r.events.forEach((e) => {
      if (e.k === "line") c.lines.push(e); else if (e.k === "progress") c.prog = e;
      else if (e.k === "done") c.done = e; else if (e.k === "next") c.boards[e.id] = "next"; else if (e.k === "board") c.boards[e.id] = e.ok ? "ok" : "bad";
    });
    if (c.lines.length > 400) c.lines = c.lines.slice(-400);
    if (c.running !== was) { if (page === "commission" && !document.activeElement.matches("input,select")) { const y = window.scrollY; render(); window.scrollTo(0, y); } return; }
    if (r.events.length && page === "commission") {
      document.querySelectorAll(".cmcell").forEach((el) => { const st = c.boards[el.dataset.cmcell]; el.classList.toggle("next", st === "next"); el.classList.toggle("ok", st === "ok"); el.classList.toggle("bad", st === "bad"); });
      const lg = $("#cmlog"), st = $("#cmstat"); if (lg) { lg.innerHTML = cmLog(); lg.scrollTop = lg.scrollHeight; } if (st) st.innerHTML = cmStatus();
      const pg = document.querySelector("progress"); if (pg && c.prog) { pg.max = c.prog.total || 1; pg.value = c.prog.done; }
    }
  } catch (e) { /* next tick */ }
}
async function cmSync() {
  const c = S.cm; clearInterval(c.timer); c.timer = null;
  if (page !== "commission") return;
  if (!c.opts) { try { c.opts = await api("GET", "/api/v2/cm/options"); if (!c.image && c.opts.images.length) c.image = c.opts.images[0].key; render(); } catch (e) { fail(e); } }
  cmPoll(); c.timer = setInterval(() => { if (!document.hidden && page === "commission") cmPoll(); }, 1500);
}

const VIEWS = { commission: viewCommission, cabinets: viewCabinets, gateway: viewGateway, module: viewModule, soak: viewSoak, firmware: viewFirmware, labels: viewLabels, sites: viewSites, events: viewEvents };
const NAV = ["cabinets", "gateway", "module", "soak", "firmware", "commission", "labels", "sites", "events"];
/* Basic mode hides the pages that change a gateway's settings, write firmware or edit the cabinet list. It is a convenience for whoever holds the phone, not security: the login is what keeps strangers out. */
const ADV_PAGES = new Set(["gateway", "firmware", "commission", "sites"]);
let uiMode = "basic"; try { uiMode = localStorage.getItem("lgs.mode") === "advanced" ? "advanced" : "basic"; } catch (e) { /* storage blocked: basic */ }
const allowed = (k) => uiMode === "advanced" || !ADV_PAGES.has(k);

function render() {
  if (!allowed(page)) { page = "cabinets"; location.hash = "#/cabinets"; toast(t("modeLocked")); }
  $("#nav").innerHTML = NAV.filter(allowed).map((k) => `<button data-nav="${k}" ${k === page ? 'aria-current="page"' : ""}>${t(k === "gateway" ? "gateway_page" : k === "module" ? "module_page" : k === "soak" ? "soak_page" : k === "firmware" ? "firmware_page" : k === "commission" ? "commission_page" : k === "labels" ? "labels_page" : k)}</button>`).join("")
    + `<button data-nav="classic">${t("classic")}</button>`;
  $("#main").innerHTML = (VIEWS[page] || viewCabinets)();
  const cur = $("#nav [aria-current]"); if (cur && cur.scrollIntoView) cur.scrollIntoView({ inline: "center", block: "nearest" });
  $("#stagechip").textContent = t("stage"); $("#infoclose").textContent = t("close");
  settingsText(); themeSelect(); modeSelect();
  document.documentElement.lang = lang;
  if (page === "events") loadEvents();
  if (page === "gateway") gwBar();
  if (page === "module") modAutoSync();
  if (page === "soak" && !S.soak.timer) soakSync();
  if (page === "firmware" && !S.fw.timer) fwSync();
  if (page === "commission" && !S.cm.timer && !S.cm.syncing) { S.cm.syncing = true; cmSync().finally(() => { S.cm.syncing = false; }); }
}

async function loadEvents() {
  try {
    const q = new URLSearchParams({ gw: S.ev.gw, days: S.ev.days, q: S.ev.q, ev: [...S.ev.types].join(",") });
    const r = await api("GET", "/api/v2/events?" + q);
    $("#evcount").textContent = t("matched", { n: r.matched });
    $("#evlist").innerHTML = r.rows.length ? r.rows.map((e) => `<div class="evrow"><span class="when">${esc((e.t || e.collected || "").replace("T", " ").slice(5, 19))}</span><span><b>${esc(e.gw)}</b> ${esc(e.text)}</span></div>`).join("") : `<p class="muted">${t(S.me && S.me.collector && S.me.collector.enabled ? "noEvents" : "noEventsOff")}</p>`;
  } catch (e) { fail(e); }
}

/* ---------- actions ---------- */
async function gwRead() {
  if (!S.gw.id) return;
  S.gw.busy = true; render();
  try { S.gw.data = await api("POST", "/api/v2/gw/read", { id: S.gw.id }); S.gw.data.ok = S.gw.data.ok !== false; }
  catch (e) { S.gw.data = { ok: false, error: e.message }; }
  S.gw.busy = false; render();
}

async function loadSites() { const r = await api("GET", "/api/v2/sites"); S.sites = r.sites; S.warnings = r.warnings; S.layouts = r.layouts; }
function readRows() {
  document.querySelectorAll(".sitesrow").forEach((row) => { const i = +row.dataset.i; row.querySelectorAll("[data-f]").forEach((el) => { S.sites[i][el.dataset.f] = el.value; }); });
}
document.addEventListener("click", async (ev) => {
  const nav = ev.target.closest("[data-nav]");
  if (nav) { if (nav.dataset.nav === "classic") { location.href = "/"; return; } page = nav.dataset.nav; location.hash = "#/" + page; if (page !== "soak") { clearInterval(S.soak.timer); S.soak.timer = null; } if (page !== "firmware") { clearInterval(S.fw.timer); S.fw.timer = null; } if (page !== "commission") { clearInterval(S.cm.timer); S.cm.timer = null; } if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways").catch(() => ({}))).gateways || []; render(); return; }
  const cell = ev.target.closest("[data-cmcell]");
  if (cell) { const id = +cell.dataset.cmcell, c = S.cm; if (c.mode === "batch") { c.sel.has(id) ? c.sel.delete(id) : c.sel.add(id); } else { c.id = String(id); c.gridOpen = false; } render(); return; }
  const crow = ev.target.closest("[data-cmrow]");
  if (crow) { const r = +crow.dataset.cmrow, g = (S.cm.opts && S.cm.opts.grid) || { cols: 8 }, ids = Array.from({ length: g.cols }, (_, k) => r * 10 + k + 1); const all = ids.every((i) => S.cm.sel.has(i)); ids.forEach((i) => (all ? S.cm.sel.delete(i) : S.cm.sel.add(i))); render(); return; }
  document.querySelectorAll("details.menu[open]").forEach((d) => { if (!d.contains(ev.target)) d.open = false; });
  const cmm = ev.target.closest("[data-cmmode]"); if (cmm) { S.cm.mode = cmm.dataset.cmmode; render(); return; }
  const type = ev.target.closest("[data-type]");
  if (type) { const x = type.dataset.type; S.ev.types.has(x) ? S.ev.types.delete(x) : S.ev.types.add(x); type.setAttribute("aria-pressed", S.ev.types.has(x)); loadEvents(); return; }
  const act = ev.target.closest("[data-act]"); if (!act) return;
  try {
    if (act.dataset.act === "check") {
      act.disabled = true; act.textContent = t("checking");
      const r = await api("POST", "/api/v2/health", {}); S.health = r.results; S.checkedAt = new Date().toTimeString().slice(0, 8); render();
    } else if (act.dataset.act === "add") { readRows(); S.sites.push({ id: "", name: "", host: "", port: 502, cabinet: "", site: "", note: "" }); S.dirty = true; render();
    } else if (act.dataset.act === "del") { readRows(); S.sites.splice(+act.dataset.i, 1); S.dirty = true; render();
    } else if (act.dataset.act === "save") { readRows(); const r = await api("PUT", "/api/v2/sites", { sites: S.sites }); S.sites = r.sites; S.warnings = r.warnings; S.dirty = false; render(); toast(t("saved"));
    } else if (act.dataset.act === "gw-read") { await gwRead();
    } else if (act.dataset.act === "gw-clear") { S.gw.edits = {}; render();
    } else if (act.dataset.act === "gw-apply") {
      const n = gwChanged(), g = S.sites.find((x) => x.id === S.gw.id);
      if (!await ask(t("applyQ", { n, g: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/apply", { id: S.gw.id, changes: S.gw.edits });
      if (!r.ok) throw new Error(r.error || "failed");
      S.gw.edits = {}; await gwRead(); toast(r.pending_reboot ? t("needReboot", { k: r.pending_reboot }) : t("applied"));
    } else if (act.dataset.act === "gw-time") {
      const wasSet = S.gw.data && S.gw.data.info && S.gw.data.info["time.set"] === "1";
      if (!wasSet && !await ask(t("clockWarn"))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "time" }); if (!r.ok) throw new Error(r.error); await gwRead(); toast(t("clockSet"));
    } else if (act.dataset.act === "sw-info") { await ask(t(act.dataset.info), true);
    } else if (act.dataset.act === "gw-vol") {
      const on = act.getAttribute("aria-checked") !== "true";
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: act.dataset.name, value: on ? "1" : "0" }); if (!r.ok) throw new Error(r.error); await gwRead();
    } else if (act.dataset.act === "gw-discard") {
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "discard" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-reboot") {
      const g = S.sites.find((x) => x.id === S.gw.id); if (!await ask(t("rebootQ", { n: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "reboot" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-defaults") {
      const g = S.sites.find((x) => x.id === S.gw.id); const typed = await ask(t("defaultsQ", { n: g ? g.name : "" }), false, true); if (typed === null) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "defaults", confirm: typed }); if (!r.ok) throw new Error(r.error); await gwRead(); toast(t("doneOk"));
    } else if (act.dataset.act === "mod-read") { await modRead();
    } else if (act.dataset.act === "mod-coil") {
      if (!S.mod.id) return;
      const latch = !!act.dataset.latch && act.dataset.val === "1";
      if (latch && Date.now() < S.mod.lockUntil) { toast(t("cooldownNote")); return; }
      const r = await api("POST", "/api/v2/mod/coil", { id: S.mod.id, device_id: S.mod.dev, addr: +act.dataset.addr, value: act.dataset.val === "1" });
      if (!r.ok) throw new Error(r.error || "failed");
      if (latch) { S.mod.lockUntil = Date.now() + 2300; document.querySelectorAll("[data-latch]").forEach((b) => { b.disabled = true; setTimeout(() => { b.disabled = false; }, 2300); }); }
      toast(t("sent") + " · " + r.ms + " ms");
    } else if (act.dataset.act === "mod-number") {
      const r = await api("POST", "/api/v2/mod/number", { id: S.mod.id, device_id: S.mod.dev, value: +$("#modnum").value }); if (!r.ok) throw new Error(r.error); toast(t("sent"));
    } else if (act.dataset.act === "soak-all") { S.sites.forEach((x) => S.soak.sel.add(x.id)); render();
    } else if (act.dataset.act === "soak-start") {
      const k = S.soak;
      const r = await api("POST", "/api/v2/soak/start", { ids: [...k.sel], mode: k.mode, picks: k.picks, hours: k.hours, start_at: k.startAt });
      toast(t("sStarted", { n: r.count }) + (r.warnings && r.warnings.length ? " · " + r.warnings[0] : "")); await soakRefresh(); render();
    } else if (act.dataset.act === "soak-stop") {
      if (!await ask(t("sStopQ"))) return; await api("POST", "/api/v2/soak/stop", {}); S.soak.was = true; await soakRefresh();
    } else if (act.dataset.act === "soak-view") {
      const r = await fetch("/api/v2/soak/file?name=" + encodeURIComponent(act.dataset.name)); S.soak.verdict = await r.text(); render();
    } else if (act.dataset.act === "gw-export") {
      const d = S.gw.data; const out = { format: "lgs-gateway-config", version: 2, gateway: d.info["sys.name"] || "", fw: d.info.fw, exported: new Date().toISOString(), settings: {} };
      d.keys.forEach((k) => { if (!k.ro) out.settings[k.key] = k.value; });
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 2)], { type: "application/json" })); a.download = (out.gateway || "gateway") + "-config.json"; a.click();
    } else if (act.dataset.act === "gw-shape") {
      Object.entries(S.gw.data.shape.fix).forEach(([k, v]) => { const cur = S.gw.data.keys.find((x) => x.key === k); if (cur && cur.value !== v) S.gw.edits[k] = v; }); render();
    } else if (act.dataset.act === "lb-preview") {
      const l = S.lab; if (!l.id) return; l.busy = true; render();
      try { l.info = (await api("POST", "/api/v2/labels/preview", { id: l.id, ward: l.ward, serial: l.serial, layout: l.layout, plate: l.plate })).info; } finally { l.busy = false; render(); }
    } else if (act.dataset.act === "lb-file") {
      const l = S.lab; if (!l.id) return;
      const r = await fetch("/api/v2/labels/file", { method: "POST", headers: { "X-LGS": "1", "Content-Type": "application/json" }, body: JSON.stringify({ id: l.id, ward: l.ward, serial: l.serial, layout: l.layout, plate: l.plate }) });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
      const name = (r.headers.get("content-disposition") || "").match(/filename="([^"]+)"/); const a = document.createElement("a"); a.href = URL.createObjectURL(await r.blob()); a.download = name ? name[1] : "label.lbx"; a.click();
    } else if (act.dataset.act === "fw-start") {
      const f = S.fw, im = (f.images && f.images.module.find((x) => x.key === f.image)); if (!f.sel.size || !im) return;
      const cabs = S.sites.filter((x) => f.sel.has(x.id));
      if (!await ask(t("fwStartQ", { n: cabs.length, i: im.label }) + "\n\n" + cabs.map((c) => c.name).join(", "))) return;
      await api("POST", "/api/v2/fw/ota/start", { ids: [...f.sel], image: f.image }); await fwRefresh();
    } else if (act.dataset.act === "fw-cancel") {
      if (!await ask(t("fwCancelQ"))) return; await api("POST", "/api/v2/fw/ota/cancel", {}); await fwRefresh();
    } else if (act.dataset.act === "fw-gwstart") {
      const f = S.fw; if (!f.gwId) return;
      const site = S.sites.find((x) => x.id === f.gwId);
      if (f.gwFile) { await api("POST", `/api/v2/fw/gateway/start?id=${encodeURIComponent(f.gwId)}&confirm=${encodeURIComponent(f.gwConfirm)}&name=${encodeURIComponent(f.gwFileName)}`, f.gwFile, true); }
      else { await api("POST", "/api/v2/fw/gateway/start", { id: f.gwId, confirm: f.gwConfirm, image: f.gwImage }); }
      f.gwConfirm = ""; await fwRefresh();
    } else if (act.dataset.act === "cm-probe") {
      S.cm.probing = true; render(); try { S.cm.probe = await api("POST", "/api/v2/cm/probe", {}); } finally { S.cm.probing = false; render(); }
    } else if (act.dataset.act === "csv-import") {
      const m = act.closest("details"); if (m) m.open = false;
      const mode = await pickImportMode(); if (!mode) return;
      S.csvMode = mode; $("#csvfile").click();
    } else if (act.dataset.act === "cm-info") {
      const im = S.cm.opts && S.cm.opts.images.find((x) => x.key === S.cm.image);
      $("#infobody").innerHTML = im ? `${fwNoteHtml(im)}<dl class="kv"><dt>${t("cmVerLbl")}</dt><dd class="mono">${esc(im.version)}</dd><dt>${t("cmShaLbl")}</dt><dd class="mono">${esc(im.sha256)}</dd></dl>` : `<p>${t("cmNeedImage")}</p>`;
      const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    } else if (act.dataset.act === "cm-clear") { S.cm.sel.clear(); render();
    } else if (act.dataset.act === "cm-cancel") {
      await api("POST", "/api/v2/cm/cancel", {}); await cmPoll();
    } else if (act.dataset.act === "cm-start") {
      S.cm.err = "";
      const c = S.cm; ["cmid", "cmlot"].forEach((k) => { const el = $("#" + k); if (el) c[k.slice(2)] = el.value; });
      if (c.mode === "batch") { c.ids = cmIdsText(); if (!c.sel.size) { toast(t("cmPickFirst")); return; } }
      else if (!c.id) { await ask(t("cmIdNeed"), true); const el = $("#cmid"); if (el) el.focus(); return; }
      const im = c.opts && c.opts.images.find((x) => x.key === c.image);
      if (!c.file && !im) { toast(t("cmNeedImage")); return; }
      const batch = c.mode === "batch";
      const body = { mode: c.mode, image: c.file ? "" : c.image, id: c.id, ids: c.ids, lot: c.lot, device_type: c.type, overwrite: !batch && c.overwrite, confirmed: true };
      if (c.file) { const q = new URLSearchParams({ mode: c.mode, id: c.id, ids: c.ids, lot: c.lot, device_type: c.type, overwrite: body.overwrite ? "1" : "0", confirmed: "1", name: c.fileName }); await api("POST", "/api/v2/cm/start?" + q, c.file, true); }
      else await api("POST", "/api/v2/cm/start", body);
      c.since = 0; c.lines = []; c.done = null; c.prog = null; c.boards = {}; c.running = true; render(); cmPoll();
    } else if (act.dataset.act === "hint") { showInfo(act.dataset.key);
    } else if (act.dataset.act === "collector") { const on = act.getAttribute("aria-checked") !== "true"; await api("POST", "/api/v2/collector", { enabled: on }); S.me = await api("GET", "/api/v2/me"); render(); }
  } catch (e) { if (String(act.dataset.act).startsWith("cm-")) S.cm.err = e.message; fail(e); render(); }
});
document.addEventListener("input", (ev) => {
  if (ev.target.id === "cmid") {
    const el = ev.target, v = el.value;
    if (v === "" || (/^[1-9]\d{0,2}$/.test(v) && +v <= 245)) { S.cm.id = v; }
    else { el.value = S.cm.id; ask(t("cmIdBad"), true).then(() => el.focus()); }
    return;
  }
  if (ev.target.closest(".sitesrow")) { S.dirty = true; }
  if (ev.target.dataset && ev.target.dataset.hubrow !== undefined) {
    const k = "bus.hub_map", orig = hubRows(S.gw.data.keys.find((x) => x.key === k).value).join(",");
    const now = [...document.querySelectorAll("[data-hubrow]")].map((x) => x.value).join(",");
    if (now === orig) delete S.gw.edits[k]; else S.gw.edits[k] = now;
    const saved = orig.split(","); document.querySelectorAll("[data-hubrow]").forEach((x, i) => { x.style.borderColor = x.value !== saved[i] ? "var(--brand)" : ""; });
    gwBar(); return;
  }
  if (ev.target.dataset && ev.target.dataset.key) {
    const k = ev.target.dataset.key, orig = S.gw.data.keys.find((x) => x.key === k).value;
    if (ev.target.value === orig) delete S.gw.edits[k]; else S.gw.edits[k] = ev.target.value;
    ev.target.style.borderColor = k in S.gw.edits ? "var(--brand)" : ""; gwBar();
  }
  if (ev.target.id === "evq") { S.ev.q = ev.target.value; clearTimeout(window._evt); window._evt = setTimeout(loadEvents, 300); }
});
document.addEventListener("change", async (ev) => {
  if (ev.target.id === "modsel") { S.mod.id = ev.target.value; S.mod.data = null; if (S.mod.id) modRead(); }
  if (ev.target.id === "moddev") { S.mod.dev = Math.max(1, Math.min(247, +ev.target.value || 1)); S.mod.data = null; }
  if (ev.target.id === "modstats") { S.mod.stats = ev.target.checked; }
  if (ev.target.id === "modauto") { S.mod.auto = ev.target.checked; modAutoSync(); }
  if (ev.target.id === "gwsel") { S.gw.id = ev.target.value; S.gw.data = null; S.gw.edits = {}; if (S.gw.id) gwRead(); else render(); }
  if (ev.target.dataset && ev.target.dataset.pick) { ev.target.checked ? S.soak.sel.add(ev.target.dataset.pick) : S.soak.sel.delete(ev.target.dataset.pick); }
  if (ev.target.id === "soakmode") S.soak.mode = ev.target.value;
  if (ev.target.id === "soakpicks") S.soak.picks = +ev.target.value;
  if (ev.target.id === "soakhours") S.soak.hours = +ev.target.value;
  if (ev.target.id === "soakat") S.soak.startAt = ev.target.value;
  if (ev.target.id === "lbsel") { S.lab.id = ev.target.value; S.lab.info = null; }
  if (ev.target.id === "lbward") S.lab.ward = ev.target.value;
  if (ev.target.id === "lbserial") S.lab.serial = ev.target.value;
  if (ev.target.id === "lblayout") { S.lab.layout = ev.target.value; S.lab.info = null; }
  if (ev.target.id === "lbplate") { S.lab.plate = ev.target.value; S.lab.info = null; }
  if (ev.target.dataset && ev.target.dataset.fwpick) { ev.target.checked ? S.fw.sel.add(ev.target.dataset.fwpick) : S.fw.sel.delete(ev.target.dataset.fwpick); }
  if (ev.target.id === "cmimage") { S.cm.image = ev.target.value; if (ev.target.value) { S.cm.file = null; S.cm.fileName = ""; render(); } }
  if (ev.target.id === "cmtype") S.cm.type = ev.target.value;
  if (ev.target.id === "cmlot") S.cm.lot = ev.target.value;
  if (ev.target.id === "cmid") S.cm.id = ev.target.value;
  if (ev.target.id === "cmpreset" && ev.target.value && S.cm.opts) { const l = S.cm.opts.layouts.find((x) => x.key === ev.target.value); if (l) { S.cm.sel = new Set(l.ids); render(); } }
  if (ev.target.id === "cmow") { S.cm.overwrite = ev.target.checked; }
  if (ev.target.id === "cmfile" && ev.target.files[0]) { S.cm.file = await ev.target.files[0].arrayBuffer(); S.cm.fileName = ev.target.files[0].name; S.cm.image = ""; render(); }
  if (ev.target.id === "fwimage") S.fw.image = ev.target.value;
  if (ev.target.id === "fwgwsel") S.fw.gwId = ev.target.value;
  if (ev.target.id === "fwgwimage") { S.fw.gwImage = ev.target.value; if (ev.target.value) { S.fw.gwFile = null; S.fw.gwFileName = ""; } }
  if (ev.target.id === "fwgwconfirm") S.fw.gwConfirm = ev.target.value;
  if (ev.target.id === "fwgwfile" && ev.target.files[0]) { S.fw.gwFile = await ev.target.files[0].arrayBuffer(); S.fw.gwFileName = ev.target.files[0].name; S.fw.gwImage = ""; render(); }
  if (ev.target.id === "gwimport" && ev.target.files[0]) {
    try {
      const j = JSON.parse(await ev.target.files[0].text()); const src = j.settings || j; let n = 0;
      S.gw.data.keys.forEach((k) => { if (!k.ro && k.key in src && String(src[k.key]) !== k.value) { S.gw.edits[k.key] = String(src[k.key]); n++; } });
      render(); toast(n ? t("impDone", { n }) : t("impNone"));
    } catch (e) { fail(e); }
  }
  if (ev.target.id === "evgw") { S.ev.gw = ev.target.value; loadEvents(); }
  if (ev.target.id === "evdays") { S.ev.days = +ev.target.value; loadEvents(); }
  if (ev.target.id === "csvfile" && ev.target.files[0]) {
    try {
      const r = await api("POST", "/api/v2/sites/import?mode=" + (S.csvMode || "merge"), await ev.target.files[0].arrayBuffer(), true);
      S.sites = r.sites; S.warnings = r.warnings; S.dirty = false; render(); toast(t("imported", { n: r.imported }));
    } catch (e) { fail(e); }
  }
});
document.addEventListener("keydown", (e) => { if ((e.key === " " || e.key === "Enter") && e.target.matches && e.target.matches(".sw")) { e.preventDefault(); e.target.click(); } });
/* A dropdown menu is nudged back inside the screen when it would run past an edge (a phone is not always as wide as the layout assumes). */
document.addEventListener("toggle", (e) => {
  const d = e.target; if (!d.matches || !d.matches("details.menu") || !d.open) return;
  const p = d.querySelector(".menupanel"); p.style.transform = ""; const r = p.getBoundingClientRect(), over = r.right - (innerWidth - 8);
  if (over > 0) p.style.transform = `translateX(-${over}px)`; else if (r.left < 8) p.style.transform = `translateX(${8 - r.left}px)`;
}, true);
$("#infoclose").onclick = () => $("#info").close();
$("#info").addEventListener("click", (e) => { if (e.target.id === "info") $("#info").close(); });
function settingsText() {
  $("#setbtn").textContent = "⚙"; $("#setbtn").setAttribute("aria-label", t("settings")); $("#setbtn").title = t("settings"); $("#settitle").textContent = t("settings"); $("#setclose").textContent = t("close");
  $("#langlbl").textContent = t("language"); $("#modelbl").textContent = t("mode"); $("#themelbl").textContent = t("theme");
  $("#langsel").value = lang;
}
$("#setbtn").onclick = () => { const d = $("#settings"); if (d.showModal) d.showModal(); else d.setAttribute("open", ""); };
$("#setclose").onclick = () => $("#settings").close();
$("#settings").addEventListener("click", (e) => { if (e.target.id === "settings") $("#settings").close(); });
$("#langsel").onchange = (e) => { lang = e.target.value; try { localStorage.setItem("lgs.lang", lang); } catch (x) { /* not remembered */ } render(); };
const THEMES = ["auto", "light", "dark", "ocean", "forest", "sand", "midnight", "contrast"];
function setTheme(name) {
  const r = document.documentElement;
  if (name === "auto" || !THEMES.includes(name)) r.removeAttribute("data-theme"); else r.dataset.theme = name;
  try { localStorage.setItem("lgs.theme", THEMES.includes(name) ? name : "auto"); } catch (e) { /* not remembered */ }
}
function themeSelect() { const el = $("#themesel"); el.setAttribute("aria-label", t("theme")); el.innerHTML = THEMES.map((n) => `<option value="${n}"${n === themeNow ? " selected" : ""}>${t("th_" + n)}</option>`).join(""); }
let themeNow = "auto"; try { const th = localStorage.getItem("lgs.theme"); if (THEMES.includes(th)) themeNow = th; } catch (e) { /* storage blocked: follow the device */ }
setTheme(themeNow);
function modeSelect() { const el = $("#modesel"); el.setAttribute("aria-label", t("mode")); el.innerHTML = ["basic", "advanced"].map((m) => `<option value="${m}"${m === uiMode ? " selected" : ""}>${t(m)}</option>`).join(""); }
$("#modesel").onchange = (e) => { uiMode = e.target.value; try { localStorage.setItem("lgs.mode", uiMode); } catch (x) { /* not remembered */ } clearInterval(S.fw.timer); S.fw.timer = null; render(); };
$("#themesel").onchange = (e) => { themeNow = e.target.value; setTheme(themeNow); };

(async () => {
  try {
    S.me = await api("GET", "/api/v2/me"); $("#ver").textContent = "v" + S.me.version;
    await loadSites();
    if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways")).gateways || [];
    S.mod.presets = (await api("GET", "/api/v2/mod/presets")).presets;
    S.soak.runs = (await api("GET", "/api/v2/soak/runs")).runs;
    S.lab.opts = await api("GET", "/api/v2/labels/options"); S.lab.layout = S.lab.opts.default_layout; S.lab.plate = S.lab.opts.default_plate;
    S.fw.images = await api("GET", "/api/v2/fw/images"); S.fw.image = (S.fw.images.module[0] || {}).key || "";
  } catch (e) { fail(e); }
  render();
})();
