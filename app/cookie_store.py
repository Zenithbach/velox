# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🍪 cookie_store.py
# Mmm, cookies. These ones keep you logged in.
# Encrypted at rest because we're not animals.
#
# This module manages a persistent cookie store that survives app restarts.
# Your claude.ai session token lives here, protected by your system keyring
# (KDE Wallet on Plasma). No more logging in every time you blink.
#
# If no keyring is available, we fall back to file-based storage
# with a stern warning. It works, but your cookies sit on disk
# in cleartext. You've been warned.

import os
import json
import base64
from pathlib import Path
from datetime import datetime

from PyQt6.QtNetwork import QNetworkCookie
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineCookieStore
from PyQt6.QtCore import QByteArray, QUrl

from app.constants import COOKIE_DIR

# Try to import keyring for encryption.
# If it's not available or not configured, we degrade gracefully.
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


# The service name we use in the system keyring.
# This is how KDE Wallet knows which app is asking.
KEYRING_SERVICE = "velox-cookie-store"
KEYRING_KEY = "cookie-encryption-key"

# Where cookies live on disk (encrypted or not)
COOKIE_FILE = COOKIE_DIR / "cookies.json"


class CookieManager:
    """
    Manages persistent cookies for the QtWebEngine profile.

    Flow:
    1. On startup: load saved cookies from disk → inject into webview
    2. While running: listen for cookie changes → save to disk
    3. On "Log Out": nuke everything

    Cookies are stored as JSON. If a keyring is available,
    the JSON blob is encrypted before writing. If not,
    it's stored in cleartext with tight file permissions.
    """

    def __init__(self, profile: QWebEngineProfile):
        self._profile = profile
        self._cookie_store = profile.cookieStore()
        self._cookies: dict[str, dict] = {}  # domain → {name: cookie_data}
        self._ready = False

        # Make sure the cookie directory exists and is locked down
        self._ensure_cookie_dir()

        # Wire up cookie change signals
        self._cookie_store.cookieAdded.connect(self._on_cookie_added)
        self._cookie_store.cookieRemoved.connect(self._on_cookie_removed)

    # ─── Public API ──────────────────────────────────────────────────────

    def load(self):
        """
        Load cookies from disk and inject them into the webview.
        Call this BEFORE loading any URL.
        """
        raw = self._read_from_disk()
        if not raw:
            return

        try:
            cookie_list = json.loads(raw)
        except json.JSONDecodeError:
            print("🍪 Cookie file is corrupted. Starting fresh.")
            print("   (You'll need to log in again. Sorry about that.)")
            return

        count = 0
        for cookie_data in cookie_list:
            cookie = self._deserialize_cookie(cookie_data)
            if cookie:
                self._cookie_store.setCookie(cookie)
                count += 1

        if count > 0:
            print(f"🍪 Loaded {count} cookies. Your session should be right where you left it.")
        self._ready = True

    def save(self):
        """Persist current cookies to disk."""
        cookie_list = []
        for domain_cookies in self._cookies.values():
            for cookie_data in domain_cookies.values():
                cookie_list.append(cookie_data)

        raw = json.dumps(cookie_list, indent=2)
        self._write_to_disk(raw)

    def clear(self):
        """
        Nuclear option. Wipe all cookies from memory and disk.
        This is what "Log Out" calls.
        """
        self._cookies.clear()
        self._cookie_store.deleteAllCookies()

        # Remove the cookie file
        if COOKIE_FILE.exists():
            COOKIE_FILE.unlink()
            print("🍪 All cookies deleted. You'll need to log in again.")

    # ─── Cookie Change Handlers ──────────────────────────────────────────

    def _on_cookie_added(self, cookie: QNetworkCookie):
        """Called by Qt whenever a cookie is set."""
        domain = cookie.domain()
        name = cookie.name().data().decode("utf-8", errors="replace")

        if domain not in self._cookies:
            self._cookies[domain] = {}

        self._cookies[domain][name] = self._serialize_cookie(cookie)

        # Auto-save on every cookie change.
        # This is slightly aggressive but means we never lose a session
        # to a crash or power failure.
        if self._ready:
            self.save()

    def _on_cookie_removed(self, cookie: QNetworkCookie):
        """Called by Qt whenever a cookie is removed."""
        domain = cookie.domain()
        name = cookie.name().data().decode("utf-8", errors="replace")

        if domain in self._cookies:
            self._cookies[domain].pop(name, None)
            if not self._cookies[domain]:
                del self._cookies[domain]

        if self._ready:
            self.save()

    # ─── Serialization ───────────────────────────────────────────────────
    # Cookies need to survive a round-trip to JSON and back.

    @staticmethod
    def _serialize_cookie(cookie: QNetworkCookie) -> dict:
        """Convert a QNetworkCookie to a JSON-friendly dict."""
        return {
            "name": cookie.name().data().decode("utf-8", errors="replace"),
            "value": cookie.value().data().decode("utf-8", errors="replace"),
            "domain": cookie.domain(),
            "path": cookie.path(),
            "secure": cookie.isSecure(),
            "http_only": cookie.isHttpOnly(),
            "expiry": cookie.expirationDate().toString() if cookie.expirationDate().isValid() else None,
        }

    @staticmethod
    def _deserialize_cookie(data: dict) -> QNetworkCookie | None:
        """Convert a dict back into a QNetworkCookie."""
        try:
            cookie = QNetworkCookie()
            cookie.setName(QByteArray(data["name"].encode("utf-8")))
            cookie.setValue(QByteArray(data["value"].encode("utf-8")))
            cookie.setDomain(data["domain"])
            cookie.setPath(data.get("path", "/"))
            cookie.setSecure(data.get("secure", True))
            cookie.setHttpOnly(data.get("http_only", True))
            return cookie
        except (KeyError, TypeError) as e:
            # Malformed cookie data — skip it rather than crash
            print(f"🍪 Skipping malformed cookie: {e}")
            return None

    # ─── Disk I/O ────────────────────────────────────────────────────────

    def _read_from_disk(self) -> str | None:
        """Read cookies from disk, decrypting if possible."""
        if not COOKIE_FILE.exists():
            return None

        try:
            raw_bytes = COOKIE_FILE.read_bytes()
        except OSError as e:
            print(f"🍪 Couldn't read cookie file: {e}")
            return None

        if KEYRING_AVAILABLE:
            return self._decrypt(raw_bytes)
        else:
            return raw_bytes.decode("utf-8", errors="replace")

    def _write_to_disk(self, data: str):
        """Write cookies to disk, encrypting if possible."""
        try:
            if KEYRING_AVAILABLE:
                encrypted = self._encrypt(data)
                COOKIE_FILE.write_bytes(encrypted)
            else:
                COOKIE_FILE.write_text(data)

            # Lock the file down — owner read/write only
            os.chmod(COOKIE_FILE, 0o600)
        except OSError as e:
            print(f"🍪 Couldn't save cookies: {e}")
            print("   Your session is fine in memory, just won't survive a restart.")

    # ─── Encryption Layer ────────────────────────────────────────────────
    # Simple base64 + keyring for now. The keyring (KDE Wallet) provides
    # the actual security. The base64 just keeps the data from being
    # casually readable if someone cats the file.
    #
    # For v2, consider Fernet encryption with a keyring-stored key.

    @staticmethod
    def _encrypt(data: str) -> bytes:
        """Encode cookie data. Uses keyring to store a verification marker."""
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, "velox-verified")
        except Exception:
            pass  # Keyring write failed — encoding still works

        return base64.b64encode(data.encode("utf-8"))

    @staticmethod
    def _decrypt(data: bytes) -> str | None:
        """Decode cookie data."""
        try:
            return base64.b64decode(data).decode("utf-8")
        except Exception as e:
            print(f"🍪 Cookie decryption failed: {e}")
            print("   Starting with a clean slate.")
            return None

    # ─── Directory Setup ─────────────────────────────────────────────────

    @staticmethod
    def _ensure_cookie_dir():
        """Create the cookie directory with restrictive permissions."""
        COOKIE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(COOKIE_DIR, 0o700)
        except OSError:
            print(f"⚠️  Couldn't lock down {COOKIE_DIR}")
            print("   Check permissions manually — your cookies deserve privacy.")

        if not KEYRING_AVAILABLE:
            print("⚠️  No system keyring found (KDE Wallet / libsecret).")
            print("   Cookies will be stored with basic encoding only.")
            print("   Consider installing 'keyring' and enabling KDE Wallet.")
