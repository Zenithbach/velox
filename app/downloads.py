# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 📥 downloads.py
# Manages file downloads from claude.ai.
# Every download goes to one place, every download gets a notification,
# and nothing downloads silently in the background.
# Your ~/Downloads folder stays clean. You're welcome.

import os
from pathlib import Path

from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineDownloadRequest
from PyQt6.QtCore import QUrl

from app.constants import DOWNLOAD_DIR


class DownloadManager:
    """
    Intercepts download requests from the webview and routes them
    to a dedicated directory with user-visible notifications.

    No silent downloads. No mystery files. No "where did that go?"
    Every file lands in ~/Downloads/Velox/ (or wherever you configured).
    """

    def __init__(self, profile: QWebEngineProfile, settings, notifications=None):
        self._profile = profile
        self._settings = settings
        self._notifications = notifications

        # Get download directory from config, with fallback
        self._download_dir = Path(
            settings.get("downloads", "directory", str(DOWNLOAD_DIR))
        )
        self._ensure_download_dir()

        # Wire up the download signal
        self._profile.downloadRequested.connect(self._on_download_requested)

        print(f"📥 Downloads will land in: {self._download_dir}")

    # ─── Signal Handlers ─────────────────────────────────────────────────

    def _on_download_requested(self, download: QWebEngineDownloadRequest):
        """
        Called when claude.ai wants to download a file.
        This fires when you click "Download" on an artifact,
        code file, or any other downloadable content.
        """
        # Figure out the filename
        suggested_name = download.downloadFileName()
        if not suggested_name:
            suggested_name = "velox-download"

        # Resolve the full path
        # If a file with the same name exists, Qt handles the conflict
        # by appending a number. We let it.
        download_path = self._download_dir / suggested_name
        download.setDownloadDirectory(str(self._download_dir))
        download.setDownloadFileName(suggested_name)

        # Accept the download
        download.accept()

        print(f"📥 Downloading: {suggested_name}")

        # Watch for completion
        download.isFinishedChanged.connect(
            lambda: self._on_download_finished(download)
        )

    def _on_download_finished(self, download: QWebEngineDownloadRequest):
        """Called when a download completes (or fails)."""
        filename = download.downloadFileName()
        state = download.state()

        if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
            full_path = Path(download.downloadDirectory()) / filename
            print(f"📥 ✅ Saved: {full_path}")

            # Send a desktop notification if the module is available
            if self._notifications:
                self._notifications.notify(
                    title="Download Complete",
                    message=f"📥 {filename}",
                    subtitle=str(self._download_dir),
                )

        elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
            print(f"📥 ❌ Cancelled: {filename}")

        elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
            print(f"📥 ⚠️ Interrupted: {filename}")
            if self._notifications:
                self._notifications.notify(
                    title="Download Failed",
                    message=f"📦 {filename} didn't stick. Check your connection.",
                )

    # ─── Setup ───────────────────────────────────────────────────────────

    def _ensure_download_dir(self):
        """Create the download directory if it doesn't exist."""
        self._download_dir.mkdir(parents=True, exist_ok=True)

    @property
    def download_dir(self) -> Path:
        """Where downloads go. For display in the tray menu, etc."""
        return self._download_dir
