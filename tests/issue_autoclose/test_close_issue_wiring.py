"""Tests for the PR-flow wiring of the issue-autoclose feature (T6).

The helper under test is `src.main._prepare_close_issue`: it reads the local
record before the stage TUI, resolves the forge once and forwards the flags to
the T4 use case. The collaborators are patched at their source modules because
the helper imports them at call time. Plain fakes, not ``Mock``, are used for
the provider and the registry — a Mock answers a truthy ``name`` and would
silently pass the GitHub gate.
"""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from click.testing import CliRunner

from src.issue_autoclose.issue_registry import RegisteredIssue, RegistryLoad
from src.issue_autoclose.resolve_close_issue import (
    CloseIssueDecision,
    CloseIssueFlags,
    CloseIssueOutcome,
)
from src.main import (
    _clear_close_issue_record,
    _prepare_close_issue,
    _publish_pr_directly,
    cli,
)

REGISTERED = RegisteredIssue(
    repo="natanfiuza/gitpr",
    number=7,
    title="Fix the thing",
    url="https://github.com/natanfiuza/gitpr/issues/7",
    created_at="2026-11-02T10:00:00",
    branch="feat/x",
)
DECISION = CloseIssueDecision(number=7, title="Fix the thing", line="close #7")
REPO_REF = SimpleNamespace(
    display="natanfiuza/gitpr", raw="git@github.com:natanfiuza/gitpr.git"
)


class _Provider:
    """A plain provider stub — ``Mock`` would fake a truthy ``name``."""

    name = "github"


class _Registry:
    """A registry stub that counts reads and removals."""

    def __init__(self, issue=None, error="", clear_error=None):
        self.issue = issue
        self.error = error
        self.clear_error = clear_error
        self.load_calls = 0
        self.clear_calls = 0

    def load(self):
        self.load_calls += 1
        return RegistryLoad(issue=self.issue, error=self.error)

    def clear(self):
        self.clear_calls += 1
        if self.clear_error:
            raise self.clear_error
        return True


class PrepareCloseIssueTest(unittest.TestCase):
    def _run(
        self,
        *,
        flags=None,
        base="release",
        may_ask=True,
        registry=None,
        outcome=None,
        scm=None,
        base_resolver=None,
        autoclose_enabled=True,
        autoclose_timeout=5,
    ):
        flags = flags if flags is not None else CloseIssueFlags()
        registry = (
            registry if registry is not None else _Registry(issue=REGISTERED)
        )
        outcome = (
            outcome
            if outcome is not None
            else CloseIssueOutcome(decision=DECISION, asked=True, accepted=True)
        )
        resolve = Mock(return_value=outcome)
        scm = scm if scm is not None else Mock(
            return_value=(_Provider(), REPO_REF)
        )
        base_resolver = (
            base_resolver
            if base_resolver is not None
            else Mock(
                return_value=SimpleNamespace(
                    branch="develop", source="project", warnings=()
                )
            )
        )
        secho = Mock()
        registry_cls = Mock(return_value=registry)

        with patch(
            "src.issue_autoclose.issue_registry.IssueRegistry", registry_cls
        ), patch(
            "src.config.issue_autoclose_enabled",
            return_value=autoclose_enabled,
        ), patch(
            "src.config.get_issue_autoclose_timeout",
            return_value=autoclose_timeout,
        ), patch(
            "src.issue_autoclose.resolve_close_issue.resolve_close_issue",
            resolve,
        ), patch(
            "src.main._resolve_scm_context", scm
        ), patch(
            "src.project_config.resolve_pull_request_base", base_resolver
        ), patch(
            "src.main.click.secho", secho
        ):
            result = _prepare_close_issue(flags, base, may_ask)

        self.registry_cls = registry_cls
        return result, registry, resolve, scm, base_resolver, secho

    def test_disabled_flag_touches_nothing(self):
        result, registry, resolve, scm, base_resolver, _ = self._run(
            flags=CloseIssueFlags(disabled=True)
        )

        self.assertEqual(result, (None, None, None))
        self.assertEqual(registry.load_calls, 0)
        scm.assert_not_called()
        resolve.assert_not_called()
        base_resolver.assert_not_called()

    def test_config_disabled_skips_before_the_registry_is_constructed(self):
        result, registry, resolve, scm, base_resolver, secho = self._run(
            autoclose_enabled=False
        )

        self.assertEqual(result, (None, None, None))
        # The constructor itself runs ``git rev-parse`` — it must not run.
        self.registry_cls.assert_not_called()
        self.assertEqual(registry.load_calls, 0)
        scm.assert_not_called()
        resolve.assert_not_called()
        base_resolver.assert_not_called()
        secho.assert_not_called()

    def test_config_disabled_wins_over_close_issue(self):
        # T4's gate order: enabled is checked before the accept flag.
        result, _, resolve, _, _, _ = self._run(
            flags=CloseIssueFlags(accept=True), autoclose_enabled=False
        )

        self.assertEqual(result, (None, None, None))
        resolve.assert_not_called()

    def test_the_configured_timeout_reaches_the_use_case(self):
        _, _, resolve, _, _, _ = self._run(autoclose_timeout=17)

        self.assertEqual(resolve.call_args.kwargs["timeout"], 17)

    def test_no_record_returns_before_the_forge(self):
        registry = _Registry()

        result, _, resolve, scm, base_resolver, _ = self._run(registry=registry)

        self.assertEqual(result, (None, None, None))
        self.assertEqual(registry.load_calls, 1)
        scm.assert_not_called()
        resolve.assert_not_called()
        base_resolver.assert_not_called()

    def test_record_reaches_the_forge_and_forwards_the_question_settings(self):
        flags = CloseIssueFlags()

        result, registry, resolve, scm, base_resolver, _ = self._run(flags=flags)

        self.assertIs(result[0], DECISION)
        self.assertIs(result[1], registry)
        early_provider, early_repo_ref = result[2]
        self.assertIs(early_provider, resolve.call_args.args[0])
        self.assertIs(early_repo_ref, REPO_REF)
        scm.assert_called_once_with()
        provider, passed_registry, repo_ref = resolve.call_args.args
        self.assertEqual(provider.name, "github")
        self.assertIs(passed_registry, registry)
        self.assertIs(repo_ref, REPO_REF)
        kwargs = resolve.call_args.kwargs
        self.assertEqual(kwargs["flags"], flags)
        self.assertTrue(kwargs["is_tty"])
        self.assertEqual(kwargs["target_branch"], "develop")
        self.assertEqual(kwargs["timeout"], 5)
        self.assertTrue(callable(kwargs["ask"]))
        base_resolver.assert_called_once_with("release", verify=False)

    def test_accept_flag_skips_the_target_branch_read(self):
        result, _, resolve, _, base_resolver, _ = self._run(
            flags=CloseIssueFlags(accept=True)
        )

        self.assertEqual(result[0], DECISION)
        self.assertEqual(resolve.call_args.kwargs["target_branch"], "")
        base_resolver.assert_not_called()

    def test_non_tty_skips_the_target_branch_read(self):
        result, _, resolve, _, base_resolver, _ = self._run(may_ask=False)

        self.assertEqual(result[0], DECISION)
        self.assertFalse(resolve.call_args.kwargs["is_tty"])
        self.assertEqual(resolve.call_args.kwargs["target_branch"], "")
        base_resolver.assert_not_called()

    def test_warning_is_printed_once_to_stderr(self):
        outcome = CloseIssueOutcome(
            warning="Could not check issue #7: boom. The local issue record was kept.",
            skipped_reason="verify-failed",
        )

        result, registry, _, _, _, secho = self._run(outcome=outcome)

        self.assertIsNone(result[0])
        self.assertIs(result[1], registry)
        self.assertIsNotNone(result[2])
        secho.assert_called_once_with(outcome.warning, fg="yellow", err=True)

    def test_scm_failure_is_reused_and_no_decision_is_made(self):
        result, _, resolve, scm, _, _ = self._run(
            scm=Mock(return_value=(None, None))
        )

        self.assertEqual(result, (None, None, (None, None)))
        scm.assert_called_once_with()
        resolve.assert_not_called()

    def test_registry_error_still_reaches_the_warning(self):
        outcome = CloseIssueOutcome(
            warning="Could not read the local issue record: bad yaml.",
            skipped_reason="registry-error",
        )
        registry = _Registry(error="bad yaml")

        result, returned_registry, resolve, scm, _, secho = self._run(
            registry=registry, outcome=outcome
        )

        self.assertIsNone(result[0])
        self.assertIs(returned_registry, registry)
        scm.assert_called_once_with()
        resolve.assert_called_once()
        secho.assert_called_once_with(outcome.warning, fg="yellow", err=True)


class CloseIssueFlagsCliTest(unittest.TestCase):
    def _invoke(self, *args):
        return CliRunner().invoke(cli, list(args))

    def test_both_flags_is_a_clear_error(self):
        result = self._invoke("--close-issue", "--no-close-issue")

        output = result.output + (result.stderr or "")
        self.assertEqual(result.exit_code, 1, output)
        self.assertIn(
            "--close-issue and --no-close-issue cannot be used together", output
        )

    def test_help_lists_both_flags(self):
        result = self._invoke("-h")

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("--close-issue", result.output)
        self.assertIn("--no-close-issue", result.output)

    def test_help_wins_over_the_conflict(self):
        result = self._invoke("-h", "--close-issue", "--no-close-issue")

        self.assertEqual(result.exit_code, 0, result.output + (result.stderr or ""))

    def test_run_without_a_record_keeps_the_flow_untouched(self):
        """SPEC #8: no record => no extra provider resolution, no forge call."""
        registry = _Registry()
        scm = Mock()
        resolve = Mock()

        with patch(
            "src.issue_autoclose.issue_registry.IssueRegistry",
            return_value=registry,
        ), patch(
            "src.issue_autoclose.resolve_close_issue.resolve_close_issue", resolve
        ), patch(
            "src.main._resolve_scm_context", scm
        ), patch(
            "src.main.check_unstaged_files", return_value=False
        ), patch(
            "src.main.setup_environment"
        ), patch(
            "src.main.check_and_update_hooks_scripts"
        ):
            result = CliRunner().invoke(cli, ["--no-unstaged-check"])

        self.assertEqual(result.exit_code, 0, result.output + (result.stderr or ""))
        self.assertEqual(registry.load_calls, 1)
        scm.assert_not_called()
        resolve.assert_not_called()


class PublishDirectlyResultTest(unittest.TestCase):
    def _publish(self, outcome):
        provider = SimpleNamespace(name="github", token="ghp_fake")
        with patch(
            "src.application.use_cases.publish_pull_request.publish_pull_request_use_case",
            return_value=outcome,
        ), patch(
            "src.core.get_current_branch", return_value="feat/x"
        ), patch(
            "src.main.click.confirm", return_value=False
        ), patch(
            "src.metrics.log_command_metric"
        ):
            return _publish_pr_directly(
                {"commit_message": "feat: x", "pr_description": "body"},
                provider,
                REPO_REF,
                "main",
                "pr.md",
            )

    def test_success_reports_the_publish(self):
        outcome = SimpleNamespace(
            status="success",
            url="https://github.com/natanfiuza/gitpr/pull/9",
            http_status=201,
            message="",
        )

        self.assertTrue(self._publish(outcome))

    def test_api_failure_does_not_report_the_publish(self):
        outcome = SimpleNamespace(
            status="error", url="", http_status=500, message="boom"
        )

        self.assertFalse(self._publish(outcome))

    def test_expired_token_does_not_report_the_publish(self):
        outcome = SimpleNamespace(
            status="error", url="", http_status=401, message="Bad credentials"
        )

        self.assertFalse(self._publish(outcome))


class ClearRecordTest(unittest.TestCase):
    def test_nothing_is_removed_without_a_decision(self):
        registry = _Registry(issue=REGISTERED)

        _clear_close_issue_record(registry, None)

        self.assertEqual(registry.clear_calls, 0)

    def test_nothing_is_removed_without_a_registry(self):
        _clear_close_issue_record(None, DECISION)

    def test_the_record_is_removed_once_a_decision_was_published(self):
        registry = _Registry(issue=REGISTERED)

        _clear_close_issue_record(registry, DECISION)

        self.assertEqual(registry.clear_calls, 1)

    def test_a_failing_clear_never_breaks_the_flow(self):
        registry = _Registry(issue=REGISTERED, clear_error=OSError("read-only"))

        _clear_close_issue_record(registry, DECISION)

        self.assertEqual(registry.clear_calls, 1)


if __name__ == "__main__":
    unittest.main()
