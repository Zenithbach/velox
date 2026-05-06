#!/usr/bin/env python3
# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🦋 main.py
# The entry point. Small on purpose.
# All the real work happens in the modules.
# This just says hello and wires everything together.

import sys
import os

# ─── Chromium / Qt Flags ─────────────────────────────────────────────────────
# These need to be set BEFORE QApplication is created.
# That's why they're up here, not buried in a module somewhere.
#
# GPU acceleration: makes scrolling smooth and rendering fast.
# Wayland: handled by Qt's own platform plugin (QT_QPA_PLATFORM),
#   NOT by Chromium's ozone flag — Fedora's QtWebEngine doesn't support
#   --ozone-platform=wayland and will crash if you try. Ask us how we know.
# Sandbox: stays ON for security (Chromium's process isolation).

os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS",
    "--enable-gpu-rasterization "
    "--enable-features=VaapiVideoDecoder "
    "--enable-wayland-ime"
)

# Let Qt pick the best platform plugin.
# On KDE Plasma Wayland this will use wayland natively.
# Falls back to xcb (X11) if Wayland isn't available.
# We don't force it — Qt and your desktop know best.
if "QT_QPA_PLATFORM" not in os.environ:
    pass  # Let Qt auto-detect. Forcing can cause issues on some setups.

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.constants import APP_NAME, APP_VERSION, STARTUP_BANNER
from app.settings import Settings
from app.window import VeloxWindow


def main():
    """
    Launch Velox. That's it. That's the function.
    """
    # Say hello 🦋
    print(STARTUP_BANNER)

    # ─── Qt Application ──────────────────────────────────────────────

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Velox")

    # Set the desktop filename so KDE associates us with our .desktop file
    app.setDesktopFileName("velox")

    # Don't quit when the last window is hidden (needed for close-to-tray in Phase 2)
    app.setQuitOnLastWindowClosed(True)  # Phase 2: change to False when tray is added

    # ─── Settings ────────────────────────────────────────────────────

    settings = Settings()

    # ─── Main Window ─────────────────────────────────────────────────

    window = VeloxWindow(settings)

    # Check if we should start minimized (usually not, but it's configurable)
    if settings.get("window", "start_minimized", False):
        print("🪟 Starting minimized (start_minimized is on)")
        # Phase 2: this will minimize to tray instead
    else:
        window.start()

    # ─── Run ─────────────────────────────────────────────────────────

    print(f"🚀 {APP_NAME} v{APP_VERSION} is ready. Happy chatting!")
    exit_code = app.exec()

    # ─── Cleanup ─────────────────────────────────────────────────────

    print("👋 Shutting down gracefully.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
