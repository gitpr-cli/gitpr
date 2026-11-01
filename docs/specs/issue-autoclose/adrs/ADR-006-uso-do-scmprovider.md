# ADR-006 — Uso do ScmProvider e escopo GitHub
Status: Aceito

**Decisão.**
- A feature só está ativa quando o provider do repositório é GitHub.
- Novos métodos no `ScmProvider`: `get_issue(repo, number)` e `get_default_branch(repo)`, se ainda não existirem. Providers sem suporte levantam `NotImplementedError`, e a feature fica desligada para eles.
- A palavra de fechamento fica atrás de um método do provider (`closing_line(number)`), com GitHub retornando `close #N`. GitLab e Azure DevOps entram no futuro sem mexer no fluxo.
- Nenhum código novo chama `requests` diretamente fora do provider.
