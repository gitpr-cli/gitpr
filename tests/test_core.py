import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch, MagicMock
from src.core import (
    get_current_branch, get_git_diff,
    get_unstaged_files, get_unstaged_categorized,
    get_unstaged_diff, get_uncommitted_summary,
    is_merge_in_progress, stage_files,
    append_coauthor_trailer, COAUTHOR_TRAILER,
    get_origin_remote_url, describe_repo,
)
from src.infrastructure.scm import RepoRef
from src.updater import __scripts_version__
from src import core
from src import i18n

class TestCore(unittest.TestCase):

    @patch('src.core.subprocess.run')
    def test_get_current_branch_success(self, mock_subprocess):
        """Testa se a função retorna corretamente o nome da branch simulada."""
        # Configura o mock para "fingir" o retorno do terminal
        mock_process = MagicMock()
        mock_process.stdout = "feature/nova-tela\n"
        mock_subprocess.return_value = mock_process

        branch = get_current_branch()
        self.assertEqual(branch, "feature/nova-tela")

    @patch('src.core.subprocess.run')
    def test_get_git_diff_success(self, mock_subprocess):
        """Testa se o diff é capturado corretamente."""
        mock_process = MagicMock()
        mock_process.stdout = "+ print('Hello World da IA')"
        mock_subprocess.return_value = mock_process

        diff = get_git_diff()
        self.assertEqual(diff, "+ print('Hello World da IA')")


class TestUnstagedFiles(unittest.TestCase):
    """Tests for get_unstaged_files() and get_unstaged_categorized()."""

    @patch('src.core.subprocess.run')
    def test_normalizes_simple_codes(self, mock_run):
        """Simple porcelain codes map to canonical labels."""
        mock_process = MagicMock()
        mock_process.stdout = (
            "?? newfile.py\n"
            " M modified.py\n"
            " D deleted.py\n"
        )
        mock_run.return_value = mock_process

        result = get_unstaged_files()
        self.assertEqual(result, [
            ("newfile.py", "new"),
            ("modified.py", "mod"),
            ("deleted.py", "del"),
        ])

    @patch('src.core.subprocess.run')
    def test_normalizes_combined_codes(self, mock_run):
        """Combined porcelain codes (AM, MM, MD, AD) are normalized."""
        mock_process = MagicMock()
        mock_process.stdout = (
            "AM staged_add_unstaged_mod.py\n"
            "MM staged_mod_unstaged_mod.py\n"
            "MD staged_mod_unstaged_del.py\n"
            "AD staged_add_unstaged_del.py\n"
        )
        mock_run.return_value = mock_process

        result = get_unstaged_files()
        self.assertEqual(result, [
            ("staged_add_unstaged_mod.py", "mod"),
            ("staged_mod_unstaged_mod.py", "mod"),
            ("staged_mod_unstaged_del.py", "del"),
            ("staged_add_unstaged_del.py", "del"),
        ])

    @patch('src.core.subprocess.run')
    def test_excludes_staged_only(self, mock_run):
        """Staged-only changes (clean working tree) are NOT returned."""
        mock_process = MagicMock()
        mock_process.stdout = (
            "M  staged_modified.py\n"
            "A  staged_added.py\n"
            "D  staged_deleted.py\n"
        )
        mock_run.return_value = mock_process

        result = get_unstaged_files()
        self.assertEqual(result, [])

    @patch('src.core.subprocess.run')
    def test_excludes_merge_conflicts(self, mock_run):
        """Merge conflicts (UU) are NOT returned as unstaged."""
        mock_process = MagicMock()
        mock_process.stdout = "UU conflicted.py\n"
        mock_run.return_value = mock_process

        result = get_unstaged_files()
        self.assertEqual(result, [])

    @patch('src.core.subprocess.run')
    def test_handles_empty_output(self, mock_run):
        """Empty porcelain output returns empty list."""
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        result = get_unstaged_files()
        self.assertEqual(result, [])

    @patch('src.core.subprocess.run')
    def test_handles_git_error(self, mock_run):
        """Returns empty list when git fails."""
        mock_run.side_effect = Exception("git not found")
        result = get_unstaged_files()
        self.assertEqual(result, [])


class TestUnstagedCategorized(unittest.TestCase):
    """Tests for get_unstaged_categorized()."""

    @patch('src.core.get_unstaged_files')
    def test_groups_by_category(self, mock_unstaged):
        """Files are grouped into new/modified/deleted lists."""
        mock_unstaged.return_value = [
            ("new1.py", "new"),
            ("mod1.py", "mod"),
            ("mod2.py", "mod"),
            ("del1.py", "del"),
        ]
        result = get_unstaged_categorized()
        self.assertEqual(result["new"], ["new1.py"])
        self.assertEqual(result["modified"], ["mod1.py", "mod2.py"])
        self.assertEqual(result["deleted"], ["del1.py"])

    @patch('src.core.get_unstaged_files')
    def test_all_empty(self, mock_unstaged):
        """Returns empty lists when nothing is unstaged."""
        mock_unstaged.return_value = []
        result = get_unstaged_categorized()
        self.assertEqual(result, {"new": [], "modified": [], "deleted": []})

    @patch('src.core.get_unstaged_files')
    def test_handles_unknown_label(self, mock_unstaged):
        """Unknown labels fall into 'deleted' bucket (safety net)."""
        mock_unstaged.return_value = [
            ("weird.py", "unknown_label"),
        ]
        result = get_unstaged_categorized()
        self.assertIn("weird.py", result["deleted"])


class TestUnstagedDiff(unittest.TestCase):
    """Tests for get_unstaged_diff()."""

    @patch('src.core.subprocess.run')
    def test_uses_no_head_revision(self, mock_run):
        """git diff is called WITHOUT HEAD (index vs working tree)."""
        mock_process = MagicMock()
        mock_process.stdout = "+unstaged change"
        mock_run.return_value = mock_process

        get_unstaged_diff()

        # Extract the command list from the mock call
        call_args = mock_run.call_args[0][0]
        self.assertNotIn("HEAD", call_args)
        self.assertIn("diff", call_args)
        self.assertIn("-U1", call_args)

    @patch('src.core.subprocess.run')
    def test_returns_diff_stdout(self, mock_run):
        """Returns the stdout from the git diff command."""
        mock_process = MagicMock()
        mock_process.stdout = "diff --git a/x.py b/x.py\n+line"
        mock_run.return_value = mock_process

        result = get_unstaged_diff()
        self.assertIn("diff --git a/x.py", result)

    @patch('src.core.subprocess.run')
    def test_returns_none_on_error(self, mock_run):
        """Returns None when the git command fails, no exception propagated."""
        mock_run.side_effect = __import__("subprocess").CalledProcessError(1, "git")
        result = get_unstaged_diff(quiet=True)
        self.assertIsNone(result)


class TestUncommittedSummary(unittest.TestCase):
    """Tests for get_uncommitted_summary()."""

    @patch('src.core.subprocess.run')
    def test_staged_only(self, mock_run):
        """Files staged but with clean working tree appear only in staged."""
        mock_process = MagicMock()
        mock_process.stdout = "M  staged.py\n"
        mock_run.return_value = mock_process

        result = get_uncommitted_summary()
        self.assertIn("staged.py", result["staged"])
        self.assertEqual(result["unstaged"], [])
        self.assertEqual(result["untracked"], [])

    @patch('src.core.subprocess.run')
    def test_untracked_only(self, mock_run):
        """Untracked files appear only in untracked."""
        mock_process = MagicMock()
        mock_process.stdout = "?? new.py\n"
        mock_run.return_value = mock_process

        result = get_uncommitted_summary()
        self.assertIn("new.py", result["untracked"])
        self.assertEqual(result["staged"], [])
        self.assertEqual(result["unstaged"], [])

    @patch('src.core.subprocess.run')
    def test_both_staged_and_unstaged(self, mock_run):
        """A file with staged + unstaged changes appears in both lists."""
        mock_process = MagicMock()
        mock_process.stdout = "MM dual.py\n"
        mock_run.return_value = mock_process

        result = get_uncommitted_summary()
        self.assertIn("dual.py", result["staged"])
        self.assertIn("dual.py", result["unstaged"])

    @patch('src.core.subprocess.run')
    def test_mixed_scenario(self, mock_run):
        """Full scenario with staged, unstaged, and untracked files."""
        mock_process = MagicMock()
        mock_process.stdout = (
            "M  staged_mod.py\n"
            "A  staged_add.py\n"
            " D unstaged_del.py\n"
            "?? new_file.py\n"
            "AM staged_new_unstaged_edit.py\n"
        )
        mock_run.return_value = mock_process

        result = get_uncommitted_summary()
        self.assertIn("staged_mod.py", result["staged"])
        self.assertIn("staged_add.py", result["staged"])
        self.assertIn("staged_new_unstaged_edit.py", result["staged"])
        self.assertIn("unstaged_del.py", result["unstaged"])
        self.assertIn("staged_new_unstaged_edit.py", result["unstaged"])
        self.assertIn("new_file.py", result["untracked"])

    @patch('src.core.subprocess.run')
    def test_handles_git_error(self, mock_run):
        """Returns empty dict structure when git fails."""
        mock_run.side_effect = Exception("git not found")
        result = get_uncommitted_summary()
        self.assertEqual(result, {"staged": [], "unstaged": [], "untracked": []})


class TestIsMergeInProgress(unittest.TestCase):
    """Tests for is_merge_in_progress() (MERGE_HEAD detection)."""

    @patch('src.core.subprocess.run')
    def test_true_when_merge_in_progress(self, mock_run):
        """MERGE_HEAD exists (rev-parse exits 0) -> merge in progress."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        self.assertTrue(is_merge_in_progress())
        mock_run.assert_called_once()
        self.assertEqual(mock_run.call_args[0][0],
                         ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"])

    @patch('src.core.subprocess.run')
    def test_false_when_no_merge(self, mock_run):
        """rev-parse exits 1 -> no merge in progress."""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process

        self.assertFalse(is_merge_in_progress())

    @patch('src.core.subprocess.run')
    def test_false_on_git_error(self, mock_run):
        """git unavailable -> never block the commit."""
        mock_run.side_effect = Exception("git not found")
        self.assertFalse(is_merge_in_progress())


class TestStageFiles(unittest.TestCase):
    """Tests for stage_files() (git add wrapper)."""

    def test_empty_list_is_success(self):
        """No files to stage -> success without touching git."""
        ok, err = stage_files([])
        self.assertTrue(ok)
        self.assertEqual(err, "")

    @patch('src.core.subprocess.run')
    def test_success_on_zero_returncode(self, mock_run):
        """git add exits 0 -> (True, '')."""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        ok, err = stage_files(["docs/foo.md"])
        self.assertTrue(ok)
        self.assertEqual(err, "")
        self.assertEqual(mock_run.call_args[0][0], ["git", "add", "docs/foo.md"])

    @patch('src.core.subprocess.run')
    def test_failure_returns_git_error(self, mock_run):
        """git add fails -> (False, error message from git)."""
        mock_process = MagicMock()
        mock_process.returncode = 128
        mock_process.stderr = "fatal: pathspec 'x.md' did not match any files\n"
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        ok, err = stage_files(["x.md"])
        self.assertFalse(ok)
        self.assertIn("pathspec", err)

    @patch('src.core.subprocess.run')
    def test_failure_on_exception(self, mock_run):
        """git unavailable -> (False, exception message)."""
        mock_run.side_effect = Exception("git not found")
        ok, err = stage_files(["x.md"])
        self.assertFalse(ok)
        self.assertEqual(err, "git not found")


class TestCoauthorTrailer(unittest.TestCase):
    """Tests for append_coauthor_trailer()."""

    @patch.dict('os.environ', {'GITPR_COAUTHOR': 'true'})
    def test_appends_trailer_with_blank_lines(self):
        """Trailer is appended separated from the message body."""
        result = append_coauthor_trailer("feat: add hello world")
        self.assertEqual(result, f"feat: add hello world\n\n\n{COAUTHOR_TRAILER}")

    @patch.dict('os.environ', {'GITPR_COAUTHOR': 'true'})
    def test_does_not_duplicate_existing_trailer(self):
        """Already-signed messages are returned unchanged."""
        signed = f"feat: add hello world\n\n\n{COAUTHOR_TRAILER}"
        self.assertEqual(append_coauthor_trailer(signed), signed)

    @patch.dict('os.environ', {'GITPR_COAUTHOR': 'true'})
    def test_empty_message_returns_trailer_alone(self):
        """None/empty messages become just the trailer (no leading blank lines)."""
        self.assertEqual(append_coauthor_trailer(""), COAUTHOR_TRAILER)
        self.assertEqual(append_coauthor_trailer(None), COAUTHOR_TRAILER)

    @patch.dict('os.environ', {'GITPR_COAUTHOR': 'false'})
    def test_respects_disable_env(self):
        """GITPR_COAUTHOR=false keeps the message untouched."""
        self.assertEqual(append_coauthor_trailer("fix: bug"), "fix: bug")

    @patch.dict('os.environ', {'GITPR_COAUTHOR': 'true'})
    def test_preserves_third_party_trailer(self):
        """A human co-author trailer is kept and the gitpr one is added."""
        result = append_coauthor_trailer(
            "fix: bug\n\nCo-Authored-By: Human <human@example.com>"
        )
        self.assertIn("Co-Authored-By: Human <human@example.com>", result)
        self.assertTrue(result.endswith(COAUTHOR_TRAILER))


class TestScmContextHelpers(unittest.TestCase):
    """Tests for get_origin_remote_url() and describe_repo()."""

    @patch('src.core.subprocess.run')
    def test_get_origin_remote_url_success(self, mock_run):
        """Verbatim origin remote URL, trailing newline stripped."""
        mock_process = MagicMock()
        mock_process.stdout = "https://github.com/owner/repo.git\n"
        mock_run.return_value = mock_process

        self.assertEqual(
            get_origin_remote_url(), "https://github.com/owner/repo.git"
        )

    @patch('src.core.subprocess.run')
    def test_get_origin_remote_url_strips_whitespace(self, mock_run):
        """Surrounding whitespace/newlines are trimmed."""
        mock_process = MagicMock()
        mock_process.stdout = "  git@gitlab.com:group/sub/proj.git  \n"
        mock_run.return_value = mock_process

        self.assertEqual(
            get_origin_remote_url(), "git@gitlab.com:group/sub/proj.git"
        )

    @patch('src.core.subprocess.run')
    def test_get_origin_remote_url_empty_output(self, mock_run):
        """No origin remote configured -> None."""
        mock_process = MagicMock()
        mock_process.stdout = ""
        mock_run.return_value = mock_process

        self.assertIsNone(get_origin_remote_url())

    @patch('src.core.subprocess.run')
    def test_get_origin_remote_url_git_error(self, mock_run):
        """git failing (not a repository) -> None, never raises."""
        mock_run.side_effect = __import__("subprocess").CalledProcessError(1, "git")
        self.assertIsNone(get_origin_remote_url())

    @patch('src.core.subprocess.run')
    def test_get_origin_remote_url_file_not_found(self, mock_run):
        """git binary missing -> None."""
        mock_run.side_effect = FileNotFoundError("git")
        self.assertIsNone(get_origin_remote_url())

    def test_describe_repo_workspace_name(self):
        """owner/repo display for GitHub-style refs."""
        repo_ref = RepoRef(
            raw="https://github.com/owner/repo.git",
            workspace="owner",
            name="repo",
            provider="github",
        )
        self.assertEqual(describe_repo(repo_ref), "owner/repo")

    def test_describe_repo_subgroup_namespace(self):
        """Full nested namespace display for GitLab sub-groups."""
        repo_ref = RepoRef(
            raw="git@gitlab.com:group/subgroup/proj.git",
            workspace="group/subgroup",
            name="proj",
            provider="gitlab",
        )
        self.assertEqual(describe_repo(repo_ref), "group/subgroup/proj")

    def test_describe_repo_azure_org_project(self):
        """Azure DevOps display-only workspace combines org/project."""
        repo_ref = RepoRef(
            raw="https://dev.azure.com/org/project/_git/repo",
            workspace="org/project",
            name="repo",
            provider="azure_devops",
        )
        self.assertEqual(describe_repo(repo_ref), "org/project/repo")


class _FakeHookResponse:
    """Minimal urlopen() result: read() plus the context manager protocol."""

    def read(self):
        return b"#!/bin/sh\necho hook\n"

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestHooksLanguage(unittest.TestCase):
    """SCRIPTS_LANG is the language the user asked for.

    SCRIPTS_INSTALLED_LANG is the language that ended up on disk. Keeping them
    apart is what lets the auto-sync notice a language change: comparing the
    request against itself never could.
    """

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        os.makedirs(os.path.join(self._tmpdir.name, ".git", "hooks"), exist_ok=True)
        previous_cwd = os.getcwd()
        os.chdir(self._tmpdir.name)
        self.addCleanup(os.chdir, previous_cwd)

    def install(self, env, current_lang="pt_br"):
        """Runs the installer against a fake .env and captures what it fetched."""
        urls, stamps = [], []

        def fake_urlopen(url, *args, **kwargs):
            urls.append(url)
            return _FakeHookResponse()

        with patch("src.core.read_env_file_values", return_value=env), patch(
            "src.i18n.CURRENT_LANG", current_lang
        ), patch("src.core.urllib.request.urlopen", side_effect=fake_urlopen), patch(
            "src.core.set_key",
            side_effect=lambda path, key, value: stamps.append((key, value)),
        ), redirect_stdout(
            io.StringIO()
        ):
            from src.core import install_git_hooks

            installed = install_git_hooks()
        return installed, urls, stamps

    def gate(self, env_version, installed_lang, wanted_lang, current_lang="pt_br"):
        """Runs the auto-sync gate; the returned list is one entry per install."""
        installs = []
        environ = {
            "SCRIPTS_VERSION": env_version,
            "SCRIPTS_INSTALLED_LANG": installed_lang,
        }
        with patch(
            "src.core.read_env_file_values", return_value={"SCRIPTS_LANG": wanted_lang}
        ), patch("src.i18n.CURRENT_LANG", current_lang), patch.dict(
            os.environ, environ
        ), patch(
            "src.core.load_dotenv"
        ), patch(
            "src.core.install_git_hooks",
            side_effect=lambda: installs.append(1) or True,
        ), redirect_stdout(
            io.StringIO()
        ):
            from src.core import check_and_update_hooks_scripts

            check_and_update_hooks_scripts()
        return installs

    def test_scripts_lang_wins_over_the_interface_language(self):
        installed, urls, stamps = self.install({"SCRIPTS_LANG": "fr_fr"}, "pt_br")
        self.assertTrue(installed)
        self.assertTrue(any("pre-commit-template.fr.sh" in url for url in urls))
        # What is on disk is recorded; the request is left for the user to own.
        self.assertIn(("SCRIPTS_INSTALLED_LANG", "fr_fr"), stamps)
        self.assertNotIn("SCRIPTS_LANG", [key for key, _ in stamps])

    def test_the_es_es_code_is_fetched_as_the_es_file(self):
        # The regression this guards: the interface code is es_es while the
        # published script is named .es, so comparing the two directly never
        # matched and Spanish users were served the English hooks forever.
        _, urls, stamps = self.install({"SCRIPTS_LANG": "es_es"})
        self.assertTrue(any("pre-commit-template.es.sh" in url for url in urls))
        self.assertIn(("SCRIPTS_INSTALLED_LANG", "es_es"), stamps)

    def test_an_empty_choice_follows_the_interface_language(self):
        _, urls, stamps = self.install({"SCRIPTS_LANG": ""}, "pt_pt")
        self.assertTrue(any("pre-commit-template.pt_pt.sh" in url for url in urls))
        self.assertIn(("SCRIPTS_INSTALLED_LANG", "pt_pt"), stamps)

    def test_the_language_chosen_with_the_lang_flag_is_honoured(self):
        # i18n.set_lang() rebinds CURRENT_LANG instead of mutating it, and this
        # module keeps a frozen copy — the "automatic" option would otherwise
        # install in whatever language the process started in.
        self.assertEqual(i18n.CURRENT_LANG, "pt_br")
        with patch("src.core.read_env_file_values", return_value={"SCRIPTS_LANG": ""}):
            i18n.set_lang("fr_fr")
            try:
                self.assertEqual(core.effective_hook_lang(), "fr_fr")
            finally:
                i18n.set_lang("pt_br")

    def test_english_installs_the_base_script_and_says_so(self):
        _, urls, stamps = self.install({"SCRIPTS_LANG": "en_us"})
        self.assertFalse(any(".en_us.sh" in url for url in urls))
        self.assertIn(("SCRIPTS_INSTALLED_LANG", "en_us"), stamps)

    def test_a_language_without_a_translation_installs_the_base_script(self):
        _, urls, _ = self.install({"SCRIPTS_LANG": "de_de"})
        self.assertFalse(any(".de_de.sh" in url for url in urls))

    def test_the_gate_reinstalls_when_disk_differs_from_the_choice(self):
        self.assertEqual(len(self.gate(__scripts_version__, "pt_br", "fr_fr")), 1)

    def test_the_gate_stays_quiet_when_disk_matches_the_choice(self):
        self.assertEqual(self.gate(__scripts_version__, "fr_fr", "fr_fr"), [])

    def test_the_gate_repairs_a_missing_installed_marker_once(self):
        # Every install made before SCRIPTS_INSTALLED_LANG existed has no
        # marker: the next run reinstalls once and then takes the fast path.
        self.assertEqual(len(self.gate(__scripts_version__, "", "pt_br")), 1)

    def test_the_gate_reinstalls_on_a_version_bump(self):
        self.assertEqual(len(self.gate("v0.0.1", "pt_br", "pt_br")), 1)


if __name__ == '__main__':
    unittest.main()