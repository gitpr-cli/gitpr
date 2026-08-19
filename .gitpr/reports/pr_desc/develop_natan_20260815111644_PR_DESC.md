# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
chore: add metrics export files and bump version to 0.0.36
```

---

🎯 Summary
This change adds exported metrics for GitPR usage in both CSV and JSON formats and increments the package version to 0.0.36. The metrics record command execution data (timestamp, command, status, provider, token usage, duration) to support operational visibility and usage analysis.

🛠️ Technical Changes
- Add `gitpr_metrics_2026-08-15.csv` with an initial metrics record.
- Add `gitpr_metrics_2026-08-15.json` containing the same structured metrics data.
- Update `__version__` in `src/updater.py` from `0.0.35` to `0.0.36`.

⚠️ Impact/Warnings
- No database schema, environment variable, or dependency changes.
- The new files are date-stamped exports under `.gitpr/metrics/export/`; future exports may add more files in that directory.

close #116