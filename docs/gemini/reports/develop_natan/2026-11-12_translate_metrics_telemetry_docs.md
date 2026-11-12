## Completion Report — Tradução de `docs/metricas-telemetria.*`

### What was done
- Sincronização dos 4 arquivos de documentação localizados (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) de `docs/metricas-telemetria.*` com as novas seções de gráficos adicionadas no commit `67a9e77d`:
  - `📈 Tendência de Tokens` / `Token Trend`
  - `📊 Latência` / `Latency Histogram`
- Atualização da tabela de seções do relatório e da lista de seções desenhadas pelo dashboard TUI (`gitpr metrics dashboard`) em todas as línguas suportadas.
- Alinhamento terminológico com o `CONTEXT.md` e os arquivos de tradução `langs/*.json`.
- Diagnóstico e validação da suíte de testes de métricas e componentes de interface.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/metricas-telemetria.pt_br.md` | docs | Adicionadas seções `Tendência de Tokens` e `Latência` na tabela e na lista do dashboard TUI |
| `docs/metricas-telemetria.pt_pt.md` | docs | Adicionadas secções `Tendência de Tokens` e `Latência` na tabela e na lista do dashboard TUI |
| `docs/metricas-telemetria.es_es.md` | docs | Adicionadas secciones `Tendencia de Tokens` e `Latencia` na tabela e na lista do dashboard TUI |
| `docs/metricas-telemetria.fr_fr.md` | docs | Adicionadas sections `Tendance des Tokens` e `Latence` na tabela e na lista do dashboard TUI |

### Impact
- **Functionality:** Paridade documental total entre a documentação em inglês e as versões traduzidas para os recursos de telemetria visual ASCII/Unicode (`Token Trend` e `Latency Histogram`).
- **Performance:** Nulo.
- **Compatibility:** 100% retrocompatível, sem impacto em código ou quebra de APIs.

### Next steps (if applicable)
- N/A
