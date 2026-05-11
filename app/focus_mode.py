# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🧘 focus_mode.py
# Shh. You're in the zone now.
# Everything that isn't your conversation has left the building.
#
# Injects CSS into the webview to hide the sidebar, navigation,
# and optionally the input box. What's left: just the conversation.
# Toggle with F11. Hit Escape or F11 again to come back.

from PyQt6.QtCore import QObject, pyqtSignal


# CSS that hides everything except the conversation content.
# These selectors target claude.ai's current DOM structure.
# If Anthropic redesigns the frontend, these may need updating.
# That's the trade-off of CSS injection — fragile but effective.

FOCUS_CSS = """
/* 🧘 Velox Focus Mode — hide everything but the conversation */

/* Sidebar / navigation */
nav, [data-testid="sidebar"], .sidebar,
div[class*="sidebar"], div[class*="Sidebar"],
div[class*="nav-"], header {
    display: none !important;
}

/* Top bar / header elements */
div[class*="header"], div[class*="Header"],
div[class*="topbar"], div[class*="TopBar"] {
    display: none !important;
}

/* Model selector and other chrome above the chat */
div[class*="model-selector"], div[class*="ModelSelector"] {
    display: none !important;
}

/* Make the main content area fill the whole window */
main, [role="main"], div[class*="main"],
div[class*="conversation"], div[class*="Conversation"] {
    margin-left: 0 !important;
    padding-left: 16px !important;
    max-width: 100% !important;
    width: 100% !important;
}

/* Subtle border to indicate focus mode is active */
body {
    border-top: 2px solid #0088FF !important;
}
"""

# Additional CSS to also hide the input box (optional)
FOCUS_CSS_HIDE_INPUT = """
/* Hide the input area too — pure reading mode */
div[class*="input"], div[class*="Input"],
div[class*="composer"], div[class*="Composer"],
form, textarea {
    display: none !important;
}
"""

# The ID we give our injected style element so we can find and remove it
STYLE_ELEMENT_ID = "velox-focus-mode"


class FocusMode(QObject):
    """
    Toggles focus/zen mode on the webview by injecting CSS.

    When active: sidebar, navigation, and header are hidden.
    The conversation fills the full window width.
    A subtle blue border at the top indicates you're in focus mode.

    When inactive: everything goes back to normal.
    No permanent changes to the page.
    """

    # Signal emitted when focus mode changes state
    toggled = pyqtSignal(bool)

    def __init__(self, webview, settings, parent=None):
        super().__init__(parent)
        self._webview = webview
        self._settings = settings
        self._active = False

    @property
    def is_active(self) -> bool:
        """Is focus mode currently on?"""
        return self._active

    def toggle(self):
        """Flip focus mode on or off."""
        if self._active:
            self.deactivate()
        else:
            self.activate()

    def activate(self):
        """
        Enter focus mode. Inject the CSS.
        🧘 Zen mode activated.
        """
        if self._active:
            return

        hide_input = self._settings.get("focus_mode", "hide_input_box", False)

        css = FOCUS_CSS
        if hide_input:
            css += FOCUS_CSS_HIDE_INPUT

        # Escape the CSS for JavaScript injection
        escaped_css = css.replace("\\", "\\\\").replace("`", "\\`")

        js = f"""
        (function() {{
            // Remove existing focus mode style if present (shouldn't be, but safety first)
            let existing = document.getElementById('{STYLE_ELEMENT_ID}');
            if (existing) existing.remove();

            // Create and inject the style element
            let style = document.createElement('style');
            style.id = '{STYLE_ELEMENT_ID}';
            style.textContent = `{escaped_css}`;
            document.head.appendChild(style);
        }})();
        """

        self._webview.page().runJavaScript(js)
        self._active = True
        self.toggled.emit(True)
        print("🧘 Focus mode activated. Just you and the conversation.")

    def deactivate(self):
        """
        Exit focus mode. Remove the injected CSS.
        Welcome back to reality.
        """
        if not self._active:
            return

        js = f"""
        (function() {{
            let style = document.getElementById('{STYLE_ELEMENT_ID}');
            if (style) style.remove();
        }})();
        """

        self._webview.page().runJavaScript(js)
        self._active = False
        self.toggled.emit(False)
        print("🧘 Focus mode off. Welcome back to reality.")
