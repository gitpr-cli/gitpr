# Documentação Técnica: Notas de Versão e Changelog (gitpr release)

`gitpr release` é o primeiro subcomando do GitPR CLI e gera o changelog / as notas de versão do repositório atual ("release notes" e "changelog" designam o mesmo fluxo). Uma única execução percorre os commits recolhidos entre uma tag de origem e o `HEAD`, classifica-os por Conventional Commits, sugere um bump semântico de versão, adiciona opcionalmente um resumo executivo de IA e antepõe uma nova secção de versão ao changelog do repositório. A geração é puramente local por omissão — nada é publicado e nenhuma tag local ou ficheiro de versão é tocado; `--publish` vai mais longe e cria a release na forge configurada após uma confirmação explícita.

---

## 1. Visão Geral

O comando raiz mantém todas as suas opções legadas inalteradas (`-r`, `-c`, `-is`, `-l`, ...) — o subcomando é uma adição, não uma reescrita. Executado sem flags, `gitpr release` realiza o fluxo local: recolhe o intervalo de commits, classifica, sugere a versão, gera a secção (opcionalmente com resumo de IA), grava o `CHANGELOG.md`, guarda o artefacto da execução e imprime uma pré-visualização no terminal limitada a 40 linhas (`… and N more lines` quando for maior — v1 não tem pré-visualização interativa em TUI). Se já existir uma secção de versão no changelog, o comando aborta em vez de a duplicar (veja a secção 6, Modo JSON e Idempotência).

### 1.1 Referência de Comando — `gitpr release`

Todas as opções do subcomando, como apresentadas por `gitpr release -h` (ou `--help`):

```bash
gitpr release
gitpr release --version 2.0.0
gitpr release --publish
```

| Opção | Descrição |
| --- | --- |
| **`--since <tag>`** | Origem do intervalo: tag ou referência a partir da qual os commits são recolhidos (predefinição: a última tag alcançável, ou o primeiro commit quando não existe tag) |
| **`--version <x.y.z>`** | Versão alvo da release (predefinição: sugestão automática de bump semântico) |
| **`--publish`** | Após gerar, publica a release na forge configurada (pede confirmação) |
| **`--draft`** | Cria a release como rascunho na forge (GitHub). Só se aplica em conjunto com `--publish`; GitLab não tem conceito de rascunho |
| **`--format {markdown\|json}`** | `json` imprime o resultado completo no stdout sem tocar em ficheiros nem publicar (predefinição: `markdown`) |
| **`--force`** | Regenera a secção de versão quando ela já existe no changelog (sobreposição de idempotência) |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Commits do intervalo `since..HEAD`, merges excluídos |
| **Resumo de IA** | Automático quando uma chave de API está configurada (desative com `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Ficheiros gravados** | Nova secção no `CHANGELOG.md` + artefacto `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publicado** | Nada — a geração local é a predefinição |
| **Tags locais / ficheiros de versão** | Nunca tocados (read-only: as sugestões de versão vêm apenas das tags git) |

---

## 2. Intervalo da Release e Sugestão de Versão

### 2.1 Intervalo de Commits — `--since <tag>`

Uma release cobre sempre os commits de uma origem até ao `HEAD`. A origem é, por omissão, a última tag alcançável, e o fim do intervalo é sempre o `HEAD` — gerar entre duas tags antigas não é suportado na v1. Commits de merge nunca chegam ao changelog: são excluídos no momento da recolha.

```bash
# Predefinição: da última tag alcançável ao HEAD
gitpr release

# Origem explícita: tudo desde v1.0.0
gitpr release --since v1.0.0
```

| Característica | Descrição |
| --- | --- |
| **Origem predefinida** | Última tag alcançável (`git describe --tags --abbrev=0`) |
| **Sem tag no repositório** | Primeira release: o intervalo começa no primeiro commit do repositório |
| **Commits de merge** | Excluídos da recolha |
| **Fim do intervalo** | Sempre `HEAD` |

### 2.2 Sugestão de Versão Semântica

Sem `--version`, o engine sugere um bump a partir dos commits classificados, seguindo o versionamento semântico:

| Commits do intervalo | Bump sugerido |
| --- | --- |
| Qualquer commit **breaking** (de rutura) | **MAJOR** |
| Nenhum commit breaking, pelo menos uma **funcionalidade** | **MINOR** |
| Apenas fixes, chores ou outras alterações | **PATCH** |

A sugestão é read-only: vem exclusivamente das tags git — o engine nunca lê ficheiros de versão (como `pyproject.toml`) e nunca cria tags locais. O prefixo `v` da última tag é preservado (`v1.2.3` sugere `v1.2.4`, gravado como `## [v1.2.4]`). Quando não existe nenhuma tag de versão semântica anterior, não há sugestão — numa primeira release, o `--version` torna-se obrigatório para publicar.

Quando a versão vem da sugestão, o comando pede confirmação antes da chamada de IA: `❓ Use the suggested version {version}?` (aceitar é a predefinição). O prompt é ignorado com `--version` explícito, em `--format json`, em terminais silenciosos ou não interativos, e com `GITPR_RELEASE_AUTO_BUMP=false` (que exige um `--version` explícito em todas as execuções).

### 2.3 Versão Explícita — `--version <x.y.z>`

O `--version` sobrepõe-se à sugestão (sem prompt de confirmação) e é a única fonte da tag publicada na forge. Introduza um `x.y.z` simples — o prefixo `v` não é necessário.

```bash
gitpr release --version 2.0.0
gitpr release --since v1.0.0 --version 1.1.0
```

---

## 3. Estrutura do Changelog e Ficheiros

### 3.1 Classificação de Commits

Cada commit do intervalo é analisado pelas regras de Conventional Commits: `type`, `scope` opcional, marcadores de breaking (`!` após o type/scope ou uma linha `BREAKING CHANGE:` no corpo) e o sufixo de squash-merge de PR `(#123)`. Commits que não seguem a convenção nunca são rejeitados — caem em **OTHER** com um aviso, e duplicados do mesmo PR são reconhecidos e deduplicados.

| Categoria | Gatilho | Título (fallback em inglês) |
| --- | --- | --- |
| **BREAKING** | Marcador de breaking em qualquer type (`feat!`, `refactor!`, `BREAKING CHANGE:` ...) | `⚠️ Breaking Changes` |
| **FEATURE** | `feat:` | `✨ Features` |
| **FIX** | `fix:` | `🐛 Fixes` |
| **PERFORMANCE** | `perf:` | `⚡ Performance` |
| **DOCS** | `docs:` | `📚 Docs` |
| **REFACTOR** | `refactor:` | `♻️ Refactoring` |
| **CHORE** | `chore:` | `🔧 Chores` |
| **OTHER** | Qualquer outra coisa (não conformes ou tipos desconhecidos) | `📦 Other Changes` |

Os blocos de categoria seguem a ordem fixa FEATURE, FIX, PERFORMANCE, DOCS, REFACTOR, CHORE, OTHER (blocos vazios são omitidos). Commits breaking aparecem apenas sob `⚠️ Breaking Changes`, nunca duplicados dentro da própria categoria. Os títulos passam pelo motor de localização do GitPR, pelo que o ficheiro gerado segue o idioma da interface, com inglês como fallback.

### 3.2 Anatomia da Secção de Versão

Uma release produz uma secção de versão: o cabeçalho `## [x.y.z] - date`, um `### Summary` opcional, um bloco por categoria presente e um rodapé `**Contributors:**` com os nomes únicos de autores (deduplicados por e-mail, ordenados). Cada entrada é apresentada como `subject (short hash)`, com o scope do commit anexado quando presente:

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 (b2c3d4e) — core

### ✨ Features
- add the gitpr release subcommand (a1b2c3d) — cli
- publish releases on GitLab (#567) (d4e5f6g) — scm

### 🐛 Fixes
- handle repositories without tags (f6a7b8c) — release

**Contributors:** Ana Souza, Bob Smith
```

A secção é anteposta ao `CHANGELOG.md` — o ficheiro nunca é reescrito de raiz e as secções anteriores são preservadas. Quando já existe uma secção `## [x.y.z]` para a mesma versão, o comando aborta com código de saída 1 (veja a secção 6, Modo JSON e Idempotência); nunca duplica e nunca substitui silenciosamente.

### 3.3 Ficheiros Gravados

| Artefacto | Caminho | Observações |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Raiz do repositório por omissão — a exceção deliberada à convenção de `.gitpr/reports/`, porque é um ficheiro público e passível de commit. Substitua com `GITPR_RELEASE_CHANGELOG_PATH` (caminhos relativos resolvidos a partir da raiz do repositório) |
| **Artefacto de notas de versão** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Gravado em todas as execuções markdown, best-effort: uma falha de gravação apenas avisa e nunca derruba o comando. Template de nome via `OUTPUT_FILE_NAME_RELEASE` |
| **Pré-visualização no terminal** | — | Impressa depois de gravar, até 40 linhas |

---

## 4. Resumo Executivo de IA

O parágrafo `### Summary` opcional é gerado pela IA a partir dos commits classificados do intervalo e escrito no idioma atual da interface.

### 4.1 Template de Skill no Primeiro Uso — `.gitpr.release.md`

```bash
# Primeira execução em modo markdown transfere o template (language-aware, nunca substitui)
gitpr release
```

Na primeira execução em modo markdown, o CLI transfere o template de skill `.gitpr.release.md` dos templates do projeto. A transferência respeita o idioma atual da interface (variantes remotas como `gitpr.release.pt_pt.md` são guardadas localmente como `.gitpr.release.md`), nunca substitui um ficheiro local existente e nunca falha por erro de rede — a execução prossegue com a persona incorporada. A transferência é totalmente omitida em `--format json`, que é stdout-only. O ficheiro é carregado como system instruction da IA (persona: **Release Manager**, contrato estrito de JSON) — edite-o localmente para personalizar o resumo executivo. Veja a [documentação de Skills e Templates](skill-template.md) para o mecanismo geral.

### 4.2 Geração e Degradação Controlada

Intervalos com mais de 200 commits são resumidos em lotes (Map-Reduce, com aviso como `📦 Large commit range detected!`), e as respostas passam pela cache MD5 padrão do GitPR, pelo que execuções inalteradas não repetem chamadas de IA. Duas observações: a cache tem como chave o prompt — editar o `.gitpr.release.md` não invalida resumos em cache — e o resumo usa sempre a mesma infraestrutura de IA dos outros comandos do GitPR (fornecedor configurado, saída JSON, tentativa automática). Veja a [documentação de Fornecedores de IA](providers-ia.md).

O resumo nunca bloqueia o comando: sem chave de API configurada, ou quando a chamada de IA falha, o comando avisa (`AI summary failed: changelog generated without a summary.`) e gera a secção apenas com as listas classificadas. `GITPR_RELEASE_AI_SUMMARY=false` desliga o resumo por completo.

---

## 5. Publicação na Forge

### 5.1 Confirmação e Salvaguardas — `--publish`

A publicação só acontece no fluxo markdown, após a geração local e a pré-visualização, atrás de uma confirmação explícita: `❓ Publish release {version} on {provider}?` — recusar (a predefinição) mantém o changelog e imprime `⏭️ Publication skipped — the changelog was generated locally.` O corpo da release enviado à forge é a secção gerada sem o cabeçalho `## [x.y.z] - date` (o título da release transporta a versão).

```bash
gitpr release --publish
gitpr release --since v1.0.0 --version 1.2.0 --publish
```

Salvaguardas: sem um remote git `origin`, o comando recusa-se a publicar (`❌ No git remote 'origin' found. Cannot publish the release.`, código de saída 1); em combinação com `--format json`, o `--publish` apenas avisa que será ignorado (`⚠️ --format json is stdout-only: --publish is ignored.`) — o modo JSON nunca publica; após uma execução local simples, o CLI sugere `ℹ️ To publish this release on the forge, run again with --publish.`

### 5.2 Forges Suportadas

A publicação visa a forge configurada nas definições SCM (`gitpr --init` ou `GITPR_SCM_PROVIDER`). Veja a [documentação Multi-Forge SCM](scm-multiforge.md) para a configuração do fornecedor.

| Forge | Release | Observações |
| --- | --- | --- |
| **GitHub** | Sim | Uma tag ausente é criada automaticamente pela API, apontando para a branch predefinida do repositório (não o `HEAD` local); rascunhos honrados |
| **GitLab** | Sim | A tag já deve existir na forge; não há conceito nativo de rascunho |
| **Bitbucket Cloud** | Não | Sem API de release — o comando avisa e mantém o changelog local para publicação manual |
| **Azure DevOps** | Não | Sem API de release — o comando avisa e mantém o changelog local para publicação manual |

Quando a publicação não é suportada, o aviso é `⚠️ Release publishing is not supported on {provider}. The changelog was generated locally — publish it manually.`

### 5.3 Rascunhos — `--draft`

O `--draft` só importa em conjunto com `--publish` (isolado, avisa `⚠️ --draft only applies together with --publish: generating the changelog locally.`). GitHub é a única forge com conceito de rascunho e, por omissão, um `--publish` no GitHub já cria um **rascunho** (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`); passe `--draft` para forçar um rascunho quando essa predefinição estiver desligada. GitLab não tem rascunhos: um pedido de rascunho apenas avisa e publica diretamente.

```bash
gitpr release --publish --draft
```

---

## 6. Modo JSON e Idempotência

### 6.1 Saída JSON Pura — `--format json`

O `--format json` é stdout-only, ideal para scripts e CI: não escreve nada (sem atualização do `CHANGELOG.md`, sem artefacto da execução, sem transferência de skill), não publica nada e nunca pergunta (a confirmação de versão é ignorada). O stream do stdout permanece limpo — os avisos viajam dentro do payload JSON. A saída segue o resultado da release: `version`, `previous_tag`, `generated_at`, `summary`, `sections` (uma lista de commits classificados por categoria), `breaking_changes`, `contributors`, `markdown` e `warnings`.

```bash
gitpr release --format json
```

### 6.2 Secção Existente e `--force`

A gravação do changelog é idempotente por versão: quando a secção `## [x.y.z]` da versão alvo já existe, o comando aborta com código de saída 1 sem alterar o ficheiro — nunca duplica conteúdo e nunca o substitui silenciosamente. O `--force` regenera e substitui essa secção (`🔄 Existing section for version {version} regenerated.`); sem secção existente, o `--force` é uma simples adição.

```bash
gitpr release --force
gitpr release --since v1.0.0 --version 1.2.0 --force
```

---

## 7. Variáveis de Ambiente

A configuração da release é lida do ficheiro global `~/.gitpr/.env` (formato dotenv). Booleanos seguem a convenção de "false desliga": não definido ou qualquer valor diferente de `false` / `0` / `no` / `off` / `n` significa ativado — as predefinições da tabela valem quando a variável não está definida.

| Variável | Valor predefinido | Finalidade |
| --- | --- | --- |
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Ficheiro do changelog; caminhos relativos resolvidos a partir da raiz do repositório, caminhos absolutos honrados |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Ativa o resumo executivo de IA; `false` gera apenas as listas classificadas |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Ativa o bump semântico automático; `false` exige um `--version` explícito |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | GitHub: `--publish` cria a release como rascunho por omissão |
| `OUTPUT_FILE_NAME_RELEASE` | `{branch}_{datetime}_RELEASE.md` | Template de nome do artefacto da execução em `.gitpr/reports/release/` |

> **Nota:** Consulte também a [documentação de Skills e Templates](skill-template.md) para personalizar os ficheiros de template de IA do GitPR.
