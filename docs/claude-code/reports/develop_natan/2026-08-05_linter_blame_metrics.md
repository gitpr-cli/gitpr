## Completion Report — Linter & Blame Metrics Integration (Phase 2)

### What was done
- Added `log_local_metric` fire-and-forget calls to `src/linter_engine.py` at end of both full-file and diff modes, recording error/warning counts
- Added `log_local_metric` fire-and-forget calls to `src/blame_engine.py` in three paths: return_data mode, successful report generation, and save-to-disk error
- All metric dispatches use the existing `log_local_metric` function from `src/metrics.py` (already daemon-threaded, fire-and-forget)
- Created 8 unit tests (4 linter + 4 blame) covering all new metric dispatch paths

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| [src/linter_engine.py](src/linter_engine.py) | feat | Added `from src.metrics import log_local_metric` import and metric dispatch at end of full-file mode and diff mode |
| [src/blame_engine.py](src/blame_engine.py) | feat | Added `from src.metrics import log_local_metric` import and metric dispatch in return_data, report_generated, and error paths |
| [tests/test_linter_metrics.py](tests/test_linter_metrics.py) | feat | New: 4 unit tests for linter metric integration |
| [tests/test_blame_metrics.py](tests/test_blame_metrics.py) | feat | New: 4 unit tests for blame metric integration |

### Impact
- **Functionality:** Linter and blame commands now register local telemetry events in `~/.gitpr/metrics/` — enabling dashboard visibility for these two commands
- **Performance:** Zero impact — `log_local_metric` uses daemon threads (fire-and-forget pattern)
- **Compatibility:** No API breaks; purely additive changes

### Test results
```
8 passed (4 linter_metrics + 4 blame_metrics)
121 passed / 1 pre-existing failure (unrelated i18n test)
```
