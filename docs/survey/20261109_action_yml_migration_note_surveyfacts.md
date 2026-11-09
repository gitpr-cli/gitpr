# Levantamento de Fatos e Decisões de Grilling: Nota de Migração do `action.yml`

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Task:** `action_yml_migration_note`
- **Participantes:** Natan Fiuza, Antigravity

---

## 1. Contexto da Tarefa

No relatório de status `docs/reports/relatorio_estado_v0.0.22.md`, constava como item herdado e ainda aberto:
> *"Criar uma nota de migração para o `action.yml`: a troca de `--linter` + `--fullreview` por `gitpr check` é quebra de contrato para workflows existentes. Item herdado, ainda aberto."*

### Fatos Levantados na Investigação do Código
1. **Implementação prévia no PR #267 (commit `d1a06f3` em 05/11/2026):**
   - A Seção 7 ("Guia de Migração: Atualizando do Workflow Legado do Action" / "Migration Guide: Upgrading from Legacy Action Workflow") já foi redigida com paridade nos 5 idiomas suportados:
     - `docs/check-ci.md` (EN)
     - `docs/check-ci.pt_br.md` (PT-BR)
     - `docs/check-ci.pt_pt.md` (PT-PT)
     - `docs/check-ci.es_es.md` (ES-ES)
     - `docs/check-ci.fr_fr.md` (FR-FR)
   - O conceito ubíquo `Legacy CI action contract` foi catalogado em `CONTEXT.md`.
   - A suíte `tests/unit/test_check_ci_docs_parity.py` assegura a existência das 7 seções e das palavras-chave contratuais nos 5 arquivos.
   - O `docs/reports/relatorio_estado_v0.0.23.md` marcou o item como concluído.
2. **Pontas Soltas de Governança Identificadas:**
   - O `action.yml` não continha comentários orientando os usuários sobre a quebra contratual e o link para a documentação.
   - Não havia um ADR formalizado na pasta canônica `docs/adr/` (análogo ao `docs/adr/0009-reviewer-attach-returns-read-back.md` para a quebra de revisores).
   - O `CHANGELOG.md` não apresentava um aviso de quebra contratual (Breaking Changes) para os fluxos CI dependentes do `action.yml`.

---

## 2. Decisões das Rodadas de Grilling

Na Rodada 1 de grilling, as seguintes decisões foram consolidadas:

| Questão | Decisão | Justificativa |
|---|---|---|
| **Q1 — Escopo e Fechamento** | **Opção A (Recomendado)** | Aproveitar a Seção 7 existente em `docs/check-ci.*.md` e fechar o ciclo de governança adicionando ADR formal em `docs/adr/`, comentários em `action.yml` e destaque em `CHANGELOG.md`. |
| **Q2 — ADR Canônico** | **Opção A (Recomendado)** | Criar `docs/adr/0011-action-unified-check-migration.md` formalizando a decisão arquitetural da quebra de contrato da composite action, justificativas e trade-offs. |
| **Q3 — Comentários no `action.yml`** | **Opção A (Recomendado)** | Adicionar cabeçalho explicativo e link no topo do `action.yml` para direcionar qualquer desenvolvedor que inspecione a action. |
| **Q4 — Registro em `CHANGELOG.md`** | **Opção A (Recomendado)** | Inserir seção / alerta de quebra de contrato em `CHANGELOG.md` alertando sobre a substituição de `*_PR_FULLREVIEW.txt` por SARIF/`gitpr check`. |

---

## 3. Relatório de Fatos e Riscos

- **Risco de Quebra:** Nenhuma alteração de runtime será realizada. As mudanças são estritamente documentais e de metadados.
- **Risco de Paridade de Testes:** O teste `tests/unit/test_check_ci_docs_parity.py` continua passando sem alterações.
- **Risco de i18n:** Nenhuma string de código do CLI/TUI foi modificada; `test_i18n.py` permanece com 22 testes verdes e 1772 chaves idênticas.
