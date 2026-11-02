# ADR-005 — Momento da pergunta e modos de execução
Status: Aceito (com a premissa P1)

**Decisão.**
- A pergunta é feita no início do fluxo `gitpr`, antes da TUI de stage e antes da geração da descrição. A resposta fica em `PrContext`.
- Pergunta: "Issue #N – título está aberta. Adicionar `close #N` à descrição do PR? [S/n]". Enter responde sim.
- Se a branch de destino configurada for diferente da branch padrão do repositório, a pergunta traz o aviso: o GitHub só fecha a issue quando o merge é feito na branch padrão.
- Sem TTY (CI, script, MCP): nunca pergunta e não insere nada, a menos que `--close-issue` esteja presente.
- `--close-issue`: insere sem perguntar, mas ainda verifica se a issue está aberta.
- `--no-close-issue`: ignora a feature nesta execução.
- Chave de configuração `issue_autoclose.enabled` (padrão `true`), com opção na TUI "config".

**Revisão T0 (2026-11-01). Identificado no código real; acordado com o usuário.**

- A pergunta continua antes da TUI de stage, mas provider e branch-alvo são resolvidos
  **de forma lazy**: só quando existe registro para o repositório atual, a feature está
  ativa e o provider é GitHub. Sem registro, o fluxo não faz nenhuma chamada nova — a
  não-regressão do teste 8 fica preservada. A resolução antecipada é reutilizada pelo
  restante do fluxo.
- A chave de configuração é **`GITPR_ISSUE_AUTOCLOSE`** (booleana, padrão `true`), no padrão
  `GITPR_*` plano do schema existente, com o timeout em `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`
  (padrão `5`). A TUI "config" já sabe renderizar opções `KIND_BOOL`.
