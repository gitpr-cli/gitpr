# Canonical Package Version SSOT and Agent Documentation Synchronization

`src/updater.py::__version__` is the sole canonical Single Source of Truth (SSOT) for the GitPR distribution package version. Agent context files (`CLAUDE.md`, `GEMINI.md`) must reflect this exact version and cite `src/updater.py`, guarded against future documentation drift by automated consistency tests.

## Context

GitPR is distributed exclusively through PyPI, where package builds (`pyproject.toml`), runtime CLI banners and version options (`src/main.py`), and CI release verification (`.github/workflows/release.yml`) all consume `src.updater.__version__`. However, agent context files (`CLAUDE.md` and `GEMINI.md`) previously contained a static, unverified `0.0.37` string that fell out of sync with the runtime version (`1.4.4`). Furthermore, `src/updater.py` contains independent asset versions (`__lang_version__` and `__scripts_version__`) that were easily conflated with the package version.

## Decision

1. **Canonical SSOT**: `src/updater.py::__version__` is the only authoritative location defining the package release version. `pyproject.toml` binds dynamically to this attribute.
2. **Agent Documentation Synchronization**: `CLAUDE.md` and `GEMINI.md` display the active package version alongside an explicit reference to `src/updater.py`.
3. **Automated Drift Guard**: An automated test (`tests/unit/test_version_consistency.py`) enforces that `CLAUDE.md`, `GEMINI.md`, and `pyproject.toml` remain strictly in lockstep with `src.updater.__version__`.
4. **Domain Separation**: `CONTEXT.md` explicitly defines the boundary between the package version and asset versions (`__lang_version__`, `__scripts_version__`).

## Consequences

Any future release bump that changes `src.updater.__version__` must also update `CLAUDE.md` and `GEMINI.md`. If a bump omits these documents, the automated consistency test will fail in CI, preventing silent documentation divergence.
