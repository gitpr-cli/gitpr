# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add binary excludes and defensive hunk collapse
```

---

## 🎯 Summary
Prevents binary artifacts from reaching the AI prompt by expanding smart-exclude coverage for additional ML/data formats and adding a final defensive collapse for any binary hunks that bypass path filtering or arrive via external callers. This reduces prompt corruption and keeps PR generation reliable.

## 🛠️ Technical Changes
- Added `*.arrow`, `*.gguf`, `*.tflite`, and `*.keras` to the fallback smart excludes and `templates/gitpr.smart-excludes.json`.
- Invoked `collapse_binary_hunks(diff_text)` at the start of `generate_pr_content` before timing and AI calls.
- Added tests verifying defensive collapse removes U+FFFD-heavy binary hunks and covers the new exclude patterns.

## ⚠️ Impact/Warnings
- Behavior change: binary hunks are now sanitized even when supplied directly as raw diffs.
- Smart-exclude behavior broadens to additional data/model formats; confirm these are not intended as text inputs.
- No database, environment variable, or dependency changes.

close #303

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)