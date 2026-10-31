# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
fix: handle legacy reviewer attach without read-back
```

---

## 🎯 Summary
Prevent misleading reviewer attachment logs when a third-party SCM provider still follows the legacy reviewer API contract and returns `None` instead of the requested reviewer list. The log now explicitly reports `(no read-back)` rather than `attached None`, and the provider contract is documented so future implementations return `list[str]`.

## 🛠️ Technical Changes
- Document the `request_pull_request_reviewers` contract change: implementations should return `list[str]`, while legacy `None` remains tolerated as “cannot verify”.
- Update PR publish logging to display `(no read-back)` when reviewer attachment cannot be verified.
- Add regression tests covering legacy `None` read-back behavior, empty read-back warnings, and one-by-one retry handling.

## ⚠️ Impact/Warnings
- No database, environment variable, or dependency changes.
- Legacy providers returning `None` are still supported and will not trigger false not-attached warnings.
- New provider implementations should return the requested reviewer list when the forge does not return a body.

close #246

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)