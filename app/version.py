"""Single source of the app version.

Shown in the header badge, the browser tab title, the startup banner, and the
packaged exe filename, so users can tell at a glance which build they run.

Bump once per actual release (when an exe is built and handed over) — not per
commit, and not while iterating during development.
"""
APP_VERSION = "1.7.1"
