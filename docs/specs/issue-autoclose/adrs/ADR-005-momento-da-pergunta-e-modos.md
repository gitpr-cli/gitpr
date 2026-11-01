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
