# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(metrics): replace JSON event files with SQLite ledger
```

---

## 🎯 Summary

Telemetry was previously persisted as per-command JSON event files and later joined back to AI cache data through a fragile post-hoc heuristic that matched events by (repo, branch, action, minute) across three diverging command→folder maps. That join was unreliable, caused cross-repo data loss on export, and routinely reported `tokens_actual = 0`. This PR replaces the whole pipeline with a local SQLite usage ledger in `~/.gitpr/metrics/telemetry.db`, written synchronously at command time, and reworks the metrics surface (CLI, TUI, MCP) and the SCM pull-request listing into a forge-agnostic, testable design.

## 🛠️ Technical Changes

- **New local ledger (`src/ledger.py`)**: SQLite store with schema versioning (`SCHEMA_VERSION`, `LedgerVersionError`), UUID string keys, WAL + `synchronous=FULL`, and a `connect()` context manager. Enforces a "never born empty" invariant via `ensure_ledger()`, which only creates the DB together with legacy JSON absorption (originals moved to `~/.gitpr/metrics_legacy/`, skip marker for declined migrations, silent non-interactive path). Adds `record_event()` (synchronous, never fails the command), `backfill_from_cache()` (rows tagged `cache_backfill`, excluded from execution aggregates), export bookkeeping on the row (`mark_exported`, `list_events_for_export`), `purge_events`/`prune_before` (VACUUM after commit), and bundle transport via ATTACH/DETACH with version checks before any write.
- **Metrics rewrite (`src/metrics.py`)**: writes into the ledger synchronously instead of spawning a daemon thread; removes `enrich_metrics_from_cache()` and copies real token counts from provider metadata at write time via `log_command_metric(meta=...)`. Adds window helpers, cost estimation/aggregation, module debt, provider breakdown, quality report (linter pass rate, map-reduce rate), and an optional forge-based cycle report with explicit status codes (ok/empty/unavailable/unsupported). Shared section renderers are consumed by both CLI and TUI. Export/purge/prune now operate on rows instead of files.
- **Forge-agnostic identity (`src/infrastructure/git/identity.py`)**: single source of truth for repo label, branch and author (`GitContext`, `repo_label`, `git_identity`, `working_context`), no longer hardcoding github.com and deliberately avoiding `ScmProvider.parse_repo_ref()` to skip provider construction per command.
- **SCM providers (base, GitHub, GitLab, Bitbucket, Azure DevOps)**: `list_open_pull_requests` becomes a thin wrapper over a new paginated `list_pull_requests(state, since, until)` with canonical state mapping per forge, date fields on `PullRequestResult`, day-level `within_window()` filtering, early-stop pagination, and continuation-token/Link/X-Next-Page/next-URL handling. Adds `supports_merged_dates` (False for Bitbucket Cloud) and raises `ScmNotSupportedError` by default.
- **PR reference recovery**: new `commit_classifier.pr_number_from_merge()` extracts PR numbers from merge commits per forge; `release_engine.py` adds a second `git log --merges --reverse` pass plus a `rev-list` walk to map commit hashes to PR numbers (squash tails stay authoritative, branch syncs claim nothing).
- **CLI (`src/main.py`)**: replaces the old `--metrics/--export/--purge/--hook-event/--dashboard` flags with a `metrics` Click group (`export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge`, hidden `hook-event`) sharing `--days/--since/--until`. Adds `_may_ask_the_user()` and `ledger.configure_terminal()` to suppress TUI prompts under `--quiet`, hooks, MCP and non-TTY runs.
- **TUI (`src/ui/metrics_app.py`, `src/ui/metrics_migration_app.py`)**: dashboard reads the ledger on a worker thread and renders the shared sections; new migration wizard offers import, import + AI-cache reconstruction, or "not now", with abort semantics that never create an empty ledger over unimported files.
- **MCP (`src/mcp_server.py`)**: new read-only `get_usage_metrics` tool plus catalogue entry (now 15 tools), returning summary, cost, quality, modules and providers with a note separating `cache_backfill` rows from executions.
- **Hooks and i18n**: post-checkout, post-merge and pre-push templates rewritten to call `gitpr --quiet metrics hook-event <name>` guarded by `command -v gitpr` and `|| true`, dropping GitHub-only bash parsing. All locale files gain the new metrics keys (some untranslated with English fallback) and file-based copy is reworded to record-based.
- **Tests**: coverage for paginated `list_pull_requests` across all four forges, the `list_open_pull_requests` wrapper and `within_window`, `pr_number_from_merge`, merge-commit PR recovery in the release engine, the ledger write path (synchronous writes, idempotent export, bundle/merge, schema versioning, migration invariant), the report renderers, the migration wizard, and the MCP catalogue.

## ⚠️ Impact/Warnings

- **Storage location change**: metrics now live in `~/.gitpr/metrics/telemetry.db`; `.gitpr/metrics/` is gitignored (local exports and per-repo cache marker only).
- **Breaking CLI surface**: `--metrics/--export/--purge/--hook-event/--dashboard` are removed in favor of the `gitpr metrics` command group.
- **New environment variables**: `GITPR_METRICS_PRICE_<MODEL>_INPUT`, `GITPR_METRICS_PRICE_<MODEL>_OUTPUT` and `GITPR_METRICS_CURRENCY`. A half-configured model is never completed from the built-in table and yields `None` (tokens without money).
- **Action required**: installed git hooks must be reinstalled via `gitpr --installhooks` to pick up the new templates.
- **Migration**: `gitpr metrics migrate` is offered once; a marker records a refusal, and the legacy JSON files are only absorbed when the ledger is first created.
- No changes to existing config keys or unrelated data formats.