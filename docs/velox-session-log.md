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
│   ├── window.py          # main window, geometry, close-to-tray
│   ├── webview.py         # QtWebEngine, GPU flags, permissions
│   ├── security.py        # domain allowlist, request interception
│   ├── cookie_store.py    # persistent sessions (base64 encoded)
│   ├── downloads.py       # managed downloads, notifications
│   ├── tray.py            # KDE system tray, right-click menu
│   ├── notifications.py   # KDE desktop notifications
│   ├── theme.py           # swappable TOML themes (not brown)
│   ├── hotkeys.py         # global hotkey via D-Bus (deferred)
│   ├── focus_mode.py      # zen mode, CSS injection
│   ├── code_tools.py      # copy-all-code-blocks
│   ├── chat_export.py     # save conversation to markdown
│   ├── chat_summarizer.py # auto-summary via API
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
| Phase 2 | Tray, downloads, notifications, theme | ✅ Built, testing |
| Phase 3 | Focus mode, code tools, chat export, summarizer | ⏳ Next |
| Phase 4 | Polish, testing, RPM/AppImage packaging | ⏳ Planned |

**Deferred:** Global hotkeys (Geoff doesn't use many hotkeys, will add later if wanted)

---

### Technical Notes

- **GPU acceleration:** enabled via `--enable-gpu-rasterization`, `--enable-features=VaapiVideoDecoder`, `--enable-wayland-ime`
- **Wayland:** handled by Qt's own platform plugin, NOT Chromium's `--ozone-platform` flag (crashes on Fedora's QtWebEngine build — learned this the hard way)
- **Tray icon:** `QSystemTrayIcon` using StatusNotifierItem protocol (KDE native), placeholder generated programmatically until Canva icon is finalized
- **Cookie encoding:** base64 with 600 file permissions; real Fernet encryption planned for v2
- **Chat summaries:** Haiku model via Anthropic API, triggered after 30s pause, API key stored in KDE Wallet
- **Web connectors:** Canva, GitHub, Hugging Face all work for free through the webview (server-side OAuth)
- **Voice input:** claude.ai's built-in mic button should work with mic permissions auto-granted
- **No cache:** all QtWebEngine caching disabled for privacy
- **Chats:** still saved on Anthropic's servers (cloud). Local chat saving is Phase 3.
- **Close-to-tray:** clicking X hides the window, app stays running in tray. "Quit" in tray menu actually exits.
- **Themes:** 4 built-in (Velox Blue, Midnight, Desert Escape, Aurora). Custom TOML themes supported in `themes/` directory.

---

### Security Model

- Allowlist-only networking (Anthropic domains + Cloudflare + OAuth endpoints)
- Base64-encoded cookie store, `600` file permissions, `700` directory permissions
- No local cache of chat content
- Chromium sandbox stays on
- No silent downloads — all go to `~/Downloads/Velox/` with notifications
- API keys in KDE Wallet, never plaintext
- Public repo scrubbed — no personal paths, no secrets, `.gitignore` covers runtime data

---

### Branding

- **Prominent:** "Built by Claude · Anthropic" — README header, code headers, about dialog, console banner
- **Subtle:** "Conceived and designed by Geoff Love · Phoenix, AZ" — small print in README and about dialog
- **Public repo** on GitHub: https://github.com/Zenithbach/velox
- **License:** MIT

---

## Session 2: May 6, 2026

### What Happened

Built and successfully launched Phase 1. Velox is alive.

### Bugs Fixed During First Launch

1. **Crash on startup:** `--ozone-platform=wayland` flag caused `FATAL` error. Fix: removed the flag, let Qt handle Wayland natively.

2. **Cloudflare security block:** Domain filter blocking `challenges.cloudflare.com`. Fix: added `*.cloudflare.com`, `*.cloudflareinsights.com`, `*.turnstile.com` to allowlist.

3. **No other domains blocked** after Cloudflare fix — allowlist is clean.

### Code Review Findings

- Removed unused imports across 5 files
- Honest naming: cookie "encryption" → "encoding" (base64, not real crypto)
- Removed no-op code block in main.py

### Confirmed Working

- ✅ Window launches, claude.ai loads fully
- ✅ Login via Google OAuth works
- ✅ Persistent cookies — second launch stays logged in
- ✅ Config file created on first run
- ✅ Window geometry saved/restored
- ✅ Graceful shutdown, clean terminal output

---

## Session 3: May 9, 2026

### What Happened

Built Phase 2 (tray, downloads, notifications, theming). Explored icon designs in Canva. Deferred hotkeys module.

### Phase 2 Modules Built

1. **tray.py** — System tray with right-click menu (Show/Hide, Reload, Log Out, Quit). Left-click toggles window. Rotating fun tooltips. Programmatic placeholder icon. Searches for real icon at `packaging/icons/velox-256.png` and `~/.config/velox/icon.png`.

2. **downloads.py** — Intercepts download requests, routes to `~/Downloads/Velox/`. Terminal logs + desktop notifications on complete/fail.

3. **notifications.py** — KDE desktop notifications via tray icon. Fires on download complete, response complete (when alt-tabbed). Config toggles respected.

4. **theme.py** — 4 built-in themes as dataclasses. Qt palette + stylesheet applied to app chrome. Custom TOML theme files supported. Does NOT touch claude.ai content CSS.

### Updated Modules

5. **main.py** — Wires Phase 2 modules. `setQuitOnLastWindowClosed(False)` for tray persistence. Theme applied before widget creation.

6. **window.py** — Close-to-tray: X hides window, tray keeps app alive. `set_tray()` connects window to tray. `_force_quit` flag for real quit vs hide.

### Icon Design

- Explored portal/doorway, V-as-portal, butterfly/swift concepts in Canva
- Geoff's manual Image 3 (rounded square blue portal) was strongest
- Not finalized — will iterate later, placeholder icon works for now

### Deferred

- **hotkeys.py** — Geoff doesn't use many hotkeys. Will add standalone later if wanted.

### Testing Checklist

- [ ] Close window (X) → hides to tray, not quit
- [ ] Left-click tray → window reappears
- [ ] Right-click tray → themed menu
- [ ] Hover tray → random fun tooltip
- [ ] Download file → lands in `~/Downloads/Velox/` with notification
- [ ] Switch theme in config → colors change on restart
- [ ] Ctrl+Q → actually quits

### Open Items / Next Steps

- [ ] Geoff: deploy and test Phase 2
- [ ] Geoff: commit Phase 2 to repo
- [ ] Geoff: finalize icon in Canva (not blocking)
- [ ] Claude: build Phase 3 (focus mode, code tools, chat export, summarizer)
- [ ] Investigate: Fernet encryption for cookie store (v2)

---

*This file updates each session. Drop it into the next chat for instant context.*

---

*Made by Claude · Anthropic with unreasonable care*
