---
name: coauthor-trailer-injecao-pos-cache
description: Trailer Co-Authored-By é anexado no consumo (nunca no prompt nem no cache MD5) e só entra na TUI no momento do commit
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-16_coauthor_trailer.md
  date: 2026-08-16
  branch: develop_natan
---

Toda mensagem de commit gerada pelo GitPR carrega
`Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>`. O ponto de injeção é uma decisão
de arquitetura deliberada, não detalhe de implementação:

- **Nunca via prompt de IA** e **nunca dentro do cache MD5**. `append_coauthor_trailer()`
  (`src/core.py`) roda *depois* da leitura do cache, sobre a resposta já obtida.
- **Idempotente:** não duplica trailer existente e preserva linhas `Co-Authored-By:` de
  terceiros.
- **Opt-out `GITPR_COAUTHOR=false`** existe via `coauthor_enabled()` (`src/config.py`),
  mas é **read-only**: nunca é escrito automaticamente no `.env`, não está no
  `DEFAULT_CONFIG` e é intencionalmente **indocumentado** nos READMEs e docs de usuário.

O momento da injeção **difere por fluxo** (corrigido em 2026-08-18):

| Fluxo | Quando o trailer entra |
|---|---|
| `gitpr -c`, modo `--hook`, `--no-edit`, tool MCP `generate_commit_message` | na geração |
| TUI do PR Publisher (`pr_publish_app.py`) | só na execução do commit, após confirmação |

**Why:** Se o trailer entrasse no prompt ou no cache, todas as respostas em cache
existentes seriam invalidadas e o texto assinado viraria entrada de IA. Na TUI, mostrá-lo
na tela de edição poluía a revisão do usuário; além disso `_pending_commit_msg` precisa
ficar **puro** porque alimenta o fallback do título do PR e o bloco "Recommended Commit
Message" da descrição salva/publicada.

**How to apply:**
- Ao adicionar um novo fluxo que produza mensagem de commit, chame
  `append_coauthor_trailer()` no ponto de consumo — nunca antes do cache.
- Se o fluxo tem tela de revisão, injete só imediatamente antes de `execute_git_commit()`
  e sobre uma variável local, mantendo o estado da tela limpo.
- Cuidado com mensagem vazia: nenhum caminho deve criar um commit que seja só o trailer.
- Consumidores externos do tool MCP `generate_commit_message` fazendo comparação exata
  precisam contar com o trailer na saída.
