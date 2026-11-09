# Plano de Execução — Auditoria e Encerramento das Dívidas da TUI de Configuração

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Task:** `config_tui_debts`
- **Origem:** Grill `/plan /grill-with-docs` (1 rodada, 3 decisões aprovadas)

---

## 1. Objetivo

Formalizar a auditoria técnica de validação e encerramento definitivo das 4 dívidas técnicas herdadas da TUI de Configuração, consolidadas a partir do relatório de estado `docs/reports/relatorio_estado_v0.0.22.md` e já entregues na versão `v0.0.23` via PR #265 (commit `74f8c38`).

---

## 2. Roteiro de Execução

1. **Auditoria Factual do Código:**
   - Conferência de `src/config_schema.py` (`ConfigField.seeded`, `DEFAULT_CONFIG` derivado, categoria `check`, 9 campos `GITPR_CHECK_*`).
   - Conferência de `src/config.py` (importação direta de `DEFAULT_CONFIG`).
   - Conferência de `src/main.py` (`print_banner()` contendo `--init`, `--base` e `--plugins`).
   - Conferência de `src/ui/linter_app.py` (`ENABLE_COMMAND_PALETTE = False`).
   - Conferência dos arquivos de internacionalização em `langs/`.

2. **Validação da Suíte de Testes Automatizados:**
   - Execução de `pytest tests/test_config_schema.py -v`.
   - Garantir que todos os 55 testes passem (incluindo `TestCheckCategory`, `TestTUIDebtsResolved` e `TestSchemaCoversDefaults`).

3. **Geração dos Artefatos de Rastreabilidade e Governança:**
   - Levantamento de fatos em `docs/survey/20261109_config_tui_debts_surveyfacts.md` (criado).
   - Plano de execução em `docs/plans/develop_natan/20261109_config_tui_debts_plansfacts.md` (este documento).
   - Plano técnico Gemini em `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_config_tui_debts.md`.
   - Relatório de conclusão mandatório em `docs/gemini/reports/develop_natan/2026-11-09_config_tui_debts.md`.
   - Walkthrough de validação em `docs/gemini/walkthrough/develop_natan/2026-11-09_config_tui_debts.md`.

---

## 3. Critérios de Sucesso

- 100% dos 4 sub-itens confirmados no código-fonte.
- 100% dos testes relevantes passando sem regressões.
- Documentação histórica e de governança sincronizada e versionada.
