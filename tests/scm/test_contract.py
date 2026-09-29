"""Contract tests: every ScmProvider implementation must honor the interface.

Each provider case auto-skips until its module exists (stages of the
multi-forge implementation land incrementally). Once a provider module is
importable its whole contract suite runs.
"""

import importlib
import inspect
import unittest

from src.infrastructure.scm.base import (
    IssueRequest,
    IssueResult,
    PullRequestRequest,
    PullRequestResult,
    RepoRef,
    ScmNotSupportedError,
    ScmProvider,
    ScmProviderError,
    within_window,
)


def _abstract_methods(cls):
    """Names of the abstract methods declared by an (abstract) class."""
    return {
        name
        for name, member in inspect.getmembers(cls)
        if getattr(member, "__isabstractmethod__", False)
    }


class ProviderContractCase(unittest.TestCase):
    """Shared contract assertions; concrete cases configure the class data.

    Not collected directly (__test__ = False): only the concrete per-provider
    subclasses below run.
    """

    __test__ = False

    MODULE = None
    CLASS = None
    KEY = None
    MINIMAL_KWARGS = {}
    CANONICAL_URL = None
    REQUIRED_EXTRA = ()  # ((kwarg, env_var), ...) validated fail-fast at init

    @classmethod
    def setUpClass(cls):
        if cls.MODULE is None:
            raise unittest.SkipTest("abstract base case")
        try:
            module = importlib.import_module(cls.MODULE)
        except ImportError:
            raise unittest.SkipTest(f"{cls.MODULE} not implemented yet")
        cls.provider_class = getattr(module, cls.CLASS)

    def _make(self, **overrides):
        kwargs = dict(self.MINIMAL_KWARGS)
        kwargs.update(overrides)
        return self.provider_class(token="test-token", **kwargs)

    def test_is_concrete_provider(self):
        self.assertTrue(issubclass(self.provider_class, ScmProvider))
        self.assertFalse(inspect.isabstract(self.provider_class))
        self.assertEqual(self.provider_class.name, self.KEY)

    def test_all_abstract_methods_overridden(self):
        unimplemented = {
            name
            for name in _abstract_methods(ScmProvider)
            if getattr(self.provider_class, name, None)
            is getattr(ScmProvider, name, None)
        }
        self.assertEqual(unimplemented, set())

    def test_default_base_url(self):
        # default_base_url is an instance method — exercise it through _make()
        # so fail-fast providers (required extras) are configured correctly.
        provider = self._make()
        self.assertIsInstance(provider.default_base_url(), str)
        self.assertTrue(provider.default_base_url())

    def test_minimal_instantiation(self):
        provider = self._make()
        self.assertEqual(provider.token, "test-token")
        self.assertEqual(provider.base_url, provider.default_base_url().rstrip("/"))

    def test_custom_base_url(self):
        provider = self._make(base_url="https://custom.example/api/")
        self.assertEqual(provider.base_url, "https://custom.example/api")

    def test_with_token_roundtrip(self):
        provider = self._make()
        refreshed = provider.with_token("new-token")
        self.assertIs(type(refreshed), type(provider))
        self.assertEqual(refreshed.token, "new-token")
        self.assertEqual(refreshed.base_url, provider.base_url)
        self.assertEqual(refreshed.extra, provider.extra)

    def test_parse_repo_ref(self):
        if not self.CANONICAL_URL:
            self.skipTest("no canonical URL configured")
        repo = self._make().parse_repo_ref(self.CANONICAL_URL)
        self.assertIsInstance(repo, RepoRef)
        self.assertEqual(repo.raw, self.CANONICAL_URL)
        self.assertEqual(repo.provider, self.KEY)
        self.assertTrue(repo.name)
        self.assertTrue(repo.workspace)

    def test_fail_fast_missing_required_extra(self):
        if not self.REQUIRED_EXTRA:
            self.skipTest("no required extra config")
        for kwarg, env_var in self.REQUIRED_EXTRA:
            with self.subTest(kwarg=kwarg, env_var=env_var):
                kwargs = dict(self.MINIMAL_KWARGS)
                kwargs.pop(kwarg, None)
                with self.assertRaises(ScmProviderError) as ctx:
                    self.provider_class(token="test-token", **kwargs)
                self.assertIn(env_var, str(ctx.exception.message))


class TestGithubContract(ProviderContractCase):
    # pytest inherits __test__ = False from the base unless each concrete
    # subclass re-enables collection explicitly.
    __test__ = True

    MODULE = "src.infrastructure.scm.github_provider"
    CLASS = "GitHubProvider"
    KEY = "github"
    MINIMAL_KWARGS = {}
    CANONICAL_URL = "https://github.com/owner/repo.git"


class TestGitlabContract(ProviderContractCase):
    __test__ = True

    MODULE = "src.infrastructure.scm.gitlab_provider"
    CLASS = "GitLabProvider"
    KEY = "gitlab"
    MINIMAL_KWARGS = {}
    CANONICAL_URL = "https://gitlab.com/group/subgroup/project.git"


class TestBitbucketContract(ProviderContractCase):
    __test__ = True

    MODULE = "src.infrastructure.scm.bitbucket_provider"
    CLASS = "BitbucketProvider"
    KEY = "bitbucket"
    MINIMAL_KWARGS = {"username": "user"}
    CANONICAL_URL = "https://bitbucket.org/workspace/repo.git"
    REQUIRED_EXTRA = (("username", "GITPR_SCM_USERNAME"),)


class TestAzureDevopsContract(ProviderContractCase):
    __test__ = True

    MODULE = "src.infrastructure.scm.azure_devops_provider"
    CLASS = "AzureDevOpsProvider"
    KEY = "azure_devops"
    MINIMAL_KWARGS = {"organization": "org", "project": "proj"}
    CANONICAL_URL = "https://dev.azure.com/org/proj/_git/repo"
    REQUIRED_EXTRA = (
        ("organization", "GITPR_SCM_ORGANIZATION"),
        ("project", "GITPR_SCM_PROJECT"),
    )


class TestDomainDataclasses(unittest.TestCase):
    """Guards the contract dataclass shapes (spec section 3)."""

    def test_pull_request_request_fields(self):
        req = PullRequestRequest(
            title="t",
            description="d",
            source_branch="feat/x",
            target_branch="main",
        )
        self.assertFalse(req.draft)
        self.assertEqual(req.labels, [])
        self.assertEqual(req.reviewers, [])

    def test_pull_request_result_fields(self):
        result = PullRequestResult(
            id=12,
            url="https://example.com/pr/12",
            number=12,
            state="open",
            source_branch="feat/x",
            target_branch="main",
            provider="github",
        )
        self.assertEqual(result.provider, "github")

    def test_repo_ref_display(self):
        repo = RepoRef(raw="u", workspace="owner", name="repo", provider="github")
        self.assertEqual(repo.display, "owner/repo")
        bare = RepoRef(raw="u", workspace="", name="repo", provider="github")
        self.assertEqual(bare.display, "repo")

    def test_issue_dataclasses(self):
        req = IssueRequest(title="t", description="d")
        result = IssueResult(id=1, url="https://x/i/1", number=1, provider="gitlab")
        self.assertEqual(req.title, "t")
        self.assertEqual(result.provider, "gitlab")


class _BareProvider(ScmProvider):
    """The smallest provider that satisfies the ABC — nothing else.

    It exists to hold the contract's defaults: what a forge that implements
    only what the ABC demands gets for the methods the ABC does not.
    """

    name = "bare"

    def default_base_url(self):
        return "https://bare.example/api"

    def parse_repo_ref(self, remote_url):
        raise ValueError(remote_url)

    def create_pull_request(self, repo, req):
        raise NotImplementedError

    def get_pull_request_diff(self, repo, pr_id):
        raise NotImplementedError

    def add_comment(self, repo, pr_id, body):
        raise NotImplementedError

    def merge_pull_request(self, repo, pr_id, strategy="merge"):
        raise NotImplementedError

    def test_connection(self):
        return True

    def check_existing_pull_request(self, repo, source_branch):
        return None

    def update_pull_request(self, repo, pr_id, title=None, description=None):
        raise NotImplementedError

    def create_issue(self, repo, req):
        raise NotImplementedError


class _ListingProvider(_BareProvider):
    """A provider whose only speciality is knowing how to list pull requests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.asked = []

    def list_pull_requests(self, repo, state="all", since=None, until=None):
        self.asked.append((state, since, until))
        return []


class TestPullRequestListingContract(unittest.TestCase):
    """The listing's shape: one implementation, one name kept, one honest hole."""

    REPO = RepoRef(raw="u", workspace="w", name="r", provider="bare")

    def test_the_open_listing_is_the_general_one_asked_for_open(self):
        """The old name survives as a wrapper, so every call site and test that
        uses it now walks the paginated implementation underneath."""
        provider = _ListingProvider("token")

        self.assertEqual(provider.list_open_pull_requests(self.REPO), [])
        self.assertEqual(provider.asked, [("open", None, None)])

    def test_a_forge_that_cannot_list_raises_instead_of_returning_nothing(self):
        """An empty list is an answer, and a wrong one for a forge that has no
        way to answer: the caller has to be able to tell "no pull requests"
        from "cannot say"."""
        with self.assertRaises(ScmNotSupportedError) as ctx:
            _BareProvider("token").list_pull_requests(self.REPO)

        self.assertEqual(ctx.exception.provider, "bare")
        # The wrapper goes through the same hole, with the same error.
        with self.assertRaises(ScmNotSupportedError):
            _BareProvider("token").list_open_pull_requests(self.REPO)

    def test_the_result_carries_the_dates_the_contract_promises(self):
        result = PullRequestResult(
            id=1, url="u", number=1, state="open",
            source_branch="a", target_branch="b", provider="bare",
        )

        self.assertEqual(result.created_at, "")
        self.assertEqual(result.merged_at, "")
        self.assertEqual(result.closed_at, "")

    def test_the_window_is_an_inclusive_range_of_calendar_days(self):
        self.assertTrue(within_window("2026-09-01T00:00:00Z", "2026-09-01", "2026-09-30"))
        self.assertTrue(within_window("2026-09-30T23:59:59Z", "2026-09-01", "2026-09-30"))
        self.assertFalse(within_window("2026-08-31T23:59:59Z", "2026-09-01", None))
        self.assertFalse(within_window("2026-10-01T00:00:00Z", None, "2026-09-30"))
        # A date the forge never published cannot be placed in a window, and
        # with no window asked for there is nothing to place it in.
        self.assertFalse(within_window("", "2026-09-01", None))
        self.assertTrue(within_window("", None, None))


class TestErrors(unittest.TestCase):
    def test_scm_provider_error_attributes(self):
        err = ScmProviderError("github", 401, "Bad credentials")
        self.assertEqual(err.provider, "github")
        self.assertEqual(err.http_status, 401)
        self.assertEqual(err.message, "Bad credentials")
        self.assertIn("401", str(err))

    def test_scm_not_supported_error(self):
        err = ScmNotSupportedError("azure_devops", "not supported here")
        self.assertIsInstance(err, ScmProviderError)
        self.assertEqual(err.provider, "azure_devops")
        self.assertEqual(err.http_status, 0)


if __name__ == "__main__":
    unittest.main()
