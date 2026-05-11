#!/bin/bash
# Velox — Built by Claude · Anthropic
# Local installation script.
# Installs Velox to your system so it shows up in your app launcher,
# the tray icon works properly, and KDE stops complaining about
# "App info not found for 'velox'".

set -e

# ─── Configuration ───────────────────────────────────────────────────────────

APP_NAME="velox"
INSTALL_DIR="$HOME/.local/share/velox"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Colors (because even installers should have personality) ────────────────

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║  🦋 Velox Installer                    ║"
echo "  ║  Built by Claude · Anthropic          ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ─── Create directories ─────────────────────────────────────────────────────

echo -e "${YELLOW}📁 Creating directories...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR/256x256/apps"
mkdir -p "$ICON_DIR/128x128/apps"
mkdir -p "$ICON_DIR/64x64/apps"
mkdir -p "$ICON_DIR/48x48/apps"
mkdir -p "$ICON_DIR/32x32/apps"
mkdir -p "$ICON_DIR/24x24/apps"
mkdir -p "$ICON_DIR/16x16/apps"

# ─── Copy application files ─────────────────────────────────────────────────

echo -e "${YELLOW}📦 Installing Velox...${NC}"

# Copy Python source
cp -r "$PROJECT_DIR/main.py" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/app" "$INSTALL_DIR/"
cp -r "$PROJECT_DIR/requirements.txt" "$INSTALL_DIR/"

# Copy themes if they exist
if [ -d "$PROJECT_DIR/themes" ]; then
    cp -r "$PROJECT_DIR/themes" "$INSTALL_DIR/"
fi

# ─── Create virtual environment ─────────────────────────────────────────────

echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
if [ ! -d "$INSTALL_DIR/.venv" ]; then
    python3 -m venv "$INSTALL_DIR/.venv"
    source "$INSTALL_DIR/.venv/bin/activate"
    pip install -q -r "$INSTALL_DIR/requirements.txt"
    deactivate
else
    echo "   Virtual environment already exists, skipping."
fi

# ─── Create launcher script ─────────────────────────────────────────────────

echo -e "${YELLOW}🚀 Creating launcher...${NC}"
cat > "$BIN_DIR/velox" << 'LAUNCHER'
#!/bin/bash
# 🦋 Velox launcher
VELOX_DIR="$HOME/.local/share/velox"
source "$VELOX_DIR/.venv/bin/activate"
python "$VELOX_DIR/main.py" "$@"
LAUNCHER
chmod +x "$BIN_DIR/velox"

# ─── Install desktop entry ──────────────────────────────────────────────────

echo -e "${YELLOW}🖥️  Installing desktop entry...${NC}"
cat > "$DESKTOP_DIR/velox.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=Velox
GenericName=Claude Desktop Client
Comment=A lightweight native desktop client for claude.ai
Exec=$BIN_DIR/velox
Icon=velox
Terminal=false
Categories=Network;Chat;Utility;
Keywords=claude;ai;chat;anthropic;
StartupNotify=true
StartupWMClass=velox
DESKTOP

# ─── Install icons ──────────────────────────────────────────────────────────

echo -e "${YELLOW}🎨 Installing icons...${NC}"

# Check for icon files in packaging/icons/
ICON_SRC="$PROJECT_DIR/packaging/icons"
if [ -f "$ICON_SRC/velox-256.png" ]; then
    cp "$ICON_SRC/velox-256.png" "$ICON_DIR/256x256/apps/velox.png"
    echo "   Installed 256x256 icon"
    
    # Generate smaller sizes if ImageMagick is available
    if command -v convert &> /dev/null; then
        for size in 128 64 48 32 24 16; do
            convert "$ICON_SRC/velox-256.png" -resize ${size}x${size} \
                "$ICON_DIR/${size}x${size}/apps/velox.png"
            echo "   Generated ${size}x${size} icon"
        done
    else
        echo "   ImageMagick not found — only 256x256 icon installed."
        echo "   Install ImageMagick for auto-resized icons: sudo dnf install ImageMagick"
    fi
else
    echo "   No icon file found at $ICON_SRC/velox-256.png"
    echo "   The app will use the placeholder icon."
fi

# Update icon cache
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true
fi

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# ─── Done ────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}✅ Velox installed successfully!${NC}"
echo ""
echo "   You can now:"
echo "   • Run from terminal:  velox"
echo "   • Find in app launcher:  search for 'Velox'"
echo "   • The tray icon portal error should be gone"
echo ""
echo -e "   ${BLUE}🦋 Happy chatting!${NC}"
