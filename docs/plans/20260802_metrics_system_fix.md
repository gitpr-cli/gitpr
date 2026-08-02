# Metrics System Fix — Implementation Plan

## Context

The GitPR metrics/telemetry system (`src/metrics.py`) has three critical issues preventing it from working correctly:

1. **Commands not logging metrics**: Several CLI commands (skill, installhooks, update, install, blame standalone, issue generation, chat) never call `log_command_metric()`, so they produce no telemetry data.
2. **Export ignores cache data**: `export_metrics()` only scans `~/.gitpr/metrics/` for `.json` event files but never looks at `~/.gitpr/cache/prompts/` where the real AI token usage (`meta_raw`) is stored inside cached responses.
3. **Dashboard broken**: `MetricsApp` (Textual TUI) fails to display data correctly — DataTable API issues, missing error recovery, no feedback on empty state.

## Plan

### 1. Add metric logging to all missing command paths (`src/main.py`)

Add `log_command_metric()` calls at the return/success points of every command that lacks them. Follow the existing pattern at `main.py:352`:

| Command                | Location in `main.py`                                 | `command` value  | Extra kwargs  |
| ---------------------- | ----------------------------------------------------- | ---------------- | ------------- |
| `--skill`              | After `generate_skill_template()` returns (~line 377) | `"skill"`        | —             |
| `--installhooks`       | After successful install (~line 381)                  | `"installhooks"` | —             |
| `--update`             | After `check_and_update()` returns (~line 366)        | `"update"`       | —             |
| `--install`            | After `run_install_wizard()` returns (~line 371)      | `"install"`      | —             |
| `--blame` (standalone) | After blame report output (~line 460 area)            | `"blame"`        | —             |
| `--chat`               | After chat TUI exits (~line 604 area)                 | `"chat"`         | provider info |

All use `status="success"` with `provider="git"` for non-AI commands.

### 2. Add metric logging to issue engine (`src/issue_engine.py`)

Inside `generate_issue_content()`, after the AI call succeeds:
- Extract `_telemetry_meta` from the AI response (same pattern as `core.py:371`)
- Pass `meta_raw` to `save_cached_response()` (currently not passing it — line 85)
- Call `log_command_metric()` with token data, matching the pattern in `core.py:377-384`

### 3. Add metric logging for GitHub issue creation (`src/ui/issue_app.py`)

In `action_create_issue()`, add `log_command_metric()` after the API call:
- `command="issue:github_create"`, `status="success"/"error"` based on HTTP response
- Track `status_code` as extra kwarg

### 4. Enrich export with cache `meta_raw` data (`src/metrics.py`)

Add `_enrich_from_cache()` helper function that:
1. Scans `~/.gitpr/cache/prompts/` recursively for `*.json` files
2. For each cache file, reads `response.meta_raw` (prompt_tokens, completion_tokens, total_tokens)
3. Returns a dict keyed by `(action_type, datetime)` for matching against metric events

Modify `export_metrics()` to call `_enrich_from_cache()` and merge token data into events where `tokens_estimated == 0` or where a matching cache entry is found. Also add `prompt_tokens`, `completion_tokens`, `total_tokens` as explicit columns in the CSV.

### 5. Fix Metrics Dashboard (`src/ui/metrics_app.py`)

Issues to fix:
- **DataTable columns**: Add columns with proper typing. Current code adds columns as strings in a loop but Textual may need explicit column keys.
- **Error handling**: Wrap `_load_metrics()` in try/except to prevent crash on malformed JSON.
- **Empty state**: Already handled but ensure the message is visible with proper styling.
- **Sort stability**: Ensure events with missing timestamps don't cause errors.
- **Row count**: The current 100-row limit is fine but should be noted in the status bar.

Key fix: Use `table.add_column(label, key=key)` and `table.add_row({key: value, ...})` pattern for safer DataTable usage if the positional API is buggy.

Also update `src/main.py` line 273-276: Allow `--dashboard` to work BOTH standalone (`gitpr --dashboard`) AND combined with `--metrics --dashboard`. Currently `--export` and `--purge` require `--metrics` prefix (`if metrics and export:`), while `--dashboard` is standalone. Make the dashboard also respond to the combined form: `if show_dashboard or (metrics and show_dashboard):` for backward compatibility.

**Textual version**: 8.2.8 — The `DataTable.add_column(label)` and `DataTable.add_row(*cells)` API should work. The main dashboard issue is likely empty data from missing metric logging, not an API incompatibility.

### 6. Create comprehensive tests (`tests/test_metrics.py`)

Test cases:
- `test_log_local_metric_creates_file` — mock `_save_metric_async`, verify file creation
- `test_log_command_metric_calls_log_local` — verify parameter forwarding and auto-provider detection
- `test_export_metrics_empty_dir` — returns `(None, None, 0)`
- `test_export_metrics_with_events` — creates temp metric files, verifies CSV/JSON output
- `test_export_metrics_skips_exported` — verifies config.json UUID tracking
- `test_export_metrics_enriches_from_cache` — creates mock cache files with meta_raw, verifies token data in output
- `test_enrich_from_cache_extracts_meta_raw` — unit test for the new enrichment function
- `test_purge_metrics_removes_files` — count-based purge verification
- `test_show_metrics_summary` — verify summary dict structure
- `test_get_metrics_dir_returns_path` — path correctness

## Files to modify

| File                    | Changes                                                                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `src/metrics.py`        | Add `_enrich_from_cache()`, modify `export_metrics()`, fix `show_metrics_summary()`                                                 |
| `src/main.py`           | Add `log_command_metric()` calls for skill, installhooks, update, install, blame, chat; fix `--dashboard` combined with `--metrics` |
| `src/issue_engine.py`   | Extract `_telemetry_meta`, pass `meta_raw` to cache, call `log_command_metric()`                                                    |
| `src/ui/issue_app.py`   | Add `log_command_metric()` after GitHub API issue creation                                                                          |
| `src/ui/metrics_app.py` | Fix DataTable API, add error handling, improve empty state                                                                          |
| `tests/test_metrics.py` | New file — comprehensive test suite                                                                                                 |

## Verification

1. Run `pytest tests/test_metrics.py -v` — all tests pass
2. Run `python run.py --metrics` — shows summary (even if empty)
3. Run `python run.py --dashboard` — TUI opens without crashing
4. Run `python run.py --metrics --export` — exports without errors
5. Run `python run.py -c` then verify `~/.gitpr/metrics/` has a new JSON file
6. Run `python -m pytest tests/ -v` — existing 79 tests still pass, 0 regressions
