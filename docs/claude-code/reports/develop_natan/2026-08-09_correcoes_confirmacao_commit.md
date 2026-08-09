## Completion Report — Correção do Fluxo de Commit e Push

### What was done

Implemented the plan `docs/plans/20260809_correcoes_confirmacao_commit.md` which fixes the commit flow when no new changes exist, adds PR description updates for existing PRs, fixes error modal sizing, adds auto-upstream on push, and improves the existing PR flow.

1. **"Nothing to commit" detection**: When `git commit` returns non-zero with output indicating no changes to commit (`"nothing to commit"`, `"nothing added to commit"`, `"no changes added to commit"`, `"changes not staged"`, `"working tree clean"`, `"no changes"`), the flow now treats this as success and proceeds to PR check instead of showing an error.
2. **Update existing PR**: Added `update_pull_request()` to `github_api.py` (`PATCH /repos/{owner}/{repo}/pulls/{number}`). When an existing PR is found and the user chooses to push, the PR body is updated with the new content from the PR Body field.
3. **Error modal sizing**: `ErrorScreen` CSS updated from `height: auto` (unbounded) to `height: auto; max-height: 80%; overflow-y: auto`.
4. **Auto-upstream on push**: When `git push` fails with "upstream" or "no upstream" in the error, automatically retries with `git push --set-upstream origin <branch>`.
5. **PR body fix**: Removed the "Recommended Commit Message" + `---` wrapper from the PR body sent to GitHub — now sends only the content of the PR Body field.
6. **Merge flow**: Added `merge_pull_request()` API, `GITPR_AUTO_MERGE` env var, and merge prompt after PR creation and existing PR push.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/github_api.py` | feat | Added `update_pull_request()` and `merge_pull_request()` functions |
| `src/config.py` | feat | Added `GITPR_AUTO_MERGE` env var |
| `src/ui/pr_publish_app.py` | feat+fix | Broadened "nothing to commit" detection (6 patterns); `_push_and_exit` now updates PR body via PATCH; auto-upstream on push failure; `ErrorScreen` max-height 80%; PR body now sends only TextArea content; merge prompt flow; `_prompt_merge`, `_do_merge` methods; `CommitConfirmScreen` customizable button labels |
| `langs/pt_br.json` | feat | 10 new i18n keys |

### Impact

- **Functionality**: Commit failures due to no staged changes no longer block the flow. Existing PRs get their description updated on push. Push automatically sets upstream if missing. User can merge PRs from the TUI.
- **Performance**: No significant change — API calls (update, merge) are in background threads.
- **Compatibility**: Backward-compatible. `GITPR_AUTO_MERGE` defaults to `false`. Existing behavior unchanged for new PRs.

### Verification

- Imports verified cleanly
- `execute_git_commit` output patterns tested against all 6 "nothing to commit" variants
