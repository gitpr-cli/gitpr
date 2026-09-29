# Métricas e Telemetria — Analytics Local Offline

O GitPR mantém um **livro-razão local e offline de uso**: uma linha para cada
comando executado, quanto custou e quanto demorou. Nada sai da sua máquina — o
livro-razão é um arquivo SQLite em `~/.gitpr/metrics/telemetry.db`.

## ✨ O Que Faz

Cada comando executado acrescenta uma linha ao livro-razão registrando:

| Campo | Descrição |
|-------|-----------|
| `timestamp` | Quando o comando terminou (ISO 8601) |
| `command` | Qual comando rodou (`commit`, `review`, `fullreview`, `linter`, `blame`, `hook:post-checkout`, etc.) |
| `status` | Resultado (`success`, `error`, `fired`, `no_changes`) |
| `provider` | Provedor de IA que respondeu (`gemini`, `deepseek`, `ollama`) |
| `model` | Modelo com que o provedor respondeu |
| `prompt_tokens` / `completion_tokens` | Contagem de tokens informada pelo provedor |
| `tokens_actual` / `tokens_estimated` | A contagem que vale: medida quando o provedor informa, estimada nos demais casos |
| `duration_ms` | Duração do comando em milissegundos |
| `repo` | Repositório como `dono/nome`, resolvido pelo mesmo parser multi-forja do resto da CLI |
| `branch` | Nome da branch atual |
| `author_name` | Autor Git local da execução |
| `modules` | Módulos que o diff tocou, normalizados nos dois primeiros segmentos do caminho (`src/fix`, `(root)` para um arquivo na raiz do repositório) |
| `source` | `execution` para um comando que rodou, `cache_backfill` para uma linha reconstruída do cache de IA |

As linhas também carregam `cache_hit`, `map_reduce`, `chunks_count`,
`linter_errors` e `linter_warnings`, que fazem sentido para alguns comandos e
ficam zerados nos demais. `modules` fica **vazio** nos comandos que nunca
tiveram um diff em mãos — o linter, o motor de blame e os hooks registram
execuções sem diff, e a seção de módulos as soma em `(sem módulo)` em vez de
fazê-las passar por um módulo com nome de nada.

## 📁 Onde os Dados Ficam Armazenados

```
~/.gitpr/metrics/
├── telemetry.db         ← o livro-razão: uma linha por comando executado (SQLite)
└── .migration_declined  ← gravado apenas se você recusou a importação

~/.gitpr/metrics_legacy/    ← os arquivos de evento pré-livro-razão, movidos para cá após a importação
~/.gitpr/cache/prompts/     ← cache de respostas da IA, origem de uma reconstrução
```

As exportações vão para o repositório em que você executa o comando, nunca para
o seu diretório pessoal:

```
./.gitpr/metrics/export/
├── gitpr_metrics_2026-09-28.csv    ← CSV consolidado
├── gitpr_metrics_2026-09-28.json   ← JSON consolidado
└── gitpr_metrics_2026-09-28.db     ← bundle gravado por `gitpr metrics bundle`
```

O livro-razão substituiu arquivos JSON de evento nomeados
`{uuid}_{AAAAMMDD}.json` em `~/.gitpr/metrics/{dono}/{branch}/`. Esses arquivos
são importados uma vez e **movidos, nunca apagados** — eles terminam em
`~/.gitpr/metrics_legacy/`, fora do diretório que o resumo conta.

## 🚀 Comandos CLI

### Mostrar Resumo

```bash
gitpr metrics
```

Conta linhas, não arquivos: o caminho do livro-razão, quantas execuções ele
guarda, quantas linhas foram reconstruídas do cache e o tamanho em disco. Um
aviso aparece enquanto houver arquivos de evento anteriores ao livro-razão
esperando importação.

Abaixo do cabeçalho vêm as seções, na ordem em que são lidas:

| Seção | O que responde |
|-------|----------------|
| 💰 Custo | Quantos tokens, e quanto custaram por modelo |
| 🧪 Qualidade | Taxa de aprovação do linter e com que frequência o caminho map-reduce disparou |
| 🧩 Módulos | Quais módulos as execuções tocaram, e quantos tokens cada um levou |
| 🤖 Provedores | Execuções e tokens por provedor — inclusive os que nunca chamam uma IA |
| ⏱ Ciclo | Quanto demoraram os pull requests com merge deste repositório, lidos da forja |

Uma seção sem nada a dizer é omitida em vez de impressa vazia. O dashboard desenha
essas mesmas linhas a partir do mesmo renderizador, então o terminal e a TUI não
conseguem contar duas histórias sobre um mesmo livro-razão.

### A Janela

Uma janela, um significado — as mesmas flags limitam o resumo, o dashboard, a
exportação, o bundle e a tool MCP:

```bash
gitpr metrics --days 30
gitpr metrics --since 2026-01-01 --until 2026-03-31
```

A janela é **inclusiva nas duas pontas** e incide na data à qual a linha se
refere. Sem nenhuma flag, as seções do livro-razão leem o livro-razão inteiro —
exceto o ciclo, que pede a resposta à rede e por isso assume os últimos 30 dias,
dizendo isso no próprio cabeçalho em vez de estreitar em silêncio.

### Custo e Tarifas

A seção de custo transforma tokens em dinheiro com duas camadas, a segunda
sobrepondo a primeira por modelo:

1. **Uma tabela embutida** com os preços de lista publicados pelos fornecedores
   para os IDs de modelo fixos que o GitPR acompanha (`deepseek-v4-flash`,
   `deepseek-v4-pro`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`), para que a
   seção diga algo numa máquina que ninguém configurou.
2. **O ambiente**, por modelo:

```ini
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT=0.435
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT=0.87
GITPR_METRICS_CURRENCY=USD
```

`<MODEL>` é o nome do modelo em maiúsculas, com cada sequência de caracteres que
não seja letra ou dígito colapsada em um `_`. As duas tarifas são obrigatórias: um
modelo com apenas uma delas é reportado só em tokens, porque tarifar a outra
metade com um zero não configurado subestimaria a conta.

- **A moeda padrão é USD**, que é a moeda em que a tabela embutida é cotada.
  Configure tarifas em outra moeda e aponte `GITPR_METRICS_CURRENCY` para ela — a
  tabela embutida então sai de cena, porque uma tarifa em dólar impressa sob o
  rótulo de outra moeda é um número errado, não um número ausente.
- **Provedores que rodam nesta máquina** (`ollama`, `local`) custam zero por
  definição e não precisam de tarifa.
- **Tarifas mudam.** Converter tokens gastos no ano passado pelo preço de hoje é
  uma aproximação, e a seção diz isso na linha abaixo do total.
- **Um total que deixa modelos de fora avisa** — `Total (parcial)` — em vez de
  deixar uma soma das linhas tarifadas parecer a conta inteira.

### A Métrica de Ciclo

A seção ⏱ é a única métrica aqui que não vem do livro-razão, e não tem como vir:
o livro-razão registra o que o GitPR rodou nesta máquina, enquanto um pull request
recebe merge na forja, por pessoas que nunca rodaram o GitPR. Por isso esta
precisa de token e de rede, e é a única seção que pode voltar sem nada por um
motivo que não é "nada aconteceu".

Ela mede `created_at → merged_at` dos pull requests que a forja reporta como
mesclados na janela — **o ciclo do próprio pull request**, da abertura ao merge.
Não é o tempo do primeiro commit de uma branch até o seu pull request: o contrato
de listagem não carrega commits de branch, então esse intervalo não está
disponível aqui, e também não é inventado a partir do livro-razão.

O cabeçalho nomeia o repositório e a janela — `⏱ Ciclo · dono/repo · últimos 30
dias` — porque esta é a única seção cujo escopo não é o do livro-razão: lida ao
lado de um resumo que diz "Todos os repositórios", um número solto pareceria
cobri-los todos.

Toda falha degrada para uma linha, nunca para um stack trace:

| O que aconteceu | O que a seção mostra |
|-----------------|----------------------|
| Sem remote origin, sem forja utilizável, sem token, sem rede | `Não lido: <o motivo>` |
| A forja não publica data de merge (Bitbucket) | Diz isso, sem gastar uma chamada de rede |
| A janela não tem nenhum pull request mesclado | `Nenhum pull request teve merge nesta janela.` |

Um merge cuja data precede a própria criação é um relógio que a forja errou, não
um ciclo negativo: essa linha é descartada em vez de entrar na média.

### Exportar Dados

```bash
gitpr metrics export
```

Grava em CSV e JSON as linhas que nunca foram exportadas, em
`./.gitpr/metrics/export/`, e então as marca como exportadas — por isso uma
segunda execução responde "Nenhuma métrica nova para exportar." em vez de se
repetir. A exportação cobre o repositório da cópia de trabalho.

- **Colunas CSV:** timestamp, day, command, status, provider, model,
  prompt_tokens, completion_tokens, tokens_actual, tokens_estimated, duration_ms,
  repo, branch, author_name, modules, cache_hit, map_reduce, linter_errors,
  linter_warnings, chunks_count, source
- **JSON:** as mesmas linhas como objetos, prontas para um script ler

### Bundle e Merge (Consolidação de Equipe)

`export` é o que uma pessoa lê; um **bundle** é o que outra máquina lê — o mesmo
recorte do livro-razão como um arquivo `.db` autossuficiente:

```bash
gitpr metrics bundle --days 30
gitpr metrics bundle --since 2026-07-01 --until 2026-09-30 -o ./entrega/
gitpr metrics merge ./entrega/gitpr_metrics_2026-09-29.db ./entrega/outro.db
```

`bundle` copia as linhas da janela para um arquivo SQLite independente, com
schema e `PRAGMA user_version` incluídos, e grava em `./.gitpr/metrics/export/`
a menos que `-o` diga outra coisa. `merge` anexa cada bundle e insere as linhas
que ainda não tem — o UUID é a chave primária, então mesclar o mesmo arquivo duas
vezes, ou dois bundles sobrepostos, nunca conta uma execução em dobro.

As versões de schema são tratadas em **uma direção só**: um bundle mais antigo é
migrado para cima ao ser anexado, e um mais novo é recusado *antes* de qualquer
escrita, com a versão que ele carrega e a que este GitPR entende — o livro-razão
local nunca fica meio importado. Atualize o GitPR para ler um bundle mais novo.

Esta é a resposta a "quanto a equipe gastou no trimestre" sem servidor: cada
máquina empacota a sua janela, e quem precisa do total mescla os arquivos num
livro-razão próprio.

### Importar Dados Anteriores ao Livro-Razão

```bash
gitpr metrics migrate
```

Lê os arquivos de evento escritos antes do livro-razão existir, insere-os e move
os originais para `~/.gitpr/metrics_legacy/`. Com um terminal, abre um assistente
que também oferece reconstruir o histórico a partir do cache de respostas da IA.
Essas linhas são marcadas com `source: cache_backfill` porque o cache indexa uma
resposta pelo seu prompt e, portanto, conta **prompts distintos, não execuções**.

### Apagar Registros Antigos

```bash
gitpr metrics prune --before 2026-01-01
```

Apaga as linhas escritas antes de uma data, após confirmação, e recupera o espaço
com `VACUUM`. `--source cache_backfill` restringe a exclusão às linhas
reconstruídas. **Não existe expiração automática**: o livro-razão responde
"quanto gastamos neste ano", e um calendário que apaga sozinho mudaria essa
resposta sem ninguém pedir.

### Limpar Dados

```bash
gitpr metrics purge
```

O caminho destrutivo: apaga todas as linhas e todos os arquivos de evento que
ainda esperam importação, após confirmação.

### Dashboard Interativo

```bash
gitpr metrics dashboard
```

Abre um **dashboard TUI** (Textual) restrito ao repositório da cópia de trabalho:

- **Barra de resumo:** total de entradas, linhas reconstruídas, total de tokens, duração total, top comandos
- **Tabela de eventos:** timestamp, comando, status, provedor, tokens, duração
- **Seções:** custo, qualidade, módulos, provedores e o ciclo — as mesmas linhas
  que `gitpr metrics` imprime, desenhadas com markup do Textual em vez das cores
  do click
- **Barra de status:** o intervalo de tempo que a tabela cobre e quantas entradas ela tem
- **Atalhos:** `F5` para atualizar, `Esc` para sair

Enquanto o livro-razão ainda não existir, o dashboard lê o cache e os arquivos de
evento, mostra uma barra de progresso durante a varredura e avisa isso na barra
de status. A seção de ciclo é desenhada de qualquer forma: ela nunca leu o
livro-razão.

## 🔧 Git Hooks (Coleta Automática)

Quando instalados via `gitpr --installhooks`, três hooks adicionais coletam
telemetria comportamental:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Trocas de branch (mudanças de contexto) — dispara só quando a branch realmente mudou |
| `pre-push` | Eventos de push (frequência de entrega) |
| `post-merge` | Eventos de pull/merge (frequência de integração) |

Os três rodam `gitpr --quiet metrics hook-event <nome>`, uma ação oculta cujo
trabalho inteiro é gravar uma linha e sair. O repositório é resolvido pelo próprio
hook, pelo mesmo parser que o resto da CLI usa, então GitLab, Bitbucket e Azure
DevOps registram o mesmo `dono/nome` que o GitHub. Uma guarda em volta da chamada
— `command -v gitpr`, mais um `|| true` no final — impede que uma máquina sem o
GitPR, ou com um GitPR que falha, quebre o seu comando Git.

## 📊 Casos de Uso

- **Tech Lead:** Ver quais repositórios, branches e autores realmente usam revisões de IA, e quais hooks disparam
- **Finanças:** Ler a seção de custo para a conta por modelo, ou `gitpr metrics --since 2026-07-01` para o trimestre
- **Qualidade:** Ler `linter_errors`, `linter_warnings` e `modules` para achar qual parte do projeto gera mais achados
- **Processo:** Observar `map_reduce` e `chunks_count` — PRs grandes disparando o caminho map-reduce apontam um problema de processo
- **Entrega:** Ler a seção de ciclo para ver quanto demoraram os pull requests com merge deste repositório, e quais demoraram mais

## 🔒 Privacidade

- **100% local** — o livro-razão é um arquivo na sua máquina; nada dele é enviado para servidores externos
- **A única exceção é a seção de ciclo** — ela pede à forja configurada os pull requests com merge do repositório em que você está. Não envia nenhuma linha do livro-razão, nenhuma contagem de tokens e nenhum diff: a pergunta é "quais pull requests tiveram merge nesta janela", e a resposta é somente leitura
- **Não é anônimo** — cada linha carrega o repositório, a branch e o nome do autor Git local. Não carrega conteúdo de arquivos nem diffs: `modules` guarda os segmentos de caminho que uma execução tocou, nunca os nomes dos arquivos, e o e-mail do autor fica no cache de IA
- **Controle do usuário** — `prune` e `purge` são manuais e confirmados; nada expira sozinho
- **Hooks opcionais** — git hooks só instalam se você executar `gitpr --installhooks`

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Configuração do servidor MCP
- [MCP Prompts](mcp-prompts.md) — Templates de mensagem pré-definidos
- [MCP Tool Annotations](mcp-annotations.md) — Dicas de integração com IDEs

---
**Dica profissional:** As exportações caem em `./.gitpr/metrics/export/`, dentro do
repositório em que você está — esse diretório pertence à sua máquina, não ao
projeto, e é o que a entrada do `.gitignore` do próprio GitPR mantém fora da
árvore. Para responder "quanto esta máquina gastou neste trimestre" sem
planilha, pergunte ao livro-razão: `gitpr metrics --since 2026-07-01`.
