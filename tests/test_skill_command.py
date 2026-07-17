import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.core import generate_skill_template


class TestSkillCommand:
    """Tests for the --skill command (generate_skill_template)."""

    @pytest.fixture(autouse=True)
    def _mock_cwd(self, tmp_path, monkeypatch):
        """Redirect os.getcwd() so .gitpr/skill/ is created under tmp_path."""
        monkeypatch.setattr("src.core.os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr("src.config.os.getcwd", lambda: str(tmp_path))

    def test_skill_download_success(self, tmp_path):
        """All template files are saved to .gitpr/skill/ when download succeeds."""
        fake_content = b"# Template content"
        mock_response = MagicMock()
        mock_response.read.return_value = fake_content
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            generate_skill_template()

        skill_dir = tmp_path / ".gitpr" / "skill"
        files = list(skill_dir.rglob("*.md")) + list(skill_dir.rglob("*.yml"))
        assert len(files) > 0, "No template files were created."

    def test_skill_no_overwrite_existing(self, tmp_path):
        """Existing templates are not overwritten."""
        skill_dir = tmp_path / ".gitpr" / "skill"
        skill_dir.mkdir(parents=True)
        existing = skill_dir / ".gitpr.commit.md"
        existing.write_text("legacy content", encoding="utf-8")

        mock_response = MagicMock()
        mock_response.read.return_value = b"new content"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False

        with patch("urllib.request.urlopen", return_value=mock_response):
            generate_skill_template()

        assert existing.read_text(encoding="utf-8") == "legacy content"

    def test_skill_handles_network_error(self, tmp_path, capsys):
        """Network errors should not raise an exception."""
        with patch("urllib.request.urlopen", side_effect=Exception("Network offline")):
            try:
                generate_skill_template()
            except Exception:
                pytest.fail("generate_skill_template should not raise on network error.")

        captured = capsys.readouterr()
        assert "Error" in captured.out or "Falha" in captured.out or "Network" in captured.out or "Erro" in captured.out
