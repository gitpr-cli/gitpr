# Implementation Plan: Migration Note for `action.yml` (`gitpr check`)

## Goal Description
Document the breaking contract introduced when `action.yml` transitioned from running sequential discrete commands (`gitpr --linter` followed by `gitpr --fullreview` with `*_PR_FULLREVIEW.txt` appended to `$GITHUB_STEP_SUMMARY`) to the unified `gitpr check` CI command with SARIF/JSON/JUnit artifact generation.

This change is documented as a comprehensive "Before & After" Migration Guide in `docs/check-ci.md` and localized across all 5 documentation languages (`en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`), bringing full section parity across the localized docs and formalizing the concept in `CONTEXT.md`.

---

## User Review Required

> [!IMPORTANT]
> **Behavioral Contract Breakage:**
> - `*_PR_FULLREVIEW.txt` is no longer created on disk by `action.yml`. Workflows that relied on `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` fail or produce empty summaries.
> - The replacement is SARIF 2.1.0 (default `gitpr-results.sarif`) uploaded via `github/codeql-action/upload-sarif@v3`.
> - Workflows that explicitly require text-based full reviews must invoke `gitpr --fullreview` directly instead of using `action.yml`.

> [!NOTE]
> **Documentation Parity Enhancement:**
> In addition to adding Section 7 (Migration Guide), this plan completes Sections 4-6 in `docs/check-ci.{pt_pt,es_es,fr_fr}.md` and Section 6 in `docs/check-ci.pt_br.md` so that all 5 localized files share the same sections and depth.

---

## Proposed Changes

Grouped by component:

### 1. Domain Modeling (`CONTEXT.md`)

#### [MODIFY] `CONTEXT.md`
Add domain entry for `Legacy CI action contract`:
- **Legacy CI action contract**: The previous GitHub Action workflow contract where `action.yml` sequentially executed `--linter` and `--fullreview`, generated an unclassified `*_PR_FULLREVIEW.txt` text artifact in the workspace, and required manual step-summary concatenation. Replaced by the unified `CI Check` pipeline producing SARIF/JSON/JUnit artifacts and deterministic exit codes.

---

### 2. Technical Documentation (`docs/check-ci.*.md`)

#### [MODIFY] `docs/check-ci.md` (English SSOT)
Add Section 7: **Migration Guide: Upgrading from Legacy Action Workflow**:
1. **Contract Differences Summary Table**:
   - Execution model (`--linter` + `--fullreview` vs `gitpr check`)
   - Artifacts generated (`*_PR_FULLREVIEW.txt` vs `gitpr-results.sarif` / JSON / JUnit)
   - Step Summary integration (manual file cat vs native GitHub Code Scanning SARIF tab)
   - Inputs (`api-key` required vs optional; new inputs: `format`, `output`, `fail-on`, `no-ia`, `baseline`, `policy`)
   - Failure criteria (unconditional linter/review crash vs configurable `--fail-on` with baseline suppressions)
2. **Before and After Workflow Examples**:
   - *Before (v0.0.12 - v0.0.36)*: showing `gitpr --linter`, `gitpr --fullreview`, `api-key: ${{ secrets.GEMINI_API_KEY }}`, and `REVIEW_FILE=$(ls *_PR_FULLREVIEW.txt)`.
   - *After (v0.0.37+)*: showing `action.yml` with `format: sarif`, `upload-sarif@v3`, and optional `no-ia: "true"`.
3. **Migration Steps & Troubleshooting**:
   - Removing references to `*_PR_FULLREVIEW.txt`.
   - Adding `security-events: write` permission to the job for SARIF upload.
   - Preserving legacy markdown reviews if explicitly desired (running `gitpr --fullreview` as a standalone run step).

#### [MODIFY] `docs/check-ci.pt_br.md` (Português - Brasil)
- Complete Section 6: Integração com GitHub Actions.
- Add Section 7: Guia de Migração: Atualizando do Workflow Legado do Action.

#### [MODIFY] `docs/check-ci.pt_pt.md` (Português - Portugal)
- Complete Sections 4-6 (Pipeline, Formatos de Artefatos, Integração GitHub Actions).
- Add Section 7: Guia de Migração: Atualizando do Fluxo de Trabalho Legado da Action.

#### [MODIFY] `docs/check-ci.es_es.md` (Español)
- Complete Sections 4-6 (Orden de Ejecución, Formatos de Artefactos, Integración GitHub Actions).
- Add Section 7: Guía de Migración: Actualización desde el Flujo de Trabajo Heredado de Action.

#### [MODIFY] `docs/check-ci.fr_fr.md` (Français)
- Complete Sections 4-6 (Ordre d'Exécution, Formats d'Artefacts, Intégration GitHub Actions).
- Add Section 7: Guide de Migration : Mise à Niveau depuis le Workflow Hérité d'Action.

---

### 3. Tests & Consistency Verification

#### [MODIFY] `tests/test_web_links.py` or new consistency test
Verify that:
- All 5 `docs/check-ci.*.md` files exist, contain Section 7 / Migration Guide heading, and code blocks parse cleanly without broken anchors.

---

## Verification Plan

### Automated Tests
- Run `pytest tests/test_web_links.py tests/test_i18n.py` to ensure link integrity and i18n stability.
- Run a custom verification script checking that all 5 files contain matching section headers and valid YAML blocks.

### Manual Verification
- Inspect the formatted markdown rendering of the "Before & After" YAML blocks to ensure syntax highlighting and line formatting are crystal clear.
