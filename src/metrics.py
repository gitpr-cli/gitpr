"""Telemetry API — the writer every call site uses, and the readers that show it.

Storage lives in ``src/ledger.py`` (one SQLite row per execution). This module
is the seam above it: the ``log_*`` functions the 34 call sites import, and the
projections the CLI and the dashboard render.

Two things were removed here rather than fixed, because the audit showed they
were the cause and not the symptom:

* The per-event JSON files, written from a daemon thread. The thread lost the
  row whenever the process exited first — the whole lifecycle of
  ``gitpr --hook-event``.
* ``enrich_metrics_from_cache()``, the join by (repo, branch, action, minute)
  that was supposed to attach real token counts after the fact. It could not
  work: it depended on a command→cache-folder map that existed in three
  diverging copies here and in the dashboard, and two of them sent
  ``fullreview``/``filereview`` to a folder that does not exist. Tokens are now
  copied from the provider's metadata when the row is written (see
  ``log_command_metric(meta=...)``), which has no map to diverge and no minute
  to coincide.
"""

import csv
import json
import os
import statistics
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src import ledger
from src.config import LOCAL_PROVIDERS, get_metrics_currency, get_model_price
from src.i18n import __
from src.infrastructure.git.identity import working_context
from src.infrastructure.scm.base import ScmProviderError

# The columns the CSV projection writes. Named for what they hold so the file
# explains itself to whoever opens it in a spreadsheet.
CSV_COLUMNS = (
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
    "source",
)

# Resolved once per process: read_payload() and the map-reduce path both write
# during a single run, and each `git` call is a process spawn.
_context = None


def _execution_context():
    """The working copy's identity, resolved once per process."""
    global _context
    if _context is None:
        _context = working_context()
    return _context


def reset_execution_context():
    """Drops the cached identity — for tests and for long-lived processes."""
    global _context
    _context = None


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------


def log_local_metric(
    command,
    status,
    provider=None,
    tokens_estimated=0,
    duration_ms=0,
    meta=None,
    **kwargs,
):
    """Records one execution in the ledger, synchronously.

    ``provider`` is the one the caller knows it used. Leave it out and the row
    is credited to whatever the provider's own metadata names, falling back to
    ``"local"`` — which is a statement that no AI was involved, never a claim
    about who answered.

    Returns the row id, or None when nothing could be written. Never raises:
    a broken ledger must not fail the command that produced the metric, and the
    failure is reported on stderr rather than swallowed.
    """
    payload = {
        "timestamp": datetime.now().isoformat(),
        "command": command,
        "status": status,
        "tokens_estimated": tokens_estimated,
        "duration_ms": duration_ms,
        **kwargs,
    }
    if provider:
        payload["provider"] = provider
    if meta:
        payload["meta"] = meta

    return ledger.record_event(payload, context=_execution_context())


def log_command_metric(
    command,
    status="success",
    provider=None,
    tokens_estimated=0,
    duration_ms=0,
    cache_hit=False,
    map_reduce_triggered=False,
    meta=None,
    **kwargs,
):
    """High-level metric logger for CLI commands.

    Args:
        command: Command name ('commit', 'review', 'fullreview', 'linter', etc.)
        status: 'success', 'error', 'triggered', 'no_changes'
        provider: AI provider used (None = local/no AI)
        tokens_estimated: Token count known before the call (usually 0)
        duration_ms: Command duration in milliseconds
        cache_hit: True if result was served from cache
        map_reduce_triggered: True if map-reduce chunking was activated
        meta: The provider's own metadata (``_telemetry_meta``) — prompt,
            completion and total tokens, model, real duration. Copied into the
            row now, at write time, which is the only moment both halves are in
            the same hand. Omit it and the row carries the estimate only.
        **kwargs: Extra fields (linter_errors, linter_warnings, chunks_count,
            modules, error_message, ...). Fields with no column are kept in the
            row's payload, so nothing a call site records is dropped.
    """
    if provider is None:
        # Auto-detect: try config, fallback to 'local'
        try:
            from src.config import get_ai_provider

            provider = get_ai_provider()
        except Exception:
            provider = "local"

    return log_local_metric(
        command=command,
        status=status,
        provider=provider,
        tokens_estimated=tokens_estimated,
        duration_ms=duration_ms,
        cache_hit=cache_hit,
        map_reduce_triggered=map_reduce_triggered,
        meta=meta,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Paths — kept because the CLI and the docs point at them
# ---------------------------------------------------------------------------


def get_metrics_dir():
    """Returns the path to the local metrics directory (~/.gitpr/metrics/)."""
    return str(ledger.get_metrics_dir())


def get_project_metrics_dir():
    """Returns the project-local .gitpr/metrics/ directory path."""
    return os.path.join(os.getcwd(), ".gitpr", "metrics")


# ---------------------------------------------------------------------------
# Fallback scan — the migration bridge, used only while no ledger exists
# ---------------------------------------------------------------------------


def scan_cache_files_for_dashboard(repo_filter=None, progress_cb=None, since_date=None):
    """Scans ~/.gitpr/cache/prompts/*/*.json and returns display rows.

    A **bridge**, not a feature: it runs only while ``telemetry.db`` does not
    exist, which is the window before the first write creates one. Once the
    ledger exists this path can be deleted without losing anything, because the
    ledger is only ever born together with the absorption of the files that
    would have fed it.

    Args:
        repo_filter: If set, only includes rows whose repo matches.
        progress_cb: Optional callback(done: int, total: int) called per file.
        since_date: Minimum YYYY-MM-DD. Defaults to January 1st of this year.
    """
    if since_date is None:
        since_date = date.today().replace(month=1, day=1).strftime("%Y-%m-%d")

    cache_base = Path.home() / ".gitpr" / "cache" / "prompts"
    rows = []

    if not cache_base.is_dir():
        return rows

    all_files = sorted(cache_base.glob("*/*.json"))
    total = len(all_files)

    for idx, cache_file in enumerate(all_files, 1):
        if progress_cb:
            progress_cb(idx, total)
        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue

        file_dt = (data.get("datetime") or "")[:10]
        if file_dt and file_dt < since_date:
            continue

        file_repo = data.get("repo", "")
        if repo_filter is not None and file_repo and file_repo != repo_filter:
            continue

        response = data.get("response") or {}
        if not isinstance(response, dict):
            continue  # Skip list-typed responses (legacy format)
        meta = response.get("meta_raw") or response.get("_telemetry_meta") or {}

        rows.append(
            {
                "timestamp": (data.get("datetime") or "").replace("T", " ")[:19],
                "command": data.get("action_type", "unknown"),
                "status": "success",
                "provider": meta.get("provider", ""),
                "tokens": meta.get("total_tokens", 0),
                "duration_ms": meta.get("duration_ms", 0),
                "repo": file_repo,
                "branch": data.get("branch", ""),
                "source": "cache",
                "md5": data.get("md5", ""),
                "path": str(cache_file),
            }
        )

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows


def scan_event_files_for_dashboard(repo_filter=None, since_date=None):
    """Reads the legacy JSON event files still on disk, as display rows.

    The companion of ``scan_cache_files_for_dashboard()``: the cache knows what
    the AI cost, the event files know which commands ran at all — including the
    ones with no AI call. Both are superseded by the ledger.
    """
    rows = []
    for path in ledger.pending_legacy_files():
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                event = json.load(f)
            if not isinstance(event, dict):
                continue
        except Exception:
            continue

        stamp = (event.get("timestamp") or "").replace("T", " ")[:19]
        if since_date and stamp[:10] and stamp[:10] < since_date:
            continue
        if repo_filter and event.get("repo", "") != repo_filter:
            continue

        rows.append(
            {
                "timestamp": stamp,
                "command": event.get("command", "unknown"),
                "status": event.get("status", "success"),
                "provider": event.get("provider", ""),
                "tokens": event.get("tokens_estimated", 0),
                "duration_ms": event.get("duration_ms", 0),
                "repo": event.get("repo", ""),
                "branch": event.get("branch", ""),
                "source": "event",
                "md5": "",
                "path": str(path),
            }
        )

    rows.sort(key=lambda r: r["timestamp"], reverse=True)
    return rows


def _ledger_rows_to_display(events):
    """Projects ledger rows onto the dashboard's row shape."""
    rows = []
    for event in events:
        modules = event.get("modules")
        if modules:
            try:
                modules = ", ".join(json.loads(modules))
            except Exception:
                pass
        rows.append(
            {
                "timestamp": (event.get("timestamp") or "").replace("T", " ")[:19],
                "command": event.get("command", ""),
                "status": event.get("status", ""),
                "provider": event.get("provider", ""),
                "model": event.get("model", ""),
                "tokens": event.get("tokens_actual") or event.get("tokens_estimated", 0),
                "duration_ms": event.get("duration_ms", 0),
                "repo": event.get("repo", ""),
                "branch": event.get("branch", ""),
                "author": event.get("author_name", ""),
                "modules": modules or "",
                "source": event.get("source", ledger.SOURCE_EXECUTION),
                "md5": "",
                "path": "",
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Window helpers
# ---------------------------------------------------------------------------


def resolve_window(days=None, since=None, until=None):
    """Turns the CLI's window flags into (since, until) YYYY-MM-DD strings.

    A window is explicit everywhere it is used — the summary, the export, the
    dashboard, the bundle. "Sprint" is deliberately not a concept here: GitPR
    has no idea which process a team follows, and a calendar range serves all
    of them. Returns (None, None) when no window was asked for.
    """
    today = date.today()
    if since:
        start = _as_day(since) or since
    elif days:
        start = (today - timedelta(days=int(days) - 1)).isoformat()
    else:
        start = None

    if until:
        end = _as_day(until) or until
    else:
        end = today.isoformat() if start else None

    return start, end


def _as_day(value):
    """Normalizes a date-ish value to YYYY-MM-DD, or None."""
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m-%d")
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return None


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------


def _execution_rows(repo_filter=None, since=None, until=None):
    """Executions in the window, oldest first — the base of every aggregate.

    ``cache_backfill`` rows are deliberately absent (R10.1). The cache keys an
    answer by prompt, so a reconstruction counts *distinct prompts*, not
    executions, and folding it into an aggregate would answer "what did we run"
    with a number that is not that. ``query_events`` defaults to executions for
    exactly this reason; the dashboard is the one surface that asks for both.
    """
    return ledger.query_events(
        repo=repo_filter or None, since=since, until=until, order="ASC"
    )


def _row_tokens(row):
    """A row's token total, in the order of who knows best.

    The provider's own count first, then the sum of its prompt/completion
    split (a row can carry the split without the total), then the local
    estimate — which is all an older row has.
    """
    total = row.get("tokens_actual") or row.get("tokens_estimated") or 0
    if total:
        return total
    return (row.get("prompt_tokens") or 0) + (row.get("completion_tokens") or 0)


def estimate_cost(provider, model, prompt_tokens, completion_tokens):
    """Money for one row, or None when its model has no configured rate.

    Local providers are free by definition (0.0). A row whose tokens were only
    *estimated* has no prompt/completion split and is not what the provider
    billed, so it is left unpriced rather than priced at a guess.
    """
    if str(provider or "").lower() in LOCAL_PROVIDERS:
        return 0.0
    rates = get_model_price(model)
    if rates is None or not (prompt_tokens or completion_tokens):
        return None
    input_rate, output_rate = rates
    return (prompt_tokens * input_rate + completion_tokens * output_rate) / 1_000_000


def cost_report(repo_filter=None, since=None, until=None):
    """Tokens and money per model over the window.

    The tokens are the ledger's and are always reported; the money exists only
    where a rate does. ``total`` is None when nothing in the window was priced,
    which is a different statement from a total of zero.
    """
    models = {}
    unpriced = []
    total = None

    for row in _execution_rows(repo_filter, since, until):
        provider = row.get("provider") or ""
        model = row.get("model") or ""
        # Nothing to price and nothing to report: a linter run spends no
        # tokens, and listing it as a model with a cost of zero would pad the
        # section with rows that cannot be spent on.
        if not _row_tokens(row):
            continue
        entry = models.setdefault(
            (provider, model),
            {
                "model": model,
                "provider": provider,
                "tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost": None,
            },
        )

        prompt = row.get("prompt_tokens") or 0
        completion = row.get("completion_tokens") or 0
        entry["prompt_tokens"] += prompt
        entry["completion_tokens"] += completion
        entry["tokens"] += _row_tokens(row)

        amount = estimate_cost(provider, model, prompt, completion)
        if amount is None:
            label = model or provider
            if label and label not in unpriced:
                unpriced.append(label)
            continue
        entry["cost"] = (entry["cost"] or 0.0) + amount
        total = (total or 0.0) + amount

    return {
        "currency": get_metrics_currency(),
        "models": sorted(models.values(), key=lambda m: m["tokens"], reverse=True),
        "total": total,
        "unpriced": unpriced,
    }


# ---------------------------------------------------------------------------
# Modules, providers, quality
# ---------------------------------------------------------------------------


def _row_modules(row):
    """The module list a row carries, or [] — the column is JSON, or NULL."""
    raw = row.get("modules")
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    if not isinstance(parsed, list):
        return []
    return [str(name) for name in parsed if str(name or "").strip()]


def module_debt(repo_filter=None, since=None, until=None):
    """How much of the window's work touched each module.

    ``modules`` holds every distinct two-segment directory a diff touched, so
    an execution that edited ``src/ui`` and ``src/fix`` counts once under each:
    these are touches, not executions, and their sum can exceed the number of
    rows. Executions with no diff in hand — the linter, blame, hooks — carry no
    module at all and are counted apart instead of being attributed to a
    module they never touched.
    """
    modules = {}
    unmapped = {"executions": 0, "tokens": 0}

    for row in _execution_rows(repo_filter, since, until):
        names = _row_modules(row)
        if not names:
            unmapped["executions"] += 1
            unmapped["tokens"] += _row_tokens(row)
            continue
        for name in names:
            entry = modules.setdefault(
                name,
                {"module": name, "executions": 0, "tokens": 0, "duration_ms": 0},
            )
            entry["executions"] += 1
            entry["tokens"] += _row_tokens(row)
            entry["duration_ms"] += row.get("duration_ms") or 0

    # Ties break on the name so two refreshes of the same ledger cannot show
    # the same numbers in a different order.
    ordered = sorted(
        modules.values(),
        key=lambda m: (-m["executions"], -m["tokens"], m["module"]),
    )
    return {"modules": ordered, "unmapped": unmapped}


def provider_breakdown(repo_filter=None, since=None, until=None):
    """Which provider and which model did the work, most used first.

    ``local`` is a row where no AI was involved at all — the linter, the hooks
    — so it is a real answer to "who did this work", not noise to be filtered.
    """
    def _rows(column, label):
        return [
            {
                label: key or "",
                "executions": totals["count"],
                "tokens": totals["tokens"],
                "duration_ms": totals["duration_ms"],
            }
            for key, totals in aggregate_by(
                column, repo_filter=repo_filter, since=since, until=until
            )
        ]

    return {"providers": _rows("provider", "provider"), "models": _rows("model", "model")}


def quality_report(repo_filter=None, since=None, until=None):
    """How the runs went: the linter's pass rate and the map-reduce rate.

    Both numbers were recorded from the first release and never computed. Each
    rate carries its own base, because they do not share one: only a linter run
    can pass the linter, and only a call the provider answered can have been
    chunked. A cache hit never reached the provider, and counting it as "did
    not chunk" would report a rate over calls that never happened.
    """
    linter_runs = 0
    linter_passed = 0
    linter_warnings = 0
    answered = 0
    chunked = 0

    for row in _execution_rows(repo_filter, since, until):
        if row.get("command") == "linter":
            linter_runs += 1
            errors = row.get("linter_errors") or 0
            linter_warnings += row.get("linter_warnings") or 0
            if not errors:
                linter_passed += 1
        # The provider's own token count is the mark of a call it answered:
        # rows without one are cache hits and local work.
        if (row.get("tokens_actual") or 0) > 0:
            answered += 1
            if row.get("map_reduce"):
                chunked += 1

    return {
        "linter": {
            "runs": linter_runs,
            "passed": linter_passed,
            "warnings": linter_warnings,
            "pass_rate": (linter_passed / linter_runs) if linter_runs else None,
        },
        "map_reduce": {
            "answered": answered,
            "chunked": chunked,
            "rate": (chunked / answered) if answered else None,
        },
    }


# ---------------------------------------------------------------------------
# Cycle — the one metric the forge answers, not the ledger
# ---------------------------------------------------------------------------

# The four answers this metric can give. ``empty`` is a real answer ("the forge
# looked and there is nothing in the window"); the other three are the metric
# not existing, and each says why, because a cycle of zero and a cycle nobody
# could measure must never look the same on screen.
CYCLE_OK = "ok"
CYCLE_EMPTY = "empty"
CYCLE_UNAVAILABLE = "unavailable"
CYCLE_UNSUPPORTED = "unsupported"

# What a bare `gitpr metrics` reads for the cycle. Not a hidden narrowing: the
# section prints the window it used. Without it, "no window asked for" would
# mean paging every merged pull request the repository ever had.
CYCLE_DEFAULT_DAYS = 30


def _cycle_window(since, until):
    """The window the forge is asked about, and how to say it in one phrase."""
    if since or until:
        return since, until, f"{since or '…'} → {until or '…'}"
    start, end = resolve_window(days=CYCLE_DEFAULT_DAYS)
    return start, end, __("last {days} days", days=CYCLE_DEFAULT_DAYS)


def _origin_remote():
    """The origin remote URL of the working copy, or "" when there is none."""
    try:
        completed = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return (completed.stdout or "").strip()


def _parse_timestamp(value):
    """An ISO 8601 timestamp as an aware datetime, or None when unusable."""
    text = str(value or "").strip()
    if not text:
        return None
    # Python 3.10's fromisoformat does not read the trailing "Z" every forge
    # writes, so the offset is spelled out before parsing.
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def cycle_report(repo_filter=None, since=None, until=None):
    """How long the merged pull requests of the window took, from the forge.

    The only metric here that does not come from the ledger, and it cannot:
    the ledger records what GitPR ran on this machine, while a pull request is
    merged on the forge, by people who never ran GitPR. So this one needs a
    token and the network, and it is the one that can come back with nothing
    for a reason that is not "nothing happened" — which is why the reason
    travels with the answer instead of the section quietly emptying.

    ``repo_filter`` is accepted for signature parity with the other readers and
    deliberately unused: it selects rows of the *ledger*, while the forge
    answers about the repository the user is standing in. The section names
    that repository so the two scopes cannot be confused on screen.

    Every failure degrades to a status, never to an exception: a metrics
    section is not worth a stack trace in the middle of a summary.
    """
    remote = _origin_remote()
    if not remote:
        return _cycle_unavailable(__("this directory has no origin remote"))

    try:
        from src.config import get_scm_settings
        from src.infrastructure.scm.factory import resolve_scm_provider

        provider = resolve_scm_provider(get_scm_settings())
        repo = provider.parse_repo_ref(remote)
    except Exception as error:  # unparsable remote, unusable configuration
        return _cycle_unavailable(str(error))

    answer = {
        "status": CYCLE_OK,
        "reason": "",
        "provider": provider.name,
        "repo": repo.display,
        "window": "",
        "count": 0,
        "average_hours": None,
        "median_hours": None,
        "slowest": [],
    }

    # Declared before the network call, in the same discipline as
    # supports_reviewable_diff: a forge that cannot answer says so instead of
    # being asked and returning something plausible. Bitbucket publishes no
    # merge date, so a cycle computed from its rows would be measuring the
    # wrong interval.
    if not getattr(provider, "supports_merged_dates", True):
        answer["status"] = CYCLE_UNSUPPORTED
        answer["reason"] = __(
            "{provider} publishes no merge date, so the cycle cannot be measured.",
            provider=provider.name,
        )
        return answer

    since, until, answer["window"] = _cycle_window(since, until)
    try:
        pulls = provider.list_pull_requests(
            repo, state="merged", since=since, until=until
        )
    except ScmProviderError as error:
        return _cycle_unavailable(str(error))

    durations = []
    for pull in pulls:
        created = _parse_timestamp(pull.created_at)
        merged = _parse_timestamp(pull.merged_at)
        if created is None or merged is None:
            continue
        # A merge that precedes its own creation is a clock the forge got
        # wrong, not a negative cycle to average in.
        hours = (merged - created).total_seconds() / 3600
        if hours < 0:
            continue
        durations.append(hours)
        answer["slowest"].append({"number": pull.number, "hours": hours})

    answer["count"] = len(durations)
    if not durations:
        # The forge answered and the window is empty. Pull requests it listed
        # without a usable pair of dates are not counted either — an interval
        # nobody published is not a short one.
        answer["status"] = CYCLE_EMPTY
        return answer

    answer["average_hours"] = sum(durations) / len(durations)
    answer["median_hours"] = statistics.median(durations)
    answer["slowest"].sort(key=lambda item: item["hours"], reverse=True)
    return answer


def _cycle_unavailable(reason):
    """The shape of "this metric was not computed", with the reason attached."""
    return {
        "status": CYCLE_UNAVAILABLE,
        "reason": reason,
        "provider": "",
        "repo": "",
        "window": "",
        "count": 0,
        "average_hours": None,
        "median_hours": None,
        "slowest": [],
    }


# ---------------------------------------------------------------------------
# Rendering — one rendering per metric, whichever surface reads it
# ---------------------------------------------------------------------------
# Section lines are (style, text) pairs, and the style names an intent rather
# than a colour: the terminal maps it onto click's palette and the dashboard
# onto Textual markup. Each metric is rendered once here and shown by both, so
# the two surfaces cannot drift into telling different stories about one
# ledger — which is what the four-sections requirement is really asking for.
TITLE = "title"
PLAIN = "plain"
WARN = "warn"


def _money(amount, currency):
    """Money in the ledger's currency, or the honest absence of a rate."""
    if amount is None:
        return __("no rate configured")
    return f"{currency} {amount:,.2f}"


def cost_lines(cost):
    """The cost section: tokens always, money only where a rate exists."""
    if not cost or not cost["models"]:
        return []

    currency = cost["currency"]
    tokens = sum(model["tokens"] for model in cost["models"])
    # A total that leaves models out is not the total: say so on the same line
    # rather than letting a sum of the priced rows read as the whole bill. With
    # nothing priced at all there is no total to qualify — the value itself
    # already says no rate was configured.
    partial = bool(cost["unpriced"]) and cost["total"] is not None
    label = __("Total (partial)") if partial else __("Total")

    lines = [
        (TITLE, f"💰 {__('Cost')}"),
        (
            PLAIN,
            f"  {__('Tokens')}: {tokens:,}  |  {label}: {_money(cost['total'], currency)}",
        ),
    ]
    for model in cost["models"]:
        lines.append(
            (
                PLAIN,
                f"  {model['model'] or model['provider']}: {model['tokens']:,}"
                f" — {_money(model['cost'], currency)}",
            )
        )
    if cost["unpriced"]:
        lines.append(
            (
                WARN,
                "  "
                + __(
                    "Rates come from GITPR_METRICS_PRICE_<MODEL>_INPUT / _OUTPUT in ~/.gitpr/.env."
                ),
            )
        )
    if cost["total"] is not None:
        lines.append(
            (
                PLAIN,
                "  " + __("Converted at today's rates — an approximation for older tokens."),
            )
        )
    return lines


def quality_lines(quality):
    """The quality section: two rates, each over the runs that can answer it."""
    if not quality:
        return []
    linter = quality["linter"]
    chunking = quality["map_reduce"]
    if not (linter["runs"] or chunking["answered"]):
        return []

    lines = [(TITLE, f"🧪 {__('Quality')}")]
    if linter["runs"]:
        lines.append(
            (
                PLAIN,
                f"  {__('Linter pass rate')}: {linter['passed']}/{linter['runs']}"
                f" ({linter['pass_rate']:.0%})",
            )
        )
    if chunking["answered"]:
        lines.append(
            (
                PLAIN,
                f"  {__('Map-reduce')}: {chunking['chunked']}/{chunking['answered']}"
                f" ({chunking['rate']:.0%})",
            )
        )
    return lines


def _duration(hours):
    """An interval in the unit that tells the truth about it.

    A single unit cannot serve this metric. Measured on a real repository whose
    pull requests are opened and merged minutes apart, "Median: 0.0 days" is
    arithmetically correct and reads as a broken panel — and the same section
    on a repository that takes a week per pull request would spend its digits
    on minutes nobody waits for. So the value picks its own unit.

    The unit suffixes are symbols, not prose: "min", "h", "d" and "s" are the
    same four in every language GitPR ships, so they are not translated and do
    not belong in the language files.
    """
    seconds = hours * 3600
    if seconds < 60:
        return f"{seconds:.0f} s"
    if hours < 1:
        return f"{seconds / 60:.0f} min"
    if hours < 48:
        return f"{hours:.1f} h"
    return f"{hours / 24:.1f} d"


def cycle_lines(cycle, limit=3):
    """The cycle section: how long the merged pull requests took, forge-side.

    The header names the repository and the window because this is the one
    section whose scope is not the ledger's: read next to a summary that says
    "All repositories", a bare number would look like it covered them all.
    """
    if not cycle:
        return []

    if cycle["status"] == CYCLE_UNAVAILABLE:
        return [
            (TITLE, f"⏱ {__('Cycle')}"),
            (WARN, "  " + __("Not read: {reason}", reason=cycle["reason"])),
        ]

    scope = f" · {cycle['repo']}" if cycle["repo"] else ""
    window = f" · {cycle['window']}" if cycle.get("window") else ""
    lines = [(TITLE, f"⏱ {__('Cycle')}{scope}{window}")]

    if cycle["status"] == CYCLE_UNSUPPORTED:
        lines.append((WARN, "  " + cycle["reason"]))
        return lines

    if cycle["status"] == CYCLE_EMPTY:
        lines.append(
            (PLAIN, "  " + __("No pull request was merged in this window."))
        )
        return lines

    lines.append(
        (
            PLAIN,
            f"  {__('Merged pull requests')}: {cycle['count']}"
            f"  |  {__('Average')}: {_duration(cycle['average_hours'])}"
            f"  |  {__('Median')}: {_duration(cycle['median_hours'])}",
        )
    )
    for pull in cycle["slowest"][:limit]:
        lines.append(
            (PLAIN, f"  #{pull['number']}: {_duration(pull['hours'])}")
        )
    return lines


def module_lines(debt, limit=8):
    """The module section: where the work went, by directory."""
    if not debt or not debt["modules"]:
        return []

    lines = [(TITLE, f"🧩 {__('Modules')}")]
    for module in debt["modules"][:limit]:
        lines.append(
            (PLAIN, f"  {module['module']}: {module['executions']} · {module['tokens']:,}")
        )
    if len(debt["modules"]) > limit:
        lines.append((PLAIN, f"  {__('+{count} more', count=len(debt['modules']) - limit)}"))
    if debt["unmapped"]["executions"]:
        lines.append(
            (
                PLAIN,
                f"  ({__('no module')}): {debt['unmapped']['executions']}"
                f" · {debt['unmapped']['tokens']:,}",
            )
        )
    return lines


def provider_lines(breakdown, limit=5):
    """The provider section: who answered, including "nobody" (local work)."""
    if not breakdown or not breakdown["providers"]:
        return []

    lines = [(TITLE, f"🤖 {__('Providers')}")]
    for provider in breakdown["providers"][:limit]:
        name = provider["provider"] or __("(unknown)")
        lines.append(
            (PLAIN, f"  {name}: {provider['executions']} · {provider['tokens']:,}")
        )
    return lines


# ---------------------------------------------------------------------------
# Export — the human-readable surface
# ---------------------------------------------------------------------------


def export_metrics(output_dir=None, repo_filter=None, since=None, until=None):
    """Writes the unexported executions to CSV + JSON.

    Reads the ledger, which replaced a state file that listed the exported ids
    of **every** repository at once: exporting repo A marked repo B's events as
    exported, so B's export answered "nothing new" forever. The mark now lives
    on the row it belongs to.

    Returns (csv_path, json_path, event_count).
    """
    events = ledger.list_events_for_export(
        repo=repo_filter or None, since=since, until=until
    )
    if not events:
        return None, None, 0

    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), ".gitpr", "metrics", "export")
    os.makedirs(output_dir, exist_ok=True)

    today_str = date.today().strftime("%Y-%m-%d")
    csv_path = os.path.join(output_dir, f"gitpr_metrics_{today_str}.csv")
    json_path = os.path.join(output_dir, f"gitpr_metrics_{today_str}.json")

    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(CSV_COLUMNS)
        for event in events:
            writer.writerow([_flat(event.get(column, "")) for column in CSV_COLUMNS])

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(events, handle, ensure_ascii=False, indent=2)

    ledger.mark_exported([event["id"] for event in events])
    return csv_path, json_path, len(events)


def _flat(value):
    """A CSV cell: JSON lists keep their brackets, None becomes empty."""
    if value is None:
        return ""
    return str(value)


# ---------------------------------------------------------------------------
# Purge and prune
# ---------------------------------------------------------------------------


def purge_metrics():
    """Deletes every ledger row and every legacy event file. Returns the count.

    The destructive path, and only ever reached from an explicit confirmation.
    """
    removed = ledger.purge_events()
    for path in ledger.pending_legacy_files():
        try:
            os.remove(path)
            removed += 1
        except Exception:
            pass
    return removed


def prune_metrics(before, source=None):
    """Removes rows older than *before* (YYYY-MM-DD). Returns the count.

    There is no automatic expiry by design: the ledger answers "what did we
    spend this year", and a calendar that deletes on its own would change that
    answer without anyone asking.
    """
    return ledger.prune_before(_as_day(before) or before, source=source)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def show_metrics_summary(repo_filter=None, since=None, until=None):
    """Summarizes the ledger for the CLI.

    Counts rows, not files. The number it replaced was produced by walking
    ``~/.gitpr/metrics`` for ``*.json``, which counted the state file itself and
    every legacy file still on disk — 1749 "events" on the machine this was
    measured on, against 8 real ones.
    """
    window = {"repo": repo_filter or None, "since": since, "until": until}
    executions = ledger.count_events(source=ledger.SOURCE_EXECUTION, **window)
    backfilled = ledger.count_events(source=ledger.SOURCE_BACKFILL, **window)
    legacy = len(ledger.pending_legacy_files())

    return {
        "total_events": executions,
        "backfilled_events": backfilled,
        "pending_legacy_files": legacy,
        "disk_usage": ledger.disk_usage(),
        "path": get_metrics_dir(),
        "db_path": str(ledger.get_ledger_path()),
        "exists": ledger.ledger_exists(),
    }


def aggregate_by(column, repo_filter=None, since=None, until=None, source=None,
                 include_backfill=False):
    """Groups executions by one column, most frequent first.

    Used by the dashboard sections and the MCP tool so that each metric is
    computed once and rendered wherever it is needed.
    """
    rows = ledger.query_events(
        repo=repo_filter or None,
        since=since,
        until=until,
        source=source,
        order="ASC",
    )
    if not include_backfill and source is None:
        rows = [r for r in rows if r.get("source") == ledger.SOURCE_EXECUTION]

    totals = {}
    for row in rows:
        key = row.get(column) or ""
        entry = totals.setdefault(key, {"count": 0, "tokens": 0, "duration_ms": 0})
        entry["count"] += 1
        entry["tokens"] += row.get("tokens_actual") or row.get("tokens_estimated") or 0
        entry["duration_ms"] += row.get("duration_ms") or 0

    return sorted(totals.items(), key=lambda item: item[1]["count"], reverse=True)
