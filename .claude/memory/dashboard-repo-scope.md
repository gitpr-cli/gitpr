---
name: dashboard-repo-scope
description: Dashboard de métricas com escopo por repositório, merge cache+eventos e export local
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-02_metrics_repo_scope_dashboard_fix.md
  date: 2026-08-02
  branch: develop_natan
---

O dashboard de métricas (`MetricsApp` em `src/ui/metrics_app.py`) foi refinado
com várias melhorias estruturais:

1. **Repo-scope**: dashboard e export filtram por `get_repo_name()` — apenas
   eventos e cache do repositório atual são exibidos. Label `📁 Repository: owner/repo`
   no header.

2. **Merge cache + eventos**: `load_cache_token_summary(repo_name)` escaneia
   `~/.gitpr/cache/prompts/*/` recursivamente e agrega tokens por action type.
   O dashboard funde esses dados com eventos de comando para totais precisos.

3. **F5 fix**: `_setup_columns()` extraído de `_populate_table()` — colunas
   são criadas UMA vez. Antes, cada F5 re-adicionava colunas vazias duplicadas.

4. **Export local**: `export_metrics()` agora salva em `./.gitpr/metrics/export/`
   (projeto-local, não `~/.gitpr/`).versionado por projeto.

5. **Processed cache tracking**: `./.gitpr/metrics/{repo}/processed_cache.json`
   rastreia quais arquivos de cache já foram processados por repositório.

**Why:** O dashboard sem repo-scope misturava dados de todos os projetos.
O F5 quebrava a UI com colunas duplicadas. O export em `~/.gitpr/` não era
portable entre máquinas.

**How to apply:**
1. `MetricsApp` recebe `repo_filter` como parâmetro (de `main.py`)
2. `export_metrics(repo_filter=...)` filtra eventos antes de exportar
3. `_setup_columns()` no `on_mount`; `_populate_table()` só adiciona rows
4. Cache files sem campo `"repo"` são excluídos quando repo filter ativo
5. `processed_cache.json` permite retomar scan incremental no futuro

Relacionado: [[metrics-telemetry-architecture]], [[metrics-cache-enrichment]]
