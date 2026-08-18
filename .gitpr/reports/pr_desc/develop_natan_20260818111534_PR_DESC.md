# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
refactor: defer coauthor trailer injection to commit execution
```

---

## 🎯 Summary

The co-author trailer was being added to the commit message before it was displayed in the TUI, causing it to appear in the preview. This change moves the injection to just before the git commit executes, keeping the TUI clean. Additionally, stale metric export files are removed and `.gitignore` no longer excludes the reports directory.

## 🛠️ Technical Changes

- Remove `append_coauthor_trailer` from the import and from the commit message generation step in `pr_publish_app.py`.
- Inject the co-author trailer dynamically when executing the git commit, using `self._pending_commit_msg`.
- Delete obsolete metric export CSV/JSON files from `.gitpr/metrics/export/`.
- Update `.gitignore` to no longer ignore `.gitpr/reports/`.

## ⚠️ Impact/Warnings

- The co-author trailer will no longer be shown in the TUI commit message preview; it is only added at commit time.
- The removal of `.gitpr/reports/` from `.gitignore` might cause that directory to be tracked if it exists; ensure it's not needed or add it back if reports should remain ignored.
- No database or environment variable changes.

close #131