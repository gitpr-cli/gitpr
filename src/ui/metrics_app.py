"""
Metrics Dashboard TUI - displays telemetry data in an interactive terminal UI.

Usage: gitpr metrics dashboard

Reads the ledger. The pre-ledger path — walking the AI cache and the event
files, then joining the two by (repo, branch, command, minute) — survives only
as a bridge for the window before the first write creates telemetry.db, and
only ever runs when that file is absent. See src/metrics.py for why the join
was removed rather than fixed.

The screen is the four sections: the overview (the summary bar plus the event
table), the cost, the quality and where the work went, by module and by
provider. The sections are the same lines `gitpr metrics` prints — rendered by
src/metrics.py and spelled in markup here — so neither surface can tell a
different story about one ledger.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, DataTable, ProgressBar
from textual.containers import Vertical, VerticalScroll
from textual.binding import Binding
from collections import Counter
import os

from src import ledger
from src.i18n import __
from src.metrics import (
    TITLE,
    WARN,
    cost_lines,
    cost_report,
    cycle_lines,
    cycle_report,
    module_debt,
    module_lines,
    provider_breakdown,
    provider_lines,
    quality_lines,
    quality_report,
    scan_cache_files_for_dashboard,
    scan_event_files_for_dashboard,
    _ledger_rows_to_display,
)

# The four ledger sections, in the order they are read. Each is one widget,
# fed by the reader and the renderer of the same name in src/metrics.py, and
# each starts hidden — the loader lights up the ones that have something to
# say. ``sections_notice`` stands in for all four while the ledger is absent.
SECTION_IDS = (
    "section_cost",
    "section_quality",
    "section_modules",
    "section_providers",
    "section_cycle",
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
    #sections {
        height: auto;
        max-height: 20;
        margin: 0 2;
    }
    #sections Static {
        height: auto;
        margin-bottom: 1;
        display: none;
    }
    #sections_notice {
        color: $text-muted;
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

    def __init__(self, repo_filter=None, since=None, until=None, **kwargs):
        super().__init__(**kwargs)
        self.repo_filter = repo_filter
        self.since = since
        self.until = until
        self.events = []
        self.using_ledger = ledger.ledger_exists()
        self._columns_set = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        repo_text = self.repo_filter or __("All repositories")
        yield Static(f"\U0001f4c1 {__('Repository')}: {repo_text}", id="repo_label")

        yield Static("", id="summary")

        with VerticalScroll(id="sections"):
            yield Static("", id="sections_notice")
            for section_id in SECTION_IDS:
                yield Static("", id=section_id)

        with Vertical(id="table_container"):
            yield DataTable(id="events_table")

        yield Static("", id="status_bar")

        # Loading overlay (hidden until a scan starts)
        with Vertical(id="loading_overlay"):
            yield Static(__("Scanning cache files..."), id="loading_label")
            yield ProgressBar(total=100, show_eta=False, id="scan_progress")

        yield Footer()

    def on_mount(self) -> None:
        """Load the table on first mount."""
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
    # Loading
    # ------------------------------------------------------------------

    def _start_scan(self) -> None:
        """Show the loading overlay and launch the background worker.

        The ledger is queried on a worker thread too: it keeps the UI
        responsive for a large database and, more importantly, keeps the two
        sources on the same code path so neither can quietly stop being
        exercised.
        """
        overlay = self.query_one("#loading_overlay")
        progress = self.query_one("#scan_progress", ProgressBar)
        self.using_ledger = ledger.ledger_exists()

        if self.using_ledger:
            # Reading a database needs no progress bar, and showing one for an
            # operation measured in milliseconds would only flash.
            overlay.display = False
            progress.display = False
        else:
            overlay.display = True
            progress.display = True
            progress.update(total=100, progress=0)

        self.run_worker(self._scan_worker, thread=True)

    def _scan_worker(self) -> None:
        """Background worker: reads the ledger, or the files while it is absent."""
        if self.using_ledger:
            rows = self._load_from_ledger()
            sections = self._load_sections()
        else:
            rows = self._load_from_files()
            sections = self._load_sections(with_ledger=False)

        self.call_from_thread(self._finish_scan, rows, sections)

    def _load_sections(self, with_ledger: bool = True) -> list:
        """The metric sections, through the readers the terminal also uses.

        Same readers, same lines, only the markup differs: a metric drawn here
        and not in `gitpr metrics` — or the other way round — would be two
        metrics wearing one name, and the two surfaces would start disagreeing
        about the same ledger.

        Runs in the scan worker, which is what makes the cycle affordable here:
        it is the one reader that waits on the network.

        ``with_ledger=False`` is the bridge path, where the four ledger readers
        have nothing to read. The cycle is kept because it does not read the
        ledger at all — it asks the forge — so hiding it there would hide the
        one section that still has an answer.
        """
        scope = {
            "repo_filter": self.repo_filter or None,
            "since": self.since,
            "until": self.until,
        }
        readers = (
            cost_report,
            quality_report,
            module_debt,
            provider_breakdown,
            cycle_report,
        )
        renderers = (
            cost_lines,
            quality_lines,
            module_lines,
            provider_lines,
            cycle_lines,
        )
        sections = list(zip(SECTION_IDS, readers, renderers))
        if not with_ledger:
            sections = sections[-1:]
        return [
            (f"#{section_id}", renderer(reader(**scope)))
            for section_id, reader, renderer in sections
        ]

    def _load_from_ledger(self) -> list:
        """Rows in the window, newest first, filtered by repository.

        ``source=None`` on purpose: cache_backfill rows belong on screen, and
        they are labeled as such in the summary and carry their own source, so
        the reader can see which is which instead of the two being silently
        mixed (R10.1). ``query_events`` defaults to executions only, which would
        have hidden the reconstructed rows from the one surface that names them.
        """
        events = ledger.query_events(
            repo=self.repo_filter or None,
            since=self.since,
            until=self.until,
            source=None,
            order="DESC",
        )
        return _ledger_rows_to_display(events)

    def _load_from_files(self) -> list:
        """The bridge: the AI cache plus the event files still on disk.

        Concatenated, not joined. The join by minute was the defect — it
        attributed a cached response to whichever execution shared its minute,
        and read the action through a map that disagreed with the writer's.
        Two clearly-labeled rows beat one row that is quietly wrong.
        """

        def progress_cb(done: int, total_count: int):
            self.call_from_thread(self._update_progress, done, total_count)

        rows = scan_cache_files_for_dashboard(
            repo_filter=self.repo_filter,
            progress_cb=progress_cb,
            since_date=self.since,
        )
        rows.extend(scan_event_files_for_dashboard(repo_filter=self.repo_filter))
        # The same window the ledger applies in SQL, applied to rows whose
        # `day` does not exist yet. ISO 8601 compares as text, which is what
        # `day >= since` relies on inside the database too.
        rows = [row for row in rows if self._in_window(row.get("timestamp"))]
        rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return rows

    def _in_window(self, timestamp) -> bool:
        """Whether a file row's timestamp falls inside --since/--until."""
        day = str(timestamp or "")[:10]
        if not day:
            return not (self.since or self.until)
        if self.since and day < str(self.since):
            return False
        if self.until and day > str(self.until):
            return False
        return True

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

    def _finish_scan(self, rows: list, sections: list = None) -> None:
        """Called on the main thread when loading is complete."""
        self.query_one("#loading_overlay").display = False
        self.events = rows
        self._populate_table()
        self._update_summary()
        self._render_sections(sections)

    def _render_sections(self, sections: list = None) -> None:
        """Draws the shared section lines, in Textual markup.

        While the ledger is absent the four readers that query it have nothing
        to read, and saying so is the honest answer — computing those metrics
        off the file rows instead would be a second implementation, which is
        how the two surfaces drifted apart in the first place. The cycle is
        drawn either way: it never read the ledger.
        """
        notice = self.query_one("#sections_notice", Static)
        notice.display = not self.using_ledger
        if notice.display:
            notice.update(
                __(
                    "Cost, quality, modules and providers need the ledger — "
                    "run `gitpr metrics migrate` to import the event files."
                )
            )

        for widget_id, lines in sections or []:
            widget = self.query_one(widget_id, Static)
            widget.display = bool(lines)
            if lines:
                widget.update(self._markup(lines))

    @staticmethod
    def _markup(lines: list) -> str:
        """The section lines as Textual markup, one rendering spelled twice.

        The styles come from src/metrics.py and only their spelling changes
        here. ``[`` is escaped because a module path or a model name may carry
        one and Textual would read it as the start of a tag.
        """
        shapes = {TITLE: "[bold cyan]{0}[/bold cyan]", WARN: "[yellow]{0}[/yellow]"}
        return "\n".join(
            shapes.get(style, "{0}").format(text.replace("[", r"\["))
            for style, text in lines
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
        """Update the summary bar with aggregate stats from the loaded rows."""
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
        backfilled = sum(
            1 for r in self.events if r.get("source") == ledger.SOURCE_BACKFILL
        )

        top_cmds = ", ".join(f"{cmd}({n})" for cmd, n in commands.most_common(3))

        lines = [
            f"{__('Total entries')}: {total}  |  {__('Reconstructed')}: {backfilled}",
            f"{__('Tokens')}: {total_tokens:,}  |  {__('Total duration')}: {total_duration_ms:,} ms",
            f"{__('Top commands')}: {top_cmds}",
        ]
        summary.update("\n".join(lines))

        # Status bar: time range + entry count
        newest = self.events[0].get("timestamp", "")[:19]
        oldest = self.events[-1].get("timestamp", "")[:19]
        status.update(
            f"{__('Range')}: {oldest} → {newest}  |  {__('Entries')}: {total}"
            + ("" if self.using_ledger else f"  |  {__('reading files before import')}")
        )

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_refresh(self) -> None:
        """Reload data from its source (F5)."""
        self._start_scan()


def launch_metrics_dashboard(repo_filter=None, since=None, until=None):
    """Entry point: launches the metrics TUI."""
    app = MetricsApp(repo_filter=repo_filter, since=since, until=until)
    app.run()
