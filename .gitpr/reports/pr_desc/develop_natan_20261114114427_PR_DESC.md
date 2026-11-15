# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: bump package version to 1.8.0 and language dictionary to v0.0.43
```

---

## 🎯 Summary

Updates the canonical version identifiers for the GitPR package and its bundled language dictionary assets. The package version moves from `1.7.0` to `1.8.0`, and the independent language dictionary asset moves from `v0.0.42` to `v0.0.43`. This keeps `src/updater.py` as the single source of truth (SSOT) aligned with the released artifacts, ensuring that version checks, update prompts, and asset resolution work against the correct baselines.

## 🛠️ Technical Changes

- Bump `__version__` from `1.7.0` to `1.8.0` in `src/updater.py`.
- Bump `__lang_version__` from `v0.0.42` to `v0.0.43` in `src/updater.py`.
- Preserve the existing separation of concerns between the package version (`__version__`) and the language dictionary asset version (`__lang_version__`).

## ⚠️ Impact/Warnings

- **Packaging:** `pyproject.toml` reads `__version__` via the setuptools `attr:` directive, so the published package metadata will now report `1.8.0`.
- **Update checks:** Clients on older versions will detect `1.8.0` as a newer release; verify that the corresponding release tag/artifact exists before publishing.
- **Language assets:** The dictionary version is bumped independently — confirm that `v0.0.43` language assets are available, otherwise lookup fallbacks may trigger.
- No database, environment variable, or dependency changes are introduced by this diff.

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)