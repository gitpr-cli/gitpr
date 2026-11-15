## Completion Report — Etapa 4: Map-Reduce Cost and Latency Documentation

### What was done
- Documented Map-Reduce cost multiplication (`N` Map batches + optional intermediate pre-reduce + `1` final Reduce call, 1s pause between calls, and aggregated `duration_ms`), telemetry columns (`map_reduce`, `chunks_count`, `duration_ms`), `DEFAULT_MODEL_PRICES` comparison table, and per-provider threshold tuning (`GITPR_MAP_REDUCE_MAX_TOKENS`, `GITPR_MAP_REDUCE_MAX_PART_TOKENS`, and `<PROVIDER>` overrides) in `docs/metricas-telemetria.md`.
- Mirrored the new `### Map-Reduce Cost and Latency` subsection across all 4 translations (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) with distinct `pt_br` vs. `pt_pt` phrasing and identical structural parity.
- Added cross-references to `docs/metricas-telemetria.md#map-reduce-cost-and-latency` in `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` (`Relacionados` and `## 3. Consequências`).
- Marked **P4 / Etapa 4** as concluded in `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/metricas-telemetria.md` | docs | Added `### Map-Reduce Cost and Latency` subsection |
| `docs/metricas-telemetria.pt_br.md` | docs | Added PT-BR translation of `### Custo e Latência do Map-Reduce` |
| `docs/metricas-telemetria.pt_pt.md` | docs | Added PT-PT translation of `### Custo e Latência do Map-Reduce` |
| `docs/metricas-telemetria.es_es.md` | docs | Added ES-ES translation of `### Coste y Latencia de Map-Reduce` |
| `docs/metricas-telemetria.fr_fr.md` | docs | Added FR-FR translation of `### Coût et Latence du Map-Reduce` |
| `docs/adr/0022-map-reduce-per-provider-token-partitioning.md` | docs | Added cross-reference to `docs/metricas-telemetria.md` |
| `docs/prompts/relatorio_pendencias_proximos_passos_i18n.md` | docs | Marked P4 / Etapa 4 as concluded |

### Impact
- **Functionality:** Documentation-only change; no runtime code modified.
- **Performance:** None.
- **Compatibility:** Preserves 100% structural parity across all 5 language variants of `docs/metricas-telemetria.*`.

### Next steps (if applicable)
- Proceed to Etapa 5 (`docs/scm-multiforge.*` and `ADR-0020` for `persisted=False` in read-only `.env` environments) when ready.
