# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 💾 chat_export.py
# Save your conversations to markdown files.
# Because scrolling back through 200 messages to find
# "wait, what did we decide?" is not a life plan.
#
# Scrapes the current conversation from the webview DOM,
# formats it as clean markdown, and saves it to disk.
# Files land in ~/Documents/Claude-Chats/ by default.

import re
from datetime import datetime

from PyQt6.QtCore import QObject

from app.constants import CHAT_EXPORT_DIR


class ChatExport(QObject):
    """
    Exports the current conversation to a markdown file.

    Triggered via Ctrl+S or the tray menu.
    Scrapes the page DOM for messages, formats them,
    and writes a clean .md file to the export directory.
    """

    def __init__(self, webview, settings, notifications=None, parent=None):
        super().__init__(parent)
        self._webview = webview
        self._settings = settings
        self._notifications = notifications

        # Ensure the export directory exists
        CHAT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    def save_current_chat(self):
        """
        Scrape the current conversation and save it as markdown.
        This is the main entry point — wire it to Ctrl+S.
        """
        js = """
        (function() {
            // Extract conversation content from the page.
            // claude.ai structures messages in containers with role indicators.

            let messages = [];

            // Strategy 1: Look for message containers with role attributes
            let msgElements = document.querySelectorAll(
                '[data-message-author-role], ' +
                'div[class*="human"], div[class*="Human"], ' +
                'div[class*="assistant"], div[class*="Assistant"]'
            );

            if (msgElements.length > 0) {
                for (let el of msgElements) {
                    let role = el.getAttribute('data-message-author-role') || '';
                    if (!role) {
                        // Try to infer from class names
                        let cls = el.className || '';
                        if (cls.match(/human|user/i)) role = 'user';
                        else if (cls.match(/assistant|claude/i)) role = 'assistant';
                    }

                    // Get the text content, preserving some structure
                    let content = '';

                    // Handle code blocks specially
                    let codeBlocks = el.querySelectorAll('pre code, pre');
                    let allText = el.cloneNode(true);

                    // Replace code blocks with markers
                    let codeIdx = 0;
                    let codes = {};
                    allText.querySelectorAll('pre').forEach(pre => {
                        let lang = '';
                        let codeEl = pre.querySelector('code');
                        if (codeEl) {
                            let match = (codeEl.className || '').match(/language-(\\w+)/);
                            if (match) lang = match[1];
                        }
                        let key = '___CODE_' + codeIdx + '___';
                        codes[key] = {lang: lang, text: pre.textContent.trim()};
                        pre.textContent = key;
                        codeIdx++;
                    });

                    content = allText.textContent || allText.innerText || '';
                    content = content.trim();

                    // Restore code blocks as markdown fenced blocks
                    for (let [key, info] of Object.entries(codes)) {
                        let fence = '```' + info.lang + '\\n' + info.text + '\\n```';
                        content = content.replace(key, '\\n\\n' + fence + '\\n\\n');
                    }

                    if (content && role) {
                        messages.push({role: role, content: content});
                    }
                }
            }

            // Strategy 2: Fallback — grab all text content in order
            if (messages.length === 0) {
                let body = document.querySelector('main') || document.body;
                let text = body.innerText || body.textContent || '';
                messages.push({role: 'unknown', content: text.trim()});
            }

            // Try to get the conversation title from the page
            let title = '';
            let titleEl = document.querySelector(
                'title, h1, [class*="title"], [class*="Title"]'
            );
            if (titleEl) {
                title = titleEl.textContent || '';
                title = title.replace(/[\\n\\r]/g, '').trim();
                // Clean up "Claude" prefix if present
                title = title.replace(/^Claude\\s*[-—]\\s*/, '');
            }

            return JSON.stringify({
                title: title,
                messages: messages,
                url: window.location.href
            });
        })();
        """

        self._webview.page().runJavaScript(js, self._handle_export_result)

    def _handle_export_result(self, result):
        """Process the scraped conversation and write to disk."""
        import json

        try:
            data = json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, TypeError):
            print("💾 ❌ Couldn't extract conversation content.")
            return

        if not data or not data.get("messages"):
            print("💾 No conversation content found to save.")
            return

        messages = data["messages"]
        title = data.get("title", "Untitled Chat")
        url = data.get("url", "")

        # Generate the markdown
        md = self._format_markdown(title, messages, url)

        # Generate filename
        filename = self._generate_filename(title)
        filepath = CHAT_EXPORT_DIR / filename

        # Write it
        try:
            filepath.write_text(md, encoding="utf-8")
            print(f"💾 ✅ Chat saved: {filepath}")

            if self._notifications:
                self._notifications.notify(
                    title="Chat Saved",
                    message=f"💾 {filename}",
                    subtitle=str(CHAT_EXPORT_DIR),
                )
        except OSError as e:
            print(f"💾 ❌ Couldn't save chat: {e}")

    def _format_markdown(self, title: str, messages: list, url: str) -> str:
        """Format the conversation as clean markdown."""
        now = datetime.now()

        lines = [
            f"# {title}",
            "",
            f"*Exported from Velox on {now.strftime('%Y-%m-%d at %I:%M %p')}*",
            "",
        ]

        if url:
            lines.append(f"Source: {url}")
            lines.append("")

        lines.append("---")
        lines.append("")

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                lines.append("## 👤 You")
            elif role == "assistant":
                lines.append("## 🦋 Claude")
            else:
                lines.append("## 💬 Message")

            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Footer
        lines.append(f"*Saved by Velox · Built by Claude · Anthropic*")

        return "\n".join(lines)

    @staticmethod
    def _generate_filename(title: str) -> str:
        """
        Generate a filename from the conversation title and date.
        Sanitizes the title to be filesystem-safe.
        """
        now = datetime.now()
        date_prefix = now.strftime("%Y-%m-%d")

        # Sanitize the title for use as a filename
        safe_title = re.sub(r'[^\w\s-]', '', title)  # Remove special chars
        safe_title = re.sub(r'\s+', '-', safe_title)  # Spaces to hyphens
        safe_title = safe_title[:60].strip('-')  # Truncate and clean

        if not safe_title:
            safe_title = "chat"

        return f"{date_prefix}_{safe_title}.md"
