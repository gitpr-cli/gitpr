"""CLI tests for the ``gitpr fix`` command surface.

The AI call, the cache and git itself are mocked — what these tests pin down is
the *routing* the command owns: which candidates a given flag combination
selects, what a dry run is allowed to call, when a patch may reach the tree at
all, and which branch it lands on. The pipeline behind it is covered by real
repositories in tests/fix/test_apply_fix.py and test_rollback_fix.py.
"""
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.diff_parser import summarize_patch
from src.fix.apply_fix import FixError
from src.fix.patch_provenance import (
    ApplyFixResult,
    FindingRef,
    PatchCandidate,
    PatchProvenance,
    PatchSafety,
)
from src.i18n import CURRENT_LANG, set_lang
from src.main import cli

DIFF = (
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def greet(name):\n"
    "-    return 'Hello'\n"
    "+    return f'Hello, {name}'\n"
)


def _candidate(finding_id="FIX-001", safety=PatchSafety.SAFE, reason="safe", diff=DIFF):
    """A real PatchCandidate, so patch_id and the display helpers are real too."""
    return PatchCandidate(
        finding=FindingRef(
            id=finding_id,
            file_path="src/app.py",
            line_start=2,
            line_end=2,
            severity="minor",
            category="style",
            message="greet() ignores its argument",
        ),
        diff_unified=diff,
        suggested_test="",
        confidence="high",
        safety=safety,
        safety_reason=reason,
        provenance=PatchProvenance(
            finding_id=finding_id,
            ai_provider="gemini",
            ai_model="gemini-pro-latest",
            prompt_version="1",
            generated_at="2026-09-13 12:00:00",
            gitpr_version="1.1.0",
        ),
    )


def _fake_apply(candidates, **kwargs):
    """apply_candidates' contract, without git: one result per candidate."""
    dry_run = kwargs.get("dry_run", True)
    return tuple(
        ApplyFixResult(
            applied=not dry_run,
            patch_id=candidate.patch_id,
            files_changed=summarize_patch(candidate.diff_unified).files,
            dry_run_diff=candidate.diff_unified,
            warnings=(),
            branch_created=kwargs.get("branch"),
        )
        for candidate in candidates
    )


def _settings(
    require_confirmation=True,
    create_branch_on_all_safe=True,
    template="fix/gitpr-{datetime}",
    max_lines=5,
    excluded=(),
):
    return {
        "safe_max_lines_changed": max_lines,
        "safe_excluded_paths": tuple(excluded),
        "require_confirmation": require_confirmation,
        "create_branch_on_all_safe": create_branch_on_all_safe,
        "branch_name_template": template,
    }


def _text(result):
    """Everything the run wrote, whichever stream the message went to."""
    return result.output + (result.stderr or "")


class FixCliTestCase(unittest.TestCase):
    """Pins the interface language to English for deterministic assertions."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def invoke(self, args, candidates=None, settings=None, rollback=None, ai_error=None, input=None):
        """Run ``gitpr fix`` with the pipeline stubbed around *candidates*."""
        collected = patch(
            "src.fix.apply_fix.collect_candidates",
            side_effect=ai_error if ai_error else None,
            return_value=None if ai_error else tuple(candidates or ()),
        )
        applied = patch("src.fix.apply_fix.apply_candidates", side_effect=_fake_apply)
        reviewed = patch("src.fix.apply_fix.resolve_review", return_value={"action_type": "review"})
        configured = patch("src.config.get_fix_settings", return_value=settings or _settings())

        with collected as collect, applied as apply, reviewed, configured:
            runner = CliRunner()
            result = runner.invoke(cli, ["fix"] + args, input=input)
        self.collect = collect
        self.apply = apply
        return result


class TestFixListing(FixCliTestCase):
    def test_no_arguments_lists_the_candidates(self):
        result = self.invoke([], candidates=[_candidate(), _candidate("FIX-002", PatchSafety.REVIEW_REQUIRED, "multiple_hunks")])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("FIX-001", result.output)
        self.assertIn("FIX-002", result.output)
        # The patch id is what --rollback addresses, so it has to be visible.
        self.assertIn(_candidate().patch_id, result.output)
        self.apply.assert_not_called()

    def test_a_candidate_is_listed_with_its_classification_reason(self):
        result = self.invoke(
            ["--list"],
            candidates=[_candidate("FIX-002", PatchSafety.REVIEW_REQUIRED, "multiple_hunks")],
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("[review_required]", result.output)
        self.assertIn("it spans more than one hunk", result.output)

    def test_a_safe_candidate_carries_no_reason(self):
        result = self.invoke(["--list"], candidates=[_candidate()])
        self.assertNotIn("single hunk", result.output)
        self.assertIn("[safe]", result.output)

    def test_an_empty_review_says_so(self):
        result = self.invoke([], candidates=[])
        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("no fixable findings", result.output)

    def test_apply_without_a_target_warns_and_still_lists(self):
        result = self.invoke(["--apply"], candidates=[_candidate()])
        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("Nothing was selected", result.output)
        self.assertIn("FIX-001", result.output)
        self.apply.assert_not_called()


class TestFixDryRun(FixCliTestCase):
    def test_one_identifier_shows_the_diff_and_writes_nothing(self):
        result = self.invoke(["FIX-001"], candidates=[_candidate(), _candidate("FIX-002")])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("+    return f'Hello, {name}'", result.output)
        self.assertIn("Dry run", result.output)
        self.apply.assert_called_once()
        self.assertTrue(self.apply.call_args.kwargs["dry_run"])
        self.assertIsNone(self.apply.call_args.kwargs.get("branch"))

    def test_the_classification_settings_reach_the_pipeline(self):
        self.invoke(
            ["FIX-001"],
            candidates=[_candidate()],
            settings=_settings(max_lines=9, excluded=("docker/**",)),
        )

        self.assertEqual(self.collect.call_args.kwargs["max_lines_changed"], 9)
        self.assertEqual(self.collect.call_args.kwargs["excluded_paths"], ("docker/**",))

    def test_an_unknown_identifier_lists_what_exists(self):
        result = self.invoke(["FIX-999"], candidates=[_candidate()])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("FIX-999", _text(result))
        self.assertIn("FIX-001", _text(result))
        self.apply.assert_not_called()

    def test_all_safe_without_apply_selects_but_does_not_write(self):
        result = self.invoke(
            ["--all-safe"],
            candidates=[_candidate(), _candidate("FIX-002", PatchSafety.EXPERIMENTAL, "apply_check_failed")],
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertTrue(self.apply.call_args.kwargs["dry_run"])
        self.assertIn("FIX-002 not applied", result.output)
        # The branch a real run would create is named up front.
        self.assertIn("fix/gitpr-", result.output)

    def test_all_safe_with_nothing_safe_says_so(self):
        result = self.invoke(
            ["--all-safe"],
            candidates=[_candidate("FIX-002", PatchSafety.REVIEW_REQUIRED, "multiple_hunks")],
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("None of the candidates is safe", result.output)
        self.apply.assert_not_called()


class TestFixApply(FixCliTestCase):
    def test_a_safe_patch_is_written_after_the_confirmation(self):
        result = self.invoke(["FIX-001", "--apply"], candidates=[_candidate()], input="y\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertFalse(self.apply.call_args.kwargs["dry_run"])
        self.assertIn("Patch applied", result.output)

    def test_a_declined_confirmation_writes_nothing(self):
        result = self.invoke(["FIX-001", "--apply"], candidates=[_candidate()], input="n\n")

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("cancelled", result.output)
        self.apply.assert_not_called()

    def test_yes_skips_the_prompt(self):
        result = self.invoke(["FIX-001", "--apply", "--yes"], candidates=[_candidate()])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("Patch applied", result.output)

    def test_configuration_can_turn_the_confirmation_off(self):
        result = self.invoke(
            ["FIX-001", "--apply"],
            candidates=[_candidate()],
            settings=_settings(require_confirmation=False),
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("Patch applied", result.output)

    def test_a_patch_that_is_not_safe_is_refused_without_force(self):
        result = self.invoke(
            ["FIX-002", "--apply", "--yes"],
            candidates=[_candidate("FIX-002", PatchSafety.REVIEW_REQUIRED, "excluded_path")],
        )

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--force", _text(result))
        self.assertIn("it touches a configured sensitive path", _text(result))
        self.apply.assert_not_called()

    def test_yes_alone_never_bypasses_the_force_gate(self):
        result = self.invoke(
            ["FIX-002", "--apply", "--yes", "--force"],
            candidates=[_candidate("FIX-002", PatchSafety.EXPERIMENTAL, "apply_check_failed")],
            input="y\n",
        )

        # --force asks for the phrase, so a y/n answer is not it.
        self.assertEqual(result.exit_code, 1)
        self.assertIn("does not match", _text(result))
        self.apply.assert_not_called()

    def test_the_typed_phrase_opens_the_door(self):
        result = self.invoke(
            ["FIX-002", "--apply", "--force"],
            candidates=[_candidate("FIX-002", PatchSafety.EXPERIMENTAL, "apply_check_failed")],
            input="apply FIX-002\n",
        )

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertFalse(self.apply.call_args.kwargs["dry_run"])
        self.assertIn("Patch applied", result.output)

    def test_a_failed_apply_is_reported_per_candidate(self):
        candidates = [_candidate(), _candidate("FIX-002")]
        with patch("src.fix.apply_fix.apply_candidates") as apply:
            apply.return_value = (
                ApplyFixResult(True, candidates[0].patch_id, ("src/app.py",), DIFF, ()),
                ApplyFixResult(
                    False, candidates[1].patch_id, ("src/app.py",), DIFF,
                    ("❌ git apply failed: patch does not apply",),
                ),
            )
            with patch("src.fix.apply_fix.collect_candidates", return_value=tuple(candidates)), \
                 patch("src.fix.apply_fix.resolve_review", return_value={}), \
                 patch("src.config.get_fix_settings", return_value=_settings()):
                result = CliRunner().invoke(cli, ["fix", "--all-safe", "--apply", "--yes"])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("Patch applied", result.output)
        self.assertIn("git apply failed", result.output)


class TestFixBranch(FixCliTestCase):
    def test_all_safe_creates_a_branch_from_the_template(self):
        result = self.invoke(["--all-safe", "--apply", "--yes"], candidates=[_candidate()])

        self.assertEqual(result.exit_code, 0, _text(result))
        branch = self.apply.call_args.kwargs["branch"]
        self.assertTrue(branch.startswith("fix/gitpr-"), branch)
        self.assertIn("Branch", result.output)

    def test_no_branch_keeps_the_patch_in_place(self):
        self.invoke(["--all-safe", "--apply", "--yes", "--no-branch"], candidates=[_candidate()])
        self.assertIsNone(self.apply.call_args.kwargs["branch"])

    def test_configuration_can_turn_the_branch_off(self):
        self.invoke(
            ["--all-safe", "--apply", "--yes"],
            candidates=[_candidate()],
            settings=_settings(create_branch_on_all_safe=False),
        )
        self.assertIsNone(self.apply.call_args.kwargs["branch"])

    def test_an_explicit_name_wins(self):
        self.invoke(
            ["--all-safe", "--apply", "--yes", "--create-branch", "fix/mine"],
            candidates=[_candidate()],
        )
        self.assertEqual(self.apply.call_args.kwargs["branch"], "fix/mine")

    def test_a_single_patch_stays_on_the_current_branch(self):
        self.invoke(["FIX-001", "--apply", "--yes"], candidates=[_candidate()])
        self.assertIsNone(self.apply.call_args.kwargs["branch"])


class TestFixFailures(FixCliTestCase):
    def test_no_cached_review_is_reported(self):
        result = self.invoke([], ai_error=FixError("❌ No review found for acme/app on branch 'main'."))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("No review found", _text(result))

    def test_a_clean_tree_is_reported(self):
        result = self.invoke([], ai_error=FixError("❌ The working tree has no changes to apply fixes to."))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("no changes to apply fixes to", _text(result))

    def test_force_with_all_safe_is_flagged_as_meaningless(self):
        result = self.invoke(["--all-safe", "--force"], candidates=[_candidate()])
        self.assertIn("--force has no effect with --all-safe", result.output)


class TestFixRollback(FixCliTestCase):
    def _entry(self):
        return {"patch_id": "FIX-001-1a2b3c4d", "files_changed": ["src/app.py"]}

    def test_rollback_undoes_the_patch(self):
        with patch("src.fix.rollback_fix.rollback_fix", return_value=self._entry()) as undo:
            result = CliRunner().invoke(cli, ["fix", "--rollback", "FIX-001-1a2b3c4d"])

        self.assertEqual(result.exit_code, 0, _text(result))
        undo.assert_called_once_with("FIX-001-1a2b3c4d")
        self.assertIn("restored", result.output)

    def test_rollback_never_calls_the_ai(self):
        with patch("src.fix.rollback_fix.rollback_fix", return_value=self._entry()), \
             patch("src.fix.apply_fix.collect_candidates") as collect:
            CliRunner().invoke(cli, ["fix", "--rollback", "FIX-001-1a2b3c4d"])

        collect.assert_not_called()

    def test_rollback_refuses_to_be_combined(self):
        with patch("src.fix.rollback_fix.rollback_fix") as undo:
            result = CliRunner().invoke(cli, ["fix", "FIX-001", "--rollback", "FIX-001-1a2b3c4d"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("--rollback", _text(result))
        undo.assert_not_called()

    def test_an_unknown_patch_id_is_reported(self):
        with patch(
            "src.fix.rollback_fix.rollback_fix",
            side_effect=FixError("❌ No applied patch with id 'FIX-999-ffffffff' was recorded here."),
        ):
            result = CliRunner().invoke(cli, ["fix", "--rollback", "FIX-999-ffffffff"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("FIX-999-ffffffff", _text(result))


class TestFixHelp(FixCliTestCase):
    def test_help_points_to_the_fix_documentation(self):
        result = CliRunner().invoke(cli, ["fix", "-h"])

        self.assertEqual(result.exit_code, 0, _text(result))
        self.assertIn("fix-command", result.output)


if __name__ == "__main__":
    unittest.main()
