#!/bin/bash
# Velox — Built by Claude · Anthropic
# Uninstall script. Removes everything install.sh put down.
# Your config and saved chats are NOT deleted — that's your data.

set -e

APP_NAME="velox"
INSTALL_DIR="$HOME/.local/share/velox"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor"

echo "🦋 Uninstalling Velox..."

# Remove app files
[ -d "$INSTALL_DIR" ] && rm -rf "$INSTALL_DIR" && echo "   Removed $INSTALL_DIR"

# Remove launcher
[ -f "$BIN_DIR/velox" ] && rm "$BIN_DIR/velox" && echo "   Removed launcher"

# Remove desktop entry
[ -f "$DESKTOP_DIR/velox.desktop" ] && rm "$DESKTOP_DIR/velox.desktop" && echo "   Removed desktop entry"

# Remove icons
for size in 256 128 64 48 32 24 16; do
    icon="$ICON_DIR/${size}x${size}/apps/velox.png"
    [ -f "$icon" ] && rm "$icon"
done
echo "   Removed icons"

# Update caches
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
gtk-update-icon-cache -f -t "$ICON_DIR" 2>/dev/null || true

echo ""
echo "✅ Velox uninstalled."
echo ""
echo "   Your config is still at: ~/.config/velox/"
echo "   Your saved chats are at: ~/Documents/Claude-Chats/"
echo "   Delete those manually if you want a clean slate."
echo ""
echo "   👋 See you around."
