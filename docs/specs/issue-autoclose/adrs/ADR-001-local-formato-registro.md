# ADR-001 — Local, formato e versionamento do registro
Status: Aceito

**Contexto.** O usuário definiu `.gitpr/conf/github.yml` para guardar a última issue criada.

**Decisão.**
- Arquivo `.gitpr/conf/github.yml`, em YAML, com `schema_version: 1`.
- Conteúdo: `last_issue` com `repo`, `number`, `title`, `url`, `created_at` (ISO 8601) e `branch`.
- O arquivo **não é versionado**. Na primeira gravação, se `git check-ignore` indicar que o caminho não está ignorado, o gitpr acrescenta `.gitpr/conf/` ao `.gitignore` e informa em uma linha. (Ver Revisão T0 abaixo: o caminho acrescentado é apenas `.gitpr/conf/github.yml`.)
- Escrita atômica (arquivo temporário e `os.replace`).
- Arquivo corrompido ou ilegível: avisar, ignorar e sobrescrever na próxima gravação.
- Nenhum token ou segredo é gravado.

**Alternativas.** Versionar o arquivo (suja o working tree, expõe dados e gera conflitos); diretório global do usuário (perde a ligação com o repositório).

**Consequências.** O registro vale só para a máquina local. O nome `github.yml` deixa espaço para `gitlab.yml` etc. no futuro.

**Revisão T0 (2026-11-01). Identificado no código real; acordado com o usuário.**

- O `.gitignore` recebe **`.gitpr/conf/github.yml`**, não o diretório `.gitpr/conf/` inteiro: o
  `.gitpr/conf/gitpr.config.yml` desse diretório é versionado de propósito
  ([ADR-015](../../../plans/ADR-015-project-local-pr-base.md)). O restante da decisão permanece.
