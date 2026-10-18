# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: bump version to 1.4.1 and language dictionary to v0.0.35
```

---

## 🎯 Summary

Bumps the GitPR release version to `1.4.1` and advances the language dictionary version to `v0.0.35`. This keeps the distributed package metadata aligned with the latest language resources and signals a new patch release to consumers.

## 🛠️ Technical Changes

- Updated `__version__` in `src/updater.py` from `1.4.0` to `1.4.1`.
- Updated `__lang_version__` from `v0.0.34` to `v0.0.35`.

## ⚠️ Impact/Warnings

- No database, environment variable, or dependency changes.
- Version metadata is read by `pyproject.toml` via `setuptools` attr, so the published package version will change to `1.4.1`.
- The language dictionary reference now points to `v0.0.35`; ensure that version is published and available.

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)