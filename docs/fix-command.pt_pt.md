# Documentação Técnica: Comando Fix (gitpr fix)

O `gitpr fix` transforma os apontamentos da última revisão de código em patches que lê antes de tocarem na sua árvore. Uma única execução resolve a revisão mais recente do repositório e da branch atuais, pede à IA o menor diff unificado que corrige cada problema assinalado pela revisão, classifica cada patch pela confiança que merece e — só quando lhe é dito — grava-o na árvore de trabalho e regista-o para que possa ser desfeito. Ler é a predefinição: sem argumentos o comando lista os candidatos e não grava nada, um único apontamento é apresentado como dry-run, e gravar exige `--apply`.

---

## 1. Visão Geral

O subcomando é uma adição à CLI, não uma alteração a ela: todas as opções legadas mantêm o seu significado e o `--force` aqui pertence ao espaço de nomes do `gitpr fix` (no `gitpr release` significa "regenerar uma secção de versão existente"). Todo o fluxo é local — nada é commitado, nada é enviado com push e nenhuma branch é criada antes de uma gravação ser confirmada.

### 1.1 Referência de Comando — `gitpr fix`

Todas as opções do subcomando, como apresentadas por `gitpr fix -h` (ou `--help`):

```bash
gitpr fix                      # lista os candidatos da última revisão
gitpr fix FIX-001              # dry-run: o diff de um apontamento, nada é gravado
gitpr fix FIX-001 --apply      # grava o patch, após uma confirmação
gitpr fix --all-safe --apply   # grava os patches seguros, numa branch nova por padrão
gitpr fix --rollback FIX-001-1a2b3c4d
```

| Opção | Descrição |
| --- | --- |
| **`[<finding-id>]`** | Apontamento tratado pela execução (`FIX-001`). Sem `--apply` é um dry-run; sem id e sem `--all-safe` o comando lista em vez de aplicar |
| **`--list`** | Lista os candidatos de correção da última revisão — é o que o comando faz sem argumentos |
| **`--apply`** | Grava o patch na árvore de trabalho. Sem isso a execução é um dry-run que não toca em nada |
| **`--all-safe`** | Seleciona todos os patches classificados como seguros. Gravá-los ainda exige `--apply` |
| **`--create-branch <name>`** | Cria e muda para esta branch antes de aplicar os patches |
| **`--no-branch`** | Aplica na branch atual mesmo quando a configuração criaria uma |
| **`--yes`** | Salta a confirmação. Nunca dispensa o `--force` |
| **`--force`** | Aplica um patch que não é seguro, após escrever uma frase de confirmação |
| **`--rollback <patch-id>`** | Desfaz um patch aplicado antes, lendo o diff do histórico local |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | Revisão em cache mais recente do repositório e da branch atuais — `gitpr -r` ou `gitpr -f`, nunca a auditoria de ficheiro (`-i`) |
| **Chamada de IA** | Uma chamada por revisão, no modelo avançado do fornecedor configurado, em cache sob `fix/` como qualquer outra chamada do GitPR |
| **Ficheiros gravados** | Nada por omissão. O `--apply` grava na árvore de trabalho e acrescenta a `.gitpr/fix_history.json` |
| **Branch** | Apenas um lote `--all-safe --apply`, e só quando a configuração o pede |
| **Desfazer** | `--rollback <patch-id>` — sem commit, sem stash, sem reset |
| **Código de saída 1** | Sem revisão, sem alterações a corrigir, sem chave de API, id de apontamento desconhecido, patch não seguro sem `--force`, uma branch que não pode ser criada |

---

## 2. Da Revisão aos Apontamentos

### 2.1 A Revisão Que Lê

O `gitpr fix` nunca revê nada por si próprio: consome a última revisão do repositório e da branch atuais a partir da cache de prompts (`~/.gitpr/cache/prompts/review/`). De entre os registos em cache, escolhe o mais recente cujo `repo` e `branch` correspondem e cujo `action_type` é `review` ou `fullreview` — os três modos de revisão partilham essa pasta, e um `filereview` (auditoria de ficheiro, `-i`) é excluído de propósito, porque uma auditoria a um único ficheiro não tem diff de branch para corrigir.

Sem nenhuma revisão registada, o comando para com `❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.` — "não existe revisão" e "a revisão não encontrou nada" nunca podem parecer a mesma coisa.

### 2.2 O Diff É Recalculado

O *texto* da revisão vem da cache; o *diff* é recalculado agora, com a própria função que produziu a revisão: `get_git_diff()` para `review`, `get_git_full_diff()` para `fullreview`, escolhida pelo `action_type` registado. É isso que ancora o patch à árvore que tem à frente hoje, e não à árvore do dia em que a revisão correu. Uma árvore de trabalho sem quaisquer alterações aborta com `❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again.`

### 2.3 Uma Chamada de IA, e os Ids Que Produz

Uma única chamada pede ao modelo o menor diff unificado por apontamento da revisão, devolvendo um objeto JSON por apontamento. Passa pela infraestrutura padrão do GitPR (fornecedor configurado, modelo avançado, saída JSON, tentativa automática) e pela cache MD5 padrão em `~/.gitpr/cache/prompts/fix/` — veja a [documentação de Fornecedores de IA](providers-ia.md).

Os ids são atribuídos pelo gitpr, nunca pelo modelo: `FIX-001`, `FIX-002`, ... pela ordem por que os apontamentos chegaram. Como o prompt é construído a partir da mesma revisão e do mesmo diff, a resposta em cache é reutilizada e **os ids mantêm-se entre execuções** — o id que uma listagem mostrou é o id a que o `--apply` se dirige. Voltar a executar `gitpr -r` produz uma nova revisão, logo um novo prompt, novos apontamentos e novos ids.

Um modelo que responde com prosa em vez do envelope esperado é um resultado normal, não uma falha: a execução reporta `ℹ️ The review raised no fixable findings.` e não grava nada.

| Campo | Significado |
| --- | --- |
| **`finding_id`** | `FIX-001` — atribuído pelo gitpr, pela ordem por que os apontamentos chegaram |
| **`file_path`** | O caminho que o patch toca. O patch é a autoridade; o `file_path` do próprio modelo é o fallback para um apontamento que não tem patch nenhum |
| **`line_start` / `line_end`** | O intervalo de linhas que a revisão assinalou (0 quando o modelo não indicou nenhum) |
| **`severity` / `category`** | Tal como a revisão os declarou (`critical`, `major`, `minor`, `info` / `bug`, `security`, ...) — registados, nunca recalculados |
| **`message`** | O apontamento, no idioma da interface |
| **`confidence`** | `high` / `medium` / `low` conforme declarados pelo modelo; `low` força a classe `experimental` |
| **`diff`** | O diff unificado que corrige o apontamento — o próprio patch |
| **`suggested_test`** | O que o modelo sugere para cobrir a correção |
| **`patch_id`** | `FIX-001-1a2b3c4d` — o id do apontamento mais os primeiros 8 dígitos hexadecimais do MD5 do diff; aquilo a que o `--rollback` se dirige |

---

## 3. Classificação de Segurança

A classificação é determinística e não envolve IA: o mesmo resumo de patch e as mesmas definições produzem sempre o mesmo veredicto, pelo que um patch classificado como `safe` num dry-run continua a ser `safe` quando o `--apply` corre. O `git apply --check` é avaliado primeiro — um patch que não aplica na árvore atual nunca é outra coisa.

| Classe | Critérios | O que desbloqueia |
| --- | --- | --- |
| **`safe`** | Aplica limpo, um ficheiro, um hunk, dentro do limite de linhas alteradas, fora dos caminhos sensíveis, e não remove nenhuma linha que pareça uma chamada | O `--all-safe --apply` pode aplicá-lo em lote |
| **`review_required`** | Aplica limpo, mas pelo menos uma condição de `safe` falhou | O `--apply` nesse apontamento, com uma confirmação |
| **`experimental`** | Não aplica nesta árvore, abrange mais do que um ficheiro, ou o modelo declarou baixa confiança | Nunca em lote. O `--force` com uma frase escrita é a única porta |

### 3.1 Códigos de Motivo

O veredicto traz sempre um motivo — a primeira condição que falhou, por esta ordem:

| Código de motivo | Significado |
| --- | --- |
| `apply_check_failed` | Não aplica na árvore atual |
| `multi_file` | Altera mais de um ficheiro |
| `low_confidence` | A IA declarou baixa confiança nele |
| `excluded_path` | Toca um caminho sensível configurado |
| `multiple_hunks` | Abrange mais de um hunk |
| `too_many_lines` | Altera mais linhas que o limite configurado |
| `removes_call` | Remove uma linha que parece uma chamada |
| `safe` | Nenhuma condição falhou |

O terminal transforma cada código numa frase traduzida; a ferramenta MCP reporta o próprio código, para que quem a invoca possa fazer correspondência com uma string estável.

### 3.2 Notas Sobre os Critérios

Um apontamento que o modelo respondeu sem um patch utilizável continua a tornar-se candidato, classificado como `experimental` com um diff vazio. Descartá-lo esconderia um problema assinalado pela revisão, e o diff vazio é a verdade — o git recusa-o, pelo que nunca pode ser aplicado por acidente.

A heurística de chamadas é deliberadamente crua: qualquer linha removida que corresponda a `\w+` seguido de um parêntese de abertura dispara-a, incluindo um comentário eliminado que apenas mencione `foo()`. Erra por excesso para `review_required`, que é a direção segura para estar errado.

Os caminhos sensíveis têm a ver com *risco* (migrations, workflows, docker, terraform), não com ruído de diff — e é por isso que são uma configuração própria e não são partilhados com a lista de Smart Excludes.

---

## 4. Ler Antes de Escrever

### 4.1 Listar Candidatos

Sem id de apontamento, o `gitpr fix` (ou `gitpr fix --list`) imprime todos os candidatos da última revisão — classe, localização, mensagem e id do patch — e não grava nada:

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

A classe é apresentada a verde (`safe`), amarelo (`review_required`) ou vermelho (`experimental`), e a frase do motivo só aparece para as duas classes não seguras.

### 4.2 Dry-Run — `gitpr fix <id>`

Com um id de apontamento e sem `--apply`, a execução imprime o bloco do candidato, todo o diff unificado com as cores de terminal usadas em todo o projeto, todos os avisos, e fecha com `ℹ️ Dry run — nothing was written. Add --apply to write it.` Nada na árvore é tocado. Quando uma branch seria criada, a execução di-lo (`ℹ️ Branch '{branch}' would be created before the patches are applied.`), e um dry-run `--all-safe` lista ainda os candidatos que deixou de fora, cada um com o id que o traz de volta.

### 4.3 Gravar — `--apply`

Um patch que não seja classificado como `safe` nunca é gravado por um `--apply` simples: a execução imprime o apontamento, a sua classe e o seu motivo, e termina com código de saída 1 (`❌ {finding_id} is {safety} ({reason}) — re-run with --force to apply it anyway.`).

```bash
gitpr fix FIX-001 --apply
gitpr fix --all-safe --apply
gitpr fix FIX-002 --apply --force
```

Para um patch `safe`, a execução pergunta `❓ Apply FIX-001 to the working tree?` (recusar é a predefinição); recusar imprime `❌ Operation cancelled by user.` e deixa a árvore intacta. O `--yes` ou `GITPR_FIX_REQUIRE_CONFIRMATION=false` salta essa pergunta.

O `--force` abre com uma frase escrita em vez de um y/n: a execução imprime a classe e o motivo e pede que a frase `apply FIX-001` seja escrita exatamente (sem espaços nas extremidades, sem distinção de maiúsculas/minúsculas). Uma divergência aborta com `❌ The confirmation phrase does not match. Nothing was applied.` e código de saída 1 — o `--yes` não dispensa esta pergunta. O `--force` em conjunto com `--all-safe` apenas avisa que não tem efeito, já que só os patches seguros são selecionados. O `gitpr fix --apply` sem id de apontamento e sem `--all-safe` avisa (`⚠️ Nothing was selected: name a finding id or add --all-safe.`) e lista os candidatos em vez de aplicar.

Um patch que o git recuse é reportado como falha com a mensagem do próprio git e o lote continua — um candidato que falha ao aplicar não diz nada sobre o seguinte. Nada é registado no histórico por causa disso: o registo existe para desfazer o que foi aplicado, e nada o foi. Cada patch gravado é reportado como `✅ Patch applied: FIX-001-1a2b3c4d (src/core.py)`.

### 4.4 Gestão de Branches

| Situação | Comportamento |
| --- | --- |
| `--all-safe --apply` com `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE=true` | Cria `GITPR_FIX_BRANCH_NAME_TEMPLATE` (predefinição `fix/gitpr-{datetime}`) a partir do `HEAD` atual e aplica o lote aí; a branch original fica intacta |
| `--create-branch <name>` | Cria essa branch em vez disso (em qualquer execução) |
| `--no-branch` | Aplica na branch atual mesmo quando a configuração criaria uma |
| Um único apontamento, ou um dry-run | Nunca cria uma branch |

A branch é criada uma única vez, antes do primeiro patch, e apenas numa execução real. Uma branch que não pode ser criada aborta o lote — continuar aplicaria os patches à branch de que o utilizador estava a tentar sair.

### 4.5 Um Ficheiro Que Já Está Sujo

Quando um patch tem como alvo um ficheiro que já tem alterações não commitadas, a execução avisa exatamente sobre esses ficheiros (`⚠️ These files already have uncommitted changes: ...`) antes de gravar. Avisar sobre todos os ficheiros sujos do repositório dispararia em quase todas as execuções reais; só a sobreposição entre o patch e as alterações pendentes é o caso em que aplicar pode surpreender o utilizador.

---

## 5. Histórico e Rollback

### 5.1 `.gitpr/fix_history.json`

Cada patch aplicado é registado em `<root>/.gitpr/fix_history.json`, **versionado no git** — todo o diff é lá guardado precisamente para que o patch possa ser desfeito sem um commit. O ficheiro é gravado atomicamente (um ficheiro temporário irmão é renomeado por cima dele), pelo que uma gravação interrompida nunca deixa um histórico a meio. A consequência de o versionar é deliberada e conhecida: aplicar uma correção suja um ficheiro versionado, pelo que ele aparece no `gitpr -c` e nas descrições de PR até ser commitado — e é por isso que o `.gitpr/fix_history.json` faz parte da lista de Smart Excludes e fica de fora dos diffs enviados à IA.

| Campo | Significado |
| --- | --- |
| **`patch_id`** | `FIX-001-1a2b3c4d` — aquilo a que o `--rollback` se dirige |
| **`finding_id`** | `FIX-001` |
| **`file_path`** | O ficheiro que a revisão assinalou |
| **`files_changed`** | Todos os caminhos que o diff toca |
| **`safety`** | `safe` / `review_required` / `experimental` no momento em que foi aplicado |
| **`branch`** | A branch em que o patch foi aplicado (`null` quando foi aplicado no local) |
| **`applied_at`** | Data/hora, no formato de cache do projeto |
| **`diff`** | O diff unificado completo, tal e qual |
| **`provenance`** | Fornecedor, modelo, versão do prompt, versão do gitpr, data/hora de geração |
| **`rolled_back_at`** | Data/hora depois de ser desfeito, caso contrário `null` |

### 5.2 `--rollback <patch-id>`

O rollback lê o diff guardado e reaplica-o com `git apply --reverse` — sem commit, sem stash, sem reset, e sem depender de a árvore de trabalho ainda corresponder ao que foi aplicado. O próprio git verifica a reversão contra o ficheiro: se a árvore avançou, a reversão falha, o erro é reportado e nenhum ficheiro fica a meio. Em caso de sucesso, a execução imprime `ℹ️ Undone patch {patch_id}: {files} restored.` e marca a entrada como desfeita.

| Recusa | Mensagem |
| --- | --- |
| Não existe esse id de patch neste repositório | `❌ No applied patch with id '{patch_id}' was recorded here.` |
| Já desfeito | `❌ Patch '{patch_id}' was already rolled back at {when}.` — desfazer duas vezes é um erro, não uma não-operação |
| Aplicado noutra branch | `❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.` — o ficheiro a restaurar não está aqui |
| A árvore avançou de forma incompatível | `❌ Could not undo patch '{patch_id}': {error}` — a mensagem do próprio git, sem nenhum ficheiro deixado a meio |

O `--rollback` não aceita id de apontamento e não pode ser combinado com `--apply` nem `--all-safe`.

---

## 6. Template de Skill — `.gitpr.fix.md`

A chamada que produz os apontamentos usa o ficheiro `.gitpr.fix.md` como instrução de sistema da IA (persona: **Senior Software Engineer**, que transforma a revisão em patches mínimos). O template é descarregado pelo `gitpr --skill` — sensível ao idioma (`gitpr.fix.md` para inglês, `gitpr.fix.pt_br.md` para PT-BR) e nunca substituindo um ficheiro local existente. Sem ele, é usada a persona incorporada.

O template enuncia o contrato de que o pipeline depende: o patch é a fonte de verdade, um hunk num ficheiro, nunca reformatar código não tocado, nunca eliminar uma chamada ou guarda existente, declarar uma `confidence` honesta, e deixar o `diff` vazio quando o apontamento precisa de uma decisão humana. Edite-o localmente para alterar a forma como os patches são escritos; o prompt é construído a partir dele, pelo que uma alteração produz um novo prompt e uma nova chamada de IA. Veja a [documentação de Skills e Templates](skill-template.md) para o mecanismo geral.

---

## 7. Integração MCP

O `list_fix_candidates` é a 13.ª ferramenta MCP e é **apenas de leitura**: reporta o que o `gitpr fix` poderia aplicar, patch incluído, e nunca grava na árvore de trabalho. O argumento opcional `finding_id` restringe a resposta a um único apontamento.

```json
{"status": "success", "finding_count": 2, "candidates": [ ... ]}
```

Cada candidato transporta `finding_id`, `patch_id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`, `safety`, `safety_reason` (o código estável, não uma frase), `confidence`, `suggested_test` e `diff`. O estado é `no_data` quando a revisão não assinalou nada que pudesse tornar-se um patch, e `error` com uma `message` quando não há revisão para ler ou o pipeline não consegue correr de todo. Veja a [documentação de Integração MCP](mcp-integration.md).

---

## 8. Variáveis de Ambiente

A configuração do fix é lida do ficheiro global `~/.gitpr/.env` (formato dotenv). Os dois booleanos seguem a convenção de "false desliga": não definido ou qualquer valor diferente de `false` / `0` / `no` / `off` / `n` significa ativado — as predefinições da tabela valem quando a variável não está definida.

| Variável | Valor predefinido | Finalidade |
| --- | --- | --- |
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | Linhas adicionadas mais removidas que um patch pode ter e continuar a ser `safe`; um valor não positivo ou impossível de interpretar recua para `5` |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | Caminhos sensíveis, separados por `;`. Um patch que toque num deles continua a aplicar, mas nunca é `safe` |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | Pede confirmação antes de gravar um patch seguro; `false` salta-a (o `--yes` faz o mesmo para uma execução) |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | O `--all-safe --apply` cria uma branch antes de gravar; o `--no-branch` sobrepõe-se para uma execução |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | Nome dessa branch. Placeholders: `{branch}` (branch atual) e `{datetime}` |

> **Nota:** Consulte também a [documentação de Skills e Templates](skill-template.md) para personalizar os ficheiros de template de IA do GitPR.
