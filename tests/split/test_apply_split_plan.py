"""Acceptance 3, 8 and 9 — the commits a plan becomes, and what survives a failure.

Three claims, and each is checked against the repository rather than against the
result object:

* **3** — the files on disk afterwards are byte-identical to the files on disk
  before. The split redistributes the work across commits; it never changes it.
* **8** — one commit per group, in the plan's order, each holding exactly its
  group's changes and no other group's.
* **9** — when a commit fails mid-sequence, the commits already made survive,
  the run stops cleanly, and the report says which groups were applied and
  which were not. There is no automatic rollback: the commits are real and the
  user undoes them with ``git reset`` if they want to.

The failure in 9 is a real ``pre-commit`` hook that refuses one specific commit,
which is the only honest way to test it — the alternative is to mock the commit
function and then assert things about a repository that was never touched.

Two of the tests below deliberately order groups so that a file is committed in
two separate commits (one hunk first, the other later). That is the case the
whole command exists for, and the case where applying the second group meets an
index whose line numbering has already moved.
"""
import os
import unittest

from src.infrastructure.git.patch_applier import run_git
from src.infrastructure.git.selective_stager import index_is_clean, staged_paths
from src.split.apply_split_plan import apply_split_plan
from src.split.hunk_parser import parse_units
from tests.split.git_fixture import SplitRepoTestCase

HOOK = """#!/bin/sh
# A commit-msg hook that refuses any commit whose message mentions REJECT, so a
# test can fail exactly one commit in the middle of a sequence.
#
# commit-msg and not pre-commit: git runs pre-commit *before* it writes the
# message out, so a pre-commit hook cannot see it — keying on the message there
# silently matches the previous commit's, or nothing at all.
if grep -q "REJECT" "$1" 2>/dev/null; then
  echo "test hook: rejecting this commit" 1>&2
  exit 1
fi
exit 0
"""


class ApplyTest(SplitRepoTestCase):
    """Acceptance 3 and 8 — the end state, and the commits on the way there."""

    #: The three concerns, named by the text each change introduces. Named
    #: rather than indexed because a unit's ordinal is the *diff's* order —
    #: which is by path, so both of ``src/app.py``'s hunks precede
    #: ``src/notes.md``'s — and a test that indexes into that is asserting the
    #: order git happens to print files in.
    MARKERS = ("app_03_fixed", "notes_05_documented", "app_38_tidied")

    def mixed_tree(self):
        """Three concerns: line 3 of app.py, line 5 of notes.md, line 38 of app.py.

        Two of the three are hunks of the *same file*, which is the case worth
        testing — and the plan commits them in the order the model returned
        them, so app.py is staged twice against two different index states.
        """
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        self.edit_line("src/app.py", 38, "app_38_tidied")
        return self.diff_now()

    @staticmethod
    def hunk_for(units, marker):
        """The unit whose changed text is *marker*."""
        return next(unit for unit in units if marker in unit.content)

    def three_group_plan(self, labels=("fix: the bug", "docs: the note", "refactor: line 38")):
        """A plan over :meth:`mixed_tree`, one group per concern, in marker order."""
        diff = self.mixed_tree()
        units = parse_units(diff)
        plan, _ = self.plan_with(
            diff,
            {
                "groups": [
                    self.grouped(self.hunk_for(units, marker).id, label=label)
                    for marker, label in zip(self.MARKERS, labels)
                ]
            },
            commit_message="MESSAGE",
        )
        # One message per group, so the order of the commits is readable in
        # ``git log``. The stubbed pipeline returns a single string for every
        # group, which would make every commit identical in the log.
        for group, label in zip(plan.groups, labels):
            group.generated_commit_message = label
        return plan

    # ── acceptance 3 ─────────────────────────────────────────────────────
    def test_the_files_on_disk_are_byte_identical_afterwards(self):
        plan = self.three_group_plan()
        before = self.snapshot()

        result = apply_split_plan(plan, self.dir)

        self.assertTrue(result.completed, result.error)
        self.assertEqual(self.snapshot(), before)

    def test_the_tree_is_clean_and_the_work_is_in_the_commits(self):
        """The other half of acceptance 3: nothing is left dangling. Every
        change is committed, so ``git status`` has nothing to report."""
        plan = self.three_group_plan()

        apply_split_plan(plan, self.dir)

        self.assertEqual(self.status_porcelain(), "")
        self.assertTrue(index_is_clean(self.dir))
        for marker in ("app_03_fixed", "notes_05_documented", "app_38_tidied"):
            self.assertNotIn(marker, self.diff_now())

    # ── acceptance 8 ─────────────────────────────────────────────────────
    def test_one_commit_per_group_in_the_plan_order(self):
        plan = self.three_group_plan(labels=("fix: the bug", "docs: the note", "refactor: tidy"))

        result = apply_split_plan(plan, self.dir)

        self.assertTrue(result.completed, result.error)
        self.assertEqual(result.committed_group_ids, ["G1", "G2", "G3"])
        # Newest first, so the log reads the plan backwards.
        subjects = self._git("log", "-3", "--format=%s").stdout.splitlines()
        self.assertEqual(subjects, ["refactor: tidy", "docs: the note", "fix: the bug"])

    def test_each_commit_holds_exactly_its_group(self):
        """The load-bearing assertion of the whole feature, made against
        ``git show``: the commit holding line 3 must not hold line 38."""
        plan = self.three_group_plan()

        result = apply_split_plan(plan, self.dir)

        self.assertTrue(result.completed, result.error)
        shown = [self._git("show", sha).stdout for _, sha in result.commits]
        expected = [
            ("app_03_fixed", "notes_05_documented", "app_38_tidied"),
            ("notes_05_documented", "app_03_fixed", "app_38_tidied"),
            ("app_38_tidied", "app_03_fixed", "notes_05_documented"),
        ]
        for diff_text, (present, *absent) in zip(shown, expected):
            self.assertIn(present, diff_text)
            for marker in absent:
                self.assertNotIn(marker, diff_text)

    def test_each_commit_touches_only_its_own_files(self):
        plan = self.three_group_plan()

        result = apply_split_plan(plan, self.dir)

        self.assertTrue(result.completed, result.error)
        touched = [
            self._git("show", "--name-only", "--format=", sha).stdout.split()
            for _, sha in result.commits
        ]
        self.assertEqual(touched, [["src/app.py"], ["src/notes.md"], ["src/app.py"]])

    def test_the_commits_carry_the_messages_the_plan_generated(self):
        plan = self.three_group_plan()

        result = apply_split_plan(plan, self.dir)

        self.assertTrue(result.completed, result.error)
        for (group_id, sha), group in zip(result.commits, plan.groups):
            self.assertEqual(group.group_id, group_id)
            self.assertEqual(
                self._git("log", "-1", "--format=%s", sha).stdout.strip(),
                group.generated_commit_message,
            )

    def test_a_plan_with_no_groups_is_refused_before_anything_runs(self):
        plan = self.three_group_plan()
        plan.groups = []
        before = self.snapshot()

        from src.split.split_plan import SplitError

        with self.assertRaises(SplitError):
            apply_split_plan(plan, self.dir)

        self.assertEqual(self.snapshot(), before)


class FailureMidSequenceTest(SplitRepoTestCase):
    """Acceptance 9 — the run stops cleanly, and the report is accurate."""

    def install_hook(self):
        """Refuse any commit whose message mentions REJECT."""
        hooks = os.path.join(self.dir, ".git", "hooks")
        os.makedirs(hooks, exist_ok=True)
        path = os.path.join(hooks, "commit-msg")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(HOOK)
        os.chmod(path, 0o755)

    def failing_plan(self):
        """Three groups where the second is the one git refuses.

        The message is what the hook matches on, so it is set per group rather
        than through the stubbed pipeline, which returns one string for all of
        them.
        """
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        self.edit_line("src/app.py", 38, "app_38_tidied")
        diff = self.diff_now()
        units = parse_units(diff)
        markers = ("app_03_fixed", "notes_05_documented", "app_38_tidied")
        messages = ("fix: first", "REJECT this one", "refactor: third")

        plan, _ = self.plan_with(
            diff,
            {
                "groups": [
                    self.grouped(ApplyTest.hunk_for(units, marker).id, label=message)
                    for marker, message in zip(markers, messages)
                ]
            },
            commit_message="MESSAGE",
        )
        for group, message in zip(plan.groups, messages):
            group.generated_commit_message = message
        return plan

    def test_the_commits_already_made_survive(self):
        self.install_hook()
        plan = self.failing_plan()
        commits_before = self._git("rev-list", "--count", "HEAD").stdout.strip()

        result = apply_split_plan(plan, self.dir)

        self.assertEqual(result.committed_group_ids, ["G1"])
        self.assertEqual(
            self._git("rev-list", "--count", "HEAD").stdout.strip(),
            str(int(commits_before) + 1),
        )
        self.assertEqual(self._git("log", "-1", "--format=%s").stdout.strip(), "fix: first")

    def test_the_run_stops_and_says_where(self):
        self.install_hook()
        plan = self.failing_plan()

        result = apply_split_plan(plan, self.dir)

        self.assertFalse(result.completed)
        self.assertEqual(result.stopped_at, "G2")
        self.assertIn("test hook: rejecting this commit", result.error)
        self.assertTrue(result.staged_but_not_committed)

    def test_the_refused_group_stays_staged_for_the_user_to_commit(self):
        """A failed *commit* is not a failed *stage*: the group is in the index
        and correct, and unstaging it would discard the only in-flight state."""
        self.install_hook()
        plan = self.failing_plan()

        result = apply_split_plan(plan, self.dir)

        self.assertEqual(staged_paths(self.dir), ("src/notes.md",))
        self.assertFalse(index_is_clean(self.dir))
        self.assertIn("notes_05_documented", run_git(["diff", "--cached"], cwd=self.dir).stdout)

    def test_the_report_names_what_was_left_behind(self):
        """Groups 2 and 3 were not committed, so their units are the ones still
        in the working tree — and the user is told their ids, not left to work
        it out from ``git status``."""
        self.install_hook()
        plan = self.failing_plan()
        ids = [unit.id for unit in parse_units(self.diff_now())]

        result = apply_split_plan(plan, self.dir)

        reported = [unit.id for unit in result.uncommitted_units]
        self.assertEqual(len(reported), 2)
        self.assertNotIn(ids[0], reported)
        self.assertEqual(sorted(reported), sorted([ids[1], ids[2]]))


if __name__ == "__main__":
    unittest.main()
