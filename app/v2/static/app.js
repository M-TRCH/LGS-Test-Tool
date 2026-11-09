/* LGS Test Tool v2 front end, stage 1: Cabinets, Sites, Events. Plain JS, no libraries. */
"use strict";

const TXT = {
  th: {
    stage: "", classic: "แบบเดิม", cabinets: "ตู้", sites: "รายการตู้", events: "เหตุการณ์",
    checkAll: "ตรวจทุกตู้", checking: "กำลังตรวจ...", checkedAt: "ตรวจล่าสุด {at}", notChecked: "ยังไม่ได้ตรวจ",
    noSites: "ยังไม่มีตู้ในรายการ เพิ่มได้ที่หน้า รายการตู้", ok: "ปกติ", warn: "ควรดู", bad: "ผิดปกติ",
    fw: "เฟิร์มแวร์", uptime: "เปิดมาแล้ว", clients: "client", clock: "นาฬิกา", rtu: "ซ่อม RS485 (สะสม)",
    clockUnset: "ยังไม่ตั้ง", repaired: "ซ่อมได้ {n}", failed: "ซ่อมไม่ได้ {n}", badcrc: "CRC เสีย {n}",
    add: "เพิ่มตู้", save: "บันทึก", saved: "บันทึกแล้ว", del: "ลบ", name: "ชื่อตู้", host: "ไอพี / โฮสต์", port: "พอร์ต",
    cabinet: "ชนิดตู้", site: "ไซต์", note: "หมายเหตุ", exportCsv: "ส่งออก CSV", importCsv: "นำเข้า CSV",
    importMerge: "เพิ่มเฉพาะที่ยังไม่มี", importReplace: "แทนที่ทั้งรายการ", imported: "นำเข้า {n} แถว",
    dupWarn: "ไอพีซ้ำกับแถวอื่น", unsaved: "มีการแก้ที่ยังไม่บันทึก", gateway: "เกตเวย์", days: "ย้อนหลัง", evFilters: "ตัวกรอง", evClear: "ล้างทั้งหมด", evType: "ชนิดเหตุการณ์", evNone: "ไม่มีรายการ", evUnitAll: "0 · ทุกโมดูล", evT_panel_sweep: "กวาดไฟหน้าตู้", evT_fw_update: "อัปเดตเฟิร์มแวร์", evT_link_up: "สายแลนเชื่อมต่อ", evT_clock_set: "ตั้งนาฬิกา", evT_coil_dropped: "สั่งไฟที่ไม่ได้บันทึก", evT_collector_start: "เริ่มเก็บข้อมูล", evT_collector_gap: "ข้อมูลขาดช่วง", evRange: "ช่วงวันที่", evTime: "ช่วงเวลา", evTimeFrom: "ตั้งแต่", evTimeTo: "ถึง", evAllDay: "ทั้งวัน", evTimeWrap: "เริ่มหลังเวลาสิ้นสุด จึงนับข้ามเที่ยงคืน เช่น 22:00 – 02:00",  evSize: "ดูทีละ", rangeEnd: "แตะอีกวันเพื่อเลือกเป็นช่วง หรือกดปิดถ้าต้องการวันเดียว", prev: "ก่อนหน้า", next: "ถัดไป", day1: "วันนี้", day7: "7 วัน", day30: "30 วัน", dayAll: "ทั้งหมด", day90: "90 วัน", all: "ทั้งหมด",
    search: "ค้นหา (ชื่อ, ไอพี)", evClient: "ผู้เชื่อมต่อ", evUnit: "โมดูล", noEvents: "ไม่มีเหตุการณ์ในช่วงนี้", noEventsOff: "ยังไม่มีข้อมูล ตัวเก็บเหตุการณ์ปิดอยู่", collect: "เก็บเหตุการณ์อัตโนมัติ",
    dashLights: "สั่งไฟ", dashConn: "เชื่อมต่อ", dashRefused: "ปฏิเสธการเชื่อมต่อ", dashQuiet: "บัสเงียบ", dashHeal: "ซ่อมบัส", dashBoot: "บูต", dashLast: "เหตุการณ์ล่าสุด", dashProblems: "ปัญหา", dashHour: "รายชั่วโมง", dashDay: "รายวัน", dashLightsBy: "จำนวนครั้งที่สั่งไฟ ({u})", dashProblemsBy: "ปัญหา: บัสเงียบ ซ่อมบัส ปฏิเสธการเชื่อมต่อ บูต ({u})", colOff: "ปิดอยู่", colOffNote: "ตัวเก็บเหตุการณ์ปิดอยู่ เปิดได้ที่ ⚙ ตั้งค่า (โหมดขั้นสูง)", colWait: "รออ่านรอบแรก", colChip: "ปกติ {n}/{total} ตู้", colKeep: "เก็บเหตุการณ์ไว้ในเครื่องนี้", colKeepQ: "เหตุการณ์ที่เก่ากว่า {n} วันจะถูกลบในรอบเก็บถัดไป ดำเนินการต่อไหม?", dayN: "{n} วัน", colLast: "อ่านล่าสุด {at} · ปกติ {n}/{total} ตู้ · ได้เพิ่ม {add} รายการ", colOld: "ยังอ่านไม่ได้ เฟิร์มแวร์ต่ำกว่า 1.14.0: {names}", colErr: "{name}: อ่านไม่สำเร็จ ({e})", evT_coil: "สั่งไฟ", evT_tcp_accept: "เชื่อมต่อ", evT_tcp_close: "ตัดการเชื่อมต่อ", evT_tcp_refused: "ปฏิเสธการเชื่อมต่อ", evT_bus_quiet: "บัสเงียบ", evT_rtu_heal: "ซ่อมบัส", evT_boot: "บูต", evT_link_down: "สายแลนหลุด", evT_cfg_saved: "บันทึกค่า", evT_sched_reset: "รีเซ็ตตามเวลา",
    gateway_page: "เกตเวย์", pick: "เลือกตู้", read: "อ่านค่า", reading: "กำลังอ่าน...",
    setClock: "ซิงค์เวลาจากเครื่องนี้", hubRow: "แถว {n}", hubDirect: "ต่อตรง", hubCh: "ช่อง {n}", cabCustom: "กำหนดเอง", cabSlots: "{n} ช่อง", cabNone: "ไม่มี", insFromScan: "จากผลสแกน", jobBusy: "มีงานอื่นกำลังทำงานอยู่ รอให้เสร็จก่อน", scanTitle: "สแกนหาโมดูล", scanExtra: "พบนอกผังตู้:", scanClear: "ล้างค่า", scanQuick: "สแกนตามผังตู้", scanFull: "สแกนทุกไอดี", scanProg: "ถาม ID {id} ({i}/{total})", scanDone: "พบ {n} โมดูล จากที่ถาม {total} ID", rptBtn: "สร้างรายงานไซต์ (PDF)", rptSoakTitle: "ผล soak ในรายงาน (ไม่บังคับ)", rptSoakNone: "ไม่ใส่ผล soak", rptSoakUpload: "อัปโหลดไฟล์ CSV…", rptBuild: "สร้างรายงาน PDF", rptBuilding: "กำลังสร้างรายงาน…", rptSoakHint: "อ่านโมดูลครบแล้ว เลือกรอบ soak ของตู้นี้ที่เก็บไว้ หรืออัปโหลดไฟล์ CSV ของรอบที่ต้องการ แล้วสร้างรายงาน", rptBuilt: "สร้างรายงานแล้ว", rptSoakIn: "ผล soak: {s}", rptProg: "อ่านโมดูล {id} ({i}/{total})", rptDone: "เสร็จ: ตอบสนอง {a}/{n} โมดูล", rptFile: "ดาวน์โหลดรายงาน", dangerTitle: "จัดการโมดูล", setIdBtn: "เปลี่ยนไอดี", setIdAsk: "ไอดีใหม่ของโมดูล {id} ใช้ได้ 1–245 หรือ 247 ต้องไม่ซ้ำโมดูลอื่น โมดูลจะรีบูตหลังเปลี่ยน", setIdRange: "ไอดีต้องเป็นจำนวนเต็ม 1–245 หรือ 247", setIdQ: "เปลี่ยนไอดีโมดูล {from} เป็น {to} แล้วบันทึก โมดูลจะรีบูต ดำเนินการต่อไหม?", setIdBusy: "กำลังเปลี่ยน ID (ราว 5 วินาที)...", setIdDone: "เปลี่ยนเป็น ID {id} แล้ว", resetBtn: "รีเซ็ตซอฟต์แวร์", resetQ: "รีบูตโมดูล {id} พิมพ์ไอดีเพื่อยืนยัน", resetBusy: "กำลังรีบูตโมดูล...", resetDone: "โมดูลกลับมาแล้ว", ntpTitle: "ให้เครื่องนี้เป็น NTP server", ntpChipOn: "ทำงาน · พอร์ต {port}", ntpChipErr: "เปิดไม่ได้", ntpPort: "พอร์ต", pwChipOn: "ตั้งแล้ว", pwChipOff: "ยังไม่ได้ตั้ง", ntpOn: "ทำงานอยู่ที่พอร์ต {port} ตอบไปแล้ว {n} ครั้ง", ntpOff: "ปิดอยู่", ntpErr: "เปิดไม่ได้: {e}", optOn: "เปิด", optOff: "ปิด", ntpUsePc: "ใช้เครื่องนี้", ntpNoIp: "หาไอพีของเครื่องนี้ฝั่งเกตเวย์ไม่เจอ", ntpUseQ: "NTP server ในเครื่องนี้ยังปิดอยู่ เปิดเลยไหม?", pwTitle: "รหัสผ่านหน้าเว็บ", pwOn: "ตั้งรหัสไว้แล้ว", pwOff: "ยังไม่ได้ตั้ง ทุกคนในเครือข่ายเปิดหน้านี้ได้", pwCurrent: "รหัสปัจจุบัน", pwNew: "รหัสใหม่", pwRepeat: "พิมพ์ซ้ำ", pwSet: "ตั้งรหัส", pwClear: "ลบรหัส", pwMismatch: "รหัสสองช่องไม่ตรงกัน", pwShort: "รหัสต้องยาวอย่างน้อย 6 ตัวอักษร", pwClearQ: "ลบรหัสผ่าน ทุกคนในเครือข่ายจะเปิดหน้านี้ได้ ดำเนินการต่อไหม?", insTitle: "ตรวจการติดตั้ง", insPickCab: "เลือกตู้ด้านบนก่อน", insMods: "โมดูลที่จะตรวจ", insStep1: "เลือกแบบการตรวจ", seqLight: "ไฟ", seqLatch: "กลอน", seqIdent: "ระบุตำแหน่ง", seqNone: "ข้าม", pkNum: "เลขบนจอ", pkShow: "แสดงเลขช่อง", pkOff: "ดับไฟเมื่อ", pkOffBtn: "กดปุ่ม", pkOffShut: "กดปุ่มแล้วปิดลิ้นชัก", pkOffDrawer: "ปิดลิ้นชัก", pkBatch: "ไฟติดครั้งละ", pkSlots: "{n} ช่อง", pkAll: "ทุกช่องที่เลือก", pkWait: "รอแต่ละชุดไม่เกิน", pkSec: "{n} วินาที", pkMin: "{n} นาที", pkNoLimit: "ไม่จำกัด", pkGroup: "จัดชุด", pkByCh: "แยกตามช่องฮับ", pkById: "ตามลำดับไอดี", pkRandom: "สุ่ม", insStep2: "เลือกโมดูล", insStep3: "ตั้งค่า", insStep4: "เริ่มตรวจ", insSel: "เลือกแล้ว {n}", insWhole: "ทั้งตู้", insClear: "ล้าง", insModeCheck: "ตรวจทั่วไป", insModePick: "ทดสอบลำดับหยิบยา", insWhat: "จะทำอะไรกับแต่ละโมดูล", insA_skip: "ข้าม (แค่ตรวจว่าตอบสนอง)", insA_light: "เปิดไฟ", insA_light_display: "เปิดไฟ+จอ", insHold: "หน่วงระหว่างชั้น (วินาที)", insIdentify: "ระบุตำแหน่ง", insUnlock: "ปลดกลอนด้วย (กลอนจะทำงานจริง)", insCoil: "จะส่ง coil {coil} ({what})", insWarnUnlock: "รอบนี้จะปลดล็อก {n} โมดูล", insPreset: "พรีเซ็ตสี", insBatch: "จุดพร้อมกัน (ช่อง)", insTimeout: "รอสูงสุดต่อชุด (วินาที)", insPDisplay: "โชว์เลขช่องบนจอ", insPUnlock: "ปลดกลอน (กลอนจะทำงานจริง)", insPClosed: "รอปิดลิ้นชักก่อนดับไฟ", insPBych: "หนึ่งชุดอยู่ช่องฮับเดียว", insRun: "เริ่มตรวจ", insPickRun: "เริ่มเดินทดสอบ", insCancel: "ยกเลิก", insCsv: "บันทึก CSV", insIdle: "ว่าง", insStarting: "กำลังเริ่ม...", insProg: "โมดูล {id} ({i}/{total})", insPrep: "กำลังเปิดไฟช่อง {id} ({i}/{total})", insWaiting: "ไฟติด {n} ช่อง กดปุ่มหน้าช่อง หยิบช่องไหนก่อนก็ได้", insClosing: "รอปิดลิ้นชัก {n} ช่อง, ไฟยังติดอีก {lit} ช่อง", insDone: "เสร็จ {n} โมดูล", insAnswered: "ตอบสนอง {n}/{total}", insMissing: "ไม่ตอบสนอง: {ids}", insFailedIds: "ทำบางขั้นไม่ผ่าน: {ids}", insPass: "✓ ผ่าน", insNoAns: "✗ ไม่ตอบสนอง", insFail: "✗ ไม่ผ่าน", insType: "ชนิด", insResult: "ผล", insDetail: "รายละเอียด", insB_run: "กำลังทำงาน", insB_pass: "ผ่านทั้งหมด", insB_issues: "พบปัญหา", insB_cancelled: "ยกเลิกแล้ว", insPickOne: "เลือกอย่างน้อยหนึ่งโมดูล", insUnlockQ: "รอบนี้จะปลดล็อก {n} โมดูล กลอนจะทำงานจริง ดำเนินการต่อไหม?", cabEmpty: "รูปทรงตู้แบบกำหนดเองต้องมีอย่างน้อยหนึ่งแถวที่มีช่อง", schDays: "วันที่รีเซ็ต", schTimes: "เวลารีเซ็ต", schSlot: "ช่วงที่ {n}", schEvery: "ทุกวัน", schNoTime: "ไม่ได้เปิดช่วงเวลาใด", schName: "ตารางรีเซ็ต", schDay: ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"], schDayS: ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"],
    resyncInfo: "เมื่อโมดูลไม่ตอบ เกตเวย์ส่งสัญญาณปรับจังหวะให้โมดูลทั้งบัสแล้วลองถามซ้ำอีกครั้ง เป็นการตั้งค่าชั่วคราวจะกลับมาเปิดเองหลังรีบูต",
    excInfo: "เมื่อบัส RS485 ไม่ตอบ ให้ตอบไคลเอนต์ด้วย exception 0x0B ทันที แทนที่จะปล่อยให้หมดเวลา เป็นการตั้งค่าชั่วคราวจะกลับมาปิดเองหลังรีบูต", clockWarn: "การตั้งนาฬิกาเป็นการเปิดใช้การรีเซ็ตตามเวลา (เช่น 03:00) ซึ่งตัดไฟเลี้ยงโมดูล ตั้งเมื่อตั้งใจเท่านั้น",
    clockSet: "ตั้งนาฬิกาแล้ว", resync: "ซ่อมจังหวะหลังไม่มีคำตอบ (RESYNC)", exc: "ตอบ exception 0x0B ทันทีเมื่อบัสไม่ตอบ (EXC)",
    volatileNote: "ชั่วคราว: กลับค่าเดิมเมื่อเกตเวย์รีบูต", reboot: "รีบูตเกตเวย์", rebootQ: "รีบูตเกตเวย์ {n}? จะตัดการสื่อสารสักครู่",
    defaults: "คืนค่าโรงงาน", defaultsQ: "คืนค่าโรงงานของ {n}? Ethernet จะปิดและ hub map หาย ต้องตั้งใหม่ พิมพ์ชื่อตู้เพื่อยืนยัน",
    discard: "ทิ้งค่าที่ค้างอยู่", danger: "จัดการเกตเวย์", changes: "{n} ค่าที่แก้", apply: "บันทึกลงเกตเวย์", applyQ: "บันทึก {n} ค่าลง {g}?",
    applied: "บันทึกแล้ว", needReboot: "ต้องรีบูตจึงมีผล: {k}", reset: "ล้างที่แก้", ro: "อ่านอย่างเดียว", rebootKey: "ต้องรีบูต",
    doneOk: "สำเร็จ", noPassword: "ยังไม่ตั้งรหัสผ่านหน้าเว็บ ทุกคนในเครือข่ายแก้ค่าเกตเวย์ได้",
    module_page: "โมดูล", devId: "รหัสโมดูล (ID)", withStats: "รวมสถิติ", auto: "อ่านอัตโนมัติทุก 2 วินาที", modNotRead: "เลือกตู้ ใส่ ID โมดูล แล้วกดอ่านค่า",
    cDevice: "อุปกรณ์", hmFmt: "{h} ชม. {m} นาที", mFmt: "{m} นาที {s} วินาที", mUnlockedAgoK: "ปลดล่าสุด", agoS: "{s} ที่แล้ว", stOn: "เปิดไฟ", stTimes: "{n} ครั้ง", stOnTime: "ไฟติดรวม", stLatch: "ปลดกลอน", stButton: "กดปุ่มยืนยัน", stRun: "เวลาทำงานรวม", stLight: "ไฟ", stTimeCol: "เวลาติด", stOld: "เฟิร์มแวร์โมดูลเก่ากว่า v3.3.0: ตัวนับหยุดที่ 65535", modInfo: "ข้อมูลโมดูล", hOk: "ปกติ", hBad: "มีปัญหา {n}", cRuntime: "การทำงาน", cHealth: "สุขภาพระบบ", cReset: "สาเหตุรีเซ็ตล่าสุด", cTemp: "อุณหภูมิ", cLatch: "กลอน / จอ", cStats: "สถิติ",
    mType: "ชนิด", mFw: "เฟิร์มแวร์", mHw: "ฮาร์ดแวร์", mBaud: "Baud", mUid: "หมายเลขชิป", mUptime: "เปิดมาแล้ว", mBoots: "จำนวนครั้งที่บูต", mMode: "โหมด",
    mPreset: "พรีเซ็ตที่ใช้อยู่", mButton: "กดยืนยันแล้ว", mRoom: "ในห้อง", mBoard: "บนบอร์ด", mCurrent: "กระแสขาเข้า", mLatch: "กลอน", mLocked: "ล็อก", mUnlocked: "ปลดแล้ว",
    mUnlockedAgo: "ปลดล่าสุด {s} วินาทีก่อน", mDisplay: "ตัวเลขบนจอ", na: "ไม่มี", presets: "พรีเซ็ตสี", pLight: "ไฟ", pLightDisp: "ไฟ + เลข", pUnlock: "ปลดกลอน", pUnlockDisp: "ปลดกลอน + เลข", grpLight: "ไฟ", grpLatch: "กลอน", grpDisp: "จอ", grpOther: "อื่น ๆ", cLight: "เปิดไฟ", cLightNum: "เปิดไฟ + เลข", dispOff: "ปิดจอ", qShowAll: "แสดงทั้งหมด", qHidden: "ซ่อนคำสั่งจอและกลอน: โมดูลนี้ไม่มีจอและกลอน", cLightUnlock: "เปิดไฟ + ปลดกลอน", cLightNumUnlock: "เปิดไฟ + เลข + ปลดกลอน", unlockTitle: "ปลดกลอน · เลือกวิธี", unlockSafe: "ปลอดภัย", unlockSafeD: "ปลดเฉพาะเมื่อกลอนล็อกอยู่ ลิ้นชักที่เปิดค้างจะไม่ถูกสั่งซ้ำ", unlockForce: "บังคับ", unlockForceD: "ปลดทันทีโดยไม่ดูสถานะกลอน", colorTitle: "{c} · เลือกสี", colorN: "สี {n}",
    quick: "คำสั่งด่วน", identify: "ระบุตำแหน่ง", allOff: "ดับทั้งหมด", latchSafety: "ปลดกลอน (ปลอดภัย)", latchForce: "ปลดกลอน (บังคับ)", dispPower: "เปิดจอ",
    number: "ตัวเลข", numAsk: "ตัวเลขที่จะแสดงบนจอโมดูล {id}", numRange: "ตัวเลขต้องเป็นจำนวนเต็ม 0 ถึง 9999", writeNumber: "เขียนตัวเลข", cooldownNote: "กลอนต้องเว้น 2.2 วินาทีระหว่างการปลด", sent: "ส่งแล้ว", fires: "ยิงกลอน {c} ครั้ง · {s} วินาที", count: "ครั้ง", seconds: "วินาที",
    soak_page: "ทดสอบต่อเนื่อง", sRepaired: "ซ่อมได้", sRepairedH: "ต่อชม.", sRepairFailed: "ซ่อมไม่ได้", sFinalTo: "timeout สุดท้าย", sBadCrc: "CRC เสีย", sOther: "อื่น ๆ", sDwell: "ค้างไว้ (วินาที)", sWins: "หน้าต่าง", sPicksCol: "การหยิบ", sPicksLive: "pick {n} · lit {lit}", sPicksDropped: "skip {n}", sConc: "ไฟติดพร้อมกันเฉลี่ย {n} ดวง", sThin: "แทบไม่ซ้อนกัน", sCrowded: "เกือบเต็มตู้", sFull: "ไฟจะค้างเต็มตู้ และมีการทิ้งครั้งหยิบ", sDuty: "บัสใช้ ~{pct}% ของวัน", sDutyHot: "สูงกว่าการใช้งานจริงหลายเท่า", sDutyOver: "บัสตามไม่ทัน", sStep1: "เลือกแบบการทดสอบ", sStep2: "เลือกตู้", sStep3: "ตั้งค่า", sStep4: "เริ่มทดสอบ", sNoType: "ยังไม่ได้กำหนดชนิดตู้", sStartLbl: "เริ่ม", sNow: "ทันที", sAtTime: "ตั้งเวลา", sDur: "ทดสอบนาน", sHoursN: "{n} ชั่วโมง", sUntilTime: "จนถึงเวลา", sUntilStop: "จนกว่าจะหยุด", sEndOnStop: "เมื่อกดหยุด", sToday: "วันนี้", sTomorrow: "พรุ่งนี้", sPlan: "เริ่ม {s} · จบ {e}", sCabs: "{n} ตู้", sPickOne: "เลือกอย่างน้อยหนึ่งตู้", sPick: "เลือกตู้ที่จะทดสอบ", sAll: "ทั้งหมด", sMode: "โหมด", sPoll: "อ่านอย่างเดียว", sPharm: "จำลองการจ่ายยา",
    sPicks: "จำนวนครั้งที่จ่ายต่อวัน", sHours: "ชั่วโมง (0 = จนกว่าจะหยุด)", sStartAt: "เริ่มเวลา (เช่น 21:00 เว้นว่าง = ทันที)", sStart: "เริ่มทดสอบ",
    sStop: "หยุด", sStopQ: "หยุดการทดสอบที่กำลังรัน? ข้อมูลถึงตอนนี้ถูกเก็บไว้", sRunning: "กำลังรัน", sArmed: "ตั้งเวลาไว้ เริ่มในอีก {t}", sLeft: "เหลือ {t}",
    sNoEnd: "ไม่มีเวลาจบ", sCab: "ตู้", sState: "สถานะ", sPass: "รอบ", sReads: "อ่าน", sFails: "พลาด", sRbt: "รีบูต", sWdt: "วอตช์ด็อก", sWorst: "ช้าสุด (ms)", sHeal: "เกตเวย์ซ่อมบัส",
    sClean: "สะอาด", sWarn: "ควรดู", sNotClean: "ไม่สะอาด", sDidNot: "ไม่ได้รัน", sStarting: "กำลังเริ่ม", sAnoms: "เหตุผิดปกติล่าสุด", sWriteFail: "err {n}", sAdv: "ตัวเลือกขั้นสูง", sSaveImg: "บันทึกเป็นรูปภาพ", sRawData: "ไฟล์ข้อมูลดิบ", sFmtCsv: "CSV ไฟล์เดียว", sFmtZip: "ZIP แยกไฟล์", sFmtLbl: "รูปแบบ", sRawN: "เลือก {n} จาก {m} ตู้", sDownload: "ดาวน์โหลด", sNoVerdict: "รอบนี้ไม่มีไฟล์สรุป (ไม่ได้จบตามปกติ) แต่ยังมีไฟล์ข้อมูลดิบ", sGap: "พักระหว่างรอบ (วินาที)", sEvery: "อ่านตัวนับทุกกี่รอบ", sSlow: "บันทึกเมื่อตอบช้ากว่า (ms)", sTmo: "timeout ฝั่ง client (วินาที)", sGapWarn: "0.4–0.9 วินาทีทำให้ฮับพลาดการอ่านครั้งแรก และเกิดผล \"โมดูลช้า\" ปลอม", sTmoWarn: "ต่ำกว่า 6 วินาทีอาจทำให้บัสเหลื่อมกันหลังฮับ", sNewer: "ใหม่กว่า", sOlder: "เก่ากว่า", sOfN: "{a}–{b} จาก {n}", sNone: "ไม่มี",
    sVerdict: "สรุปผลรอบล่าสุด", vClean: "สะอาด {a} จาก {b} ตู้", vMeta: "รันนาน {h} ชม. · timeout {to} วินาที", vEarly: "หยุดก่อนเวลา", vGw: "ตัวนับของเกตเวย์", vRestart: "เกตเวย์รีสตาร์ท {n} ครั้ง", vWrong: "เฟรมตอบผิดไอดีถูกทิ้ง {n} ครั้ง", vNoGw: "อ่านตัวนับเกตเวย์ไม่ได้ (ไม่มีคอนโซลหรือเฟิร์มแวร์เก่ากว่า 1.13): {names}", soakColsTxt: "ตารางบน (โมดูลของแต่ละตู้)\n• mod = จำนวนโมดูล\n• pass = รอบที่อ่านครบทุกตัว\n• reads = จำนวนครั้งที่อ่าน\n• fail = อ่านไม่ได้\n• rbt = โมดูลรีบูต\n• wdt = โมดูลถูกวอตช์ด็อกรีเซ็ต\n• cross = ครั้งที่สลับช่องฮับ\n• worst = ตอบช้าสุด (ms)\n• drop = เฟรมตอบผิดไอดีถูกทิ้ง\n• silent = ไอดีที่ไม่ตอบ\n\nตารางล่าง (ตัวนับของเกตเวย์)\n• ซ่อมได้ = พลาดครั้งแรก แต่เกตเวย์ลองใหม่แล้วอ่านได้\n• ซ่อมไม่ได้ = ลองใหม่แล้วยังไม่ได้\n• timeout สุดท้าย = ไม่มีคำตอบเลย\n• CRC เสีย = ตอบมาแต่ข้อมูลเพี้ยน\n• อื่น ๆ = เฟรมแปลกอื่น\n\nสี\n• เทา = ศูนย์\n• เหลือง = ควรดู\n• แดง = ผิดปกติ\n\nถ้าเฟรมตอบผิดไอดีมาก ให้เพิ่ม timeout ฝั่ง client", sHistory: "รอบที่ผ่านมา", sView: "ดูสรุป", sNoRuns: "ยังไม่มีรอบที่ผ่านมา", sFrames: "เฟรมที่ถูกทิ้ง: {n}",
    sNeedType: "ตู้ที่ไม่ได้กำหนดชนิดจะเริ่มไม่ได้ ตั้งที่หน้า รายการตู้", sStarted: "เริ่มแล้ว {n} ตู้", sCsv: "ไฟล์ CSV", sLongNote: "รันบนเซิร์ฟเวอร์ ปิดหน้านี้ได้ ผลเก็บใน data/exports",
    labels_page: "ป้าย", firmware_page: "เฟิร์มแวร์", lbWard: "ชื่อวอร์ด (พิมพ์บนป้าย)", lbSerial: "ซีเรียลจากคลัง (ไม่เก็บ)", lbLayout: "แบบป้าย", lbPlate: "กรอบ",
    lbPreview: "ดูตัวอย่างข้อมูล", lbDownload: "ดาวน์โหลด .lbx", expCfg: "ส่งออก config", impCfg: "นำเข้า config", impDone: "นำเข้า {n} ค่า (ยังไม่บันทึก ตรวจแล้วกดบันทึกลงเกตเวย์)", impNone: "ไม่มีค่าที่ต่างจากเกตเวย์",
    shapeBad: "ชนิดตู้ใน รายการตู้ ({l}) ไม่ตรงกับเกตเวย์: {w}", shapeFix: "ตั้งค่าที่ตรงให้ (ยังไม่บันทึก)", shapeNoFix: "เกตเวย์รุ่นนี้แก้เองไม่ได้ (ไม่มี panel.shape)",
    fwGoP_pick: "เลือกกลุ่ม", fwGoP_probe: "ตรวจโมดูล", fwGoP_metadata: "ส่งข้อมูลไฟล์", fwGoP_enter: "เข้าโหมดรับไฟล์", fwGoP_enter_wait: "รอโมดูลลบพื้นที่", fwGoP_enter_check: "ตรวจการเข้าโหมด", fwGoP_stream: "ส่งไฟล์", fwGoP_repair: "ตรวจก้อนที่ขาด", fwGoP_repair_send: "ส่งก้อนที่ขาดซ้ำ", fwGoP_finalize: "ให้โมดูลตรวจไฟล์", fwGoP_finalize_wait: "รอตรวจไฟล์", fwGoP_finalize_check: "อ่านผลตรวจ", fwGoP_apply: "สั่งใช้ไฟล์", fwGoP_apply_wait: "รอโมดูลรีบูต", fwGoP_apply_confirm: "ยืนยันเวอร์ชันใหม่", fwGoP_waiting_for_quiet: "รอจังหวะที่ไม่มีคนใช้", 
    fwGo: "อัปเดตโมดูล – เกตเวย์ทำงานเบื้องหลัง", fwGoNote: "เกตเวย์อ่านไฟล์จากคลังของตัวเอง ส่งในช่วงที่บัสว่าง และหยุดพักเองเมื่อมีคำสั่งเข้ามา เริ่มแล้วปิด Tool ได้", fwGoImage: "ไฟล์ในคลัง", fwGoNoImage: "เลือกตู้ก่อน หรือคลังของตู้นั้นยังว่าง", fwGoStart: "เริ่มให้เกตเวย์อัปเดต", fwGoStartQ: "ให้เกตเวย์ {n} ตู้อัปเดตโมดูลด้วย {i}?", fwGoStartNote: "โมดูลจะรีบูตทีละตัวตอนที่ไม่มีคนใช้", fwGoAbort: "หยุด", fwGoAbortQ: "สั่งหยุดการอัปเดตของ {n} ตู้?", fwGoResult: "ดูผล", fwGoAdv: "ตัวเลือกขั้นสูง", fwGoIdle: "บัสว่างก่อนส่ง (วินาที)", fwGoGroup: "โมดูลต่อรอบ", fwGoApplyIdle: "บัสว่างก่อนรีบูตโมดูล (วินาที)", fwGoApplyQuiet: "โมดูลไม่ถูกสั่งมานาน (วินาที)", fwGoCab: "ตู้", fwGoState: "สถานะ", fwGoPhase: "ขั้นตอน", fwGoProg: "ความคืบหน้า", fwGoWait: "รออัปเดต", fwGoDone: "อัปเดตแล้ว", fwGoFail: "ไม่สำเร็จ", fwGoPaused: "พักมา (วินาที)", fwGoS_running: "กำลังทำ", fwGoS_scheduled: "รอช่วงเวลา", fwGoSched: "อัปเดตแบบตั้งเวลา", fwGoSchedTitle: "อัปเดตแบบตั้งเวลา", fwGoSchedOk: "เริ่มตามเวลา", fwGoWin: "ช่วงเวลา {a}–{u} ทุกวันจนเสร็จ", fwGoAt: "เริ่ม", fwGoUntil: "สิ้นสุด", fwGoGate_open: "เปิด", fwGoGate_closed: "ปิด", fwGoGate_ending: "ใกล้หมดช่วง", fwGoGate_reset_hold: "เว้นช่วง reset", fwGoS_done_ok: "เสร็จ", fwGoS_done_with_failures: "เสร็จ มีที่ไม่สำเร็จ", fwGoS_aborted: "หยุดแล้ว", fwGoS_interrupted: "ถูกขัดจังหวะ", fwGoS_none: "ไม่เคยรัน", fwGoS_unreachable: "ต่อไม่ได้", fwGoS_unsupported: "เฟิร์มแวร์เก่า ไม่รองรับ", fwGoStarted: "เริ่มแล้ว {n} ตู้", fwGoSkipped: "{n} ตู้เริ่มไม่ได้: {why}", fwGoMod: "โมดูล", fwGoFw: "เฟิร์มแวร์", fwGoErr: "รหัสผิดพลาด", 
    fwDpRefresh: "รีเฟรช", fwDpSend: "กำลังส่งไฟล์",fwOpKeep: "กำลังอ่านไฟล์จากเกตเวย์มาเก็บไว้ใน Tool...", fwOpDel: "กำลังลบไฟล์ออกจากเกตเวย์...", fwOpLoad: "กำลังอ่านรายการจากเกตเวย์...",fwDpStarting: "กำลังเริ่มส่ง...", fwDpSending: "กำลังส่งไฟล์ {p}% · {a} / {b} ไบต์", fwDpVerify: "ส่งครบแล้ว เกตเวย์กำลังตรวจ CRC และบันทึก",
    fwDepot: "คลังเฟิร์มแวร์โมดูลบนเกตเวย์", fwDepotNote: "ฝากไฟล์อัปเดตโมดูลไว้ในเกตเวย์ แล้วอัปเดตภายหลังจากเครื่องอื่นได้ โดยเครื่องที่สั่งไม่ต้องมีไฟล์", fwDpPut: "อัปโหลดลงเกตเวย์", fwDpBusy: "กำลังอัปโหลดไฟล์…", fwDpSlot: "ช่อง", fwDpName: "ชื่อไฟล์", fwDpSize: "ขนาด", fwDpState: "สถานะ", fwDpEmpty: "ว่าง", fwDpPartial: "ไม่สมบูรณ์", fwDpOk: "สมบูรณ์", fwDpDel: "ลบ", fwDpKeep: "ดาวน์โหลด", fwDpKept: "เก็บไว้ใน Tool แล้ว: {n}", fwKeptTitle: "ไฟล์ที่ดาวน์โหลดไว้", fwKeptDelQ: "ลบ {n} ออกจาก Tool?", fwKeptNone: "ยังไม่มี", fwDpDelQ: "ลบ {n} ออกจากคลังของ {g}?", fwDpDone: "อัปโหลด {n} ลง {g} แล้ว", fwSrc: "ที่มาของไฟล์", fwSrcBundle: "ไฟล์ในเครื่องมือ", fwSrcDepot: "อ่านจากคลังของเกตเวย์", fwSrcGw: "เกตเวย์ที่ถือไฟล์", fwSrcNone: "คลังนี้ยังไม่มีไฟล์ที่สมบูรณ์", fwOta: "อัปเดตโมดูล – ผ่าน OTA", fwOtaNote: "Tool ส่งไฟล์ให้โมดูลเองผ่านเกตเวย์ ต้องเปิด Tool ค้างไว้จนจบ ตู้ที่เลือกจะใช้งานไม่ได้ระหว่างอัปเดต", fwImage: "ไฟล์เฟิร์มแวร์", fwStart: "เริ่มอัปเดต", fwCancel: "ยกเลิก", fwCancelQ: "ยกเลิกการอัปเดต? โมดูลที่ค้างอยู่ในเซสชันอาจต้องอัปเดตซ้ำ",
    fwStartQ: "อัปเดตเฟิร์มแวร์โมดูลทุกตัวใน {n} ตู้ด้วย {i}? ทำย้อนจากหน้านี้ไม่ได้ ตู้ที่ใช้งานอยู่จะใช้ไม่ได้ระหว่างอัปเดต", fwRun: "กำลังอัปเดต", fwNoOta: "ยังไม่มีอิมเมจ OTA ในโปรแกรมนี้",
    fwGw: "อัปเดตเฟิร์มแวร์เกตเวย์", fwUpload: "หรืออัปโหลดไฟล์ .bin", fwConfirm: "พิมพ์ชื่อตู้เพื่อยืนยัน", fwConfirmHint: "ชื่อตู้",
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
    theme: "ธีม", th_auto: "ตามเครื่อง", th_light: "สว่าง", th_dark: "มืด", th_ocean: "ทะเล", th_forest: "ป่า", th_sand: "ทราย", th_ember: "ถ่านไฟ", th_rose: "กุหลาบ", th_lavender: "ลาเวนเดอร์", th_graphite: "กราไฟต์",
    lbPicture: "ตัวอย่างป้าย", lbPicNote: "ภาพจากไฟล์ .lbx จริง QR เป็นตัวจริง ฟอนต์ตรงกับไฟล์เมื่อเครื่องที่เปิดมีฟอนต์ Arial และ Browallia New",
    sCsvFiles: "ไฟล์ข้อมูล",
    close: "ปิด", noExplain: "ยังไม่มีคำอธิบายสำหรับค่านี้", curValue: "ค่าปัจจุบัน", newValue: "ค่าที่กำลังแก้",
    matched: "พบ {n} รายการ", evExport: "ส่งออก CSV", loginAgain: "ต้องเข้าสู่ระบบอีกครั้ง", error: "ผิดพลาด: {e}", d: "วัน", h: "ชม.",
  },
  en: {
    stage: "", classic: "Classic UI", cabinets: "Cabinets", sites: "Sites", events: "Events",
    checkAll: "Check all", checking: "Checking...", checkedAt: "Last checked {at}", notChecked: "Not checked yet",
    noSites: "No cabinets saved yet. Add them on the Sites page.", ok: "OK", warn: "Look", bad: "Fault",
    fw: "Firmware", uptime: "Up for", clients: "Clients", clock: "Clock", rtu: "RS485 repairs (total)",
    clockUnset: "not set", repaired: "{n} repaired", failed: "{n} failed", badcrc: "{n} bad CRC",
    add: "Add cabinet", save: "Save", saved: "Saved", del: "Delete", name: "Name", host: "IP / host", port: "Port",
    cabinet: "Cabinet type", site: "Site", note: "Note", exportCsv: "Export CSV", importCsv: "Import CSV",
    importMerge: "Add only new rows", importReplace: "Replace the list", imported: "Imported {n} rows",
    dupWarn: "same address as another row", unsaved: "Unsaved changes", gateway: "Gateway", days: "Range", evFilters: "Filters", evClear: "Clear all", evType: "Event type", evNone: "Nothing here", evUnitAll: "0 · all modules", evT_panel_sweep: "Panel sweep", evT_fw_update: "Firmware update", evT_link_up: "Link up", evT_clock_set: "Clock set", evT_coil_dropped: "Light commands not logged", evT_collector_start: "Collection started", evT_collector_gap: "Data gap", evRange: "Date range", evTime: "Time of day", evTimeFrom: "From", evTimeTo: "To", evAllDay: "All day", evTimeWrap: "From is later than to, so this runs past midnight, e.g. 22:00 – 02:00",  evSize: "Show", rangeEnd: "Tap another day for a range, or close for a single day", prev: "Previous", next: "Next", day1: "Today", day7: "7 days", day30: "30 days", dayAll: "All", day90: "90 days", all: "All",
    search: "Search (name, IP)", evClient: "Client", evUnit: "Module", noEvents: "No events in this range", noEventsOff: "No data yet: the event collector is off", collect: "Collect events automatically",
    dashLights: "Light commands", dashConn: "Connections", dashRefused: "Refused", dashQuiet: "Bus quiet", dashHeal: "Bus repairs", dashBoot: "Boots", dashLast: "Last event", dashProblems: "Problems", dashHour: "per hour", dashDay: "per day", dashLightsBy: "Light commands ({u})", dashProblemsBy: "Problems: bus quiet, repairs, refused, boots ({u})", colOff: "Off", colOffNote: "The event collector is off; switch it on in ⚙ Settings (advanced mode).", colWait: "waiting for the first read", colChip: "{n}/{total} OK", colKeep: "Keep on this PC", colKeepQ: "Events older than {n} days will be deleted at the next collection. Continue?", dayN: "{n} days", colLast: "Last read {at} · {n}/{total} OK · {add} new", colOld: "Not readable, firmware older than 1.14.0: {names}", colErr: "{name}: read failed ({e})", evT_coil: "Coil", evT_tcp_accept: "Connect", evT_tcp_close: "Disconnect", evT_tcp_refused: "Refused", evT_bus_quiet: "Bus quiet", evT_rtu_heal: "Bus repair", evT_boot: "Boot", evT_link_down: "Link down", evT_cfg_saved: "Settings saved", evT_sched_reset: "Scheduled reset",
    gateway_page: "Gateway", pick: "Choose cabinet", read: "Read", reading: "Reading...",
    setClock: "Sync time from this PC", hubRow: "Row {n}", hubDirect: "Direct", hubCh: "Channel {n}", cabCustom: "Custom", cabSlots: "{n} slots", cabNone: "None", insFromScan: "From the scan", jobBusy: "Another job is running; wait for it to finish", scanTitle: "Scan for modules", scanExtra: "Found outside the layout:", scanClear: "Clear", scanQuick: "Scan the cabinet layout", scanFull: "Scan every id", scanProg: "asking id {id} ({i}/{total})", scanDone: "found {n} module(s) out of {total} ids asked", rptBtn: "Site report (PDF)", rptSoakTitle: "Soak result in the report (optional)", rptSoakNone: "No soak result", rptSoakUpload: "Upload a CSV…", rptBuild: "Build the PDF", rptBuilding: "Building the report…", rptSoakHint: "The modules are read. Pick one of this cabinet's saved soak runs, or upload the CSV of the run you want, then build the report.", rptBuilt: "Report built", rptSoakIn: "Soak result: {s}", rptProg: "reading module {id} ({i}/{total})", rptDone: "done: {a}/{n} modules answered", rptFile: "Download report", dangerTitle: "Module management", setIdBtn: "Change id", setIdAsk: "New id for module {id}: 1-245 or 247, not used by another module. The module reboots after the change.", setIdRange: "The id must be a whole number, 1-245 or 247", setIdQ: "Change module {from} to id {to} and save it? The module reboots.", setIdBusy: "Changing the id (about 5 s)...", setIdDone: "Now at id {id}", resetBtn: "Software reset", resetQ: "Reboot module {id}. Type the id to confirm.", resetBusy: "Rebooting the module...", resetDone: "The module is back", ntpTitle: "This PC as NTP server", ntpChipOn: "on · port {port}", ntpChipErr: "cannot start", ntpPort: "Port", pwChipOn: "set", pwChipOff: "not set", ntpOn: "serving on port {port}, {n} answer(s) so far", ntpOff: "off", ntpErr: "cannot start: {e}", optOn: "On", optOff: "Off", ntpUsePc: "Use this PC", ntpNoIp: "cannot tell this PC's address toward the gateway", ntpUseQ: "The NTP server on this PC is off. Switch it on?", pwTitle: "Web password", pwOn: "a password is set", pwOff: "not set: anyone on the network can open this page", pwCurrent: "Current password", pwNew: "New password", pwRepeat: "Repeat", pwSet: "Set password", pwClear: "Remove password", pwMismatch: "the two passwords differ", pwShort: "at least 6 characters", pwClearQ: "Remove the password? Anyone on the network will be able to open this page.", insTitle: "Installation check", insPickCab: "Pick a cabinet above first", insMods: "Modules to check", insStep1: "Choose the check", seqLight: "Light", seqLatch: "Latch", seqIdent: "Identify", seqNone: "Skip", pkNum: "Number on display", pkShow: "Show the slot number", pkOff: "Light goes out on", pkOffBtn: "Button press", pkOffShut: "Button, then drawer shut", pkOffDrawer: "Drawer shut", pkBatch: "Light at a time", pkSlots: "{n} slots", pkAll: "All selected", pkWait: "Wait per batch", pkSec: "{n} s", pkMin: "{n} min", pkNoLimit: "No limit", pkGroup: "Batches", pkById: "By id order", pkByCh: "By hub channel", pkRandom: "Random", insStep2: "Choose modules", insStep3: "Settings", insStep4: "Run", insSel: "{n} selected", insWhole: "Whole cabinet", insClear: "Clear", insModeCheck: "General check", insModePick: "Pick walkthrough", insWhat: "What to do on each module", insA_skip: "Skip (only check it answers)", insA_light: "Light", insA_light_display: "Light + display", insHold: "Delay between steps (s)", insIdentify: "Identify", insUnlock: "Also throw the latch (it really moves)", insCoil: "will send coil {coil} ({what})", insWarnUnlock: "this run will unlock {n} module(s)", insPreset: "Colour preset", insBatch: "Light together (slots)", insTimeout: "Timeout per batch (s)", insPDisplay: "Show the slot number", insPUnlock: "Release the latch (it really moves)", insPClosed: "Wait for the drawer to close", insPBych: "Keep a batch on one hub channel", insRun: "Run check", insPickRun: "Start walkthrough", insCancel: "Cancel", insCsv: "Export CSV", insIdle: "idle", insStarting: "starting...", insProg: "module {id} ({i}/{total})", insPrep: "lighting slot {id} ({i}/{total})", insWaiting: "{n} slots lit: press each slot's button, in any order", insClosing: "{n} waiting to be closed, {lit} still lit", insDone: "done: {n} module(s)", insAnswered: "answered {n}/{total}", insMissing: "no answer: {ids}", insFailedIds: "failed a step: {ids}", insPass: "✓ pass", insNoAns: "✗ no answer", insFail: "✗ fail", insType: "type", insResult: "result", insDetail: "detail", insB_run: "RUNNING", insB_pass: "ALL PASS", insB_issues: "ISSUES FOUND", insB_cancelled: "CANCELLED", insPickOne: "select at least one module", insUnlockQ: "This run will unlock {n} module(s); the latches really move. Continue?", cabEmpty: "A custom cabinet shape needs at least one row with slots", schDays: "Reset days", schTimes: "Reset times", schSlot: "Time {n}", schEvery: "Every day", schNoTime: "No time switched on", schName: "Reset schedule", schDay: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], schDayS: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    resyncInfo: "After a missing reply the gateway re-syncs every module on the bus and retries once. Temporary: returns to on when the gateway reboots.",
    excInfo: "When the RS485 bus does not answer, reply to the client with exception 0x0B at once instead of letting it time out. Temporary: returns to off when the gateway reboots.", clockWarn: "Setting the clock also arms the scheduled reset (e.g. 03:00), which cuts the shelf's power. Do it on purpose only.",
    clockSet: "Clock set", resync: "Re-sync after a missing reply (RESYNC)", exc: "Answer a bus timeout with exception 0x0B at once (EXC)",
    volatileNote: "Temporary: reverts when the gateway reboots", reboot: "Reboot gateway", rebootQ: "Reboot gateway {n}? It will be unreachable for a moment.",
    defaults: "Factory defaults", defaultsQ: "Reset {n} to factory defaults? Ethernet goes off and the hub map is lost; both must be set again. Type the cabinet's name to confirm.",
    discard: "Discard staged edits", danger: "Gateway actions", changes: "{n} changed", apply: "Save to gateway", applyQ: "Save {n} value(s) to {g}?",
    applied: "Saved", needReboot: "Needs a reboot to take effect: {k}", reset: "Clear edits", ro: "read-only", rebootKey: "needs reboot",
    doneOk: "Done", noPassword: "No web password set: anyone on the network can edit the gateway.",
    module_page: "Module", devId: "Module ID", withStats: "Include statistics", auto: "Read automatically every 2 s", modNotRead: "Choose a cabinet, enter a module ID, press Read",
    cDevice: "Device", hmFmt: "{h} h {m} min", mFmt: "{m} min {s} s", mUnlockedAgoK: "Last unlock", agoS: "{s} ago", stOn: "Lit", stTimes: "{n} times", stOnTime: "Total on time", stLatch: "Unlocked", stButton: "Button presses", stRun: "Total run time", stLight: "Light", stTimeCol: "On time", stOld: "Module firmware older than v3.3.0: counters stop at 65535", modInfo: "Module details", hOk: "healthy", hBad: "{n} issue(s)", cRuntime: "Runtime", cHealth: "Health", cReset: "Last reset cause", cTemp: "Temperatures", cLatch: "Latch / display", cStats: "Statistics",
    mType: "Type", mFw: "Firmware", mHw: "Hardware", mBaud: "Baud", mUid: "Chip serial", mUptime: "Uptime", mBoots: "Boots", mMode: "Mode",
    mPreset: "Active preset", mButton: "Confirm presses", mRoom: "Room", mBoard: "Board", mCurrent: "Input current", mLatch: "Latch", mLocked: "locked", mUnlocked: "unlocked",
    mUnlockedAgo: "last unlock {s} s ago", mDisplay: "Display number", na: "n/a", presets: "Colour presets", pLight: "Light", pLightDisp: "Light + number", pUnlock: "Unlock", pUnlockDisp: "Unlock + number", grpLight: "Light", grpLatch: "Latch", grpDisp: "Display", grpOther: "Other", cLight: "Light", cLightNum: "Light + number", dispOff: "Display off", qShowAll: "Show all", qHidden: "Display and latch commands hidden: this module has neither", cLightUnlock: "Light + unlock", cLightNumUnlock: "Light + number + unlock", unlockTitle: "Unlock · choose how", unlockSafe: "Safe", unlockSafeD: "Only when the latch reads locked; an open drawer is left alone", unlockForce: "Force", unlockForceD: "Pulse now, whatever the latch reads", colorTitle: "{c} · pick a colour", colorN: "Colour {n}",
    quick: "Quick commands", identify: "Identify", allOff: "All off", latchSafety: "Unlock (safe)", latchForce: "Unlock (force)", dispPower: "Display on",
    number: "Number", numAsk: "Number to show on module {id}'s display", numRange: "The number must be a whole number from 0 to 9999", writeNumber: "Write number", cooldownNote: "A latch needs 2.2 s between unlocks", sent: "Sent", fires: "{c} fires · {s} s", count: "count", seconds: "seconds",
    soak_page: "Soak", sRepaired: "Repaired", sRepairedH: "per hour", sRepairFailed: "Repair failed", sFinalTo: "Final timeouts", sBadCrc: "Bad CRC", sOther: "Other", sDwell: "Stays lit (seconds)", sWins: "Windows", sPicksCol: "Picks", sPicksLive: "pick {n} · lit {lit}", sPicksDropped: "skip {n}", sConc: "{n} lights on at once on average", sThin: "almost never overlapping", sCrowded: "close to the whole cabinet", sFull: "the cabinet stays full and picks will be dropped", sDuty: "bus use ~{pct}% of the day", sDutyHot: "several times real use", sDutyOver: "the bus cannot keep up", sStep1: "Choose the test", sStep2: "Choose cabinets", sStep3: "Settings", sStep4: "Run", sNoType: "no cabinet type set", sStartLbl: "Start", sNow: "Now", sAtTime: "At a time", sDur: "Run for", sHoursN: "{n} hours", sUntilTime: "Until a time", sUntilStop: "Until stopped", sEndOnStop: "when you stop it", sToday: "today", sTomorrow: "tomorrow", sPlan: "Starts {s} - ends {e}", sCabs: "{n} cabinet(s)", sPickOne: "Choose at least one cabinet", sPick: "Choose the cabinets to test", sAll: "All", sMode: "Mode", sPoll: "Read only", sPharm: "Pharmacy simulation",
    sPicks: "Picks per day", sHours: "Hours (0 = until stopped)", sStartAt: "Start at (e.g. 21:00, empty = now)", sStart: "Start soak",
    sStop: "Stop", sStopQ: "Stop the running soak? Data up to now is kept.", sRunning: "Running", sArmed: "Armed, starts in {t}", sLeft: "{t} left",
    sNoEnd: "no end time", sCab: "Cabinet", sState: "State", sPass: "Passes", sReads: "Reads", sFails: "Fails", sRbt: "Reboots", sWdt: "WDT", sWorst: "Worst ms", sHeal: "Gateway repairs",
    sClean: "clean", sWarn: "look", sNotClean: "not clean", sDidNot: "did not run", sStarting: "starting", sAnoms: "Latest anomalies", sWriteFail: "err {n}", sAdv: "Advanced options", sSaveImg: "Save as image", sRawData: "Raw data files", sFmtCsv: "One CSV", sFmtZip: "ZIP, separate files", sFmtLbl: "Format", sRawN: "{n} of {m} cabinets selected", sDownload: "Download", sNoVerdict: "This run has no summary file (it did not end normally), but its raw data is still here", sGap: "Pause between passes (s)", sEvery: "Read counters every N passes", sSlow: "Log replies slower than (ms)", sTmo: "Client timeout (s)", sGapWarn: "0.4-0.9 s makes the hub lose first reads and creates false slow-module findings", sTmoWarn: "Under 6 s can leave the bus out of step behind a hub", sNewer: "Newer", sOlder: "Older", sOfN: "{a}–{b} of {n}", sNone: "none",
    sVerdict: "Latest run verdict", vClean: "{a} of {b} cabinets clean", vMeta: "ran {h} h · timeout {to} s", vEarly: "stopped early", vGw: "Gateway counters", vRestart: "gateway restarted {n}x", vWrong: "Reply frames discarded as the wrong unit id: {n}", vNoGw: "Gateway counters not available (no console or firmware older than 1.13): {names}", soakColsTxt: "Top table (modules of each cabinet)\n• mod = modules\n• pass = passes that read every module\n• reads = reads\n• fail = failed reads\n• rbt = module reboots\n• wdt = module watchdog resets\n• cross = hub channel crossings\n• worst = slowest reply (ms)\n• drop = reply frames with the wrong unit id, discarded\n• silent = ids that never answered\n\nBottom table (gateway counters)\n• Repaired = missed first try, retried by the gateway and got it\n• Repair failed = retried and still nothing\n• Final timeouts = no reply at all\n• Bad CRC = a reply with damaged data\n• Other = other odd frames\n\nColour\n• grey = zero\n• amber = take a look\n• red = abnormal\n\nIf wrong-id frames are many, raise the client timeout", sHistory: "Past runs", sView: "View verdict", sNoRuns: "No past runs yet", sFrames: "Frames pymodbus discarded: {n}",
    sNeedType: "A cabinet with no type cannot start. Set it on the Sites page.", sStarted: "Started {n} cabinets", sCsv: "CSV files", sLongNote: "Runs on the server: you can close this page. Results go to data/exports.",
    labels_page: "Labels", firmware_page: "Firmware", lbWard: "Ward name (printed)", lbSerial: "Serial from the warehouse (not stored)", lbLayout: "Label layout", lbPlate: "Frame",
    lbPreview: "Preview data", lbDownload: "Download .lbx", expCfg: "Export config", impCfg: "Import config", impDone: "Imported {n} values (not saved yet: review, then Save to gateway)", impNone: "Nothing differs from the gateway",
    shapeBad: "The cabinet type on the Sites page ({l}) does not match the gateway: {w}", shapeFix: "Stage the matching values (not saved yet)", shapeNoFix: "This firmware cannot be told (no panel.shape)",
    fwGoP_pick: "choosing a group", fwGoP_probe: "checking modules", fwGoP_metadata: "sending image info", fwGoP_enter: "entering update mode", fwGoP_enter_wait: "modules erasing", fwGoP_enter_check: "checking update mode", fwGoP_stream: "sending the image", fwGoP_repair: "checking for missing chunks", fwGoP_repair_send: "re-sending missing chunks", fwGoP_finalize: "modules checking the image", fwGoP_finalize_wait: "waiting for the check", fwGoP_finalize_check: "reading the check", fwGoP_apply: "applying", fwGoP_apply_wait: "module rebooting", fwGoP_apply_confirm: "confirming the new version", fwGoP_waiting_for_quiet: "waiting for a quiet moment", 
    fwGo: "Module update – gateway works in the background", fwGoNote: "The gateway reads the image from its own depot, sends it in the gaps of the bus and pauses by itself when a request arrives. Once started the tool can be closed.", fwGoImage: "Image in the depot", fwGoNoImage: "Choose a cabinet first, or its depot is empty", fwGoStart: "Start on the gateways", fwGoStartQ: "Have the gateways of {n} cabinets update their modules with {i}?", fwGoStartNote: "Modules reboot one at a time while nobody is using them.", fwGoAbort: "Stop", fwGoAbortQ: "Stop the update on {n} cabinets?", fwGoResult: "Result", fwGoAdv: "Advanced options", fwGoIdle: "Bus quiet before sending (s)", fwGoGroup: "Modules per round", fwGoApplyIdle: "Bus quiet before a module reboots (s)", fwGoApplyQuiet: "Module not written for (s)", fwGoCab: "Cabinet", fwGoState: "State", fwGoPhase: "Step", fwGoProg: "Progress", fwGoWait: "Waiting to apply", fwGoDone: "Updated", fwGoFail: "Failed", fwGoPaused: "Paused for (s)", fwGoS_running: "running", fwGoS_scheduled: "waiting for the window", fwGoSched: "Update at set times", fwGoSchedTitle: "Update at set times", fwGoSchedOk: "Start", fwGoWin: "Window {a}–{u}, every day until done", fwGoAt: "From", fwGoUntil: "Until", fwGoGate_open: "open", fwGoGate_closed: "closed", fwGoGate_ending: "ending soon", fwGoGate_reset_hold: "holding for the reset", fwGoS_done_ok: "done", fwGoS_done_with_failures: "done, some failed", fwGoS_aborted: "stopped", fwGoS_interrupted: "interrupted", fwGoS_none: "never run", fwGoS_unreachable: "unreachable", fwGoS_unsupported: "old firmware, not supported", fwGoStarted: "Started on {n} cabinets", fwGoSkipped: "{n} cabinets could not start: {why}", fwGoMod: "Module", fwGoFw: "Firmware", fwGoErr: "Error code", 
    fwDpRefresh: "Refresh", fwDpSend: "Sending file",fwOpKeep: "Reading the file from the gateway to keep it in the Tool...", fwOpDel: "Deleting the file from the gateway...", fwOpLoad: "Reading the list from the gateway...",fwDpStarting: "Starting...", fwDpSending: "Sending {p}% · {a} / {b} bytes", fwDpVerify: "Sent. The gateway is checking the CRC and saving it",
    fwDepot: "Module firmware stored on the gateway", fwDepotNote: "Leave a module update file in the gateway, then update later from another PC that does not have the file", fwDpPut: "Upload to gateway", fwDpBusy: "Uploading the file…", fwDpSlot: "Slot", fwDpName: "File", fwDpSize: "Size", fwDpState: "State", fwDpEmpty: "empty", fwDpPartial: "incomplete", fwDpOk: "complete", fwDpDel: "Delete", fwDpKeep: "Download", fwDpKept: "Kept in the tool: {n}", fwKeptTitle: "Downloaded images", fwKeptDelQ: "Remove {n} from the tool?", fwKeptNone: "None yet", fwDpDelQ: "Delete {n} from {g}?", fwDpDone: "{n} put on {g}", fwSrc: "Image source", fwSrcBundle: "Bundled with the tool", fwSrcDepot: "Read from a gateway", fwSrcGw: "Gateway holding the image", fwSrcNone: "This gateway holds no complete image", fwOta: "Module update – over OTA", fwOtaNote: "The tool sends the image to the modules through the gateway and must stay open until it finishes. The chosen cabinets are unusable while updating.", fwImage: "Firmware file", fwStart: "Start update", fwCancel: "Cancel", fwCancelQ: "Cancel the update? Modules left in a session may need updating again.",
    fwStartQ: "Update the firmware of every module in {n} cabinets with {i}? This cannot be undone from this page, and cabinets in use are unusable during the update.", fwRun: "Updating", fwNoOta: "No OTA image is bundled in this build",
    fwGw: "Gateway firmware update", fwUpload: "or upload a .bin file", fwConfirm: "Type the cabinet's name to confirm", fwConfirmHint: "Cabinet name",
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
    theme: "Theme", th_auto: "Follow device", th_light: "Light", th_dark: "Dark", th_ocean: "Ocean", th_forest: "Forest", th_sand: "Sand", th_ember: "Ember", th_rose: "Rose", th_lavender: "Lavender", th_graphite: "Graphite",
    lbPicture: "Label preview", lbPicNote: "Drawn from the real .lbx with the real QR. Fonts match the file when this device has Arial and Browallia New.",
    sCsvFiles: "Data files",
    close: "Close", noExplain: "No explanation for this setting yet", curValue: "Current value", newValue: "Value being edited",
    matched: "{n} found", evExport: "Export CSV", loginAgain: "Sign in again", error: "Error: {e}", d: "d", h: "h",
  },
};
let lang = (localStorage.getItem("lgs.lang") || "th");
const t = (k, p) => { let s = (TXT[lang] && TXT[lang][k]) || TXT.en[k] || k; for (const a in (p || {})) s = s.replace("{" + a + "}", p[a]); return s; };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: new Set(), types: new Set(), client: new Set(), unit: new Set(), from: "", to: "", tfrom: "00:00", tto: "23:59", page: 0, size: 10, facets: null, open: new Set() }, gw: { id: "", data: null, edits: {}, busy: false }, lab: { id: "", ward: "", serial: "", layout: "", plate: "", opts: null, info: null, busy: false }, fw: { images: null, sel: new Set(), image: "", go: { sel: new Set(), image: "", names: [], adv: false, opts: { idle: 5, group: 8, apply_idle: 5, apply_quiet: 300 }, nightAt: "01:00", nightUntil: "04:00", rows: null, at: 0, busy: false }, src: "bundle", srcId: "", srcSlots: null, srcSlot: -1, dp: { id: "", slots: null, image: "", file: null, fileName: "", busy: false }, ota: null, gwId: "", gwImage: "", gwConfirm: "", gwFile: null, gwFileName: "", gw: null, timer: null }, soak: { view: null, gap: 2, every: 5, slow: 400, tmo: 6, adv: false, anP: 0, sel: new Set(), mode: "pharmacy", picks: 2000, dwell: 20, windows: 8, est: null, durMode: "hours", hours: 8, startMode: "now", sh: 21, sm: 0, eh: 8, em: 0, status: null, runs: [], timer: null, was: false }, mod: { id: "", dev: 11, data: null, busy: false, auto: false, stats: false, presets: [], lockUntil: 0 },
  ins: { id: "", layout: null, sel: new Set(), mode: "check", action: "light", unlock: false, identify: false, hold: 1, preset: 1, batch: 4, timeout: 60, display: true, punlock: true, off: "btnshut", order: "ch", running: false, since: 0, res: {}, rows: [], lit: new Set(), closing: new Set(), testing: null, text: "", banner: "", summary: "", file: false, err: "" },
  scan: { running: false, found: [], asked: new Set(), at: 0, text: "", err: "", file: false },
  rpt: { id: "", running: false, text: "", err: "", file: false, ready: false, soaks: [], soak: "", upName: "", upText: "", building: false, built: false, note: "" },
  jobSince: 0, jobTimer: null, jobResumed: false };
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
/* ask(text) -> true/false; ask(text, true) is an alert; ask(text, false, true) also wants something typed and resolves with it, or null if cancelled;
   hint is the grey example shown in the empty field. */
/* The set-times popup of the background module update: start time and end time (the end may be earlier than the start:
   the window then runs past midnight); there is no number of days, it goes on every day until it is done. Resolves {at, until, nights} on OK, or null when dismissed. */
function askSchedule(go) {
  return new Promise((resolve) => {
    const d = $("#schedpick"), pad = (n) => String(n).padStart(2, "0");
    const sel = (p, n, v) => `<select data-p="${p}">${Array.from({ length: n }, (_, i) => `<option value="${i}"${i === v ? " selected" : ""}>${pad(i)}</option>`).join("")}</select>`;
    const [ah, am] = (go.nightAt || "01:00").split(":").map(Number), [uh, um] = (go.nightUntil || "04:00").split(":").map(Number);
    $("#sctitle").textContent = t("fwGoSchedTitle");
    $("#scinfo").setAttribute("aria-label", t("explain")); $("#scok").textContent = t("fwGoSchedOk"); $("#scno").textContent = t("askNo");
    $("#scbody").innerHTML = [["fwGoAt", "a", ah, am], ["fwGoUntil", "u", uh, um]].map(([k, p, h, m]) => `<div class="tmrow"><span class="small muted">${t(k)}</span>${sel(p + "h", 24, h)}<b>:</b>${sel(p + "m", 60, m)}</div>`).join("");
    const v = (p) => pad(+$(`#scbody [data-p="${p}"]`).value);
    const read = () => ({ at: `${v("ah")}:${v("am")}`, until: `${v("uh")}:${v("um")}` });
    const valid = () => { const w = read(); return w.at !== w.until; };
    const sum = () => { $("#scok").disabled = !valid(); };
    $("#scbody").onchange = sum;
    sum();
    const done = (v) => { d.onclose = null; if (d.open) d.close(); resolve(v); };
    $("#scok").onclick = () => done(valid() ? read() : null); $("#scno").onclick = () => done(null); d.onclose = () => resolve(null);
    if (d.showModal) d.showModal(); else d.setAttribute("open", "");
  });
}
function ask(text, alertOnly, typed, hint) {
  return new Promise((resolve) => {
    const d = $("#ask"), inp = $("#askin"); inp.hidden = !typed; inp.value = ""; inp.placeholder = hint || ""; $("#asktext").textContent = text; $("#askok").textContent = t("askOk"); $("#askno").textContent = t("askNo"); $("#askno").hidden = !!alertOnly;
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

/* The collector's last poll as one chip: green when every gateway was read, amber when some were not; it opens the details. */
function colChip(c) {
  const all = Object.values(c.status || {}), ok = all.filter((r) => r.ok).length;
  return !c.enabled ? `<span class="chip off">${t("colOff")}</span>`
    : !all.length ? `<span class="chip off">${t("colWait")}</span>`
    : `<button class="chip ${ok === all.length ? "ok" : "warn"}" data-act="col-status" type="button"><i class="dot"></i>${t("colChip", { n: ok, total: all.length })}</button>`;
}
function viewEvents() {
  const c = (S.me && S.me.collector) || {};
  if (!S.ev.from) S.ev.from = S.ev.to = ymd(new Date());
  return `<div class="evpage"><div class="row" style="gap:10px;align-items:center"><h1>${t("events")}</h1>${colChip(c)}</div>
    ${c.enabled ? "" : `<div class="notice info">${t("colOffNote")}</div>`}
    <div class="evlayout">
      <aside class="evfilters card" id="evfilters">${filterPanel()}</aside>
      <div class="evmain">
        <div class="fchips" id="evchips" hidden></div>
        <div id="evdash" class="stack"></div>
        <section class="card stack">
          <div class="row between"><div class="small muted" id="evcount"></div><div class="row" style="gap:10px"><label class="small muted" for="evsize">${t("evSize")}</label><select id="evsize">${[10, 20, 50, 100].map((n) => `<option value="${n}"${n === S.ev.size ? " selected" : ""}>${n}</option>`).join("")}</select><a class="btn" id="evcsv" href="#" download>${t("evExport")}</a></div></div>
          <div id="evlist"></div><div class="row between" id="evpager"></div>
        </section>
      </div>
    </div></div>`;
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
    4: ["รีเซ็ตไฟเลี้ยงโมดูล", "Reset the shelf power"], 5: ["ทดสอบไฟสถานะ", "Test the status lamps"], 6: ["เปิดไฟทุกช่อง (8 สี)", "Light every slot (8 colours)"] };
  const out = { 0: ["ไม่ใช้", "Not used"], 1: ["พร้อมใช้งาน", "Ready"], 2: ["กำลังทำงาน", "Busy"], 3: ["ผิดปกติ", "Fault"], 4: ["สาย LAN เชื่อมอยู่", "LAN up"],
    5: ["มีไคลเอนต์เชื่อมอยู่", "A client is connected"], 6: ["กำลังไล่ช่อง", "A sweep is running"], 7: ["กำลังตัดไฟเลี้ยงโมดูล", "Shelf power is dropped"], 8: ["ไฟเลี้ยงโมดูล", "Shelf power"] };
  const m = { "rs485.baud": { 9600: ["9600", "9600"], 19200: ["19200", "19200"], 38400: ["38400", "38400"], 57600: ["57600", "57600"] },
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
function gwChanged() { return new Set(Object.keys(S.gw.edits).map(gwUnit)).size; }
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
const GWTH = { "sys.name": "ชื่อเกตเวย์", "sys.wdt_ms": "Watchdog (ms)", "net.ip": "ไอพีเกตเวย์", "net.ntp": "ไอพีเซิร์ฟเวอร์เวลา NTP", "time.tz_min": "โซนเวลา (UTC)", "panel.cabinet": "รูปทรงตู้", "panel.lamp_hold_ms": "สถานะกำลังทำงานค้างนาน (ms)", "panel.lamp_dead": "เงียบกี่ครั้งจึงนับเป็นผิดปกติ", "sched.reset_enabled": "รีเซตไฟเลี้ยงโมดูลตามเวลา",
  "rs485.t2_ms": "เวลาเงียบที่ถือว่าจบคำตอบ (ms)", "usb.gap_ms": "เวลาเงียบที่ถือว่าจบคำสั่ง (ms)", "panel.preset": "พรีเซ็ตไฟที่ปุ่มสั่ง", "bus.hub_map": "แผนที่ช่อง", "bus.hub_retry": "จำนวนยิงกระตุ้นเมื่อข้ามช่อง", "bus.hub_gap_ms": "เผื่อเวลาเพิ่ม (ms)" };
/* bus.hub_map is ten numbers, one per row (slave IDs 11-108): which hub channel the row hangs on, 0 = wired straight. */
const hubRows = (str) => { const a = String(str || "").split(",").map((x) => parseInt(x, 10) || 0); while (a.length < 10) a.push(0); return a.slice(0, 10); };
/* panel.cabinet + panel.shape are one choice for the person: a preset (40/64/80) or a custom list of slots per row. The shape wins when set,
   and cabinet 0 means "follow the shape" (the gateway refuses 0 without one), so this widget writes the pair together. */
const CAB_PRESET = { 40: "4,4,4,4,4,4,4,4,4,4", 64: "8,8,8,4,4,4,4,8,8,8", 80: "8,8,8,8,8,8,8,8,8,8" };
const cabCur = (key) => (key in S.gw.edits ? S.gw.edits[key] : S.gw.data.keys.find((x) => x.key === key).value);
const cabSaved = (key) => S.gw.data.keys.find((x) => x.key === key).value;
const cabCustom = (cab, shape) => +cab === 0 || hubRows(shape).some((n) => n > 0);
const cabDesc = (cab, shape) => cabCustom(cab, shape) ? t("cabCustom") + " (" + hubRows(shape).filter((n) => n > 0).join(",") + ")" : t("cabSlots", { n: cab });
function cabSet(cab, shape) {
  const norm = (k, v) => (k === "panel.shape" ? hubRows(v).join(",") : String(v));
  for (const [k, v] of [["panel.cabinet", cab], ["panel.shape", shape]]) { if (norm(k, v) === norm(k, cabSaved(k))) delete S.gw.edits[k]; else S.gw.edits[k] = String(v); }
}
/* The reset schedule is five numbers in the gateway (days mask, slots mask, four HHMM) but one idea for the person: which days, and which times.
   Days: bit0 = Sunday ... bit6 = Saturday, 0 = every day (never all-unticked). Slots: bit0 = time 1 ... bit3 = time 4. HHMM: 300 = 03:00. */
const SCH_KEYS = ["sched.reset_days", "sched.reset_slots", "sched.reset_hhmm", "sched.reset_hhmm2", "sched.reset_hhmm3", "sched.reset_hhmm4"];
const schHhmmKey = (i) => SCH_KEYS[2 + i];
const schCur = (key) => +cabCur(key), schSaved = (key) => +cabSaved(key);
const schSet = (key, v) => { if (+v === schSaved(key)) delete S.gw.edits[key]; else S.gw.edits[key] = String(v); };
const hhmmText = (n) => String(Math.floor(n / 100)).padStart(2, "0") + ":" + String(n % 100).padStart(2, "0");
function schDesc(get) {
  const days = get("sched.reset_days"), names = t("schDayS"), slots = get("sched.reset_slots");
  const d = days === 0 || days === 127 ? t("schEvery") : names.filter((_, i) => days & (1 << i)).join(",");
  const times = [0, 1, 2, 3].filter((i) => slots & (1 << i)).map((i) => hhmmText(get(schHhmmKey(i)))).join(", ");
  return times ? d + " " + times : t("schNoTime");
}
/* Keys shown inside another key's widget: not fields of their own, not counted. */
const GWMERGED = { "panel.shape": "panel.cabinet", "sched.reset_slots": "sched.reset_days", "sched.reset_hhmm": "sched.reset_days", "sched.reset_hhmm2": "sched.reset_days", "sched.reset_hhmm3": "sched.reset_days", "sched.reset_hhmm4": "sched.reset_days" };
const gwUnit = (k) => (k === "panel.shape" ? "panel.cabinet" : SCH_KEYS.includes(k) ? "sched.reset_days" : k);
/* The "?" button, only where there is something to say: no button when the name says it all, or when there is no explanation text. */
const GWNOINFO = new Set(["sys.name", "net.enabled", "net.dhcp", "net.ip", "net.mask", "net.gw", "net.dns", "net.port", "net.ntp", "net.ntp_port", "time.tz_min", "rs485.baud", "usb.max_ms", "panel.enabled", "sched.reset_enabled"]);
function whyBtn(k) {
  const tx = k.text && k.text[lang];
  if (k.ro || GWNOINFO.has(k.key) || !(tx && tx.hint)) return "";
  return `<button class="why" data-act="hint" data-key="${esc(k.key)}" type="button" aria-label="${t("explain")}">?</button>`;
}
/* Shorter Thai explanations for this page than the shared i18n table has. */
const GWTHHINT = { "panel.lamp_dead": "บัส RS485 เงียบติดกันกี่ครั้งจึงนับเป็นผิดปกติ แล้วไฟที่ตามสถานะผิดปกติจะติด การสลับช่องฮับทำให้เงียบ 1 ครั้งตามปกติ จึงควรตั้งให้สูงกว่านั้นมาก", "panel.lamp_dwell_ms": "ไฟแต่ละดวงต้องคงสถานะอย่างน้อยเท่านี้ก่อนสลับ กันรีเลย์สับรัว ไม่รวมไฟเลี้ยงโมดูล", "panel.lamp_hold_ms": "หลังมีการสื่อสาร Modbus แต่ละครั้ง เกตเวย์จะนับเป็นกำลังทำงานต่ออีกเท่านี้ ไฟที่ตามสถานะกำลังทำงานจึงติดค้างแทนการกระพริบ ตั้งสั้นไปไฟจะกระตุกและรีเลย์ทำงานหนักขึ้น", "panel.preset": "เลือกว่าตอนกดปุ่มหน้าตู้ จะสั่งโมดูลให้เปิดไฟด้วยพรีเซ็ตหมายเลขไหน (1–8) สีและความสว่างกำหนดไว้ในพรีเซ็ตที่ตัวโมดูล ไม่ได้ตั้งที่เกตเวย์ และมีผลเฉพาะบอร์ดที่มีไฟ ring", "bus.hub_retry": "จำนวนครั้งที่ส่งคำสั่งเมื่อต้องเปลี่ยนไปคุยกับช่องฮับอื่น", "bus.hub_settle_ms": "เวลาที่ฮับใช้สลับช่อง รอโดยไม่มีการรับส่งข้อมูล", "bus.hub_budget_ms": "เวลามากสุดต่อหนึ่งคำสั่ง รวมเวลารอฮับสลับช่อง ต้องน้อยกว่าเวลารอคำตอบของฝั่งที่สั่ง (เซิร์ฟเวอร์) ไม่อย่างนั้นฝั่งนั้นจะหมดเวลาก่อน", "bus.hub_map": "เลือกว่าแต่ละแถวของตู้ต่ออยู่กับช่องไหนของฮับ RS485 ตั้งแต่ช่อง 1–8 ถ้าเลือกต่อตรง คือแถวที่ไม่ผ่านฮับ และตั้งต่อตรงทั้ง 10 แถว เกตเวย์จะปิดการจัดการฮับ", "sys.wdt_ms": "บอร์ดรีเซ็ตตัวเองถ้าเฟิร์มแวร์หยุดทำงานนานเท่านี้ ต้องนานกว่าเวลารอสาย LAN ตอนเปิดเครื่อง ไม่อย่างนั้นบอร์ดจะรีสตาร์ทวนไม่จบ มีผลหลังรีบูต" };
/* Not shown on this page: panel.lamps is redundant with setting every output to "not used" (the gateway default is on, and it is left untouched). */
const GWHIDE = new Set(["panel.lamps"]);
function gwLabel(k) { if (lang === "th" && GWTH[k.key]) return GWTH[k.key]; const tx = k.text && k.text[lang]; return (tx && tx.label) || (GWNAMES[k.key] && GWNAMES[k.key][lang === "th" ? 0 : 1]) || k.key; }

function showInfo(key) {
  const k = S.gw.data && S.gw.data.keys.find((x) => x.key === key); if (!k) return;
  const tx = (k.text && k.text[lang]) || {};
  const flags = [k.reboot ? t("rebootKey") : "", k.ro ? t("ro") : ""].filter(Boolean).map((f) => `<span class="chip ${f === t("ro") ? "off" : "warn"}">${esc(f)}</span>`).join(" ");
  $("#infobody").innerHTML = `<h2 style="margin-bottom:10px">${esc(gwLabel(k))}</h2>
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
    d.keys.forEach((k) => { if (GWHIDE.has(k.key) || (GWMERGED[k.key] && d.keys.some((x) => x.key === GWMERGED[k.key]))) return; const p = k.key.split(".")[0]; (groups[p] = groups[p] || []).push(k); });
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
      if (k.key === "panel.shape" && d.keys.some((x) => x.key === "panel.cabinet")) return "";
      if (k.key === "panel.cabinet" && d.keys.some((x) => x.key === "panel.shape")) {
        const cab = cabCur("panel.cabinet"), shp = cabCur("panel.shape"), custom = cabCustom(cab, shp), rows = hubRows(shp), saved = hubRows(cabSaved("panel.shape"));
        const edited = "panel.cabinet" in g.edits || "panel.shape" in g.edits, mark = ' style="border-color:var(--brand)"';
        const mode = [40, 64, 80].map((n) => `<option value="${n}"${!custom && +cab === n ? " selected" : ""}>${t("cabSlots", { n })}</option>`).join("") + `<option value="custom"${custom ? " selected" : ""}>${t("cabCustom")}</option>`;
        const cells = rows.map((v, i) => `<div class="hubcell"><span>${t("hubRow", { n: i + 1 })}</span><select data-cabrow="${i}"${v !== saved[i] ? mark : ""}>`
          + [0, 1, 2, 3, 4, 5, 6, 7, 8].map((c) => `<option value="${c}"${v === c ? " selected" : ""}>${c ? c : t("cabNone")}</option>`).join("") + `</select></div>`).join("");
        return `<div class="field" style="grid-column:1/-1"><label>${esc(gwLabel(k))}</label><select data-cabmode${edited ? mark : ""}>${mode}</select>
          <div class="hubgrid" data-cabgrid style="margin-top:8px"${custom ? "" : " hidden"}>${cells}</div></div>`;
      }
      if (k.key === "sched.reset_days" && SCH_KEYS.every((x) => d.keys.some((y) => y.key === x))) {
        const days = schCur("sched.reset_days"), slots = schCur("sched.reset_slots"), mark = ' style="border-color:var(--brand)"', names = t("schDay");
        const chips = names.map((n, i) => `<label class="chk"><input type="checkbox" data-schday="${i}"${days === 0 || days & (1 << i) ? " checked" : ""}>${esc(n)}</label>`).join("");
        const rows = [0, 1, 2, 3].map((i) => { const kk = schHhmmKey(i), on = !!(slots & (1 << i));
          return `<div class="schrow"><label class="chk"><input type="checkbox" data-schslot="${i}"${on ? " checked" : ""}>${t("schSlot", { n: i + 1 })}</label><input type="time" data-schtime="${i}" value="${hhmmText(schCur(kk))}"${kk in g.edits ? mark : ""}${on ? "" : ' class="off"'}></div>`; }).join("");
        return `<div class="field" style="grid-column:1/-1"><label>${t("schDays")}</label><div class="schdays">${chips}</div></div><div class="field" style="grid-column:1/-1"><label>${t("schTimes")}</label><div class="schgrid">${rows}</div></div>`;
      }
      if (GWENUM[k.key] && !k.ro) {
        const L = GWENUM[k.key], i18 = lang === "th" ? 0 : 1, vals = Object.keys(L).sort((x, y) => x - y), cur = String(val);
        const opts = vals.map((v) => `<option value="${v}"${v === cur ? " selected" : ""}>${esc(L[v][i18])}</option>`).join("") + (vals.includes(cur) ? "" : `<option value="${esc(cur)}" selected>${esc(cur)}</option>`);
        return `<div class="field"><label>${esc(gwLabel(k))}${whyBtn(k)}</label>
          <select data-key="${esc(k.key)}"${ed ? ' style="border-color:var(--brand)"' : ""}>${opts}</select></div>`;
      }
      return `<div class="field"><label>${esc(gwLabel(k))}${whyBtn(k)}</label>
        <input data-key="${esc(k.key)}" value="${esc(val)}" ${k.ro ? 'disabled class="ro"' : ""} ${ed ? 'style="border-color:var(--brand)"' : ""}>${k.key === "net.ntp" ? `<button class="btn" data-act="ntp-use" type="button">${t("ntpUsePc")}</button>` : ""}</div>`;
    };
    const sh = d.shape && d.shape.layout && !d.shape.agreed ? `<div class="notice">${t("shapeBad", { l: esc(d.shape.label), w: esc(d.shape.why) })}<div class="row" style="margin-top:8px">${d.shape.fixable ? `<button class="btn" data-act="gw-shape">${t("shapeFix")}</button>` : `<span class="small">${t("shapeNoFix")}</span>`}</div></div>` : "";
    body = sh + `<section class="card"><dl class="kv"><dt>${t("fw")}</dt><dd class="mono">${esc(i.fw)}</dd><dt>${t("uptime")}</dt><dd>${fmtUp(+i["sys.up"] || 0)} (${esc(i["sys.reset"] || "")})</dd>
        <dt>${t("clients")}</dt><dd>${esc(i["net.client"] || "?")}/2</dd><dt>${t("clock")}</dt><dd>${i["time.set"] === "1" ? esc((i["time.now"] || "").replace("T", " ")) : t("clockUnset")}</dd></dl></section>
      <section class="card stack">${order.map((grp) => `<details><summary><b>${esc(TXT[lang]["g_" + grp] || grp)}</b> <span class="small muted">${groups[grp].length}</span></summary><div class="fgrid" style="margin-top:8px">${groups[grp].map(field).join("")}</div></details>`).join("") || `<p class="muted">${t("noKeys")}</p>`}</section>
      <section class="card stack"><h3>${t("danger")}</h3><div class="row"><button class="btn" data-act="gw-time">${t("setClock")}</button><button class="btn" data-act="gw-reboot">${t("reboot")}</button><button class="btn" id="rptrun" data-act="rpt-run"${anyJob() && !S.rpt.running ? " disabled" : ""}>${t("rptBtn")}</button><button class="btn" data-act="gw-defaults" style="color:var(--bad)">${t("defaults")}</button></div>${sw("resync", i["rtu.heal"] === "1", "", "resyncInfo")}${sw("exc", i["tcp.exc"] === "1", "", "excInfo")}</section>`;
  } else if (d && !d.ok) body = `<div class="notice bad">${esc(d.error)}</div>`;
  return `<div class="row between"><h1>${t("gateway_page")}</h1></div>
    <section class="card stack"><div class="row" style="align-items:flex-end"><div class="field" style="min-width:0;flex:1"><label>${t("pick")}</label><select id="gwsel"><option value="">—</option>${opts}</select></div>
      <button class="btn primary" data-act="gw-read" style="flex:none;min-width:112px;white-space:nowrap">${g.busy ? t("reading") : t("read")}</button></div></section>
    <div class="stack" style="margin-top:12px">${body}</div><div id="gwbar"></div>`;
}
function gwBar() {
  const el = $("#gwbar"); if (!el) return;
  const d = S.gw.data; if (!(d && d.ok)) { el.innerHTML = ""; return; }
  const n = gwChanged();
  const shown = (k, v) => { const e = GWENUM[k] && GWENUM[k][v]; return e ? e[lang === "th" ? 0 : 1] : v; };
  const emptyShape = ("panel.cabinet" in S.gw.edits || "panel.shape" in S.gw.edits) && +cabCur("panel.cabinet") === 0 && !hubRows(cabCur("panel.shape")).some((x) => x > 0);
  const diffs = n ? `<b>${t("changes", { n })}</b>` + Object.entries(S.gw.edits).map(([k, v]) => {
    if (k === "panel.shape" && "panel.cabinet" in S.gw.edits) return "";
    if (SCH_KEYS.includes(k)) { if (k !== Object.keys(S.gw.edits).find((x) => SCH_KEYS.includes(x))) return ""; return `<div class="small">${t("schName")}: ${esc(schDesc(schSaved))} → <b>${esc(schDesc(schCur))}</b></div>`; }
    if (k === "panel.cabinet" || k === "panel.shape") { const c = d.keys.find((x) => x.key === "panel.cabinet"); return `<div class="small">${esc(gwLabel(c))}: ${esc(cabDesc(cabSaved("panel.cabinet"), cabSaved("panel.shape")))} → <b>${esc(cabDesc(cabCur("panel.cabinet"), cabCur("panel.shape")))}</b></div>`; }
    const kk = d.keys.find((x) => x.key === k); return `<div class="small">${esc(gwLabel(kk))}: ${esc(shown(k, kk.value))} → <b>${esc(shown(k, v))}</b></div>`; }).join("") : "";
  /* Always there: save, and the JSON file buttons. The list of changed values only while something has changed. */
  el.innerHTML = `<section class="card stack" style="position:sticky;bottom:calc(var(--navh) + 8px);margin-top:12px;${n ? "border-color:var(--brand)" : ""}">${diffs}${emptyShape ? `<div class="small" style="color:var(--bad)">${t("cabEmpty")}</div>` : ""}
    <div class="row"><button class="btn primary" data-act="gw-apply"${n && !emptyShape ? "" : " disabled"}>${t("apply")}</button>${n ? `<button class="btn" data-act="gw-clear">${t("reset")}</button>` : ""}
      <button class="btn" data-act="gw-export">${t("expCfg")}</button><label class="btn">${t("impCfg")}<input type="file" id="gwimport" accept=".json,application/json" hidden></label></div></section>`;
}


const PCOL = { 1: "#ff3232", 2: "#32ff32", 3: "#3264ff", 4: "#ffd700", 5: "#00e5e5", 6: "#ff32ff", 7: "#ff5a1e", 8: "#ffffff" };   /* preset 8 is white on the module */
function viewModule() {
  const m = S.mod, d = m.data;
  const opts = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === m.id ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const kv = (rows) => `<dl class="kv">${rows.filter(Boolean).map(([k, v]) => `<dt>${esc(k)}</dt><dd>${v}</dd>`).join("")}</dl>`;
  let cards = `<div class="notice info">${t("modNotRead")}</div>`;
  if (d && d.ok === false && !d.device) cards = `<div class="notice bad">${esc((d.errors || [d.error || ""]).join(" · "))}</div>`;
  else if (d && d.device) {
    const dv = d.device, rt = d.runtime, tp = d.temps, lt = d.latch;
    /* The decoders write "10 = STANDARD", "30505 (v3.5.5)", "SENSOR FAULT (0x8000)": the raw number is for the classic tool's register view, not for reading. */
    const pl = (v) => String(v == null ? "" : v).replace(/^-?\d+ = /, "").replace(/^\d+ \((.*)\)$/, "$1").replace(/ \(0x[0-9a-f]+\)$/i, "");
    const hc = (d.health || []).map((h) => `<span class="chip ${h.ok === null ? "off" : h.ok ? "ok" : "bad"}"><i class="dot"></i>${esc(h.name)}${h.ok === null ? " " + t("na") : ""}</span>`).join(" ");
    const S2 = d.stats, hm = (sec) => { sec = +sec || 0; const h = Math.floor(sec / 3600), mi = Math.floor((sec % 3600) / 60); return h ? t("hmFmt", { h, m: mi }) : t("mFmt", { m: mi, s: sec % 60 }); };
    const bad = (d.health || []).filter((h) => h.ok === false).length;    /* a sensor fault is already one of these */
    const sumChip = `<span class="chip ${bad ? "bad" : "ok"}"><i class="dot"></i>${bad ? t("hBad", { n: bad }) : t("hOk")}</span>`;
    const red = (on, txt) => `<span${on ? ' style="color:var(--bad)"' : ""}>${esc(txt)}</span>`;
    const sec = (title, body) => `<section class="msub"><h3>${title}</h3>${body}</section>`;
    const device = sec(t("cDevice"), kv([[t("mType"), esc(pl(dv.type))], [t("mFw"), esc(pl(dv.fw))], [t("mHw"), esc(pl(dv.hw))], [t("mBaud"), esc(dv.baud)], dv.uid ? [t("mUid"), `<span class="mono">${esc(dv.uid)}</span>`] : null]));
    const runtime = sec(t("cRuntime"), kv([[t("mUptime"), esc(rt.uptime)], [t("mBoots"), rt.boots], [t("mMode"), esc(pl(rt.mode))], [t("mPreset"), esc(pl(rt.preset))], rt.button !== undefined && rt.button !== null ? [t("mButton"), rt.button + (rt.held ? " ●" : "")] : null]));
    /* Health and the temperatures belong together: the two sensor chips ARE the temperature readings. */
    const health = sec(t("cHealth"), `<div class="row" style="gap:6px">${hc}</div>${tp ? kv([[t("mRoom"), red(tp.fault, pl(tp.room))], [t("mBoard"), red(tp.fault, pl(tp.board))], tp.current ? [t("mCurrent"), esc(tp.current)] : null]) : ""}${d.reset ? kv([[t("cReset"), esc(d.reset)]]) : ""}`);
    const latch = lt ? sec(t("cLatch"), kv([[t("mLatch"), lt.state ? t(lt.state === "locked" ? "mLocked" : "mUnlocked") : "—"], [t("mUnlockedAgoK"), t("agoS", { s: hm(lt.unlocked_ago_s) })], d.display !== undefined ? [t("mDisplay"), d.display] : null])) : "";
    const stats = S2 ? sec(t("cStats"), kv([[t("stOn"), t("stTimes", { n: S2.on_count })], [t("stOnTime"), hm(S2.on_seconds)],
        S2.v2 ? [t("stLatch"), t("stTimes", { n: S2.latch_fires })] : null, S2.v2 ? [t("stButton"), t("stTimes", { n: S2.button_presses })] : null, S2.v2 ? [t("stRun"), hm(S2.op_seconds)] : null])
      + `<table class="sttab"><tr><th>${t("stLight")}</th><th>${t("count")}</th><th>${t("stTimeCol")}</th></tr>${S2.presets.map((p) => `<tr><td><i class="dot" style="color:${PCOL[p.p]};width:10px;height:10px;display:inline-block;vertical-align:middle"></i> ${p.p}</td><td>${p.count}</td><td>${hm(p.seconds)}</td></tr>`).join("")}</table>`
      + (S2.v2 ? "" : `<div class="small muted">${t("stOld")}</div>`)) : "";
    /* One box, closed by default: the summary line says what most visits need (which module, which firmware, is it healthy).
       Two rows (device | health, runtime | latch) with the statistics down the right: boxes side by side share a height. */
    cards = `<details class="card" id="moddet"${m.open ? " open" : ""}><summary class="row" style="gap:8px;cursor:pointer"><b>${t("modInfo")}</b><span class="small muted">ID ${dv.id} · ${esc(pl(dv.type))} · ${esc(pl(dv.fw))}</span>${sumChip}</summary>
      <div class="mgrid">${device}${health}${runtime}${latch}${stats ? stats.replace('class="msub"', 'class="msub mstats"') : ""}</div>
      <p class="small muted" style="margin:10px 0 0">${t("checkedAt", { at: esc(d.at) })} · ${d.ms} ms</p></details>`;
  }
  const lb = (addr, label, cls) => `<button class="btn ${cls || ""}" data-act="mod-coil" data-addr="${addr}" data-val="1"${cls === "latch" ? " data-latch=1" : ""}>${label}</button>`;
  /* Commands the module that was read cannot carry are hidden unless "show all" is ticked. Only one fact is used, and it
     comes from the module itself: device type 10 (STANDARD) is the 8-window mask board with no OLED (LGS-Control-Table,
     note 13) and the Standard cabinet has no latches, so every display and latch command is moot there. Nothing is hidden before a module has been read. */
  const typeNo = d && d.device ? parseInt(String(d.device.type), 10) : NaN, noOled = typeNo === 10;
  const oled = (html) => (noOled && !m.showAll ? "" : html);
  const cb = (kind, label, latch) => `<button class="btn" data-act="mod-color" data-kind="${kind}"${latch ? " data-latch=1" : ""}>${label}</button>`;
  return `<h1>${t("module_page")}</h1>
    <section class="card stack"><div class="row" style="align-items:flex-end"><div class="field" style="min-width:220px;flex:1"><label>${t("pick")}</label><select id="modsel"><option value="">—</option>${opts}</select></div>
      <div class="field" style="width:140px"><label>${t("devId")}</label><input id="moddev" type="number" min="1" max="247" value="${m.dev}"></div>
      <button class="btn primary" data-act="mod-read" style="flex:none;min-width:112px;white-space:nowrap">${m.busy ? t("reading") : t("read")}</button></div>
      <div class="row"><label class="row"><input type="checkbox" id="modauto"${m.auto ? " checked" : ""}> ${t("auto")}</label></div></section>
    <div class="stack" style="margin-top:12px">${cards}
      <h2>${t("quick")}</h2><section class="card stack">
        <div class="row" style="justify-content:flex-end"><label class="row"><input type="checkbox" id="modall"${m.showAll ? " checked" : ""}> ${t("qShowAll")}</label></div>
        <div class="stack tight"><b class="small muted">${t("grpLight")}</b><div class="qgrid">${cb("enable", t("cLight"))}${oled(cb("display", t("cLightNum")))}</div></div>
        ${oled(`<div class="stack tight"><b class="small muted">${t("grpLatch")}</b><div class="qgrid"><button class="btn" data-act="mod-unlock" data-latch=1>${t("pUnlock")}</button>${cb("latch", t("cLightUnlock"), 1)}${cb("latch_display", t("cLightNumUnlock"), 1)}</div></div>`)}
        ${oled(`<div class="stack tight"><b class="small muted">${t("grpDisp")}</b><div class="qgrid"><button class="btn" data-act="mod-number">${t("writeNumber")}</button>
          <button class="btn" data-act="mod-coil" data-addr="1010" data-val="1">${t("dispPower")}</button><button class="btn" data-act="mod-coil" data-addr="1010" data-val="0">${t("dispOff")}</button></div></div>`)}
        <div class="stack tight"><b class="small muted">${t("grpOther")}</b><div class="qgrid">${lb(509, t("identify"))}${lb(511, t("allOff"))}</div></div>
        </section>
      <h2>${t("insTitle")}</h2><section class="card stack">${insView()}</section>
      <h2>${t("scanTitle")}</h2><section class="card stack">${scanView()}</section>
      ${uiMode === "advanced" ? `<h2>${t("dangerTitle")}</h2><section class="card stack" style="border-color:var(--bad)">${dangerView()}</section>` : ""}</div>`;
}
let modTimer = null;
async function modCoil(addr, on, latch) {
  if (!S.mod.id) return;
  if (latch && Date.now() < S.mod.lockUntil) { toast(t("cooldownNote")); return; }
  const r = await api("POST", "/api/v2/mod/coil", { id: S.mod.id, device_id: S.mod.dev, addr, value: on });
  if (!r.ok) throw new Error(r.error || "failed");
  if (latch) { S.mod.lockUntil = Date.now() + 2300; document.querySelectorAll("[data-latch]").forEach((b) => { b.disabled = true; setTimeout(() => { b.disabled = false; }, 2300); }); }
  toast(t("sent") + " · " + r.ms + " ms");
}
/* One chooser popup: the command is picked first, then what it needs (a colour 1-8, or safe/forced for an unlock).
   Resolves with the chosen value, or 0 if cancelled. items: [{v, html, cls}]. */
function pickFrom(title, items, cols, info) {
  return new Promise((resolve) => {
    const d = $("#colorpick"); $("#colortitle").innerHTML = esc(title) + (info ? " " + infoBtn(info) : "");
    const g = $("#colorgrid"); g.style.gridTemplateColumns = `repeat(${cols || 2},minmax(0,1fr))`;
    g.innerHTML = items.map((it) => `<button class="btn colbtn ${it.cls || ""}" type="button" data-col="${it.v}">${it.html}</button>`).join("");
    $("#colorno").textContent = t("insCancel");
    const done = (v) => { d.onclose = null; if (d.open) d.close(); resolve(v); };
    g.onclick = (e) => { const x = e.target.closest("[data-col]"); if (x) done(+x.dataset.col); };
    $("#colorno").onclick = () => done(0); d.onclose = () => resolve(0);
    if (d.showModal) d.showModal(); else d.setAttribute("open", "");
  });
}
const pickColor = (command) => pickFrom(t("colorTitle", { c: command }),
  [1, 2, 3, 4, 5, 6, 7, 8].map((n) => ({ v: n, html: `<i class="dot" style="color:${PCOL[n]};width:16px;height:16px"></i>${t("colorN", { n })}` })));
/* Coil 1020 only pulses a latch the module reads as locked (an open drawer is left alone); 1019 pulses it regardless. */
const pickUnlock = () => pickFrom(t("unlockTitle"), [{ v: 1020, html: t("unlockSafe") }, { v: 1019, html: `<span style="color:var(--bad)">${t("unlockForce")}</span>` }], 2, "unlockHow");
async function modRead() {
  const m = S.mod; if (!m.id || !(m.dev >= 1)) return;
  if (anyJob()) return;
  if (m.busy) { m.again = true; return; }          /* asked while a read runs: read once more when it ends */
  m.busy = true; m.again = false;
  const id = m.id, dev = m.dev;
  let r;
  try { r = await api("POST", "/api/v2/mod/monitor", { id, device_id: dev, stats: true }); }
  catch (e) { r = { ok: false, error: e.message }; }
  m.busy = false;
  /* The cabinet or the id changed while this read was out: its answer belongs to the old one, never show it as the new one. */
  if (id === m.id && dev === m.dev) m.data = r; else m.again = true;
  if (m.again) { m.again = false; return modRead(); }
  if (page === "module") renderKeep();
}
/* re-render without losing a typed value or the scroll position */
function renderKeep() { const y = window.scrollY; render(); window.scrollTo(0, y); }
function modAutoSync() {
  clearInterval(modTimer); modTimer = null;
  if (S.mod.auto && page === "module") modTimer = setInterval(() => { if (!document.hidden && page === "module") modRead(); }, 2000);
}


/* ---------- long module jobs: installation check, scan, full module test, site report ----------
   All run on the server (app/v2/install_api.py), one at a time. The page starts one, then a single poller folds its events
   into the state of that kind (S.ins / S.scan / S.rpt) and repaints only that kind's box. Everything shown lives
   in S, so a full render() (the module auto-read does one) loses nothing. */
const INS_INFO = {
  schedNote: ["เกตเวย์ทำเองตามเวลาของมัน เริ่มกลุ่มใหม่และรีบูตโมดูลเฉพาะในช่วงนี้ และเว้นช่วง reset ชั้นวางที่ตั้งไว้ ปิด Test Tool ได้หลังสั่ง\n\nเกตเวย์ทำเฉพาะช่วงเวลาที่กำหนด ทุกวันจนเสร็จ (กดหยุดได้ตลอด) ถ้าเวลาสิ้นสุดน้อยกว่าเวลาเริ่ม ช่วงนั้นข้ามเที่ยงคืน",
    "The gateway keeps to it by itself, on its own clock: it starts groups and reboots modules only inside the window, and keeps clear of the scheduled shelf reset. The Test Tool can be closed after starting.\n\nThe gateway works only inside the window you set, every day until it is done (Stop at any time). If the end time is earlier than the start, the window runs past midnight."],
  goNote: ["เกตเวย์อ่านไฟล์จากคลังของตัวเอง ส่งในช่วงที่บัสว่าง และหยุดพักเองเมื่อมีคำสั่งเข้ามา เริ่มแล้วปิด Tool ได้",
    "The gateway reads the image from its own depot, sends it in the gaps of the bus and pauses by itself when a request arrives. Once started the tool can be closed."],
  otaNote: ["Tool ส่งไฟล์ให้โมดูลเองผ่านเกตเวย์ ต้องเปิด Tool ค้างไว้จนจบ ตู้ที่เลือกจะใช้งานไม่ได้ระหว่างอัปเดต",
    "The tool sends the image to the modules through the gateway and must stay open until it finishes. The chosen cabinets are unusable while updating."],
  depotNote: ["ฝากไฟล์อัปเดตโมดูลไว้ในเกตเวย์ แล้วอัปเดตภายหลังจากเครื่องอื่นได้ โดยเครื่องที่สั่งไม่ต้องมีไฟล์",
    "Leave a module update file in the gateway, then update later from another PC that does not have the file"],
  soakDwell: ["ไฟแต่ละช่องติดค้างกี่วินาทีก่อนดับเอง (เหมือนรอคนกดยืนยัน) ตั้งนานขึ้นถ้าอยากให้ไฟติดซ้อนกันหลายดวง",
    "How many seconds a light stays on before it goes off by itself (as if waiting for a confirm). Make it longer to get several lights on at once."],
  soakCols: ["ตารางบน (โมดูลของแต่ละตู้)\n• mod = จำนวนโมดูล\n• pass = รอบที่อ่านครบทุกตัว\n• reads = จำนวนครั้งที่อ่าน\n• fail = อ่านไม่ได้\n• rbt = โมดูลรีบูต\n• wdt = โมดูลถูกวอตช์ด็อกรีเซ็ต\n• cross = ครั้งที่สลับช่องฮับ\n• worst = ตอบช้าสุด (ms)\n• drop = เฟรมตอบผิดไอดีถูกทิ้ง\n• silent = ไอดีที่ไม่ตอบ\n\nตารางล่าง (ตัวนับของเกตเวย์)\n• ซ่อมได้ = พลาดครั้งแรก แต่เกตเวย์ลองใหม่แล้วอ่านได้\n• ซ่อมไม่ได้ = ลองใหม่แล้วยังไม่ได้\n• timeout สุดท้าย = ไม่มีคำตอบเลย\n• CRC เสีย = ตอบมาแต่ข้อมูลเพี้ยน\n• อื่น ๆ = เฟรมแปลกอื่น\n\nสี\n• เทา = ศูนย์\n• เหลือง = ควรดู\n• แดง = ผิดปกติ\n\nถ้าเฟรมตอบผิดไอดีมาก ให้เพิ่ม timeout ฝั่ง client",
    "Top table (modules of each cabinet)\n• mod = modules\n• pass = passes that read every module\n• reads = reads\n• fail = failed reads\n• rbt = module reboots\n• wdt = module watchdog resets\n• cross = hub channel crossings\n• worst = slowest reply (ms)\n• drop = reply frames with the wrong unit id, discarded\n• silent = ids that never answered\n\nBottom table (gateway counters)\n• Repaired = missed first try, retried by the gateway and got it\n• Repair failed = retried and still nothing\n• Final timeouts = no reply at all\n• Bad CRC = a reply with damaged data\n• Other = other odd frames\n\nColour\n• grey = zero\n• amber = take a look\n• red = abnormal\n\nIf wrong-id frames are many, raise the client timeout"],
  soakHealCol: ["สถิติจากตัวนับบนเกตเวย์\n• fix = พลาดครั้งแรก แต่เกตเวย์ลองใหม่แล้วอ่านได้\n• /h = จำนวน fix ต่อชั่วโมง\n• fail = ลองใหม่แล้วยังไม่ได้\n• to = timeout สุดท้าย ไม่มีคำตอบเลย\n• crc = ตอบมาแต่ข้อมูลเพี้ยน",
    "Statistics from the gateway's own counters\n• fix = missed first try, retried by the gateway and got it\n• /h = fixes per hour\n• fail = retried and still nothing\n• to = final timeout, no reply at all\n• crc = a reply with damaged data"],
  soakPickCol: ["สถิติจากการจำลองการหยิบ\n• pick = จำนวนครั้งที่เปิดไฟสำเร็จสะสม\n• lit = จำนวนช่องที่ไฟติดอยู่ตอนนี้\n• skip = ครั้งหยิบที่ข้ามไป เพราะตู้ไฟติดทุกช่อง ไม่มีช่องว่างให้เปิด\n• err = จำนวนครั้งที่สั่งเปิดหรือดับไฟแล้วโมดูลไม่ตอบรับ",
    "Statistics from the pick simulation\n• pick = lights switched on successfully, total\n• lit = slots with the light on right now\n• skip = picks skipped because every slot was already lit\n• err = on/off commands the module did not acknowledge"],
  soakGap: ["เวลาพักหลังอ่านครบหนึ่งรอบ ก่อนเริ่มรอบถัดไป ค่าปกติ 2.0 วินาที อย่าตั้ง 0.4–0.9 เพราะจะทำให้ฮับพลาดการอ่านครั้งแรกเอง",
    "Pause after each full pass before the next one. Normal is 2.0 s. Avoid 0.4-0.9 s: it makes the hub lose first reads by itself."],
  soakEvery: ["อ่านตัวนับรีบูตและวอตช์ด็อกของโมดูลทุกกี่รอบ ค่าปกติ 5 ถี่ขึ้นเจอรีบูตเร็วขึ้น แต่ใช้บัสมากขึ้น",
    "How often the modules' reboot and watchdog counters are read. Normal is 5. More often finds a reboot sooner but uses more bus time."],
  soakSlow: ["โมดูลที่ตอบช้ากว่าค่านี้จะขึ้นเป็นเหตุผิดปกติ ค่าปกติ 400 ms",
    "A module that replies slower than this is listed as an anomaly. Normal is 400 ms."],
  soakTmo: ["เวลาที่โปรแกรมรอคำตอบหนึ่งครั้งก่อนยอมแพ้ ค่าปกติ 6 วินาที ต้องไม่ต่ำกว่าเวลาที่ฮับถือคำตอบ (ราว 2 วินาที) ไม่งั้นบัสอาจเหลื่อมกัน ใช้เฉพาะการทดสอบต่อเนื่อง",
    "How long the tool waits for one reply before giving up. Normal is 6 s. It must stay above the time a hub holds a reply (about 2 s) or the bus can fall out of step. Applies to the continuous test only."],
  soakWins: ["จะสุ่มใช้กี่หน้าต่างจากสูงสุด 8 ต่อช่อง (ปกติ 8) ตู้ที่มีไฟวงแหวนจะติดได้ทีละดวง",
    "How many of the 8 windows per slot to pick from (normally 8). On cabinets with a ring light only one is lit at a time."],
  soakPicks: ["จำลองคนมาหยิบยา ทุกครั้งจะเปิดไฟหนึ่งช่อง (สุ่ม) ค้างไว้สักพักแล้วดับ ตัวเลขคือจำนวนครั้งต่อตู้ต่อวัน กระจายเท่า ๆ กัน เช่น 2,000 = ราว 1 ครั้งทุก 43 วินาที ไม่มีการปลดกลอน",
    "Simulates people picking medicine: each time one random slot is lit for a while, then switched off. The number is picks per cabinet per day, spread evenly: 2,000 is about one every 43 seconds. The latch is never fired."],
  unlockHow: ["ปลอดภัย: ปลดเฉพาะเมื่อกลอนล็อกอยู่ ลิ้นชักที่เปิดค้างจะไม่ถูกสั่งซ้ำ\nบังคับ: ปลดทันทีโดยไม่ดูสถานะกลอน",
    "Safe: only when the latch reads locked; an open drawer is left alone.\nForce: pulse now, whatever the latch reads."],
  pick: ["ซ้อมขั้นตอนจ่ายยาจริง: ไฟติดพร้อมกันเป็นชุด เหมือนตอนใบสั่งยาสั่งงานจริง คนที่หน้าตู้หยิบช่องไหนก่อนก็ได้ ไฟแต่ละช่องจะดับเมื่อกดปุ่มหน้าช่องนั้น ครบชุดแล้วชุดถัดไปจะติดต่อ พิสูจน์ไฟ ปุ่ม และวงจรยืนยันครบในรอบเดียว ต้องใช้เฟิร์มแวร์โมดูล v3.2.0",
    "The dispensing flow as a rehearsal: a batch of slots lights up together, just as a prescription lights them, and someone at the cabinet picks them in any order; each light goes out as its front button is pressed. When the batch is done the next one lights. Needs module firmware v3.2.0."],
  action: ["หนึ่งคำสั่งต่อโมดูล ใช้ชุดเดียวกับที่เฟิร์มแวร์มีให้ เปิดไฟวงแหวน หรือเปิดไฟพร้อมโชว์เลขประจำช่อง ถ้าติ๊กปลดกลอนจะยกระดับคำสั่งนั้นให้ปลดกลอนด้วย จอแสดง Slave ID ถ้าเกิน 99 จะแสดงเลขช่องแทน เพราะจอรองรับสองหลัก",
    "One command per module, the same combinations the firmware offers: the ring, or the ring with the module's number. Ticking the latch upgrades whichever is chosen. The display shows the slave ID; IDs above 99 show the column number, because it holds two digits."],
  unlock: ["แต่ละโมดูลมีเวลาพัก 2 วินาทีของตัวเอง การไล่ทดสอบข้ามโมดูลจึงไม่ถูกหน่วง กลอนที่เปิดอยู่แล้วจะปล่อยพัลส์ไม่ได้ ให้ปิดลิ้นชักแล้วตรวจใหม่",
    "Each module keeps its own 2 s cooldown, so a sweep across different modules is not slowed down. A latch that is already open cannot be pulsed: close the drawer and run it again."],
  batch: ["จำนวนช่องที่ไฟติดพร้อมกัน หนึ่งชุดจะอยู่ในแถวเดียวเสมอ เพราะฮับ RS485 ต้องเงียบราว 2 วินาทีเพื่อสลับช่อง การเฝ้าสองแถวพร้อมกันจึงหน่วงหลายวินาทีกว่าจะเห็นการกด ใส่ 0 = จุดทุกช่องที่เลือกพร้อมกัน",
    "How many slots light at once. A batch never spans rows: the RS485 hub needs about two seconds of silence to change channel. 0 lights everything selected at once."],
  closed: ["การหยิบยายังไม่จบตอนกดปุ่ม แต่จบเมื่อปิดลิ้นชักแล้ว เปิดตัวเลือกนี้ ช่องนั้นต้องปิดอยู่ก่อนเริ่ม และไฟจะติดค้างจนโมดูลรายงานว่ากลอนล็อก ช่องที่เปิดค้างไว้จึงผ่านไม่ได้",
    "The pick is not over when the button is pressed but when the drawer is shut again. With this on, the slot must start closed and the light stays on until the module reports its latch locked."],
  bych: ["เปิด: ช่องที่อยู่คนละช่องฮับจะติดเป็นคนละชุดต่อกันไป ทำให้ยืนยันได้เร็ว ปิด: หนึ่งชุดจะจุดครบตามจำนวนที่ตั้งไม่ว่าอยู่ช่องใด เหมือนใบสั่งยาจริง แต่ไฟจะดับช้าลงราว 2 วินาทีต่อรอบ",
    "On: slots either side of a channel boundary light one batch after the other. Off: the batch holds as many slots as asked for wherever they are, as a real prescription does, but each light takes about two seconds longer to go out."],
  scan: ["ถามทีละ ID ว่ามีโมดูลตอบไหม (อ่านอย่างเดียว) แบบเร็วถามเฉพาะช่องในผังตู้ รวม 247 (ค่าโรงงาน) และ 246 (โหมดตั้ง ID) แบบเต็มถาม 1–245 ด้วย ใช้เวลาราว 2 นาที ID ที่พบแต่ไม่อยู่ในผังจะขึ้นสีส้ม",
    "Asks each id in turn whether a module answers (read-only). Quick asks the cabinet's slots plus 247 (factory) and 246 (SET_ID mode); full also asks 1-245 and takes about two minutes. Ids found outside the cabinet's layout show orange."],
};
const infoBtn = (k) => `<button class="why" data-act="ins-info" data-k="${k}" type="button" aria-label="${t("explain")}">?</button>`;
const insInfoBtn = infoBtn;
const insSelText = () => t("insSel", { n: S.ins.sel.size });
function insReset() { Object.assign(S.ins, { res: {}, rows: [], lit: new Set(), closing: new Set(), testing: null, text: "", banner: "", summary: "", file: false, err: "" }); }
async function insLayout() {
  const i = S.ins; if (!S.mod.id) { i.layout = null; i.id = ""; return; }
  if (i.id === S.mod.id) return;                         /* loaded, loading or failed for this cabinet already */
  i.id = S.mod.id; i.layout = null; i.sel = new Set(); insReset(); S.scan.found = []; S.scan.text = ""; S.scan.asked = new Set(); S.scan.at = 0;
  try { i.layout = await api("GET", "/api/v2/ins/layout?id=" + encodeURIComponent(S.mod.id)); } catch (e) { i.layout = null; i.err = e.message; }
  if (page === "module") renderKeep();
}

/* ---- one poller for whichever job runs ---- */
const JOBST = { check: () => S.ins, scan: () => S.scan, report: () => S.rpt };
const anyJob = () => Object.values(JOBST).some((f) => f().running);
function jobFold(kind, ev) { ({ check: insFold, scan: scanFold, report: rptFold })[kind](ev); }
function jobPaint() { insPaint(); scanPaint(); rptPaint(); }
async function jobPoll() {
  try {
    const r = await api("GET", "/api/v2/ins/events?since=" + S.jobSince), st = JOBST[r.kind] && JOBST[r.kind]();
    if (st) { if (r.kind === "check" && r.mode) S.ins.mode = r.mode; r.events.forEach((ev) => jobFold(r.kind, ev)); st.running = r.running; st.file = r.csv; if (r.error) st.err = r.error; }
    S.jobSince = r.seq;
    if (!r.running) { clearInterval(S.jobTimer); S.jobTimer = null; Object.values(JOBST).forEach((f) => { f().running = false; }); if (page === "module" || page === "gateway") renderKeep(); jobPaint(); return; }
  } catch (e) { /* a missed poll is only a late repaint */ }
  jobPaint();
}
function jobSync() { if (!S.jobTimer) S.jobTimer = setInterval(jobPoll, 700); }
async function jobStart(kind, url, body) {
  if (anyJob()) { toast(t("jobBusy")); return false; }
  const st = JOBST[kind](); st.running = true; st.err = ""; S.jobSince = 0; jobPaint();
  try { await api("POST", url, body); jobSync(); return true; }
  catch (e) { st.running = false; st.err = e.message; jobPaint(); return false; }
}
/* The page may be opened while a job the server started is still running (another tab, a reload): pick it up. */
async function jobResume() {
  if (S.jobResumed) return; S.jobResumed = true;
  try {
    const r = await api("GET", "/api/v2/ins/events?since=0"), st = JOBST[r.kind] && JOBST[r.kind]();
    if (!st || (!r.running && !r.events.length)) return;
    const site = S.sites.find((x) => x.name === r.cabinet);
    if (r.kind === "scan" && site && !S.mod.id) { S.mod.id = site.id; await insLayout(); }
    if (r.kind === "check") { if (site) { S.mod.id = site.id; await insLayout(); } S.ins.mode = r.mode || S.ins.mode; insReset(); }
    if (r.kind === "report" && site) S.rpt.id = site.id;
    if (r.kind === "report" && r.running && page === "gateway") setTimeout(rptOpen, 0);
    r.events.forEach((ev) => jobFold(r.kind, ev)); S.jobSince = r.seq; st.running = r.running; st.file = r.csv;
    if (r.running) jobSync(); if (page === "module" || page === "gateway") renderKeep();
  } catch (e) { /* no job to resume */ }
}
const fileLink = (st, label) => `<a class="btn" href="/api/v2/ins/file" download${st.file && !st.running ? "" : " hidden"}>${label}</a>`;

/* ---- installation check / pick walkthrough ---- */
const insCoil = () => { const i = S.ins; return 1001 + (i.action === "light_display" ? 10 : 0) + (i.unlock ? 20 : 0); };
function insCaption() {
  const i = S.ins, el = $("#inscap"); if (!el) return;
  /* Only the warning that latches will really move, and only when some will. */
  el.innerHTML = i.unlock && i.action !== "skip" && i.sel.size ? `<div class="small" style="color:var(--bad)">${t("insWarnUnlock", { n: i.sel.size })}</div>` : "";
  el.hidden = !el.innerHTML;
}
function insCls(id) {
  const i = S.ins, r = i.res[id];
  if (r) return r; if (i.closing.has(id)) return "closing"; if (i.testing === id || i.lit.has(id)) return "next"; return i.sel.has(id) ? "on" : "";
}
function insGridHtml() {
  const L = S.ins.layout; if (!L) return "";
  const have = new Set(L.ids), cols = 8;
  let h = `<div class="cmgrid" style="grid-template-columns:auto repeat(${cols},minmax(0,1fr))">`;
  for (const row of L.rows) {
    h += `<button class="cmrow" data-act="ins-row" data-r="${row.r}" aria-label="R${row.r}">R${row.r}</button>`;
    for (let k = 1; k <= cols; k++) { const id = row.r * 10 + k; h += have.has(id) ? `<button class="cmcell ${insCls(id)}" data-act="ins-cell" data-id="${id}">${id}</button>` : "<span></span>"; }
  }
  return h + "</div>";
}
function insDyn() {
  const i = S.ins, b = i.banner;
  const chip = b ? `<span class="chip ${b === "pass" ? "ok" : b === "run" ? "warn" : b === "issues" ? "bad" : "off"}">${t("insB_" + b)}</span>` : "";
  const resText = (r) => (r.ok ? t("insPass") : !r.responded ? t("insNoAns") : t("insFail"));
  const rows = i.rows.slice().reverse().map((r) => `<tr><td>${r.id}</td><td>${esc(r.type || "—")}</td><td style="color:var(${r.ok ? "--ok" : "--bad"})">${resText(r)}</td><td>${esc(r.steps.map((s) => `${s.label}: ${s.ok ? "ok" : "FAIL"}${s.note && !s.ok ? ` (${s.note})` : ""}`).join("; "))}</td></tr>`).join("");
  return `${chip || i.text ? `<div class="row" style="gap:10px">${chip}<span class="small">${esc(i.text)}</span></div>` : ""}${i.err ? `<div class="notice bad">${esc(i.err)}</div>` : ""}
    ${i.summary ? `<div class="small">${esc(i.summary)}</div>` : ""}
    ${rows ? `<div id="insres" class="insres"><table><tr><th>ID</th><th>${t("insType")}</th><th>${t("insResult")}</th><th>${t("insDetail")}</th></tr>${rows}</table></div>` : ""}`;
}
/* Cancel while a check runs; once there is a result on screen the same button clears it (the selection stays). */
function insStopBtn() {
  const i = S.ins, has = !i.running && (i.rows.length || Object.keys(i.res).length || i.summary || i.banner);
  return has ? `<button class="btn" id="insstop" data-act="ins-clear">${t("scanClear")}</button>`
    : `<button class="btn" id="insstop" data-act="job-stop"${i.running ? "" : " disabled"}>${t("insCancel")}</button>`;
}
/* The newest result is on top and the box is as tall as the header plus five rows: older ones are a scroll away. */
function insResFit() {
  const box = $("#insres"); if (!box) return;
  const fit = () => {
    const rows = box.querySelectorAll("tr");
    box.style.maxHeight = rows.length > 6 ? Math.ceil(rows[6].getBoundingClientRect().top - rows[0].getBoundingClientRect().top) + 2 + "px" : "";
  };
  fit();
  /* Row heights change after the fit on a phone (the web font arriving, a rotation, the detail column re-wrapping):
     refit whenever the table itself changes size, so the box keeps showing five rows, not six or seven. */
  const table = box.querySelector("table");
  if (table && !table._fitObs && window.ResizeObserver) { table._fitObs = new ResizeObserver(fit); table._fitObs.observe(table); }
}
function insPaint() {
  const g = $("#insgrid"); if (g) g.innerHTML = insGridHtml();
  const el = $("#insdyn"); if (el) { el.innerHTML = insDyn(); el.hidden = !el.innerHTML.trim(); }
  insResFit();
  const busy = anyJob(), run = $("#insrun"), stop = $("#insstop"); if (run) run.disabled = busy; if (stop) stop.outerHTML = insStopBtn();
  const f = $("#insfile"); if (f) f.hidden = !(S.ins.file && !S.ins.running);
}
function insFold(ev) {
  const i = S.ins, pick = i.mode === "pick";
  if (ev.t === "start") { i.testing = ev.id; i.text = t(pick ? "insPrep" : "insProg", { id: ev.id, i: ev.index, total: ev.total }); i.banner = "run"; }
  else if (ev.t === "done") {
    i.testing = null; i.lit.delete(ev.id); i.closing.delete(ev.id); i.res[ev.id] = ev.ok ? "ok" : "bad"; i.rows.push(ev);
    if (pick && (i.lit.size || i.closing.size)) i.text = i.closing.size ? t("insClosing", { n: i.closing.size, lit: i.lit.size }) : t("insWaiting", { n: i.lit.size });
  } else if (ev.t === "lit") { i.testing = null; i.lit = new Set(ev.ids); i.closing = new Set(); i.text = t("insWaiting", { n: ev.ids.length }); }
  else if (ev.t === "pressed") { i.lit.delete(ev.id); i.closing.add(ev.id); i.text = t("insClosing", { n: i.closing.size, lit: i.lit.size }); }
  else if (ev.t === "end") {
    i.testing = null; i.lit = new Set(); i.closing = new Set(); i.text = t("insDone", { n: ev.total });
    i.banner = ev.cancelled ? "cancelled" : ev.passed ? "pass" : "issues";
    const parts = [t("insAnswered", { n: ev.answered, total: ev.total })];
    if (ev.missing.length) parts.push(t("insMissing", { ids: ev.missing.join(", ") }));
    if (ev.failed.length) parts.push(t("insFailedIds", { ids: ev.failed.join(", ") }));
    i.summary = parts.join(" · ");
  }
}
async function insStart() {
  const i = S.ins; if (!S.mod.id || anyJob()) return;
  if (!i.sel.size) { toast(t("insPickOne")); return; }
  const pick = i.mode === "pick", unlock = pick ? (i.punlock || i.off === "shut") : (i.unlock && i.action !== "skip");
  if (unlock && !await ask(t("insUnlockQ", { n: i.sel.size }))) return;
  insReset(); i.banner = "run"; i.text = t("insStarting");
  await jobStart("check", "/api/v2/ins/start", { id: S.mod.id, mode: i.mode, ids: [...i.sel].sort((a, b) => a - b), action: i.action, unlock: pick ? (i.punlock || i.off === "shut") : i.unlock, identify: i.identify, hold_s: i.hold,
    preset: i.preset, display: i.display, require_locked: i.off !== "btn", drawer_only: i.off === "shut", timeout_s: i.timeout, batch: i.batch, by_channel: i.order === "ch", shuffle: i.order === "random" });
}
/* Four numbered steps, in the order a person has to decide them: what kind of check, which modules, how, then run it.
   The slot grid is both the picker (step 2) and the result map: cells turn green / red as the run reaches them. */
function insView() {
  const i = S.ins;
  if (!S.mod.id) return `<div class="notice info">${t("insPickCab")}</div>`;
  if (!i.layout) return i.err ? `<div class="notice bad">${esc(i.err)}</div>` : `<p class="muted">${t("reading")}</p>`;
  const num = (k, lo, hi, step) => `<input type="number" data-ins="${k}" min="${lo}" max="${hi}" step="${step || 1}" value="${i[k]}">`;
  const chk = (k, label, info) => `<div class="field"><label class="chk"><input type="checkbox" data-ins="${k}"${i[k] ? " checked" : ""}>${t(label)}${info ? infoBtn(info) : ""}</label></div>`;
  const seqSel = (label, k, opts, cur, off) => `<div class="field"><label>${label}</label><select data-ins="${k}"${off ? " disabled" : ""}>${opts.map(([v, l]) => `<option value="${v}"${v === cur ? " selected" : ""}>${esc(l)}</option>`).join("")}</select></div>`;
  const withCur = (opts, cur, lbl) => (opts.some(([v]) => v === cur) ? opts : opts.concat([[cur, lbl(cur)]]));   /* a stored value outside the list stays selectable */
  const step = (n, title, body, extra) => `<div class="istep"><div class="row" style="gap:8px;align-items:center"><span class="inum">${n}</span><b>${title}</b>${extra || ""}</div>${body}</div>`;
  const modes = ["check", "pick"].map((m) => `<button class="btn${i.mode === m ? " primary" : ""}" data-act="ins-mode" data-m="${m}" aria-pressed="${i.mode === m}">${t(m === "check" ? "insModeCheck" : "insModePick")}</button>`).join("");
  const opts = i.mode === "check"
    ? /* What happens at each module, in the order it happens: the light (the latch rides on the same command, so it can
         only follow a light), then identify. */
      `<div class="seq" style="grid-column:1/-1">${seqSel(t("seqLight"), "action", [["skip", t("seqNone")], ["light", t("cLight")], ["light_display", t("cLightNum")]], i.action)}<span class="seqarr">→</span>
         ${seqSel(t("seqLatch"), "unlock", [["0", t("seqNone")], ["1", t("pUnlock")]], i.unlock && i.action !== "skip" ? "1" : "0", i.action === "skip")}<span class="seqarr">→</span>
         ${seqSel(t("seqIdent"), "identify", [["0", t("seqNone")], ["1", t("identify")]], i.identify ? "1" : "0")}</div>
       <div class="field" style="grid-column:1/-1;width:200px;max-width:100%"><label>${t("insHold")}</label>${num("hold", 0.2, 5, 0.1)}</div><div id="inscap" style="grid-column:1/-1" hidden></div>`
    : /* A pick, as it happens at the cabinet: the slot lights (in a colour, with its number or not), the latch opens or not,
         and the light goes out on the button, or on the button and the drawer shut again. Then how many at a time and how long to wait. */
      `<div class="seq seq4" style="grid-column:1/-1">${seqSel(t("seqLight"), "preset", [1, 2, 3, 4, 5, 6, 7, 8].map((n) => [String(n), t("colorN", { n })]), String(i.preset))}<span class="seqarr">→</span>
         ${seqSel(t("pkNum"), "display", [["1", t("pkShow")], ["0", t("seqNone")]], i.display ? "1" : "0")}<span class="seqarr">→</span>
         ${seqSel(t("seqLatch"), "punlock", [["1", t("pUnlock")], ["0", t("seqNone")]], i.punlock || i.off === "shut" ? "1" : "0", i.off === "shut")}<span class="seqarr">→</span>
         ${seqSel(t("pkOff"), "off", [["btn", t("pkOffBtn")], ["btnshut", t("pkOffShut")], ["shut", t("pkOffDrawer")]], i.off)}</div>
       ${seqSel(t("pkBatch"), "batch", withCur([[1, "1"], [2, "2"], [4, "4"], [8, "8"], [16, "16"], [0, t("pkAll")]].map(([v, l]) => [String(v), v ? t("pkSlots", { n: l }) : l]), String(i.batch), (v) => t("pkSlots", { n: v })), String(i.batch))}
       ${seqSel(t("pkWait"), "timeout", withCur([[30, t("pkSec", { n: 30 })], [60, t("pkMin", { n: 1 })], [120, t("pkMin", { n: 2 })], [300, t("pkMin", { n: 5 })], [0, t("pkNoLimit")]].map(([v, l]) => [String(v), l]), String(i.timeout), (v) => t("pkSec", { n: v })), String(i.timeout))}
       ${seqSel(t("pkGroup"), "order", [["ch", t("pkByCh")], ["id", t("pkById")], ["random", t("pkRandom")]], i.order)}`;
  const fromScan = S.scan.found.length ? `<button class="btn" data-act="ins-fromscan">${t("insFromScan")}</button>` : "";
  const res = insDyn();
  return step(1, t("insStep1"), `<div class="row" style="gap:8px">${modes}</div>`)
    + step(2, t("insStep2"), `<div class="row" style="gap:8px"><button class="btn" data-act="ins-whole">${t("insWhole")}</button>${fromScan}<button class="btn" data-act="ins-none">${t("insClear")}</button></div><div id="insgrid">${insGridHtml()}</div>`,
      `<span class="small muted" id="inssel">${insSelText()}</span>`)
    + step(3, t("insStep3"), `<div class="fgrid">${opts}</div>`)
    + step(4, t("insStep4"), `<div class="row" style="gap:8px"><button class="btn primary" id="insrun" data-act="ins-run"${anyJob() ? " disabled" : ""}>${t(i.mode === "check" ? "insRun" : "insPickRun")}</button>${insStopBtn()}
      ${fileLink(i, t("insCsv")).replace("<a ", '<a id="insfile" ')}</div><div id="insdyn" class="stack"${res.trim() ? "" : " hidden"}>${res}</div>`);
}

/* ---- bus scan ---- */
function scanFold(ev) {
  const s = S.scan;
  if (ev.t === "probe") { s.full = ev.total > 100; s.text = t("scanProg", { i: ev.index, total: ev.total, id: ev.id }); s.at = ev.id; s.asked.add(ev.id); if (ev.found) s.found.push({ id: ev.id, type: ev.type }); }
  else if (ev.t === "end") { s.found = ev.found; s.at = 0; s.text = ev.cancelled ? t("insB_cancelled") : t("scanDone", { n: ev.found.length, total: ev.total }); }
}
/* The result laid out like the cabinet, eight to a row: found = green, asked and silent = red, being asked = amber.
   Ids that answered outside the layout (247 factory, 246 SET_ID, a wrong id) are listed underneath. */
function scanDyn() {
  const s = S.scan, L = S.ins.layout, found = new Map(s.found.map((f) => [f.id, f.type]));
  const cell = (id) => { const f = found.has(id), cls = f ? " ok" : s.at === id ? " next" : s.asked.has(id) ? " bad" : "";
    return f ? `<button class="cmcell${cls}" data-act="scan-pick" data-id="${id}" title="${esc(found.get(id))}">${id}</button>` : `<span class="cmcell${cls}" style="display:grid;place-items:center;cursor:default">${id}</span>`; };
  let grid = "";
  if (s.full) {
    /* Every id: ten to a row by tens (1-9, 10-19 ... 240-247). Found = green, found outside the cabinet's layout = amber,
       a layout slot that stayed silent = red, any other silent id just fades. */
    const lay = new Set((L && L.ids) || []);
    const fcell = (id) => { const f = found.has(id), cls = f ? (lay.has(id) ? " ok" : " extra") : s.at === id ? " next" : s.asked.has(id) ? (lay.has(id) ? " bad" : " dim") : "";
      return f ? `<button class="cmcell sm${cls}" data-act="scan-pick" data-id="${id}" title="${esc(found.get(id))}">${id}</button>` : `<span class="cmcell sm${cls}">${id}</span>`; };
    grid = `<div class="cmgrid" style="grid-template-columns:auto repeat(10,minmax(0,1fr))">`;
    for (let r = 0; r <= 24; r++) { grid += `<span class="cmrow">${r * 10}</span>`; for (let k = 0; k <= 9; k++) { const id = r * 10 + k; grid += id >= 1 && id <= 247 ? fcell(id) : "<span></span>"; } }
    grid += "</div>";
  } else if (L) {
    grid = `<div class="cmgrid" style="grid-template-columns:auto repeat(8,minmax(0,1fr))">`;
    for (const row of L.rows) { grid += `<span class="cmrow">R${row.r}</span>`; for (let k = 1; k <= 8; k++) { const id = row.r * 10 + k; grid += row.ids.includes(id) ? cell(id) : "<span></span>"; } }
    grid += "</div>";
  }
  const have = new Set((L && L.ids) || []), extra = s.full ? [] : s.found.filter((f) => !have.has(f.id));
  const ex = extra.length ? `<div class="row" style="gap:6px;align-items:center"><span class="small muted">${t("scanExtra")}</span>${extra.map((f) => `<button class="cmcell next" style="min-width:56px;padding:0 8px" data-act="scan-pick" data-id="${f.id}" title="${esc(f.type)}">${f.id}</button>`).join("")}</div>` : "";
  const started = s.running || s.asked.size;
  return `${s.err ? `<div class="notice bad">${esc(s.err)}</div>` : ""}${started ? grid : ""}${ex}`;
}
function scanPaint() {
  const el = $("#scandyn"); if (el) { el.innerHTML = scanDyn(); el.hidden = !el.innerHTML; }   /* an empty box would leave an extra gap under the buttons */
  const stt = $("#scanstat"); if (stt) stt.textContent = S.scan.text || t("insIdle");
  const busy = anyJob(); document.querySelectorAll("[data-act=scan-run]").forEach((b) => { b.disabled = busy; }); const st = $("#scanstop"); if (st) st.outerHTML = scanStopBtn();
}
/* Cancel while a scan runs; once there is a result on screen the same button clears it. */
function scanStopBtn() {
  const s = S.scan, has = !s.running && (s.asked.size || s.found.length);
  return has ? `<button class="btn" id="scanstop" data-act="scan-clear">${t("scanClear")}</button>`
    : `<button class="btn" id="scanstop" data-act="job-stop"${s.running ? "" : " disabled"}>${t("insCancel")}</button>`;
}
function scanView() {
  if (!S.mod.id) return `<div class="notice info">${t("insPickCab")}</div>`;
  return `<div class="row" style="gap:8px;align-items:center"><button class="btn primary" data-act="scan-run" data-full="0"${anyJob() ? " disabled" : ""}>${t("scanQuick")}</button><button class="btn" data-act="scan-run" data-full="1"${anyJob() ? " disabled" : ""}>${t("scanFull")}</button>
    ${scanStopBtn()}<span id="scanstat" class="small muted" style="margin-left:auto">${esc(S.scan.text || t("insIdle"))}</span></div><div id="scandyn" class="stack"${scanDyn() ? "" : " hidden"}>${scanDyn()}</div>`;
}

/* ---- site report (gateway page): runs in its own popup, which carries the progress, Cancel and then the download ---- */
function rptFold(ev) {
  const r = S.rpt;
  if (ev.t === "start") { r.i = ev.index - 1; r.total = ev.total; r.text = t("rptProg", { i: ev.index, total: ev.total, id: ev.id }); }
  else if (ev.t === "end") { r.i = r.total = ev.total; r.text = ev.cancelled ? t("insB_cancelled") : t("rptDone", { a: ev.answered, n: ev.total }); }
  else if (ev.t === "ready") {
    r.ready = true;
    api("GET", "/api/v2/ins/report/soaks").then((x) => { r.soaks = x.soaks || []; rptPaint(); }).catch(() => { /* the list is a convenience: upload still works */ });
  }
}
function rptPaint() {
  const b = $("#rptrun"); if (b) b.disabled = (anyJob() && !S.rpt.running) || !S.gw.id;
  const d = $("#rptdlg"); if (!d || !d.open) return;
  const r = S.rpt;
  const pick = r.ready && !r.running && !r.built ? `<div class="stack"><div class="small muted">${t("rptSoakHint")}</div>
    <div class="field"><label>${t("rptSoakTitle")}</label><select id="rptsoak"><option value="">${t("rptSoakNone")}</option>${(r.soaks || []).map((x) => `<option value="${esc(x.name)}"${x.name === r.soak ? " selected" : ""}>${esc(x.when)} · ${esc(x.name)}</option>`).join("")}</select></div>
    <div class="row"><button class="btn" type="button" data-act="rpt-upload">${t("rptSoakUpload")}</button><span class="small muted">${esc(r.upName)}</span><input type="file" id="rptfile" accept=".csv,text/csv" hidden></div>
    <button class="btn primary" type="button" data-act="rpt-build"${r.building ? " disabled" : ""}>${r.building ? t("rptBuilding") : t("rptBuild")}</button></div>` : "";
  const done = r.built ? `<div class="notice info">${esc(t("rptBuilt"))}${r.note ? " · " + esc(t("rptSoakIn", { s: r.note })) : ""}</div>` : "";
  $("#rptbody").innerHTML = `<div>${esc(r.text || t("insStarting"))}</div>${r.total ? `<progress max="${r.total}" value="${r.i || 0}" style="width:100%"></progress>` : ""}${pick}${done}${r.err ? `<div class="notice bad">${esc(r.err)}</div>` : ""}`;
  $("#rptcancel").hidden = !r.running; $("#rptdl").hidden = !(r.built && r.file && !r.running); $("#rptclose").hidden = r.running;
}
function rptOpen() {
  const d = $("#rptdlg"); $("#rpttitle").textContent = t("rptBtn"); $("#rptcancel").textContent = t("insCancel"); $("#rptdl").textContent = t("rptFile"); $("#rptclose").textContent = t("close");
  if (!d.open) { if (d.showModal) d.showModal(); else d.setAttribute("open", ""); }
  rptPaint();
}

/* ---- module danger: set slave id, software reset ---- */
async function modSetId() {
  const m = S.mod; if (!m.id) return;
  const typed = await ask(t("setIdAsk", { id: m.dev }), false, true); if (typed === null) return;
  const raw = typed.trim(), nid = Number(raw);
  if (raw === "" || !Number.isInteger(nid) || nid < 1 || nid > 247 || nid === 246) { await ask(t("setIdRange"), true); return; }
  if (nid === m.dev) return;
  if (!(await ask(t("setIdQ", { from: m.dev, to: nid })))) return;
  toast(t("setIdBusy"));
  // the typed id is the confirmation the server checks for
  const r = await api("POST", "/api/v2/mod/setid", { id: m.id, device_id: m.dev, new_id: nid, confirm: String(nid) });
  if (!r.ok) throw new Error(r.error || "failed");
  m.dev = nid; m.data = null; toast(t("setIdDone", { id: nid })); await modRead();
}
async function modReset() {
  const m = S.mod; if (!m.id) return;
  const typed = await ask(t("resetQ", { id: m.dev }), false, true, String(m.dev)); if (typed === null) return;
  toast(t("resetBusy"));
  const r = await api("POST", "/api/v2/mod/reset", { id: m.id, device_id: m.dev, confirm: typed });
  if (!r.ok) throw new Error(r.error || "failed");
  toast(t("resetDone")); await modRead();
}
function dangerView() {
  return `<div class="row" style="gap:8px;align-items:center"><button class="btn" data-act="mod-setid" style="color:var(--bad)">${t("setIdBtn")}</button>
    <button class="btn" data-act="mod-reset" style="color:var(--bad)">${t("resetBtn")}</button></div>`;
}

/* ---- settings dialog: this PC as NTP server, web password ---- */
async function srvSettings() {
  const el = $("#setsrv"); if (!el) return;
  if (uiMode !== "advanced") { el.innerHTML = ""; return; }
  let n = null; try { n = await api("GET", "/api/v2/ntp"); } catch (e) { /* shown as off */ }
  const on = !!(n && n.enabled), pw = !!(S.me && S.me.auth), c = (S.me && S.me.collector) || {};
  const ntpChip = !n ? "" : n.running ? `<span class="chip ok">${t("ntpChipOn", { port: n.port })}</span>` : on && n.error ? `<span class="chip bad">${t("ntpChipErr")}</span>` : `<span class="chip off">${t("optOff")}</span>`;
  const ntpNote = !n || n.running ? "" : on && n.error ? n.error : "";
  /* Two separate blocks, each a heading with its state as a chip on the right: the state is not a second label. */
  el.innerHTML = `<div class="setsec"><div class="row between"><b>${t("ntpTitle")}</b>${ntpChip}</div>
      <div class="row" style="gap:8px;align-items:center;flex-wrap:nowrap"><select id="ntpon" style="flex:1;min-width:0"><option value="0"${on ? "" : " selected"}>${t("optOff")}</option><option value="1"${on ? " selected" : ""}>${t("optOn")}</option></select>
        <input id="ntpport" type="number" min="1" max="65535" value="${n ? n.port : 123}" style="width:96px" aria-label="${t("ntpPort")}" title="${t("ntpPort")}"></div>
      ${ntpNote ? `<div class="small ${on && n.error && !n.running ? "" : "muted"}"${on && n.error && !n.running ? ' style="color:var(--bad)"' : ""}>${esc(ntpNote)}</div>` : ""}</div>
    <div class="setsec"><div class="row between"><b>${t("collect")}</b>${colChip(c)}</div>
      <div class="row" style="gap:8px;align-items:center;flex-wrap:nowrap"><select id="colon" style="flex:1;min-width:0"><option value="0"${c.enabled ? "" : " selected"}>${t("optOff")}</option><option value="1"${c.enabled ? " selected" : ""}>${t("optOn")}</option></select>
        <select id="colkeep" style="width:120px" aria-label="${t("colKeep")}" title="${t("colKeep")}">${[30, 90, 180, 365].map((d) => `<option value="${d}"${d === (c.retention_days || 90) ? " selected" : ""}>${t("dayN", { n: d })}</option>`).join("")}</select></div></div>
    <div class="setsec"><div class="row between"><b>${t("pwTitle")}</b><span class="chip ${pw ? "ok" : "warn"}">${t(pw ? "pwChipOn" : "pwChipOff")}</span></div>
      ${pw ? `<input id="pw0" type="password" autocomplete="current-password" placeholder="${t("pwCurrent")}">` : ""}<input id="pw1" type="password" autocomplete="new-password" placeholder="${t("pwNew")}"><input id="pw2" type="password" autocomplete="new-password" placeholder="${t("pwRepeat")}">
      <div class="row" style="gap:8px"><button class="btn" data-act="pw-set" type="button">${t("pwSet")}</button>${pw ? `<button class="btn" data-act="pw-clear" type="button" style="color:var(--bad)">${t("pwClear")}</button>` : ""}</div></div>`;
}
async function colApply(el) {
  const c = (S.me && S.me.collector) || {}, was = c.retention_days || 90, want = +$("#colkeep").value;
  try {
    if (el.id === "colkeep" && want < was && !(await ask(t("colKeepQ", { n: want })))) { el.value = was; return; }
    const r = await api("POST", "/api/v2/collector", el.id === "colon" ? { enabled: el.value === "1" } : { retention_days: want });
    if (r.error) throw new Error(r.error);
    S.me = await api("GET", "/api/v2/me"); S.ev.from = S.ev.to = "";
  } catch (e) { fail(e); }
  srvSettings(); if (page === "events") render();
}
async function ntpApply() {
  try { await api("POST", "/api/v2/ntp", { enabled: $("#ntpon").value === "1", port: +$("#ntpport").value }); } catch (e) { fail(e); }
  srvSettings();
}

const fmtDur = (sec) => { sec = Math.max(0, Math.round(sec)); const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60); return h ? `${h} ${t("h")} ${m} m` : `${m} m ${sec % 60} s`; };
/* The verdict is a plain-text report written by the engine (and kept as a file for the classic tool). It is read back from
   that text into a small model (one headline, the cabinet table, the gateway table, a few notes) and drawn twice: as HTML on
   the page and as a PNG on a canvas. Colour on what needs a look; what the columns mean lives behind the ? button. */
function verdictModel(txt) {
  const lines = String(txt).split("\n");
  const num = (v) => Number(String(v).replace(/,/g, "")) || 0;
  const head = /^fleet soak\s+(.*)$/.exec(lines[0] || "");
  const ran = /ran for ([\d.]+) h(\s+\(stopped early\))?\s+client timeout ([\d.]+) s/.exec(lines[1] || "");
  const cleanM = /^(\d+) of (\d+) cabinets completely clean/m.exec(txt);
  const cabs = [], gws = [];
  let wrong = null, noGw = "";
  for (const ln of lines) {
    if (/^(cabinet|-{5,})/.test(ln.trim()) || !ln.trim()) continue;
    let m = /^(\S+)\s+(\d+)\s+--\s*did not run\s*--\s*(.*)$/.exec(ln);
    if (m) { cabs.push({ name: m[1], dnr: true, note: m[3].trim() }); continue; }
    m = /^gateway counters not available[^:]*:\s*(.*)$/.exec(ln);
    if (m) { noGw = m[1].trim(); continue; }
    m = /^(\S+)\s+(\d+)\s+(\d+)\s+([\d,]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.+)$/.exec(ln);
    if (m && !/^\s/.test(ln)) { cabs.push({ name: m[1], mod: m[2], pass: m[3], reads: m[4], fail: num(m[5]), rbt: num(m[6]), wdt: num(m[7]), cross: m[8], worst: num(m[9]), drop: m[10], silent: m[11].trim() }); continue; }
    m = /^\s+(\S+)\s+repaired\s+(\d+)\s+\(([\d.]+)\/h\)\s+repair failed\s+(\d+)\s+final timeouts\s+(\d+)\s+bad crc\s+(\d+)\s+other\s+(\d+)(.*)$/.exec(ln);
    if (m) { gws.push({ name: m[1], rep: num(m[2]), perh: m[3], rfail: num(m[4]), to: num(m[5]), crc: num(m[6]), other: num(m[7]), rest: m[8] }); continue; }
    m = /reply frames discarded as the wrong unit id:\s*(none|\d+)/.exec(ln);
    if (m) wrong = m[1] === "none" ? 0 : Number(m[1]);
  }
  const lvl = (bad, warn) => (bad ? "bad" : warn ? "warn" : "ok");
  const cell = (v, bad, warn) => ({ v: String(v), n: true, cls: bad ? "vbad" : warn ? "vwarn" : v === 0 || v === "0" ? "vzero" : "" });
  const total = cleanM ? Number(cleanM[2]) : cabs.length, clean = cleanM ? Number(cleanM[1]) : 0;
  const level = clean < total ? "bad" : gws.some((g) => g.rep || g.other || /warn/.test(g.rest)) ? "warn" : "ok";
  return {
    started: head ? head[1].trim() : "", ran: ran ? { h: ran[1], to: ran[3], early: !!ran[2] } : null, clean, total, level, noGw, wrong,
    cabHead: ["cabinet", "mod", "pass", "reads", "fail", "rbt", "wdt", "cross", "worst", "drop", "silent ids"],
    cabs: cabs.map((c) => {
      if (c.dnr) return { name: c.name, level: "bad", rowBad: false, dnr: true, note: c.note, cells: [] };
      const bad = !!(c.fail || c.rbt || c.wdt || c.silent !== "none");
      return { name: c.name, level: lvl(bad, c.worst >= 1000), rowBad: bad, cells: [
        cell(c.mod, 0, 0), cell(c.pass, 0, 0), cell(c.reads, 0, 0), cell(c.fail, c.fail), cell(c.rbt, c.rbt), cell(c.wdt, c.wdt), cell(c.cross, 0, 0),
        cell(c.worst, false, c.worst >= 1000), { v: c.drop, n: true, cls: "vzero" }, { v: c.silent, n: false, cls: c.silent !== "none" ? "vbad" : "vzero" }] };
    }),
    gwHead: [t("sCab"), t("sRepaired"), t("sRepairedH"), t("sRepairFailed"), t("sFinalTo"), t("sBadCrc"), t("sOther")],
    gws: gws.map((g) => {
      const bad = !!(g.rfail || g.to || g.crc || /NOT CLEAN/.test(g.rest)), warn = !!(g.rep || g.other || /warn/.test(g.rest));
      const rb = /gateway restarted (\d+)x/.exec(g.rest);
      return { name: g.name, level: lvl(bad, warn), rowBad: bad, restart: rb ? rb[1] : "", cells: [
        cell(g.rep, false, g.rep), { v: g.perh, n: true, cls: /warn/.test(g.rest) ? "vwarn" : g.rep ? "" : "vzero" }, cell(g.rfail, g.rfail), cell(g.to, g.to), cell(g.crc, g.crc), cell(g.other, false, g.other)] };
    }),
  };
}
function verdictHtml(txt, inCard) {
  const m = verdictModel(txt);
  const dot = (l) => `<i class="vdot ${l}"></i>`;
  const th = (c, n) => `<th${n ? ' class="num"' : ""}>${esc(c)}</th>`;
  const td = (c) => `<td class="${c.n ? "num " : ""}${c.cls}">${esc(c.v)}</td>`;
  let out = `<div class="vhead"><span class="chip ${m.level}"><i class="dot"></i>${t("vClean", { a: m.clean, b: m.total })}</span>`
    + `<span class="small muted">${m.ran ? t("vMeta", { h: m.ran.h, to: m.ran.to }) + (m.ran.early ? " · " + t("vEarly") : "") : ""}${m.started ? " · " + esc(m.started) : ""}</span></div>`;
  if (!inCard && t("soakColsTxt")) out += `<details class="collg"><summary class="why" aria-label="${t("explain")}">?</summary><div class="small muted" style="white-space:pre-line">${esc(t("soakColsTxt"))}</div></details>`;
  out += `<div style="overflow-x:auto"><table class="evtab"><tr>${m.cabHead.map((c, i) => th(c, i > 0 && i < 10)).join("")}</tr>`
    + m.cabs.map((c) => c.dnr
      ? `<tr><td>${dot("bad")}<b>${esc(c.name)}</b></td><td colspan="10" class="vbad">${t("sDidNot")}${c.note ? ` <span class="small">${esc(c.note)}</span>` : ""}</td></tr>`
      : `<tr class="${c.rowBad ? "vrow bad" : ""}"><td>${dot(c.level)}<b>${esc(c.name)}</b></td>${c.cells.map(td).join("")}</tr>`).join("") + "</table></div>";
  if (m.gws.length) {
    out += `<div class="vsub">${t("vGw")}</div><div style="overflow-x:auto"><table class="evtab"><tr>${m.gwHead.map((c, i) => th(c, i > 0)).join("")}</tr>`
      + m.gws.map((g) => `<tr class="${g.rowBad ? "vrow bad" : ""}"><td>${dot(g.level)}<b>${esc(g.name)}</b>${g.restart ? ` <span class="small vwarn">${t("vRestart", { n: g.restart })}</span>` : ""}</td>${g.cells.map(td).join("")}</tr>`).join("") + "</table></div>";
  }
  if (m.noGw) out += `<div class="small vwarn">${t("vNoGw", { names: esc(m.noGw) })}</div>`;
  if (m.wrong !== null) out += `<div class="small ${m.wrong ? "vwarn" : "muted"}">${t("vWrong", { n: m.wrong })}</div>`;
  return out;
}
/* The same verdict drawn on a canvas, to save as a picture: white background and light colours (not the page's theme), the
   page's font, two times the size so it stays sharp when pasted into a report. Resolves to a PNG blob. */
function verdictPng(txt) {
  const m = verdictModel(txt), body = getComputedStyle(document.body);
  // a picture for a report: always white paper and the light-theme colours, whatever theme the page is in
  const C = { ink: "#1b2430", muted: "#6b7785", line: "#dfe4ea", bg: "#ffffff", ok: "#0f8a4f", warn: "#9a6700", bad: "#c62828", okbg: "#e3f4ea", warnbg: "#fff1d6", badbg: "#fde7e7" };
  const font = body.fontFamily || "sans-serif", PAD = 28, RH = 32, S = 2;
  const lvlColor = (l) => (l === "bad" ? C.bad : l === "warn" ? C.warn : C.ok);
  const cabW = [170, 60, 70, 96, 60, 60, 60, 76, 76, 60], gwW = [260, 120, 100, 130, 150, 110, 100];
  // the picture is as wide as its widest table (or note line), not a fixed size: measure first
  const mc = document.createElement("canvas").getContext("2d");
  const mw = (str, px, bold) => { mc.font = `${bold ? "600 " : ""}${px}px ${font}`; return mc.measureText(String(str)).width; };
  const cabBase = cabW.reduce((a, b) => a + b, 0), gwBase = gwW.reduce((a, b) => a + b, 0);
  const silentW = Math.max(110, ...m.cabs.filter((c) => !c.dnr).map((c) => mw(c.cells[9].v, 14) + 24));
  const dnrW = Math.max(0, ...m.cabs.filter((c) => c.dnr).map((c) => cabW[0] + mw(t("sDidNot") + (c.note ? " " + c.note : ""), 14, 1) + 16));
  const noteW = Math.max(0, m.noGw ? mw(t("vNoGw", { names: m.noGw }), 13) : 0, m.wrong !== null ? mw(t("vWrong", { n: m.wrong }), 13) : 0);
  const titleW = Math.max(mw(t("soak_page"), 22, 1), mw([m.ran ? t("vMeta", { h: m.ran.h, to: m.ran.to }) + (m.ran.early ? " · " + t("vEarly") : "") : "", m.started].filter(Boolean).join(" · "), 13));
  const tableW = Math.max(cabBase + silentW, gwBase, dnrW, noteW, titleW);
  const W = Math.ceil(tableW + PAD * 2);
  cabW.push(tableW - cabBase);                 // the last column takes what is left, so both tables end at the same edge
  gwW[0] += tableW - gwBase;
  const rows = (m.cabs.length + 1) + (m.gws.length ? m.gws.length + 1 : 0);
  const notes = (m.noGw ? 1 : 0) + (m.wrong !== null ? 1 : 0);
  const H = PAD * 2 + 34 + 26 + 44 + rows * RH + (m.gws.length ? 44 : 0) + notes * 26 + 10;
  const cv = document.createElement("canvas"); cv.width = W * S; cv.height = H * S;
  const g = cv.getContext("2d"); g.scale(S, S); g.textBaseline = "middle";
  g.fillStyle = C.bg; g.fillRect(0, 0, W, H);
  const txtAt = (s, x, y, o) => { g.font = `${o && o.b ? "600 " : ""}${(o && o.size) || 14}px ${font}`; g.fillStyle = (o && o.color) || C.ink; g.textAlign = (o && o.align) || "left"; g.fillText(String(s), x, y); };
  let y = PAD;
  txtAt(t("soak_page"), PAD, y + 17, { b: 1, size: 22 }); y += 34;
  txtAt([m.ran ? t("vMeta", { h: m.ran.h, to: m.ran.to }) + (m.ran.early ? " · " + t("vEarly") : "") : "", m.started].filter(Boolean).join(" · "), PAD, y + 8, { size: 13, color: C.muted }); y += 26;
  const chipTxt = t("vClean", { a: m.clean, b: m.total });
  g.font = `600 15px ${font}`; const cw = g.measureText(chipTxt).width + 44;
  g.fillStyle = m.level === "bad" ? C.badbg : m.level === "warn" ? C.warnbg : C.okbg; g.beginPath(); g.roundRect(PAD, y, cw, 32, 16); g.fill();
  g.fillStyle = lvlColor(m.level); g.beginPath(); g.arc(PAD + 15, y + 16, 4, 0, 7); g.fill();
  txtAt(chipTxt, PAD + 26, y + 17, { b: 1, size: 15, color: lvlColor(m.level) }); y += 44;
  const drawTable = (head, body, widths, numFrom, numTo) => {
    const tw = widths.reduce((a, b) => a + b, 0);
    let x = PAD;
    head.forEach((h, i) => { const num = i >= numFrom && i < numTo; txtAt(h, num ? x + widths[i] - 10 : x + 8, y + RH / 2, { size: 12, color: C.muted, align: num ? "right" : "left" }); x += widths[i]; });
    y += RH; g.strokeStyle = C.line; g.lineWidth = 1; g.beginPath(); g.moveTo(PAD, y - 0.5); g.lineTo(PAD + tw, y - 0.5); g.stroke();
    for (const r of body) {
      if (r.rowBad) { g.fillStyle = C.badbg; g.fillRect(PAD, y, tw, RH); }
      g.fillStyle = lvlColor(r.level); g.beginPath(); g.arc(PAD + 14, y + RH / 2, 4, 0, 7); g.fill();
      txtAt(r.name, PAD + 26, y + RH / 2, { b: 1 });
      if (r.dnr) txtAt(t("sDidNot") + (r.note ? " " + r.note : ""), PAD + widths[0], y + RH / 2, { color: C.bad, b: 1 });
      else {
        let cx = PAD + widths[0];
        r.cells.forEach((c, i) => {
          const w = widths[i + 1], col = c.cls === "vbad" ? C.bad : c.cls === "vwarn" ? C.warn : c.cls === "vzero" ? C.muted : C.ink;
          txtAt(c.v, c.n ? cx + w - 10 : cx + 8, y + RH / 2, { color: col, b: c.cls === "vbad" || c.cls === "vwarn", align: c.n ? "right" : "left" }); cx += w;
        });
      }
      y += RH; g.strokeStyle = C.line; g.beginPath(); g.moveTo(PAD, y - 0.5); g.lineTo(PAD + tw, y - 0.5); g.stroke();
    }
  };
  drawTable(m.cabHead, m.cabs, cabW, 1, 10);
  if (m.gws.length) {
    y += 14; txtAt(t("vGw"), PAD, y + 8, { b: 1, size: 15 }); y += 30;
    drawTable(m.gwHead, m.gws.map((r) => ({ ...r, name: r.name + (r.restart ? "  " + t("vRestart", { n: r.restart }) : "") })), gwW, 1, 7);
  }
  y += 8;
  if (m.noGw) { txtAt(t("vNoGw", { names: m.noGw }), PAD, y + 8, { size: 13, color: C.warn }); y += 26; }
  if (m.wrong !== null) txtAt(t("vWrong", { n: m.wrong }), PAD, y + 8, { size: 13, color: m.wrong ? C.warn : C.muted });
  return new Promise((res) => cv.toBlob(res, "image/png"));
}
/* Continuous test, in the same four numbered steps as the installation check: what kind, which cabinets, how long, go.
   While a run is going the steps give way to its live status. */
const SOAK_HOURS = [1, 2, 4, 6, 8, 10, 12, 24, 48, 72];
/* The "view summary" dialog of a past run: the summary (and a button to save it as a picture) on top, the raw data below. */
function soakViewDraw() {
  const w = S.soak.view; if (!w) return;
  const sum = w.txt ? `<div class="row" style="gap:8px;margin-bottom:12px"><button class="btn sm" type="button" data-act="soak-png">${t("sSaveImg")}</button></div><div class="soakv">${verdictHtml(w.txt)}</div>` : `<p class="muted">${t("sNoVerdict")}</p>`;
  const raw = w.cabs.length ? `<div class="soakraw"><div class="vsub">${t("sRawData")}</div>
    <div class="row" style="gap:8px"><button class="btn sm" type="button" data-act="soak-pick-all">${t("sAll")}</button><button class="btn sm" type="button" data-act="soak-pick-none">${t("insClear")}</button><span id="soakexpn" class="small muted">${t("sRawN", { n: w.pick.size, m: w.cabs.length })}</span></div>
    <div class="cabgrid soakexp">${w.cabs.map((c) => `<label class="chk"><input type="checkbox" data-expcab="${esc(c)}"${w.pick.has(c) ? " checked" : ""}> ${esc(c)}</label>`).join("")}</div>
    <div class="row between soakexpbar" style="flex-wrap:wrap;gap:12px"><div class="row" style="gap:12px;align-items:center"><span class="small muted">${t("sFmtLbl")}</span><div class="segctl" role="group">${["csv", "zip"].map((f) => `<button type="button" data-act="soak-fmt" data-f="${f}" aria-pressed="${w.fmt === f}">${t(f === "csv" ? "sFmtCsv" : "sFmtZip")}</button>`).join("")}</div></div><button class="btn primary" type="button" data-act="soak-dl"${w.pick.size ? "" : " disabled"}>${t("sDownload")}</button></div></div>` : "";
  $("#infobody").innerHTML = `<div style="max-height:72vh;overflow:auto;display:grid;gap:16px;padding:4px 6px">${sum}${raw}</div>`;
}
function soakViewSync() {
  const w = S.soak.view; if (!w) return;
  document.querySelectorAll("#infobody [data-expcab]").forEach((el) => { el.checked = w.pick.has(el.dataset.expcab); });
  const dl = document.querySelector('#infobody [data-act="soak-dl"]'); if (dl) dl.disabled = !w.pick.size;
  const n = $("#soakexpn"); if (n) n.textContent = t("sRawN", { n: w.pick.size, m: w.cabs.length });
  document.querySelectorAll('#infobody [data-act="soak-fmt"]').forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.f === w.fmt)));
}
function soakAdvWarn() {
  const k = S.soak, w = [];
  if (k.gap >= 0.4 && k.gap <= 0.9) w.push(t("sGapWarn"));
  if (k.tmo < 6) w.push(t("sTmoWarn"));
  return w.map(esc).join("<br>");
}
/* When the run would start and end, from the page's own choices (the server keeps its own rule: a clock time already past means tomorrow). */
function soakPlan() {
  const k = S.soak, now = new Date();
  const next = (h, m, after) => { const d = new Date(after); d.setHours(h, m, 0, 0); if (d <= after) d.setDate(d.getDate() + 1); return d; };
  const start = k.startMode === "at" ? next(k.sh, k.sm, now) : now;
  const hours = k.durMode === "until" ? Math.round(((next(k.eh, k.em, start) - start) / 3600000) * 100) / 100 : k.hours;
  return { start, hours, end: hours ? new Date(start.getTime() + hours * 3600000) : null };
}
function soakWhen(d) {
  const day = ymd(d) === ymd(new Date()) ? t("sToday") : ymd(d) === ymd(new Date(Date.now() + 86400000)) ? t("sTomorrow") : fmtDay(ymd(d));
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")} ${day}`;
}
/* The two numbers a pharmacy run is judged by before it starts, from the server (same functions as the classic page):
   windows lit at once = picks/day / 86400 x dwell, against what the smallest chosen cabinet can hold, and the share of
   every day the bus spends on picks. Colour: grey = fine or thin, green = exercises several windows, amber = a lot, red = too much. */
function soakCalcHtml() {
  const e = S.soak.est; if (!e) return "";
  const line = (text, tone) => `<div class="small" style="color:var(--${tone})">${esc(text)}</div>`;
  const rate = fmtN(S.soak.picks), pct = Math.round(e.duty * 100);
  let conc, ct;
  if (e.concurrent >= e.capacity) { conc = t("sFull", { cap: e.capacity }); ct = "bad"; }
  else if (e.concurrent >= e.capacity * 0.5) { conc = t("sConc", { n: e.concurrent.toFixed(1), cap: e.capacity }) + " · " + t("sCrowded"); ct = "warn"; }
  else if (e.concurrent < 1) { conc = t("sConc", { n: e.concurrent.toFixed(2), cap: e.capacity }) + " · " + t("sThin"); ct = "muted"; }
  else { conc = t("sConc", { n: e.concurrent.toFixed(1), cap: e.capacity }); ct = "ok"; }
  let duty = t("sDuty", { pct, rate }), dt = "muted";
  if (e.duty >= 1) { duty += " · " + t("sDutyOver"); dt = "bad"; } else if (e.duty >= 0.25) { duty += " · " + t("sDutyHot"); dt = "warn"; }
  return line(conc, ct) + line(duty, dt);
}
async function soakEstimate() {
  clearTimeout(soakEstimate.t);
  soakEstimate.t = setTimeout(async () => {
    const k = S.soak; if (page !== "soak" || k.mode !== "pharmacy" || !k.sel.size) { k.est = null; const el0 = $("#soakcalc"); if (el0) el0.innerHTML = ""; return; }
    try {
      const mine = (soakEstimate.n = (soakEstimate.n || 0) + 1);
      const r = await api("POST", "/api/v2/soak/estimate", { ids: [...k.sel], picks: k.picks, dwell_s: k.dwell, windows: k.windows });
      if (mine !== soakEstimate.n) return;
      k.est = r; const el = $("#soakcalc"); if (el) el.innerHTML = soakCalcHtml();
    } catch (e) { /* the reading is a convenience; the run does not depend on it */ }
  }, 250);
}
function viewSoak() {
  const k = S.soak, st = k.status || {};
  const running = !!st.running;
  const chip = (state) => { const cls = { clean: "ok", warn: "warn", "not clean": "bad", "did not run": "bad", starting: "info" }[state] || "info"; const key = { clean: "sClean", warn: "sWarn", "not clean": "sNotClean", "did not run": "sDidNot", starting: "sStarting" }[state]; return `<span class="chip ${cls}"><i class="dot"></i>${t(key || "sStarting")}</span>`; };
  const step = (n, title, body, extra) => `<div class="istep"><div class="row" style="gap:8px;align-items:center"><span class="inum">${n}</span><b>${title}</b>${extra || ""}</div>${body}</div>`;
  const sel = (id, opts, cur) => `<select id="${id}">${opts.map(([v, l]) => `<option value="${v}"${String(v) === String(cur) ? " selected" : ""}>${l}</option>`).join("")}</select>`;
  const pad = (n) => String(n).padStart(2, "0");
  const withClock = (main, show, idh, idm, h, m) => `<div class="row" style="gap:6px;flex-wrap:nowrap"><div style="flex:2;min-width:0">${main}</div>${show ? `<div style="flex:1;min-width:0">${sel(idh, Array.from({ length: 24 }, (_, i) => [i, pad(i)]), h)}</div><b>:</b><div style="flex:1;min-width:0">${sel(idm, Array.from({ length: 60 }, (_, i) => [i, pad(i)]), m)}</div>` : ""}</div>`;
  let head = "";
  if (running) {
    const when = st.starts_in_s != null ? t("sArmed", { t: fmtDur(st.starts_in_s) }) : (st.left_s != null ? t("sLeft", { t: fmtDur(st.left_s) }) : t("sNoEnd"));
    head = `<section class="card stack"><div class="row between"><div><b>${t("sRunning")}</b> · ${t("sCabs", { n: st.count })} · ${esc(when)}</div><button class="btn" style="color:var(--bad)" data-act="soak-stop">${t("sStop")}</button></div>
      <div class="small muted">${t("sLongNote")}${st.frames_discarded ? " · " + t("sFrames", { n: st.frames_discarded }) : ""}</div></section>`;
  } else {
    const modes = ["pharmacy", "poll"].map((m) => `<button class="btn${k.mode === m ? " primary" : ""}" type="button" data-act="soak-mode" data-m="${m}" aria-pressed="${k.mode === m}">${t(m === "pharmacy" ? "sPharm" : "sPoll")}</button>`).join("");
    const cells = S.sites.map((x) => {
      const ok = !!x.cabinet, on = k.sel.has(x.id);
      return `<button class="cabcell${on ? " on" : ""}" type="button" data-cab="${esc(x.id)}" aria-pressed="${on}"${ok ? "" : " disabled"}><b>${esc(x.name)}</b><span>${ok ? esc(x.host) : t("sNoType")}</span></button>`;
    }).join("");
    const plan = soakPlan();
    const planText = t("sPlan", { s: k.startMode === "at" ? soakWhen(plan.start) : t("sNow"), e: plan.end ? soakWhen(plan.end) : t("sEndOnStop") });
    const durOpts = [...SOAK_HOURS.map((h) => [h, t("sHoursN", { n: h })]), ["until", t("sUntilTime")], [0, t("sUntilStop")]];
    const settings = `<div class="fgrid">
        <div class="field"><label>${t("sStartLbl")}</label>${withClock(sel("soakstart", [["now", t("sNow")], ["at", t("sAtTime")]], k.startMode), k.startMode === "at", "soaksh", "soaksm", k.sh, k.sm)}</div>
        <div class="field"><label>${t("sDur")}</label>${withClock(sel("soakdur", durOpts, k.durMode === "until" ? "until" : k.hours), k.durMode === "until", "soakeh", "soakem", k.eh, k.em)}</div>
        ${k.mode === "pharmacy" ? `<div class="field"><label>${t("sPicks")}${infoBtn("soakPicks")}</label><input id="soakpicks" type="number" min="1" max="200000" value="${k.picks}"></div>
        <div class="field"><label>${t("sDwell")}${infoBtn("soakDwell")}</label><input id="soakdwell" type="number" min="1" max="3600" value="${k.dwell}"></div>
        <div class="field"><label>${t("sWins")}${infoBtn("soakWins")}</label><input id="soakwins" type="number" min="1" max="8" value="${k.windows}"></div>` : ""}</div>
      ${k.mode === "pharmacy" ? `<div id="soakcalc" class="stack tight">${soakCalcHtml()}</div>` : ""}
      <details class="advbox" id="soakadv"${k.adv ? " open" : ""}><summary>${t("sAdv")}</summary><div class="fgrid" style="margin-top:10px">
        <div class="field"><label>${t("sGap")}${infoBtn("soakGap")}</label><input id="soakgap" type="number" min="0.1" max="30" step="0.5" value="${k.gap}"></div>
        <div class="field"><label>${t("sEvery")}${infoBtn("soakEvery")}</label><input id="soakevery" type="number" min="1" max="100" value="${k.every}"></div>
        <div class="field"><label>${t("sSlow")}${infoBtn("soakSlow")}</label><input id="soakslow" type="number" min="50" max="5000" value="${k.slow}"></div>
        <div class="field"><label>${t("sTmo")}${infoBtn("soakTmo")}</label><input id="soaktmo" type="number" min="4" max="30" step="0.5" value="${k.tmo}"></div></div>
        <div id="soakadvwarn" class="small vwarn">${soakAdvWarn()}</div></details>`;
    head = `<section class="card stack">
      ${step(1, t("sStep1"), `<div class="row" style="gap:8px">${modes}</div>`)}
      ${step(2, t("sStep2"), `<div class="row" style="gap:8px"><button class="btn" type="button" data-act="soak-all">${t("sAll")}</button><button class="btn" type="button" data-act="soak-none">${t("insClear")}</button></div>
        ${S.sites.length ? `<div class="cabgrid">${cells}</div>` : `<p class="muted">${t("noSites")}</p>`}`, `<span class="small muted">${t("insSel", { n: k.sel.size })}</span>`)}
      ${step(3, t("sStep3"), settings)}
      ${step(4, t("sStep4"), `<div class="small muted">${esc(planText)}</div><div class="row" style="gap:8px"><button class="btn primary" type="button" data-act="soak-start">${t("sStart")}</button></div>`)}
    </section>`;
  }
  const pharm = (st.cabinets || []).some((c) => c.writes || c.picks);
  const picksCell = (c) => `${t("sPicksLive", { n: fmtN(c.picks), lit: c.lit })}${c.dropped ? ` · ${t("sPicksDropped", { n: c.dropped })}` : ""}${c.write_fails ? ` · ${t("sWriteFail", { n: c.write_fails })}` : ""}`;
  const cabs = (st.cabinets || []).length ? `<section class="card" style="overflow-x:auto"><table><tr><th>${t("sCab")}</th><th>${t("sState")}</th><th>${t("sReads")}</th>${pharm ? `<th>${t("sPicksCol")}${infoBtn("soakPickCol")}</th>` : ""}<th>${t("sFails")}</th><th>${t("sRbt")}</th><th>${t("sWdt")}</th><th>${t("sWorst")}</th><th>${t("sHeal")}${infoBtn("soakHealCol")}</th></tr>
    ${st.cabinets.map((c) => `<tr><td><b>${esc(c.name)}</b>${c.note ? `<div class="tiny" style="color:var(--bad)">${esc(c.note)}</div>` : ""}</td><td>${chip(c.state)}</td><td>${c.reads.toLocaleString()}</td>${pharm ? `<td>${picksCell(c)}</td>` : ""}<td>${c.fails}</td><td>${c.reboots}</td><td>${c.watchdogs}</td><td>${c.worst_ms}</td>
      <td>${c.gw_seen ? `fix ${c.gw_healed} · ${c.heal_per_h}/h${c.gw_heal_failed ? ` · fail ${c.gw_heal_failed}` : ""}${c.gw_timeouts ? ` · to ${c.gw_timeouts}` : ""}${c.gw_bad_crc ? ` · crc ${c.gw_bad_crc}` : ""}` : "—"}</td></tr>`).join("")}</table></section>` : "";
  S.soak.anP = Math.min(S.soak.anP, Math.max(0, Math.ceil((st.anomalies || []).length / 5) - 1));
  const an = (st.anomalies || []).length ? `<section class="card stack"><h3>${t("sAnoms")}</h3>${st.anomalies.slice(S.soak.anP * 5, S.soak.anP * 5 + 5).map((a) => `<div class="evrow"><span class="when">${esc(a.at)}</span><span><b>${esc(a.cabinet)}</b> ${a.id ? "id " + a.id + " " : ""}${esc(a.kind)} ${esc(a.detail)}</span></div>`).join("")}${st.anomalies.length > 5 ? `<div class="row between"><button class="btn sm" type="button" data-act="soak-an-pg" data-d="-1"${S.soak.anP <= 0 ? " disabled" : ""}>‹ ${t("sNewer")}</button><span class="small muted">${t("sOfN", { a: S.soak.anP * 5 + 1, b: Math.min(S.soak.anP * 5 + 5, st.anomalies.length), n: st.anomalies.length })}</span><button class="btn sm" type="button" data-act="soak-an-pg" data-d="1"${(S.soak.anP + 1) * 5 >= st.anomalies.length ? " disabled" : ""}>${t("sOlder")} ›</button></div>` : ""}</section>` : "";
  const fin = st.finished && !running ? `<section class="card stack"><h3>${t("sVerdict")}${infoBtn("soakCols")}</h3><div class="soakv">${verdictHtml(st.finished.text, true)}</div></section>` : "";
  const runDate = (stamp) => { const m = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/.exec(stamp || ""); return m ? `${fmtDay(m[1])} ${m[2]}` : stamp; };
  const hist = `<section class="card stack"><h3>${t("sHistory")}</h3>${(k.runs || []).length ? `<div class="soakruns">${k.runs.map((r) => `<div class="soakrun"><div class="row between"><b>${esc(runDate(r.started))}</b>
      <button class="btn sm" type="button" data-act="soak-view" data-stamp="${esc(r.stamp)}">${t("sView")}</button></div></div>`).join("")}</div>` : `<p class="muted">${t("sNoRuns")}</p>`}</section>`;
  return `<h1>${t("soak_page")}</h1><div class="stack">${head}${cabs}${an}${fin}${hist}</div>`;
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
  return rows.length ? `<div style="overflow-x:auto"><table class="evtab"><tr><th>${t("sCab")}</th><th>${t("sState")}</th><th>${t("fwPhase")}</th><th>%</th><th>${t("fwLeft")}</th><th>${t("fwCensus")}</th></tr>
    ${rows.map((r) => `<tr><td><b>${esc(r.name)}</b> <span class="tiny muted">${esc(r.modules)}</span></td><td>${esc(r.state)}${r.channels ? ` <span class="tiny muted">${esc(r.channel)}/${esc(r.channels)}</span>` : ""}</td><td>${esc(r.phase)}</td><td>${esc(r.pct)}</td><td>${r.left.length ? esc(r.left.join(",")) : t("fwNone")}</td><td class="small">${esc(r.census || r.note)}</td></tr>`).join("")}</table></div>` : "";
}
function dpProgHtml() {
  const d = S.fw.dp, p = d.prog;
  if (!d.busy && d.op) {
    if (d.op === "fwOpLoad") return "";
    if (d.op === "fwOpKeep" && p && p.state === "reading" && p.total) {
      const q = Math.min(100, Math.round((p.done / p.total) * 100));
      return `<div class="pbar"><progress value="${p.done}" max="${p.total}"></progress><div class="ptxt"><span>${t(d.op)}</span><span><b>${q}%</b> · ${fmtN(p.done)} / ${fmtN(p.total)} B</span></div></div>`;
    }
    return `<div class="pbar"><progress></progress><div class="ptxt"><span>${t(d.op)}</span></div></div>`;
  }
  if (!d.busy) return "";
  if (!p || p.state === "idle" || !p.total) return `<div class="pbar"><progress></progress><div class="ptxt"><span>${t("fwDpStarting")}</span></div></div>`;
  const pct = Math.min(100, Math.round((p.done / p.total) * 100));
  if (p.state === "verifying") return `<div class="pbar"><progress></progress><div class="ptxt"><span>${t("fwDpVerify")}</span></div></div>`;
  return `<div class="pbar"><progress value="${p.done}" max="${p.total}"></progress><div class="ptxt"><span>${t("fwDpSend")}</span><span><b>${pct}%</b> · ${fmtN(p.done)} / ${fmtN(p.total)} B</span></div></div>`;
}
function fwCabTiles(set, sel) {
  if (!S.sites.length) return `<p class="muted">${t("noSites")}</p>`;
  return `<div><div class="flabel">${t("pick")}</div><div class="row" style="gap:8px;align-items:center;margin:4px 0 8px"><button class="btn" type="button" data-act="fw-tileall" data-set="${set}">${t("sAll")}</button><button class="btn" type="button" data-act="fw-tilenone" data-set="${set}">${t("insClear")}</button><span class="small muted">${t("insSel", { n: sel.size })}</span></div>
    <div class="cabgrid">${S.sites.map((x) => { const on = sel.has(x.id); return `<button class="cabcell${on ? " on" : ""}" type="button" data-act="fw-tile" data-set="${set}" data-id="${esc(x.id)}" aria-pressed="${on}"><b>${esc(x.name)}</b><span>${esc(x.host)}</span></button>`; }).join("")}</div></div>`;
}
const fwOpen = (k) => ((S.fw.open || {})[k] ? " open" : "");
// The fleet OTA report is plain text written for a file; show it in the page's own type and table style.
function fwOutcomeHtml(text) {
  const L = String(text || "").split("\n");
  const head = (L.shift() || "").trim().split(/\s{2,}/);
  const meta = [], rows = [], tail = [];
  let cols = null, inTable = false;
  for (const raw of L) {
    const ln = raw.trimEnd();
    if (!ln.trim()) { if (inTable && rows.length) inTable = false; continue; }
    if (/^-{5,}$/.test(ln.trim())) { inTable = true; continue; }
    if (/^cabinet\s/.test(ln)) { cols = ln.trim().split(/\s{2,}/); continue; }
    if (inTable) { rows.push(ln.trim().split(/\s{2,}/)); continue; }
    (cols ? tail : meta).push(ln.trim());
  }
  const bad = (c) => /^[^\d]*(\d+)\/(\d+)$/.exec(c) && RegExp.$1 !== RegExp.$2;
  const tbl = cols && rows.length ? `<div style="overflow-x:auto"><table class="evtab"><tr>${cols.map((c, i) => `<th${i && i < 4 ? ' class="num"' : ""}>${esc(c)}</th>`).join("")}</tr>${rows.map((r) => `<tr>${r.map((c, i) => `<td${i && i < 4 ? ' class="num"' : ""}${bad(c) ? ' class="num bad"' : ""}>${i === 0 ? "<b>" + esc(c) + "</b>" : esc(c)}</td>`).join("")}</tr>`).join("")}</table></div>` : "";
  return `<div class="vsub">${esc(head[0] || "")}${head[1] ? ` <span class="small muted">${esc(head[1])}</span>` : ""}</div>${meta.length ? `<div class="small muted">${meta.map(esc).join("<br>")}</div>` : ""}${tbl}${tail.length ? `<div class="small">${tail.map((x, i) => (i < tail.length - 1 ? esc(x) : `<span class="muted">${esc(x)}</span>`)).join("<br>")}</div>` : ""}`;
}
function viewFirmware() {
  const f = S.fw, im = f.images, ota = f.ota || {}, gw = f.gw || {};
  const sitesRows = fwCabTiles("ota", f.sel);
  const modImgs = im ? im.module.map((i) => `<option value="${esc(i.key)}"${i.key === f.image ? " selected" : ""}>${esc(i.version)}</option>`).join("") : "";
  const dpImgs = im ? im.module.map((i) => `<option value="${esc(i.key)}"${i.key === (f.dp.image || (im.module[0] || {}).key) ? " selected" : ""}>${esc(i.version)}</option>`).join("") : "";
  const gwImgs = im ? im.gateway.map((i) => `<option value="${esc(i.key)}"${i.key === f.gwImage ? " selected" : ""}>${esc(i.version)}</option>`).join("") : "";
  const gsite = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === f.gwId ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const gwOpts = (cur) => S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === cur ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  const doneSlots = (f.srcSlots || []).filter((x) => x.state === 2);
  const srcOpts = doneSlots.length ? doneSlots.map((x) => `<option value="${x.slot}"${x.slot === f.srcSlot ? " selected" : ""}>${esc(x.name)} · ${fmtN(x.size)} B</option>`).join("") : `<option value="-1">${f.srcId ? t("fwSrcNone") : "—"}</option>`;
  const dp = f.dp;
  const keptList = im ? im.module.filter((i) => i.kept) : [];
  const stateTxt = (x) => (x.state === 2 ? `<span class="chip ok"><i class="dot"></i>${t("fwDpOk")}</span>` : x.state === 1 ? `<span class="chip warn"><i class="dot"></i>${t("fwDpPartial")}</span>` : `<span class="muted small">${t("fwDpEmpty")}</span>`);
  const dpTable = dp.slots ? `<div style="overflow-x:auto${dp.op === "fwOpLoad" ? ";opacity:.4;filter:grayscale(1);pointer-events:none;transition:opacity .15s" : ""}"><table class="evtab"><tr><th>${t("fwDpSlot")}</th><th>${t("fwDpName")}</th><th class="num">${t("fwDpSize")}</th><th>CRC</th><th>${t("fwDpState")}</th><th></th></tr>${dp.slots.map((x) => `<tr><td>${x.slot + 1}</td><td>${x.state ? esc(x.name) : "—"}</td><td class="num">${x.state ? fmtN(x.size) + " B" : ""}</td><td class="mono small">${x.state === 2 ? x.crc.toString(16).toUpperCase().padStart(8, "0") : ""}</td><td>${stateTxt(x)}</td><td>${x.state === 2 ? `<button class="btn sm" type="button" data-act="fw-dpkeep" data-slot="${x.slot}"${dp.busy || dp.op ? " disabled" : ""}>${t("fwDpKeep")}</button> ` : ""}${x.state ? `<button class="btn sm" type="button" data-act="fw-dpdel" data-slot="${x.slot}" data-name="${esc(x.name)}"${dp.busy || dp.op ? " disabled" : ""}>${t("fwDpDel")}</button>` : ""}</td></tr>`).join("")}</table></div>` : "";
  const go = f.go;
  const goRows = (go.rows || []).filter((r) => go.sel.has(r.id));
  const goTable = goRows.length ? `<div style="overflow-x:auto"><table class="evtab"><tr><th>${t("fwGoCab")}</th><th>${t("fwGoState")}</th><th>${t("fwGoPhase")}</th><th class="num">${t("fwGoProg")}</th><th class="num">${t("fwGoWait")}</th><th class="num">${t("fwGoDone")}</th><th class="num">${t("fwGoFail")}</th><th class="num">${t("fwGoPaused")}</th><th></th></tr>${goRows.map((r) => {
    const o = r.ota || {}, run = o.state === "running" || o.state === "scheduled", bad = o.state === "done_with_failures" || o.state === "interrupted" || o.state === "unreachable" || o.state === "unsupported";
    const cls = o.state === "done_ok" ? "ok" : run ? "warn" : bad ? "bad" : "";
    return `<tr><td><b>${esc(r.name)}</b></td><td><span class="chip ${cls}"><i class="dot"></i>${t("fwGoS_" + (o.state || "none"))}</span></td><td class="small">${o.state === "scheduled" ? esc((o.window || "").replace("-", "–")) + (o.gate ? " · " + esc(TXT[lang]["fwGoGate_" + o.gate] ? t("fwGoGate_" + o.gate) : o.gate) : "") : run ? esc(TXT[lang]["fwGoP_" + o.phase] ? t("fwGoP_" + o.phase) : (o.phase || "")) : ""}</td><td class="num" title="${run && o.chunk ? esc(o.chunk) : ""}">${(() => { const q = o.state === "done_ok" ? 100 : run && +o.modules ? Math.min(100, Math.round((+o.applied || 0) / +o.modules * 100)) : -1; return q < 0 ? "" : `<div class="tpbar"><b>${q}%</b><progress value="${q}" max="100"></progress></div>`; })()}</td><td class="num">${run ? esc(o.verified || "0") : ""}</td><td class="num">${run ? esc(o.applied || "0") + (o.modules ? " / " + esc(o.modules) : "") : ""}</td><td class="num${run && +o.failed ? " vbad" : ""}">${run ? esc(o.failed || "0") : ""}</td><td class="num">${run ? esc(o.paused_s || "0") : ""}</td><td>${run ? "" : `<button class="btn sm" type="button" data-act="fw-goresult" data-id="${esc(r.id)}">${t("fwGoResult")}</button>`}</td></tr>`;
  }).join("")}</table></div>` : "";
  const goAnyRun = goRows.some((r) => ["running", "scheduled"].includes((r.ota || {}).state));
  const goBlock = `<details class="card fwsec" data-fwsec="go"${fwOpen("go")}><summary>${t("fwGo")}</summary><div class="stack">
    ${fwCabTiles("go", go.sel)}
    <div class="field"><label>${t("fwImage")}${infoBtn("goNote")}</label><select id="fwgoimage">${go.names.length ? go.names.map((n) => `<option value="${esc(n)}"${n === go.image ? " selected" : ""}>${esc(n)}</option>`).join("") : `<option value="">${t("fwGoNoImage")}</option>`}</select></div>
    <details class="advbox" id="fwgoadv"${go.adv ? " open" : ""}><summary>${t("fwGoAdv")}</summary><div class="fgrid" style="margin-top:10px">
      <div class="field"><label>${t("fwGoIdle")}</label><input id="fwgoidle" type="number" min="1" max="600" value="${go.opts.idle}"></div>
      <div class="field"><label>${t("fwGoGroup")}</label><input id="fwgogroup" type="number" min="1" max="8" value="${go.opts.group}"></div>
      <div class="field"><label>${t("fwGoApplyIdle")}</label><input id="fwgoapplyidle" type="number" min="1" max="3600" value="${go.opts.apply_idle}"></div>
      <div class="field"><label>${t("fwGoApplyQuiet")}</label><input id="fwgoapplyquiet" type="number" min="0" max="86400" value="${go.opts.apply_quiet}"></div></div></details>
    <div class="row" style="gap:8px"><button class="btn primary" data-act="fw-gostart"${go.sel.size && go.image && !go.busy && !goAnyRun ? "" : " disabled"}>${goAnyRun ? t("fwRun") : t("fwGoStart")}</button>${goAnyRun ? "" : `<button class="btn" data-act="fw-gosched"${go.sel.size && go.image && !go.busy ? "" : " disabled"}>${t("fwGoSched")}</button>`}${goAnyRun ? `<button class="btn" style="color:var(--bad)" data-act="fw-goabort">${t("fwGoAbort")}</button>` : ""}</div>${goTable}</div></details>`;
  const depotBlock = `<details class="card fwsec" data-fwsec="depot"${fwOpen("depot")}><summary>${t("fwDepot")}</summary><div class="stack"><div class="fgrid">
      <div class="field"><label>${t("pick")}${infoBtn("depotNote")}</label><select id="fwdpsel"><option value="">—</option>${gwOpts(dp.id)}</select></div>
      <div class="field"><label>${t("fwImage")}<button class="why" type="button" data-act="fw-imginfo" data-kind="dp" aria-label="${t("cmWhat")}" title="${t("cmWhat")}">i</button></label><select id="fwdpimage">${dpImgs || `<option value="">${t("fwNoOta")}</option>`}</select></div>
      <div class="field"><label>${t("fwUpload")}</label>${fileBox("fwdpfile", dp.fileName)}</div></div>${dpTable}
    <div id="fwdpprog">${dpProgHtml()}</div><div class="row" style="gap:8px"><button class="btn primary" data-act="fw-dpput"${dp.id && !dp.busy && !dp.op ? "" : " disabled"}>${dp.busy ? t("fwDpBusy") : t("fwDpPut")}</button><button class="btn" data-act="fw-dprefresh"${dp.id && !dp.busy && !dp.op ? "" : " disabled"}>${t("fwDpRefresh")}</button></div>
    <div class="vsub">${t("fwKeptTitle")}</div>${keptList.length ? `<div class="stack tight">${keptList.map((k) => `<div class="row between"><span>${esc(k.version)} <span class="small muted">· ${fmtN(k.size)} B · ${esc(k.source)}</span></span><button class="btn sm" type="button" data-act="fw-keptdel" data-name="${esc(k.version)}">${t("fwDpDel")}</button></div>`).join("")}</div>` : `<span class="small muted">${t("fwKeptNone")}</span>`}</div></details>`;
  const log = (ota.log || []).length ? `<div class="vsub">${t("fwLog")}</div><div style="max-height:260px;overflow:auto">${ota.log.slice(-60).map((l) => `<div class="evrow"><span class="when">${esc(l.at)}</span><span><b>${esc(l.cabinet)}</b> ${esc(l.text)}</span></div>`).join("")}</div>` : "";
  const outcome = ota.outcome && !ota.running ? fwOutcomeHtml(ota.outcome.text) : "";
  const otaBlock = `<details class="card fwsec" data-fwsec="ota"${fwOpen("ota") || (ota.running ? " open" : "")}><summary>${t("fwOta")}</summary><div class="stack">${sitesRows || `<p class="muted">${t("noSites")}</p>`}
        <div class="fgrid"><div class="field"><label>${t("fwSrc")}${infoBtn("otaNote")}</label><select id="fwsrc"><option value="bundle"${f.src === "bundle" ? " selected" : ""}>${t("fwSrcBundle")}</option><option value="depot"${f.src === "depot" ? " selected" : ""}>${t("fwSrcDepot")}</option></select></div>
        ${f.src === "depot" ? `<div class="field"><label>${t("fwSrcGw")}</label><select id="fwsrcgw"><option value="">—</option>${gwOpts(f.srcId)}</select></div>
          <div class="field"><label>${t("fwImage")}</label><select id="fwsrcslot">${srcOpts}</select></div>`
          : `<div class="field"><label>${t("fwImage")}<button class="why" type="button" data-act="fw-imginfo" data-kind="ota" aria-label="${t("cmWhat")}" title="${t("cmWhat")}">i</button></label><select id="fwimage">${modImgs || `<option value="">${t("fwNoOta")}</option>`}</select></div>`}</div>
        <div class="row" style="gap:8px"><button class="btn primary" data-act="fw-start"${ota.running ? " disabled" : ""}>${ota.running ? t("fwRun") : t("fwStart")}</button>${ota.running ? `<button class="btn" style="color:var(--bad)" data-act="fw-cancel">${t("fwGoAbort")}</button>` : ""}</div>${fwRows(ota.rows || [])}${outcome}${log}</div></details>`;
  const gwStat = gw.name ? `<div class="notice ${gw.done ? (gw.ok ? "info" : "bad") : ""}">${gw.running ? t("fwGwRun") + " " + gw.pct + "%" : gw.done ? (gw.ok ? t("fwDone") : t("fwFail")) + " · " + esc(gw.summary) : ""}
      <div class="mono tiny" style="white-space:pre-wrap;margin-top:6px">${esc((gw.lines || []).join("\n"))}</div></div>` : "";
  const gwBlock = `<details class="card fwsec" data-fwsec="gw"${fwOpen("gw")}><summary>${t("fwGw")}</summary><div class="stack"><div class="fgrid">
      <div class="field"><label>${t("fwImage")}<button class="why" type="button" data-act="fw-imginfo" data-kind="gw" aria-label="${t("cmWhat")}" title="${t("cmWhat")}">i</button></label><select id="fwgwimage"><option value="">—</option>${gwImgs}</select></div>
      <div class="field"><label>${t("fwUpload")}</label>${fileBox("fwgwfile", f.gwFileName)}</div>
      <div class="field"><label>${t("pick")}</label><select id="fwgwsel"><option value="">—</option>${gsite}</select></div>
      <div class="field"><label>${t("fwConfirm")}</label><input id="fwgwconfirm" value="${esc(f.gwConfirm)}" autocomplete="off" placeholder="${esc(((S.sites.find((x) => x.id === f.gwId)) || {}).name || t("fwConfirmHint"))}"></div></div>
      <div class="row"><button class="btn" style="color:var(--bad)" data-act="fw-gwstart"${gw.running ? " disabled" : ""}>${t("fwGwStart")}</button></div>${gwStat}</div></details>`;
  // order on the page: the gateway's own firmware, the depot, the gateway-run module update (reads from the depot), then the Tool-driven module OTA
  return `<h1>${t("firmware_page")}</h1><div class="stack">${gwBlock}${depotBlock}${goBlock}${otaBlock}</div>`;
}
async function fwDepotLoad(which) {
  const f = S.fw, d = f.dp, id = which === "src" ? f.srcId : d.id;
  if (which === "src") { f.srcSlots = null; f.srcSlot = -1; } else if (!d.op) d.slots = null;
  if (id) {
    try {
      const r = await api("GET", "/api/v2/fw/depot?id=" + encodeURIComponent(id));
      if (which === "src") { f.srcSlots = r.slots; const ok = r.slots.find((x) => x.state === 2); f.srcSlot = ok ? ok.slot : -1; } else d.slots = r.slots;
    } catch (e) { fail(e); }
  }
  render();
}
async function fwGoNames() {
  const go = S.fw.go, first = [...go.sel][0];
  go.names = [];
  if (first) {
    try {
      const r = await api("GET", "/api/v2/fw/depot?id=" + encodeURIComponent(first));
      go.names = r.slots.filter((x) => x.state === 2).map((x) => x.name);
    } catch (e) { /* the card says "choose a cabinet or its depot is empty" */ }
  }
  if (!go.names.includes(go.image)) go.image = go.names[0] || "";
  render();
}
async function fwGoPoll(force) {
  const go = S.fw.go;
  const ids = [...go.sel];
  if (!ids.length || go.polling || (!force && Date.now() - go.at < 10000)) return;
  go.at = Date.now(); go.polling = true;      // one request at a time: a slow cabinet must not pile requests up behind the browser's connection limit
  try { go.rows = (await api("GET", "/api/v2/fw/gwota/status?ids=" + encodeURIComponent(ids.join(",")))).rows; } catch (e) { /* next tick */ } finally { go.polling = false; }
}
async function fwRefresh() {
  fwGoPoll(false);
  try {
    S.fw.ota = await api("GET", "/api/v2/fw/ota/status");
    S.fw.gw = await api("GET", "/api/v2/fw/gateway/status");
    // redraw only when what the page shows has changed: a redraw every tick replaces the buttons between mouse-down and mouse-up, and the click is lost
    const sig = JSON.stringify([S.fw.ota, S.fw.gw, S.fw.go.rows]);
    if (page === "firmware" && sig !== S.fw.sig && !document.activeElement.matches("input,select")) { S.fw.sig = sig; const y = window.scrollY; render(); window.scrollTo(0, y); }
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
  "v1.14.0": {
    th: { date: "5 พ.ย. 2569", head: "บันทึกเหตุการณ์ ซิงก์เวลา คอนโซลผ่านเครือข่าย คลังไฟล์โมดูล และอัปเดตโมดูลเบื้องหลัง", items: [
      "บันทึกเหตุการณ์ในตัวเกตเวย์ (ใช้ $LGS LOG และ $LGS LOG SINCE) เก็บเหตุสำคัญ เช่น ไฟตู้ดับ (bus_quiet) การรีเซ็ตตามเวลา และการเชื่อมต่อของไคลเอนต์ ให้ Tool ดึงไปดูย้อนหลังได้โดยไม่ต้องมี PC ค้างไว้",
      "ซิงก์เวลาจากเซิร์ฟเวอร์ NTP (ตั้ง IP ที่ net.ntp และเขตเวลาที่ time.tz_min) ทำให้นาฬิกาถูกต้องเองหลังไฟดับ",
      "คอนโซลและอัปเดตเฟิร์มแวร์ผ่านเครือข่าย: ใช้ unit 255 / FC 0x41 ที่พอร์ต 502 ส่งคำสั่ง $LGS ได้แบบเดียวกับพอร์ต USB และอัปเดตเฟิร์มแวร์เกตเวย์ผ่านเครือข่าย (ปิดได้ด้วย net.console=0)",
      "คลังไฟล์เฟิร์มแวร์โมดูลบนเกตเวย์: อัปโหลดไฟล์ไว้ในเกตเวย์แล้วอัปเดตโมดูลภายหลังจากเครื่องอื่นได้ โดยเครื่องที่สั่งไม่ต้องมีไฟล์",
      "อัปเดตโมดูลเบื้องหลัง ($LGS OTA START/STATUS/RESULT/ABORT): เกตเวย์ทำเอง ส่งเฉพาะตอนบัสว่าง และสั่งโมดูลเปลี่ยนเฟิร์มแวร์เฉพาะตอนที่คาดว่าจะไม่มีใครมาอ่านโมดูลนั้นในอีก 8 วินาที (รู้จากจังหวะการอ่านที่ผ่านมา) บนโต๊ะทดสอบการรีบูตของโมดูลไม่ชนกับการอ่านเลยใน 32 ครั้ง",
      "ความเข้ากันได้: ไม่เปลี่ยนโครงสร้างการตั้งค่า (schema 11) การตั้งค่าที่เก็บไว้คงอยู่ ขนาดไฟล์ 312,796 B",
      "ไฟสถานะสามดวงของตู้ติดค้างตลอดที่อัปเดตโมดูลเบื้องหลัง (ยกเว้นไฟเลี้ยงชั้นและ output ที่ตั้งเป็นไม่ใช้) คำสั่ง $LGS LAMP ยังบังคับไฟได้ชั่วคราว", "สถานะ: รุ่นจริง ป้ายรุ่น v1.14.0 ผ่านการรีวิวโค้ดก่อนปล่อย ทดสอบบนตู้ Std-11 อัปเดตโมดูลเบื้องหลังผ่าน 40/40 ใน 20.8 นาที"] },
    en: { date: "5 Nov 2026", head: "Event log, time sync, console over the network, module depot and background module update", items: [
      "Event log inside the gateway ($LGS LOG and $LGS LOG SINCE): keeps the important events, such as a cabinet power loss (bus_quiet), scheduled resets and client connections, so the Tool can collect them later without a PC left running.",
      "Time sync from an NTP server (set the IP in net.ntp and the zone in time.tz_min): the clock corrects itself after a power cut.",
      "Console and firmware update over the network: unit 255 / FC 0x41 on port 502 carries the same $LGS commands as the USB port, and the gateway's firmware can be updated over the network (closed with net.console=0).",
      "Module firmware depot on the gateway: leave a module update file in the gateway, then update later from another PC that does not have the file.",
      "Background module update ($LGS OTA START/STATUS/RESULT/ABORT): the gateway does it itself, sends only while the bus is quiet, and tells a module to switch firmware only when no one is expected to read that module within 8 seconds (learned from the recent read rhythm). On the bench, module reboots never collided with polling in 32 tries.",
      "Compatibility: the stored-settings layout is unchanged (schema 11), so saved settings survive. File size 312,796 B.",
      "The cabinet's three status lamps stay lit for the whole background module update (not the shelf power, not outputs set to unused); $LGS LAMP can still force a lamp for a moment.", "Status: release, tag v1.14.0. Passed the pre-release code review; on cabinet Std-11 the background update did 40 of 40 modules in 20.8 minutes."] } },
  "v1.13.0": {
    th: { date: "26 ต.ค. 2569", head: "ซ่อมการหลุดเฟสบนบัส: ส่งซิงก์ใหม่เมื่อไม่มีคำตอบ และรอคำตอบให้ถูกจังหวะ", items: [
      "ซิงก์ใหม่หลังไม่มีคำตอบ (rtu.heal): เมื่อโมดูลไม่ตอบ เกตเวย์ส่งคำสั่งอ่านแบบ broadcast (ยูนิต 0 ไม่มีใครตอบ) หนึ่งครั้งเพื่อให้โมดูลทุกตัวบนช่องนั้นกลับมาตรงเฟส แล้วลองคำขอเดิมอีกหนึ่งครั้ง ทำเฉพาะ ID ที่เคยตอบมาตั้งแต่เปิดเครื่อง และไม่ทำทันทีหลังข้ามช่องฮับ (เฟรมแรกหลังข้ามช่องหายตามธรรมชาติของฮับ) ไม่ส่งซิงก์นี้จากสะพาน USB เด็ดขาด เพราะ PC ที่คุมอยู่ต้องไม่ได้รับเฟรมเกิน",
      "หน้าต่างรอคำตอบที่รู้เรื่องเสียงสะท้อน: ทรานซีฟเวอร์ของ Opta สะท้อนทุกไบต์ที่ส่งกลับมา เดิมเกตเวย์เอาเสียงสะท้อนไปนับเป็นต้นคำตอบ จึงให้เวลาโมดูลแค่ ~20 ms ตอนนี้ตัดเสียงสะท้อนทิ้งก่อนแล้วให้ไบต์แรกของคำตอบมีหน้าต่างของตัวเอง 150 ms รับมือกับโมดูลที่หน่วง 25-60 ms ตอนบันทึกสถิติรายชั่วโมงได้ (เดิมโดนนับเป็นเงียบราว 16% ของนาทีชั่วโมงเต็ม)",
      "ตัวนับและคำสั่งใหม่: rtu.bad_crc (ID ถูกแต่ CRC เสีย) และ rtu.bad_other (เฟรมสั้นเกินหรือคนละ ID) แยกโมดูลที่ตอบเพี้ยนออกจากโมดูลที่เงียบ คำสั่ง $LGS RESYNC [0|1] เปิดปิดการซิงก์ใหม่ (ค่าเริ่มต้น 1 ทุกครั้งที่บูต) และ $LGS EXC [0|1] ให้ตอบ Modbus exception 0x0B ทันทีเมื่อ RS485 ไม่ตอบ (ค่าเริ่มต้น 0) ทั้งสองไม่ถูกเก็บถาวร",
      "ผลบนโต๊ะทดสอบ: 12 ตู้ทดสอบต่อเนื่องข้ามคืน 17 ชั่วโมงไม่มีครั้งแรกพลาด ตู้ Ref-12 จาก 470 เหลือ 6 เหตุอ่านช้า",
      "เป็นตัวบรรเทา ไม่ใช่แก้ที่ต้นเหตุ ต้นเหตุอยู่ที่ไลบรารี Modbus ในโมดูล เฟิร์มแวร์โมดูล v3.5.5 ขึ้นไปแก้ที่ต้นเหตุแล้ว",
      "ความเข้ากันได้: ไม่เปลี่ยนโครงสร้างการตั้งค่า (schema 11) การตั้งค่าที่เก็บไว้คงอยู่ ขนาดไฟล์ 297,968 B"] },
    en: { date: "26 Oct 2026", head: "Repairs bus phase loss: re-sync after a missing reply, and a reply window that knows about the echo", items: [
      "Re-sync after a missing reply (rtu.heal): when a module does not answer, the gateway sends one broadcast read (unit 0, nobody replies) so every module on that channel gets back into phase, then retries the original request once. Only for an ID that has answered since boot, and not right after a hub crossing (the first frame after a crossing is lost by design). The re-sync is never sent from the USB bridge, because a PC master must not receive an extra frame.",
      "Echo-aware reply window: the Opta's transceiver echoes every byte it sends. The gateway used to take the echo for the start of the reply, so a module only had ~20 ms to answer. It now discards the echo first and gives the first reply byte its own 150 ms window, which absorbs modules that stall 25-60 ms while writing their hourly stats (they used to be counted silent in about 16% of their hour marks).",
      "New counters and commands: rtu.bad_crc (right ID, bad CRC) and rtu.bad_other (runts or other IDs) tell a garbled module from a silent one. $LGS RESYNC [0|1] switches the re-sync (default 1 at every boot) and $LGS EXC [0|1] answers an RS485 timeout at once with Modbus exception 0x0B (default 0). Neither is stored.",
      "Bench results: 12 cabinets, a 17 h overnight soak with no first-try misses, Ref-12 from 470 down to 6 slow events.",
      "A mitigation, not the root fix: the cause is the Modbus library in the module. Module firmware v3.5.5 and later removes it.",
      "Compatibility: stored settings layout unchanged (schema 11), so settings survive. File size 297,968 B."] } },
  "v1.12.4": {
    th: { date: "23 ก.ย. 2569", head: "panel.cabinet ตั้งเป็น 0 ได้ (ไม่ใช้ชุดสำเร็จรูป ให้ยึดตาม panel.shape)", items: [
      "ปัญหา: panel.cabinet ตั้งชื่อตามจำนวนช่อง แต่จำนวนช่องบอกรูปทรงตู้ไม่ได้ 40 คือสิบแถวแถวละสี่ ส่วนตู้เย็นก็มี 40 ช่องแต่เป็นห้าแถวแถวละแปด จึงไม่มีตัวเลขที่ถูก ตู้ที่ใช้ panel.shape อยู่แล้วต้องเก็บค่าที่โกหกไว้ (เช่น Chest-Nar-01 ขนาด 7x8 เก็บ 64 มาตลอด)",
      "ตอนนี้ panel.cabinet=0 หมายถึงไม่มีชุดสำเร็จรูป ให้รูปทรงตาม panel.shape ทั้งหมด ตัวตรวจสอบปฏิเสธ 0 ถ้ายังไม่ได้ตั้ง shape และบันทึกสองคีย์เป็นชุดเดียวกัน ลำดับที่เขียนไม่สำคัญ",
      "ตู้ที่ไม่รู้จักเดิมกวาด 80 ช่องโดยปริยาย (อาจเป็นช่องที่ไม่มีจริง ดูเหมือนแถวเสีย) ตอนนี้กวาด 0 ช่อง ให้เห็นว่าตั้งค่าผิด",
      "ตรวจบนฮาร์ดแวร์แล้ว: Chest-Nar-01 กด SAVE ผ่าน และเมื่อกดปุ่มแดงที่ตู้ การกวาดเดินครบทั้งเจ็ดแถวจาก panel.shape อย่างเดียว",
      "ความเข้ากันได้: ไม่เปลี่ยนโครงสร้างการตั้งค่า (schema 11) ตู้ที่ใช้ชุดสำเร็จรูปอยู่ทำงานเหมือนเดิมทุกอย่าง ไม่จำเป็นต้องอัปเดตทั้งฟลีต"] },
    en: { date: "23 Sep 2026", head: "panel.cabinet can be 0 (no preset: follow panel.shape)", items: [
      "Problem: panel.cabinet is named for a slot count, and a slot count does not determine a geometry. 40 means ten rows of four, but the refrigerated cabinet is also forty slots and is five rows of eight, so no number describes it. Cabinets that already used panel.shape had to store a value that lied (Chest-Nar-01, a 7x8, carried 64 for its whole life).",
      "panel.cabinet=0 now means no preset, the shape is the whole description. The validator refuses 0 unless a shape is set, and both keys stage and validate as one set, so the order they are written in does not matter.",
      "An unrecognised cabinet used to sweep 80 slots (some of which may not exist, which reads as a dead row). It now sweeps 0, so the misconfiguration shows.",
      "Verified on hardware: Chest-Nar-01 saves it, and when the red button was pressed at the cabinet the sweep walked all seven rows off panel.shape alone.",
      "Compatibility: stored settings layout unchanged (schema 11). A cabinet already on a catalogue preset behaves exactly as before, so no fleet-wide update is needed."] } },
  "v1.12.3": {
    th: { date: "9 ก.ย. 2569", head: "ปุ่มแผงหน้าตู้ใหม่ all_8: ไล่ไฟทุกช่องแสงของทุกช่อง", items: [
      "all_on เดิมจุดไฟแค่หนึ่งพรีเซ็ตต่อช่อง (เลือกโดย panel.preset) บนตู้วงแหวนนั่นคือจอทั้งหมด แต่บนบอร์ดมาสก์ 8 สี (type 10) มันจุดแค่หนึ่งช่องแสงจากแปดและไม่บอกอะไรเกี่ยวกับอีกเจ็ดช่อง (type 80 คือแปดสิบช่องแบบนี้) ตอนนี้มีการกระทำที่หกที่ไล่ทุกช่องแสงของทุกช่อง ตรวจที่ตู้ได้โดยไม่ต้องมี PC",
      "ไล่ทีละช่องแสงต่อหนึ่งจังหวะ ไม่ใช่ทีละช่อง เพราะแปดช่องแสงคือแปดคำสั่ง coil ถ้ายิงในจังหวะเดียวจะค้าง loop() และสะพาน USB สะพาน TCP กับวอตช์ด็อกต้องรอ ผลคือจำนวนจังหวะรวมเป็น 640 แทน 80",
      "all_off ส่ง coil 511 (All Off ของโมดูล: กลับสู่สภาพพักจากทุกการตั้งค่า coil) แทนการล้างคอยล์ชุดเดียว จึงดับทั้งแปดช่องแสงที่ all_8 จุด และเคลียร์ coil ที่เครื่องมืออื่นทิ้งไว้ด้วย บนตู้วงแหวนผลที่เห็นเหมือนเดิม",
      "ความเข้ากันได้: ไม่เปลี่ยนโครงสร้างการตั้งค่า (schema 11)"] },
    en: { date: "9 Sep 2026", head: "New front-panel action all_8: lights every window of every slot", items: [
      "all_on used to light ONE preset per slot (chosen by panel.preset). On a ring cabinet that is the whole display, but on a type-10 mask board it lights one window in eight and says nothing about the other seven (a type 80 is eighty of those). There is now a sixth action that walks every window of every slot, so a cabinet can be checked with no PC.",
      "It advances one window per tick, not one slot: eight windows is eight coil writes, and firing them in one tick would hold loop(), so the USB bridge, the TCP bridge and the watchdog would wait. The sweep total becomes 640 steps instead of 80.",
      "all_off now sends coil 511 (the module's own All Off: back to rest from any coil configuration) instead of clearing one combo coil, so it puts out the eight windows an all_8 sweep lit and clears any stray coil another tool left set. On a ring cabinet the visible result is the same.",
      "Compatibility: stored settings layout unchanged (schema 11)."] } },
  "v1.12.2": {
    th: { date: "26 ส.ค. 2569", head: "รีเซ็ตเกตเวย์ไม่ทำให้นาฬิกาหาย (รวม v1.12.1)", items: [
      "ปัญหา: ตัวตั้งเวลาไม่ยอมทำงานเมื่อนาฬิกายังไม่ถูกตั้ง ซึ่งถูกต้อง (เกตเวย์ที่เพิ่งบูตแล้วเชื่อว่าเป็นปี 1970 จะรีเซ็ตทันทีที่ถึงเวลานั้น) แต่ \"ยังไม่ตั้ง\" เก็บในแรมเฉย ๆ รีบูตจึงลืม ทั้งที่ RTC ข้างล่างนับต่อเนื่อง เห็นบนโต๊ะทดสอบ 25 ส.ค.: เกตเวย์รีบูต 15:36 แล้วสิบแปดชั่วโมงถัดไปปฏิเสธรีเซ็ตตี 3 ทั้งที่นาฬิกาถูกต้อง บนตู้โรงพยาบาลนั่นคือรีเซ็ตที่ไม่เกิดขึ้นโดยไม่มีใครรู้",
      "ตอนนี้ตัวบอกอยู่ในโดเมนแบ็กอัป (RTC_BKP_DR3) ข้าง RTC จึงอยู่และหายตามเงื่อนไขเดียวกับนาฬิกา: รีบูตเก็บทั้งคู่ ไฟดับหายทั้งคู่ ตอนบูตจะคืนนาฬิกาจาก RTC เมื่อมีตัวบอกและค่าอยู่ระหว่างปี 2026-2100 และบันทึก clock_set aux=3 ในบันทึกเหตุการณ์",
      "ไม่ช่วยตอนไฟดับจริง (ต้องมีแบตสำรอง VBAT) ทางแก้ยังเป็น net.ntp ที่ติดต่อได้",
      "รวม v1.12.1: เอาต์พุตรีเลย์ถูกเขียนซ้ำทุก 5 วินาที (เดิมเขียนตอนบูตและเมื่อสถานะเปลี่ยนเท่านั้น) และอ่านกลับ ถ้าไม่ตรงบันทึกครั้งเดียวต่อเหตุ ไม่ใช่ทุกจังหวะ เห็นได้เฉพาะ latch ของ GPIO เสีย ไม่เห็นรีเลย์ที่ไฟคอยล์ตก",
      "รวม v1.12.1: เหตุการณ์ bus_quiet ในบันทึก: RTU timeout ติดกันหกครั้ง (ทุกสเลฟเงียบพร้อมกัน ซึ่งเป็นสิ่งที่ตู้ที่ไฟดับดูเหมือนจากฝั่งนี้) บันทึกเวลาที่เงียบและเวลาที่กลับมาพร้อมจำนวนวินาที โมดูลตายตัวเดียวไม่ทำให้เกิด ไม่ต้องมี PC คอยดู",
      "ความเข้ากันได้: ไม่เปลี่ยนโครงสร้างการตั้งค่า (schema 11)"] },
    en: { date: "26 Aug 2026", head: "A gateway reset no longer loses the clock (includes v1.12.1)", items: [
      "Problem: the scheduler refuses to fire while the clock is unset, which is right (a gateway that booted believing it was 1970 would fire the moment its target time came round in that fiction). But \"unset\" was a plain RAM flag, so a reboot forgot it while the RTC kept counting. Seen on the bench on 25 Aug: the gateway rebooted at 15:36 and for the next eighteen hours declined to run the 03:00 reset with a good clock. On a hospital cabinet that is a reset that silently never happens.",
      "The marker now lives in the backup domain (RTC_BKP_DR3) next to the RTC, so it is kept and lost on exactly the terms the clock is: a reset keeps both, a power cut takes both. At boot the clock is restored from the RTC when the marker is present and the reading is between 2026 and 2100, and the recovery is logged as clock_set aux=3.",
      "It does not help across a real power cut (that needs a battery on VBAT). The fix for that remains a reachable net.ntp.",
      "Includes v1.12.1: the relay outputs are re-written every 5 seconds (they used to be written at boot and when the commanded state changed) and read back, with a disagreement logged once per episode, not once per tick. It sees a corrupted GPIO latch, not a relay whose coil supply sagged.",
      "Includes v1.12.1: a bus_quiet event in the log: six consecutive RTU timeouts (every slave silent at once, which is what a cabinet losing power looks like from here) is stamped when the bus goes quiet and when it comes back, with the seconds it was gone. One dead module cannot trip it, and no PC has to be watching.",
      "Compatibility: stored settings layout unchanged (schema 11)."] } },
  "v1.12.0": {
    th: { date: "14 ส.ค. 2569", head: "คอนโซลและการอัปเดตเฟิร์มแวร์ผ่านเครือข่าย (พอร์ต 502 เป็นยูนิต 255) รวม v1.11.0", items: [
      "ทำทุกอย่างที่ USB ทำได้ผ่าน TCP: คอนโซล $LGS และการอัปเดตเฟิร์มแวร์เดินบนพอร์ต 502 เป็นยูนิต 255 / function code 0x41 ไม่ต้องเปิดพอร์ตใหม่ (lwIP ของบอร์ดนี้มีแค่ 4 ซ็อกเก็ตและถูกใช้ครบแล้ว) คำสั่งเดียวกัน เซสชัน HELLO เดียวกัน ชุดแก้ที่ค้างอยู่ชุดเดียวกับ USB และไม่มีอะไรที่ส่งถึงยูนิต 255 ลงบัส RS485 อีก (เดิมถูกส่งต่อและเสียเวลารอ timeout เต็ม)",
      "อัปเดตเฟิร์มแวร์: ส่งไฟล์เข้าพาร์ติชัน OTA บน QSPI ทีละ 240 ไบต์ ตรวจ CRC จากไฟล์ที่อ่านกลับ แล้วให้ bootloader จากโรงงานเป็นผู้ติดตั้ง ผ่านบนโต๊ะทดสอบ: 297,748 ไบต์ใน 23.6 วินาที แล้วกลับมาบนเครือข่ายใน 8 วินาทีพร้อมรายงานเวอร์ชันใหม่",
      "รวม v1.11.0: NTP กู้เวลา, บันทึกเหตุการณ์บน QSPI, ช่อง TCP ช่องที่สอง (สอง client พร้อมกัน), ปุ่มแผงหน้าตู้ lamp test, และอ่านสาเหตุการรีเซ็ตจาก RTC backup DR8 (bootloader ล้าง RSR ก่อน)",
      "net.console=0 ปิดทางเข้าคอนโซลผ่าน TCP ได้ เปิดคืนได้ทาง USB เท่านั้น"] },
    en: { date: "14 Aug 2026", head: "Console and firmware update over the network (port 502 as unit 255), includes v1.11.0", items: [
      "Everything USB can do, over TCP: the $LGS console and the firmware update ride port 502 as unit 255 / function code 0x41, so no new port is needed (lwIP on this board is built for 4 sockets and all four are in use). Same verbs, same HELLO session, same staged-edit set as USB, and nothing addressed to unit 255 reaches the RS485 bus any more (it used to be forwarded and burn a full timeout).",
      "Firmware update: the file is staged on the QSPI OTA partition in 240-byte chunks, CRC-checked on read-back, and then applied by the factory bootloader. Proven on the bench: 297,748 bytes in 23.6 s, back on the network 8 s later reporting the new version.",
      "Includes v1.11.0: NTP time recovery, the event log on QSPI, a second TCP client slot (two clients at once), the front-panel lamp-test action, and the reset reason read from RTC backup DR8 (the bootloader clears RSR first).",
      "net.console=0 closes the TCP console path; only USB can reopen it."] } },
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
  const lotField = `<div class="field"><label>${t("cmLot")}</label><input id="cmlot" value="${esc(c.lot)}" autocomplete="off"></div>`;
  // the cell next to the cabinet type is split in half: module id and lot (one module), or the module preset and lot (a batch, whose grid follows below)
  const lotId = c.mode === "batch"
    ? `<div class="halves"><div class="field"><label>${t("cmGrid")}</label><select id="cmpreset"><option value="">${t("cmPreset")}</option>${presets}</select></div>${lotField}</div>
      <div class="field" style="grid-column:1/-1"><div class="row"><button class="btn" data-act="cm-clear">${t("cmClear")}</button><span class="small muted">${t("cmSelected", { n: c.sel.size })}</span></div>${cmGridHtml()}</div>`
    : `<div class="halves"><div class="field"><label>${t("cmId")}</label><input id="cmid" value="${esc(c.id)}" inputmode="numeric" autocomplete="off"></div>${lotField}</div>`;
  const ow = c.mode === "batch" ? "" : `<label class="row" style="min-height:40px"><input type="checkbox" id="cmow"${c.overwrite ? " checked" : ""}> <span>${t("cmOverwrite")}</span></label>`;
  return `<h1>${t("commission_page")}</h1><div class="stack">${c.err ? `<div class="notice bad">${esc(c.err)}</div>` : ""}
    <section class="card stack"><div class="row"><button class="btn" data-act="cm-probe"${c.probing ? " disabled" : ""}>${c.probing ? t("cmProbing") : t("cmProbe")}</button></div>${probe}</section>
    <section class="card stack"><div class="seg"><button data-cmmode="single" aria-pressed="${c.mode === "single"}">${t("cmSingle")}</button><button data-cmmode="batch" aria-pressed="${c.mode === "batch"}">${t("cmBatch")}</button></div><div class="fgrid">
      <div class="field"><label>${t("cmImage")}<button class="why" type="button" data-act="cm-info" aria-label="${t("cmWhat")}" title="${t("cmWhat")}">i</button></label><select id="cmimage"><option value="">—</option>${imgs}</select></div>
      <div class="field"><label>${t("cmUpload")}</label>${fileBox("cmfile", c.fileName)}</div>
      <div class="field"><label>${t("cmType")}</label><select id="cmtype">${types}</select></div>
      ${lotId}</div>${ow}
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
const NAV = ["cabinets", "module", "events", "gateway", "sites", "firmware", "soak", "commission", "labels"];
/* Basic mode is what a technician on site needs day to day: cabinets, modules (read, quick commands, scan, installation check) and events. Everything that changes settings, firmware, module ids or the cabinet list, runs for hours or prints labels, and the classic tool, is advanced. It is a convenience for whoever holds the phone, not security: the login is what keeps strangers out. */
const ADV_PAGES = new Set(["gateway", "labels", "soak", "firmware", "commission", "sites"]);
let uiMode = "basic"; try { uiMode = localStorage.getItem("lgs.mode") === "advanced" ? "advanced" : "basic"; } catch (e) { /* storage blocked: basic */ }
const allowed = (k) => uiMode === "advanced" || !ADV_PAGES.has(k);

function render() {
  if (!allowed(page)) { page = "cabinets"; location.hash = "#/cabinets"; toast(t("modeLocked")); }
  $("#nav").innerHTML = NAV.filter(allowed).map((k) => `<button data-nav="${k}" ${k === page ? 'aria-current="page"' : ""}>${t(k === "gateway" ? "gateway_page" : k === "module" ? "module_page" : k === "soak" ? "soak_page" : k === "firmware" ? "firmware_page" : k === "commission" ? "commission_page" : k === "labels" ? "labels_page" : k)}</button>`).join("")
    + (uiMode === "advanced" ? `<button data-nav="classic">${t("classic")}</button>` : "");
  $("#main").innerHTML = (VIEWS[page] || viewCabinets)();
  const cur = $("#nav [aria-current]"); if (cur && cur.scrollIntoView) cur.scrollIntoView({ inline: "center", block: "nearest" });
  $("#stagechip").textContent = TXT[lang].stage || ""; $("#infoclose").textContent = t("close");
  settingsText(); themeSelect(); modeSelect();
  document.documentElement.lang = lang;
  if (page === "events") { loadEvents(); loadSummary(); }
  if (page === "gateway") gwBar();
  if (page === "module") { modAutoSync(); insCaption(); insResFit(); insLayout(); jobResume(); }
  if (page === "gateway") jobResume();
  if (page === "soak" && !S.soak.timer) soakSync();
  if (page === "soak") soakEstimate();
  if (page === "firmware" && !S.fw.timer) fwSync();
  if (page === "commission" && !S.cm.timer && !S.cm.syncing) { S.cm.syncing = true; cmSync().finally(() => { S.cm.syncing = false; }); }
}

/* The events dashboard: six counters, a lights chart, a problems chart and one row per gateway, over the
   same gateway/days filter as the list. Bars are one series each (the title names it), so no legend box. */
const EV_TILES = [["coil", "dashLights"], ["tcp_accept", "dashConn"], ["tcp_refused", "dashRefused"], ["bus_quiet", "dashQuiet"], ["rtu_heal", "dashHeal"], ["boot", "dashBoot"]];
const EV_BAD = new Set(["tcp_refused", "bus_quiet", "rtu_heal", "boot"]);
const fmtN = (n) => Number(n).toLocaleString(lang === "th" ? "th-TH" : "en-US");
function barChart(series, key, color, label, hourly) {
  const W = 640, H = 150, L = 38, B = 20, T = 8, n = series.length, max = Math.max(1, ...series.map((x) => x[key]));
  const nice = (m) => { const p = Math.pow(10, Math.floor(Math.log10(m))); const f = m / p; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * p; };
  const top = Math.max(2, nice(max)), bw = (W - L) / n, bar = Math.max(1, Math.min(18, bw - 2));
  const y = (v) => T + (H - T - B) * (1 - v / top);
  const lab = (k) => (hourly ? k.slice(11, 13) + ":00" : k.slice(5).replace("-", "/"));
  const full = (k) => (hourly ? k.slice(5, 10).replace("-", "/") + " " + k.slice(11, 13) + ":00" : k.slice(5).replace("-", "/"));
  const every = Math.ceil(n / 8);
  const bars = series.map((x, i) => {
    const h = Math.max(0, H - B - y(x[key])), cx = L + bw * i + bw / 2;
    return `<g class="bar" data-tip="${esc(full(x.t) + " · " + label + " " + fmtN(x[key]))}"><rect x="${L + bw * i}" y="${T}" width="${bw}" height="${H - T - B}" fill="transparent"/>${x[key] ? `<rect x="${cx - bar / 2}" y="${y(x[key])}" width="${bar}" height="${h}" rx="${Math.min(4, bar / 2)}" fill="${color}"/>` : ""}</g>`;
  }).join("");
  const grid = [0, 0.5, 1].filter((f) => Number.isInteger(top * f)).map((f) => `<line x1="${L}" x2="${W}" y1="${y(top * f)}" y2="${y(top * f)}" stroke="var(--line)" stroke-width="1"/><text x="${L - 6}" y="${y(top * f) + 4}" text-anchor="end" font-size="11" fill="var(--muted)">${fmtN(top * f)}</text>`).join("");
  const xs = series.map((x, i) => (i % every === 0 ? `<text x="${L + bw * i + bw / 2}" y="${H - 4}" text-anchor="middle" font-size="11" fill="var(--muted)">${lab(x.t)}</text>` : "")).join("");
  return `<svg viewBox="0 0 ${W} ${H}" class="evchart" role="img" aria-label="${esc(label)}">${grid}${bars}${xs}</svg>`;
}
async function loadSummary() {
  const el = $("#evdash"); if (!el) return;
  try {
    const mine = (loadSummary.n = (loadSummary.n || 0) + 1);
    const r = await api("GET", "/api/v2/events/summary?" + evParams());
    if (!$("#evdash") || mine !== loadSummary.n) return;
    S.ev.facets = r.facets; renderFilters();
    const tiles = EV_TILES.map(([k, lbl]) => `<div class="kpi"><div class="kpiv${EV_BAD.has(k) && r.totals[k] ? " bad" : ""}">${fmtN(r.totals[k])}</div><div class="kpil">${t(lbl)}</div></div>`).join("");
    const unit = t(r.hourly ? "dashHour" : "dashDay");
    const charts = !r.series.length ? "" : `<div class="evcharts"><div><div class="small muted">${t("dashLightsBy", { u: unit })}</div>${barChart(r.series, "lights", "var(--brand)", t("dashLights"), r.hourly)}</div>
      <div><div class="small muted">${t("dashProblemsBy", { u: unit })}</div>${barChart(r.series, "problems", "var(--bad)", t("dashProblems"), r.hourly)}</div></div>`;
    const head = ["gateway", "dashLights", "dashConn", "dashRefused", "dashQuiet", "dashHeal", "dashBoot", "dashLast"].map((k) => `<th${k === "gateway" || k === "dashLast" ? "" : ' class="num"'}>${t(k)}</th>`).join("");
    const cell = (v, bad) => `<td class="num${bad && v ? " bad" : ""}">${fmtN(v)}</td>`;
    const rows = r.gateways.map((g) => `<tr><td><b>${esc(g.gw)}</b></td>${cell(g.coil)}${cell(g.tcp_accept)}${cell(g.tcp_refused, 1)}${cell(g.bus_quiet, 1)}${cell(g.rtu_heal, 1)}${cell(g.boot, 1)}<td class="when">${esc((g.last || "").replace("T", " ").slice(5, 16))}</td></tr>`).join("");
    el.innerHTML = `<section class="card stack"><div class="kpis">${tiles}</div>${charts}</section>
      <section class="card stack" style="overflow-x:auto"><table class="evtab"><tr>${head}</tr>${rows}</table></section>`;
    const tip = $("#evtip") || document.body.appendChild(Object.assign(document.createElement("div"), { id: "evtip", className: "evtip", hidden: true }));
    el.querySelectorAll(".evchart").forEach((svg) => {
      svg.onpointermove = (e) => { const g = e.target.closest(".bar"); if (!g) { tip.hidden = true; return; } tip.textContent = g.dataset.tip; tip.hidden = false; tip.style.left = Math.max(8, Math.min(e.clientX + 12, innerWidth - tip.offsetWidth - 8)) + "px"; tip.style.top = Math.max(8, e.clientY - 34) + "px"; };
      svg.onpointerleave = () => { tip.hidden = true; };
    });
  } catch (e) { fail(e); }
}
try { const n = +localStorage.getItem("lgs.evsize"); if ([10, 20, 50, 100].includes(n)) S.ev.size = n; } catch (e) { /* default */ }
const ymd = (d) => d.toLocaleDateString("sv-SE");
const MON = { th: ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."], en: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"] };
const DOW = { th: ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"], en: ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"] };
const fmtDay = (s) => { const [y, m, d] = s.split("-").map(Number); return `${d} ${MON[lang === "th" ? "th" : "en"][m - 1]} ${y}`; };
const fmtRange = (a, b) => (a === b ? fmtDay(a) : `${fmtDay(a)} – ${fmtDay(b)}`);
/* Is the chosen range exactly "the last n days, ending today"? Lights the matching shortcut. */
const rangeIs = (n) => S.ev.to === ymd(new Date()) && S.ev.from === ymd(new Date(Date.now() - 86400000 * (n - 1)));
/* The filter panel, in the manner of a parametric part search: a group per property (gateway, event type, client, module),
   each a list of tick boxes with the count that ticking it would leave. Several ticks in a group mean "any of these";
   groups combine. The counts come with the dashboard (loadSummary) and are left out until the first answer. */
const evSet = (k) => (k === "ev" ? S.ev.types : S.ev[k]);
const evLabel = (k, v) => (k === "ev" ? (TXT[lang] && TXT[lang]["evT_" + v] ? t("evT_" + v) : v) : k === "unit" && v === "0" ? t("evUnitAll") : v);
const RANGE_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>`, CLOCK_ICON = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>`;
const EV_GROUPS = [["gw", "gateway"], ["ev", "evType"], ["client", "evClient"], ["unit", "evUnit"]];
function filterPanel() {
  const f = S.ev.facets || { gw: [], ev: [], client: [], unit: [] };
  const groups = EV_GROUPS.map(([k, title]) => {
    const have = new Set(f[k].map((o) => o.v)), sel = evSet(k);
    const items = [...f[k], ...[...sel].filter((v) => !have.has(v)).map((v) => ({ v, n: 0 }))];
    const body = items.map((o) => `<label class="fopt${o.n ? "" : " zero"}"><input type="checkbox" data-f="${k}" value="${esc(o.v)}"${sel.has(o.v) ? " checked" : ""}><span>${esc(evLabel(k, o.v))}</span><em>${fmtN(o.n)}</em></label>`).join("");
    return `<details class="fgrp" data-g="${k}"${S.ev.open.has(k) ? " open" : ""}><summary><span>${t(title)}</span>${sel.size ? `<span class="fcnt">${sel.size}</span>` : ""}</summary><div class="fbody">${body || `<p class="small muted" style="margin:6px 4px">${S.ev.facets ? t("evNone") : t("reading")}</p>`}</div></details>`;
  }).join("");
  return `<div class="fhead"><b>${t("evFilters")}</b></div>
    <div class="field"><label>${t("evRange")}</label><button class="rangebtn" id="evrange" type="button" data-act="ev-pick">${RANGE_ICON}<span id="evrangetxt">${esc(fmtRange(S.ev.from, S.ev.to))}</span></button></div>
    <div class="field"><label>${t("evTime")}</label><button class="rangebtn${timeOn() ? " on" : ""}" id="evtime" type="button" data-act="ev-time">${CLOCK_ICON}<span id="evtimetxt">${esc(timeText())}</span></button></div>
    ${groups}`;
}
const evActive = () => S.ev.gw.size + S.ev.types.size + S.ev.client.size + S.ev.unit.size > 0 || timeOn();
function renderFilters() {
  const el = $("#evfilters"); if (!el) return;
  const keep = {}; el.querySelectorAll(".fgrp").forEach((g) => { keep[g.dataset.g] = g.querySelector(".fbody").scrollTop; });
  el.innerHTML = filterPanel();
  el.querySelectorAll(".fgrp").forEach((g) => { g.querySelector(".fbody").scrollTop = keep[g.dataset.g] || 0; });
  const ch = $("#evchips"); if (!ch) return;
  const chips = [];
  for (const [k] of EV_GROUPS) for (const v of evSet(k)) chips.push(`<button class="fchip" type="button" data-f="${k}" data-v="${esc(v)}">${esc(evLabel(k, v))} <b>×</b></button>`);
  if (timeOn()) chips.push(`<button class="fchip" type="button" data-f="time">${esc(timeText())} <b>×</b></button>`);
  if (chips.length) chips.push(`<button class="fclear" type="button" data-act="ev-clear">${t("evClear")}</button>`);   // beside what it clears
  ch.hidden = !chips.length; ch.innerHTML = chips.join("");
}
/* every query the page makes carries the same filters */
function evParams() {
  const q = new URLSearchParams({ start: S.ev.from, end: S.ev.to });
  for (const [k] of EV_GROUPS) if (evSet(k).size) q.set(k, [...evSet(k)].join(","));
  if (timeOn()) { q.set("tfrom", S.ev.tfrom); q.set("tto", S.ev.tto); }
  return q;
}
function evRefresh() { clearTimeout(evRefresh.t); evRefresh.t = setTimeout(() => { loadEvents(); loadSummary(); }, 150); }
const timeOn = () => !(S.ev.tfrom === "00:00" && S.ev.tto === "23:59");
const timeText = () => (timeOn() ? `${S.ev.tfrom} – ${S.ev.tto}` : t("evAllDay"));
/* A time-of-day window popup: it applies on every chosen day (03:00–04:00 over a week = that hour each night), and a
   "from" later than "to" runs past midnight. Like the calendar it holds the choice until it is closed, then applies once. */
function openTime(from, to, apply) {
  const d = $("#timepick"), pad = (n) => String(n).padStart(2, "0");
  const sel = (p, n, v) => `<select data-p="${p}">${Array.from({ length: n }, (_, i) => `<option value="${i}"${i === v ? " selected" : ""}>${pad(i)}</option>`).join("")}</select>`;
  const [fh, fm] = from.split(":").map(Number), [th, tm] = to.split(":").map(Number);
  $("#tmtitle").textContent = t("evTime");
  $("#tmbody").innerHTML = [["evTimeFrom", "f", fh, fm], ["evTimeTo", "t", th, tm]].map(([k, p, h, m]) => `<div class="tmrow"><span class="small muted">${t(k)}</span>${sel(p + "h", 24, h)}<b>:</b>${sel(p + "m", 60, m)}</div>`).join("");
  const val = () => { const v = (p) => pad(+$(`#tmbody [data-p="${p}"]`).value); return { from: `${v("fh")}:${v("fm")}`, to: `${v("th")}:${v("tm")}` }; };
  const hint = () => { const x = val(); $("#tmhint").textContent = x.from > x.to ? t("evTimeWrap") : ""; };
  $("#tmbody").onchange = hint; hint();
  $("#tmall").textContent = t("evAllDay"); $("#tmall").onclick = () => { for (const [p, v] of [["fh", 0], ["fm", 0], ["th", 23], ["tm", 59]]) $(`#tmbody [data-p="${p}"]`).value = v; hint(); };
  $("#tmno").textContent = t("close"); $("#tmno").onclick = () => d.close();
  d.onclose = () => { d.onclose = null; const x = val(); if (x.from !== from || x.to !== to) apply(x); };
  if (d.showModal) d.showModal(); else d.setAttribute("open", "");
}
/* A calendar popup for a from/to range. The popup stays open until the close button (or Esc); choices are only held
   while it is open and `apply({from, to})` runs once, on close, if the range changed. Tap a day for that single day,
   tap a second day to stretch it into a range, or use a shortcut.
   Only days the collector still keeps are selectable. */
function openRange(from, to, min, max, apply, allFrom) {
  const d = $("#rangepick"), g = $("#rpgrid"); let a = from, b = to, step = 0;
  let [vy, vm] = to.split("-").map(Number); vm -= 1;
  const [ny, nm] = min.split("-").map(Number), [xy, xm] = max.split("-").map(Number);
  const paint = () => {
    $("#rptitle").textContent = new Date(vy, vm, 1).toLocaleDateString(lang === "th" ? "th-TH-u-ca-gregory" : "en-US", { month: "long", year: "numeric" });
    $("#rpprev").disabled = vy * 12 + vm <= ny * 12 + nm - 1; $("#rpnext").disabled = vy * 12 + vm >= xy * 12 + xm - 1;
    const first = new Date(vy, vm, 1).getDay(), days = new Date(vy, vm + 1, 0).getDate();
    let h = DOW[lang === "th" ? "th" : "en"].map((x) => `<div class="dow">${x}</div>`).join("") + "<span></span>".repeat(first);
    for (let i = 1; i <= days; i++) {
      const s = `${vy}-${String(vm + 1).padStart(2, "0")}-${String(i).padStart(2, "0")}`;
      const cls = [s === a || s === b ? "edge" : s > a && s < b ? "in" : "", s === max ? "today" : ""].join(" ");
      h += `<button type="button" class="${cls}" data-d="${s}"${s < min || s > max ? " disabled" : ""}>${i}</button>`;
    }
    g.innerHTML = h;
    $("#rpshort").innerHTML = [1, 7, 30].map((n) => `<button type="button" data-n="${n}" aria-pressed="${a === ymd(new Date(Date.now() - 86400000 * (n - 1))) && b === max}">${n === 1 ? t("day1") : t("dayN", { n })}</button>`).join("")
      + (allFrom ? `<button type="button" data-all="1" aria-pressed="${a === allFrom && b === max}">${t("dayAll")}</button>` : "");
    $("#rphint").textContent = step ? t("rangeEnd") : "";
  };
  const set = (x, y) => { a = x; b = y; };
  $("#rpshort").onclick = (e) => { const all = e.target.closest("[data-all]"), x = all || e.target.closest("[data-n]"); if (!x) return; step = 0; set(all ? allFrom : ymd(new Date(Date.now() - 86400000 * (+x.dataset.n - 1))), max); [vy, vm] = max.split("-").map(Number).slice(0, 2); vm -= 1; paint(); };
  g.onclick = (e) => {
    const x = e.target.closest("[data-d]"); if (!x) return;
    const day = x.dataset.d;
    if (!step) { set(day, day); step = 1; } else { set(day < a ? day : a, day < a ? a : day); step = 0; }
    paint();
  };
  $("#rpprev").onclick = () => { vm -= 1; if (vm < 0) { vm = 11; vy -= 1; } paint(); };
  $("#rpnext").onclick = () => { vm += 1; if (vm > 11) { vm = 0; vy += 1; } paint(); };
  $("#rpno").textContent = t("close"); $("#rpno").onclick = () => d.close();
  d.onclose = () => { d.onclose = null; if (a !== from || b !== to) apply({ from: a, to: b }); };
  paint();
  if (d.showModal) d.showModal(); else d.setAttribute("open", "");
}
async function loadEvents() {
  try {
    const q = evParams();
    const mine = (loadEvents.n = (loadEvents.n || 0) + 1);
    const r = await api("GET", "/api/v2/events?" + q + "&limit=" + S.ev.size + "&offset=" + S.ev.page * S.ev.size);
    if (mine !== loadEvents.n || !$("#evcount")) return;
    $("#evcount").textContent = t("matched", { n: r.matched });
    const last = Math.max(0, Math.ceil(r.matched / S.ev.size) - 1);
    if (S.ev.page > last) { S.ev.page = last; return loadEvents(); }
    const pg = $("#evpager");
    if (pg) pg.innerHTML = r.matched > S.ev.size ? `<button class="btn sm" type="button" data-act="ev-page" data-d="-1"${S.ev.page ? "" : " disabled"}>‹ ${t("prev")}</button><span class="small muted">${S.ev.page * S.ev.size + 1}–${Math.min(r.matched, (S.ev.page + 1) * S.ev.size)} / ${fmtN(r.matched)}</span><button class="btn sm" type="button" data-act="ev-page" data-d="1"${S.ev.page < last ? "" : " disabled"}>${t("next")} ›</button>` : "";
    const csv = $("#evcsv"); if (csv) { csv.href = "/api/v2/events/csv?" + q; csv.classList.toggle("disabled", !r.matched); csv.setAttribute("aria-disabled", String(!r.matched)); }
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
  if (nav) { if (nav.dataset.nav === "classic") { location.href = "/classic"; return; } page = nav.dataset.nav; location.hash = "#/" + page; if (page !== "soak") { clearInterval(S.soak.timer); S.soak.timer = null; } if (page !== "firmware") { clearInterval(S.fw.timer); S.fw.timer = null; } if (page !== "commission") { clearInterval(S.cm.timer); S.cm.timer = null; } if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways").catch(() => ({}))).gateways || []; render(); return; }
  const cell = ev.target.closest("[data-cmcell]");
  if (cell) { const id = +cell.dataset.cmcell, c = S.cm; if (c.mode === "batch") { c.sel.has(id) ? c.sel.delete(id) : c.sel.add(id); } else { c.id = String(id); c.gridOpen = false; } render(); return; }
  const crow = ev.target.closest("[data-cmrow]");
  if (crow) { const r = +crow.dataset.cmrow, g = (S.cm.opts && S.cm.opts.grid) || { cols: 8 }, ids = Array.from({ length: g.cols }, (_, k) => r * 10 + k + 1); const all = ids.every((i) => S.cm.sel.has(i)); ids.forEach((i) => (all ? S.cm.sel.delete(i) : S.cm.sel.add(i))); render(); return; }
  document.querySelectorAll("details.menu[open]").forEach((d) => { if (!d.contains(ev.target)) d.open = false; });
  const cmm = ev.target.closest("[data-cmmode]"); if (cmm) { S.cm.mode = cmm.dataset.cmmode; render(); return; }
  const cab = ev.target.closest("[data-cab]");
  if (cab) { const id = cab.dataset.cab; S.soak.sel.has(id) ? S.soak.sel.delete(id) : S.soak.sel.add(id); render(); return; }
  const chip = ev.target.closest(".fchip");
  if (chip) {
    if (chip.dataset.f === "time") { S.ev.tfrom = "00:00"; S.ev.tto = "23:59"; } else evSet(chip.dataset.f).delete(chip.dataset.v);
    S.ev.page = 0; renderFilters(); evRefresh(); return;
  }
  if (ev.target.closest('[data-act="ev-clear"]')) {
    S.ev.gw.clear(); S.ev.types.clear(); S.ev.client.clear(); S.ev.unit.clear(); S.ev.tfrom = "00:00"; S.ev.tto = "23:59";
    S.ev.page = 0; renderFilters(); evRefresh(); return;
  }
  if (ev.target.closest('[data-act="ev-time"]')) {
    openTime(S.ev.tfrom, S.ev.tto, (r) => { S.ev.tfrom = r.from; S.ev.tto = r.to; S.ev.page = 0; renderFilters(); evRefresh(); });
    return;
  }
  if (ev.target.closest('[data-act="ev-pick"]')) {
    const keep = (S.me.collector || {}).retention_days || 90, now = new Date();
    // "All" = from the oldest day any gateway has a file for (the collector keeps at most 365 days), so the export and the
    // page both cover everything collected rather than a guess at it.
    let allFrom = "";
    try { allFrom = ((await api("GET", "/api/v2/events/gateways")).gateways || []).map((g) => g.first).filter(Boolean).sort()[0] || ""; } catch (e) { /* the picker still works without it */ }
    const floor = ymd(new Date(now.getTime() - 86400000 * Math.max(7, keep)));
    openRange(S.ev.from, S.ev.to, allFrom && allFrom < floor ? allFrom : floor, ymd(now),
      (r) => { S.ev.from = r.from; S.ev.to = r.to; S.ev.page = 0; renderFilters(); evRefresh(); }, allFrom);
    return;
  }
  const pgb = ev.target.closest('[data-act="ev-page"]');
  if (pgb) { S.ev.page = Math.max(0, S.ev.page + +pgb.dataset.d); loadEvents(); return; }
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
    } else if (act.dataset.act === "gw-reboot") {
      const g = S.sites.find((x) => x.id === S.gw.id); if (!await ask(t("rebootQ", { n: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "reboot" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-defaults") {
      const g = S.sites.find((x) => x.id === S.gw.id); const typed = await ask(t("defaultsQ", { n: g ? g.name : "" }), false, true); if (typed === null) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "defaults", confirm: typed }); if (!r.ok) throw new Error(r.error); await gwRead(); toast(t("doneOk"));
    } else if (act.dataset.act === "mod-read") { await modRead();
    } else if (act.dataset.act === "mod-coil") {
      await modCoil(+act.dataset.addr, act.dataset.val === "1", !!act.dataset.latch && act.dataset.val === "1");
    } else if (act.dataset.act === "mod-unlock") {
      if (!S.mod.id) return;
      if (Date.now() < S.mod.lockUntil) { toast(t("cooldownNote")); return; }
      const coil = await pickUnlock(); if (!coil) return;
      await modCoil(coil, true, true);
    } else if (act.dataset.act === "mod-color") {
      if (!S.mod.id) return;
      const kind = act.dataset.kind, latch = !!act.dataset.latch;
      if (latch && Date.now() < S.mod.lockUntil) { toast(t("cooldownNote")); return; }
      const n = await pickColor(act.textContent.trim()); if (!n) return;
      await modCoil({ enable: 1000, display: 1010, latch: 1020, latch_display: 1030 }[kind] + n, true, latch);
    } else if (act.dataset.act === "mod-number") {
      if (!S.mod.id) return;
      const typed = await ask(t("numAsk", { id: S.mod.dev }), false, true); if (typed === null) return;
      const raw = typed.trim(), v = Number(raw);
      if (raw === "" || !Number.isInteger(v) || v < 0 || v > 9999) { await ask(t("numRange"), true); return; }
      const r = await api("POST", "/api/v2/mod/number", { id: S.mod.id, device_id: S.mod.dev, value: v }); if (!r.ok) throw new Error(r.error); toast(t("sent"));
    } else if (act.dataset.act === "soak-an-pg") { S.soak.anP = Math.max(0, S.soak.anP + (+act.dataset.d)); render();
    } else if (act.dataset.act === "fw-tile" || act.dataset.act === "fw-tileall" || act.dataset.act === "fw-tilenone") {
      const isGo = act.dataset.set === "go", st = isGo ? S.fw.go.sel : S.fw.sel;
      if (act.dataset.act === "fw-tile") { const id = act.dataset.id; st.has(id) ? st.delete(id) : st.add(id); }
      else if (act.dataset.act === "fw-tileall") S.sites.forEach((x) => st.add(x.id)); else st.clear();
      render();
      if (isGo) fwGoNames().then(() => fwGoPoll(true)).then(render);
    } else if (act.dataset.act === "soak-all") { S.sites.forEach((x) => { if (x.cabinet) S.soak.sel.add(x.id); }); render();
    } else if (act.dataset.act === "soak-none") { S.soak.sel.clear(); render();
    } else if (act.dataset.act === "soak-mode") { S.soak.mode = act.dataset.m; render();
    } else if (act.dataset.act === "soak-start") {
      const k = S.soak;
      if (!k.sel.size) { toast(t("sPickOne")); return; }
      const hh = (n) => String(n).padStart(2, "0");
      const r = await api("POST", "/api/v2/soak/start", { ids: [...k.sel], mode: k.mode, picks: k.picks, dwell_s: k.dwell, windows: k.windows, gap_s: k.gap, counter_every: k.every, slow_ms: k.slow, timeout_s: k.tmo, hours: soakPlan().hours, start_at: k.startMode === "at" ? `${hh(k.sh)}:${hh(k.sm)}` : "" });
      toast(t("sStarted", { n: r.count }) + (r.warnings && r.warnings.length ? " · " + r.warnings[0] : "")); await soakRefresh(); render();
    } else if (act.dataset.act === "soak-stop") {
      if (!await ask(t("sStopQ"))) return; await api("POST", "/api/v2/soak/stop", {}); S.soak.was = true; await soakRefresh();
    } else if (act.dataset.act === "soak-view") {
      const run = (S.soak.runs || []).find((x) => x.stamp === act.dataset.stamp); if (!run) return;
      let txt = "";
      if (run.verdict) { const r = await fetch("/api/v2/soak/file?name=" + encodeURIComponent(run.verdict)); if (r.ok) txt = await r.text(); }
      const cabs = run.csv.map((c) => c.replace(/^soak-/, "").replace(/-\d{8}-\d{6}\.csv$/, ""));
      S.soak.view = { stamp: run.stamp, txt, cabs, pick: new Set(cabs), fmt: "csv" };
      soakViewDraw();
      const d = $("#info"); d.classList.add("wide"); d.onclose = () => { d.classList.remove("wide"); S.soak.view = null; }; if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    } else if (act.dataset.act === "soak-png") {
      const w = S.soak.view; if (!w || !w.txt) return;
      const blob = await verdictPng(w.txt); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `soak-${w.stamp}.png`; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    } else if (act.dataset.act === "soak-pick-all" || act.dataset.act === "soak-pick-none") {
      const w = S.soak.view; if (!w) return; w.pick = act.dataset.act === "soak-pick-all" ? new Set(w.cabs) : new Set(); soakViewSync();
    } else if (act.dataset.act === "soak-fmt") {
      const w = S.soak.view; if (!w) return; w.fmt = act.dataset.f; soakViewSync();
    } else if (act.dataset.act === "soak-dl") {
      const w = S.soak.view; if (!w || !w.pick.size) return;
      const a = document.createElement("a"); a.href = `/api/v2/soak/export?stamp=${encodeURIComponent(w.stamp)}&cabs=${encodeURIComponent([...w.pick].join(","))}&format=${w.fmt}`; a.click();
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
      const f = S.fw, fromDepot = f.src === "depot";
      const im = fromDepot ? (f.srcSlots || []).find((x) => x.slot === f.srcSlot && x.state === 2) : (f.images && f.images.module.find((x) => x.key === f.image));
      if (!f.sel.size || !im) return;
      const cabs = S.sites.filter((x) => f.sel.has(x.id));
      const label = fromDepot ? `${im.name} (${(S.sites.find((x) => x.id === f.srcId) || {}).name || ""})` : im.label;
      if (!await ask(t("fwStartQ", { n: cabs.length, i: label }) + "\n\n" + cabs.map((c) => c.name).join(", "))) return;
      await api("POST", "/api/v2/fw/ota/start", fromDepot ? { ids: [...f.sel], depot: { id: f.srcId, slot: f.srcSlot } } : { ids: [...f.sel], image: f.image }); await fwRefresh();
    } else if (act.dataset.act === "fw-gostart" || act.dataset.act === "fw-gosched") {
      const go = S.fw.go; if (!go.sel.size || !go.image || go.busy) return;
      if ((go.rows || []).some((r) => go.sel.has(r.id) && ["running", "scheduled"].includes((r.ota || {}).state))) return;
      const opts = { ...go.opts };
      if (act.dataset.act === "fw-gosched") {
        const w = await askSchedule(go); if (!w) return;
        go.nightAt = w.at; go.nightUntil = w.until;
        opts.at = w.at; opts.until = w.until;
      }
      if (!await ask(t("fwGoStartQ", { n: go.sel.size, i: go.image }) + "\n\n" + t("fwGoStartNote") + (opts.at ? "\n" + t("fwGoWin", { a: opts.at, u: opts.until }) : ""))) return;
      go.busy = true; render();
      try {
        const r = await api("POST", "/api/v2/fw/gwota/start", { ids: [...go.sel], image: go.image, opts });
        const ok = r.rows.filter((x) => !x.error), bad = r.rows.filter((x) => x.error);
        toast(t("fwGoStarted", { n: ok.length }) + (bad.length ? " · " + t("fwGoSkipped", { n: bad.length, why: bad[0].error }) : ""));
      } catch (e) { fail(e); } finally { go.busy = false; await fwGoPoll(true); render(); }
    } else if (act.dataset.act === "fw-goabort") {
      const go = S.fw.go, ids = (go.rows || []).filter((r) => ["running", "scheduled"].includes((r.ota || {}).state)).map((r) => r.id);
      if (!ids.length || !await ask(t("fwGoAbortQ", { n: ids.length }))) return;
      try { await api("POST", "/api/v2/fw/gwota/abort", { ids }); } catch (e) { fail(e); }
      await fwGoPoll(true); render();
    } else if (act.dataset.act === "fw-goresult") {
      try {
        const r = await api("GET", "/api/v2/fw/gwota/result?id=" + encodeURIComponent(act.dataset.id) + "&n=0");
        const run = r.run || {}, mods = r.modules || [];
        $("#infobody").innerHTML = `<div class="stack"><div class="small muted">${esc(run.image || "")} · ${esc(run.state || "")} · ${esc(String(run.size || ""))} B</div><div style="max-height:60vh;overflow:auto"><table class="evtab"><tr><th>${t("fwGoMod")}</th><th>${t("fwGoState")}</th><th class="num">${t("fwGoFw")}</th><th class="num">${t("fwGoErr")}</th></tr>${mods.map((m) => `<tr><td>${esc(m.id)}</td><td class="${/failed|gave_up|no_reply/.test(m.st) ? "vbad" : /updated|same/.test(m.st) ? "" : "vwarn"}">${esc(m.st)}</td><td class="num">${esc(m.fw || "")}</td><td class="num">${esc(m.err || "")}</td></tr>`).join("")}</table></div></div>`;
        const d = $("#info"); d.classList.add("wide"); d.onclose = () => d.classList.remove("wide"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
      } catch (e) { fail(e); }
    } else if (act.dataset.act === "fw-dpput") {
      const d = S.fw.dp; if (!d.id || d.busy) return;
      const g = S.sites.find((x) => x.id === d.id) || {};
      d.busy = true; d.prog = null; render();
      const dpTimer = setInterval(async () => {
        try { d.prog = await api("GET", "/api/v2/fw/depot/progress?id=" + encodeURIComponent(d.id)); } catch (e) { return; }
        const box = $("#fwdpprog"); if (box && d.busy) box.innerHTML = dpProgHtml();
      }, 500);
      try {
        const key = d.image || ((S.fw.images && S.fw.images.module[0]) || {}).key;
        const r = d.file ? await api("POST", `/api/v2/fw/depot/put?id=${encodeURIComponent(d.id)}&name=${encodeURIComponent(d.fileName)}`, d.file, true)
          : await api("POST", "/api/v2/fw/depot/put", { id: d.id, image: key });
        d.slots = r.slots; toast(t("fwDpDone", { n: r.name, g: g.name }));
      } catch (e) { fail(e); } finally { clearInterval(dpTimer); d.busy = false; d.prog = null; render(); }
    } else if (act.dataset.act === "fw-dprefresh") {
      const d = S.fw.dp; if (!d.id || d.busy || d.op) return;
      d.op = "fwOpLoad"; render();
      try { await Promise.all([fwDepotLoad("dp"), new Promise((r) => setTimeout(r, 400))]); } finally { d.op = null; render(); }
    } else if (act.dataset.act === "fw-dpkeep") {
      const d = S.fw.dp; if (d.busy || d.op) return;
      d.op = "fwOpKeep"; d.prog = null; render();
      const kpTimer = setInterval(async () => {
        try { d.prog = await api("GET", "/api/v2/fw/depot/progress?id=" + encodeURIComponent(d.id)); } catch (e) { return; }
        const box = $("#fwdpprog"); if (box && d.op === "fwOpKeep") box.innerHTML = dpProgHtml();
      }, 400);
      try { const r = await api("POST", "/api/v2/fw/depot/keep", { id: d.id, slot: +act.dataset.slot }); S.fw.images = r.images; toast(t("fwDpKept", { n: r.kept.name })); } catch (e) { fail(e); }
      clearInterval(kpTimer); d.op = null; d.prog = null; render();
    } else if (act.dataset.act === "fw-keptdel") {
      if (!await ask(t("fwKeptDelQ", { n: act.dataset.name }))) return;
      try { const r = await api("POST", "/api/v2/fw/kept/delete", { name: act.dataset.name }); S.fw.images = r.images; if (S.fw.image === "kept:" + act.dataset.name) S.fw.image = ""; } catch (e) { fail(e); }
      render();
    } else if (act.dataset.act === "fw-dpdel") {
      const d = S.fw.dp, g = S.sites.find((x) => x.id === d.id) || {};
      if (!await ask(t("fwDpDelQ", { n: act.dataset.name, g: g.name }))) return;
      if (d.busy || d.op) return;
      d.op = "fwOpDel"; render();
      try { const r = await api("POST", "/api/v2/fw/depot/delete", { id: d.id, slot: +act.dataset.slot }); d.slots = r.slots; } catch (e) { fail(e); }
      d.op = null; render();
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
    } else if (act.dataset.act === "fw-imginfo") {
      const f = S.fw, kind = act.dataset.kind, im0 = f.images || {};
      const list = kind === "gw" ? im0.gateway : im0.module;
      const key = kind === "gw" ? f.gwImage : kind === "dp" ? (f.dp.image || ((im0.module || [])[0] || {}).key) : f.image;
      const im = (list || []).find((x) => x.key === key);
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
    } else if (act.dataset.act === "ins-mode") { S.ins.mode = act.dataset.m; render();
    } else if (act.dataset.act === "ins-cell" || act.dataset.act === "ins-row" || act.dataset.act === "ins-whole" || act.dataset.act === "ins-none") {
      const i = S.ins; if (i.running || !i.layout) return;
      if (act.dataset.act === "ins-cell") { const id = +act.dataset.id; i.sel.has(id) ? i.sel.delete(id) : i.sel.add(id); delete i.res[id]; }
      else if (act.dataset.act === "ins-row") { const ids = i.layout.ids.filter((x) => Math.floor(x / 10) === +act.dataset.r), all = ids.every((x) => i.sel.has(x)); ids.forEach((x) => { all ? i.sel.delete(x) : i.sel.add(x); delete i.res[x]; }); }
      else { i.sel = act.dataset.act === "ins-whole" ? new Set(i.layout.ids) : new Set(); i.res = {}; i.rows = []; i.summary = ""; i.banner = ""; i.text = ""; }
      insPaint(); insCaption(); const se = $("#inssel"); if (se) se.textContent = insSelText();
    } else if (act.dataset.act === "ins-run") { await insStart();
    } else if (act.dataset.act === "job-stop") { await api("POST", "/api/v2/ins/cancel", {});
    } else if (act.dataset.act === "ins-fromscan") { const L = S.ins.layout; if (!L || anyJob()) return; const have = new Set(L.ids); S.ins.sel = new Set(S.scan.found.map((f) => f.id).filter((x) => have.has(x))); S.ins.res = {}; insPaint(); insCaption(); const se = $("#inssel"); if (se) se.textContent = insSelText();
    } else if (act.dataset.act === "ins-clear") { insReset(); insPaint();
    } else if (act.dataset.act === "scan-clear") { Object.assign(S.scan, { found: [], asked: new Set(), at: 0, text: "", err: "" }); scanPaint(); const fs = document.querySelector("[data-act=ins-fromscan]"); if (fs) fs.remove();
    } else if (act.dataset.act === "scan-run") { S.scan.found = []; S.scan.text = ""; S.scan.asked = new Set(); S.scan.at = 0; S.scan.full = act.dataset.full === "1"; await jobStart("scan", "/api/v2/ins/scan", { id: S.mod.id, full: act.dataset.full === "1" });
    } else if (act.dataset.act === "scan-pick") { S.mod.dev = +act.dataset.id; S.mod.data = null; renderKeep(); await modRead();
    } else if (act.dataset.act === "rpt-run") {
      if (S.rpt.running) { rptOpen(); return; }             /* closed while it ran: just show it again */
      if (!S.gw.id) return; Object.assign(S.rpt, { id: S.gw.id, text: "", file: false, i: 0, total: 0, err: "", ready: false, soaks: [], soak: "", upName: "", upText: "", building: false, built: false, note: "" }); rptOpen();
      if (!await jobStart("report", "/api/v2/ins/report", { id: S.gw.id })) rptPaint();
    } else if (act.dataset.act === "rpt-upload") { $("#rptfile").click();
    } else if (act.dataset.act === "rpt-build") {
      const r = S.rpt; if (r.building) return;
      r.building = true; r.err = ""; rptPaint();
      try {
        const out = r.upText ? await api("POST", "/api/v2/ins/report/build?name=" + encodeURIComponent(r.upName), r.upText, true)
                             : await api("POST", "/api/v2/ins/report/build", { soak: r.soak });
        r.built = true; r.file = true; r.note = out.soak || "";
      } catch (e) { r.err = e.message; }
      r.building = false; rptPaint();
    } else if (act.dataset.act === "mod-setid") { await modSetId();
    } else if (act.dataset.act === "mod-reset") { await modReset();
    } else if (act.dataset.act === "ntp-use") {
      const n = await api("GET", "/api/v2/ntp?toward=" + encodeURIComponent(S.gw.id)); if (!n.ip) { toast(t("ntpNoIp")); return; }
      const k = S.gw.data.keys.find((x) => x.key === "net.ntp"); if (k && n.ip !== k.value) S.gw.edits["net.ntp"] = n.ip; else delete S.gw.edits["net.ntp"];
      if (!n.running && await ask(t("ntpUseQ"))) await api("POST", "/api/v2/ntp", { enabled: true, port: n.port });
      renderKeep();
    } else if (act.dataset.act === "pw-set") {
      const a = $("#pw1").value, b = $("#pw2").value; if (a !== b) { toast(t("pwMismatch")); return; } if (a.length < 6) { toast(t("pwShort")); return; }
      await api("POST", "/api/v2/auth", { password: a, current: ($("#pw0") || {}).value || "" }); location.href = "/login";
    } else if (act.dataset.act === "pw-clear") { if (!await ask(t("pwClearQ"))) return; await api("POST", "/api/v2/auth", { clear: true, current: ($("#pw0") || {}).value || "" }); S.me.auth = false; srvSettings();
    } else if (act.dataset.act === "col-status") {
      const all = Object.values((S.me.collector || {}).status || {}), ok = all.filter((r) => r.ok), old = all.filter((r) => /too old/.test(r.error || "")),
        bad = all.filter((r) => !r.ok && !/too old/.test(r.error || "")), at = all.map((r) => r.at || "").sort().pop() || "";
      const lines = [t("colLast", { at: at.slice(11, 16), n: ok.length, total: all.length, add: ok.reduce((a, r) => a + (r.new || 0), 0) })];
      if (old.length) lines.push(t("colOld", { names: old.map((r) => r.name).join(", ") }));
      bad.forEach((r) => lines.push(t("colErr", { name: r.name, e: r.error })));
      $("#infobody").innerHTML = `<p style="margin:0;white-space:pre-line">${esc(lines.join("\n"))}</p>`; const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    } else if (act.dataset.act === "about") {
      const th = lang === "th";
      $("#infobody").innerHTML = `<div class="stack"><b>Thanes Development Co., Ltd.</b>
        <p style="margin:0">${th ? "บริษัทจัดหาโซลูชันทางการแพทย์ วิทยาศาสตร์ และห้องปฏิบัติการให้โรงพยาบาล ห้องแล็บ และมหาวิทยาลัย ตั้งแต่ให้คำปรึกษาจนถึงดูแลระยะยาว มีประสบการณ์กว่า 35 ปี" : "A company supplying medical, scientific and laboratory solutions to hospitals, labs and universities, from consultation to long-term support, with over 35 years of experience."}</p>
        <p class="small muted" style="margin:0">${th ? "Smart Coldchain · Clean Room · Pathology · Pharmacy · ระบบท่อลำเลียง · AI และ Cloud" : "Smart Coldchain · Clean Room · Pathology · Pharmacy · Tube Systems · AI &amp; Cloud"}</p>
        <a href="https://www.thanesgroup.com/about/" target="_blank" rel="noopener noreferrer">thanesgroup.com</a></div>`;
      const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    } else if (act.dataset.act === "ins-info") { const x = INS_INFO[act.dataset.k]; $("#infobody").innerHTML = `<p style="margin:0;white-space:pre-line">${esc(x[lang === "th" ? 0 : 1])}</p>`; const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
    } else if (act.dataset.act === "hint") { showInfo(act.dataset.key);
    }
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
  if (ev.target.dataset && (ev.target.dataset.cabmode !== undefined || ev.target.dataset.cabrow !== undefined)) {
    const grid = document.querySelector("[data-cabgrid]"), cells = [...grid.querySelectorAll("[data-cabrow]")];
    if (ev.target.dataset.cabmode !== undefined) {
      const v = ev.target.value;
      if (v === "custom") {
        /* Start from the geometry of the preset it was on, so it is never an empty (refused) shape. */
        const cur = hubRows(cabCur("panel.shape")), shape = cur.some((n) => n > 0) ? cur.join(",") : (CAB_PRESET[+cabCur("panel.cabinet")] || CAB_PRESET[80]);
        hubRows(shape).forEach((n, i) => { cells[i].value = n; });
        cabSet(0, shape); grid.hidden = false;
      } else { cabSet(+v, "0"); grid.hidden = true; }
    } else {
      const shape = cells.map((x) => x.value).join(",");
      cabSet(shape.split(",").some((n) => +n > 0) ? 0 : cabCur("panel.cabinet"), shape);
    }
    const saved = hubRows(cabSaved("panel.shape")), edited = "panel.cabinet" in S.gw.edits || "panel.shape" in S.gw.edits;
    cells.forEach((x, i) => { x.style.borderColor = +x.value !== saved[i] ? "var(--brand)" : ""; });
    document.querySelector("[data-cabmode]").style.borderColor = edited ? "var(--brand)" : "";
    gwBar(); return;
  }
  if (ev.target.dataset && (ev.target.dataset.schday !== undefined || ev.target.dataset.schslot !== undefined || ev.target.dataset.schtime !== undefined)) {
    const q = (sel) => [...document.querySelectorAll(sel)], el = ev.target, mark = (x, on) => { x.style.borderColor = on ? "var(--brand)" : ""; };
    if (el.dataset.schday !== undefined) {
      const boxes = q("[data-schday]"), on = boxes.map((x) => x.checked);
      if (!on.some(Boolean)) { el.checked = true; return; }              /* no day ticked would mean "every day": keep one */
      const mask = on.reduce((m, v, i) => m | (v ? 1 << i : 0), 0), saved = schSaved("sched.reset_days");
      schSet("sched.reset_days", mask === 127 ? (saved === 0 || saved === 127 ? saved : 0) : mask);
    } else if (el.dataset.schslot !== undefined) {
      schSet("sched.reset_slots", q("[data-schslot]").reduce((m, x, i) => m | (x.checked ? 1 << i : 0), 0));
      q("[data-schtime]")[+el.dataset.schslot].classList.toggle("off", !el.checked);
    } else if (/^\d\d:\d\d$/.test(el.value)) {
      const i = +el.dataset.schtime, kk = schHhmmKey(i); schSet(kk, +el.value.slice(0, 2) * 100 + +el.value.slice(3)); mark(el, kk in S.gw.edits);
    }
    gwBar(); return;
  }
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
});
/* Filter groups: stacked and collapsible on a phone; on a wide screen they are drop-downs in one row, one open at a time,
   closed again by a click anywhere else or Esc. */
const evWide = () => matchMedia("(min-width: 900px)").matches;
function evCloseGroups(except) {
  for (const g of document.querySelectorAll(".fgrp[open]")) if (g !== except) g.open = false;
  for (const k of [...S.ev.open]) if (!except || k !== except.dataset.g) S.ev.open.delete(k);
}
document.addEventListener("toggle", (e) => { if (e.target.dataset && e.target.dataset.fwsec) { const was = (S.fw.open || {})[e.target.dataset.fwsec]; (S.fw.open = S.fw.open || {})[e.target.dataset.fwsec] = e.target.open; if (e.target.dataset.fwsec === "go" && e.target.open && !was) fwGoPoll(true).then(render); } if (e.target.id === "soakadv") S.soak.adv = e.target.open; if (e.target.id === "fwgoadv") S.fw.go.adv = e.target.open; }, true);
document.addEventListener("toggle", (e) => {
  const g = e.target.closest && e.target.closest(".fgrp"); if (!g) return;
  if (g.open) { if (evWide()) evCloseGroups(g); S.ev.open.add(g.dataset.g); } else S.ev.open.delete(g.dataset.g);
}, true);
document.addEventListener("pointerdown", (e) => { if (evWide() && S.ev.open.size && !e.target.closest(".fgrp")) evCloseGroups(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape" && evWide() && S.ev.open.size) evCloseGroups(); });
document.addEventListener("change", async (ev) => {
  if (ev.target.id === "modsel") { S.mod.id = ev.target.value; S.mod.data = null; if (S.mod.id) modRead(); else render(); insLayout(); }
  if (ev.target.id === "ntpon" || ev.target.id === "ntpport") ntpApply();
  if (ev.target.id === "colon" || ev.target.id === "colkeep") colApply(ev.target);
  if (ev.target.dataset && ev.target.dataset.ins) {
    const k = ev.target.dataset.ins, el = ev.target;
    S.ins[k] = el.type === "checkbox" ? el.checked : el.type === "number" ? +el.value
      : ["preset", "batch", "timeout"].includes(k) ? +el.value : ["unlock", "identify", "display", "punlock"].includes(k) ? el.value === "1" : el.value;
    if (k === "action" || k === "off") renderKeep(); else insCaption();   /* the latch step follows these two */          /* no light, no latch: the latch step greys out */
  }
  if (ev.target.id === "moddev") { S.mod.dev = Math.max(1, Math.min(247, +ev.target.value || 1)); S.mod.data = null; }
  if (ev.target.id === "modall") { S.mod.showAll = ev.target.checked; renderKeep(); }
  if (ev.target.id === "modauto") { S.mod.auto = ev.target.checked; modAutoSync(); }
  if (ev.target.id === "gwsel") { S.gw.id = ev.target.value; S.gw.data = null; S.gw.edits = {}; if (S.gw.id) gwRead(); else render(); }
  if (ev.target.dataset && ev.target.dataset.expcab !== undefined && S.soak.view) { const w = S.soak.view; if (ev.target.checked) w.pick.add(ev.target.dataset.expcab); else w.pick.delete(ev.target.dataset.expcab); soakViewSync(); }
  if (ev.target.id === "soakgap") { S.soak.gap = Math.max(0.1, Math.min(30, +ev.target.value || 2)); $("#soakadvwarn").innerHTML = soakAdvWarn(); }
  if (ev.target.id === "soakevery") S.soak.every = Math.max(1, Math.min(100, Math.round(+ev.target.value) || 5));
  if (ev.target.id === "soakslow") S.soak.slow = Math.max(50, Math.min(5000, Math.round(+ev.target.value) || 400));
  if (ev.target.id === "soaktmo") { S.soak.tmo = Math.max(4, Math.min(30, +ev.target.value || 6)); $("#soakadvwarn").innerHTML = soakAdvWarn(); }
  if (ev.target.id === "soakpicks") { S.soak.picks = +ev.target.value; soakEstimate(); }
  if (ev.target.id === "soakdwell") { S.soak.dwell = +ev.target.value; soakEstimate(); }
  if (ev.target.id === "soakwins") { S.soak.windows = Math.max(1, Math.min(8, +ev.target.value || 8)); soakEstimate(); }
  if (ev.target.id === "soakstart") { S.soak.startMode = ev.target.value; render(); }
  if (ev.target.id === "soakdur") { if (ev.target.value === "until") S.soak.durMode = "until"; else { S.soak.durMode = "hours"; S.soak.hours = +ev.target.value; } render(); }
  for (const [id, key] of [["soaksh", "sh"], ["soaksm", "sm"], ["soakeh", "eh"], ["soakem", "em"]]) if (ev.target.id === id) { S.soak[key] = +ev.target.value; render(); }
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
  if (ev.target.dataset && ev.target.dataset.gopick !== undefined) { const g = S.fw.go; if (ev.target.checked) g.sel.add(ev.target.dataset.gopick); else g.sel.delete(ev.target.dataset.gopick); g.rows = null; fwGoNames().then(() => fwGoPoll(true)); }
  if (ev.target.id === "rptsoak") { S.rpt.soak = ev.target.value; S.rpt.upText = ""; S.rpt.upName = ""; rptPaint(); }
  if (ev.target.id === "rptfile" && ev.target.files[0]) { const f = ev.target.files[0]; S.rpt.upText = await f.text(); S.rpt.upName = f.name; S.rpt.soak = ""; rptPaint(); }
  if (ev.target.id === "fwgoimage") S.fw.go.image = ev.target.value;
  if (ev.target.id === "fwgoidle") S.fw.go.opts.idle = +ev.target.value || 5;
  if (ev.target.id === "fwgogroup") S.fw.go.opts.group = Math.max(1, Math.min(8, +ev.target.value || 8));
  if (ev.target.id === "fwgoapplyidle") S.fw.go.opts.apply_idle = +ev.target.value || 5;
  if (ev.target.id === "fwgoapplyquiet") S.fw.go.opts.apply_quiet = Math.max(0, +ev.target.value || 0);
  if (ev.target.id === "fwsrc") { S.fw.src = ev.target.value; render(); }
  if (ev.target.id === "fwsrcgw") { S.fw.srcId = ev.target.value; fwDepotLoad("src"); }
  if (ev.target.id === "fwsrcslot") S.fw.srcSlot = +ev.target.value;
  if (ev.target.id === "fwdpsel") { S.fw.dp.id = ev.target.value; fwDepotLoad("dp"); }
  if (ev.target.id === "fwdpimage") { S.fw.dp.image = ev.target.value; S.fw.dp.file = null; S.fw.dp.fileName = ""; }
  if (ev.target.id === "fwdpfile" && ev.target.files[0]) { S.fw.dp.file = await ev.target.files[0].arrayBuffer(); S.fw.dp.fileName = ev.target.files[0].name; render(); }
  if (ev.target.id === "fwgwsel") { S.fw.gwId = ev.target.value; render(); }
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
  if (ev.target.dataset && ev.target.dataset.f && ev.target.type === "checkbox") {
    const set = evSet(ev.target.dataset.f); ev.target.checked ? set.add(ev.target.value) : set.delete(ev.target.value);
    S.ev.page = 0; evRefresh();
    const g = ev.target.closest(".fgrp"), cnt = g && g.querySelector(".fcnt"); if (g && !cnt && set.size) renderFilters(); else if (cnt) cnt.textContent = set.size || "";
    const ch = $("#evchips"); if (ch) { renderFilters(); }
  }
  if (ev.target.id === "evsize") { S.ev.size = +ev.target.value; S.ev.page = 0; try { localStorage.setItem("lgs.evsize", String(S.ev.size)); } catch (e) { /* not remembered */ } loadEvents(); }
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
/* The module details box stays as the person left it across the auto-read's re-renders. */
document.addEventListener("toggle", (e) => { if (e.target.id === "moddet") S.mod.open = e.target.open; }, true);
$("#rptclose").onclick = () => $("#rptdlg").close();
$("#rptcancel").onclick = () => api("POST", "/api/v2/ins/cancel", {}).catch(fail);
$("#info").addEventListener("click", (e) => { if (e.target.id === "info") $("#info").close(); });
function settingsText() {
  $("#setbtn").textContent = "⚙"; $("#setbtn").setAttribute("aria-label", t("settings")); $("#setbtn").title = t("settings"); $("#settitle").textContent = t("settings"); $("#setclose").textContent = t("close");
  $("#langlbl").textContent = t("language"); $("#modelbl").textContent = t("mode"); $("#themelbl").textContent = t("theme");
  $("#langsel").value = lang;
}
$("#setbtn").onclick = () => { const d = $("#settings"); srvSettings(); if (d.showModal) d.showModal(); else d.setAttribute("open", ""); };
$("#setclose").onclick = () => $("#settings").close();
$("#settings").addEventListener("click", (e) => { if (e.target.id === "settings") $("#settings").close(); });
$("#langsel").onchange = (e) => { lang = e.target.value; try { localStorage.setItem("lgs.lang", lang); } catch (x) { /* not remembered */ } render(); };
const THEMES = ["auto", "light", "dark", "ocean", "forest", "sand", "rose", "lavender", "ember", "graphite"];
function setTheme(name) {
  const r = document.documentElement;
  if (name === "auto" || !THEMES.includes(name)) r.removeAttribute("data-theme"); else r.dataset.theme = name;
  try { localStorage.setItem("lgs.theme", THEMES.includes(name) ? name : "auto"); } catch (e) { /* not remembered */ }
}
function themeSelect() { const el = $("#themesel"); el.setAttribute("aria-label", t("theme")); el.innerHTML = THEMES.map((n) => `<option value="${n}"${n === themeNow ? " selected" : ""}>${t("th_" + n)}</option>`).join(""); }
let themeNow = "ocean"; try { const th = localStorage.getItem("lgs.theme"); if (THEMES.includes(th)) themeNow = th; } catch (e) { /* storage blocked: stay on the default (ocean) */ }
setTheme(themeNow);
function modeSelect() { const el = $("#modesel"); el.setAttribute("aria-label", t("mode")); el.innerHTML = ["basic", "advanced"].map((m) => `<option value="${m}"${m === uiMode ? " selected" : ""}>${t(m)}</option>`).join(""); }
$("#modesel").onchange = (e) => { uiMode = e.target.value; try { localStorage.setItem("lgs.mode", uiMode); } catch (x) { /* not remembered */ } clearInterval(S.fw.timer); S.fw.timer = null; render(); srvSettings(); };
$("#themesel").onchange = (e) => { themeNow = e.target.value; setTheme(themeNow); };

(async () => {
  try {
    S.me = await api("GET", "/api/v2/me"); $("#ver").textContent = "v" + S.me.version;
    await loadSites();
    S.mod.presets = (await api("GET", "/api/v2/mod/presets")).presets;
    S.soak.runs = (await api("GET", "/api/v2/soak/runs")).runs;
    S.lab.opts = await api("GET", "/api/v2/labels/options"); S.lab.layout = S.lab.opts.default_layout; S.lab.plate = S.lab.opts.default_plate;
    S.fw.images = await api("GET", "/api/v2/fw/images"); S.fw.image = (S.fw.images.module[0] || {}).key || ""; S.fw.gwImage = (S.fw.images.gateway[0] || {}).key || "";
  } catch (e) { fail(e); }
  render();
})();
