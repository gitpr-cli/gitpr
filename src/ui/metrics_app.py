"""
Metrics Dashboard TUI - displays telemetry data in an interactive terminal UI.

Usage: gitpr --metrics --dashboard
"""
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Vertical, Horizontal
from textual.binding import Binding
import json
import os
from datetime import datetime
from collections import Counter

from src.i18n import __


class MetricsApp(App):
    """Interactive terminal dashboard for local telemetry data."""

    TITLE = __("GitPR - Metrics Dashboard")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
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

    def __init__(self, metrics_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.metrics_dir = metrics_dir or os.path.join(
            os.path.expanduser("~"), ".gitpr", "metrics"
        )
        self.events = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static("", id="summary")

        with Vertical(id="table_container"):
            yield DataTable(id="events_table")

        yield Static("", id="status_bar")
        yield Footer()

    def on_mount(self) -> None:
        """Load data and populate the table."""
        self._load_metrics()
        self._populate_table()
        self._update_summary()

    def _load_metrics(self) -> None:
        """Scan the metrics directory for all event JSON files."""
        self.events = []
        if not os.path.isdir(self.metrics_dir):
            return

        for root, dirs, files in os.walk(self.metrics_dir):
            for fname in files:
                if fname.endswith(".json") and not fname.startswith("config"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            self.events.append(json.load(f))
                    except Exception:
                        pass

        # Sort by timestamp, newest first
        self.events.sort(
            key=lambda e: e.get("timestamp", ""),
            reverse=True,
        )

    def _populate_table(self) -> None:
        """Fill the DataTable with the loaded events."""
        table = self.query_one("#events_table", DataTable)
        table.clear()

        if not self.events:
            table.add_column(__("No metrics data found."))
            return

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

        for evt in self.events[:100]:  # Show last 100 events
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
        """Update the summary bar with aggregate stats."""
        summary = self.query_one("#summary", Static)
        status = self.query_one("#status_bar", Static)

        if not self.events:
            summary.update(__("No metrics data found in ~/.gitpr/metrics/"))
            status.update(
                __("Use 'gitpr --metrics --export' to consolidate data for dashboards.")
            )
            return

        total = len(self.events)
        commands = Counter(e.get("command", "?") for e in self.events)
        providers = Counter(e.get("provider", "?") for e in self.events)
        total_tokens = sum(e.get("tokens_estimated", 0) for e in self.events)
        errors = sum(1 for e in self.events if e.get("status") == "error")

        top_cmds = ", ".join(f"{cmd}({n})" for cmd, n in commands.most_common(3))
        top_prov = ", ".join(f"{p}({n})" for p, n in providers.most_common(2))

        lines = [
            f"{__('Total events')}: {total}  |  {__('Errors')}: {errors}  |  {__('Total tokens')}: {total_tokens:,}",
            f"{__('Top commands')}: {top_cmds}",
            f"{__('Providers')}: {top_prov}",
        ]
        summary.update("\n".join(lines))

        # Show the newest event timestamp
        newest = self.events[0].get("timestamp", "")[:19].replace("T", " ")
        oldest = self.events[-1].get("timestamp", "")[:19].replace("T", " ")
        status.update(
            f"{__('Range')}: {oldest} → {newest}  |  {__('Showing')} {min(total, 100)} {__('of')} {total} {__('events')}"
        )

    def action_refresh(self) -> None:
        """Reload data from disk."""
        self._load_metrics()
        self._populate_table()
        self._update_summary()


def launch_metrics_dashboard(metrics_dir=None):
    """Entry point: launches the metrics TUI."""
    app = MetricsApp(metrics_dir=metrics_dir)
    app.run()
