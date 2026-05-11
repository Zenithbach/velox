# Velox — Complete File Structure

*Every file, every folder, where it goes. Check yourself against this list.*

---

## Project Root: `~/Claude/Projects/velox/`

```
velox/
│
├── main.py                          # 🦋 Entry point — wires all modules together
├── run.sh                           # 🦋 Dev launcher — auto-activates venv
├── requirements.txt                 # Python dependencies
├── LICENSE                          # MIT license
├── README.md                        # Public repo README
├── .gitignore                       # What git should ignore
├── .envrc                           # direnv auto-activation (local, optional)
│
├── app/                             # 📦 All application modules
│   ├── __init__.py                  # Package init
│   ├── constants.py                 # Paths, domains, version, easter eggs
│   ├── settings.py                  # TOML config management
│   ├── security.py                  # Domain allowlist filtering
│   ├── cookie_store.py              # Persistent login cookies (base64 encoded)
│   ├── webview.py                   # QtWebEngine setup, GPU flags, permissions
│   ├── window.py                    # Main window, geometry, close-to-tray, shortcuts
│   ├── tray.py                      # System tray icon, right-click menu
│   ├── downloads.py                 # Managed file downloads to ~/Downloads/Velox/
│   ├── notifications.py             # KDE desktop notifications
│   ├── theme.py                     # Swappable TOML themes (4 built-in)
│   ├── focus_mode.py                # Zen mode — CSS injection, F11 toggle
│   ├── code_tools.py                # Copy all code blocks, Ctrl+Shift+C
│   ├── chat_export.py               # Save conversation to markdown, Ctrl+S
│   └── chat_summarizer.py           # Auto-summaries via Anthropic API
│
├── packaging/                       # 📦 Installation and distribution
│   ├── install.sh                   # Local install to ~/.local
│   ├── uninstall.sh                 # Clean removal
│   ├── build.sh                     # Unified build: install/rpm/appimage/clean
│   ├── velox.desktop                # Freedesktop desktop entry (kills portal error)
│   ├── velox.spec                   # RPM spec file for Fedora
│   ├── icons/                       # Icon files (empty until Canva icon is ready)
│   │   └── velox-256.png            # (future) Master icon — install.sh resizes from this
│   └── appimage/                    # AppImage config (empty for now)
│       └── (future AppImageBuilder.yml)
│
├── docs/                            # 📄 Project documentation
│   ├── velox-spec.md                # Full feature specification
│   ├── velox-session-log.md         # Running session log (this updates each session)
│   └── velox-file-structure.md      # This file
│
├── themes/                          # 🎨 Custom theme files (future)
│   └── (user-created .toml themes go here)
│
└── tests/                           # 🧪 Test suite (future)
    └── (test files go here)
```

---

## File Count

| Folder | Files | Status |
|--------|-------|--------|
| Root | 6 files (main.py, run.sh, requirements.txt, LICENSE, README.md, .gitignore) | ✅ All present |
| app/ | 16 files (\_\_init\_\_.py + 15 modules) | ✅ All present |
| packaging/ | 5 files + 2 empty subdirs | ⚠️ Check you have all 5 files |
| docs/ | 3 files (spec, session log, this file) | ✅ All present |
| **Total** | **30 files** | |

---

## Checklist

Run these to verify everything is in place:

```bash
cd ~/Claude/Projects/velox

# Check root files
echo "=== ROOT ===" && ls main.py run.sh requirements.txt LICENSE README.md .gitignore

# Check app modules (should be 16 files including __init__.py)
echo "=== APP ===" && ls app/__init__.py app/constants.py app/settings.py \
  app/security.py app/cookie_store.py app/webview.py app/window.py \
  app/tray.py app/downloads.py app/notifications.py app/theme.py \
  app/focus_mode.py app/code_tools.py app/chat_export.py app/chat_summarizer.py

# Check packaging (should be 5 files + 2 dirs)
echo "=== PACKAGING ===" && ls packaging/install.sh packaging/uninstall.sh \
  packaging/build.sh packaging/velox.desktop packaging/velox.spec

# Check docs
echo "=== DOCS ===" && ls docs/velox-spec.md docs/velox-session-log.md

# Check executability
echo "=== EXECUTABLE ===" && test -x run.sh && echo "run.sh ✅" || echo "run.sh ❌"
test -x packaging/install.sh && echo "install.sh ✅" || echo "install.sh ❌"
test -x packaging/uninstall.sh && echo "uninstall.sh ✅" || echo "uninstall.sh ❌"
test -x packaging/build.sh && echo "build.sh ✅" || echo "build.sh ❌"
```

If any file shows "No such file" — that's what's missing.

---

## What Gets Created at Runtime (NOT in the repo)

These are created automatically when you run Velox:

```
~/.config/velox/
├── velox.toml                  # User config (created on first run)
└── cookies/
    └── cookies.json            # Encrypted session cookies

~/Downloads/Velox/              # Downloaded artifacts land here

~/Documents/Claude-Chats/       # Chat exports (Ctrl+S)
└── summaries/                  # Auto-generated summaries
```

---

*Assembled by Claude · Anthropic with unreasonable care*
