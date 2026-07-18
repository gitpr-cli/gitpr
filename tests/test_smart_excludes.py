import json
from unittest.mock import patch, MagicMock

from src.core import _load_smart_excludes, _FALLBACK_SMART_EXCLUDES
from src.updater import __lang_version__


# ──────────────────────────────────────────────────────────────
# _load_smart_excludes
# ──────────────────────────────────────────────────────────────
class TestLoadSmartExcludes:
    def test_local_file_hit_when_version_matches(self, tmp_path, monkeypatch):
        """Up-to-date local copy is used without any network access."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.lock", "go.sum"]}), encoding="utf-8"
        )

        with patch("src.core.urllib.request.urlopen") as mock_open:
            result = _load_smart_excludes()
            mock_open.assert_not_called()

        assert result == [":(exclude)*.lock", ":(exclude)go.sum"]

    def test_downloads_and_caches_when_version_differs(self, tmp_path, monkeypatch):
        """Version mismatch triggers download, saves local copy + version marker."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.core.__lang_version__", "v999")
        remote_data = {"excludes": ["*.svg"]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(remote_data).encode()
        mock_resp.__enter__.return_value = mock_resp

        with patch("src.core.urllib.request.urlopen", return_value=mock_resp):
            result = _load_smart_excludes()

        assert result == [":(exclude)*.svg"]
        cached = json.loads(
            (tmp_path / ".gitpr" / "conf" / "gitpr.smart-excludes.json").read_text(encoding="utf-8")
        )
        assert cached == remote_data
        env_text = (tmp_path / ".gitpr" / ".env").read_text(encoding="utf-8")
        assert "SMART_EXCLUDES_VERSION" in env_text
        assert "v999" in env_text

    def test_falls_back_to_stale_local_on_download_failure(self, tmp_path, monkeypatch):
        """When the download fails, the stale local copy is still used."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.core.__lang_version__", "v999")
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.old"]}), encoding="utf-8"
        )

        with patch("src.core.urllib.request.urlopen", side_effect=Exception("offline")):
            result = _load_smart_excludes()

        assert result == [":(exclude)*.old"]

    def test_falls_back_to_constant_when_nothing_available(self, tmp_path, monkeypatch):
        """No local copy + download failure = hardcoded fallback constant."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)

        with patch("src.core.urllib.request.urlopen", side_effect=Exception("offline")):
            result = _load_smart_excludes()

        assert result == [f":(exclude){p}" for p in _FALLBACK_SMART_EXCLUDES]
