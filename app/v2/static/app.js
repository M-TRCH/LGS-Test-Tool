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
    matched: "{n} found", loginAgain: "Sign in again", error: "Error: {e}", d: "d", h: "h",
  },
};
let lang = (localStorage.getItem("lgs.lang") || "th");
const t = (k, p) => { let s = (TXT[lang] && TXT[lang][k]) || TXT.en[k] || k; for (const a in (p || {})) s = s.replace("{" + a + "}", p[a]); return s; };
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const $ = (s, r = document) => r.querySelector(s);

let S = { sites: [], warnings: [], layouts: [], health: {}, checkedAt: "", dirty: false, me: null, ev: { gw: "", days: 1, q: "", types: new Set() } };
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

const VIEWS = { cabinets: viewCabinets, sites: viewSites, events: viewEvents };
const NAV = [["cabinets", "▦"], ["sites", "☰"], ["events", "≡"]];

function render() {
  $("#nav").innerHTML = NAV.map(([k, ic]) => `<button data-nav="${k}" ${k === page ? 'aria-current="page"' : ""}><span class="ic">${ic}</span>${t(k)}</button>`).join("")
    + `<button data-nav="classic"><span class="ic">↗</span>${t("classic")}</button>`;
  $("#nav").style.gridTemplateColumns = window.innerWidth < 900 ? `repeat(${NAV.length + 1},1fr)` : "";
  $("#main").innerHTML = (VIEWS[page] || viewCabinets)();
  $("#stagechip").textContent = t("stage");
  $("#langbtn").textContent = lang.toUpperCase();
  document.documentElement.lang = lang;
  if (page === "events") loadEvents();
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
    } else if (act.dataset.act === "collector") { const on = act.getAttribute("aria-checked") !== "true"; await api("POST", "/api/v2/collector", { enabled: on }); S.me = await api("GET", "/api/v2/me"); render(); }
  } catch (e) { fail(e); render(); }
});
document.addEventListener("input", (ev) => {
  if (ev.target.closest(".sitesrow")) { S.dirty = true; }
  if (ev.target.id === "evq") { S.ev.q = ev.target.value; clearTimeout(window._evt); window._evt = setTimeout(loadEvents, 300); }
});
document.addEventListener("change", async (ev) => {
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
