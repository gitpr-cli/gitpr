---
name: metrics-cache-enrichment
description: Enriquecimento de métricas com tokens reais via scan do cache de prompts
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-02_metrics_system_fix.md
  date: 2026-08-02
  branch: develop_natan
---

O export de métricas é enriquecido com dados reais de tokens extraídos do cache
de prompts da IA:

- `enrich_metrics_from_cache()` em `src/metrics.py` escaneia `~/.gitpr/cache/prompts/`
  e extrai `prompt_tokens`, `completion_tokens`, `tokens_actual` dos arquivos JSON
  de cache que contêm `response.meta_raw` ou `response._telemetry_meta`.

- `generate_issue_content()` em `src/issue_engine.py` extrai `_telemetry_meta`
  da resposta da IA e passa como `meta_raw` para `save_cached_response()`.
  Sem isso, caches de issue ficavam sem dados reais de tokens.

- As colunas `prompt_tokens`, `completion_tokens`, `tokens_actual` são
  adicionadas ao CSV de export.

- Dashboard (`MetricsApp`) pula o subdiretório `export/` ao escanear métricas
  (antes crashava com `AttributeError` porque encontrava JSON de lista).

**Why:** As métricas de evento registram apenas `tokens_estimated` (estimativa
local). Os dados reais (`usage.prompt_tokens`, `usage.completion_tokens`) só
existem na resposta da API, que é cacheada. O enriquecimento casa os dois.

**How to apply:**
1. Todo `call_ai_model()` deve retornar `meta_raw` com `_telemetry_meta`
2. `save_cached_response()` deve receber e persistir `meta_raw`
3. `_telemetry_meta` contém: `prompt_tokens`, `completion_tokens`, `model`, `duration_ms`
4. O matching é por minuto-granularity com token tie-breaker (suficiente para ~99% dos casos)
5. Dashboard deve ter guard contra JSON não-dict (lista, escalar) para evitar crash

Relacionado: [[metrics-telemetry-architecture]], [[ai-call-duration-tracking]]
