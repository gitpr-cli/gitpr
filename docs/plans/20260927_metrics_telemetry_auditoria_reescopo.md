# Metrics & Telemetry — Auditoria + Re-escopo (branch `develop_natan`)

## Context

A feature `metrics`/`telemetry` do GitPR foi desenvolvida entre 2026-07-26 e 2026-08-18
(7 commits), declarada concluída e **encerrada**. O pedido desta sessão é auditar o que
foi pedido × o que foi entregue, e entrevistar o autor para verificar se o resultado
está em sintonia com a intenção original do produto.

Esta sessão é de **levantamento + entrevista**. Nenhum código será alterado até o
entendimento compartilhado ser confirmado.

> **Nota de baseline:** o arquivo indicado pelo usuário
> (`docs/claude-code/reports/develop_natan/2026-07-26_metrics_telemetry.md`) é um
> **Relatório de Conclusão**, não o plano. Existem três camadas de "o que foi pedido",
> e a auditoria usa as três:
> 1. **Conceito** — `docs/plans/metricas_analytics_dashboard.md` (8 métricas candidatas, 5 fases)
> 2. **Plano mestre** — `docs/plans/plano_metricas_telemetria.md` (5 fases, schema JSON, CLI, 9 chaves i18n)
> 3. **Relatório** — `2026-07-26_metrics_telemetry.md` (declara fases 2-5 feitas + 4 "next steps")

---

## 1. O que foi entregue (verificado no código)

| Camada                | Entrega                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Plano mestre, 5 fases | **Todas implementadas** — e ultrapassadas por 5 ciclos de correção posteriores (2026-08-02 ×3, 08-05, 08-15/08-18) |
| Código                | `src/metrics.py` (628 linhas), `src/ui/metrics_app.py` (450), 34 call sites de métrica em 11+ arquivos             |
| CLI                   | `--metrics`, `--metrics --export`, `--metrics --purge`, `--dashboard`, `--hook-event` (oculto)                     |
| Hooks                 | 3 templates × 5 idiomas em `scripts/`                                                                              |
| Testes                | 45 testes em 3 arquivos (`test_metrics.py` 34, `test_blame_metrics.py` 7, `test_linter_metrics.py` 4)              |
| Docs                  | `docs/metricas-telemetria.md` + 4 traduções; README ×5; ARCHITECTURE ×5; HELP_MAP                                  |
| i18n                  | 17 chaves de métricas em cada um dos 6 arquivos de idioma                                                          |

**O relatório de 2026-07-26 está desatualizado.** Seu "Next steps" diz "adicionar
cobertura de testes para `export_metrics()`, `purge_metrics()` e `MetricsApp`" —
**isso foi feito** (34 testes). O que sobrou real dos 4 next steps é só o `--metrics --serve`
(que era um "considerar", não um requisito).

### Arquitetura real (diverge do plano: são DOIS armazenamentos)

```
Fonte A — arquivos de evento (o que o plano desenhou)
  ~/.gitpr/metrics/{owner}/{branch}/{uuid15}_{YYYYMMDD}.json
  gravado por log_local_metric() em thread daemon  [fire-and-forget]
  lido por: --metrics (resumo), --export, --purge, --dashboard

Fonte B — cache de resposta da IA (o que o dashboard privilegia)
  ~/.gitpr/cache/prompts/{action}/{md5}.json  →  response.meta_raw
  gravado por save_cached_response() (síncrono)
  lido por: --dashboard, enrich_metrics_from_cache()

Fonte C — log de uso em texto (feature irmã, NÃO é a métricas)
  ~/.gitpr/logs/{uuid5}.log   ←  src/usage_log.py, escrito de forma SÍNCRONA

O dashboard LÊ AS DUAS (A + B) e faz merge por (repo, branch, command, minuto).
O --export lê só A, e tenta enriquecer com B por join difuso.
```

A Fonte B é a **única com tokens reais, `duration_ms`, `model` e autor**; a Fonte A é a
única que vê **comandos sem IA** (linter, blame, hooks), **cache hits** e **erros**.

---

## 2. Defeitos e lacunas confirmados (verificados no código)

| #   | Severidade                                                | Achado                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | Evidência                                                                                               |
| --- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| G1  | **Alta — perda de dados**                                 | `export_metrics()` monta `all_files` de **todos os donos**, filtra `events` por repo, mas grava no `config.json` global os UUIDs de **todos** os `all_files`. Como `main.py` sempre passa `repo_filter=get_repo_name()`, exportar no repo A marca os eventos do repo B como exportados — e o export do repo B responde "No new metrics to export." **Perda permanente e silenciosa.**                                                                                                                                                          | `src/metrics.py:309-320` vs `:339-342` vs `:381-385`                                                    |
| G2  | Média                                                     | `enrich_metrics_from_cache()` mapeia `fullreview→fullreview` e `filereview→filereview`, mas a pasta real de cache é `review`. **O join nunca casa para esses dois comandos** → `tokens_actual` sempre 0 no CSV. São **3 cópias divergentes** do mesmo mapa (a terceira, em `metrics_app._merge_rows`, está correta).                                                                                                                                                                                                                           | `src/metrics.py:168-175`, `:533-540`, `src/ui/metrics_app.py:249-256`, verdade em `src/core.py:864-865` |
| G3  | Média                                                     | `log_local_metric()` grava em **thread daemon** — o interpretador pode encerrar antes. O caminho mais exposto é `gitpr --hook-event` (`main.py:651-656`), cujo processo inteiro é "inicia → dispara → sai": exatamente o caso de uso dos hooks. O `src/usage_log.py` documenta esse mesmo risco no próprio docstring e por isso grava de forma síncrona. O comportamento está **travado por teste** (`test_runs_in_background_thread` asserta `daemon is True`).                                                                               | `src/metrics.py:30-69`, `src/usage_log.py` (docstring), `tests/test_metrics.py`                         |
| G4  | Média                                                     | **Hooks inconsistentes.** `post-merge` (5 idiomas) chama `gitpr --hook-event`; `post-checkout` e `pre-push` (10 arquivos) gravam JSON direto via heredoc bash, sem `gitpr`. A doc afirma que "estes hooks usam `gitpr --hook-event <name> --quiet`" — falso para 2 de 3.                                                                                                                                                                                                                                                                       | `scripts/*.sh`, `docs/metricas-telemetria.md:96`                                                        |
| G5  | Média                                                     | **Hooks são invisíveis fora do GitHub.** O bash calcula `REPO` com `grep github\.com`, caindo para `basename` (nome sem owner) em GitLab/Bitbucket/Azure; o filtro do dashboard usa `get_repo_name()`, que também é GitHub-only e devolve `unknown/repo`. Os dois não casam → o evento é descartado.                                                                                                                                                                                                                                           | `scripts/post-checkout-template.sh:12`, `src/core.py:685-705`, `src/ui/metrics_app.py:214-216`          |
| G6  | Média                                                     | **Docs contradizem o código** (nas 5 línguas): CSV documentado com 8 colunas (o código escreve 11); export documentado em `~/.gitpr/metrics/export/` (o código escreve em `./.gitpr/metrics/export/`); "last 100 events" (não há limite); resumo com "errors" e "top providers" (não existem — o real é Total entries / Cache files / Tokens / Total duration / Top commands); nome de arquivo `XXXX-XXXXX-XXXX_20260726.json` (real: `{uuid15}_{YYYYMMDD}.json`).                                                                             | `docs/metricas-telemetria.md` vs `src/metrics.py`, `src/ui/metrics_app.py`                              |
| G7  | Baixa                                                     | `show_metrics_summary()` conta **todo** `*.json`, incluindo o `config.json` → `total_files` superestimado em 1. Medição real nesta máquina: `total_files: 1749`, `total_events: 8`, `488.4 KB` — **1749 eventos acumulados e nenhuma rotação/retenção**.                                                                                                                                                                                                                                                                                       | `src/metrics.py:452-460`                                                                                |
| G8  | Baixa                                                     | `--dashboard` **não tem entrada no HELP_MAP** → `gitpr -h --dashboard` cai no help genérico. `--metrics` tem.                                                                                                                                                                                                                                                                                                                                                                                                                                  | `src/main.py:187-191`, `:267`                                                                           |
| G9  | Baixa                                                     | `load_cache_token_summary()` é **código morto em produção** — definido e testado, mas nenhum arquivo em `src/` o chama. Foi criado para o "totalizador faltando commits" e nunca foi ligado.                                                                                                                                                                                                                                                                                                                                                   | `src/metrics.py:216`, só `tests/test_metrics.py` o importa                                              |
| G10 | Baixa                                                     | **Sem cobertura de teste** para `scan_cache_files_for_dashboard()` e para o rastreio `processed_cache.json` — justamente a superfície mais nova.                                                                                                                                                                                                                                                                                                                                                                                               | `tests/`                                                                                                |
| G11 | Baixa                                                     | `./.gitpr/` **não está no `.gitignore`** → `gitpr --metrics --export` dentro de um repo cria `./.gitpr/metrics/export/*.csv` e `./.gitpr/metrics/{repo}/processed_cache.json` prontos para commit acidental. Obs.: `.gitpr/skill/` é conteúdo intencional, então um ignore cego de `.gitpr/` não serve.                                                                                                                                                                                                                                        | `.gitignore`                                                                                            |
| G12 | Baixa                                                     | `_get_owner_name()` chama `subprocess.run(..., text=True)` **sem `encoding='utf-8', errors='replace'`** — viola regra do CLAUDE.md. `get_repo_name()`/`get_current_branch()` (chamados pela métrica) também não passam `errors='replace'` (pré-existente).                                                                                                                                                                                                                                                                                     | `src/metrics.py:18-25`, `src/core.py:669-705`                                                           |
| G13 | Baixa                                                     | Nenhum evento carrega **autor**. O plano pedia coluna `author` no CSV; o dado existe (`author_name`/`author_email` no cache), mas não chega ao evento nem ao CSV.                                                                                                                                                                                                                                                                                                                                                                              | `src/metrics.py:51-65` vs `src/cache.py:80-93`                                                          |
| G14 | Baixa                                                     | CHANGELOG v0.0.32 cita `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()` — **funções que não existem**; o código usa `log_local_metric`/`log_command_metric`.                                                                                                                                                                                                                                                                                                                                                                    | `CHANGELOG.md`                                                                                          |
| G15 | **Média — feature adjacente (release), achado pela R6.2** | A correlação de PR do motor de release é **só para squash-merge**: `_extract_pr_number()` lê o sufixo `(#123)`, e o `changelog_builder` só renderiza `· [#n](url)` quando ele existe. **Este repositório não faz squash** — faz merge commit (`Merge pull request #193 from gitpr-cli/develop_natan`, 19 ocorrências). Resultado: `pr_number` é sempre `None` e o segmento de PR documentado no CLAUDE.md **nunca apareceu em nenhum CHANGELOG** (`grep -c 'pull/' CHANGELOG.md` = 0). Fora do escopo da métricas, salvo decisão em contrário. | `src/commit_classifier.py:13,98,128`, `src/changelog_builder.py:150-157`, `CHANGELOG.md`                |

---

## 3. Conceito × Realidade — as 8 métricas prometidas

| #   | Métrica do doc de conceito                            | Status                                                                                                                       |
| --- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 1   | Frequência de code reviews (dia/semana)               | ✅ Respondível (linhas do cache por timestamp)                                                                                |
| 2   | Taxa de aprovação do linter (%)                       | ⚠️ Parcial — `linter_errors`/`linter_warnings` são gravados, mas **nenhuma taxa é calculada ou exibida**                      |
| 3   | Uso de IA por funcionalidade                          | ✅ "Top commands"                                                                                                             |
| 4   | Provedores mais usados                                | ❌ **Não existe** — a doc promete "top providers", o resumo não tem quebra por provedor                                       |
| 5   | Tempo médio entre commit e PR                         | ❌ Sem dado que ligue commit a PR                                                                                             |
| 6   | Tokens consumidos por sprint (custo)                  | ⚠️ Total de tokens existe; **sem janela de sprint e sem conversão para R$/US$**                                               |
| 7   | Dívida técnica rastreada (issues de blame por módulo) | ❌ Sem granularidade de módulo — blame grava `commits_analyzed`, e a abertura de issue grava `issue:github_create` sem módulo |
| 8   | Map-Reduce ativado (%)                                | ⚠️ `map_reduce_triggered` é gravado, mas **nenhuma taxa é computada/exibida**                                                 |

**Resumo: 2 de 8 completas, 3 parciais, 3 ausentes.**

---

## 4. Árvore de decisão

### Rodada 1 — decidida

| #    | Pergunta                      | Resposta                                                                                      |
| ---- | ----------------------------- | --------------------------------------------------------------------------------------------- |
| R1.1 | Job-to-be-done / quem consome | **Os três, sem hierarquia** — dev + gestão de time + controle de custo                        |
| R1.2 | Direção                       | **Os dois, em ondas** — Onda 1: verdade + correções · Onda 2: construir as métricas faltantes |
| R1.3 | O que "métricas" nomeia       | **Quatro superfícies, cada uma nomeada** — eventos, cache de IA, log de uso/auditoria, export |

**Consequências de R1.1 (promovem itens de "desejável" para "requisito"):**
- Autoria nos eventos (hoje inexistente — G13)
- Agregação multi-máquina (hoje inexistente — sem comando de merge)
- Conversão de tokens em dinheiro + janela de sprint (hoje inexistente)
- Quebra por provedor e por modelo (hoje inexistente — a doc promete)
- Rotação/retenção (1749 eventos acumulados, 488 KB, zero política)

**Consequências de R1.3:** produzir um glossário no padrão do repo
(`docs/plans/glossary-*.md` — já existem 8) nomeando as quatro superfícies, e
avaliar um ADR para a escolha de ledger (atende os 3 critérios: difícil reverter,
surpreendente sem contexto, trade-off real). Nota: o repo **não tem** `CONTEXT.md`
nem `docs/adr/` — a convenção local é `docs/plans/`.

### Evidência nova — o cache NÃO serve como ledger de uso

`save_cached_response()` grava em `{md5(prompt)}.json`. No cache hit, `core.py`
retorna **antes** de salvar. Logo **execuções idênticas repetidas colapsam em uma
única linha** — o cache conta *prompts distintos*, não *execuções*. Só os arquivos
de evento são 1-por-execução (`{uuid}_{data}.json`). Isso decide a Rodada 2 em favor
dos eventos como ledger.

### Rodada 2 — decidida

| #    | Pergunta            | Resposta                                                                                                                                                                                                                                         |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R2.1 | Ledger canônico     | **Eventos = ledger por execução; cache enriquece.** Tokens reais, duração, provedor e modelo copiados do `meta_raw` **para dentro do evento na hora da escrita**; o join difuso por minuto é **deletado** (G2 morre junto com o mapa divergente) |
| R2.2 | Atribuição          | **`author_login` + `author_name`, sem e-mail.** O e-mail permanece só no cache. A doc troca "anônimo" por "local e sob seu controle"                                                                                                             |
| R2.3 | Hooks               | **Unificar os três em `gitpr --hook-event`**, resolvendo o repo por `parse_repo_ref()` ([infrastructure/scm/](src/infrastructure/scm/)), com guarda `command -v gitpr` + `                                                                       |  | true` |
| R2.4 | Agregação de equipe | **`gitpr --metrics --merge <arquivos>`**, deduplicando por UUID                                                                                                                                                                                  |

**Consequências encadeadas de R2.1 (a confirmar na Rodada 3):**
- O `config.json` de UUIDs exportados pode deixar de existir → **G1 deixa de ser um bug a corrigir e vira código removido**
- O dashboard pode parar de varrer o cache (hoje: filtro "desde 1º de janeiro", `processed_cache.json`, barra de progresso, 1749 arquivos) → **os outros 2 mapas de pasta de cache também morrem**
- A durabilidade do daemon fire-and-forget passa de "detalhe" a **defeito de correção** — o ledger agora é a verdade de custo e de time

### Rodada 3 — decidida

| #    | Pergunta                | Resposta                                                                                                                  |
| ---- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| R3.1 | Durabilidade            | **Escrita síncrona**, com o contexto git resolvido uma vez por processo. Inverte o teste que hoje assere `daemon is True` |
| R3.2 | Forma física            | **SQLite local** — `~/.gitpr/metrics/telemetry.db` (escolha do usuário, contra a recomendação de JSONL)                   |
| R3.3 | Histórico               | **Comando de backfill a partir do cache**, marcando `source: "cache_backfill"`                                            |
| R3.4 | `usage_log.py` × ledger | **Separados, com os papéis escritos no glossário** (auditoria × telemetria)                                               |

**Consequências de R3.2 (SQLite) — o que muda em relação ao plano anterior:**
- **G1 deixa de existir como bug**: o controle de export vira `WHERE exported_at IS NULL` (ou corte por data); o state file de UUIDs e a lista de `all_files` são removidos, não corrigidos
- **Dedup do merge fica grátis**: UUID como chave primária → `INSERT OR IGNORE`
- **Retenção vira um `DELETE`** por data — resolve os 1749 arquivos sem política
- **Concorrência resolvida**: hooks e CLI podem escrever ao mesmo tempo (WAL); append de JSONL entre processos concorrentes era risco real, sobretudo no Windows
- **Guardrail necessário**: o `.db` é binário e opaco. O `--export` CSV/JSON **permanece** como a visão humana e a interface pública; o banco é detalhe de implementação, nunca a interface
- **Risco novo**: a migração dos 1749 eventos antigos + o backfill passam a ser pré-requisito de qualquer leitura do dashboard

### Rodada 4 — decidida

| #    | Pergunta            | Resposta                                                                                                                                               |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R4.1 | Transporte do merge | **Export = `.db` recortado** por repo e período; `--merge` via `ATTACH` + `INSERT OR IGNORE`. CSV/JSON continua como visão humana, não como transporte |
| R4.2 | Identidade do repo  | **`parse_repo_ref()`** no ledger, igual aos hooks — uma identidade só, multi-forge                                                                     |
| R4.3 | Varredura do cache  | **Mantida como fallback** (escolha do usuário, contra a recomendação)                                                                                  |
| R4.4 | Migração × ondas    | **Onda 1 = verdade + migração juntas**                                                                                                                 |

**Consequências de R4.3 (fallback mantido):**
- Os **dois mapas divergentes de pasta de cache sobrevivem** → consolidar num único mapa compartilhado passa a ser **requisito**, não limpeza opcional (G2)
- Surge a pergunta nova: **quando exatamente o fallback dispara** — sem uma regra clara, "DB vazio" é ambíguo e a mesma tela pode mostrar duas contagens para o mesmo período
- O caminho de leitura do cache precisa nascer com data de saída, senão vira permanente

### Rodada 5 — decidida

| #    | Pergunta            | Resposta                                                                                                      |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------------------- |
| R5.1 | Disparo do fallback | **Só quando `telemetry.db` não existe** → é ponte de migração, com critério objetivo para ser deletado depois |
| R5.2 | Escopo da Onda 2    | **Todas as seis métricas pendentes** (escolha do usuário, além das 4 deriváveis)                              |
| R5.3 | Custo               | **Tabela de preços embutida + override por `.env`**, moeda configurável                                       |
| R5.4 | MCP                 | **Uma tool de leitura** `get_usage_metrics(repo, since, until)`, sem escrita                                  |

**Consequências de R5.2 (as seis) — duas delas não são deriváveis do ledger como ele está:**
- **Dívida técnica por módulo** exige que o evento passe a carregar os caminhos/módulos tocados — o ledger **não guarda arquivos hoje**. Isso muda o schema e todos os call sites
- **Tempo médio commit→PR** exige correlacionar commits com PRs. Nada no ledger liga os dois. Existe infraestrutura reusável: o motor de release já resolve PRs pelo sufixo `(#123)` do squash-merge, e `infrastructure/scm/web_links.py` já monta URLs

### Rodada 6 — decidida

| #    | Pergunta         | Resposta                                                                                                            |
| ---- | ---------------- | ------------------------------------------------------------------------------------------------------------------- |
| R6.1 | Módulo no ledger | **Módulo normalizado — os 2 primeiros segmentos do caminho** (`src/fix`, `src/ui`), nunca o caminho completo        |
| R6.2 | commit→PR        | **Relatório derivado, fora do ledger** — é métrica do repositório, não do uso do GitPR                              |
| R6.3 | Janela do custo  | **Janela de calendário explícita** (`--since`/`--until` + atalhos de 7/30 dias); a doc troca "sprint" por "período" |
| R6.4 | Legado           | **Migrar e mover** os 1749 originais para `~/.gitpr/metrics/_migrated_legacy/` — nunca apagar                       |

**Consequências de R6.1 (módulo normalizado):**
- O evento precisa carregar o **conjunto** de módulos tocados (um diff toca vários) → campo novo no schema, não uma coluna escalar
- Nem todo call site tem diff na mão: linter, blame e hooks gravam sem módulo → o campo é **nullable por construção**
- Fecha a lacuna da métrica 7 (dívida técnica por módulo) sem exportar a árvore de arquivos inteira

**Consequências de R6.2 (relatório derivado):**
- Não entra no ledger, não entra no export do merge, não passa pelo MCP de uso
- **A premissa da minha recomendação caiu.** Eu propus reusar o motor de release, que resolve PR pelo sufixo `(#123)` do squash-merge. Verificado: este repositório **não faz squash** — faz merge commit. Zero sufixos `(#123)` em todas as refs e zero links de PR no CHANGELOG inteiro (ver **G15**). O mecanismo reusável é outro: o **merge commit** `Merge pull request #N from <owner>:<branch>` dá o número do PR, e a diferença entre a data do merge e a do primeiro commit do ramo dá o ciclo — **tudo offline, sem token**. Custo: o formato da mensagem é do GitHub; GitLab/Bitbucket/Azure têm o seu, então o parser precisa ser consciente do provedor (mesma disciplina do `parse_repo_ref()`)
- O que continua reusável sem ressalva: `pull_request_url()` em `infrastructure/scm/web_links.py:96`

**Consequências de R6.3 (janela explícita):**
- `--since`/`--until` valem para **todas** as superfícies de leitura (resumo, export, dashboard, MCP), não só o custo — uma janela, um significado
- Preço muda no tempo: converter tokens antigos pela tabela de hoje é **aproximação**, e a doc deve dizer isso

**Consequências de R6.4 (mover, não apagar):**
- `--purge` continua sendo o único caminho destrutivo, com confirmação
- O fallback de varredura (R5.1: só quando `telemetry.db` não existe) **não** varre `_migrated_legacy/`: se o `.db` sumiu depois da migração, o dado já foi com ele
- **Verificado**: o resumo (`show_metrics_summary()`, `src/metrics.py:452-460`) conta `*.json` **recursivamente** com `os.walk` — se a pasta de legado ficar dentro de `~/.gitpr/metrics/`, os 1749 arquivos continuam contados e o G7 dobra em vez de sumir. O destino `_migrated_legacy/` precisa ficar **fora** de `metrics_dir`, ou o walk precisa pulá-la

### Rodada 7 — decidida

| #    | Pergunta            | Resposta                                                                                                                                                                                                                     |
| ---- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R7.1 | Gatilho da migração | **TUI de criação+importação quando o `gitpr` roda sem banco**; e no `--init`, criação **silenciosa**, com progresso **textual** (sem TUI) se houver arquivos. Resposta própria do usuário, mais elaborada que as três opções |
| R7.2 | Módulos por evento  | **Todos os distintos, sem teto** (escolha do usuário, contra o teto de 20)                                                                                                                                                   |
| R7.3 | Retenção            | **Sem expiração automática**; `--metrics --prune --before <data>` explícito, com `VACUUM`                                                                                                                                    |
| R7.4 | commit→PR           | **Via API da forja** (escolha do usuário, contra a caminhada offline)                                                                                                                                                        |

**Consequências de R7.1 (TUI no startup) — abre a Rodada 8:**
- "Ao executar o gitpr" colide com os modos que **não podem bloquear nem desenhar TUI**: `--quiet`, `--hook-event` (o processo inteiro é "inicia → dispara → sai"), `--mcp` / `gitpr-mcp` (o stdout é o fluxo JSON-RPC) e execução não-interativa em CI. Precisa de matriz explícita
- **Se o TUI for abortado sem importar, o banco nasceu?** Se sim, o fallback cala (R5.1) e os 1749 arquivos ficam órfãos — a mesma perda silenciosa do G1, por outra causa
- Instalação nova não tem nada a importar: um wizard de *migração* não deveria ser o primeiro contato de quem nunca teve dados

**Consequências de R7.2 (sem teto):**
- O tamanho do evento passa a depender do tamanho do diff; uma refatoração ampla carrega dezenas de módulos para dentro do `.db` que viaja no merge
- O teto era a única defesa de tamanho; sem ele, o corte por profundidade (R6.1, 2 segmentos) é a única redução — e já está aplicado
- Mitigação adiável: como o campo é uma **lista**, um teto pode ser acrescentado depois sem migração de schema

**Consequências de R7.3 (sem expiração):**
- `--prune` passa a ser o único caminho destrutivo além do `--purge` — ambos com confirmação
- O sprawl original morre por outro caminho: 1749 arquivos viram 1749 linhas

**Consequências de R7.4 (API da forja) — abre a Rodada 8:**
- Precisa de **token** e de rede: o relatório deixa de funcionar offline e entra em rate limit em repositório grande
- **Fato verificado**: o contrato `ScmProvider` (`src/infrastructure/scm/base.py`) só sabe **listar PRs abertos** — `list_open_pull_requests` (abstrato, linha 165). **Não há como listar PRs merged**, e `get_pull_request(repo, pr_id)` (linha 248) é concreto mas **exige o número**. A API responde bem sobre um PR que você já sabe qual é; ela não sabe dizer quais PRs existiram
- Logo: escolher a API para o **tempo** não resolve de onde vem o **índice** dos PRs a consultar

### Rodada 8 — decidida

| #    | Pergunta       | Resposta                                                                                                                                                                                                            |
| ---- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R8.1 | Gatilho do TUI | **Só em invocação interativa e só quando há arquivos a importar**; nos modos que não podem bloquear (`--quiet`, `--hook-event`, `--mcp`/`gitpr-mcp`, CI) e quando não há nada a importar, o banco nasce em silêncio |
| R8.2 | TUI abortado   | **O banco não nasce até a importação concluir ou ser explicitamente pulada**; pular grava marcador para não reperguntar. Enquanto o banco não existe, o fallback segue lendo os arquivos — R5.1 preservada          |
| R8.3 | Índice de PRs  | **Capacidade nova no `ScmProvider`** — listar PRs por estado e período, com paginação de verdade (escolha do usuário, contra o índice offline)                                                                      |
| R8.4 | G15            | **Dentro deste trabalho** — o motor de release é corrigido junto (escolha do usuário, contra deixar registrado)                                                                                                     |

**Consequências de R8.1 + R8.2 (o TUI de migração):**
- A invariante fica forte: **o banco só existe depois de absorver os arquivos.** Não há estado em que o banco cale o fallback sem ter migrado — o G1 não pode se repetir por essa via
- O TUI é um wizard de **migração**, não de setup: instalação nova nunca o vê
- `--init` continua sendo o caminho silencioso, e é também onde o token SCM já é validado — as duas coisas de que o relatório commit→PR precisa

**Consequências de R8.3 (capacidade nova no contrato) — abre a Rodada 9:**
- **Fato verificado**: `list_open_pull_requests` é abstrato nos 4 provedores (`base.py:165`) e **pagina uma página só**; **não existe nada que liste merged**. A capacidade nova é trabalho original em 4 forges, com 4 vocabulários de estado e 4 formatos de resposta
- A mesma capacidade serve **dois consumidores** — o relatório commit→PR e o conserto do G15. Desenhar uma vez, não duas
- Abre a pergunta de contrato: o método antigo é substituído ou convive?

**Consequências de R8.4 (G15 dentro) — abre a Rodada 9:**
- **Fato verificado**: `release_engine.py:429` roda `git log --no-merges`. Os merge commits **nunca chegam** ao classificador, e `_extract_pr_number()` (`commit_classifier.py:128`) só lê sufixo de squash. Num repositório de merge commit, `pr_number` é `None` **por construção** — o G15 está inteiramente explicado pelo código, não é regressão
- Consertar exige decidir **como atribuir PR a commit** num repo de merge commit — não é trocar uma regex
- O conserto muda a saída de um artefato **já publicado** (o CHANGELOG) — a retroação precisa de regra explícita

### Rodada 9 — decidida

| #    | Pergunta                  | Resposta                                                                                                                                                                |
| ---- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R9.1 | PR↔commit no release      | **Segunda passada** com `git log --merges` monta o mapa `hash → número do PR` via `rev-list <merge>^1..<merge>^2`; os bullets continuam um por commit, agora com o link |
| R9.2 | `list_open_pull_requests` | **A nova substitui, e a antiga vira wrapper fino** (`state=open`); o nome permanece, nenhum call site quebra                                                            |
| R9.3 | Multi-forge               | **Os quatro provedores**, com `ScmNotSupportedError` onde a forja genuinamente não souber filtrar — nunca resultado inventado                                           |
| R9.4 | Superfície do export      | **Flag própria**: `--metrics --export` segue CSV/JSON; `--metrics --bundle` produz o `.db` recortado do merge                                                           |

**Consequências de R9.1 (mapa de ancestralidade):**
- `git log --no-merges` (`release_engine.py:429`) **permanece** — a segunda passada é adicional e limitada ao mesmo range que o release já calcula
- O mapa precisa de regra para **merge que não é PR** (`Merge branch 'main' into develop_natan`, presente no histórico deste repo): commits trazidos por esses não podem ganhar número de PR emprestado
- Um commit alcançável por mais de um merge (PR + sincronização com a main) precisa de desempate — o mais próximo na ancestralidade vence
- **Redundância assumida e explicada**: o release acha PR por ancestralidade local (precisa de atribuição por commit e roda offline); a métrica de ciclo acha PR pela listagem da API (precisa do período inteiro e das datas autoritativas). Trabalhos diferentes, mecanismos diferentes

**Consequências de R9.2 (wrapper):**
- A implementação do wrapper fica na **classe base**, não replicada em 4 provedores: cada provedor implementa só a listagem nova
- O defeito de paginar uma página só deixa de existir de fato, não só de nome

**Consequências de R9.3 (os quatro + exceção honesta):**
- Quatro vocabulários de estado mapeados: GitHub `merged`/`closed`, GitLab `merged`, Bitbucket `MERGED`, Azure `completed`
- A exceção precisa ser **declarável antes da chamada de rede**, no padrão de `supports_reviewable_diff` (Azure), para o relatório poder degradar em vez de estourar

**Consequências de R9.4 (`--bundle`):**
- `--metrics --export` **não muda** → a doc das 5 línguas continua válida para ele (só o G6, que já era falso, é corrigido)
- O G11 fica mais estreito: só o `--bundle` escreve um binário em `./.gitpr/`

### Rodada 10 — decidida

| #     | Pergunta         | Resposta                                                                                                        |
| ----- | ---------------- | --------------------------------------------------------------------------------------------------------------- |
| R10.1 | Backfill no TUI  | **Entra como segunda fonte**, marcado `source: cache_backfill` e **fora dos agregados de execução** por padrão  |
| R10.2 | Onde exibir      | **Seções no dashboard** (visão geral, custo, qualidade, ciclo) **+ resumo textual** no subcomando               |
| R10.3 | CLI              | **Vira subcomando `gitpr metrics`** com sub-ações; as flags antigas **não** sobrevivem como alias               |
| R10.4 | Schema do bundle | **`PRAGMA user_version`**: migra quando o bundle é mais velho, **recusa com mensagem clara** quando é mais novo |

**Consequências de R10.1 (backfill separado):**
- Os agregados da Onda 2 leem **só** linhas de execução; `cache_backfill` aparece em consulta própria
- O TUI de migração passa a ter **duas ofertas** — absorver os arquivos de evento (a verdade) e reconstruir do cache (a aproximação) — e o texto precisa deixar claro qual é qual, porque a segunda conta **prompts distintos**, não execuções
- `--purge` e `--prune` precisam distinguir as duas origens, senão apagam histórico reconstruído sem avisar

**Consequências de R10.2 (seções + texto):**
- O dashboard deixa de ser uma tabela de eventos e vira **quatro seções**; a tabela sobrevive como a seção "visão geral"
- Cada métrica é calculada uma vez e renderizada duas vezes — nenhuma métrica existe só numa das leituras
- Assumido no plano: o resumo textual é o `gitpr metrics` sem sub-ação

**Consequências de R10.3 (subcomando):**
- `--metrics`, `--dashboard` e `--hook-event` (oculto) saem da raiz do CLI; entram `metrics` e `metrics export|bundle|merge|prune|migrate|dashboard`
- `HELP_MAP`/`HELP_PRIORITY` passam a registrar `metrics` **e** as sub-ações — resolve o **G8** pela raiz, em vez de remendar a entrada faltante
- A doc das 5 línguas reescreve todos os exemplos `gitpr --metrics ...` (já ia reescrever pelo G6)
- **Risco assumido**: quebra scripts e aliases existentes. Mitigado por o `enforce_update_required()` já forçar a versão mais nova (sem cauda longa de CLIs antigas) e por a feature ter 2 meses de vida

**Consequências de R10.4 (`user_version`):**
- O `--merge` recusa bundle mais novo **antes** do `ATTACH` — o banco local nunca fica meio-escrito, e a mensagem diz qual versão veio e qual o código entende
- **Colisão detectada com R8.1/R8.2** → ver Rodada 11

### Rodada 11 — decidida (fronteira esgotada)

| #     | Pergunta                              | Resposta                                                                           |
| ----- | ------------------------------------- | ---------------------------------------------------------------------------------- |
| R11.1 | Não-interativo com arquivos presentes | **Importar em silêncio, com progresso textual** (escolha do usuário, contra adiar) |

**Consequências de R11.1 — a invariante da R8.2 sobrevive, reinterpretada:**
- O que a R8.2 proíbe é o banco **vazio** com arquivos no disco, não a criação automática. O banco nasce **junto com a absorção**, seja por decisão do usuário (TUI) ou do programa (silencioso) — nunca antes
- **Refinamento obrigatório**: o progresso textual vai para **stderr**, nunca stdout — o `gitpr-mcp` tem o stdout ocupado pelo fluxo JSON-RPC (o monkey-patch de stdout está documentado no CLAUDE.md)
- Sob `--quiet` (que a R2.3 fixou para os hooks), o progresso é suprimido: a importação acontece em silêncio de fato, e o único vestígio é o banco passar a existir. Custo aceito conscientemente
- Acontece no máximo **uma vez por máquina** — depois disso o banco existe e esse caminho nunca mais é tocado

---

## 5. Plano de execução

### Passo 0 — Artefatos desta sessão (antes de tocar em código)

| Arquivo                                                         | Papel                                                                                                                                                |
| --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docs/survey/20260927_metrics_audit_surveyfacts.md`             | Levantamento completo: defeitos G1–G15 com evidência, conceito × realidade das 8 métricas, as 11 rodadas de decisão                                  |
| `docs/plans/develop_natan/20260927_metrics_audit_plansfacts.md` | Este plano                                                                                                                                           |
| `docs/plans/glossary-metrics-telemetry.md`                      | Glossário das **quatro superfícies** (exigido pela R1.3), no padrão dos 8 `glossary-*.md` existentes                                                 |
| `docs/plans/ADR-008-metrics-ledger.md`                          | ADR do ledger — atende os 3 critérios: difícil reverter, surpreendente sem contexto, trade-off real (JSONL × SQLite, decidido contra a recomendação) |

Observação registrada, **fora do escopo**: o repo já tem **dois** `ADR-002-*.md` (`gitpr-release-subcommand` e `reviewer-suggestion`). Anotar, não consertar aqui.

### Onda 1 — Verdade + migração

Objetivo: o ledger existe, o histórico está dentro dele, e o que a doc promete é o que o código faz.

| #   | Trabalho                                                                                                                                                                                                                                                                                 | Onde                                                                                           |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1   | **Ledger SQLite.** `_save_metric_async()` sai (thread daemon → **escrita síncrona**, com o contexto git resolvido uma vez por processo). Schema com UUID PK, `modules` como lista JSON, `source`, `PRAGMA user_version`, WAL, `ATTACH` + `INSERT OR IGNORE` para o merge                 | `src/metrics.py:30-69`                                                                         |
| 2   | **Identidade.** `parse_repo_ref()` no evento, igual aos hooks; `get_repo_name()` deixa de ser a fonte (mata G5)                                                                                                                                                                          | `src/metrics.py`, `src/infrastructure/scm/`                                                    |
| 3   | **Enriquecer na escrita.** `meta_raw` (tokens, modelo, duração, provedor) copiado para dentro do evento no caminho de sucesso. `enrich_metrics_from_cache()` e o join difuso por minuto são **deletados** — mata o G2 e os 3 mapas divergentes (a R4.3 exige o mapa único compartilhado) | `src/core.py:1165-1186`, `src/metrics.py:168-175`, `:533-540`, `src/ui/metrics_app.py:249-256` |
| 4   | **Migração.** TUI de migração quando interativo e há o que importar; importação silenciosa com progresso em **stderr** nos demais modos; originais movidos para **fora de `metrics_dir`** (verificado: `show_metrics_summary()` conta `*.json` recursivamente, `src/metrics.py:452-460`) | `src/ui/` (novo módulo), `src/metrics.py`                                                      |
| 5   | **Backfill do cache.** Segunda oferta do TUI, `source: cache_backfill`, excluída dos agregados de execução                                                                                                                                                                               | `src/ui/`, `src/metrics.py`                                                                    |
| 6   | **Hooks.** Os 15 arquivos `scripts/*.sh` passam a chamar `gitpr --hook-event`, com guarda `command -v gitpr` + `\|\| true`; saem o heredoc bash e o `grep github\.com` (mata G4 e G5)                                                                                                    | `scripts/*.sh`                                                                                 |
| 7   | **CLI.** Subcomando `gitpr metrics` (+ `export`); `HELP_MAP`/`HELP_PRIORITY` registram `metrics` **e** as sub-ações (mata G8 pela raiz). `--metrics`/`--dashboard`/`--hook-event` saem da raiz                                                                                           | `src/main.py:187-191`, `:420-448`, `:651-711`                                                  |
| 8   | **Baseline de defeitos.** G6 (doc × 5 línguas), G7 (contagem), G9 (função morta removida), G10 (testes da varredura), G11 (`.gitignore`), G12 (`errors='replace'`), G13 (autor), G14 (CHANGELOG)                                                                                         | ver §2                                                                                         |

### Onda 2 — As seis métricas

| #   | Trabalho                                                                                                                                                                                                                                                 |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9   | **Janela** — `--since`/`--until` em **todas** as leituras (resumo, dashboard, bundle, MCP); a doc troca "sprint" por "período"                                                                                                                           |
| 10  | **Custo** — tabela de preços embutida + override por `.env`, moeda configurável (padrão BRL; ollama/local = 0). A doc declara que converter tokens antigos pela tabela de hoje é aproximação                                                             |
| 11  | **Dívida por módulo** — a partir do campo `modules` (2 segmentos, sem teto)                                                                                                                                                                              |
| 12  | **Provedores e modelos** — quebra por provedor e por modelo, que a doc promete desde o início                                                                                                                                                            |
| 13  | **Qualidade** — taxa de aprovação do linter e taxa de map-reduce (ambos os dados já são gravados, nunca foram calculados)                                                                                                                                |
| 14  | **Ciclo commit→PR** — capacidade nova no `ScmProvider` (`list_pull_requests` com estado e período, paginada de verdade) nos **4 provedores**, `ScmNotSupportedError` declarável antes da rede; `list_open_pull_requests` vira **wrapper na classe base** |
| 15  | **G15** — `release_engine.py:429` ganha a segunda passada `--merges` + mapa de ancestralidade, com desempate para merge de branch e para commit alcançável por dois merges                                                                               |
| 16  | **Superfícies** — dashboard com 4 seções (visão geral, custo, qualidade, ciclo) + resumo textual em `gitpr metrics`; tool MCP `get_usage_metrics(repo, since, until)` só de leitura                                                                      |
| 17  | **Transporte** — `gitpr metrics bundle` (`.db` recortado) e `gitpr metrics merge` (`ATTACH` + `INSERT OR IGNORE`, migra para baixo, **recusa para cima** com mensagem clara, antes do `ATTACH`)                                                          |
| 18  | **Retenção** — `gitpr metrics prune --before <data>` + `VACUUM`; sem expiração automática                                                                                                                                                                |

### Verificação

- **Suíte completa**: `python -m pytest tests/ -v` (45 testes de métricas hoje, mais os novos)
- **Testes novos obrigatórios**:
  - migração: absorve os arquivos, move os originais, e **o banco nunca fica vazio com arquivos presentes**
  - bundle/merge: schema mais velho migra; schema mais novo é recusado **sem** deixar o banco local meio-escrito
  - G15: mapa de ancestralidade com merge-de-branch e merge-de-PR no mesmo range, e commit alcançável por dois merges
  - wrapper: `list_open_pull_requests` continua devolvendo o mesmo que antes, agora paginado
  - G12: nenhum `open()`/`subprocess` novo sem `errors='replace'`
- **Manual**: `gitpr metrics`, `gitpr metrics dashboard`, `gitpr metrics bundle` + `merge` com um `.db` vindo de outro repo, e um hook disparando sem banco
- **Regressão obrigatória** (exigida pelo CLAUDE.md): `gitpr -c`, `gitpr -r`, `gitpr release` — o G15 mexe no motor de release

### Notas de execução

- **Nunca commitar** (regra do CLAUDE.md): tudo fica na árvore de trabalho para revisão
- `encoding='utf-8', errors='replace'` em todo `open()`/`subprocess` novo — e nos existentes que violam (G12)
- Relatório de conclusão obrigatório em `docs/claude-code/reports/develop_natan/2026-09-27_metrics_telemetry_v2.md`

---

## 6. Estado

- [x] Levantamento verificado no código
- [x] Entrevista: **11 rodadas, 40 perguntas**, fronteira esgotada
- [x] Plano de execução em duas ondas
- [ ] Passo 0 — salvar survey, plansfacts, glossário e ADR-008
- [ ] Onda 1 — verdade + migração
- [ ] Onda 2 — as seis métricas
- [ ] Relatório de conclusão
