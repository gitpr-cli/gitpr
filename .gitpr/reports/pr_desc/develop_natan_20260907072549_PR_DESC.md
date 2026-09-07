# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add PR reviewer suggestions from blame
```

---

🎯 Summary

This PR adds opt-out reviewer suggestions to the interactive PR publish flow. The flow now takes the unified diff it already computes, isolates the added lines, and runs `git blame --line-porcelain` over those exact line ranges to identify which contributors own the code being changed. Candidates are ranked by lines touched, files touched, and author recency, while excluding the PR author and known bot identities. Suggestions default to ON, can be disabled with `--no-suggest-reviewers` or `GITPR_SUGGEST_REVIEWERS=false`, and on GitHub the accepted/edited handles are submitted to the created PR.

🛠️ Technical Changes

- `src/diff_parser.py`: new pure parser maps unified diff text into per-file new-side added line numbers; handles renames, quoted/escaped paths, `/dev/null` deletion-only files, multiple hunks, and binary/mode-only diffs.
- `src/blame_engine.py`: adds `get_blame_for_range`, a porcelain `git blame --line-porcelain` reader that returns committed `BlameHit` records and skips uncommitted working-tree lines (`Not Committed Yet`).
- `src/reviewer_suggestion.py`: new pure scoring/ranking module. It aggregates hits by normalized email, filters bots and the PR author, and assigns weighted scores using touched lines, touched files, and a recency half-life.
- `src/suggest_reviewers.py`: new orchestration layer that connects diff parsing, blame, and ranking. It groups added lines into contiguous blame ranges, caps blame work per file, and converts missing blame history into non-fatal warnings.
- `src/config.py`: introduces `GITPR_SUGGEST_REVIEWERS`, `GITPR_REVIEWER_SUGGESTION_TOP_N`, and `GITPR_REVIEWER_SUGGESTION_EXCLUDED`, all read from `~/.gitpr/.env`.
- `src/main.py` and `src/ui/pr_publish_app.py`: add the `--no-suggest-reviewers` flag, render the Suggested Reviewers section in the publisher, allow editing GitHub handles, and attach reviewers after PR creation/update without blocking the publish on failure.
- `src/infrastructure/scm/github_provider.py`: adds GitHub handle resolution from noreply emails and user search, plus `POST /pulls/{n}/requested_reviewers`; `src/infrastructure/scm/base.py` keeps a non-supported default so other forges show suggestions locally only.
- Localizations were updated for `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, and `pt_pt`; generated `.gitpr/metrics` export files were also added.

⚠️ Impact/Warnings

- No database schema changes and no new runtime dependencies were introduced.
- Reviewers suggestions are computed by default in the interactive PR flow. Each contiguous added segment may run one `git blame` subprocess, but work is bounded by the diff size and capped per file; disable globally with `GITPR_SUGGEST_REVIEWERS=false` or per-run with `--no-suggest-reviewers`.
- New environment variables in `~/.gitpr/.env`: `GITPR_SUGGEST_REVIEWERS=false` disables the feature globally; `GITPR_REVIEWER_SUGGESTION_TOP_N` controls the number of candidates (default `3`); `GITPR_REVIEWER_SUGGESTION_EXCLUDED` accepts a CSV of author names/emails to skip.
- On GitHub, the PR is published first and reviewers are requested afterwards. A reviewer request failure (invalid handle, rate limit, etc.) never blocks the PR — it only appends a warning. Non-GitHub forges display suggestions locally only because their current APIs do not support requesting reviewers.

close #155