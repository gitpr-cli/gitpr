"""Tests for the shared git wrapper, against real repositories.

Every patch here comes from ``patch_for`` — a diff git itself produced — so a
passing "it applies" assertion means something. The fixture also proves the
negative cases: a patch that does not match the tree must be refused, and a dry
run must leave the working tree bit-for-bit as it found it.
"""
import os
import shutil
import tempfile
import unittest

from src.fix.patch_applier import (
    apply_patch,
    check_patch,
    create_branch,
    current_branch,
    current_head,
    is_git_repository,
    modified_files,
    repo_root,
    reverse_patch,
)
from tests.fix.git_fixture import GitRepoTestCase

NEW_BODY = "def greet(name):\n    return f'Hi, {name}!'\n"


class TestCheckPatch(GitRepoTestCase):
    def setUp(self):
        super().setUp()
        self.original = self.seed()
        self.patch = self.patch_for("src/app.py", NEW_BODY)

    def test_a_generated_patch_applies(self):
        applies, error = check_patch(self.patch, cwd=self.dir)
        self.assertTrue(applies, error)
        self.assertEqual(error, "")

    def test_checking_writes_nothing(self):
        before = self.status_porcelain()
        check_patch(self.patch, cwd=self.dir)
        self.assertEqual(self.status_porcelain(), before)
        self.assertEqual(self.read("src/app.py"), self.original)

    def test_text_that_is_not_a_patch_is_refused(self):
        applies, error = check_patch("this is not a patch at all\n", cwd=self.dir)
        self.assertFalse(applies)
        self.assertTrue(error)

    def test_a_patch_whose_context_moved_is_refused(self):
        self.commit("src/app.py", "def greet(who):\n    return who\n")
        applies, _ = check_patch(self.patch, cwd=self.dir)
        self.assertFalse(applies)


class TestApplyPatch(GitRepoTestCase):
    def setUp(self):
        super().setUp()
        self.original = self.seed()
        self.patch = self.patch_for("src/app.py", NEW_BODY)

    def test_applying_writes_the_file(self):
        applied, error = apply_patch(self.patch, cwd=self.dir)
        self.assertTrue(applied, error)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)

    def test_a_refused_patch_leaves_the_file_untouched(self):
        before = self.status_porcelain()
        applied, error = apply_patch("--- a/nope\n+++ b/nope\n@@ -1,1 +1,1 @@\n-a\n+b\n", cwd=self.dir)
        self.assertFalse(applied)
        self.assertTrue(error)
        self.assertEqual(self.status_porcelain(), before)

    def test_the_file_becomes_dirty(self):
        apply_patch(self.patch, cwd=self.dir)
        self.assertIn("src/app.py", modified_files(cwd=self.dir))


class TestReversePatch(GitRepoTestCase):
    def setUp(self):
        super().setUp()
        self.original = self.seed()
        self.patch = self.patch_for("src/app.py", NEW_BODY)

    def test_reversing_restores_the_original(self):
        apply_patch(self.patch, cwd=self.dir)
        self.assertEqual(self.read("src/app.py"), NEW_BODY)

        reverted, error = reverse_patch(self.patch, cwd=self.dir)
        self.assertTrue(reverted, error)
        self.assertEqual(self.read("src/app.py"), self.original)
        self.assertEqual(self.status_porcelain(), "")

    def test_reversing_something_never_applied_is_refused(self):
        before = self.status_porcelain()
        reverted, error = reverse_patch(self.patch, cwd=self.dir)
        self.assertFalse(reverted)
        self.assertTrue(error)
        self.assertEqual(self.status_porcelain(), before)

    def test_reversing_after_an_external_edit_is_refused(self):
        # The tree no longer holds what the patch expects, so the reverse must
        # fail loudly instead of writing a half-correct file.
        apply_patch(self.patch, cwd=self.dir)
        self.write("src/app.py", "def greet(name):\n    return name\n")
        reverted, error = reverse_patch(self.patch, cwd=self.dir)
        self.assertFalse(reverted)
        self.assertTrue(error)
        self.assertEqual(self.read("src/app.py"), "def greet(name):\n    return name\n")


class TestBranchOperations(GitRepoTestCase):
    def setUp(self):
        super().setUp()
        self.original = self.seed()

    def test_create_branch_switches_and_keeps_the_commit(self):
        head_before = current_head(cwd=self.dir)
        created, error = create_branch("fix/gitpr-20260913120000", cwd=self.dir)
        self.assertTrue(created, error)
        self.assertEqual(current_branch(cwd=self.dir), "fix/gitpr-20260913120000")
        self.assertEqual(current_head(cwd=self.dir), head_before)

    def test_the_original_branch_keeps_its_commit(self):
        head_before = self._git("rev-parse", "main").stdout.strip()
        patch = self.patch_for("src/app.py", NEW_BODY)
        create_branch("fix/gitpr-x", cwd=self.dir)
        apply_patch(patch, cwd=self.dir)

        # main's side of the history is untouched. The applied change is
        # uncommitted, so git carries it across a checkout — which is why the
        # assertion reads the commit and not the file, and why undoing a fix is
        # `git apply --reverse` rather than a reset.
        self.assertEqual(self._git("rev-parse", "main").stdout.strip(), head_before)
        self.assertEqual(self._git("show", "main:src/app.py").stdout, self.original)
        self._git("checkout", "main")
        self.assertEqual(self.read("src/app.py"), NEW_BODY)

    def test_an_existing_name_is_refused(self):
        created, error = create_branch("main", cwd=self.dir)
        self.assertFalse(created)
        self.assertTrue(error)
        self.assertEqual(current_branch(cwd=self.dir), "main")

    def test_an_invalid_name_is_refused(self):
        created, error = create_branch("fix/../oops", cwd=self.dir)
        self.assertFalse(created)
        self.assertTrue(error)


class TestRepositoryQueries(GitRepoTestCase):
    def test_repo_root_is_the_fixture_directory(self):
        root = repo_root(cwd=self.dir)
        self.assertIsNotNone(root)
        self.assertEqual(
            os.path.normcase(root), os.path.normcase(os.path.realpath(self.dir))
        )

    def test_outside_a_repository_there_is_no_root(self):
        outside = tempfile.mkdtemp(prefix="gitpr_fix_not_a_repo_")
        self.addCleanup(shutil.rmtree, outside, ignore_errors=True)
        # A temp directory normally sits outside every repository, but a system
        # TMPDIR can be nested inside one — so the assertion is that the root
        # never turns out to be the directory itself.
        root = repo_root(cwd=outside)
        self.assertNotEqual(
            os.path.normcase(root or ""), os.path.normcase(os.path.realpath(outside))
        )

    def test_is_git_repository(self):
        self.assertTrue(is_git_repository(cwd=self.dir))

    def test_modified_files_lists_untracked_and_changed(self):
        self.seed()
        self.write("src/app.py", "changed\n")
        self.write("notes.txt", "untracked\n")
        files = modified_files(cwd=self.dir)
        self.assertIn("src/app.py", files)
        self.assertIn("notes.txt", files)

    def test_modified_files_is_empty_on_a_clean_tree(self):
        self.seed()
        self.assertEqual(modified_files(cwd=self.dir), ())


if __name__ == "__main__":
    unittest.main()
