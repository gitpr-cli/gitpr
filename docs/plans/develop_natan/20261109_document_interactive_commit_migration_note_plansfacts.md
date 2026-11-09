# Execution Plan Facts — Documentação da Quebra de Comportamento do `-c` Interativo como Nota de Migração

**Data:** 2026-11-09  
**Branch:** develop_natan  
**Task:** document_interactive_commit_migration_note  

---

## 1. Visão Geral

Adicionar formalmente a nota de migração documentando a alteração comportamental de `gitpr -c` (`--commit`). O comando, que antes da v1.4.4 era puramente um utilitário silencioso de console que imprimia a mensagem sem comitar, passou a abrir um fluxo TUI interativo completo de 4 etapas que realiza o commit no repositório. Para ambientes automatizados e CI, orientar expressamente o uso de `--hook <arquivo>` e detalhar o fallback de console sob ausência de TTY.

---

## 2. Etapas de Execução

### Etapa 1: Atualização do Modelo de Domínio (`CONTEXT.md`)
- Refinar a entrada `Commit flow` para enfatizar a dependência de um `Interactive run` para a execução efetiva do commit e a distinção em relação a execuções em scripts/hooks/CI.

### Etapa 2: Atualização dos Documentos Técnicos em 5 Idiomas
- **`docs/commit-message-ia.md` (EN)**:
  - Adicionar callout `> [!WARNING] Migration Note (Interactive Workflow vs. Silent Legacy)` ao final da Seção 1.
  - Atualizar a Seção 3 ("Git Hooks Integration (Non-Interactive)") com nota expressa sobre CI e automação headless via `--hook`.
- **`docs/commit-message-ia.pt_br.md` (PT-BR)**:
  - Adicionar callout `> [!WARNING] Nota de Migração (Fluxo Interativo vs. Legado Silencioso)`.
  - Atualizar a Seção 3 com orientações de CI/Hooks.
- **`docs/commit-message-ia.pt_pt.md` (PT-PT)**:
  - Adicionar callout `> [!WARNING] Nota de Migração (Fluxo Interativo vs. Legado Silencioso)`.
  - Atualizar a Seção 3 com orientações de CI/Hooks em português europeu.
- **`docs/commit-message-ia.es_es.md` (ES-ES)**:
  - Adicionar callout `> [!WARNING] Nota de Migración (Flujo Interactivo vs. Legado Silencioso)`.
  - Atualizar a Seção 3 com orientações de CI/Hooks em espanhol.
- **`docs/commit-message-ia.fr_fr.md` (FR-FR)**:
  - Adicionar callout `> [!WARNING] Note de Migration (Flux Interactif vs. Silencieux Legacy)`.
  - Atualizar a Seção 3 com orientações de CI/Hooks em francês.

### Etapa 3: Validação Automatizada
- Executar `pytest tests/test_doc_links.py` para garantir integridade dos links e paridade documental.
- Executar a suíte de testes de commit (`pytest tests/test_commit_app.py tests/test_core.py`) para assegurar que nada foi quebrado.

---

## 3. Critérios de Aceite
- Todos os 5 arquivos de `docs/commit-message-ia.*.md` contêm a nota de migração destacando o comportamento anterior (< 1.4.4) e a instrução clara para CI usando `--hook`.
- `CONTEXT.md` reflete fielmente o modelo conceitual.
- Todos os testes de documentação e cobertura passam com 100% de sucesso.
