# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: bump GitPR, language and scripts versions
```

---

## 🎯 Summary

Update the project version identifiers to mark a new GitPR release and to point to the latest language dictionary and Git hook script bundles. The three version constants are tracked independently so that shipping new translations or hook scripts does not require a full application release, and vice versa.

## 🛠️ Technical Changes

- Bump `__version__` from `1.3.0` to `1.4.0` (GitPR application version).
- Bump `__lang_version__` from `v0.0.33` to `v0.0.34` (language dictionary version control).
- Bump `__scripts_version__` from `v0.0.3` to `v0.0.4` (Git hook scripts version control, independent from the language version).

## ⚠️ Impact/Warnings

- **Version resolution:** `pyproject.toml` reads `__version__` via setuptools `attr:`, so the published/installed package version changes to `1.4.0`. Downstream pins or lock files referencing `1.3.0` may need updating.
- **Runtime dependency:** clients fetching language dictionaries (`v0.0.34`) and hook scripts (`v0.0.4`) will now request the newer remote artifacts; those versions must exist in the corresponding distribution sources before release.
- No database, environment variable, or third-party dependency changes.


close #206

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)