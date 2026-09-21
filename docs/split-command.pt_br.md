# Documentação Técnica: Comando de Divisão (gitpr split)

`gitpr split` lê uma árvore de trabalho que carrega várias preocupações sem relação entre si, agrupa os hunks por intenção lógica com IA e propõe um commit atômico por preocupação — cada um com uma mensagem gerada só para aquele subconjunto de alterações. Ler é o padrão e gravar é opt-in: sem argumentos o comando imprime o plano e oferece aplicá-lo, `--dry-run` imprime e para sem nunca perguntar, e `--apply` confirma uma vez e então estagia e commita grupo a grupo.

O problema que ele resolve é o que todo desenvolvedor reconhece: uma correção de bug, um refactor e um ajuste de configuração que cresceram na mesma tarde, agora inseparáveis em um único `git diff`, onde as únicas saídas são `git add -p` na mão ou uma mensagem de commit que lista três coisas sem relação.

---

## 1. Visão Geral

O subcomando é um acréscimo à CLI, não uma mudança nela: toda opção legada mantém o seu sentido, e o fluxo inteiro é local — nenhum `git commit` é criado até que `--apply` seja confirmado, nada é enviado ao remoto e nenhuma branch é criada.

### 1.1 Referência do Comando — `gitpr split`

Todas as opções do subcomando, como mostra `gitpr split -h` (ou `--help`):

```bash
gitpr split                    # imprime o plano e depois oferece aplicá-lo
gitpr split --dry-run          # imprime o plano e para — nunca pergunta
gitpr split --apply            # imprime o plano, confirma uma vez, estagia e commita
gitpr split --apply --yes      # o mesmo, sem a confirmação
gitpr split --max-groups 3     # no máximo três commits atômicos
```

| Opção | Descrição |
| --- | --- |
| **`--dry-run`** | Imprime o plano e para. Nunca pergunta, nunca toca no índice nem na árvore de trabalho, em qualquer estado do índice |
| **`--apply`** | Executa o plano: staging seletivo e um commit por grupo, em ordem |
| **`--yes`** | Pula a confirmação. Nunca ignora o `--check` de cada grupo |
| **`--max-groups <n>`** | Limite de quantos commits o plano pode propor, sobrepondo a configuração |
| **`--provider <name>`** | Força o provedor de IA nesta execução (`gemini`, `deepseek`, `ollama`) |

| Característica | Descrição |
| --- | --- |
| **Fonte de dados** | As alterações não commitadas da árvore de trabalho — estagiadas, não estagiadas e ambas juntas, como um único diff contra HEAD |
| **Chamadas de IA** | Uma chamada para agrupar os hunks, mais uma chamada por grupo para escrever a sua mensagem de commit |
| **Arquivos gravados** | Nenhum por padrão. `--apply` grava no índice do Git e cria commits; a árvore de trabalho nunca é gravada |
| **Índice** | Deixado limpo antes da execução. `--apply` pede uma vez permissão para desestagiar tudo |
| **Desfazer** | Nenhum embutido. O resultado são commits comuns — `git reset`/`git reflog` são as ferramentas |
| **Código de saída 1** | Não é um repositório Git, `--dry-run` combinado com `--apply`, árvore de trabalho vazia, sem chave de API ou provedor inalcançável, repositório sem commits sobre os quais construir, ou plano sem grupos |

### 1.1.1 Quando o Comando Pergunta

`--apply` declara uma intenção, então `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` pode legitimamente pular a pergunta. Nenhuma flag declara intenção alguma, então nesse modo a pergunta **é** o comando e é sempre feita — um `gitpr split` puro não deve commitar sozinho só porque um valor de configuração diz que confirmações estão desligadas. `--yes` é o usuário dizendo isso explicitamente, e pula a pergunta nos dois modos.

### 1.2 O Que "Atômico" Significa Aqui

Um commit atômico é um commit que contém toda alteração de que uma preocupação precisa e nenhuma alteração pertencente a outra. A unidade de divisão é o **hunk** — um bloco `@@` de um arquivo — e nunca algo menor: dividir um único hunk em fragmentos menores está fora de escopo, e também está dividir um pull request já publicado na forge.

A unidade é o hunk e não o arquivo porque o caso que vale a pena resolver é justamente aquele em que um único arquivo carrega duas preocupações. Um arquivo cujos hunks pertencem todos à mesma preocupação não é um caso especial disso: é a mesma maquinaria chegando à resposta óbvia.

### 1.3 O Que Está Fora de Escopo

- Arquivos que o git não rastreia. Eles não carregam hunks, e `git diff HEAD` não os descreve, então não participam de nenhum plano. Eles são nomeados em um aviso, nunca ignorados em silêncio.
- Dividir um hunk mais adiante.
- Desfazer uma divisão. O resultado são commits normais e o Git normal os reverte; nenhum rollback dedicado foi construído, ao contrário do `gitpr fix`, onde um patch gravado não tem commit para resetar.
- Reordenar, juntar e desmarcar grupos de forma interativa. Entrega futura.

---

## 2. Capturando o Diff

### 2.1 A Captura de Diff Própria, e Por Quê

O split não usa `get_git_diff()`, o diff que todos os outros fluxos leem:

```python
SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")
```

A diferença é o `-w`, que os outros fluxos passam e o split não pode passar. Com `-w`, uma diferença que é *apenas* espaço em branco é renderizada como contexto — e a linha de contexto emitida pode não bater byte a byte com o arquivo. Um patch construído a partir de tal diff ou é recusado pelo `git apply` ou, pior, aplica conteúdo que difere da árvore de trabalho. Isso quebraria a garantia sobre a qual este comando é construído: os arquivos em disco no fim são byte a byte idênticos aos arquivos em disco no início.

O `-U1` também é abandonado: uma linha de contexto deixa pouca âncora para o `git apply --check`. O `-B`, que decompõe reescritas em exclusão mais adição, é abandonado pelo mesmo motivo que é ruim aqui como em qualquer lugar — transforma um hunk aplicável em dois que precisam ser aplicados em conjunto.

O `-M` é **mantido**, e é essencial. Sem detecção de renomeação, uma renomeação chega como uma exclusão mais uma adição, e a adição é um arquivo não rastreado — fora de escopo. O split então commitaria uma exclusão pura do caminho antigo enquanto o arquivo novo ficaria sem rastreio ao lado, o que se lê como perda de dados.

`--binary` é inócuo para texto e é a única coisa que torna um arquivo binário alterado aplicável.

### 2.2 Sem Exclusões Inteligentes

Os fluxos de revisão descartam lockfiles, arquivos gerados e binários antes de mandar um diff para a IA. O split não descarta nada.

O motivo é que a exclusão não é gratuita aqui, ela é *errada*. Um lockfile e o seu manifesto descrevem uma única alteração; excluir o lockfile commita o manifesto sozinho e deixa uma árvore em que os dois discordam — um commit intermediário quebrado, que é exatamente o que este comando existe para evitar. O ruído é limitado, em vez disso, truncando cada unidade no prompt e limitando quantas unidades são enviadas.

### 2.3 Capturar Primeiro, Desestagiar Depois

O `--apply` precisa de um índice contra o qual estagiar, e o índice pode já conter trabalho: um arquivo novo estagiado, uma renomeação estagiada. Esse estado não é um acidente a ser limpo antes de ler o diff — é o que torna essas alterações *visíveis*. Um arquivo novo só aparece em `git diff HEAD` porque o índice o rastreia; desestagie-o antes e ele se torna não rastreado, fora de escopo, e some do plano.

Então a ordem é fixa: o diff é capturado contra qualquer estado de índice existente, e tudo é desestagiado imediatamente antes do primeiro `git apply --cached`. Isso é sólido porque todo hunk em um `git diff HEAD` carrega uma pré-imagem tirada de HEAD, seja o que for que o índice guarde. Depois da desestagiação o índice *é* HEAD, então essas mesmas pré-imagens aplicam limpo. Não há novo diff, não há aborto por divergência e não há plano que se remodele em silêncio entre ser mostrado e ser aplicado.

### 2.4 Arquivos Não Rastreados

Eles estão fora de escopo e são reportados: o plano carrega um aviso que os nomeia. "Não há nada aqui" e "havia algo aqui e eu pulei" nunca podem parecer a mesma coisa.

---

## 3. O Plano

### 3.1 Unidades

Uma unidade é uma de duas coisas, e a diferença importa em todo o percurso:

| Unidade | O que é |
| --- | --- |
| **`Hunk`** | Um bloco `@@` de um arquivo, com o seu conteúdo literal, o cabeçalho de arquivo que o precede, início e contagem dos dois lados, e a sua posição na travessia original |
| **`OpaqueSection`** | Uma seção do diff sem hunks — uma alteração binária, uma renomeação pura, uma mudança apenas de modo, a criação de um arquivo vazio — mantida inteira e literal |

Seções opacas nunca são enviadas à IA. Não há decisão de agrupamento a pedir sobre elas, e uma unidade sobre a qual o modelo não consegue raciocinar é uma unidade para a qual ele inventa um id plausível. Cada uma se torna o seu próprio grupo de uma unidade: um commit atômico de uma alteração indivisível.

O cabeçalho de arquivo é **armazenado, não reconstruído**. `new file mode`, `deleted file mode`, `old mode`/`new mode` e a forma citada do git para caminhos com espaços ou bytes não-ASCII são todos irrecuperáveis a partir de um caminho, e sintetizá-los produz um patch que o git recusa.

### 3.2 As Fronteiras do Hunk São Decididas por Contagem

Um hunk termina quando as contagens do seu cabeçalho se esgotam — nunca no próximo `@@`. Dentro de um hunk, uma linha removida que diz `--- algo` e uma linha adicionada que diz `+++ algo` ficam na coluna 0 e são indistinguíveis de um par de cabeçalhos de arquivo, enquanto uma linha de contexto sempre carrega o seu espaço inicial. Contar é a única regra correta.

A contagem também serve de validador de entrada malformada. Uma seção cujas contagens não se reconciliam com o seu corpo degrada **inteira** para um `OpaqueSection`: nunca uma lista parcial de hunks, porque metade de uma seção ilegível não é algo para entregar ao `git apply`, e um patch que aplica a maior parte de um arquivo é pior do que um que o recusa.

### 3.3 Identidade da Unidade

O id de uma unidade é `0007-1a2b3c4d` — a posição na travessia, depois os oito primeiros dígitos hexadecimais de um MD5 sobre o caminho do arquivo, o cabeçalho do hunk e o corpo.

As duas metades são essenciais. A posição depende apenas da ordem de travessia, que o texto do diff fixa, então a mesma árvore de trabalho sempre produz os mesmos ids e um `--dry-run` repetido imprime o que imprimiu antes. O hash é o que separa dois arquivos alterados *de forma idêntica* — uma cópia vendorizada e o seu original produzem o mesmo cabeçalho e o mesmo corpo e não diferem em nada além do caminho.

### 3.4 Agrupamento

O agrupamento é **uma chamada de IA, sem lotes**. Lotes são a forma óbvia de cobrir um diff grande demais para um prompt, e são errados para esta tarefa: hunks de uma preocupação que caem em lados opostos de uma fronteira de lote nunca podem ser reunidos, porque nenhum lote vê os hunks do outro. O modelo então responde com confiança sobre a metade que consegue ver. O split prefere degradar com honestidade — unidades que não cabem ficam sem grupo e sem commit — a produzir um plano que parece completo e não é.

Todo id que o modelo devolve é validado contra as unidades realmente enviadas. Ids desconhecidos são descartados com um aviso; duplicatas são mantidas uma vez; unidades que o modelo nunca mencionou viram unidades sem grupo. Nenhuma unidade inventada entra em um grupo, e nenhuma unidade real é descartada em silêncio.

Quando existem mais unidades do que `GITPR_SPLIT_MAX_HUNKS` permite, as maiores são mantidas e o resto vai para a lista sem grupo com um aviso nomeando os seus ids. Maiores primeiro e não os N primeiros: cortar na ordem dos arquivos deixaria sistematicamente os últimos arquivos do diff sem análise.

### 3.5 Pré-validação de Conflito

Antes de o plano ser mostrado, cada grupo passa por `git apply --cached --check` contra um índice limpo. Um grupo que falha tem todas as unidades de todos os arquivos que toca — de todos os grupos e da lista sem grupo — fundidas nele, e a sua mensagem de commit é regerada para o patch fundido, porque uma mensagem descrevendo um subgrupo seria uma mentira sobre o commit que ela rotula.

O laço é limitado e sempre termina. Quando forçar arquivos inteiros ainda falha — um arquivo CRLF, uma unidade binária — essas unidades vão para `ungrouped_units` com um aviso. Nada é descartado e nada é meio-aplicado.

Um conflito a partir de um diff `-U3` real é mais raro do que parece. O git funde quaisquer duas alterações a menos de sete linhas de distância em um único hunk, o que deixa três linhas de contexto intocado entre os hunks que ele emite, então qualquer subconjunto deles aplica limpo em um índice que está em HEAD. As duas formas de um grupo ser genuinamente recusado são uma incompatibilidade de fim de linha e dois hunks cobrindo as mesmas linhas.

### 3.6 Mensagens de Commit

A mensagem de cada grupo vem de `generate_pr_content()` — a mesma função que o fluxo de commit padrão usa, recebendo apenas o patch daquele grupo em vez do diff inteiro. Nada do pipeline de mensagens é duplicado: a skill `.gitpr.commit.md`, o cache MD5 de prompts e o caminho map-reduce para patches grandes são herdados como estão.

Um patch com três dos nove hunks de um arquivo é construído reconstruindo o cabeçalho do arquivo e aqueles três hunks, não fatiando o texto do diff original. Uma fatia carrega deslocamentos que estavam corretos no diff do arquivo inteiro e estão errados no menor.

---

## 4. Aplicando

### 4.1 A Sequência

Para cada grupo, na ordem que o plano fixa:

1. Confirmar que o índice está limpo — nada estagiado. Verificado antes de cada grupo, para que um grupo que vazou para além do seu próprio commit não possa ser estagiado em cima do próximo e aparecer depois como um commit contendo trabalho de outra pessoa.
2. Reconstruir o patch do grupo e rodar `git apply --cached --check`, depois `git apply --cached`. Ambos passam pelo mesmo `patch_applier` do `gitpr fix`, então o patch é entregue ao git como **bytes na entrada padrão** — a defesa contra a tradução de fim de linha em modo texto do Windows, que de outra forma transformaria cada `\n` em `\r\n` e faria o git rejeitar o patch inteiro, em silêncio, e só ali.
3. Verificar que o que chegou ao índice é exatamente o grupo: o conjunto de caminhos de `git diff --cached --name-only -M` deve ser igual ao conjunto de arquivos do grupo, e as contagens `(adicionadas, removidas)` por arquivo de `--numstat` devem ser iguais às contagens lidas das linhas `+` e `-` das unidades. Numstat e não os cabeçalhos dos hunks: os números de um cabeçalho descrevem a região que ele cobre, contexto incluído, e mudam quando um commit vizinho move as linhas ao redor, então uma verificação baseada em cabeçalho daria falso alarme em um plano perfeitamente correto.
4. Commitar, com a mensagem gerada do grupo.
5. Confirmar que o índice está limpo de novo.

A árvore de trabalho nunca é gravada. Todo arquivo em disco mantém toda alteração que tinha, estagiada ou não; no fim, `git status` mostra uma árvore limpa e os commits contêm o trabalho.

### 4.2 O Que Fica Para Trás

Unidades em `ungrouped_units` permanecem sem commit e sem stage no fim. Esse é o resultado honesto para um hunk que o modelo não classificou, um grupo que não pôde ser estagiado, ou uma unidade cortada por exceder o orçamento. Elas são listadas no relatório; o usuário as commita ou roda `gitpr split` de novo sobre o que sobrou.

### 4.3 Quando Algo Falha no Meio da Sequência

**Não há rollback automático.** Um split produz commits comuns, e desfazê-los é `git reset`, que o usuário já tem. O que o comando garante, em vez disso, é que ele para de forma limpa e diz exatamente o que aconteceu:

| Falha | O que o índice contém depois |
| --- | --- |
| Estagiar um grupo | Tudo o que foi estagiado para aquele grupo é desestagiado de novo, e o relatório diz que a execução parou naquele grupo |
| Commitar um grupo | O grupo permanece estagiado, e o relatório diz isso literalmente — em vez de esconder quais unidades estavam em voo |
| Commits 1..N-1 | Intocados. São commits reais e permanecem |

---

## 5. Skill Template

O split **não tem skill template**, e não lê nenhum.

`.gitpr.split.md` seria a forma óbvia, e estaria errada. `get_skill_context()` responde a um tipo de ação não registrado com a skill de *review* — `DEFAULT_SKILL_TYPE = "review"` — então uma chamada feita antes de o tipo estar registrado em todo lugar entregaria silenciosamente ao prompt de agrupamento uma persona de revisão de código. Registrá-lo propriamente significa uma nova entrada em `SKILL_FILES_BY_TYPE`, um novo rótulo na lista de ordem verificada da tela de configuração, um novo recurso no servidor MCP, um template por idioma e as suas traduções: uma superfície grande, para um prompt que descreve um esquema de resposta fixo e não deveria ser editado à mão.

A instrução de agrupamento está, portanto, embutida em `hunk_grouper.py`, onde fica ao lado do código que analisa a sua saída.

---

## 6. Variáveis de Ambiente

| Variável | Padrão | Descrição |
| --- | --- | --- |
| `GITPR_SPLIT_MAX_GROUPS` | `5` | Limite máximo de quantos commits atômicos um plano pode propor |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | `true` | Mostra o plano e pergunta antes de o primeiro commit ser criado |
| `GITPR_SPLIT_MAX_HUNKS` | `50` | Limite máximo de quantas unidades são enviadas à chamada de agrupamento |

As três são editáveis na tela de configuração, sob **Split**.

Um valor não positivo ou não interpretável para qualquer um dos tetos volta ao padrão em vez de ser honrado: um teto de zero transformaria silenciosamente "divida isto" em "não divida nada" em vez de em um erro que alguém pudesse ver.
