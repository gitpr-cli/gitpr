# Documentação Técnica: Notas de Versão e Changelog (gitpr release)

`gitpr release` é o primeiro subcomando do GitPR CLI e gera o changelog / as notas de versão do repositório atual ("release notes" e "changelog" nomeiam o mesmo fluxo). Uma única execução varre os commits coletados entre uma tag de origem e o `HEAD`, classifica-os por Conventional Commits, sugere um bump semântico de versão, adiciona opcionalmente um resumo executivo de IA e prefixa uma nova seção de versão ao changelog do repositório. A geração é puramente local por padrão — nada é publicado e nenhuma tag local ou arquivo de versão é tocado; `--publish` vai além e cria a release na forge configurada após uma confirmação explícita.

---

## 1. Visão Geral

O comando raiz mantém todas as suas opções legadas inalteradas (`-r`, `-c`, `-is`, `-l`, ...) — o subcomando é uma adição, não uma reescrita. Executado sem flags, `gitpr release` realiza o fluxo local: coleta o intervalo de commits, classifica, sugere a versão, gera a seção (opcionalmente com resumo de IA), grava o `CHANGELOG.md`, salva o artefato da execução e imprime uma prévia no terminal limitada a 40 linhas (`… and N more lines` quando for maior — v1 não tem prévia interativa em TUI). Se uma seção de versão já existir no changelog, o comando aborta em vez de duplicá-la (veja a seção 6, Modo JSON e Idempotência).

### 1.1 Referência de Comando — `gitpr release`

Todas as opções do subcomando, como mostrado por `gitpr release -h` (ou `--help`):

```bash
gitpr release
gitpr release --version 2.0.0
gitpr release --publish
```

| Opção | Descrição |
| --- | --- |
| **`--since <tag>`** | Origem do intervalo: tag ou referência a partir de onde os commits são coletados (padrão: a última tag alcançável, ou o primeiro commit quando não existe tag) |
| **`--version <x.y.z>`** | Versão alvo da release (padrão: sugestão automática de bump semântico) |
| **`--publish`** | Após gerar, publica a release na forge configurada (pede confirmação) |
| **`--draft`** | Cria a release como rascunho na forge (GitHub). Só se aplica junto com `--publish`; GitLab não tem conceito de rascunho |
| **`--format {markdown\|json}`** | `json` imprime o resultado completo no stdout sem tocar em arquivos nem publicar (padrão: `markdown`) |
| **`--force`** | Regenera a seção de versão quando ela já existe no changelog (override de idempotência) |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Commits do intervalo `since..HEAD`, merges excluídos |
| **Resumo de IA** | Automático quando uma chave de API está configurada (desative com `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Arquivos gravados** | Nova seção no `CHANGELOG.md` + artefato `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publicado** | Nada — a geração local é o padrão |
| **Tags locais / arquivos de versão** | Nunca tocados (read-only: as sugestões de versão vêm apenas das tags git) |

---

## 2. Intervalo da Release e Sugestão de Versão

### 2.1 Intervalo de Commits — `--since <tag>`

Uma release sempre cobre os commits de uma origem até o `HEAD`. A origem é, por padrão, a última tag alcançável, e o fim do intervalo é sempre o `HEAD` — gerar entre duas tags antigas não é suportado na v1. Commits de merge nunca chegam ao changelog: são excluídos no momento da coleta.

```bash
# Padrão: da última tag alcançável ao HEAD
gitpr release

# Origem explícita: tudo desde v1.0.0
gitpr release --since v1.0.0
```

| Característica | Descrição |
| --- | --- |
| **Origem padrão** | Última tag alcançável (`git describe --tags --abbrev=0`) |
| **Sem tag no repositório** | Primeira release: o intervalo começa no primeiro commit do repositório |
| **Commits de merge** | Excluídos da coleta |
| **Fim do intervalo** | Sempre `HEAD` |

### 2.2 Sugestão de Versão Semântica

Sem `--version`, o engine sugere um bump a partir dos commits classificados, seguindo o versionamento semântico:

| Commits do intervalo | Bump sugerido |
| --- | --- |
| Qualquer commit **breaking** (de quebra) | **MAJOR** |
| Nenhum commit breaking, pelo menos uma **feature** | **MINOR** |
| Apenas fixes, chores ou outras mudanças | **PATCH** |

A sugestão é read-only: ela vem exclusivamente das tags git — o engine nunca lê arquivos de versão (como `pyproject.toml`) e nunca cria tags locais. O prefixo `v` da última tag é preservado (`v1.2.3` sugere `v1.2.4`, gravado como `## [v1.2.4]`). Quando não existe nenhuma tag de versão semântica anterior, não há sugestão — numa primeira release, o `--version` torna-se obrigatório para publicar.

Quando a versão vem da sugestão, o comando pede confirmação antes da chamada de IA: `❓ Use the suggested version {version}?` (aceitar é o padrão). O prompt é pulado com `--version` explícito, em `--format json`, em terminais silenciosos ou não interativos, e com `GITPR_RELEASE_AUTO_BUMP=false` (que exige um `--version` explícito em toda execução).

### 2.3 Versão Explícita — `--version <x.y.z>`

O `--version` sobrepõe a sugestão (sem prompt de confirmação) e é a única fonte da tag publicada na forge. Passe um `x.y.z` simples — o prefixo `v` não é necessário.

```bash
gitpr release --version 2.0.0
gitpr release --since v1.0.0 --version 1.1.0
```

---

## 3. Estrutura do Changelog e Arquivos

### 3.1 Classificação de Commits

Cada commit do intervalo é analisado pelas regras de Conventional Commits: `type`, `scope` opcional, marcadores de breaking (`!` após o type/scope ou uma linha `BREAKING CHANGE:` no corpo) e o sufixo de squash-merge de PR `(#123)`. Commits que não seguem a convenção nunca são rejeitados — caem em **OTHER** com um aviso, e duplicatas do mesmo PR são reconhecidas e deduplicadas.

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

Os blocos de categoria seguem a ordem fixa FEATURE, FIX, PERFORMANCE, DOCS, REFACTOR, CHORE, OTHER (blocos vazios são pulados). Commits breaking aparecem apenas sob `⚠️ Breaking Changes`, nunca duplicados dentro da própria categoria. Os títulos passam pelo engine de localização do GitPR, então o arquivo gerado segue o idioma da interface, com inglês como fallback.

### 3.2 Anatomia da Seção de Versão

Uma release produz uma seção de versão: o cabeçalho `## [x.y.z] - date`, um `### Summary` opcional, um bloco por categoria presente e um rodapé `**Contributors:**` com os nomes únicos de autores (deduplicados por e-mail, ordenados). Cada entrada é renderizada como `subject (short hash)`, com o scope do commit anexado quando presente:

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

A seção é prefixada ao `CHANGELOG.md` — o arquivo nunca é reescrito do zero e as seções anteriores são preservadas. Quando uma seção `## [x.y.z]` para a mesma versão já existe, o comando aborta com código de saída 1 (veja a seção 6, Modo JSON e Idempotência); ele nunca duplica e nunca sobrescreve em silêncio.

### 3.3 Arquivos Gravados

| Artefato | Caminho | Observações |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Raiz do repositório por padrão — a exceção deliberada à convenção de `.gitpr/reports/`, porque é um arquivo público e commitável. Substitua com `GITPR_RELEASE_CHANGELOG_PATH` (caminhos relativos resolvidos a partir da raiz do repositório) |
| **Artefato de release notes** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Gravado em toda execução markdown, best-effort: uma falha de gravação apenas avisa e nunca derruba o comando. Template de nome via `OUTPUT_FILE_NAME_RELEASE` |
| **Prévia no terminal** | — | Impressa após salvar, até 40 linhas |

---

## 4. Resumo Executivo de IA

O parágrafo `### Summary` opcional é gerado pela IA a partir dos commits classificados do intervalo e escrito no idioma atual da interface.

### 4.1 Template de Skill no Primeiro Uso — `.gitpr.release.md`

```bash
# Primeira execução em modo markdown baixa o template (language-aware, nunca sobrescreve)
gitpr release
```

Na primeira execução em modo markdown, o CLI baixa o template de skill `.gitpr.release.md` dos templates do projeto. O download respeita o idioma atual da interface (variantes remotas como `gitpr.release.pt_br.md` são salvas localmente como `.gitpr.release.md`), nunca sobrescreve um arquivo local existente e nunca falha por erro de rede — a execução prossegue com a persona embutida. O download é totalmente pulado em `--format json`, que é stdout-only. O arquivo é carregado como system instruction da IA (persona: **Release Manager**, contrato estrito de JSON) — edite-o localmente para customizar o resumo executivo. Veja a [documentação de Skills e Templates](skill-template.md) para o mecanismo geral.

### 4.2 Geração e Degradação Suave

Intervalos com mais de 200 commits são resumidos em lotes (Map-Reduce, com aviso como `📦 Large commit range detected!`), e as respostas passam pelo cache MD5 padrão do GitPR, então execuções inalteradas não repetem chamadas de IA. Duas observações: o cache é chaveado pelo prompt — editar o `.gitpr.release.md` não invalida resumos cacheados — e o resumo usa sempre a mesma infraestrutura de IA dos outros comandos do GitPR (provedor configurado, saída JSON, retry automático). Veja a [documentação de Provedores de IA](providers-ia.md).

O resumo nunca bloqueia o comando: sem chave de API configurada, ou quando a chamada de IA falha, o comando avisa (`AI summary failed: changelog generated without a summary.`) e gera a seção apenas com as listas classificadas. `GITPR_RELEASE_AI_SUMMARY=false` desliga o resumo por completo.

---

## 5. Publicação na Forge

### 5.1 Confirmação e Salvaguardas — `--publish`

A publicação só acontece no fluxo markdown, após a geração local e a prévia, atrás de uma confirmação explícita: `❓ Publish release {version} on {provider}?` — recusar (o padrão) mantém o changelog e imprime `⏭️ Publication skipped — the changelog was generated locally.` O corpo da release enviado à forge é a seção gerada sem o cabeçalho `## [x.y.z] - date` (o título da release carrega a versão).

```bash
gitpr release --publish
gitpr release --since v1.0.0 --version 1.2.0 --publish
```

Salvaguardas: sem um remote git `origin`, o comando se recusa a publicar (`❌ No git remote 'origin' found. Cannot publish the release.`, código de saída 1); combinado com `--format json`, o `--publish` apenas avisa que será ignorado (`⚠️ --format json is stdout-only: --publish is ignored.`) — o modo JSON nunca publica; após uma execução local simples, o CLI sugere `ℹ️ To publish this release on the forge, run again with --publish.`

### 5.2 Forges Suportadas

A publicação mira a forge configurada nas definições SCM (`gitpr --init` ou `GITPR_SCM_PROVIDER`). Veja a [documentação Multi-Forge SCM](scm-multiforge.md) para a configuração do provedor.

| Forge | Release | Observações |
| --- | --- | --- |
| **GitHub** | Sim | Uma tag ausente é criada automaticamente pela API, apontando para a branch padrão do repositório (não o `HEAD` local); rascunhos honrados |
| **GitLab** | Sim | A tag já deve existir na forge; não há conceito nativo de rascunho |
| **Bitbucket Cloud** | Não | Sem API de release — o comando avisa e mantém o changelog local para publicação manual |
| **Azure DevOps** | Não | Sem API de release — o comando avisa e mantém o changelog local para publicação manual |

Quando a publicação não é suportada, o aviso é `⚠️ Release publishing is not supported on {provider}. The changelog was generated locally — publish it manually.`

### 5.3 Rascunhos — `--draft`

O `--draft` só importa junto com `--publish` (sozinho, ele avisa `⚠️ --draft only applies together with --publish: generating the changelog locally.`). GitHub é a única forge com conceito de rascunho e, por padrão, um `--publish` no GitHub já cria um **rascunho** (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`); passe `--draft` para forçar um rascunho quando esse padrão estiver desligado. GitLab não tem rascunhos: um pedido de rascunho apenas avisa e publica direto.

```bash
gitpr release --publish --draft
```

---

## 6. Modo JSON e Idempotência

### 6.1 Saída JSON Pura — `--format json`

O `--format json` é stdout-only, ideal para scripts e CI: não escreve nada (sem atualização do `CHANGELOG.md`, sem artefato da execução, sem download de skill), não publica nada e nunca pergunta (a confirmação de versão é pulada). O stream do stdout permanece limpo — os avisos viajam dentro do payload JSON. A saída segue o resultado da release: `version`, `previous_tag`, `generated_at`, `summary`, `sections` (uma lista de commits classificados por categoria), `breaking_changes`, `contributors`, `markdown` e `warnings`.

```bash
gitpr release --format json
```

### 6.2 Seção Existente e `--force`

A gravação do changelog é idempotente por versão: quando a seção `## [x.y.z]` da versão alvo já existe, o comando aborta com código de saída 1 sem alterar o arquivo — nunca duplica conteúdo e nunca o sobrescreve em silêncio. O `--force` regenera e substitui essa seção (`🔄 Existing section for version {version} regenerated.`); sem seção existente, o `--force` é uma simples adição.

```bash
gitpr release --force
gitpr release --since v1.0.0 --version 1.2.0 --force
```

---

## 7. Variáveis de Ambiente

A configuração da release é lida do arquivo global `~/.gitpr/.env` (formato dotenv). Booleanos seguem a convenção de "false desliga": não definido ou qualquer valor diferente de `false` / `0` / `no` / `off` / `n` significa ativado — os padrões da tabela valem quando a variável não está definida.

| Variável | Valor padrão | Finalidade |
| --- | --- | --- |
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Arquivo do changelog; caminhos relativos resolvidos a partir da raiz do repositório, caminhos absolutos honrados |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Ativa o resumo executivo de IA; `false` gera apenas as listas classificadas |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Ativa o bump semântico automático; `false` exige um `--version` explícito |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | GitHub: `--publish` cria a release como rascunho por padrão |
| `OUTPUT_FILE_NAME_RELEASE` | `{branch}_{datetime}_RELEASE.md` | Template de nome do artefato da execução em `.gitpr/reports/release/` |

> **Nota:** Consulte também a [documentação de Skills e Templates](skill-template.md) para personalizar os arquivos de template de IA do GitPR.
