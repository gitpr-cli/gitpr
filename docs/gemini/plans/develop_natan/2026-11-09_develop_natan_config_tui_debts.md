# Implementation Plan — Auditoria e Encerramento das Dívidas da TUI de Configuração

**Branch**: `develop_natan`  
**Date**: `2026-11-09`  
**Task**: `config_tui_debts`

## Goal Description
Realizar a auditoria técnica de validação e o encerramento formal do item herdado registrado em `docs/reports/relatorio_estado_v0.0.22.md`:
> *Dívidas registradas no plano do config TUI: `DEFAULT_CONFIG` ficou redundante com o schema; o banner de abertura não lista `--init`, `--base` nem `--plugins`; o `LinterApp` é o **único** app Textual que ainda não desabilita a command palette; e as **9 `GITPR_CHECK_*`** ainda **não** têm categoria no schema. **Item herdado, ainda aberto.***

Os fatos levantados demonstram que as implementações correspondentes foram entregues no PR #265 (commit `74f8c38`) e registradas como concluídas em `docs/reports/relatorio_estado_v0.0.23.md`. O objetivo deste plano é consolidar a verificação formal, auditar os 4 sub-itens e emitir os artefatos de governança necessários.

## User Review Required
> [!NOTE]
> As decisões de escopo foram alinhadas e confirmadas na Rodada 1 do grill:
> - **Q1 (Objetivo):** Opção A (Recomendado) — Auditoria e Encerramento Formal do Item.
> - **Q2 (Testes e Domínio):** Opção A (Recomendado) — Manter como está, aproveitando a cobertura existente.
> - **Q3 (Governança):** Opção A (Recomendado) — Roteiro completo de artefatos de auditoria.

## Open Questions
Nenhuma pergunta aberta pendente; fronteira do grill esgotada.

## Proposed Changes

### Governança e Rastreabilidade Documental
Nenhuma alteração de código produtivo é necessária, visto que os 4 pontos já estão integrados e verificados:
1. `DEFAULT_CONFIG` derivado de `ConfigField.seeded` em `src/config_schema.py` e importado em `src/config.py`.
2. `--init`, `--base` e `--plugins` presentes no banner em `src/main.py:254` e sincronizados nos arquivos `langs/*.json`.
3. `ENABLE_COMMAND_PALETTE = False` definido em `src/ui/linter_app.py:53`.
4. Categoria `"check"` e as 9 variáveis `GITPR_CHECK_*` registradas em `src/config_schema.py`.

#### [NEW] `docs/survey/20261109_config_tui_debts_surveyfacts.md`
Fatos e decisões da auditoria técnica.

#### [NEW] `docs/plans/develop_natan/20261109_config_tui_debts_plansfacts.md`
Plano de execução da auditoria técnica.

#### [NEW] `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_config_tui_debts.md`
Plano técnico detalhado do Gemini (este documento).

#### [NEW] `docs/gemini/reports/develop_natan/2026-11-09_config_tui_debts.md`
Relatório mandatório de conclusão da tarefa.

#### [NEW] `docs/gemini/walkthrough/develop_natan/2026-11-09_config_tui_debts.md`
Walkthrough de validação e comprovação da auditoria.

## Verification Plan

### Automated Tests
Executar a suíte de testes de integridade do schema e das dívidas resolvidas:
```bash
python -m pytest tests/test_config_schema.py -v
```

Cenários validados:
- `TestSchemaCoversDefaults::test_default_config_derived_from_seeded_fields`: confirma derivação de `DEFAULT_CONFIG` via `seeded=True`.
- `TestCheckCategory::test_check_category_declared_and_documented`: confirma presença da categoria `check` e documentação `check-ci.md`.
- `TestCheckCategory::test_check_fields_present_and_not_seeded`: confirma a presença dos 9 campos `GITPR_CHECK_*` com `seeded=False`.
- `TestTUIDebtsResolved::test_linter_app_disables_command_palette`: confirma que `LinterApp.ENABLE_COMMAND_PALETTE == False`.
- `TestTUIDebtsResolved::test_banner_includes_init_and_base`: confirma que o banner inclui `--init`, `--base` e `--plugins`.

### Manual Verification
- Inspeção estática de `src/main.py`, `src/config_schema.py`, `src/config.py` e `src/ui/linter_app.py`.
- Inspeção de conformidade dos termos em `CONTEXT.md`.
