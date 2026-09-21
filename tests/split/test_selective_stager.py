"""Acceptance 4 and 5 — staging a subset, and refusing the subsets that cannot be.

This is the module that writes to a real index, so every assertion here is made
against git's own answer — ``git diff --cached``, ``--name-only``, ``--numstat``
— and never against the stager's internal state. A stager that believes it
staged something is worth nothing.

The conflict tests are the interesting ones. A conflict cannot be built by
choosing two awkward hunks out of a real ``-U3`` diff: git merges any two
changes closer than seven lines apart into a single hunk, which leaves three
lines of untouched context between the hunks it does emit, so any subset of
them applies cleanly. The two ways a group really is refused are a newline
mismatch and two hunks covering the same lines, and both are exercised below.
"""
import dataclasses
import os
import unittest

from src.infrastructure.git.patch_applier import run_git
from src.infrastructure.git.selective_stager import (
    HunkConflictError,
    check_units,
    index_is_clean,
    stage_hunks,
    staged_numstat,
    staged_paths,
    unstage_all,
)
from src.split.hunk_parser import parse_units
from tests.split.git_fixture import SplitRepoTestCase


class StageSubsetTest(SplitRepoTestCase):
    """Acceptance 4 — exactly the hunks asked for, and nothing else."""

    def three_hunks(self):
        """Two concerns in ``src/app.py``, a third in ``src/notes.md``."""
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/app.py", 38, "app_38_fixed")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        return parse_units(self.diff_now())

    def test_staging_two_of_three_hunks_leaves_the_third_out(self):
        units = self.three_hunks()

        stage_hunks([units[0], units[2]], self.dir)

        staged = run_git(["diff", "--cached"], cwd=self.dir).stdout
        self.assertIn("app_03_fixed", staged)
        self.assertIn("notes_05_documented", staged)
        self.assertNotIn("app_38_fixed", staged)

    def test_the_unstaged_hunks_stay_in_the_working_tree(self):
        units = self.three_hunks()

        stage_hunks([units[0]], self.dir)

        # Uncommitted and unstaged, but still on disk: staging a subset must
        # not write to the working tree at all.
        self.assertIn("app_38_fixed", self.read("src/app.py"))
        self.assertIn("notes_05_documented", self.read("src/notes.md"))

        remaining = run_git(["diff"], cwd=self.dir).stdout
        self.assertIn("app_38_fixed", remaining)
        self.assertNotIn("app_03_fixed", remaining)

    def test_only_the_staged_files_are_reported(self):
        units = self.three_hunks()

        stage_hunks([units[2]], self.dir)

        self.assertEqual(staged_paths(self.dir), ("src/notes.md",))
        self.assertEqual(staged_numstat(self.dir), {"src/notes.md": (1, 1)})

    def test_hunks_of_one_file_split_across_commits(self):
        """The point of the whole feature: one file, two concerns, two stages."""
        units = self.three_hunks()

        stage_hunks([units[0]], self.dir)
        self.assertEqual(staged_numstat(self.dir), {"src/app.py": (1, 1)})

        unstage_all(self.dir)
        stage_hunks([units[1]], self.dir)

        staged = run_git(["diff", "--cached"], cwd=self.dir).stdout
        self.assertIn("app_38_fixed", staged)
        self.assertNotIn("app_03_fixed", staged)


class IndexStateTest(SplitRepoTestCase):
    """The index preconditions the apply loop relies on."""

    def test_index_is_clean_before_and_dirty_after(self):
        self.edit_line("src/app.py", 3, "app_03_fixed")
        units = parse_units(self.diff_now())

        self.assertTrue(index_is_clean(self.dir))

        stage_hunks(units, self.dir)
        self.assertFalse(index_is_clean(self.dir))

        unstage_all(self.dir)
        self.assertTrue(index_is_clean(self.dir))

    def test_unstage_all_keeps_the_working_tree(self):
        self.edit_line("src/app.py", 3, "app_03_fixed")
        units = parse_units(self.diff_now())
        stage_hunks(units, self.dir)

        unstage_all(self.dir)

        # The change is back where it started: on disk, uncommitted, unstaged.
        self.assertIn("app_03_fixed", self.read("src/app.py"))
        self.assertEqual(staged_paths(self.dir), ())
        self.assertIn("app_03_fixed", self.diff_now())

    def test_staging_nothing_is_a_programming_error(self):
        with self.assertRaises(ValueError):
            stage_hunks([], self.dir)

    def test_check_units_answers_without_mutating(self):
        self.edit_line("src/app.py", 3, "app_03_fixed")
        units = parse_units(self.diff_now())

        ok, error = check_units(units, self.dir)

        self.assertTrue(ok, error)
        self.assertEqual(error, "")
        self.assertTrue(index_is_clean(self.dir))

    def test_check_units_reports_a_patch_that_cannot_apply(self):
        self.edit_line("src/app.py", 3, "app_03_fixed")
        units = parse_units(self.diff_now())
        # A hunk whose context no longer exists — what a stale or mistranslated
        # hunk looks like to git.
        stale = dataclasses.replace(
            units[0],
            content=units[0].content.replace("app_02", "app_99"),
            id="stale",
        )

        ok, error = check_units([stale], self.dir)

        self.assertFalse(ok)
        self.assertIn("does not apply", error)
        self.assertTrue(index_is_clean(self.dir))


class ConflictTest(SplitRepoTestCase):
    """Acceptance 5 — a refused group raises, carrying the units it was for."""

    def test_overlapping_hunks_are_refused(self):
        """Two hunks covering the same lines cannot both reach the index."""
        self.edit_line("src/app.py", 3, "app_03_fixed")
        units = parse_units(self.diff_now())
        twin = dataclasses.replace(units[0], id="twin", ordinal=99)

        with self.assertRaises(HunkConflictError) as caught:
            stage_hunks([units[0], twin], self.dir)

        self.assertEqual([unit.id for unit in caught.exception.units], [units[0].id, "twin"])
        self.assertTrue(caught.exception.error)
        self.assertTrue(index_is_clean(self.dir))

    def test_a_crlf_file_is_refused_rather_than_half_applied(self):
        """The accepted limitation, pinned as a guarantee.

        The diff is read with universal newlines and the file-level split strips
        the remaining carriage returns, so the rebuilt patch carries LF context
        lines for a file whose lines end in CRLF. Git refuses it — which is the
        outcome the design wants: a loud failure, never an index holding content
        that differs from the working tree.
        """
        crlf = b"alpha\r\nbravo\r\ncharlie\r\ndelta\r\necho\r\n"
        path = os.path.join(self.dir, "src", "legacy.txt")
        with open(path, "wb") as handle:
            handle.write(crlf)
        self._git("add", "--", "src/legacy.txt")
        self._git("commit", "-m", "chore: seed crlf")
        with open(path, "wb") as handle:
            handle.write(crlf.replace(b"bravo", b"BRAVO"))

        units = parse_units(self.diff_now())
        self.assertEqual(len(units), 1)

        with self.assertRaises(HunkConflictError) as caught:
            stage_hunks(units, self.dir)

        self.assertIn("does not apply", caught.exception.error)
        self.assertEqual([unit.id for unit in caught.exception.units], [units[0].id])
        self.assertTrue(index_is_clean(self.dir))
        self.assertIn("BRAVO", self.read("src/legacy.txt"))


if __name__ == "__main__":
    unittest.main()
