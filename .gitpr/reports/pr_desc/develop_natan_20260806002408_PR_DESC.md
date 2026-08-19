# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
fix: update Portuguese translations and version configuration
```

---

## 🎯 Summary
This PR updates the Portuguese (pt-PT) translation file with numerous spelling and grammar corrections, ensuring consistency and accuracy of the localization. Additionally, it refactors version management to be dynamic via setuptools, and adds new metric export files for telemetry data.

## 🛠️ Technical Changes
- Fixed over 100 translation errors in `langs/pt_pt.json` (accents, word choices, grammar).
- Made version dynamic in `pyproject.toml` using `[tool.setuptools.dynamic]` with `version = {attr = "src.updater.__version__"}`.
- Reordered imports in `src/updater.py` to resolve a circular dependency between `i18n` and version constants.
- Added new metric export files (CSV and JSON) to track telemetry data.

## ⚠️ Impact/Warnings
- Version is now defined exclusively in `src/updater.py`; any packaging or build scripts that relied on a hardcoded version in `pyproject.toml` must be updated.
- Extensive changes to the Portuguese translation file; verify all keys still map correctly.
- New metric files will be included in the build output; ensure they are included or excluded as per deployment requirements.