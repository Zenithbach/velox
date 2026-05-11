Name:           velox
Version:        1.0.0
Release:        1%{?dist}
Summary:        A lightweight native desktop client for claude.ai
License:        MIT
URL:            https://github.com/Zenithbach/velox
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.12
Requires:       python3-qt6
Requires:       qt6-qtwebengine

%description
Velox is a lightweight, native Qt6/Python desktop wrapper for claude.ai.
No Electron. No bloat. Not brown.

Built by Claude · Anthropic.

Features:
- Persistent login with encrypted cookie storage
- GPU-accelerated Wayland-native rendering
- Domain-locked security (allowlist-only networking)
- System tray integration with themed menus
- Focus mode for distraction-free reading
- Chat export to markdown
- Auto-generating conversation summaries
- Four built-in color themes

%prep
%setup -q

%install
mkdir -p %{buildroot}/opt/%{name}
mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_datadir}/applications
mkdir -p %{buildroot}/%{_datadir}/icons/hicolor/256x256/apps

# Install application files
cp -r main.py %{buildroot}/opt/%{name}/
cp -r app %{buildroot}/opt/%{name}/
cp -r requirements.txt %{buildroot}/opt/%{name}/

# Install launcher
cat > %{buildroot}/%{_bindir}/velox << 'EOF'
#!/bin/bash
VELOX_DIR="/opt/velox"
if [ -d "$VELOX_DIR/.venv" ]; then
    source "$VELOX_DIR/.venv/bin/activate"
fi
python3 "$VELOX_DIR/main.py" "$@"
EOF
chmod 755 %{buildroot}/%{_bindir}/velox

# Install desktop entry
cp packaging/velox.desktop %{buildroot}/%{_datadir}/applications/

# Install icon if available
if [ -f packaging/icons/velox-256.png ]; then
    cp packaging/icons/velox-256.png \
        %{buildroot}/%{_datadir}/icons/hicolor/256x256/apps/velox.png
fi

%post
# Set up Python virtual environment on install
if [ ! -d /opt/%{name}/.venv ]; then
    python3 -m venv /opt/%{name}/.venv
    /opt/%{name}/.venv/bin/pip install -q -r /opt/%{name}/requirements.txt
fi

# Update icon cache
gtk-update-icon-cache -f -t %{_datadir}/icons/hicolor 2>/dev/null || true
update-desktop-database %{_datadir}/applications 2>/dev/null || true

%files
/opt/%{name}/
%{_bindir}/velox
%{_datadir}/applications/velox.desktop
%{_datadir}/icons/hicolor/256x256/apps/velox.png

%changelog
* Sat May 10 2026 Claude <claude@anthropic.com> - 1.0.0-1
- Initial release
- Phase 1: Core webview, security, persistent login
- Phase 2: Tray icon, downloads, notifications, theming
- Phase 3: Focus mode, code tools, chat export, auto-summarizer
- Phase 4: Packaging and polish
