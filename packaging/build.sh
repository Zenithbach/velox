#!/bin/bash
# Velox — Built by Claude · Anthropic
# Unified build script. Builds RPM, AppImage, or installs locally.
#
# Usage:
#   ./build.sh install     — install locally (~/.local)
#   ./build.sh uninstall   — remove local installation
#   ./build.sh rpm         — build an RPM package
#   ./build.sh appimage    — build an AppImage
#   ./build.sh all         — build RPM + AppImage
#   ./build.sh clean       — remove build artifacts

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

VERSION="1.0.0"

# ─── Colors ──────────────────────────────────────────────────────────────────

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    echo -e "${BLUE}🦋 Velox Build Script${NC}"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  install     Install locally to ~/.local"
    echo "  uninstall   Remove local installation"
    echo "  rpm         Build an RPM package (requires rpmbuild)"
    echo "  appimage    Build an AppImage (requires appimagetool)"
    echo "  all         Build RPM + AppImage"
    echo "  clean       Remove build artifacts"
    echo ""
}

do_install() {
    echo -e "${YELLOW}Running local install...${NC}"
    bash "$SCRIPT_DIR/install.sh"
}

do_uninstall() {
    echo -e "${YELLOW}Running uninstall...${NC}"
    bash "$SCRIPT_DIR/uninstall.sh"
}

do_rpm() {
    echo -e "${YELLOW}Building RPM...${NC}"

    if ! command -v rpmbuild &> /dev/null; then
        echo -e "${RED}❌ rpmbuild not found. Install with: sudo dnf install rpm-build${NC}"
        exit 1
    fi

    # Set up rpmbuild directory structure
    BUILD_ROOT="$PROJECT_DIR/build/rpm"
    mkdir -p "$BUILD_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

    # Create tarball
    TAR_NAME="velox-${VERSION}"
    TAR_DIR="$BUILD_ROOT/SOURCES"
    mkdir -p "/tmp/$TAR_NAME"
    cp -r "$PROJECT_DIR/main.py" "$PROJECT_DIR/app" "$PROJECT_DIR/requirements.txt" \
          "$PROJECT_DIR/packaging" "$PROJECT_DIR/LICENSE" "$PROJECT_DIR/README.md" \
          "/tmp/$TAR_NAME/"
    tar -czf "$TAR_DIR/$TAR_NAME.tar.gz" -C /tmp "$TAR_NAME"
    rm -rf "/tmp/$TAR_NAME"

    # Copy spec file
    cp "$SCRIPT_DIR/velox.spec" "$BUILD_ROOT/SPECS/"

    # Build
    rpmbuild --define "_topdir $BUILD_ROOT" -bb "$BUILD_ROOT/SPECS/velox.spec"

    echo -e "${GREEN}✅ RPM built! Check: $BUILD_ROOT/RPMS/${NC}"
}

do_appimage() {
    echo -e "${YELLOW}Building AppImage...${NC}"

    if ! command -v appimagetool &> /dev/null; then
        echo -e "${RED}❌ appimagetool not found.${NC}"
        echo "   Download from: https://github.com/AppImage/appimagetool/releases"
        exit 1
    fi

    # Set up AppDir structure
    APPDIR="$PROJECT_DIR/build/Velox.AppDir"
    rm -rf "$APPDIR"
    mkdir -p "$APPDIR/usr/bin"
    mkdir -p "$APPDIR/usr/share/velox"
    mkdir -p "$APPDIR/usr/share/applications"
    mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"

    # Copy application
    cp -r "$PROJECT_DIR/main.py" "$APPDIR/usr/share/velox/"
    cp -r "$PROJECT_DIR/app" "$APPDIR/usr/share/velox/"
    cp -r "$PROJECT_DIR/requirements.txt" "$APPDIR/usr/share/velox/"

    # Create AppRun
    cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF="$(readlink -f "$0")"
APPDIR="$(dirname "$SELF")"
export PATH="$APPDIR/usr/bin:$PATH"

# Use system Python with our app
cd "$APPDIR/usr/share/velox"
python3 main.py "$@"
APPRUN
    chmod +x "$APPDIR/AppRun"

    # Desktop entry
    cp "$SCRIPT_DIR/velox.desktop" "$APPDIR/usr/share/applications/"
    cp "$SCRIPT_DIR/velox.desktop" "$APPDIR/"  # AppImage needs it at root too

    # Icon
    if [ -f "$SCRIPT_DIR/icons/velox-256.png" ]; then
        cp "$SCRIPT_DIR/icons/velox-256.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/velox.png"
        cp "$SCRIPT_DIR/icons/velox-256.png" "$APPDIR/velox.png"
    else
        # Generate a placeholder PNG using Python
        python3 -c "
from app.tray import _generate_placeholder_icon
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap
import sys
app = QApplication(sys.argv)
icon = _generate_placeholder_icon()
pixmap = icon.pixmap(256, 256)
pixmap.save('$APPDIR/velox.png')
print('Generated placeholder icon')
" 2>/dev/null || echo "   Could not generate icon, continuing without"
    fi

    # Build the AppImage
    ARCH=x86_64 appimagetool "$APPDIR" "$PROJECT_DIR/build/Velox-${VERSION}-x86_64.AppImage"

    echo -e "${GREEN}✅ AppImage built! Check: $PROJECT_DIR/build/Velox-${VERSION}-x86_64.AppImage${NC}"
}

do_clean() {
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    rm -rf "$PROJECT_DIR/build"
    echo -e "${GREEN}✅ Clean.${NC}"
}

# ─── Main ────────────────────────────────────────────────────────────────────

case "${1:-}" in
    install)    do_install ;;
    uninstall)  do_uninstall ;;
    rpm)        do_rpm ;;
    appimage)   do_appimage ;;
    all)        do_rpm; do_appimage ;;
    clean)      do_clean ;;
    *)          usage ;;
esac
