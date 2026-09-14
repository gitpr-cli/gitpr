"""Unit tests for the shared code extractor (extract_code_blocks, extract_unified_diff)."""
import unittest

from src.fix.patch_extractor import extract_code_blocks, extract_unified_diff

DIFF = """diff --git a/src/a.py b/src/a.py
--- a/src/a.py
+++ b/src/a.py
@@ -1,2 +1,3 @@
 def hello():
+    # note
     return 1
"""


class TestExtractCodeBlocks(unittest.TestCase):
    def test_fenced_block_with_language(self):
        text = "Here you go:\n\n```python\nprint(1)\n```\n"
        self.assertEqual(extract_code_blocks(text), ["print(1)\n"])

    def test_fenced_block_without_language(self):
        text = "```\nx = 1\n```\n"
        self.assertEqual(extract_code_blocks(text), ["x = 1\n"])

    def test_several_blocks_keep_order(self):
        text = "```python\na\n```\ntext\n```python\nb\n```\n"
        self.assertEqual(extract_code_blocks(text), ["a\n", "b\n"])

    def test_empty_and_none_give_no_blocks(self):
        for text in ("", None, "no fences here"):
            with self.subTest(text=text):
                self.assertEqual(extract_code_blocks(text), [])

    def test_fallback_handles_an_unterminated_fence(self):
        # The regex needs a closing fence; a truncated answer has none, so the
        # split-based fallback takes over and strips the language identifier.
        text = "```python\ncode line"
        self.assertEqual(extract_code_blocks(text), ["code line"])

    def test_trailing_text_without_fence_is_ignored(self):
        text = "```python\nx = 1\n```\nand some prose"
        self.assertEqual(extract_code_blocks(text), ["x = 1\n"])


class TestExtractUnifiedDiff(unittest.TestCase):
    def test_bare_diff_is_returned(self):
        self.assertEqual(extract_unified_diff(DIFF), DIFF)

    def test_fenced_diff_is_unwrapped(self):
        self.assertEqual(extract_unified_diff("```diff\n" + DIFF + "```\n"), DIFF)

    def test_result_always_ends_with_a_single_newline(self):
        self.assertEqual(extract_unified_diff(DIFF + "\n\n\n"), DIFF)

    def test_the_later_block_wins_when_the_first_is_not_a_diff(self):
        # A model often explains first and only then prints the patch.
        text = "```python\nprint(1)\n```\n\n```diff\n" + DIFF + "```\n"
        self.assertEqual(extract_unified_diff(text), DIFF)

    def test_prose_or_a_plain_snippet_is_not_a_diff(self):
        for text in (
            "",
            "   \n",
            None,
            "no diff at all",
            "```python\nx = 1\n```",
            "--- a/x\n+++ b/x\n",  # headers with no hunk
            "diff --git a/x b/x\nold mode 100644\nnew mode 100755\n",
        ):
            with self.subTest(text=text):
                self.assertIsNone(extract_unified_diff(text))

    def test_trailing_spaces_on_context_lines_survive(self):
        # rstrip() would eat them; only the newlines may be trimmed.
        diff = "--- a/x\n+++ b/x\n@@ -1,1 +1,1 @@\n ctx   \n-old\n+new\n"
        self.assertEqual(extract_unified_diff(diff), diff)

    def test_ai_style_diff_without_the_git_header(self):
        diff = "--- a/mod.py\n+++ b/mod.py\n@@ -1,1 +1,2 @@\n keep\n+added\n"
        self.assertEqual(extract_unified_diff(diff), diff)


if __name__ == "__main__":
    unittest.main()
