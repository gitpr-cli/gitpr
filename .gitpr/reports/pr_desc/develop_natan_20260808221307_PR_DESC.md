# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add existing PR detection and user prompt
```

---

## 🎯 Summary

Improve the PR publishing flow by detecting open pull requests for the current branch and prompting the user accordingly. This prevents unintentional duplicate PRs and gives users clear options to open the existing PR in a browser or force-create a new one. Thread-safety and UI feedback were improved alongside new localization strings for a better user experience.

## 🛠️ Technical Changes

- Added `check_existing_pr` function in `src/github_api.py` to query GitHub API for open PRs from the current branch.
- Updated `CommitConfirmScreen` to accept customizable button labels via parameters `btn_yes` and `btn_no`.
- Updated `CommitProgressScreen` to support an initial status message and adjust layout.
- Refactored `_start_commit_and_publish` to execute commit, push, and publish in a background thread, checking for existing PRs before publishing.
- Added new UI flow: `_on_existing_pr_found` and related methods prompt the user when an open PR exists, allowing to create new or open existing, with optional browser launch.
- Enhanced thread safety by capturing stdout in the background thread and using `call_from_thread` for UI updates.
- Added new localization entries in `es_es.json`, `fr_fr.json`, `pt_br.json`, and `pt_pt.json` for the PR existence handling messages.

## ⚠️ Impact/Warnings

- The custom button labels in `CommitConfirmScreen` rely on the translations being available; missing translations might fall back to the old defaults.
- Thread-safety implementation now suppresses stdout in the background thread, which may hide print-based debug outputs.
- No database, environment variable, or dependency changes.