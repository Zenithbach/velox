# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🔒 security.py
# The bouncer at the door. If your domain isn't on the list,
# you're not getting in. Nothing personal.
#
# This module intercepts EVERY network request the webview makes
# and checks it against our allowlist. No exceptions, no "just this once,"
# no "but it looked trustworthy." If you paste an API key into a chat,
# it's not leaking to some random analytics endpoint. Not on our watch.

import fnmatch
from urllib.parse import urlparse

from PyQt6.QtWebEngineCore import (
    QWebEngineUrlRequestInterceptor,
    QWebEngineUrlRequestInfo,
)

from app.constants import ALLOWED_DOMAINS, BLOCKED_DOMAINS


class DomainFilter(QWebEngineUrlRequestInterceptor):
    """
    Intercepts every network request and blocks anything
    that isn't on the guest list.

    Uses fnmatch for wildcard domain matching because
    regex for URL filtering is how you get CVEs.
    """

    def __init__(self, log_blocked: bool = False, parent=None):
        super().__init__(parent)
        self._log_blocked = log_blocked

        # Pre-process the lists so we're not doing it on every request.
        # Lowercase everything because domains are case-insensitive
        # and we don't want "Evil.Tracker.COM" sneaking past.
        self._allowed = [d.lower() for d in ALLOWED_DOMAINS]
        self._blocked = [d.lower() for d in BLOCKED_DOMAINS]

    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """
        Called for EVERY request. Yes, every single one.
        Images, scripts, fonts, websockets, the lot.

        If the domain isn't allowed → blocked.
        If the domain IS allowed but also in the block list → blocked.
        Belt AND suspenders.
        """
        url = info.requestUrl()
        host = url.host().lower()

        # Step 1: Is it explicitly blocked? (Takes priority over everything)
        if self._matches_any(host, self._blocked):
            info.block(True)
            if self._log_blocked:
                print(f"🚫 Blocked (explicit): {host} — {url.toString()}")
            return

        # Step 2: Is it on the guest list?
        if self._matches_any(host, self._allowed):
            # Welcome in. 🎉
            return

        # Step 3: Not on any list → blocked by default.
        # This is the "deny by default" philosophy.
        # Better to break a CDN asset than leak your session token.
        info.block(True)
        if self._log_blocked:
            print(f"🚫 Nope. Not on the guest list: {host} — {url.toString()}")

    def set_logging(self, enabled: bool):
        """Toggle request logging. Useful for debugging the allowlist."""
        self._log_blocked = enabled
        state = "ON 🔍" if enabled else "OFF"
        print(f"   Security logging: {state}")

    # ─── Internal ────────────────────────────────────────────────────────

    @staticmethod
    def _matches_any(host: str, patterns: list[str]) -> bool:
        """
        Check if a hostname matches any pattern in the list.
        Supports wildcards like *.anthropic.com.

        We check both the exact host and with a leading dot
        so that "cdn.claude.ai" matches "*.claude.ai".
        """
        for pattern in patterns:
            if fnmatch.fnmatch(host, pattern):
                return True
            # Also check if the pattern without the wildcard prefix
            # matches as a suffix. This catches subdomains more reliably.
            if pattern.startswith("*."):
                suffix = pattern[1:]  # ".anthropic.com"
                if host.endswith(suffix) or host == pattern[2:]:
                    return True
        return False


def check_domain(url_string: str) -> bool:
    """
    Convenience function for testing. Pass a URL string,
    get back True if it would be allowed, False if blocked.

    Usage:
        >>> check_domain("https://claude.ai/chat/123")
        True
        >>> check_domain("https://evil-tracker.com/pixel.gif")
        False
    """
    parsed = urlparse(url_string)
    host = parsed.hostname or ""
    host = host.lower()

    # Check blocked first
    allowed = [d.lower() for d in ALLOWED_DOMAINS]
    blocked = [d.lower() for d in BLOCKED_DOMAINS]

    if DomainFilter._matches_any(host, blocked):
        return False
    return DomainFilter._matches_any(host, allowed)
