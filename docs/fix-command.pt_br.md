# Documentação Técnica: Comando de Correção (gitpr fix)

`gitpr fix` transforma os apontamentos da última revisão de código em patches que você lê antes de eles tocarem na sua árvore de trabalho. Uma única execução resolve a revisão mais recente do repositório e da branch atuais, pede à IA o menor diff unificado que corrija cada problema apontado pela revisão, classifica cada patch pelo quanto se pode confiar nele e — somente quando instruído — grava-o na árvore de trabalho e o registra, para que possa ser desfeito. Ler é o padrão: sem argumentos o comando lista os candidatos e não grava nada, um único apontamento é exibido como dry-run, e gravar exige `--apply`.

---

## 1. Visão Geral

O subcomando é uma adição à CLI, não uma mudança nela: toda opção legada mantém seu significado, e o `--force` aqui tem escopo próprio sob `gitpr fix` (em `gitpr release` ele significa "regerar uma seção de versão existente"). Todo o fluxo é local — nada é commitado, nada é enviado, nenhuma branch é criada antes que uma gravação seja confirmada.

### 1.1 Referência de Comando — `gitpr fix`

Todas as opções do subcomando, como mostrado por `gitpr fix -h` (ou `--help`):

```bash
gitpr fix                      # lista os candidatos da última revisão
gitpr fix FIX-001              # dry-run: o diff de um apontamento, nada é gravado
gitpr fix FIX-001 --apply      # grava o patch, após uma confirmação
gitpr fix --all-safe --apply   # grava todo patch seguro, em uma branch nova por padrão
gitpr fix --rollback FIX-001-1a2b3c4d
```

| Opção | Descrição |
| --- | --- |
| **`[<finding-id>]`** | Apontamento tratado pela execução (`FIX-001`). Sem `--apply` é um dry-run; sem id e sem `--all-safe` o comando apenas lista |
| **`--list`** | Lista os candidatos de correção da última revisão — é o que o comando faz sem argumentos |
| **`--apply`** | Grava o patch na árvore de trabalho. Sem isso a execução é um dry-run que não toca em nada |
| **`--all-safe`** | Seleciona todos os patches classificados como seguros. Gravá-los ainda exige `--apply` |
| **`--create-branch <name>`** | Cria e muda para esta branch antes de aplicar os patches |
| **`--no-branch`** | Aplica na branch atual mesmo quando a configuração criaria uma nova branch |
| **`--yes`** | Pula a confirmação. Nunca dispensa o `--force` |
| **`--force`** | Aplica um patch que não é seguro, após digitar uma frase de confirmação |
| **`--rollback <patch-id>`** | Desfaz um patch aplicado antes, lendo o diff do histórico local |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Revisão mais recente em cache do repositório e da branch atuais — `gitpr -r` ou `gitpr -f`, nunca a auditoria de arquivo (`-i`) |
| **Chamada de IA** | Uma chamada por revisão, no modelo avançado do provedor configurado, com cache em `fix/` como qualquer outra chamada do GitPR |
| **Arquivos gravados** | Nada por padrão. O `--apply` grava na árvore de trabalho e acrescenta ao `.gitpr/fix_history.json` |
| **Branch** | Apenas um lote `--all-safe --apply`, e só quando a configuração pedir |
| **Desfazer** | `--rollback <patch-id>` — sem commit, sem stash, sem reset |
| **Código de saída 1** | Nenhuma revisão, nenhuma alteração a corrigir, nenhuma chave de API, id de apontamento desconhecido, patch inseguro sem `--force`, branch que não pode ser criada |

---

## 2. Da Revisão aos Apontamentos

### 2.1 A Revisão que Ele Lê

`gitpr fix` nunca revisa nada por conta própria: ele consome a última revisão do repositório e da branch atuais a partir do cache de prompts (`~/.gitpr/cache/prompts/review/`). Entre os registros em cache, ele pega o mais recente cujo `repo` e `branch` correspondem e cujo `action_type` é `review` ou `fullreview` — os três modos de revisão compartilham essa pasta, e um `filereview` (auditoria de arquivo, `-i`) é excluído de propósito, porque uma auditoria de um único arquivo não tem diff de branch a corrigir.

Sem revisão registrada, o comando para com `❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.` — "não há revisão" e "a revisão não encontrou nada" nunca podem parecer a mesma coisa.

### 2.2 O Diff É Recalculado

O *texto* da revisão vem do cache; o *diff* é recalculado agora, com a mesma função que produziu a revisão: `get_git_diff()` para `review`, `get_git_full_diff()` para `fullreview`, selecionados pelo `action_type` registrado. É isso que ancora o patch à árvore que está na sua frente hoje, e não à árvore do dia em que a revisão rodou. Uma árvore de trabalho sem nenhuma alteração aborta com `❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again.`

### 2.3 Uma Chamada de IA, e os Ids que Ela Produz

Uma única chamada pede ao modelo o menor diff unificado por apontamento da revisão, retornando um objeto JSON por apontamento. Ela passa pela infraestrutura padrão do GitPR (provedor configurado, modelo avançado, saída JSON, retry) e pelo cache MD5 padrão em `~/.gitpr/cache/prompts/fix/` — veja a [documentação de Provedores de IA](providers-ia.md).

Os ids são atribuídos pelo gitpr, nunca pelo modelo: `FIX-001`, `FIX-002`, ... na ordem em que os apontamentos chegaram. Como o prompt é montado a partir da mesma revisão e do mesmo diff, a resposta em cache é reaproveitada e **os ids permanecem os mesmos entre execuções** — o id que uma listagem mostrou é o id ao qual o `--apply` se refere. Rodar `gitpr -r` de novo produz uma nova revisão, logo um novo prompt, novos apontamentos e novos ids.

Um modelo que responde com prosa em vez do envelope esperado é um desfecho comum, não uma falha: a execução reporta `ℹ️ The review raised no fixable findings.` e não grava nada.

| Campo | Significado |
| --- | --- |
| **`finding_id`** | `FIX-001` — atribuído pelo gitpr, na ordem em que os apontamentos chegaram |
| **`file_path`** | O caminho que o patch toca. O patch é a fonte da verdade; o `file_path` do próprio modelo é o fallback para um apontamento que não tem patch nenhum |
| **`line_start` / `line_end`** | O intervalo de linhas que a revisão apontou (0 quando o modelo não informou nenhum) |
| **`severity` / `category`** | Como a revisão os declarou (`critical`, `major`, `minor`, `info` / `bug`, `security`, ...) — registrados, nunca recalculados |
| **`message`** | O apontamento, no idioma da interface |
| **`confidence`** | `high` / `medium` / `low` conforme declarado pelo modelo; `low` força a classe `experimental` |
| **`diff`** | O diff unificado que corrige o apontamento — o patch em si |
| **`suggested_test`** | O que o modelo sugere para cobrir a correção |
| **`patch_id`** | `FIX-001-1a2b3c4d` — o id do apontamento mais os 8 primeiros dígitos hexadecimais do MD5 do diff; é o id ao qual o `--rollback` se refere |

---

## 3. Classificação de Segurança

A classificação é determinística e não envolve IA: o mesmo resumo de patch e as mesmas configurações sempre produzem o mesmo veredito, então um patch classificado `safe` em um dry-run continua `safe` quando o `--apply` roda. O `git apply --check` é avaliado primeiro — um patch que não aplica na árvore atual nunca é outra coisa.

| Classe | Critérios | O que ela abre |
| --- | --- | --- |
| **`safe`** | Aplica de forma limpa, um arquivo, um hunk, dentro do limite de linhas alteradas, fora dos caminhos sensíveis, e não exclui nenhuma linha que pareça uma chamada | `--all-safe --apply` pode agrupá-lo |
| **`review_required`** | Aplica de forma limpa, mas ao menos uma condição de `safe` falhou | `--apply` naquele apontamento, com uma confirmação |
| **`experimental`** | Não aplica nesta árvore, abrange mais de um arquivo, ou o modelo declarou baixa confiança | Nunca agrupado. `--force` com frase digitada é a única porta |

### 3.1 Códigos de Motivo

O veredito sempre traz um motivo — a primeira condição que disparou, nesta ordem:

| Código de motivo | Significado |
| --- | --- |
| `apply_check_failed` | Não aplica na árvore atual |
| `multi_file` | Altera mais de um arquivo |
| `low_confidence` | A IA declarou baixa confiança nele |
| `excluded_path` | Toca um caminho sensível configurado |
| `multiple_hunks` | Abrange mais de um hunk |
| `too_many_lines` | Altera mais linhas que o limite configurado |
| `removes_call` | Remove uma linha que parece uma chamada |
| `safe` | Nenhuma condição falhou |

O terminal transforma cada código em uma frase traduzida; a ferramenta MCP reporta o próprio código, para que quem a chama possa comparar com uma string estável.

### 3.2 Notas sobre os Critérios

Um apontamento que o modelo respondeu sem um patch utilizável ainda se torna um candidato, classificado `experimental` com diff vazio. Descartá-lo esconderia um problema que a revisão apontou, e o diff vazio é a verdade — o git o recusa, então ele nunca pode ser aplicado por acidente.

A heurística de chamada é deliberadamente crua: qualquer linha removida que case com `\w+` seguido de um parêntese aberto a dispara, inclusive um comentário excluído que apenas mencione `foo()`. Ela erra na direção de `review_required`, que é a direção segura de errar.

Os caminhos sensíveis são sobre *risco* (migrations, workflows, docker, terraform), não sobre ruído de diff — por isso são uma configuração própria e não são compartilhados com a lista de Smart Excludes.

---

## 4. Ler Antes de Gravar

### 4.1 Listando Candidatos

Sem id de apontamento, `gitpr fix` (ou `gitpr fix --list`) imprime todos os candidatos da última revisão — classe, localização, mensagem e id do patch — e não grava nada:

```text
🔎 Fix candidates from the last review:
  FIX-001  [safe]  src/core.py:210
     The retry loop swallows the exception.
     ↳ FIX-001-1a2b3c4d
  FIX-002  [review_required]  src/config.py:88
     The default timeout is duplicated.
     ↳ FIX-002-9f8e7d6c — it changes more lines than the configured limit
ℹ️ Apply one with 'gitpr fix <id> --apply'; the safe ones can be batched with '--all-safe --apply'.
```

A classe é colorida de verde (`safe`), amarelo (`review_required`) ou vermelho (`experimental`), e a frase de motivo só aparece para as duas classes não seguras.

### 4.2 Dry-Run — `gitpr fix <id>`

Com um id de apontamento e sem `--apply`, a execução imprime o bloco do candidato, todo o diff unificado nas cores de terminal usadas em todo o projeto, todos os avisos, e fecha com `ℹ️ Dry run — nothing was written. Add --apply to write it.` Nada na árvore é tocado. Quando uma branch seria criada, a execução diz isso (`ℹ️ Branch '{branch}' would be created before the patches are applied.`), e um dry-run com `--all-safe` lista ainda os candidatos que ficaram de fora, cada um com o id que o traz de volta.

### 4.3 Gravando — `--apply`

Um patch que não é classificado como `safe` nunca é gravado por um `--apply` simples: a execução imprime o apontamento, sua classe e seu motivo, e sai com código 1 (`❌ {finding_id} is {safety} ({reason}) — re-run with --force to apply it anyway.`).

```bash
gitpr fix FIX-001 --apply
gitpr fix --all-safe --apply
gitpr fix FIX-002 --apply --force
```

Para um patch `safe`, a execução pergunta `❓ Apply FIX-001 to the working tree?` (recusar é o padrão); recusar imprime `❌ Operation cancelled by user.` e deixa a árvore intacta. `--yes` ou `GITPR_FIX_REQUIRE_CONFIRMATION=false` pula esse prompt.

O `--force` abre em uma frase digitada em vez de um s/n: a execução imprime a classe e o motivo e pede que a frase `apply FIX-001` seja digitada exatamente (com espaços aparados nas pontas, sem diferenciar maiúsculas de minúsculas). Uma divergência aborta com `❌ The confirmation phrase does not match. Nothing was applied.` e código de saída 1 — o `--yes` não dispensa esse prompt. `--force` junto com `--all-safe` apenas avisa que não tem efeito, já que só patches seguros são selecionados. `gitpr fix --apply` sem id de apontamento e sem `--all-safe` avisa (`⚠️ Nothing was selected: name a finding id or add --all-safe.`) e lista os candidatos em vez disso.

Um patch que o git recusa é reportado como falha com a mensagem do próprio git e o lote continua — um candidato que falha ao aplicar não diz nada sobre o próximo. Nada é registrado no histórico para ele: o registro existe para desfazer o que foi aplicado, e nada foi. Cada patch gravado é reportado como `✅ Patch applied: FIX-001-1a2b3c4d (src/core.py)`.

### 4.4 Tratamento de Branch

| Situação | Comportamento |
| --- | --- |
| `--all-safe --apply` com `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE=true` | Cria `GITPR_FIX_BRANCH_NAME_TEMPLATE` (padrão `fix/gitpr-{datetime}`) a partir do `HEAD` atual e aplica o lote nela; a branch original fica intacta |
| `--create-branch <name>` | Cria essa branch em vez disso (qualquer execução) |
| `--no-branch` | Aplica na branch atual mesmo quando a configuração criaria uma nova branch |
| Um único apontamento, ou um dry-run | Nunca cria branch |

A branch é criada uma vez, antes do primeiro patch, e só em uma execução real. Uma branch que não pode ser criada aborta o lote — continuar aplicaria os patches na branch que o usuário estava tentando deixar.

### 4.5 Um Arquivo que Já Está Sujo

Quando um patch tem como alvo um arquivo que já tem alterações não commitadas, a execução avisa exatamente sobre esses arquivos (`⚠️ These files already have uncommitted changes: ...`) antes de gravar. Avisar sobre todos os arquivos sujos do repositório dispararia em quase toda execução real; só a sobreposição entre o patch e as alterações pendentes é o caso em que aplicar pode surpreender o usuário.

---

## 5. Histórico e Rollback

### 5.1 `.gitpr/fix_history.json`

Todo patch aplicado é registrado em `<root>/.gitpr/fix_history.json`, **rastreado pelo git** — o diff inteiro é armazenado ali justamente para que o patch possa ser desfeito sem um commit. O arquivo é gravado de forma atômica (um arquivo temporário irmão renomeado por cima dele), então uma gravação interrompida nunca deixa um histórico pela metade. A consequência de rastreá-lo é deliberada e conhecida: aplicar uma correção suja um arquivo rastreado, então ele aparece em `gitpr -c` e nas descrições de PR até ser commitado — por isso `.gitpr/fix_history.json` acompanha a lista de Smart Excludes e fica fora dos diffs da IA.

| Campo | Significado |
| --- | --- |
| **`patch_id`** | `FIX-001-1a2b3c4d` — é o id ao qual o `--rollback` se refere |
| **`finding_id`** | `FIX-001` |
| **`file_path`** | O arquivo que a revisão apontou |
| **`files_changed`** | Todo caminho que o diff toca |
| **`safety`** | `safe` / `review_required` / `experimental` no momento em que foi aplicado |
| **`branch`** | A branch na qual o patch foi aplicado (`null` quando foi aplicado no lugar) |
| **`applied_at`** | Timestamp, no formato de cache do projeto |
| **`diff`** | O diff unificado completo, literalmente |
| **`provenance`** | Provedor, modelo, versão do prompt, versão do gitpr, timestamp de geração |
| **`rolled_back_at`** | Timestamp depois de desfeito, `null` caso contrário |

### 5.2 `--rollback <patch-id>`

O rollback lê o diff armazenado e o reproduz com `git apply --reverse` — sem commit, sem stash, sem reset e sem depender de a árvore de trabalho ainda corresponder ao que foi aplicado. O próprio git verifica a reversão contra o arquivo: se a árvore avançou, a reversão falha, o erro é reportado e nenhum arquivo fica pela metade. Em caso de sucesso, a execução imprime `ℹ️ Undone patch {patch_id}: {files} restored.` e marca a entrada como desfeita.

| Recusa | Mensagem |
| --- | --- |
| Nenhum patch com esse id neste repositório | `❌ No applied patch with id '{patch_id}' was recorded here.` |
| Já desfeito | `❌ Patch '{patch_id}' was already rolled back at {when}.` — desfazer duas vezes é um erro, não uma operação sem efeito |
| Aplicado em outra branch | `❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.` — o arquivo a restaurar não está aqui |
| A árvore avançou de forma incompatível | `❌ Could not undo patch '{patch_id}': {error}` — a mensagem do próprio git, sem nenhum arquivo deixado pela metade |

O `--rollback` não aceita id de apontamento e não pode ser combinado com `--apply` nem `--all-safe`.

---

## 6. Template de Skill — `.gitpr.fix.md`

A chamada de apontamentos usa o arquivo `.gitpr.fix.md` como system instruction da IA (persona: **Engenheiro de Software Sênior**, normalizando a revisão em patches mínimos). O template é baixado por `gitpr --skill` — respeitando o idioma (`gitpr.fix.md` para inglês, `gitpr.fix.pt_br.md` para PT-BR) e nunca sobrescrevendo um arquivo local existente. Sem ele, a persona embutida é usada.

O template enuncia o contrato do qual o pipeline depende: o patch é a fonte da verdade, um hunk em um arquivo, nunca reformatar código não tocado, nunca excluir uma chamada ou uma guarda existente, declarar uma `confidence` honesta e deixar o `diff` vazio quando o apontamento exigir uma decisão humana. Edite-o localmente para mudar como os patches são escritos; o prompt é montado a partir dele, então uma alteração produz um novo prompt e uma nova chamada de IA. Veja a [documentação de Skills e Templates](skill-template.md) para o mecanismo geral.

---

## 7. Integração MCP

`list_fix_candidates` é a 13ª ferramenta MCP e é **somente leitura**: ela reporta o que o `gitpr fix` poderia aplicar, patch incluído, e nunca grava na árvore de trabalho. O argumento opcional `finding_id` restringe a resposta a um apontamento.

```json
{"status": "success", "finding_count": 2, "candidates": [ ... ]}
```

Cada candidato carrega `finding_id`, `patch_id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`, `safety`, `safety_reason` (o código estável, não uma frase), `confidence`, `suggested_test` e `diff`. O status é `no_data` quando a revisão não apontou nada que pudesse virar um patch, e `error` com uma `message` quando não há revisão para ler ou o pipeline não consegue rodar de jeito nenhum. Veja a [documentação de Integração MCP](mcp-integration.md).

---

## 8. Variáveis de Ambiente

A configuração do fix é lida do arquivo global `~/.gitpr/.env` (formato dotenv). Os dois booleanos seguem a convenção de "false desliga": não definido ou qualquer valor diferente de `false` / `0` / `no` / `off` / `n` significa ativado — os padrões da tabela valem quando a variável não está definida.

| Variável | Valor padrão | Finalidade |
| --- | --- | --- |
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | Linhas adicionadas + removidas que um patch pode ter e ainda ser classificado como `safe`; um valor não positivo ou não interpretável cai para `5` |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | Caminhos sensíveis, separados por `;`. Um patch que toca um deles ainda aplica, mas nunca é `safe` |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | Pede uma confirmação antes de gravar um patch seguro; `false` a dispensa (`--yes` faz o mesmo para uma execução) |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | `--all-safe --apply` cria uma branch antes de gravar; `--no-branch` sobrepõe isso para uma execução |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | Nome dessa branch. Placeholders: `{branch}` (branch atual) e `{datetime}` |

> **Nota:** Consulte também a [documentação de Skills e Templates](skill-template.md) para personalizar os arquivos de template de IA do GitPR.
