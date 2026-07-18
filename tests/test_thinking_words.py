from unittest.mock import patch, MagicMock

from src.spinner import _load_thinking_words
from src.updater import __lang_version__


# ──────────────────────────────────────────────────────────────
# _load_thinking_words
# ──────────────────────────────────────────────────────────────
class TestLoadThinkingWords:
    def test_env_words_used_when_version_matches(self, tmp_path, monkeypatch):
        """Up-to-date .env words are used without any network access."""
        monkeypatch.setattr("src.spinner.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SPINNER_THINKING_WORDS", "Alpha|Beta")
        monkeypatch.setenv("THINKING_WORDS_VERSION", __lang_version__)

        with patch("src.spinner.urllib.request.urlopen") as mock_open:
            words = _load_thinking_words()
            mock_open.assert_not_called()

        assert words == ["Alpha", "Beta"]

    def test_version_mismatch_triggers_download(self, tmp_path, monkeypatch):
        """A __lang_version__ change forces a re-download even with .env words."""
        monkeypatch.setattr("src.spinner.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.spinner.__lang_version__", "v999")
        monkeypatch.setenv("SPINNER_THINKING_WORDS", "Old|Words")
        (tmp_path / ".gitpr").mkdir(parents=True)

        mock_resp = MagicMock()
        mock_resp.read.return_value = "Fresh\nWords\n".encode()
        mock_resp.__enter__.return_value = mock_resp

        with patch("src.spinner.urllib.request.urlopen", return_value=mock_resp):
            words = _load_thinking_words()

        assert words == ["Fresh", "Words"]
        env_text = (tmp_path / ".gitpr" / ".env").read_text(encoding="utf-8")
        assert "Fresh|Words" in env_text
        assert "THINKING_WORDS_VERSION" in env_text
        assert "v999" in env_text

    def test_stale_env_words_on_download_failure(self, tmp_path, monkeypatch):
        """When the download fails, the stale .env words are still used."""
        monkeypatch.setattr("src.spinner.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.spinner.__lang_version__", "v999")
        monkeypatch.setenv("SPINNER_THINKING_WORDS", "Stale|List")

        with patch("src.spinner.urllib.request.urlopen", side_effect=Exception("offline")):
            words = _load_thinking_words()

        assert words == ["Stale", "List"]
