# Plano de Execução — Auditoria de Pendências (`🚧 Próximos Passos` e `🌐 Internacionalização e Documentação`)

- **Branch:** `develop_natan`
- **Data:** 2026-11-15
- **Task:** `audit_reports_pending_items`
- **Origem:** sessão `/plan /grill-with-docs` — análise de `docs/reports/`

## Objetivo

Consolidar todas as pendências reais das seções `🚧 Próximos Passos` e `🌐 Internacionalização e Documentação` dos 25 relatórios em `docs/reports/`, validando cada ponto no código-fonte e salvando o roteiro executável completo em `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

## Decisões

1. **Escopo das etapas:** `Etapa 1` a `Etapa 8` restringem-se a alterações determinísticas de código, testes, i18n e documentação no repositório.
2. **Separação de backlog/operação:** Reajuste de tag `v1.7.0`/release, `scripts/marketplace-setup-wizard.sh` com PATs e novos provedores de IA (OpenAI/locais) ficam documentados na Seção 3 (*Ações Operacionais do Mantenedor & Backlog Futuro*).
3. **Normalização de `docs/`:** `docs/github-issue-prompt-com-gh.md` será movido para `docs/extra/` na Etapa 3, eliminando `_EN_ONLY` em `tests/unit/test_docs_translation_parity.py`.
4. **Precisão factual:** Nomes reais de variáveis (`GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, padrões `90000`/`50000`) e caminho inexistente (`tests/unit/test_project_config_seed_docs.py` a ser criado) refletem exatamente o código inspecionado.

## Mudanças

| Área | Arquivo | Mudança |
| --- | --- | --- |
| Prompts | `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` | Criação da matriz consolidada (concluído vs. pendente), Etapas 1–8 executáveis e Seção 3 |
| Survey | `docs/survey/20261115_audit_reports_pending_items_surveyfacts.md` | Registro dos fatos verificados na auditoria |
| Plan (grill) | `docs/plans/develop_natan/20261115_audit_reports_pending_items_plansfacts.md` | Registro do plano de documentação/deliverable |
| Plan (GEMINI) | `docs/gemini/plans/develop_natan/2026-11-15_develop_natan_audit_reports_pending_items.md` | Plano conforme padrão `GEMINI.md` |
| Report | `docs/gemini/reports/develop_natan/2026-11-15_audit_reports_pending_items.md` | Relatório obrigatório de conclusão da tarefa |

## Riscos e limites aceitos

- Esta entrega documenta e instrui as `Etapa 1` a `Etapa 8`; nenhuma das 8 etapas foi aplicada no código nesta tarefa, conforme escopo aprovado na Rodada 1.
- Os comandos `pytest` listados em cada etapa são instruções de verificação para o agente executor quando executar o roteiro.
