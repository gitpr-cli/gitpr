# Plano de execução — Metrics & Telemetry v2 (branch `develop_natan`)

> Execução do re-escopo da feature `metrics`, decidido em entrevista de 11 rodadas
> (2026-09-27). O levantamento que originou este plano vive em
> [20260927_metrics_audit_surveyfacts.md](../../survey/20260927_metrics_audit_surveyfacts.md);
> o vocabulário canônico, no [glossário](../glossary-metrics-telemetry.md);
> a decisão de arquitetura, no [ADR-008](../ADR-008-metrics-ledger.md).

## Contexto

A feature `metrics`/telemetria foi entregue entre 2026-07-26 e 2026-08-18, declarada
concluída e encerrada. O plano mestre (`docs/plans/plano_metricas_telemetria.md`) foi
**integralmente cumprido e ultrapassado** por 5 ciclos de correção posteriores.

A auditoria de 2026-09-27 encontrou 15 defeitos verificados no código, três das oito
métricas concebidas que nunca existiram, e documentação publicada em 5 línguas
descrevendo um produto que o código não entrega. A causa raiz é arquitetural: **a fonte
privilegiada era o cache de IA**, que é chaveado por MD5 do prompt e portanto conta
*prompts distintos*, não *execuções* — apesar de ser a única fonte com tokens reais,
modelo, duração e autor.

Este plano substitui os arquivos de evento JSON por um **ledger SQLite**, corrige os
defeitos, e constrói as seis métricas que faltam.

## Passo 0 — Artefatos da sessão

| Arquivo | Papel |
|---|---|
| `docs/survey/20260927_metrics_audit_surveyfacts.md` | Levantamento completo: G1–G15 com evidência, conceito × realidade, 11 rodadas |
| `docs/plans/develop_natan/20260927_metrics_audit_plansfacts.md` | Este plano |
| `docs/plans/glossary-metrics-telemetry.md` | Glossário das **quatro superfícies** (exigido pela R1.3) |
| `docs/plans/ADR-008-metrics-ledger.md` | ADR do ledger |

Observação registrada, **fora do escopo**: o repo já tem **dois** `ADR-002-*.md`
(`gitpr-release-subcommand` e `reviewer-suggestion`). Anotar, não consertar aqui.

## Onda 1 — Verdade + migração

Objetivo: o ledger existe, o histórico está dentro dele, e o que a doc promete é o que o
código faz.

| # | Trabalho | Onde |
|---|---|---|
| 1 | **Ledger SQLite.** `_save_metric_async()` sai (thread daemon → **escrita síncrona**, com o contexto git resolvido uma vez por processo). Schema com UUID PK, `modules` como lista JSON, `source`, `PRAGMA user_version`, WAL, `ATTACH` + `INSERT OR IGNORE` para o merge | `src/metrics.py:30-69` |
| 2 | **Identidade.** `parse_repo_ref()` no evento, igual aos hooks; `get_repo_name()` deixa de ser a fonte (mata G5) | `src/metrics.py`, `src/infrastructure/scm/` |
| 3 | **Enriquecer na escrita.** `meta_raw` (tokens, modelo, duração, provedor) copiado para dentro do evento no caminho de sucesso. `enrich_metrics_from_cache()` e o join difuso por minuto são **deletados** — mata o G2 e os 3 mapas divergentes; a R4.3 exige o mapa único compartilhado | `src/core.py:1165-1186`, `src/metrics.py:168-175`, `:533-540`, `src/ui/metrics_app.py:249-256` |
| 4 | **Migração.** TUI quando interativo e há o que importar; importação silenciosa com progresso em **stderr** nos demais modos; originais movidos para **fora de `metrics_dir`** | `src/ui/` (módulo novo), `src/metrics.py` |
| 5 | **Backfill do cache.** Segunda oferta do TUI, `source: cache_backfill`, excluída dos agregados de execução | `src/ui/`, `src/metrics.py` |
| 6 | **Hooks.** Os 15 arquivos `scripts/*.sh` passam a chamar `gitpr --hook-event`, com guarda `command -v gitpr` + `\|\| true`; saem o heredoc bash e o `grep github\.com` (mata G4 e G5) | `scripts/*.sh` |
| 7 | **CLI.** Subcomando `gitpr metrics` (+ `export`); `HELP_MAP`/`HELP_PRIORITY` registram `metrics` **e** as sub-ações (mata G8 pela raiz). `--metrics`/`--dashboard`/`--hook-event` saem da raiz | `src/main.py:187-191`, `:420-448`, `:651-711` |
| 8 | **Baseline de defeitos.** G6 (doc × 5 línguas), G7 (contagem), G9 (função morta removida), G10 (testes da varredura), G11 (`.gitignore`), G12 (`errors='replace'`), G13 (autor), G14 (CHANGELOG) | ver §2 do survey |

## Onda 2 — As seis métricas

| # | Trabalho |
|---|---|
| 9 | **Janela** — `--since`/`--until` em **todas** as leituras (resumo, dashboard, bundle, MCP); a doc troca "sprint" por "período" |
| 10 | **Custo** — tabela de preços embutida + override por `.env`, moeda configurável (padrão BRL; ollama/local = 0). A doc declara que converter tokens antigos pela tabela de hoje é aproximação |
| 11 | **Dívida por módulo** — a partir do campo `modules` (2 segmentos, sem teto) |
| 12 | **Provedores e modelos** — quebra por provedor e por modelo, que a doc promete desde o início |
| 13 | **Qualidade** — taxa de aprovação do linter e taxa de map-reduce (dados já gravados, nunca calculados) |
| 14 | **Ciclo commit→PR** — capacidade nova no `ScmProvider` (`list_pull_requests` com estado e período, paginada de verdade) nos **4 provedores**, `ScmNotSupportedError` declarável antes da rede; `list_open_pull_requests` vira **wrapper na classe base** |
| 15 | **G15** — `release_engine.py:429` ganha a segunda passada `--merges` + mapa de ancestralidade, com desempate para merge de branch e para commit alcançável por dois merges |
| 16 | **Superfícies** — dashboard com 4 seções (visão geral, custo, qualidade, ciclo) + resumo textual em `gitpr metrics`; tool MCP `get_usage_metrics(repo, since, until)` só de leitura |
| 17 | **Transporte** — `gitpr metrics bundle` (`.db` recortado) e `gitpr metrics merge` (`ATTACH` + `INSERT OR IGNORE`, migra para baixo, **recusa para cima** com mensagem clara, antes do `ATTACH`) |
| 18 | **Retenção** — `gitpr metrics prune --before <data>` + `VACUUM`; sem expiração automática |

## Regras que valem para as duas ondas

- **O banco nunca fica vazio com arquivos no disco.** Ele nasce **junto com a absorção**,
  por decisão do usuário (TUI) ou do programa (silencioso) — nunca antes. É o que impede
  o G1 de se repetir por outra via (R8.2 + R11.1).
- **`git log --no-merges` permanece** no release engine; a segunda passada do G15 é
  adicional e limitada ao mesmo range que o release já calcula (R9.1).
- **`--metrics --export` não muda de significado** — CSV e JSON continuam sendo a visão
  humana; o `.db` recortado do merge sai por `gitpr metrics bundle` (R9.4).
- **Progresso textual vai para stderr**, nunca stdout — o `gitpr-mcp` tem o stdout
  ocupado pelo fluxo JSON-RPC (R11.1).
- **Nunca commitar** (regra do CLAUDE.md): tudo fica na árvore de trabalho.
- `encoding='utf-8', errors='replace'` em todo `open()`/`subprocess` novo — e nos
  existentes que violam (G12).

## Verificação

- **Suíte completa**: `python -m pytest tests/ -v` (45 testes de métricas hoje, mais os novos)
- **Testes novos obrigatórios**:
  - migração: absorve os arquivos, move os originais, e **o banco nunca fica vazio com arquivos presentes**
  - bundle/merge: schema mais velho migra; schema mais novo é recusado **sem** deixar o banco local meio-escrito
  - G15: mapa de ancestralidade com merge-de-branch e merge-de-PR no mesmo range, e commit alcançável por dois merges
  - wrapper: `list_open_pull_requests` continua devolvendo o mesmo que antes, agora paginado
  - G12: nenhum `open()`/`subprocess` novo sem `errors='replace'`
- **Manual**: `gitpr metrics`, `gitpr metrics dashboard`, `gitpr metrics bundle` + `merge`
  com um `.db` vindo de outro repo, e um hook disparando sem banco
- **Regressão obrigatória** (exigida pelo CLAUDE.md): `gitpr -c`, `gitpr -r`, `gitpr release`
  — o G15 mexe no motor de release

## Risco assumido

A R10.3 aposenta as flags `--metrics`/`--dashboard` da raiz **sem alias de compatibilidade**.
Quebra scripts e aliases existentes. Mitigado por o `enforce_update_required()` já forçar
todo mundo para a versão mais nova — não há cauda longa de CLIs antigas — e por a feature
ter dois meses de vida.
