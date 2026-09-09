import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.core import ensure_release_skill_template, generate_skill_template


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

    def _download_all(self, urls):
        """Mocks urlopen collecting the requested URLs and returning content."""

        def fake_urlopen(url, timeout=None):
            urls.append(url)
            response = MagicMock()
            response.read.return_value = b"# Template content"
            response.__enter__.return_value = response
            response.__exit__.return_value = False
            return response

        return fake_urlopen

    def test_skill_download_includes_release_english(self, tmp_path, monkeypatch):
        """-s (EN) requests gitpr.release.md and saves .gitpr.release.md."""
        monkeypatch.setattr("src.core.CURRENT_LANG", "en_us")
        requested = []
        with patch("urllib.request.urlopen", side_effect=self._download_all(requested)):
            generate_skill_template()

        assert any(url.endswith("templates/gitpr.release.md") for url in requested)
        assert (tmp_path / ".gitpr" / "skill" / ".gitpr.release.md").exists()

    def test_skill_download_includes_release_language_variant(self, tmp_path, monkeypatch):
        """-s under pt_br requests gitpr.release.pt_br.md (same suffix rule)."""
        monkeypatch.setattr("src.core.CURRENT_LANG", "pt_br")
        requested = []
        with patch("urllib.request.urlopen", side_effect=self._download_all(requested)):
            generate_skill_template()

        assert any(url.endswith("templates/gitpr.release.pt_br.md") for url in requested)
        assert (tmp_path / ".gitpr" / "skill" / ".gitpr.release.md").exists()


class TestEnsureReleaseSkillTemplate:
    """R4: first-use auto-download of .gitpr.release.md (never overwrites)."""

    @pytest.fixture(autouse=True)
    def _mock_cwd(self, tmp_path, monkeypatch):
        """Redirect os.getcwd() so .gitpr/skill/ is created under tmp_path."""
        monkeypatch.setattr("src.core.os.getcwd", lambda: str(tmp_path))
        monkeypatch.setattr("src.config.os.getcwd", lambda: str(tmp_path))

    def _download_one(self, urls):
        def fake_urlopen(url, timeout=None):
            urls.append(url)
            response = MagicMock()
            response.read.return_value = b"# Release persona"
            response.__enter__.return_value = response
            response.__exit__.return_value = False
            return response

        return fake_urlopen

    def test_english_downloads_unversioned_template(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.CURRENT_LANG", "en_us")
        requested = []
        with patch("urllib.request.urlopen", side_effect=self._download_one(requested)):
            ensure_release_skill_template()

        assert len(requested) == 1
        assert requested[0].endswith("templates/gitpr.release.md")
        content = (tmp_path / ".gitpr" / "skill" / ".gitpr.release.md").read_text("utf-8")
        assert content == "# Release persona"

    def test_pt_br_downloads_suffixed_variant(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.CURRENT_LANG", "pt_br")
        requested = []
        with patch("urllib.request.urlopen", side_effect=self._download_one(requested)):
            ensure_release_skill_template()

        assert len(requested) == 1
        assert requested[0].endswith("templates/gitpr.release.pt_br.md")

    def test_unsupported_language_is_a_noop(self, tmp_path, monkeypatch):
        """Locales without a gitpr.release.* variant never hit the network."""
        monkeypatch.setattr("src.core.CURRENT_LANG", "de_de")
        with patch("urllib.request.urlopen") as urlopen:
            ensure_release_skill_template()

        urlopen.assert_not_called()
        assert not (tmp_path / ".gitpr" / "skill" / ".gitpr.release.md").exists()

    def test_existing_file_is_never_overwritten(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.CURRENT_LANG", "en_us")
        skill_dir = tmp_path / ".gitpr" / "skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / ".gitpr.release.md").write_text("keep me", encoding="utf-8")

        with patch("urllib.request.urlopen") as urlopen:
            ensure_release_skill_template()

        urlopen.assert_not_called()
        content = (skill_dir / ".gitpr.release.md").read_text("utf-8")
        assert content == "keep me"

    def test_network_failure_never_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.core.CURRENT_LANG", "en_us")
        with patch("urllib.request.urlopen", side_effect=Exception("offline")):
            try:
                ensure_release_skill_template()
            except Exception:
                pytest.fail("ensure_release_skill_template should not raise.")
