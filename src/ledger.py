"""Local usage ledger — one SQLite row per GitPR command execution.

The ledger answers "how many times", "how much did it cost" and "who ran it".
It is deliberately **not** the AI response cache: ``save_cached_response()``
keys files by ``md5(prompt)`` and the cache-hit path returns before rewriting,
so the cache counts *distinct prompts*. Five identical reviews are one cache
file and five executions. Tokens, model, duration and provider come FROM the
cache — that is the only place the provider reports them — but they are copied
into the row **at write time**, never joined afterwards. The join-by-minute
that used to do this depended on a cache-folder map that existed in three
diverging copies (two of them wrong for ``fullreview``/``filereview``); copying
at write time has no map to diverge and no minute to coincide.

Three properties the old JSON event files did not have:

* **One row per execution, always.** The write is synchronous. The daemon
  thread it replaces lost the row whenever the process exited before the thread
  was scheduled — which is the whole lifecycle of ``gitpr --hook-event``.
* **The ledger is never born empty while event files are on disk.** It comes
  into existence together with the absorption of those files, never before —
  see ``ensure_ledger()``.
* **A repo identity that is not GitHub-only.** ``core.get_repo_name()`` matched
  ``github\\.com`` and answered ``unknown/repo`` everywhere else, which is why
  hook events from other forges were written but never counted.

The ``.db`` is an implementation detail. The CSV/JSON export stays the public,
human-readable surface (see ``ADR-008``); only ``gitpr metrics bundle`` writes a
binary, and only to move rows to another machine.
"""

import json
import os
import re
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.i18n import __
from src.infrastructure.git.identity import working_context

# Bumped whenever the schema below changes in a way older code cannot read.
# ``gitpr metrics merge`` migrates a bundle that is behind and refuses one that
# is ahead, so the number is a contract between GitPR versions, not a comment.
SCHEMA_VERSION = 1

LEDGER_FILENAME = "telemetry.db"

# Where the absorbed JSON event files are moved. Deliberately a sibling of the
# metrics directory, not a child: show_metrics_summary() walks ~/.gitpr/metrics
# recursively, so legacy files left inside would keep being counted.
LEGACY_DIRNAME = "metrics_legacy"

# Written when the user declines the migration wizard. While it exists the
# ledger is created silently and the files are left alone — the user chose that,
# and `gitpr metrics migrate` reopens the offer. Without it the wizard would
# interrupt every single command.
SKIP_MARKER = ".migration_declined"

# The three env values the ledger writes that are not "execution". Everything
# downstream filters on this column rather than trusting a timestamp.
SOURCE_EXECUTION = "execution"
SOURCE_BACKFILL = "cache_backfill"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id                TEXT PRIMARY KEY,
    timestamp         TEXT NOT NULL,
    day               TEXT NOT NULL,
    command           TEXT NOT NULL,
    status            TEXT NOT NULL,
    provider          TEXT DEFAULT '',
    model             TEXT DEFAULT '',
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    tokens_actual     INTEGER NOT NULL DEFAULT 0,
    tokens_estimated  INTEGER NOT NULL DEFAULT 0,
    duration_ms       INTEGER NOT NULL DEFAULT 0,
    repo              TEXT DEFAULT '',
    branch            TEXT DEFAULT '',
    author_name       TEXT DEFAULT '',
    modules           TEXT,
    cache_hit         INTEGER NOT NULL DEFAULT 0,
    map_reduce        INTEGER NOT NULL DEFAULT 0,
    linter_errors     INTEGER,
    linter_warnings   INTEGER,
    chunks_count      INTEGER,
    error_message     TEXT,
    source            TEXT NOT NULL DEFAULT 'execution',
    exported_at       TEXT,
    payload           TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_day ON events(day);
CREATE INDEX IF NOT EXISTS idx_events_repo_day ON events(repo, day);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
"""

# Columns the writer fills from the payload; anything else lands in `payload`.
_COLUMNS = (
    "id",
    "timestamp",
    "day",
    "command",
    "status",
    "provider",
    "model",
    "prompt_tokens",
    "completion_tokens",
    "tokens_actual",
    "tokens_estimated",
    "duration_ms",
    "repo",
    "branch",
    "author_name",
    "modules",
    "cache_hit",
    "map_reduce",
    "linter_errors",
    "linter_warnings",
    "chunks_count",
    "error_message",
    "source",
    "exported_at",
    "payload",
)

# The two halves of the statement that moves rows between databases (bundle and
# merge): the same names on either side of the INSERT, except `exported_at`,
# which is blanked. Export bookkeeping belongs to the machine that exports, and
# rows that arrive pre-stamped would make the receiver's first export answer
# "nothing new".
_TRANSPORT_COLUMNS = ", ".join(_COLUMNS)
_TRANSPORT_SELECT = ", ".join(
    "NULL" if column == "exported_at" else column for column in _COLUMNS
)

# kwargs that map onto a column. Everything else a call site passes is kept in
# `payload` — the ledger must not lose a field the caller recorded just because
# no query reads it yet.
_KWARG_COLUMNS = {
    "cache_hit": "cache_hit",
    "map_reduce_triggered": "map_reduce",
    "linter_errors": "linter_errors",
    "linter_warnings": "linter_warnings",
    "chunks_count": "chunks_count",
    "error_message": "error_message",
    "error_msg": "error_message",
    "modules": "modules",
}

_DIFF_PATH_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.M)

# How deep a module name goes. Two segments keep "src/fix" and "docs/plans"
# apart while keeping the project's file tree out of the database that travels
# between machines in a bundle.
MODULE_DEPTH = 2

_warned = False


class LedgerError(Exception):
    """The ledger could not be read or written."""


class LedgerVersionError(LedgerError):
    """The database was written by a newer GitPR than this one.

    Raised before anything is written, so a bundle from the future leaves the
    local database untouched rather than half-migrated.
    """

    def __init__(self, found: int, supported: int):
        self.found = found
        self.supported = supported
        super().__init__(
            f"Ledger schema version {found} is newer than this GitPR supports "
            f"({supported}). Upgrade GitPR to read it."
        )


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def get_metrics_dir() -> Path:
    """~/.gitpr/metrics/ — the directory the ledger lives in."""
    return Path.home() / ".gitpr" / "metrics"


def get_ledger_path() -> Path:
    """~/.gitpr/metrics/telemetry.db."""
    return get_metrics_dir() / LEDGER_FILENAME


def get_legacy_dir() -> Path:
    """Where absorbed JSON event files are moved.

    A sibling of the metrics directory on purpose: the summary walks
    ~/.gitpr/metrics recursively, so a child directory would keep the old files
    in the count.
    """
    return Path.home() / ".gitpr" / LEGACY_DIRNAME


def get_skip_marker() -> Path:
    return get_metrics_dir() / SKIP_MARKER


def ledger_exists() -> bool:
    return get_ledger_path().exists()


# ---------------------------------------------------------------------------
# Connection and schema
# ---------------------------------------------------------------------------


@contextmanager
def connect(path=None):
    """The ledger connection, for the length of a ``with`` block.

    A context manager rather than a bare connection because ``with conn:`` on
    a raw sqlite3 connection commits but does **not** close it — every caller
    looked like it was managing the file and none of them was. On Windows a
    leaked connection keeps the database locked.

    Commits on the way out and closes either way. If the block raises, the
    transaction is rolled back: a half-written row is worse than no row, since
    the ledger is the answer to "what did we spend".

    Raises LedgerVersionError when the file belongs to a newer GitPR, before
    the block's body can run.
    """
    db_path = Path(path) if path else get_ledger_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        # WAL lets a hook and an interactive command write concurrently, which
        # the per-command JSON files could only manage by accident.
        conn.execute("PRAGMA journal_mode=WAL")
        # FULL is deliberate and is the whole point of the synchronous write: an
        # fsync per execution is nothing next to the AI call that preceded it,
        # and "the ledger is the truth of what we spent" does not survive
        # losing the last row to a power cut.
        conn.execute("PRAGMA synchronous=FULL")
        _ensure_schema(conn)

        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_schema(conn):
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise LedgerVersionError(version, SCHEMA_VERSION)
    if version == 0:
        conn.executescript(_SCHEMA)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def _warn_once(message):
    """Reports a ledger failure without ever breaking the command.

    Telemetry must not turn a working ``gitpr`` into a failing one — but the
    audit that produced this module found that silence is how data went missing
    for two months, so a failure is said out loud, once per process, on stderr
    (stdout belongs to the MCP server's JSON-RPC stream).
    """
    global _warned
    if _warned:
        return
    _warned = True
    try:
        import click

        click.secho(f"⚠️  {message}", fg="yellow", err=True)
    except Exception:
        pass


def extract_modules(diff_text, depth=MODULE_DEPTH):
    """Normalized module names touched by a unified diff, or None.

    A module is the first *depth* segments of the changed file's **directory**
    — ``src/fix/apply_fix.py`` is ``src/fix``, ``src/main.py`` is ``src``, and a
    file at the repository root is ``(root)``. The file name is dropped because
    the question is which part of the project hurts, not which file.

    Returns None — not an empty list — when there is no diff to read: the field
    is nullable by construction, because the linter, the blame engine and the
    hooks all record executions that never had a diff in hand.
    """
    if not diff_text:
        return None

    modules = []
    for _old, new in _DIFF_PATH_RE.findall(diff_text):
        path = new.strip().strip('"')
        directory = path.rsplit("/", 1)[0] if "/" in path else ""
        parts = [seg for seg in directory.split("/") if seg]
        module = "/".join(parts[:depth]) if parts else "(root)"
        if module not in modules:
            modules.append(module)

    return modules or None


def _row_from_payload(payload, context=None, source=SOURCE_EXECUTION, event_id=None):
    """Maps the caller's flat payload onto the ledger's columns."""
    context = context or working_context()
    payload = dict(payload)

    timestamp = payload.get("timestamp") or datetime.now().isoformat()
    day = str(timestamp)[:10]

    meta = payload.pop("meta", None) or {}

    row = {name: None for name in _COLUMNS}
    row["id"] = event_id or uuid.uuid4().hex
    row["timestamp"] = timestamp
    row["day"] = day
    row["command"] = payload.pop("command", "") or ""
    row["status"] = payload.pop("status", "") or ""
    row["duration_ms"] = payload.pop("duration_ms", 0) or 0
    row["tokens_estimated"] = payload.pop("tokens_estimated", 0) or 0

    # Identity comes from the working copy, never from the caller: the hook path
    # and the interactive path must produce the same string or the dashboard
    # silently drops one of them. Callers that replay *historical* records —
    # the legacy files and the cache backfill — override these three fields
    # afterwards, because a past execution's repository is whatever it was then,
    # not whichever directory the user happens to be standing in now.
    payload.pop("repo", None)
    payload.pop("branch", None)
    row["repo"] = context.repo
    row["branch"] = context.branch
    row["author_name"] = context.author_name

    # Enrichment, copied from the provider's own metadata at write time. The
    # caller's provider is the outer fallback, not the inner one: a caller that
    # named one knew what it was doing, but a caller that said nothing lets the
    # metadata speak. "local" is the last resort and means no AI was involved.
    row["provider"] = (
        payload.pop("provider", None) or meta.get("provider", "") or "local"
    )
    row["model"] = meta.get("model", "") or ""
    row["prompt_tokens"] = meta.get("prompt_tokens", 0) or 0
    row["completion_tokens"] = meta.get("completion_tokens", 0) or 0
    row["tokens_actual"] = meta.get("total_tokens", 0) or 0

    for kwarg, column in _KWARG_COLUMNS.items():
        if kwarg in payload:
            row[column] = payload.pop(kwarg)

    for flag in ("cache_hit", "map_reduce"):
        row[flag] = 1 if row[flag] else 0

    if row["modules"] is not None and not isinstance(row["modules"], str):
        row["modules"] = json.dumps(row["modules"], ensure_ascii=False)

    row["source"] = source
    row["payload"] = json.dumps(payload, ensure_ascii=False) if payload else None
    return row


def record_event(payload, context=None, source=SOURCE_EXECUTION, event_id=None, path=None):
    """Writes one execution row synchronously.

    Returns the row id, or None when the write could not happen — a broken
    ledger must never fail the command that produced the metric. The failure is
    reported on stderr rather than swallowed.
    """
    try:
        ensure_ledger(interactive=_interactive, path=path, progress=_progress_arg())
        row = _row_from_payload(payload, context=context, source=source, event_id=event_id)
        with connect(path) as conn:
            columns = ", ".join(_COLUMNS)
            placeholders = ", ".join(f":{name}" for name in _COLUMNS)
            conn.execute(
                f"INSERT OR IGNORE INTO events ({columns}) VALUES ({placeholders})", row
            )
        return row["id"]
    except LedgerVersionError:
        # A newer database is a deliberate refusal, not a telemetry hiccup —
        # say it plainly instead of degrading quietly.
        _warn_once(
            f"Ledger at {get_ledger_path()} was written by a newer GitPR; "
            "this run's metrics were not recorded."
        )
        return None
    except Exception as exc:
        _warn_once(f"Could not record metrics: {exc}")
        return None


# ---------------------------------------------------------------------------
# The "never born empty" invariant
# ---------------------------------------------------------------------------

# How much of a terminal this run may use, told to us by the CLI — the only
# layer that sees the flags. Two booleans because they answer two questions:
# ``_interactive`` is whether the migration may *ask* (draw a TUI), and
# ``_quiet`` is whether it may *print* (the one-time import progress on stderr).
# The defaults are the careful ones: a process that never says otherwise gets no
# TUI and no progress, which is right for the MCP server, for tests and for
# anyone importing this module as a library.
_interactive = False
_quiet = False

# Set when the wizard was closed without an answer. The answer is still owed, so
# nothing absorbs the files behind the user's back for the rest of this process.
_answer_pending = False


def configure_terminal(interactive=False, quiet=False):
    """Records how much of a terminal this run may use. See the notes above.

    Called once per run, before anything looks at the ledger, so it also starts
    the run with no answer outstanding: a pending one belongs to the run that
    raised it and must not outlive it.
    """
    global _interactive, _quiet, _answer_pending
    _interactive = bool(interactive)
    _quiet = bool(quiet)
    _answer_pending = False


def mark_answer_pending():
    """Called by the wizard when it is closed without a decision."""
    global _answer_pending
    _answer_pending = True


def interactive() -> bool:
    """Whether this run may stop and draw a TUI, as told by the CLI."""
    return _interactive


def _progress_arg():
    """``None`` (the default reporter) or ``False`` (no progress at all)."""
    return False if _quiet else None


def pending_legacy_files():
    """JSON event files still sitting in ~/.gitpr/metrics/, oldest first."""
    metrics_dir = get_metrics_dir()
    if not metrics_dir.is_dir():
        return []

    found = []
    for root, dirs, files in os.walk(metrics_dir):
        # The export output is a report, not an event.
        if "export" in Path(root).relative_to(metrics_dir).parts:
            continue
        for name in files:
            if not name.endswith(".json") or name.startswith("config"):
                continue
            found.append(Path(root) / name)

    return sorted(found)


def marker_present() -> bool:
    return get_skip_marker().exists()


def write_skip_marker(reason=""):
    """Records that the user declined the migration, so it stops being offered."""
    try:
        marker = get_skip_marker()
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(
            json.dumps(
                {"declined_at": datetime.now().isoformat(), "reason": reason},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def ensure_ledger(interactive=False, path=None, progress=None):
    """Makes sure a ledger exists before the first write.

    The invariant is that **the ledger never exists empty while event files are
    on disk**. It is created here — and only here — together with the absorption
    of those files, either because the user ran the wizard or because the
    program absorbed them silently. There is no state in which the ledger
    silences the cache fallback without having taken the data in.

    ``progress`` is the callback to use, ``None`` for the default reporter on
    stderr and ``False`` for no progress output at all (``--quiet``).

    Returns True when a ledger was created by this call, and False when one was
    already there — or when the user closed the wizard without deciding, in
    which case the ledger is deliberately not born: the caller's write will
    create it empty, which is why the wizard also calls
    ``mark_answer_pending()`` to keep this process from absorbing what the user
    is still deciding about.
    """
    if path is None and ledger_exists():
        return False

    db_path = Path(path) if path else get_ledger_path()
    if db_path.exists():
        return False

    legacy = [] if path else pending_legacy_files()
    if not legacy:
        # Nothing to lose: an empty ledger with nothing on disk is honest.
        with connect(db_path):
            pass
        return True

    if interactive and not marker_present():
        from src.ui.metrics_migration_app import run_migration_wizard

        # The wizard decides: it either absorbs (possibly both sources) or
        # writes the skip marker. Either way the ledger is never created empty.
        if not run_migration_wizard(legacy_files=legacy, progress=progress):
            # Aborted. Creating the ledger now would be the whole defect back
            # again by another route: the file scan reads only while telemetry.db
            # is absent, so an empty ledger would silence it and orphan the
            # files. Returning False leaves the next run to ask again.
            return False

    if marker_present() or _answer_pending:
        # Declined — on this run, an earlier one, or by closing the wizard. The
        # marker and the pending flag silence the *question*, never the answer:
        # absorbing here, which is what the silent path below does, would import
        # the files the user just refused on the very next command. They stay
        # where they are until `gitpr metrics migrate` is run on purpose. The
        # ledger is still born: the write that called us would create it
        # regardless, and an empty ledger is the honest state for "there is no
        # history in here yet".
        if not ledger_exists():
            with connect(db_path):
                pass
        return True

    # Non-interactive path (--init, --quiet, --mcp, CI, a piped run): absorb
    # silently, reporting progress as text on stderr. stdout belongs to the MCP
    # server's JSON-RPC stream.
    absorb_legacy_files(files=legacy, progress=progress)
    if not db_path.exists():
        with connect(db_path):
            pass
    return True


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------


def _window_clause(repo=None, since=None, until=None, source=None, command=None):
    clauses, params = [], {}
    if repo:
        clauses.append("repo = :repo")
        params["repo"] = repo
    if since:
        clauses.append("day >= :since")
        params["since"] = str(since)
    if until:
        clauses.append("day <= :until")
        params["until"] = str(until)
    if source:
        clauses.append("source = :source")
        params["source"] = source
    if command:
        clauses.append("command = :command")
        params["command"] = command
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def query_events(
    repo=None,
    since=None,
    until=None,
    source=SOURCE_EXECUTION,
    command=None,
    order="DESC",
    limit=None,
    path=None,
):
    """Rows in the window, as dictionaries. Empty list when there is no ledger."""
    db_path = Path(path) if path else get_ledger_path()
    if not db_path.exists():
        return []

    where, params = _window_clause(
        repo=repo, since=since, until=until, source=source, command=command
    )
    direction = "ASC" if str(order).upper() == "ASC" else "DESC"
    sql = f"SELECT * FROM events{where} ORDER BY timestamp {direction}"
    if limit:
        sql += " LIMIT :limit"
        params["limit"] = int(limit)

    try:
        with connect(db_path) as conn:
            return [dict(row) for row in conn.execute(sql, params)]
    except Exception as exc:
        _warn_once(f"Could not read metrics: {exc}")
        return []


def count_events(repo=None, since=None, until=None, source=None, path=None):
    """How many rows match the window."""
    db_path = Path(path) if path else get_ledger_path()
    if not db_path.exists():
        return 0

    where, params = _window_clause(repo=repo, since=since, until=until, source=source)
    try:
        with connect(db_path) as conn:
            return conn.execute(f"SELECT COUNT(*) FROM events{where}", params).fetchone()[0]
    except Exception as exc:
        _warn_once(f"Could not read metrics: {exc}")
        return 0


def disk_usage(path=None):
    """Total bytes the ledger occupies, WAL included, as a display string."""
    db_path = Path(path) if path else get_ledger_path()
    total = 0
    for suffix in ("", "-wal", "-shm"):
        candidate = Path(str(db_path) + suffix)
        try:
            total += candidate.stat().st_size
        except OSError:
            pass

    if total < 1024:
        return f"{total} B"
    if total < 1024 * 1024:
        return f"{total / 1024:.1f} KB"
    return f"{total / (1024 * 1024):.1f} MB"


# ---------------------------------------------------------------------------
# Export bookkeeping — replaces the config.json UUID list (defect G1)
# ---------------------------------------------------------------------------


def mark_exported(ids, path=None):
    """Stamps the given rows as exported.

    The state lives on the row. The file this replaces recorded the ids of every
    repository at once, so exporting repo A silently marked repo B's events as
    already exported and its export answered "no new metrics" forever.
    """
    ids = list(ids)
    if not ids:
        return
    stamp = datetime.now().isoformat()
    try:
        with connect(path) as conn:
            conn.executemany(
                "UPDATE events SET exported_at = ? WHERE id = ?",
                [(stamp, event_id) for event_id in ids],
            )
    except Exception as exc:
        _warn_once(f"Could not mark metrics as exported: {exc}")


def list_events_for_export(repo=None, since=None, until=None, path=None):
    """Executions that have not been exported yet, oldest first."""
    db_path = Path(path) if path else get_ledger_path()
    if not db_path.exists():
        return []

    where, params = _window_clause(repo=repo, since=since, until=until)
    connector = " AND " if where else " WHERE "
    sql = f"SELECT * FROM events{where}{connector}exported_at IS NULL ORDER BY timestamp ASC"
    try:
        with connect(db_path) as conn:
            return [dict(row) for row in conn.execute(sql, params)]
    except Exception as exc:
        _warn_once(f"Could not read metrics: {exc}")
        return []


# ---------------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------------


def purge_events(path=None):
    """Removes every row and reclaims the space. Returns how many were removed."""
    db_path = Path(path) if path else get_ledger_path()
    if not db_path.exists():
        return 0
    try:
        with connect(db_path) as conn:
            removed = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            conn.execute("DELETE FROM events")
            # Commit before VACUUM: it rewrites the whole file and cannot run
            # inside a transaction. Doing it in the other order raises, and the
            # rollback takes the DELETE with it — which is how this returned 0
            # while reporting success.
            conn.commit()
            conn.execute("VACUUM")
        return removed
    except Exception as exc:
        _warn_once(f"Could not purge metrics: {exc}")
        return 0


def prune_before(day, source=None, path=None):
    """Removes rows older than *day*. Returns how many were removed.

    There is deliberately no automatic expiry: the ledger is the answer to
    "what did we spend this year", and a calendar that deletes on its own would
    change that answer without anyone asking. ``--prune`` is the only destructive
    path besides ``--purge``, and both are asked for explicitly.
    """
    db_path = Path(path) if path else get_ledger_path()
    if not db_path.exists():
        return 0

    clauses = ["day < :day"]
    params = {"day": str(day)}
    if source:
        clauses.append("source = :source")
        params["source"] = source

    try:
        with connect(db_path) as conn:
            cursor = conn.execute(
                f"DELETE FROM events WHERE {' AND '.join(clauses)}", params
            )
            removed = cursor.rowcount or 0
            # See purge_events: VACUUM needs the transaction closed first.
            conn.commit()
            conn.execute("VACUUM")
        return removed
    except Exception as exc:
        _warn_once(f"Could not prune metrics: {exc}")
        return 0


# ---------------------------------------------------------------------------
# Transport — the ledger as a file that travels
# ---------------------------------------------------------------------------

# Migrations that bring an older bundle up to SCHEMA_VERSION, keyed by the
# version they start from. Empty on purpose: version 1 is the first, so no
# bundle can be older than what this code writes — the walk below is what makes
# the number a contract between versions rather than a comment.
_BUNDLE_MIGRATIONS = {}


def _quote_sql_literal(value):
    """A path as a SQL string literal. ATTACH takes no bound parameters."""
    return "'" + str(value).replace("'", "''") + "'"


def bundle_schema_version(path):
    """The schema version a file claims, or 0 when it is not a GitPR ledger.

    Reads read-only, so pointing this at a file tells you about it without
    writing a ``-wal`` beside it.
    """
    db_path = Path(path)
    if not db_path.exists():
        raise LedgerError(f"{db_path} does not exist.")

    conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    try:
        table = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
        ).fetchone()
        version = conn.execute("PRAGMA user_version").fetchone()[0]
    finally:
        conn.close()

    # A version without the table is a file wearing our number; no table at all
    # is simply not ours, whatever it says.
    return version if table else 0


def default_bundle_path():
    """Where ``gitpr metrics bundle`` writes when it is not told where to.

    Beside the CSV/JSON export, so the generated files of one run sit together.
    """
    return (
        Path.cwd()
        / ".gitpr"
        / "metrics"
        / "export"
        / f"gitpr_metrics_{datetime.now().strftime('%Y-%m-%d')}.db"
    )


def build_bundle(destination, repo=None, since=None, until=None, source=None, path=None):
    """Writes the rows in the window to *destination* as a standalone ledger.

    Returns how many rows it carries. Schema and ``user_version`` travel with
    it, so the receiving machine can read the version before it attaches
    anything and refuse a bundle from the future (see ``merge_bundles``).

    ``exported_at`` is blanked on the way out. It records what *this* machine
    has already written to CSV, and a bundle that arrives pre-stamped would make
    the receiver's first export answer "nothing new" — defect G1's shape in a
    new place.

    The destination must not exist: replacing a file is a decision for the
    caller, which is the only layer that can ask. That refusal is also what
    keeps a bundle from being written over the ledger itself, which does exist.
    """
    source_path = Path(path) if path else get_ledger_path()
    if not source_path.exists():
        raise LedgerError("There is no ledger to cut a bundle from.")

    destination = Path(destination)
    if destination.exists():
        raise LedgerError(f"{destination} already exists.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    where, params = _window_clause(repo=repo, since=since, until=until, source=source)

    with connect(destination) as conn:
        # ATTACH cannot run inside a transaction, and the schema creation above
        # may have opened one.
        conn.commit()
        conn.execute(f"ATTACH DATABASE {_quote_sql_literal(source_path)} AS source")
        try:
            conn.execute(
                f"INSERT INTO events ({_TRANSPORT_COLUMNS}) "
                f"SELECT {_TRANSPORT_SELECT} FROM source.events{where}",
                params,
            )
            return conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        finally:
            # DETACH refuses while a transaction is open.
            conn.commit()
            conn.execute("DETACH DATABASE source")


def merge_bundles(paths, path=None):
    """Merges each bundle into the local ledger. Returns (merged, skipped).

    Every bundle's version is read *before* the first ATTACH, so a bundle from
    the future leaves the local ledger exactly as it was — not half of one
    merge done and the rest refused.

    Rows are keyed by their UUID, so a bundle carrying rows this machine already
    has adds nothing: merging the same file twice is safe, which is what makes
    "send me your numbers" a sentence without a protocol behind it.
    """
    bundles = [Path(bundle) for bundle in paths]
    versions = []
    for bundle in bundles:
        version = bundle_schema_version(bundle)
        if version == 0:
            raise LedgerError(f"{bundle} is not a GitPR ledger.")
        if version > SCHEMA_VERSION:
            raise LedgerVersionError(version, SCHEMA_VERSION)
        versions.append(version)

    merged = skipped = 0
    with connect(path) as conn:
        for bundle, version in zip(bundles, versions):
            added, present = _merge_one(conn, bundle, version)
            merged += added
            skipped += present
    return merged, skipped


def _merge_one(conn, bundle, version):
    """Copies one bundle's rows into the open ledger. Returns (merged, skipped)."""
    present = 0
    before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    conn.commit()
    conn.execute(f"ATTACH DATABASE {_quote_sql_literal(bundle)} AS bundle")
    try:
        while version < SCHEMA_VERSION:
            migrate = _BUNDLE_MIGRATIONS.get(version)
            if migrate is None:
                raise LedgerError(
                    f"No migration from schema {version} to {SCHEMA_VERSION} "
                    f"for {bundle}."
                )
            migrate(conn)
            version += 1

        present = conn.execute("SELECT COUNT(*) FROM bundle.events").fetchone()[0]
        conn.execute(
            f"INSERT OR IGNORE INTO events ({_TRANSPORT_COLUMNS}) "
            f"SELECT {_TRANSPORT_SELECT} FROM bundle.events"
        )
        conn.commit()
    finally:
        conn.commit()
        conn.execute("DETACH DATABASE bundle")

    after = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    merged = after - before
    return merged, present - merged


# ---------------------------------------------------------------------------
# Absorption of the legacy JSON event files
# ---------------------------------------------------------------------------


def _progress_reporter(label):
    """A callback that prints to stderr, or None when there is no terminal.

    stderr, never stdout: ``gitpr-mcp`` runs on stdio with stdout reserved for
    JSON-RPC, and a progress line there would corrupt the protocol.
    """

    def report(done, total):
        if total and (done == total or done % 50 == 0):
            sys.stderr.write(f"\r{label} {done}/{total}")
            sys.stderr.flush()
            if done == total:
                sys.stderr.write("\n")
                sys.stderr.flush()

    return report


def absorb_legacy_files(files=None, progress=None, path=None):
    """Moves the old JSON event files into the ledger.

    Each row is keyed by the file's path relative to the metrics directory, so
    two owners with the same uuid cannot collide and re-running the migration
    cannot duplicate. The originals are then **moved** to
    ~/.gitpr/metrics_legacy/ — outside the metrics directory, which is walked
    recursively — and never deleted: the move is reversible by hand and
    deleting would not be.

    Returns ``(absorbed, already_present)``.
    """
    files = pending_legacy_files() if files is None else list(files)
    if not files:
        return 0, 0

    context = working_context()
    metrics_dir = get_metrics_dir()
    destination = get_legacy_dir()
    reporter = progress if progress is not None else _progress_reporter(__("Importing"))
    absorbed = already = 0

    columns = ", ".join(_COLUMNS)
    placeholders = ", ".join(f":{name}" for name in _COLUMNS)

    # One connection for the whole batch: the migration writes thousands of rows
    # and a connection per row would make it visibly slow. connect() creates the
    # schema on the way in, so this is also where the ledger is born.
    with connect(path) as conn:
        for index, source_file in enumerate(files, 1):
            try:
                with open(source_file, "r", encoding="utf-8", errors="replace") as handle:
                    payload = json.load(handle)
                if not isinstance(payload, dict):
                    raise ValueError("not an event object")
            except Exception:
                _move_legacy(source_file, destination)
                if reporter:
                    reporter(index, len(files))
                continue

            try:
                relative = source_file.relative_to(metrics_dir).with_suffix("")
            except ValueError:
                relative = Path(source_file.stem)
            event_id = relative.as_posix()

            row = _row_from_payload(
                payload, context=context, event_id=event_id, source=SOURCE_EXECUTION
            )
            # The file recorded where it ran; the working copy is wherever the
            # user is standing today. For historical rows the file wins.
            row["repo"] = payload.get("repo") or row["repo"]
            row["branch"] = payload.get("branch") or row["branch"]
            row["author_name"] = payload.get("author_name") or row["author_name"]
            # Left unexported on purpose. These events predate the ledger and no
            # export has ever reported them, so the first one after the
            # migration must. Stamping them here would keep the whole archive out
            # of the CSV — present in the ledger, absent from its human view, and
            # nothing would ever say so.

            cursor = conn.execute(
                f"INSERT OR IGNORE INTO events ({columns}) VALUES ({placeholders})", row
            )
            if cursor.rowcount:
                absorbed += 1
            else:
                already += 1
            _move_legacy(source_file, destination)

            if reporter:
                reporter(index, len(files))

    return absorbed, already


def _move_legacy(source_file, destination):
    """Moves one legacy file out of the metrics directory, preserving its path."""
    try:
        relative = source_file.relative_to(get_metrics_dir())
    except ValueError:
        relative = Path(source_file.name)

    target = destination / relative
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(source_file), str(target))
    except Exception:
        pass  # A file we cannot move is a file we simply leave where it is


# ---------------------------------------------------------------------------
# Backfill from the AI cache — the second, weaker source
# ---------------------------------------------------------------------------


def backfill_from_cache(repo=None, progress=None, path=None):
    """Reconstructs history from the AI response cache.

    These rows are marked ``cache_backfill`` and kept out of the execution
    aggregates by default, because the cache counts **distinct prompts**: a
    prompt run five times is one cache file. The backfill answers "what existed
    before the ledger", never "how many times it ran".

    Returns the number of rows written.
    """
    cache_base = Path.home() / ".gitpr" / "cache" / "prompts"
    if not cache_base.is_dir():
        return 0

    files = sorted(cache_base.glob("*/*.json"))
    if not files:
        return 0

    reporter = progress if progress is not None else _progress_reporter(
        __("Reconstructing")
    )
    context = working_context()
    written = 0

    with connect(path) as conn:
        columns = ", ".join(_COLUMNS)
        placeholders = ", ".join(f":{name}" for name in _COLUMNS)

        for index, cache_file in enumerate(files, 1):
            if reporter:
                reporter(index, len(files))
            try:
                with open(cache_file, "r", encoding="utf-8", errors="replace") as handle:
                    data = json.load(handle)
                if not isinstance(data, dict):
                    continue
                response = data.get("response") or {}
                if not isinstance(response, dict):
                    continue
                meta = response.get("meta_raw") or response.get("_telemetry_meta") or {}
            except Exception:
                continue

            stamp = str(data.get("datetime") or "").strip()
            if not stamp:
                continue

            payload = {
                "timestamp": stamp.replace(" ", "T"),
                "command": data.get("action_type", "") or cache_file.parent.name,
                "status": "success",
                "provider": meta.get("provider", ""),
                # The tokens, the model and the duration live *in the cache* and
                # nowhere else — reconstructing without them would recover the
                # dates of past work and nothing about its cost, which is half
                # of what the backfill is for.
                "duration_ms": meta.get("duration_ms", 0) or 0,
                "meta": meta,
            }
            row = _row_from_payload(
                payload,
                context=context,
                source=SOURCE_BACKFILL,
                event_id=f"cache-{cache_file.stem}",
            )
            # The cache records the repo it ran in; trust it over the working
            # copy, which is wherever the user happens to be standing now.
            row["repo"] = data.get("repo", "") or context.repo
            row["branch"] = data.get("branch", "") or ""
            row["author_name"] = data.get("author_name", "") or context.author_name
            # Exportable like any other row: `source` tells them apart in the
            # CSV, and an export that silently dropped part of the ledger would
            # be answering a question nobody asked.

            if repo and row["repo"] != repo:
                continue

            conn.execute(
                f"INSERT OR IGNORE INTO events ({columns}) VALUES ({placeholders})", row
            )
            written += 1

    return written
