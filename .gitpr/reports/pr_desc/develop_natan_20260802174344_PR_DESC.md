# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
feat: add token reauth, cache enrichment, and repo-scoped dashboard fixes
```

---

## 🎯 Summary

This update strengthens the GitPR metrics/telemetry system by adding comprehensive logging, cache-based token enrichment, repository-scoped dashboard filtering, and a token reauthentication flow. It also resolves dashboard refresh column duplication and ensures metric export is project-local. These changes improve visibility into AI token usage, reliability of GitHub interactions, and developer experience when viewing metrics per project.

## 🛠️ Technical Changes

- Added `validate_github_token` in `config.py` for proactive PAT validation via GitHub API.
- Refactored `tui_issue.py` to validate token before TUI launch, with automatic re-prompt on expiration (max 3 attempts).
- Modified `issue_app.py` to detect 401 errors and signal `reauth` action, allowing re-authentication without losing draft.
- Integrated `reauth` loop in `main.py` for seamless token renewal.
- Extended `metrics.py` with `log_command_metric` calls in missing CLI paths (skill, installhooks, update, install, blame, chat, issue creation).
- Enhanced `issue_engine.py` to capture AI telemetry metadata and store it in cache, enabling accurate token counting.
- Added `enrich_metrics_from_cache` to merge AI token usage from cache into metric exports, and added new CSV columns (`prompt_tokens`, `completion_tokens`, `tokens_actual`).
- Implemented `load_cache_token_summary` for aggregating cache token data per repository, used in dashboard totals.
- Updated `MetricsApp` dashboard to filter events by repository (`repo_filter`), show repo label, fix F5 column duplication, and include cache token summations.
- Changed `export_metrics` to accept a `repo_filter` and default to project-local output directory (`./.gitpr/metrics/export/`).
- Added 26+ new tests covering cache summation, repo filtering, export enrichment, dashboard behavior, and token reauth.
- Fixed dashboard crash when scanning export subdirectory (non-dict JSON).
- Updated plan documents and reports for metrics and token reauth.

## ⚠️ Impact/Warnings

- **Environment Variables:** No new required variables. Token validation uses existing `GITHUB_TOKEN_ENCRYPTED`.
- **Dependencies:** No new dependencies.
- **Database:** No database changes.
- **Breaking API:** `export_metrics()` signature extended with optional `repo_filter` parameter (backward-compatible). Default output directory changed from `~/.gitpr/metrics/export/` to `./.gitpr/metrics/export/`; existing exports in home directory are not affected.
- **Performance:** Minor overhead: one HTTP call to validate token on `-is` invocation (~200ms), cache scanning on dashboard load (~50ms per 100 cache files).

close #69