"""Web URL building for the release notes (SCM formatting helper).

The release flow is the only place GitPR turns a git remote into browser
links, so these tests pin the two halves of that contract: normalizing every
remote shape into an https base, and the per-forge page patterns. The None
answers matter as much as the strings — they are what makes the caller fall
back to plain text instead of writing a broken link.
"""

import unittest

from src.infrastructure.scm.web_links import (
    commit_url,
    pull_request_url,
    repo_web_base,
    user_url,
)


class TestRepoWebBase(unittest.TestCase):
    def test_https_remote_drops_the_git_suffix(self):
        self.assertEqual(
            repo_web_base("https://github.com/natanfiuza/gitpr.git"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_https_remote_without_suffix(self):
        self.assertEqual(
            repo_web_base("https://github.com/natanfiuza/gitpr"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_trailing_slash_is_ignored(self):
        self.assertEqual(
            repo_web_base("https://github.com/natanfiuza/gitpr/"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_scp_like_remote_becomes_https(self):
        self.assertEqual(
            repo_web_base("git@github.com:natanfiuza/gitpr.git"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_ssh_scheme_remote(self):
        self.assertEqual(
            repo_web_base("ssh://git@github.com/natanfiuza/gitpr.git"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_git_scheme_remote(self):
        self.assertEqual(
            repo_web_base("git://github.com/natanfiuza/gitpr.git"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_credentials_are_stripped(self):
        self.assertEqual(
            repo_web_base("https://user:token@github.com/natanfiuza/gitpr.git"),
            "https://github.com/natanfiuza/gitpr",
        )

    def test_nested_gitlab_group_is_preserved(self):
        self.assertEqual(
            repo_web_base("git@gitlab.example.com:group/sub/repo.git"),
            "https://gitlab.example.com/group/sub/repo",
        )

    def test_port_is_preserved(self):
        self.assertEqual(
            repo_web_base("ssh://git@gitlab.example.com:2222/group/repo.git"),
            "https://gitlab.example.com:2222/group/repo",
        )

    def test_azure_devops_remote(self):
        self.assertEqual(
            repo_web_base("https://dev.azure.com/natanfiuza/gitpr/_git/gitpr"),
            "https://dev.azure.com/natanfiuza/gitpr/_git/gitpr",
        )

    def test_empty_and_missing_values(self):
        for value in (None, "", "   "):
            self.assertIsNone(repo_web_base(value))

    def test_unparseable_remote(self):
        self.assertIsNone(repo_web_base("not-a-remote"))
        self.assertIsNone(repo_web_base("https://github.com"))


class TestCommitUrl(unittest.TestCase):
    def test_github(self):
        self.assertEqual(
            commit_url("github", "https://github.com/o/r", "abc1234"),
            "https://github.com/o/r/commit/abc1234",
        )

    def test_gitlab(self):
        self.assertEqual(
            commit_url("gitlab", "https://gitlab.com/o/r", "abc1234"),
            "https://gitlab.com/o/r/-/commit/abc1234",
        )

    def test_bitbucket(self):
        self.assertEqual(
            commit_url("bitbucket", "https://bitbucket.org/o/r", "abc1234"),
            "https://bitbucket.org/o/r/commits/abc1234",
        )

    def test_azure_devops(self):
        self.assertEqual(
            commit_url(
                "azure_devops", "https://dev.azure.com/org/prj/_git/r", "abc1234"
            ),
            "https://dev.azure.com/org/prj/_git/r/commit/abc1234",
        )

    def test_unknown_provider_and_missing_base(self):
        self.assertIsNone(commit_url("gerrit", "https://example.com/o/r", "abc1234"))
        self.assertIsNone(commit_url("github", None, "abc1234"))

    def test_provider_key_is_normalized(self):
        self.assertEqual(
            commit_url(" GitHub ", "https://github.com/o/r", "abc1234"),
            "https://github.com/o/r/commit/abc1234",
        )


class TestPullRequestUrl(unittest.TestCase):
    def test_github(self):
        self.assertEqual(
            pull_request_url("github", "https://github.com/o/r", 190),
            "https://github.com/o/r/pull/190",
        )

    def test_gitlab(self):
        self.assertEqual(
            pull_request_url("gitlab", "https://gitlab.com/o/r", 190),
            "https://gitlab.com/o/r/-/merge_requests/190",
        )

    def test_bitbucket(self):
        self.assertEqual(
            pull_request_url("bitbucket", "https://bitbucket.org/o/r", 190),
            "https://bitbucket.org/o/r/pull-requests/190",
        )

    def test_azure_devops(self):
        self.assertEqual(
            pull_request_url("azure_devops", "https://dev.azure.com/org/prj/_git/r", 190),
            "https://dev.azure.com/org/prj/_git/r/pullrequest/190",
        )

    def test_unknown_provider(self):
        self.assertIsNone(pull_request_url("gerrit", "https://example.com/o/r", 190))


class TestUserUrl(unittest.TestCase):
    def test_profile_is_the_host_plus_the_login(self):
        self.assertEqual(
            user_url("github", "https://github.com/o/r", "natanfiuza"),
            "https://github.com/natanfiuza",
        )
        self.assertEqual(
            user_url("gitlab", "https://gitlab.com/group/sub/repo", "natanfiuza"),
            "https://gitlab.com/natanfiuza",
        )
        self.assertEqual(
            user_url("bitbucket", "https://bitbucket.org/o/r", "natanfiuza"),
            "https://bitbucket.org/natanfiuza",
        )

    def test_azure_devops_has_no_profile_page(self):
        self.assertIsNone(
            user_url("azure_devops", "https://dev.azure.com/org/prj/_git/r", "someone")
        )

    def test_unknown_provider_and_missing_base(self):
        self.assertIsNone(user_url("gerrit", "https://example.com/o/r", "someone"))
        self.assertIsNone(user_url("github", None, "someone"))


if __name__ == "__main__":
    unittest.main()
