"""Unit tests for the remote pull request review orchestrator.

The forge and the AI are both stubbed: the provider is a hand-written object
with the four methods the pipeline uses, so the assertions can be about *what
the pipeline asked of them* — which diff reached the engine, with which cache
scope, whether the forge was written to, and how many times the model was
called. The last one is the point of most of the error cases: a bad pull request
number has to cost nothing, and "no AI call" is only provable with a mock.

The provider is a stub rather than a real GitHubProvider with `requests` patched
because the pipeline is provider-agnostic by design; the providers themselves
are covered in tests/scm/ against their real HTTP calls.
"""
import unittest
from unittest.mock import patch

from src.i18n import CURRENT_LANG, set_lang
from src.infrastructure.scm.base import PullRequestResult, RepoRef, ScmProviderError
from src.review.diff_source import DiffOrigin
from src.review.remote_pr import (
    ReviewPrError,
    build_comment_body,
    review_remote_pr,
)

PATCH = (
    "diff --git a/src/app.py b/src/app.py\n"
    "--- a/src/app.py\n"
    "+++ b/src/app.py\n"
    "@@ -1,2 +1,2 @@\n"
    " def greet(name):\n"
    "-    return 'Hello'\n"
    "+    return f'Hello, {name}'\n"
)

LOCK = (
    "diff --git a/poetry.lock b/poetry.lock\n"
    "--- a/poetry.lock\n"
    "+++ b/poetry.lock\n"
    "@@ -1 +1 @@\n"
    "-old\n"
    "+new\n"
)

REVIEW = "## Review\n\nThe argument is ignored — use it or drop it."


def _repo():
    return RepoRef(
        raw="https://github.com/owner/repo.git",
        workspace="owner",
        name="repo",
        provider="github",
    )


def _pr(number=42, state="open", source_branch="feature/login", target_branch="main"):
    return PullRequestResult(
        id=number,
        url=f"https://github.com/owner/repo/pull/{number}",
        number=number,
        state=state,
        source_branch=source_branch,
        target_branch=target_branch,
        provider="github",
    )


class FakeProvider:
    """The four methods the review pipeline uses, and a record of the calls.

    ``supports_reviewable_diff`` is an instance attribute so a test can flip it
    the way Azure DevOps does — with the class attribute it declares.
    """

    name = "github"

    def __init__(
        self,
        diff=PATCH,
        pr=None,
        supports_reviewable_diff=True,
        pr_error=None,
        diff_error=None,
    ):
        self.diff = diff
        self._pr = pr if pr is not None else _pr()
        self.supports_reviewable_diff = supports_reviewable_diff
        self.pr_error = pr_error
        self.diff_error = diff_error
        self.comments = []
        self.pr_calls = []
        self.diff_calls = []

    def get_pull_request(self, repo, pr_id):
        self.pr_calls.append((repo, pr_id))
        if self.pr_error:
            raise self.pr_error
        return self._pr

    def get_pull_request_diff(self, repo, pr_id):
        self.diff_calls.append((repo, pr_id))
        if self.diff_error:
            raise self.diff_error
        return self.diff

    def add_comment(self, repo, pr_id, body):
        self.comments.append((repo, pr_id, body))


class RemoteReviewTestCase(unittest.TestCase):
    """Pins the interface language and stubs the two outbound layers."""

    @classmethod
    def setUpClass(cls):
        cls._previous_lang = CURRENT_LANG
        set_lang("en_us")

    @classmethod
    def tearDownClass(cls):
        set_lang(cls._previous_lang)

    def setUp(self):
        self.provider = FakeProvider()
        self.patterns = []

        engine = patch(
            "src.core.generate_pr_content",
            return_value={"review": REVIEW},
        )
        excludes = patch(
            "src.core.get_smart_exclude_patterns", side_effect=lambda: list(self.patterns)
        )
        linter = patch(
            "src.linter_engine.parse_diff_and_lint",
            return_value={"errors": [], "warnings": []},
        )

        self.engine = engine.start()
        self.excludes = excludes.start()
        self.linter = linter.start()
        self.addCleanup(patch.stopall)

    def review(self, ai_provider="gemini", **kwargs):
        return review_remote_pr(
            kwargs.pop("pr_number", 42),
            self.provider,
            _repo(),
            ai_provider,
            **kwargs,
        )


class TestHappyPath(RemoteReviewTestCase):
    def test_returns_the_review_and_the_pull_request_url(self):
        result = self.review()

        self.assertEqual(result.review, REVIEW)
        self.assertEqual(result.pr_number, 42)
        self.assertEqual(result.pr_url, "https://github.com/owner/repo/pull/42")

    def test_the_diff_source_names_the_pull_request_and_its_branches(self):
        source = self.review().diff_source

        self.assertEqual(source.origin, DiffOrigin.REMOTE_PR)
        self.assertEqual(source.identifier, "pr-42")
        self.assertEqual(source.pr_number, 42)
        self.assertEqual(source.base_branch, "main")
        self.assertEqual(source.head_branch, "feature/login")
        self.assertTrue(source.is_remote)

    def test_the_forge_is_read_twice_and_never_written_to(self):
        """The default is a read-only review, comment or no comment."""
        self.review()

        self.assertEqual(self.provider.pr_calls, [(_repo(), 42)])
        self.assertEqual(self.provider.diff_calls, [(_repo(), 42)])
        self.assertEqual(self.provider.comments, [])

    def test_nothing_is_posted_unless_asked(self):
        result = self.review(post_comment=False)
        self.assertFalse(result.comment_posted)
        self.assertEqual(self.provider.comments, [])


class TestPipelineParity(RemoteReviewTestCase):
    """The remote flow feeds the local engine — same call, different diff."""

    def test_the_engine_receives_the_fetched_diff_verbatim(self):
        self.review()
        args = self.engine.call_args.args
        self.assertEqual(args, ("review", "review", PATCH, "gemini"))

    def test_the_engine_is_told_to_record_the_diff(self):
        """What `gitpr fix` reads back — a remote diff has no local tree."""
        self.review()
        self.assertTrue(self.engine.call_args.kwargs["store_diff"])

    def test_the_cache_scope_is_the_pull_request_identifier(self):
        """The local flow passes "" here; this is what keeps the two apart."""
        self.review()
        self.assertEqual(self.engine.call_args.kwargs["cache_scope"], "::diff-source::pr-42")

    def test_two_pull_requests_are_scoped_differently(self):
        self.review(pr_number=42)
        first = self.engine.call_args.kwargs["cache_scope"]
        self.review(pr_number=43)
        second = self.engine.call_args.kwargs["cache_scope"]

        self.assertNotEqual(first, second)

    def test_the_linter_runs_without_the_external_bridge(self):
        """The bridge lints files on disk — the local tree, not this PR."""
        self.review()
        self.assertTrue(self.linter.call_args.kwargs["skip_external"])

    def test_the_linter_lints_the_diff_that_was_reviewed(self):
        self.review()
        self.assertEqual(self.linter.call_args.args, (PATCH,))

    def test_crlf_diffs_reach_the_engine_normalized(self):
        self.provider.diff = PATCH.replace("\n", "\r\n")
        self.review()
        self.assertEqual(self.engine.call_args.args[2], PATCH)

    def test_the_ai_provider_reaches_the_engine(self):
        self.review(ai_provider="deepseek")
        self.assertEqual(self.engine.call_args.args[3], "deepseek")


class TestSmartExcludes(RemoteReviewTestCase):
    def test_an_excluded_file_is_filtered_out_of_the_reviewed_diff(self):
        self.provider.diff = PATCH + LOCK
        self.patterns.append("*.lock")

        result = self.review()

        self.assertNotIn("poetry.lock", result.diff_source.content)
        self.assertIn("src/app.py", result.diff_source.content)
        self.assertIn("src/app.py", self.engine.call_args.args[2])

    def test_the_user_is_told_which_files_were_skipped(self):
        self.provider.diff = PATCH + LOCK
        self.patterns.append("*.lock")

        warnings = " ".join(self.review().warnings)

        self.assertIn("poetry.lock", warnings)
        self.assertIn("smart excludes", warnings)

    def test_a_review_with_nothing_left_never_calls_the_ai(self):
        self.provider.diff = LOCK
        self.patterns.append("*.lock")

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("smart excludes", str(caught.exception))
        self.engine.assert_not_called()

    def test_without_patterns_nothing_is_dropped(self):
        self.provider.diff = PATCH + LOCK
        result = self.review()

        self.assertEqual(result.warnings, [])
        self.assertEqual(self.engine.call_args.args[2], PATCH + LOCK)


class TestMapReduceWarning(RemoteReviewTestCase):
    def test_a_large_diff_warns_about_batching(self):
        """The engine splits silently; a review published as a comment needs it said."""
        with patch("src.core.split_diff_into_chunks", return_value=["a", "b", "c"]):
            warnings = " ".join(self.review().warnings)

        self.assertIn("3", warnings)
        self.assertIn("map-reduce", warnings)

    def test_a_small_diff_warns_about_nothing(self):
        with patch("src.core.split_diff_into_chunks", return_value=["a"]):
            self.assertEqual(self.review().warnings, [])

    def test_a_chunker_failure_does_not_break_the_review(self):
        """The warning is a courtesy — it must never be the reason a run dies."""
        with patch("src.core.split_diff_into_chunks", side_effect=ValueError("boom")):
            result = self.review()

        self.assertEqual(result.review, REVIEW)


class TestRejectionsBeforeTheAi(RemoteReviewTestCase):
    """Every rejection here must cost zero tokens."""

    def test_a_forge_without_a_reviewable_diff_is_refused_first(self):
        self.provider.supports_reviewable_diff = False

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("github", str(caught.exception))
        self.engine.assert_not_called()
        # Before the network, not after: the capability is known up front.
        self.assertEqual(self.provider.pr_calls, [])

    def test_a_missing_pull_request_says_so(self):
        self.provider.pr_error = ScmProviderError("github", 404, "Not Found")

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("#42", str(caught.exception))
        self.assertIn("not found", str(caught.exception))
        self.engine.assert_not_called()
        self.assertEqual(self.provider.diff_calls, [])

    def test_a_private_pull_request_names_the_token(self):
        self.provider.pr_error = ScmProviderError("github", 403, "Forbidden")

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        message = str(caught.exception)
        self.assertIn("permission", message)
        self.assertIn("--init", message)
        self.engine.assert_not_called()

    def test_a_closed_pull_request_is_not_reviewed(self):
        self.provider._pr = _pr(state="closed")

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("not open", str(caught.exception))
        self.assertIn("closed", str(caught.exception))
        self.engine.assert_not_called()
        self.assertEqual(self.provider.diff_calls, [])

    def test_a_merged_pull_request_is_not_reviewed(self):
        self.provider._pr = _pr(state="merged")

        with self.assertRaises(ReviewPrError):
            self.review()

        self.engine.assert_not_called()

    def test_a_provider_that_reports_no_state_is_let_through(self):
        """Nothing promised, nothing to enforce — the diff decides."""
        self.provider._pr = _pr(state="")
        self.assertEqual(self.review().review, REVIEW)

    def test_an_empty_diff_is_refused(self):
        self.provider.diff = ""

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("no diff", str(caught.exception))
        self.engine.assert_not_called()

    def test_a_file_summary_wearing_a_diff_name_is_refused(self):
        """The safety net behind the capability flag — Azure aside, any forge."""
        self.provider.diff = "/src/app.py (+12 -3)\n"

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("file summary", str(caught.exception))
        self.engine.assert_not_called()

    def test_a_failing_diff_request_names_the_pull_request(self):
        self.provider.diff_error = ScmProviderError("github", 500, "Server Error")

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("#42", str(caught.exception))
        self.engine.assert_not_called()

    def test_an_empty_ai_answer_is_an_error_not_an_empty_report(self):
        self.engine.return_value = {"review": "   "}

        with self.assertRaises(ReviewPrError) as caught:
            self.review()

        self.assertIn("no review", str(caught.exception))


class TestPostComment(RemoteReviewTestCase):
    def test_the_comment_is_posted_on_the_pull_request(self):
        result = self.review(post_comment=True)

        self.assertTrue(result.comment_posted)
        self.assertEqual(len(self.provider.comments), 1)
        repo, pr_id, _body = self.provider.comments[0]
        self.assertEqual(pr_id, 42)
        self.assertEqual(repo.name, "repo")

    def test_the_comment_carries_the_review(self):
        self.review(post_comment=True)
        self.assertIn(REVIEW, self.provider.comments[0][2])

    def test_the_comment_says_a_model_wrote_it(self):
        """It lands on someone else's PR: the reader must know where it came from."""
        self.review(post_comment=True)
        body = self.provider.comments[0][2]

        self.assertIn("Automated review by GitPR", body)
        self.assertIn("Gemini", body)
        self.assertIn("AI-generated", body)

    def test_the_comment_names_the_provider_that_reviewed(self):
        self.review(ai_provider="deepseek", post_comment=True)
        self.assertIn("Deepseek", self.provider.comments[0][2])

    def test_the_comment_carries_the_linter_alerts(self):
        self.linter.return_value = {"errors": ["line too long"], "warnings": []}

        self.review(post_comment=True)

        body = self.provider.comments[0][2]
        self.assertIn("line too long", body)
        self.assertIn("Local Static Analysis Alerts", body)

    def test_the_comment_is_announced_as_a_warning(self):
        warnings = " ".join(self.review(post_comment=True).warnings)
        self.assertIn("published as a comment", warnings)

    def test_a_failed_review_posts_nothing(self):
        self.provider._pr = _pr(state="closed")

        with self.assertRaises(ReviewPrError):
            self.review(post_comment=True)

        self.assertEqual(self.provider.comments, [])

    def test_a_forge_error_while_posting_propagates(self):
        """The caller learns the review exists but was not published."""
        self.provider.add_comment = lambda *a, **k: (_ for _ in ()).throw(
            ScmProviderError("github", 422, "Unprocessable")
        )

        with self.assertRaises(ScmProviderError):
            self.review(post_comment=True)


class TestBuildCommentBody(unittest.TestCase):
    """The composer on its own — the file and the comment share it."""

    def test_without_alerts_the_body_is_the_review_and_the_footer(self):
        body = build_comment_body(REVIEW, {"errors": [], "warnings": []}, "gemini")

        self.assertTrue(body.startswith(REVIEW))
        self.assertIn("---", body)

    def test_alerts_are_composed_the_way_the_report_composes_them(self):
        """Same function as the .txt, so the two can never read differently."""
        alerts = {"errors": ["E1"], "warnings": ["W1"]}

        body = build_comment_body(REVIEW, alerts, "gemini")

        self.assertIn("- E1", body)
        self.assertIn("- W1", body)

    def test_no_commit_sha_is_claimed(self):
        """PullRequestResult carries none, so any revision marker would be invented."""
        body = build_comment_body(REVIEW, {"errors": [], "warnings": []}, "gemini")
        self.assertNotIn("commit", body)


if __name__ == "__main__":
    unittest.main()
