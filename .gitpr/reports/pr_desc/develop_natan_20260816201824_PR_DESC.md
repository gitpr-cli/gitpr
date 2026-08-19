# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
fix: generate linter report only when violations found
```

---

## 🎯 Summary

Prevents the creation of empty Markdown linter reports by only generating the report when there are warnings or errors. This reduces noise in the repository and avoids unnecessary file writes when the codebase passes linting.

## 🛠️ Technical Changes

- Add conditional guard `if has_warnings or has_errors:` around the report generation block in `src/main.py`.
- Update the inline comment to reflect the new conditional behavior.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- Behavior change: Linter reports will no longer be produced when the code is clean; ensure downstream processes do not depend on the existence of an empty report.

close #129