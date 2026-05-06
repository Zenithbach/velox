# **BUILT BY CLAUDE · ANTHROPIC — WITH UNREASONABLE CARE**

---

# Velox — Desktop App Specification

*The Electron-free Claude experience. Light, fast, not brown.*

---

## What This Is

**Velox** is a lightweight, native Qt6/Python desktop app that wraps claude.ai in a dedicated window — replacing the Electron-based Claude Desktop app with something that doesn't eat RAM, doesn't randomly log you out, and doesn't look like the inside of an adobe house.

No MCP. No Cowork. No complexity you don't need. Just a fast, stable, secure, and genuinely fun chat interface with smart features that make long conversations manageable.

## Target Environment

- **OS:** Fedora Linux 44
- **Desktop:** KDE Plasma 6.6.4 on Wayland
- **Hardware:** Framework Laptop 16 — Ryzen AI 9 HX 370, RTX 5070 Laptop, 64 GB RAM
- **Python:** 3.12+ (system or venv)
- **Toolkit:** PyQt6 + QtWebEngine

---

## Architecture

Modular by design. Every feature is its own file, does one thing, can be swapped or removed without breaking the rest.

```
velox/
├── main.py                      # Entry point — tiny, just wires modules together
├── app/
│   ├── __init__.py
│   ├── window.py                # Main window management, show/hide, geometry
│   ├── webview.py               # QtWebEngine setup, permissions, GPU flags
│   ├── security.py              # Domain filtering, request interception
│   ├── cookie_store.py          # Persistent encrypted cookie/session storage
│   ├── downloads.py             # Download handling, confirmations, target directory
│   ├── tray.py                  # System tray icon, right-click menu
│   ├── hotkeys.py               # Global hotkey registration (D-Bus on Wayland)
│   ├── focus_mode.py            # Zen mode — CSS injection to strip UI chrome
│   ├── code_tools.py            # Copy-all-code-blocks, code extraction
│   ├── chat_export.py           # Manual conversation save to markdown
│   ├── chat_summarizer.py       # Auto-generating running summary via API
│   ├── theme.py                 # App theming, colors, swappable palettes
│   ├── notifications.py         # Desktop notifications for completed responses
│   ├── settings.py              # Config management, loads/saves TOML
│   └── constants.py             # Allowed domains, default paths, version info
├── themes/
│   ├── default.toml             # The "not brown" default theme
│   ├── midnight.toml            # Dark/moody option
│   └── desert_escape.toml       # Ironic Arizona counter-programming
├── config/
│   └── velox.toml           # User config (created on first run)
├── tests/
│   ├── test_security.py
│   ├── test_cookie_store.py
│   ├── test_downloads.py
│   └── test_chat_export.py
└── README.md
```

---

## Module Specifications

### 🪟 window.py — Main Window

- Single-window design (no tabs for v1, clean and simple)
- Remembers size, position, and monitor between sessions
- Close-to-tray behavior (window hides, app stays alive)
- Restore on tray click or global hotkey
- KDE window class set properly so Plasma rules work

### 🌐 webview.py — QtWebEngine Core

- Loads `https://claude.ai` in a QtWebEngine view
- GPU acceleration enabled by default:
  - `--enable-gpu-rasterization`
  - `--enable-features=VaapiVideoDecoder`
  - `--ozone-platform=wayland`
- Microphone permission auto-granted (for claude.ai's built-in voice input)
- Camera permission denied by default
- Clipboard access enabled (needed for normal copy/paste)
- JavaScript enabled (required for claude.ai to function)
- Drag-and-drop file uploads supported
- Zoom level persists between sessions
- User-agent string set to match a standard browser so claude.ai doesn't gate features

### 🔒 security.py — Domain Lockdown

**This is the foundation. Everything else sits on top of it.**

- **Allowlist-only networking:** webview can only connect to:
  - `claude.ai`
  - `*.anthropic.com`
  - `*.claude.ai`
  - CDN domains required by the frontend (identified during testing)
  - OAuth endpoints for web connectors (GitHub, Canva, Hugging Face, Google)
- All other requests blocked silently
- No third-party trackers, analytics, or ad networks
- Request interception via `QWebEngineUrlRequestInterceptor`
- Logs blocked requests to a debug file (off by default, toggle in config)

### 🍪 cookie_store.py — Persistent Session Storage

- Custom cookie jar stored at `~/.config/velox/cookies/`
- Directory permissions: `700` (owner-only)
- **Encryption at rest** via KDE Wallet / libsecret integration
  - Session tokens never stored in cleartext on disk
  - Falls back to file-based storage with warning if no keyring available
- Isolated from Brave and all other browsers
- Cookie persistence = no more random logouts
- Option to wipe session from tray menu ("Log Out")

### 📥 downloads.py — Download Handling

- Default download directory: `~/Downloads/velox/` (configurable)
- Desktop notification on download complete
- No silent downloads — every download shows a notification with filename
- "Open folder" action on notification click
- Download history not logged (privacy)

### 🔲 tray.py — System Tray

- Uses `QSystemTrayIcon` (native KDE StatusNotifierItem protocol)
- Custom icon (fun, not boring — designed in theme module)
- Left-click: toggle window visibility
- Right-click menu:
  - Show / Hide Window
  - Focus Mode (toggle)
  - Save Conversation
  - Settings
  - Log Out
  - Quit
- Config toggle: `tray_enabled = true` (kill switch if KDE acts up)

### ⌨️ hotkeys.py — Global Hotkey

- Default: `Ctrl+Alt+Space` (configurable)
- Wayland-compatible via KDE's D-Bus global shortcuts interface
- Toggles window visibility (show/hide + focus)
- Falls back to X11 grab if running under XWayland
- Registers/unregisters cleanly on app start/quit

### 🧘 focus_mode.py — Zen Mode

- Toggled via hotkey (default: `F11` or configurable) or tray menu
- Injects CSS into the webview that hides:
  - Sidebar / conversation list
  - Input box (optional — configurable)
  - Navigation elements
  - Any non-content UI
- Leaves only the conversation content, full-window
- Visual indicator that focus mode is active (subtle border glow or corner badge)
- Second toggle or `Escape` restores full UI
- **Copy All Code Blocks** button appears in focus mode:
  - Extracts every code snippet from the current visible response
  - Copies to clipboard as a single concatenated block with language labels

### 💾 chat_export.py — Manual Conversation Save

- Triggered via hotkey (`Ctrl+S`) or tray menu
- Scrapes current conversation content from the DOM
- Saves as markdown to `~/Documents/Claude-Chats/`
- Filename format: `YYYY-MM-DD_conversation-title.md`
- Handles code blocks, formatting, user/assistant labels
- Overwrites previous save of same conversation (keeps latest)

### 🧠 chat_summarizer.py — Auto-Running Summary

**The killer feature.**

- Monitors the webview for new messages
- After a configurable pause (default: 30 seconds of no new messages), triggers a summary update
- Sends recent unsummarized exchanges to the Anthropic API:
  - Model: `claude-haiku-4-5-20251001` (fast, cheap)
  - Prompt: extract topics, decisions, action items, key ideas
- Appends to a running markdown summary file:
  - Location: `~/Documents/Claude-Chats/summaries/`
  - Filename: `YYYY-MM-DD_conversation-title_summary.md`
- Summary format:

```markdown
# Chat Summary — 2026-05-05

## Session Start: 2:15 PM MST

### Topic Heading
- Key point or decision
- Key point or decision

### Next Topic
- Key point
- Action item flagged
```

- Configurable:
  - `summarizer_enabled = true`
  - `summarizer_delay_seconds = 30`
  - `summarizer_model = "claude-haiku-4-5-20251001"`
  - `api_key` stored in KDE Wallet (never in config file)
- API key prompt on first enable — stored securely, never plaintext

### 🎨 theme.py — Visual Theming

- App chrome themed via Qt stylesheets (window frame, tray menu, notifications, settings panel, dialogs)
- Swappable theme files in TOML format
- Ships with multiple themes (not brown)
- Themes define:
  - Primary, secondary, accent colors
  - Background and surface colors
  - Font family and sizes for app chrome
  - Icon style (tray icon variants per theme)
  - Focus mode overlay color
- Config: `theme = "default"` (swappable without restart ideally, or on restart)
- KDE system theme can be followed as an option: `follow_system_theme = false`
- **Does NOT inject CSS into claude.ai content** — we don't fight upstream UI changes

### 🔔 notifications.py — Desktop Notifications

- Uses Qt's native notification system (integrates with KDE notification center)
- Triggers:
  - Long response complete (when window is not focused)
  - Download complete
  - Summary updated (optional, off by default)
  - Focus mode toggled (subtle)
- Respects system Do Not Disturb

### ⚙️ settings.py — Configuration

- Reads/writes `~/.config/velox/velox.toml`
- Created with sane defaults on first run
- All module behaviors configurable without editing code
- Example config:

```toml
[window]
width = 1200
height = 800
start_minimized = false

[security]
log_blocked_requests = false

[downloads]
directory = "~/Downloads/velox/"

[tray]
enabled = true

[hotkeys]
toggle_window = "Ctrl+Alt+Space"
focus_mode = "F11"
save_chat = "Ctrl+S"

[focus_mode]
hide_input_box = false

[summarizer]
enabled = true
delay_seconds = 30
model = "claude-haiku-4-5-20251001"

[theme]
active = "default"
follow_system_theme = false

[notifications]
on_response_complete = true
on_download_complete = true
on_summary_update = false

[zoom]
level = 1.0
```

---

## Future Modules (v2 Roadmap)

These are planned but explicitly out of scope for v1. The modular architecture means they slot in without touching existing code.

| Module | Purpose |
|---|---|
| `obsidian_bridge.py` | Side panel to browse and paste from Obsidian vault into chat context |
| `kde_calendar.py` | KDE Calendar/Akonadi integration — learning reminders, session scheduling, popup notifications for study goals |
| `chat_sync.py` | Cross-desktop sync for saved chats and summaries (Syncthing, rsync, or git-based — TBD) |
| `voice_controls.py` | Voice chat enhancements — playback speed control (2x), possibly JS injection on audio elements or local audio pipeline via GStreamer |
| `mcp_bridge.py` | Minimal local file access if needed later (not full MCP spec) |
| `tabs.py` | Multiple conversation tabs or sidebar |
| `conversation_search.py` | Search across saved chat exports |
| `whisper_bridge.py` | Hook into system-wide Whisper dictation |
| `auto_export.py` | Auto-save every conversation without manual trigger |

---

## Security Summary

| Concern | Mitigation |
|---|---|
| Network leakage | Allowlist-only domain filtering |
| Session token theft | Encrypted cookie store via KDE Wallet |
| Cache snooping | All QtWebEngine caching disabled |
| Clipboard exposure | Enabled (required), scoped to claude.ai only |
| API key storage | KDE Wallet / libsecret, never plaintext |
| Download safety | No silent downloads, confirmation on every file |
| Process isolation | Chromium sandbox enabled |
| File permissions | `~/.config/velox/` at `700` |

---

## Build Order

Incremental. Each phase produces a working app. We don't build phase 2 until phase 1 is solid.

### Phase 1 — Core (the "does it even work" phase)
1. `main.py` + `constants.py` + `settings.py` — app skeleton, config loading
2. `webview.py` — get claude.ai rendering with GPU accel and Wayland
3. `window.py` — proper window management, geometry persistence
4. `security.py` — domain lockdown before we do anything else
5. `cookie_store.py` — persistent login

**Milestone: a working, secure, persistent Claude chat window.**

### Phase 2 — Desktop Integration
6. `tray.py` — system tray with basic menu
7. `hotkeys.py` — global toggle hotkey
8. `downloads.py` — managed downloads to dedicated folder
9. `notifications.py` — response-complete and download alerts
10. `theme.py` — initial "not brown" theme

**Milestone: feels like a real desktop app.**

### Phase 3 — Smart Features
11. `focus_mode.py` — zen mode with code extraction
12. `code_tools.py` — copy-all-code-blocks
13. `chat_export.py` — manual save to markdown
14. `chat_summarizer.py` — auto-running conversation summaries via API

**Milestone: genuinely better than the Electron app.**

### Phase 4 — Polish & Packaging
15. Additional themes
16. Settings UI (optional — TOML editing is fine for v1)
17. Testing suite
18. Packaging (see below)

**Milestone: install on any machine in under a minute.**

---

## Packaging

Three formats, covering everything you'd run. All built from the same source, automated via a build script.

### RPM (Fedora — your primary)
- Proper `.spec` file with dependencies declared
- Installs to `/opt/velox/` with a launcher in `/usr/bin/`
- Desktop entry file for KDE app launcher (`.desktop`)
- Icon installed to standard Freedesktop icon paths
- Config created on first run at `~/.config/velox/`
- Build with: `rpmbuild` or a simple `build-rpm.sh` wrapper
- Install on another Fedora box: `sudo dnf install velox-*.rpm`

### AppImage (portable — any Linux)
- Single self-contained file, no install needed
- Bundles Python + PyQt6 + all dependencies
- Run on any Linux distro without installing anything
- Perfect for tossing on a USB stick or sharing with someone
- Build with: `appimage-builder` or `python-appimage`
- Larger file size (~150-200MB) but zero dependency headaches

### Flatpak (sandboxed — future option)
- Best for distribution to other people eventually
- Sandboxed by default which pairs well with the security model
- KDE/Flathub integration is solid
- More complex to set up but cleanest long-term packaging story
- Lower priority — RPM and AppImage cover your actual needs first

### Build script
A single `build.sh` at the project root:
```bash
./build.sh rpm        # builds the RPM
./build.sh appimage   # builds the AppImage
./build.sh all        # builds both
```

### Architecture added to project structure:
```
velox/
├── packaging/
│   ├── build.sh              # unified build script
│   ├── velox.spec        # RPM spec file
│   ├── velox.desktop     # Freedesktop desktop entry
│   ├── appimage/
│   │   └── AppImageBuilder.yml
│   └── icons/                # your Canva icons go here
│       ├── velox-16.png
│       ├── velox-24.png
│       ├── velox-32.png
│       ├── velox-48.png
│       ├── velox-64.png
│       ├── velox-128.png
│       ├── velox-256.png
│       └── velox.svg     # if available
```

---

## Dependencies

```
PyQt6
PyQt6-WebEngine
toml
keyring              # KDE Wallet integration
anthropic            # For chat summarizer API calls
```

All installable via pip. No system dependencies beyond Qt6 (already on KDE Plasma).

---

## Code Personality & Easter Eggs

**This codebase has a soul. Read it and smile.**

### Comment style throughout
Forget sterile docstrings. Every module gets comments with character:

```python
# Velox — Built by Claude · Anthropic
# This module keeps your cookies safe and your logins eternal.
# No, not those cookies. The digital kind. Though those too, honestly.

# 🔒 security.py
# The bouncer at the door. If your domain isn't on the list,
# you're not getting in. Nothing personal.

# 🧘 focus_mode.py  
# Shh. You're in the zone now.
# Everything that isn't your conversation has left the building.

# 🧠 chat_summarizer.py
# Because scrolling back through 200 messages to find
# "wait, what did we decide?" is not a life plan.

# 🍪 cookie_store.py
# Mmm, cookies. These ones keep you logged in.
# Encrypted at rest because we're not animals.
```

### Easter eggs to scatter
- **About dialog:** rotate a random tagline each time it opens:
  - "Claude was here. And here. And also here."
  - "Zero Electron atoms were harmed in the making of this app."
  - "Not brown since 2026."
  - "Lighter than your lightest browser tab."
  - "I'm not saying Electron is heavy, but..."
  - "🌵 Desert-tested. Adobe-free."
- **First launch:** a one-time welcome toast: "Hey! I'm Velox. I'm like the other Claude app, but I don't eat your RAM for breakfast."
- **Focus mode toggle:** brief flash text — "🧘 Zen mode activated" / "Welcome back to reality"
- **Tray icon tooltip:** rotates between fun messages: "Velox · Waiting patiently" / "Velox · Not consuming 400MB of RAM right now" / "Velox · Still not brown"
- **Console/log output:** startup banner:
```
  ╔═══════════════════════════════════════╗
  ║  🦋 Velox                         ║
  ║  Built by Claude · Anthropic          ║
  ║  Not an Electron in sight             ║
  ╚═══════════════════════════════════════╝
```
- **Error messages with personality:**
  - Network blocked: "🚫 Nope. That domain isn't on the guest list."
  - Download failed: "📦 That download didn't stick. Want to try again?"
  - Cookie store locked: "🍪 The cookie jar is stuck. Is KDE Wallet having a day?"

### The rule
Fun, not obnoxious. Every joke should also be informative — the comment should still tell you what the code does. The Easter egg should still tell the user what happened. Personality is the seasoning, not the meal.

---

## Branding & Attribution

**This is a Claude-built project. That's the headline, everywhere.**

### README.md (top of repo — first thing anyone sees)
```
# velox

### Built by Claude · Anthropic

A lightweight, native Qt6/Python desktop app for claude.ai.
No Electron. No bloat. Not brown.

---

Conceived and designed by Geoff Love · Phoenix, AZ
```

### Code file headers (every `.py` file)
```python
# Velox — Built by Claude · Anthropic
# https://github.com/[your-username]/velox
```

### About dialog (in the app itself)
- Top: **"Built by Claude · Anthropic"** — large, prominent, the first thing you read
- Below: app version, link to repo
- Bottom, small: *"Designed by Geoff Love"*

### Commit messages
- Regular commits attributed normally through git
- README and repo description make the Claude authorship clear

### Why this matters
This project demonstrates what a non-coder can build by collaborating with Claude — from planning through architecture through implementation. The code is Claude's. The vision, requirements, and design decisions are Geoff's. Both matter, and the repo makes that distinction visible.

---

## What This App Is Not

- Not a replacement for Claude Code CLI (use that for file/code work)
- Not an MCP host (no local server management)
- Not a browser (locked to claude.ai only)
- Not brown

## Icon Design Spec (for Canva)

When you're ready to design the Velox icon, here's what you need:

**Required sizes (KDE/Freedesktop standard):**
- 16x16 px — system tray at 1x scale
- 24x24 px — small tray on HiDPI
- 32x32 px — taskbar
- 48x48 px — app launcher
- 64x64 px — KDE app grid
- 128x128 px — about dialog, large previews
- 256x256 px — source/master (everything scales down from this)
- 512x512 px — if you want a crisp Flatpak/store icon later

**Format:** PNG with transparent background. SVG if Canva supports export (KDE prefers SVG for scalability).

**Design direction:**
- Should feel like it *belongs* on a KDE desktop — clean, modern, not cartoonish
- Visually distinct from the official Claude sparkle logo (we're not pretending to be official)
- Convey "chat" or "conversation" without being a generic speech bubble
- Fun but not silly — this is a tool you use every day, not a toy
- Should read clearly at 16x16 (tray size) — no fine detail that disappears at small sizes
- Consider a small visual nod to Qt or the "not Electron" ethos if you can make it subtle

**Color guidance:**
- Design a version that works on both light and dark panel backgrounds
- Or: one vibrant icon that pops against either (KDE panels can be either)
- Whatever palette you pick, we can pull it into the app theme to match

**What to avoid:**
- Brown
- The Anthropic logo (trademark, and we're unofficial)
- Anything that looks AI-generated-generic (the glowing brain, the robot face, etc.)

---

*Ready to build. Phase 1 first.*

---

**BUILT BY CLAUDE · ANTHROPIC**
