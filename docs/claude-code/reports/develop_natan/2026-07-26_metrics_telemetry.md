## Completion Report — Metrics & Telemetry System (Phases 2-5)

### What was done

Implemented a complete local offline telemetry system for GitPR, expanding the
existing `src/metrics.py` skeleton into a full metrics engine with aggregation,
export, purge, and interactive TUI dashboard. Added fire-and-forget metric hooks
to CLI command handlers and AI call paths. Created git hook templates for
behavioral telemetry. Added `--metrics` CLI flag with sub-options.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/metrics.py` | feat | Added `log_command_metric()`, `export_metrics()`, `purge_metrics()`, `show_metrics_summary()`, `get_metrics_dir()`, `get_metrics_state_file()` — expanded from 57 to ~220 lines |
| `src/core.py` | feat | Added lazy-imported `log_command_metric()` calls in single-chunk and map-reduce paths within `generate_pr_content()`; added 3 new hooks to `install_git_hooks()` |
| `src/core.py` | fix | Changed `from src.metrics import log_local_metric, log_command_metric` to lazy imports to resolve circular import (metrics → core → metrics) |
| `src/main.py` | feat | Added `--metrics`, `--export`, `--purge`, `--dashboard`, `--hook-event` flags; handler chain for export/purge/summary/dashboard/hook-event; HELP_MAP and HELP_PRIORITY entries for `metrics` |
| `src/main.py` | feat | Added `log_command_metric()` call in linter handler |
| `src/ui/metrics_app.py` | new | Interactive TUI dashboard (Textual) with DataTable, summary stats, F5 refresh, Esc exit |
| `scripts/post-checkout-template.sh` | new | Git hook: logs branch-switch events |
| `scripts/pre-push-template.sh` | new | Git hook: logs push events |
| `scripts/post-merge-template.sh` | new | Git hook: logs pull/merge events |
| `langs/pt_br.json` | feat | +16 metrics-related translation keys (427 total) |
| `langs/pt_pt.json` | feat | +16 metrics-related translation keys (427 total) |
| `langs/es_es.json` | feat | +16 metrics-related translation keys (427 total) |
| `langs/fr_fr.json` | feat | +16 metrics-related translation keys (427 total) |
| `docs/plans/plano_metricas_telemetria.md` | plan | Completed all 5 phases with detailed implementation specs, JSON structures, and code patterns |
| `docs/plans/metricas_analytics_dashboard.md` | reference | Reference doc explaining the metrics concept |

### Architecture

```
~/.gitpr/metrics/
├── {owner}/{branch}/{uuid}_{YYYYMMDD}.json   ← fire-and-forget events
├── config.json                               ← export state (UUIDs processed)
└── export/
    ├── gitpr_metrics_2026-07-26.csv          ← consolidated CSV
    └── gitpr_metrics_2026-07-26.json         ← consolidated JSON
```

**Metric payload:**
```json
{
  "timestamp": "2026-07-26T14:30:00",
  "command": "review", "status": "success",
  "provider": "gemini", "tokens_estimated": 4500,
  "duration_ms": 3200, "repo": "owner/repo",
  "branch": "feature/xyz", "cache_hit": false,
  "map_reduce_triggered": false
}
```

**CLI surface:**
```
gitpr --metrics                  → summary (files, disk, path)
gitpr --metrics --export         → CSV + JSON output
gitpr --metrics --purge          → confirm + clean
gitpr --metrics --dashboard      → TUI (Textual)
gitpr --hook-event <name> --quiet → hidden: log git hook event
```

### Impact

- **Functionality:** Every AI-powered command now emits a telemetry event.
  Linter runs emit error/warning counts. Map-reduce triggers are tracked.
  Git hooks capture branch switches, pushes, and merges.
  Export produces CSV for spreadsheets/dashboards.
  Dashboard TUI gives instant visibility into usage patterns.

- **Performance:** All metric writes are fire-and-forget daemon threads —
  zero latency impact on CLI commands. Export uses `click.progressbar()`
  for large directories.

- **Compatibility:** No API breaks. The `--metrics` flag is additive.
  Existing `log_local_metric()` signature unchanged. No new dependencies.

### Next steps

- [ ] Add i18n keys for the 16 new metrics strings to English fallback
  (currently they show as raw English when no translation matches)
- [ ] Consider a `--metrics --serve` mode that starts an HTTP server for
  browser-based dashboards
- [ ] Add test coverage for `export_metrics()`, `purge_metrics()`, and
  `MetricsApp` TUI
- [ ] Sync the 3 new git hook template descriptions to READMEs in all
  5 languages
