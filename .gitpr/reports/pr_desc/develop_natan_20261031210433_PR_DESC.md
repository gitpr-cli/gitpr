# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
test: enforce version SSOT consistency across docs
```

---

## 🎯 Summary

Establishes `src/updater.__version__` as the single, explicit Source of Truth (SSOT) for the GitPR package version and locks that contract down with automated tests. Previously the version could silently drift between `pyproject.toml`, `CLAUDE.md`, and `GEMINI.md`, leading to releases and documentation reporting different numbers. This change makes the intent obvious in code and fails fast in CI as soon as any of those artifacts diverge.

## 🛠️ Technical Changes

- Clarified the `__version__` / `__lang_version__` / `__scripts_version__` block in `src/updater.py` to document that `__version__` is the canonical SSOT read by `setuptools` (`attr:`) and by `i18n.py`.
- Explicitly documented that `__lang_version__` and `__scripts_version__` are independent asset versions with their own `v`-prefixed convention, not tied to the package version.
- Added `tests/unit/test_version_consistency.py` covering:
  - `__version__` is a valid PEP 440 string without a leading `v`.
  - `pyproject.toml` keeps `version = {attr = "src.updater.__version__"}` (dynamic binding intact).
  - `CLAUDE.md` and `GEMINI.md` `- **Current version:**` entries match `__version__`.
  - Asset versions (`__lang_version__`, `__scripts_version__`) remain `v`-prefixed and distinct from the package version.
- Synchronized documentation artifacts (`CLAUDE.md`, `GEMINI.md`, `CONTEXT.md`, ADR 0014 and related plans/reports) with the SSOT definition.

## ⚠️ Impact/Warnings

- **No runtime behavior change**: version values themselves are unchanged (`1.4.4` / `v0.0.37`); only comments and tests were added.
- **CI impact**: the new tests will fail if `CLAUDE.md` or `GEMINI.md` versions are edited without bumping `src/updater.__version__` (and vice versa). Version bumps must now update code and docs in the same commit.
- **No database, environment variable, or dependency changes.**
- Release tooling that parses `pyproject.toml` continues to resolve the version dynamically from `src.updater.__version__`.

close #250

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)