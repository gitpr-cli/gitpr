import json
from unittest.mock import patch, MagicMock

from src.core import (
    _load_smart_excludes,
    _FALLBACK_SMART_EXCLUDES,
    _load_docs_smart_excludes,
    _FALLBACK_DOCS_SMART_EXCLUDES,
    _get_raw_docs_patterns,
    get_changed_docs_list,
)
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


# ──────────────────────────────────────────────────────────────
# _load_docs_smart_excludes
# ──────────────────────────────────────────────────────────────
class TestLoadDocsSmartExcludes:
    def test_local_file_hit_when_version_matches(self, tmp_path, monkeypatch):
        """Up-to-date local copy is used without any network access."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.md", "*.txt"]}), encoding="utf-8"
        )

        with patch("src.core.urllib.request.urlopen") as mock_open:
            result = _load_docs_smart_excludes()
            mock_open.assert_not_called()

        assert result == [":(exclude)*.md", ":(exclude)*.txt"]

    def test_downloads_and_caches_when_version_differs(self, tmp_path, monkeypatch):
        """Version mismatch triggers download, saves local copy + version marker."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.core.__lang_version__", "v999")
        remote_data = {"excludes": ["*.rst"]}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(remote_data).encode()
        mock_resp.__enter__.return_value = mock_resp

        with patch("src.core.urllib.request.urlopen", return_value=mock_resp):
            result = _load_docs_smart_excludes()

        assert result == [":(exclude)*.rst"]
        cached = json.loads(
            (tmp_path / ".gitpr" / "conf" / "gitpr.docs-smart-excludes.json").read_text(encoding="utf-8")
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
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.old_doc"]}), encoding="utf-8"
        )

        with patch("src.core.urllib.request.urlopen", side_effect=Exception("offline")):
            result = _load_docs_smart_excludes()

        assert result == [":(exclude)*.old_doc"]

    def test_falls_back_to_constant_when_nothing_available(self, tmp_path, monkeypatch):
        """No local copy + download failure = hardcoded fallback constant."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)

        with patch("src.core.urllib.request.urlopen", side_effect=Exception("offline")):
            result = _load_docs_smart_excludes()

        assert result == [f":(exclude){p}" for p in _FALLBACK_DOCS_SMART_EXCLUDES]


# ──────────────────────────────────────────────────────────────
# _get_raw_docs_patterns
# ──────────────────────────────────────────────────────────────
class TestGetRawDocsPatterns:
    def test_returns_plain_patterns_from_local_cache(self, tmp_path, monkeypatch):
        """Raw patterns are returned without :(exclude) prefix."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.md", "*.rst"]}), encoding="utf-8"
        )

        result = _get_raw_docs_patterns()
        assert result == ["*.md", "*.rst"]

    def test_falls_back_to_constant(self, tmp_path, monkeypatch):
        """No local copy + download failure = fallback constant (plain patterns)."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)

        with patch("src.core.urllib.request.urlopen", side_effect=Exception("offline")):
            result = _get_raw_docs_patterns()

        assert result == list(_FALLBACK_DOCS_SMART_EXCLUDES)
        assert "*.md" in result


# ──────────────────────────────────────────────────────────────
# get_changed_docs_list
# ──────────────────────────────────────────────────────────────
class TestGetChangedDocsList:
    def test_filters_docs_from_diff_name_only(self, tmp_path, monkeypatch):
        """Only doc-extension files are returned from git diff --name-only."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.md", "*.txt"]}), encoding="utf-8"
        )

        fake_output = "src/main.py\ndocs/README.md\nsrc/core.py\nCHANGELOG.txt\nassets/logo.png\n"
        mock_run = MagicMock()
        mock_run.stdout = fake_output
        mock_run.returncode = 0

        with patch("src.core.subprocess.run", return_value=mock_run):
            result = get_changed_docs_list()

        assert result == ["docs/README.md", "CHANGELOG.txt"]

    def test_uses_ancestor_hash_when_provided(self, tmp_path, monkeypatch):
        """When ancestor_hash is given, git diff uses it instead of HEAD."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.md"]}), encoding="utf-8"
        )

        mock_run = MagicMock()
        mock_run.stdout = "docs/guide.md\n"
        mock_run.returncode = 0

        with patch("src.core.subprocess.run", return_value=mock_run) as mock_run_patch:
            result = get_changed_docs_list(ancestor_hash="abc123")

        # Verify the command uses the ancestor hash, not HEAD
        call_args = mock_run_patch.call_args[0][0]
        assert "abc123" in call_args
        assert result == ["docs/guide.md"]

    def test_returns_empty_on_git_failure(self, tmp_path, monkeypatch):
        """Git errors are caught silently, returning an empty list."""
        monkeypatch.setattr("src.core.Path.home", lambda: tmp_path)
        monkeypatch.setenv("SMART_EXCLUDES_VERSION", __lang_version__)
        conf = tmp_path / ".gitpr" / "conf"
        conf.mkdir(parents=True)
        (conf / "gitpr.docs-smart-excludes.json").write_text(
            json.dumps({"excludes": ["*.md"]}), encoding="utf-8"
        )

        with patch("src.core.subprocess.run", side_effect=Exception("git failed")):
            result = get_changed_docs_list()

        assert result == []
