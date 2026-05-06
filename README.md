# Velox

### Built by Claude · Anthropic

A lightweight, native Qt6/Python desktop app for claude.ai.
No Electron. No bloat. Not brown.

---

## What is this?

Velox is a dedicated desktop wrapper for [claude.ai](https://claude.ai) built with PyQt6 and QtWebEngine. It replaces the Electron-based Claude Desktop app with something that:

- **Stays logged in** — persistent, encrypted cookie storage means no more random logouts
- **Doesn't eat your RAM** — it's a Qt window, not a Chromium instance pretending to be an app inside another Chromium instance
- **Runs natively on Wayland** — GPU-accelerated, no XWayland translation layer
- **Locks down your data** — allowlist-only networking, no trackers, no cache on disk
- **Has personality** — because life is too short for boring software

## Status

🚧 **Phase 1** — Core functionality. Working secure chat window with persistent login.

See [docs/velox-spec.md](docs/velox-spec.md) for the full feature spec and build roadmap.

## Quick Start

```bash
# Clone
git clone git@github.com:Zenithbach/velox.git
cd velox

# Set up environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Make sure Qt6 WebEngine is available
sudo dnf install qt6-qtwebengine   # Fedora
# sudo apt install python3-pyqt6.qtwebengine   # Debian/Ubuntu

# Run
python main.py
```

## Target Environment

Built and tested on:
- Fedora Linux 44
- KDE Plasma 6.6.4 on Wayland
- Python 3.12+

Should work on any Linux with Qt6 and Wayland/X11, but that's where it lives day-to-day.

## Architecture

Modular by design. Every feature is its own file. Swap, remove, or extend without touching the rest.

```
velox/
├── main.py              # Entry point
├── app/
│   ├── window.py        # Main window management
│   ├── webview.py       # QtWebEngine + permissions
│   ├── security.py      # Domain allowlist filtering
│   ├── cookie_store.py  # Encrypted persistent sessions
│   ├── settings.py      # TOML config management
│   └── constants.py     # Paths, domains, version info
└── docs/
    ├── velox-spec.md          # Full feature specification
    └── velox-session-log.md   # Design session notes
```

## Security

- **Allowlist-only networking** — only Anthropic domains and OAuth endpoints get through
- **Encrypted cookie store** — session tokens protected by KDE Wallet / libsecret
- **Zero cache** — no chat content stored on disk outside of your explicit exports
- **Chromium sandbox** — process isolation stays enabled
- **No silent downloads** — every file download triggers a notification

## Roadmap

| Phase | What | Status |
|---|---|---|
| Phase 1 | Core window, security, persistent login | 🔨 In progress |
| Phase 2 | Tray icon, hotkeys, downloads, notifications, theming | ⏳ Planned |
| Phase 3 | Focus mode, code tools, chat export, auto-summaries | ⏳ Planned |
| Phase 4 | Polish, testing, RPM/AppImage packaging | ⏳ Planned |

## About

This project demonstrates what a non-coder can build by collaborating with Claude — from planning through architecture through implementation. The code is Claude's. The vision, requirements, and design decisions are Geoff's. Both matter.

---

*Conceived and designed by Geoff Love · Phoenix, AZ*

*Latin: swift. And we meant it.*
