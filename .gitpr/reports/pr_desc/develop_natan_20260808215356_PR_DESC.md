# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add Spanish push status translations and PR body logging
```

---

🎯 Summary
This update enhances the user interface by providing Spanish translations for push operation status messages (pushing, failed, successful). It also adds detailed logging of the PR body during the publish process to aid in debugging and monitoring.

🛠️ Technical Changes
- Added translation keys `📤 Pushing to remote...`, `❌ Push Failed`, and `✅ Push successful!` to `langs/es_es.json`.
- In `src/ui/pr_publish_app.py`, added logging of the PR body length and a preview (first 200 characters) when publishing a PR.

⚠️ Impact/Warnings
- No breaking changes. No database or environment variable modifications required. This is a localization and logging-only enhancement.