# Documentação Técnica: Revisão de Pull Request Remoto (gitpr review-pr)

`gitpr review-pr <number>` revê um pull request que já se encontra aberto na forge, obtendo o seu diff diretamente a partir da API. A branch em revisão não necessita de existir na sua máquina — nunca faz checkout dela, nunca faz fetch e nunca altera a sua árvore de trabalho. É o modo concebido para o revisor convidado para o pull request de outra pessoa, onde o código a analisar reside do outro lado da rede.

A revisão em si não é um segundo motor: é o `gitpr -r` com o diff proveniente de outra origem. A mesma chamada de IA, a mesma skill `.gitpr.review.md`, as mesmas regras de linter, o mesmo ficheiro de relatório e a mesma cache — razão pela qual uma revisão remota e uma revisão local do mesmo diff são interpretadas de forma idêntica.

---

## 1. Visão Geral

O subcomando constitui uma adição à CLI, não uma alteração: todas as opções legadas mantêm o seu comportamento e os fluxos locais (`gitpr -r`, `gitpr -f`, `gitpr fix`) permanecem inalterados. A leitura é a predefinição — sem quaisquer opções, a forge é apenas *lida* e nada é publicado em local algum.

### 1.1 Referência de Comandos — `gitpr review-pr`

Todas as opções do subcomando, tal como apresentadas por `gitpr review-pr -h` (ou `--help`):

```bash
gitpr review-pr 123                    # rever o pull request e gravar o .txt
gitpr review-pr 123 --provider deepseek  # rever com um motor de IA específico
gitpr review-pr 123 --post-comment     # publicar também a revisão no pull request
```

| Opção | Descrição |
| --- | --- |
| **`<number>`** | O número do pull request tal como apresentado na forge (`123`). Obrigatório e inteiro — um argumento não numérico constitui erro de utilização |
| **`--provider <name>`** | Força o motor de IA para esta execução (`gemini`, `deepseek` ou `ollama`). Sem ela, é utilizado o padrão configurado |
| **`--post-comment`** | Publica a revisão sob a forma de comentário no pull request. **Sem esta opção, a forge nunca é alterada** |

| Característica | Descrição |
| --- | --- |
| **Origem dos dados** | O diff fornecido pela API da forge para esse pull request — nunca a sua árvore de trabalho |
| **Forge** | A configurada via `gitpr --init` (GitHub, GitLab, Bitbucket). O Azure DevOps é recusado — ver §3 |
| **Chamada de IA** | Uma chamada, no modelo avançado do fornecedor configurado, com cache em `review/` tal como qualquer outra chamada GitPR |
| **Ficheiros gravados** | `{branch}_{datetime}_PR_REVIEW.txt` na pasta de relatórios (`OUTPUT_FILE_NAME_REVIEW`) |
| **Publicação** | Nenhuma, exceto quando `--post-comment` for fornecido |
| **Árvore local** | Nunca é lida, nunca verificada quanto a ficheiros unstaged e nunca modificada — sem checkout, sem fetch, sem alternância de branch |
| **Código de saída 1** | Nenhuma forge configurada, forge sem diff compatível, pull request inexistente ou fechado, diff vazio ou totalmente filtrado, API inacessível, chave de IA ausente |

---

## 2. O Que É uma Revisão Remota

### 2.1 O Diff É Obtido a Partir da API

A forge é consultada inicialmente para obter os metadados do pull request e, subsequentemente, o respetivo diff:

| Passo | O que estabelece |
| --- | --- |
| `get_pull_request` | Confirma que o número existe, em que estado se encontra e que branches interliga |
| `get_pull_request_diff` | O diff unificado a rever |

A resolução direta do número permite distinguir "não existe" de "foi integrado na semana passada": a listagem de pull requests devolve apenas os que estão abertos, pelo que um número em falta poderia significar qualquer um dos casos. Os metadados fornecem igualmente os nomes das duas branches necessárias ao relatório.

O pedido de metadados não é meramente decorativo — é o que impede que um número desatualizado consuma tokens inutilmente (§4.2).

### 2.2 O Diff É Normalizado

Um diff que nunca transitou pelo git chega na estrutura exata em que a forge o enviou. Três etapas são executadas antes de a IA o receber:

| Passo | Motivo |
| --- | --- |
| **Finais de linha unificados para LF** | GitLab e Bitbucket fornecem CRLF em branches criadas em Windows, e o analisador divide em `^diff --git a/`, o que falharia com um `\r` residual |
| **O conteúdo é validado como diff real** | Um fornecedor que declare fornecer diffs mas responda com texto simples é intercetado aqui, evitando ser analisado como se fosse código |
| **Aplicação de smart excludes** | Os lockfiles e recursos minificados são filtrados do diff *revisto*, e não de um diff local (§2.3) |

### 2.3 Smart Excludes em Execução Python

Cada diff local tem os seus smart excludes aplicados pelo próprio git, através de pathspecs `:(exclude)`. Um diff obtido via API nunca passa pelo git; consequentemente, os mesmos padrões são aplicados em Python, secção a secção de cada ficheiro, emitindo-se um aviso com os ficheiros omitidos:

```text
⚠️  3 file(s) skipped by the smart excludes: package-lock.json, poetry.lock, dist/app.min.js
```

A lista de padrões coincide com a utilizada nos fluxos locais (`~/.gitpr/conf/gitpr.smart-excludes.json`), e a variável `GITPR_SKIP_SMART_EXCLUDES` também a desativa aqui. Um pull request cujos ficheiros sejam todos lockfiles não tem nada para rever, alertando para esse facto em vez de submeter um diff vazio ao modelo.

### 2.4 Isolamento em Cache Distinto da Revisão Local

A chave MD5 da cache é calculada com base no prompt, e este depende do diff. Assim, uma revisão remota de uma branch que coincidentemente estivesse em checkout local produziria um prompt idêntico em bytes, sendo satisfeita pela cache local pré-existente. Para evitar isso, o fluxo remoto acrescenta um identificador de âmbito à chave de cache:

```text
::diff-source::pr-123
```

Este âmbito é adicionado **estritamente** à chave de cache — nunca ao texto submetido à IA. O impacto para instalações existentes é nulo: os fluxos locais transmitem um âmbito vazio, mantendo as suas chaves byte a byte idênticas e preservando todas as entradas de cache anteriores.

### 2.5 O Diff Revisto É Registado

A revisão é armazenada em cache juntamente com o diff que lhe deu origem, o que permite ao `gitpr fix` corrigir a revisão exata que foi analisada em vez de recalcular um diff da sua árvore. Numa revisão remota, isto é indispensável, uma vez que a branch pode nem sequer existir localmente. Consulte a [documentação do Comando Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=pt_pt) para perceber como esta informação é recuperada.

O registo é associado ao repositório e à branch **em que se encontra** — os mesmos campos que cada revisão em cache transporta, permitindo ao `gitpr fix` localizá-la. As branches próprias do pull request são registadas no interior da entrada (como o `{branch}` do nome do relatório e na origem do diff), mas não servem de chave de pesquisa: rever o PR #123 enquanto está em `develop` arquiva a revisão sob `develop`.

---

## 3. Forges Compatíveis com Revisão

Uma revisão necessita de um diff unificado, formato que nem todas as forges disponibilizam.

| Forge | Revisão Remota | Motivo |
| --- | --- | --- |
| **GitHub** | Sim | `GET /repos/{owner}/{repo}/pulls/{n}/files` com cabeçalho `Accept: application/vnd.github.diff` |
| **GitLab** | Sim | `changes[].diff` por ficheiro, com cabeçalhos de ficheiro sintetizados (§3.1) |
| **Bitbucket** | Sim | `GET .../pullrequests/{n}/diff` |
| **Azure DevOps** | **Não** | A sua API devolve uma lista de ficheiros alterados com contagem de linhas, não um diff unificado. Recusado antes de qualquer chamada de rede, com mensagem a sugerir a revisão local |

Esta compatibilidade é declarada pelo próprio fornecedor (`supports_reviewable_diff` no `ScmProvider`), pelo que uma nova forge introduzida no futuro define o seu suporte de forma explícita. Por detrás deste indicador existe uma segunda validação: o conteúdo transferido é verificado quanto à estrutura real de diff, detetando fornecedores que declarem capacidade mas respondam com sumários de ficheiros (§2.2).

### 3.1 GitLab: Síntese de Cabeçalhos de Ficheiro

A API do GitLab devolve o campo `diff` de cada ficheiro alterado como um bloco isolado, contendo a identificação do ficheiro em campos separados `old_path` / `new_path`. Sem tratamento prévio, a revisão receberia blocos anónimos — a IA não saberia a que ficheiro correspondia a alteração, inviabilizando tanto os smart excludes como a segmentação em lotes, já que ambos dependem da linha `diff --git a/…`. O fornecedor reconstrói esse cabeçalho antes de cada bloco:

```diff
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
```

O GitLab também assinala quando um diff foi truncado por ultrapassar o limite de tamanho da API (`overflow: true`). Um diff truncado é incompleto e, por isso, é recusado de imediato com uma instrução a sugerir a revisão local do merge request, evitando uma análise parcial apresentada como se fosse total.

---

## 4. O Relatório, Avisos e Falhas

### 4.1 O Relatório

A saída produz o mesmo ficheiro que a revisão local gera, através do mesmo módulo de formatação — bloco de linter no topo, revisão por IA em baixo — com uma distinção no nome: o marcador `{branch}` assume a branch de **origem** do pull request, normalizada para o sistema de ficheiros (`feature/login` torna-se `feature-login`), visto que o relatório pertence à revisão examinada e não à branch em que tem o checkout feito. Um pull request sem nome de branch recorre a `pr-123`.

```text
✅ Code Review successfully generated: 'feature-login_20260917143210_PR_REVIEW.txt'
```

Mais nenhum conteúdo é impresso: a revisão nunca é apresentada no terminal, exatamente como nos fluxos locais. O caminho do relatório é configurado por `OUTPUT_FILE_NAME_REVIEW`, a mesma variável da revisão local — o modo remoto não introduz novas definições.

### 4.2 Recusas Sem Custos de Quota

Todas as situações resolúveis pelo utilizador são intercetadas **antes** da invocação da IA, garantindo que um identificador incorreto, um pull request fechado ou um token inválido não gastam tokens:

| Situação | Mensagem |
| --- | --- |
| A forge não fornece um diff compatível | `{provider} does not serve a reviewable diff: … Review this pull request locally, or use a forge that serves diffs.` |
| O número não existe | `Pull request #123 was not found in {repo}.` |
| O token não tem permissões de leitura (401/403) | `No permission to read pull request #123 in {repo}. Check the token configured for {provider} (gitpr --init).` |
| Está fechado ou integrado | `Pull request #123 is not open (state: closed). Only open pull requests can be reviewed.` |
| O diff regressou vazio | `Pull request #123 has no diff to review.` |
| Regressou como sumário de ficheiros | `{provider} returned a file summary instead of a diff for pull request #123. It cannot be reviewed.` |
| Todos os ficheiros foram filtrados pelos smart excludes | `Every file of pull request #123 matches the smart excludes — nothing left to review.` |
| O modelo não devolveu resposta utilizável | `The AI returned no review for pull request #123.` |

Os quatro estados de abertura entre as forges suportadas — GitHub `open`, GitLab `opened`, Azure `active`, Bitbucket `OPEN` — são avaliados sem distinção de maiúsculas/minúsculas. Um fornecedor que não reporte qualquer estado é aceite, evitando bloqueios sobre propriedades não garantidas.

### 4.3 Avisos

Os avisos cobrem ocorrências relevantes que não inviabilizam a execução. São apresentados antes do relatório e, quando combinado com `--post-comment`, incluídos no comentário publicado — um leitor no pull request tem direito a saber se a revisão ignorou lockfiles.

| Aviso | Quando ocorre |
| --- | --- |
| `{count} file(s) skipped by the smart excludes: {files}` | O filtro omitiu pelo menos um ficheiro |
| `Large diff: processed in {count} batches (map-reduce).` | O diff tem dimensão suficiente para exigir divisão em lotes |

A contagem de lotes é obtida diretamente do módulo de segmentação e não através de captura da saída de terminal, garantindo compatibilidade com ferramentas MCP. Caso o analisador não forneça a contagem, a execução prossegue normalmente: o aviso é informativo e nunca causa a interrupção do processo.

### 4.4 Uma Execução com Falha Não Grava Ficheiros

Qualquer erro termina a execução com código de saída 1, apresenta a razão no stderr e **não grava nenhum relatório** — a presença de um ficheiro `.txt` em disco assegura que existe uma revisão válida, impedindo que uma falha seja interpretada como ausência de problemas. O comando também não repete a chamada: as exceções são levantadas antes do motor de IA, evitando custos adicionais.

---

## 5. Publicação — `--post-comment`

Com a opção `--post-comment`, a revisão é colocada como comentário no próprio pull request. Trata-se de um comentário único, criado após o sucesso da revisão e a execução do linter, sendo **sempre um novo comentário** — revisões anteriores efetuadas pela ferramenta são preservadas, evitando a sobreposição de comentários sobre os quais possam existir respostas.

O corpo reproduz o conteúdo do relatório acompanhado de um rodapé:

```markdown
## 🚨 Local Static Analysis Alerts (YAML Rules)

- 🚨 console.log usage detected in app.js (Line 42)

---

## 🤖 AI Code Review

…

---

*Automated review by GitPR 1.1.0 — AI provider: Gemini. AI-generated content: verify before acting on it.*
```

O rodapé assegura a transparência no pull request de **terceiros**: qualquer leitor que não tenha executado a CLI tem assim forma de saber que o texto foi elaborado por IA. Os alertas são gerados exatamente pela mesma função que monta o `.txt`, garantindo absoluta coerência entre o ficheiro e o comentário.

Nenhum SHA de commit é incluído. A forge não fornece essa informação na resposta do diff, e criar uma referência artificial num comentário público traria menor fiabilidade do que omiti-la.

Se a revisão falhar, nada é publicado — o comentário só é gerado a jusante de uma revisão bem-sucedida. Caso a publicação do comentário falhe (por exemplo, um token com permissão de leitura mas sem escrita), o erro surge identificado como falha da forge e a CLI termina com código 1: a revisão foi gerada, mas não foi publicada.

---

## 6. Template de Skill — `.gitpr.review.md`

A revisão remota recorre à mesma instrução de sistema da revisão local: `.gitpr.review.md` (persona e foco da análise), obtida via `gitpr --skill` — respeitando o idioma ativo e sem substituir ficheiros locais pré-existentes. Não existe uma skill específica para o modo remoto; se a interpretação variasse consoante a proveniência do diff, perder-se-ia a coerência do motor unificado.

---

## 7. Integração MCP

`review_remote_pr` é a 14ª ferramenta MCP e funciona em modo **estritamente de leitura**: analisa um pull request aberto e devolve a revisão e os alertas de linter, sem capacidade de publicação. Não disponibiliza o parâmetro `post_comment`, por conceção — uma ferramenta invocada autonomamente por um agente não deve poder escrever diretamente no pull request de outra pessoa.

```json
{"status": "success", "pr_number": 123, "pr_url": "…", "head_branch": "feature/login",
 "base_branch": "main", "origin": "remote_pr", "linter": {…}, "warnings": [], "review": "…"}
```

Ao contrário da CLI, esta ferramenta não grava nenhum ficheiro `.txt` — as ferramentas MCP não geram artefactos em disco — e resolve a forge autonomamente. Num repositório sem forge configurada, responde com um erro JSON indicando a necessidade de `gitpr --init` em vez de mensagens de terminal. O estado devolvido é `error` com o respetivo `message` para todas as recusas detalhadas na §4.2. Consulte a [documentação de Integração MCP](https://gitpr.natanfiuza.dev.br/docs/mcp-integration?lang=pt_pt).

---

## 8. Variáveis de Ambiente

A revisão remota **não introduz qualquer variável de configuração nova**. Utiliza os mesmos parâmetros já suportados pela revisão local:

| Variável | Finalidade |
| --- | --- |
| `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN` / `GITPR_SCM_TOKEN_ENCRYPTED` | A forge e respetivo token, configurados por `gitpr --init` |
| `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` | Parâmetros adicionais da forge (GitLab auto-hospedado, Azure, Bitbucket) |
| `OUTPUT_FILE_NAME_REVIEW` | Nome do ficheiro de relatório (padrão `{branch}_{datetime}_PR_REVIEW.txt`) |
| `DEFAULT_AI_PROVIDER` | Motor de IA utilizado quando `--provider` não for fornecido |
| `GITPR_SKIP_SMART_EXCLUDES` | Desativa o filtro de smart excludes, tanto em modo local como remoto |

> **Nota:** Consulte também a [documentação de Code Review com IA](https://gitpr.natanfiuza.dev.br/docs/code-review-ia?lang=pt_pt) para conhecer os restantes modos de revisão e a [documentação do Comando Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=pt_pt) para compreender o consumo do diff registado.
