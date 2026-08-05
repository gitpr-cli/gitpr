---
name: cache-filter-repo-branch
description: Cache JSON inclui campo repo; filtro por repo_name + branch_name evita colisões entre projetos
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-02_cache_repo.md
  date: 2026-07-02
  branch: develop_natan
---

Todos os arquivos JSON de cache gerados pelo GitPR incluem o campo `"repo": "owner/repo"`.
A função `get_cached_pr_descriptions()` em `src/cache.py` filtra por `repo_name` E `branch_name`,
evitando misturar caches de projetos diferentes que tenham branches com o mesmo nome
(ex: duas branches `feature/login` em repositórios distintos).

A função `get_repo_name()` em `src/core.py` extrai `owner/repo` do `git remote -v`.
O cache de PR usa `save_cached_response()` que grava o campo `"repo"` automaticamente.

**Why:** Antes dessa mudança, o `--history` filtrava apenas por nome de branch.
Dois projetos diferentes com branches de mesmo nome retornavam dados do projeto errado.
Caches antigos sem o campo `"repo"` são ignorados silenciosamente pelo novo filtro.

**How to apply:** Ao adicionar novos tipos de cache que precisam de filtro por repositório:
1. Garantir que `save_cached_response()` está sendo chamada com o contexto correto
2. Usar `get_repo_name()` para obter o identificador do repositório
3. Filtrar por ambos `repo_name` e `branch_name` nas consultas
4. Caches legacy sem `"repo"` são descartados (comportamento seguro)
