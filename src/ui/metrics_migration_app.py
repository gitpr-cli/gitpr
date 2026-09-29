"""
Metrics migration wizard — the one question that has to be asked in person.

GitPR 0.0.37 and earlier wrote one JSON file per recorded command into
~/.gitpr/metrics/. From 0.0.38 those events live in a SQLite ledger instead, and
the file scan survives only as a bridge for machines that have not migrated yet
(see src/ledger.py). That bridge reads only while telemetry.db is *absent*, so
creating an empty database is the one thing that can silently orphan the
archive — which is what this wizard exists to prevent.

Three answers, and the wording keeps them apart:

* **Import into the ledger** — the event files are the truth: one file, one
  execution.
* **Also reconstruct from the AI cache** — an approximation, and a weaker one.
  The cache is keyed by md5(prompt) and a cache hit returns before writing, so
  it holds one file per *distinct prompt*: a command run five times is one cache
  file, and a prompt edited once is two. Rows from here are marked
  ``cache_backfill`` and stay out of the execution aggregates.
* **Not now** — nothing is imported, a marker records the refusal so the
  question is not asked again, and the files are left exactly where they are.

Closing the wizard is none of the three: nothing is written, not even the
ledger, and the next run asks again.

The wizard only *decides*. The work runs afterwards in src/ledger.py, where the
"never born empty" invariant lives in one place and progress is text on stderr —
stdout belongs to the MCP server's JSON-RPC stream.

Usage: gitpr metrics migrate
"""

from textual.app import App, ComposeResult
from textual.widgets import Button, Static
from textual.containers import Vertical, Horizontal
from textual.binding import Binding

from src.i18n import __


class MigrationApp(App):
    """Asks whether the pre-ledger event files should be imported."""

    TITLE = __("GitPR - Metrics Migration")
    ENABLE_COMMAND_PALETTE = False

    CSS = """
    #migration_dialog {
        width: 72;
        height: auto;
        padding: 1 2;
        background: $surface;
        border: thick $accent;
        margin: 2 4;
    }
    .migration_title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    .migration_intro {
        margin-bottom: 1;
    }
    .migration_option {
        text-style: bold;
    }
    .migration_hint {
        color: $text-muted;
        margin-bottom: 1;
    }
    #migration_buttons {
        height: auto;
        align-horizontal: center;
    }
    Button {
        width: 24;
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "abort", __("Not now"), show=False),
    ]

    def __init__(self, file_count=0, **kwargs):
        super().__init__(**kwargs)
        self.file_count = file_count
        self.choice = None

    def compose(self) -> ComposeResult:
        with Vertical(id="migration_dialog"):
            yield Static(__("GitPR - Metrics Migration"), classes="migration_title")
            yield Static(
                __(
                    "GitPR found {count} metric files written before the ledger "
                    "existed. What should become of them?"
                ).format(count=self.file_count),
                classes="migration_intro",
            )

            yield Static(__("Import into the ledger"), classes="migration_option")
            yield Static(
                __("Each file is one recorded execution — what actually ran."),
                classes="migration_hint",
            )

            yield Static(
                __("Also reconstruct from the AI cache"), classes="migration_option"
            )
            yield Static(
                __(
                    "An approximation: the cache holds one file per distinct prompt, "
                    "so a command run five times counts once."
                ),
                classes="migration_hint",
            )

            yield Static(__("Not now"), classes="migration_option")
            yield Static(
                __("Nothing is imported, GitPR stops asking, and your files stay put."),
                classes="migration_hint",
            )

            with Horizontal(id="migration_buttons"):
                yield Button(__("Import"), variant="primary", id="import_only")
                yield Button(__("Import and reconstruct"), id="import_backfill")
                yield Button(__("Not now"), id="skip")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.choice = {
            "import_only": "import",
            "import_backfill": "import_backfill",
            "skip": "skip",
        }.get(event.button.id)
        self.exit(self.choice)

    def action_abort(self) -> None:
        # Escape is not a fourth answer: it declines to answer at all.
        self.choice = None
        self.exit(None)


def run_migration_wizard(legacy_files=None, progress=None):
    """Shows the wizard and carries out whatever it decided.

    Returns True when the question was answered — imported (possibly both
    sources) or explicitly skipped — and False when the window was closed
    without choosing, in which case nothing at all is written and this process
    stops absorbing anything: the answer is still owed, and the next write must
    not take it upon itself to import what the user was still deciding about.
    """
    from src import ledger

    legacy_files = list(legacy_files or [])

    app = MigrationApp(file_count=len(legacy_files))
    app.run()
    choice = app.choice

    if choice is None:
        ledger.mark_answer_pending()
        return False

    if choice == "skip":
        ledger.write_skip_marker(reason="declined in the migration wizard")
        return True

    ledger.absorb_legacy_files(files=legacy_files, progress=progress)

    if choice == "import_backfill":
        ledger.backfill_from_cache(progress=progress)

    return True
