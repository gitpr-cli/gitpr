# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: handle existing PRs and add auto-merge support
```

---

## 🎯 Summary
This PR enhances the PR publishing workflow by detecting existing open pull requests for the current branch before pushing. It offers interactive options to push and update the existing PR, open it in a browser, or create a new one. It also adds support for auto-merging PRs via the GitHub API, with optional automatic merge controlled by an environment variable. UI improvements include better error handling, thread safety, and localization updates for the new strings.

## 🛠️ Technical Changes
- Added translation keys for existing PR scenarios, merge prompts, browser opening, etc. across Spanish, French, Portuguese (Brazil and Portugal).
- Introduced `check_existing_pr()`, `update_pull_request()`, and `merge_pull_request()` functions in `src/github_api.py` to interact with the GitHub REST API.
- Refactored `PrPublishApp._start_commit_and_publish` into a background thread with improved error handling and stdout redirection for thread safety.
- Made `CommitConfirmScreen` accept custom button labels.
- Enhanced `CommitProgressScreen` to accept an initial status message.
- Modified PR body format: removed the recommended commit message section.
- Added `GITPR_AUTO_MERGE` configuration option.
- Implemented push-to-existing-PR flow with description update.
- Added interactive merge prompt after PR creation.

## ⚠️ Impact/Warnings
- Requires a GitHub token with write permissions (push, create PR, merge).
- New environment variable `GITPR_AUTO_MERGE` (set to `true`/`1`/`yes`/`y`) controls automatic merging after PR creation. Defaults to `false`.
- PR description no longer includes the commit message snippet; users relying on it may need to adjust.
- The `check_existing_pr` function uses `{repo_owner}:{branch}` as the head parameter, which may need adjustment for forked repositories.