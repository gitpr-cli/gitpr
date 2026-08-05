---
name: ai-call-duration-tracking
description: Rastreamento de duração real (wall-clock) das chamadas de IA via perf_counter
metadata:
  type: project
  source: docs/claude-code/reports/develop_natan/2026-08-02_cache_duration_dashboard_progress.md
  date: 2026-08-02
  branch: develop_natan
---

A duração real (wall-clock) das chamadas de IA é capturada e propagada por todo
o pipeline:

1. **Captura**: `time.perf_counter()` em `call_ai_model()` (`src/ai_providers.py`)
   antes do retry loop. `duration_ms` é injetado em `meta_raw` como parte do
   `_telemetry_meta`.

2. **Persistência**: `meta_raw` é salvo no cache JSON via `save_cached_response()`.

3. **Agregação**: `_aggregate_meta()` em `core.py` soma `duration_ms` entre
   chunks do map-reduce (cada chunk tem sua própria duração).

4. **Dashboard**: `scan_cache_files_for_dashboard()` em `metrics.py` escaneia
   TODOS os arquivos de cache (sem filtro de data ou row cap), executado em
   thread separada com `ProgressBar` overlay.

5. **Métricas de comando**: `duration_ms` total é passado para `log_command_metric()`
   (cache hit + success + error paths) em `core.py` e `issue_engine.py`.

**Why:** Antes, o dashboard mostrava `duration_ms = 0` para a maioria dos eventos
porque a duração não era capturada no pipeline da IA. O tracking ponta-a-ponta
permite analisar performance real das chamadas.

**How to apply:**
1. Usar `time.perf_counter()` (não `time.time()`) — é monotônico, imune a ajustes de relógio
2. Capturar ANTES do retry loop (retries reenviam payload idêntico, duração total inclui todos)
3. Injetar `duration_ms` no `meta_raw` antes de `_telemetry_meta` ser extraído
4. `_aggregate_meta` deve somar (`+=`) não sobrescrever
5. Cache antigo sem `duration_ms` mostra 0 (backward-compatible)
