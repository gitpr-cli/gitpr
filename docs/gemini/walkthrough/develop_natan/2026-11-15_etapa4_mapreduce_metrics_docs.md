# Walkthrough — Etapa 4: Map-Reduce Cost and Latency Documentation

## Changes Made
- Added `### Map-Reduce Cost and Latency` right after `### Cost and Rates` in:
  - [metricas-telemetria.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/metricas-telemetria.md)
  - [metricas-telemetria.pt_br.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/metricas-telemetria.pt_br.md)
  - [metricas-telemetria.pt_pt.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/metricas-telemetria.pt_pt.md)
  - [metricas-telemetria.es_es.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/metricas-telemetria.es_es.md)
  - [metricas-telemetria.fr_fr.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/metricas-telemetria.fr_fr.md)
- Updated [0022-map-reduce-per-provider-token-partitioning.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/adr/0022-map-reduce-per-provider-token-partitioning.md) with cross-references in `Relacionados` and `## 3. Consequências`.
- Marked **P4 / Etapa 4** as concluded in [relatorio_pendencias_proximos_passos_i18n.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/prompts/relatorio_pendencias_proximos_passos_i18n.md).

## What Was Tested & Validation Results
- `python -m pytest tests/unit/test_docs_translation_parity.py -v`: all 3 parity tests passed (`test_every_doc_has_all_four_languages`, `test_translations_match_english_structure`, `test_parity_exceptions_are_still_real`).
- Note: `tests/test_metrics.py` was also started in the combined run; non-UI tests up to `TestMigrationWizard::test_an_abort_does_not_leave_an_empty_ledger_behind` passed, and `TestMigrationWizardUi::test_importing_is_the_primary_button` hung in the sandbox environment and was cancelled.
