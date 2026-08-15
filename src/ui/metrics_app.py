"""
Metrics Dashboard TUI - displays telemetry data in an interactive terminal UI.

Usage: gitpr --dashboard
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, ProgressBar
from textual.containers import Vertical
from textual.binding import Binding
import json
import os
from collections import Counter

from src.i18n import __
from src.metrics import (
    scan_cache_files_for_dashboard,
    load_processed_cache_list,
    save_processed_cache_list,
    get_processed_cache_file,
)


class MetricsApp(App):
    """Interactive terminal dashboard for local telemetry data."""

    TITLE = __("GitPR - Metrics Dashboard")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #repo_label {
        padding: 0 2;
        color: $accent;
        text-style: bold;
        margin: 0 2;
    }
    #summary {
        padding: 1 2;
        background: $surface;
        border: solid $primary;
        margin: 1 2;
    }
    #table_container {
        height: 1fr;
        margin: 0 2;
    }
    #status_bar {
        padding: 0 2;
        color: $text-muted;
    }
    #loading_overlay {
        display: none;
        align: center middle;
        background: $surface;
        border: solid $accent;
        padding: 3 4;
        margin: 2 4;
    }
    #loading_label {
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    #scan_progress {
        width: 100%;
        display: none;
    }
    """

    BINDINGS = [
        Binding("f5", "refresh", __("Refresh")),
        Binding("escape", "quit", __("Exit")),
    ]

    def __init__(self, metrics_dir=None, repo_filter=None, **kwargs):
        super().__init__(**kwargs)
        self.metrics_dir = metrics_dir or os.path.join(
            os.path.expanduser("~"), ".gitpr", "metrics"
        )
        self.repo_filter = repo_filter
        self.repo_key = repo_filter or "all_repos"
        self.events = []

        # Load last_scan from the per-repo processed-cache file
        self._last_scan_date = None
        try:
            state = load_processed_cache_list(self.repo_key)
            # load_processed_cache_list returns a set; we need the last_scan field
            state_file = get_processed_cache_file(self.repo_key)
            if os.path.exists(state_file):
                import json as _json

                with open(state_file, "r", encoding="utf-8", errors="replace") as f:
                    raw = _json.load(f)
                self._last_scan_date = raw.get("last_scan", None)
        except Exception:
            pass

        self._columns_set = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        repo_text = self.repo_filter or __("All repositories")
        yield Static(f"\U0001f4c1 {__('Repository')}: {repo_text}", id="repo_label")

        yield Static("", id="summary")

        with Vertical(id="table_container"):
            yield DataTable(id="events_table")

        yield Static("", id="status_bar")

        # Loading overlay (hidden until scan starts)
        with Vertical(id="loading_overlay"):
            yield Static(__("Scanning cache files..."), id="loading_label")
            yield ProgressBar(total=100, show_eta=False, id="scan_progress")

        yield Footer()

    def on_mount(self) -> None:
        """Start the scan on first mount."""
        self._setup_columns()
        self._start_scan()

    def _setup_columns(self) -> None:
        """Set up table columns once (not re-added on refresh)."""
        if self._columns_set:
            return
        table = self.query_one("#events_table", DataTable)
        columns = [
            __("Timestamp"),
            __("Command"),
            __("Status"),
            __("Provider"),
            __("Tokens"),
            __("Duration (ms)"),
        ]
        for col in columns:
            table.add_column(col)
        self._columns_set = True

    # ------------------------------------------------------------------
    # Scan orchestration
    # ------------------------------------------------------------------

    def _start_scan(self, incremental: bool = False) -> None:
        """Show the loading overlay and launch the background scan worker.

        Args:
            incremental: If True (F5 refresh), only scan files newer than
                         last_scan. New rows are merged with existing data.
                         If False (initial mount), scan all files since Jan 1st.
        """
        overlay = self.query_one("#loading_overlay")
        overlay.display = True
        progress = self.query_one("#scan_progress", ProgressBar)
        progress.display = True
        progress.update(total=100, progress=0)

        # Determine since_date
        if incremental and self._last_scan_date:
            since_date = self._last_scan_date[:10]  # YYYY-MM-DD
        else:
            since_date = None  # scan_cache_files_for_dashboard defaults to Jan 1st

        self.run_worker(
            lambda: self._scan_worker(since_date=since_date, incremental=incremental),
            thread=True,
        )

    def _scan_worker(self, since_date=None, incremental=False) -> None:
        """Background worker: scans cache files + metric events with progress."""

        # Phase 1: scan cache files
        def progress_cb(done: int, total_count: int):
            self.call_from_thread(self._update_progress, done, total_count)

        cache_rows = scan_cache_files_for_dashboard(
            repo_filter=self.repo_filter,
            progress_cb=progress_cb,
            since_date=since_date,
        )

        # Phase 2: load metric events from ~/.gitpr/metrics/
        event_rows = self._load_metric_events()

        # Merge: event rows enrich cache rows, unmatched events are appended
        rows = self._merge_rows(cache_rows, event_rows)

        self.call_from_thread(self._finish_scan, rows, incremental)

    def _load_metric_events(self) -> list:
        """Walk ~/.gitpr/metrics/ and return event rows (no progress bar)."""
        events = []
        if not os.path.isdir(self.metrics_dir):
            return events

        for root, dirs, files in os.walk(self.metrics_dir):
            # Skip the export subdirectory
            if "export" in root.replace(self.metrics_dir, "").split(os.sep):
                continue
            for fname in files:
                if fname.endswith(".json") and not fname.startswith("config"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                            data = json.load(f)
                        if isinstance(data, dict):
                            events.append(data)
                    except Exception:
                        pass

        # Filter by repo
        if self.repo_filter:
            events = [e for e in events if e.get("repo", "") == self.repo_filter]

        # Convert to row format
        rows = []
        for evt in events:
            row = {
                "timestamp": (evt.get("timestamp") or "").replace("T", " ")[:19],
                "command": evt.get("command", "unknown"),
                "status": evt.get("status", "success"),
                "provider": evt.get("provider", ""),
                "tokens": evt.get("tokens_estimated", 0),
                "duration_ms": evt.get("duration_ms", 0),
                "repo": evt.get("repo", ""),
                "branch": evt.get("branch", ""),
                "source": "event",
                "md5": "",
                "path": "",
            }
            rows.append(row)

        return rows

    @staticmethod
    def _merge_rows(cache_rows: list, event_rows: list) -> list:
        """Merge cache and event rows, deduplicating by (repo, branch, command, minute).

        When a cache row and an event row match, the event's status/provider/duration
        enrich the cache row. Unmatched event rows are appended as-is.
        """
        if not event_rows:
            return cache_rows

        # Map to normalize action_type → cache folder name for matching
        _action_map = {
            "pr": "pr_desc",
            "commit": "commit",
            "review": "review",
            "fullreview": "review",
            "filereview": "review",
            "issue": "issue",
        }

        # Build lookup for cache rows: (repo, branch, action, minute) → row index
        cache_index = {}
        for i, row in enumerate(cache_rows):
            action = _action_map.get(row.get("command", ""), row.get("command", ""))
            ts = row.get("timestamp", "")[:16]  # YYYY-MM-DD HH:MM
            key = (row.get("repo", ""), row.get("branch", ""), action, ts)
            if key not in cache_index:
                cache_index[key] = i

        used_events = set()
        merged = list(cache_rows)

        for evt in event_rows:
            cmd = evt.get("command", "")
            action = _action_map.get(cmd, cmd)
            ts = evt.get("timestamp", "")[:16]
            key = (evt.get("repo", ""), evt.get("branch", ""), action, ts)

            if key in cache_index:
                idx = cache_index[key]
                # Enrich cache row with event data (status, provider, real duration)
                if evt.get("status"):
                    merged[idx]["status"] = evt["status"]
                if evt.get("provider"):
                    merged[idx]["provider"] = evt["provider"]
                if evt.get("duration_ms", 0) > 0:
                    merged[idx]["duration_ms"] = evt["duration_ms"]
                if evt.get("tokens", 0) > 0 and merged[idx]["tokens"] == 0:
                    merged[idx]["tokens"] = evt["tokens"]
            else:
                # Unmatched event — append as new row
                merged.append(evt)

        # Re-sort by timestamp descending
        merged.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return merged

    def _update_progress(self, done: int, total: int) -> None:
        """Update the progress bar from the worker thread."""
        try:
            progress = self.query_one("#scan_progress", ProgressBar)
            progress.update(total=total, progress=done)
            label = self.query_one("#loading_label", Static)
            label.update(
                __("Scanning cache files... {done} / {total}", done=done, total=total)
            )
        except Exception:
            pass  # Widget may not exist yet or may have been removed

    def _finish_scan(self, rows: list, incremental: bool = False) -> None:
        """Called on the main thread when scanning is complete.

        Args:
            rows: Newly scanned rows.
            incremental: If True, merge with existing events (F5 refresh).
        """
        from datetime import datetime as _dt

        # Hide the loading overlay
        overlay = self.query_one("#loading_overlay")
        overlay.display = False

        if incremental and self.events:
            # Merge: deduplicate by (repo, branch, command, timestamp)
            existing_keys = {
                (
                    r.get("repo", ""),
                    r.get("branch", ""),
                    r.get("command", ""),
                    r.get("timestamp", ""),
                )
                for r in self.events
            }
            new_rows = [
                r
                for r in rows
                if (
                    r.get("repo", ""),
                    r.get("branch", ""),
                    r.get("command", ""),
                    r.get("timestamp", ""),
                )
                not in existing_keys
            ]
            new_count = len(new_rows)
            if new_rows:
                self.events = new_rows + self.events
                self.events.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        else:
            new_count = len(rows)
            self.events = rows

        self._populate_table()
        self._update_summary()

        # Fire-and-forget: save processed cache paths (per-repo)
        cache_paths = [r["path"] for r in rows if r.get("source") == "cache"]
        if cache_paths:
            try:
                save_processed_cache_list(cache_paths, self.repo_key)
            except Exception:
                pass  # Never break the UI for a state-file write

        # Update last_scan date for next incremental refresh
        self._last_scan_date = _dt.now().isoformat()

        # Notify user how many new files were found (F5 only)
        if incremental:
            status = self.query_one("#status_bar", Static)
            status.update(
                f"{__('F5 refresh')}: {new_count} {__('new entries')}  |  {__('Entries')}: {len(self.events)}"
            )

    # ------------------------------------------------------------------
    # Table + summary rendering
    # ------------------------------------------------------------------

    def _populate_table(self) -> None:
        """Fill the DataTable with loaded rows (replaces all rows, keeps columns)."""
        table = self.query_one("#events_table", DataTable)
        table.clear()

        if not self.events:
            table.add_row(
                __("No metrics data found."),
                __("Run some GitPR commands (commit, review, linter)"),
                __("to generate telemetry. Then refresh with F5."),
                "",
                "",
                "",
            )
            return

        for row in self.events:
            ts = row.get("timestamp", "")[:19]
            table.add_row(
                ts,
                row.get("command", ""),
                row.get("status", ""),
                row.get("provider", ""),
                str(row.get("tokens", 0)),
                str(row.get("duration_ms", 0)),
            )

    def _update_summary(self) -> None:
        """Update the summary bar with aggregate stats from scanned rows."""
        summary = self.query_one("#summary", Static)
        status = self.query_one("#status_bar", Static)

        if not self.events:
            summary.update(__("No metrics data found in ~/.gitpr/cache/prompts/"))
            status.update(
                __(
                    "Use GitPR commands normally — metrics are logged automatically. Press F5 to refresh."
                )
            )
            return

        total = len(self.events)
        commands = Counter(r.get("command", "?") for r in self.events)
        total_tokens = sum(r.get("tokens", 0) for r in self.events)
        total_duration_ms = sum(r.get("duration_ms", 0) for r in self.events)
        cache_count = sum(1 for r in self.events if r.get("source") == "cache")

        top_cmds = ", ".join(f"{cmd}({n})" for cmd, n in commands.most_common(3))

        lines = [
            f"{__('Total entries')}: {total}  |  {__('Cache files')}: {cache_count}",
            f"{__('Tokens')}: {total_tokens:,}  |  {__('Total duration')}: {total_duration_ms:,} ms",
            f"{__('Top commands')}: {top_cmds}",
        ]
        summary.update("\n".join(lines))

        # Status bar: time range + entry count
        newest = self.events[0].get("timestamp", "")[:19]
        oldest = self.events[-1].get("timestamp", "")[:19]
        status.update(
            f"{__('Range')}: {oldest} → {newest}  |  {__('Entries')}: {total}"
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_refresh(self) -> None:
        """Reload data from disk (F5). Incremental — only scans files newer than last_scan."""
        self._start_scan(incremental=True)


def launch_metrics_dashboard(metrics_dir=None, repo_filter=None):
    """Entry point: launches the metrics TUI."""
    app = MetricsApp(metrics_dir=metrics_dir, repo_filter=repo_filter)
    app.run()
