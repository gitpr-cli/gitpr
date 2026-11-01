# ADR-002 — Registro único por repositório, sem chave de usuário
Status: Aceito (substitui a exigência original de subdividir por usuário)

**Contexto.** O pedido inicial previa subdivisão por usuário. Na entrevista (Q2), ficou decidido que, como o arquivo não é versionado, não há compartilhamento entre pessoas.

**Decisão.** Um único `last_issue` por arquivo. Não há consulta a `/user` nem uso de `git config user.email` para este fim.

**Consequências.** Implementação mais simples. Se um dia o arquivo for compartilhado, o `schema_version` permite migrar para uma estrutura `users.<chave>`.
