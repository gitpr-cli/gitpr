"""Tests for undoing an applied patch, against a real repository.

The history entry is built here rather than by driving the whole pipeline: what
these tests are about is the reversal, and ``apply_patch`` plus ``make_entry``
produce exactly the state ``apply_fix`` leaves behind — a modified file and a
recorded diff — without paying for an AI call that has nothing to do with it.
"""
import os
import shutil
import tempfile
import unittest

from src.fix.fix_history import append_entry, find_entry, load_history, make_entry
from src.fix.patch_applier import apply_patch, current_branch, create_branch, repo_root
from src.fix.patch_provenance import FindingRef, PatchProvenance, PatchSafety
from src.fix.rollback_fix import rollback_fix
from src.fix.apply_fix import FixError
from tests.fix.git_fixture import GitRepoTestCase

NEW_BODY = "def greet(name):\n    return f'Hi, {name}!'\n"

FINDING = FindingRef(
    id="FIX-001",
    file_path="src/app.py",
    line_start=2,
    line_end=2,
    severity="minor",
    category="style",
    message="greet() returns a hard-coded greeting",
)
PROVENANCE = PatchProvenance(
    finding_id="FIX-001",
    ai_provider="gemini",
    ai_model="gemini-pro-latest",
    prompt_version="1",
    generated_at="2026-09-13 12:00:00",
    gitpr_version="1.1.0",
)


class RollbackTestCase(GitRepoTestCase):
    prefix = "gitpr_fix_rollback_"

    def setUp(self):
        super().setUp()
        self.original = self.seed()

    def apply_patch_and_record(self, content=NEW_BODY, branch=None):
        """Leave the tree holding *content* and the history holding its diff."""
        patch = self.patch_for("src/app.py", content)
        applied, error = apply_patch(patch, cwd=self.dir)
        self.assertTrue(applied, error)

        entry = make_entry(
            patch_id="FIX-001-1a2b3c4d",
            finding=FINDING,
            diff=patch,
            provenance=PROVENANCE,
            files_changed=("src/app.py",),
            safety=PatchSafety.SAFE,
            branch=branch,
        )
        append_entry(entry, self.dir)
        return patch


class TestRollbackSucceeds(RollbackTestCase):
    def test_the_file_goes_back_to_what_it_was(self):
        self.apply_patch_and_record()
        self.assertEqual(self.read("src/app.py"), NEW_BODY)

        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        self.assertEqual(self.read("src/app.py"), self.original)

    def test_the_tree_is_clean_afterwards(self):
        self.apply_patch_and_record()
        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)
        # Only the history file itself is left untracked; the patch is gone.
        self.assertEqual(self.status_porcelain().strip(), "?? .gitpr/")

    def test_the_entry_is_stamped_as_undone(self):
        self.apply_patch_and_record()
        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)
        entry = find_entry("FIX-001-1a2b3c4d", self.dir)
        self.assertRegex(entry["rolled_back_at"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        self.assertEqual(entry["diff"], self.patch_for("src/app.py", NEW_BODY))

    def test_the_entry_that_was_undone_is_returned(self):
        self.apply_patch_and_record()
        entry = rollback_fix("FIX-001-1a2b3c4d", root=self.dir)
        self.assertEqual(entry["patch_id"], "FIX-001-1a2b3c4d")
        self.assertEqual(entry["files_changed"], ["src/app.py"])

    def test_a_patch_applied_in_place_can_be_undone_from_the_same_branch(self):
        self.apply_patch_and_record(branch=None)
        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)
        self.assertEqual(self.read("src/app.py"), self.original)

    def test_other_entries_in_the_history_survive(self):
        self.apply_patch_and_record()
        other = make_entry(
            patch_id="FIX-002-bbbbbbbb",
            finding=FINDING,
            diff="--- a/other\n+++ b/other\n@@ -1,1 +1,1 @@\n-a\n+b\n",
            provenance=PROVENANCE,
            files_changed=("other",),
        )
        append_entry(other, self.dir)

        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        history = load_history(self.dir)
        self.assertEqual(len(history), 2)
        self.assertIsNone(find_entry("FIX-002-bbbbbbbb", self.dir)["rolled_back_at"])


class TestRollbackOnABranch(RollbackTestCase):
    def test_a_patch_applied_on_a_branch_is_undone_there(self):
        create_branch("fix/gitpr-x", cwd=self.dir)
        self.apply_patch_and_record(branch="fix/gitpr-x")

        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        self.assertEqual(self.read("src/app.py"), self.original)
        self.assertEqual(current_branch(cwd=self.dir), "fix/gitpr-x")

    def test_undoing_from_another_branch_is_refused(self):
        create_branch("fix/gitpr-x", cwd=self.dir)
        self.apply_patch_and_record(branch="fix/gitpr-x")
        self._git("checkout", "main")

        with self.assertRaises(FixError) as caught:
            rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        self.assertIn("fix/gitpr-x", str(caught.exception))
        # The branch it belongs to is untouched.
        self.assertEqual(self.read("src/app.py"), NEW_BODY)
        self._git("checkout", "fix/gitpr-x")
        self.assertEqual(self.read("src/app.py"), NEW_BODY)


class TestRollbackRefuses(RollbackTestCase):
    def test_an_unknown_patch_is_refused(self):
        self.apply_patch_and_record()
        with self.assertRaises(FixError) as caught:
            rollback_fix("FIX-999-ffffffff", root=self.dir)
        self.assertIn("FIX-999-ffffffff", str(caught.exception))

    def test_undoing_twice_is_refused(self):
        self.apply_patch_and_record()
        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        with self.assertRaises(FixError) as caught:
            rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        self.assertIn("already rolled back", str(caught.exception))
        self.assertEqual(self.read("src/app.py"), self.original)

    def test_an_externally_edited_file_is_refused_without_damage(self):
        self.apply_patch_and_record()
        edited = "def greet(name):\n    return name\n"
        self.write("src/app.py", edited)

        with self.assertRaises(FixError):
            rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        self.assertEqual(self.read("src/app.py"), edited)
        self.assertIsNone(find_entry("FIX-001-1a2b3c4d", self.dir)["rolled_back_at"])

    def test_an_empty_history_is_refused(self):
        with self.assertRaises(FixError):
            rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

    def test_outside_a_repository_it_refuses(self):
        outside = tempfile.mkdtemp(prefix="gitpr_fix_rollback_outside_")
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        if repo_root(cwd=outside) is not None:
            self.skipTest("this machine's temp directory sits inside a repository")
        with self.assertRaises(FixError):
            rollback_fix("FIX-001-1a2b3c4d", root=outside)


class TestRollbackKeepsTheOriginalFile(RollbackTestCase):
    def test_the_file_matches_the_committed_version_again(self):
        self.apply_patch_and_record()
        rollback_fix("FIX-001-1a2b3c4d", root=self.dir)

        committed = self._git("show", "HEAD:src/app.py").stdout
        self.assertEqual(self.read("src/app.py"), committed)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "src", "app.py")))


if __name__ == "__main__":
    unittest.main()
