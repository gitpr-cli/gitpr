# Plan: Add Duration to Cache, Progress Bar on Dashboard, and Indefinite Cache Scanning

## Context

The user wants three improvements to the metrics/dashboard system:

1. **Duration in `meta_raw`**: Currently `response.meta_raw` in cache files only stores `{prompt_tokens, completion_tokens, total_tokens}`. The actual wall-clock time of AI calls is not recorded anywhere — the dashboard's "Duration (ms)" column always shows `0`. The user wants real timing data captured and persisted.

2. **Progress bar on dashboard open**: The dashboard (`MetricsApp`) currently loads silently with no visual feedback during the scan of `~/.gitpr/cache/prompts/` and `~/.gitpr/metrics/`. The user wants a progress bar showing the file scanning progress.

3. **Indefinite range + processed-files tracking**: The dashboard should search ALL files in `~/.gitpr/cache/prompts/` (no date filter, no cap). After loading, create a list of already-processed files in `./.gitpr/metrics/` (project-local directory).

## Design

### Change 1: Add `duration_ms` to `meta_raw`

**File**: `src/ai_providers.py` — `call_ai_model()`

- Capture `start = time.perf_counter()` after spinner starts (before the retry loop).
- After successful API response (but before `result_json["_telemetry_meta"] = meta_raw`), calculate `elapsed_ms = int((time.perf_counter() - start) * 1000)`.
- Add `"duration_ms": elapsed_ms` to the `meta_raw` dict alongside token counts.
- This flows downstream: `meta_raw` → `result_json["_telemetry_meta"]` → popped by `core.py` → `save_cached_response(meta_raw=total_meta)` → cache file `response.meta_raw.duration_ms` → readable by `load_cache_token_summary()` and `enrich_metrics_from_cache()`.

**File**: `src/core.py` — `generate_pr_content()`

- Capture `t_start = time.perf_counter()` at the beginning of the function (after cache check, before AI call).
- After the full pipeline completes (cache hit or AI call), compute `duration_ms = int((time.perf_counter() - t_start) * 1000)`.
- Pass `duration_ms` to both calls to `log_command_metric()` (success and error paths).
- For cache hits: also pass `duration_ms` (should be near-zero since it's just a file read).

**File**: `src/issue_engine.py`

- Capture `start = time.perf_counter()` before the AI call.
- Pass `duration_ms` to `log_command_metric()` calls (cache hit and success paths).

### Change 2: Progress bar during dashboard cache scan

**File**: `src/ui/metrics_app.py` — `MetricsApp`

Add a loading progress indicator during the scan phase:

- Add a `#progress` `Static` widget in `compose()` (hidden by default, `display: none` in CSS).
- In `on_mount()`, instead of calling `_load_metrics()` directly:
  1. Show the progress label with "Scanning cache files..."
  2. Use `self.set_interval(0.05, self._scan_tick)` to pump progress updates.
  3. Delegate the actual file walking to a method that counts files first, then processes them.
- After scanning completes, hide the progress widget, populate the table, and update the summary.
- The progress bar approach: since scanning is fast (~100ms for 600 files), use a count-based label like `"Scanning: 145/656 files from ~/.gitpr/cache/prompts/"` updated via `set_interval` ticks, rather than a full `ProgressBar` widget (which requires knowing the total upfront and adds complexity for a sub-second operation).

Alternative simpler approach (recommended):
- Pre-count files with a quick `glob` before scanning.
- Show a `Static` label that updates with progress count during the scan loop.
- No need for threads/workers — the scan is fast. Just update the label periodically.

### Change 3: Indefinite range and processed-files tracking

**File**: `src/metrics.py` — new function `scan_cache_files_for_dashboard(repo_filter=None)`

Create a new function that:
1. Scans ALL `~/.gitpr/cache/prompts/*/*.json` files (no date filter, no cap).
2. For each file, extracts: `repo`, `branch`, `datetime`, `action_type`, `meta_raw` (tokens + duration), `md5`.
3. Returns a consolidated list of cache entries enriched with token and duration data.

**File**: `src/metrics.py` — new function `get_processed_cache_state()` / `mark_cache_files_processed()`

- State file: `./.gitpr/metrics/processed_cache.json` (project-local).
- Format: `{"processed_md5s": [...], "last_scan": "ISO datetime", "total_processed": N}`.
- `get_processed_cache_state()`: reads the file, returns the set of processed MD5s.
- `mark_cache_files_processed(md5_list)`: writes/updates the state file with new MD5s.

**File**: `src/ui/metrics_app.py` — `_load_metrics()`

- Call `scan_cache_files_for_dashboard(repo_filter)` to get ALL cache entries.
- Call `get_processed_cache_state()` to check which are new.
- After loading, call `mark_cache_files_processed(all_md5s)` to mark them.
- Display both cache entries AND metric events in the DataTable.
- Remove the 100-row cap (or raise to a much higher limit like 500 with a note).

## Files to Modify

| File                    | Change | Description                                                                                                                         |
| ----------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `src/ai_providers.py`   | feat   | Add `duration_ms` to `meta_raw` in `call_ai_model()`                                                                                |
| `src/core.py`           | feat   | Capture command duration, pass to `log_command_metric()`                                                                            |
| `src/issue_engine.py`   | feat   | Capture command duration, pass to `log_command_metric()`                                                                            |
| `src/metrics.py`        | feat   | Add `scan_cache_files_for_dashboard()`, `get_processed_cache_state()`, `mark_cache_files_processed()`                               |
| `src/ui/metrics_app.py` | feat   | Add progress bar during scan; use new scanning function; show cache entries in DataTable; remove 100-row cap; track processed files |

## Verification

1. **Unit tests**: Run `pipenv run pytest -v` to ensure existing tests pass.
2. **Duration in cache**: Run `gitpr -c` to generate a commit message, then inspect `~/.gitpr/cache/prompts/commit/*.json` — verify `response.meta_raw.duration_ms` is present and > 0.
3. **Dashboard progress bar**: Run `gitpr --dashboard` — verify a progress label appears during scanning and disappears after loading.
4. **Processed files tracking**: After running the dashboard, verify `./.gitpr/metrics/processed_cache.json` exists and contains processed MD5s.
5. **Dashboard data**: Verify the DataTable shows data from all cache files, not just the last 100, and the "Duration (ms)" column shows real values.
