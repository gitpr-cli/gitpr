# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(metrics): replace JSON telemetry with local SQLite ledger
```

---

## 🎯 Summary

Replaces the fire-and-forget per-command JSON telemetry files (written from a daemon thread) and the flat `--metrics/--export/--purge/--hook-event/--dashboard` flags with a durable, synchronous SQLite ledger under `~/.gitpr/metrics/telemetry.db`, exposed through a proper `gitpr metrics` subcommand group. Short-lived processes such as hook events no longer lose rows on exit, the cache-based enrichment (which silently zeroed `tokens_actual` for `fullreview`/`filereview` due to three divergent command→cache-folder maps) is removed by copying token/model/provider metadata into the row at write time, and repositories that merge via merge commits now get correct PR attribution across all supported forges.

## 🛠️ Technical Changes

- **New ledger module (`src/ledger.py`)** — SQLite schema v1 with `PRAGMA user_version` versioning, WAL journaling and `synchronous=FULL`; sync `record_event()`, read helpers (`query_events`, `count_events`, `disk_usage`), retention (`purge_events`, `prune_before`), per-row export bookkeeping, bundle transport (`build_bundle`/`merge_bundles` via ATTACH/DETACH), and legacy absorption (`absorb_legacy_files`, `backfill_from_cache`) guarded by a `SKIP_MARKER` so migration is never re-prompted.
- **New git identity module (`src/infrastructure/git/identity.py`)** — single source of truth for repo label, branch and author; reads the three config keys in one subprocess and works on all forges (not just GitHub). Deliberately avoids constructing an SCM provider during telemetry writes.
- **SCM providers add `list_pull_requests(repo, state, since, until)`** — GitHub, GitLab, Bitbucket and Azure DevOps translate canonical states (`open`/`merged`/`closed`/`all`), paginate on their native cursors, filter by an inclusive date window and early-stop where possible. `PullRequestResult` gains `created_at`/`merged_at`/`closed_at`, a `within_window()` helper and a `supports_merged_dates` capability flag.
- **Merge-commit PR detection (`src/commit_classifier.py`)** — new `pr_number_from_merge()` parses GitHub, Bitbucket, Azure DevOps and GitLab merge subjects/bodies so PRs merged through merge commits (not squashes) are attributed.
- **Metrics pricing (`src/config.py`)** — `DEFAULT_MODEL_PRICES` (DeepSeek, Gemini), `GITPR_METRICS_PRICE_<MODEL>_INPUT/_OUTPUT` and `GITPR_METRICS_CURRENCY` overrides, `get_model_price()` returning `None` when no rate is known (distinct from a configured `0.0`), and zero-cost local providers.
- **Metrics rewrite (`src/metrics.py`)** — removes `enrich_metrics_from_cache()`/`load_cache_token_summary()`; adds `cost_report`/`cost_lines`, `quality_report`/`quality_lines`, `module_debt`/`module_lines`, `provider_breakdown`/`provider_lines`, `cycle_report`/`cycle_lines`, `resolve_window`, `aggregate_by` and `prune_metrics` so CLI and dashboard share a single rendering per metric.
- **UI (`src/ui/metrics_app.py`, `src/ui/metrics_migration_app.py`)** — dashboard loads from the ledger (file scan kept only as a pre-migration bridge) and renders the five new sections; new wizard imports legacy event files and/or reconstructs from the AI cache.
- **Release engine (`src/release_engine.py`)** — adds `_collect_merge_pr_map()` to map commit hashes to PR numbers parsed from merge-commit messages.
- **Core fixes (`src/core.py`)** — removes two duplicated cache-folder maps (the cause of `tokens_actual` always being `0`), aggregates `provider`/`model` across map-reduce chunks, forwards `meta`/`modules` to `log_command_metric`, and decodes git output with `errors="replace"`.
- **Git hooks rewritten** — `post-checkout`, `post-merge` and `pre-push` templates call `gitpr --quiet metrics hook-event <name>` guarded by `command -v gitpr` and `|| true`, dropping the GitHub-only bash repo resolution that wrote events under unusable folder names.
- **CLI rework (`src/main.py`)** — flat metrics flags deleted in favor of a `metrics` group with `export`, `bundle`, `merge`, `dashboard`, `migrate`, `prune`, `purge` and a hidden `hook-event`, shared `--days/--since/--until` window options, and a one-time migration prompt at startup.
- **MCP tool (`src/mcp_server.py`)** — new read-only `get_usage_metrics(repo, since, until)` tool exposing summary, cost, quality, module debt and provider breakdown (catalog now 15 tools).
- **i18n** — ~200 new strings across `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`; obsolete keys removed; `scripts/fix_mangled_i18n_keys.py` updated for the renamed purge message.
- **Housekeeping & tests** — `.gitignore` excludes `.gitpr/metrics/` while keeping `.gitpr/skill/` tracked; tests expanded across SCM providers, commit classifier, MCP server, ledger/metrics, release engine merge mapping and usage log.

## ⚠️ Impact/Warnings

- **Breaking CLI change:** `--metrics`, `--export`, `--purge`, `--hook-event` and `--dashboard` no longer exist; callers must migrate to `gitpr metrics <action>`.
- **New environment variables:** `GITPR_METRICS_PRICE_<MODEL>_INPUT`, `GITPR_METRICS_PRICE_<MODEL>_OUTPUT` and `GITPR_METRICS_CURRENCY`.
- **Database:** no user-facing migration — the SQLite file is created on first write. Legacy JSON event files are optionally absorbed via the one-time migration wizard (declinable with a persistent skip marker).
- **Installed Git hooks must be reinstalled** to gain the forge-agnostic repo resolution.
- **Behavioral change:** token/model/provider data is now captured at write time instead of enriched from cache, so historical cache-based enrichment is no longer applied to new rows.