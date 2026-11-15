# Implementation Plan — Audit of Pending Items (`docs/reports/`)

- **Date:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `audit_reports_pending_items`

## Goal

Audit all 25 status reports under `docs/reports/` focusing on **`🚧 Próximos Passos`** and **`🌐 Internacionalização e Documentação`**, cross-verify each claim against the current `develop_natan` working tree, and produce an actionable stage-by-stage execution report in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

## Approach

1. Inspect `docs/reports/relatorio_estado_ GitPR-CLI.md` through `relatorio_estado_v0.0.25.md` and aggregate all pending roadmap, i18n, and documentation items.
2. Verify current repository state (`src/updater.py`, `CLAUDE.md`, `GEMINI.md`, `CHANGELOG.md`, `src/ui/pr_publish_app.py`, `docs/mcp-integration.md`, `docs/config-tui*.md`, `docs/pull-request-publication*.md`, `docs/metricas-telemetria.md`, `docs/scm-multiforge.md`, `src/config.py`, `src/scm_settings.py`, `src/infrastructure/scm/github_provider.py`, `src/mcp_server.py`, `langs/*.json`, `extensions/vscode/`, `README*.md`, and doc/i18n/scm test suites) to filter out already-completed items and confirm exact gaps.
3. Align scope and deliverable format with the user (`Q1`–`Q3`) and write:
   - `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (Matrix + `Etapa 1`–`Etapa 8` + Maintainer/Future Backlog section)
   - Required `/grill-with-docs` survey and plan artifacts plus `GEMINI.md` plan and completion report.
