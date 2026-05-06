# Velox — Session Log

*Assembled by Claude · Anthropic, one walk at a time*

---

## Session: May 5, 2026

### What Happened

Started with a simple question — "how hard is it to rebuild the Claude desktop app on Linux?" — and ended up designing a whole app from scratch.

---

### Key Decisions Made

**App concept:** A native Qt6/Python desktop wrapper for claude.ai called **Velox** (Claude + Qt). Replaces the Electron-based Claude Desktop app with something lightweight, stable, and fun.

**What's in scope (v1):**
- QtWebEngine webview pointed at claude.ai
- Persistent login via encrypted cookie store (no more random logouts)
- GPU-accelerated, Wayland-native rendering
- System tray icon with right-click menu
- Global hotkey (Ctrl+Alt+Space) to summon the window
- Domain-locked security (Anthropic domains only, everything else blocked)
- Download management to a dedicated folder
- Focus/zen mode — strips UI to show only conversation content
- Copy-all-code-blocks button
- Manual chat export to markdown
- Auto-running conversation summaries via Anthropic API (Haiku)
- Fun theming (explicitly not brown)
- Modular architecture — every feature is its own swappable file
- RPM and AppImage packaging for installing on other machines
- Easter eggs and personality throughout the code
- Public repo with "Built by Claude" branding prominent

**What's explicitly out of scope (v1):**
- MCP / local file access (too buggy on Linux, not needed)
- Cowork mode (not used)
- Claude Code integration (will learn CLI separately)
- Tabs / multi-conversation UI

**What's on the v2 roadmap:**
- Obsidian vault integration (side panel to paste context)
- KDE Calendar/Akonadi integration (learning reminders, popups)
- Cross-desktop chat sync (Syncthing or git-based)
- Voice chat with playback speed control (2x)
- System-wide Whisper speech-to-text bridge
- MCP bridge (minimal, if needed later)
- Conversation tabs/sidebar
- Search across saved chat exports
- Auto-export all conversations

**v3 dream:** animated talking buddy interface (noted, not touched)

---

### Architecture

Modular Python/Qt6 app. Each feature is its own module. Config via TOML. Secrets via KDE Wallet.

```
velox/
├── main.py
├── app/
│   ├── window.py          # main window, geometry
│   ├── webview.py         # QtWebEngine, GPU flags, permissions
│   ├── security.py        # domain allowlist, request interception
│   ├── cookie_store.py    # encrypted persistent sessions
│   ├── downloads.py       # managed downloads, confirmations
│   ├── tray.py            # KDE system tray
│   ├── hotkeys.py         # global hotkey via D-Bus
│   ├── focus_mode.py      # zen mode, CSS injection
│   ├── code_tools.py      # copy-all-code-blocks
│   ├── chat_export.py     # save conversation to markdown
│   ├── chat_summarizer.py # auto-summary via API
│   ├── theme.py           # swappable TOML themes
│   ├── notifications.py   # KDE desktop notifications
│   ├── settings.py        # config management
│   └── constants.py       # allowed domains, paths, version
├── themes/
├── packaging/
│   ├── build.sh
│   ├── velox.spec
│   ├── velox.desktop
│   ├── appimage/
│   └── icons/
├── config/
└── tests/
```

---

### Build Order

| Phase | What | Milestone |
|---|---|---|
| Phase 1 | Skeleton, webview, window, security, cookies | Working secure chat window |
| Phase 2 | Tray, hotkeys, downloads, notifications, theme | Feels like a real app |
| Phase 3 | Focus mode, code tools, chat export, summarizer | Better than Electron app |
| Phase 4 | Polish, more themes, testing, RPM/AppImage packaging | Installable anywhere |

---

### Technical Notes

- **GPU acceleration:** enabled via `--enable-gpu-rasterization`, `--enable-features=VaapiVideoDecoder`, `--ozone-platform=wayland`
- **Wayland hotkeys:** KDE D-Bus global shortcuts interface, not X11 grab
- **Tray icon:** `QSystemTrayIcon` using StatusNotifierItem protocol (KDE native)
- **Cookie encryption:** KDE Wallet / libsecret integration
- **Chat summaries:** Haiku model via Anthropic API, triggered after 30s pause, API key stored in KDE Wallet
- **Web connectors:** Canva, GitHub, Hugging Face all work for free through the webview (server-side OAuth)
- **Voice input:** claude.ai's built-in mic button should work with mic permissions auto-granted
- **No cache:** all QtWebEngine caching disabled for privacy

---

### Security Model

- Allowlist-only networking (Anthropic domains + OAuth endpoints)
- Encrypted cookie store, `700` permissions on config dir
- No local cache of chat content
- Chromium sandbox stays on
- No silent downloads
- API keys in KDE Wallet, never plaintext
- Public repo scrubbed — no personal paths, no secrets, `.gitignore` covers runtime data

---

### Branding

- **Prominent:** "Built by Claude · Anthropic" — README header, code headers, about dialog, console banner
- **Subtle:** "Conceived and designed by Geoff Love · Phoenix, AZ" — small print in README and about dialog
- **Public repo** on GitHub — portfolio piece
- **License:** MIT (TBD, to be added)

---

### Fun Stuff

- Rotating Easter egg taglines in about dialog
- Personality in code comments and error messages
- First-launch welcome toast
- Rotating tray icon tooltips
- ASCII art startup banner in console
- Multiple non-brown themes shipping by default

---

### Open Items / Next Steps

- [ ] Geoff: create GitHub repo (public, `velox` or `velox-desktop`)
- [ ] Geoff: set up Python venv with dependencies
- [ ] Geoff: `sudo dnf install qt6-qtwebengine` if not already present
- [ ] Geoff: design icon in Canva (spec in the planning doc)
- [ ] Claude: build Phase 1 when repo is ready
- [ ] Decide on MIT license (or alternative)
- [ ] Test claude.ai voice input mic button in QtWebEngine
- [ ] Identify exact CDN domains needed for allowlist during testing

---

*This file updates each session. Drop it into the next chat for instant context.*
