"""The page that heals itself — for a screen nobody will touch for a week.

Three nights (2026-09-26, 09-29 twice) the browser page of a fleet run was
found dead in the morning while the run underneath it was fine. v1.9.1 made
the run independent of its page; this makes the page come back on its own,
because on the hospital's server nobody is going to press F5.

How a NiceGUI page dies, read from nicegui.js 2.24:

  * The server keeps a client's state only `reconnect_timeout` seconds after
    its socket drops (3.0 s by default — one switch blink). After that, a
    reconnecting browser fails its handshake and nicegui.js RELOADS.
  * A reconnection attempt that TIMES OUT (socket.io gives it 20 s) also
    makes nicegui.js reload — at the exact moment the server is unreachable.
    A reload that fails leaves Chrome's own error page, which never retries.
    That is the corpse found in the morning: the page reloaded itself into
    a dead LAN and stayed there.

So: the server keeps client state for a full minute of outage (main.py sets
reconnect_timeout), the page reloads only after the server has ANSWERED a
probe (the reload-into-nothing is intercepted below), and a page whose
socket says "connected" but that has stopped hearing the server's heartbeat
reloads itself too. Every reload lands on a fresh page that inherits the
run (v1.9.1), so a reload costs nothing but a blink.

The heartbeat is one attribute on a hidden element, updated by a timer: no
JavaScript request/response bookkeeping, and it rides the same channel as
every other update, so it measures what matters — is THIS page still being
drawn by the server.
"""
from __future__ import annotations

import time

from nicegui import app, ui

BEAT_S = 2.0            # server-side heartbeat period
STALE_S = 60            # no beat for this long while visible -> reload
PROBE_PATH = "/_lgs/alive"

# Runs before socket.io loads (add_head_html sits above the deferred scripts
# in NiceGUI's template), so it can catch the `io` global at the moment the
# library defines it and hand NiceGUI a wrapped copy.
_HEAD_JS = """
<script>
(function () {
  var stale_ms = %(stale_ms)d, probe = "%(probe)s";
  var reloading = false;

  // Reload only once the server answers. A reload that fails leaves the
  // browser's error page, which never retries; this never fails.
  function safeReload(why) {
    if (reloading) return;
    reloading = true;
    console.log("lgs page guard: " + why + " - reloading when the server answers");
    var tries = 0;
    (function probeLoop() {
      tries += 1;
      fetch(probe + "?t=" + Date.now(), {cache: "no-store"})
        .then(function (r) { if (r.ok) { window.location.reload(); }
                             else { setTimeout(probeLoop, 3000); } })
        .catch(function () { setTimeout(probeLoop, tries < 20 ? 3000 : 10000); });
    })();
  }
  window.lgsSafeReload = safeReload;

  // Intercept nicegui.js's reload-on-connect-timeout: same intent, but wait
  // for the server first. Everything else socket.io does is untouched.
  var realIo = null;
  function wrapIo(io) {
    return function () {
      var socket = io.apply(this, arguments);
      var on = socket.on.bind(socket);
      socket.on = function (name, handler) {
        if (name === "connect_error") {
          return on(name, function (err) {
            if (err && err.message === "timeout") { safeReload("connection attempt timed out"); return; }
            handler(err);
          });
        }
        return on(name, handler);
      };
      return socket;
    };
  }
  try {
    Object.defineProperty(window, "io", {
      configurable: true,
      get: function () { return realIo; },
      set: function (v) { realIo = (typeof v === "function") ? wrapIo(v) : v; }
    });
  } catch (e) { /* older browser: no interception, the rest still works */ }

  // Heartbeat watchdog. The server bumps data-beat every couple of seconds;
  // a page that has not seen a bump for a minute is not being drawn any
  // more, whatever the socket believes. Checked only while visible: a
  // background tab is throttled and would cry wolf, so it is checked the
  // moment it is shown instead.
  var lastBeat = "", lastChange = Date.now();
  function check() {
    var el = document.querySelector("[data-lgs-beat]");
    if (!el) return;
    var beat = el.getAttribute("data-lgs-beat");
    if (beat !== lastBeat) { lastBeat = beat; lastChange = Date.now(); return; }
    if (document.visibilityState === "visible" && Date.now() - lastChange > stale_ms) {
      safeReload("no heartbeat for " + Math.round((Date.now() - lastChange) / 1000) + " s");
    }
  }
  setInterval(check, 5000);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") setTimeout(check, 1000);
  });
})();
</script>
"""


def install() -> None:
    """Call once per page build (inside the @ui.page function)."""
    ui.add_head_html(_HEAD_JS % {"stale_ms": int(STALE_S * 1000), "probe": PROBE_PATH})
    beat = ui.element("span").props("data-lgs-beat=0").style("display:none")
    t0 = time.monotonic()

    def tick() -> None:
        # Monotonic seconds since the page was built; the page only cares
        # that the value keeps changing.
        beat.props(f"data-lgs-beat={time.monotonic() - t0:.1f}")

    ui.timer(BEAT_S, tick)


@app.get(PROBE_PATH)
def _alive() -> str:
    """Cheap, no client state, no page build: 'is the server there'."""
    return "ok"
