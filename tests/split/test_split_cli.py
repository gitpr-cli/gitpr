"""CLI tests for the ``gitpr split`` command surface.

What these pin down is the *routing* the command owns and nothing else: which
flag combination prompts, which one writes, what reaches the planning call, and
what the report says when a run stops halfway. The pipeline behind it is
covered against real repositories in tests/split/test_generate_split_plan.py and
test_apply_split_plan.py — so here the plan and the result are built by hand,
which is the point: a test that drove a real repository to check that
``--dry-run`` never writes would be proving it about git rather than about the
flag.

The one routing decision worth stating outright is the confirmation. ``--apply``
states an intent, so ``GITPR_SPLIT_REQUIRE_CONFIRMATION=false`` may skip the
question. Bare mode has no such intent to appeal to, so it always asks —
otherwise typing ``gitpr split`` would commit on its own.
"""
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.i18n import CURRENT_LANG, set_lang
from src.main import cli
from src.split.apply_split_plan import ApplySplitResult
from src.split.split_plan import Hunk, HunkGroup, SplitPlan


def _hunk(path, marker, ordinal):
    """A real ``Hunk``, so ``file_paths`` and the ids are real too.

    Ten fields is a lot to write per test, and all but three of them are
    arithmetic the display layer never reads; the ones it does read —
    ``file_path``, ``id`` and the body that carries *marker* — are the ones
    spelled out here.
    """
    content = f"@@ -{ordinal + 1},1 +{ordinal + 1},1 @@\n-old line\n+{marker}\n"
    return Hunk(
        file_path=path,
        hunk_header=f"@@ -{ordinal + 1},1 +{ordinal + 1},1 @@",
        content=content,
        line_start_old=ordinal + 1,
        line_start_new=ordinal + 1,
        id=f"{ordinal:04d}-abcdef01",
        file_header=f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n",
        old_count=1,
        new_count=1,
        ordinal=ordinal,
    )


def _group(group_id, label, *units, message=None, justification="because"):
    return HunkGroup(
        group_id=group_id,
        intent_label=label,
        justification=justification,
        units=list(units),
        generated_commit_message=message or f"{label}: a message",
    )


def _plan(groups=None, ungrouped=(), warnings=()):
    groups = list(groups) if groups is not None else [
        _group("G1", "fix: the bug", _hunk("src/app.py", "app_fixed", 0)),
        _group("G2", "docs: the note", _hunk("src/notes.md", "notes_added", 1)),
    ]
    return SplitPlan(
        groups=groups,
        ungrouped_units=list(ungrouped),
        total_units=sum(len(group.units) for group in groups) + len(ungrouped),
        warnings=list(warnings),
    )


def _result(commits=(), stopped_at="", error="", staged=False, uncommitted=()):
    return ApplySplitResult(
        commits=list(commits),
        uncommitted_units=list(uncommitted),
        staged_but_not_committed=staged,
        stopped_at=stopped_at,
        error=error,
    )


def _settings(max_groups=5, require_confirmation=True, max_units=50):
    return {
        "max_groups": max_groups,
        "require_confirmation": require_confirmation,
        "max_units": max_units,
    }


def _text(result):
    """Everything the run wrote, whichever stream the message went to."""
    return result.output + (result.stderr or "")


class SplitCliTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def invoke(
        self,
        args,
        plan=None,
        result=None,
        settings=None,
        untracked=(),
        error=None,
        apply_error=None,
        is_repo=True,
        diff="a diff",
        input=None,
    ):
        """Run ``gitpr split`` with every edge stubbed; git is never reached.

        The two split entry points are imported inside the command body, so they
        are patched on their own modules; the diff capture and the settings
        getter are module-level imports in ``src.main`` and are patched there.
        Patching ``src.core`` would leave the names ``main`` already bound
        untouched and the real ``git`` would run.
        """
        planned = patch(
            "src.split.generate_split_plan.generate_split_plan",
            side_effect=error,
            return_value=None if error else (plan if plan is not None else _plan()),
        )
        applied = patch(
            "src.split.apply_split_plan.apply_split_plan",
            side_effect=apply_error,
            return_value=None if apply_error else (result or _result()),
        )
        with planned as planning, applied as applying, \
             patch("src.main.get_split_diff", return_value=diff) as captured, \
             patch(
                 "src.main.get_uncommitted_summary",
                 return_value={"staged": [], "unstaged": [], "untracked": list(untracked)},
             ), \
             patch("src.main.get_split_settings", return_value=settings or _settings()), \
             patch(
                 "src.infrastructure.git.patch_applier.is_git_repository",
                 return_value=is_repo,
             ):
            runner = CliRunner()
            outcome = runner.invoke(cli, ["split"] + args, input=input)
        self.planning = planning
        self.applying = applying
        self.captured = captured
        return outcome


class TestSplitPlanOutput(SplitCliTestCase):
    """What the user is shown before anything is decided."""

    def test_the_plan_names_every_group_its_files_and_its_message(self):
        result = self.invoke(["--dry-run"])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("G1", result.output)
        self.assertIn("fix: the bug", result.output)
        self.assertIn("src/app.py", result.output)
        self.assertIn("fix: the bug: a message", result.output)
        self.assertIn("2 commit(s) proposed", result.output)

    def test_ungrouped_units_are_listed_rather_than_omitted(self):
        """A plan that silently hid them would read as complete when it is not."""
        plan = _plan(ungrouped=[_hunk("src/other.py", "other_touched", 2)])

        result = self.invoke(["--dry-run"], plan=plan)

        self.assertIn("Not grouped", result.output)
        self.assertIn("src/other.py", result.output)

    def test_warnings_are_printed(self):
        result = self.invoke(["--dry-run"], plan=_plan(warnings=["⚠️ 2 untracked file(s)"]))

        self.assertIn("2 untracked file(s)", result.output)

    def test_untracked_files_reach_the_planning_call(self):
        self.invoke(["--dry-run"], untracked=["src/scratch.py"])

        self.assertEqual(
            self.planning.call_args.kwargs["untracked"], ["src/scratch.py"]
        )

    def test_the_split_diff_is_captured_not_the_commit_diff(self):
        """``-w`` renders whitespace-only changes as context, which would break
        the byte-identical guarantee — so split captures its own diff."""
        self.invoke(["--dry-run"])
        self.captured.assert_called_once()


class TestSplitDryRun(SplitCliTestCase):
    def test_dry_run_never_applies_and_says_so(self):
        result = self.invoke(["--dry-run"])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.applying.assert_not_called()
        self.assertIn("Dry run", result.output)
        self.assertNotIn("commit(s) created", result.output)

    def test_dry_run_never_prompts_even_with_nothing_to_answer(self):
        """No ``input`` is supplied: a prompt would exhaust stdin and fail."""
        result = self.invoke(["--dry-run"])

        self.assertEqual(result.exit_code, 0, _text(result))

    def test_dry_run_cannot_be_combined_with_apply(self):
        result = self.invoke(["--dry-run", "--apply"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--dry-run and --apply", _text(result))
        self.planning.assert_not_called()
        self.applying.assert_not_called()


class TestSplitConfirmation(SplitCliTestCase):
    def test_bare_mode_offers_to_apply_and_a_yes_applies(self):
        result = self.invoke([], input="y\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.applying.assert_called_once()

    def test_a_declined_offer_writes_nothing(self):
        result = self.invoke([], input="n\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.applying.assert_not_called()
        self.assertIn("cancelled", result.output)
        # The plan was already printed, so declining still leaves the user with
        # something: the proposal they just read.
        self.assertIn("G1", result.output)

    def test_apply_confirms_once_then_writes(self):
        result = self.invoke(["--apply"], input="y\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.applying.assert_called_once()

    def test_yes_skips_the_prompt(self):
        self.invoke(["--apply", "--yes"])

        self.applying.assert_called_once()

    def test_configuration_can_turn_the_confirmation_off_for_apply(self):
        self.invoke(["--apply"], settings=_settings(require_confirmation=False))

        self.applying.assert_called_once()

    def test_bare_mode_asks_even_when_the_configuration_says_not_to(self):
        """The question *is* the command when no flag states an intent, so a
        configuration value must not turn ``gitpr split`` into a silent commit.
        No input is supplied: prompting here is the assertion."""
        result = self.invoke([], settings=_settings(require_confirmation=False), input="n\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.applying.assert_not_called()
        self.assertIn("cancelled", result.output)

    def test_yes_still_skips_that_question(self):
        """The escape hatch from the rule above: ``--yes`` is the user saying
        so explicitly, which the configuration value alone is not."""
        self.invoke(["--yes"], settings=_settings(require_confirmation=False), input=None)

        self.applying.assert_called_once()


class TestSplitOptions(SplitCliTestCase):
    def test_max_groups_reaches_the_planner(self):
        self.invoke(["--dry-run", "--max-groups", "3"])

        self.assertEqual(self.planning.call_args.kwargs["max_groups"], 3)

    def test_the_configured_limit_is_the_default(self):
        self.invoke(["--dry-run"], settings=_settings(max_groups=9))

        self.assertEqual(self.planning.call_args.kwargs["max_groups"], 9)

    def test_the_unit_budget_comes_from_configuration(self):
        self.invoke(["--dry-run"], settings=_settings(max_units=12))

        self.assertEqual(self.planning.call_args.kwargs["max_units"], 12)

    def test_the_provider_is_forced_when_asked(self):
        self.invoke(["--dry-run", "--provider", "deepseek"])

        self.assertEqual(self.planning.call_args.kwargs["provider"], "deepseek")

    def test_without_a_provider_the_planner_resolves_its_own(self):
        self.invoke(["--dry-run"])

        self.assertIsNone(self.planning.call_args.kwargs["provider"])


class TestSplitReport(SplitCliTestCase):
    def test_each_commit_is_reported_with_its_group(self):
        result = self.invoke(
            ["--apply", "--yes"],
            result=_result(commits=[("G1", "a" * 40), ("G2", "b" * 40)]),
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("2 commit(s) created", result.output)
        self.assertIn("aaaaaaaaaa", result.output)
        self.assertIn("bbbbbbbbbb", result.output)

    def test_a_run_that_stops_says_where_and_why(self):
        result = self.invoke(
            ["--apply", "--yes"],
            result=_result(
                commits=[("G1", "a" * 40)],
                stopped_at="G2",
                error="test hook: rejecting this commit",
                staged=True,
            ),
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("stopped at G2", result.output)
        self.assertIn("test hook: rejecting this commit", result.output)
        self.assertIn("staged and was not committed", result.output)
        # Group 1 is a real commit and the report must not imply otherwise.
        self.assertIn("1 commit(s) created", result.output)

    def test_a_staging_failure_says_the_changes_are_back(self):
        result = self.invoke(
            ["--apply", "--yes"],
            result=_result(stopped_at="G1", error="patch does not apply", staged=False),
        )

        self.assertIn("back in the working tree", result.output)
        self.assertNotIn("staged and was not committed", result.output)

    def test_what_was_left_uncommitted_is_counted(self):
        result = self.invoke(
            ["--apply", "--yes"],
            result=_result(
                stopped_at="G2",
                error="no",
                uncommitted=[_hunk("src/a.py", "x", 0), _hunk("src/b.py", "y", 1)],
            ),
        )

        self.assertIn("Still uncommitted: 2 change unit(s)", result.output)

    def test_a_complete_run_reports_nothing_but_the_commits(self):
        result = self.invoke(["--apply", "--yes"], result=_result(commits=[("G1", "a" * 40)]))

        self.assertNotIn("stopped", result.output)
        self.assertNotIn("Still uncommitted", result.output)


class TestSplitFailures(SplitCliTestCase):
    def test_a_clean_tree_is_reported_and_nothing_is_applied(self):
        from src.split.split_plan import SplitError

        result = self.invoke(
            ["--apply", "--yes"],
            error=SplitError("⚠️ No changes to split."),
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("No changes to split", _text(result))
        self.applying.assert_not_called()

    def test_a_missing_ai_provider_is_reported(self):
        from src.split.split_plan import SplitError

        result = self.invoke(
            ["--dry-run"], error=SplitError("⚠️ No AI provider is configured.")
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("No AI provider is configured", _text(result))

    def test_a_refusal_from_the_applier_is_reported(self):
        from src.split.split_plan import SplitError

        result = self.invoke(
            ["--apply", "--yes"],
            apply_error=SplitError("⚠️ This repository has no commits to build on."),
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no commits to build on", _text(result))

    def test_a_directory_that_is_not_a_repository_is_refused_before_planning(self):
        result = self.invoke([], is_repo=False)

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Not a Git repository", _text(result))
        self.planning.assert_not_called()


class TestSplitHelp(SplitCliTestCase):
    def test_help_points_to_the_split_documentation(self):
        result = CliRunner().invoke(cli, ["split", "-h"])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("split-command", result.output)

    def test_help_does_not_advertise_an_interactive_mode(self):
        """``--interactive`` is absent, not stubbed: the plan is the interface."""
        result = CliRunner().invoke(cli, ["split", "-h"])

        self.assertNotIn("--interactive", result.output)


if __name__ == "__main__":
    unittest.main()
