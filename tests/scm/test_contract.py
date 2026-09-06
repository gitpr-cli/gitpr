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
