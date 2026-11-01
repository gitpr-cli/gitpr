Leia, nesta ordem: `docs/specs/issue-autoclose/glossario.md`, `docs/specs/issue-autoclose/adrs/` (todos os ADRs), `docs/specs/issue-autoclose/entrevista.md` e `docs/specs/issue-autoclose/00-SPEC.md`.

Implemente a feature descrita na SPEC seguindo estas regras:

1. Comece apenas pela tarefa T0 (investigação). Não escreva código de produção. Entregue o relatório pedido na T0 e aguarde minha confirmação.
2. Depois, execute uma tarefa por vez, na ordem T1 a T9. Ao terminar cada uma: rode os testes, mostre o resultado e faça um commit isolado com mensagem Conventional Commits. Aguarde minha confirmação para seguir.
3. Reaproveite o que já existe (ScmProvider, GitHubProvider, montagem final do corpo do PR, config TUI, i18n, metrics). Não crie mecanismos paralelos.
4. Se o código real divergir da SPEC ou de algum ADR, pare e pergunte antes de decidir.
5. Não faça nada que esteja na seção "Fora de escopo".
6. Toda string visível ao usuário deve passar pelo i18n existente (5 idiomas).
