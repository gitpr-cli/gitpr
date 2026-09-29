"""Tests for the metrics/telemetry system (src/metrics.py, src/ledger.py).

The ledger replaced a directory of per-event JSON files written from a daemon
thread. These tests are written against the replacement, and several of them
exist only to hold down a specific defect the audit found — they are marked
"Regression" with the finding's name, so a future rewrite knows what it is
about to re-break.

Every test redirects the home directory: the ledger resolves to
``~/.gitpr/metrics/telemetry.db`` and nothing here may touch the real one.
"""
import asyncio
import json
import os
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src import ledger
from src import metrics
from src.infrastructure.git.identity import GitContext
from src.infrastructure.scm.base import PullRequestResult, RepoRef, ScmProviderError
from src.main import cli
from src.metrics import (
    cost_report,
    export_metrics,
    get_metrics_dir,
    log_command_metric,
    log_local_metric,
    module_debt,
    provider_breakdown,
    prune_metrics,
    purge_metrics,
    quality_report,
    resolve_window,
    show_metrics_summary,
)
from src.config import metrics_price_env_key

OWNER_REPO = "owner/repo"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Redirects Path.home and fixes the working-copy identity.

    The identity is stubbed because the alternative is spawning `git` from a
    test, and the value is never what is under test — where it is *read from*
    is (see TestIdentitySource).
    """
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(
        metrics,
        "working_context",
        lambda: GitContext(
            repo=OWNER_REPO, branch="main", author_name="Ana", author_email="a@x.io"
        ),
    )
    metrics.reset_execution_context()
    # The terminal flags are per-run globals too, and one test's refusal to
    # answer the migration wizard must not silence the next test's absorption.
    ledger.configure_terminal()
    yield tmp_path
    metrics.reset_execution_context()
    ledger.configure_terminal()


def _seed_metric_file(metrics_dir, owner="test_owner", branch="main", payload=None):
    """Creates one legacy event JSON file and returns its path."""
    import uuid
    from datetime import date

    uid = uuid.uuid4().hex[:15]
    dstr = date.today().strftime("%Y%m%d")
    fdir = metrics_dir / owner / branch
    fdir.mkdir(parents=True, exist_ok=True)
    fpath = fdir / f"{uid}_{dstr}.json"

    if payload is None:
        payload = {
            "timestamp": "2026-01-15T10:30:00.123456",
            "command": "commit",
            "status": "success",
            "provider": "gemini",
            "tokens_estimated": 500,
            "duration_ms": 1200,
            "repo": OWNER_REPO,
            "branch": "main",
        }

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    return fpath


def _seed_cache_file(cache_dir, action_folder="commit", payload=None, meta_raw=None):
    """Creates a cache JSON file with optional meta_raw."""
    import hashlib

    fdir = cache_dir / action_folder
    fdir.mkdir(parents=True, exist_ok=True)
    md5 = hashlib.md5(
        ("test_prompt_" + (payload or {}).get("action_type", "x")).encode()
    ).hexdigest()
    fpath = fdir / f"{md5}.json"

    if payload is None:
        payload = {
            "action_type": "commit",
            "repo": OWNER_REPO,
            "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        }

    data = dict(payload)
    data["response"] = {"meta_raw": meta_raw} if meta_raw else {}

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return fpath


def _rows(source=None):
    return ledger.query_events(source=source)


# ---------------------------------------------------------------------------
# Writing — the promise the daemon thread broke
# ---------------------------------------------------------------------------


class TestWriteIsSynchronous:
    """Regression (G3): the row must exist when the call returns.

    log_local_metric used to hand the payload to a daemon thread. The
    interpreter can exit before that thread is scheduled, which is precisely
    what happens on `gitpr --hook-event` — a process whose whole life is
    "start, fire, exit". The assertion is the absence of the thread, not a
    sleep: a sleep would pass by luck and fail in CI.
    """

    def test_row_exists_the_moment_the_call_returns(self, home):
        assert log_local_metric(command="commit", status="success") is not None
        rows = _rows()
        assert len(rows) == 1
        assert rows[0]["command"] == "commit"

    def test_no_thread_is_spawned(self, home, monkeypatch):
        import threading

        started = []
        monkeypatch.setattr(
            threading, "Thread", MagicMock(side_effect=AssertionError("a thread!"))
        )
        del started  # only the patch matters

        log_local_metric(command="commit", status="success")
        assert len(_rows()) == 1

    def test_returns_the_event_id(self, home):
        event_id = log_local_metric(command="lint", status="success")
        assert event_id == _rows()[0]["id"]

    def test_never_raises_when_the_ledger_cannot_be_written(self, home, monkeypatch):
        """Telemetry must not turn a working gitpr into a failing one."""
        monkeypatch.setattr(
            ledger, "connect", MagicMock(side_effect=OSError("read-only home"))
        )
        assert log_local_metric(command="commit", status="success") is None

    def test_reports_the_failure_once_on_stderr(self, home, monkeypatch, capsys):
        monkeypatch.setattr(
            ledger, "connect", MagicMock(side_effect=OSError("disk full"))
        )
        # `_warned` is deliberately process-global (one complaint per process,
        # not one per event), so it has to be cleared to observe it at all.
        monkeypatch.setattr(ledger, "_warned", False)

        log_local_metric(command="commit", status="success")
        log_local_metric(command="review", status="success")

        err = capsys.readouterr().err
        assert err.count("disk full") == 1, (
            "the ledger must complain exactly once per process, not once per event"
        )

    def test_never_prints_to_stdout(self, home, capsys):
        """The MCP server reserves stdout for the JSON-RPC stream."""
        log_local_metric(command="commit", status="success")
        assert capsys.readouterr().out == ""


class TestEnrichAtWrite:
    """Regression (G2): tokens were joined in after the fact and never matched.

    The provider's own metadata — real token counts, model, provider — is
    copied into the row while both are still in hand. The old path joined the
    event to its cache file by (repo, branch, action, minute) using a
    command→folder map that disagreed with the writer's, so tokens_actual was
    always 0 for fullreview and filereview.
    """

    def test_meta_is_copied_into_columns(self, home):
        log_local_metric(
            command="commit",
            status="success",
            meta={
                "provider": "gemini",
                "model": "gemini-pro-latest",
                "prompt_tokens": 120,
                "completion_tokens": 40,
                "total_tokens": 160,
            },
        )
        row = _rows()[0]
        assert row["provider"] == "gemini"
        assert row["model"] == "gemini-pro-latest"
        assert row["prompt_tokens"] == 120
        assert row["completion_tokens"] == 40
        assert row["tokens_actual"] == 160

    def test_the_explicit_provider_wins_over_the_meta(self, home):
        log_local_metric(
            command="commit",
            status="success",
            provider="deepseek",
            meta={"provider": "gemini"},
        )
        assert _rows()[0]["provider"] == "deepseek"

    def test_without_meta_the_row_keeps_the_estimate(self, home):
        log_local_metric(command="linter", status="success", tokens_estimated=42)
        row = _rows()[0]
        assert row["tokens_actual"] == 0
        assert row["tokens_estimated"] == 42
        assert row["model"] == ""

    def test_fullreview_keeps_its_own_name_in_the_ledger(self, home):
        """Regression (G2): the metric copies renamed it to `review` to match
        a cache folder, which is what made the join disagree with the writer."""
        log_command_metric(
            command="fullreview",
            status="success",
            provider="gemini",
            meta={"total_tokens": 900, "provider": "gemini"},
        )
        assert _rows()[0]["command"] == "fullreview"
        assert _rows()[0]["tokens_actual"] == 900


class TestLogCommandMetric:
    def test_auto_detects_provider(self, home, monkeypatch):
        monkeypatch.setattr("src.config.get_ai_provider", lambda: "gemini")
        log_command_metric(command="commit", status="success")
        assert _rows()[0]["provider"] == "gemini"

    def test_explicit_provider_is_preserved(self, home):
        log_command_metric(command="commit", status="success", provider="deepseek")
        assert _rows()[0]["provider"] == "deepseek"

    def test_provider_falls_back_to_local_when_config_fails(self, home, monkeypatch):
        monkeypatch.setattr(
            "src.config.get_ai_provider", MagicMock(side_effect=RuntimeError("no config"))
        )
        log_command_metric(command="commit", status="success")
        assert _rows()[0]["provider"] == "local"

    def test_flags_land_on_their_columns(self, home):
        log_command_metric(
            command="pr",
            status="success",
            provider="gemini",
            cache_hit=True,
            map_reduce_triggered=True,
        )
        row = _rows()[0]
        assert row["cache_hit"] == 1
        assert row["map_reduce"] == 1

    def test_extra_kwargs_are_not_dropped(self, home):
        """A field with no column is kept in the payload, not discarded."""
        log_command_metric(
            command="linter",
            status="success",
            provider="git",
            linter_errors=3,
            linter_warnings=7,
            error_message="boom",
        )
        row = _rows()[0]
        assert row["linter_errors"] == 3
        assert row["linter_warnings"] == 7
        assert row["error_message"] == "boom"

    def test_unknown_kwargs_survive_in_the_payload(self, home):
        log_command_metric(
            command="blame", status="success", provider="git", commits_analyzed=12
        )
        payload = json.loads(_rows()[0]["payload"])
        assert payload["commits_analyzed"] == 12


class TestIdentitySource:
    """Regression (G5): the repo label must come from the working copy.

    get_repo_name() hardcodes github.com and answers "unknown/repo" on every
    other forge, so a hook firing in a GitLab clone recorded an event that the
    dashboard then filtered out.
    """

    def test_repo_branch_and_author_come_from_the_working_copy(self, home):
        log_local_metric(command="commit", status="success")
        row = _rows()[0]
        assert row["repo"] == OWNER_REPO
        assert row["branch"] == "main"
        assert row["author_name"] == "Ana"

    def test_the_caller_cannot_override_the_identity(self, home):
        """A live execution's repository is where it ran, not what it claims."""
        log_local_metric(
            command="commit", status="success", repo="someone/else", branch="other"
        )
        row = _rows()[0]
        assert row["repo"] == OWNER_REPO
        assert row["branch"] == "main"

    def test_the_author_email_stays_out_of_the_ledger(self, home):
        """The database travels between machines in a bundle (R2.2)."""
        log_local_metric(command="commit", status="success")
        row = _rows()[0]
        assert row["author_name"] == "Ana"
        assert "a@x.io" not in json.dumps(dict(row))

    def test_the_context_is_resolved_once_per_process(self, home, monkeypatch):
        calls = []
        monkeypatch.setattr(
            metrics,
            "working_context",
            lambda: (calls.append(1), GitContext(repo=OWNER_REPO))[1],
        )
        metrics.reset_execution_context()

        for _ in range(3):
            log_local_metric(command="commit", status="success")

        assert len(calls) == 1, "each resolution is two git spawns"


class TestModules:
    def test_modules_are_recorded_as_a_normalized_list(self, home):
        from src.ledger import extract_modules

        diff = (
            "diff --git a/src/fix/apply_fix.py b/src/fix/apply_fix.py\n"
            "diff --git a/src/ui/metrics_app.py b/src/ui/metrics_app.py\n"
            "diff --git a/README.md b/README.md\n"
        )
        log_command_metric(
            command="review",
            status="success",
            provider="gemini",
            modules=extract_modules(diff),
        )
        assert json.loads(_rows()[0]["modules"]) == [
            "src/fix",
            "src/ui",
            "(root)",
        ]

    def test_modules_are_null_without_a_diff(self, home):
        log_local_metric(command="linter", status="success")
        assert _rows()[0]["modules"] is None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestExportMetrics:
    def test_empty_ledger_exports_nothing(self, home, tmp_path):
        assert export_metrics(output_dir=str(tmp_path)) == (None, None, 0)

    def test_produces_csv_and_json(self, home, tmp_path):
        log_local_metric(command="commit", status="success", provider="gemini")
        log_local_metric(command="review", status="success", provider="deepseek")

        csv_path, json_path, count = export_metrics(output_dir=str(tmp_path))

        assert count == 2
        assert os.path.exists(csv_path)
        assert os.path.exists(json_path)

        header = Path(csv_path).read_text(encoding="utf-8").splitlines()[0]
        assert header.startswith("timestamp,day,command,status,provider,model,")
        assert len(Path(csv_path).read_text(encoding="utf-8").splitlines()) == 3

        payload = json.loads(Path(json_path).read_text(encoding="utf-8"))
        assert len(payload) == 2

    def test_exporting_one_repo_does_not_consume_another(self, home, tmp_path):
        """Regression (G1) — the data-loss bug the audit started from.

        The export state was a single config.json listing the ids of *every*
        repository, while the rows written to it were filtered by the caller's
        repo. Exporting repo A marked repo B's events as exported, so B's
        export answered "nothing new" forever, silently and permanently.
        """
        _write_as(OWNER_REPO, "commit")
        _write_as("other/repo", "review")

        _, _, count_a = export_metrics(output_dir=str(tmp_path), repo_filter=OWNER_REPO)
        assert count_a == 1

        _, _, count_b = export_metrics(output_dir=str(tmp_path), repo_filter="other/repo")
        assert count_b == 1, "repo B's events were marked exported by repo A's export"

    def test_an_event_is_exported_once(self, home, tmp_path):
        log_local_metric(command="commit", status="success")

        assert export_metrics(output_dir=str(tmp_path))[2] == 1
        assert export_metrics(output_dir=str(tmp_path))[2] == 0

    def test_repo_filter_isolates_the_rows(self, home, tmp_path):
        _write_as(OWNER_REPO, "commit")
        _write_as("other/repo", "review")

        csv_path, _, count = export_metrics(
            output_dir=str(tmp_path), repo_filter="other/repo"
        )
        assert count == 1
        body = Path(csv_path).read_text(encoding="utf-8")
        assert "other/repo" in body
        assert OWNER_REPO not in body

    def test_the_window_limits_the_export(self, home, tmp_path):
        log_local_metric(command="commit", status="success")
        assert export_metrics(
            output_dir=str(tmp_path), since="2099-01-01"
        ) == (None, None, 0)

    def test_output_dir_defaults_into_the_project(self, home, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        log_local_metric(command="commit", status="success")

        csv_path, _, _ = export_metrics()

        assert Path(csv_path).parent == tmp_path / ".gitpr" / "metrics" / "export"


def _write_as(repo, command):
    """Writes one row attributed to *repo*."""
    ledger.record_event(
        {"command": command, "status": "success", "provider": "gemini"},
        context=GitContext(repo=repo, branch="main", author_name="Ana"),
    )


def _write_on(day, command="commit", tokens=0):
    """Writes one execution dated *day*, whatever today is.

    A window can only be shown to work against rows whose date is known, and
    ``log_local_metric`` always stamps ``now``.
    """
    ledger.record_event(
        {
            "command": command,
            "status": "success",
            "provider": "gemini",
            "timestamp": f"{day}T10:00:00",
            "tokens_estimated": tokens,
        },
        context=GitContext(repo=OWNER_REPO, branch="main", author_name="Ana"),
    )


# ---------------------------------------------------------------------------
# Transport — bundle and merge
# ---------------------------------------------------------------------------


class TestBundleAndMerge:
    """Export is the human-readable surface; this is how rows travel between
    machines with their UUIDs intact (R4.1/R9.4)."""

    def test_a_bundle_carries_the_window_and_the_repo_it_was_asked_for(self, home, tmp_path):
        _write_as(OWNER_REPO, "commit")
        _write_as("other/repo", "review")
        _write_on("2026-01-10", command="blame")

        bundle = tmp_path / "team.db"
        rows = ledger.build_bundle(
            bundle, repo=OWNER_REPO, since="2026-01-01", until="2026-01-31"
        )

        assert rows == 1
        assert _bundle_rows(bundle, "command") == ["blame"]

    def test_a_bundle_arrives_unmarked(self, home, tmp_path):
        """Export bookkeeping belongs to the machine that exports: a bundle
        arriving pre-stamped would make the receiver's export answer "nothing
        new" — the shape of defect G1 in a new place."""
        log_local_metric(command="commit", status="success")
        export_metrics(output_dir=str(tmp_path / "out"))
        assert ledger.list_events_for_export() == [], "the export did not consume the row"

        bundle = tmp_path / "team.db"
        ledger.build_bundle(bundle)

        assert _bundle_rows(bundle, "exported_at") == [None]

    def test_merging_brings_the_rows_in(self, home, tmp_path):
        _write_as(OWNER_REPO, "commit")
        _write_as(OWNER_REPO, "review")
        ledger.record_event(
            {"command": "blame", "status": "success", "provider": "gemini"},
            source=ledger.SOURCE_BACKFILL,
        )
        bundle = tmp_path / "team.db"
        ledger.build_bundle(bundle)
        ledger.purge_events()
        assert ledger.count_events() == 0

        merged, skipped = ledger.merge_bundles([bundle])

        assert (merged, skipped) == (3, 0)
        # The origin travels with the row: reconstructed history stays out of
        # the execution aggregates on the machine that receives it, too.
        assert ledger.count_events(source=ledger.SOURCE_EXECUTION) == 2
        assert ledger.count_events(source=ledger.SOURCE_BACKFILL) == 1
        assert {
            row["command"] for row in _rows(source=ledger.SOURCE_EXECUTION)
        } == {"commit", "review"}

    def test_a_stamped_row_arriving_in_a_bundle_is_unstamped(self, home, tmp_path):
        """The receiver's export bookkeeping cannot be spent by the sender's."""
        log_local_metric(command="commit", status="success")
        bundle = tmp_path / "team.db"
        ledger.build_bundle(bundle)
        with sqlite3.connect(str(bundle)) as conn:
            conn.execute("UPDATE events SET exported_at = '2026-01-01T00:00:00'")
        ledger.purge_events()

        ledger.merge_bundles([bundle])

        assert ledger.list_events_for_export() != [], "the merge consumed the row"

    def test_merging_the_same_bundle_twice_adds_nothing(self, home, tmp_path):
        """Rows are keyed by UUID, so "send me your numbers" needs no protocol."""
        log_local_metric(command="commit", status="success")
        bundle = tmp_path / "team.db"
        ledger.build_bundle(bundle)

        assert ledger.merge_bundles([bundle]) == (0, 1)
        assert ledger.count_events() == 1

    def test_a_bundle_from_the_future_is_refused_before_anything_is_attached(
        self, home, tmp_path
    ):
        """The refusal must not leave a merge half-done (R10.4)."""
        log_local_metric(command="commit", status="success")
        bundle = tmp_path / "team.db"
        ledger.build_bundle(bundle)
        with sqlite3.connect(str(bundle)) as conn:
            conn.execute(f"PRAGMA user_version = {ledger.SCHEMA_VERSION + 1}")

        with pytest.raises(ledger.LedgerVersionError) as excinfo:
            ledger.merge_bundles([bundle])

        assert excinfo.value.found == ledger.SCHEMA_VERSION + 1
        assert ledger.count_events() == 1, "the local ledger was written to anyway"

    def test_one_bad_bundle_does_not_merge_the_others(self, home, tmp_path):
        """All the versions are read before the first ATTACH, so a refusal in
        the second file cannot leave the first one already folded in."""
        log_local_metric(command="commit", status="success")
        good = tmp_path / "good.db"
        ledger.build_bundle(good)
        bad = tmp_path / "bad.db"
        ledger.build_bundle(bad)
        with sqlite3.connect(str(bad)) as conn:
            conn.execute(f"PRAGMA user_version = {ledger.SCHEMA_VERSION + 1}")

        ledger.purge_events()

        with pytest.raises(ledger.LedgerVersionError):
            ledger.merge_bundles([good, bad])

        assert ledger.count_events() == 0

    def test_a_file_that_is_not_a_ledger_is_refused(self, home, tmp_path):
        stranger = tmp_path / "notes.db"
        with sqlite3.connect(str(stranger)) as conn:
            conn.execute("CREATE TABLE notes (body TEXT)")

        with pytest.raises(ledger.LedgerError):
            ledger.merge_bundles([stranger])

        assert ledger.bundle_schema_version(stranger) == 0

    def test_a_bundle_does_not_overwrite_a_file(self, home, tmp_path):
        log_local_metric(command="commit", status="success")
        destination = tmp_path / "team.db"
        destination.write_text("something I care about", encoding="utf-8")

        with pytest.raises(ledger.LedgerError):
            ledger.build_bundle(destination)

        assert destination.read_text(encoding="utf-8") == "something I care about"

    def test_there_is_nothing_to_bundle_without_a_ledger(self, home, tmp_path):
        with pytest.raises(ledger.LedgerError):
            ledger.build_bundle(tmp_path / "team.db")

    def test_the_command_line_bundles_and_merges(self, home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        log_local_metric(command="commit", status="success")
        bundle = tmp_path / "team.db"

        written = CliRunner().invoke(cli, ["metrics", "bundle", "-o", str(bundle)])
        assert written.exit_code == 0, written.output
        assert bundle.exists()

        ledger.purge_events()
        merged = CliRunner().invoke(cli, ["metrics", "merge", str(bundle)])

        assert merged.exit_code == 0, merged.output
        assert ledger.count_events() == 1

    def test_the_command_line_asks_before_replacing_a_bundle(self, home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        log_local_metric(command="commit", status="success")
        bundle = tmp_path / "team.db"
        bundle.write_text("older bundle", encoding="utf-8")

        declined = CliRunner().invoke(
            cli, ["metrics", "bundle", "-o", str(bundle)], input="n\n"
        )

        assert declined.exit_code == 0, declined.output
        assert bundle.read_text(encoding="utf-8") == "older bundle"

        replaced = CliRunner().invoke(
            cli, ["metrics", "bundle", "-o", str(bundle)], input="y\n"
        )
        assert replaced.exit_code == 0, replaced.output
        assert ledger.bundle_schema_version(bundle) == ledger.SCHEMA_VERSION

    def test_merge_without_files_says_so(self, home):
        result = CliRunner().invoke(cli, ["metrics", "merge"])

        assert result.exit_code == 0, result.output
        assert ledger.count_events() == 0


def _bundle_rows(bundle, column):
    """The values of one column in a bundle, read without the ledger's help."""
    with sqlite3.connect(str(bundle)) as conn:
        return [row[0] for row in conn.execute(f"SELECT {column} FROM events")]


# ---------------------------------------------------------------------------
# The window
# ---------------------------------------------------------------------------


class TestResolveWindow:
    """One window, one meaning (R6.3): the same two dates narrow every reading
    surface, and the day shortcuts are only shortcuts for them."""

    def test_no_flags_is_no_window(self):
        assert resolve_window() == (None, None)

    def test_days_ends_today_and_counts_back(self):
        since, until = resolve_window(days=7)

        assert until == date.today().isoformat()
        assert since == (date.today() - timedelta(days=6)).isoformat()

    def test_since_alone_runs_until_today(self):
        since, until = resolve_window(since="2026-01-01")

        assert since == "2026-01-01"
        assert until == date.today().isoformat()

    def test_until_alone_leaves_the_start_open(self):
        assert resolve_window(until="2026-01-01") == (None, "2026-01-01")

    def test_the_explicit_date_wins_over_the_shortcut(self):
        assert resolve_window(days=7, since="2026-01-01")[0] == "2026-01-01"

    def test_a_longer_timestamp_is_cut_to_its_day(self):
        """The column compares as text, so "2026-01-01T10:00:00" as a *start*
        would sort past every row of that same day and exclude all of them."""
        assert resolve_window(since="2026-01-01T10:00:00")[0] == "2026-01-01"


class TestTheWindowOnTheLedger:
    """The window reaches SQL: the bounds are inclusive on both ends."""

    def test_the_summary_counts_only_the_window(self, home):
        _write_on("2026-01-10")
        _write_on("2026-02-10")

        assert show_metrics_summary(since="2026-02-01")["total_events"] == 1

    def test_the_start_day_is_included(self, home):
        _write_on("2026-01-10")

        assert show_metrics_summary(since="2026-01-10")["total_events"] == 1

    def test_the_end_day_is_included(self, home):
        _write_on("2026-01-10")

        assert show_metrics_summary(until="2026-01-10")["total_events"] == 1
        assert show_metrics_summary(until="2026-01-09")["total_events"] == 0

    def test_the_export_leaves_the_rest_of_the_ledger_alone(self, home, tmp_path):
        _write_on("2026-01-10")
        _write_on("2026-02-10", command="review")

        _, _, count = export_metrics(output_dir=str(tmp_path), since="2026-02-01")

        assert count == 1
        csv_path = tmp_path / f"gitpr_metrics_{date.today().isoformat()}.csv"
        body = csv_path.read_text(encoding="utf-8")
        assert "2026-02-10" in body
        assert "2026-01-10" not in body

    def test_an_event_outside_the_window_is_not_marked_exported(self, home, tmp_path):
        """The window narrows what is written, not what is forgotten: the row
        left out is still there to be exported by a later, wider call."""
        _write_on("2026-01-10")
        _write_on("2026-02-10", command="review")

        export_metrics(output_dir=str(tmp_path), since="2026-02-01")

        assert ledger.count_events() == 2
        _, _, count = export_metrics(output_dir=str(tmp_path))
        assert count == 1


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class TestShowMetricsSummary:
    def test_counts_rows_not_files(self, home):
        """Regression (G7): it walked the directory for *.json and counted the
        export state file and every legacy event still on disk with them."""
        for _ in range(3):
            log_local_metric(command="commit", status="success")
        _seed_metric_file(home / ".gitpr" / "metrics")

        summary = show_metrics_summary()

        assert summary["total_events"] == 3
        assert summary["pending_legacy_files"] == 1

    def test_backfilled_rows_are_counted_apart(self, home):
        log_local_metric(command="commit", status="success")
        ledger.record_event(
            {"command": "commit", "status": "success"},
            source=ledger.SOURCE_BACKFILL,
            context=GitContext(repo=OWNER_REPO),
        )

        summary = show_metrics_summary()

        assert summary["total_events"] == 1
        assert summary["backfilled_events"] == 1

    def test_empty_ledger_reports_zero(self, home):
        """No ledger at all: the summary must not create one."""
        summary = show_metrics_summary()

        assert summary["total_events"] == 0
        assert summary["exists"] is False

    def test_the_window_limits_the_count(self, home):
        log_local_metric(command="commit", status="success")
        assert show_metrics_summary(since="2099-01-01")["total_events"] == 0

    def test_reports_the_database_it_actually_read(self, home):
        log_local_metric(command="commit", status="success")
        summary = show_metrics_summary()

        assert summary["db_path"].endswith("telemetry.db")
        assert summary["path"] == get_metrics_dir()


# ---------------------------------------------------------------------------
# Purge and prune
# ---------------------------------------------------------------------------


class TestPurgeMetrics:
    def test_removes_every_row(self, home):
        for _ in range(3):
            log_local_metric(command="commit", status="success")

        assert purge_metrics() == 3
        assert _rows() == []

    def test_removes_the_legacy_files_too(self, home):
        metrics_dir = home / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)
        _seed_metric_file(metrics_dir)

        assert purge_metrics() == 2
        assert ledger.pending_legacy_files() == []

    def test_on_an_empty_ledger_it_is_a_no_op(self, home):
        assert purge_metrics() == 0


class TestPruneMetrics:
    def test_removes_only_rows_before_the_cutoff(self, home):
        ledger.record_event(
            {"command": "old", "status": "success", "timestamp": "2020-01-01T00:00:00"},
            context=GitContext(repo=OWNER_REPO),
        )
        log_local_metric(command="new", status="success")

        assert prune_metrics("2021-01-01") == 1
        assert [r["command"] for r in _rows()] == ["new"]

    def test_can_prune_one_source_only(self, home):
        """`prune` must be able to spare the reconstructed history (R10.1)."""
        ledger.record_event(
            {"command": "a", "status": "success", "timestamp": "2020-01-01T00:00:00"},
            context=GitContext(repo=OWNER_REPO),
        )
        ledger.record_event(
            {"command": "b", "status": "success", "timestamp": "2020-01-01T00:00:00"},
            source=ledger.SOURCE_BACKFILL,
            context=GitContext(repo=OWNER_REPO),
        )

        assert prune_metrics("2021-01-01", source=ledger.SOURCE_EXECUTION) == 1
        assert [r["command"] for r in _rows()] == ["b"]


# ---------------------------------------------------------------------------
# Migration — the invariant
# ---------------------------------------------------------------------------


class TestMigration:
    """`The ledger is never born empty while event files are on disk.`

    This is the invariant that keeps the G1 loss from happening by a different
    route: a database that exists and is empty silences the file fallback while
    claiming to have taken the data in.
    """

    def test_absorbing_takes_every_file_in(self, home):
        metrics_dir = home / ".gitpr" / "metrics"
        for owner in ("alice", "bob", "carol"):
            for branch in ("main", "dev"):
                _seed_metric_file(metrics_dir, owner=owner, branch=branch)

        absorbed, already = ledger.absorb_legacy_files()

        assert absorbed == 6
        assert already == 0
        assert len(_rows()) == 6

    def test_a_second_run_absorbs_nothing(self, home):
        """Idempotent by construction: the first run moved the files away, so
        the second has nothing to find and nothing to duplicate."""
        metrics_dir = home / ".gitpr" / "metrics"
        for owner in ("alice", "bob"):
            _seed_metric_file(metrics_dir, owner=owner)

        ledger.absorb_legacy_files()
        absorbed, _already = ledger.absorb_legacy_files()

        assert absorbed == 0
        assert len(_rows()) == 2

    def test_absorbed_rows_keep_the_repository_they_recorded(self, home):
        """A historical replay takes its identity from the record, not from
        whichever directory the user happens to be standing in today."""
        metrics_dir = home / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir, owner="alice", payload={
            "timestamp": "2026-01-15T10:30:00",
            "command": "commit",
            "status": "success",
            "repo": "alice/repo",
            "branch": "feature",
        })

        ledger.absorb_legacy_files()

        row = _rows()[0]
        assert row["repo"] == "alice/repo"
        assert row["branch"] == "feature"
        assert row["repo"] != OWNER_REPO

    def test_colliding_ids_do_not_lose_files(self, home):
        """Two owners can legitimately hold a file with the same uuid name."""
        import shutil

        metrics_dir = home / ".gitpr" / "metrics"
        first = _seed_metric_file(metrics_dir, owner="alice")
        second = metrics_dir / "bob" / "main" / first.name
        second.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(first, second)

        absorbed, _ = ledger.absorb_legacy_files()

        assert absorbed == 2, "one file was dropped on a primary-key collision"
        assert len(_rows()) == 2

    def test_the_originals_are_moved_out_of_the_metrics_directory(self, home):
        """Regression (G7): the summary walks metrics/ recursively, so leaving
        the legacy files there would keep them in the count forever."""
        metrics_dir = home / ".gitpr" / "metrics"
        original = _seed_metric_file(metrics_dir)

        ledger.absorb_legacy_files()

        assert not original.exists()
        assert list(ledger.get_legacy_dir().rglob("*.json")), "not moved anywhere"
        assert not (metrics_dir / "alice").exists()

    def test_moving_is_reversible_by_hand(self, home):
        """Moved, never deleted — R6.4. The file keeps its name and contents."""
        metrics_dir = home / ".gitpr" / "metrics"
        original = _seed_metric_file(metrics_dir)
        expected = json.loads(original.read_text(encoding="utf-8"))

        ledger.absorb_legacy_files()

        moved = list(ledger.get_legacy_dir().rglob(original.name))
        assert len(moved) == 1
        assert json.loads(moved[0].read_text(encoding="utf-8")) == expected

    def test_a_corrupt_file_does_not_abort_the_migration(self, home):
        metrics_dir = home / ".gitpr" / "metrics"
        bad = metrics_dir / "alice" / "main" / "broken_20260101.json"
        bad.parent.mkdir(parents=True, exist_ok=True)
        bad.write_text("{not json", encoding="utf-8")
        _seed_metric_file(metrics_dir, owner="bob")

        absorbed, _ = ledger.absorb_legacy_files()

        assert absorbed == 1
        assert len(_rows()) == 1

    def test_ensure_ledger_absorbs_silently_when_not_interactive(self, home):
        metrics_dir = home / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)

        assert ledger.ensure_ledger(interactive=False) is True

        assert len(_rows()) == 1
        assert ledger.pending_legacy_files() == []

    def test_ensure_ledger_never_leaves_the_database_empty_with_files_present(
        self, home
    ):
        """The invariant, stated as a test."""
        metrics_dir = home / ".gitpr" / "metrics"
        for _ in range(4):
            _seed_metric_file(metrics_dir)

        ledger.ensure_ledger(interactive=False)

        assert ledger.ledger_exists()
        assert len(_rows()) == 4, "the database was born empty with 4 files on disk"

    def test_ensure_ledger_creates_one_when_there_is_nothing_to_absorb(self, home):
        assert ledger.ensure_ledger(interactive=False) is True
        assert ledger.ledger_exists()
        assert ledger.pending_legacy_files() == []

    def test_ensure_ledger_is_idempotent(self, home):
        ledger.ensure_ledger(interactive=False)
        assert ledger.ensure_ledger(interactive=False) is False

    def test_migrating_does_not_mark_anything_as_already_exported(self, home):
        """No export ever reported this history, so the first one after the
        migration must. Stamping the rows on the way in would keep the whole
        archive out of the CSV with nothing to say so."""
        metrics_dir = home / ".gitpr" / "metrics"
        for _ in range(3):
            _seed_metric_file(metrics_dir)
        _seed_cache_file(
            home / ".gitpr" / "cache" / "prompts", meta_raw={"model": "m"}
        )

        ledger.absorb_legacy_files()
        ledger.backfill_from_cache()

        assert len(ledger.list_events_for_export(repo=OWNER_REPO)) == 4


class TestMigrationWizard:
    """The interactive path. The wizard decides, then the ledger absorbs.

    ``MigrationApp.run`` is replaced with a scripted answer: what is under test
    is the decision's consequence, not Textual's event loop, which
    TestMigrationWizardUi covers separately.
    """

    @staticmethod
    def _answer(choice):
        def run(app):
            app.choice = choice

        return run

    def test_importing_absorbs_the_event_files(self, home, monkeypatch):
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        metrics_dir = home / ".gitpr" / "metrics"
        for _ in range(3):
            _seed_metric_file(metrics_dir)
        monkeypatch.setattr(MigrationApp, "run", self._answer("import"))

        assert run_migration_wizard(legacy_files=ledger.pending_legacy_files()) is True

        assert len(ledger.query_events(source=ledger.SOURCE_EXECUTION)) == 3
        assert ledger.pending_legacy_files() == []

    def test_importing_and_reconstructing_adds_the_cache_rows(
        self, home, monkeypatch
    ):
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        _seed_metric_file(home / ".gitpr" / "metrics")
        _seed_cache_file(
            home / ".gitpr" / "cache" / "prompts",
            meta_raw={"provider": "gemini", "model": "gemini-pro-latest"},
        )
        monkeypatch.setattr(MigrationApp, "run", self._answer("import_backfill"))

        run_migration_wizard(legacy_files=ledger.pending_legacy_files())

        assert len(ledger.query_events(source=ledger.SOURCE_EXECUTION)) == 1
        backfilled = ledger.query_events(source=ledger.SOURCE_BACKFILL)
        assert len(backfilled) == 1
        assert backfilled[0]["model"] == "gemini-pro-latest"

    def test_reconstructing_alone_still_takes_the_event_files(self, home, monkeypatch):
        """The two offers are not alternatives — the second offer is the first
        one plus an approximation, never a substitute for the truth."""
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        _seed_metric_file(home / ".gitpr" / "metrics")
        monkeypatch.setattr(MigrationApp, "run", self._answer("import_backfill"))

        run_migration_wizard(legacy_files=ledger.pending_legacy_files())

        assert len(ledger.query_events(source=ledger.SOURCE_EXECUTION)) == 1

    def test_skipping_writes_the_marker_and_imports_nothing(self, home, monkeypatch):
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        metrics_dir = home / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)
        monkeypatch.setattr(MigrationApp, "run", self._answer("skip"))

        assert run_migration_wizard(legacy_files=ledger.pending_legacy_files()) is True

        assert ledger.marker_present() is True
        assert len(_rows()) == 0
        assert len(ledger.pending_legacy_files()) == 1, "the files must stay put"

    def test_skipping_stops_the_question_being_asked_again(self, home, monkeypatch):
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        asked = []

        def counting_answer(app):
            asked.append(True)
            app.choice = "skip"

        monkeypatch.setattr(MigrationApp, "run", counting_answer)
        _seed_metric_file(home / ".gitpr" / "metrics")
        run_migration_wizard(legacy_files=ledger.pending_legacy_files())
        assert len(asked) == 1

        # The marker short-circuits the wizard — and the silence that follows
        # must not turn into an import of the very files just refused.
        assert ledger.ensure_ledger(interactive=True) is True
        assert len(asked) == 1, "the wizard asked again after a refusal"
        assert ledger.ledger_exists()
        assert len(_rows()) == 0
        assert len(ledger.pending_legacy_files()) == 1, "the refusal was undone"

    def test_a_hook_does_not_import_after_a_refusal(self, home, monkeypatch):
        """Regression (G1, by the other route): the silent path runs on every
        command, so a refusal that only silenced the question would be undone by
        the next hook — the user would be imported from, having said no."""
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        _seed_metric_file(home / ".gitpr" / "metrics")
        monkeypatch.setattr(MigrationApp, "run", self._answer("skip"))
        run_migration_wizard(legacy_files=ledger.pending_legacy_files())

        ledger.ensure_ledger(interactive=False)

        assert len(_rows()) == 0
        assert len(ledger.pending_legacy_files()) == 1

    def test_closing_the_window_decides_nothing(self, home, monkeypatch):
        from src.ui.metrics_migration_app import MigrationApp, run_migration_wizard

        metrics_dir = home / ".gitpr" / "metrics"
        _seed_metric_file(metrics_dir)
        monkeypatch.setattr(MigrationApp, "run", self._answer(None))

        assert run_migration_wizard(legacy_files=ledger.pending_legacy_files()) is False

        assert ledger.marker_present() is False
        assert ledger.ledger_exists() is False
        assert len(ledger.pending_legacy_files()) == 1

    def test_an_abort_does_not_leave_an_empty_ledger_behind(self, home, monkeypatch):
        """Regression (G1, by the other route): the scan reads only while
        telemetry.db is absent. A database created over an aborted wizard would
        silence the fallback and orphan the archive — so an abort must not
        create one, and the next run must ask again."""
        from src.ui.metrics_migration_app import MigrationApp

        _seed_metric_file(home / ".gitpr" / "metrics")
        monkeypatch.setattr(MigrationApp, "run", self._answer(None))

        assert ledger.ensure_ledger(interactive=True) is False

        assert ledger.ledger_exists() is False
        assert len(ledger.pending_legacy_files()) == 1


class TestMigrationWizardUi:
    """The buttons *are* the decision, so they get a test of their own.

    Composing with a real file count also proves the count reaches the text: a
    missing placeholder would raise here rather than in front of the user.
    """

    @staticmethod
    def _press(*keys):
        async def run():
            from src.ui.metrics_migration_app import MigrationApp

            app = MigrationApp(file_count=2)
            async with app.run_test() as pilot:
                for key in keys:
                    if key.startswith("#"):
                        await pilot.click(key)
                    else:
                        await pilot.press(key)
                return app.choice

        return asyncio.run(run())

    def test_importing_is_the_primary_button(self):
        assert self._press("#import_only") == "import"

    def test_the_second_offer_is_the_import_plus_the_cache(self):
        assert self._press("#import_backfill") == "import_backfill"

    def test_skipping_is_available(self):
        assert self._press("#skip") == "skip"

    def test_escape_is_not_a_fourth_answer(self):
        assert self._press("escape") is None


# ---------------------------------------------------------------------------
# The fallback bridge
# ---------------------------------------------------------------------------


class TestFallbackScan:
    """R5.1 — the file scan runs only while telemetry.db does not exist."""

    def test_cache_scan_reads_the_cache_files(self, home):
        _seed_cache_file(home / ".gitpr" / "cache" / "prompts", "commit", meta_raw={
            "provider": "gemini", "total_tokens": 555, "duration_ms": 800
        })

        rows = metrics.scan_cache_files_for_dashboard(since_date="2020-01-01")

        assert len(rows) == 1
        assert rows[0]["tokens"] == 555
        assert rows[0]["provider"] == "gemini"
        assert rows[0]["source"] == "cache"

    def test_cache_scan_skips_list_typed_responses(self, home):
        """Legacy entries stored a bare list rather than a response object."""
        path = _seed_cache_file(home / ".gitpr" / "cache" / "prompts", "commit")
        data = json.loads(path.read_text(encoding="utf-8"))
        data["response"] = ["not", "a", "dict"]
        path.write_text(json.dumps(data), encoding="utf-8")

        assert metrics.scan_cache_files_for_dashboard(since_date="2020-01-01") == []

    def test_cache_scan_ignores_corrupt_files(self, home):
        cache_dir = home / ".gitpr" / "cache" / "prompts" / "commit"
        cache_dir.mkdir(parents=True, exist_ok=True)
        (cache_dir / "broken.json").write_text("{not json", encoding="utf-8")
        _seed_cache_file(home / ".gitpr" / "cache" / "prompts", "review")

        rows = metrics.scan_cache_files_for_dashboard(since_date="2020-01-01")

        assert len(rows) == 1

    def test_cache_scan_respects_the_repo_filter(self, home):
        cache_dir = home / ".gitpr" / "cache" / "prompts"
        _seed_cache_file(cache_dir, "commit", payload={
            "action_type": "commit", "repo": "other/repo", "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        })

        assert metrics.scan_cache_files_for_dashboard(
            repo_filter=OWNER_REPO, since_date="2020-01-01"
        ) == []

    def test_event_scan_reads_the_files_still_on_disk(self, home):
        _seed_metric_file(home / ".gitpr" / "metrics")

        rows = metrics.scan_event_files_for_dashboard()

        assert len(rows) == 1
        assert rows[0]["source"] == "event"
        assert rows[0]["tokens"] == 500

    def test_the_two_scans_are_never_joined(self, home):
        """Regression (G2): the rows keep their own identity; nothing is merged
        by minute, so the same execution can appear once per source and each
        row is traceable to the file it came from."""
        _seed_metric_file(home / ".gitpr" / "metrics")
        _seed_cache_file(home / ".gitpr" / "cache" / "prompts", "commit", payload={
            "action_type": "commit", "repo": OWNER_REPO, "branch": "main",
            "datetime": "2026-01-15 10:30:00",
        })

        rows = metrics.scan_cache_files_for_dashboard(since_date="2020-01-01")
        rows += metrics.scan_event_files_for_dashboard()

        assert sorted(r["source"] for r in rows) == ["cache", "event"]
        assert all(r["path"] for r in rows), "a row that cannot be traced back"


class TestDashboard:
    """The dashboard loads on a worker thread, so every test waits for it.

    ``pilot.pause()`` alone is not enough: a thread blocked on I/O reads as
    idle, and the assertion can fire while the load is still running.
    """

    def test_reads_the_ledger_when_it_exists(self, home):
        for command in ("commit", "review"):
            log_local_metric(command=command, status="success", provider="gemini")

        assert self._row_count() == 2

    def test_the_first_write_takes_the_legacy_files_in_with_it(self, home):
        """The invariant, seen from the dashboard: a write with event files on
        disk produces a database that already holds them, so the table shows
        both rather than the new row alone (which is exactly how the old
        implementation lost the older data from view)."""
        _seed_metric_file(home / ".gitpr" / "metrics", payload={
            "timestamp": "2026-01-15T10:30:00", "command": "linter",
            "status": "success", "provider": "git", "repo": OWNER_REPO,
            "branch": "main",
        })

        log_local_metric(command="commit", status="success", provider="gemini")

        assert ledger.pending_legacy_files() == []
        assert self._row_count() == 2

    def test_falls_back_to_the_files_without_a_ledger(self, home):
        _seed_metric_file(home / ".gitpr" / "metrics")

        assert self._row_count() == 1, "the fallback bridge stopped reading"

    def test_empty_state_does_not_crash(self, home):
        assert self._row_count() == 1  # the placeholder row

    def test_the_repo_filter_scopes_the_rows(self, home):
        log_local_metric(command="commit", status="success")
        _write_as("other/repo", "review")

        assert self._row_count(repo_filter=OWNER_REPO) == 1

    def test_the_backfill_rows_are_labeled(self, home):
        ledger.record_event(
            {"command": "commit", "status": "success", "tokens_estimated": 10},
            source=ledger.SOURCE_BACKFILL,
            context=GitContext(repo=OWNER_REPO, branch="main"),
        )

        assert self._row_count() == 1

    def test_refresh_does_not_duplicate_the_columns(self, home):
        log_local_metric(command="commit", status="success")

        async def run():
            from textual.widgets import DataTable

            from src.ui.metrics_app import MetricsApp

            app = MetricsApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                await app.workers.wait_for_complete()
                await pilot.pause()

                table = app.query_one("#events_table", DataTable)
                before = len(table.columns)

                await pilot.press("f5")
                await app.workers.wait_for_complete()
                await pilot.pause()

                assert len(table.columns) == before
                assert table.row_count == 1

        asyncio.run(run())

    def test_an_empty_database_renders_without_crashing(self, home):
        """An empty ledger is a legitimate state (a fresh install) and the
        dashboard has to show it rather than fall over on a missing key."""
        ledger.ensure_ledger(interactive=False)

        async def run():
            from src.ui.metrics_app import MetricsApp

            app = MetricsApp()
            async with app.run_test() as pilot:
                await pilot.pause()
                await app.workers.wait_for_complete()
                await pilot.pause()
                assert app.using_ledger is True
                assert app.events == []

        asyncio.run(run())

    @staticmethod
    def _row_count(repo_filter=None, since=None, until=None):
        async def run():
            from textual.widgets import DataTable

            from src.ui.metrics_app import MetricsApp

            app = MetricsApp(repo_filter=repo_filter, since=since, until=until)
            async with app.run_test() as pilot:
                await pilot.pause()
                await app.workers.wait_for_complete()
                await pilot.pause()
                return app.query_one("#events_table", DataTable).row_count

        return asyncio.run(run())

    @staticmethod
    def _loaded(repo_filter=None, since=None, until=None):
        """The rows the app ended up holding, not the table's row count.

        An empty state renders one placeholder row, so the count cannot tell
        "nothing in the window" from "the window was not applied".
        """

        async def run():
            from src.ui.metrics_app import MetricsApp

            app = MetricsApp(repo_filter=repo_filter, since=since, until=until)
            async with app.run_test() as pilot:
                await pilot.pause()
                await app.workers.wait_for_complete()
                await pilot.pause()
                return app.events

        return asyncio.run(run())

    def test_the_window_narrows_the_ledger_rows(self, home):
        _write_on("2026-01-10", command="commit")
        _write_on("2026-02-10", command="review")

        assert [r["command"] for r in self._loaded(since="2026-02-01")] == ["review"]

    def test_the_window_narrows_the_fallback_rows(self, home):
        """The bridge has no SQL to filter in — the same two dates are applied
        to the rows it produced, whose `day` column does not exist yet."""
        _seed_metric_file(home / ".gitpr" / "metrics", payload={
            "timestamp": "2026-01-15T10:30:00", "command": "commit",
            "status": "success", "provider": "gemini", "repo": OWNER_REPO,
            "branch": "main",
        })

        assert self._loaded(since="2026-02-01") == []
        assert len(self._loaded(until="2026-01-31")) == 1

    # -- the sections --------------------------------------------------

    def test_the_cost_section_shows_what_the_ledger_holds(self, home, monkeypatch):
        monkeypatch.setenv(metrics_price_env_key("m", "INPUT"), "1.0")
        monkeypatch.setenv(metrics_price_env_key("m", "OUTPUT"), "10.0")
        ledger.record_event(
            {
                "command": "commit",
                "status": "success",
                "provider": "gemini",
                "meta": {"model": "m", "prompt_tokens": 1_000_000,
                         "completion_tokens": 1_000_000, "total_tokens": 2_000_000},
            },
            context=GitContext(repo=OWNER_REPO),
        )

        text = self._section("#section_cost")

        assert "2,000,000" in text, "the tokens the terminal counts"
        assert "USD 11.00" in text, "the money the terminal prices"

    def test_the_sections_hold_the_same_numbers_as_the_terminal(self, home):
        """One rendering, two spellings. The dashboard must not be a second
        implementation of the metrics — that is how the two surfaces started
        disagreeing in the first place."""
        log_local_metric(command="linter", status="success", provider="git")
        log_local_metric(command="commit", status="success", provider="deepseek")

        rendered = metrics.cost_lines(cost_report()) + metrics.quality_lines(
            quality_report()
        ) + metrics.provider_lines(provider_breakdown())
        sections = " ".join(
            self._section(widget_id) or ""
            for widget_id in ("#section_cost", "#section_quality",
                              "#section_modules", "#section_providers")
        )

        for _style, text in rendered:
            assert text.strip() in sections

    def test_a_section_with_nothing_to_say_is_hidden(self, home):
        ledger.ensure_ledger(interactive=False)

        assert self._section("#section_cost") is None

    def test_the_window_narrows_the_sections(self, home, monkeypatch):
        monkeypatch.setenv(metrics_price_env_key("m", "INPUT"), "1.0")
        monkeypatch.setenv(metrics_price_env_key("m", "OUTPUT"), "1.0")
        ledger.record_event(
            {"command": "commit", "status": "success", "provider": "gemini",
             "timestamp": "2026-01-10T10:00:00",
             "meta": {"model": "m", "prompt_tokens": 1, "completion_tokens": 0,
                      "total_tokens": 1}},
            context=GitContext(repo=OWNER_REPO),
        )

        assert "Tokens" in self._section("#section_cost", since="2026-01-01")
        assert self._section("#section_cost", since="2026-02-01") is None

    def test_the_bridge_says_the_sections_need_the_ledger(self, home):
        """While the database is absent (a migration the user declined) the
        readers have nothing to read, and the honest answer is to say so —
        not to compute the same four metrics a second way off the file rows."""
        _seed_metric_file(home / ".gitpr" / "metrics")

        notice = self._section("#sections_notice")

        assert "gitpr metrics migrate" in notice
        assert self._section("#section_cost") is None

    @classmethod
    def _section(cls, widget_id, repo_filter=None, since=None, until=None,
                 cycle=None):
        """One section's rendered text, or None when it is not displayed.

        The markup is parsed the way the screen parses it, so what is asserted
        on is what the reader ends up seeing — a model name carrying a bracket
        would otherwise pass a test the screen itself fails.

        The cycle reader asks the forge, and the home fixture does not hide the
        real ``~/.gitpr/.env`` from ``load_dotenv`` — so without the stub below
        this suite would query the developer's actual repository with their
        actual token. It is replaced by an offline answer here, and the one
        test that cares about the section passes its own through ``cycle``.
        """
        offline = metrics._cycle_unavailable("offline in tests")

        async def run():
            from textual.content import Content
            from textual.widgets import Static

            from src.ui.metrics_app import MetricsApp

            app = MetricsApp(repo_filter=repo_filter, since=since, until=until)
            async with app.run_test() as pilot:
                await pilot.pause()
                await app.workers.wait_for_complete()
                await pilot.pause()
                widget = app.query_one(widget_id, Static)
                if not widget.display:
                    return None
                return str(Content.from_markup(str(widget.content)))

        with patch("src.ui.metrics_app.cycle_report",
                   return_value=cycle or offline):
            return asyncio.run(run())

    def test_the_cycle_section_renders_in_the_dashboard(self, home):
        """The dashboard draws the same lines the terminal prints — the cycle
        included, though it is the one section that does not read the ledger."""
        cycle = {
            "status": metrics.CYCLE_OK, "reason": "", "provider": "github",
            "repo": OWNER_REPO, "window": "2026-09-01 → 2026-09-30", "count": 2,
            "average_hours": 9.0, "median_hours": 9.0,
            "slowest": [{"number": 7, "hours": 12.0}],
        }
        expected = metrics.cycle_lines(cycle)

        rendered = self._section("#section_cycle", cycle=cycle)

        for _style, text in expected:
            assert text.strip() in rendered


# ---------------------------------------------------------------------------
# The schema contract
# ---------------------------------------------------------------------------


class TestSchema:
    def test_a_new_database_is_stamped_with_the_schema_version(self, home):
        ledger.ensure_ledger(interactive=False)

        with sqlite3.connect(str(ledger.get_ledger_path())) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == (
                ledger.SCHEMA_VERSION
            )

    def test_a_newer_database_is_refused_before_anything_is_written(self, home):
        """A bundle from the future must not leave the local file half-migrated."""
        path = ledger.get_ledger_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(path)) as conn:
            conn.execute(f"PRAGMA user_version = {ledger.SCHEMA_VERSION + 1}")

        with pytest.raises(ledger.LedgerVersionError) as excinfo:
            with ledger.connect():
                pytest.fail("the body must never run against a newer database")

        assert excinfo.value.found == ledger.SCHEMA_VERSION + 1
        assert excinfo.value.supported == ledger.SCHEMA_VERSION

    def test_the_row_has_every_column_the_queries_read(self, home):
        log_local_metric(command="commit", status="success")
        row = _rows()[0]

        for column in (
            "id",
            "timestamp",
            "day",
            "command",
            "status",
            "provider",
            "model",
            "tokens_actual",
            "duration_ms",
            "repo",
            "branch",
            "author_name",
            "source",
            "exported_at",
        ):
            assert column in row.keys(), column

    def test_a_fresh_row_is_not_marked_exported(self, home):
        log_local_metric(command="commit", status="success")
        assert _rows()[0]["exported_at"] in (None, "")


class TestExtractModules:
    def test_two_segments_of_the_directory(self):
        assert ledger.extract_modules(
            "diff --git a/src/fix/apply_fix.py b/src/fix/apply_fix.py"
        ) == ["src/fix"]

    def test_a_file_at_the_root_is_root(self):
        assert ledger.extract_modules("diff --git a/README.md b/README.md") == ["(root)"]

    def test_duplicates_are_collapsed(self):
        diff = (
            "diff --git a/src/a.py b/src/a.py\n"
            "diff --git a/src/b.py b/src/b.py\n"
        )
        assert ledger.extract_modules(diff) == ["src"]

    def test_no_diff_is_null_not_empty(self):
        assert ledger.extract_modules("") is None
        assert ledger.extract_modules(None) is None

    def test_a_diff_with_no_file_headers_is_null(self):
        assert ledger.extract_modules("+ a line with no header\n") is None

    def test_renames_are_read_from_the_new_path(self):
        assert ledger.extract_modules(
            "diff --git a/old/x.py b/new/y.py"
        ) == ["new"]


class TestCost:
    """Money exists only where a rate does (R5.3).

    The price table ships empty on purpose: list prices change while a ledger
    does not, and a stale rate rendered as currency cannot be told apart from a
    bill. What is delivered is the mechanism — the rates come from the
    environment, and a model nobody priced is reported in tokens alone.
    """

    @staticmethod
    def _priced(monkeypatch, model, input_rate, output_rate):
        monkeypatch.setenv(metrics_price_env_key(model, "INPUT"), str(input_rate))
        monkeypatch.setenv(metrics_price_env_key(model, "OUTPUT"), str(output_rate))

    @staticmethod
    def _row(model, prompt, completion, provider="gemini"):
        ledger.record_event(
            {
                "command": "commit",
                "status": "success",
                "provider": provider,
                "meta": {
                    "model": model,
                    "prompt_tokens": prompt,
                    "completion_tokens": completion,
                    "total_tokens": prompt + completion,
                },
            },
            context=GitContext(repo=OWNER_REPO, branch="main", author_name="Ana"),
        )

    def test_without_a_rate_the_tokens_are_still_counted(self, home, monkeypatch):
        monkeypatch.delenv(metrics_price_env_key("m", "INPUT"), raising=False)
        self._row("m", 1000, 500)

        report = cost_report()

        assert report["models"][0]["tokens"] == 1500
        assert report["models"][0]["cost"] is None
        assert report["total"] is None
        assert report["unpriced"] == ["m"]

    def test_a_configured_rate_prices_the_tokens(self, home, monkeypatch):
        self._priced(monkeypatch, "m", 1.0, 10.0)  # per million tokens
        self._row("m", 1_000_000, 1_000_000)

        report = cost_report()

        assert report["models"][0]["cost"] == pytest.approx(11.0)
        assert report["total"] == pytest.approx(11.0)
        assert report["unpriced"] == []

    def test_an_estimated_row_is_not_priced_at_a_guess(self, home, monkeypatch):
        """Only a real count carries the prompt/completion split a price needs,
        and an estimate is not what the provider billed."""
        self._priced(monkeypatch, "gemini-pro-latest", 1.0, 10.0)
        ledger.record_event(
            {
                "command": "commit",
                "status": "success",
                "provider": "gemini",
                "tokens_estimated": 900,
            },
            context=GitContext(repo=OWNER_REPO),
        )

        report = cost_report()

        assert report["models"][0]["tokens"] == 900
        assert report["models"][0]["cost"] is None
        # No model was recorded, so the provider is what can be named.
        assert report["unpriced"] == ["gemini"]

    def test_a_local_provider_costs_zero_without_a_rate(self, home):
        self._row("llama3", 400, 100, provider="ollama")

        report = cost_report()

        assert report["models"][0]["cost"] == 0.0
        assert report["total"] == 0.0
        assert report["unpriced"] == []

    def test_a_row_that_spent_no_tokens_is_not_a_cost_row(self, home):
        """The linter spends nothing; listing it beside the models would pad
        the section with rows that cannot be spent on."""
        log_local_metric(command="linter", status="success", linter_errors=0)

        assert cost_report()["models"] == []

    def test_the_total_says_when_it_leaves_models_out(self, home, monkeypatch):
        """A sum of the priced rows is not the bill, and the report has to
        make the difference visible rather than let the number read as one."""
        self._priced(monkeypatch, "priced", 1.0, 0.0)
        self._row("priced", 1_000_000, 0)
        self._row("unknown", 500_000, 0)

        report = cost_report()

        assert report["total"] == pytest.approx(1.0)
        assert report["unpriced"] == ["unknown"]

    def test_half_a_price_is_not_a_price(self, home, monkeypatch):
        """Pricing the output at an unconfigured zero would understate the
        bill, so both rates are required or neither is used."""
        monkeypatch.setenv(metrics_price_env_key("m", "INPUT"), "1.0")
        monkeypatch.delenv(metrics_price_env_key("m", "OUTPUT"), raising=False)
        self._row("m", 1000, 1000)

        assert cost_report()["models"][0]["cost"] is None

    def test_the_currency_defaults_to_the_built_in_tables_and_can_be_changed(
        self, home, monkeypatch
    ):
        """The default label has to be the currency the built-in rates are
        published in, or an unconfigured machine prints dollar rates as reais."""
        monkeypatch.delenv("GITPR_METRICS_CURRENCY", raising=False)
        assert cost_report()["currency"] == "USD"

        monkeypatch.setenv("GITPR_METRICS_CURRENCY", "BRL")
        assert cost_report()["currency"] == "BRL"

    def test_a_built_in_rate_prices_a_known_model(self, home, monkeypatch):
        """The cost section says something on a machine nobody configured."""
        monkeypatch.delenv("GITPR_METRICS_CURRENCY", raising=False)
        self._row("deepseek-v4-flash", 1_000_000, 1_000_000)

        report = cost_report()

        assert report["models"][0]["cost"] == pytest.approx(0.14 + 0.28)
        assert report["total"] == pytest.approx(0.42)
        assert report["unpriced"] == []

    def test_a_configured_rate_wins_over_the_built_in_one(self, home, monkeypatch):
        monkeypatch.delenv("GITPR_METRICS_CURRENCY", raising=False)
        self._priced(monkeypatch, "deepseek-v4-flash", 1.0, 0.0)
        self._row("deepseek-v4-flash", 1_000_000, 0)

        assert cost_report()["total"] == pytest.approx(1.0)

    def test_a_built_in_rate_steps_aside_for_another_currency(self, home, monkeypatch):
        """A dollar rate in a report labeled in reais is a wrong number, so the
        model reports tokens and the .env hint instead."""
        monkeypatch.setenv("GITPR_METRICS_CURRENCY", "BRL")
        self._row("deepseek-v4-flash", 1_000_000, 1_000_000)

        report = cost_report()

        assert report["models"][0]["cost"] is None
        assert report["total"] is None
        assert report["unpriced"] == ["deepseek-v4-flash"]

    def test_prices_are_grouped_per_model(self, home, monkeypatch):
        self._priced(monkeypatch, "small", 1.0, 1.0)
        self._priced(monkeypatch, "big", 0.0, 0.0)
        self._row("small", 1_000_000, 0)
        self._row("small", 1_000_000, 0)
        self._row("big", 800, 200)

        report = cost_report()

        assert [m["model"] for m in report["models"]] == ["small", "big"]
        assert report["models"][0]["cost"] == pytest.approx(2.0)
        assert report["models"][1]["cost"] == 0.0

    def test_the_backfill_is_not_a_cost(self, home, monkeypatch):
        """A reconstruction counts distinct prompts, not executions: adding it
        to the bill would charge for work that may have run many times."""
        self._priced(monkeypatch, "m", 1.0, 0.0)
        ledger.record_event(
            {
                "command": "commit",
                "status": "success",
                "provider": "gemini",
                "meta": {"model": "m", "prompt_tokens": 1_000_000},
            },
            source=ledger.SOURCE_BACKFILL,
            context=GitContext(repo=OWNER_REPO),
        )

        report = cost_report()

        assert report["models"] == []
        assert report["total"] is None

    def test_the_window_narrows_the_cost(self, home, monkeypatch):
        self._priced(monkeypatch, "m", 1.0, 0.0)
        _write_on("2026-01-10")
        ledger.record_event(
            {
                "command": "commit", "status": "success", "provider": "gemini",
                "timestamp": "2026-02-10T10:00:00",
                "meta": {"model": "m", "prompt_tokens": 1_000_000},
            },
            context=GitContext(repo=OWNER_REPO),
        )

        assert cost_report(since="2026-02-01")["total"] == pytest.approx(1.0)

    def test_the_env_key_is_the_model_name_normalized(self):
        assert (
            metrics_price_env_key("gemini-pro-latest", "INPUT")
            == "GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_INPUT"
        )
        assert (
            metrics_price_env_key("deepseek.v4/pro", "OUTPUT")
            == "GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT"
        )


class TestModuleDebt:
    """Debt by module — the metric the concept document promised and the
    ledger only became able to answer once the event carried its paths."""

    def test_an_execution_counts_once_under_each_module_it_touched(self, home):
        log_local_metric(
            command="commit", status="success",
            modules=["src/ui", "src/fix"], tokens_estimated=10,
        )

        debt = module_debt()

        assert [m["module"] for m in debt["modules"]] == ["src/fix", "src/ui"]
        assert all(m["executions"] == 1 for m in debt["modules"])

    def test_the_modules_sum_by_work_done(self, home):
        for _ in range(2):
            log_local_metric(
                command="commit", status="success",
                modules=["src/ui"], tokens_estimated=5,
            )
        log_local_metric(
            command="review", status="success", modules=["src/fix"], tokens_estimated=7
        )

        debt = module_debt()

        assert debt["modules"][0] == {
            "module": "src/ui", "executions": 2, "tokens": 10, "duration_ms": 0
        }

    def test_a_row_without_a_diff_is_not_attributed_to_a_module(self, home):
        """The linter, blame and the hooks have no paths in hand; crediting
        them to a module they never touched would invent the data."""
        log_local_metric(command="linter", status="success", linter_errors=0)
        log_local_metric(command="commit", status="success", modules=["src/ui"])

        debt = module_debt()

        assert debt["unmapped"] == {"executions": 1, "tokens": 0}
        assert len(debt["modules"]) == 1

    def test_a_modules_cell_that_is_not_a_list_is_ignored(self, home):
        log_local_metric(command="commit", status="success", modules="src/ui")

        assert module_debt()["unmapped"]["executions"] == 1

    def test_the_window_narrows_the_debt(self, home):
        _write_on("2026-01-10")
        ledger.record_event(
            {
                "command": "commit", "status": "success",
                "timestamp": "2026-02-10T10:00:00", "modules": ["src/ui"],
            },
            context=GitContext(repo=OWNER_REPO),
        )

        assert [m["module"] for m in module_debt(since="2026-02-01")["modules"]] == ["src/ui"]


class TestProviderBreakdown:
    def test_providers_and_models_are_listed_most_used_first(self, home):
        for _ in range(2):
            log_command_metric(command="commit", provider="gemini", meta={"model": "pro"})
        log_command_metric(command="review", provider="deepseek", meta={"model": "flash"})

        breakdown = provider_breakdown()

        assert [p["provider"] for p in breakdown["providers"]] == ["gemini", "deepseek"]
        assert [m["model"] for m in breakdown["models"]] == ["pro", "flash"]

    def test_local_work_is_a_row_of_its_own(self, home):
        """`local` says no AI was involved — the linter, the hooks. It is an
        answer to "who did this work", not an unknown to be dropped."""
        log_local_metric(command="linter", status="success")

        assert provider_breakdown()["providers"][0]["provider"] == "local"

    def test_tokens_and_durations_come_along(self, home):
        log_command_metric(
            command="commit", provider="gemini", duration_ms=1200,
            meta={"model": "pro", "total_tokens": 300},
        )

        provider = provider_breakdown()["providers"][0]

        assert provider["tokens"] == 300
        assert provider["duration_ms"] == 1200


class TestQualityReport:
    def test_the_linter_pass_rate_counts_only_linter_runs(self, home):
        log_local_metric(command="linter", status="success", linter_errors=0,
                         linter_warnings=2)
        log_local_metric(command="linter", status="error", linter_errors=3)
        log_local_metric(command="commit", status="success")

        linter = quality_report()["linter"]

        assert linter == {
            "runs": 2, "passed": 1, "warnings": 2, "pass_rate": 0.5
        }

    def test_a_window_without_a_linter_run_has_no_rate(self, home):
        """0 would be a claim about runs that did not happen."""
        assert quality_report()["linter"]["pass_rate"] is None

    def test_the_map_reduce_rate_counts_the_calls_the_provider_answered(self, home):
        log_command_metric(
            command="fullreview", provider="gemini", map_reduce_triggered=True,
            meta={"model": "pro", "total_tokens": 100},
        )
        log_command_metric(
            command="commit", provider="gemini",
            meta={"model": "pro", "total_tokens": 50},
        )

        rate = quality_report()["map_reduce"]

        assert rate["answered"] == 2
        assert rate["chunked"] == 1
        assert rate["rate"] == 0.5

    def test_a_cache_hit_is_not_a_call_that_did_not_chunk(self, home):
        """It never reached the provider, so it cannot have been chunked —
        and counting it as "not chunked" would report a rate over calls that
        never happened."""
        log_command_metric(command="commit", provider="gemini", cache_hit=True)
        log_command_metric(
            command="fullreview", provider="gemini", map_reduce_triggered=True,
            meta={"model": "pro", "total_tokens": 100},
        )

        rate = quality_report()["map_reduce"]

        assert rate["answered"] == 1
        assert rate["rate"] == 1.0

    def test_the_window_narrows_both_rates(self, home):
        _write_on("2026-01-10")

        quality = quality_report(since="2026-02-01")

        assert quality["linter"]["runs"] == 0
        assert quality["map_reduce"]["answered"] == 0


class TestTheWindowOnTheCommandLine:
    """Regression (Click): a group parses its own options *before* the
    subcommand name, so `gitpr metrics --days 7 export` would set a window only
    the group callback ever sees. The flags are declared on each reading
    sub-action instead — this is what notices if one of them loses them."""

    def test_the_summary_takes_the_three_flags(self):
        result = CliRunner().invoke(cli, ["metrics", "-h"])

        assert result.exit_code == 0, result.output
        for flag in ("--days", "--since", "--until"):
            assert flag in result.output

    @pytest.mark.parametrize("action", ["export", "dashboard"])
    def test_the_reading_actions_take_them_too(self, action):
        result = CliRunner().invoke(cli, ["metrics", action, "-h"])

        assert result.exit_code == 0, result.output
        for flag in ("--days", "--since", "--until"):
            assert flag in result.output

    def test_the_flag_reaches_the_reader(self, home, tmp_path, monkeypatch):
        """The window is not decoration: an empty one exports nothing, and the
        row it left out is still there for a wider call.

        Asserted on the files, not on the printed sentence: the sentence is a
        translation, and the suite's language is whatever the last test left
        behind.
        """
        monkeypatch.chdir(tmp_path)
        _write_on("2026-01-10")

        result = CliRunner().invoke(cli, ["metrics", "export", "--since", "2026-02-01"])

        assert result.exit_code == 0, result.output
        assert list(tmp_path.glob("**/*.csv")) == []

        wider = CliRunner().invoke(cli, ["metrics", "export"])
        assert wider.exit_code == 0, wider.output
        assert len(list(tmp_path.glob("**/*.csv"))) == 1


class _FakeForge:
    """A forge that answers with the pull requests it was handed.

    ``supports_merged_dates`` is a class attribute on the real providers and is
    declared *before* the network call, so a forge that cannot answer must
    never be asked — which is half of what these tests assert.
    """

    name = "github"
    supports_merged_dates = True

    def __init__(self, pulls=(), error=None, supports_merged_dates=True):
        self.pulls = list(pulls)
        self.error = error
        self.supports_merged_dates = supports_merged_dates
        self.asked = []

    def parse_repo_ref(self, remote_url):
        return RepoRef(
            raw=remote_url, workspace="owner", name="repo", provider=self.name
        )

    def list_pull_requests(self, repo, state="all", since=None, until=None):
        self.asked.append((state, since, until))
        if self.error:
            raise self.error
        return self.pulls


def _pull(number, created, merged):
    return PullRequestResult(
        id=number, url=f"https://x/pull/{number}", number=number, state="merged",
        source_branch="b", target_branch="main", provider="github",
        created_at=created, merged_at=merged,
    )


@pytest.fixture
def forge(monkeypatch):
    """Makes cycle_report read the forge it is handed, with an origin remote."""
    monkeypatch.setattr(metrics, "_origin_remote", lambda: "https://github.com/o/r.git")

    def _install(fake):
        monkeypatch.setattr(
            "src.infrastructure.scm.factory.resolve_scm_provider", lambda config: fake
        )
        monkeypatch.setattr("src.config.get_scm_settings", lambda: {})
        return fake

    return _install


class TestCycleReport:
    """The one metric the forge answers: it must degrade, never guess."""

    def test_average_and_median_come_from_the_merged_interval(self, forge):
        fake = forge(_FakeForge([
            _pull(1, "2026-09-01T00:00:00Z", "2026-09-01T06:00:00Z"),   # 6 h
            _pull(2, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z"),   # 24 h
            _pull(3, "2026-09-01T00:00:00Z", "2026-09-02T18:00:00Z"),   # 42 h
        ]))

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["status"] == metrics.CYCLE_OK
        assert cycle["count"] == 3
        assert cycle["average_hours"] == 24.0
        assert cycle["median_hours"] == 24.0
        # The slowest is what a reader can act on, so it comes first.
        assert [p["number"] for p in cycle["slowest"]] == [3, 2, 1]

    def test_the_forge_is_asked_for_merged_pull_requests_in_the_window(self, forge):
        fake = forge(_FakeForge())

        metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert fake.asked == [("merged", "2026-09-01", "2026-09-30")]

    def test_a_bare_call_reads_a_month_and_says_so(self, forge):
        """An unbounded listing is not what "no window" can mean here: it would
        page a repository's whole history over the network."""
        fake = forge(_FakeForge([_pull(1, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z")]))

        cycle = metrics.cycle_report()

        state, since, until = fake.asked[0]
        assert since and until
        assert cycle["window"] == "last 30 days"

    def test_a_pull_request_without_a_merge_date_is_not_counted_as_fast(self, forge):
        """An interval nobody published is not a short one. Bitbucket publishes
        no merge date at all, so this is the shape that reaches here."""
        forge(_FakeForge([
            _pull(1, "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z"),
            _pull(2, "2026-09-01T00:00:00Z", ""),
        ]))

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["count"] == 1

    def test_a_window_with_nothing_merged_is_an_answer(self, forge):
        forge(_FakeForge())

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["status"] == metrics.CYCLE_EMPTY
        assert cycle["average_hours"] is None

    def test_a_negative_interval_is_dropped_not_averaged(self, forge):
        """A merge that precedes its own creation is a clock the forge got
        wrong, not a cycle of minus three hours."""
        forge(_FakeForge([
            _pull(1, "2026-09-02T00:00:00Z", "2026-09-01T00:00:00Z"),
            _pull(2, "2026-09-01T00:00:00Z", "2026-09-01T12:00:00Z"),
        ]))

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["count"] == 1
        assert cycle["average_hours"] == 12.0

    def test_a_forge_that_publishes_no_merge_date_is_never_asked(self, forge):
        fake = forge(_FakeForge(supports_merged_dates=False))

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["status"] == metrics.CYCLE_UNSUPPORTED
        assert fake.asked == []

    def test_a_forge_error_becomes_a_reason_not_a_traceback(self, forge):
        forge(_FakeForge(error=ScmProviderError("github", 401, "Bad credentials")))

        cycle = metrics.cycle_report(since="2026-09-01", until="2026-09-30")

        assert cycle["status"] == metrics.CYCLE_UNAVAILABLE
        assert "Bad credentials" in cycle["reason"]

    def test_without_an_origin_remote_there_is_no_forge_to_ask(self, monkeypatch):
        monkeypatch.setattr(metrics, "_origin_remote", lambda: "")

        cycle = metrics.cycle_report()

        assert cycle["status"] == metrics.CYCLE_UNAVAILABLE
        assert "origin" in cycle["reason"]


class TestCycleLines:
    """One rendering, so the four answers cannot be confused on screen."""

    def test_the_header_names_the_repository_and_the_window(self, forge):
        forge(_FakeForge([_pull(1, "2026-09-01T00:00:00Z", "2026-09-01T06:00:00Z")]))

        lines = metrics.cycle_lines(
            metrics.cycle_report(since="2026-09-01", until="2026-09-30")
        )

        assert "owner/repo" in lines[0][1]
        assert "2026-09-01 → 2026-09-30" in lines[0][1]

    def test_the_unit_follows_the_value(self):
        """A single unit cannot serve this metric: on a repository whose pull
        requests are merged seconds apart, "0.0 days" is true and reads as a
        broken panel."""
        assert metrics._duration(16 / 3600) == "16 s"
        assert metrics._duration(0.5) == "30 min"
        assert metrics._duration(6) == "6.0 h"
        assert metrics._duration(72) == "3.0 d"

    def test_an_empty_window_says_so_instead_of_showing_zero(self, forge):
        forge(_FakeForge())

        lines = metrics.cycle_lines(metrics.cycle_report(since="2026-09-01"))

        assert any("No pull request was merged" in text for _, text in lines)

    def test_an_unavailable_metric_carries_its_reason(self, monkeypatch):
        monkeypatch.setattr(metrics, "_origin_remote", lambda: "")

        lines = metrics.cycle_lines(metrics.cycle_report())

        assert lines[1][0] == metrics.WARN
        assert "origin" in lines[1][1]


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
