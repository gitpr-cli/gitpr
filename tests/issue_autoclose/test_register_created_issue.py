"""Tests for recording the issue ``gitpr -is`` just created (T3).

The unit tests point the registry at a temporary directory; the two
git-repository tests run ``git init`` there and never touch the checkout. The
wiring tests build the real ``IssueApp`` and stub only the widgets, the exit
call and the single registration seam, so ``action_create_issue`` runs its own
branching.
"""
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.infrastructure.scm.base import IssueResult, RepoRef
from src.issue_autoclose.issue_registry import (
    GITIGNORE_ENTRY,
    IssueRegistry,
    IssueRegistryError,
    RegisteredIssue,
)
from src.issue_autoclose.register_created_issue import (
    RegistrationOutcome,
    register_created_issue,
)
from src.ui.issue_app import IssueApp

REPO_REF = RepoRef(
    raw="https://github.com/owner/name.git",
    workspace="owner",
    name="name",
    provider="github",
)
RESULT = IssueResult(
    id="101",
    url="https://github.com/owner/name/issues/7",
    number=7,
    provider="github",
)


class _Provider:
    """A provider stub: only the attributes the code under test reads."""

    def __init__(self, name="github", result=None):
        self.name = name
        self.result = result
        self.created = []

    def create_issue(self, repo, request):
        self.created.append((repo, request))
        return self.result


class _Registry:
    """A registry stub that records what it was handed."""

    def __init__(self, error=None, gitignore_updated=False):
        self.error = error
        self.gitignore_updated = gitignore_updated
        self.recorded = []

    def record(self, issue):
        self.recorded.append(issue)
        if self.error is not None:
            raise self.error
        return type("RecordResult", (), {"gitignore_updated": self.gitignore_updated})()


def _git_init(root):
    subprocess.run(
        ["git", "init", "-q"],
        cwd=str(root),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


class RegisterCreatedIssueTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.registry = _Registry()

    def tearDown(self):
        self._tmp.cleanup()

    def _register(self, provider=None, repo_ref=REPO_REF, result=RESULT, title="Fix the thing", branch="feat/x"):
        return register_created_issue(
            provider or _Provider(),
            repo_ref,
            result,
            title,
            branch,
            registry=self.registry,
        )

    def test_github_is_recorded_with_every_field(self):
        outcome = self._register()

        self.assertTrue(outcome.recorded)
        self.assertEqual(outcome.skipped_reason, "")
        self.assertEqual(outcome.error, "")
        self.assertEqual(len(self.registry.recorded), 1)

        issue = self.registry.recorded[0]
        self.assertEqual(issue.repo, "owner/name")
        self.assertEqual(issue.number, 7)
        self.assertEqual(issue.title, "Fix the thing")
        self.assertEqual(issue.url, "https://github.com/owner/name/issues/7")
        self.assertEqual(issue.branch, "feat/x")
        # created_at is an ISO 8601 instant, the format the record re-reads.
        self.assertTrue(issue.created_at)
        self.assertIsNotNone(datetime.fromisoformat(issue.created_at))

    def test_non_github_forge_is_skipped_without_touching_the_registry(self):
        outcome = self._register(provider=_Provider(name="gitlab"))

        self.assertFalse(outcome.recorded)
        self.assertEqual(outcome.skipped_reason, "not-github")
        self.assertEqual(self.registry.recorded, [])

    def test_repository_label_must_be_owner_slash_name(self):
        repo_ref = RepoRef(raw="name", workspace="", name="name", provider="github")

        outcome = self._register(repo_ref=repo_ref)

        self.assertEqual(outcome.recorded, False)
        self.assertEqual(outcome.skipped_reason, "no-repo")
        self.assertEqual(self.registry.recorded, [])

    def test_invalid_number_or_url_is_skipped(self):
        cases = [
            IssueResult(id="1", url=RESULT.url, number=None, provider="github"),
            IssueResult(id="1", url=RESULT.url, number=0, provider="github"),
            IssueResult(id="1", url=RESULT.url, number=True, provider="github"),
            IssueResult(id="1", url="", number=7, provider="github"),
        ]
        for result in cases:
            with self.subTest(number=result.number, url=result.url):
                outcome = self._register(result=result)
                self.assertFalse(outcome.recorded)
                self.assertEqual(outcome.skipped_reason, "invalid-result")
        self.assertEqual(self.registry.recorded, [])

    def test_registry_error_becomes_write_failed(self):
        self.registry.error = IssueRegistryError("disk is read-only")

        outcome = self._register()

        self.assertFalse(outcome.recorded)
        self.assertEqual(outcome.skipped_reason, "write-failed")
        self.assertIn("disk is read-only", outcome.error)

    def test_unexpected_error_is_swallowed_too(self):
        # Bookkeeping must never break a creation that already succeeded.
        self.registry.error = RuntimeError("boom")

        outcome = self._register()

        self.assertFalse(outcome.recorded)
        self.assertEqual(outcome.skipped_reason, "write-failed")
        self.assertIn("boom", outcome.error)

    def test_gitignore_flag_is_propagated(self):
        self.registry.gitignore_updated = True

        outcome = self._register()

        self.assertTrue(outcome.recorded)
        self.assertTrue(outcome.gitignore_updated)


class RegisterAgainstRealRegistryTest(unittest.TestCase):
    """End-to-end through ``IssueRegistry`` on a throwaway repository."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git_init(self.root)
        self.registry = IssueRegistry(
            path=self.root / ".gitpr" / "conf" / "github.yml"
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_record_reads_back_after_registration(self):
        outcome = register_created_issue(
            _Provider(), REPO_REF, RESULT, "Fix the thing", "feat/x", registry=self.registry
        )

        self.assertTrue(outcome.recorded)
        loaded = self.registry.load()
        self.assertEqual(loaded.error, "")
        self.assertEqual(
            loaded.issue,
            RegisteredIssue(
                repo="owner/name",
                number=7,
                title="Fix the thing",
                url=RESULT.url,
                created_at=loaded.issue.created_at,
                branch="feat/x",
            ),
        )
        # The first write also puts the record out of the repository's sight.
        self.assertTrue(outcome.gitignore_updated)
        gitignore = (self.root / ".gitignore").read_text(encoding="utf-8", errors="replace")
        self.assertIn(GITIGNORE_ENTRY, gitignore.splitlines())


class _Widget:
    def __init__(self, value="", text=""):
        self.value = value
        self.text = text


class IssueAppWiringTest(unittest.TestCase):
    """``action_create_issue`` must record exactly after a GitHub success."""

    def setUp(self):
        self.widgets = {
            "#issue_title": _Widget(value="My title"),
            "#issue_body": _Widget(text="My body"),
        }
        self.exit = Mock()
        self.log_metric = Mock()

    def _build_app(self, provider):
        with patch("src.ui.issue_app.get_current_branch", return_value="feat/x"):
            app = IssueApp(
                issue_data={"titulo": "Draft", "corpo": "Draft body"},
                repo_info="owner/name",
                github_token="token",
                provider=provider,
                repo_ref=REPO_REF,
            )
        app.query_one = lambda selector, *args, **kwargs: self.widgets[selector]
        app.exit = self.exit
        return app

    def _run_create(self, provider, outcome=None):
        app = self._build_app(provider)
        register = Mock(return_value=outcome or RegistrationOutcome(recorded=True))
        with patch("src.ui.issue_app.register_created_issue", register), patch(
            "src.metrics.log_command_metric", self.log_metric
        ):
            app.action_create_issue()
        return app, register

    def test_github_creation_records_the_issue(self):
        provider = _Provider(result=RESULT)

        app, register = self._run_create(provider)

        register.assert_called_once()
        args = register.call_args.args
        self.assertEqual(args, (provider, REPO_REF, RESULT, "My title", "feat/x"))
        self.assertEqual(app.final_action, "created")
        self.assertIn(RESULT.url, app.final_message)
        self.exit.assert_called_once()
        self.log_metric.assert_called_with(
            command="issue:github_create", status="success", provider="github"
        )

    def test_non_github_creation_does_not_record(self):
        provider = _Provider(name="gitlab", result=RESULT)

        app, register = self._run_create(provider)

        register.assert_not_called()
        self.assertEqual(app.final_action, "created")

    def test_failed_recording_warns_and_keeps_the_creation(self):
        provider = _Provider(result=RESULT)

        app, _ = self._run_create(
            provider,
            outcome=RegistrationOutcome(skipped_reason="write-failed", error="disk full"),
        )

        self.assertEqual(app.final_action, "created")
        self.assertIn("disk full", app.final_message)
        self.log_metric.assert_called_with(
            command="issue:github_create", status="success", provider="github"
        )

    def test_gitignore_update_is_announced(self):
        provider = _Provider(result=RESULT)

        app, _ = self._run_create(
            provider, outcome=RegistrationOutcome(recorded=True, gitignore_updated=True)
        )

        self.assertEqual(app.final_action, "created")
        self.assertIn(GITIGNORE_ENTRY, app.final_message)


if __name__ == "__main__":
    unittest.main()
