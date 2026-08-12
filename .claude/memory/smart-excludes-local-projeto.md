---
name: smart-excludes-local-projeto
description: Arquivo local .gitpr/conf/gitpr.smart-excludes.json mergeado com lista global no runtime
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-10_smart_excludes_local_projeto.md
  date: 2026-08-10
  branch: develop_natan
---

Além da lista global de Smart Excludes (controlada remotamente via template JSON),
o GitPR agora suporta um arquivo local por projeto em
`.gitpr/conf/gitpr.smart-excludes.json`. No runtime, `_load_smart_excludes()` em
`src/core.py` carrega ambas as listas e faz merge (união com deduplicação),
permitindo que exclusões específicas do projeto convivam com as globais sem
conflito.

O arquivo local é criado automaticamente por `_seed_local_smart_excludes()` na
primeira execução (idempotente — nunca sobrescreve um arquivo existente). Três
variáveis de ambiente controlam o comportamento:

| Variável | Efeito |
|---|---|
| `GITPR_SKIP_SMART_EXCLUDES` | `"1"`/`"true"` desabilita totalmente o filtro |
| `GITPR_SMART_EXCLUDES_GLOBAL` | Caminho alternativo para o arquivo global |
| `GITPR_SMART_EXCLUDES_LOCAL` | Caminho alternativo para o arquivo local |

A função `_load_docs_smart_excludes()` também respeita `GITPR_SKIP_SMART_EXCLUDES`.

**Why:** Antes, a lista de exclusões era puramente global (template remoto no GitHub).
Projetos que precisavam de exclusões adicionais tinham que modificar o arquivo global
em `~/.gitpr/conf/`, que era sobrescrito a cada atualização de versão. O arquivo
local resolve isso: exclusões do projeto persistem independentemente de atualizações
globais.

**How to apply:**
1. Exclusões específicas do projeto vão em `.gitpr/conf/gitpr.smart-excludes.json`
2. Exclusões genéricas (cross-project) continuam no template remoto global
3. `_seed_local_smart_excludes()` deve ser chamado no download de templates (`--skill`)
4. O merge é union+dedup — não há remoção de exclusões globais via arquivo local
5. Para debug, `GITPR_SKIP_SMART_EXCLUDES=1` desabilita tudo sem modificar arquivos

Ver também: [[smart-excludes-remote-control]], [[version-marker-pattern]]
