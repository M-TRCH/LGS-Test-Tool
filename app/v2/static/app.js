/* LGS Test Tool v2 front end, stage 1: Cabinets, Sites, Events. Plain JS, no libraries. */
"use strict";

const TXT = {
  th: {
    stage: "v2 ขั้นแรก", classic: "หน้าแบบเดิม", cabinets: "ตู้", sites: "รายการตู้", events: "เหตุการณ์",
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
    matched: "{n} found", loginAgain: "Sign in again", error: "Error: {e}", d: "d", h: "h",
  },
};
let lang = (localStorage.getItem("lgs.lang") || "th");
const t = (k, p) => { let s = (TXT[lang] && TXT[lang][k]) || TXT.en[k] || k; for (const a in (p || {})) s = s.replace("{" + a + "}", p[a]); return s; };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: "", days: 1, q: "", types: new Set() }, gw: { id: "", data: null, edits: {}, busy: false } };
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
    body = `<section class="card"><dl class="kv"><dt>${t("fw")}</dt><dd class="mono">${esc(i.fw)}</dd><dt>${t("uptime")}</dt><dd>${fmtUp(+i["sys.up"] || 0)} (${esc(i["sys.reset"] || "")})</dd>
        <dt>${t("clients")}</dt><dd>${esc(i["net.client"] || "?")}/2</dd><dt>${t("clock")}</dt><dd>${i["time.set"] === "1" ? esc((i["time.now"] || "").replace("T", " ")) : t("clockUnset")}</dd></dl></section>
      <section class="card stack"><div class="row"><button class="btn" data-act="gw-time">${t("setClock")}</button></div><p class="small muted">${t("clockWarn")}</p>
        ${sw("resync", i["rtu.heal"] === "1")}${sw("exc", i["tcp.exc"] === "1")}</section>
      <section class="card stack">${order.map((grp) => `<details${grp === "rs485" || grp === "net" ? " open" : ""}><summary><b>${esc(grp)}</b> <span class="small muted">${groups[grp].length}</span></summary><div class="fgrid" style="margin-top:8px">${groups[grp].map(field).join("")}</div></details>`).join("")}</section>
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

const VIEWS = { cabinets: viewCabinets, gateway: viewGateway, sites: viewSites, events: viewEvents };
const NAV = [["cabinets", "▦"], ["gateway", "⚙"], ["sites", "☰"], ["events", "≡"]];

function render() {
  $("#nav").innerHTML = NAV.map(([k, ic]) => `<button data-nav="${k}" ${k === page ? 'aria-current="page"' : ""}><span class="ic">${ic}</span>${t(k === "gateway" ? "gateway_page" : k)}</button>`).join("")
    + `<button data-nav="classic"><span class="ic">↗</span>${t("classic")}</button>`;
  $("#nav").style.gridTemplateColumns = window.innerWidth < 900 ? `repeat(${NAV.length + 1},1fr)` : "";
  $("#main").innerHTML = (VIEWS[page] || viewCabinets)();
  $("#stagechip").textContent = t("stage");
  $("#langbtn").textContent = lang.toUpperCase();
  document.documentElement.lang = lang;
  if (page === "events") loadEvents();
  if (page === "gateway") gwBar();
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
  if (nav) { if (nav.dataset.nav === "classic") { location.href = "/"; return; } page = nav.dataset.nav; location.hash = "#/" + page; if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways").catch(() => ({}))).gateways || []; render(); return; }
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
  if (ev.target.id === "gwsel") { S.gw.id = ev.target.value; S.gw.data = null; S.gw.edits = {}; if (S.gw.id) gwRead(); else render(); }
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
window.addEventListener("resize", () => { $("#nav").style.gridTemplateColumns = window.innerWidth < 900 ? `repeat(${NAV.length + 1},1fr)` : ""; });
try { const th = localStorage.getItem("lgs.theme"); if (th) document.documentElement.dataset.theme = th; } catch (e) { /* storage blocked: default theme */ }

(async () => {
  try {
    S.me = await api("GET", "/api/v2/me"); $("#ver").textContent = "v" + S.me.version;
    await loadSites();
    if (page === "events") S.evGw = (await api("GET", "/api/v2/events/gateways")).gateways || [];
  } catch (e) { fail(e); }
  render();
})();
