# Survey Facts — Etapa 4: Documentação de Custo e Latência de Map-Reduce

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `etapa4_mapreduce_metrics_docs`
- **Origem:** `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` (L128–L146)

## 1. Fatos Levantados no Repositório

- **Limiares Map-Reduce (`src/config.py:252-302`):**
  - `DEFAULT_MAP_REDUCE_MAX_TOKENS = 90000` (`GITPR_MAP_REDUCE_MAX_TOKENS`)
  - `DEFAULT_MAP_REDUCE_MAX_PART_TOKENS = 50000` (`GITPR_MAP_REDUCE_MAX_PART_TOKENS`)
  - Overrides por provedor: `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` e `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>` (`_GEMINI`, `_DEEPSEEK`, `_OLLAMA`)
  - Garantia invariante: `max_part_tokens <= max_tokens`
- **Tabela de preços embutida (`src/config.py:342-353`):**
  - `deepseek-v4-flash`: `(0.14, 0.28)` USD por 1M tokens (input / output)
  - `deepseek-v4-pro`: `(0.435, 0.87)` USD por 1M tokens
  - `gemini-2.5-pro`: `(1.25, 10.00)` USD por 1M tokens
  - `gemini-2.5-flash-lite`: `(0.10, 0.40)` USD por 1M tokens
  - `LOCAL_PROVIDERS = ("ollama", "local")`: custo zero por definição
- **Registro no Ledger (`src/core.py:1488-1545`, `1726` e `src/metrics.py:40-62`, `575-600`):**
  - Quando `len(chunks) > 1`, `src/core.py` grava uma linha de gatilho `log_local_metric(command="map_reduce", status="triggered", map_reduce_triggered=True, chunks_count=len(chunks))`.
  - A linha principal do comando também recebe `map_reduce_triggered=(len(chunks) > 1)` e agrega `prompt_tokens`, `completion_tokens`, `total_tokens` e `duration_ms` de todas as chamadas (Map + eventual pré-reduce + Reduce).
  - Na seção `🧪 Quality` (`compute_quality` em `src/metrics.py`), a taxa de disparo do Map-Reduce é `chunked / answered` (linhas com `tokens_actual > 0` e `map_reduce == 1`).
- **Glossário e ADR:**
  - `CONTEXT.md` já define `Map-reduce trigger threshold`, `Map-reduce part size` e `Cascade chunking`.
  - `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` documenta a decisão de fatiamento em cascata e limites por provedor, mas ainda não referencia `docs/metricas-telemetria.md`.
- **Contrato de paridade (`tests/unit/test_docs_translation_parity.py`):**
  - Compara os 5 idiomas (`.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) por contagem exata de `headings`, `table_rows`, `bullets` e `fences` (fora de blocos de código).

## 2. Decisões das Rodadas de Grill

- **Q1 (Posicionamento):** Subseção `### Map-Reduce Cost and Latency` logo após `### Cost and Rates` (antes de `### The Cycle Metric`) em `docs/metricas-telemetria.*`.
- **Q2 (Formato):** Explicação da multiplicação de chamadas/tokens + bullets de leitura das colunas (`map_reduce`, `chunks_count`, `duration_ms`) + tabela comparativa compacta com preços de `DEFAULT_MODEL_PRICES` + bloco `ini` com `GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS` e variantes `<PROVIDER>`.
- **Q3 (ADR-0022 e CONTEXT.md):** Atualizar apenas `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` (`Relacionados` + nota em `## 3. Consequências`), mantendo `CONTEXT.md` intacto.
- **Q4 (Testes):** Manter estritamente o escopo da Etapa 4 e validar com `tests/unit/test_docs_translation_parity.py` e `tests/test_metrics.py`.
