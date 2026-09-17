"""Tests for src/reviewer_resolution.py — identity -> forge login.

The bug this module exists for: the reviewer field shows an author NAME when
no handle resolves, the user types that name, and the CLI used to POST it as
if it were a login. GitHub answers 201 to an unknown login and attaches
nobody, so the request vanished without a trace. Everything here is offline:
the provider is a fake.
"""
import unittest
from types import SimpleNamespace

from src.reviewer_resolution import (
    ResolvedReviewer,
    ResolutionOutcome,
    match_candidate,
    resolve_candidates,
    resolve_typed_reviewers,
)
from src.reviewer_suggestion import ReviewerCandidate

# The real-world case: a corporate address with no public GitHub account and
# no noreply form, so email_to_handle cannot see it.
EDUARDA = ReviewerCandidate(
    author_name="Eduarda Leal",
    author_email="eduardaleal@grafjb.com.br",
    touched_lines=12,
    touched_files=3,
    last_touch_date="2026-09-10",
    last_commit_hash="abc123",
)


class _Provider:
    """Fake provider recording every call it receives."""

    def __init__(
        self,
        commit_logins=None,
        handles=None,
        users=None,
        raise_on_commit=None,
        raise_on_users=None,
    ):
        self.commit_logins = commit_logins or {}
        self.handles = handles or {}
        self.users = users if users is not None else {}
        self.raise_on_commit = raise_on_commit
        self.raise_on_users = raise_on_users
        self.calls = []

    def get_commit_author_login(self, repo, sha, timeout=10):
        self.calls.append(("commit", sha))
        if self.raise_on_commit:
            raise self.raise_on_commit
        return self.commit_logins.get(sha)

    def email_to_handle(self, email, timeout=15):
        self.calls.append(("email", email))
        return self.handles.get(email)

    def get_user_login(self, login, timeout=10):
        self.calls.append(("user", login))
        if self.raise_on_users:
            raise self.raise_on_users
        return self.users.get(login)


class TestResolveCandidates(unittest.TestCase):
    def test_commit_author_is_the_primary_path(self):
        provider = _Provider(commit_logins={"abc123": "eduarda"})

        resolutions = resolve_candidates([EDUARDA], provider, "repo")

        self.assertEqual(len(resolutions), 1)
        self.assertEqual(resolutions[0].login, "eduarda")
        self.assertEqual(resolutions[0].name, "Eduarda Leal")
        # The email search is not even tried once the commit resolves.
        self.assertEqual(provider.calls, [("commit", "abc123")])

    def test_email_search_is_the_fallback(self):
        provider = _Provider(handles={"eduardaleal@grafjb.com.br": "eduarda"})

        resolutions = resolve_candidates([EDUARDA], provider, "repo")

        self.assertEqual(resolutions[0].login, "eduarda")
        self.assertEqual(provider.calls, [("commit", "abc123"), ("email", EDUARDA.author_email)])

    def test_unresolvable_person_keeps_an_empty_login(self):
        provider = _Provider()

        resolutions = resolve_candidates([EDUARDA], provider, "repo")

        self.assertEqual(resolutions[0].login, "")
        self.assertEqual(resolutions[0].key, "eduardaleal@grafjb.com.br")

    def test_commit_lookup_failure_falls_through_to_email(self):
        provider = _Provider(
            handles={"eduardaleal@grafjb.com.br": "eduarda"},
            raise_on_commit=RuntimeError("boom"),
        )

        resolutions = resolve_candidates([EDUARDA], provider, "repo")

        self.assertEqual(resolutions[0].login, "eduarda")

    def test_candidate_without_commit_hash_skips_the_commit_call(self):
        candidate = ReviewerCandidate(author_name="Ana", author_email="ana@x.com")
        provider = _Provider(handles={"ana@x.com": "ana"})

        resolve_candidates([candidate], provider, "repo")

        self.assertEqual(provider.calls, [("email", "ana@x.com")])

    def test_provider_without_the_methods_is_tolerated(self):
        """Fakes and non-GitHub providers keep working (duck-typed getattr)."""
        resolutions = resolve_candidates([EDUARDA], SimpleNamespace(), "repo")

        self.assertEqual(resolutions[0].login, "")


class TestMatchCandidate(unittest.TestCase):
    def setUp(self):
        self.resolutions = [
            ResolvedReviewer(name="Ana Lima", email="ana@example.com", login="ana"),
            ResolvedReviewer(name="Eduarda Leal", email="ed@corp.com", login=""),
        ]

    def test_matches_login_name_and_email(self):
        for value in ("ana", "ANA", " Ana Lima ", "ana@example.com", "Ana@Example.com"):
            with self.subTest(value=value):
                self.assertIsNotNone(match_candidate(value, self.resolutions))

    def test_partial_name_never_matches(self):
        self.assertIsNone(match_candidate("Eduarda", self.resolutions))
        self.assertIsNone(match_candidate("Leal", self.resolutions))

    def test_unknown_value_matches_nothing(self):
        self.assertIsNone(match_candidate("carla", self.resolutions))
        self.assertIsNone(match_candidate("", self.resolutions))


class TestResolveTypedReviewers(unittest.TestCase):
    """The reported bug, at the resolution layer."""

    def test_typed_display_name_of_an_unresolved_person_is_dropped(self):
        provider = _Provider()
        view_key = "eduardaleal@grafjb.com.br"

        outcome = resolve_typed_reviewers(
            ["Eduarda Leal"],
            resolutions=[ResolvedReviewer(name="Eduarda Leal", email=view_key, login="")],
            known_logins=[],
            provider=provider,
            repo="repo",
        )

        self.assertEqual(outcome.logins, [], "the name must never be submitted")
        self.assertEqual(len(outcome.dropped), 1)
        self.assertIn("Eduarda Leal", outcome.dropped[0][0])
        self.assertIn("no GitHub account found", outcome.dropped[0][1])
        # The name is not an email, so the email path is skipped; the login
        # lookup is the last rung and the real provider rejects a value with a
        # space before spending a request on it (tests/scm/test_github_provider.py).
        self.assertEqual(provider.calls, [("user", "Eduarda Leal")])

    def test_prefilled_handle_passes_through_without_any_request(self):
        provider = _Provider()

        outcome = resolve_typed_reviewers(
            ["ana", "bob"],
            resolutions=[],
            known_logins=["ana", "bob"],
            provider=provider,
            repo="repo",
        )

        self.assertEqual(outcome.logins, ["ana", "bob"])
        self.assertEqual(outcome.dropped, [])
        self.assertEqual(provider.calls, [])

    def test_typed_name_of_a_resolved_person_uses_its_login(self):
        provider = _Provider()

        outcome = resolve_typed_reviewers(
            ["Eduarda Leal"],
            resolutions=[
                ResolvedReviewer(
                    name="Eduarda Leal", email="ed@corp.com", login="eduarda"
                )
            ],
            known_logins=[],
            provider=provider,
            repo="repo",
        )

        self.assertEqual(outcome.logins, ["eduarda"])
        self.assertEqual(provider.calls, [], "already resolved — no new lookup")

    def test_typed_email_is_looked_up(self):
        provider = _Provider(handles={"nova@example.com": "nova"})

        outcome = resolve_typed_reviewers(
            ["nova@example.com"], provider=provider, repo="repo"
        )

        self.assertEqual(outcome.logins, ["nova"])
        self.assertEqual(provider.calls, [("email", "nova@example.com")])

    def test_typed_login_is_validated_on_the_forge(self):
        provider = _Provider(users={"carla": "Carla"})

        outcome = resolve_typed_reviewers(["carla"], provider=provider, repo="repo")

        self.assertEqual(outcome.logins, ["Carla"], "the canonical login is used")
        self.assertEqual(provider.calls, [("user", "carla")])

    def test_unknown_login_is_reported_not_sent(self):
        provider = _Provider()

        outcome = resolve_typed_reviewers(["ghost"], provider=provider, repo="repo")

        self.assertEqual(outcome.logins, [])
        self.assertEqual(len(outcome.dropped), 1)

    def test_lookup_failure_is_reported_not_sent(self):
        provider = _Provider(raise_on_users=RuntimeError("gateway down"))

        outcome = resolve_typed_reviewers(["carla"], provider=provider, repo="repo")

        self.assertEqual(outcome.logins, [])
        self.assertEqual(len(outcome.dropped), 1)

    def test_duplicates_are_collapsed_and_blanks_ignored(self):
        provider = _Provider()

        outcome = resolve_typed_reviewers(
            ["ana", "ANA", " ana ", "", "  "],
            known_logins=["ana"],
            provider=provider,
            repo="repo",
        )

        self.assertEqual(outcome.logins, ["ana"])
        self.assertEqual(outcome.dropped, [])

    def test_no_provider_never_raises(self):
        outcome = resolve_typed_reviewers(["ana", "ana@example.com"])

        self.assertIsInstance(outcome, ResolutionOutcome)
        self.assertEqual(outcome.logins, [])
        self.assertEqual(len(outcome.dropped), 2)


if __name__ == "__main__":
    unittest.main()
