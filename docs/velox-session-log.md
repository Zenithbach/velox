# Velox — Session Log

*Assembled by Claude · Anthropic, one walk at a time*

---

## Session 1: May 5, 2026

### What Happened

Started with "how hard is it to rebuild the Claude desktop app on Linux?" — ended up designing a whole app from scratch.

### Key Decisions

- **App concept:** Native Qt6/Python wrapper for claude.ai called **Velox** (Latin: swift)
- **Naming journey:** Claudette → trademark concern → Nimbus → taken → Velox
- **Architecture:** Modular, one module per feature, TOML config, KDE Wallet for secrets
- **MCP excluded:** Too buggy on Linux, not needed
- **Public repo:** https://github.com/Zenithbach/velox with MIT license
- **Branding:** "Built by Claude" prominent, "Designed by Geoff Love" subtle

---

## Session 2: May 6, 2026

### What Happened

Built and launched Phase 1. Two bugs fixed on first run.

### Bugs Fixed

1. `--ozone-platform=wayland` crashes Fedora's QtWebEngine → removed, let Qt handle Wayland natively
2. Cloudflare domains missing from allowlist → added `*.cloudflare.com`, `*.cloudflareinsights.com`, `*.turnstile.com`

### Confirmed Working

✅ Window launches, claude.ai loads, OAuth login works, persistent cookies survive restart, config created, geometry saved, clean shutdown

---

## Session 3: May 9, 2026

### What Happened

Built Phase 2 (tray, downloads, notifications, theming). Explored icon designs. Deferred hotkeys.

### Modules Built

- **tray.py** — system tray with right-click menu, rotating tooltips, placeholder icon
- **downloads.py** — managed downloads to `~/Downloads/Velox/` with notifications
- **notifications.py** — KDE desktop notifications via tray
- **theme.py** — 4 built-in themes (Velox Blue, Midnight, Desert Escape, Aurora)
- **main.py / window.py** — updated for close-to-tray behavior

### Decisions

- Hotkeys deferred (Geoff doesn't use many, Wayland D-Bus complexity not worth it yet)
- Icon not finalized — Geoff's Image 3 (blue portal) is leading candidate, placeholder works for now
- Set up direnv for automatic venv activation

---

## Session 4: May 10, 2026

### What Happened

Built Phase 3 — the killer feature phase. Focus mode, code tools, chat export, auto-summarizer.

| Time | Topic | Note |
|------|-------|------|
| ~8:30 PM | Phase 3 build | All 4 modules built, wired into main/window/tray |
| ~9:00 PM | Deployed and tested | Velox running Phase 3, chat export confirmed working |
| ~9:00 PM | Browser error persists | "Previous message wasn't sent" appears in Velox too — confirmed Anthropic server-side issue |
| ~9:15 PM | Code review | Removed 2 unused Path imports, all 16 files clean |
| ~9:15 PM | VPN discussion | Proton VPN causes issues with claude.ai, split tunnel considered |

### Phase 3 Modules Built

1. **focus_mode.py** — F11 toggles zen mode. CSS injection hides sidebar, nav, header. Escape exits. Blue border indicator.
2. **code_tools.py** — Ctrl+Shift+C copies all code blocks from conversation to clipboard, labeled by language.
3. **chat_export.py** — Ctrl+S saves current conversation as markdown to `~/Documents/Claude-Chats/`.
4. **chat_summarizer.py** — Watches for 30s conversation pause, calls Haiku API for topic summaries, appends to running markdown files in `~/Documents/Claude-Chats/summaries/`. Needs `ANTHROPIC_API_KEY` env var or keyring entry.

### Updated Modules

- **main.py** — wires all Phase 3 modules
- **window.py** — `set_phase3()` method, F11/Escape/Ctrl+S/Ctrl+Shift+C shortcuts
- **tray.py** — Focus Mode, Save Chat, Copy All Code in right-click menu

### Key Finding

"Previous message wasn't sent" error confirmed as Anthropic server-side — appears identically in Velox (Qt/custom network stack) and browser. Not a client issue.

### VPN Note

Proton VPN triggers claude.ai's bot detection / Cloudflare challenges. Split tunnel (exclude claude.ai from VPN) is the pragmatic fix. Annoying but workable.

### Code Review

- 16 files, 2,831 lines, 90 easter eggs
- 2 unused `Path` imports removed (chat_export.py, chat_summarizer.py)
- Zero personal info, zero hardcoded paths
- All files pass syntax check

### Project Stats

| Metric | Value |
|--------|-------|
| Total files | 16 Python + README + LICENSE + .gitignore + requirements.txt |
| Total lines | 2,831 |
| Easter eggs | 90 |
| Themes | 4 |
| Phases complete | 3 of 4 |
| Sessions | 4 |
| Days elapsed | 5 |

---

### Build Order

| Phase | What | Status |
|---|---|---|
| Phase 1 | Skeleton, webview, window, security, cookies | ✅ Complete |
| Phase 2 | Tray, downloads, notifications, theme | ✅ Complete |
| Phase 3 | Focus mode, code tools, chat export, summarizer | ✅ Complete |
| Phase 4 | Polish, testing, RPM/AppImage packaging | ⏳ Next |

### Open Items

- [ ] Geoff: commit Phase 3 cleanup to repo
- [ ] Geoff: set up Anthropic API key for summarizer
- [ ] Geoff: test focus mode (F11), chat export (Ctrl+S), code copy (Ctrl+Shift+C)
- [ ] Geoff: configure Proton VPN split tunnel for claude.ai
- [ ] Geoff: finalize icon in Canva
- [ ] Claude: build Phase 4 (polish, testing, RPM/AppImage packaging)
- [ ] v2: Fernet encryption for cookie store
- [ ] v2: Obsidian vault integration

---

*This file updates each session. Drop it into the next chat for instant context.*

---

*Claude · Anthropic was here*
