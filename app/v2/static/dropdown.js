/* One look for every drop-down in the Tool.
 *
 * The browser's own <select> list is drawn by the operating system and ignores the theme: it is the plain grey box on the
 * Modules and Firmware pages next to the filter panel on the Events page, which is drawn by the Tool. This file gives every
 * <select> the Tool's own button and list (the same border, radius, shadow and hover as the Events filters), WITHOUT
 * changing how the page talks to it: the <select> stays in the document, hidden, and keeps its value and its `change`
 * event, so every `select.value`, `#id` lookup and change handler in app.js works as it did.
 *
 *   - the button shows the chosen option and a caret; it copies the select's inline style (widths, flex) and aria-label;
 *   - the list opens under the button (above it when there is no room), inside the open <dialog> if there is one;
 *   - Up/Down/Home/End/Enter/Esc work, typing a letter jumps to the next option that starts with it;
 *   - the value / selectedIndex setters are wrapped, so `sel.value = x` from code updates the button without a re-render;
 *   - a <select multiple> and any select with data-native stay native.
 */
(function () {
  "use strict";
  const SKIP = "select[multiple], select[data-native]";
  let openDd = null;                                   // { sel, btn, panel, active }

  const labelOf = (sel) => { const o = sel.options[sel.selectedIndex]; return o ? o.textContent.trim() : ""; };

  function sync(sel) {
    const b = sel._ddBtn;
    if (!b) return;
    b.firstChild.textContent = labelOf(sel) || " ";
    b.disabled = sel.disabled;
  }

  function enhance(sel) {
    if (sel._ddBtn || sel.matches(SKIP)) return;
    const b = document.createElement("button");
    b.type = "button";
    b.className = "ddbtn";
    b.setAttribute("aria-haspopup", "listbox");
    b.setAttribute("aria-expanded", "false");
    const lab = sel.getAttribute("aria-label") || sel.title;
    if (lab) { b.setAttribute("aria-label", lab); b.title = sel.title || lab; }
    if (sel.getAttribute("style")) b.setAttribute("style", sel.getAttribute("style"));
    b.appendChild(document.createElement("span"));
    const caret = document.createElement("span");
    caret.className = "ddc";
    caret.setAttribute("aria-hidden", "true");
    b.appendChild(caret);
    sel.classList.add("ddhide");
    sel.after(b);
    sel._ddBtn = b;
    b._sel = sel;
    b.addEventListener("click", () => (openDd && openDd.sel === sel ? close() : openList(sel)));
    sync(sel);
  }

  function enhanceAll(root) {
    if (root.nodeType !== 1) return;
    if (root.matches && root.matches("select")) enhance(root);
    root.querySelectorAll && root.querySelectorAll("select").forEach(enhance);
  }

  // ── the list ──────────────────────────────────────────────────────────────
  function rows(sel) {
    const out = [];
    for (const child of sel.children) {
      if (child.tagName === "OPTGROUP") {
        out.push({ group: child.label });
        for (const o of child.children) out.push({ o });
      } else if (child.tagName === "OPTION") out.push({ o: child });
    }
    return out;
  }

  function openList(sel) {
    close();
    const btn = sel._ddBtn;
    if (!btn || btn.disabled) return;
    const panel = document.createElement("div");
    panel.className = "ddpanel";
    panel.setAttribute("role", "listbox");
    const items = [];
    for (const r of rows(sel)) {
      const el = document.createElement("div");
      if (r.group !== undefined) { el.className = "ddgrp"; el.textContent = r.group; panel.appendChild(el); continue; }
      el.className = "ddopt";
      el.setAttribute("role", "option");
      el.dataset.i = String(r.o.index);
      const t = document.createElement("span");
      t.textContent = r.o.textContent.trim() || " ";
      const tick = document.createElement("i");
      tick.setAttribute("aria-hidden", "true");
      el.append(t, tick);
      if (r.o.disabled) el.classList.add("off");
      if (r.o.index === sel.selectedIndex) { el.classList.add("on"); el.setAttribute("aria-selected", "true"); }
      el.addEventListener("pointerdown", (e) => e.preventDefault());       // keep focus where it is
      el.addEventListener("click", () => { if (!r.o.disabled) choose(sel, r.o.index); });
      el.addEventListener("pointermove", () => setActive(dd, el));
      panel.appendChild(el);
      items.push(el);
    }
    const host = btn.closest("dialog[open]") || document.body;
    host.appendChild(panel);
    const dd = { sel, btn, panel, items, active: items.find((x) => x.classList.contains("on")) || items.find((x) => !x.classList.contains("off")) || null, typed: "", typedAt: 0 };
    openDd = dd;
    btn.setAttribute("aria-expanded", "true");
    btn.classList.add("open");
    place(dd);
    if (dd.active) { dd.active.classList.add("act"); dd.active.scrollIntoView({ block: "nearest" }); }
  }

  function place(dd) {
    // position:fixed is measured from the viewport even inside an open <dialog>, so no offset to correct for
    const { btn, panel } = dd;
    const r = btn.getBoundingClientRect();
    const vh = window.innerHeight, vw = window.innerWidth;
    panel.style.minWidth = Math.max(r.width, 160) + "px";
    panel.style.maxWidth = Math.min(vw - 16, 420) + "px";
    panel.style.maxHeight = "";
    const below = vh - r.bottom - 12, above = r.top - 12;
    const want = Math.min(panel.scrollHeight + 14, 320);
    const up = below < Math.min(want, 180) && above > below;
    panel.style.maxHeight = Math.max(120, Math.min(320, up ? above : below)) + "px";
    panel.style.left = Math.min(Math.max(8, r.left), Math.max(8, vw - panel.offsetWidth - 8)) + "px";
    if (up) { panel.style.top = ""; panel.style.bottom = vh - r.top + 6 + "px"; }
    else { panel.style.bottom = ""; panel.style.top = r.bottom + 6 + "px"; }
  }

  function setActive(dd, el) {
    if (dd.active === el || !el) return;
    if (dd.active) dd.active.classList.remove("act");
    dd.active = el;
    el.classList.add("act");
    el.scrollIntoView({ block: "nearest" });
  }

  function choose(sel, index) {
    const changed = sel.selectedIndex !== index;
    sel.selectedIndex = index;
    close();
    if (changed) {
      sel.dispatchEvent(new Event("input", { bubbles: true }));
      sel.dispatchEvent(new Event("change", { bubbles: true }));
    }
    sel._ddBtn && sel._ddBtn.focus({ preventScroll: true });
  }

  function close() {
    if (!openDd) return;
    openDd.panel.remove();
    openDd.btn.setAttribute("aria-expanded", "false");
    openDd.btn.classList.remove("open");
    openDd = null;
  }

  // ── keyboard and dismissal (one set of listeners for the whole page) ──────
  document.addEventListener("keydown", (e) => {
    const t = e.target;
    if (!openDd) {
      if (t && t.classList && t.classList.contains("ddbtn") && ["ArrowDown", "ArrowUp"].includes(e.key)) { e.preventDefault(); openList(t._sel); }
      return;
    }
    const dd = openDd, i = dd.items.indexOf(dd.active);
    const step = (d) => { let k = i; do { k += d; } while (dd.items[k] && dd.items[k].classList.contains("off")); if (dd.items[k]) setActive(dd, dd.items[k]); };
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); const b = dd.btn; close(); b.focus({ preventScroll: true }); }
    else if (e.key === "ArrowDown") { e.preventDefault(); step(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); step(-1); }
    else if (e.key === "Home") { e.preventDefault(); setActive(dd, dd.items.find((x) => !x.classList.contains("off"))); }
    else if (e.key === "End") { e.preventDefault(); setActive(dd, [...dd.items].reverse().find((x) => !x.classList.contains("off"))); }
    else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (dd.active) choose(dd.sel, +dd.active.dataset.i); }
    else if (e.key === "Tab") close();
    else if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const now = Date.now();
      dd.typed = now - dd.typedAt > 700 ? e.key.toLowerCase() : dd.typed + e.key.toLowerCase();
      dd.typedAt = now;
      const hit = dd.items.find((x) => !x.classList.contains("off") && x.textContent.trim().toLowerCase().startsWith(dd.typed));
      if (hit) setActive(dd, hit);
    }
  }, true);
  document.addEventListener("pointerdown", (e) => { if (openDd && !openDd.panel.contains(e.target) && !openDd.btn.contains(e.target)) close(); }, true);
  window.addEventListener("resize", close);
  window.addEventListener("scroll", (e) => { if (openDd && !openDd.panel.contains(e.target)) close(); }, true);

  // ── keep the button in step with the select ───────────────────────────────
  for (const prop of ["value", "selectedIndex"]) {
    const d = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, prop);
    if (!d || !d.set) continue;
    Object.defineProperty(HTMLSelectElement.prototype, prop, { configurable: true, enumerable: d.enumerable, get: d.get, set(v) { d.set.call(this, v); sync(this); } });
  }
  document.addEventListener("change", (e) => { if (e.target && e.target._ddBtn) sync(e.target); }, true);

  const watch = new MutationObserver((records) => {
    for (const r of records) {
      r.addedNodes.forEach(enhanceAll);
      const owner = r.target.nodeType === 1 ? r.target.closest && r.target.closest("select") : r.target.parentElement && r.target.parentElement.closest("select");
      if (owner && owner._ddBtn) sync(owner);
      if (r.type === "attributes" && r.target._ddBtn) sync(r.target);
    }
  });
  function start() {
    enhanceAll(document.body);
    watch.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ["disabled", "selected"], characterData: true });
  }
  if (document.body) start(); else document.addEventListener("DOMContentLoaded", start);
})();
