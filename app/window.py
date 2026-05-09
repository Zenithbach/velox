# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🪟 window.py
# The frame around the art. Manages the main application window:
# size, position, which monitor it was on, close-to-tray behavior.
# Remembers where you left it because nobody likes re-arranging
# their windows every time they launch an app.

from PyQt6.QtCore import QSize, QPoint
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import QMainWindow, QApplication

from app.webview import VeloxWebView
from app.constants import APP_NAME, APP_VERSION


class VeloxWindow(QMainWindow):
    """
    The main (and only) window.

    Responsibilities:
    - Host the webview
    - Save/restore geometry between sessions
    - Handle zoom shortcuts
    - Close-to-tray behavior (hides instead of quitting)
    - Set the window title and icon

    This is deliberately simple. The webview does the real work.
    The window just holds it.
    """

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._tray = None  # Set later via set_tray()
        self._force_quit = False  # True when quitting for real, not hiding

        # ─── Window Properties ───────────────────────────────────────

        self.setWindowTitle(f"{APP_NAME} — claude.ai")

        # Set the WM_CLASS so KDE Plasma can identify us properly.
        # This matters for window rules, task manager grouping, etc.
        self.setObjectName("velox")

        # Minimum size — don't let it get uselessly small
        self.setMinimumSize(QSize(600, 400))

        # ─── Restore Geometry ────────────────────────────────────────

        self._restore_geometry()

        # ─── Create the Webview ──────────────────────────────────────

        self._webview = VeloxWebView(settings, self)
        self.setCentralWidget(self._webview)

        # ─── Keyboard Shortcuts ──────────────────────────────────────

        self._setup_shortcuts()

    # ─── Public API ──────────────────────────────────────────────────────

    def start(self):
        """Show the window and load claude.ai."""
        self.show()
        self._webview.start()
        print(f"🪟 {APP_NAME} v{APP_VERSION} is up and running.")

    @property
    def webview(self) -> VeloxWebView:
        """Access the webview (for other modules that need it)."""
        return self._webview

    def set_tray(self, tray):
        """
        Connect the tray icon to this window.
        Called by main.py after both window and tray are created.
        Once set, closing the window hides to tray instead of quitting.
        """
        self._tray = tray

    def toggle_visibility(self):
        """
        Show if hidden, hide if shown. Used by global hotkey and tray icon.
        If the window is visible but not focused, bring it to front.
        """
        if self.isVisible() and not self.isMinimized():
            if self.isActiveWindow():
                self.hide()
            else:
                # Visible but not focused — bring to front
                self.activateWindow()
                self.raise_()
        else:
            self.show()
            self.activateWindow()
            self.raise_()

    # ─── Geometry Persistence ────────────────────────────────────────────

    def _restore_geometry(self):
        """
        Put the window back where it was last time.
        If no saved position, use the defaults from config.
        """
        width = self._settings.get("window", "width", 1200)
        height = self._settings.get("window", "height", 800)
        x = self._settings.get("window", "x", -1)
        y = self._settings.get("window", "y", -1)

        self.resize(QSize(width, height))

        if x >= 0 and y >= 0:
            # Sanity check: make sure the saved position is actually on a screen.
            # If you unplugged a monitor, we don't want the window floating in the void.
            screen_geo = QApplication.primaryScreen().availableGeometry()
            if screen_geo.contains(QPoint(x, y)):
                self.move(QPoint(x, y))
            else:
                # Saved position is off-screen. Let the WM figure it out.
                pass
        # else: x or y is -1, meaning "let the WM decide" (first run)

    def _save_geometry(self):
        """Save current window position and size to settings."""
        geo = self.geometry()
        self._settings.set("window", "width", geo.width())
        self._settings.set("window", "height", geo.height())
        self._settings.set("window", "x", geo.x())
        self._settings.set("window", "y", geo.y())

    # ─── Keyboard Shortcuts ──────────────────────────────────────────────

    def _setup_shortcuts(self):
        """
        In-app keyboard shortcuts. These only work when the window is focused.
        Global hotkeys (Ctrl+Alt+Space) are handled by hotkeys.py in Phase 2.
        """
        # Zoom controls — Ctrl+Plus, Ctrl+Minus, Ctrl+0
        zoom_in = QAction("Zoom In", self)
        zoom_in.setShortcuts([
            QKeySequence("Ctrl+="),
            QKeySequence("Ctrl++"),
        ])
        zoom_in.triggered.connect(self._webview.zoom_in)
        self.addAction(zoom_in)

        zoom_out = QAction("Zoom Out", self)
        zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out.triggered.connect(self._webview.zoom_out)
        self.addAction(zoom_out)

        zoom_reset = QAction("Reset Zoom", self)
        zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset.triggered.connect(self._webview.zoom_reset)
        self.addAction(zoom_reset)

        # Reload — sometimes claude.ai gets stuck
        reload_action = QAction("Reload", self)
        reload_action.setShortcut(QKeySequence("F5"))
        reload_action.triggered.connect(self._webview.reload)
        self.addAction(reload_action)

        # Quit — Ctrl+Q because we're civilized
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self._on_quit)
        self.addAction(quit_action)

    # ─── Event Overrides ─────────────────────────────────────────────────

    def closeEvent(self, event):
        """
        Handle window close.
        If tray is active: hide to tray (app keeps running).
        If no tray or force-quitting: save state and actually close.

        This is why closing the window doesn't kill the app.
        Click the X → window hides. Click "Quit" in tray → actually quits.
        """
        if self._tray and self._tray.isVisible() and not self._force_quit:
            # Hide to tray instead of closing
            self._save_geometry()
            self.hide()
            event.ignore()
        else:
            # Actually quitting
            self._save_state()
            event.accept()

    def _save_state(self):
        """Save all persistent state before exit."""
        self._save_geometry()
        self._webview.save_state()
        self._settings.save()
        print("💾 State saved. See you next time. 🦋")

    def _on_quit(self):
        """Clean quit from keyboard shortcut."""
        self._force_quit = True
        self._save_state()
        QApplication.quit()
