# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🔲 tray.py
# The little icon that lives in your panel and proves
# the app is still running even when the window is hidden.
# Left-click to toggle, right-click for the menu.
# Rotate tooltips because life's too short for static text.

import random

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt

from app.constants import TRAY_TOOLTIPS


def _generate_placeholder_icon() -> QIcon:
    """
    Generate a simple placeholder tray icon programmatically.
    A glowing blue portal on a dark background.
    This gets replaced when a real icon file is available.

    Why not just ship a PNG? Because we want zero external
    dependencies for Phase 2. The real icon arrives when
    Geoff finishes the Canva design. Until then: programmer art.
    """
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Dark outer frame
    painter.setBrush(QBrush(QColor(20, 25, 45)))
    painter.setPen(QPen(QColor(40, 50, 80), 2))
    painter.drawRoundedRect(2, 2, size - 4, size - 4, 8, 8)

    # Inner portal glow
    painter.setBrush(QBrush(QColor(0, 140, 255)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(14, 12, size - 28, size - 24, 4, 4)

    # Bright center
    painter.setBrush(QBrush(QColor(80, 200, 255)))
    painter.drawRoundedRect(20, 18, size - 40, size - 36, 2, 2)

    painter.end()

    return QIcon(pixmap)


def _load_icon() -> QIcon:
    """
    Try to load a real icon file. Fall back to the placeholder
    if no icon file exists yet.

    Icon search order:
    1. packaging/icons/velox-256.png (in the repo)
    2. ~/.config/velox/icon.png (user-supplied)
    3. Generated placeholder (the blue portal square)
    """
    from pathlib import Path
    from app.constants import CONFIG_DIR

    search_paths = [
        Path(__file__).parent.parent / "packaging" / "icons" / "velox-256.png",
        CONFIG_DIR / "icon.png",
    ]

    for path in search_paths:
        if path.exists():
            icon = QIcon(str(path))
            if not icon.isNull():
                print(f"🔲 Loaded icon from {path}")
                return icon

    print("🔲 Using placeholder icon (no icon file found yet)")
    return _generate_placeholder_icon()


class VeloxTray(QSystemTrayIcon):
    """
    System tray icon with a right-click menu.

    Left-click: toggle window visibility
    Right-click: menu with show/hide, logout, quit

    Tooltip rotates through fun messages because
    static tooltips are for apps that don't care.
    """

    def __init__(self, window, settings, parent=None):
        super().__init__(parent)
        self._window = window
        self._settings = settings

        # ─── Icon ────────────────────────────────────────────────────
        self.setIcon(_load_icon())

        # ─── Tooltip ─────────────────────────────────────────────────
        self._set_random_tooltip()

        # ─── Menu ────────────────────────────────────────────────────
        self._menu = QMenu()
        self._build_menu()
        self.setContextMenu(self._menu)

        # ─── Signals ─────────────────────────────────────────────────
        self.activated.connect(self._on_activated)

    # ─── Public API ──────────────────────────────────────────────────────

    def start(self):
        """Show the tray icon. Call after window is set up."""
        if self._settings.get("tray", "enabled", True):
            self.show()
            print(f"🔲 Tray icon is live. Right-click for options.")
        else:
            print("🔲 Tray icon disabled in config.")

    def set_phase3(self, focus_mode=None, code_tools=None, chat_export=None):
        """Connect Phase 3 modules for tray menu actions."""
        self._focus_mode = focus_mode
        self._code_tools = code_tools
        self._chat_export = chat_export

    # ─── Menu Construction ───────────────────────────────────────────────

    def _build_menu(self):
        """Build the right-click context menu."""

        # Show / Hide
        show_action = self._menu.addAction("Show / Hide Window")
        show_action.triggered.connect(self._toggle_window)

        self._menu.addSeparator()

        # Focus Mode (Phase 3)
        self._focus_action = self._menu.addAction("🧘 Focus Mode")
        self._focus_action.triggered.connect(self._toggle_focus)

        # Save Chat (Phase 3)
        self._save_action = self._menu.addAction("💾 Save Chat")
        self._save_action.triggered.connect(self._save_chat)

        # Copy All Code (Phase 3)
        self._copy_code_action = self._menu.addAction("💻 Copy All Code")
        self._copy_code_action.triggered.connect(self._copy_code)

        self._menu.addSeparator()

        # Reload
        reload_action = self._menu.addAction("🔄 Reload")
        reload_action.triggered.connect(self._reload)

        self._menu.addSeparator()

        # Log Out
        logout_action = self._menu.addAction("🔓 Log Out")
        logout_action.triggered.connect(self._logout)

        # Quit
        quit_action = self._menu.addAction("👋 Quit Velox")
        quit_action.triggered.connect(self._quit)

    # ─── Actions ─────────────────────────────────────────────────────────

    def _on_activated(self, reason):
        """Handle tray icon clicks."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left-click: toggle window
            self._toggle_window()
            self._set_random_tooltip()  # Fresh tooltip each time

    def _toggle_window(self):
        """Show the window if hidden, hide if shown."""
        self._window.toggle_visibility()

    def _reload(self):
        """Reload claude.ai in the webview."""
        self._window.webview.reload()
        print("🔄 Reloading claude.ai...")

    def _toggle_focus(self):
        """Toggle focus mode from tray menu."""
        if hasattr(self, '_focus_mode') and self._focus_mode:
            self._focus_mode.toggle()
        else:
            print("🧘 Focus mode not available yet.")

    def _save_chat(self):
        """Save current chat from tray menu."""
        if hasattr(self, '_chat_export') and self._chat_export:
            self._chat_export.save_current_chat()
        else:
            print("💾 Chat export not available yet.")

    def _copy_code(self):
        """Copy all code blocks from tray menu."""
        if hasattr(self, '_code_tools') and self._code_tools:
            self._code_tools.copy_all_code_blocks()
        else:
            print("💻 Code tools not available yet.")

    def _logout(self):
        """Clear cookies and reload. You'll need to log in again."""
        self._window.webview.logout()
        self._window.show()
        self._window.activateWindow()

    def _quit(self):
        """Clean quit from tray menu."""
        self._window._save_state()
        QApplication.quit()

    # ─── Tooltip Fun ─────────────────────────────────────────────────────

    def _set_random_tooltip(self):
        """Pick a random tooltip from the fun list."""
        tooltip = random.choice(TRAY_TOOLTIPS)
        self.setToolTip(tooltip)
