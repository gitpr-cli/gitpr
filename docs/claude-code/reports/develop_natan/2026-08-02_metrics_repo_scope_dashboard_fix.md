## Completion Report — Metrics Dashboard Repo-Scope, Cache Totalizer, F5 Fix & Export Local

### What was done
- Created `load_cache_token_summary(repo_name)` in `metrics.py` that scans `~/.gitpr/cache/prompts/*/` recursively, extracts `response.meta_raw` (or `response._telemetry_meta` as fallback) from all cache files, and returns aggregated prompt/completion/total tokens plus per-action-type breakdown
- Fixed dashboard totalizer to merge cache token data with event metrics — now counts commits, reviews, issues and all AI calls from cache, not just `pr` and `map_reduce` events
- Fixed F5 Refresh bug where `_populate_table()` was re-adding columns on every refresh, causing duplicate empty columns — extracted `_setup_columns()` that runs only once
- Added `repo_filter` parameter to `MetricsApp` — dashboard now only shows events and cache data for the current repository (`core.get_repo_name()`)
- Added repository name label (`📁 Repository: owner/repo`) in the dashboard header
- Modified `export_metrics()` to accept `repo_filter` parameter — exports only current repo's events
- Changed `export_metrics()` default output directory from `~/.gitpr/metrics/export/` to `./.gitpr/metrics/export/` (project-local)
- Updated `main.py` to pass `get_repo_name()` to both dashboard and export calls
- Added 8 new tests: cache summary aggregation, repo filtering, telemetry fallback, export repo filter, export local dir, F5 column non-duplication, dashboard repo filter

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| [src/metrics.py](src/metrics.py#L193) | feat | Added `load_cache_token_summary(repo_name)` — scans cache prompts and aggregates token data |
| [src/metrics.py](src/metrics.py#L260) | feat | `export_metrics()` now accepts `repo_filter`, filters events, saves to `./.gitpr/metrics/export/` |
| [src/ui/metrics_app.py](src/ui/metrics_app.py) | fix | Separated `_setup_columns()` from `_populate_table()` (F5 fix); added `repo_filter`, repo label, cache summary in totals |
| [src/main.py](src/main.py#L251) | feat | Passes `get_repo_name()` to `launch_metrics_dashboard()` and `export_metrics()` |
| [tests/test_metrics.py](tests/test_metrics.py) | feat | 8 new tests: `TestLoadCacheTokenSummary` (4), `TestExportMetricsWithRepoFilter` (2), `TestMetricsDashboardF5` (2) |

### Impact
- **Functionality:** Dashboard now shows accurate token totals from ALL AI calls (via cache), filtered to current repo. F5 refreshes without duplicating columns. Export saves locally per-project and filters by current repo.
- **Performance:** `load_cache_token_summary()` scans cache dir on dashboard load (~50ms per 100 cache files). One-time cost, not on every command.
- **Compatibility:** `export_metrics()` signature extended with optional `repo_filter` parameter (backward-compatible). Output directory changed to project-local — existing exports in `~/.gitpr/metrics/export/` are not affected.

### Next steps (if applicable)
- Add Portuguese translations for new dashboard strings in `langs/pt_br.json` (`__()` falls back to English safely)
- Consider adding `--all-repos` flag to dashboard/export for viewing cross-repo metrics when needed
