---
name: metrics-telemetry-architecture
description: Arquitetura de telemetria offline com fire-and-forget threads e dashboard TUI
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-07-26_metrics_telemetry.md
  date: 2026-07-26
  branch: develop_natan
---

Sistema de telemetria 100% local e offline do GitPR:

```
~/.gitpr/metrics/
├── {owner}/{branch}/{uuid}_{YYYYMMDD}.json   ← eventos fire-and-forget
├── config.json                               ← estado de exportação
└── export/
    ├── gitpr_metrics_YYYY-MM-DD.csv          ← consolidado
    └── gitpr_metrics_YYYY-MM-DD.json         ← consolidado
```

**Métricas capturadas por evento:** timestamp, command, status, provider,
tokens_estimated, duration_ms, repo, branch, cache_hit, map_reduce_triggered.

**Princípios de design:**
- **Fire-and-forget**: todo `log_command_metric()` escreve em thread daemon —
  zero latência para comandos CLI
- **Lazy import**: `log_command_metric()` é importado lazy para evitar
  circular imports (`metrics → core → metrics`)
- **Export**: `click.progressbar()` para diretórios grandes; CSV + JSON
- **Dashboard TUI**: `MetricsApp` (Textual) com DataTable, F5 refresh, summary stats
- **Git hooks**: templates `post-checkout`, `pre-push`, `post-merge` em `scripts/`

**Why:** Fornece visibilidade de uso sem depender de serviços externos.
O design fire-and-forget garante que a telemetria nunca impacta a performance
dos comandos. Tudo fica no filesystem local.

**How to apply:**
1. Novos comandos devem chamar `log_command_metric()` com status, provider, duration
2. Usar lazy import: `from src.metrics import log_command_metric` dentro da função
3. Eventos são agregados por uuid+data; re-execuções no mesmo dia sobrescrevem
4. Dashboard acessível via `gitpr --metrics --dashboard`
5. Export via `gitpr --metrics --export` (salva em `./.gitpr/metrics/export/`)

Relacionado: [[metrics-cache-enrichment]], [[dashboard-repo-scope]]
