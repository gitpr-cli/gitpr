# Walkthrough: Action.yml Migration Guide (`gitpr check`)

This walkthrough details the addition of the "Before & After" Migration Guide for `action.yml` (`gitpr check`) across the documentation and domain model.

## 1. Domain Concept in `CONTEXT.md`
Added the formal domain definition:
- **Legacy CI action contract**: The previous GitHub Action workflow contract where `action.yml` sequentially executed discrete commands (`gitpr --linter` followed by `gitpr --fullreview`), generated an unclassified `*_PR_FULLREVIEW.txt` text artifact in the workspace, and required manual step-summary concatenation. Replaced by the unified `CI Check` pipeline producing SARIF/JSON/JUnit artifacts and deterministic exit codes.

---

## 2. Technical Documentation & Multilingual Parity

Section 7 (**Migration Guide / Guia de Migração / Guía de Migración / Guide de Migration**) was added to `docs/check-ci.md` and all four localized files. Additionally, missing earlier sections were completed to establish identical 7-section coverage across all 5 languages:

1. **Overview / Visão Geral / Visión General / Vue d'ensemble**
2. **CLI Options and Environment Variables**
3. **Exit Codes**
4. **Pipeline Execution Order**
5. **Artifact Formats (SARIF 2.1.0, JSON, JUnit XML)**
6. **GitHub Actions Integration**
7. **Migration Guide: Upgrading from Legacy Action Workflow**

### Key Points Covered in the Migration Guide:
- **Absence of `*_PR_FULLREVIEW.txt`**: Explains why `gitpr check` does not emit text files and how pipelines relying on `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` should be updated.
- **Native SARIF / Code Scanning**: Shows how to upload `gitpr-results.sarif` via `github/codeql-action/upload-sarif@v3`.
- **Optional API Key**: Explains zero-cost CI capability with `no-ia: "true"`.
- **Exit Codes and Baseline Suppressions**: Highlights `--fail-on` and suppression of legacy findings via `.gitpr/baseline.json`.
- **Side-by-side YAML snippets**: Comparing legacy vs modern workflow configurations.
- **Preserving Standalone Text Reviews**: Guidance on calling `gitpr --fullreview` directly for workflows that specifically need raw text outputs.

---

## 3. Automated Verification

Added `tests/unit/test_check_ci_docs_parity.py` which validates:
- Presence of all 5 localized files.
- Exact presence of sections 1 through 7 in every file.
- Presence of migration keywords (`action.yml`, `--linter`, `--fullreview`, `gitpr check`, `SARIF`).
- Presence of `Legacy CI action contract` in `CONTEXT.md`.

Test execution verified:
- `pytest tests/unit/test_check_ci_docs_parity.py`: **2 passed**
- Full test suite run (`test_config_schema.py`, `test_i18n.py`, `test_web_links.py`, `test_check_ci_docs_parity.py`): **102 passed**
