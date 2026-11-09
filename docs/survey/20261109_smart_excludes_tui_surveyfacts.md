# Survey — Auditoria e Encerramento do Item 10 (Smart Excludes na TUI de Configuração)

- **Data:** 2026-11-09
- **Branch:** `develop_natan`
- **Origem:** Grill `/plan /grill-with-docs` (1 rodada, 3 decisões)
- **Objeto:** Auditoria técnica e encerramento formal do Item 10 herdado do survey da TUI de configuração
- **Estado:** Confirmado e Validado

---

## 1. Contexto da Tarefa

Nas versões anteriores do GitPR (desde a `v0.0.14` até a `v0.0.22`), o relatório de estado registrava continuamente:
> *Seção Smart Exclude na TUI: os campos `GITPR_SMART_EXCLUDES_*` seguem sob `diff`, sem categoria própria. **Item herdado, ainda aberto.***

Esta sessão de grill foi acionada para averiguar o status deste débito técnico herdado, mapear os fatos do código e formalizar a auditoria de conclusão.

---

## 2. Decisões Confirmadas no Grill (Rodada 1)

| # | Tema | Decisão |
|---|------|---------|
| **Q1** | Objetivo da Sessão | **Confirmação e Auditoria de Entrega (Opção A):** Fatos comprovam que o item 10 já foi codificado, testado e integrado na versão `v0.0.23` via PR #263 (commit `b3e547d`). O objetivo é auditar formalmente e confirmar a cobertura e o encerramento do item. |
| **Q2** | Escopo e Gaps da Seção | **Manter como está (Opção A):** A arquitetura atual e o conjunto de campos (`GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`, `SMART_EXCLUDES_VERSION`, `#excludes_pane` com 3 fontes e editor) atendem integralmente à especificação do Item 10 sem necessidade de novas mutações de código. |
| **Q3** | Formalização Documental | **Aprovar roteiro (Opção A):** Registrar os artefatos de governança em `docs/survey/`, `docs/plans/` e relatórios para manter o histórico de rastreabilidade do projeto. |

---

## 3. Fatos do Código Levantados e Auditados

1. **Remoção da categoria temporária `diff` e criação de `smart_excludes`:**
   - Em `src/config_schema.py:267-271`, a categoria `smart_excludes` está formalmente declarada com a descrição e documentação associada (`doc="smart-excludes.md"`).
   - Não existe nenhuma ocorrência ou categoria `"diff"` no menu lateral (`CATEGORY_ORDER`).

2. **Agrupamento dos campos de configuração:**
   - `src/config_schema.py:1440`: `GITPR_SKIP_SMART_EXCLUDES` (`KIND_BOOL`) sob categoria `smart_excludes`.
   - `src/config_schema.py:1450`: `GITPR_SMART_EXCLUDES_GLOBAL` (`KIND_PATH`) sob categoria `smart_excludes`.
   - `src/config_schema.py:1460`: `GITPR_SMART_EXCLUDES_LOCAL` (`KIND_PATH`) sob categoria `smart_excludes`.
   - `src/config_schema.py:1470`: `SMART_EXCLUDES_VERSION` (`KIND_VERSION`, com botão `ACTION_DOWNLOAD`) sob categoria `smart_excludes`.

3. **Painel especializado `#excludes_pane` em `src/ui/config_app.py`:**
   - Exibição dinâmica controlada por `self.selected_category() == "smart_excludes"` e ausência de termo de busca.
   - Lista de 3 fontes (`ListView`): Projeto (`excludeitem_project`), Global Core (`excludeitem_core`) e Global Docs (`excludeitem_docs`).
   - Botão de criação de arquivo local (`#excludes_create`) exibido quando `.gitpr/conf/gitpr.smart-excludes.json` ainda não existe no repositório.
   - Editor `TextArea` com modo editável para o projeto e modo somente leitura para as listas globais (Core e Docs).
   - Rastreio de dirty-state (`self.dirty_excludes()`) e salvamento atômico integrado com a tecla de atalho `F2`.

4. **Glossário de Domínio em `CONTEXT.md`:**
   - Termo canônico `Smart Excludes` documentado em `CONTEXT.md:162-168`, delimitando os termos recomendados e banindo termos obsoletos (`diff ignore`, `ignore patterns`).

5. **Testes Unitários e Automatizados:**
   - `tests/test_config_schema.py:436` (`test_smart_excludes_category_replaces_diff`): Valida que `smart_excludes` está presente, `diff` está ausente, e todos os 4 campos pertencem à categoria.
   - `tests/test_config_app.py:2020-2120` (`TestSmartExcludesSection`): Valida a montagem da sidebar, as 3 fontes, o estado read-only das listas globais, a criação do arquivo local e o salvamento via `F2`.
