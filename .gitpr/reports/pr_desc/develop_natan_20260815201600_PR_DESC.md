# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
refactor: remove unused FileStageScreen and localize staging strings
```

---

🎯 Summary
Removes the unused `FileStageScreen` modal from the PR publishing app, cleaning up dead code and simplifying the user interface. Also updates translations for staging-related messages in Spanish, French, and Portuguese, and corrects the editor selection help text for MCP configuration.

🛠️ Technical Changes
- Delete the `FileStageScreen` class, its CSS, and associated handlers from `src/ui/pr_publish_app.py`
- Remove unused imports `get_unstaged_files` and `stage_files` from `src/ui/pr_publish_app.py`
- Update `langs/es_es.json`, `langs/fr_fr.json`, and `langs/pt_pt.json` to translate the "No files selected for staging." message and add a new translation for "❌ Failed to stage files: {error}"
- Add `claude-code` to the list of available editor choices in the MCP server CLI help text

⚠️ Impact/Warnings
- No database, environment variable, or dependency changes.
- The file staging modal is no longer available in the PR publishing flow. If this feature was previously used, it has been intentionally removed; verify with product owner.

close #122