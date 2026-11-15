# Plano de Execução — Etapa 4: Custo e Latência de Map-Reduce (`docs/metricas-telemetria.*` e `ADR-0022`)

- **Data:** 2026-11-15
- **Branch:** `develop_natan`
- **Task:** `etapa4_mapreduce_metrics_docs`

## Escopo Acordado

1. **Atualizar `docs/metricas-telemetria.md` (canônico em inglês):**
   - Inserir a subseção `### Map-Reduce Cost and Latency` imediatamente após `### Cost and Rates` (antes de `### The Cycle Metric`).
   - Explicar como diffs acima de `GITPR_MAP_REDUCE_MAX_TOKENS` (padrão `90,000` tokens) disparam `N` chamadas de Map (cada lote limitado por `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, padrão `50,000` tokens) + eventual pré-reduce intermediário + `1` chamada final de Reduce, com pausa de 1s entre chamadas e agregação de `duration_ms`.
   - Documentar a leitura de `map_reduce`, `chunks_count` e `duration_ms` no ledger/CSV/JSON e na seção `🧪 Quality`.
   - Incluir tabela comparativa compacta com os preços reais de `DEFAULT_MODEL_PRICES` em `src/config.py` (`gemini-2.5-flash-lite`, `gemini-2.5-pro`, `deepseek-v4-flash`, `deepseek-v4-pro`, `ollama`/`local`).
   - Incluir bloco `ini` com `GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS` e overrides por provedor `GITPR_MAP_REDUCE_MAX_TOKENS_<PROVIDER>` / `GITPR_MAP_REDUCE_MAX_PART_TOKENS_<PROVIDER>`, além de dicas práticas para equilibrar latência vs. orçamento.
2. **Espelhar nos 4 idiomas (`pt_br`, `pt_pt`, `es_es`, `fr_fr`):**
   - Traduzir a nova subseção em `docs/metricas-telemetria.pt_br.md`, `docs/metricas-telemetria.pt_pt.md`, `docs/metricas-telemetria.es_es.md` e `docs/metricas-telemetria.fr_fr.md` (mantendo pt-BR e pt-PT distintos).
   - Preservar paridade estrutural idêntica (mesma contagem de headings, linhas de tabela `|`, bullets e cercas ` ``` `).
3. **Atualizar `docs/adr/0022-map-reduce-per-provider-token-partitioning.md`:**
   - Adicionar link cruzado em `Relacionados` e nota em `## 3. Consequências` apontando para `docs/metricas-telemetria.md`.
4. **Verificação:**
   - Executar `python -m pytest tests/unit/test_docs_translation_parity.py tests/test_metrics.py -v`.
