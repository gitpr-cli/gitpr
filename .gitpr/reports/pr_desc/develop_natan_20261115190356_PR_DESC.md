# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: bump version to 1.9.0 and language dictionary to v0.0.44
```

---

## 🎯 Summary

Prepares the release of GitPR 1.9.0 by promoting the canonical package version (SSOT) and advancing the language dictionary asset to `v0.0.44`. The change keeps the runtime version metadata aligned with the accompanying release documentation, ensuring that the published package, the generated release notes, and the bundled translation assets all report a consistent, verifiable version.

## 🛠️ Technical Changes

- Bump `__version__` from `1.8.0` to `1.9.0` in `src/updater.py`, the canonical single source of truth for the package version consumed by `pyproject.toml` via `setuptools` attr.
- Bump `__lang_version__` from `v0.0.43` to `v0.0.44`, advancing the language dictionary asset independently of the package version.
- Synchronize release artifacts (`CHANGELOG.md` and release/PR description reports) with the new version identifiers.

## ⚠️ Impact/Warnings

- **Versioning/Release:** This is a release-tagging change; downstream consumers pinned to `1.8.x` will not pick up the new language assets until they upgrade.
- **Dependencies:** No dependency changes.
- **Database:** No database migrations or schema changes.
- **Environment variables:** No new or modified environment variables.
- **Language assets:** `__lang_version__` is an independent asset version — verify that the `v0.0.44` dictionary is available before publishing, otherwise runtime lookups may fail to resolve translations.

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)