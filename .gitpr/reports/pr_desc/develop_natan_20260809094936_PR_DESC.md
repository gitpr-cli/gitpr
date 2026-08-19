# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add existing PR check, merge prompt and auto-merge support
```

---

## 🎯 Summary

This update improves the PR publishing workflow by detecting existing open pull requests for the current branch, allowing users to push new commits to an existing PR or create a new one. It also introduces an optional merge prompt and a `GITPR_AUTO_MERGE` environment variable to skip manual confirmation.

## 🛠️ Technical Changes

- Added `check_existing_pr()` and `merge_pull_request()` to `github_api.py` for detecting open PRs and merging via GitHub API.
- Extended `PrPublishApp` with logic to handle existing PR detection before push and offer user choices (push to existing, open in browser).
- Added `GITPR_AUTO_MERGE` config boolean to skip merge prompt and merge automatically.
- Updated progress screens to support dynamic status messages and custom button labels.
- Expanded translations (es_es, fr_fr, pt_br, pt_pt) to cover new UI messages.
- PR body now omits the commit message recommendation and only sends the diff-based summary.

## ⚠️ Impact/Warnings

- Introduces new environment variable `GITPR_AUTO_MERGE` (default `false`). Set to `true` to enable automatic merging of PRs.
- Requires GitHub token with `repo` scope for merging; existing token scopes may need to be extended.
- Changes behaviour: previously, the flow always created a new PR. Now it checks for existing ones, potentially altering the user workflow.
- New translations must be present for all supported languages; missing keys would show untranslated strings.
- All changes are backward compatible; falling back to previous behaviour if no existing PR is found.