# ADR-008 — O ledger de uso é um banco SQLite, uma linha por execução, escrito de forma síncrona

- **Status:** Aceito
- **Data:** 2026-09-27
- **Contexto:** auditoria da feature `metrics` ([survey](../../survey/20260927_metrics_audit_surveyfacts.md) §2, §3); grill rodadas 1–11
- **Glossário:** [glossary-metrics-telemetry.md](glossary-metrics-telemetry.md)
- **Plano:** [20260927_metrics_audit_plansfacts.md](develop_natan/20260927_metrics_audit_plansfacts.md)

## Contexto

A telemetria do GitPR foi entregue com **duas** fontes de dados e nunca decidiu qual delas era a verdade.

A primeira são arquivos de evento JSON, um por comando executado, em `~/.gitpr/metrics/{owner}/{branch}/{uuid}_{data}.json` — a forma que o plano mestre desenhou. A segunda é o cache de respostas da IA (`~/.gitpr/cache/prompts/{action}/{md5}.json`), que o dashboard passou a privilegiar porque é a única fonte com **tokens reais, modelo, duração e autor**: esses metadados chegam da própria API do provedor ([src/ai_providers.py:139-213](../src/ai_providers.py#L139-L213)) e são gravados em `response._telemetry_meta`.

A escolha parecia óbvia — a fonte com os dados melhores é a fonte melhor — e está errada por uma razão de forma, não de conteúdo: **`save_cached_response()` grava em `{md5(prompt)}.json`, e no cache hit o `core.py` retorna antes de regravar** ([src/core.py:976-989](../src/core.py#L976-L989)). Execuções idênticas repetidas colapsam numa linha só. O cache conta **prompts distintos**; a pergunta que a feature existe para responder é **quantas vezes**. Cinco revisões iguais de um mesmo diff são uma linha no cache e cinco comandos na vida real.

Os arquivos de evento têm a propriedade oposta e a pagam: são 1-por-execução por construção, e por isso veem também o que não passa por IA (linter, blame, hooks), o cache hit e o erro. O que eles não têm, os metadados do provedor, só existe no cache.

Três defeitos verificados nascem dessa indefinição. O **G1**: `export_metrics()` montava a lista de arquivos de **todos** os donos, filtrava os eventos por repo e gravava no estado global os UUIDs de todos — exportar no repo A marcava os eventos do repo B como exportados, permanentemente e em silêncio ([src/metrics.py:309-320](../src/metrics.py#L309-L320) contra [:381-385](../src/metrics.py#L381-L385)). O **G2**: como o join entre as duas fontes era feito *depois*, por proximidade de minuto, ele dependia de um mapa de pastas de cache que existia em **três cópias divergentes** ([src/metrics.py:168-175](../src/metrics.py#L168-L175), [:533-540](../src/metrics.py#L533-L540), [src/ui/metrics_app.py:249-256](../src/ui/metrics_app.py#L249-L256); a verdade está em [src/core.py:864-865](../src/core.py#L864-L865)) — e duas delas apontavam `fullreview`/`filereview` para pastas que não existem, então `tokens_actual` era sempre zero nesses comandos. O **G3**: a gravação era fire-and-forget numa thread daemon ([src/metrics.py:30-69](../src/metrics.py#L30-L69)), e o processo inteiro do `--hook-event` é "inicia → dispara → sai" — o interpretador encerra antes de a thread ser escalonada, e o evento se perde. O risco não era hipotético: o [src/usage_log.py](../src/usage_log.py) documenta exatamente esse risco no próprio docstring e por isso sempre gravou de forma síncrona.

O estado acumulado mostrava o custo da ausência de política: **1749 arquivos, 488 KB, nenhuma rotação**, contados recursivamente por `show_metrics_summary()` ([src/metrics.py:452-460](../src/metrics.py#L452-L460)) — que ainda incluía o próprio `config.json` na conta.

## Decisão

### 1. Uma linha por execução, não por prompt

O ledger é o registro de **execuções**. O cache continua existindo com o papel que sempre teve — evitar chamadas repetidas à IA — e passa a ser consultado **na hora da escrita**, como fonte de metadados, nunca como registro de uso.

A consequência é que os agregados de uso (frequência, custo, tendência, provedor, modelo) leem o ledger, e o cache não é mais uma segunda via de leitura. O fallback de varredura do cache sobrevive por uma única razão, com critério objetivo de saída: é a **ponte** para quem ainda não tem banco (R5.1), e pode ser deletado no dia em que todo mundo tiver.

### 2. SQLite local, em `~/.gitpr/metrics/telemetry.db`

Banco embutido da stdlib, sem dependência nova. A escolha foi feita **contra** a recomendação técnica de manter o formato de arquivo (JSONL append-only), por três razões que só aparecem quando o ledger deixa de ser um log e passa a ser a verdade de custo e de time:

- **Deduplicação do merge é do banco, não do código.** A chave primária é o UUID do evento, então a agregação multi-máquina é `ATTACH` + `INSERT OR IGNORE` (R4.1). Com arquivos, cada merge exigiria reimplementar identidade e conflito em Python.
- **Retenção é um `DELETE` por data** (R7.3), não uma varredura de 1749 arquivos sem política.
- **Concorrência.** Hooks e CLI podem escrever ao mesmo tempo; o WAL resolve. Append concorrente de JSONL entre processos era risco real, sobretudo no Windows.

O guardrail vem junto e é do mesmo peso que a decisão: **o `.db` é detalhe de implementação e nunca a interface.** O CSV/JSON do `--metrics --export` permanece como a visão humana e a interface pública da feature (R3.2) — um banco binário não se abre num leitor de planilha. O transporte entre máquinas sai por uma flag própria, `gitpr metrics bundle` (R9.4), e é o **único** caminho que escreve um binário no diretório de trabalho.

### 3. Escrita síncrona, com o contexto git resolvido uma vez por processo

A gravação deixa de ser fire-and-forget. O contexto git (repo, branch, autor) é resolvido uma vez por processo e reusado por todos os eventos daquela execução, de modo que o custo não cresce com o número de gravações.

Isso **inverte um teste existente**: `test_runs_in_background_thread` assere `daemon is True` hoje, e passará a asserir que nada é perdido quando o processo encerra imediatamente após o disparo — que é o caso dos hooks, e a razão de a mudança existir.

### 4. Enriquecer na escrita, nunca por join posterior

Tokens, modelo, duração e provedor são copiados do `meta_raw` para dentro do evento no caminho de sucesso. `enrich_metrics_from_cache()` e o join difuso por minuto são **deletados**.

Copiar na escrita não é otimização: elimina a classe inteira de defeito a que o G2 pertence. Um join por proximidade de minuto depende de duas coisas que não se sustentam — que o mapa de pastas esteja correto em todo lugar que o consulta, e que o evento e a linha de cache sejam o mesmo comando. Nenhuma das duas é verificável de fora. Copiar na escrita não tem mapa para divergir nem minuto para coincidir.

### 5. `source` distingue execução de reconstrução

Cada linha carrega `source`: `execution` (observada) ou `cache_backfill` (reconstruída do cache). As duas convivem na mesma tabela e **não** convivem nos mesmos agregados (R10.1).

É a válvula que permite oferecer histórico a quem chega depois sem contaminar a contagem: a linha reconstruída responde "o que existiu no passado" e nunca "quantas vezes rodou". Sem essa coluna, ou o backfill não existiria, ou existiria mentindo.

## Consequências

- **O ledger nasce junto com a absorção, nunca antes.** É a invariante que impede o G1 de se repetir por outra via: não existe estado em que o ledger cale o fallback de varredura sem ter absorvido os arquivos (R8.2 + R11.1). Em modo não-interativo com arquivos presentes, a criação e a importação acontecem em silêncio, com progresso textual em **stderr** — o stdout do `gitpr-mcp` pertence ao fluxo JSON-RPC.
- **Os originais são movidos, nunca apagados** (R6.4), e para **fora** de `metrics_dir`: verificado que a contagem é recursiva, então uma pasta de legado dentro de `~/metrics/` dobraria o G7 em vez de resolvê-lo.
- **O `config.json` de UUIDs exportados deixa de existir.** O G1 não é corrigido, é removido: o controle de exportação vira consulta, e não há estado global para desincronizar.
- **O `--prune` passa a ser o único caminho destrutivo** além do `--purge`, ambos com confirmação. Deliberadamente **não** há expiração automática (R7.3): apagar por calendário mudaria sozinho a resposta de "quanto gastamos no ano".
- **O evento cresce com o diff.** Os módulos tocados entram como lista, normalizada nos dois primeiros segmentos (R6.1) e **sem teto** (R7.2): uma refatoração ampla carrega dezenas de módulos para dentro do `.db` que viaja no merge. Como o campo é lista, um teto pode ser acrescentado depois sem migração de schema.
- **Risco operacional aceito:** a migração dos 1749 arquivos legados passa a ser pré-requisito de qualquer leitura do dashboard. Um banco meio-absorvido é pior do que nenhum, e por isso a importação só marca o banco como pronto ao final.
- **Ponto cego aceito:** o ledger mede o uso **nesta máquina**. A visão de equipe depende de alguém rodar `bundle` e `merge` — não há sincronização automática, e não há como haver sem servidor.
- **A proximidade com o `usage_log.py` é permanente e precisa de disciplina.** Duas superfícies gravam por execução, em momentos diferentes e com propósitos diferentes: o ledger mede, o log audita. Convergir economizaria código e custaria a promessa de uma das duas (R3.4).

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| **Reusar o cache de IA como ledger** | Conta prompts distintos, não execuções — não há conserto de schema: a chave do cache *é* o conteúdo do prompt. E não vê comando sem IA, cache hit nem erro |
| **JSONL append-only** (recomendação técnica inicial) | Dedup do merge viraria código nosso; retenção viraria varredura; append concorrente entre hooks e CLI sem garantia, sobretudo no Windows |
| **Arquivos de evento, só corrigindo os defeitos** | Mantém 1749 arquivos sem política, o `config.json` de estado global (G1) e o join difuso (G2). Corrige a superfície e conserva a causa |
| **Manter as duas fontes como pares** (o estado entregue) | É a origem dos três defeitos. Duas fontes com papéis não-declarados não são redundância, são ambiguidade |
| **Enriquecer o evento depois, por join por chave exata** | Trocaria o join por minuto por um join por hash de prompt — e o evento passaria a precisar carregar o hash do prompt que ele não conhece. Copiar na escrita é o mesmo trabalho, feito no único momento em que os dois dados estão na mesma mão |
| **SQLite como interface** (exportar `.db` como produto) | Um binário opaco não é visão humana; o time lê planilha. Só o `bundle` escreve binário, e só para transportar |
| **Expiração automática por retenção** | Apagaria história de custo por calendário, mudando sozinho a resposta de períodos passados. `prune` explícito com confirmação cobre o mesmo risco sem a surpresa |
| **Servidor/telemetria remota** | Contraria a promessa da feature: telemetria **local**, sob controle de quem a gera |
