# Velox v2 Integration Guide

> Built by Claude · Anthropic — because instructions should be as organized as the thing they're building.

## Overview

Two new modules, three existing files touched. Total diff is small — the new modules do the heavy lifting independently.

---

## Step 1: Drop in the new files

```bash
cd ~/Claude/Projects/velox
cp ~/Downloads/tagger.py app/
cp ~/Downloads/download_organizer.py app/
```

## Step 2: Update `app/constants.py`

Open `app/constants.py` and add these near your other path constants:

```python
# 📚 Default archive directory for organized chat exports
CHAT_ARCHIVE_DIR = Path.home() / "Documents" / "Claude-Chats"
```

Then find your `DEFAULT_CONFIG = { ... }` dictionary and add this section inside it (next to the existing `"downloads"` section):

```python
    # 📂 Smart Downloads — v2
    "downloads_v2": {
        "chat_archive": str(Path.home() / "Documents" / "Claude-Chats"),
        "auto_organize": True,       # 🤖 Extract zips into named folders
        "timestamp_prefix": True,    # 🕐 "2026-05-12_Chat-Title"
        "auto_tag": True,            # 🏷️ YAML frontmatter on .md files
        "generate_index": True,      # 📖 INDEX.md in each folder
    },
```

Also add this to `ORGANIZER_MESSAGES` (or wherever you keep Easter egg lists):

```python
ORGANIZER_MESSAGES = [
    "📂 Your downloads have been given a purpose in life.",
    "🏷️ Tagged, bagged, and ready for future-you.",
    "📖 INDEX.md generated. You're welcome, three-days-from-now-you.",
    "🗂️ From chaos to clarity. Executive function as a service.",
    "📚 Filed under: things you'll actually find later.",
    "🔖 Your Obsidian vault just got a care package.",
]
```

## Step 3: Hook into `app/downloads.py`

This is the key integration point. In your existing `VeloxDownloadManager` (or whatever the download handler class is called), find where the download completes — the method that fires after a file finishes downloading.

Add these imports at the top of `downloads.py`:

```python
from app.download_organizer import DownloadOrganizer
```

In the `__init__` method, create the organizer:

```python
self._organizer = DownloadOrganizer(settings)
```

Then in the download-complete handler (the method that currently just prints a notification), add:

```python
# After the file has been saved to the download directory:
if filepath.suffix.lower() == '.zip' and self._organizer.auto_organize:
    # Grab the chat title from the page
    chat_title = self._get_chat_title()
    source_url = self._get_chat_url()
    
    result = self._organizer.organize_zip(
        filepath=filepath,
        chat_title=chat_title,
        source_url=source_url,
    )
    if result:
        # Notify the user
        from app.notifications import VeloxNotifier
        # (or however notifications are wired in your app)
```

### Getting the chat title from the page

Add this method to your download manager (or to `webview.py` — wherever you can run JavaScript on the page):

```python
def _get_chat_title(self) -> str:
    """
    Extract the current chat title from the claude.ai page.
    Falls back to the page <title> tag.
    
    🔍 "Scraping our own UI. Very meta."
    """
    # The page title is usually "Chat Name - Claude"
    page_title = self._page.title() if self._page else ""
    
    # Strip the " - Claude" suffix
    if " - Claude" in page_title:
        return page_title.split(" - Claude")[0].strip()
    if " — Claude" in page_title:
        return page_title.split(" — Claude")[0].strip()
    
    return page_title or "Untitled Chat"

def _get_chat_url(self) -> str:
    """Get the current page URL."""
    if self._page:
        return self._page.url().toString()
    return ""
```

## Step 4: Hook into `app/chat_export.py`

In your `ChatExporter` class, find where it writes the markdown file. Add the tagger call right before or after the write:

```python
from app.tagger import inject_frontmatter

# After writing the export file:
inject_frontmatter(
    filepath=export_path,
    chat_name=chat_title,
    status="final",
    source_url=source_url,
)
```

## Step 5: Delete old config and test

```bash
# Regenerate config with new v2 sections
rm ~/.config/velox/velox.toml

# Test
python main.py
```

The new config will include the `[downloads_v2]` section. Try a "Download All" from a chat and check:

1. Does the zip get renamed? (check `~/Downloads/Velox/`)
2. Does the folder appear? (check `~/Documents/Claude-Chats/`)
3. Does the folder have an `INDEX.md`?
4. Do the `.md` files have YAML frontmatter?

## Step 6: Commit

```bash
git add -A
git commit -m "🏷️ v2: smart download organizer with auto-tagging and INDEX.md"
git push origin main
```

---

## What users get

Without changing any settings, Velox v2 will:
- Extract downloaded zips into `~/Documents/Claude-Chats/2026-05-12_Chat-Title/`
- Tag every `.md` file with YAML frontmatter (title, date, tags, topics)
- Generate an `INDEX.md` that maps everything in the folder
- Work completely offline — no API keys, no network calls

Users can customize in `~/.config/velox/velox.toml`:

```toml
[downloads_v2]
chat_archive = "~/Documents/Claude-Chats/"
auto_organize = true
timestamp_prefix = true
auto_tag = true
generate_index = true
```

---

*Mapped out by Claude · Anthropic — the filing clerk who never takes lunch breaks.*
