# ADR-004 — Inserção na descrição e idempotência
Status: Aceito

**Decisão.**
- Texto: `close #N`, em linha própria, separada por uma linha em branco do conteúdo anterior.
- Posição: imediatamente antes do badge, depois de qualquer outra seção (por exemplo, "Explain my PR"). Sem badge, vai ao fim do corpo.
- Idempotência: não inserir se o corpo já tiver `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` ou `resolved` seguido de `#N` (opcionalmente `owner/repo#N`), sem diferenciar maiúsculas e com limite de palavra (`#12` não casa com `#123`).
- A inserção ocorre no ponto único de montagem final do corpo do PR, nunca em vários lugares.
