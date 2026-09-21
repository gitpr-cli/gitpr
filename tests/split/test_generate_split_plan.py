"""Acceptance 6 and 7 — the plan reads, and the message pipeline is shared.

Two of the ten acceptance criteria are about the *shape* of the solution rather
than about an answer: that building a plan writes nothing (6), and that a
group's commit message comes from the same function the default commit flow
uses, with no second implementation of it anywhere (7). Both are contract
tests, and both pass for the wrong reason if written loosely — "nothing was
written" is only meaningful against a fingerprint that covers the index as well
as the files, and "the shared pipeline was used" is only meaningful against the
patch that was handed to it.

The rest of the file covers the units the model never sees, and the one
conflict a real ``-U3`` diff can produce: a CRLF file.
"""
import os
import unittest

from src.split.generate_split_plan import generate_split_plan
from src.split.hunk_parser import build_patch, parse_units
from src.split.split_plan import Hunk, OpaqueSection, SplitError
from tests.split.git_fixture import SplitRepoTestCase


class PlanTestCase(SplitRepoTestCase):
    """The scaffolding both of the classes below plan with."""

    MESSAGE = "chore: a message"

    def plan_for(self, diff, ai, **kwargs):
        """``(plan, mocks)`` — every AI edge stubbed, every git call real."""
        kwargs.setdefault("repo_path", self.dir)
        kwargs.setdefault("quiet", True)
        with self.stubbed(ai=ai, commit_message=self.MESSAGE) as mocks:
            plan = generate_split_plan(diff, **kwargs)
        return plan, mocks

    @staticmethod
    def group(*ids, label="fix", justification="because"):
        return {
            "unit_ids": list(ids),
            "intent_label": label,
            "justification": justification,
        }

    @staticmethod
    def hunk_ids(units):
        return [unit.id for unit in units if isinstance(unit, Hunk)]

    @staticmethod
    def opaque_units(units):
        return [unit for unit in units if isinstance(unit, OpaqueSection)]

    def prompt_sent(self, mocks):
        """The prompt ``call_ai_model`` was handed — positional argument 4."""
        return mocks["ai"].call_args.args[3]

    def fingerprint(self):
        """Everything a write could change: the files, the index, and HEAD."""
        return (
            self.read("src/app.py"),
            self.read("src/notes.md"),
            self.status_porcelain(),
            self._git("rev-parse", "HEAD").stdout,
        )


class PlanTest(PlanTestCase):
    """The plan, its numbering, and the calls it makes to get there."""

    def mixed_tree(self):
        """Three concerns: two in ``src/app.py``, one in ``src/notes.md``."""
        self.edit_line("src/app.py", 3, "app_03_fixed")
        self.edit_line("src/app.py", 38, "app_38_tidied")
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        return self.diff_now()

    # ── the plan itself ──────────────────────────────────────────────────
    def test_the_groups_come_back_numbered_and_messaged(self):
        diff = self.mixed_tree()
        ids = [unit.id for unit in parse_units(diff)]

        plan, _ = self.plan_for(
            diff,
            {
                "groups": [
                    self.group(ids[0], ids[1], label="fix: two bugs"),
                    self.group(ids[2], label="docs: a note"),
                ]
            },
        )

        self.assertEqual([group.group_id for group in plan.groups], ["G1", "G2"])
        self.assertEqual([group.intent_label for group in plan.groups],
                         ["fix: two bugs", "docs: a note"])
        self.assertEqual(plan.groups[0].file_paths, ("src/app.py",))
        self.assertEqual(plan.groups[1].file_paths, ("src/notes.md",))
        self.assertEqual(
            [group.generated_commit_message for group in plan.groups],
            [self.MESSAGE, self.MESSAGE],
        )
        self.assertEqual(plan.total_groups, 2)

    def test_every_unit_reaches_a_group_or_the_ungrouped_list(self):
        diff = self.mixed_tree()
        ids = [unit.id for unit in parse_units(diff)]

        plan, _ = self.plan_for(diff, {"groups": [self.group(ids[0])]})

        seen = [unit.id for group in plan.groups for unit in group.units]
        seen += [unit.id for unit in plan.ungrouped_units]
        self.assertEqual(sorted(seen), sorted(ids))
        self.assertEqual(plan.total_units, 3)

    def test_an_empty_diff_is_a_split_error_and_costs_nothing(self):
        with self.stubbed(ai={"groups": []}) as mocks:
            with self.assertRaises(SplitError):
                generate_split_plan("   \n", repo_path=self.dir)

        mocks["ai"].assert_not_called()
        mocks["message"].assert_not_called()

    def test_untracked_files_are_named_in_a_warning(self):
        diff = self.mixed_tree()
        ids = [unit.id for unit in parse_units(diff)]

        plan, _ = self.plan_for(
            diff,
            {"groups": [self.group(*ids)]},
            untracked=["src/scratch.py", "notes.txt"],
        )

        warning = " ".join(plan.warnings)
        self.assertIn("src/scratch.py", warning)
        self.assertIn("2 untracked file(s)", warning)
        # Out of scope, so absent from the plan entirely — but not from the report.
        self.assertEqual(plan.total_units, 3)

    # ── acceptance 6 ─────────────────────────────────────────────────────
    def test_building_a_plan_writes_nothing(self):
        """The plan is a proposal. Proposing touches no file, no index, no HEAD."""
        diff = self.mixed_tree()
        before = self.fingerprint()
        ids = [unit.id for unit in parse_units(diff)]

        plan, _ = self.plan_for(diff, {"groups": [self.group(ids[0])]})

        self.assertEqual(plan.total_groups, 1)
        self.assertEqual(self.fingerprint(), before)

    def test_building_a_plan_writes_nothing_even_when_it_conflicts(self):
        """Acceptance 6 in the state where keeping read-only is hardest: a group
        the pre-validation has to refuse. That check runs against a HEAD index
        built in a temporary file precisely so this leaves no trace."""
        self.seed_crlf_file()
        diff = self.diff_now()
        before = self.fingerprint()
        ids = [unit.id for unit in parse_units(diff)]

        plan, _ = self.plan_for(diff, {"groups": [self.group(*ids)]})

        self.assertEqual(plan.groups, [])
        self.assertEqual(self.fingerprint(), before)

    # ── acceptance 7 ─────────────────────────────────────────────────────
    def test_each_message_comes_from_the_shared_commit_pipeline(self):
        """The contract: one call to ``generate_pr_content`` per group, with
        that group's *rebuilt patch*. A message generated from the whole diff,
        or by a second implementation of the prompt, fails here."""
        diff = self.mixed_tree()
        ids = [unit.id for unit in parse_units(diff)]

        plan, mocks = self.plan_for(
            diff,
            {"groups": [self.group(ids[0], ids[1]), self.group(ids[2])]},
        )

        calls = mocks["message"].call_args_list
        self.assertEqual(len(calls), 2)
        for call, group in zip(calls, plan.groups):
            self.assertEqual(call.args[:2], ("commit", "commit"))
            self.assertEqual(call.kwargs["provider"], "gemini")
            self.assertEqual(call.args[2], build_patch(group.units))

    def test_a_message_is_written_from_its_own_group_alone(self):
        """The consequence of the contract above, stated in content rather than
        in call shape: group 1's patch carries group 1's change and not group
        2's, so the message cannot describe a commit that was never made."""
        diff = self.mixed_tree()
        ids = [unit.id for unit in parse_units(diff)]

        _, mocks = self.plan_for(
            diff, {"groups": [self.group(ids[0]), self.group(ids[2])]}
        )

        first, second = (call.args[2] for call in mocks["message"].call_args_list)
        self.assertIn("app_03_fixed", first)
        self.assertNotIn("notes_05_documented", first)
        self.assertIn("notes_05_documented", second)
        self.assertNotIn("app_03_fixed", second)

    # ── a group the pre-validation cannot save ───────────────────────────
    def seed_crlf_file(self):
        """Commit a CRLF file, then change it.

        The diff is read with universal newlines and ``split_patch_sections``
        strips the remaining carriage returns, so the rebuilt patch carries LF
        context lines for a file whose lines end in CRLF. Git refuses it — the
        one conflict a real ``-U3`` diff can produce, and the loud failure the
        design prefers to an index holding content that differs from the tree.
        """
        crlf = b"alpha\r\nbravo\r\ncharlie\r\n"
        path = os.path.join(self.dir, "src", "legacy.txt")
        with open(path, "wb") as handle:
            handle.write(crlf)
        self._git("add", "--", "src/legacy.txt")
        self._git("commit", "-m", "chore: seed crlf")
        with open(path, "wb") as handle:
            handle.write(crlf.replace(b"bravo", b"BRAVO"))

    def test_a_group_that_cannot_be_staged_is_left_ungrouped(self):
        self.seed_crlf_file()
        diff = self.diff_now()
        ids = [unit.id for unit in parse_units(diff)]

        plan, mocks = self.plan_for(diff, {"groups": [self.group(*ids)]})

        self.assertEqual(plan.groups, [])
        self.assertEqual([unit.id for unit in plan.ungrouped_units], ids)
        self.assertIn("could not be staged", " ".join(plan.warnings))
        # Nothing survives to be committed, so no message is written for it.
        mocks["message"].assert_not_called()


class OpaqueTest(PlanTestCase):
    """Sections with no hunks: each a commit of its own, none of them the AI's."""

    def test_a_mode_change_becomes_its_own_group_and_never_reaches_the_ai(self):
        self.edit_line("src/notes.md", 5, "notes_05_documented")
        self._git("update-index", "--chmod=+x", "src/app.py")
        diff = self.diff_now()

        units = parse_units(diff)
        self.assertEqual([unit.reason for unit in self.opaque_units(units)], ["mode"])
        mode_unit = self.opaque_units(units)[0]

        plan, mocks = self.plan_for(
            diff, {"groups": [self.group(*self.hunk_ids(units), label="docs")]}
        )

        self.assertEqual([group.intent_label for group in plan.groups], ["docs", "mode"])
        self.assertEqual(plan.groups[1].file_paths, ("src/app.py",))
        # Absent from the prompt: there is no grouping decision to ask about an
        # indivisible change, so the model is never asked — and a unit it cannot
        # reason about is a unit it would invent a plausible id for.
        self.assertNotIn(mode_unit.id, self.prompt_sent(mocks))

    def test_a_pure_rename_is_one_group_and_needs_no_ai_at_all(self):
        """``-M`` is load-bearing: without rename detection this arrives as a
        deletion plus an untracked addition, and split would commit the bare
        deletion while the new file sat untracked beside it."""
        self._git("mv", "src/notes.md", "src/readme.md")
        diff = self.diff_now()

        units = parse_units(diff)
        self.assertEqual([unit.reason for unit in self.opaque_units(units)], ["rename"])

        plan, mocks = self.plan_for(diff, {"groups": []})

        self.assertEqual([group.intent_label for group in plan.groups], ["rename"])
        self.assertEqual(plan.groups[0].file_paths, ("src/readme.md",))
        # Nothing to group, so nothing to ask.
        mocks["ai"].assert_not_called()

    def test_a_rename_carrying_changes_keeps_its_rename_header(self):
        """A renamed *and* modified file is a hunk-bearing section, and the
        rename lives in its file header — stored, never reconstructed, because
        ``rename from``/``rename to`` are not recoverable from a path."""
        self._git("mv", "src/notes.md", "src/readme.md")
        self.edit_line("src/readme.md", 5, "notes_05_documented")
        diff = self.diff_now()

        units = parse_units(diff)
        self.assertEqual(self.opaque_units(units), [])
        hunk = units[0]

        self.assertIn("rename from src/notes.md", hunk.file_header)
        patch = build_patch([hunk])
        self.assertIn("rename from src/notes.md", patch)
        self.assertIn("rename to src/readme.md", patch)
        self.assertIn("notes_05_documented", patch)


if __name__ == "__main__":
    unittest.main()
