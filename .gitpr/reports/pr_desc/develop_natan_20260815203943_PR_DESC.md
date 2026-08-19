# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
refactor: apply consistent code formatting
```

---

## 🎯 Summary

Standardize code formatting across the entire codebase using Black-style conventions. This change improves readability, reduces future diff noise, and enforces consistent use of double quotes, line wrapping, trailing commas, and function signature formatting.

## 🛠️ Technical Changes

- Convert all single-quoted strings to double quotes.
- Wrap long function calls, signatures, and conditions to fit within line length limits.
- Add trailing commas to multi-line collection literals, function calls, and imports.
- Reformat dictionary and list indentation to consistent style.
- Standardize regex and string literal prefixes.
- Reorder imports and add missing blank lines for PEP 8 compliance.
- Normalize spacing in expressions, comments, and multi-line statements.

## ⚠️ Impact/Warnings

- **No functional changes** — this is purely a cosmetic/style refactor.
- Large diff may cause merge conflicts with in-progress feature branches; coordinate merges accordingly.
- Ensure CI/CD formatting checks are updated to match the new style to prevent drift.

close #124