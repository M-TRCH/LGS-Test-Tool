/* LGS Test Tool v2 front end, stage 1: Cabinets, Sites, Events. Plain JS, no libraries. */
"use strict";

const TXT = {
  th: {
    stage: "v2 preview", classic: "แบบเดิม", cabinets: "ตู้", sites: "รายการตู้", events: "เหตุการณ์",
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
    setClock: "ซิงค์เวลาจากเครื่องนี้", hubRow: "แถว {n}", hubDirect: "ต่อตรง", hubCh: "ช่อง {n}", cabCustom: "กำหนดเอง", cabSlots: "{n} ช่อง", cabNone: "ไม่มี", insFromScan: "จากผลสแกน", jobBusy: "มีงานอื่นกำลังทำงานอยู่ รอให้เสร็จก่อน", scanTitle: "สแกนหาโมดูล", scanQuick: "สแกนเร็ว (ตามผังตู้)", scanFull: "สแกนเต็ม (1–247)", scanProg: "ถาม ID {id} ({i}/{total})", scanDone: "พบ {n} โมดูล จากที่ถาม {total} ID", swTitle: "ทดสอบโมดูลแบบเต็มชุด", swLoops: "จำนวนรอบ", swLights: "ทดสอบไฟ พรีเซ็ต และจอ", swLatch: "ทดสอบปลดกลอนด้วย (กลอนจะทำงานจริง)", swRun: "เริ่มทดสอบโมดูล {id}", swPhase: "ขั้น {p} ({i}/{total})", swPhaseCol: "ขั้น", swDone: "เสร็จ: ผ่าน {ok} ไม่ผ่าน {fail} ผิดพลาด {err}", swLatchQ: "การทดสอบนี้จะปลดกลอนโมดูล {id} จริง ดำเนินการต่อไหม?", rptBtn: "สร้างรายงานไซต์ (PDF)", rptProg: "อ่านโมดูล {id} ({i}/{total})", rptDone: "เสร็จ: ตอบสนอง {a}/{n} โมดูล", rptFile: "ดาวน์โหลดรายงาน", dangerTitle: "จัดการโมดูล", setIdNew: "Slave ID ใหม่", setIdBtn: "เปลี่ยน ID ของโมดูล {id}", setIdNeed: "ใส่ Slave ID ใหม่ก่อน", setIdQ: "เปลี่ยน Slave ID ของโมดูล {from} เป็น {to} แล้วบันทึก โมดูลจะรีบูต พิมพ์ {to} เพื่อยืนยัน", setIdBusy: "กำลังเปลี่ยน ID (ราว 5 วินาที)...", setIdDone: "เปลี่ยนเป็น ID {id} แล้ว", resetBtn: "รีเซ็ตซอฟต์แวร์โมดูล {id}", resetQ: "รีบูตโมดูล {id} พิมพ์ {id} เพื่อยืนยัน", resetBusy: "กำลังรีบูตโมดูล...", resetDone: "โมดูลกลับมาแล้ว", ntpTitle: "ให้เครื่องนี้เป็น NTP server", ntpChipOn: "ทำงาน · พอร์ต {port}", ntpChipErr: "เปิดไม่ได้", ntpServed: "ตอบเวลาไปแล้ว {n} ครั้ง", ntpPort: "พอร์ต", pwChipOn: "ตั้งแล้ว", pwChipOff: "ยังไม่ได้ตั้ง", ntpOn: "ทำงานอยู่ที่พอร์ต {port} ตอบไปแล้ว {n} ครั้ง", ntpOff: "ปิดอยู่", ntpErr: "เปิดไม่ได้: {e}", optOn: "เปิด", optOff: "ปิด", ntpUsePc: "ใช้เครื่องนี้", ntpNoIp: "หาไอพีของเครื่องนี้ฝั่งเกตเวย์ไม่เจอ", ntpUseQ: "NTP server ในเครื่องนี้ยังปิดอยู่ เปิดเลยไหม?", pwTitle: "รหัสผ่านหน้าเว็บ", pwOn: "ตั้งรหัสไว้แล้ว", pwOff: "ยังไม่ได้ตั้ง ทุกคนในเครือข่ายเปิดหน้านี้ได้", pwNew: "รหัสใหม่", pwRepeat: "พิมพ์ซ้ำ", pwSet: "ตั้งรหัส", pwClear: "ลบรหัส", pwMismatch: "รหัสสองช่องไม่ตรงกัน", pwShort: "รหัสต้องยาวอย่างน้อย 6 ตัวอักษร", pwClearQ: "ลบรหัสผ่าน ทุกคนในเครือข่ายจะเปิดหน้านี้ได้ ดำเนินการต่อไหม?", insTitle: "ตรวจการติดตั้ง", insPickCab: "เลือกตู้ด้านบนก่อน", insMods: "โมดูลที่จะตรวจ", insSel: "เลือกแล้ว {n}", insWhole: "ทั้งตู้", insClear: "ล้าง", insModeCheck: "ตรวจทั่วไป", insModePick: "ทดสอบลำดับหยิบยา", insWhat: "จะทำอะไรกับแต่ละโมดูล", insA_skip: "ข้าม (แค่ตรวจว่าตอบสนอง)", insA_light: "เปิดไฟ", insA_light_display: "เปิดไฟ+จอ", insHold: "ค้างแต่ละขั้น (วินาที)", insIdentify: "ระบุตัวตน (กะพริบสีขาว ~5 วินาที)", insUnlock: "ปลดกลอนด้วย (กลอนจะทำงานจริง)", insCoil: "จะส่ง coil {coil} ({what})", insWarnUnlock: "รอบนี้จะปลดล็อก {n} โมดูล", insPreset: "พรีเซ็ตสี", insBatch: "จุดพร้อมกัน (ช่อง)", insTimeout: "รอสูงสุดต่อชุด (วินาที)", insPDisplay: "โชว์เลขช่องบนจอ", insPUnlock: "ปลดกลอน (กลอนจะทำงานจริง)", insPClosed: "รอปิดลิ้นชักก่อนดับไฟ", insPBych: "หนึ่งชุดอยู่ช่องฮับเดียว", insRun: "เริ่มตรวจ", insPickRun: "เริ่มเดินทดสอบ", insCancel: "ยกเลิก", insCsv: "บันทึก CSV", insIdle: "ว่าง", insStarting: "กำลังเริ่ม...", insProg: "โมดูล {id} ({i}/{total})", insPrep: "กำลังเปิดไฟช่อง {id} ({i}/{total})", insWaiting: "ไฟติด {n} ช่อง กดปุ่มหน้าช่อง หยิบช่องไหนก่อนก็ได้", insClosing: "รอปิดลิ้นชัก {n} ช่อง, ไฟยังติดอีก {lit} ช่อง", insDone: "เสร็จ {n} โมดูล", insAnswered: "ตอบสนอง {n}/{total}", insMissing: "ไม่ตอบสนอง: {ids}", insFailedIds: "ทำบางขั้นไม่ผ่าน: {ids}", insPass: "✓ ผ่าน", insNoAns: "✗ ไม่ตอบสนอง", insFail: "✗ ไม่ผ่าน", insType: "ชนิด", insResult: "ผล", insDetail: "รายละเอียด", insB_run: "กำลังทำงาน", insB_pass: "ผ่านทั้งหมด", insB_issues: "พบปัญหา", insB_cancelled: "ยกเลิกแล้ว", insPickOne: "เลือกอย่างน้อยหนึ่งโมดูล", insUnlockQ: "รอบนี้จะปลดล็อก {n} โมดูล กลอนจะทำงานจริง ดำเนินการต่อไหม?", cabEmpty: "รูปทรงตู้แบบกำหนดเองต้องมีอย่างน้อยหนึ่งแถวที่มีช่อง", schDays: "วันที่รีเซ็ต", schTimes: "เวลารีเซ็ต", schSlot: "ช่วงที่ {n}", schEvery: "ทุกวัน", schNoTime: "ไม่ได้เปิดช่วงเวลาใด", schName: "ตารางรีเซ็ต", schDay: ["อาทิตย์", "จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์"], schDayS: ["อา", "จ", "อ", "พ", "พฤ", "ศ", "ส"],
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
    mUnlockedAgo: "ปลดล่าสุด {s} วินาทีก่อน", mDisplay: "ตัวเลขบนจอ", na: "ไม่มี", presets: "พรีเซ็ตสี", pLight: "ไฟ", pLightDisp: "ไฟ + เลข", pUnlock: "ปลดกลอน", pUnlockDisp: "ปลดกลอน + เลข", grpLight: "ไฟ", grpLatch: "กลอน", grpOther: "จอและอื่น ๆ", cLight: "เปิดไฟ", cLightNum: "เปิดไฟ + เลข", dispOff: "ปิดจอ", colorTitle: "{c} · เลือกสี", colorN: "สี {n}",
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
    lbPreview: "ดูตัวอย่างข้อมูล", lbDownload: "ดาวน์โหลด .lbx", expCfg: "ส่งออก config", impCfg: "นำเข้า config", impDone: "นำเข้า {n} ค่า (ยังไม่บันทึก ตรวจแล้วกดบันทึกลงเกตเวย์)", impNone: "ไม่มีค่าที่ต่างจากเกตเวย์",
    shapeBad: "ชนิดตู้ใน รายการตู้ ({l}) ไม่ตรงกับเกตเวย์: {w}", shapeFix: "ตั้งค่าที่ตรงให้ (ยังไม่บันทึก)", shapeNoFix: "เกตเวย์รุ่นนี้แก้เองไม่ได้ (ไม่มี panel.shape)",
    fwOta: "อัปเดตโมดูลผ่าน OTA (หลายตู้)", fwImage: "อิมเมจ", fwStart: "เริ่มอัปเดต", fwCancel: "ยกเลิก", fwCancelQ: "ยกเลิกการอัปเดต? โมดูลที่ค้างอยู่ในเซสชันอาจต้องอัปเดตซ้ำ",
    fwStartQ: "อัปเดตเฟิร์มแวร์โมดูลทุกตัวใน {n} ตู้ด้วย {i}? ทำย้อนจากหน้านี้ไม่ได้ ตู้ที่ใช้งานอยู่จะใช้ไม่ได้ระหว่างอัปเดต", fwRun: "กำลังอัปเดต", fwNoOta: "ยังไม่มีอิมเมจ OTA ในโปรแกรมนี้",
    fwGw: "อัปเดตเกตเวย์ผ่านเครือข่าย (ทีละตู้)", fwGwNote: "เกตเวย์รีบูตตอนจบ และตัดไฟเลี้ยงโมดูลชั่วครู่ (โมดูลทุกตัวรีบูตด้วย) พิมพ์ชื่อตู้เพื่อยืนยัน", fwUpload: "หรือเลือกไฟล์ .bin เอง", fwConfirm: "พิมพ์ชื่อตู้เพื่อยืนยัน",
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
    stage: "v2 preview", classic: "Classic UI", cabinets: "Cabinets", sites: "Sites", events: "Events",
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
    setClock: "Sync time from this PC", hubRow: "Row {n}", hubDirect: "Direct", hubCh: "Channel {n}", cabCustom: "Custom", cabSlots: "{n} slots", cabNone: "None", insFromScan: "From the scan", jobBusy: "Another job is running; wait for it to finish", scanTitle: "Scan for modules", scanQuick: "Quick scan (cabinet layout)", scanFull: "Full scan (1-247)", scanProg: "asking id {id} ({i}/{total})", scanDone: "found {n} module(s) out of {total} ids asked", swTitle: "Full module test", swLoops: "Rounds", swLights: "Test lights, presets and display", swLatch: "Also test the latch (it really moves)", swRun: "Test module {id}", swPhase: "phase {p} ({i}/{total})", swPhaseCol: "phase", swDone: "done: {ok} ok, {fail} fail, {err} error", swLatchQ: "This test really unlocks module {id}. Continue?", rptBtn: "Site report (PDF)", rptProg: "reading module {id} ({i}/{total})", rptDone: "done: {a}/{n} modules answered", rptFile: "Download report", dangerTitle: "Module management", setIdNew: "New slave id", setIdBtn: "Change id of module {id}", setIdNeed: "Enter the new slave id first", setIdQ: "Change module {from} to slave id {to} and save it; the module reboots. Type {to} to confirm.", setIdBusy: "Changing the id (about 5 s)...", setIdDone: "Now at id {id}", resetBtn: "Software reset module {id}", resetQ: "Reboot module {id}. Type {id} to confirm.", resetBusy: "Rebooting the module...", resetDone: "The module is back", ntpTitle: "This PC as NTP server", ntpChipOn: "on · port {port}", ntpChipErr: "cannot start", ntpServed: "{n} time answer(s) so far", ntpPort: "Port", pwChipOn: "set", pwChipOff: "not set", ntpOn: "serving on port {port}, {n} answer(s) so far", ntpOff: "off", ntpErr: "cannot start: {e}", optOn: "On", optOff: "Off", ntpUsePc: "Use this PC", ntpNoIp: "cannot tell this PC's address toward the gateway", ntpUseQ: "The NTP server on this PC is off. Switch it on?", pwTitle: "Web password", pwOn: "a password is set", pwOff: "not set: anyone on the network can open this page", pwNew: "New password", pwRepeat: "Repeat", pwSet: "Set password", pwClear: "Remove password", pwMismatch: "the two passwords differ", pwShort: "at least 6 characters", pwClearQ: "Remove the password? Anyone on the network will be able to open this page.", insTitle: "Installation check", insPickCab: "Pick a cabinet above first", insMods: "Modules to check", insSel: "{n} selected", insWhole: "Whole cabinet", insClear: "Clear", insModeCheck: "General check", insModePick: "Pick walkthrough", insWhat: "What to do on each module", insA_skip: "Skip (only check it answers)", insA_light: "Light", insA_light_display: "Light + display", insHold: "Hold each step (s)", insIdentify: "Identify (blink white ~5 s)", insUnlock: "Also throw the latch (it really moves)", insCoil: "will send coil {coil} ({what})", insWarnUnlock: "this run will unlock {n} module(s)", insPreset: "Colour preset", insBatch: "Light together (slots)", insTimeout: "Timeout per batch (s)", insPDisplay: "Show the slot number", insPUnlock: "Release the latch (it really moves)", insPClosed: "Wait for the drawer to close", insPBych: "Keep a batch on one hub channel", insRun: "Run check", insPickRun: "Start walkthrough", insCancel: "Cancel", insCsv: "Export CSV", insIdle: "idle", insStarting: "starting...", insProg: "module {id} ({i}/{total})", insPrep: "lighting slot {id} ({i}/{total})", insWaiting: "{n} slots lit: press each slot's button, in any order", insClosing: "{n} waiting to be closed, {lit} still lit", insDone: "done: {n} module(s)", insAnswered: "answered {n}/{total}", insMissing: "no answer: {ids}", insFailedIds: "failed a step: {ids}", insPass: "✓ pass", insNoAns: "✗ no answer", insFail: "✗ fail", insType: "type", insResult: "result", insDetail: "detail", insB_run: "RUNNING", insB_pass: "ALL PASS", insB_issues: "ISSUES FOUND", insB_cancelled: "CANCELLED", insPickOne: "select at least one module", insUnlockQ: "This run will unlock {n} module(s); the latches really move. Continue?", cabEmpty: "A custom cabinet shape needs at least one row with slots", schDays: "Reset days", schTimes: "Reset times", schSlot: "Time {n}", schEvery: "Every day", schNoTime: "No time switched on", schName: "Reset schedule", schDay: ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], schDayS: ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
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
    mUnlockedAgo: "last unlock {s} s ago", mDisplay: "Display number", na: "n/a", presets: "Colour presets", pLight: "Light", pLightDisp: "Light + number", pUnlock: "Unlock", pUnlockDisp: "Unlock + number", grpLight: "Light", grpLatch: "Latch", grpOther: "Display and more", cLight: "Light", cLightNum: "Light + number", dispOff: "Display off", colorTitle: "{c} · pick a colour", colorN: "Colour {n}",
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
    lbPreview: "Preview data", lbDownload: "Download .lbx", expCfg: "Export config", impCfg: "Import config", impDone: "Imported {n} values (not saved yet: review, then Save to gateway)", impNone: "Nothing differs from the gateway",
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

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: "", days: 1, q: "", types: new Set() }, gw: { id: "", data: null, edits: {}, busy: false }, lab: { id: "", ward: "", serial: "", layout: "", plate: "", opts: null, info: null, busy: false }, fw: { images: null, sel: new Set(), image: "", ota: null, gwId: "", gwImage: "", gwConfirm: "", gwFile: null, gwFileName: "", gw: null, timer: null }, soak: { sel: new Set(), mode: "pharmacy", picks: 2000, hours: 12, startAt: "", status: null, runs: [], verdict: "", timer: null, was: false }, mod: { id: "", dev: 11, data: null, busy: false, auto: false, stats: false, presets: [], lockUntil: 0 },
  ins: { id: "", layout: null, sel: new Set(), mode: "check", action: "light", unlock: false, identify: false, hold: 1, preset: 1, batch: 4, timeout: 60, display: true, punlock: true, closed: true, bych: true, running: false, since: 0, res: {}, rows: [], lit: new Set(), closing: new Set(), testing: null, text: "", banner: "", summary: "", file: false, err: "" },
  scan: { running: false, found: [], text: "", err: "", file: false },
  sweep: { running: false, loops: 1, lights: true, latch: false, text: "", banner: "", phases: [], bad: [], err: "", file: false },
  rpt: { id: "", running: false, text: "", err: "", file: false },
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


const PCOL = { 1: "#ff3232", 2: "#32ff32", 3: "#3264ff", 4: "#ffd700", 5: "#00e5e5", 6: "#ff32ff", 7: "#ff5a1e", 8: "#fff096" };
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
       Three columns that each keep their own height, so a short section is never stretched to match a tall one. */
    cards = `<details class="card" id="moddet"${m.open ? " open" : ""}><summary class="row" style="gap:8px;cursor:pointer"><b>${t("modInfo")}</b><span class="small muted">ID ${dv.id} · ${esc(pl(dv.type))} · ${esc(pl(dv.fw))}</span>${sumChip}</summary>
      <div class="mgrid"><div class="mcol">${device}${runtime}</div><div class="mcol">${health}${latch}</div><div class="mcol">${stats}</div></div>
      <p class="small muted" style="margin:10px 0 0">${t("checkedAt", { at: esc(d.at) })} · ${d.ms} ms</p></details>`;
  }
  const lb = (addr, label, cls) => `<button class="btn ${cls || ""}" data-act="mod-coil" data-addr="${addr}" data-val="1"${cls === "latch" ? " data-latch=1" : ""}>${label}</button>`;
  const cb = (kind, label, latch) => `<button class="btn" data-act="mod-color" data-kind="${kind}"${latch ? " data-latch=1" : ""}>${label}</button>`;
  return `<h1>${t("module_page")}</h1>
    <section class="card stack"><div class="row" style="align-items:flex-end"><div class="field" style="min-width:220px;flex:1"><label>${t("pick")}</label><select id="modsel"><option value="">—</option>${opts}</select></div>
      <div class="field" style="width:140px"><label>${t("devId")}</label><input id="moddev" type="number" min="1" max="247" value="${m.dev}"></div>
      <button class="btn primary" data-act="mod-read" style="flex:none;min-width:112px;white-space:nowrap">${m.busy ? t("reading") : t("read")}</button></div>
      <div class="row"><label class="row"><input type="checkbox" id="modauto"${m.auto ? " checked" : ""}> ${t("auto")}</label></div></section>
    <div class="stack" style="margin-top:12px">${cards}
      <h2>${t("quick")}</h2><section class="card stack">
        <div class="stack tight"><b class="small muted">${t("grpLight")}</b><div class="qgrid">${cb("enable", t("cLight"))}${cb("display", t("cLightNum"))}</div></div>
        <div class="stack tight"><b class="small muted">${t("grpLatch")}</b><div class="qgrid">${cb("latch", t("pUnlock"), 1)}${cb("latch_display", t("pUnlockDisp"), 1)}${lb(1020, t("latchSafety"), "latch")}${lb(1019, t("latchForce"), "latch")}</div></div>
        <div class="stack tight"><b class="small muted">${t("grpOther")}</b><div class="qgrid">${lb(509, t("identify"))}${lb(511, t("allOff"))}
          <button class="btn" data-act="mod-coil" data-addr="1010" data-val="1">${t("dispPower")}</button><button class="btn" data-act="mod-coil" data-addr="1010" data-val="0">${t("dispOff")}</button></div></div>
        <div class="row" style="align-items:flex-end"><div class="field" style="width:160px"><label>${t("number")}</label><input id="modnum" type="number" min="0" max="9999" value="45"></div><button class="btn" data-act="mod-number">${t("writeNumber")}</button></div>
        <p class="small muted">${t("cooldownNote")}</p></section>
      ${uiMode === "advanced" ? `<h2>${t("swTitle")}</h2><section class="card stack">${sweepView()}</section>
      <h2>${t("dangerTitle")}</h2><section class="card stack" style="border-color:var(--bad)">${dangerView()}</section>` : ""}
      <h2>${t("scanTitle")}</h2><section class="card stack">${scanView()}</section>
      <h2>${t("insTitle")}</h2><section class="card stack">${insView()}</section></div>`;
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
/* One popup for "which colour": the command is chosen first, the preset (1-8) second. Resolves with the preset number, or 0 if cancelled. */
function pickColor(command) {
  return new Promise((resolve) => {
    const d = $("#colorpick"); $("#colortitle").textContent = t("colorTitle", { c: command });
    $("#colorgrid").innerHTML = [1, 2, 3, 4, 5, 6, 7, 8].map((n) => `<button class="btn colbtn" type="button" data-col="${n}"><i class="dot" style="color:${PCOL[n]};width:16px;height:16px"></i>${t("colorN", { n })}</button>`).join("");
    $("#colorno").textContent = t("insCancel");
    const done = (v) => { d.onclose = null; if (d.open) d.close(); resolve(v); };
    $("#colorgrid").onclick = (e) => { const b = e.target.closest("[data-col]"); if (b) done(+b.dataset.col); };
    $("#colorno").onclick = () => done(0); d.onclose = () => resolve(0);
    if (d.showModal) d.showModal(); else d.setAttribute("open", "");
  });
}
async function modRead() {
  const m = S.mod; if (!m.id || !(m.dev >= 1)) return;
  if (m.busy || anyJob()) return;
  m.busy = true;
  try { m.data = await api("POST", "/api/v2/mod/monitor", { id: m.id, device_id: m.dev, stats: true }); }
  catch (e) { m.data = { ok: false, error: e.message }; }
  m.busy = false; if (page === "module") renderKeep();
}
/* re-render without losing a typed value or the scroll position */
function renderKeep() { const y = window.scrollY, num = $("#modnum") && $("#modnum").value; render(); if ($("#modnum") && num) $("#modnum").value = num; window.scrollTo(0, y); }
function modAutoSync() {
  clearInterval(modTimer); modTimer = null;
  if (S.mod.auto && page === "module") modTimer = setInterval(() => { if (!document.hidden && page === "module") modRead(); }, 2000);
}


/* ---------- long module jobs: installation check, scan, full module test, site report ----------
   All run on the server (app/v2/install_api.py), one at a time. The page starts one, then a single poller folds its events
   into the state of that kind (S.ins / S.scan / S.sweep / S.rpt) and repaints only that kind's box. Everything shown lives
   in S, so a full render() (the module auto-read does one) loses nothing. */
const INS_INFO = {
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
  sweep: ["ทดสอบโมดูลตัวเดียวแบบละเอียด: อ่านทุกรีจิสเตอร์ เขียนค่าทดสอบแล้วอ่านกลับ (คืนค่าเดิมเมื่อจบ) ตรวจพรีเซ็ต จอ และไฟ ส่วนปลดกลอนเลือกเพิ่มได้ ใช้กับงานซ่อมหรือ QA ไม่ใช่การตรวจหน้างานทั้งตู้",
    "A deep test of one module: reads every register, writes test values and reads them back (restoring the originals at the end), checks presets, display and lights; the latch is optional. For repair or QA, not for checking a whole cabinet on site."],
  setid: ["เปลี่ยน Slave ID ของโมดูลที่อ่านอยู่ แล้วบันทึกลงหน่วยความจำ โมดูลจะรีบูตและตอบที่ ID ใหม่ เครื่องมือจะไม่ยอมถ้า ID ใหม่มีโมดูลอื่นใช้อยู่ ใช้ได้ 1–245 หรือ 247",
    "Changes the slave id of the module being read and saves it; the module reboots and answers at the new id. Refused when another module already answers at the new id. 1-245 or 247."],
};
const infoBtn = (k) => `<button class="why" data-act="ins-info" data-k="${k}" type="button" aria-label="${t("explain")}">?</button>`;
const insInfoBtn = infoBtn;
const insSelText = () => `${S.ins.layout.label} · ${t("insSel", { n: S.ins.sel.size })}`;
function insReset() { Object.assign(S.ins, { res: {}, rows: [], lit: new Set(), closing: new Set(), testing: null, text: "", banner: "", summary: "", file: false, err: "" }); }
async function insLayout() {
  const i = S.ins; if (!S.mod.id) { i.layout = null; i.id = ""; return; }
  if (i.id === S.mod.id) return;                         /* loaded, loading or failed for this cabinet already */
  i.id = S.mod.id; i.layout = null; i.sel = new Set(); insReset(); S.scan.found = []; S.scan.text = "";
  try { i.layout = await api("GET", "/api/v2/ins/layout?id=" + encodeURIComponent(S.mod.id)); } catch (e) { i.layout = null; i.err = e.message; }
  if (page === "module") renderKeep();
}

/* ---- one poller for whichever job runs ---- */
const JOBST = { check: () => S.ins, scan: () => S.scan, sweep: () => S.sweep, report: () => S.rpt };
const anyJob = () => Object.values(JOBST).some((f) => f().running);
function jobFold(kind, ev) { ({ check: insFold, scan: scanFold, sweep: sweepFold, report: rptFold })[kind](ev); }
function jobPaint() { insPaint(); scanPaint(); sweepPaint(); rptPaint(); }
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
  const what = ["light"].concat(i.action === "light_display" ? ["display"] : [], i.unlock ? ["latch"] : []).join(" + ");
  el.innerHTML = (i.action !== "skip" ? `<div class="small muted">${t("insCoil", { coil: insCoil(), what })}</div>` : "")
    + (i.unlock && i.action !== "skip" ? `<div class="small" style="color:var(--bad)">${t("insWarnUnlock", { n: i.sel.size })}</div>` : "");
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
  const rows = i.rows.map((r) => `<tr><td>${r.id}</td><td>${esc(r.type || "—")}</td><td style="color:var(${r.ok ? "--ok" : "--bad"})">${resText(r)}</td><td>${esc(r.steps.map((s) => `${s.label}: ${s.ok ? "ok" : "FAIL"}${s.note && !s.ok ? ` (${s.note})` : ""}`).join("; "))}</td></tr>`).join("");
  return `<div class="row" style="gap:10px">${chip}<span class="small">${esc(i.text || t("insIdle"))}</span></div>${i.err ? `<div class="notice bad">${esc(i.err)}</div>` : ""}
    ${insGridHtml()}${i.summary ? `<div class="small">${esc(i.summary)}</div>` : ""}
    ${rows ? `<div style="overflow-x:auto"><table><tr><th>ID</th><th>${t("insType")}</th><th>${t("insResult")}</th><th>${t("insDetail")}</th></tr>${rows}</table></div>` : ""}`;
}
function insPaint() {
  const el = $("#insdyn"); if (el) el.innerHTML = insDyn();
  const busy = anyJob(), run = $("#insrun"), stop = $("#insstop"); if (run) run.disabled = busy; if (stop) stop.disabled = !S.ins.running;
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
  const pick = i.mode === "pick", unlock = pick ? i.punlock : (i.unlock && i.action !== "skip");
  if (unlock && !await ask(t("insUnlockQ", { n: i.sel.size }))) return;
  insReset(); i.banner = "run"; i.text = t("insStarting");
  await jobStart("check", "/api/v2/ins/start", { id: S.mod.id, mode: i.mode, ids: [...i.sel].sort((a, b) => a - b), action: i.action, unlock: pick ? i.punlock : i.unlock, identify: i.identify, hold_s: i.hold,
    preset: i.preset, display: i.display, require_locked: i.closed, timeout_s: i.timeout, batch: i.batch, by_channel: i.bych });
}
function insView() {
  const i = S.ins;
  if (!S.mod.id) return `<div class="notice info">${t("insPickCab")}</div>`;
  if (!i.layout) return i.err ? `<div class="notice bad">${esc(i.err)}</div>` : `<p class="muted">${t("reading")}</p>`;
  const num = (k, lo, hi, step) => `<input type="number" data-ins="${k}" min="${lo}" max="${hi}" step="${step || 1}" value="${i[k]}">`;
  const chk = (k, label, info) => `<div class="field"><label class="chk"><input type="checkbox" data-ins="${k}"${i[k] ? " checked" : ""}>${t(label)}${info ? infoBtn(info) : ""}</label></div>`;
  const modes = ["check", "pick"].map((m) => `<button class="btn${i.mode === m ? " primary" : ""}" data-act="ins-mode" data-m="${m}" aria-pressed="${i.mode === m}">${t(m === "check" ? "insModeCheck" : "insModePick")}</button>`).join("");
  const opts = i.mode === "check"
    ? `<div class="field"><label>${t("insWhat")}${infoBtn("action")}</label><select data-ins="action">${["skip", "light", "light_display"].map((a) => `<option value="${a}"${i.action === a ? " selected" : ""}>${t("insA_" + a)}</option>`).join("")}</select></div>
       <div class="field"><label>${t("insHold")}</label>${num("hold", 0.2, 5, 0.1)}</div>
       ${chk("identify", "insIdentify")}${chk("unlock", "insUnlock", "unlock")}<div id="inscap"></div>`
    : `<div class="field"><label>${t("insPreset")}</label><select data-ins="preset">${[1, 2, 3, 4, 5, 6, 7, 8].map((n) => `<option value="${n}"${i.preset === n ? " selected" : ""}>${t("colorN", { n })}</option>`).join("")}</select></div>
       <div class="field"><label>${t("insBatch")}${infoBtn("batch")}</label>${num("batch", 0, 16)}</div>
       <div class="field"><label>${t("insTimeout")}</label>${num("timeout", 0, 600)}</div>
       ${chk("display", "insPDisplay")}${chk("punlock", "insPUnlock")}${chk("closed", "insPClosed", "closed")}${chk("bych", "insPBych", "bych")}`;
  const fromScan = S.scan.found.length ? `<button class="btn" data-act="ins-fromscan">${t("insFromScan")}</button>` : "";
  return `<div class="row" style="gap:8px;align-items:center">${modes}${infoBtn("pick")}</div>
    <div class="row" style="gap:8px"><b>${t("insMods")}</b><span class="small muted" id="inssel">${insSelText()}</span></div>
    <div class="row" style="gap:8px"><button class="btn" data-act="ins-whole">${t("insWhole")}</button>${fromScan}<button class="btn" data-act="ins-none">${t("insClear")}</button></div>
    <div class="fgrid">${opts}</div>
    <div class="row" style="gap:8px"><button class="btn primary" id="insrun" data-act="ins-run"${anyJob() ? " disabled" : ""}>${t(i.mode === "check" ? "insRun" : "insPickRun")}</button><button class="btn" id="insstop" data-act="job-stop"${i.running ? "" : " disabled"}>${t("insCancel")}</button>
      ${fileLink(i, t("insCsv")).replace("<a ", '<a id="insfile" ')}</div>
    <div id="insdyn" class="stack">${insDyn()}</div>`;
}

/* ---- bus scan ---- */
function scanFold(ev) {
  const s = S.scan;
  if (ev.t === "probe") { s.text = t("scanProg", { i: ev.index, total: ev.total, id: ev.id }); if (ev.found) s.found.push({ id: ev.id, type: ev.type }); }
  else if (ev.t === "end") { s.found = ev.found; s.text = ev.cancelled ? t("insB_cancelled") : t("scanDone", { n: ev.found.length, total: ev.total }); }
}
function scanDyn() {
  const s = S.scan, have = new Set((S.ins.layout && S.ins.layout.ids) || []);
  const chips = s.found.map((f) => `<button class="cmcell${have.has(f.id) ? " ok" : " next"}" style="min-width:64px;padding:0 8px" data-act="scan-pick" data-id="${f.id}" title="${esc(f.type)}">${f.id}</button>`).join("");
  return `<span class="small">${esc(s.text || t("insIdle"))}</span>${s.err ? `<div class="notice bad">${esc(s.err)}</div>` : ""}${chips ? `<div class="row" style="gap:6px">${chips}</div>` : ""}`;
}
function scanPaint() {
  const el = $("#scandyn"); if (el) el.innerHTML = scanDyn();
  const busy = anyJob(); document.querySelectorAll("[data-act=scan-run]").forEach((b) => { b.disabled = busy; }); const st = $("#scanstop"); if (st) st.disabled = !S.scan.running;
}
function scanView() {
  if (!S.mod.id) return `<div class="notice info">${t("insPickCab")}</div>`;
  return `<div class="row" style="gap:8px;align-items:center"><button class="btn primary" data-act="scan-run" data-full="0"${anyJob() ? " disabled" : ""}>${t("scanQuick")}</button><button class="btn" data-act="scan-run" data-full="1"${anyJob() ? " disabled" : ""}>${t("scanFull")}</button>
    <button class="btn" id="scanstop" data-act="job-stop"${S.scan.running ? "" : " disabled"}>${t("insCancel")}</button>${infoBtn("scan")}</div><div id="scandyn" class="stack">${scanDyn()}</div>`;
}

/* ---- full module test (testsuite sweep) ---- */
function sweepFold(ev) {
  const w = S.sweep;
  if (ev.t === "phase") w.text = t("swPhase", { p: ev.name, i: ev.index, total: ev.total });
  else if (ev.t === "step" && ev.result !== "OK") w.bad.push(ev);
  else if (ev.t === "phaseend") w.phases.push(ev);
  else if (ev.t === "end") { w.banner = ev.cancelled ? "cancelled" : ev.passed ? "pass" : "issues"; w.text = t("swDone", { ok: ev.ok, fail: ev.fail, err: ev.err }); }
}
function sweepDyn() {
  const w = S.sweep, b = w.banner;
  const chip = b ? `<span class="chip ${b === "pass" ? "ok" : b === "issues" ? "bad" : "off"}">${t("insB_" + b)}</span>` : "";
  const ph = w.phases.length ? `<div style="overflow-x:auto"><table><tr><th>${t("swPhaseCol")}</th><th>OK</th><th>FAIL</th><th>ERR</th></tr>${w.phases.map((p) => `<tr><td>${esc(p.name)}</td><td>${p.ok}</td><td>${p.fail}</td><td>${p.err}</td></tr>`).join("")}</table></div>` : "";
  const bad = w.bad.length ? `<div class="small" style="color:var(--bad)">${w.bad.slice(0, 30).map((s) => esc(`${s.phase} ${s.name} (${s.addr}) ${s.op}: ${s.result} ${s.note || s.decoded}`)).join("<br>")}</div>` : "";
  return `<div class="row" style="gap:10px">${chip}<span class="small">${esc(w.text || t("insIdle"))}</span></div>${w.err ? `<div class="notice bad">${esc(w.err)}</div>` : ""}${ph}${bad}`;
}
function sweepPaint() {
  const el = $("#swdyn"); if (el) el.innerHTML = sweepDyn();
  const r = $("#swrun"), st = $("#swstop"), f = $("#swfile"); if (r) r.disabled = anyJob(); if (st) st.disabled = !S.sweep.running; if (f) f.hidden = !(S.sweep.file && !S.sweep.running);
}
function sweepView() {
  const w = S.sweep;
  return `<div class="fgrid"><div class="field"><label>${t("swLoops")}</label><input type="number" data-sw="loops" min="1" max="10" value="${w.loops}"></div>
      <div class="field"><label class="chk"><input type="checkbox" data-sw="lights"${w.lights ? " checked" : ""}>${t("swLights")}</label></div>
      <div class="field"><label class="chk"><input type="checkbox" data-sw="latch"${w.latch ? " checked" : ""}>${t("swLatch")}</label></div></div>
    <div class="row" style="gap:8px;align-items:center"><button class="btn primary" id="swrun" data-act="sw-run"${anyJob() ? " disabled" : ""}>${t("swRun", { id: S.mod.dev })}</button><button class="btn" id="swstop" data-act="job-stop"${w.running ? "" : " disabled"}>${t("insCancel")}</button>
      ${fileLink(w, t("insCsv")).replace("<a ", '<a id="swfile" ')}${infoBtn("sweep")}</div><div id="swdyn" class="stack">${sweepDyn()}</div>`;
}

/* ---- site report (gateway page): runs in its own popup, which carries the progress, Cancel and then the download ---- */
function rptFold(ev) {
  const r = S.rpt;
  if (ev.t === "start") { r.i = ev.index - 1; r.total = ev.total; r.text = t("rptProg", { i: ev.index, total: ev.total, id: ev.id }); }
  else if (ev.t === "end") { r.i = r.total = ev.total; r.text = ev.cancelled ? t("insB_cancelled") : t("rptDone", { a: ev.answered, n: ev.total }); }
}
function rptPaint() {
  const b = $("#rptrun"); if (b) b.disabled = (anyJob() && !S.rpt.running) || !S.gw.id;
  const d = $("#rptdlg"); if (!d || !d.open) return;
  const r = S.rpt;
  $("#rptbody").innerHTML = `<div>${esc(r.text || t("insStarting"))}</div>${r.total ? `<progress max="${r.total}" value="${r.i || 0}" style="width:100%"></progress>` : ""}${r.err ? `<div class="notice bad">${esc(r.err)}</div>` : ""}`;
  $("#rptcancel").hidden = !r.running; $("#rptdl").hidden = !(r.file && !r.running); $("#rptclose").hidden = r.running;
}
function rptOpen() {
  const d = $("#rptdlg"); $("#rpttitle").textContent = t("rptBtn"); $("#rptcancel").textContent = t("insCancel"); $("#rptdl").textContent = t("rptFile"); $("#rptclose").textContent = t("close");
  if (!d.open) { if (d.showModal) d.showModal(); else d.setAttribute("open", ""); }
  rptPaint();
}

/* ---- module danger: set slave id, software reset ---- */
async function modSetId() {
  const m = S.mod, el = $("#newid"), nid = +(el && el.value);
  if (!m.id || !(nid >= 1)) { toast(t("setIdNeed")); return; }
  const typed = await ask(t("setIdQ", { from: m.dev, to: nid }), false, true); if (typed === null) return;
  toast(t("setIdBusy"));
  const r = await api("POST", "/api/v2/mod/setid", { id: m.id, device_id: m.dev, new_id: nid, confirm: typed });
  if (!r.ok) throw new Error(r.error || "failed");
  m.dev = nid; m.data = null; toast(t("setIdDone", { id: nid })); await modRead();
}
async function modReset() {
  const m = S.mod; if (!m.id) return;
  const typed = await ask(t("resetQ", { id: m.dev }), false, true); if (typed === null) return;
  toast(t("resetBusy"));
  const r = await api("POST", "/api/v2/mod/reset", { id: m.id, device_id: m.dev, confirm: typed });
  if (!r.ok) throw new Error(r.error || "failed");
  toast(t("resetDone")); await modRead();
}
function dangerView() {
  return `<div class="row" style="align-items:flex-end;gap:8px"><div class="field" style="width:160px"><label>${t("setIdNew")}${infoBtn("setid")}</label><input id="newid" type="number" min="1" max="247"></div>
      <button class="btn" data-act="mod-setid" style="color:var(--bad)">${t("setIdBtn", { id: S.mod.dev })}</button></div>
    <div class="row"><button class="btn" data-act="mod-reset" style="color:var(--bad)">${t("resetBtn", { id: S.mod.dev })}</button></div>`;
}

/* ---- settings dialog: this PC as NTP server, web password ---- */
async function srvSettings() {
  const el = $("#setsrv"); if (!el) return;
  if (uiMode !== "advanced") { el.innerHTML = ""; return; }
  let n = null; try { n = await api("GET", "/api/v2/ntp"); } catch (e) { /* shown as off */ }
  const on = !!(n && n.enabled), pw = !!(S.me && S.me.auth);
  const ntpChip = !n ? "" : n.running ? `<span class="chip ok">${t("ntpChipOn", { port: n.port })}</span>` : on && n.error ? `<span class="chip bad">${t("ntpChipErr")}</span>` : `<span class="chip off">${t("optOff")}</span>`;
  const ntpNote = !n ? "" : n.running ? t("ntpServed", { n: n.served }) : on && n.error ? n.error : "";
  /* Two separate blocks, each a heading with its state as a chip on the right: the state is not a second label. */
  el.innerHTML = `<div class="setsec"><div class="row between"><b>${t("ntpTitle")}</b>${ntpChip}</div>
      <div class="row" style="gap:8px;align-items:center;flex-wrap:nowrap"><select id="ntpon" style="flex:1;min-width:0"><option value="0"${on ? "" : " selected"}>${t("optOff")}</option><option value="1"${on ? " selected" : ""}>${t("optOn")}</option></select>
        <input id="ntpport" type="number" min="1" max="65535" value="${n ? n.port : 123}" style="width:96px" aria-label="${t("ntpPort")}" title="${t("ntpPort")}"></div>
      ${ntpNote ? `<div class="small ${on && n.error && !n.running ? "" : "muted"}"${on && n.error && !n.running ? ' style="color:var(--bad)"' : ""}>${esc(ntpNote)}</div>` : ""}</div>
    <div class="setsec"><div class="row between"><b>${t("pwTitle")}</b><span class="chip ${pw ? "ok" : "warn"}">${t(pw ? "pwChipOn" : "pwChipOff")}</span></div>
      <input id="pw1" type="password" autocomplete="new-password" placeholder="${t("pwNew")}"><input id="pw2" type="password" autocomplete="new-password" placeholder="${t("pwRepeat")}">
      <div class="row" style="gap:8px"><button class="btn" data-act="pw-set" type="button">${t("pwSet")}</button>${pw ? `<button class="btn" data-act="pw-clear" type="button" style="color:var(--bad)">${t("pwClear")}</button>` : ""}</div></div>`;
}
async function ntpApply() {
  try { await api("POST", "/api/v2/ntp", { enabled: $("#ntpon").value === "1", port: +$("#ntpport").value }); } catch (e) { fail(e); }
  srvSettings();
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
const NAV = ["cabinets", "module", "gateway", "labels", "events", "soak", "firmware", "commission", "sites"];
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
  $("#stagechip").textContent = t("stage"); $("#infoclose").textContent = t("close");
  settingsText(); themeSelect(); modeSelect();
  document.documentElement.lang = lang;
  if (page === "events") loadEvents();
  if (page === "gateway") gwBar();
  if (page === "module") { modAutoSync(); insCaption(); insLayout(); jobResume(); }
  if (page === "gateway") jobResume();
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
    } else if (act.dataset.act === "gw-reboot") {
      const g = S.sites.find((x) => x.id === S.gw.id); if (!await ask(t("rebootQ", { n: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "reboot" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-defaults") {
      const g = S.sites.find((x) => x.id === S.gw.id); const typed = await ask(t("defaultsQ", { n: g ? g.name : "" }), false, true); if (typed === null) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "defaults", confirm: typed }); if (!r.ok) throw new Error(r.error); await gwRead(); toast(t("doneOk"));
    } else if (act.dataset.act === "mod-read") { await modRead();
    } else if (act.dataset.act === "mod-coil") {
      await modCoil(+act.dataset.addr, act.dataset.val === "1", !!act.dataset.latch && act.dataset.val === "1");
    } else if (act.dataset.act === "mod-color") {
      if (!S.mod.id) return;
      const kind = act.dataset.kind, latch = !!act.dataset.latch;
      if (latch && Date.now() < S.mod.lockUntil) { toast(t("cooldownNote")); return; }
      const n = await pickColor(act.textContent.trim()); if (!n) return;
      await modCoil({ enable: 1000, display: 1010, latch: 1020, latch_display: 1030 }[kind] + n, true, latch);
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
    } else if (act.dataset.act === "scan-run") { S.scan.found = []; S.scan.text = ""; await jobStart("scan", "/api/v2/ins/scan", { id: S.mod.id, full: act.dataset.full === "1" });
    } else if (act.dataset.act === "scan-pick") { S.mod.dev = +act.dataset.id; S.mod.data = null; renderKeep(); await modRead();
    } else if (act.dataset.act === "sw-run") {
      const w = S.sweep; if (!S.mod.id) return;
      if (w.latch && !await ask(t("swLatchQ", { id: S.mod.dev }))) return;
      Object.assign(w, { text: "", banner: "", phases: [], bad: [], file: false });
      await jobStart("sweep", "/api/v2/ins/sweep", { id: S.mod.id, device_id: S.mod.dev, loops: w.loops, lights: w.lights, latch: w.latch, fires: 1 });
    } else if (act.dataset.act === "rpt-run") {
      if (S.rpt.running) { rptOpen(); return; }             /* closed while it ran: just show it again */
      if (!S.gw.id) return; Object.assign(S.rpt, { id: S.gw.id, text: "", file: false, i: 0, total: 0, err: "" }); rptOpen();
      if (!await jobStart("report", "/api/v2/ins/report", { id: S.gw.id })) rptPaint();
    } else if (act.dataset.act === "mod-setid") { await modSetId();
    } else if (act.dataset.act === "mod-reset") { await modReset();
    } else if (act.dataset.act === "ntp-use") {
      const n = await api("GET", "/api/v2/ntp?toward=" + encodeURIComponent(S.gw.id)); if (!n.ip) { toast(t("ntpNoIp")); return; }
      const k = S.gw.data.keys.find((x) => x.key === "net.ntp"); if (k && n.ip !== k.value) S.gw.edits["net.ntp"] = n.ip; else delete S.gw.edits["net.ntp"];
      if (!n.running && await ask(t("ntpUseQ"))) await api("POST", "/api/v2/ntp", { enabled: true, port: n.port });
      renderKeep();
    } else if (act.dataset.act === "pw-set") {
      const a = $("#pw1").value, b = $("#pw2").value; if (a !== b) { toast(t("pwMismatch")); return; } if (a.length < 6) { toast(t("pwShort")); return; }
      await api("POST", "/api/v2/auth", { password: a }); location.href = "/login";
    } else if (act.dataset.act === "pw-clear") { if (!await ask(t("pwClearQ"))) return; await api("POST", "/api/v2/auth", { clear: true }); S.me.auth = false; srvSettings();
    } else if (act.dataset.act === "ins-info") { const x = INS_INFO[act.dataset.k]; $("#infobody").innerHTML = `<p style="margin:0;white-space:pre-line">${esc(x[lang === "th" ? 0 : 1])}</p>`; const d = $("#info"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
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
  if (ev.target.id === "evq") { S.ev.q = ev.target.value; clearTimeout(window._evt); window._evt = setTimeout(loadEvents, 300); }
});
document.addEventListener("change", async (ev) => {
  if (ev.target.id === "modsel") { S.mod.id = ev.target.value; S.mod.data = null; if (S.mod.id) modRead(); else render(); insLayout(); }
  if (ev.target.dataset && ev.target.dataset.sw) { const k = ev.target.dataset.sw, el = ev.target; S.sweep[k] = el.type === "checkbox" ? el.checked : Math.max(1, Math.min(10, +el.value || 1)); }
  if (ev.target.id === "ntpon" || ev.target.id === "ntpport") ntpApply();
  if (ev.target.dataset && ev.target.dataset.ins) { const k = ev.target.dataset.ins, el = ev.target; S.ins[k] = el.type === "checkbox" ? el.checked : el.type === "number" ? +el.value : (k === "preset" ? +el.value : el.value); insCaption(); }
  if (ev.target.id === "moddev") { S.mod.dev = Math.max(1, Math.min(247, +ev.target.value || 1)); S.mod.data = null; }
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
$("#modesel").onchange = (e) => { uiMode = e.target.value; try { localStorage.setItem("lgs.mode", uiMode); } catch (x) { /* not remembered */ } clearInterval(S.fw.timer); S.fw.timer = null; render(); srvSettings(); };
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
