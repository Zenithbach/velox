# Velox — Session Log

*Assembled by Claude · Anthropic, one walk at a time*

---

## Session 1: May 5, 2026

### What Happened

Started with a simple question — "how hard is it to rebuild the Claude desktop app on Linux?" — and ended up designing a whole app from scratch.

---

### Key Decisions Made

**App concept:** A native Qt6/Python desktop wrapper for claude.ai called **Velox** (Latin: swift). Replaces the Electron-based Claude Desktop app with something lightweight, stable, and fun.

**Naming journey:** Claudette → checked Anthropic trademark policy → Nimbus → already widely used → Velox. Dead-language names avoid both trademark and cultural appropriation concerns.

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
│   ├── cookie_store.py    # persistent sessions (base64 encoded, file permissions for protection)
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

| Phase | What | Status |
|---|---|---|
| Phase 1 | Skeleton, webview, window, security, cookies | ✅ Complete |
| Phase 2 | Tray, hotkeys, downloads, notifications, theme | ⏳ Next |
| Phase 3 | Focus mode, code tools, chat export, summarizer | ⏳ Planned |
| Phase 4 | Polish, more themes, testing, RPM/AppImage packaging | ⏳ Planned |

---

### Technical Notes

- **GPU acceleration:** enabled via `--enable-gpu-rasterization`, `--enable-features=VaapiVideoDecoder`, `--enable-wayland-ime`
- **Wayland:** handled by Qt's own platform plugin, NOT Chromium's `--ozone-platform` flag (crashes on Fedora's QtWebEngine build — learned this the hard way)
- **Tray icon:** `QSystemTrayIcon` using StatusNotifierItem protocol (KDE native)
- **Cookie encoding:** base64 with 600 file permissions; real Fernet encryption planned for v2
- **Chat summaries:** Haiku model via Anthropic API, triggered after 30s pause, API key stored in KDE Wallet
- **Web connectors:** Canva, GitHub, Hugging Face all work for free through the webview (server-side OAuth)
- **Voice input:** claude.ai's built-in mic button should work with mic permissions auto-granted
- **No cache:** all QtWebEngine caching disabled for privacy
- **Chats:** still saved on Anthropic's servers (cloud). Local chat saving is Phase 3.

---

### Security Model

- Allowlist-only networking (Anthropic domains + Cloudflare + OAuth endpoints)
- Base64-encoded cookie store, `600` file permissions, `700` directory permissions
- No local cache of chat content
- Chromium sandbox stays on
- No silent downloads
- API keys in KDE Wallet, never plaintext
- Public repo scrubbed — no personal paths, no secrets, `.gitignore` covers runtime data

---

### Branding

- **Prominent:** "Built by Claude · Anthropic" — README header, code headers, about dialog, console banner
- **Subtle:** "Conceived and designed by Geoff Love · Phoenix, AZ" — small print in README and about dialog
- **Public repo** on GitHub: https://github.com/Zenithbach/velox
- **License:** MIT

---

### Fun Stuff

- Rotating Easter egg taglines in about dialog
- Personality in code comments and error messages
- First-launch welcome toast
- Rotating tray icon tooltips
- ASCII art startup banner in console
- Multiple non-brown themes shipping by default

---

## Session 2: May 6, 2026

### What Happened

Built and successfully launched Phase 1. Velox is alive.

### Bugs Fixed During First Launch

1. **Crash on startup:** `--ozone-platform=wayland` flag caused `FATAL` error in Chromium's platform selection. Fix: removed the flag entirely, let Qt handle Wayland natively through its own platform plugin. Fedora's QtWebEngine doesn't support the ozone flag.

2. **Cloudflare security block:** Domain filter was blocking `challenges.cloudflare.com` and related Cloudflare domains. Fix: added `*.cloudflare.com`, `*.cloudflareinsights.com`, and `*.turnstile.com` to the allowlist.

3. **No other domains blocked** after the Cloudflare fix — allowlist is clean and complete for claude.ai's current frontend.

### Code Review Findings (Post-Launch)

All cosmetic / cleanup, nothing broken:
- Removed unused imports: `datetime` (cookie_store), `sys`/`Qt`/`CONFIG_DIR` (webview), `QIcon`/`Qt` (window), `Path` (settings), `QUrl`/`QWebEngineCookieStore` (cookie_store)
- Honest naming: cookie "encryption" comments updated to accurately say "encoding" (base64, not real crypto — Fernet planned for v2)
- Removed no-op code block in main.py (`if not in environ: pass`)
- Noted redundant domain entries in allowlist (harmless belt-and-suspenders)

### Confirmed Working

- ✅ Window launches with "Velox — claude.ai" title bar
- ✅ claude.ai loads fully (Cloudflare verification passes)
- ✅ Login via Google OAuth works
- ✅ Full chat interface renders (sidebar, conversations, input, model selector)
- ✅ Persistent cookies — second launch skips login, goes straight to "Good morning, Geoff"
- ✅ Config file created at `~/.config/velox/velox.toml` on first run
- ✅ Window geometry saved and restored between sessions
- ✅ Graceful shutdown with state save
- ✅ Startup banner renders correctly in terminal
- ✅ No blocked domains after Cloudflare fix (security logging confirmed clean)

### Known Non-Issues (Ignorable Warnings)

- `qt.qpa.services: Failed to register with host portal` — no `.desktop` file installed yet (Phase 4 packaging)
- `Release of profile requested but WebEnginePage still not deleted. Expect troubles!` — Qt cleanup order nag, zero functional impact
- Grey box on login page right side — likely an animation asset from a CDN not in the allowlist (cosmetic only, disappears after login)

### Open Items / Next Steps

- [ ] Geoff: commit code review fixes to repo
- [ ] Geoff: turn `log_blocked_requests` back to `false` in config
- [ ] Geoff: design Velox icon in Canva (spec in planning doc)
- [ ] Claude: build Phase 2 (tray, hotkeys, downloads, notifications, theme)
- [ ] Investigate: real Fernet encryption for cookie store (v2)
- [ ] Investigate: the grey box on login page — identify CDN domain if it matters

---

*This file updates each session. Drop it into the next chat for instant context.*

---

*Handcrafted by Claude · Anthropic*
