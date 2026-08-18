# Plano: Atualizar docs/ARCHITECTURE.md + versões nos idiomas suportados

## Contexto

- `docs/ARCHITECTURE.md` foi atualizado pela última vez em 2026-08-16 (commit `a755237`) e seu conteúdo está em grande parte atualizado, **mas está escrito em português (sabor PT-PT)** — violando a convenção do próprio projeto (declarada no próprio arquivo, linha 198, e na memória `docs-multilingue-convencao`): **o `.md` base é o inglês canônico**, e as localizações usam sufixos `<nome>.<lang>.md`.
- Pedido do usuário: atualizar `docs/ARCHITECTURE.md` e criar as versões nos idiomas suportados (EN canônico + PT-BR, PT-PT, ES, FR).
- Este plano é salvo em `docs/plans/` conforme a convenção `YYYY-MM-DD_<taskname>.md`.

## Premissas (baseadas nas convenções do repo, verificadas)

1. **O arquivo base passa a ser inglês.** Verificado: os arquivos base `blame-arqueologo.md`, `code-review-ia.md`, `pull-request-publication.md`, `mcp-integration.md` têm conteúdo em EN; `get_doc_url()` trata o nome sem sufixo como EN. O texto atual em PT vira o ponto de partida do `ARCHITECTURE.pt_pt.md`.
2. **Idiomas:** `pt_br`, `pt_pt`, `es_es`, `fr_fr` (4 localizações; códigos de sufixo conforme convenção).
3. **Links entre docs mantêm nomes base** em todas as versões (verificado: docs traduzidos como `metricas-telemetria.es_es.md` apontam para `mcp-integration.md`, não para nomes localizados).
4. **Regras de tradução:** blocos de código, comandos, flags, caminhos, variáveis de ambiente e âncoras de seção NUNCA são traduzidos; apenas a prosa é localizada. Estrutura de títulos idêntica nos 5 arquivos.

## Delta de conteúdo a aplicar (achados da exploração)

Apenas **1 commit** desde a última atualização do doc altera comportamento descrito, além da completude da lista:

1. **Coauthor trailer** (`4bf8e48` feat + `d65c175` refactor, 2026-08-18): commits carregam o trailer `Co-Authored-By` anexado no momento da execução do commit; a tela de edição da TUI do publicador de PR nunca o exibe. → Adicionar 1 frase ao bullet do recurso de commit (seção "Auto-Commit") e/ou ao item 14 do ecossistema TUI.
2. **Completude da lista de docs** (seção "Documentação Detalhada", hoje com 14 entradas): adicionar os 18 docs base faltantes — docs de funcionalidade: `auto-update`, `code-review-ia`, `commit-message-ia`, `git-hooks-locais`, `git-status`, `github-ci-linter`, `gitpr-issue-option`, `guia-regex-gitpr`, `mcp-annotations`, `mcp-prompts`, `otimizacao-de-tokens`, `pr-descricao-padrao`, `providers-ia`, `skill-template`, `untracked-files`; how-tos apenas em EN: `github-issue-prompt-com-gh`, `como_reverter_commit_git_localmente`, `testar_sem_usar_pypi`. (Existência de cada alvo de link verificada na execução.)
3. **Nenhuma outra mudança necessária:** as flags de `src/main.py` batem com a lista de recursos do doc; contagens MCP confirmadas (12 tools / 7 prompts); a árvore de estrutura do projeto bate exatamente com `src/`; o diff não commitado de `src/updater.py` é apenas bump de versão (0.0.36→0.0.37) — o ARCHITECTURE.md não cita números de versão, então nada muda.

## Arquivos

| Arquivo | Ação | Idioma |
| --- | --- | --- |
| `docs/ARCHITECTURE.md` | Reescrita | EN (canônico, com o delta acima) |
| `docs/ARCHITECTURE.pt_br.md` | Novo | PT-BR (tradução do EN) |
| `docs/ARCHITECTURE.pt_pt.md` | Novo | PT-PT (adaptação do texto PT atual + delta) |
| `docs/ARCHITECTURE.es_es.md` | Novo | ES (tradução do EN) |
| `docs/ARCHITECTURE.fr_fr.md` | Novo | FR (tradução do EN) |
| `docs/plans/2026-08-18_architecture_multilang.md` | Novo | Cópia deste plano |
| `docs/claude-code/reports/develop_natan/2026-08-18_architecture_multilang.md` | Novo | Relatório de conclusão (obrigatório por CLAUDE.md) |

## Passos

1. Salvar cópia deste plano em `docs/plans/2026-08-18_architecture_multilang.md`.
2. Reescrever `docs/ARCHITECTURE.md` em EN aplicando o delta (nota do coauthor trailer + lista completa de docs).
3. Criar as 4 versões localizadas (primeiro pt_pt, reusando o texto PT atual; depois pt_br, es_es, fr_fr a partir do canônico EN).
4. Verificar estrutura/links.
5. Escrever o relatório de conclusão.

## Verificação

- Os 5 arquivos compartilham estrutura de títulos idêntica (diff dos TOCs extraídos).
- Todo link markdown da "Documentação Detalhada" resolve para um arquivo existente em `docs/`.
- Conteúdo EN conferido contra as flags de `src/main.py` e contagens de `src/mcp_server.py` (já feito na exploração — conteúdo permanece alinhado).
- Conferência pontual das traduções: código/comandos/flags intactos em relação à versão EN.

## Fora de escopo (anotado para o relatório)

- `src/main.py` `HELP_MAP` tem 2 referências de doc quebradas (`chat-interativo.md` → arquivo real `understanding_chat_functionality.md`; `metricas_analytics_dashboard.md` → `metricas-telemetria.md`). Bug de código, não faz parte desta tarefa de docs — sugerido como próximo passo.
