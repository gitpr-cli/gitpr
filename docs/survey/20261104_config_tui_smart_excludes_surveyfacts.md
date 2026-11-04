# Survey — Seção Smart Exclude na TUI de Configuração (Item 10)

- **Data:** 2026-11-04
- **Branch:** `develop_natan`
- **Origem:** Grill `/plan /grill-with-docs` (2 rodadas, 9 decisões)
- **Objeto:** Encerramento do Item 10 herdado do survey da TUI de configuração
- **Estado:** Planejado, pronto para execução

## 1. Contexto da Tarefa

Nas versões anteriores do GitPR (desde a v0.0.14 até a v0.0.22), o relatório de estado registrava continuamente:
> *Seção Smart Exclude na TUI: o item 10 do survey da TUI de configuração continua não iniciado, e os campos `GITPR_SMART_EXCLUDES_*` seguem sob `diff`, sem categoria própria. **Item herdado, ainda aberto.***

No schema de configuração (`src/config_schema.py`), a categoria `"diff"` continha exclusivamente três campos: `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL` e `GITPR_SMART_EXCLUDES_LOCAL`. O marcador `SMART_EXCLUDES_VERSION` estava isolado na categoria `"advanced"`, e não havia visualização ou gestão das listas de padrões dentro da TUI.

Esta tarefa resolve definitivamente o item 10 criando a categoria dedicada `smart_excludes`, movendo os campos e o marcador de versão para ela, e introduzindo um painel dedicado com visualização das listas globais (Core e Docs) e editor de padrões do projeto (`.gitpr/conf/gitpr.smart-excludes.json`).

## 2. Decisões Confirmadas no Grill (Rodadas 1 e 2)

### Rodada 1 — Identidade, Escopo e Arquitetura

| # | Tema | Decisão |
|---|------|---------|
| Q1 | Identidade da Categoria | Substituir e renomear diretamente a categoria `diff` por `smart_excludes` (`id="smart_excludes"`, label `Smart Excludes`, doc `smart-excludes.md`). A categoria vazia `diff` é removida. |
| Q2 | Escopo da Seção na TUI | Escopo Completo (Item 10 integral): Formulário com campos do `.env` e versão + painel inferior especializado para visualização e edição das listas de exclusão. |
| Q3 | Marcador de Versão | Mover `SMART_EXCLUDES_VERSION` ("Filters List Version") da categoria `advanced` para `smart_excludes`, com botão de forçar download atualizado. |
| Q4 | Criação do Arquivo Local | Botão explícito na TUI para semear `.gitpr/conf/gitpr.smart-excludes.json` caso não exista no workspace (sem auto-seed silencioso). |
| Q5 | Glossário de Domínio | Registrar o termo canônico "Smart Excludes" em `CONTEXT.md`. |

### Rodada 2 — Interação, Formato do Editor e Ciclo de Vida

| # | Tema | Decisão |
|---|------|---------|
| Q6 | Formato de Edição dos Padrões | Um padrão glob por linha em `TextArea`. Linhas vazias ou com `#` são ignoradas; ao salvar, converte para lista JSON limpa preservando `_comment`. |
| Q7 | Navegação entre Fontes | Seletor de lista (idêntico ao modelo de Skills) com as 3 opções: Projeto (editável), Global Core (somente leitura), Global Docs (somente leitura). |
| Q8 | Ciclo de Vida (`F2`, `Ctrl+R`, `Esc`) | `F2` unificado salva arquivo do projeto junto com pendências do `.env`; `Ctrl+R` reverte para o disco; `Esc` com alterações pendentes pede confirmação. |
| Q9 | Documentação e Testes | Atualizar `docs/smart-excludes.md` e suas 4 versões traduzidas (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`), com testes automatizados em `test_config_schema.py` e `test_config_app.py`. |

## 3. Fatos do Código Levantados

1. **`CATEGORIES` e `CATEGORY_ORDER`**: `src/config_schema.py:152-261` define as categorias. A substituição de `diff` por `smart_excludes` mantém `test_config_schema.py` e `test_config_app.py` válidos, pois o índice 0 (general), 1 (ai) e 2 (pr) permanecem inalterados, e `advanced` continua como última categoria.
2. **`ConfigApp` e Panes Especializados**: `src/ui/config_app.py` já possui a arquitetura completa para lidar com panes de arquivos (estabelecida em `_SKILL_PANE_ID`, `dirty_skills()`, `_write_skills()`). Replicaremos esse padrão para `_EXCLUDES_PANE_ID`.
3. **Carga e Seed de Exclusões**: `src/core.py:118-281` implementa `_seed_local_smart_excludes()`, `_download_smart_excludes()`, e `_load_smart_excludes()`. O arquivo local do projeto reside em `.gitpr/conf/gitpr.smart-excludes.json`.
4. **Traduções e i18n**: As chaves literais `__("...")` novas adicionadas no schema e na TUI deverão ser incluídas diretamente nos 5 arquivos `langs/*.json` (`pt_br`, `pt_pt`, `es_es`, `fr_fr`, mantendo fallback em inglês) para passar no gate rígido de `tests/test_i18n.py`.
