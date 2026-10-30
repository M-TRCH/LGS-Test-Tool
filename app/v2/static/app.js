/* LGS Test Tool v2 front end, stage 1: Cabinets, Sites, Events. Plain JS, no libraries. */
"use strict";

const TXT = {
  th: {
    stage: "v2 ขั้นแรก", classic: "แบบเดิม", cabinets: "ตู้", sites: "รายการตู้", events: "เหตุการณ์",
    checkAll: "ตรวจทุกตู้", checking: "กำลังตรวจ...", checkedAt: "ตรวจล่าสุด {at}", notChecked: "ยังไม่ได้ตรวจ",
    noSites: "ยังไม่มีตู้ในรายการ เพิ่มได้ที่หน้า รายการตู้", ok: "ปกติ", warn: "ควรดู", bad: "ผิดปกติ",
    fw: "เฟิร์มแวร์", uptime: "เปิดมาแล้ว", clients: "client", clock: "นาฬิกา", rtu: "ซ่อม RS485 (สะสม)",
    clockUnset: "ยังไม่ตั้ง", repaired: "ซ่อมได้ {n}", failed: "ซ่อมไม่ได้ {n}", badcrc: "CRC เสีย {n}",
    probeNote: "การตรวจแต่ละครั้งเปิดการเชื่อมต่อสั้นๆ หนึ่งครั้งต่อตู้ และถูกบันทึกในเหตุการณ์ของเกตเวย์ จึงไม่ตรวจอัตโนมัติ",
    add: "เพิ่มตู้", save: "บันทึก", saved: "บันทึกแล้ว", del: "ลบ", name: "ชื่อตู้", host: "ไอพี / โฮสต์", port: "พอร์ต",
    cabinet: "ชนิดตู้", site: "ไซต์", note: "หมายเหตุ", exportCsv: "ส่งออก CSV", importCsv: "นำเข้า CSV",
    importMerge: "เพิ่มเฉพาะที่ยังไม่มี", importReplace: "แทนที่ทั้งรายการ", imported: "นำเข้า {n} แถว",
    dupWarn: "ไอพีซ้ำกับแถวอื่น", unsaved: "มีการแก้ที่ยังไม่บันทึก", sitesHint: "รายการนี้เก็บบนเซิร์ฟเวอร์ ทุกเครื่องเห็นเหมือนกัน ไม่ต้องกรอกไอพีซ้ำ",
    gateway: "เกตเวย์", days: "ย้อนหลัง", day1: "วันนี้", day7: "7 วัน", day30: "30 วัน", day90: "90 วัน", all: "ทั้งหมด",
    search: "ค้นหา (ชื่อ, ไอพี)", noEvents: "ไม่มีเหตุการณ์ในช่วงนี้", collect: "เก็บเหตุการณ์อัตโนมัติ",
    collectHint: "ดึงบันทึกจากเกตเวย์ทุกตู้ในรายการตู้ทุก 5 นาที เก็บ 90 วัน ต้องใช้เฟิร์มแวร์เกตเวย์ 1.14.0 ขึ้นไป",
    gateway_page: "เกตเวย์", pick: "เลือกตู้", read: "อ่านค่า", reading: "กำลังอ่าน...", notRead: "เลือกตู้แล้วกดอ่านค่า",
    setClock: "ตั้งนาฬิกาจากเครื่องนี้", clockWarn: "การตั้งนาฬิกาเป็นการเปิดใช้การรีเซ็ตตามเวลา (เช่น 03:00) ซึ่งตัดไฟชั้นวาง ตั้งเมื่อตั้งใจเท่านั้น",
    clockSet: "ตั้งนาฬิกาแล้ว", resync: "ซ่อมจังหวะหลังไม่มีคำตอบ (RESYNC)", exc: "ตอบ exception 0x0B ทันทีเมื่อบัสไม่ตอบ (EXC)",
    volatileNote: "ชั่วคราว: กลับค่าเดิมเมื่อเกตเวย์รีบูต", reboot: "รีบูตเกตเวย์", rebootQ: "รีบูตเกตเวย์ {n}? จะตัดการสื่อสารสักครู่",
    defaults: "คืนค่าโรงงาน", defaultsQ: "คืนค่าโรงงานของ {n}? Ethernet จะปิดและ hub map หาย ต้องตั้งใหม่ พิมพ์ชื่อตู้เพื่อยืนยัน",
    discard: "ทิ้งค่าที่ค้างอยู่", danger: "ส่วนอันตราย", changes: "{n} ค่าที่แก้", apply: "บันทึกลงเกตเวย์", applyQ: "บันทึก {n} ค่าลง {g}?",
    applied: "บันทึกแล้ว", needReboot: "ต้องรีบูตจึงมีผล: {k}", reset: "ล้างที่แก้", ro: "อ่านอย่างเดียว", rebootKey: "ต้องรีบูต",
    doneOk: "สำเร็จ", sessionHint: "เขียนค่าทุกครั้งผ่านเซสชัน HELLO และบันทึกแบบครบหรือไม่เลย", noPassword: "ยังไม่ตั้งรหัสผ่านหน้าเว็บ ทุกคนในเครือข่ายแก้ค่าเกตเวย์ได้",
    module_page: "โมดูล", devId: "รหัสโมดูล (ID)", withStats: "รวมสถิติ", auto: "อ่านอัตโนมัติทุก 2 วินาที", modNotRead: "เลือกตู้ ใส่ ID โมดูล แล้วกดอ่านค่า",
    cDevice: "อุปกรณ์", cRuntime: "การทำงาน", cHealth: "สุขภาพระบบ", cReset: "สาเหตุรีเซ็ตล่าสุด", cTemp: "อุณหภูมิ", cLatch: "กลอน / จอ", cStats: "สถิติ",
    mType: "ชนิด", mFw: "เฟิร์มแวร์", mHw: "ฮาร์ดแวร์", mBaud: "Baud", mUid: "หมายเลขชิป", mUptime: "เปิดมาแล้ว", mBoots: "จำนวนครั้งที่บูต", mMode: "โหมด",
    mPreset: "พรีเซ็ตที่ใช้อยู่", mButton: "กดยืนยันแล้ว", mRoom: "ในห้อง", mBoard: "บนบอร์ด", mCurrent: "กระแสขาเข้า", mLatch: "กลอน", mLocked: "ล็อก", mUnlocked: "ปลดแล้ว",
    mUnlockedAgo: "ปลดล่าสุด {s} วินาทีก่อน", mDisplay: "ตัวเลขบนจอ", na: "ไม่มี", presets: "พรีเซ็ตสี", pLight: "ไฟ", pLightDisp: "ไฟ + เลข", pUnlock: "ปลดกลอน", pUnlockDisp: "ปลดกลอน + เลข",
    quick: "คำสั่งด่วน", identify: "ระบุตำแหน่ง (กะพริบ)", allOff: "ดับทั้งหมด", latchSafety: "ปลดกลอน (ปลอดภัย)", latchForce: "ปลดกลอน (บังคับ)", dispPower: "เปิดจอ",
    number: "ตัวเลข (0-9999)", writeNumber: "เขียนตัวเลข", cooldownNote: "กลอนต้องเว้น 2.2 วินาทีระหว่างการปลด", sent: "ส่งแล้ว", fires: "ยิงกลอน {c} ครั้ง · {s} วินาที", count: "ครั้ง", seconds: "วินาที",
    soak_page: "Soak", sPick: "เลือกตู้ที่จะทดสอบ", sAll: "ทั้งหมด", sMode: "โหมด", sPoll: "อ่านอย่างเดียว", sPharm: "จำลองจ่ายยา",
    sPicks: "จำนวน pick ต่อวัน", sHours: "ชั่วโมง (0 = จนกว่าจะหยุด)", sStartAt: "เริ่มเวลา (เช่น 21:00 เว้นว่าง = ทันที)", sStart: "เริ่ม Soak",
    sStop: "หยุด", sStopQ: "หยุด soak ที่กำลังรัน? ข้อมูลถึงตอนนี้ถูกเก็บไว้", sRunning: "กำลังรัน", sArmed: "ตั้งเวลาไว้ เริ่มในอีก {t}", sLeft: "เหลือ {t}",
    sNoEnd: "ไม่มีเวลาจบ", sCab: "ตู้", sState: "สถานะ", sPass: "รอบ", sReads: "อ่าน", sFails: "พลาด", sRbt: "รีบูต", sWdt: "WDT", sWorst: "ช้าสุด ms", sHeal: "เกตเวย์ซ่อม",
    sClean: "สะอาด", sWarn: "ควรดู", sNotClean: "ไม่สะอาด", sDidNot: "ไม่ได้รัน", sStarting: "กำลังเริ่ม", sAnoms: "เหตุผิดปกติล่าสุด", sNone: "ไม่มี",
    sVerdict: "สรุปผลรอบล่าสุด", sHistory: "รอบที่ผ่านมา", sView: "ดูสรุป", sNoRuns: "ยังไม่มีรอบที่ผ่านมา", sFrames: "เฟรมที่ pymodbus ทิ้ง: {n}",
    sNeedType: "ตู้ที่ไม่ได้กำหนดชนิดจะเริ่มไม่ได้ ตั้งที่หน้า รายการตู้", sStarted: "เริ่มแล้ว {n} ตู้", sCsv: "ไฟล์ CSV", sLongNote: "รันบนเซิร์ฟเวอร์ ปิดหน้านี้ได้ ผลเก็บใน data/exports",
    labels_page: "ป้าย", firmware_page: "เฟิร์มแวร์", lbWard: "ชื่อวอร์ด (พิมพ์บนป้าย)", lbSerial: "ซีเรียลจากคลัง (ไม่เก็บ)", lbLayout: "แบบป้าย", lbPlate: "กรอบ",
    lbPreview: "ดูตัวอย่างข้อมูล", lbDownload: "ดาวน์โหลด .lbx", lbInfo: "{name} · {ip} · {mac} · {rows} แถว", lbReady: "ยาว {mm} มม. · QR {qr} ไบต์ ({ecc}, กู้ได้ {rec}%, เหลือ {spare} ไบต์) · ไฟล์ {size} ไบต์",
    lbNote: "อ่านชื่อ ไอพี MAC และแผนผังแถวจากเกตเวย์ตอนกด ป้ายจึงไม่ใช่ของเก่า ซีเรียลเป็นของฐานข้อมูลคลัง ไม่เก็บในโปรแกรม",
    expCfg: "ส่งออก config (JSON)", impCfg: "นำเข้า config (JSON)", impDone: "นำเข้า {n} ค่า (ยังไม่บันทึก ตรวจแล้วกดบันทึกลงเกตเวย์)", impNone: "ไม่มีค่าที่ต่างจากเกตเวย์",
    shapeBad: "ชนิดตู้ใน รายการตู้ ({l}) ไม่ตรงกับเกตเวย์: {w}", shapeFix: "ตั้งค่าที่ตรงให้ (ยังไม่บันทึก)", shapeNoFix: "เกตเวย์รุ่นนี้แก้เองไม่ได้ (ไม่มี panel.shape)",
    fwOta: "อัปเดตโมดูลผ่าน OTA (หลายตู้)", fwImage: "อิมเมจ", fwStart: "เริ่มอัปเดต", fwCancel: "ยกเลิก", fwCancelQ: "ยกเลิกการอัปเดต? โมดูลที่ค้างอยู่ในเซสชันอาจต้องอัปเดตซ้ำ",
    fwStartQ: "อัปเดตเฟิร์มแวร์โมดูลทุกตัวใน {n} ตู้ด้วย {i}? ทำย้อนจากหน้านี้ไม่ได้ ตู้ที่ใช้งานอยู่จะใช้ไม่ได้ระหว่างอัปเดต", fwRun: "กำลังอัปเดต", fwNoOta: "ยังไม่มีอิมเมจ OTA ในโปรแกรมนี้",
    fwGw: "อัปเดตเกตเวย์ผ่านเครือข่าย (ทีละตู้)", fwGwNote: "เกตเวย์รีบูตตอนจบ และตัดไฟชั้นวางชั่วครู่ (โมดูลทุกตัวรีบูตด้วย) พิมพ์ชื่อตู้เพื่อยืนยัน", fwUpload: "หรือเลือกไฟล์ .bin เอง", fwConfirm: "พิมพ์ชื่อตู้เพื่อยืนยัน",
    fwGwStart: "อัปเดตเกตเวย์", fwGwRun: "กำลังอัปเดตเกตเวย์", fwDone: "เสร็จ", fwFail: "ไม่สำเร็จ", fwLog: "บันทึกการทำงาน", fwNone: "—", fwCensus: "ผลตรวจ", fwLeft: "ยังไม่ใช่รุ่นใหม่", fwPhase: "ขั้น",
    matched: "พบ {n} รายการ", loginAgain: "ต้องเข้าสู่ระบบอีกครั้ง", error: "ผิดพลาด: {e}", d: "วัน", h: "ชม.",
  },
  en: {
    stage: "v2 stage 1", classic: "Classic UI", cabinets: "Cabinets", sites: "Sites", events: "Events",
    checkAll: "Check all", checking: "Checking...", checkedAt: "Last checked {at}", notChecked: "Not checked yet",
    noSites: "No cabinets saved yet. Add them on the Sites page.", ok: "OK", warn: "Look", bad: "Fault",
    fw: "Firmware", uptime: "Up for", clients: "Clients", clock: "Clock", rtu: "RS485 repairs (total)",
    clockUnset: "not set", repaired: "{n} repaired", failed: "{n} failed", badcrc: "{n} bad CRC",
    probeNote: "Each check opens one short connection per gateway and shows up in that gateway's event log, so it is never automatic.",
    add: "Add cabinet", save: "Save", saved: "Saved", del: "Delete", name: "Name", host: "IP / host", port: "Port",
    cabinet: "Cabinet type", site: "Site", note: "Note", exportCsv: "Export CSV", importCsv: "Import CSV",
    importMerge: "Add only new rows", importReplace: "Replace the list", imported: "Imported {n} rows",
    dupWarn: "same address as another row", unsaved: "Unsaved changes", sitesHint: "Stored on the server, the same on every device: no retyping IPs.",
    gateway: "Gateway", days: "Range", day1: "Today", day7: "7 days", day30: "30 days", day90: "90 days", all: "All",
    search: "Search (name, IP)", noEvents: "No events in this range", collect: "Collect events automatically",
    collectHint: "Pulls every saved cabinet's gateway log every 5 minutes, kept 90 days. Needs gateway firmware 1.14.0 or newer.",
    gateway_page: "Gateway", pick: "Choose cabinet", read: "Read", reading: "Reading...", notRead: "Choose a cabinet and press Read",
    setClock: "Set clock from this PC", clockWarn: "Setting the clock also arms the scheduled reset (e.g. 03:00), which cuts the shelf's power. Do it on purpose only.",
    clockSet: "Clock set", resync: "Re-sync after a missing reply (RESYNC)", exc: "Answer a bus timeout with exception 0x0B at once (EXC)",
    volatileNote: "Temporary: reverts when the gateway reboots", reboot: "Reboot gateway", rebootQ: "Reboot gateway {n}? It will be unreachable for a moment.",
    defaults: "Factory defaults", defaultsQ: "Reset {n} to factory defaults? Ethernet goes off and the hub map is lost; both must be set again. Type the cabinet's name to confirm.",
    discard: "Discard staged edits", danger: "Danger zone", changes: "{n} changed", apply: "Save to gateway", applyQ: "Save {n} value(s) to {g}?",
    applied: "Saved", needReboot: "Needs a reboot to take effect: {k}", reset: "Clear edits", ro: "read-only", rebootKey: "needs reboot",
    doneOk: "Done", sessionHint: "Every write goes through a HELLO session and is saved all or nothing.", noPassword: "No web password set: anyone on the network can edit the gateway.",
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
    lbPreview: "Preview data", lbDownload: "Download .lbx", lbInfo: "{name} · {ip} · {mac} · {rows} rows", lbReady: "{mm} mm long · QR {qr} bytes ({ecc}, recovers {rec}%, {spare} bytes spare) · file {size} bytes",
    lbNote: "Name, IP, MAC and the row map are read from the gateway when you press the button, so a sticker is never stale. The serial belongs to the warehouse database and is not kept here.",
    expCfg: "Export config (JSON)", impCfg: "Import config (JSON)", impDone: "Imported {n} values (not saved yet: review, then Save to gateway)", impNone: "Nothing differs from the gateway",
    shapeBad: "The cabinet type on the Sites page ({l}) does not match the gateway: {w}", shapeFix: "Stage the matching values (not saved yet)", shapeNoFix: "This firmware cannot be told (no panel.shape)",
    fwOta: "Module update over OTA (several cabinets)", fwImage: "Image", fwStart: "Start update", fwCancel: "Cancel", fwCancelQ: "Cancel the update? Modules left in a session may need updating again.",
    fwStartQ: "Update the firmware of every module in {n} cabinets with {i}? This cannot be undone from this page, and cabinets in use are unusable during the update.", fwRun: "Updating", fwNoOta: "No OTA image is bundled in this build",
    fwGw: "Gateway update over the network (one at a time)", fwGwNote: "The gateway reboots at the end and cuts the shelf's power for a moment (every module reboots too). Type the cabinet's name to confirm.", fwUpload: "or choose a .bin file", fwConfirm: "Type the cabinet's name to confirm",
    fwGwStart: "Update gateway", fwGwRun: "Updating gateway", fwDone: "Done", fwFail: "Failed", fwLog: "Log", fwNone: "—", fwCensus: "Result", fwLeft: "not on the new image", fwPhase: "Phase",
    matched: "{n} found", loginAgain: "Sign in again", error: "Error: {e}", d: "d", h: "h",
  },
};
let lang = (localStorage.getItem("lgs.lang") || "th");
const t = (k, p) => { let s = (TXT[lang] && TXT[lang][k]) || TXT.en[k] || k; for (const a in (p || {})) s = s.replace("{" + a + "}", p[a]); return s; };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: "", days: 1, q: "", types: new Set() }, gw: { id: "", data: null, edits: {}, busy: false }, lab: { id: "", ward: "", serial: "", layout: "", plate: "", opts: null, info: null, busy: false }, fw: { images: null, sel: new Set(), image: "", ota: null, gwId: "", gwImage: "", gwConfirm: "", gwFile: null, gwFileName: "", gw: null, timer: null }, soak: { sel: new Set(), mode: "pharmacy", picks: 2000, hours: 12, startAt: "", status: null, runs: [], verdict: "", timer: null, was: false }, mod: { id: "", dev: 11, data: null, busy: false, auto: false, stats: false, presets: [], lockUntil: 0 } };
let page = (location.hash || "#/cabinets").slice(2) || "cabinets";

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
    const why = h && h.reasons && h.reasons.length ? `<div class="notice ${state === "bad" ? "bad" : ""}">${h.reasons.map(esc).join("<br>")}</div>` : "";
    return `<section class="card cab"><h3><span>${esc(s.name)}</span><span class="chip ${state === "off" ? "off" : state}"><i class="dot"></i>${esc(chip)}</span></h3>
      <div class="small muted mono">${esc(s.host)}:${s.port}${s.cabinet ? " · " + esc(s.cabinet) : ""}${s.site ? " · " + esc(s.site) : ""}</div>${body}${why}</section>`;
  }).join("");
  return `<div class="row between"><h1>${t("cabinets")}</h1><div class="row"><span class="small muted">${S.checkedAt ? t("checkedAt", { at: esc(S.checkedAt) }) : ""}</span>
    <button class="btn primary" data-act="check">${t("checkAll")}</button></div></div>
    <p class="small muted">${t("probeNote")}</p>
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
  return `<div class="row between"><h1>${t("sites")}</h1><div class="row">
      <button class="btn" data-act="add">${t("add")}</button><button class="btn primary" data-act="save">${t("save")}</button></div></div>
    <p class="small muted">${t("sitesHint")}</p>
    ${S.dirty ? `<div class="notice">${t("unsaved")}</div>` : ""}
    ${S.warnings.map((w) => `<div class="notice">${esc(w)}</div>`).join("")}
    <section class="card" id="sitelist">${S.sites.map(siteRow).join("") || `<p class="muted">${t("noSites")}</p>`}</section>
    <section class="card stack"><div class="row"><a class="btn" href="/api/v2/sites.csv" download>${t("exportCsv")}</a>
      <label class="btn">${t("importCsv")}<input type="file" id="csvfile" accept=".csv,text/csv" hidden></label>
      <select id="csvmode" aria-label="import mode"><option value="merge">${t("importMerge")}</option><option value="replace">${t("importReplace")}</option></select></div></section>`;
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


const GWGROUPS = ["sys", "rs485", "usb", "net", "time", "bus", "panel", "sched"];
function gwChanged() { return Object.keys(S.gw.edits).length; }
function gwLabel(k) { const tx = k.text && k.text[lang]; return (tx && tx.label) || k.key; }
function viewGateway() {
  const g = S.gw, d = g.data;
  const opts = S.sites.map((x) => `<option value="${esc(x.id)}"${x.id === g.id ? " selected" : ""}>${esc(x.name)} · ${esc(x.host)}</option>`).join("");
  let body = `<div class="notice info">${t("notRead")}</div>`;
  if (d && d.ok) {
    const i = d.info;
    const groups = {};
    d.keys.forEach((k) => { const p = k.key.split(".")[0]; (groups[p] = groups[p] || []).push(k); });
    const order = [...GWGROUPS.filter((x) => groups[x]), ...Object.keys(groups).filter((x) => !GWGROUPS.includes(x))];
    const sw = (name, on) => `<div class="switch"><div><b>${t(name)}</b><div class="small muted">${t("volatileNote")}</div></div><button class="sw" role="switch" aria-checked="${on}" data-act="gw-vol" data-name="${name}"></button></div>`;
    const field = (k) => {
      const ed = k.key in g.edits, val = ed ? g.edits[k.key] : k.value;
      const hint = k.text && k.text[lang] && k.text[lang].hint;
      return `<div class="field"><label>${esc(gwLabel(k))} <span class="tiny muted mono">${esc(k.key)}</span>${k.reboot ? ` <span class="chip warn">${t("rebootKey")}</span>` : ""}${k.ro ? ` <span class="chip off">${t("ro")}</span>` : ""}</label>
        <input data-key="${esc(k.key)}" value="${esc(val)}" ${k.ro ? "disabled" : ""} ${ed ? 'style="border-color:var(--brand)"' : ""}>${hint ? `<span class="hint">${esc(hint)}</span>` : ""}</div>`;
    };
    const sh = d.shape && d.shape.layout && !d.shape.agreed ? `<div class="notice">${t("shapeBad", { l: esc(d.shape.label), w: esc(d.shape.why) })}<div class="row" style="margin-top:8px">${d.shape.fixable ? `<button class="btn" data-act="gw-shape">${t("shapeFix")}</button>` : `<span class="small">${t("shapeNoFix")}</span>`}</div></div>` : "";
    body = sh + `<section class="card"><dl class="kv"><dt>${t("fw")}</dt><dd class="mono">${esc(i.fw)}</dd><dt>${t("uptime")}</dt><dd>${fmtUp(+i["sys.up"] || 0)} (${esc(i["sys.reset"] || "")})</dd>
        <dt>${t("clients")}</dt><dd>${esc(i["net.client"] || "?")}/2</dd><dt>${t("clock")}</dt><dd>${i["time.set"] === "1" ? esc((i["time.now"] || "").replace("T", " ")) : t("clockUnset")}</dd></dl></section>
      <section class="card stack"><div class="row"><button class="btn" data-act="gw-time">${t("setClock")}</button></div><p class="small muted">${t("clockWarn")}</p>
        ${sw("resync", i["rtu.heal"] === "1")}${sw("exc", i["tcp.exc"] === "1")}</section>
      <section class="card stack">${order.map((grp) => `<details${grp === "rs485" || grp === "net" ? " open" : ""}><summary><b>${esc(grp)}</b> <span class="small muted">${groups[grp].length}</span></summary><div class="fgrid" style="margin-top:8px">${groups[grp].map(field).join("")}</div></details>`).join("")}</section>
      <section class="card stack"><div class="row"><button class="btn" data-act="gw-export">${t("expCfg")}</button><label class="btn">${t("impCfg")}<input type="file" id="gwimport" accept=".json,application/json" hidden></label></div></section>
      <section class="card stack"><h3>${t("danger")}</h3><div class="row"><button class="btn" data-act="gw-discard">${t("discard")}</button><button class="btn" data-act="gw-reboot">${t("reboot")}</button><button class="btn" data-act="gw-defaults" style="color:var(--bad)">${t("defaults")}</button></div></section>`;
  } else if (d && !d.ok) body = `<div class="notice bad">${esc(d.error)}</div>`;
  return `<div class="row between"><h1>${t("gateway_page")}</h1></div>
    ${S.me && !S.me.auth ? `<div class="notice">${t("noPassword")}</div>` : ""}
    <section class="card stack"><div class="row"><div class="field" style="min-width:220px;flex:1"><label>${t("pick")}</label><select id="gwsel"><option value="">—</option>${opts}</select></div>
      <button class="btn primary" data-act="gw-read">${g.busy ? t("reading") : t("read")}</button></div><p class="small muted">${t("sessionHint")}</p></section>
    <div class="stack" style="margin-top:12px">${body}</div><div id="gwbar"></div>`;
}
function gwBar() {
  const n = gwChanged(), el = $("#gwbar"); if (!el) return;
  if (!n) { el.innerHTML = ""; return; }
  const diffs = Object.entries(S.gw.edits).map(([k, v]) => { const was = S.gw.data.keys.find((x) => x.key === k).value; return `<div class="small mono">${esc(k)}: ${esc(was)} → <b>${esc(v)}</b></div>`; }).join("");
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
  const fin = st.finished && !running ? `<section class="card stack"><h3>${t("sVerdict")}</h3><pre class="mono small" style="white-space:pre-wrap;overflow-x:auto;margin:0">${esc(st.finished.text)}</pre></section>` : "";
  const hist = `<section class="card stack"><h3>${t("sHistory")}</h3>${(k.runs || []).length ? k.runs.map((r) => `<div class="stack tight" style="padding:8px 0;border-bottom:1px solid var(--line)"><div class="row between"><b>${esc(r.started)}</b>
      ${r.verdict ? `<button class="btn" data-act="soak-view" data-name="${esc(r.verdict)}">${t("sView")}</button>` : ""}</div>
      <div class="small">${r.csv.map((c) => `<a href="/api/v2/soak/file?name=${encodeURIComponent(c)}&download=1">${esc(c.replace(/^soak-/, "").replace(/-\d{8}-\d{6}\.csv$/, ""))}</a>`).join(" · ")}</div></div>`).join("") : `<p class="muted">${t("sNoRuns")}</p>`}
      ${k.verdict ? `<pre class="mono small" style="white-space:pre-wrap;overflow-x:auto;margin:0">${esc(k.verdict)}</pre>` : ""}</section>`;
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
  const info = l.info ? `<div class="notice info">${t("lbInfo", { name: esc(l.info.name), ip: esc(l.info.ip), mac: esc(l.info.mac), rows: l.info.rows })}<br>${t("lbReady", { mm: l.info.mm, qr: l.info.qr_bytes, ecc: l.info.ecc, rec: l.info.recover_pct, spare: l.info.spare_bytes, size: l.info.size })}
      <details style="margin-top:6px"><summary class="small">QR</summary><pre class="mono tiny" style="white-space:pre-wrap;margin:0">${esc(l.info.payload)}</pre></details></div>` : "";
  return `<h1>${t("labels_page")}</h1><p class="small muted">${t("lbNote")}</p>
    <section class="card stack"><div class="fgrid">
      <div class="field"><label>${t("pick")}</label><select id="lbsel"><option value="">—</option>${opts}</select></div>
      <div class="field"><label>${t("lbWard")}</label><input id="lbward" value="${esc(l.ward)}"></div>
      <div class="field"><label>${t("lbSerial")}</label><input id="lbserial" value="${esc(l.serial)}"></div>
      <div class="field"><label>${t("lbLayout")}</label><select id="lblayout">${o ? o.layouts.map((x) => `<option value="${esc(x.key)}"${x.key === l.layout ? " selected" : ""}>${esc(x.title)}</option>`).join("") : ""}</select></div>
      <div class="field"><label>${t("lbPlate")}</label><select id="lbplate">${o ? o.plates.map((x) => `<option value="${esc(x.key)}"${x.key === l.plate ? " selected" : ""}>${esc(x.text[lang] || x.key)}</option>`).join("") : ""}</select></div></div>
      <div class="row"><button class="btn" data-act="lb-preview">${l.busy ? t("reading") : t("lbPreview")}</button><button class="btn primary" data-act="lb-file">${t("lbDownload")}</button></div>${info}</section>`;
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
      <div class="field"><label>${t("fwUpload")}</label><input type="file" id="fwgwfile" accept=".bin"><span class="hint">${esc(f.gwFileName || "")}</span></div>
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

const VIEWS = { cabinets: viewCabinets, gateway: viewGateway, module: viewModule, soak: viewSoak, firmware: viewFirmware, labels: viewLabels, sites: viewSites, events: viewEvents };
const NAV = ["cabinets", "gateway", "module", "soak", "firmware", "labels", "sites", "events"];

function render() {
  $("#nav").innerHTML = NAV.map((k) => `<button data-nav="${k}" ${k === page ? 'aria-current="page"' : ""}>${t(k === "gateway" ? "gateway_page" : k === "module" ? "module_page" : k === "soak" ? "soak_page" : k === "firmware" ? "firmware_page" : k === "labels" ? "labels_page" : k)}</button>`).join("")
    + `<button data-nav="classic">${t("classic")}</button>`;
  $("#main").innerHTML = (VIEWS[page] || viewCabinets)();
  const cur = $("#nav [aria-current]"); if (cur && cur.scrollIntoView) cur.scrollIntoView({ inline: "center", block: "nearest" });
  $("#stagechip").textContent = t("stage");
  $("#langbtn").textContent = lang.toUpperCase();
  document.documentElement.lang = lang;
  if (page === "events") loadEvents();
  if (page === "gateway") gwBar();
  if (page === "module") modAutoSync();
  if (page === "soak" && !S.soak.timer) soakSync();
  if (page === "firmware" && !S.fw.timer) fwSync();
}

async function loadEvents() {
  try {
    const q = new URLSearchParams({ gw: S.ev.gw, days: S.ev.days, q: S.ev.q, ev: [...S.ev.types].join(",") });
    const r = await api("GET", "/api/v2/events?" + q);
    $("#evcount").textContent = t("matched", { n: r.matched });
    $("#evlist").innerHTML = r.rows.length ? r.rows.map((e) => `<div class="evrow"><span class="when">${esc((e.t || e.collected || "").replace("T", " ").slice(5, 19))}</span><span><b>${esc(e.gw)}</b> ${esc(e.text)}</span></div>`).join("") : `<p class="muted">${t("noEvents")}</p>`;
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
  if (nav) { if (nav.dataset.nav === "classic") { location.href = "/"; return; } page = nav.dataset.nav; location.hash = "#/" + page; if (page !== "soak") { clearInterval(S.soak.timer); S.soak.timer = null; } if (page !== "firmware") { clearInterval(S.fw.timer); S.fw.timer = null; } if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways").catch(() => ({}))).gateways || []; render(); return; }
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
      if (!confirm(t("applyQ", { n, g: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/apply", { id: S.gw.id, changes: S.gw.edits });
      if (!r.ok) throw new Error(r.error || "failed");
      S.gw.edits = {}; await gwRead(); toast(r.pending_reboot ? t("needReboot", { k: r.pending_reboot }) : t("applied"));
    } else if (act.dataset.act === "gw-time") {
      if (!confirm(t("clockWarn"))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "time" }); if (!r.ok) throw new Error(r.error); await gwRead(); toast(t("clockSet"));
    } else if (act.dataset.act === "gw-vol") {
      const on = act.getAttribute("aria-checked") !== "true";
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: act.dataset.name, value: on ? "1" : "0" }); if (!r.ok) throw new Error(r.error); await gwRead();
    } else if (act.dataset.act === "gw-discard") {
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "discard" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-reboot") {
      const g = S.sites.find((x) => x.id === S.gw.id); if (!confirm(t("rebootQ", { n: g ? g.name : "" }))) return;
      const r = await api("POST", "/api/v2/gw/action", { id: S.gw.id, action: "reboot" }); if (!r.ok) throw new Error(r.error); toast(t("doneOk"));
    } else if (act.dataset.act === "gw-defaults") {
      const g = S.sites.find((x) => x.id === S.gw.id); const typed = prompt(t("defaultsQ", { n: g ? g.name : "" })); if (typed === null) return;
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
      if (!confirm(t("sStopQ"))) return; await api("POST", "/api/v2/soak/stop", {}); S.soak.was = true; await soakRefresh();
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
      if (!confirm(t("fwStartQ", { n: cabs.length, i: im.label }) + "\n\n" + cabs.map((c) => c.name).join(", "))) return;
      await api("POST", "/api/v2/fw/ota/start", { ids: [...f.sel], image: f.image }); await fwRefresh();
    } else if (act.dataset.act === "fw-cancel") {
      if (!confirm(t("fwCancelQ"))) return; await api("POST", "/api/v2/fw/ota/cancel", {}); await fwRefresh();
    } else if (act.dataset.act === "fw-gwstart") {
      const f = S.fw; if (!f.gwId) return;
      const site = S.sites.find((x) => x.id === f.gwId);
      if (f.gwFile) { await api("POST", `/api/v2/fw/gateway/start?id=${encodeURIComponent(f.gwId)}&confirm=${encodeURIComponent(f.gwConfirm)}&name=${encodeURIComponent(f.gwFileName)}`, f.gwFile, true); }
      else { await api("POST", "/api/v2/fw/gateway/start", { id: f.gwId, confirm: f.gwConfirm, image: f.gwImage }); }
      f.gwConfirm = ""; await fwRefresh();
    } else if (act.dataset.act === "collector") { const on = act.getAttribute("aria-checked") !== "true"; await api("POST", "/api/v2/collector", { enabled: on }); S.me = await api("GET", "/api/v2/me"); render(); }
  } catch (e) { fail(e); render(); }
});
document.addEventListener("input", (ev) => {
  if (ev.target.closest(".sitesrow")) { S.dirty = true; }
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
      const r = await api("POST", "/api/v2/sites/import?mode=" + $("#csvmode").value, await ev.target.files[0].arrayBuffer(), true);
      S.sites = r.sites; S.warnings = r.warnings; S.dirty = false; render(); toast(t("imported", { n: r.imported }));
    } catch (e) { fail(e); }
  }
});
document.addEventListener("keydown", (e) => { if ((e.key === " " || e.key === "Enter") && e.target.matches && e.target.matches(".sw")) { e.preventDefault(); e.target.click(); } });
$("#langbtn").onclick = () => { lang = lang === "th" ? "en" : "th"; localStorage.setItem("lgs.lang", lang); render(); };
$("#themebtn").onclick = () => { const r = document.documentElement, dark = r.dataset.theme === "dark"; r.dataset.theme = dark ? "light" : "dark"; localStorage.setItem("lgs.theme", r.dataset.theme); };
try { const th = localStorage.getItem("lgs.theme"); if (th) document.documentElement.dataset.theme = th; } catch (e) { /* storage blocked: default theme */ }

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
