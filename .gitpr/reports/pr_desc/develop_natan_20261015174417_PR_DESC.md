# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add unified gitpr check CI command with SARIF/JSON/JUnit output
```

---

## 🎯 Summary

Consolidates the fragmented CI workflow (separate linter and AI review steps) into a single, deterministic `gitpr check` command that emits machine-readable artifacts. This unifies code review, linting, secret scanning, risk scoring, and baseline classification behind one entry point with predictable exit codes, enabling native integration with GitHub Code Scanning, GitLab SAST, Azure DevOps, and JUnit-consuming CI systems.

## 🛠️ Technical Changes

- **New CLI command `gitpr check`** (`src/main.py`) with options `--base`, `--format`, `--output`, `--fail-on`, `--no-ia`, `--ia-only-high-risk`, `--baseline`, and `--policy`.
- **New use case** `src/application/use_cases/run_check.py` orchestrating the full pipeline: policy resolution, diff extraction, linter/secret scanning, optional AI review, preliminary risk scoring, baseline classification, and deterministic exit codes (`0` success, `1` blocking findings, `2` incomplete/error).
- **New `check` domain module** (`src/domain/check/`): `check_types.py` (severity model, finding/result/summary types), `check_config.py` (config with CLI > env > defaults precedence), and `check_output.py` (format dispatch and atomic file writing).
- **New CI infrastructure** (`src/infrastructure/ci/`): `sarif_builder.py` (SARIF 2.1.0), `junit_builder.py` (JUnit XML), and `masking.py` (regex-based masking of AWS keys, GitHub/OpenAI/Gemini/Slack tokens, private keys, bearer tokens, and basic-auth URLs).
- **Refactored `action.yml`** into a single `gitpr check` step exposing the new inputs; `api_key` is no longer required and a `--no-ia` path enables zero-cost runs.
- **i18n**: added strings for the new command and messages across all 6 supported locales.
- **Tests**: new unit and CLI coverage for config precedence, output builders, masking, and use case exit-code behavior.

## ⚠️ Impact/Warnings

- **Breaking change to `action.yml`**: the previous `--linter` + `--fullreview` execution is replaced by `gitpr check`. Existing workflows relying on the old step behavior or the `*_PR_FULLREVIEW.txt` artifact must migrate.
- **API key is now optional** (`required: false`, default empty); when unset, AI review is skipped with a warning instead of failing.
- **Exit code contract**: `2` is now returned for tampered/corrupt baselines, invalid policies, and mid-run AI failures — CI pipelines must handle it.
- **New environment variables** for configuration: `GITPR_CHECK_BASE`, `GITPR_CHECK_FORMAT`, `GITPR_CHECK_OUTPUT`, `GITPR_CHECK_FAIL_ON`, `GITPR_CHECK_NO_IA`, `GITPR_CHECK_IA_ONLY_HIGH_RISK`, `GITPR_CHECK_BASELINE_PATH`, `GITPR_CHECK_POLICY`, `GITPR_CHECK_TIMEOUT_SECONDS`.
- **Default behavior change**: output defaults to SARIF written to `gitpr-results.sarif` and runs fail on `error` severity, which may surface newly blocking findings on first adoption. No database migrations involved.


close #209

---

[![GitPR](https://img.shields.io/badge/GitPR-13_errors_%C2%B7_20_warnings-red)](https://gitpr.natanfiuza.dev.br/)