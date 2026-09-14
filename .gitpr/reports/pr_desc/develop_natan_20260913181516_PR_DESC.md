# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: bump version to 1.1.0 and language dictionary to v0.0.25
```

---

## 🎯 Summary

Releases GitPR `1.1.0` alongside the `v0.0.25` language dictionary. The version constants in `src/updater.py` are the single source of truth consumed by `pyproject.toml` (via setuptools `attr:`) and by the update/self-check flow, so bumping them here is what actually publishes the new release metadata and points clients at the refreshed language definitions.

## 🛠️ Technical Changes

- Update `__version__` from `1.0.0` to `1.1.0` in `src/updater.py`.
- Update `__lang_version__` from `v0.0.24` to `v0.0.25` in `src/updater.py`.
- Keep `__scripts_version__` unchanged.

## ⚠️ Impact/Warnings

- **Packaging:** `pyproject.toml` reads `__version__` at build time, so the published artifact version becomes `1.1.0`. Any release pipeline or pinned dependency on `1.0.0` must be reviewed.
- **Language dictionary:** The `v0.0.25` dictionary must already be published and reachable; otherwise clients picking up this release will fail to resolve the new dictionary version.
- **No database, environment variable, or dependency changes.**
- **No functional/behavioral changes** beyond version identifiers.