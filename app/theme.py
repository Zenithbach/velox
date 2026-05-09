# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🎨 theme.py
# Because Anthropic made everything brown and we said no.
# Swappable TOML themes for the app chrome — tray menu,
# notifications, window frame, focus mode overlay.
#
# The webview itself stays untouched (we don't fight upstream CSS).
# This themes everything AROUND it.

import toml
from pathlib import Path
from dataclasses import dataclass, field

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor

from app.constants import APP_NAME


# ─── Theme Data ──────────────────────────────────────────────────────────────

@dataclass
class Theme:
    """
    A Velox theme. Defines colors for the app chrome.
    Loaded from a TOML file or constructed with defaults.
    """
    name: str = "default"
    display_name: str = "Velox Blue"

    # Primary palette
    primary: str = "#0088FF"         # Electric blue — the portal glow
    primary_light: str = "#50C8FF"   # Lighter variant
    primary_dark: str = "#0055AA"    # Darker variant

    # Backgrounds
    bg_dark: str = "#141929"         # Dark background (window frame, tray menu)
    bg_surface: str = "#1E2340"      # Surface (cards, panels)
    bg_hover: str = "#2A3055"        # Hover state

    # Text
    text_primary: str = "#E8ECFF"    # Main text
    text_secondary: str = "#8890B0"  # Muted text
    text_accent: str = "#50C8FF"     # Highlighted text

    # Focus mode
    focus_overlay: str = "#0D1117"   # Focus mode background
    focus_border: str = "#0088FF"    # Focus mode accent border

    # Status
    success: str = "#00CC88"         # Downloads complete, etc.
    warning: str = "#FFB800"         # Warnings
    error: str = "#FF4466"           # Errors


# ─── Built-in Themes ─────────────────────────────────────────────────────────
# These ship with the app. No external files needed.
# Because "not brown" is a feature, not a bug.

BUILTIN_THEMES = {
    "default": Theme(
        name="default",
        display_name="Velox Blue",
        # Uses all the dataclass defaults above
    ),
    "midnight": Theme(
        name="midnight",
        display_name="Midnight",
        primary="#8B5CF6",
        primary_light="#A78BFA",
        primary_dark="#6D28D9",
        bg_dark="#0F0F1A",
        bg_surface="#1A1A2E",
        bg_hover="#252540",
        text_primary="#E2E0F0",
        text_secondary="#7C7AA0",
        text_accent="#A78BFA",
        focus_overlay="#0A0A14",
        focus_border="#8B5CF6",
    ),
    "desert_escape": Theme(
        name="desert_escape",
        display_name="Desert Escape",
        # Ironic Arizona counter-programming: everything brown IS NOT.
        primary="#FF6B35",
        primary_light="#FF9F6B",
        primary_dark="#CC4400",
        bg_dark="#1A1520",
        bg_surface="#251E2A",
        bg_hover="#302838",
        text_primary="#F0E8E0",
        text_secondary="#A08878",
        text_accent="#FF9F6B",
        focus_overlay="#120E16",
        focus_border="#FF6B35",
    ),
    "aurora": Theme(
        name="aurora",
        display_name="Aurora",
        primary="#00D4AA",
        primary_light="#40FFD0",
        primary_dark="#009977",
        bg_dark="#0A1A18",
        bg_surface="#122420",
        bg_hover="#1A3530",
        text_primary="#E0F5F0",
        text_secondary="#70A898",
        text_accent="#40FFD0",
        focus_overlay="#060F0D",
        focus_border="#00D4AA",
    ),
}


# ─── Theme Manager ───────────────────────────────────────────────────────────

class ThemeManager:
    """
    Loads and applies themes to the Qt application.
    Checks for custom TOML themes in the themes/ directory,
    falls back to built-in themes.
    """

    def __init__(self, settings):
        self._settings = settings
        self._current_theme: Theme = BUILTIN_THEMES["default"]

        # Load the configured theme
        theme_name = settings.get("theme", "active", "default")
        self.apply_theme(theme_name)

    @property
    def current(self) -> Theme:
        """The currently active theme."""
        return self._current_theme

    @property
    def available_themes(self) -> list[str]:
        """List all available theme names (built-in + custom)."""
        themes = list(BUILTIN_THEMES.keys())

        # Check for custom theme files
        themes_dir = Path(__file__).parent.parent / "themes"
        if themes_dir.exists():
            for f in themes_dir.glob("*.toml"):
                name = f.stem
                if name not in themes:
                    themes.append(name)

        return themes

    def apply_theme(self, name: str):
        """
        Load and apply a theme by name.

        Search order:
        1. Built-in themes
        2. TOML files in the themes/ directory
        3. Fall back to default if nothing matches
        """
        # Check built-in themes first
        if name in BUILTIN_THEMES:
            self._current_theme = BUILTIN_THEMES[name]
            self._apply_to_app()
            print(f"🎨 Theme: {self._current_theme.display_name}")
            return

        # Check for custom TOML theme file
        themes_dir = Path(__file__).parent.parent / "themes"
        theme_file = themes_dir / f"{name}.toml"

        if theme_file.exists():
            try:
                theme_data = toml.load(theme_file)
                self._current_theme = Theme(**theme_data)
                self._apply_to_app()
                print(f"🎨 Theme: {self._current_theme.display_name} (custom)")
                return
            except Exception as e:
                print(f"🎨 ⚠️ Couldn't load theme '{name}': {e}")
                print(f"   Falling back to default.")

        # Fallback
        self._current_theme = BUILTIN_THEMES["default"]
        self._apply_to_app()
        print(f"🎨 Theme: {self._current_theme.display_name} (fallback)")

    def _apply_to_app(self):
        """
        Apply the current theme to the Qt application palette.
        This affects menus, tooltips, and any native Qt widgets.
        The webview content is NOT affected (that's claude.ai's domain).
        """
        app = QApplication.instance()
        if not app:
            return

        theme = self._current_theme
        palette = QPalette()

        # Window backgrounds
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.bg_dark))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme.bg_surface))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.bg_hover))

        # Text colors
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text_primary))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme.text_primary))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(theme.text_secondary))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(theme.text_accent))

        # Buttons
        palette.setColor(QPalette.ColorRole.Button, QColor(theme.bg_surface))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text_primary))

        # Highlights
        palette.setColor(QPalette.ColorRole.Highlight, QColor(theme.primary))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(theme.text_primary))

        # Links
        palette.setColor(QPalette.ColorRole.Link, QColor(theme.primary_light))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor(theme.primary_dark))

        # Tooltips
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(theme.bg_surface))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(theme.text_primary))

        app.setPalette(palette)

    def get_stylesheet(self) -> str:
        """
        Generate a Qt stylesheet for finer control over menu appearance.
        Applied to the tray menu and any future settings dialogs.
        """
        theme = self._current_theme
        return f"""
            QMenu {{
                background-color: {theme.bg_surface};
                color: {theme.text_primary};
                border: 1px solid {theme.bg_hover};
                border-radius: 8px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 24px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {theme.primary_dark};
                color: {theme.text_primary};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {theme.bg_hover};
                margin: 4px 8px;
            }}
        """
