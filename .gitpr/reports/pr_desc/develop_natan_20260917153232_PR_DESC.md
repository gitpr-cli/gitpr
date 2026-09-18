# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: resolve reviewer identities to forge logins before attaching
```

---

## 🎯 Summary

Reviewer suggestions come out of `git blame`, so they carry author **names and emails**, not forge handles. When no handle could be resolved, the UI displayed the bare author name — and typing that name back into the reviewer field caused GitPR to POST it verbatim as if it were a login. GitHub answers `201` to a nonexistent login and attaches nobody, so the request vanished silently and the user believed the review had been requested.

This change introduces a dedicated identity-resolution layer that runs **twice**: before the TUI opens (to prefill the field and flag the people with no account) and at attach time (for whatever the user typed or edited). Values that cannot be resolved are never submitted — they are dropped with a visible warning instead.

It also closes the second silent failure mode of the GitHub API: a login that is **accepted** (`201`) but **not attached** is now detected by reading back `requested_reviewers` from the response.

## 🛠️ Technical Changes

- **New `src/reviewer_resolution.py`**: `resolve_candidates` (login resolution per candidate), `resolve_typed_reviewers` (resolution ladder for typed values), `match_candidate` (exact match on login, name or email after normalization) and the `ResolvedReviewer` / `ResolutionOutcome` structures. Pure, never raises, provider duck-typed via `getattr` so fakes and non-reviewer forges keep working.
- **Resolution ladder**: already-known handle (no request) → exact match on a suggested person → email lookup (`email_to_handle`) → forge login validation (`get_user_login`).
- **`GitHubProvider`**: `request_pull_request_reviewers` now returns the logins actually attached (read from the 201 body); two new read-only helpers `get_commit_author_login` (maps a commit SHA to the account linked to its author email — the reliable path for corporate addresses the user-search API cannot see) and `get_user_login` (validates/canonicalizes a typed handle, rejects values that cannot be a login without spending a request, and distinguishes 404 from transient errors).
- **`ScmProvider` contract**: `request_pull_request_reviewers` return type changed from `None` to `list[str]`; the read-back is documented as the only way to detect a silently ignored login.
- **`main._reviewer_suggestion_view`**: now builds `resolutions` via `resolve_candidates`, prefills `handles`, and marks unresolved people so the hint lines flag them; carries `resolutions` into the view so the attach step does not resolve the same people twice.
- **`pr_publish_app`**: `_attach_reviewers` resolves the typed values before submitting, reports dropped values, and on a `422` for a multi-reviewer batch retries **one by one** (GitHub rejects the whole batch when a single login is ineligible — the PR author, a non-collaborator — which used to drop the good reviewers too). New `NoticeScreen` modal blocks the merge prompt until the user acknowledges the warnings.
- **`reviewer_suggestion`**: `_identity_key` renamed to `identity_key` (public), new `normalize_identity`, and `ReviewerCandidate` now carries `last_commit_hash` so aggregation keeps the commit of the most recent touch.
- **`suggest_reviewers`**: `format_suggestion_lines` keys on the identity key instead of the normalized email and accepts `no_login` to append the "no GitHub account found" note.
- **i18n**: 7 new keys in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`; `GitHub usernames, comma separated` replaced by `GitHub login, name or email, comma separated`; language dictionary bumped to `v0.0.27`.
- **Tests**: new `tests/test_reviewer_resolution.py` (resolution ladder, partial-name rejection, dedup, failure tolerance), extended GitHub provider tests (read-back, commit author, user lookup, 404 vs 403), publisher tests (typed name never submitted, silent ignore warns and blocks merge, batch rejected then retried individually) and aggregation/formatting tests.

## ⚠️ Impact/Warnings

- **Breaking provider contract**: `ScmProvider.request_pull_request_reviewers` now returns `list[str]` instead of `None`. Any custom or third-party provider subclass must be updated; callers relying on the previous `None` return will not break but will miss the read-back (`None` is treated as "cannot verify", never as a failure).
- **Forge API calls**: two new GitHub endpoints are hit (`GET /commits/{sha}`, `GET /users/{login}`) during suggestion and attach. This increases request volume and consumes rate limit; both are best-effort and never block the publish.
- **Blocking modal**: the new `NoticeScreen` waits for user acknowledgement (Escape or Close) before the merge flow continues. This is intentional — the merge prompt would otherwise take over the screen — but it does pause automated flows when warnings exist.
- **Localization**: 7 new translation keys plus a rewritten placeholder string; language dictionary version raised to `v0.0.27` — translation pipelines must pick up the new version.
- **No database migration and no new environment variables.**
- **Housekeeping**: `.gitpr/metrics/export/gitpr_metrics_2026-09-17.csv` / `.json` look like generated local artifacts and probably should not be tracked — consider adding `.gitpr/metrics/export/` to `.gitignore`.


close #171