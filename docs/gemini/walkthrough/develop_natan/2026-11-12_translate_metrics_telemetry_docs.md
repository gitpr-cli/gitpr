# Walkthrough — Tradução de `docs/metricas-telemetria.*`

## Mudanças Realizadas

Sincronizamos a documentação de métricas e telemetria em Português do Brasil (`pt_br`), Português de Portugal (`pt_pt`), Espanhol (`es_es`) e Francês (`fr_fr`) para incluir os gráficos de visualização ASCII/Unicode adicionados recentemente à versão em inglês (`docs/metricas-telemetria.md`).

### 1. Português do Brasil (`docs/metricas-telemetria.pt_br.md`)
- **Tabela de Seções:**
  - `📈 Tendência de Tokens`: Consumo diário contínuo de tokens (até 14 dias, preservando dias com zero) com sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, média diária e barras horizontais diárias.
  - `📊 Latência`: Distribuição de execuções cronometradas (`duration_ms > 0`) em 5 faixas de latência (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) com Média, Mediana (P50) e P95.
- **Dashboard TUI:** Inclusão de `tendência de tokens` e `histograma de latência` no resumo das seções exibidas.

### 2. Português de Portugal (`docs/metricas-telemetria.pt_pt.md`)
- **Tabela de Secções:**
  - `📈 Tendência de Tokens`: Consumo diário contínuo de tokens (até 14 dias, preservando dias com zero) com sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, média diária e barras horizontais diárias.
  - `📊 Latência`: Distribuição de execuções cronometradas (`duration_ms > 0`) em 5 intervalos de latência (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) com Média, Mediana (P50) e P95.
- **Dashboard TUI:** Inclusão de `tendência de tokens` e `histograma de latência` na listagem de secções, mantendo "fornecedores" e "secções".

### 3. Espanhol (`docs/metricas-telemetria.es_es.md`)
- **Tabela de Secciones:**
  - `📈 Tendencia de Tokens`: Consumo diario continuo de tokens (hasta 14 días, conservando los días con cero) con sparkline Unicode (`▁▂▃▄▅▆▇█`), pico, promedio diario y barras horizontales diarias.
  - `📊 Latencia`: Distribución de ejecuciones cronometradas (`duration_ms > 0`) a lo largo de 5 rangos de latencia (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) con Media, Mediana (P50) y P95.
- **Dashboard TUI:** Inclusão de `tendencia de tokens` e `histograma de latencia` nas seções renderizadas.

### 4. Francês (`docs/metricas-telemetria.fr_fr.md`)
- **Tabela de Sections:**
  - `📈 Tendance des Tokens`: Consommation quotidienne continue de tokens (jusqu'à 14 jours, en préservant les jours à zéro) avec sparkline Unicode (`▁▂▃▄▅▆▇█`), pic, moyenne quotidienne et barres horizontales quotidiennes.
  - `📊 Latence`: Distribution des exécutions chronométrées (`duration_ms > 0`) sur 5 tranches de latence (`< 1s`, `1–5s`, `5–15s`, `15–30s`, `≥ 30s`) avec Moyenne, Médiane (P50) et P95.
- **Dashboard TUI:** Inclusão de `tendance des tokens` e `histogramme de latence` nas seções renderizadas.

## Validação e Testes
- Testes unitários de cálculo e geração das linhas dos gráficos executados via `pytest tests/test_metrics.py -k "TestTokenTrendReport or TestLatencyReport"` (8/8 passaram).
- Testes de UI Textual executados com sucesso com 4/4 asserções aprovadas.
