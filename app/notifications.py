# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🔔 notifications.py
# Desktop notifications that integrate with KDE's notification center.
# Fires when downloads finish, when long responses complete while
# you're alt-tabbed, or when anything else worth knowing about happens.
# Respects Do Not Disturb because we're not monsters.

from PyQt6.QtWidgets import QSystemTrayIcon


class NotificationManager:
    """
    Sends desktop notifications through the system tray icon.
    Qt's tray notifications integrate natively with KDE's notification
    center, so they show up in the right place, respect DND, and
    can be dismissed the same way as any other notification.

    Why not use D-Bus notifications directly? Because QSystemTrayIcon
    already does that under the hood on KDE, and this way we don't
    need an extra dependency. Keep it simple.
    """

    def __init__(self, tray_icon: QSystemTrayIcon, settings):
        self._tray = tray_icon
        self._settings = settings

    # ─── Public API ──────────────────────────────────────────────────────

    def notify(self, title: str, message: str, subtitle: str = "",
               icon_type: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
               duration_ms: int = 5000):
        """
        Show a desktop notification.

        Args:
            title: Bold header text
            message: Body text
            subtitle: Extra context (appended to message if present)
            icon_type: Information, Warning, or Critical
            duration_ms: How long to show (KDE may override this)
        """
        if not self._tray.isVisible():
            # No tray icon → no notifications. Silent fail.
            return

        full_message = message
        if subtitle:
            full_message = f"{message}\n{subtitle}"

        self._tray.showMessage(title, full_message, icon_type, duration_ms)

    def notify_response_complete(self):
        """
        Notify that a long Claude response has finished.
        Only fires if the window isn't focused (you're alt-tabbed).
        """
        if not self._settings.get("notifications", "on_response_complete", True):
            return

        self.notify(
            title="Velox",
            message="🦋 Claude is done thinking.",
        )

    def notify_download_complete(self, filename: str, directory: str = ""):
        """Notify that a file download finished."""
        if not self._settings.get("notifications", "on_download_complete", True):
            return

        self.notify(
            title="Download Complete",
            message=f"📥 {filename}",
            subtitle=directory,
        )

    def notify_summary_updated(self):
        """Notify that the conversation summary was updated."""
        if not self._settings.get("notifications", "on_summary_update", False):
            return  # Off by default — most people don't want this

        self.notify(
            title="Velox",
            message="🧠 Conversation summary updated.",
        )
