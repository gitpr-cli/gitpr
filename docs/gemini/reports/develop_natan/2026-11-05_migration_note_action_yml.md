## Completion Report — Migration Note for `action.yml` (`gitpr check`)

### What was done
- Documented the contract breaking change in `action.yml` (the transition from running `--linter` + `--fullreview` to `gitpr check`) by authoring a comprehensive "Before & After" Migration Guide in `docs/check-ci.md`.
- Completed missing sections across all localized versions, bringing full 7-section parity across the 5 supported languages:
  - `docs/check-ci.md` (EN): Added Section 7 (Migration Guide: Upgrading from Legacy Action Workflow).
  - `docs/check-ci.pt_br.md` (PT-BR): Added Section 6 (Integração com GitHub Actions) and Section 7 (Guia de Migração: Atualizando do Workflow Legado do Action).
  - `docs/check-ci.pt_pt.md` (PT-PT): Added Sections 4-7 (Pipeline, Formatos de Artefactos, Integração GitHub Actions, Guia de Migração).
  - `docs/check-ci.es_es.md` (ES-ES): Added Sections 4-7 (Orden de Ejecución, Formatos de Artefactos, Integración GitHub Actions, Guía de Migración).
  - `docs/check-ci.fr_fr.md` (FR-FR): Added Sections 4-7 (Ordre d'Exécution, Formats d'Artefacts, Intégration GitHub Actions, Guide de Migration).
- Added the ubiquitous domain concept `Legacy CI action contract` to `CONTEXT.md`.
- Added automated parity and contract verification tests in `tests/unit/test_check_ci_docs_parity.py`. Verified that all 102 tests pass across `test_config_schema.py`, `test_i18n.py`, `test_web_links.py`, and `test_check_ci_docs_parity.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/check-ci.md` | docs | Added Section 7 (Migration Guide: Upgrading from Legacy Action Workflow) with Before & After comparison and troubleshooting. |
| `docs/check-ci.pt_br.md` | docs | Completed Section 6 (GitHub Actions) and added Section 7 (Guia de Migração). |
| `docs/check-ci.pt_pt.md` | docs | Completed Sections 4-7 in European Portuguese. |
| `docs/check-ci.es_es.md` | docs | Completed Sections 4-7 in Spanish. |
| `docs/check-ci.fr_fr.md` | docs | Completed Sections 4-7 in French. |
| `CONTEXT.md` | docs | Added domain definition for `Legacy CI action contract`. |
| `tests/unit/test_check_ci_docs_parity.py` | test | Added automated test suite ensuring all 5 doc variants maintain 7-section parity and migration keywords. |

### Impact
- **Functionality:** CI pipeline maintainers now have clear technical documentation detailing why `*_PR_FULLREVIEW.txt` is no longer emitted by `action.yml`, how to transition to SARIF 2.1.0 and Code Scanning, and how to preserve standalone full reviews if necessary.
- **Performance:** Documentation and test-only changes; zero runtime overhead.
- **Compatibility:** Provides explicit migration steps for workflows upgrading across the breaking change from v0.0.36 to v0.0.37+.

### Next steps (if applicable)
- Technical debt documented in `docs/reports/relatorio_estado_v0.0.22.md` for `action.yml` migration is now fully resolved and guarded by automated tests.
