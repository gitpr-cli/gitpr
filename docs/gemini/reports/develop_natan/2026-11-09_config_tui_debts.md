## Completion Report — Auditoria e Encerramento das Dívidas da TUI de Configuração

### What was done
- Conduzida auditoria técnica e validação formal do item herdado das dívidas do plano do config TUI (`docs/reports/relatorio_estado_v0.0.22.md`):
  1. `DEFAULT_CONFIG` derivado do schema via `ConfigField.seeded` (eliminando redundância e duplicação em `src/config.py`).
  2. Banner de abertura em `src/main.py:254` atualizado com `--init`, `--base` e `--plugins`, sincronizado em todos os 6 arquivos de tradução em `langs/`.
  3. Desativação da command palette em `LinterApp` (`src/ui/linter_app.py:53`) via `ENABLE_COMMAND_PALETTE = False`.
  4. Inclusão da categoria `check` e das 9 variáveis `GITPR_CHECK_*` no schema declarativo (`src/config_schema.py`).
- Executada verificação automatizada completa via pytest com 55 testes passando em `tests/test_config_schema.py`.
- Gerados artefatos de rastreabilidade e governança documental:
  - `docs/survey/20261109_config_tui_debts_surveyfacts.md`
  - `docs/plans/develop_natan/20261109_config_tui_debts_plansfacts.md`
  - `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_config_tui_debts.md`
  - `docs/gemini/walkthrough/develop_natan/2026-11-09_config_tui_debts.md`
  - `docs/gemini/reports/develop_natan/2026-11-09_config_tui_debts.md`

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/survey/20261109_config_tui_debts_surveyfacts.md` | docs | Survey facts levantados na sessão de grill. |
| `docs/plans/develop_natan/20261109_config_tui_debts_plansfacts.md` | docs | Plano de execução da auditoria. |
| `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_config_tui_debts.md` | docs | Plano técnico detalhado do Gemini. |
| `docs/gemini/walkthrough/develop_natan/2026-11-09_config_tui_debts.md` | docs | Walkthrough comprovando a conformidade dos 4 sub-itens. |
| `docs/gemini/reports/develop_natan/2026-11-09_config_tui_debts.md` | docs | Relatório mandatório de conclusão da tarefa. |

### Impact
- **Functionality:** O item herdado do relatório de estado da `v0.0.22` encontra-se formalmente auditado e concluído, com rastreabilidade completa e cobertura garantida pelos testes de regressão existentes (`TestCheckCategory`, `TestTUIDebtsResolved`, `TestSchemaCoversDefaults`).
- **Performance:** Nulo. Não houve alterações no fluxo de runtime; testes executam de forma determinística em segundos.
- **Compatibility:** Total compatibilidade retroativa mantida em todas as superfícies do CLI e da TUI.

### Next steps (if applicable)
- Todas as dívidas listadas no item foram auditadas, validadas e formalmente encerradas.
