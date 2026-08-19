# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add existing PR detection and push flow improvements
```

---

## 🎯 Summary
This PR introduces detection of existing open pull requests for a branch before pushing, allowing users to decide whether to push to the existing PR, create a new one (for some locales), or just open the existing PR in the browser. This prevents accidental duplicate PRs and gives more control over the push workflow.

## 🛠️ Technical Changes
- Added `check_existing_pr()` in `github_api.py` to query for open PRs from the current branch.
- Modified `CommitConfirmScreen` to accept custom button labels (`btn_yes`, `btn_no`).
- Adjusted `CommitProgressScreen` styling and added initial status parameter.
- Overhauled `_start_commit_and_publish` to run in a background thread, redirect stdout for thread safety, and integrate existing PR checks.
- Added several new UI methods: `_on_existing_pr_found_before_push`, `_push_and_exit`, `_prompt_open_browser`, and browser prompt handlers.
- Added extensive translation strings in `es`, `fr`, `pt_BR`, and `pt_PT` for existing PR dialogues, push errors, and browser prompts.
- Note: `pt_BR` locale offers a push-to-existing-PR flow (“Yes, Push to Existing PR”), while other locales prompt to create a new PR if desired.

## ⚠️ Impact/Warnings
- **New translation keys**: All supported locales must have the new keys (`⚠️ Existing Pull Request`, `✅ Commit pushed to existing PR`, `🔗 Open in Browser`, etc.) or the UI will show raw English fallbacks.
- **Thread safety**: `stdout` is now redirected during the commit/push background thread to avoid terminal interference.
- **User flows**: The former direct “commit → push → create PR” sequence now offers a modal when an existing PR is found, potentially altering the expected one-click experience for users who rely on automated pushes.