"""
Metrics Dashboard TUI - displays telemetry data in an interactive terminal UI.

Usage: gitpr --dashboard
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
import json
import os
from collections import Counter

from src.i18n import __
from src.metrics import load_cache_token_summary


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
        self.events = []
        self.cache_summary = {}
        self._columns_set = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        repo_text = self.repo_filter or __("All repositories")
        yield Static(f"📁 {__('Repository')}: {repo_text}", id="repo_label")

        yield Static("", id="summary")

        with Vertical(id="table_container"):
            yield DataTable(id="events_table")

        yield Static("", id="status_bar")
        yield Footer()

    def on_mount(self) -> None:
        """Load data and populate the table on first mount."""
        self._setup_columns()
        self._load_metrics()
        self._populate_table()
        self._update_summary()

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

    def _load_metrics(self) -> None:
        """Scan the metrics directory for all event JSON files, filtered by repo."""
        self.events = []
        if not os.path.isdir(self.metrics_dir):
            self.cache_summary = {}
            return

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
                            self.events.append(data)
                    except Exception:
                        pass

        # Filter by repo
        if self.repo_filter:
            self.events = [e for e in self.events if e.get("repo", "") == self.repo_filter]

        # Sort by timestamp, newest first
        self.events.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True,
        )

        # Load cache summary for enriched totals
        self.cache_summary = load_cache_token_summary(self.repo_filter)

    def _populate_table(self) -> None:
        """Fill the DataTable with loaded events (replaces all rows, keeps columns)."""
        table = self.query_one("#events_table", DataTable)
        table.clear()

        if not self.events:
            table.add_row(
                __("No metrics data found."),
                __("Run some GitPR commands (commit, review, linter)"),
                __("to generate telemetry. Then refresh with F5."),
                "", "", ""
            )
            return

        for evt in self.events[:100]:
            ts = evt.get("timestamp", "")[:19].replace("T", " ")
            table.add_row(
                ts,
                evt.get("command", ""),
                evt.get("status", ""),
                evt.get("provider", ""),
                str(evt.get("tokens_estimated", 0)),
                str(evt.get("duration_ms", 0)),
            )

    def _update_summary(self) -> None:
        """Update the summary bar with aggregate stats from events + cache."""
        summary = self.query_one("#summary", Static)
        status = self.query_one("#status_bar", Static)

        if not self.events and not self.cache_summary.get("file_count", 0):
            summary.update(__("No metrics data found in ~/.gitpr/metrics/"))
            status.update(
                __("Use GitPR commands normally — metrics are logged automatically. Press F5 to refresh.")
            )
            return

        total = len(self.events)
        commands = Counter(e.get("command", "?") for e in self.events)
        providers = Counter(e.get("provider", "?") for e in self.events)
        total_tokens = sum(e.get("tokens_estimated", 0) for e in self.events)
        errors = sum(1 for e in self.events if e.get("status") == "error")

        # Merge cache action counts into commands
        cache_actions = self.cache_summary.get("by_action", {})
        for action, info in cache_actions.items():
            if info["count"] > 0:
                commands[action] += info["count"]

        cache_tokens = self.cache_summary.get("total_tokens", 0)
        cache_files = self.cache_summary.get("file_count", 0)

        top_cmds = ", ".join(f"{cmd}({n})" for cmd, n in commands.most_common(3))
        top_prov = ", ".join(f"{p}({n})" for p, n in providers.most_common(2))

        lines = [
            f"{__('Total events')}: {total}  |  {__('Errors')}: {errors}",
            f"{__('Tokens (events)')}: {total_tokens:,}  |  {__('Tokens (cache)')}: {cache_tokens:,}  |  {__('Cache files')}: {cache_files}",
            f"{__('Top commands')}: {top_cmds}",
            f"{__('Providers')}: {top_prov}",
        ]
        summary.update("\n".join(lines))

        # Status bar: time range + row count
        if self.events:
            newest = self.events[0].get("timestamp", "")[:19].replace("T", " ")
            oldest = self.events[-1].get("timestamp", "")[:19].replace("T", " ")
            status.update(
                f"{__('Range')}: {oldest} → {newest}  |  {__('Showing')} {min(total, 100)} {__('of')} {total} {__('events')}"
            )
        else:
            status.update(
                f"{__('Cache files found')}: {cache_files}  |  {__('Press F5 to refresh')}"
            )

    def action_refresh(self) -> None:
        """Reload data from disk (F5). Only clears rows, not columns."""
        self._load_metrics()
        self._populate_table()
        self._update_summary()


def launch_metrics_dashboard(metrics_dir=None, repo_filter=None):
    """Entry point: launches the metrics TUI."""
    app = MetricsApp(metrics_dir=metrics_dir, repo_filter=repo_filter)
    app.run()
