# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add telemetry logging to linter, blame, and git hooks
```

---

## 🎯 Summary
This PR integrates local telemetry (metrics) logging into the linter and blame engines, and updates post-checkout and pre-push git hooks to write event logs directly. It enables visibility into command usage and hook events for team dashboards, closing out Phase 2 of the metrics integration.

## 🛠️ Technical Changes
- Added `log_local_metric` calls in `src/linter_engine.py` at the end of full-file and diff lint modes, recording error/warning counts and mode identifier.
- Added `log_local_metric` calls in `src/blame_engine.py` in three paths: `return_data` mode, successful report generation, and save-to-disk error, recording commits_analyzed and mode.
- Rewrote `scripts/post-checkout-template.sh` to directly write a JSON log file to `~/.gitpr/metrics/` on branch switches, including previous and current branch names.
- Rewrote `scripts/pre-push-template.sh` to directly write a JSON log file on push events, including the count of commits being pushed.
- Added 8 new unit tests (4 linter metrics + 4 blame metrics) covering all new metric dispatch paths.
- Added metric export example files for reference (CSV and JSON).

## ⚠️ Impact/Warnings
- **No API breaks** – all changes are additive.
- **Git hooks** now write directly to `~/.gitpr/metrics/`; the updated templates must be installed via `gitpr --installhooks` for the hooks to take effect.
- **Performance** – `log_local_metric` uses daemon threads (fire-and-forget), so there is negligible performance impact.
- **Dependencies** – no new dependencies required.

close #80