# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
chore: add automated PyPI and GitHub release workflow
```

---

## 🎯 Summary
Adds a GitHub Actions release workflow to automate package build verification, PyPI publishing via Trusted Publishing, and GitHub Release creation when a version tag is pushed. This reduces manual release steps and prevents publishing a tag that does not match the package version.

## 🛠️ Technical Changes
- Add `.github/workflows/release.yml` triggered by `v*` tags, workflow file changes, and manual dispatch.
- Run the test suite on Python 3.11 with pytest and create a temporary GitPR profile for tests.
- Verify the Git tag matches `src.updater.__version__` and abort the release on mismatch.
- Build sdist and wheel distributions, validate metadata with `twine check --strict`, and upload build artifacts.
- Publish to PyPI using `pypa/gh-action-pypi-publish` with OIDC trusted publishing and the `pypi` environment.
- Create a GitHub Release with generated release notes and attach the distribution artifacts.
- Scope permissions and limit publish/release jobs to version tags.

## ⚠️ Impact/Warnings
- Requires PyPI Trusted Publisher configuration for `gitpr-cli` and a GitHub environment named `pypi`; no PyPI token secret is used.
- Version tags must follow `v{__version__}` and match `src.updater.__version__`, otherwise the release fails intentionally.
- CI installs `pytest`, `build`, and `twine`; no runtime dependencies or database changes are introduced.
- Required workflow permissions: `id-token: write` for PyPI publishing and `contents: write` for GitHub Release creation.
- Manual dispatch runs test/build jobs, but publishing and release creation only run for `v*` tags.

close #240

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)