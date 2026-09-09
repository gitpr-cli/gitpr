# Glossário — Release Notes / Changelog (`gitpr release`)

> Vocabulário canônico da feature `gitpr release`.
> Spec: [20260904_skill_gitpr_release_notes_spec.md](20260904_skill_gitpr_release_notes_spec.md) (anotada em 2026-09-07).
> Decisões de implementação: [ADR-002](ADR-002-gitpr-release-subcommand.md), [ADR-003](ADR-003-gitpr-release-flat-modules.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **changelog** | Artefato versionado no repositório (`CHANGELOG.md` na raiz por padrão) com uma **seção de versão** por release. Público e commitável — diferente das saídas de rascunho em `.gitpr/reports/`. |
| **seção de versão** | Bloco `## [x.y.z] - data` + categorias + resumo no changelog. É a unidade de idempotência: se a versão já tem seção, o comando **aborta** (regenerar só com confirmação ou `--force`) — nunca duplica, nunca sobrescreve silenciosamente. |
| **release notes** | Corpo de texto da release publicada na forge. Conteúdo = a mesma seção do changelog (sem o cabeçalho `## [x.y.z]`, duplicado pelo título da release). |
| **release draft** (forge-draft) | Rascunho da release **na forge** (GitHub Releases). Não confundir com "não publicar localmente": o modo local é o **default** do comando (gera + salva + prévia) e não tem nome próprio. GitLab não tem rascunho nativo — `draft=True` vira warning e publica direto. |
| **range since..HEAD** | Intervalo de commits da release: da tag informada por `--since` (default: última tag) até o `HEAD`. Extremidade final fixa em `HEAD` nesta fase (Q13); "entre duas tags antigas" está fora de escopo. |
| **versão alvo (target version)** | Versão da nova release, vinda de `--version` ou da **sugestão de bump**. É a única fonte da tag publicada. |
| **versão sugerida (suggested bump)** | Leitura **read-only**: o comando nunca edita arquivos de versão nem cria tags locais (Q3). Sem tag semver anterior → nenhuma sugestão; `--version` é obrigatório para `--publish`. |
| **primeira release** | Range sem tag anterior: começa no primeiro commit do repositório (`previous_tag = None`). Sem base semver, não há bump sugerido. |
| **bump semântico** | Regra MAJOR/MINOR/PATCH sobre os commits classificados: qualquer `breaking` → MAJOR; sem breaking com ≥1 feature → MINOR; só fixes/outros → PATCH. `GITPR_RELEASE_AUTO_BUMP=false` exige `--version` explícito. |
| **commits classificados** | Commits do range parseados por Conventional Commits em `ClassifiedCommit` (tipo/escopo/`breaking`/`pr_number`). Fora do padrão → categoria `OTHER` + warning (nunca falha). |
| **resumo executivo** | Parágrafo gerado por IA no topo da seção (idioma da interface). `GITPR_RELEASE_AI_SUMMARY=false`, sem chave ou falha → degrada com warning para lista classificada pura; nunca bloqueia o comando. |
| **contribuidores** | Nomes de autor únicos e normalizados do range, listados no rodapé da seção. |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Default | Significado |
|---|---|---|
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Caminho do changelog (na raiz do repo por padrão; relativo ao repo ou absoluto). |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Gera o resumo executivo por IA (degradação graciosa quando indisponível). |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Sugere a versão por bump semântico; `false` = exigir `--version`. |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | `--publish` no GitHub cria a release como draft. |

Seguem a convenção do projeto: dotenv plano + entrada em `DEFAULT_CONFIG`
(config.py), sem YAML de config.

## Notas de fidelidade de forge

- **GitHub:** `POST /repos/{owner}/{repo}/releases`. `draft` honrado. Se a tag
  não existir, a **API a cria apontando para a branch default** — não para o
  `HEAD` local; comportamento documentado no help.
- **GitLab:** `POST /projects/{id}/releases`. A **tag deve já existir** na forge
  (criada pelo usuário); sem conceito de draft — `draft=True` vira warning.
- **Bitbucket Cloud / Azure DevOps:** sem Release nativo na API — `create_release`
  herda o default `ScmNotSupportedError`; o fluxo local (changelog) continua.
