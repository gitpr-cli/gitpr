"""Regression: a Latin-1 (non-UTF-8) file must not break the branch diff.

The diff used to be captured with encoding="utf-8" and no errors= handler.
The decoding error killed subprocess's reader thread, stdout came back as
None and the run reported "no new code found" instead of the branch changes.
The project-wide contract is UTF-8 with replacement: the legacy byte must
surface as U+FFFD and the rest of the diff must survive.
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from src.core import get_git_full_diff
from tests.fix.git_fixture import GitRepoTestCase

# 0xFA is "ú" in Latin-1 and invalid alone in UTF-8 — the byte from the bug.
# Written in binary so the fixture reaches git untouched.
LATIN1_CONTENT = b"# aten\xe7\xe3o: conte\xfado legado\nVALUE = 1\n"


class TestFullDiffLatin1(GitRepoTestCase):
    """A real repository whose branch adds a committed Latin-1 file."""

    prefix = "gitpr_full_diff_"

    def setUp(self):
        super().setUp()
        self.assertIn(b"\xfa", LATIN1_CONTENT, "fixture must carry byte 0xFA")

        # A real origin: a bare repository with main pushed and origin/HEAD
        # pointing at it, so get_git_full_diff() can run its own fetch,
        # symbolic-ref and merge-base instead of having them mocked.
        self.remote = tempfile.mkdtemp(prefix=self.prefix + "origin_")
        self.addCleanup(shutil.rmtree, self.remote, ignore_errors=True)
        self._git("init", "--bare", "-b", "main", self.remote)
        self.commit(
            "src/app.py", "def greet():\n    return 'hi'\n", message="chore: seed"
        )
        self._git("remote", "add", "origin", self.remote)
        self._git("push", "--quiet", "origin", "main")
        self._git("fetch", "--quiet", "origin")
        self._git("remote", "set-head", "origin", "-a")
        self.assertEqual(
            self._git("symbolic-ref", "refs/remotes/origin/HEAD").stdout.strip(),
            "refs/remotes/origin/main",
        )

        # The file lands on a branch, so it appears as added lines in the diff
        # between the merge base and the working tree.
        self._git("checkout", "-b", "feature")
        with open(os.path.join(self.dir, "legacy_encoding.py"), "wb") as handle:
            handle.write(LATIN1_CONTENT)
        self._git("add", "--", "legacy_encoding.py")
        self._git("commit", "-m", "chore: add legacy latin-1 file")

    def test_latin1_diff_is_decoded_with_replacement(self):
        # get_git_full_diff() runs git in the process cwd. Registered during the
        # test, after the fixture's rmtree cleanup, so LIFO restores the cwd
        # BEFORE Windows tries to delete this tree.
        previous_cwd = os.getcwd()
        self.addCleanup(os.chdir, previous_cwd)
        os.chdir(self.dir)

        # The developer's global smart-excludes override must not decide
        # whether the fixture file is visible. redirect_stdout keeps click's
        # emoji banner out of a cp1252 pipe outside pytest's capture.
        with patch("src.core.SMART_EXCLUDES", []), contextlib.redirect_stdout(
            io.StringIO()
        ):
            diff = get_git_full_diff()

        self.assertIsNotNone(diff, "git diff returned no output for valid content")
        self.assertTrue("legacy_encoding.py" in diff, "diff does not mention the file")
        # "conteúdo" -> "conte�do": pins the exact byte the strict codec rejected.
        self.assertTrue("conte�do" in diff, "byte 0xFA was not replaced by U+FFFD")


    def test_binary_blob_with_long_ascii_header_is_collapsed_by_guard(self):
        """A binary file without NUL in the first 8KB is diffed as text by git,
        but the Binary hunk guard collapses its U+FFFD hunks while keeping Latin-1 code intact."""
        previous_cwd = os.getcwd()
        self.addCleanup(os.chdir, previous_cwd)
        os.chdir(self.dir)

        # > 8000 bytes of ASCII so git's buffer_is_binary() treats it as text,
        # followed by non-UTF-8 binary bytes (0x80..0xFF) with no NUL byte.
        ascii_header = b"HEADER_FIELD=1234567890\n" * 360  # 8640 bytes
        binary_tail = bytes(range(0x80, 0xFF)) * 4 + b"\n"
        with open(os.path.join(self.dir, "custom_blob.unknown_ext"), "wb") as handle:
            handle.write(ascii_header + binary_tail)
        self._git("add", "--", "custom_blob.unknown_ext")
        self._git("commit", "-m", "chore: add custom binary blob without NUL")

        with patch("src.core.SMART_EXCLUDES", []), contextlib.redirect_stdout(
            io.StringIO()
        ):
            diff = get_git_full_diff()

        self.assertIsNotNone(diff)
        # 1. Legitimate Latin-1 source code keeps its hunks and isolated U+FFFD
        self.assertIn("legacy_encoding.py", diff)
        self.assertIn("conte\ufffddo", diff)
        self.assertIn("+VALUE = 1", diff)
        # 2. The binary blob's hunks are collapsed into a standard binary marker
        self.assertIn(
            "Binary files /dev/null and b/custom_blob.unknown_ext differ", diff
        )
        self.assertNotIn("HEADER_FIELD=1234567890", diff)
        self.assertNotIn("\ufffd" * 8, diff)

    def test_smart_excludes_filters_standard_binary_extensions_at_git_level(self):
        """Standard binary files (.pdf, .png, .zip) are excluded by SMART_EXCLUDES pathspecs."""
        from src.core import _FALLBACK_SMART_EXCLUDES

        previous_cwd = os.getcwd()
        self.addCleanup(os.chdir, previous_cwd)
        os.chdir(self.dir)

        # Write a pseudo-PDF with a long ASCII header + high-bit bytes
        pdf_bytes = b"%PDF-1.7\n" + (b"% comment line\n" * 600) + bytes(range(0x80, 0xFF)) + b"\n"
        with open(os.path.join(self.dir, "manual.pdf"), "wb") as handle:
            handle.write(pdf_bytes)
        self._git("add", "--", "manual.pdf")
        self._git("commit", "-m", "chore: add large pdf")

        excludes = [f":(exclude){p}" for p in _FALLBACK_SMART_EXCLUDES]
        with patch("src.core.SMART_EXCLUDES", excludes), contextlib.redirect_stdout(
            io.StringIO()
        ):
            diff = get_git_full_diff()

        self.assertIsNotNone(diff)
        self.assertNotIn("manual.pdf", diff)
        self.assertIn("legacy_encoding.py", diff)
        self.assertIn("conte\ufffddo", diff)


class TestCollapseBinaryHunksUnit(unittest.TestCase):
    """Unit tests for the Binary hunk guard (collapse_binary_hunks)."""

    def test_fast_path_leaves_utf8_diff_untouched(self):
        from src.diff_parser import collapse_binary_hunks

        raw = (
            "diff --git a/src/app.py b/src/app.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/src/app.py\n"
            "+++ b/src/app.py\n"
            "@@ -1 +1,2 @@\n"
            " def greet():\n"
            "+    return 'ok'\n"
        )
        self.assertIs(collapse_binary_hunks(raw), raw)

    def test_preserves_latin1_source_with_scattered_accents(self):
        from src.diff_parser import collapse_binary_hunks

        raw = (
            "diff --git a/src/legacy.py b/src/legacy.py\n"
            "index 1111111..2222222 100644\n"
            "--- a/src/legacy.py\n"
            "+++ b/src/legacy.py\n"
            "@@ -1,2 +1,3 @@\n"
            " # aten\ufffd\ufffdo: fun\ufffd\ufffdo de valida\ufffd\ufffdo\n"
            "+# configura\ufffd\ufffdo padr\ufffdo do m\ufffddulo\n"
            "+VALUE = 42\n"
        )
        self.assertEqual(collapse_binary_hunks(raw), raw)

    def test_collapses_section_with_contiguous_fffd_run(self):
        from src.diff_parser import collapse_binary_hunks

        raw = (
            "diff --git a/data/dump.custom b/data/dump.custom\n"
            "index 1111111..2222222 100644\n"
            "--- a/data/dump.custom\n"
            "+++ b/data/dump.custom\n"
            "@@ -1 +1 @@\n"
            "-old\n"
            "+prefix_" + ("\ufffd" * 8) + "_suffix\n"
        )
        expected = (
            "diff --git a/data/dump.custom b/data/dump.custom\n"
            "index 1111111..2222222 100644\n"
            "Binary files a/data/dump.custom and b/data/dump.custom differ\n"
        )
        self.assertEqual(collapse_binary_hunks(raw), expected)

    def test_collapses_section_with_high_fffd_density(self):
        from src.diff_parser import collapse_binary_hunks

        # 36 U+FFFD spread in pairs (never reaching 8 contiguous), density > 10%
        noisy_line = "+ab\ufffd\ufffdcd\ufffd\ufffdef\ufffd\ufffdgh\ufffd\ufffdij\ufffd\ufffdkl\ufffd\ufffd\n"
        raw = (
            "diff --git a/blob.raw b/blob.raw\n"
            "index abcdef0..1234567 100644\n"
            "--- a/blob.raw\n"
            "+++ b/blob.raw\n"
            "@@ -0,0 +1,3 @@\n"
            + (noisy_line * 3)
        )
        collapsed = collapse_binary_hunks(raw)
        self.assertIn("Binary files a/blob.raw and b/blob.raw differ", collapsed)
        self.assertNotIn("\ufffd", collapsed)

    def test_remote_pr_filter_excluded_sections_applies_binary_hunk_guard(self):
        from src.review.diff_normalizer import filter_excluded_sections

        raw = (
            "diff --git a/unknown.blob b/unknown.blob\n"
            "index 1111111..2222222 100644\n"
            "--- a/unknown.blob\n"
            "+++ b/unknown.blob\n"
            "@@ -1 +1 @@\n"
            "+" + ("\ufffd" * 16) + "\n"
        )
        filtered, dropped = filter_excluded_sections(raw, ["*.lock"])
        self.assertEqual(dropped, [])
        self.assertIn("Binary files a/unknown.blob and b/unknown.blob differ", filtered)
        self.assertNotIn("\ufffd", filtered)


if __name__ == "__main__":
    unittest.main()
