import unittest
from unittest.mock import patch, MagicMock
from src.core import (
    get_current_branch, get_git_diff,
    get_unstaged_files, get_unstaged_categorized,
    get_unstaged_diff, get_uncommitted_summary,
)

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


if __name__ == '__main__':
    unittest.main()