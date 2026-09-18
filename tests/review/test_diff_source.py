"""Unit tests for DiffSource — the provenance contract of both review flows.

The object carries no logic worth mocking: what these tests pin down is the
cache scope, because that single string is what keeps a review of pull request
42 from being answered by the cached review of an identical local diff (and the
other way round). The empty scope of the local origin is asserted as hard as the
remote one — it is what makes the switch to DiffSource invisible to every cache
the user already has.
"""
import unittest

from src.infrastructure.scm.base import RepoRef
from src.review.diff_source import DiffOrigin, DiffSource

DIFF = "diff --git a/src/app.py b/src/app.py\n@@ -1 +1 @@\n-a\n+b\n"


def _repo():
    return RepoRef(
        raw="https://github.com/owner/repo.git",
        workspace="owner",
        name="repo",
        provider="github",
    )


def _local():
    return DiffSource(origin=DiffOrigin.LOCAL, content=DIFF, identifier="head")


def _remote(identifier="pr-42", pr_number=42):
    return DiffSource(
        origin=DiffOrigin.REMOTE_PR,
        content=DIFF,
        identifier=identifier,
        pr_number=pr_number,
        repo_ref=_repo(),
        base_branch="main",
        head_branch="feature/login",
    )


class TestDiffOrigin(unittest.TestCase):
    def test_origin_values_are_the_serialised_form(self):
        """The enum value is what reaches the JSON of the MCP tool."""
        self.assertEqual(DiffOrigin.LOCAL.value, "local")
        self.assertEqual(DiffOrigin.REMOTE_PR.value, "remote_pr")


class TestCacheScope(unittest.TestCase):
    def test_local_origin_has_an_empty_scope(self):
        """Empty, so the MD5 of every existing local review is unchanged."""
        self.assertEqual(_local().cache_scope, "")

    def test_remote_origin_is_scoped_by_identifier(self):
        self.assertEqual(_remote().cache_scope, "::diff-source::pr-42")

    def test_two_pull_requests_never_share_a_scope(self):
        self.assertNotEqual(_remote("pr-42").cache_scope, _remote("pr-43").cache_scope)

    def test_the_same_pull_request_keeps_its_scope(self):
        """The cache only helps if the same PR rebuilds the same key."""
        self.assertEqual(_remote().cache_scope, _remote().cache_scope)

    def test_a_remote_scope_never_collides_with_a_local_one(self):
        self.assertNotEqual(_remote().cache_scope, _local().cache_scope)

    def test_the_scope_is_a_suffix_not_a_replacement(self):
        """It is concatenated onto the prompt hash, so it must only append."""
        self.assertTrue(_remote().cache_scope.startswith("::"))


class TestIsRemote(unittest.TestCase):
    def test_local_source_is_not_remote(self):
        self.assertFalse(_local().is_remote)

    def test_remote_source_is_remote(self):
        self.assertTrue(_remote().is_remote)


class TestProvenanceFields(unittest.TestCase):
    def test_local_carries_no_pull_request_metadata(self):
        """The working tree has no PR behind it — the fields stay empty."""
        source = _local()
        self.assertIsNone(source.pr_number)
        self.assertIsNone(source.repo_ref)
        self.assertIsNone(source.base_branch)
        self.assertIsNone(source.head_branch)

    def test_remote_carries_the_branches_of_the_pull_request(self):
        source = _remote()
        self.assertEqual(source.pr_number, 42)
        self.assertEqual(source.base_branch, "main")
        self.assertEqual(source.head_branch, "feature/login")
        self.assertEqual(source.repo_ref.name, "repo")

    def test_the_dataclass_is_frozen(self):
        """Provenance is decided once; nothing downstream may rewrite it."""
        with self.assertRaises(Exception):
            _remote().pr_number = 7


if __name__ == "__main__":
    unittest.main()
