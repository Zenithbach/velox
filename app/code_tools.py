# Velox — Built by Claude · Anthropic
# https://github.com/Zenithbach/velox
#
# 💻 code_tools.py
# Because clicking five separate "copy" buttons on five separate
# code blocks is not a life plan.
#
# Extracts all code blocks from the current conversation view
# and copies them to the clipboard as a single concatenated block,
# with language labels so you know what's what.
#
# Configurable: [code_tools] mode = "all" or "last"
# "all" grabs the whole conversation, "last" grabs just the last response.

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject


class CodeTools(QObject):
    """
    Code extraction utilities for the webview.

    Main feature: "Copy All Code Blocks" — grabs every <code> block
    from the conversation (or just the last response, configurable)
    and puts them on the clipboard in one shot.
    """

    def __init__(self, webview, settings=None, parent=None):
        super().__init__(parent)
        self._webview = webview
        self._settings = settings

    def copy_all_code_blocks(self):
        """
        Copy code blocks based on the configured mode.
        Mode "all" = whole conversation, "last" = last response only.
        Configurable in velox.toml: [code_tools] mode = "all"
        """
        mode = "all"
        if self._settings:
            mode = self._settings.get("code_tools", "mode", "all")

        if mode == "last":
            self._copy_from_last_response()
        else:
            self._copy_from_all()

    def _copy_from_all(self):
        """
        Extract all code blocks from the entire conversation.

        Result on clipboard looks like:
            -- python --
            def hello():
                print("world")

            -- bash --
            echo "hello"
        """
        js = """
        (function() {
            let blocks = document.querySelectorAll('pre code, pre');
            let results = [];

            for (let block of blocks) {
                let code = block.textContent || block.innerText;
                code = code.trim();
                if (!code) continue;

                let lang = 'code';
                let classes = (block.className || '') + ' ' + (block.parentElement?.className || '');
                let match = classes.match(/language-(\\w+)/);
                if (match) {
                    lang = match[1];
                }

                results.push({lang: lang, code: code});
            }

            if (results.length === 0) {
                return JSON.stringify({count: 0, text: ''});
            }

            let formatted = results.map(r => {
                return '── ' + r.lang + ' ──\\n' + r.code;
            }).join('\\n\\n');

            return JSON.stringify({count: results.length, text: formatted});
        })();
        """

        self._webview.page().runJavaScript(js, self._handle_code_result)

    def _copy_from_last_response(self):
        """
        Extract code blocks from only the LAST assistant response.
        More targeted — gets just what Claude just said.
        """
        js = """
        (function() {
            let targetContainer = null;

            let allContainers = document.querySelectorAll('div[data-message-author-role="assistant"]');
            if (allContainers.length > 0) {
                targetContainer = allContainers[allContainers.length - 1];
            }

            let searchRoot = targetContainer || document;
            let blocks = searchRoot.querySelectorAll('pre code, pre');
            let results = [];

            for (let block of blocks) {
                let code = block.textContent || block.innerText;
                code = code.trim();
                if (!code) continue;

                let lang = 'code';
                let classes = (block.className || '') + ' ' + (block.parentElement?.className || '');
                let match = classes.match(/language-(\\w+)/);
                if (match) {
                    lang = match[1];
                }

                results.push({lang: lang, code: code});
            }

            if (results.length === 0) {
                return JSON.stringify({count: 0, text: ''});
            }

            let formatted = results.map(r => {
                return '── ' + r.lang + ' ──\\n' + r.code;
            }).join('\\n\\n');

            return JSON.stringify({count: results.length, text: formatted});
        })();
        """

        self._webview.page().runJavaScript(js, self._handle_code_result)

    def _handle_code_result(self, result):
        """Process the extracted code and copy to clipboard."""
        import json
        try:
            data = json.loads(result) if isinstance(result, str) else result
        except (json.JSONDecodeError, TypeError):
            print("💻 ❌ Couldn't extract code blocks.")
            return

        if not data or data.get("count", 0) == 0:
            print("💻 No code blocks found on the page.")
            return

        clipboard = QApplication.clipboard()
        clipboard.setText(data["text"])
        count = data["count"]
        print(f"💻 ✅ Copied {count} code block{'s' if count != 1 else ''} to clipboard.")
