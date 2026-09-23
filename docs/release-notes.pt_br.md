# Documentação Técnica: Notas de Versão e Changelog (gitpr release)

`gitpr release` é o primeiro subcomando do GitPR CLI e gera o changelog / as notas de versão do repositório atual ("release notes" e "changelog" nomeiam o mesmo fluxo). Uma única execução resolve onde a release anterior terminou — a seção da versão anterior no changelog —, coleta os commits dali até o `HEAD`, classifica-os por Conventional Commits, descarta tudo o que uma seção anterior já listou, sugere um bump semântico de versão, adiciona opcionalmente um resumo executivo de IA e prefixa uma nova seção de versão ao changelog do repositório. Cada entrada traz o link do commit e a data do evento, o pull request quando o commit veio de um squash merge, e os contribuidores são linkados ao seu perfil na forge. A geração é puramente local por padrão — nada é publicado e nenhuma tag local ou arquivo de versão é tocado; `--publish` vai além e cria a release na forge configurada após uma confirmação explícita.

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
| **`--since <tag>`** | Origem do intervalo: tag ou referência a partir de onde os commits são coletados (padrão: a release anterior — veja a Seção 2.1) |
| **`--version <x.y.z>`** | Versão alvo da release (padrão: sugestão automática de bump semântico) |
| **`--publish`** | Após gerar, publica a release na forge configurada (pede confirmação) |
| **`--draft`** | Cria a release como rascunho na forge (GitHub). Só se aplica junto com `--publish`; GitLab não tem conceito de rascunho |
| **`--format {markdown\|json}`** | `json` imprime o resultado completo no stdout sem tocar em arquivos nem publicar (padrão: `markdown`) |
| **`--force`** | Regenera a seção de versão quando ela já existe no changelog (override de idempotência) |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Commits do intervalo `origin..HEAD` (origem = a release anterior), merges excluídos, menos o que uma seção anterior já listou |
| **Resumo de IA** | Automático quando uma chave de API está configurada (desative com `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Arquivos gravados** | Nova seção no `CHANGELOG.md` + artefato `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publicado** | Nada — a geração local é o padrão |
| **Tags locais / arquivos de versão** | Nunca tocados (read-only: as sugestões de versão vêm da versão anterior no changelog, com a última tag como alternativa) |

---

## 2. Intervalo da Release e Sugestão de Versão

### 2.1 Intervalo de Commits — `--since <tag>`

Uma release sempre cobre os commits de uma origem até o `HEAD`. A origem é, por padrão, **a release anterior registrada no changelog**, de modo que cada versão lista apenas o seu próprio delta e nada que já foi publicado; o fim do intervalo é sempre o `HEAD` — gerar entre duas tags antigas não é suportado na v1. Commits de merge nunca chegam ao changelog: são excluídos no momento da coleta.

```bash
# Padrão: da release anterior no changelog ao HEAD
gitpr release

# Origem explícita: tudo desde v1.0.0
gitpr release --since v1.0.0
```

A origem padrão é resolvida percorrendo esta cadeia, parando no primeiro passo que produza uma referência utilizável (todo candidato precisa ser ancestral do `HEAD`):

| # | Origem | Quando se aplica |
| --- | --- | --- |
| 1 | **`--since <ref>`** | A flag é sempre honrada, e uma referência desconhecida aborta a execução |
| 2 | **Hash do commit mais recente da seção da versão anterior** | O caso normal: hashes de commit independem de tags, então o intervalo é exato mesmo quando as tags de versão vivem apenas em outro branch |
| 3 | **A versão daquela seção, como tag (`1.2.0` ou `v1.2.0`)** | Seções escritas à mão, ou geradas antes de os hashes serem emitidos |
| 4 | **Última tag alcançável (`git describe --tags --abbrev=0`)** | Nada acima pôde ser usado. Esse intervalo pode listar commits já publicados, então vem com um aviso visível e uma entrada em `warnings` |

Uma seção cujos commits já foram listados é descartada uma segunda vez por um **filtro de segurança**: antes de renderizar, qualquer commit cujo hash curto apareça em *outra* seção de versão do changelog é removido, e a contagem é reportada (`{count} commit(s) already released in a previous version were skipped.`). A âncora já evita isso; o filtro mantém honesto um changelog editado à mão. Quando todos os commits do intervalo já foram publicados, a execução aborta em vez de gravar uma seção vazia (`❌ Nothing new to release: every commit of the range is already in {path}.`).

| Característica | Descrição |
| --- | --- |
| **Origem padrão** | A seção da versão anterior no changelog (veja a cadeia acima) |
| **Sem seção anterior** | Primeira release: o intervalo começa na última tag, ou no primeiro commit do repositório quando não há tag |
| **Commits de merge** | Excluídos da coleta |
| **Commits já publicados** | Removidos pelo filtro de segurança, com contagem |
| **Fim do intervalo** | Sempre `HEAD` |

### 2.2 Sugestão de Versão Semântica

Sem `--version`, o engine sugere um bump a partir dos commits classificados, seguindo o versionamento semântico:

| Commits do intervalo | Bump sugerido |
| --- | --- |
| Qualquer commit **breaking** (de quebra) | **MAJOR** |
| Nenhum commit breaking, pelo menos uma **feature** | **MINOR** |
| Apenas fixes, chores ou outras mudanças | **PATCH** |

A sugestão é read-only: ela vem exclusivamente da release anterior — a versão da seção anterior do changelog, com a última tag git como alternativa — então o engine nunca lê arquivos de versão (como `pyproject.toml`) e nunca cria tags locais. O prefixo `v` da versão anterior é preservado (`v1.2.3` sugere `v1.2.4`, gravado como `## [v1.2.4]`). Quando não existe nenhuma versão semântica anterior, não há sugestão — numa primeira release, o `--version` torna-se obrigatório para publicar.

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

Uma release produz uma seção de versão: o cabeçalho `## [x.y.z] - date`, um `### Summary` opcional, um bloco por categoria presente e um rodapé `**Contributors:**` com os nomes únicos de autores (deduplicados por e-mail, ordenados). Toda entrada segue este formato:

```text
- {subject} ([{short_hash}]({commit_url})) — {scope} · [#{n}]({pr_url}) · {YYYY-MM-DD}
```

| Parte | Regra |
| --- | --- |
| `({short_hash})` | Sempre presente, linkado ao commit na forge. A forma curta permanece visível como texto do link |
| `— {scope}` | Apenas quando o Conventional Commit declara um scope (posição inalterada) |
| `· [#{n}]({pr_url})` | Apenas quando o commit carrega um número de PR (sufixo `(#123)` de squash merge) |
| `· {YYYY-MM-DD}` | Sempre presente — a data de autoria do commit |

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 ([b2c3d4e](https://github.com/acme/app/commit/b2c3d4e…)) — core · 2026-09-02

### ✨ Features
- add the gitpr release subcommand ([a1b2c3d](https://github.com/acme/app/commit/a1b2c3d…)) — cli · 2026-09-01
- publish releases on GitLab ([d4e5f6a](https://github.com/acme/app/commit/d4e5f6a…)) — scm · [#567](https://github.com/acme/app/pull/567) · 2026-09-03

### 🐛 Fixes
- handle repositories without tags ([f6a7b8c](https://github.com/acme/app/commit/f6a7b8c…)) — release · 2026-09-04

**Contributors:** [@anasouza](https://github.com/anasouza), Bob Smith
```

Os contribuidores são linkados ao seu perfil quando a forge expõe um: o e-mail do autor é resolvido para um login, e o rodapé renderiza `[@login]({profile_url})` no lugar do nome de exibição. A resolução é best-effort e nunca bloqueia a release — um nome que não puder ser mapeado (sem token, offline, endereço privado, ou uma forge sem perfis simples como o Azure DevOps) mantém o nome de exibição puro. Os acertos ficam em cache em `~/.gitpr/cache/contributors.json` (`email → login`); apenas os acertos são gravados, então uma execução limitada por rate limit tenta de novo na próxima release.

Sem contexto de link da forge — sem remote `origin`, ou um remote cujo host não é uma das forges suportadas — a seção degrada para texto puro: os hashes ficam sem link e a data e o número do PR permanecem. Uma seção nunca é perdida por falha de link.

A seção é prefixada ao `CHANGELOG.md` — o arquivo nunca é reescrito do zero e as seções anteriores são preservadas. Quando uma seção `## [x.y.z]` da mesma versão já existe, o comando aborta com código de saída 1 (veja a Seção 6, Modo JSON e Idempotência); nunca duplica e nunca sobrescreve em silêncio.

### 3.3 Arquivos Gravados

| Artefato | Caminho | Observações |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Raiz do repositório por padrão — a exceção deliberada à convenção de `.gitpr/reports/`, porque é um arquivo público e commitável. Substitua com `GITPR_RELEASE_CHANGELOG_PATH` (caminhos relativos resolvidos a partir da raiz do repositório) |
| **Artefato de release notes** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Gravado em toda execução markdown, best-effort: uma falha de gravação apenas avisa e nunca derruba o comando. Template de nome via `OUTPUT_FILE_NAME_RELEASE` |
| **Prévia no terminal** | — | Impressa após salvar, até 40 linhas |
| **Cache de contribuidores** | `~/.gitpr/cache/contributors.json` | Mapa `email → login` compartilhado por todos os repositórios; gravado apenas em acertos, best-effort (uma falha de gravação significa apenas que a próxima execução resolve de novo) |

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

O `--format json` é stdout-only, ideal para scripts e CI: não escreve nada (sem atualização do `CHANGELOG.md`, sem artefato da execução, sem download de skill), não publica nada e nunca pergunta (a confirmação de versão é pulada). O stream do stdout permanece limpo — os avisos viajam dentro do payload JSON. A saída segue o resultado da release: `version`, `previous_version` (a versão lida do changelog), `previous_tag` (a origem do intervalo resolvida, que é um hash de commit quando a âncora veio de uma seção), `generated_at`, `summary`, `sections` (uma lista de commits classificados por categoria), `breaking_changes`, `contributors`, `markdown` e `warnings`.

```bash
gitpr release --format json
```

### 6.2 Seção Existente e `--force`

A gravação do changelog é idempotente por versão: quando a seção `## [x.y.z]` da versão alvo já existe, o comando aborta com código de saída 1 sem alterar o arquivo — nunca duplica conteúdo e nunca o sobrescreve em silêncio. O `--force` regenera e substitui essa seção **por inteiro**, do seu cabeçalho até o próximo cabeçalho de versão, mantendo as seções vizinhas intactas (`🔄 Existing section for version {version} regenerated.`); sem seção existente, o `--force` é uma simples adição.

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
