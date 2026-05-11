# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 🧠 chat_summarizer.py
# The killer feature. Because scrolling back through a 200-message chat
# to find "wait, what did we decide?" is not how we live.
#
# Monitors the conversation for new messages. After a pause (default 30s),
# scrapes the recent exchange, sends it to the Anthropic API (Haiku — fast
# and cheap), and appends a topic summary to a running markdown file.
#
# The result: a growing index of every conversation you have,
# organized by date and topic. Drop it into Obsidian, grep it,
# or paste it into the next chat for instant context.

import json
import threading
from datetime import datetime

from PyQt6.QtCore import QObject, QTimer

from app.constants import SUMMARY_DIR

# Try to import the Anthropic client
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# The system prompt for the summarizer model.
# Haiku gets this context on every call.
SUMMARIZER_SYSTEM_PROMPT = """You are a conversation summarizer for Velox, a desktop Claude client.

Your job: extract the key topics, decisions, and action items from a conversation excerpt.

Output format (strict markdown):
### [Topic Title]
- Key point or decision
- Key point or decision
- Action item (if any)

Rules:
- Be concise. 2-5 bullet points per topic.
- Multiple topics get separate ### headings.
- Focus on DECISIONS and OUTCOMES, not the back-and-forth.
- If code was written, note WHAT it does, not the code itself.
- Skip pleasantries, greetings, and filler.
- No meta-commentary about the summarization process.
"""


class ChatSummarizer(QObject):
    """
    Auto-generates running conversation summaries.

    Flow:
    1. Polls the webview for new message content
    2. After a configurable pause with no new messages, triggers a summary
    3. Sends the new content to Anthropic API (Haiku)
    4. Appends the summary to a per-conversation markdown file
    5. Repeat

    The summary files live in ~/Documents/Claude-Chats/summaries/
    and grow throughout the conversation. They're the index to your
    knowledge, not a replacement for the full chat.
    """

    def __init__(self, webview, settings, notifications=None, parent=None):
        super().__init__(parent)
        self._webview = webview
        self._settings = settings
        self._notifications = notifications

        self._enabled = settings.get("summarizer", "enabled", True)
        self._delay = settings.get("summarizer", "delay_seconds", 30) * 1000  # ms
        self._model = settings.get("summarizer", "model", "claude-haiku-4-5-20251001")

        self._last_content_hash = ""
        self._pending_content = ""
        self._current_title = ""

        # Timer that fires after the delay period of no new messages
        self._debounce_timer = QTimer(self)
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._trigger_summary)

        # Polling timer — checks for new content periodically
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_for_changes)

        # Ensure summary directory exists
        SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

        if not ANTHROPIC_AVAILABLE:
            print("🧠 Summarizer: 'anthropic' package not installed. Summaries disabled.")
            self._enabled = False

        if self._enabled:
            self._try_init_client()

    def _try_init_client(self):
        """
        Initialize the Anthropic API client.
        API key comes from the environment variable ANTHROPIC_API_KEY
        or from the system keyring.
        """
        import os

        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            # Try the system keyring
            try:
                import keyring
                api_key = keyring.get_password("velox-api", "anthropic-api-key")
            except Exception:
                pass

        if api_key:
            self._client = anthropic.Anthropic(api_key=api_key)
            print("🧠 Summarizer ready. Watching for conversation changes.")
        else:
            print("🧠 Summarizer: no API key found.")
            print("   Set ANTHROPIC_API_KEY env var or store it in your keyring:")
            print("   python -c \"import keyring; keyring.set_password('velox-api', 'anthropic-api-key', 'your-key-here')\"")
            self._enabled = False
            self._client = None

    # ─── Public API ──────────────────────────────────────────────────────

    def start(self):
        """Start watching for conversation changes."""
        if not self._enabled:
            return

        # Poll every 10 seconds for changes
        self._poll_timer.start(10000)
        print("🧠 Summarizer is watching for conversation changes.")

    def stop(self):
        """Stop watching."""
        self._poll_timer.stop()
        self._debounce_timer.stop()

    # ─── Content Monitoring ──────────────────────────────────────────────

    def _poll_for_changes(self):
        """Check if the conversation content has changed."""
        js = """
        (function() {
            // Get the text content of all messages
            let messages = document.querySelectorAll(
                '[data-message-author-role]'
            );

            let texts = [];
            let title = document.title || 'Untitled';

            // Get the last few messages (we don't need the whole history every time)
            let startIdx = Math.max(0, messages.length - 6);
            for (let i = startIdx; i < messages.length; i++) {
                let el = messages[i];
                let role = el.getAttribute('data-message-author-role') || 'unknown';
                let text = (el.textContent || '').trim().substring(0, 2000);
                texts.push(role + ': ' + text);
            }

            return JSON.stringify({
                title: title,
                content: texts.join('\\n---\\n'),
                messageCount: messages.length
            });
        })();
        """

        self._webview.page().runJavaScript(js, self._check_content)

    def _check_content(self, result):
        """Compare new content to last known state."""
        try:
            data = json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, TypeError):
            return

        if not data or not data.get("content"):
            return

        content = data["content"]
        title = data.get("title", "Untitled")
        content_hash = str(hash(content))

        if content_hash != self._last_content_hash:
            # Content changed — reset the debounce timer
            self._last_content_hash = content_hash
            self._pending_content = content
            self._current_title = title
            self._debounce_timer.start(self._delay)

    # ─── Summary Generation ──────────────────────────────────────────────

    def _trigger_summary(self):
        """
        Debounce timer expired — time to summarize.
        Run in a thread so we don't block the UI.
        """
        if not self._pending_content or not self._client:
            return

        content = self._pending_content
        title = self._current_title
        self._pending_content = ""

        # Run API call in a background thread
        thread = threading.Thread(
            target=self._generate_summary,
            args=(content, title),
            daemon=True
        )
        thread.start()

    def _generate_summary(self, content: str, title: str):
        """
        Call the Anthropic API to generate a summary.
        Runs in a background thread.
        """
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=500,
                system=SUMMARIZER_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this conversation excerpt:\n\n{content}"
                    }
                ]
            )

            summary_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    summary_text += block.text

            if summary_text:
                self._append_summary(title, summary_text)

        except Exception as e:
            print(f"🧠 ⚠️ Summary generation failed: {e}")

    def _append_summary(self, title: str, summary: str):
        """Append the generated summary to the running summary file."""
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M %p")

        # Clean up the title for filename use
        import re
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'\s+', '-', safe_title)[:60].strip('-') or "chat"

        filename = f"{date_str}_{safe_title}_summary.md"
        filepath = SUMMARY_DIR / filename

        # Build the entry
        entry = f"\n## Updated: {time_str}\n\n{summary}\n\n---\n"

        # If the file doesn't exist, create it with a header
        if not filepath.exists():
            header = (
                f"# Chat Summary — {title}\n\n"
                f"*Auto-generated by Velox · Built by Claude · Anthropic*\n\n"
                f"---\n"
            )
            filepath.write_text(header + entry, encoding="utf-8")
            print(f"🧠 ✅ New summary file: {filepath}")
        else:
            # Append to existing file
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(entry)
            print(f"🧠 ✅ Summary updated: {filepath}")

        if self._notifications:
            self._notifications.notify_summary_updated()
