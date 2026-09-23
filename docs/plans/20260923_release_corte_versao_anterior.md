# gitpr release — corte por versão anterior, links e datas

## Context

`gitpr release` está listando, em toda versão nova, **todos** os commits de todas as versões
anteriores. A versão 1.3.0 saiu com 124 bullets; a 1.2.0 tinha 115, e **115 desses repetem** na
1.3.0. O `### Resumo` também arrasta conteúdo velho ("preparação da versão 1.1.0").

**A causa raiz não é a IA.** As 7 categorias são 100% determinísticas
([commit_classifier.py](src/commit_classifier.py) + [changelog_builder.py](src/changelog_builder.py));
a IA escreve apenas o `### Resumo`. A repetição vem inteiramente do range do `git log`:

[release_engine.py:102](src/release_engine.py#L102) usa `git describe --tags --abbrev=0`, que neste
repositório resolve para **`v0.0.8`** — só 8 tags (v0.0.1…v0.0.8) são ancestrais de
`develop_natan`. As tags `v1.0.0`/`v1.1.0`/`v1.2.0` vivem apenas em `origin/main`.

| Range                                              | Commits |
| -------------------------------------------------- | ------- |
| `v0.0.8..HEAD` (atual)                             | **124** |
| `v1.2.0..HEAD`                                     | 9       |
| `6138cf1..HEAD` (hash mais recente do bloco 1.3.0) | 0       |

115 (correto na 1.2.0) + 9 (novos) = 124 = exatamente o que a 1.3.0 repetiu.

Resultado esperado: cada release lista **apenas** o delta real, com link do commit, link do PR
(quando houver), data e contribuidores linkados ao perfil.

## Decisões (fechadas com o usuário)

| #   | Decisão                                                                                                           |
| --- | ----------------------------------------------------------------------------------------------------------------- |
| 1   | Fronteira = bloco da versão anterior no `CHANGELOG.md`                                                            |
| 2   | Âncora do range = **hash mais recente dos bullets do bloco anterior**, com a **tag daquela versão como fallback** |
| 3   | Filtro anti-duplicata contra **todos** os blocos anteriores do CHANGELOG                                          |
| 4   | Login do contribuidor via `email_to_handle()`, com cache                                                          |
| 5   | URLs web em **módulo isolado novo**; nenhum provider existente é alterado                                         |
| 6   | Bullet = formato A (data no fim) + número do PR com link                                                          |
| 7   | Sem âncora derivável → degrada para `git describe` **com aviso visível**                                          |
| 8   | Regenerar a seção 1.3.0 já poluída                                                                                |

## Formato final do bullet

```
- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}
```

- `— {scope}` só quando o Conventional Commit tiver escopo (posição atual, inalterada)
- `· [#{n}]({pr_url})` só quando `pr_number` existir (commits de squash-merge)
- `· {YYYY-MM-DD}` sempre — data do autor (`%aI`), já disponível em `ClassifiedCommit.date`
- Sem contexto de link (remote desconhecido, forge sem padrão): a hash fica **sem link** mas a data permanece

Exemplos reais da seção 1.3.0:

```
- add Semgrep, Gitleaks and Bandit SAST bridges ([a799664](…/commit/a799664)) — linter · 2026-09-22
- resolve reviewer identities to GitHub logins before attach ([eb55400](…/commit/eb55400)) · 2026-09-18
```

Rodapé, com o login resolvido; quem não resolver continua com o nome puro:

```
**Contribuidores:** [@natanfiuza](https://github.com/natanfiuza)
```

## Mudanças

### 1. `src/infrastructure/scm/web_links.py` (novo, ~70 linhas)

Tabela `provider → template` de URL HTML + derivação do host a partir do remote. Funções puras,
sem I/O: `repo_web_base(remote_url)`, `commit_url(provider, base, sha)`,
`pull_request_url(provider, base, number)`, `user_url(provider, base, login)`.

- `repo_web_base`: normaliza `git@host:path.git` e `ssh://…`/`https://…` → `https://host/path`
- Padrões: github `{base}/commit/{sha}` · gitlab `{base}/-/commit/{sha}` · bitbucket `{base}/commits/{sha}` · azure_devops `{base}/commit/{sha}`; PRs respectivamente `/pull/`, `/-/merge_requests/`, `/pull-requests/`, `/pullrequest/`
- `user_url`: `{host}/{login}` para github/gitlab/bitbucket; **`None`** para Azure (não há perfil simples) e para provider desconhecido → degrada para nome puro

### 2. `src/changelog_builder.py` — renderização pura

- Novo contrato `LinkContext(provider, base, logins)` — `logins` mapeia **nome de exibição → login**
- `_commit_line(commit, links=None)` passa a montar a linha do formato final acima
- `build_release_section(..., links=None)` — parâmetro novo com default `None`, então as chamadas atuais continuam válidas; renderiza o rodapé usando `links.logins`
- `normalize_contributors()` e `ReleaseNotesResult.contributors` **não mudam** (compatibilidade do `--format json`)
- O módulo continua **sem I/O**: recebe o `LinkContext` pronto

### 3. `src/release_engine.py` — corte, filtro e contexto de links

Novas funções privadas (mantendo o estilo flat do módulo, ADR-003):

- `_read_changelog(path)` → conteúdo ou `None`
- `_version_blocks(content)` → `[(versão, corpo)]` na ordem do arquivo, via `^##\s*\[([^\]]+)\]`; descarta `Unreleased` e o que não passar em `parse_semver_tag` (reuso de [version_bump.py:25](src/version_bump.py#L25))
- `_previous_block(content, target_version)` → primeiro bloco semver que **não seja** o `target_version` (necessário para `--force`, que regenera um bloco já existente)
- `_hashes_in(text)` → `[\(\[]([0-9a-f]{7,40})[\)\]]`, truncado em 7; cobre o formato antigo `(a799664)` e o novo `([a799664](url))`
- `_range_origin(root, since_tag, target_version, changelog_path, warnings)` — ordem de resolução:
  1. `--since` explícito (vence sempre)
  2. hash mais recente do bloco anterior — resolvido num único `git log --no-walk` com `%aI`, pega a maior data
  3. tag da versão daquele bloco (`1.2.0` ou `v1.2.0`)
  4. `_latest_tag()` + **aviso** no console e em `result.warnings`
  - Toda âncora é validada com `git merge-base --is-ancestor <ref> HEAD`; se falhar, cai para o próximo passo
- `_drop_released(commits, content, target_version)` — remove commits cuja `short_hash` apareça em qualquer bloco **exceto** o do `target_version`; roda logo após `classify_commits()`
- `_resolve_contributor_logins(commits, quiet)` — best-effort, **nunca levanta**: cache em `~/.gitpr/cache/contributors.json` (`email → login`), resolve os ausentes com `getattr(provider, "email_to_handle", None)` (mesmo padrão de [reviewer_resolution.py:63](src/reviewer_resolution.py#L63)), provider vindo de `resolve_scm_provider(get_scm_settings())`. **Só acertos entram no cache** — falha transitória ou rate limit não envenena o arquivo. Sem token ⇒ apenas nomes puros
- `_build_link_context(root, commits, quiet)` — `get_origin_remote_url()` ([core.py:708](src/core.py#L708)) + `detect_provider_from_remote()` → `LinkContext`
- `generate_release_notes()` ganha `changelog_path="CHANGELOG.md"` (resolvido contra o repo root) e usa o bloco anterior como **baseline do bump semver**, em vez de `_latest_semver_tag()`. Isso corrige de quebra a sugestão de versão, que hoje parte de `v0.0.8` e sugeriria `v0.0.9` em vez de `1.4.0`
- `ReleaseNotesResult` ganha `previous_version: str | None` (versão lida do CHANGELOG). O campo `previous_tag` é **mantido** para não quebrar o `--format json` e passa a carregar a âncora resolvida (tag ou sha) — a doc explica a nova semântica

### 4. `src/main.py` — fiação mínima

Repassar `changelog_path=settings["changelog_path"]` para `generate_release_notes()` na chamada de
[main.py:1716](src/main.py#L1716). Nada mais muda: `upsert_changelog` e o artefato já consomem
`result.markdown`, que passa a sair com links.

### 5. Testes

| Arquivo                           | Mudança                                                                                                                                                                                                                    |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tests/test_web_links.py`         | **novo** — base a partir de ssh/https/scp, URLs por provider, Azure sem perfil de usuário, provider desconhecido → `None`                                                                                                  |
| `tests/test_changelog_builder.py` | atualizar as asserções de bullet (ganham data; ver [test_changelog_builder.py:66-136](tests/test_changelog_builder.py#L66-L136)) + novos casos: link do commit, link do PR, rodapé com login, degradação sem `LinkContext` |
| `tests/test_release_engine.py`    | atualizar os testes que fixam `v1.2.3..HEAD`; novos: âncora pelo hash do bloco, fallback para a tag, aviso de degradação, filtro anti-duplicata, baseline do bump vindo do CHANGELOG                                       |

### 6. Documentação e artefatos

- `docs/release-notes.md` + as 4 traduções (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`) — §2 (range default e cadeia de fallback), §3.2 (anatomia do bullet com link/PR/data e rodapé linkado), menção a `~/.gitpr/cache/contributors.json`
- `CLAUDE.md` — atualizar a linha de fluxo do `release` (corte pelo CHANGELOG) e a seção de skills
- Índice do `README.md`, se ele listar a doc de release
- `docs/survey/20260923_release_dedup_links_surveyfacts.md` — levantamento da sessão de grill (contexto, decisões das 3 rodadas, fatos apurados)
- `docs/claude-code/reports/develop_natan/2026-09-23_release_dedup_links.md` — relatório de conclusão obrigatório
- **Nenhuma chave de i18n nova**: o formato não introduz texto traduzível; `**Contribuidores:**` reaproveita a chave `Contributors` existente

## Fora de escopo

- A regra 7 não commitada em [.gitpr/skill/.gitpr.release.md](.gitpr/skill/.gitpr.release.md) ("Create the summary and all items in English") é **inerte** — a IA não gera os itens. Fica como está.
- Idioma misto dos cabeçalhos no `CHANGELOG.md` (seguem `GITPR_LANG` em tempo de render) — comportamento atual, não faz parte deste pedido.
- Metadados de PR (`author.login` via API de commits) como alternativa ao `email_to_handle`.

## Ordem de execução e verificação

1. `web_links.py` + `test_web_links.py` → `python -m pytest tests/test_web_links.py -v`
2. Renderização em `changelog_builder.py` + atualização de `test_changelog_builder.py`
3. Corte/filtro/links em `release_engine.py` + atualização de `test_release_engine.py`
4. Fiação em `main.py`
5. Suíte completa: `python -m pytest tests/ -v` (a suíte é a rede de segurança das asserções de layout)
6. **Prova no repositório real**: `gitpr release --version 1.3.0 --force`
   - a seção 1.3.0 deve cair de **124 → ~9 bullets**, sem nenhum commit da 1.2.0
   - cada bullet com `([hash](link))`, PR quando houver, e `· YYYY-MM-DD`
   - rodapé `[@natanfiuza](https://github.com/natanfiuza)`
   - o `### Resumo` deve parar de citar a versão 1.1.0
7. Confirmar que rodar de novo **sem** `--force` aborta (idempotência preservada) e que `--format json` continua stdout puro
8. Verificar os dois artefatos: `CHANGELOG.md` e `.gitpr/reports/release/*_RELEASE.md`
