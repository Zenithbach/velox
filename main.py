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

from PyQt6.QtWidgets import QApplication

from app.constants import APP_NAME, APP_VERSION, STARTUP_BANNER
from app.settings import Settings
from app.window import VeloxWindow
from app.tray import VeloxTray
from app.notifications import NotificationManager
from app.downloads import DownloadManager
from app.theme import ThemeManager
from app.focus_mode import FocusMode
from app.code_tools import CodeTools
from app.chat_export import ChatExport
from app.chat_summarizer import ChatSummarizer


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

    # Don't quit when the last window is hidden — tray keeps us alive
    app.setQuitOnLastWindowClosed(False)

    # ─── Settings ────────────────────────────────────────────────────

    settings = Settings()

    # ─── Theme ───────────────────────────────────────────────────────
    # Apply theme before creating any widgets so colors are right from the start

    theme_manager = ThemeManager(settings)

    # ─── Main Window ─────────────────────────────────────────────────

    window = VeloxWindow(settings)

    # ─── Tray Icon ───────────────────────────────────────────────────

    tray = VeloxTray(window, settings)

    # Apply themed stylesheet to the tray menu
    tray.contextMenu().setStyleSheet(theme_manager.get_stylesheet())

    # Tell the window about the tray so it can hide-to-tray on close
    window.set_tray(tray)

    # ─── Notifications ───────────────────────────────────────────────

    notifications = NotificationManager(tray, settings)

    # ─── Downloads ───────────────────────────────────────────────────
    # Wire into the webview's profile so we catch download requests

    download_manager = DownloadManager(
        profile=window.webview._profile,
        settings=settings,
        notifications=notifications,
    )

    # ─── Focus Mode ──────────────────────────────────────────────────

    focus_mode = FocusMode(window.webview, settings)

    # ─── Code Tools ──────────────────────────────────────────────────

    code_tools = CodeTools(window.webview)

    # ─── Chat Export ─────────────────────────────────────────────────

    chat_export = ChatExport(
        window.webview, settings, notifications=notifications
    )

    # ─── Chat Summarizer ─────────────────────────────────────────────

    summarizer = ChatSummarizer(
        window.webview, settings, notifications=notifications
    )

    # ─── Wire Phase 3 into Window ────────────────────────────────────
    # Give the window access to these modules for keyboard shortcuts

    window.set_phase3(
        focus_mode=focus_mode,
        code_tools=code_tools,
        chat_export=chat_export,
    )

    # Give the tray access for menu items
    tray.set_phase3(
        focus_mode=focus_mode,
        code_tools=code_tools,
        chat_export=chat_export,
    )

    # ─── Start Everything ────────────────────────────────────────────

    tray.start()

    if settings.get("window", "start_minimized", False):
        print("🪟 Starting minimized to tray")
        window.webview.start()  # Load the page even if window is hidden
    else:
        window.start()

    # Start the summarizer after the page is loading
    summarizer.start()

    # ─── Run ─────────────────────────────────────────────────────────

    print(f"🚀 {APP_NAME} v{APP_VERSION} is ready. Happy chatting!")
    exit_code = app.exec()

    # ─── Cleanup ─────────────────────────────────────────────────────

    print("👋 Shutting down gracefully.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
