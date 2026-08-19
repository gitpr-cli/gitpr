# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add duration to AI calls and improve metrics dashboard
```

---

## 🎯 Summary
Adds wall-clock duration measurement to AI calls and enhances the metrics dashboard with a progress bar, indefinite cache scanning, and per-project processed-file tracking, giving users accurate performance data and a smoother loading experience.

## 🛠️ Technical Changes
- Measure `duration_ms` using `time.perf_counter()` in `ai_providers`, `core`, and `issue_engine`, and persist it in cache metadata.
- Pass `duration_ms` to all `log_command_metric()` calls (success, cache hit, error) for accurate telemetry.
- Introduce `scan_cache_files_for_dashboard()` in `metrics.py` to scan all `~/.gitpr/cache/prompts/*/*.json` files (no date filter by default).
- Implement per-repo processed-cache tracking via `./.gitpr/metrics/{repo}/processed_cache.json` to support incremental scans.
- Rewrite the dashboard (`MetricsApp`): add a `ProgressBar` overlay during scanning, merge cache and event rows, remove the 100-row cap, and enable F5 incremental refresh.
- Add `provider` and `model` fields to `meta_raw` for later attribution.

## ⚠️ Impact/Warnings
- **Breaking:** None. Backward compatible; old cache files without `duration_ms` display as 0.
- **New local state:** Per-project `./.gitpr/metrics/{repo}/processed_cache.json` is created automatically. The directory does not need to be version controlled.
- **Performance:** Scanning 600+ cache files completes in tens of milliseconds and runs in a background thread, keeping the UI responsive.

close #73