# SPEC — GitPR Automated Changelog / Release Notes (`gitpr release`)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: gerar changelog e release notes automaticamente a partir do histórico de commits/branches entre tags, reaproveitando o motor de issues já existente (histórico de branch, flag `-ht`) e a infraestrutura de IA (providers Gemini/DeepSeek/Ollama) para sumarização.

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler o módulo responsável pela flag `-ht` (histórico de branch, hoje usado no motor de issues) e extrair: (a) assinatura exata da função, (b) como ele delimita o intervalo de commits (por branch, por range de commits, por data), (c) formato de saída (lista de commits crus, ou já parseados por tipo Conventional Commits).
2. Confirmar se o projeto já parseia Conventional Commits (`feat:`, `fix:`, `chore:`, `BREAKING CHANGE:` etc.) em algum ponto do pipeline de commit/hooks — se sim, reaproveitar esse parser em vez de reimplementar.
3. Verificar como o projeto identifica tags Git hoje (se há alguma função utilitária de leitura de tags/versões, ou se precisa ser criada do zero nesta feature).
4. Confirmar a interface real de `ai_providers.py` (Strategy Pattern) para reaproveitar o mesmo mecanismo de chamada de IA usado em geração de PR description — não criar um segundo caminho de acesso a provider de IA.
5. Verificar se `github_api.py`/`ScmProvider` (se a abstração multi-forge já existir) suporta criação de "Release" nativa da forge (GitHub Releases, GitLab Releases) — se sim, mapear o endpoint; se não, esta feature deve gerar apenas o arquivo `CHANGELOG.md` e o texto de release, sem publicar automaticamente.
6. Confirmar o formato de versionamento hoje usado no projeto (`pyproject.toml`, `setup.py`, arquivo `VERSION`, ou tags Git) para saber de onde ler/escrever a versão corrente.

Não prosseguir com a implementação sem completar os passos 1–4.

## 1. Escopo da feature

- **Objetivo:** gerar automaticamente (a) um `CHANGELOG.md` atualizado e (b) o corpo de texto de uma release (draft), a partir de todos os commits/PRs mergeados entre a última tag e o `HEAD` (ou entre duas tags informadas).
- **Comando novo:** `gitpr release` com subopções:
  - `gitpr release --draft` — gera o texto e mostra na TUI/terminal sem publicar nada.
  - `gitpr release --since <tag>` — define o ponto de partida manualmente (default: última tag encontrada).
  - `gitpr release --version <x.y.z>` — versão alvo da release (default: sugestão automática via bump semântico, ver seção 4).
  - `gitpr release --publish` — além de gerar, publica a release na forge (GitHub Release / GitLab Release) via `ScmProvider`/`github_api.py`.
  - `gitpr release --format {markdown|json}` — saída para consumo humano ou por CI.
- **Fora de escopo nesta fase:** publicação em múltiplos formatos de distribuição (npm, PyPI changelog automático), assinatura/verificação de release (GPG), notificação automática em Slack/Discord da release (isso é Tier 2, feature separada já mapeada em outra análise).
- **Compatibilidade:** a feature não deve alterar o comportamento do motor de issues/`-ht` existente — apenas consumi-lo. Se `CHANGELOG.md` já existir no repositório do usuário, a feature deve fazer merge/prepend da nova seção, nunca sobrescrever o arquivo inteiro.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/release/
├── commit_classifier.py       # NOVO (ou reaproveitar parser Conventional Commits existente)
├── version_bump.py            # NOVO — cálculo de bump semântico (major/minor/patch)
└── changelog_builder.py       # NOVO — monta estrutura de changelog a partir de commits classificados

src/application/use_cases/
└── generate_release_notes.py  # NOVO — orquestra: histórico -> classificação -> IA (resumo) -> changelog -> (opcional) publicação

src/infrastructure/git/
└── tag_reader.py               # NOVO (ou estender módulo já existente de leitura de branch/-ht)

src/infrastructure/scm/
└── (extensão de github_provider.py / gitlab_provider.py)  # ALTERAR — adicionar create_release()

core.py ou main.py               # ALTERAR — registrar comando `gitpr release` e subflags
src/ui/                           # ALTERAR (opcional) — TUI de preview/edição do release draft antes de publicar

tests/domain/release/
├── test_commit_classifier.py
├── test_version_bump.py
└── test_changelog_builder.py
tests/application/use_cases/
└── test_generate_release_notes.py
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/release/changelog_builder.py
from dataclasses import dataclass, field
from enum import Enum


class ChangeCategory(str, Enum):
    FEATURE = "feature"
    FIX = "fix"
    BREAKING = "breaking"
    PERFORMANCE = "performance"
    DOCS = "docs"
    REFACTOR = "refactor"
    CHORE = "chore"
    OTHER = "other"


@dataclass
class ClassifiedCommit:
    hash: str
    short_hash: str
    author_name: str
    author_email: str
    date: str                  # ISO 8601
    subject: str
    body: str
    category: ChangeCategory
    scope: str | None          # ex.: "linter", "mcp", "pr" (do Conventional Commit)
    breaking: bool
    pr_number: int | None      # se identificável via merge commit / squash message
    raw_type: str              # o prefixo original ("feat", "fix", etc.), antes da categorização


@dataclass
class ReleaseNotesResult:
    version: str                       # versão alvo, ex.: "1.2.0"
    previous_tag: str | None           # tag de origem, None se for a primeira release
    generated_at: str                  # ISO 8601
    summary: str                       # resumo em linguagem natural gerado por IA
    sections: dict[ChangeCategory, list[ClassifiedCommit]]
    breaking_changes: list[ClassifiedCommit]
    contributors: list[str]            # nomes/e-mails únicos normalizados
    markdown: str                      # changelog já formatado, pronto para prepend
    warnings: list[str]                # ex.: "12 commits sem Conventional Commits, categorizados como OTHER"
```

## 4. Algoritmo — pipeline completo

A skill deve implementar, nesta ordem:

1. **Resolver o range de commits.** Se `--since` não for informado, buscar a tag mais recente via `git describe --tags --abbrev=0` (ou lib já usada no projeto). Se não houver nenhuma tag, usar o primeiro commit do repositório como início (primeira release).
2. **Obter a lista de commits no range**, reaproveitando o motor de histórico de branch (`-ht`) já existente — não reimplementar a extração de log do Git.
3. **Classificar cada commit** por Conventional Commits: parsear prefixo (`feat`, `fix`, `perf`, `docs`, `refactor`, `chore`, etc.), scope entre parênteses, e presença de `BREAKING CHANGE:` no corpo ou `!` após o tipo/scope (ex.: `feat!:`). Se o commit não seguir o padrão, categorizar como `OTHER` e adicionar warning (não falhar).
4. **Deduplicar por PR quando aplicável.** Se o repositório usa squash-merge, cada commit já corresponde a 1 PR — identificar `pr_number` via regex no subject (padrão comum: `(#123)` ao final da mensagem de squash do GitHub) quando presente.
5. **Calcular sugestão de bump de versão** (`version_bump.py`):
   - Qualquer commit com `breaking = True` → sugerir bump de **MAJOR**.
   - Nenhum breaking, mas há ao menos um `feature` → sugerir bump de **MINOR**.
   - Apenas `fix`/`chore`/`docs`/`refactor` → sugerir bump de **PATCH**.
   - Ler a versão atual do arquivo de versionamento do projeto (`pyproject.toml`/`VERSION`/última tag) e aplicar o bump sugerido; permitir override via `--version`.
6. **Gerar resumo em linguagem natural via IA.** Montar um prompt estruturado com a lista de commits classificados (título + escopo + categoria) e pedir ao provider de IA configurado (reaproveitando `ai_providers.py`) um parágrafo de resumo executivo no topo da release — não listar código, apenas destacar o impacto para quem lê o changelog. Aplicar o mesmo mecanismo de map-reduce/cache já usado no review de diffs, caso o volume de commits seja grande.
7. **Montar o Markdown final** com estrutura fixa:
   ```markdown
   ## [1.2.0] - 2026-09-04

   ### Resumo
   {resumo gerado por IA}

   ### ⚠ Breaking Changes
   - {commit.subject} ({commit.short_hash})

   ### ✨ Features
   - {commit.subject} ({commit.short_hash}) — {scope}

   ### 🐛 Fixes
   - ...

   ### 🔧 Outros
   - ...

   **Contribuidores:** {lista de nomes únicos}
   ```
8. **Prepend no `CHANGELOG.md`** existente (criar o arquivo se não existir), nunca sobrescrever o conteúdo anterior.
9. **Se `--publish` for informado**, chamar `create_release()` do `ScmProvider`/`github_api.py` para criar a release na forge, usando a tag (`--version`), o título e o markdown gerado como corpo.

```python
# src/application/use_cases/generate_release_notes.py
def generate_release_notes(
    repo_path: str,
    since_tag: str | None,
    target_version: str | None,
    ai_provider,          # instância já resolvida via factory de ai_providers.py
    scm_provider=None,    # instância já resolvida via ScmProvider, se publish=True
    publish: bool = False,
) -> ReleaseNotesResult:
    ...
```

## 5. Extensão necessária em `ScmProvider` (se já implementada)

Se a abstração multi-forge da spec anterior já existir, adicionar ao contrato `ScmProvider` (`base.py`):

```python
@abstractmethod
def create_release(self, repo: RepoRef, tag: str, title: str, body: str, draft: bool = False) -> str:
    """Retorna a URL da release criada."""
    ...
```

Endpoints de referência para as implementações concretas:
- **GitHub:** `POST /repos/{owner}/{repo}/releases` — body: `tag_name`, `name`, `body`, `draft`.
- **GitLab:** `POST /projects/{id}/releases` — body: `tag_name`, `name`, `description`.
- **Bitbucket Cloud:** não possui conceito nativo de "Release" via API pública equivalente — nesta fase, se o provider ativo for Bitbucket, `create_release` deve levantar `NotImplementedError` com mensagem clara, e o comando `gitpr release --publish` deve avisar o usuário e oferecer apenas a geração local do `CHANGELOG.md`.
- **Azure DevOps:** releases são geridas por Pipelines/Release Management, não pela API de Git — mesmo tratamento do Bitbucket (gerar local, avisar que publicação automática não é suportada nesta fase).

Se a abstração multi-forge **ainda não existir** no momento desta implementação, a skill deve implementar `create_release` apenas para GitHub dentro de `github_api.py`, isolado em uma função própria, preparada para ser movida para `ScmProvider` quando aquela abstração for implementada.

## 6. Config

Adicionar ao schema de config existente:

```yaml
release:
  changelog_path: "CHANGELOG.md"
  commit_types:              # customizável, caso o time use tipos além do Conventional Commits padrão
    feat: feature
    fix: fix
    perf: performance
    docs: docs
    refactor: refactor
    chore: chore
  ai_summary: true            # false = changelog só com lista de commits, sem resumo gerado por IA
  auto_bump: true             # false = sempre exigir --version explícito
  publish_draft_by_default: true  # releases criadas via --publish nascem como draft na forge
```

## 7. Integração com `core.py` e CLI

```python
# core.py — novo comando
def cmd_release(args):
    since_tag = args.since or tag_reader.get_latest_tag(repo_root)
    result = generate_release_notes(
        repo_path=repo_root,
        since_tag=since_tag,
        target_version=args.version,
        ai_provider=resolve_ai_provider(config),
        scm_provider=resolve_scm_provider(config["scm"]) if args.publish else None,
        publish=args.publish,
    )
    write_or_prepend_changelog(config["release"]["changelog_path"], result.markdown)
    if args.format == "json":
        print(json.dumps(asdict(result), default=str))
    else:
        render_release_summary_terminal(result)
```

Exibir na TUI (ou terminal, se TUI não for prioridade nesta fase) uma prévia editável do texto de release antes de publicar — mesma filosofia já usada no PR Publisher (nunca publicar sem confirmação explícita, princípio já estabelecido nas specs anteriores).

## 8. Testes obrigatórios (critério de aceite)

1. **Teste de classificação de commits** (`test_commit_classifier.py`): cobrir todos os tipos Conventional Commits suportados, variações com/sem scope, `BREAKING CHANGE:` no corpo, e `!` no header (`feat!:`). Commits fora do padrão devem cair em `OTHER` sem lançar exceção.
2. **Teste de bump de versão** (`test_version_bump.py`): matriz completa — apenas fixes → PATCH; ao menos um feature sem breaking → MINOR; qualquer breaking → MAJOR, independentemente de quantos fixes/features também existam no range.
3. **Teste de deduplicação por PR**: commits de squash-merge com `(#123)` no subject devem ter `pr_number` extraído corretamente; commits sem esse padrão devem ter `pr_number = None` sem falhar.
4. **Teste de primeira release** (sem tag anterior): pipeline deve funcionar usando o primeiro commit do repositório como início, sem lançar exceção por ausência de tag.
5. **Teste de idempotência do `CHANGELOG.md`**: rodar `gitpr release` duas vezes com o mesmo range não deve duplicar a seção já escrita — ou deve detectar que a versão já existe no changelog e abortar com mensagem clara (decisão a confirmar com o usuário: sobrescrever a seção da mesma versão ou recusar).
6. **Teste de integração do use case completo** com repositório git de fixture (tags e commits reais criados no teste), incluindo mock do provider de IA (resposta determinística) para não depender de rede.
7. **Teste de `create_release` por provider**: GitHub e GitLab devem chamar o endpoint correto com o payload correto (mock de HTTP); Bitbucket e Azure DevOps devem levantar `NotImplementedError` com mensagem clara, sem quebrar o restante do fluxo (o changelog local ainda deve ser gerado).
8. **Teste de não-regressão do motor `-ht`**: qualquer alteração feita nesse módulo para reuso nesta feature não pode alterar o comportamento hoje usado pela geração de issues.

Critério de "feature completa": todos os testes acima passam; `gitpr release --draft` funciona sem qualquer chave de API de SCM configurada (só precisa da IA para o resumo, e mesmo isso deve ser opcional via `ai_summary: false`); publicação real (`--publish`) só é exercitada em teste de integração com mocks, nunca contra API real em CI.

## 9. Ordem de execução recomendada

1. Implementar `commit_classifier.py` (parsing puro de Conventional Commits, sem I/O) com testes unitários completos — reaproveitar parser existente se o projeto já tiver um para os hooks de commit.
2. Implementar `version_bump.py` (lógica pura de decisão MAJOR/MINOR/PATCH) com testes de matriz completa.
3. Implementar `tag_reader.py` (ou estender o módulo do `-ht`) para resolver a tag mais recente e o range de commits — validar contra um repositório de teste com tags reais.
4. Implementar `changelog_builder.py` montando o Markdown a partir de commits já classificados, sem envolver IA ainda (testar com resumo fixo/mockado).
5. Integrar a chamada real ao provider de IA (via `ai_providers.py`) para o resumo executivo — validar contra pelo menos um provider real antes de finalizar.
6. Implementar `generate_release_notes.py` (use case completo) conectando as peças 1–5, com teste de integração usando fixture de repositório git real.
7. Adicionar `create_release()` a `github_api.py` (ou `ScmProvider`, se a abstração multi-forge já existir); implementar para GitHub e GitLab; `NotImplementedError` tratado para Bitbucket/Azure DevOps.
8. Registrar o comando `gitpr release` em `core.py`/CLI, com todas as subflags (`--draft`, `--since`, `--version`, `--publish`, `--format`).
9. (Opcional, se houver tempo/prioridade) Adicionar preview editável na TUI antes de publicar.
10. Atualizar `config.schema.yml` e documentação (README/CLI help).
11. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa deve ser um commit/PR isolado e revisável. Não implementar classificação, bump de versão, geração de changelog e publicação em um único commit grande.

## 10. Encaixe estratégico (contexto de monetização)

Classificada como Tier 1 (alto impacto, baixo esforço) porque reaproveita o motor de histórico de branch (`-ht`) já existente e a infraestrutura de IA já madura (BYOK/Ollama), sem exigir backend novo. Fica no tier **Free/Community**: é uma feature de produtividade individual/de repositório que qualquer usuário sente o valor imediatamente ("ninguém resiste a changelog automático", como apontado nas análises originais), e serve como demonstração pública do produto — um `CHANGELOG.md` bem formatado, gerado por IA, é conteúdo visível em qualquer repositório público que vira vitrine passiva do GitPR. A publicação para múltiplos repositórios de uma mesma organização, agregada em um dashboard de releases, é o gancho natural para o futuro tier **Team**.
