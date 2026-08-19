# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add progress status messages and push translations
```

---

## 🎯 Summary
Improves user feedback during PR operations by adding initial status messages to the progress screen and translating push-related notifications into Spanish.

## 🛠️ Technical Changes
- Added Spanish translations for push status messages (pushing, failed, success).
- Increased height of progress dialog to 35% for better layout.
- Enhanced status text styling with a background color for readability.
- `CommitProgressScreen` now accepts an optional `initial_status` parameter to set the initial status text, replacing the empty placeholder.
- Pass translated status messages ("🔍 Running linter...", "📦 Executing commit...") when opening the progress screen for linter and commit operations.
- Added debug logging for PR body length and preview to aid troubleshooting.

## ⚠️ Impact/Warnings
- No breaking changes; UI adjustments are backward-compatible.
- Translation keys added; ensure corresponding entries exist in other language files if needed.
- Debug log addition may slightly increase log verbosity; consider removing in production if not required.