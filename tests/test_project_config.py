"""Unit tests for the project-local configuration (src/project_config.py).

The file is a second configuration store, deliberately separate from
~/.gitpr/.env: it is versioned with the repository, written as YAML and read
from the repository root. The tests build real git repositories in temporary
directories — path resolution, the seed's ignore check and the remote
verification all shell out to git, so a mock would assert the mock.
"""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from src.project_config import (
    BASE_BRANCH_FIELD,
    DEFAULT_BASE_BRANCH,
    HEADER_COMMENT,
    PROJECT_CONFIG_RELATIVE_PATH,
    SOURCE_AUTO,
    SOURCE_CLI,
    SOURCE_ENV,
    SOURCE_PROJECT,
    BaseBranchError,
    CurrentBranchError,
    current_branch,
    ensure_project_config,
    list_branches,
    load_project_field_values,
    project_config_path,
    read_project_config,
    resolve_pull_request_base,
    verify_remote_base,
    write_project_field_values,
)


def git(*args, cwd):
    return subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def init_repo(path):
    git("init", "-q", cwd=path)
    # Pin the checked-out branch: git init picks main or master depending on
    # the machine, and the self-target rule below turns that default into a
    # test failure on whichever of the two a test also uses as the remote base.
    git("symbolic-ref", "HEAD", "refs/heads/work", cwd=path)
    git(
        "-c",
        "user.name=GitPR Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "--allow-empty",
        "-m",
        "init",
        "-q",
        cwd=path,
    )


class TempDirTestCase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.root = Path(self._tmpdir.name)

        # The global default is read from the environment and, failing that,
        # from ~/.gitpr/.env. Both are pinned here so the assertions below
        # describe this machine's file rather than the developer's.
        env_patcher = patch.dict(os.environ)
        env_patcher.start()
        self.addCleanup(env_patcher.stop)
        os.environ.pop("PR_DEFAULT_BASE", None)

        env_file_patcher = patch(
            "src.config.ENV_FILE", str(self.root / "gitpr.env")
        )
        env_file_patcher.start()
        self.addCleanup(env_file_patcher.stop)

    def repo(self, name="repo"):
        path = self.root / name
        path.mkdir()
        init_repo(path)
        return path

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class TestProjectConfigPath(TempDirTestCase):
    def test_resolves_to_the_repository_root_from_a_subdirectory(self):
        repo = self.repo()
        nested = repo / "src" / "deep"
        nested.mkdir(parents=True)

        self.assertEqual(
            project_config_path(start_dir=nested),
            repo / PROJECT_CONFIG_RELATIVE_PATH,
        )

    def test_falls_back_to_the_starting_directory_outside_a_repository(self):
        plain = self.root / "plain"
        plain.mkdir()

        self.assertEqual(
            project_config_path(start_dir=plain), plain / PROJECT_CONFIG_RELATIVE_PATH
        )


class TestEnsureProjectConfig(TempDirTestCase):
    def test_creates_the_file_with_the_header_and_main(self):
        repo = self.repo()

        result = ensure_project_config(start_dir=repo)

        self.assertTrue(result.created)
        self.assertFalse(result.ignored)
        text = result.path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(HEADER_COMMENT))
        self.assertEqual(
            yaml.safe_load(text),
            {"pull_request": {"base_branch": DEFAULT_BASE_BRANCH}},
        )

    def test_seeds_the_global_default_when_one_is_configured(self):
        repo = self.repo()

        with patch.dict(os.environ, {"PR_DEFAULT_BASE": "release"}):
            result = ensure_project_config(start_dir=repo)

        self.assertEqual(
            yaml.safe_load(result.path.read_text(encoding="utf-8")),
            {"pull_request": {"base_branch": "release"}},
        )

    def test_seeds_the_global_default_saved_in_the_configuration_file(self):
        repo = self.repo()
        env_file = self.write(self.root / "gitpr.env", "PR_DEFAULT_BASE=release\n")

        with patch("src.config.ENV_FILE", str(env_file)):
            result = ensure_project_config(start_dir=repo)

        self.assertEqual(
            yaml.safe_load(result.path.read_text(encoding="utf-8")),
            {"pull_request": {"base_branch": "release"}},
        )

    def test_never_overwrites_an_existing_file(self):
        repo = self.repo()
        path = repo / PROJECT_CONFIG_RELATIVE_PATH
        self.write(path, "pull_request:\n  base_branch: develop\n")

        result = ensure_project_config(start_dir=repo)

        self.assertFalse(result.created)
        self.assertIn("base_branch: develop", path.read_text(encoding="utf-8"))

    def test_reports_a_file_the_gitignore_keeps_out_of_the_repository(self):
        repo = self.repo()
        self.write(repo / ".gitignore", ".gitpr/\n")

        result = ensure_project_config(start_dir=repo)

        self.assertTrue(result.created)
        self.assertTrue(result.ignored)

    def test_is_a_no_op_outside_a_repository(self):
        plain = self.root / "plain"
        plain.mkdir()

        result = ensure_project_config(start_dir=plain)

        self.assertFalse(result.created)
        self.assertFalse(result.path.exists())


class TestListBranches(TempDirTestCase):
    def test_lists_local_branches_and_the_ones_on_origin(self):
        repo = self.repo()
        git("branch", "feature", cwd=repo)
        git("update-ref", "refs/remotes/origin/develop", "HEAD", cwd=repo)

        branches = list_branches(start_dir=repo)

        self.assertIn("feature", branches)
        self.assertIn("develop", branches)
        self.assertNotIn("origin/develop", branches)

    def test_a_branch_on_both_sides_is_listed_once(self):
        repo = self.repo()
        git("branch", "develop", cwd=repo)
        git("update-ref", "refs/remotes/origin/develop", "HEAD", cwd=repo)

        self.assertEqual(list_branches(start_dir=repo).count("develop"), 1)

    def test_origin_head_is_not_offered_as_a_branch(self):
        repo = self.repo()
        git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=repo)
        git(
            "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main",
            cwd=repo,
        )

        branches = list_branches(start_dir=repo)

        self.assertNotIn("HEAD", branches)
        self.assertNotIn("origin/HEAD", branches)

    def test_outside_a_repository_the_list_is_empty(self):
        plain = self.root / "plain"
        plain.mkdir()

        self.assertEqual(list_branches(start_dir=plain), [])


class TestCurrentBranch(TempDirTestCase):
    def test_reports_the_checked_out_branch(self):
        self.assertEqual(current_branch(start_dir=self.repo()), "work")

    def test_a_detached_head_has_no_branch(self):
        repo = self.repo()
        git("checkout", "--detach", "-q", cwd=repo)

        self.assertEqual(current_branch(start_dir=repo), "")

    def test_outside_a_repository_there_is_no_branch(self):
        plain = self.root / "plain"
        plain.mkdir()

        self.assertEqual(current_branch(start_dir=plain), "")


class TestReadProjectConfig(TempDirTestCase):
    def test_missing_file_reads_as_empty(self):
        config = read_project_config(path=self.root / "absent.yml")

        self.assertEqual(config.base_branch, "")
        self.assertEqual(config.error, "")

    def test_valid_file_reads_the_branch(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "pull_request:\n  base_branch: develop\n",
        )

        config = read_project_config(path=path)

        self.assertEqual(config.base_branch, "develop")
        self.assertEqual(config.error, "")

    def test_malformed_yaml_is_reported_not_raised(self):
        path = self.write(self.root / "gitpr.config.yml", "pull_request: [\n")

        config = read_project_config(path=path)

        self.assertEqual(config.base_branch, "")
        self.assertNotEqual(config.error, "")

    def test_a_file_that_is_not_a_mapping_is_reported(self):
        path = self.write(self.root / "gitpr.config.yml", "- a\n- b\n")

        config = read_project_config(path=path)

        self.assertIn("YAML mapping", config.error)

    def test_pull_request_must_be_a_mapping(self):
        path = self.write(
            self.root / "gitpr.config.yml", "pull_request: develop\n"
        )

        config = read_project_config(path=path)

        self.assertIn("pull_request", config.error)

    def test_base_branch_must_be_text(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "pull_request:\n  base_branch: 42\n",
        )

        config = read_project_config(path=path)

        self.assertIn("base_branch", config.error)

    def test_field_values_are_empty_when_the_file_cannot_be_read(self):
        path = self.write(self.root / "gitpr.config.yml", "- a\n")

        self.assertEqual(load_project_field_values(path=path), {})

    def test_field_values_expose_the_branch(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "pull_request:\n  base_branch: develop\n",
        )

        self.assertEqual(
            load_project_field_values(path=path), {BASE_BRANCH_FIELD: "develop"}
        )


class TestWriteProjectFieldValues(TempDirTestCase):
    def test_writes_the_branch_and_keeps_the_header(self):
        path = self.root / ".gitpr" / "conf" / "gitpr.config.yml"

        write_project_field_values({BASE_BRANCH_FIELD: "develop"}, path=path)

        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(HEADER_COMMENT))
        self.assertEqual(
            yaml.safe_load(text), {"pull_request": {"base_branch": "develop"}}
        )

    def test_preserves_every_other_key_in_the_file(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "other: 1\npull_request:\n  base_branch: main\n  draft: true\n",
        )

        write_project_field_values({BASE_BRANCH_FIELD: "develop"}, path=path)

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(data["other"], 1)
        self.assertEqual(data["pull_request"]["base_branch"], "develop")
        self.assertTrue(data["pull_request"]["draft"])

    def test_an_empty_value_removes_the_key(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "pull_request:\n  base_branch: develop\n",
        )

        write_project_field_values({BASE_BRANCH_FIELD: ""}, path=path)

        self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8")), {})

    def test_a_removal_drops_the_key(self):
        path = self.write(
            self.root / "gitpr.config.yml",
            "pull_request:\n  base_branch: develop\n",
        )

        write_project_field_values({}, removals=[BASE_BRANCH_FIELD], path=path)

        self.assertEqual(yaml.safe_load(path.read_text(encoding="utf-8")), {})

    def test_refuses_to_overwrite_yaml_that_is_not_a_mapping(self):
        path = self.write(self.root / "gitpr.config.yml", "- a\n")
        before = path.read_text(encoding="utf-8")

        with self.assertRaises(ValueError):
            write_project_field_values({BASE_BRANCH_FIELD: "develop"}, path=path)

        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_refuses_to_overwrite_a_pull_request_that_is_not_a_mapping(self):
        path = self.write(
            self.root / "gitpr.config.yml", "pull_request: develop\n"
        )
        before = path.read_text(encoding="utf-8")

        with self.assertRaises(ValueError):
            write_project_field_values({BASE_BRANCH_FIELD: "develop"}, path=path)

        self.assertEqual(path.read_text(encoding="utf-8"), before)


class TestResolvePullRequestBase(TempDirTestCase):
    def setUp(self):
        super().setUp()
        self.path = self.root / "gitpr.config.yml"

    def test_the_cli_flag_wins_over_every_other_source(self):
        self.write(self.path, "pull_request:\n  base_branch: develop\n")

        with patch.dict(os.environ, {"PR_DEFAULT_BASE": "release"}):
            resolved = resolve_pull_request_base(
                "hotfix", config_path=self.path, verify=False
            )

        self.assertEqual(resolved.branch, "hotfix")
        self.assertEqual(resolved.source, SOURCE_CLI)

    def test_the_project_file_wins_over_the_global_default(self):
        self.write(self.path, "pull_request:\n  base_branch: develop\n")

        with patch.dict(os.environ, {"PR_DEFAULT_BASE": "release"}):
            resolved = resolve_pull_request_base(config_path=self.path, verify=False)

        self.assertEqual(resolved.branch, "develop")
        self.assertEqual(resolved.source, SOURCE_PROJECT)

    def test_the_global_default_is_used_when_the_project_has_no_value(self):
        with patch.dict(os.environ, {"PR_DEFAULT_BASE": "release"}):
            resolved = resolve_pull_request_base(config_path=self.path, verify=False)

        self.assertEqual(resolved.branch, "release")
        self.assertEqual(resolved.source, SOURCE_ENV)

    def test_the_global_default_is_read_from_the_configuration_file(self):
        env_file = self.write(self.root / "gitpr.env", "PR_DEFAULT_BASE=release\n")

        with patch("src.config.ENV_FILE", str(env_file)):
            resolved = resolve_pull_request_base(config_path=self.path, verify=False)

        self.assertEqual(resolved.branch, "release")
        self.assertEqual(resolved.source, SOURCE_ENV)

    def test_an_explicitly_empty_variable_does_not_fall_back_to_the_file(self):
        env_file = self.write(self.root / "gitpr.env", "PR_DEFAULT_BASE=release\n")

        with patch.dict(os.environ, {"PR_DEFAULT_BASE": ""}):
            with patch("src.config.ENV_FILE", str(env_file)):
                with patch("src.core.get_base_branch", return_value="trunk"):
                    resolved = resolve_pull_request_base(
                        config_path=self.path, verify=False
                    )

        self.assertEqual(resolved.branch, "trunk")
        self.assertEqual(resolved.source, SOURCE_AUTO)

    def test_detection_is_the_last_resort(self):
        with patch.dict(os.environ, {"PR_DEFAULT_BASE": ""}):
            with patch("src.core.get_base_branch", return_value="trunk"):
                resolved = resolve_pull_request_base(
                    config_path=self.path, verify=False
                )

        self.assertEqual(resolved.branch, "trunk")
        self.assertEqual(resolved.source, SOURCE_AUTO)

    def test_a_project_value_equal_to_the_checked_out_branch_is_refused(self):
        repo = self.repo()
        config = repo / ".gitpr" / "conf" / "gitpr.config.yml"
        self.write(config, "pull_request:\n  base_branch: work\n")
        # Even a branch that does exist on origin cannot be the target of a
        # request opened from itself.
        git("update-ref", "refs/remotes/origin/work", "HEAD", cwd=repo)

        with self.assertRaises(CurrentBranchError):
            resolve_pull_request_base(config_path=config, start_dir=repo)

    def test_a_broken_project_file_warns_and_falls_through(self):
        self.write(self.path, "- a\n")

        with patch.dict(os.environ, {"PR_DEFAULT_BASE": "release"}):
            resolved = resolve_pull_request_base(config_path=self.path, verify=False)

        self.assertEqual(resolved.branch, "release")
        self.assertEqual(len(resolved.warnings), 1)
        self.assertIn(str(self.path), resolved.warnings[0])


class TestVerifyRemoteBase(TempDirTestCase):
    def test_accepts_a_branch_that_exists_on_origin(self):
        repo = self.repo()
        git("update-ref", "refs/remotes/origin/main", "HEAD", cwd=repo)

        verify_remote_base("main", start_dir=repo)  # must not raise

    def test_rejects_the_branch_checked_out(self):
        repo = self.repo()
        git("update-ref", "refs/remotes/origin/work", "HEAD", cwd=repo)

        with self.assertRaises(CurrentBranchError) as raised:
            verify_remote_base("work", start_dir=repo)

        # Caught as BaseBranchError by the CLI, refused with its own type.
        self.assertIsInstance(raised.exception, BaseBranchError)
        self.assertIn("cannot target itself", str(raised.exception))

    def test_rejects_a_branch_missing_on_origin_with_a_fetch_hint(self):
        repo = self.repo()
        git("remote", "add", "origin", "https://example.invalid/repo.git", cwd=repo)

        with self.assertRaises(BaseBranchError) as raised:
            verify_remote_base("develop", start_dir=repo)

        self.assertIn("git fetch origin develop", str(raised.exception))

    def test_reports_a_repository_without_an_origin_remote(self):
        repo = self.repo()

        with self.assertRaises(BaseBranchError) as raised:
            verify_remote_base("develop", start_dir=repo)

        self.assertIn("origin", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
