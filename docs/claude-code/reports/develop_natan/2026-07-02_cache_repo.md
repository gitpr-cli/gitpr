## Relatório de Conclusão — Nome do Repositório no Cache

### O que foi feito
- Adicionado campo `"repo"` (owner/repo) em todos os arquivos JSON de cache gerados pelo GitPR
- Alterada a função `get_cached_pr_descriptions()` para filtrar por `repo_name` E `branch_name`
- Criada função `get_repo_name()` em `core.py` que extrai `owner/repo` do `git remote -v`
- Atualizada `get_branch_history_text()` para usar repo + branch no contexto do `--history`

### Arquivos alterados

| Arquivo | Tipo de mudança | Descrição |
|---|---|---|
| `src/core.py` | feat | Adicionado `import re`; nova função `get_repo_name()`; `get_branch_history_text()` usa repo+branch |
| `src/cache.py` | feat | `save_cached_response()` grava campo `"repo"`; `get_cached_pr_descriptions(repo_name, branch_name)` filtra por ambos |

### Impacto
- **Funcionalidade:** O `--history` agora filtra o cache por repositório E branch, evitando misturar caches de projetos diferentes que tenham branches com o mesmo nome (ex: duas branches `feature/login` em repositórios diferentes)
- **Performance:** Sem impacto — a consulta continua sendo leitura sequencial da pasta `pr_desc/`
- **Compatibilidade:** Assinatura de `get_cached_pr_descriptions()` mudou de 1 para 2 parâmetros. Único call site (`core.py:375`) foi atualizado. Caches antigos sem o campo `"repo"` serão ignorados pelo novo filtro (comportamento seguro)

### Próximos passos (se aplicável)
- Considerar migração automática de caches antigos (adicionar campo `"repo"` a arquivos JSON existentes)
