# Survey — Auditoria da feature `metrics` / telemetria

> Levantamento completo da sessão de auditoria da feature `metrics` do GitPR
> (branch `develop_natan`, 2026-09-27). Fatos verificados no código, não em relatórios.
> O plano de execução que saiu daqui vive em
> [20260927_metrics_audit_plansfacts.md](../plans/develop_natan/20260927_metrics_audit_plansfacts.md);
> o vocabulário canônico, no [glossário](../plans/glossary-metrics-telemetry.md);
> a decisão de arquitetura, no [ADR-008](../plans/ADR-008-metrics-ledger.md).

## 1. O pedido

Auditar a feature `metrics`/telemetria contra o que foi pedido, e entrevistar o autor
para verificar se o resultado está em sintonia com a intenção original do produto.
Nenhum código foi alterado durante o levantamento.

### Nota de baseline — o arquivo indicado não é o plano

O usuário indicou `docs/claude-code/reports/develop_natan/2026-07-26_metrics_telemetry.md`
como "o plano inicial". Ele é um **Relatório de Conclusão**, não um plano. Existem três
camadas distintas de "o que foi pedido", e a auditoria usou as três:

| Camada | Arquivo | Papel |
|---|---|---|
| **Conceito** | `docs/plans/metricas_analytics_dashboard.md` | 8 métricas candidatas, 5 fases de escopo, fluxo de dados, enquadramento de privacidade |
| **Plano mestre** | `docs/plans/plano_metricas_telemetria.md` | 5 fases, schema JSON do evento, layout de diretórios, colunas do CSV, 9 chaves i18n, tabela de mudanças por arquivo, checklist de 7 verificações |
| **Relatório** | `2026-07-26_metrics_telemetry.md` | Declara as fases 2–5 concluídas + 4 "next steps" |

## 2. O que foi entregue

**O plano mestre foi integralmente entregue — e ultrapassado.** As 5 fases estão
todas no código, com 5 ciclos de correção posteriores por cima (2026-08-02 ×3,
08-05, 08-15/08-18).

| Camada | Entrega verificada |
|---|---|
| Código | `src/metrics.py` (628 linhas), `src/ui/metrics_app.py` (450), 34 call sites de métrica em 11+ arquivos |
| CLI | `--metrics`, `--metrics --export`, `--metrics --purge`, `--dashboard`, `--hook-event` (oculto) |
| Hooks | 3 templates × 5 idiomas em `scripts/` |
| Testes | 45 testes em 3 arquivos — `test_metrics.py` 34, `test_blame_metrics.py` 7, `test_linter_metrics.py` 4 |
| Docs | `docs/metricas-telemetria.md` + 4 traduções; README ×5; ARCHITECTURE ×5; HELP_MAP |
| i18n | 17 chaves de métricas em cada um dos 6 arquivos de idioma |

### O relatório de 2026-07-26 está desatualizado

Seu "Next steps" pede "adicionar cobertura de testes para `export_metrics()`,
`purge_metrics()` e `MetricsApp` TUI" — **isso foi feito** (34 testes). Dos 4 next
steps, o único que sobra real é o `--metrics --serve`, que no documento original era
um "considerar", não um requisito.

## 3. A arquitetura real — dois armazenamentos, não um

O plano desenhou **um** armazenamento. O código tem **dois**, com papéis diferentes e
sobreposição parcial. O dashboard lê os dois e faz merge; o `--export` lê só um.

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
```

A Fonte B é a **única com tokens reais, `duration_ms`, `model` e autor**. A Fonte A é
a única que vê **comandos sem IA** (linter, blame, hooks), **cache hits** e **erros**.

O dashboard lê as duas e faz merge por `(repo, branch, command, minuto)`. O `--export`
lê só a Fonte A e tenta enriquecer com a B por um join difuso.

### A evidência que decidiu o modelo de dados

`save_cached_response()` grava em `{md5(prompt)}.json`. No cache hit, `core.py` retorna
**antes** de salvar. Logo **execuções idênticas repetidas colapsam em uma única linha**:
o cache conta *prompts distintos*, não *execuções*. Cinco execuções do mesmo review sobre
o mesmo diff produzem **uma** linha no cache.

Só os arquivos de evento são 1-por-execução. Isso tornou o cache inutilizável como ledger
de uso — apesar de ser a única fonte com tokens reais — e é a raiz da decisão do ADR-008.

## 4. Defeitos confirmados (15, todos verificados na fonte)

| # | Severidade | Achado | Evidência |
|---|---|---|---|
| G1 | **Alta — perda de dados** | `export_metrics()` monta `all_files` de **todos os donos**, filtra `events` por repo, mas grava no `config.json` global os UUIDs de **todos** os `all_files`. Como `main.py` sempre passa `repo_filter=get_repo_name()`, exportar no repo A marca os eventos do repo B como exportados — e o export do repo B responde "No new metrics to export." **Perda permanente e silenciosa.** | `src/metrics.py:309-320` vs `:339-342` vs `:381-385` |
| G2 | Média | `enrich_metrics_from_cache()` mapeia `fullreview→fullreview` e `filereview→filereview`, mas a pasta real de cache é `review`. **O join nunca casa para esses dois comandos** → `tokens_actual` sempre 0 no CSV. São **3 cópias divergentes** do mesmo mapa (a terceira, em `metrics_app._merge_rows`, está correta). | `src/metrics.py:168-175`, `:533-540`, `src/ui/metrics_app.py:249-256`; verdade em `src/core.py:864-865` |
| G3 | Média | `log_local_metric()` grava em **thread daemon** — o interpretador pode encerrar antes. O caminho mais exposto é `gitpr --hook-event` (`main.py:651-656`), cujo processo inteiro é "inicia → dispara → sai": exatamente o caso de uso dos hooks. O `src/usage_log.py` documenta esse mesmo risco no próprio docstring e por isso grava de forma síncrona. O comportamento está **travado por teste** (`test_runs_in_background_thread` asserta `daemon is True`). | `src/metrics.py:30-69`, `src/usage_log.py` (docstring), `tests/test_metrics.py` |
| G4 | Média | **Hooks inconsistentes.** `post-merge` (5 idiomas) chama `gitpr --hook-event`; `post-checkout` e `pre-push` (10 arquivos) gravam JSON direto via heredoc bash, sem `gitpr`. A doc afirma que "estes hooks usam `gitpr --hook-event <name> --quiet`" — falso para 2 de 3. | `scripts/*.sh`, `docs/metricas-telemetria.md:96` |
| G5 | Média | **Hooks são invisíveis fora do GitHub.** O bash calcula `REPO` com `grep github\.com`, caindo para `basename` (nome sem owner) em GitLab/Bitbucket/Azure; o filtro do dashboard usa `get_repo_name()`, que também é GitHub-only e devolve `unknown/repo`. Os dois não casam → o evento é descartado. | `scripts/post-checkout-template.sh:12`, `src/core.py:685-705`, `src/ui/metrics_app.py:214-216` |
| G6 | Média | **Docs contradizem o código** (nas 5 línguas): CSV documentado com 8 colunas (o código escreve 11); export documentado em `~/.gitpr/metrics/export/` (o código escreve em `./.gitpr/metrics/export/`); "last 100 events" (não há limite); resumo com "errors" e "top providers" (não existem); nome de arquivo `XXXX-XXXXX-XXXX_20260726.json` (real: `{uuid15}_{YYYYMMDD}.json`). | `docs/metricas-telemetria.md` vs `src/metrics.py`, `src/ui/metrics_app.py` |
| G7 | Baixa | `show_metrics_summary()` conta **todo** `*.json` recursivamente, incluindo o `config.json` → `total_files` superestimado. Medição real nesta máquina: `total_files: 1749`, `total_events: 8`, `488.4 KB` — **1749 eventos acumulados e nenhuma rotação/retenção**. | `src/metrics.py:452-460` |
| G8 | Baixa | `--dashboard` **não tem entrada no HELP_MAP** → `gitpr -h --dashboard` cai no help genérico. `--metrics` tem. | `src/main.py:187-191`, `:267` |
| G9 | Baixa | `load_cache_token_summary()` é **código morto em produção** — definido e testado, mas nenhum arquivo em `src/` o chama. | `src/metrics.py:216`; só `tests/test_metrics.py` o importa |
| G10 | Baixa | **Sem cobertura de teste** para `scan_cache_files_for_dashboard()` e para o rastreio `processed_cache.json` — justamente a superfície mais nova. | `tests/` |
| G11 | Baixa | `./.gitpr/` **não está no `.gitignore`** → o export cria `./.gitpr/metrics/export/*.csv` e `./.gitpr/metrics/{repo}/processed_cache.json` prontos para commit acidental. Obs.: `.gitpr/skill/` é conteúdo intencional, então um ignore cego de `.gitpr/` não serve. | `.gitignore` |
| G12 | Baixa | `_get_owner_name()` chama `subprocess.run(..., text=True)` **sem `encoding='utf-8', errors='replace'`** — viola regra do CLAUDE.md. `get_repo_name()`/`get_current_branch()` também não passam `errors='replace'`. | `src/metrics.py:18-25`, `src/core.py:669-705` |
| G13 | Baixa | Nenhum evento carrega **autor**. O plano pedia coluna `author` no CSV; o dado existe (`author_name`/`author_email` no cache), mas não chega ao evento nem ao CSV. | `src/metrics.py:51-65` vs `src/cache.py:80-93` |
| G14 | Baixa | CHANGELOG v0.0.32 cita `log_hook_event()`, `log_linter_metric()`, `log_blame_metric()` — **funções que não existem**; o código usa `log_local_metric`/`log_command_metric`. | `CHANGELOG.md` |
| G15 | **Média — feature adjacente (release)** | A correlação de PR do motor de release é **só para squash-merge**: `_extract_pr_number()` lê o sufixo `(#123)`, e o `changelog_builder` só renderiza `· [#n](url)` quando ele existe. **Este repositório não faz squash** — faz merge commit (`Merge pull request #193 from gitpr-cli/develop_natan`, 19 ocorrências). Resultado: `pr_number` é sempre `None` e o segmento de PR documentado no CLAUDE.md **nunca apareceu em nenhum CHANGELOG** (`grep -c 'pull/' CHANGELOG.md` = 0). O `release_engine.py:429` roda `git log --no-merges`, então os merge commits nunca chegam ao classificador — o defeito está inteiramente explicado pelo código. | `src/release_engine.py:429`, `src/commit_classifier.py:13,98,128`, `src/changelog_builder.py:150-157`, `CHANGELOG.md` |

## 5. Conceito × realidade — as 8 métricas prometidas

| # | Métrica do doc de conceito | Status |
|---|---|---|
| 1 | Frequência de code reviews (dia/semana) | ✅ Respondível |
| 2 | Taxa de aprovação do linter (%) | ⚠️ Parcial — os dados são gravados, **nenhuma taxa é calculada ou exibida** |
| 3 | Uso de IA por funcionalidade | ✅ "Top commands" |
| 4 | Provedores mais usados | ❌ **Não existe** — a doc promete, o resumo não tem quebra por provedor |
| 5 | Tempo médio entre commit e PR | ❌ Sem dado que ligue commit a PR |
| 6 | Tokens consumidos por sprint (custo) | ⚠️ Total existe; **sem janela e sem conversão para dinheiro** |
| 7 | Dívida técnica rastreada por módulo | ❌ Sem granularidade de módulo |
| 8 | Map-Reduce ativado (%) | ⚠️ Gravado, **nunca computado nem exibido** |

**Resumo: 2 de 8 completas, 3 parciais, 3 ausentes.**

## 6. Fatos verificados durante a entrevista

Fatos que a entrevista exigiu e que mudaram decisões — todos medidos na fonte, não inferidos:

| Fato | Onde | Consequência |
|---|---|---|
| O contrato `ScmProvider` só lista PRs **abertos**; não há como listar merged, e `get_pull_request(repo, pr_id)` exige o número | `src/infrastructure/scm/base.py:165`, `:248` | A API não sabe dizer **quais** PRs existiram — só responde sobre um que você já conhece |
| O repositório **não faz squash-merge**; faz merge commit, e não há um único sufixo `(#123)` em todas as refs | `.git`, `CHANGELOG.md` | Explica o G15 por completo; o padrão correto aqui é `Merge pull request #N from <owner>:<branch>` |
| `show_metrics_summary()` conta `*.json` **recursivamente** | `src/metrics.py:452-460` | A pasta de legado tem de ficar **fora** de `metrics_dir`, senão o G7 dobra em vez de sumir |
| `release_engine.py` roda `git log --no-merges` | `src/release_engine.py:429` | Merge commits nunca chegam ao classificador — consertar o G15 não é trocar uma regex |
| O dashboard **lê as duas fontes** e faz merge | `src/ui/metrics_app.py:172-236` | Uma conclusão inicial de que ele ignorava os eventos estava **errada** e foi corrigida antes de virar achado |
| ADRs no repo vão até **ADR-007**, e há **dois** `ADR-002-*.md` | `docs/plans/` | O novo ADR é o 008; a colisão de numeração fica registrada, fora do escopo |

## 7. As 11 rodadas da entrevista

40 perguntas, fronteira esgotada. O detalhe de cada consequência vive no plano de execução;
aqui fica o registro das decisões.

| Rodada | Tema | Decisões |
|---|---|---|
| 1 | Raiz | Job-to-be-done = **os três, sem hierarquia** (dev, gestão, custo) · direção em **duas ondas** · "métricas" nomeia **quatro superfícies** |
| 2 | Ledger | **Eventos = ledger por execução; cache enriquece na escrita** · autoria = `author_login` + nome, sem e-mail · **unificar os 3 hooks** em `gitpr --hook-event` · comando `--merge` |
| 3 | Forma | **Escrita síncrona** · **SQLite** (`telemetry.db`) · backfill a partir do cache · `usage_log` e ledger **separados** |
| 4 | Transporte | Bundle = **`.db` recortado** · identidade por **`parse_repo_ref()`** · varredura do cache **mantida como fallback** · Onda 1 = verdade + migração juntas |
| 5 | Escopo | Fallback só quando **`telemetry.db` não existe** · **todas as seis** métricas pendentes · tabela de preços embutida + `.env` · uma tool MCP de leitura |
| 6 | Modelo | Módulo **normalizado (2 segmentos)** · commit→PR como **relatório derivado** · **janela de calendário** explícita · legado **movido**, nunca apagado |
| 7 | Gatilho | **TUI** de criação+importação ao rodar sem banco; `--init` **silencioso** com progresso textual · módulos **sem teto** · **sem expiração automática** · tempo via **API da forja** |
| 8 | Fronteira | TUI só **interativo e com o que importar** · banco **não nasce** até decidir · **capacidade nova no `ScmProvider`** · **G15 dentro** do escopo |
| 9 | Contratos | **Segunda passada** de merge commits no release · a listagem nova **substitui** a antiga (wrapper) · **os 4 provedores**, com exceção honesta · **`--bundle`** com flag própria |
| 10 | Superfícies | Backfill **no TUI**, marcado e fora dos agregados · **seções no dashboard + resumo textual** · vira **subcomando `gitpr metrics`** · **`user_version`**: migra para baixo, recusa para cima |
| 11 | Colisão | Não-interativo com arquivos presentes: **importar em silêncio**, com progresso em **stderr** |

### Decisões que contrariaram a recomendação técnica

Registradas explicitamente porque carregam custo aceito:

| Decisão | Recomendação vencida | Custo aceito |
|---|---|---|
| **SQLite** em vez de JSONL (R3.2) | JSONL | Banco binário opaco; exige `user_version`, bundle versionado e o CSV como interface pública |
| **Fallback de varredura mantido** (R4.3) | Removê-lo | Os mapas divergentes de pasta de cache sobrevivem; consolidar vira requisito |
| **Todas as seis métricas** (R5.2) | Só as 4 deriváveis | Duas exigem coleta nova (módulos no schema; ciclo commit→PR) |
| **Módulos sem teto** (R7.2) | Teto de 20 + flag | O tamanho do evento passa a depender do tamanho do diff |
| **Tempo via API da forja** (R7.4) | Caminhada offline nos merge commits | Exige token e rede; entra em rate limit |
| **Índice via capacidade nova no `ScmProvider`** (R8.3) | Índice offline pelos merge commits | Trabalho original em 4 forges |
| **Importar em silêncio** (R11.1) | Não criar e adiar | Sob `--quiet` (o modo dos hooks) a importação é invisível de fato |

### Duas premissas minhas que caíram na verificação

1. **O dashboard ignorava os arquivos de evento.** Falso — ele roda duas fases e faz merge.
   Corrigido antes de virar achado.
2. **O motor de release resolvia PR pelo sufixo `(#123)`.** Falso **neste repositório**, que
   não faz squash. Virou o G15.

## 8. O que a auditoria conclui

**A entrega não é o problema — a sintonia é.** O plano mestre foi cumprido e ultrapassado.
O que a auditoria encontrou foi:

- Uma feature cuja **documentação publicada em 5 línguas descreve um produto que não existe**
  (G6), incluindo métricas que ela promete e o código nunca calculou.
- **Três das oito métricas concebidas nunca existiram**, porque dependiam de dados que o
  ledger não guardava.
- Um **ledger que perde dados em silêncio** (G1) e cuja durabilidade é uma thread daemon
  num processo cujo trabalho é terminar rápido (G3).
- E a causa raiz: **a fonte privilegiada era o cache**, que por construção conta prompts
  distintos e não execuções — e era a única com tokens, modelo e duração.
