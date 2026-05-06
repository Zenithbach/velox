# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 📐 constants.py
# The foundation stones. Paths, domains, version numbers.
# If it's hardcoded and shared, it lives here.
# Change these and everything downstream follows. That's the idea.

import os
from pathlib import Path

# ─── Identity ────────────────────────────────────────────────────────────────

APP_NAME = "Velox"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "A window to Claude. Nothing more, nothing less."
APP_URL = "https://github.com/Zenithbach/velox"

# The thing we're wrapping. The whole reason we're here.
CLAUDE_URL = "https://claude.ai"

# ─── Paths ───────────────────────────────────────────────────────────────────
# Everything derives from XDG-ish conventions.
# No hardcoded /home/whoever nonsense. Ever.

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "velox"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "velox"
COOKIE_DIR = CONFIG_DIR / "cookies"
CONFIG_FILE = CONFIG_DIR / "velox.toml"

# Where your chats and summaries land
CHAT_EXPORT_DIR = Path.home() / "Documents" / "Claude-Chats"
SUMMARY_DIR = CHAT_EXPORT_DIR / "summaries"

# Downloads — not your browser's junk drawer
DOWNLOAD_DIR = Path.home() / "Downloads" / "Velox"

# ─── Security: The Guest List ────────────────────────────────────────────────
# If a domain isn't here, it doesn't get through. Period.
# We'll discover CDN domains during testing and add them.
# OAuth endpoints are included so web connectors (Canva, GitHub, etc.) work.

ALLOWED_DOMAINS = [
    # Core — the whole reason this app exists
    "claude.ai",
    "*.claude.ai",
    "*.anthropic.com",

    # Cloudflare — claude.ai sits behind Cloudflare for DDoS/bot protection.
    # Without these, you get stuck on "Performing security verification" forever.
    # Learned this the fun way on first launch. 🎉
    "*.cloudflare.com",
    "challenges.cloudflare.com",
    "*.cloudflareinsights.com",
    "*.turnstile.com",           # Cloudflare's CAPTCHA alternative

    # CDN / static assets (claude.ai frontend dependencies)
    "cdn.claude.ai",
    "*.cloudfront.net",          # AWS CloudFront — commonly used for static assets
    "*.googleapis.com",          # Google Fonts, APIs
    "*.gstatic.com",             # Google static content

    # OAuth — so your web connectors keep working
    # These only fire when YOU initiate a login flow
    "github.com",
    "*.github.com",
    "accounts.google.com",
    "*.canva.com",
    "huggingface.co",
    "*.huggingface.co",

    # Sentry / telemetry from claude.ai itself
    # (we can't strip these without breaking the frontend)
    "*.sentry.io",
    "*.ingest.sentry.io",
]

# Domains we NEVER allow, even if they match a wildcard above
# (paranoia layer — belt AND suspenders)
BLOCKED_DOMAINS = [
    "*.doubleclick.net",
    "*.googlesyndication.com",
    "*.googleadservices.com",
    "*.facebook.com",
    "*.meta.com",
    "*.tiktok.com",
]

# ─── User Agent ──────────────────────────────────────────────────────────────
# We pretend to be a normal browser so claude.ai doesn't gate features.
# This is a real Chrome on Linux user-agent string.
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# ─── Fun Stuff ───────────────────────────────────────────────────────────────
# Because life is too short for boring software.

STARTUP_BANNER = """
  ╔═══════════════════════════════════════╗
  ║  🦋 Velox                             ║
  ║  Built by Claude · Anthropic          ║
  ║  Not an Electron in sight             ║
  ╚═══════════════════════════════════════╝
"""

WELCOME_TOAST = (
    "Hey! I'm Velox. I'm like the other Claude app, "
    "but I don't eat your RAM for breakfast. 🦋"
)

TRAY_TOOLTIPS = [
    "Velox · Waiting patiently",
    "Velox · Not consuming 400MB of RAM right now",
    "Velox · Still not brown",
    "Velox · Lighter than your lightest browser tab",
    "Velox · Zero Electron atoms present",
    "Velox · 🌵 Desert-tested. Adobe-free.",
]

ABOUT_TAGLINES = [
    "Claude was here. And here. And also here.",
    "Zero Electron atoms were harmed in the making of this app.",
    "Not brown since 2026.",
    "Lighter than your lightest browser tab.",
    "I'm not saying Electron is heavy, but...",
    "🌵 Desert-tested. Adobe-free.",
    "Latin for swift. And we meant it.",
]

# ─── Default Config ──────────────────────────────────────────────────────────
# These are the sane defaults that get written on first launch.
# The actual config file is velox.toml — this is just the template.

DEFAULT_CONFIG = {
    "window": {
        "width": 1200,
        "height": 800,
        "x": -1,            # -1 means "let the WM decide"
        "y": -1,
        "start_minimized": False,
    },
    "security": {
        "log_blocked_requests": False,
    },
    "downloads": {
        "directory": str(DOWNLOAD_DIR),
    },
    "tray": {
        "enabled": True,
    },
    "hotkeys": {
        "toggle_window": "Ctrl+Alt+Space",
        "focus_mode": "F11",
        "save_chat": "Ctrl+S",
    },
    "focus_mode": {
        "hide_input_box": False,
    },
    "summarizer": {
        "enabled": True,
        "delay_seconds": 30,
        "model": "claude-haiku-4-5-20251001",
    },
    "theme": {
        "active": "default",
        "follow_system_theme": False,
    },
    "notifications": {
        "on_response_complete": True,
        "on_download_complete": True,
        "on_summary_update": False,
    },
    "zoom": {
        "level": 1.0,
    },
}
