# Survey de fatos — Grill da spec `gitpr release` (changelog/release notes)

> Levantamento automático da skill `grill-with-docs` ao fim da sessão de grill.
> Espec alvo: [20260904_skill_gitpr_release_notes_spec.md](../plans/20260904_skill_gitpr_release_notes_spec.md)

- **Data:** 2026-09-07
- **Branch:** `develop_natan`
- **Sessão:** 3 rodadas de grill (Q1–Q13) + 2 explorações de fatos (Seção 0 da spec)
- **Resultado:** fronteira esgotada, entendimento compartilhado confirmado — todas as decisões aceitas como "recomendado"
- **Artefatos relacionados:** [ADR-002](../plans/ADR-002-gitpr-release-subcommand.md), [ADR-003](../plans/ADR-003-gitpr-release-flat-modules.md), [glossário release notes](../plans/glossary-release-notes.md), spec anotada (seção "Decisões do grill")

## Contexto da tarefa

A spec descreve a feature `gitpr release`: gerar `CHANGELOG.md` e corpo de release notes a partir do histórico de commits entre a última tag e o `HEAD`, com classificação por Conventional Commits, sugestão de bump semântico e resumo por IA (reaproveitando providers Gemini/DeepSeek/Ollama), com publicação opcional na forge. A sessão de grill tinha o objetivo de **afiar a spec**: executar a Seção 0 (fatos obrigatórios do código), entrevistar as decisões de fronteira e registrar o desenho final antes de qualquer implementação.

**Escopo da sessão = documentação.** A implementação fica para uma sessão futura da skill de implementação, que deve ler a spec anotada.

## Decisões das rodadas

| Rodada | Q | Tema | Decisão (recomendado, aceito) |
|---|---|---|---|
| 1 | Q1 | Idioma do artefato | Segue o idioma da interface (`GITPR_LANG`): cabeçalhos localizados via `__()`, resumo IA no mesmo idioma. Corrigir exemplo misto EN/PT da spec. |
| 1 | Q2 | Idempotência do CHANGELOG | Seção da versão já existe → abortar com mensagem clara; regenerar só com confirmação explícita ou `--force`. Nunca duplicar / nunca sobrescrever silenciosamente. |
| 1 | Q3 | Escopo read-only v1 | Não edita arquivos de versão, não cria tag local. `--publish` GitHub: tag auto-criada via API (aponta p/ default branch — documentar). GitLab: exige tag pré-existente. Bitbucket/Azure: sem publicação. |
| 1 | Q4 | Semântica de flags | Default = gera + salva CHANGELOG + prévia em terminal (não publica). `--publish` = publica com `click.confirm`. `--draft` = rascunho **na forge** (GitHub), só com `--publish`. |
| 1 | Q5 | TUI nesta fase | Não. Prévia em terminal + confirmação. TUI editável = fase 2. |
| 1 | Q6 | Sem chave/falha de IA | `ai_summary` default `true`; degrada com warning p/ changelog só-classificado. Nunca bloqueia. |
| 2 | Q7 | Forma do comando | Converter para `click.group` com `invoke_without_command=True`: sem subcomando roteia p/ dispatch legado (~29 flags intactos); `gitpr release` = subcomando (`--draft/--since/--version/--publish/--format`). |
| 2 | Q8 | Local do CHANGELOG | Default `CHANGELOG.md` na **raiz** do repo (artefato público commitável). Override `GITPR_RELEASE_CHANGELOG_PATH`. |
| 2 | Q9 | Fonte da versão | Última tag semver do range (prefixo `v` opcional, preservado). Sem tag semver → sem sugestão; `--version` obrigatório p/ `--publish`. Sem sniff de arquivos de versão. |
| 2 | Q10 | Estrutura de módulos | Flat no estilo da casa (sem camadas DDD): `commit_classifier.py`, `version_bump.py`, `changelog_builder.py` (puros), `release_engine.py` (orquestração). Testes flat. |
| 2 | Q11 | Contrato `create_release` | **Não-abstrato**, default `ScmNotSupportedError` (precedente `request_pull_request_reviewers`/Azure `create_issue`). GitHub: draft honrado. GitLab: sem draft (warning se `draft=True`), tag deve existir. Bitbucket/Azure: herdam raise; fluxo local intacto. |
| 2 | Q12 | Config + JSON | Env vars `GITPR_RELEASE_CHANGELOG_PATH`, `_AI_SUMMARY` (true), `_AUTO_BUMP` (true), `_PUBLISH_DRAFT_BY_DEFAULT` (true) em `DEFAULT_CONFIG`. `--format json` = stdout-only, não toca arquivos nem publica. |
| 3 | Q13 | Extremidade do range | Range sempre `--since` → `HEAD`. Gerar entre duas tags antigas: fora de escopo v1. |

## Relatório de fatos levantados

Executado por 2 agentes de exploração sobre o código (conclusões com referências):

1. **Motor `-ht` não é reutilizável como fonte de commits.** `get_branch_history_text()` ([core.py:1713](../src/core.py#L1713)) retorna texto formatado para prompt de IA — range por `git merge-base origin/<base> HEAD`, linhas cruas `%h | %ad | %an | %s`, sem cap, mais PR descriptions do cache ([cache.py:86](../src/cache.py#L86)). Não é lista estruturada, não é delimitado por tag. A extração estruturada tag→HEAD da feature é código novo.
2. **Não existe parser Conventional Commits** em `src/` nem `scripts/` — ocorrências de `feat:`/`BREAKING` são docstrings/i18n/fixtures; `linter_engine.py` parseia comentários de código; `blame_engine.py` parseia porcelain do blame. `commit_classifier.py` nasce do zero.
3. **Não existe utilidade de leitura de tags** (zero `git describe`/`--tags` em `src/`). A versão do GitPR vive em `__version__` ([updater.py:12](../src/updater.py#L12)) — **0.0.38**, não 0.0.37 (CLAUDE.md defasado); `pyproject.toml` lê via `attr`; releases verificadas via GitHub API/PyPI, sem tags locais.
4. **CLI é um único `click.command`** ([main.py:266](../src/main.py#L266)) com ~29 options e dispatch por `if flag:` sequenciais; sem `click.group`/subcomando; entry point `gitpr = src.main:cli`.
5. **IA:** chamada pública JSON = `call_ai_model(provider, api_key, api_model, prompt, system_instruction, quiet, action)` ([ai_providers.py:101](../src/ai_providers.py#L101)) — retry 3×/2s, temp 0.0, `None` em falha; cache no chamador; map-reduce é loop duplicado por fluxo sobre **diffs** (`split_diff_into_chunks`, [core.py:711](../src/core.py#L711)).
6. **SCM:** ABC `ScmProvider` com 11 métodos abstratos ([base.py:121](../src/infrastructure/scm/base.py#L121)); erros `ScmProviderError`/`ScmNotSupportedError`; precedentes de "não suportado" = método **não-abstrato com default raise** (`request_pull_request_reviewers`, [base.py:206](../src/infrastructure/scm/base.py#L206); Azure `create_issue`, [azure_devops_provider.py:369](../src/infrastructure/scm/azure_devops_provider.py#L369)); **nenhum método de release/tag em nenhum provider**; `factory.resolve_scm_provider(config)` é o único entry point sancionado.
7. **Config é `.env`-only** (`~/.gitpr/.env`; sem YAML/`config.schema.yml`); novos defaults entram em `DEFAULT_CONFIG` ([config.py:16](../src/config.py#L16)); booleans seguem o idioma de conjunto `in ("true","1","yes","y")`; convenção `GITPR_*`.
8. **Saídas:** todo output vai p/ `.gitpr/reports/<folder>/` via `resolve_output_path` ([core.py:423](../src/core.py#L423)) — changelog na raiz é exceção deliberada (Q8); arquivos sempre truncate-write UTF-8; prepend existe só no hook ([main.py:1321](../src/main.py#L1321)); confirmação interativa = `click.confirm` (sem helper de confirm-antes-de-publicar).
9. **Repo raiz** tem `CHANGELOG.md`; **não** tem `CONTEXT.md` nem `docs/adr/` (convenção da casa: ADRs e glossários em `docs/plans/`, ex.: `ADR-001-scm-abstraction.md`, `glossary-scm-multiforge.md`); `docs/survey/` criado nesta sessão.
10. **Versões de templates/scripts:** `__lang_version__` v0.0.21 e `__scripts_version__` v0.0.3 ([updater.py:13-16](../src/updater.py#L13)) governam re-download OTA (i18n/hooks) — a feature não mexe nesses mecanismos.

## Fechamento

Fronteira esgotada após Q13. Nenhuma decisão ficou implícita. Próximo passo (fora desta sessão): implementação pela skill de leitura da spec anotada, seguindo ADR-002/ADR-003 e o glossário.
