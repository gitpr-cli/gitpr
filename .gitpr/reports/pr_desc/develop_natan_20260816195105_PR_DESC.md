# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add co-author trailer with opt-out env var
```

---

🎯 Summary

This change adds automatic attribution to AI-generated commit messages by appending a `Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>` trailer. The feature is enabled by default and can be disabled via `GITPR_COAUTHOR=false` in `~/.gitpr/.env`. The goal is to clearly mark AI assistance in commits.

🛠️ Technical Changes

- Added `coauthor_enabled()` in `src/config.py` to read the `GITPR_COAUTHOR` environment variable (defaults to true).
- Added `COAUTHOR_TRAILER` constant and `append_coauthor_trailer()` helper in `src/core.py` to append the trailer idempotently with a blank line separation.
- Integrated the helper into CLI commit flow (`src/main.py`), auto-commit flow, MCP server `generate_commit_message` tool, and UI (`src/ui/pr_publish_app.py`).
- Updated and added unit tests for the new behavior and environment opt-out.
- Added example metrics export files (CSV and JSON) under `.gitpr/metrics/export/`.

⚠️ Impact/Warnings

- Default commit output changes: all AI-generated commit messages will now include a co-author trailer unless explicitly disabled.
- To opt out, users must set `GITPR_COAUTHOR=false` in `~/.gitpr/.env`; no automatic modification of `.env` is performed.
- The new metrics export files appear to be artifacts and should not affect runtime unless consumed by other tooling.

close #127