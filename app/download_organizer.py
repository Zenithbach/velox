# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 📂 download_organizer.py — The Filing Clerk Who Actually Shows Up
# Takes chaotic downloads and turns them into self-documenting folders.
# Renames zips, extracts to named directories, tags everything,
# and generates an INDEX.md so future-you knows what past-you was doing.
#
# "Executive function as a service."

import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from app.tagger import inject_frontmatter, generate_index


# ── Filename sanitization ────────────────────────────────────────────
# Because chat titles can be anything and filesystems are picky.

# Characters that have no business in a filename
UNSAFE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f(){}[\]!@#$%^&+=,;\'`~]')

# Multiple dashes/underscores collapse to one
MULTI_SEP = re.compile(r'[-_]{2,}')

# Maximum folder name length (most filesystems cap at 255)
MAX_NAME_LENGTH = 80


def sanitize_name(name: str) -> str:
    """
    Turn a chat title into a filesystem-safe folder/file name.

    "Hello SuperClaude! 🦋" → "Hello-SuperClaude"
    "My Project (v2) — Final!!!" → "My-Project-v2-Final"

    🧼 "Filenames should be boring. Save the personality for the content."
    """
    if not name or not name.strip():
        return f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Remove emoji (Unicode emoji ranges)
    cleaned = re.sub(
        r'[\U0001F600-\U0001F64F'    # emoticons
        r'\U0001F300-\U0001F5FF'      # symbols & pictographs
        r'\U0001F680-\U0001F6FF'      # transport & map
        r'\U0001F1E0-\U0001F1FF'      # flags
        r'\U00002702-\U000027B0'      # dingbats
        r'\U0000FE00-\U0000FE0F'      # variation selectors
        r'\U0001F900-\U0001F9FF'      # supplemental symbols
        r'\U0001FA00-\U0001FA6F'      # chess symbols
        r'\U0001FA70-\U0001FAFF'      # symbols extended
        r'\U00002600-\U000026FF'      # misc symbols
        r']+', '', name
    )

    # Replace unsafe characters and common separators with dashes
    cleaned = UNSAFE_CHARS.sub('-', cleaned)
    cleaned = cleaned.replace(' ', '-')
    cleaned = cleaned.replace('—', '-')
    cleaned = cleaned.replace('–', '-')

    # Collapse multiple separators
    cleaned = MULTI_SEP.sub('-', cleaned)

    # Strip leading/trailing dashes
    cleaned = cleaned.strip('-_')

    # Truncate
    if len(cleaned) > MAX_NAME_LENGTH:
        cleaned = cleaned[:MAX_NAME_LENGTH].rstrip('-_')

    # Final fallback
    if not cleaned:
        return f"chat-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    return cleaned


class DownloadOrganizer:
    """
    The brains behind smart download organization.

    Takes a downloaded file (or zip), figures out where it should go,
    creates a named folder, extracts/copies the contents, runs the
    tagger on markdown files, and generates an INDEX.md.

    Usage:
        organizer = DownloadOrganizer(settings)
        result = organizer.organize(filepath, chat_title, source_url)

    📦 "Your downloads called. They want structure."
    """

    def __init__(self, settings=None):
        """
        Initialize with settings for configurable paths.

        Reads from velox.toml:
            [downloads]
            chat_archive = "~/Documents/Claude-Chats/"
            auto_organize = true
            timestamp_prefix = true
        """
        self._settings = settings

        # Archive directory — where organized chat folders go
        default_archive = str(Path.home() / "Documents" / "Claude-Chats")
        archive_str = default_archive
        if settings:
            archive_str = settings.get(
                "downloads", "chat_archive", default_archive
            )
        self._archive_dir = Path(archive_str).expanduser()

        # Whether to auto-organize downloads
        self._auto_organize = True
        if settings:
            self._auto_organize = settings.get(
                "downloads", "auto_organize", True
            )

        # Whether to prepend timestamps to folder names
        self._timestamp_prefix = True
        if settings:
            self._timestamp_prefix = settings.get(
                "downloads", "timestamp_prefix", True
            )

    @property
    def archive_dir(self) -> Path:
        return self._archive_dir

    @property
    def auto_organize(self) -> bool:
        return self._auto_organize

    def organize(
        self,
        filepath: Path,
        chat_title: str = "",
        source_url: str = "",
    ) -> Path | None:
        """
        Organize a downloaded file into a named, tagged, indexed folder.

        For zip files: extracts into a named folder under the archive dir.
        For individual files: copies into the same folder structure.

        Returns the path to the organized folder, or None if skipped.

        🗂️ "From chaos to clarity in one function call."
        """
        filepath = Path(filepath)

        if not filepath.exists():
            print(f"  📭 File not found: {filepath}")
            return None

        if not self._auto_organize:
            return None

        # Build the folder name
        folder_name = self._build_folder_name(chat_title, filepath)
        dest_folder = self._archive_dir / folder_name

        # Create the destination (parents too)
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Process based on file type
        if zipfile.is_zipfile(filepath):
            self._extract_zip(filepath, dest_folder)
        else:
            self._copy_file(filepath, dest_folder)

        # Tag all markdown files in the folder
        md_count = self._tag_markdown_files(dest_folder, chat_title, source_url)

        # Generate the INDEX.md
        index_path = generate_index(
            folder=dest_folder,
            chat_name=chat_title or folder_name,
            source_url=source_url,
        )

        print(f"  📂 Organized to: {dest_folder}")
        print(f"  🏷️ Tagged {md_count} markdown file(s)")
        print(f"  📖 INDEX.md generated")

        return dest_folder

    def organize_zip(
        self,
        filepath: Path,
        chat_title: str = "",
        source_url: str = "",
    ) -> Path | None:
        """
        Convenience method specifically for zip files.
        Renames the zip file itself too.

        Returns the organized folder path.
        """
        filepath = Path(filepath)

        if not filepath.exists() or not zipfile.is_zipfile(filepath):
            return None

        # Rename the zip to match the chat title
        if chat_title:
            new_name = sanitize_name(chat_title) + ".zip"
            new_path = filepath.parent / new_name
            if new_path != filepath:
                shutil.move(str(filepath), str(new_path))
                filepath = new_path
                print(f"  📋 Renamed zip: {new_name}")

        return self.organize(filepath, chat_title, source_url)

    def _build_folder_name(self, chat_title: str, filepath: Path) -> str:
        """
        Build a folder name from the chat title and optional timestamp.

        With timestamp:  "2026-05-12_Hello-SuperClaude"
        Without:         "Hello-SuperClaude"

        🕐 "Timestamps: because 'which version?' is a question nobody
            wants to answer at midnight."
        """
        if chat_title:
            base = sanitize_name(chat_title)
        else:
            # Fall back to the filename without extension
            base = sanitize_name(filepath.stem)

        if self._timestamp_prefix:
            date_str = datetime.now().strftime("%Y-%m-%d")
            return f"{date_str}_{base}"

        return base

    def _extract_zip(self, zip_path: Path, dest_folder: Path) -> None:
        """
        Extract a zip file into the destination folder.
        Handles nested directories gracefully — flattens if there's
        only one top-level directory inside the zip.

        🤐 "Unzipping with opinions about folder structure."
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Check if zip has a single root directory
                top_levels = set()
                for name in zf.namelist():
                    parts = Path(name).parts
                    if parts:
                        top_levels.add(parts[0])

                if len(top_levels) == 1:
                    # Single root dir — extract contents directly
                    # (avoids the annoying folder-in-a-folder pattern)
                    root = top_levels.pop()
                    for member in zf.namelist():
                        # Skip the root directory entry itself
                        rel = Path(member).relative_to(root) if member.startswith(root + '/') else None
                        if rel and str(rel) != '.':
                            target = dest_folder / rel
                            if member.endswith('/'):
                                target.mkdir(parents=True, exist_ok=True)
                            else:
                                target.parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(member) as src, open(target, 'wb') as dst:
                                    dst.write(src.read())
                else:
                    # Multiple roots or flat — extract as-is
                    zf.extractall(dest_folder)

            print(f"  🤐 Extracted: {zip_path.name}")

        except zipfile.BadZipFile:
            print(f"  ❌ Bad zip file: {zip_path.name}")
            # Copy the file anyway so nothing is lost
            self._copy_file(zip_path, dest_folder)

    def _copy_file(self, filepath: Path, dest_folder: Path) -> None:
        """Copy a single file into the destination folder."""
        dest = dest_folder / filepath.name

        # Avoid overwriting — add a number suffix if needed
        if dest.exists():
            stem = filepath.stem
            suffix = filepath.suffix
            counter = 1
            while dest.exists():
                dest = dest_folder / f"{stem}-{counter}{suffix}"
                counter += 1

        shutil.copy2(str(filepath), str(dest))

    def _tag_markdown_files(
        self,
        folder: Path,
        chat_name: str,
        source_url: str,
    ) -> int:
        """
        Run the tagger on every markdown file in the folder.
        Returns the count of files that got frontmatter injected.

        🏷️ "Tag everything. Search later. Thank yourself eventually."
        """
        count = 0
        for md_file in folder.glob("*.md"):
            if md_file.name == "INDEX.md":
                continue
            if inject_frontmatter(
                filepath=md_file,
                chat_name=chat_name,
                status="final",
                source_url=source_url,
            ):
                count += 1
        return count
