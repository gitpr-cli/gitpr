# Documentação Técnica: Comando de Divisão (gitpr split)

`gitpr split` lê uma árvore de trabalho que contém várias preocupações não relacionadas entre si, agrupa os hunks por intenção lógica com recurso a IA e propõe um commit atómico por preocupação — cada um com uma mensagem gerada exclusivamente para esse subconjunto de alterações. A leitura é o comportamento predefinido e a escrita é opt-in: sem argumentos o comando imprime o plano e propõe aplicá-lo, `--dry-run` imprime e termina sem nunca perguntar, e `--apply` confirma uma vez, preparando no índice (*staging*) e efetuando o commit grupo a grupo.

O problema que resolve é aquele que qualquer programador reconhece: uma correção de erro, uma refatorização e um ajuste de configuração desenvolvidos na mesma tarde, agora inseparáveis num único `git diff`, onde as únicas alternativas seriam `git add -p` manual ou uma mensagem de commit que enumera três assuntos distintos.

---

## 1. Visão Geral

O subcomando é uma adição à CLI, e não uma alteração ao seu comportamento base: todas as opções legadas mantêm o respetivo significado, e todo o fluxo é estritamente local — nenhum `git commit` é criado até que `--apply` seja confirmado, nada é enviado para o repositório remoto e nenhuma branch é criada.

### 1.1 Referência do Comando — `gitpr split`

Todas as opções do subcomando, conforme apresentado por `gitpr split -h` (ou `--help`):

```bash
gitpr split                    # imprime o plano e depois propõe a sua aplicação
gitpr split --dry-run          # imprime o plano e termina — nunca solicita confirmação
gitpr split --apply            # imprime o plano, confirma uma vez, prepara no índice e cria os commits
gitpr split --apply --yes      # o mesmo, sem o pedido de confirmação
gitpr split --max-groups 3     # no máximo três commits atómicos
```

| Opção | Descrição |
| --- | --- |
| **`--dry-run`** | Imprime o plano e termina. Nunca solicita confirmação, nunca altera o índice nem a árvore de trabalho, independentemente do estado do índice |
| **`--apply`** | Executa o plano: preparação seletiva no índice e um commit por grupo, por ordem |
| **`--yes`** | Omite o pedido de confirmação. Nunca ignora a verificação `--check` de cada grupo |
| **`--max-groups <n>`** | Limite máximo de commits que o plano pode propor, sobrepondo-se à configuração |
| **`--provider <name>`** | Força o fornecedor de IA para esta execução (`gemini`, `deepseek`, `ollama`) |

| Característica | Descrição |
| --- | --- |
| **Origem dos dados** | As alterações não consolidadas em commit na árvore de trabalho — preparadas (*staged*), não preparadas (*unstaged*) ou ambas em simultâneo, como um diff único face ao HEAD |
| **Chamadas de IA** | Uma chamada para agrupar os hunks, mais uma chamada por grupo para redigir a respetiva mensagem de commit |
| **Ficheiros gravados** | Nenhum por predefinição. `--apply` grava no índice do Git e cria commits; a árvore de trabalho física nunca é modificada |
| **Índice** | Deixado limpo antes da execução. `--apply` solicita autorização uma vez para remover todas as alterações do índice |
| **Anulação** | Nenhuma embutida. O resultado são commits convencionais — `git reset`/`git reflog` são as ferramentas adequadas |
| **Código de saída 1** | Não é um repositório Git, `--dry-run` combinado com `--apply`, árvore de trabalho vazia, ausência de chave de API ou fornecedor inacessível, repositório sem commits sobre os quais construir, ou plano sem grupos |

### 1.1.1 Quando o Comando Solicita Confirmação

`--apply` declara uma intenção explícita, pelo que `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` pode legitimamente suprimir a questão. A ausência de parâmetros não declara qualquer intenção, pelo que nesse modo a pergunta **é** a essência do comando e é sempre efetuada — uma execução simples de `gitpr split` não deve consolidar commits autonomamente apenas porque um valor de configuração indica que as confirmações estão desativadas. `--yes` representa a confirmação prévia do utilizador, suprimindo o pedido de autorização em ambos os modos.

### 1.2 O Que "Atómico" Significa Aqui

Um commit atómico é um commit que contém todas as alterações necessárias para uma única preocupação e nenhuma alteração pertencente a outra. A unidade elementar de divisão é o **hunk** — um bloco `@@` de um ficheiro — e nunca uma fração menor: a divisão de um único hunk em sub-hunks está fora de âmbito, assim como a divisão de um pull request já publicado na plataforma de alojamento (*forge*).

A unidade é o hunk e não o ficheiro porque o cenário crítico a resolver é precisamente aquele em que um único ficheiro contém duas preocupações distintas. Um ficheiro cujos hunks pertençam integralmente à mesma preocupação não é uma exceção: é o mesmo mecanismo a produzir o resultado evidente.

### 1.3 Fora de Âmbito

- Ficheiros não monitorizados pelo Git (*untracked*). Não contêm hunks e `git diff HEAD` não os descreve, não participando em nenhum plano. São identificados num aviso e nunca ignorados em silêncio.
- Divisão granular interna de um hunk.
- Reversão automática de uma divisão. O resultado traduz-se em commits padrão e o Git convencional reverte-os; não foi implementado nenhum rollback dedicado, ao contrário do `gitpr fix`, onde um patch aplicado não dispõe de commit para resetar.
- Reordenação interativa, fusão e desseleção de grupos. Previsto para uma versão futura.

---

## 2. Captura do Diff

### 2.1 Captura Própria de Diff e Justificação

O comando split não utiliza `get_git_diff()`, que é o diff consumido por todos os restantes fluxos:

```python
SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")
```

A diferença fundamental reside em `-w`, passado por outros fluxos mas estritamente interdito no split. Com `-w`, uma alteração que consiste *exclusivamente* em espaços em branco é formatada como contexto — e a linha de contexto emitida pode não corresponder byte a byte ao ficheiro real. Um patch gerado a partir de tal diff seria rejeitado pelo `git apply` ou, pior ainda, aplicaria conteúdo divergente da árvore de trabalho. Tal comportamento violaria a garantia elementar deste comando: os ficheiros em disco no final são rigorosamente idênticos, byte a byte, aos ficheiros no início do processo.

O parâmetro `-U1` é também rejeitado: uma única linha de contexto oferece pouca margem para a fixação do hunk em `git apply --check`. O parâmetro `-B`, que decompõe reescritas em remoção e adição, é descartado pelo mesmo motivo — converteria um hunk aplicável em dois que teriam obrigatoriamente de ser aplicados em conjunto.

O parâmetro `-M` é **mantido** e é estrutural. Sem deteção de renomeações, uma renomeação seria processada como uma remoção seguida de uma adição, e a adição figuraria como um ficheiro não monitorizado — fora de âmbito. O split acabaria por registar uma remoção pura do caminho original enquanto o novo ficheiro ficaria esquecido e sem controlo de versão, o que configuraria perda efetiva de dados.

`--binary` é inócuo para texto simples e é o único mecanismo que viabiliza a aplicação de ficheiros binários modificados.

### 2.2 Sem Exclusões Inteligentes (*Smart Excludes*)

Os fluxos normais de revisão descartam ficheiros de bloqueio (*lockfiles*), ficheiros gerados e binários antes de submeterem o diff à IA. O comando split não descarta absolutamente nada.

A justificação é que tal exclusão não é inócua neste contexto, é *incorreta*. Um lockfile e o respetivo manifesto descrevem uma alteração conjunta; excluir o lockfile implicaria consolidar apenas o manifesto, deixando a árvore de trabalho num estado inconsistente onde ambos discordam — criando um commit intermédio inválido, situação que este comando visa precisamente impedir. O excesso de ruído é controlado truncando cada unidade no prompt e limitando o número total de unidades transmitidas.

### 2.3 Capturar Primeiro, Desestagiar no Fim

O comando `--apply` necessita de um índice limpo para preparar as alterações de forma seletiva, podendo o índice já conter alterações prévias: um novo ficheiro preparado, uma renomeação preparada. Esse estado não deve ser descartado antes da leitura do diff — é precisamente o que torna essas alterações *visíveis*. Um ficheiro novo só surge no `git diff HEAD` porque o índice o regista; caso seja desestagiado previamente, passa a ficheiro não monitorizado, fica fora de âmbito e desaparece do plano.

Assim, a ordem é rigorosa: o diff é capturado com base no estado existente do índice, e tudo é desestagiado imediatamente antes da execução do primeiro `git apply --cached`. Este procedimento é fiável porque qualquer hunk presente em `git diff HEAD` contém uma pré-imagem referente ao HEAD, independentemente do que constar no índice. Após a desestagiação total, o índice coincide com o HEAD, permitindo que essas mesmas pré-imagens se apliquem de forma limpa. Não há recálculo de diff, não há interrupção por divergência e nenhum plano sofre mutações invisíveis entre a apresentação e a execução.

### 2.4 Ficheiros Não Monitorizados (*Untracked*)

Estão fora de âmbito e são devidamente comunicados: o plano inclui um aviso explícito discriminando-os. As mensagens "Não existem alterações a processar" e "Existiam alterações que foram omitidas" nunca devem ser confundidas.

---

## 3. O Plano

### 3.1 Unidades

Uma unidade corresponde a um de dois tipos, sendo esta distinção determinante ao longo de todo o fluxo:

| Unidade | Descrição |
| --- | --- |
| **`Hunk`** | Um bloco `@@` de um ficheiro, com o respetivo conteúdo literal, cabeçalho de ficheiro precedente, linhas de início e contagem de ambas as versões, e posição na travessia original |
| **`OpaqueSection`** | Uma secção do diff desprovida de hunks convencionais — alteração binária, renomeação pura, modificação de permissões/modos, criação de ficheiro vazio — preservada integralmente de forma literal |

As secções opacas nunca são submetidas à IA. Não existe qualquer decisão de agrupamento semântico a solicitar ao modelo, e uma unidade sobre a qual o modelo não consiga raciocinar resultaria na geração de identificadores arbitrários. Cada uma é convertida num grupo autónomo constituído por essa unidade única: um commit atómico de uma alteração indivisível.

O cabeçalho do ficheiro é **preservado, nunca reconstruído**. `new file mode`, `deleted file mode`, `old mode`/`new mode` e a notação com aspas utilizada pelo Git para caminhos com espaços ou carateres não-ASCII não podem ser deduzidos unicamente pelo caminho, e tentar sintetizá-los geraria um patch incompatível com o Git.

### 3.2 Limites de Hunk Determinados por Contagem

Um hunk termina rigorosamente quando a contagem especificada no respetivo cabeçalho se esgota — nunca na ocorrência do `@@` subsequente. No interior de um hunk, uma linha removida iniciada por `--- algo` e uma linha adicionada iniciada por `+++ algo` surgem na coluna 0 e seriam indistinguíveis de um cabeçalho de ficheiro, ao passo que uma linha de contexto apresenta sempre um espaço inicial. O método de contagem é o único matematicamente correto.

A contagem atua em simultâneo como validador de entradas corrompidas. Uma secção cujas contagens não correspondam ao conteúdo é degradada **na totalidade** para uma `OpaqueSection`: nunca para uma lista parcial de hunks, pois uma fração de uma secção ilegível não pode ser entregue a `git apply`, sendo preferível rejeitar a aplicação do que aplicar um ficheiro a meio.

### 3.3 Identidade da Unidade

O identificador de uma unidade possui a estrutura `0007-1a2b3c4d` — a posição ordinal de travessia, seguida dos primeiros oito dígitos hexadecimais do hash MD5 calculado sobre o caminho do ficheiro, cabeçalho do hunk e corpo.

Ambos os componentes são determinantes. A posição ordinal decorre exclusivamente da ordem de travessia estipulada pelo texto do diff, assegurando que a mesma árvore de trabalho produzirá sempre os mesmos identificadores e garantindo idempotência em execuções sucessivas de `--dry-run`. O hash distingue ficheiros com modificações *idênticas* — uma cópia vendorizada e o ficheiro original produzem o mesmo cabeçalho e corpo, diferindo unicamente pelo caminho.

### 3.4 Agrupamento

O agrupamento consiste em **uma única chamada de IA, sem fragmentação em lotes**. O processamento em lotes (*batching*) seria a forma intuitiva de contornar diffs de grande dimensão, mas revela-se inadequado para esta finalidade: hunks de uma mesma preocupação distribuídos por lotes distintos ficariam permanentemente isolados, impossibilitando a sua união. O modelo responderia com aparente certeza considerando apenas a fração visível. O split prefere uma degradação transparente — unidades não incluídas permanecem sem grupo e sem commit — em vez de forjar um plano ficticiamente completo.

Todos os identificadores devolvidos pelo modelo são validados contra as unidades efetivamente transmitidas. Identificadores desconhecidos são descartados com aviso; duplicados são unificados; unidades não mencionadas pelo modelo transitam para a lista de unidades sem grupo. Nenhuma unidade fictícia ingressa num grupo e nenhuma unidade real é omitida em silêncio.

Quando o total de unidades ultrapassa `GITPR_SPLIT_MAX_HUNKS`, as maiores são preservadas e as restantes transitam para a lista de unidades não agrupadas, com aviso indicando os respetivos identificadores. Esta seleção baseia-se na dimensão e não na ordem de ficheiros, impedindo a exclusão sistemática dos últimos ficheiros do diff.

### 3.5 Pré-validação de Conflitos

Antes da exibição do plano, cada grupo é submetido a validação com `git apply --cached --check` num índice limpo. Na eventualidade de falha, todas as unidades de todos os ficheiros afetados por esse grupo — provenientes de qualquer grupo ou da lista não agrupada — são fundidas no mesmo grupo, regenerando-se a mensagem de commit para o patch consolidado, evitando mensagens parciais desconformes com as alterações reais.

O ciclo de correção é estritamente limitado e garante terminação. Se mesmo após a união de ficheiros completos a aplicação falhar (por exemplo, incompatibilidade CRLF ou unidades binárias), tais unidades são transferidas para `ungrouped_units` com o aviso correspondente. Nenhuma alteração é perdida ou aplicada de forma incompleta.

Conflitos gerados a partir de um diff real com contexto `-U3` são excecionais. O Git funde automaticamente modificações distanciadas por menos de sete linhas num único hunk, garantindo três linhas de contexto intocado entre hunks consecutivos, pelo que qualquer subconjunto se aplica perfeitamente num índice ao nível de HEAD. As únicas causas reais de rejeição residem em discrepâncias de terminação de linha (*newline*) ou sobreposição estrita das mesmas linhas.

### 3.6 Mensagens de Commit

A mensagem de cada grupo é gerada através de `generate_pr_content()` — a mesma função utilizada no fluxo de commit predefinido, recebendo unicamente o patch do grupo em questão em vez do diff integral. Nenhum mecanismo de mensagens é duplicado: a skill `.gitpr.commit.md`, o cache de prompts MD5 e o fluxo map-reduce para patches extensos são integralmente reaproveitados.

Um patch composto por três dos nove hunks de um ficheiro é produzido através da reconstrução estruturada do cabeçalho do ficheiro e desses três blocos específicos, e nunca pelo recorte direto do texto do diff original, o qual conteria deslocamentos (*offsets*) inválidos para o subconjunto reduzido.

---

## 4. Aplicação do Plano

### 4.1 Sequência de Execução

Para cada grupo, de acordo com a ordem estabelecida no plano:

1. Validação de índice limpo — nenhuma alteração em stage. Verificado antes de cada grupo, impedindo que resíduos de um grupo anterior contaminem o commit seguinte com código alheio.
2. Reconstrução do patch do grupo e execução de `git apply --cached --check`, seguida de `git apply --cached`. Ambos os passos recorrem ao componente `patch_applier` (idêntico ao do `gitpr fix`), sendo o patch transmitido ao Git como **bytes através do stdin** — salvaguarda contra a conversão automática de quebras de linha em ambiente Windows (`\n` para `\r\n`), que provocaria a rejeição silenciosa do patch.
3. Validação estrita de que o conteúdo indexado coincide com o grupo: a lista de caminhos de `git diff --cached --name-only -M` deve ser idêntica ao conjunto de ficheiros do grupo, e as contagens `(adicionadas, removidas)` por ficheiro em `--numstat` devem coincidir com as contagens das linhas `+` e `-` das unidades. A validação recorre a numstat e não aos cabeçalhos dos hunks, dado que as linhas indicadas no cabeçalho variam após a aplicação de commits prévios adjacentes, o que causaria falsos alarmes num plano válido.
4. Criação do commit, integrando a mensagem previamente gerada para o grupo.
5. Nova validação de índice limpo.

A árvore de trabalho física nunca é modificada. Cada ficheiro em disco conserva integralmente as suas alterações; no final, o `git status` reflete uma árvore de trabalho limpa e os commits consolidam o trabalho realizado.

### 4.2 Alterações Remanescentes

As unidades presentes em `ungrouped_units` permanecem não preparadas e não consolidadas em commit no termo da execução. Este é o comportamento correto para hunks não classificados pelo modelo, grupos impossibilitados de preparação no índice ou unidades excluídas por limitação de capacidade. Ficam discriminadas no relatório final, podendo o utilizador consolidá-las manualmente ou reexecutar `gitpr split` sobre as alterações remanescentes.

### 4.3 Falhas a Meio da Sequência

**Não existe rollback automático.** O comando split gera commits convencionais, cuja anulação pode ser realizada diretamente pelo utilizador através de `git reset`. Em contrapartida, o comando garante uma interrupção segura com diagnóstico inequívoco:

| Falha | Estado subsequente do índice |
| --- | --- |
| Ao preparar um grupo (*staging*) | Todas as alterações preparadas para esse grupo são revertidas do índice, indicando o relatório a interrupção no grupo correspondente |
| Ao criar o commit do grupo | O grupo permanece preparado no índice e o relatório reflete este estado de forma explícita — evidenciando as unidades afetadas |
| Commits 1..N-1 | Inalterados. Constituem commits consolidados e válidos, sendo preservados |

---

## 5. Modelo de Skill (*Skill Template*)

O comando split **não possui nem consulta qualquer modelo de skill**.

A introdução de `.gitpr.split.md` pareceria a abordagem óbvia, mas seria incorreta. A função `get_skill_context()` atribui por omissão a skill de *review* (`DEFAULT_SKILL_TYPE = "review"`) a qualquer ação não registada, pelo que uma chamada anterior ao registo global injetaria inadvertidamente uma persona de revisão de código no prompt de agrupamento. Implementar este registo exigiria uma nova entrada em `SKILL_FILES_BY_TYPE`, uma nova etiqueta na interface de configuração com validação estrita de ordenação, um recurso adicional no servidor MCP e templates localizados por idioma — uma superfície desproporcionada para um prompt associado a um esquema de resposta rígido e não editável manualmente.

A instrução de agrupamento encontra-se, por conseguinte, integrada em `hunk_grouper.py`, contígua à lógica de validação do respetivo output.

---

## 6. Variáveis de Ambiente

| Variável | Predefinição | Descrição |
| --- | --- | --- |
| `GITPR_SPLIT_MAX_GROUPS` | `5` | Limite máximo de commits atómicos que um plano pode propor |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | `true` | Apresenta o plano e solicita autorização antes da criação do primeiro commit |
| `GITPR_SPLIT_MAX_HUNKS` | `50` | Limite máximo de unidades submetidas à chamada de agrupamento |

As três variáveis podem ser configuradas no ecrã de preferências, na secção **Split**.

Qualquer valor não positivo ou inválido reverte automaticamente para a predefinição correspondente: um limite de zero transformaria silenciosamente a instrução "dividir alterações" em "não dividir nada", em vez de sinalizar um erro visível ao utilizador.
