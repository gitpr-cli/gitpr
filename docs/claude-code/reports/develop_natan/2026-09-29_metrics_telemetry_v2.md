## Completion Report — Metrics & Telemetry: auditoria e re-escopo (duas ondas)

> Relatório de implementação. O levantamento completo está em
> [docs/survey/20260927_metrics_audit_surveyfacts.md](../../../survey/20260927_metrics_audit_surveyfacts.md);
> o plano aprovado (11 rodadas, 40 perguntas), em
> [docs/plans/develop_natan/20260927_metrics_audit_plansfacts.md](../../../plans/develop_natan/20260927_metrics_audit_plansfacts.md);
> o vocabulário canônico, em
> [docs/plans/glossary-metrics-telemetry.md](../../../plans/glossary-metrics-telemetry.md);
> a decisão de arquitetura do ledger, em
> [docs/plans/ADR-008-metrics-ledger.md](../../../plans/ADR-008-metrics-ledger.md).

### What was done

A feature `metrics` estava declarada concluída desde 2026-07-26. A auditoria encontrou
**15 defeitos** (G1–G15) e **3 das 8 métricas prometidas ausentes**, e a entrevista
decidiu o desenho em 11 rodadas. O trabalho foi feito em duas ondas, como aprovado.

#### Onda 1 — verdade + migração

1. **`src/ledger.py`** (novo, ~1000 linhas) — o ledger SQLite em
   `~/.gitpr/metrics/telemetry.db`: UUID como chave primária, `modules` como lista JSON,
   `source`, `PRAGMA user_version` (`SCHEMA_VERSION = 1`, com `LedgerVersionError`),
   modo WAL e **escrita síncrona**. A thread daemon fire-and-forget saiu (G3) — o teste
   que a travava (`daemon is True`) foi invertido.
2. **`src/infrastructure/git/identity.py`** (novo) — a gramática de remote URL
   (`repo_label`) e a identidade git (`git_identity`) num lugar só. O `src/usage_log.py`
   agora delega para cá em vez de manter a sua própria cópia, e o ledger usa a mesma —
   é o que permite juntar os dois registros (G5, R4.2).
3. **Enriquecer na escrita** — `meta_raw` (tokens reais, modelo, duração, provedor) é
   copiado do cache para dentro da linha **no caminho de sucesso**.
   `enrich_metrics_from_cache()` e o join difuso por minuto foram **deletados**, e com
   eles os três mapas divergentes de pasta de cache (G2) e a função morta
   `load_cache_token_summary()` (G9).
4. **Migração e fallback** — `absorb_legacy_files()` absorve os arquivos de evento
   legados e **move** os originais para `~/.gitpr/metrics_legacy/`, fora de
   `metrics_dir` (dentro, o resumo os contaria recursivamente — G7 dobraria em vez de
   sumir). `pending_legacy_files()` pula `export/` e `config.json`, que são relatório e
   estado, não evento.
5. **`src/ui/metrics_migration_app.py`** (novo) — a TUI que **só abre em invocação
   interativa e só quando há o que importar** (R8.1). Nos modos que não podem bloquear
   (`--quiet`, `--hook-event`, `--mcp`/`gitpr-mcp`, CI) a absorção acontece em silêncio,
   com progresso **em stderr** — nunca stdout, que o `gitpr-mcp` reserva para JSON-RPC
   (R11.1). A invariante que impede o G1 de se repetir: **o banco nasce junto com a
   absorção, nunca antes** (R8.2).
6. **Backfill do cache** — segunda oferta do wizard, marcada `source: cache_backfill` e
   fora dos agregados de execução (R10.1).
7. **Hooks** — os 15 `scripts/*.sh` passam a chamar `gitpr --quiet metrics hook-event`,
   com guarda `command -v gitpr` + `|| true`. Saíram o heredoc bash e o
   `grep github\.com`, que escreviam JSON direto e resolviam o repo como `basename`
   (G4, G5).
8. **CLI** — `gitpr metrics` virou subcomando com `export`, `bundle`, `merge`,
   `migrate`, `prune`, `purge`, `dashboard` e o oculto `hook-event`. `--metrics`,
   `--dashboard` e `--hook-event` **saíram da raiz**, sem alias (R10.3).
9. **Baseline de defeitos** — G6 (docs × 5 línguas reescritas contra o código), G7,
   G9, G10 (testes da varredura do dashboard), G11 (`.gitpr/metrics/` no `.gitignore`,
   sem ignorar `.gitpr/skill/`), G12 (`errors='replace'` no que a mudança tocou),
   G13 (autor na linha), G14 (o CHANGELOG citava três funções que nunca existiram).

#### Onda 2 — as seis métricas

10. **Janela** — `--since`/`--until` + `--days N`, válidos para **todas** as superfícies
    de leitura (resumo, dashboard, export, bundle e tool MCP). Uma janela, um
    significado; inclusiva nas duas pontas (R6.3).
11. **Custo** — tabela de preços embutida (cotada em **USD**) + override por
    `GITPR_METRICS_PRICE_<MODEL>_INPUT`/`_OUTPUT`, com `GITPR_METRICS_CURRENCY`. As duas
    tarifas são obrigatórias; um modelo com só uma é reportado em tokens. Um total que
    deixou modelos sem tarifa sai como `Total (parcial)` (R5.3).
12. **Dívida por módulo** — a partir do campo `modules`, normalizado nos dois primeiros
    segmentos do caminho, sem teto de quantidade, `(root)` para arquivos de raiz e
    `(sem módulo)` para os comandos que nunca tiveram diff em mãos (R6.1, R7.2).
13. **Provedores e modelos** — a quebra por provedor e por modelo que a documentação de
    conceito prometia desde o início e o resumo nunca deu.
14. **Qualidade** — taxa de aprovação do linter e taxa de disparo do map-reduce: os dois
    dados eram gravados e nunca calculados.
15. **Ciclo** — capacidade nova no contrato `ScmProvider`:
    `list_pull_requests(repo, state, since, until)` nos **quatro** provedores,
    `list_open_pull_requests` virou **wrapper fino na classe base**, e
    `supports_merged_dates = False` no Bitbucket declara antes da rede o que a forja não
    sabe datar (R8.3, R9.2, R9.3).
16. **G15** — o motor de release ganhou a **segunda passada** `git log --merges` sobre o
    mesmo range, montando `hash → número do PR` por `rev-list <merge>^1..<merge>^2`. Os
    bullets continuam um por commit, agora com o link (R9.1).
17. **Superfícies** — dashboard com seções (visão geral, custo, qualidade, módulos,
    fornecedores, ciclo) e o mesmo conteúdo em texto em `gitpr metrics`, ambos a partir
    de **um renderizador só**, que devolve pares `(style, text)` — por isso o terminal e
    a TUI não conseguem divergir (R10.2).
18. **Transporte e retenção** — `gitpr metrics bundle` (o `.db` recortado) e
    `gitpr metrics merge` (`ATTACH` + `INSERT OR IGNORE`, dedup pela chave primária;
    migra para cima, **recusa para baixo** com a versão que veio e a que o código entende,
    antes de tocar no banco local) (R4.1, R9.4, R10.4). `gitpr metrics prune --before`
    com `VACUUM`; **sem expiração automática** (R7.3).
19. **MCP** — a tool 15, `get_usage_metrics(repo, since, until)`, só de leitura e sem
    atalho de dia: quem chama nomeia as suas próprias datas (R5.4).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/ledger.py` | feat | **novo** — ledger SQLite, absorção do legado, bundle/merge/prune |
| `src/infrastructure/git/identity.py` | feat | **novo** — `repo_label()` + `git_identity()`, compartilhados |
| `src/ui/metrics_migration_app.py` | feat | **novo** — wizard de migração (TUI, só interativo e só com o que importar) |
| `src/metrics.py` | refactor | −462/+939 — leituras sobre o ledger, seis métricas, escritor único |
| `src/main.py` | feat | −104/+431 — o grupo `metrics` e os seus subcomandos; raiz limpa |
| `src/mcp_server.py` | feat | tool `get_usage_metrics` (read-only) |
| `src/config.py` | feat | tabela de preços, moeda, chaves de override |
| `src/core.py` | refactor | enriquecimento na escrita; o join difuso saiu |
| `src/usage_log.py` | refactor | −61 — delega a identidade compartilhada |
| `src/ui/metrics_app.py` | refactor | seções a partir do renderizador compartilhado |
| `src/release_engine.py` | fix | segunda passada `--merges` (G15) |
| `src/commit_classifier.py` | refactor | mapa de ancestralidade `hash → PR` |
| `src/infrastructure/scm/base.py` | feat | `list_pull_requests` + wrapper + `supports_merged_dates` |
| `src/infrastructure/scm/{github,gitlab,bitbucket,azure_devops}_provider.py` | feat | a listagem por estado e período nos quatro |
| `scripts/*-template*.sh` | fix | 15 arquivos — `gitpr metrics hook-event`, guarda `command -v` |
| `scripts/fix_mangled_i18n_keys.py` | fix | a chave de `purge` acompanhou "records" |
| `langs/*.json` | fix | 6 arquivos — 1258 chaves; as novas e as 2 de `gitpr tests` |
| `docs/metricas-telemetria*.md` | docs | 5 arquivos — reescritos contra o código (G6) |
| `docs/ARCHITECTURE*.md` | docs | 5 arquivos — `gitpr metrics` no fluxo |
| `docs/plans/glossary-metrics-telemetry.md` | docs | **novo** — as quatro superfícies |
| `docs/plans/ADR-008-metrics-ledger.md` | docs | **novo** — JSONL × SQLite |
| `docs/survey/…_surveyfacts.md`, `docs/plans/develop_natan/…_plansfacts.md` | docs | **novos** — levantamento e plano |
| `CLAUDE.md`, `GEMINI.md` | docs | grupo de comandos, Tools 15, seção do ledger, variáveis |
| `CHANGELOG.md` | docs | G14 — as três funções que nunca existiram |
| `.gitignore` | chore | `.gitpr/metrics/` (o `skill/` continua versionado) |
| `tests/test_metrics.py` | test | −651/+2002 |
| `tests/scm/*.py` | test | contrato + os quatro provedores |
| `tests/test_release_engine.py`, `tests/test_commit_classifier.py` | test | o mapa de ancestralidade |
| `tests/test_mcp_server.py`, `tests/test_usage_log.py` | test | a tool nova; a delegação |

### Impact

- **Functionality:** a CLI mudou de forma. `gitpr --metrics`, `gitpr --dashboard` e
  `gitpr --hook-event` **não existem mais** — passam a `gitpr metrics`, `gitpr metrics
  dashboard` e `gitpr metrics hook-event`. Um script antigo quebra; foi risco assumido
  na R10.3 e mitigado pelo `enforce_update_required()`, que não deixa cauda longa de
  CLIs antigas.
- **Migração de dados:** na primeira execução com arquivos legados presentes, o banco
  nasce e os arquivos são **movidos** (nunca apagados) para `~/.gitpr/metrics_legacy/`.
  Nesta máquina: **1764 arquivos absorvidos**, 1806 linhas, 15 repositórios distintos.
- **Custo:** a moeda padrão passou de `BRL` para **USD**, que é a moeda em que a tabela
  embutida é cotada. Quem quiser BRL configura tarifas em BRL **e** aponta
  `GITPR_METRICS_CURRENCY` — a tabela embutida então sai de cena, porque uma tarifa em
  dólares sob rótulo de outra moeda é um número errado, não um número ausente.
- **Performance:** a escrita do ledger é **síncrona** por decisão, e o contexto git é
  resolvido **uma vez por processo** — o custo por comando é uma chamada de git, não
  três. A absorção usa **uma conexão para o lote inteiro**; uma por linha tornaria a
  migração visivelmente lenta. O dashboard deixou de varrer o cache quando o banco
  existe.
- **Compatibilidade:** `list_open_pull_requests` mantém o nome e a resposta, agora
  paginada de verdade — nenhum chamador quebra. O `src/github_api.py` continua sendo o
  shim depreciado. O `.db` é detalhe de implementação; a interface pública segue sendo o
  CSV/JSON do `export` (R3.2).

### O que ficou de fora, e o que ficou registrado como dívida

- **Os hooks instalados nesta máquina são os antigos.** O conserto mudou os **templates**;
  hooks já instalados só mudam com um `gitpr --installhooks` novo. Enquanto isso, eles
  continuam escrevendo JSON no formato legado — e é exatamente isso que explica os 6
  arquivos `{id}_pre-push.json` / `{id}_post-checkout.json` que reapareceram em
  `~/.gitpr/metrics/` **depois** da migração. Não é regressão do ledger: é o hook antigo
  fazendo o que sempre fez. Some com uma reinstalação.
- **35 arquivos `.gitpr/metrics/*` já rastreados pelo git** continuam rastreados — o
  `.gitignore` impede entradas novas, mas não destrackeia o que já está no índice. O
  `git rm --cached` é do usuário, não meu.
- **12 das 46 chamadas `subprocess.run` de `src/` seguem sem `errors='replace'`**
  (`cache.py:23,26`; `core.py:1366,1390,1400,1421,1966,1976`;
  `infrastructure/git/patch_applier.py:87`; `issue_engine.py:22`;
  `main.py:1134,1137`) — G12 foi corrigido só no que esta mudança tocou, por
  "Surgical Changes".
- **Três testes falham, e já falhavam antes deste trabalho**:
  `test_config_schema.py::TestSkillsSection` (×2) e
  `test_mcp_server.py::TestSkillRegistryAgreement` (×1) — os dois registries de skills
  não conhecem os comandos `tests` e `explain` adicionados pelos dois commits anteriores
  a esta sessão. Não os consertei: são de outra feature.
- **`tests/sync_i18n.py` degrada os seis arquivos de idioma** quando rodado por inteiro.
  Eu o rodei, vi o estrago, e reparei conforme
  `.claude/memory/i18n-sync-canonicos-roundtrip.md`. O conserto do `sync_i18n.py` em si
  não estava no escopo.

### Verificação

- **Suíte completa:** `python -m pytest tests/ -q` → **3 failed, 2103 passed, 2 skipped**
  em 316 s. As três falhas são as de skills descritas acima.
- **Manual:** `gitpr metrics`, `gitpr metrics dashboard`, `gitpr metrics bundle` +
  `merge` com um `.db` vindo de outro repo, um hook disparando sem banco, e
  `gitpr metrics -h` (a ajuda contextual do grupo vem do Click e do epílogo do doc, **não**
  do `HELP_MAP` — o plano supunha o contrário e foi corrigido contra o comportamento real).

### Next steps

- Reinstalar os hooks (`gitpr --installhooks`) numa máquina que já os tinha, para parar
  de produzir arquivos no formato legado.
- Re-rodar `gitpr metrics migrate` para absorver os 6 arquivos que o hook antigo escreveu
  depois da primeira migração.
- Consertar os dois registries de skills (`tests`, `explain`) — dívida de outra feature.
- `git rm --cached` dos 35 arquivos `.gitpr/metrics/*` rastreados.
- O `--metrics --serve` do relatório de 2026-07-26 continua sendo um "considerar", nunca
  um requisito — segue não feito, e agora com o MCP no lugar dele.
