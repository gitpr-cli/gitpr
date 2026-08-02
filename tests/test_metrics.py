"""Tests for the metrics/telemetry system (src/metrics.py and src/ui/metrics_app.py)."""
import json
import os
import sys
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.metrics import (
    log_local_metric,
    log_command_metric,
    export_metrics,
    purge_metrics,
    show_metrics_summary,
    get_metrics_dir,
    enrich_metrics_from_cache,
    load_cache_token_summary,
    _save_metric_async,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_metric_file(metrics_dir, owner="test_owner", branch="main", payload=None):
    """Create a single metric JSON file and return its path."""
    import uuid
    from datetime import date

    uid = uuid.uuid4().hex[:15]
    dstr = date.today().strftime("%Y%m%d")
    fname = f"{uid}_{dstr}.json"
    fdir = metrics_dir / owner / branch
    fdir.mkdir(parents=True, exist_ok=True)
    fpath = fdir / fname

    if payload is None:
        payload = {
            "timestamp": "2026-01-15T10:30:00.123456",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 500,
            "duration_ms": 1200,
            "repo": "owner/repo",
            "branch": "main",
        }

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return fpath


def _seed_cache_file(cache_dir, action_folder="commit", payload=None, meta_raw=None):
    """Create a cache JSON file with optional meta_raw."""
    import hashlib

    fdir = cache_dir / action_folder
    fdir.mkdir(parents=True, exist_ok=True)
    md5 = hashlib.md5(("test_prompt_" + (payload or {}).get("action_type", "x")).encode()).hexdigest()
    fpath = fdir / f"{md5}.json"

    if payload is None:
        payload = {
            "action_type": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }

    data = dict(payload)
    if meta_raw:
        data["response"] = {"meta_raw": meta_raw}
    else:
        data["response"] = {}

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return fpath


# ---------------------------------------------------------------------------
# log_local_metric / _save_metric_async
# ---------------------------------------------------------------------------

class TestSaveMetricAsync:
    def test_writes_json_file_to_correct_path(self, tmp_path, monkeypatch):
        """Payload is written to metrics/{owner}/{branch}/{uuid}_{date}.json."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("src.metrics._get_owner_name", lambda: "test_owner")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "feature-x")
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "owner/repo")
        monkeypatch.setattr("src.metrics.gerar_uuid_base_15", lambda: "abc123456789012")

        payload = {"command": "commit", "status": "success", "provider": "gemini",
                   "tokens_estimated": 100, "duration_ms": 50,
                   "repo": "owner/repo", "branch": "feature-x"}

        _save_metric_async(payload)

        expected_dir = tmp_path / ".gitpr" / "metrics" / "test_owner" / "feature-x"
        assert expected_dir.is_dir()

        files = list(expected_dir.glob("*.json"))
        assert len(files) == 1
        assert files[0].name.startswith("abc123456789012")

        with open(files[0], "r", encoding="utf-8") as f:
            saved = json.load(f)
        assert saved["command"] == "commit"
        assert saved["status"] == "success"

    def test_never_raises_on_failure(self, tmp_path, monkeypatch):
        """Fire-and-forget: must never raise even if disk is full."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        # Make mkdir fail
        monkeypatch.setattr(Path, "mkdir", MagicMock(side_effect=OSError("disk full")))

        # Should not raise
        _save_metric_async({"command": "test"})

    def test_creates_nested_directories(self, tmp_path, monkeypatch):
        """Parent directories are created automatically."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("src.metrics._get_owner_name", lambda: "deeply")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "nested/branch")
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "a/b")
        monkeypatch.setattr("src.metrics.gerar_uuid_base_15", lambda: "x" * 15)

        _save_metric_async({"command": "x"})

        expected_dir = tmp_path / ".gitpr" / "metrics" / "deeply" / "nested-branch"
        assert expected_dir.is_dir()


class TestLogCommandMetric:
    def _make_thread_sync(self, monkeypatch):
        """Patch threading.Thread so the target runs synchronously on start()."""
        original_thread = threading.Thread

        class SyncThread(original_thread):
            def start(self):
                self.run()

        monkeypatch.setattr(threading, "Thread", SyncThread)

    def test_auto_detects_provider(self, tmp_path, monkeypatch):
        """When provider is None, auto-detect from config."""
        self._make_thread_sync(monkeypatch)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("src.metrics._get_owner_name", lambda: "o")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "b")
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "r/b")
        monkeypatch.setattr("src.metrics.gerar_uuid_base_15", lambda: "a" * 15)
        monkeypatch.setattr("src.config.get_ai_provider", lambda: "gemini")

        log_command_metric(command="commit", status="success")

        metrics_dir = tmp_path / ".gitpr" / "metrics"
        files = list(metrics_dir.rglob("*.json"))
        assert len(files) == 1
        with open(files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["provider"] == "gemini"

    def test_explicit_provider_preserved(self, tmp_path, monkeypatch):
        """Explicit provider="github" is not overwritten."""
        self._make_thread_sync(monkeypatch)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("src.metrics._get_owner_name", lambda: "o")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "b")
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "r/b")
        monkeypatch.setattr("src.metrics.gerar_uuid_base_15", lambda: "a" * 15)

        log_command_metric(command="issue:github_create", status="success", provider="github")

        metrics_dir = tmp_path / ".gitpr" / "metrics"
        files = list(metrics_dir.rglob("*.json"))
        with open(files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["provider"] == "github"

    def test_extra_kwargs_persisted(self, tmp_path, monkeypatch):
        """Extra kwargs (linter_errors, cache_hit, etc.) land in the payload."""
        self._make_thread_sync(monkeypatch)
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr("src.metrics._get_owner_name", lambda: "o")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "b")
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "r/b")
        monkeypatch.setattr("src.metrics.gerar_uuid_base_15", lambda: "a" * 15)

        log_command_metric(command="linter", status="success",
                           linter_errors=3, linter_warnings=7,
                           cache_hit=True, map_reduce_triggered=True,
                           custom_field="extra")

        metrics_dir = tmp_path / ".gitpr" / "metrics"
        files = list(metrics_dir.rglob("*.json"))
        with open(files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["linter_errors"] == 3
        assert data["linter_warnings"] == 7
        assert data["cache_hit"] is True
        assert data["map_reduce_triggered"] is True
        assert data["custom_field"] == "extra"

    def test_runs_in_background_thread(self, monkeypatch):
        """log_command_metric spawns a daemon thread."""
        fake_thread = MagicMock()
        monkeypatch.setattr(threading, "Thread", fake_thread)
        monkeypatch.setattr("src.metrics.get_repo_name", lambda: "r/b")
        monkeypatch.setattr("src.metrics.get_current_branch", lambda: "b")

        log_command_metric(command="x")
        fake_thread.assert_called_once()
        thread_instance = fake_thread.return_value
        assert thread_instance.daemon is True
        thread_instance.start.assert_called_once()


# ---------------------------------------------------------------------------
# export_metrics
# ---------------------------------------------------------------------------

class TestExportMetrics:
    def test_empty_dir_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        csv_path, json_path, count = export_metrics()
        assert csv_path is None
        assert json_path is None
        assert count == 0

    def test_produces_csv_and_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 500,
            "duration_ms": 1200,
            "repo": "owner/repo",
            "branch": "main",
        })
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T11:00:00",
            "command": "review",
            "status": "error",
            "provider": "deepseek",
            "tokens_estimated": 0,
            "duration_ms": 300,
            "repo": "owner/repo",
            "branch": "main",
        })

        csv_path, json_path, count = export_metrics()
        assert count == 2
        assert csv_path.endswith(".csv")
        assert json_path.endswith(".json")

        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            csv_text = f.read()
        assert "commit" in csv_text
        assert "review" in csv_text
        assert "gemini" in csv_text
        assert "deepseek" in csv_text
        # New columns present
        assert "prompt_tokens" in csv_text
        assert "completion_tokens" in csv_text
        assert "tokens_actual" in csv_text

        # Verify JSON content
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        assert len(json_data) == 2

    def test_skips_already_exported_uuids(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)

        # First export
        csv1, json1, count1 = export_metrics()
        assert count1 == 1

        # Second export — nothing new
        csv2, json2, count2 = export_metrics()
        assert count2 == 0
        assert csv2 is None

    def test_skips_export_subdirectory(self, tmp_path, monkeypatch):
        """Files inside export/ are never collected for re-export."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        export_dir = metrics_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Place a file inside export/ — should be ignored
        with open(export_dir / "already_exported.json", "w", encoding="utf-8") as f:
            json.dump([{"dummy": "list"}], f)

        _seed_metric_file(metrics_dir)
        csv_path, json_path, count = export_metrics()
        assert count == 1  # Only the real metric file, not the export list


# ---------------------------------------------------------------------------
# enrich_metrics_from_cache
# ---------------------------------------------------------------------------

class TestEnrichMetricsFromCache:
    def test_matches_event_by_repo_branch_action_datetime(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }, meta_raw={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})

        events = [{
            "timestamp": "2026-01-15T10:30:45",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 0,
            "repo": "owner/repo",
            "branch": "main",
        }]

        result = enrich_metrics_from_cache(events)
        assert len(result) == 1
        assert result[0]["prompt_tokens"] == 100
        assert result[0]["completion_tokens"] == 50
        assert result[0]["tokens_actual"] == 150

    def test_reads_telemetry_meta_as_fallback(self, tmp_path, monkeypatch):
        """Cache files with response._telemetry_meta (issue engine style) are also read."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        fdir = cache_dir / "issue"
        fdir.mkdir(parents=True, exist_ok=True)

        import hashlib
        md5 = hashlib.md5(b"issue_prompt").hexdigest()
        fpath = fdir / f"{md5}.json"
        data = {
            "repo": "owner/repo",
            "branch": "feat",
            "action_type": "issue",
            "datetime": "2026-06-01 14:00:00",
            "response": {"_telemetry_meta": {"total_tokens": 999}},
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f)

        events = [{
            "timestamp": "2026-06-01T14:00:30",
            "command": "issue",
            "repo": "owner/repo",
            "branch": "feat",
        }]

        result = enrich_metrics_from_cache(events)
        assert result[0]["tokens_actual"] == 999

    def test_prefers_exact_token_match(self, tmp_path, monkeypatch):
        """When two cache entries match the same minute, prefer exact total_tokens match."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }, meta_raw={"prompt_tokens": 80, "completion_tokens": 20, "total_tokens": 100})

        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "datetime": "2026-01-15 10:30:05",
        }, meta_raw={"prompt_tokens": 400, "completion_tokens": 100, "total_tokens": 500})

        events = [{
            "timestamp": "2026-01-15T10:30:45",
            "command": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "tokens_estimated": 500,  # Matches second cache entry exactly
        }]

        result = enrich_metrics_from_cache(events)
        assert result[0]["tokens_actual"] == 500

    def test_no_cache_dir_returns_unchanged(self, tmp_path, monkeypatch):
        """When cache dir doesn't exist, events are returned as-is."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        events = [{"command": "test"}]
        result = enrich_metrics_from_cache(events)
        assert result == events

    def test_ignores_corrupt_files(self, tmp_path, monkeypatch):
        """Malformed cache JSON is silently skipped."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        fdir = cache_dir / "commit"
        fdir.mkdir(parents=True, exist_ok=True)
        # Write invalid JSON
        (fdir / "bad.json").write_text("not json at all", encoding="utf-8")

        events = [{"command": "commit", "repo": "x", "branch": "y",
                    "timestamp": "2026-01-01T00:00:00"}]
        result = enrich_metrics_from_cache(events)
        assert len(result) == 1  # No crash, no enrichment

    def test_skips_non_dict_cache_entries(self, tmp_path, monkeypatch):
        """Cache files that are JSON lists/strings are ignored."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        fdir = cache_dir / "commit"
        fdir.mkdir(parents=True, exist_ok=True)
        (fdir / "list.json").write_text('["not", "a", "dict"]', encoding="utf-8")

        events = [{"command": "commit", "repo": "x", "branch": "y",
                    "timestamp": "2026-01-01T00:00:00"}]
        result = enrich_metrics_from_cache(events)
        assert len(result) == 1  # No crash

    def test_export_includes_cache_tokens(self, tmp_path, monkeypatch):
        """End-to-end: metric file + matching cache → exported JSON has token fields."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"

        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 0,
            "duration_ms": 500,
            "repo": "owner/repo",
            "branch": "main",
        })
        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit",
            "repo": "owner/repo",
            "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }, meta_raw={"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280})

        csv_path, json_path, count = export_metrics()
        assert count == 1

        with open(json_path, "r", encoding="utf-8") as f:
            exported = json.load(f)
        assert exported[0]["prompt_tokens"] == 200
        assert exported[0]["completion_tokens"] == 80
        assert exported[0]["tokens_actual"] == 280


# ---------------------------------------------------------------------------
# purge_metrics
# ---------------------------------------------------------------------------

class TestPurgeMetrics:
    def test_removes_metric_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)
        _seed_metric_file(metrics_dir, branch="feat")
        assert len(list(metrics_dir.rglob("*.json"))) == 2

        removed = purge_metrics()
        assert removed == 2
        assert len(list(metrics_dir.rglob("*.json"))) == 0

    def test_preserves_config_json(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        config_file = metrics_dir / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text('{"exported": []}', encoding="utf-8")

        _seed_metric_file(metrics_dir)
        purge_metrics()

        assert config_file.exists()
        # Only config.json remains
        files = list(metrics_dir.rglob("*.json"))
        assert len(files) == 1
        assert files[0].name == "config.json"


# ---------------------------------------------------------------------------
# show_metrics_summary
# ---------------------------------------------------------------------------

class TestShowMetricsSummary:
    def test_returns_zero_for_empty_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        summary = show_metrics_summary()
        assert summary["total_files"] == 0
        assert summary["total_events"] == 0

    def test_counts_files_correctly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)
        _seed_metric_file(metrics_dir)
        _seed_metric_file(metrics_dir, branch="feat")

        summary = show_metrics_summary()
        assert summary["total_files"] == 3


# ---------------------------------------------------------------------------
# get_metrics_dir
# ---------------------------------------------------------------------------

class TestGetMetricsDir:
    def test_returns_correct_path(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        path = get_metrics_dir()
        expected = str(tmp_path / ".gitpr" / "metrics")
        assert path == expected


# ---------------------------------------------------------------------------
# Dashboard (headless smoke tests via asyncio + Textual run_test)
# ---------------------------------------------------------------------------

class TestMetricsDashboard:
    def test_app_loads_with_data(self, tmp_path, monkeypatch):
        """Dashboard loads events, populates table, and doesn't crash."""
        import asyncio

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 500,
            "duration_ms": 1200,
            "repo": "owner/repo",
            "branch": "main",
        })
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T11:00:00",
            "command": "review",
            "status": "success",
            "provider": "deepseek",
            "tokens_estimated": 0,
            "duration_ms": 300,
            "repo": "owner/repo",
            "branch": "main",
        })

        async def run():
            from src.ui.metrics_app import MetricsApp
            app = MetricsApp(metrics_dir=str(metrics_dir))
            async with app.run_test() as pilot:
                await pilot.pause()
                # Table should have 2 data rows
                from textual.widgets import DataTable
                table = app.query_one("#events_table", DataTable)
                assert table.row_count == 2

        asyncio.run(run())

    def test_app_empty_state_does_not_crash(self, tmp_path, monkeypatch):
        """Dashboard with no data renders without crashing."""
        import asyncio

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)

        async def run():
            from src.ui.metrics_app import MetricsApp
            app = MetricsApp(metrics_dir=str(metrics_dir))
            async with app.run_test() as pilot:
                await pilot.pause()
                from textual.widgets import DataTable
                table = app.query_one("#events_table", DataTable)
                # Should have 1 placeholder row
                assert table.row_count == 1

        asyncio.run(run())

    def test_app_skips_export_and_config_files(self, tmp_path, monkeypatch):
        """Export list (JSON array) and config.json are ignored."""
        import asyncio

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        export_dir = metrics_dir / "export"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Place a list-typed export file (this was the crash cause)
        with open(export_dir / "gitpr_metrics_2026-01-15.json", "w", encoding="utf-8") as f:
            json.dump([{"bad": "list"}], f)

        # Place a config.json
        with open(metrics_dir / "config.json", "w", encoding="utf-8") as f:
            json.dump({"exported": []}, f)

        # Place a valid event
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00",
            "command": "pr",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 100,
            "duration_ms": 200,
            "repo": "a/b",
            "branch": "main",
        })

        async def run():
            from src.ui.metrics_app import MetricsApp
            app = MetricsApp(metrics_dir=str(metrics_dir))
            async with app.run_test() as pilot:
                await pilot.pause()
                from textual.widgets import DataTable
                table = app.query_one("#events_table", DataTable)
                # Only the valid event — not the list, not config.json
                assert table.row_count == 1

        asyncio.run(run())


# ---------------------------------------------------------------------------
# load_cache_token_summary
# ---------------------------------------------------------------------------

class TestLoadCacheTokenSummary:
    def test_aggregates_all_cache_files(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit", "repo": "owner/repo", "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }, meta_raw={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        _seed_cache_file(cache_dir, action_folder="review", payload={
            "action_type": "review", "repo": "owner/repo", "branch": "main",
            "datetime": "2026-01-15 11:00:00",
        }, meta_raw={"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280})

        summary = load_cache_token_summary(repo_name="owner/repo")
        assert summary["total_prompt_tokens"] == 300
        assert summary["total_completion_tokens"] == 130
        assert summary["total_tokens"] == 430
        assert summary["file_count"] == 2
        assert "commit" in summary["by_action"]
        assert "review" in summary["by_action"]
        assert summary["by_action"]["commit"]["count"] == 1
        assert summary["by_action"]["commit"]["tokens"] == 150

    def test_filters_by_repo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        _seed_cache_file(cache_dir, action_folder="commit", payload={
            "action_type": "commit", "repo": "owner/repo-a", "branch": "main",
            "datetime": "2026-01-15 10:30:00",
            "_key": "a",
        }, meta_raw={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        _seed_cache_file(cache_dir, action_folder="review", payload={
            "action_type": "review", "repo": "owner/repo-b", "branch": "main",
            "datetime": "2026-01-15 10:30:00",
            "_key": "b",
        }, meta_raw={"prompt_tokens": 999, "completion_tokens": 888, "total_tokens": 1887})

        summary = load_cache_token_summary(repo_name="owner/repo-a")
        assert summary["file_count"] == 1
        assert summary["total_tokens"] == 150

    def test_reads_telemetry_meta_fallback(self, tmp_path, monkeypatch):
        """Cache files with response._telemetry_meta are also counted."""
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        cache_dir = tmp_path / ".gitpr" / "cache" / "prompts"
        fdir = cache_dir / "issue"
        fdir.mkdir(parents=True, exist_ok=True)

        import hashlib
        md5 = hashlib.md5(b"issue_prompt").hexdigest()
        fpath = fdir / f"{md5}.json"
        data = {
            "repo": "owner/repo", "branch": "feat",
            "action_type": "issue", "datetime": "2026-06-01 14:00:00",
            "response": {"_telemetry_meta": {"total_tokens": 999, "prompt_tokens": 800, "completion_tokens": 199}},
        }
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f)

        summary = load_cache_token_summary(repo_name="owner/repo")
        assert summary["total_tokens"] == 999
        assert summary["file_count"] == 1

    def test_empty_dir_returns_zeros(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        summary = load_cache_token_summary()
        assert summary["total_tokens"] == 0
        assert summary["file_count"] == 0


# ---------------------------------------------------------------------------
# export_metrics with repo_filter and local output dir
# ---------------------------------------------------------------------------

class TestExportMetricsWithRepoFilter:
    def test_filters_events_by_repo(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, owner="owner1", payload={
            "timestamp": "2026-01-15T10:30:00", "command": "commit",
            "status": "success", "provider": "gemini", "tokens_estimated": 100,
            "duration_ms": 50, "repo": "owner1/repo-a", "branch": "main",
        })
        _seed_metric_file(metrics_dir, owner="owner2", payload={
            "timestamp": "2026-01-15T11:00:00", "command": "review",
            "status": "success", "provider": "deepseek", "tokens_estimated": 200,
            "duration_ms": 30, "repo": "owner2/repo-b", "branch": "main",
        })

        csv_path, json_path, count = export_metrics(repo_filter="owner1/repo-a")
        assert count == 1
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data[0]["repo"] == "owner1/repo-a"

    def test_output_dir_is_project_local(self, tmp_path, monkeypatch):
        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        project_dir = tmp_path / "my-project"
        project_dir.mkdir()
        monkeypatch.setattr(os, "getcwd", lambda: str(project_dir))

        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00", "command": "pr",
            "status": "success", "provider": "gemini", "tokens_estimated": 1,
            "duration_ms": 2, "repo": "a/b", "branch": "main",
        })

        csv_path, json_path, count = export_metrics()
        assert count == 1
        # Output should be under the project dir, not ~/.gitpr
        expected_dir = project_dir / ".gitpr" / "metrics" / "export"
        assert str(expected_dir) in str(csv_path)
        assert expected_dir.is_dir()


# ---------------------------------------------------------------------------
# Dashboard F5 column non-duplication
# ---------------------------------------------------------------------------

class TestMetricsDashboardF5:
    def test_refresh_does_not_duplicate_columns(self, tmp_path, monkeypatch):
        """F5 should clear rows but not re-add columns."""
        import asyncio

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, payload={
            "timestamp": "2026-01-15T10:30:00", "command": "commit",
            "status": "success", "provider": "gemini", "tokens_estimated": 100,
            "duration_ms": 50, "repo": "a/b", "branch": "main",
        })

        async def run():
            from src.ui.metrics_app import MetricsApp
            app = MetricsApp(metrics_dir=str(metrics_dir))
            async with app.run_test() as pilot:
                await pilot.pause()
                from textual.widgets import DataTable
                table = app.query_one("#events_table", DataTable)
                col_count_before = len(table.columns)
                row_count_before = table.row_count
                assert row_count_before == 1

                # Simulate F5 refresh
                app.action_refresh()
                await pilot.pause()

                col_count_after = len(table.columns)
                row_count_after = table.row_count
                # Columns must NOT have doubled
                assert col_count_after == col_count_before
                # Rows still present
                assert row_count_after == row_count_before

        asyncio.run(run())

    def test_dashboard_with_repo_filter(self, tmp_path, monkeypatch):
        """Dashboard filters events by repo when repo_filter is set."""
        import asyncio

        monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
        metrics_dir = tmp_path / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, owner="owner1", payload={
            "timestamp": "2026-01-15T10:30:00", "command": "commit",
            "status": "success", "provider": "gemini", "tokens_estimated": 100,
            "duration_ms": 50, "repo": "owner1/repo-a", "branch": "main",
        })
        _seed_metric_file(metrics_dir, owner="owner2", payload={
            "timestamp": "2026-01-15T11:00:00", "command": "review",
            "status": "success", "provider": "deepseek", "tokens_estimated": 200,
            "duration_ms": 30, "repo": "owner2/repo-b", "branch": "main",
        })

        async def run():
            from src.ui.metrics_app import MetricsApp
            app = MetricsApp(metrics_dir=str(metrics_dir), repo_filter="owner1/repo-a")
            async with app.run_test() as pilot:
                await pilot.pause()
                from textual.widgets import DataTable
                table = app.query_one("#events_table", DataTable)
                # Only the filtered repo's event
                assert table.row_count == 1

        asyncio.run(run())
