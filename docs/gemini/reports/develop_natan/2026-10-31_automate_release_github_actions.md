## Completion Report — Automate PyPI & GitHub Release via GitHub Actions

### What was done
- Created `.github/workflows/release.yml` with a 4-job automated pipeline triggered on Git version tags (`v*`), PRs altering the workflow (dry-run validation), and manual `workflow_dispatch`.
- Configured pre-release test execution (`pytest tests/ -q`) to guarantee that broken code is never published.
- Added a strict consistency guard asserting `v${__version__} == ${GITHUB_REF_NAME}` before building the package distributions, preventing accidental mismatches between Git tags and package versions.
- Added package distribution build (`sdist` and `wheel`) and strict metadata validation using `twine check --strict dist/*`.
- Configured secure Trusted Publishing (OIDC) to PyPI via `pypa/gh-action-pypi-publish@release/v1` targeting the `pypi` environment with ephemeral token generation (`permissions: id-token: write`).
- Configured automated GitHub Release creation via `softprops/action-gh-release@v2`, attaching the compiled distribution packages and generating release notes automatically.
- Defined new domain terms (`Release workflow` and `Trusted publishing`) in `CONTEXT.md`.
- Updated `docs/reports/relatorio_estado_v0.0.21.md` and `GEMINI.md` to reflect the automated CI/CD release workflow.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `.github/workflows/release.yml` | feat | New automated PyPI and GitHub release workflow |
| `CONTEXT.md` | docs | Added domain terms for Release workflow and Trusted publishing |
| `GEMINI.md` | docs | Updated publishing instructions documenting the automated release workflow |
| `docs/reports/relatorio_estado_v0.0.21.md` | docs | Updated CI/CD overview and closed inherited backlog item |

### Impact
- **Functionality:** Replaces manual builds and manual `twine upload dist/*` with an automated, secure CI/CD release pipeline triggered whenever a version tag (`v*`) is pushed.
- **Performance:** Completely removes manual packaging overhead while running test suites and package metadata verification in parallel or sequence.
- **Compatibility:** Fully compatible with PEP 440, PyPA packaging standards, and existing Git tag naming conventions (`v*`).

### Next steps (if applicable)
- In PyPI project settings (`https://pypi.org/manage/project/gitpr-cli/settings/publishing/`), ensure the GitHub publisher is linked with workflow `release.yml` and environment `pypi`.
