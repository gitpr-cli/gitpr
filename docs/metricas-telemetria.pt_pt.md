# Métricas e Telemetria — Analytics Local Offline

O GitPR mantém um **registo local e offline de utilização**: uma linha por cada
comando executado, quanto custou e quanto demorou. Nada sai da sua máquina — o
registo é um ficheiro SQLite em `~/.gitpr/metrics/telemetry.db`.

## ✨ O Que Faz

Cada comando executado acrescenta uma linha ao registo, gravando:

| Campo | Descrição |
|-------|-----------|
| `timestamp` | Quando o comando terminou (ISO 8601) |
| `command` | Qual comando correu (`commit`, `review`, `fullreview`, `linter`, `blame`, `hook:post-checkout`, etc.) |
| `status` | Resultado (`success`, `error`, `fired`, `no_changes`) |
| `provider` | Provedor de IA que respondeu (`gemini`, `deepseek`, `ollama`) |
| `model` | Modelo com que o provedor respondeu |
| `prompt_tokens` / `completion_tokens` | Contagem de tokens comunicada pelo provedor |
| `tokens_actual` / `tokens_estimated` | A contagem que conta: medida quando o provedor a comunica, estimada nos restantes casos |
| `duration_ms` | Duração do comando em milissegundos |
| `repo` | Repositório como `dono/nome`, resolvido pelo mesmo parser multi-forja do resto da CLI |
| `branch` | Nome da branch atual |
| `author_name` | Autor Git local da execução |
| `modules` | Módulos que o diff tocou, normalizados nos dois primeiros segmentos do caminho (`src/fix`, `(root)` para um ficheiro na raiz do repositório) |
| `source` | `execution` para um comando que correu, `cache_backfill` para uma linha reconstruída a partir da cache de IA |

As linhas transportam também `cache_hit`, `map_reduce`, `chunks_count`,
`linter_errors` e `linter_warnings`, que fazem sentido para alguns comandos e
ficam a zero nos restantes. `modules` fica **vazio** nos comandos que nunca
tiveram um diff em mãos — o linter, o motor de blame e os hooks registam
execuções sem diff, e a secção de módulos soma-as em `(sem módulo)` em
vez de as fazer passar por um módulo com nome de nada.

## 📁 Onde os Dados Ficam Armazenados

```
~/.gitpr/metrics/
├── telemetry.db         ← o registo: uma linha por comando executado (SQLite)
└── .migration_declined  ← gravado apenas se recusou a importação

~/.gitpr/metrics_legacy/    ← os ficheiros de evento anteriores ao registo, movidos para aqui após a importação
~/.gitpr/cache/prompts/     ← cache de respostas da IA, origem de uma reconstrução
```

As exportações vão para o repositório onde executa o comando, nunca para o seu
diretório pessoal:

```
./.gitpr/metrics/export/
├── gitpr_metrics_2026-09-28.csv    ← CSV consolidado
├── gitpr_metrics_2026-09-28.json   ← JSON consolidado
└── gitpr_metrics_2026-09-28.db     ← bundle gravado por `gitpr metrics bundle`
```

O registo substituiu ficheiros JSON de evento nomeados
`{uuid}_{AAAAMMDD}.json` em `~/.gitpr/metrics/{dono}/{branch}/`. Esses ficheiros
são importados uma vez e **movidos, nunca eliminados** — ficam em
`~/.gitpr/metrics_legacy/`, fora do diretório que o resumo conta.

## 🚀 Comandos CLI

### Mostrar Resumo

```bash
gitpr metrics
```

Conta linhas, não ficheiros: o caminho do registo, quantas execuções contém,
quantas linhas foram reconstruídas a partir da cache e o tamanho em disco. Surge
um aviso enquanto houver ficheiros de evento anteriores ao registo à espera de
importação.

Abaixo do cabeçalho vêm as secções, pela ordem em que são lidas:

| Secção | O que responde |
|--------|----------------|
| 💰 Custo | Quantos tokens, e quanto custaram por modelo |
| 🧪 Qualidade | Taxa de aprovação do linter e com que frequência o caminho map-reduce disparou |
| 🧩 Módulos | Que módulos as execuções tocaram, e quantos tokens cada um levou |
| 🤖 Fornecedores | Execuções e tokens por fornecedor — incluindo os que nunca chamam uma IA |
| ⏱ Ciclo | Quanto demoraram os pull requests com merge deste repositório, lidos da forja |

Uma secção sem nada a dizer é omitida em vez de impressa vazia. O dashboard
desenha estas mesmas linhas a partir do mesmo renderizador, por isso o terminal e
a TUI não conseguem contar duas histórias sobre um mesmo registo.

### A Janela

Uma janela, um significado — as mesmas flags limitam o resumo, o dashboard, a
exportação, o bundle e a tool MCP:

```bash
gitpr metrics --days 30
gitpr metrics --since 2026-01-01 --until 2026-03-31
```

A janela é **inclusiva nos dois extremos** e incide na data a que a linha diz
respeito. Sem nenhuma flag, as secções do registo leem o registo inteiro — exceto
o ciclo, que pede a resposta à rede e por isso assume os últimos 30 dias, dizendo
isso no próprio cabeçalho em vez de estreitar em silêncio.

### Custo e Tarifas

A secção de custo transforma tokens em dinheiro com duas camadas, a segunda a
sobrepor-se à primeira por modelo:

1. **Uma tabela incorporada** com os preços de tabela publicados pelos
   fornecedores para os IDs de modelo fixos que o GitPR acompanha
   (`deepseek-v4-flash`, `deepseek-v4-pro`, `gemini-2.5-pro`,
   `gemini-2.5-flash-lite`), para que a secção diga algo numa máquina que ninguém
   configurou.
2. **O ambiente**, por modelo:

```ini
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT=0.435
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT=0.87
GITPR_METRICS_CURRENCY=USD
```

`<MODEL>` é o nome do modelo em maiúsculas, com cada sequência de caracteres que
não seja letra ou dígito colapsada num `_`. As duas tarifas são obrigatórias: um
modelo com apenas uma delas é reportado só em tokens, porque tarifar a outra
metade com um zero não configurado subestimaria a conta.

- **A moeda predefinida é USD**, que é a moeda em que a tabela incorporada está
  cotada. Configure tarifas noutra moeda e aponte `GITPR_METRICS_CURRENCY` para
  ela — a tabela incorporada sai então de cena, porque uma tarifa em dólares
  impressa sob o rótulo de outra moeda é um número errado, não um número ausente.
- **Fornecedores que correm nesta máquina** (`ollama`, `local`) custam zero por
  definição e não precisam de tarifa.
- **As tarifas mudam.** Converter tokens gastos no ano passado pelo preço de hoje
  é uma aproximação, e a secção di-lo na linha abaixo do total.
- **Um total que deixa modelos de fora avisa** — `Total (parcial)` — em vez de
  deixar uma soma das linhas tarifadas parecer a conta inteira.

### A Métrica de Ciclo

A secção ⏱ é a única métrica aqui que não vem do registo, e não tem como vir: o
registo regista o que o GitPR correu nesta máquina, enquanto um pull request é
integrado na forja, por pessoas que nunca correram o GitPR. Por isso esta precisa
de token e de rede, e é a única secção que pode voltar sem nada por um motivo que
não é "nada aconteceu".

Mede `created_at → merged_at` dos pull requests que a forja reporta com merge na
janela — **o ciclo do próprio pull request**, da abertura ao merge. Não é o tempo
do primeiro commit de uma branch até ao seu pull request: o contrato de listagem
não transporta commits de branch, por isso esse intervalo não está disponível
aqui, e também não é inventado a partir do registo.

O cabeçalho nomeia o repositório e a janela — `⏱ Ciclo · dono/repo · últimos 30
dias` — porque esta é a única secção cujo âmbito não é o do registo: lida ao lado
de um resumo que diz "Todos os repositórios", um número solto pareceria cobri-los
todos.

Toda a falha degrada numa linha, nunca num stack trace:

| O que aconteceu | O que a secção mostra |
|-----------------|-----------------------|
| Sem remote origin, sem forja utilizável, sem token, sem rede | `Não lido: <o motivo>` |
| A forja não publica data de merge (Bitbucket) | Di-lo, sem gastar uma chamada de rede |
| A janela não tem nenhum pull request com merge | `Nenhum pull request teve merge nesta janela.` |

Um merge cuja data precede a própria criação é um relógio que a forja errou, não
um ciclo negativo: essa linha é descartada em vez de entrar na média.

### Exportar Dados

```bash
gitpr metrics export
```

Grava em CSV e JSON as linhas que nunca foram exportadas, em
`./.gitpr/metrics/export/`, e marca-as de seguida como exportadas — por isso uma
segunda execução responde "Nenhuma métrica nova para exportar." em vez de se
repetir. A exportação abrange o repositório da cópia de trabalho.

- **Colunas CSV:** timestamp, day, command, status, provider, model,
  prompt_tokens, completion_tokens, tokens_actual, tokens_estimated, duration_ms,
  repo, branch, author_name, modules, cache_hit, map_reduce, linter_errors,
  linter_warnings, chunks_count, source
- **JSON:** as mesmas linhas como objetos, prontas a serem lidas por um script

### Bundle e Merge (Consolidação de Equipa)

`export` é o que uma pessoa lê; um **bundle** é o que outra máquina lê — o mesmo
recorte do registo como um ficheiro `.db` autónomo:

```bash
gitpr metrics bundle --days 30
gitpr metrics bundle --since 2026-07-01 --until 2026-09-30 -o ./entrega/
gitpr metrics merge ./entrega/gitpr_metrics_2026-09-29.db ./entrega/outro.db
```

`bundle` copia as linhas da janela para um ficheiro SQLite independente, com
esquema e `PRAGMA user_version` incluídos, e grava em `./.gitpr/metrics/export/`
a menos que `-o` diga outra coisa. `merge` anexa cada bundle e insere as linhas
que ainda não tem — o UUID é a chave primária, por isso fundir o mesmo ficheiro
duas vezes, ou dois bundles sobrepostos, nunca conta uma execução a dobrar.

As versões de esquema são tratadas **numa só direção**: um bundle mais antigo é
migrado para cima ao ser anexado, e um mais recente é recusado *antes* de qualquer
escrita, com a versão que transporta e a que este GitPR entende — o registo local
nunca fica meio importado. Atualize o GitPR para ler um bundle mais recente.

Esta é a resposta a "quanto gastou a equipa no trimestre" sem servidor: cada
máquina empacota a sua janela, e quem precisa do total funde os ficheiros num
registo próprio.

### Importar Dados Anteriores ao Registo

```bash
gitpr metrics migrate
```

Lê os ficheiros de evento escritos antes de o registo existir, insere-os e move
os originais para `~/.gitpr/metrics_legacy/`. Com um terminal, abre um assistente
que oferece também reconstruir o histórico a partir da cache de respostas da IA.
Essas linhas ficam marcadas com `source: cache_backfill` porque a cache indexa uma
resposta pelo seu prompt e, por isso, conta **prompts distintos, não execuções**.

### Eliminar Registos Antigos

```bash
gitpr metrics prune --before 2026-01-01
```

Elimina as linhas escritas antes de uma data, após confirmação, e recupera o
espaço com `VACUUM`. `--source cache_backfill` restringe a eliminação às linhas
reconstruídas. **Não existe expiração automática**: o registo responde "quanto
gastámos neste ano", e um calendário que elimina sozinho mudaria essa resposta sem
ninguém pedir.

### Limpar Dados

```bash
gitpr metrics purge
```

O caminho destrutivo: elimina todas as linhas e todos os ficheiros de evento que
ainda aguardam importação, após confirmação.

### Dashboard Interativo

```bash
gitpr metrics dashboard
```

Abre um **dashboard TUI** (Textual) restrito ao repositório da cópia de trabalho:

- **Barra de resumo:** total de entradas, linhas reconstruídas, total de tokens, duração total, top comandos
- **Tabela de eventos:** timestamp, comando, estado, provedor, tokens, duração
- **Secções:** custo, qualidade, módulos, fornecedores e o ciclo — as mesmas linhas
  que `gitpr metrics` imprime, desenhadas com markup do Textual em vez das cores
  do click
- **Barra de estado:** o intervalo de tempo que a tabela cobre e quantas entradas tem
- **Atalhos:** `F5` para atualizar, `Esc` para sair

Enquanto o registo ainda não existir, o dashboard lê a cache e os ficheiros de
evento, mostra uma barra de progresso durante a varredura e indica isso na barra
de estado.

A secção de ciclo é desenhada de qualquer forma: ela nunca leu o registo.

## 🔧 Git Hooks (Recolha Automática)

Quando instalados via `gitpr --installhooks`, três hooks adicionais recolhem
telemetria comportamental:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Trocas de branch (mudanças de contexto) — dispara apenas quando a branch mudou mesmo |
| `pre-push` | Eventos de push (frequência de entrega) |
| `post-merge` | Eventos de pull/merge (frequência de integração) |

Os três executam `gitpr --quiet metrics hook-event <nome>`, uma ação oculta cuja
única tarefa é gravar uma linha e sair. O repositório é resolvido pelo próprio
hook, pelo mesmo parser que o resto da CLI usa, pelo que GitLab, Bitbucket e Azure
DevOps registam o mesmo `dono/nome` que o GitHub. Uma guarda em volta da chamada
— `command -v gitpr`, mais um `|| true` no final — impede que uma máquina sem o
GitPR, ou com um GitPR que falha, quebre o seu comando Git.

## 📊 Casos de Uso

- **Tech Lead:** Ver que repositórios, branches e autores usam realmente revisões de IA, e que hooks disparam
- **Finanças:** Ler a secção de custo para a conta por modelo, ou `gitpr metrics --since 2026-07-01` para o trimestre
- **Qualidade:** Ler `linter_errors`, `linter_warnings` e `modules` para encontrar que parte do projeto gera mais achados
- **Processo:** Observar `map_reduce` e `chunks_count` — PRs grandes a disparar o caminho map-reduce apontam um problema de processo
- **Entrega:** Ler a secção de ciclo para ver quanto demoraram os pull requests com merge deste repositório, e quais demoraram mais

## 🔒 Privacidade

- **100% local** — o registo é um ficheiro na sua máquina; nada dele é enviado para servidores externos
- **A única exceção é a secção de ciclo** — pede à forja configurada os pull requests com merge do repositório onde está. Não envia nenhuma linha do registo, nenhuma contagem de tokens e nenhum diff: a pergunta é "que pull requests tiveram merge nesta janela", e a resposta é só de leitura
- **Não é anónimo** — cada linha transporta o repositório, a branch e o nome do autor Git local. Não transporta conteúdo de ficheiros nem diffs: `modules` guarda os segmentos de caminho que uma execução tocou, nunca os nomes dos ficheiros, e o e-mail do autor fica na cache de IA
- **Controlo do utilizador** — `prune` e `purge` são manuais e confirmados; nada expira sozinho
- **Hooks opcionais** — git hooks só instalam se executar `gitpr --installhooks`

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Configuração do servidor MCP
- [MCP Prompts](mcp-prompts.md) — Modelos de mensagem pré-definidos
- [MCP Tool Annotations](mcp-annotations.md) — Dicas de integração com IDEs

---
**Dica profissional:** As exportações ficam em `./.gitpr/metrics/export/`, dentro do
repositório onde está — esse diretório pertence à sua máquina, não ao projeto, e é
o que a entrada do `.gitignore` do próprio GitPR mantém fora da árvore. Para
responder "quanto gastou esta máquina neste trimestre" sem folha de cálculo,
pergunte ao registo: `gitpr metrics --since 2026-07-01`.
