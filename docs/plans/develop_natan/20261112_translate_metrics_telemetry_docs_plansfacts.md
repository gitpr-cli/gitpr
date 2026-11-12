# Plan Facts — Tradução de `docs/metricas-telemetria.*` (`translate_metrics_telemetry_docs`)

- **Data:** 2026-11-12
- **Branch:** `develop_natan`
- **Tarefa:** Sincronizar as documentações localizadas (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) de métricas e telemetria com os gráficos de tendência de tokens e histograma de latência introduzidos em `docs/metricas-telemetria.md`.

## 1. Contexto e Objetivo

O commit `67a9e77d` adicionou ao `docs/metricas-telemetria.md` duas seções de gráficos ASCII/Unicode:
- `📈 Token Trend`: série temporal de consumo contínuo de tokens diários (até 14 dias, preservando dias com zero), sparkline Unicode, pico, média diária e gráfico de barras horizontais.
- `📊 Latency`: distribuição das execuções cronometradas (`duration_ms > 0`) em 5 intervalos (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`), com Média, Mediana (P50) e P95.

A versão em inglês foi atualizada na tabela de seções e na descrição do dashboard interativo TUI. As versões nos demais idiomas ficaram defasadas e precisam ser traduzidas mantendo alinhamento terminológico com o `CONTEXT.md` e `langs/*.json`.

## 2. Decisões do Grill

1. **Terminologia Canônica:**
   - **PT-BR:** `📈 Tendência de Tokens` e `📊 Latência` (dashboard: "custo, tendência de tokens, qualidade, histograma de latência, módulos, provedores e o ciclo").
   - **PT-PT:** `📈 Tendência de Tokens` e `📊 Latência` (dashboard: "custo, tendência de tokens, qualidade, histograma de latência, módulos, fornecedores e o ciclo" — respeitando "fornecedores" e "secções").
   - **ES-ES:** `📈 Tendencia de Tokens` e `📊 Latencia` (dashboard: "coste, tendencia de tokens, calidad, histograma de latencia, módulos, proveedores y el ciclo").
   - **FR-FR:** `📈 Tendance des Tokens` e `📊 Latence` (dashboard: "coût, tendance des tokens, qualité, histogramme de latence, modules, fournisseurs et le cycle").
2. **Tradução de "latency buckets":**
   - PT-BR: `5 faixas de latência`
   - PT-PT: `5 intervalos de latência`
   - ES-ES: `5 rangos de latencia`
   - FR-FR: `5 tranches de latence`
3. **Escopo:**
   - Estritamente os 4 arquivos `docs/metricas-telemetria.{pt_br,pt_pt,es_es,fr_fr}.md`.

## 3. Passos de Execução

1. Editar `docs/metricas-telemetria.pt_br.md`:
   - Adicionar as linhas de `Tendência de Tokens` e `Latência` na tabela de seções.
   - Atualizar a lista de seções na descrição do dashboard interativo.
2. Editar `docs/metricas-telemetria.pt_pt.md`:
   - Adicionar as linhas correspondentes na tabela de secções.
   - Atualizar a lista de secções na descrição do dashboard interativo.
3. Editar `docs/metricas-telemetria.es_es.md`:
   - Adicionar as linhas correspondentes na tabela de secciones.
   - Atualizar a lista de secciones na descrição do dashboard interactivo.
4. Editar `docs/metricas-telemetria.fr_fr.md`:
   - Adicionar as linhas correspondentes na tabela de sections.
   - Atualizar a lista de sections na descrição do tableau de bord interactif.
5. Executar suíte de testes (`pytest tests/test_metrics.py`).
6. Gerar relatório de conclusão em `docs/gemini/reports/develop_natan/2026-11-12_translate_metrics_telemetry_docs.md` e walkthrough.
