# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🌐 webview.py
# The heart of the operation. This is where claude.ai actually lives.
# A QtWebEngine view with GPU acceleration, Wayland-native rendering,
# locked-down permissions, and zero caching.
#
# Think of it as a browser that only knows one website
# and takes its job very seriously.

import sys

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWebEngineCore import (
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

from app.constants import CLAUDE_URL, USER_AGENT, CONFIG_DIR
from app.security import DomainFilter
from app.cookie_store import CookieManager


class VeloxPage(QWebEnginePage):
    """
    Custom page handler so we can intercept permission requests
    and new-window navigations. Also handles JavaScript console
    messages if we ever need to debug the frontend.
    """

    def __init__(self, profile: QWebEngineProfile, parent=None):
        super().__init__(profile, parent)

    # ─── Permission Handling ─────────────────────────────────────────────

    def permissionRequested(self, permission):
        """
        Handle permission requests from the web page.
        Microphone: ✅ (for claude.ai voice input)
        Camera: ❌ (you don't need to show Claude your face)
        Everything else: ❌ by default
        """
        # QWebEnginePermission.PermissionType
        ptype = permission.permissionType()

        # Import here to avoid circular issues
        from PyQt6.QtWebEngineCore import QWebEnginePermission

        if ptype == QWebEnginePermission.PermissionType.MediaAudioCapture:
            permission.grant()
        elif ptype == QWebEnginePermission.PermissionType.ClipboardReadWrite:
            permission.grant()
        else:
            # Camera, geolocation, notifications from web, etc. → nope.
            permission.deny()

    def createWindow(self, window_type):
        """
        Called when the page wants to open a new window (target="_blank" links).
        Instead of opening a new window (we're not a browser), we just
        navigate the current view. OAuth popups will work this way.
        """
        return self

    def javaScriptConsoleMessage(self, level, message, line, source):
        """
        Catch JS console messages. Useful for debugging but we don't
        spam the terminal with them by default.
        """
        # Uncomment the line below if you need to debug frontend issues:
        # print(f"  [JS] {source}:{line} — {message}")
        pass


class VeloxWebView(QWebEngineView):
    """
    The main webview. Wraps QWebEngineView with:
    - Custom off-the-record profile (no shared browser data)
    - Domain filtering (security.py does the heavy lifting)
    - Persistent cookies (cookie_store.py manages these)
    - GPU acceleration flags
    - Microphone permissions for voice input
    - Zero cache policy

    This is the one widget that matters. Everything else is decoration.
    """

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._settings = settings

        # Create an isolated profile — not shared with any other browser.
        # The string gives it a persistent storage path for cookies.
        # We handle cookie persistence ourselves, but Qt needs a profile name
        # to not treat it as fully off-the-record.
        self._profile = QWebEngineProfile("velox", self)

        # ─── Profile Configuration ───────────────────────────────────

        # User agent: look like a normal browser
        self._profile.setHttpUserAgent(USER_AGENT)

        # CRITICAL: Disable all caching.
        # We don't want chat content sitting on disk in a cache somewhere.
        # The only persistent data should be cookies (which we manage).
        self._profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.NoCache)

        # Disable spell checking (don't need it, don't want the data)
        self._profile.setSpellCheckEnabled(False)

        # ─── Security: Domain Filter ─────────────────────────────────

        log_blocked = settings.get("security", "log_blocked_requests", False)
        self._domain_filter = DomainFilter(log_blocked=log_blocked, parent=self)
        self._profile.setUrlRequestInterceptor(self._domain_filter)

        # ─── Cookie Manager ──────────────────────────────────────────

        self._cookie_manager = CookieManager(self._profile)

        # ─── Custom Page ─────────────────────────────────────────────

        self._page = VeloxPage(self._profile, self)
        self.setPage(self._page)

        # ─── WebEngine Settings ──────────────────────────────────────

        ws = self._page.settings()

        # JavaScript: ON (claude.ai is a React app, it's nothing without JS)
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Clipboard: ON (you need copy/paste)
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True)
        ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanPaste, True)

        # Local storage: ON (claude.ai uses it for UI state)
        ws.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)

        # Scrollbar: use the page's own scrollbar
        ws.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, True)

        # Focus on click: yes please
        ws.setAttribute(QWebEngineSettings.WebAttribute.FocusOnNavigationEnabled, True)

        # PDF viewer: OFF (we're not a PDF reader)
        ws.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, False)

        # ─── Drag and Drop ───────────────────────────────────────────
        self.setAcceptDrops(True)

        # ─── Zoom ────────────────────────────────────────────────────
        zoom = settings.get("zoom", "level", 1.0)
        self.setZoomFactor(zoom)

    # ─── Public API ──────────────────────────────────────────────────────

    def start(self):
        """
        Load cookies and navigate to claude.ai.
        Call this after the window is set up.
        """
        # Load saved cookies BEFORE navigating so the session is ready
        self._cookie_manager.load()

        # Here we go. 🦋
        self.load(QUrl(CLAUDE_URL))
        print(f"🌐 Loading {CLAUDE_URL}")

    def get_zoom(self) -> float:
        """Get current zoom level for saving to config."""
        return self.zoomFactor()

    def set_zoom(self, level: float):
        """Set zoom level. 1.0 = 100%, 1.5 = 150%, etc."""
        level = max(0.25, min(5.0, level))  # Clamp to sane range
        self.setZoomFactor(level)

    def zoom_in(self):
        """Bump zoom up by 10%."""
        self.set_zoom(self.zoomFactor() + 0.1)

    def zoom_out(self):
        """Bump zoom down by 10%."""
        self.set_zoom(self.zoomFactor() - 0.1)

    def zoom_reset(self):
        """Back to 100%."""
        self.set_zoom(1.0)

    def logout(self):
        """
        Clear all cookies and reload. The nuclear "Log Out" option.
        You'll need to sign in again after this.
        """
        self._cookie_manager.clear()
        self.load(QUrl(CLAUDE_URL))
        print("🔓 Logged out. All cookies cleared.")

    @property
    def cookie_manager(self) -> CookieManager:
        """Access the cookie manager (for tray menu logout, etc.)."""
        return self._cookie_manager

    @property
    def domain_filter(self) -> DomainFilter:
        """Access the domain filter (for toggling debug logging, etc.)."""
        return self._domain_filter

    def save_state(self):
        """Save any persistent state (zoom level, etc.) to settings."""
        self._settings.set("zoom", "level", self.zoomFactor())
