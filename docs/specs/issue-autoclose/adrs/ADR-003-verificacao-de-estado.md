# ADR-003 — Verificação de estado e política de falha
Status: Aceito

**Decisão.**
- Consultar a issue pelo `ScmProvider` (`get_issue`), que no GitHub usa `GET /repos/{owner}/{repo}/issues/{n}`.
- Perguntar apenas se `state == open` e o objeto **não** for pull request (a rota de issues também devolve PRs).
- Issue fechada, 404 ou PR: limpar o registro em silêncio.
- Erro de rede, timeout, 401/403 ou 5xx: não perguntar, mostrar um aviso de uma linha e seguir o fluxo normal. O registro é mantido.
- Timeout curto e configurável (padrão sugerido: 5 s).
- `--no-close-issue` não faz nenhuma chamada de rede.
