"""Tests for the automatic issue-closure decision (T4).

The provider and the registry are plain fakes: the decision never touches the
network or the checkout by itself, and every edge case of the tree — a corrupt
record, a missing issue, a forge that does not answer — is reachable by
configuring one of them. ``ask`` is a ``Mock`` so the question can be inspected
without a terminal.
"""
import unittest
from dataclasses import FrozenInstanceError
from unittest.mock import Mock

from click.exceptions import Abort

from src.infrastructure.scm.base import IssueInfo, RepoRef, ScmProviderError
from src.issue_autoclose.issue_registry import (
    IssueRegistryError,
    RegisteredIssue,
    RegistryLoad,
)
from src.issue_autoclose.resolve_close_issue import (
    CloseIssueFlags,
    resolve_close_issue,
)

REPO_REF = RepoRef(
    raw="https://github.com/owner/name.git",
    workspace="owner",
    name="name",
    provider="github",
)
REGISTERED = RegisteredIssue(
    repo="owner/name",
    number=7,
    title="Fix the thing",
    url="https://github.com/owner/name/issues/7",
    created_at="2026-11-01T09:00:00-03:00",
    branch="feat/x",
)
OPEN = IssueInfo(
    number=7,
    title="Fix the thing",
    url="https://github.com/owner/name/issues/7",
    state="open",
    is_pull_request=False,
)


class _Provider:
    """A plain provider stub — ``Mock`` would fake a truthy ``name``."""

    def __init__(
        self,
        name="github",
        info=None,
        error=None,
        line="close #7",
        default_branch="main",
        default_branch_error=None,
    ):
        self.name = name
        self.info = OPEN if info is None else info
        self.error = error
        self.line = line
        self.default_branch = default_branch
        self.default_branch_error = default_branch_error
        self.issue_calls = []
        self.branch_calls = []
        self.line_calls = []

    def get_issue(self, repo, number, timeout=5):
        self.issue_calls.append((repo, number, timeout))
        if self.error is not None:
            raise self.error
        return self.info

    def get_default_branch(self, repo, timeout=5):
        self.branch_calls.append((repo, timeout))
        if self.default_branch_error is not None:
            raise self.default_branch_error
        return self.default_branch

    def closing_line(self, number):
        self.line_calls.append(number)
        return self.line


class _Registry:
    """A registry stub that counts reads and removals."""

    def __init__(self, issue=REGISTERED, error="", load_error=None, clear_error=None):
        self.issue = issue
        self.error = error
        self.load_error = load_error
        self.clear_error = clear_error
        self.load_calls = 0
        self.clear_calls = 0

    def load(self):
        self.load_calls += 1
        if self.load_error is not None:
            raise self.load_error
        return RegistryLoad(issue=self.issue, error=self.error)

    def clear(self):
        self.clear_calls += 1
        if self.clear_error is not None:
            raise self.clear_error


class ResolveCloseIssueTest(unittest.TestCase):
    def setUp(self):
        self.provider = _Provider()
        self.registry = _Registry()
        self.ask = Mock(return_value=True)

    def _resolve(
        self,
        provider=None,
        registry=None,
        repo_ref=REPO_REF,
        flags=None,
        enabled=True,
        is_tty=True,
        target_branch="main",
        ask=None,
        timeout=5,
    ):
        return resolve_close_issue(
            provider or self.provider,
            registry or self.registry,
            repo_ref,
            flags=flags,
            enabled=enabled,
            is_tty=is_tty,
            target_branch=target_branch,
            ask=self.ask if ask is None else ask,
            timeout=timeout,
        )


class GatesTest(ResolveCloseIssueTest):
    def test_flag_disabled_skips_before_reading_the_registry(self):
        outcome = self._resolve(flags=CloseIssueFlags(disabled=True))

        self.assertEqual(outcome.skipped_reason, "flag-disabled")
        self.assertIsNone(outcome.decision)
        self.assertEqual(self.registry.load_calls, 0)
        self.assertEqual(self.provider.issue_calls, [])
        self.ask.assert_not_called()

    def test_feature_disabled_by_config_skips_before_reading_the_registry(self):
        outcome = self._resolve(enabled=False)

        self.assertEqual(outcome.skipped_reason, "disabled")
        self.assertEqual(self.registry.load_calls, 0)
        self.assertEqual(self.provider.issue_calls, [])

    def test_non_github_provider_is_skipped_without_network(self):
        outcome = self._resolve(provider=_Provider(name="gitlab"))

        self.assertEqual(outcome.skipped_reason, "not-github")
        self.assertEqual(self.registry.load_calls, 0)
        self.assertEqual(self.provider.issue_calls, [])

    def test_flag_disabled_wins_over_a_non_github_provider(self):
        outcome = self._resolve(
            provider=_Provider(name="gitlab"),
            flags=CloseIssueFlags(disabled=True),
        )

        self.assertEqual(outcome.skipped_reason, "flag-disabled")


class RegistryTest(ResolveCloseIssueTest):
    def test_missing_record_is_a_silent_skip(self):
        outcome = self._resolve(registry=_Registry(issue=None))

        self.assertEqual(outcome.skipped_reason, "no-record")
        self.assertEqual(outcome.warning, "")
        self.assertEqual(self.provider.issue_calls, [])

    def test_corrupt_record_warns_and_skips_without_network(self):
        outcome = self._resolve(registry=_Registry(error="bad yaml"))

        self.assertEqual(outcome.skipped_reason, "registry-error")
        self.assertIn("bad yaml", outcome.warning)
        self.assertEqual(self.registry.clear_calls, 0)
        self.assertEqual(self.provider.issue_calls, [])

    def test_registry_load_raising_is_swallowed(self):
        outcome = self._resolve(registry=_Registry(load_error=RuntimeError("boom")))

        self.assertEqual(outcome.skipped_reason, "registry-error")
        self.assertIn("boom", outcome.warning)
        self.assertEqual(self.provider.issue_calls, [])

    def test_record_of_another_repository_is_ignored_and_kept(self):
        registry = _Registry(issue=REGISTERED)

        outcome = resolve_close_issue(
            self.provider,
            registry,
            RepoRef(raw="name", workspace="other", name="repo", provider="github"),
            ask=self.ask,
        )

        self.assertEqual(outcome.skipped_reason, "other-repo")
        self.assertEqual(registry.clear_calls, 0)
        self.assertEqual(self.provider.issue_calls, [])
        # The record was read once; the comparison never re-read the file.
        self.assertEqual(registry.load_calls, 1)

    def test_repository_comparison_ignores_case(self):
        registry = _Registry(
            issue=RegisteredIssue(
                repo="OWNER/Name",
                number=7,
                title="Fix the thing",
                url=REGISTERED.url,
                created_at=REGISTERED.created_at,
            )
        )

        outcome = self._resolve(registry=registry)

        self.assertTrue(outcome.accepted)
        self.assertEqual(self.provider.issue_calls, [(REPO_REF, 7, 5)])

    def test_unresolved_repository_is_ignored_without_network(self):
        empty_ref = RepoRef(raw="name", workspace="", name="", provider="github")

        outcome = self._resolve(repo_ref=empty_ref)

        self.assertEqual(outcome.skipped_reason, "other-repo")
        self.assertEqual(self.provider.issue_calls, [])


class VerificationTest(ResolveCloseIssueTest):
    def test_issue_is_fetched_by_the_recorded_number_and_timeout(self):
        self._resolve(timeout=9)

        self.assertEqual(self.provider.issue_calls, [(REPO_REF, 7, 9)])

    def test_closed_issue_is_cleared_silently_without_asking(self):
        outcome = self._resolve(
            provider=_Provider(info=IssueInfo(7, "Fix", "", state="closed"))
        )

        self.assertEqual(outcome.skipped_reason, "issue-not-open")
        self.assertEqual(outcome.warning, "")
        self.assertEqual(self.registry.clear_calls, 1)
        self.ask.assert_not_called()

    def test_state_is_compared_case_and_whitespace_insensitively(self):
        outcome = self._resolve(
            provider=_Provider(info=IssueInfo(7, "Fix", "", state=" OPEN "))
        )

        self.assertTrue(outcome.accepted)

    def test_unknown_state_is_treated_as_not_open(self):
        outcome = self._resolve(provider=_Provider(info=IssueInfo(7, "Fix", "", state="")))

        self.assertEqual(outcome.skipped_reason, "issue-not-open")
        self.assertEqual(self.registry.clear_calls, 1)

    def test_pull_request_number_wins_over_an_open_state(self):
        outcome = self._resolve(
            provider=_Provider(
                info=IssueInfo(7, "Fix", "", state="open", is_pull_request=True)
            )
        )

        self.assertEqual(outcome.skipped_reason, "issue-is-pr")
        self.assertEqual(self.registry.clear_calls, 1)
        self.ask.assert_not_called()

    def test_missing_issue_404_is_cleared_silently(self):
        outcome = self._resolve(
            provider=_Provider(error=ScmProviderError("github", 404, "Not Found"))
        )

        self.assertEqual(outcome.skipped_reason, "issue-missing")
        self.assertEqual(outcome.warning, "")
        self.assertEqual(self.registry.clear_calls, 1)

    def test_failed_clear_is_swallowed(self):
        registry = _Registry(clear_error=IssueRegistryError("read-only"))
        provider = _Provider(error=ScmProviderError("github", 404, "Not Found"))

        outcome = self._resolve(provider=provider, registry=registry)

        self.assertEqual(outcome.skipped_reason, "issue-missing")

    def test_http_failures_warn_and_keep_the_record(self):
        for status in (401, 403, 0, 500, 503, 429):
            with self.subTest(http_status=status):
                self.registry = _Registry()
                outcome = self._resolve(
                    provider=_Provider(
                        error=ScmProviderError("github", status, "no answer")
                    )
                )

                self.assertEqual(outcome.skipped_reason, "verify-failed")
                self.assertIn("no answer", outcome.warning)
                self.assertEqual(self.registry.clear_calls, 0)

    def test_unexpected_provider_exception_warns_and_keeps_the_record(self):
        outcome = self._resolve(provider=_Provider(error=RuntimeError("boom")))

        self.assertEqual(outcome.skipped_reason, "verify-failed")
        self.assertIn("boom", outcome.warning)
        self.assertEqual(self.registry.clear_calls, 0)

    def test_verification_warning_mentions_the_issue_number(self):
        outcome = self._resolve(
            provider=_Provider(error=ScmProviderError("github", 500, "boom"))
        )

        self.assertIn("#7", outcome.warning)


class DecisionTest(ResolveCloseIssueTest):
    def test_close_issue_flag_accepts_without_asking(self):
        outcome = self._resolve(flags=CloseIssueFlags(accept=True))

        self.assertEqual(outcome.skipped_reason, "")
        self.assertTrue(outcome.accepted)
        self.assertFalse(outcome.asked)
        self.assertEqual(outcome.decision.number, 7)
        self.assertEqual(outcome.decision.line, "close #7")
        self.ask.assert_not_called()
        self.assertEqual(self.provider.branch_calls, [])
        self.assertEqual(self.registry.clear_calls, 0)

    def test_close_issue_flag_still_verifies_the_issue(self):
        outcome = self._resolve(
            provider=_Provider(error=ScmProviderError("github", 500, "boom")),
            flags=CloseIssueFlags(accept=True),
        )

        self.assertEqual(outcome.skipped_reason, "verify-failed")
        self.assertIsNone(outcome.decision)

    def test_without_a_tty_nothing_is_asked_or_inserted(self):
        outcome = self._resolve(is_tty=False)

        self.assertEqual(outcome.skipped_reason, "no-tty")
        self.assertIsNone(outcome.decision)
        self.ask.assert_not_called()
        self.assertEqual(self.provider.branch_calls, [])
        self.assertEqual(self.provider.line_calls, [])
        self.assertEqual(self.registry.clear_calls, 0)

    def test_without_an_ask_callable_nothing_is_asked(self):
        outcome = resolve_close_issue(
            self.provider, self.registry, REPO_REF, ask=None
        )

        self.assertEqual(outcome.skipped_reason, "no-tty")

    def test_without_a_tty_the_issue_is_still_verified(self):
        self._resolve(is_tty=False)

        self.assertEqual(self.provider.issue_calls, [(REPO_REF, 7, 5)])

    def test_open_issue_with_yes_returns_the_decision(self):
        outcome = self._resolve()

        self.assertEqual(outcome.skipped_reason, "")
        self.assertTrue(outcome.asked)
        self.assertTrue(outcome.accepted)
        self.assertEqual(outcome.decision.number, 7)
        self.assertEqual(outcome.decision.title, "Fix the thing")
        self.assertEqual(outcome.decision.line, "close #7")
        self.assertEqual(self.registry.clear_calls, 0)

    def test_open_issue_with_no_returns_no_decision(self):
        self.ask.return_value = False

        outcome = self._resolve()

        self.assertEqual(outcome.skipped_reason, "declined")
        self.assertTrue(outcome.asked)
        self.assertFalse(outcome.accepted)
        self.assertIsNone(outcome.decision)
        self.assertEqual(self.registry.clear_calls, 0)

    def test_ask_is_called_with_yes_as_the_default(self):
        self._resolve()

        self.ask.assert_called_once()
        self.assertEqual(self.ask.call_args.kwargs, {"default": True})

    def test_question_names_the_issue_title_and_closing_line(self):
        self._resolve()

        question = self.ask.call_args.args[0]
        self.assertIn("#7", question)
        self.assertIn("Fix the thing", question)
        self.assertIn('"close #7"', question)

    def test_closing_line_comes_from_the_provider(self):
        provider = _Provider(line="Closes #7")

        outcome = self._resolve(provider=provider)

        self.assertEqual(outcome.decision.line, "Closes #7")
        self.assertEqual(provider.line_calls, [7])

    def test_empty_forge_title_falls_back_to_the_recorded_title(self):
        outcome = self._resolve(
            provider=_Provider(info=IssueInfo(7, "  ", "", state="open"))
        )

        self.assertEqual(outcome.decision.title, "Fix the thing")

    def test_ctrl_c_propagates_and_keeps_the_record(self):
        self.ask.side_effect = Abort()

        with self.assertRaises(Abort):
            self._resolve()

        self.assertEqual(self.registry.clear_calls, 0)

    def test_outcome_is_frozen(self):
        outcome = self._resolve()

        with self.assertRaises(FrozenInstanceError):
            outcome.skipped_reason = "changed"


class BranchWarningTest(ResolveCloseIssueTest):
    def test_target_branch_different_from_default_warns(self):
        outcome = self._resolve(target_branch="develop")

        question = self.ask.call_args.args[0]
        self.assertIn('"develop"', question)
        self.assertIn('"main"', question)
        self.assertIn("default branch", question)
        self.assertIn("develop", outcome.decision.target_branch_warning)
        self.assertEqual(outcome.warning, "")

    def test_declined_decision_still_shows_the_warning_in_the_question(self):
        self.ask.return_value = False

        outcome = self._resolve(target_branch="develop")

        self.assertIn("default branch", self.ask.call_args.args[0])
        self.assertIsNone(outcome.decision)

    def test_same_target_and_default_branch_has_no_warning(self):
        outcome = self._resolve(target_branch="main")

        self.assertEqual(outcome.decision.target_branch_warning, "")
        self.assertNotIn("Warning:", self.ask.call_args.args[0])

    def test_empty_default_branch_has_no_warning(self):
        outcome = self._resolve(
            provider=_Provider(default_branch=""), target_branch="develop"
        )

        self.assertEqual(outcome.decision.target_branch_warning, "")

    def test_empty_target_branch_has_no_warning(self):
        outcome = self._resolve(target_branch="")

        self.assertEqual(outcome.decision.target_branch_warning, "")

    def test_default_branch_failure_keeps_the_question_plain(self):
        outcome = self._resolve(
            provider=_Provider(
                default_branch_error=ScmProviderError("github", 500, "boom")
            ),
            target_branch="develop",
        )

        self.assertEqual(outcome.decision.target_branch_warning, "")
        self.assertTrue(outcome.accepted)

    def test_default_branch_is_fetched_only_on_the_ask_path(self):
        self._resolve(
            flags=CloseIssueFlags(accept=True),
            target_branch="develop",
        )
        self.assertEqual(self.provider.branch_calls, [])

        self.provider = _Provider()
        self._resolve(is_tty=False, target_branch="develop")
        self.assertEqual(self.provider.branch_calls, [])

        self.provider = _Provider()
        self._resolve(target_branch="develop", timeout=8)
        self.assertEqual(self.provider.branch_calls, [(REPO_REF, 8)])


if __name__ == "__main__":
    unittest.main()
