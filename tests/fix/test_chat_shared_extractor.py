"""Acceptance 8/9: the chat shortcuts read code through the shared layer.

F5 (action_apply_code) and ctrl+s (action_auto_patch_focused) used to carry a
verbatim copy of the extraction regex. They now call
``src.fix.patch_extractor.extract_code_blocks``. Driving the real Textual app
would need a display, so the handlers are invoked unbound against a mock ``self``
— they touch only ``memory``, ``_focused_msg_content``, ``_focused_msg_index``
and ``_notify_action``. The user-visible result must be exactly what it was: the
same ``GITPR_PATCH_SUGGESTION_<key>.txt`` in the working directory, and the same
notification.
"""
import inspect
import os
import re
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

from src.fix.patch_extractor import extract_code_blocks
from src.i18n import __
from src.ui import chat_app as chat_app_module
from src.ui.chat_app import ChatApp

ANSWER_WITH_CODE = (
    "Use this instead:\n\n"
    "```python\n"
    "def fixed():\n"
    "    return 2\n"
    "```\n\n"
    "That should do it.\n"
)

ANSWER_WITHOUT_CODE = "I would just rename the variable, no code needed.\n"


class ChatShortcutTestCase(unittest.TestCase):
    """Runs the handlers inside a temporary working directory."""

    def setUp(self):
        self._cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="gitpr_chat_export_")
        self.addCleanup(os.chdir, self._cwd)
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        os.chdir(self._tmp)

    def _fake_app(self, answer, focused_index=0):
        """A stand-in for ChatApp carrying only what the handlers touch."""
        app = MagicMock()
        app._focused_msg_content = answer
        app._focused_msg_index = focused_index
        app.memory.get_history.return_value = [
            {"role": "user", "content": "how do I fix this?"},
            {"role": "assistant", "content": answer},
        ]
        return app

    def _exported_files(self):
        return [n for n in os.listdir(self._tmp) if n.startswith("GITPR_PATCH_SUGGESTION_")]

    def _read_only_export(self):
        files = self._exported_files()
        self.assertEqual(len(files), 1, f"expected one export, got {files}")
        with open(
            os.path.join(self._tmp, files[0]), "r", encoding="utf-8", errors="replace"
        ) as handle:
            return files[0], handle.read()


class TestF5Shortcut(ChatShortcutTestCase):
    def test_writes_the_blocks_the_shared_extractor_returns(self):
        app = self._fake_app(ANSWER_WITH_CODE)
        ChatApp.action_apply_code(app)

        name, written = self._read_only_export()
        self.assertTrue(re.fullmatch(r"GITPR_PATCH_SUGGESTION_\w{3}-\w{3}\.txt", name))
        self.assertEqual(written, "\n\n".join(extract_code_blocks(ANSWER_WITH_CODE)))
        app._notify_action.assert_called_once_with(
            __("⚡ Auto-Patch: Code extracted and saved to {file}!", file=name)
        )

    def test_answer_without_code_creates_no_file(self):
        app = self._fake_app(ANSWER_WITHOUT_CODE)
        ChatApp.action_apply_code(app)

        self.assertEqual(self._exported_files(), [])
        app._notify_action.assert_called_once_with(
            __("❌ No code blocks found in the last AI message."), severity="warning"
        )

    def test_no_ai_answer_warns_without_touching_the_tree(self):
        app = MagicMock()
        app.memory.get_history.return_value = [{"role": "user", "content": "hi"}]
        ChatApp.action_apply_code(app)

        self.assertEqual(self._exported_files(), [])
        app._notify_action.assert_called_once_with(
            __("❌ No AI responses available to extract code from."), severity="warning"
        )


class TestCtrlSShortcut(ChatShortcutTestCase):
    def test_writes_the_focused_message_blocks(self):
        app = self._fake_app(ANSWER_WITH_CODE, focused_index=2)
        ChatApp.action_auto_patch_focused(app)

        name, written = self._read_only_export()
        self.assertEqual(written, "\n\n".join(extract_code_blocks(ANSWER_WITH_CODE)))
        app._notify_action.assert_called_once_with(
            __(
                "🧪 Auto-Patch: Code extracted from message #{n} and saved to {file}!",
                n=3,
                file=name,
            )
        )

    def test_answer_without_code_creates_no_file(self):
        app = self._fake_app(ANSWER_WITHOUT_CODE, focused_index=4)
        ChatApp.action_auto_patch_focused(app)

        self.assertEqual(self._exported_files(), [])
        app._notify_action.assert_called_once_with(
            __("❌ No code blocks found in message #{n}.", n=5), severity="warning"
        )

    def test_no_focused_message_warns(self):
        app = self._fake_app("", focused_index=0)
        app._focused_msg_content = ""
        ChatApp.action_auto_patch_focused(app)

        self.assertEqual(self._exported_files(), [])
        app._notify_action.assert_called_once_with(
            __("❌ No AI message focused. Use F7/F8 to select one."), severity="warning"
        )


class TestNoLocalExtractionLeft(unittest.TestCase):
    """Both handlers must delegate, not carry their own copy of the regex."""

    def test_handlers_call_the_shared_extractor(self):
        for handler in (
            ChatApp.action_apply_code,
            ChatApp.action_auto_patch_focused,
        ):
            with self.subTest(handler=handler.__name__):
                source = inspect.getsource(handler)
                self.assertIn("extract_code_blocks(", source)
                self.assertNotIn("re.findall", source)

    def test_the_module_keeps_no_regex_of_its_own(self):
        with open(
            inspect.getsourcefile(chat_app_module), "r", encoding="utf-8", errors="replace"
        ) as handle:
            module_source = handle.read()
        self.assertNotIn("re.findall", module_source)


if __name__ == "__main__":
    unittest.main()
