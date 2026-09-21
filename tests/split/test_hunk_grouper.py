"""Acceptance 2 — a bad grouping answer costs a grouping decision, never a change.

The model is the least trustworthy part of this pipeline and the answer it gives
is the least structured thing in it, so the tests here are mostly about the
answers it should not be able to give: ids that do not exist, ids repeated
across groups, groups with nothing in them, more groups than were asked for,
prose where JSON was requested.

The invariant under all of them is one line long, and one test states it
directly: every unit that went in comes out either in a group or in the
ungrouped list, exactly once.
"""
import unittest

# `_select_for_prompt` is private and imported anyway: which unit survives the
# trim is a fact about the trimmer, and a test that reimplemented it would be
# asserting against its own copy.
from src.split.hunk_grouper import (
    MAX_BODY_LINES,
    _select_for_prompt,
    group_units,
    grouping_prompt,
)
from src.split.hunk_parser import parse_units
from src.split.split_plan import SplitError
from tests.split.git_fixture import SplitRepoTestCase

#: Three hunks across two files — enough for a real partition, small enough to
#: read.
DIFF = (
    "diff --git a/a.txt b/a.txt\n"
    "index 1111111..2222222 100644\n"
    "--- a/a.txt\n"
    "+++ b/a.txt\n"
    "@@ -1,3 +1,3 @@\n"
    " a1\n"
    "-a2\n"
    "+a2x\n"
    " a3\n"
    "@@ -10,3 +10,3 @@\n"
    " a10\n"
    "-a11\n"
    "+a11x\n"
    " a12\n"
    "diff --git a/b.txt b/b.txt\n"
    "index 3333333..4444444 100644\n"
    "--- a/b.txt\n"
    "+++ b/b.txt\n"
    "@@ -1,3 +1,3 @@\n"
    " b1\n"
    "-b2\n"
    "+b2x\n"
    " b3\n"
)


class GroupingTest(SplitRepoTestCase):
    """The answer, validated against the units that were actually sent."""

    def setUp(self):
        super().setUp()
        self.units = parse_units(DIFF)
        self.ids = [unit.id for unit in self.units]

    def group(self, payload, **kwargs):
        kwargs.setdefault("max_groups", 5)
        with self.stubbed(ai=payload):
            return group_units(self.units, **kwargs)

    # ── the happy path ───────────────────────────────────────────────────
    def test_a_valid_answer_becomes_groups(self):
        groups, ungrouped, warnings = self.group(
            {
                "groups": [
                    {
                        "unit_ids": [self.ids[0], self.ids[2]],
                        "intent_label": "fix: the two bugs",
                        "justification": "both correct the same off-by-one",
                    },
                    {
                        "unit_ids": [self.ids[1]],
                        "intent_label": "refactor: rename",
                        "justification": "no behaviour change",
                    },
                ]
            }
        )

        self.assertEqual([group.group_id for group in groups], ["G1", "G2"])
        self.assertEqual([group.intent_label for group in groups],
                         ["fix: the two bugs", "refactor: rename"])
        self.assertEqual([unit.id for unit in groups[0].units], [self.ids[0], self.ids[2]])
        self.assertEqual([unit.id for unit in groups[1].units], [self.ids[1]])
        self.assertEqual(ungrouped, [])
        self.assertEqual(warnings, [])

    def test_groups_carry_their_files(self):
        groups, _, _ = self.group(
            {"groups": [{"unit_ids": self.ids, "intent_label": "x", "justification": "y"}]}
        )

        self.assertEqual(groups[0].file_paths, ("a.txt", "b.txt"))
        self.assertTrue(groups[0].has_hunks)

    # ── answers that must not be believed ────────────────────────────────
    def test_unknown_ids_are_discarded_with_a_warning(self):
        """Acceptance 2: no ghost unit ever enters a group, and nothing raises."""
        groups, ungrouped, warnings = self.group(
            {
                "groups": [
                    {
                        "unit_ids": [self.ids[0], "9999-deadbeef"],
                        "intent_label": "fix",
                        "justification": "…",
                    }
                ]
            }
        )

        self.assertEqual([unit.id for unit in groups[0].units], [self.ids[0]])
        self.assertIn("9999-deadbeef", " ".join(warnings))
        self.assertEqual(len(groups), 1)

    def test_a_group_of_only_unknown_ids_disappears(self):
        groups, ungrouped, warnings = self.group(
            {
                "groups": [
                    {"unit_ids": ["9999-deadbeef"], "intent_label": "x", "justification": "y"}
                ]
            }
        )

        self.assertEqual(groups, [])
        self.assertEqual([unit.id for unit in ungrouped], self.ids)
        self.assertIn("9999-deadbeef", " ".join(warnings))

    def test_a_repeated_id_is_kept_once(self):
        groups, _, _ = self.group(
            {
                "groups": [
                    {"unit_ids": [self.ids[0]], "intent_label": "first", "justification": "…"},
                    {"unit_ids": [self.ids[0]], "intent_label": "second", "justification": "…"},
                ]
            }
        )

        self.assertEqual([unit.id for unit in groups[0].units], [self.ids[0]])
        # The second group had nothing left, and an empty group is not a commit.
        self.assertEqual(len(groups), 1)

    def test_units_the_model_never_mentioned_are_ungrouped(self):
        groups, ungrouped, warnings = self.group(
            {"groups": [{"unit_ids": [self.ids[0]], "intent_label": "x", "justification": "y"}]}
        )

        self.assertEqual([unit.id for unit in ungrouped], [self.ids[1], self.ids[2]])
        self.assertIn("2 unit(s)", " ".join(warnings))

    def test_units_the_model_declared_ungrouped_are_ungrouped_quietly(self):
        """An explicit "I could not place this" is an answer, not a failure."""
        groups, ungrouped, warnings = self.group(
            {
                "groups": [{"unit_ids": [self.ids[0]], "intent_label": "x", "justification": "y"}],
                "ungrouped": [self.ids[1], self.ids[2]],
            }
        )

        self.assertEqual([unit.id for unit in ungrouped], [self.ids[1], self.ids[2]])
        self.assertEqual(warnings, [])

    def test_prose_instead_of_the_envelope_leaves_everything_ungrouped(self):
        """Stored by the transport as an unhelpful answer rather than a crash."""
        with self.stubbed(ai={"groups": None, "ungrouped": None}):
            groups, ungrouped, _ = group_units(self.units, max_groups=5)

        self.assertEqual(groups, [])
        self.assertEqual([unit.id for unit in ungrouped], self.ids)

    def test_more_groups_than_the_cap_leave_the_surplus_ungrouped(self):
        payload = {
            "groups": [
                {"unit_ids": [unit_id], "intent_label": f"g{n}", "justification": "…"}
                for n, unit_id in enumerate(self.ids)
            ]
        }

        groups, ungrouped, warnings = self.group(payload, max_groups=2)

        self.assertEqual(len(groups), 2)
        self.assertEqual([unit.id for unit in ungrouped], [self.ids[2]])
        # Named once, by the surplus warning only.
        self.assertEqual(len(warnings), 1)
        self.assertIn(self.ids[2], warnings[0])

    def test_no_unit_is_ever_lost(self):
        """The invariant, stated once over a deliberately hostile answer."""
        payload = {
            "groups": [
                {"unit_ids": [self.ids[0], self.ids[0], "nope-1"], "intent_label": "a", "justification": "…"},
                {"unit_ids": ["nope-2", "nope-3"], "intent_label": "b", "justification": "…"},
                {"unit_ids": [self.ids[1]], "intent_label": "c", "justification": "…"},
                {"unit_ids": [self.ids[2]], "intent_label": "d", "justification": "…"},
                "not even a dict",
            ]
        }

        groups, ungrouped, _ = self.group(payload, max_groups=2)

        seen = [unit.id for group in groups for unit in group.units]
        seen += [unit.id for unit in ungrouped]
        self.assertEqual(sorted(seen), sorted(self.ids))
        self.assertEqual(len(seen), len(set(seen)))

    # ── the budget ───────────────────────────────────────────────────────
    def test_units_over_the_cap_are_ungrouped_and_named(self):
        """Which unit survives the trim is the trimmer's business, not the test's:
        asking it is what keeps this test about the cap rather than about sizes."""
        kept, dropped = _select_for_prompt(self.units, 1)
        groups, ungrouped, warnings = self.group(
            {
                "groups": [
                    {"unit_ids": [kept[0].id], "intent_label": "x", "justification": "y"}
                ]
            },
            max_units=1,
        )

        self.assertEqual([unit.id for unit in groups[0].units], [kept[0].id])
        self.assertEqual([unit.id for unit in ungrouped], [unit.id for unit in dropped])
        self.assertIn("exceeded the analysis budget", warnings[0])
        for unit in dropped:
            self.assertIn(unit.id, warnings[0])

    def test_ids_that_were_never_sent_are_treated_as_unknown(self):
        """A unit trimmed for budget was not in the prompt, so the model cannot
        have placed it — its answer about that id is invented by definition."""
        with self.stubbed(
            ai={"groups": [{"unit_ids": self.ids, "intent_label": "x", "justification": "y"}]}
        ):
            groups, ungrouped, warnings = group_units(
                self.units, max_groups=5, max_units=1
            )

        placed = {unit.id for group in groups for unit in group.units}
        self.assertEqual(len(placed), 1)
        self.assertEqual(len(ungrouped), 2)
        # Two ids the model named that it never saw, and were discarded for it.
        self.assertIn("do not exist", " ".join(warnings))

    # ── provider and cache ───────────────────────────────────────────────
    def test_a_cached_grouping_is_used_without_calling_the_ai(self):
        cached = {
            "groups": [{"unit_ids": self.ids, "intent_label": "cached", "justification": "…"}]
        }
        with self.stubbed(ai={"groups": []}, cached=cached) as mocks:
            groups, _, _ = group_units(self.units, max_groups=5)

        self.assertEqual(groups[0].intent_label, "cached")
        mocks["ai"].assert_not_called()

    def test_a_missing_api_key_stops_before_any_call(self):
        with self.stubbed(ai={"groups": []}, api_key="") as mocks:
            with self.assertRaises(SplitError):
                group_units(self.units, max_groups=5)

        mocks["ai"].assert_not_called()

    def test_an_empty_response_raises(self):
        with self.stubbed(ai=None):
            with self.assertRaises(SplitError):
                group_units(self.units, max_groups=5)

    def test_no_units_is_no_work(self):
        with self.stubbed(ai={"groups": []}) as mocks:
            self.assertEqual(group_units([], max_groups=5), ([], [], []))

        mocks["ai"].assert_not_called()


class PromptTest(SplitRepoTestCase):
    """What the model is shown — bounded, and honest about the bound."""

    def setUp(self):
        super().setUp()
        self.units = parse_units(DIFF)

    def test_every_unit_id_and_file_is_in_the_prompt(self):
        prompt = grouping_prompt(self.units, max_groups=4)

        for unit in self.units:
            self.assertIn(unit.id, prompt)
            self.assertIn(unit.file_path, prompt)
        self.assertIn("at most 4 groups", prompt)

    def test_a_long_hunk_is_truncated_and_says_so(self):
        """The cut is exactly at :data:`MAX_BODY_LINES`, and it is announced —
        a model shown a hunk that silently stops mid-change reads it as the
        whole change."""
        from dataclasses import replace

        long_unit = replace(
            self.units[0],
            content="\n".join(f"+line {n}" for n in range(200)),
        )

        prompt = grouping_prompt([long_unit], max_groups=2)

        self.assertIn("+line 0", prompt)
        self.assertIn(f"+line {MAX_BODY_LINES - 1}", prompt)
        self.assertNotIn(f"+line {MAX_BODY_LINES}", prompt)
        self.assertNotIn("+line 199", prompt)
        self.assertIn(f"{200 - MAX_BODY_LINES} more lines", prompt)


if __name__ == "__main__":
    unittest.main()
