# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat(release): bound range by changelog and link release notes
```

---

## 🎯 Summary

Release notes repeated commits that had already shipped in earlier versions. The range origin came from `git describe`, which only sees tags reachable from HEAD (e.g. `v0.0.8` instead of `v1.2.0`), so the generated section re-listed the whole history and the suggested version could even be lower than the version already in the changelog. This change makes the previous changelog section the source of truth for the range and adds real, clickable commit / pull request / contributor links to the generated artifact, which is the first place GitPR has to build an HTML link locally instead of reading `html_url` from an API payload.

## 🛠️ Technical Changes

- add `src/infrastructure/scm/web_links.py`: pure, no-I/O helpers (`repo_web_base`, `commit_url`, `pull_request_url`, `user_url`) that normalize any remote shape (`https`, `ssh://`, `git://`, scp-like, credentials, custom port, nested GitLab groups) into an https base and apply per-forge page patterns (GitHub, GitLab, Bitbucket, Azure DevOps).
- `release_engine`: resolve the range origin from the previous changelog section using two anchors — the newest bullet hash of that section (resolved in a single `git log --no-walk`, ordered by epoch to survive mixed timezones) and, as fallback, the section's version tag; degrade to the latest tag with a user-facing warning when neither resolves.
- `release_engine`: drop commits already listed in other release sections before rendering, and fail fast with a clear error when the range contains nothing new.
- `release_engine`: derive the version-bump baseline from the previous changelog version first, then the range anchor, then the highest reachable semver tag.
- `release_engine`: assemble a `LinkContext` (provider, repo base, contributor logins) from the `origin` remote; contributor logins are resolved best-effort via the forge commit lookup, then the e-mail search, and cached in `~/.gitpr/cache/contributors.json` (only successful lookups are stored).
- `changelog_builder`: new `LinkContext` dataclass; bullets now render `subject ([hash](url)) — scope · [#PR](url) · date` and contributor names link to their profile, gracefully degrading to plain text when no context/pattern exists.
- fix changelog section boundaries: block headers are now matched at level 2 only, so `--force` replaces the whole old block (including its `### Summary` and contributor footer) instead of leaving stale subsections behind.
- `generate_release_notes` accepts a `changelog_path` (wired from `settings["changelog_path"]` in `main.py`) and forwards `quiet` to the AI calls so the spinner never corrupts `--format json` output.
- add translations for the three new messages in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`; add the date/link tests and the new `tests/test_web_links.py` suite.

## ⚠️ Impact/Warnings

- **Breaking API change:** `ReleaseNotesResult` gains the required field `previous_version`; any external consumer instantiating it must be updated. `build_release_section` also gains an optional `links` parameter (backward compatible).
- **New behavior:** the release now aborts with `❌ Nothing new to release` when every commit of the range is already in the changelog; `--since` still overrides the changelog anchor.
- **New local state:** `~/.gitpr/cache/contributors.json` is written best-effort (never fails a release); remove it to force a re-resolution of contributor logins.
- **Optional network calls:** contributor name linking hits the configured SCM provider; without a token, offline, or on an unsupported forge it silently degrades to plain display names.
- **Version bump:** `1.2.0` → `1.3.0`, language dictionary `v0.0.31` → `v0.0.32`.
- No database or environment-variable changes; no new dependency added.
- The added `.gitpr/metrics/export/*` files are generated report artifacts.

close #191

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)