# Implementation Plan - Tradução de `docs/metricas-telemetria.*` (Gráficos de Telemetria)

- **Data:** 2026-11-12
- **Branch:** `develop_natan`
- **Tarefa:** `translate_metrics_telemetry_docs`

## Objetivo

Sincronizar os documentos de métricas e telemetria nos 4 idiomas (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) adicionando as descrições dos gráficos `Token Trend` e `Latency Histogram` introduzidos no commit `67a9e77d`.

## Alterações Propostas

### 1. `docs/metricas-telemetria.pt_br.md`
- Inserir na tabela de seções:
  - `| 📈 Tendência de Tokens | Consumo diário contínuo de tokens (até 14 dias, preservando dias com zero) com sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, média diária e barras horizontais diárias |`
  - `| 📊 Latência | Distribuição de execuções cronometradas (`duration_ms > 0`) em 5 faixas de latência (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) com Média, Mediana (P50) e P95 |`
- Atualizar lista de seções do dashboard:
  - `- **Seções:** custo, tendência de tokens, qualidade, histograma de latência, módulos, provedores e o ciclo — as mesmas linhas...`

### 2. `docs/metricas-telemetria.pt_pt.md`
- Inserir na tabela de secções:
  - `| 📈 Tendência de Tokens | Consumo diário contínuo de tokens (até 14 dias, preservando dias com zero) com sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, média diária e barras horizontais diárias |`
  - `| 📊 Latência | Distribuição de execuções cronometradas (`duration_ms > 0`) em 5 intervalos de latência (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) com Média, Mediana (P50) e P95 |`
- Atualizar lista de secções do dashboard:
  - `- **Secções:** custo, tendência de tokens, qualidade, histograma de latência, módulos, fornecedores e o ciclo — as mesmas linhas...`

### 3. `docs/metricas-telemetria.es_es.md`
- Inserir na tabela de secciones:
  - `| 📈 Tendencia de Tokens | Consumo diario continuo de tokens (hasta 14 días, conservando los días con cero) con sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, promedio diario y barras horizontales diarias |`
  - `| 📊 Latencia | Distribución de ejecuciones cronometradas (`duration_ms > 0`) a lo largo de 5 rangos de latencia (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) con Media, Mediana (P50) y P95 |`
- Atualizar lista de secciones do dashboard:
  - `- **Secciones:** coste, tendencia de tokens, calidad, histograma de latencia, módulos, proveedores y el ciclo — las mismas líneas...`

### 4. `docs/metricas-telemetria.fr_fr.md`
- Inserir na tabela de sections:
  - `| 📈 Tendance des Tokens | Consommation quotidienne continue de tokens (jusqu'à 14 jours, en préservant les jours à zéro) avec sparkline Unicode (`▁▂▃▄▅▆▇█`), pic, moyenne quotidienne et barres horizontales quotidiennes |`
  - `| 📊 Latence | Distribution des exécutions chronométrées (`duration_ms > 0`) sur 5 tranches de latence (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) avec Moyenne, Médiane (P50) et P95 |`
- Atualizar lista de sections do dashboard:
  - `- **Sections :** coût, tendance des tokens, qualité, histogramme de latence, modules, fournisseurs et le cycle — les mêmes lignes...`

## Verificação

- `pytest tests/test_metrics.py`
- Comparação lado a lado dos diffs para consistência.
