# ADR-004 — Inserção na descrição e idempotência
Status: Aceito

**Decisão.**
- Texto: `close #N`, em linha própria, separada por uma linha em branco do conteúdo anterior.
- Posição: imediatamente antes do badge, depois de qualquer outra seção (por exemplo, "Explain my PR"). Sem badge, vai ao fim do corpo.
- Idempotência: não inserir se o corpo já tiver `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` ou `resolved` seguido de `#N` (opcionalmente `owner/repo#N`), sem diferenciar maiúsculas e com limite de palavra (`#12` não casa com `#123`).
- A inserção ocorre no ponto único de montagem final do corpo do PR, nunca em vários lugares.

**Revisão T0 (2026-11-01). Identificado no código real; acordado com o usuário.**

- O ponto físico de inserção é o `pr_desc_body`, logo após a seção "Explain my PR"
  (`src/main.py:1807-1813`), **antes** da escrita do `.md` local. O badge continua sendo
  anexado depois, em `attach_pr_badge` (`src/branding/badge_builder.py:121`), de modo que a
  linha fica imediatamente antes dele. Como consequência, o `.md` local e o `--no-publish`
  também recebem a linha — o que não aconteceria se ela fosse inserida apenas no badge.
