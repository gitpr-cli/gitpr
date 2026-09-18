"""CLI tests for ``gitpr review-pr``.

The pipeline, the forge and the AI are all stubbed here too: what these tests
pin down is the *routing* the command owns — which flags become which arguments,
what the user is told when the run fails, which file the report lands in and
which one it never touches. The review itself is covered in test_remote_pr.py,
the forge calls in tests/scm/.

Two of these assertions are about the command's absence of behaviour, which is
where a subcommand usually goes wrong: it must not check the working tree (the
diff does not come from it) and it must not write a report when the review
failed.
"""
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from src.i18n import CURRENT_LANG, set_lang
from src.infrastructure.scm.base import RepoRef, ScmProviderError
from src.main import cli
from src.review.diff_source import DiffOrigin, DiffSource
from src.review.remote_pr import ReviewPrError, ReviewRemotePrResult

REVIEW = "## Review\n\nThe argument is ignored — use it or drop it."
DIFF = "diff --git a/src/app.py b/src/app.py\n@@ -1 +1 @@\n-a\n+b\n"


def _repo():
    return RepoRef(
        raw="https://github.com/owner/repo.git",
        workspace="owner",
        name="repo",
        provider="github",
    )


def _result(head_branch="feature/login", pr_number=42, warnings=(), linter=None):
    return ReviewRemotePrResult(
        pr_number=pr_number,
        pr_url=f"https://github.com/owner/repo/pull/{pr_number}",
        review=REVIEW,
        diff_source=DiffSource(
            origin=DiffOrigin.REMOTE_PR,
            content=DIFF,
            identifier=f"pr-{pr_number}",
            pr_number=pr_number,
            repo_ref=_repo(),
            base_branch="main",
            head_branch=head_branch,
        ),
        linter_results=linter or {"errors": [], "warnings": []},
        warnings=list(warnings),
    )


class ReviewPrCliTestCase(unittest.TestCase):
    """Pins the interface language and gives every run its own report folder."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def setUp(self):
        self.report_dir = tempfile.mkdtemp(prefix="gitpr-review-pr-")
        self.addCleanup(shutil.rmtree, self.report_dir, True)
        self.report_path = os.path.join(self.report_dir, "report.txt")

    def invoke(self, args, result=None, error=None, scm=None, ai_provider="gemini", linter=None):
        """Run ``gitpr review-pr`` with the forge and the pipeline stubbed."""
        pipeline = patch(
            "src.review.remote_pr.review_remote_pr",
            return_value=result if result is not None else _result(linter=linter),
            side_effect=error,
        )
        context = patch(
            "src.main._resolve_scm_context",
            return_value=scm if scm is not None else (_provider(), _repo()),
        )
        output = patch("src.main.resolve_output_path", return_value=self.report_path)
        provider = patch("src.main.get_ai_provider", return_value=ai_provider)
        unstaged = patch("src.main.check_unstaged_files")

        with pipeline as pipeline_mock, context, output, provider as provider_mock, unstaged as unstaged_mock:
            runner = CliRunner()
            cli_result = runner.invoke(cli, ["review-pr"] + args)

        self.pipeline = pipeline_mock
        self.provider = provider_mock
        self.unstaged = unstaged_mock
        return cli_result

    def report(self):
        """The report the run wrote, or None when it wrote nothing."""
        if not os.path.exists(self.report_path):
            return None
        with open(self.report_path, encoding="utf-8", errors="replace") as handle:
            return handle.read()


def _provider():
    """A stand-in for the forge: only its identity is ever read here."""
    provider = MagicMock()
    provider.name = "github"
    return provider


def _text(result):
    """Everything the run wrote, whichever stream the message went to."""
    return result.output + (result.stderr or "")


class TestArguments(ReviewPrCliTestCase):
    def test_the_number_reaches_the_pipeline(self):
        self.invoke(["42"])
        self.assertEqual(self.pipeline.call_args.args[0], 42)

    def test_the_forge_and_repository_reach_the_pipeline(self):
        self.invoke(["42"])
        args = self.pipeline.call_args.args
        self.assertEqual(args[1].name, "github")
        self.assertEqual(args[2].name, "repo")

    def test_nothing_is_published_without_the_flag(self):
        """The forge is never written to unless the user asks for it."""
        self.invoke(["42"])
        self.assertFalse(self.pipeline.call_args.args[4])

    def test_post_comment_reaches_the_pipeline(self):
        self.invoke(["42", "--post-comment"])
        self.assertTrue(self.pipeline.call_args.args[4])

    def test_the_configured_provider_is_used_by_default(self):
        self.invoke(["42"], ai_provider="ollama")
        self.assertEqual(self.pipeline.call_args.args[3], "ollama")

    def test_the_provider_flag_overrides_the_configuration(self):
        self.invoke(["42", "--provider", "deepseek"])
        self.assertEqual(self.pipeline.call_args.args[3], "deepseek")

    def test_the_provider_flag_does_not_consult_the_configuration(self):
        self.invoke(["42", "--provider", "deepseek"])
        self.provider.assert_not_called()

    def test_the_working_tree_is_never_checked(self):
        """The diff comes from the API — the local tree is not part of this run."""
        self.invoke(["42"])
        self.unstaged.assert_not_called()

    def test_a_missing_number_is_a_usage_error(self):
        result = self.invoke([])
        self.assertEqual(result.exit_code, 2)

    def test_a_non_numeric_number_is_a_usage_error(self):
        result = self.invoke(["abc"])
        self.assertEqual(result.exit_code, 2)
        self.pipeline = None if not hasattr(self, "pipeline") else self.pipeline


class TestReport(ReviewPrCliTestCase):
    def test_the_review_is_written_to_a_file(self):
        self.invoke(["42"])
        self.assertIn(REVIEW, self.report())

    def test_the_report_is_named_after_the_branch_under_review(self):
        captured = {}

        def _capture(env_var, pattern, branch, moment):
            captured["branch"] = branch
            return self.report_path

        with patch("src.main.resolve_output_path", side_effect=_capture):
            with patch("src.review.remote_pr.review_remote_pr", return_value=_result()):
                with patch("src.main._resolve_scm_context", return_value=(_provider(), _repo())):
                    runner = CliRunner()
                    runner.invoke(cli, ["review-pr", "42"])

        self.assertEqual(captured["branch"], "feature-login")

    def test_a_branch_without_a_name_falls_back_to_the_number(self):
        captured = {}

        def _capture(env_var, pattern, branch, moment):
            captured["branch"] = branch
            return self.report_path

        with patch("src.main.resolve_output_path", side_effect=_capture):
            with patch("src.review.remote_pr.review_remote_pr", return_value=_result(head_branch=None)):
                with patch("src.main._resolve_scm_context", return_value=(_provider(), _repo())):
                    runner = CliRunner()
                    runner.invoke(cli, ["review-pr", "42"])

        self.assertEqual(captured["branch"], "pr-42")

    def test_the_linter_alerts_are_filed_with_the_review(self):
        self.invoke(["42"], linter={"errors": ["line too long"], "warnings": []})
        self.assertIn("line too long", self.report())

    def test_the_review_is_not_printed_to_the_terminal(self):
        """Same contract as the local review: the report is the artefact."""
        result = self.invoke(["42"])
        self.assertNotIn("The argument is ignored", result.output)

    def test_a_failed_review_writes_no_report(self):
        error = ReviewPrError("Pull request #42 was not found in owner/repo.")

        result = self.invoke(["42"], error=error)

        self.assertEqual(result.exit_code, 1)
        self.assertIsNone(self.report())


class TestWarnings(ReviewPrCliTestCase):
    def test_the_warnings_are_printed(self):
        result = self.invoke(["42"], result=_result(warnings=["2 file(s) skipped by the smart excludes: a.lock"]))
        self.assertIn("skipped by the smart excludes", result.output)

    def test_a_clean_run_prints_no_warning(self):
        result = self.invoke(["42"])
        self.assertNotIn("⚠️", result.output)


class TestFailures(ReviewPrCliTestCase):
    def test_an_unreviewable_pull_request_exits_nonzero(self):
        result = self.invoke(["42"], error=ReviewPrError("Pull request #42 is not open (state: closed)."))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("not open", _text(result))

    def test_the_ai_is_never_reached_when_the_pull_request_is_rejected(self):
        """The pipeline raises before the engine; the command must not retry."""
        self.invoke(["42"], error=ReviewPrError("nope"))
        self.assertEqual(self.pipeline.call_count, 1)

    def test_a_forge_error_exits_nonzero_with_the_reason(self):
        result = self.invoke(["42"], error=ScmProviderError("github", 500, "Server Error"))

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Server Error", _text(result))

    def test_an_unresolved_forge_stops_before_the_pipeline(self):
        """No provider means no repository to read — the message comes from --init."""
        result = self.invoke(["42"], scm=(None, None))

        self.assertEqual(result.exit_code, 1)
        self.pipeline.assert_not_called()


class TestHelp(ReviewPrCliTestCase):
    def test_the_help_lists_both_options(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["review-pr", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--post-comment", result.output)
        self.assertIn("--provider", result.output)

    def test_the_help_links_to_the_documentation(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["review-pr", "--help"])

        self.assertIn("review-pr", result.output)
        self.assertIn("gitpr.natanfiuza.dev.br", result.output)

    def test_the_short_help_flag_works(self):
        """Every subcommand accepts -h — the root group's flags are not inherited."""
        runner = CliRunner()
        result = runner.invoke(cli, ["review-pr", "-h"])

        self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
