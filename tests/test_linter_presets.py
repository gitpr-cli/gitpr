import json
from unittest.mock import patch, MagicMock

from src.linter_wizard import load_linter_presets, _LINTER_PRESETS
from src.updater import __lang_version__


# ──────────────────────────────────────────────────────────────
# load_linter_presets
# ──────────────────────────────────────────────────────────────
class TestLoadLinterPresets:
    def test_local_file_hit_when_version_matches(self, tmp_path, monkeypatch):
        """Up-to-date local copy is used without any network access."""
        monkeypatch.setattr("src.linter_wizard.Path.home", lambda: tmp_path)
        monkeypatch.setenv("LINTER_PRESETS_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.linter-presets.json").write_text(
            json.dumps({"linters": [{"name": "Local"}]}), encoding="utf-8"
        )

        with patch("src.linter_wizard.urllib.request.urlopen") as mock_open:
            presets = load_linter_presets()
            mock_open.assert_not_called()

        assert presets == [{"name": "Local"}]

    def test_downloads_and_caches_when_version_differs(self, tmp_path, monkeypatch):
        """Version mismatch triggers download, saves local copy + version marker."""
        monkeypatch.setattr("src.linter_wizard.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.linter_wizard.__lang_version__", "v999")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"linters": [{"name": "Remote"}]}).encode()
        mock_resp.__enter__.return_value = mock_resp

        with patch("src.linter_wizard.urllib.request.urlopen", return_value=mock_resp):
            presets = load_linter_presets()

        assert presets == [{"name": "Remote"}]
        cached = json.loads(
            (tmp_path / ".gitpr" / "conf" / "gitpr.linter-presets.json").read_text(encoding="utf-8")
        )
        assert cached == {"linters": [{"name": "Remote"}]}
        env_text = (tmp_path / ".gitpr" / ".env").read_text(encoding="utf-8")
        assert "LINTER_PRESETS_VERSION" in env_text
        assert "v999" in env_text

    def test_force_redownloads_even_when_version_matches(self, tmp_path, monkeypatch):
        """force=True skips the version gate — the download button needs that."""
        monkeypatch.setattr("src.linter_wizard.Path.home", lambda: tmp_path)
        monkeypatch.setenv("LINTER_PRESETS_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        local_file = conf / "gitpr.linter-presets.json"
        local_file.write_text(json.dumps({"linters": [{"name": "Old"}]}), encoding="utf-8")
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"linters": [{"name": "Fresh"}]}).encode()
        mock_resp.__enter__.return_value = mock_resp

        with patch("src.linter_wizard.urllib.request.urlopen", return_value=mock_resp) as mock_open:
            presets = load_linter_presets(force=True)

        assert mock_open.called
        assert presets == [{"name": "Fresh"}]
        assert json.loads(local_file.read_text(encoding="utf-8")) == {"linters": [{"name": "Fresh"}]}
        env_text = (tmp_path / ".gitpr" / ".env").read_text(encoding="utf-8")
        assert "LINTER_PRESETS_VERSION" in env_text
        assert __lang_version__ in env_text

    def test_force_keeps_the_stale_copy_when_the_download_fails(self, tmp_path, monkeypatch):
        """A forced download that fails must not lose the previous copy."""
        monkeypatch.setattr("src.linter_wizard.Path.home", lambda: tmp_path)
        monkeypatch.setenv("LINTER_PRESETS_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        local_file = conf / "gitpr.linter-presets.json"
        local_file.write_text(json.dumps({"linters": [{"name": "Old"}]}), encoding="utf-8")

        with patch("src.linter_wizard.urllib.request.urlopen", side_effect=Exception("offline")):
            presets = load_linter_presets(force=True)

        assert presets == [{"name": "Old"}]
        assert json.loads(local_file.read_text(encoding="utf-8")) == {"linters": [{"name": "Old"}]}

    def test_falls_back_to_constant_when_nothing_available(self, tmp_path, monkeypatch):
        """No local copy + download failure = built-in preset constant."""
        monkeypatch.setattr("src.linter_wizard.Path.home", lambda: tmp_path)

        with patch("src.linter_wizard.urllib.request.urlopen", side_effect=Exception("offline")):
            presets = load_linter_presets(force=True)

        assert presets == _LINTER_PRESETS
