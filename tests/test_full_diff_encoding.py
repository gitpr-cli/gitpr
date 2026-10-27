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


if __name__ == "__main__":
    unittest.main()
