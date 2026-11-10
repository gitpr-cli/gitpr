# 0018 — Gráficos 2D em ASCII e Navegação por Abas no Dashboard de Métricas

- **Status:** Aceito
- **Data:** 2026-11-10
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** Evolução da experiência visual de telemetria no comando `gitpr metrics dashboard`, suprindo a limitação de exibição de gráficos estatísticos e séries temporais em terminal sem adicionar dependências pesadas externas e sem quebrar a paridade de dados com a CLI.

## Contexto e Decisão

O GitPR armazena sua telemetria em um ledger SQLite local offline (`~/.gitpr/metrics/telemetry.db`). O CLI padrão (`gitpr metrics`) e a TUI interativa (`gitpr metrics dashboard`) compartilham os mesmos relatórios analíticos (`latency_report()` e `token_trend_report()`).

Anteriormente, os dados de latência e consumo diário de tokens eram exibidos em ambas as superfícies apenas por barras horizontais de texto em uma única linha (`_bar()` usando `█░`) e um sparkline unidimensional (`▁▂▃▄▅▆▇█`). Na TUI, essas seções ficavam espremidas em um container vertical com rolagem acima da tabela de eventos, sem espaço para leitura visual de distribuições de frequência ou curvas temporais.

Decidimos adotar a seguinte arquitetura:

1. **Separação em Módulo Agnóstico Puro (`src/ascii_chart.py`)**:
   - Criação de um motor de renderização de matrizes 2D em caracteres de blocos Unicode/ASCII (`█`, `▄`, `│`, `─`, `┼`).
   - Implementação de funções puras determinísticas (`render_vertical_histogram()` e `render_token_timeseries()`), sem dependência do Textual e sem bibliotecas externas pesadas (como matplotlib ou plotext).
   - Testabilidade unitária síncrona e instantânea.

2. **Paridade de Dados com Especialização de Superfície**:
   - O CLI (`gitpr metrics`) permanece com suas barras horizontais compactas de linha única, ideais para rolagem rápida e saídas de terminal enxutas.
   - O Dashboard TUI (`gitpr metrics dashboard`) utiliza os gráficos 2D com eixos cartesianos X/Y, gridlines e cards integrados de métricas estatísticas (P50, P95, Média, Pico).
   - Ambas as superfícies consomem estritamente as mesmas estruturas de dados de `src/metrics.py`, assegurando que um mesmo ledger nunca conte duas histórias divergentes.

3. **Interface por Abas no Dashboard (`TabbedContent`)**:
   - Reestruturação do `MetricsApp` em duas abas:
     - `[1: 📋 Eventos]`: Resumo superior, seções de texto e tabela detalhada de eventos (`DataTable`).
     - `[2: 📊 Gráficos & Tendências]`: Painéis dedicados e expansivos com rolagem vertical (`VerticalScroll`) para o Histograma Vertical de Latência e a Série Temporal de Tokens.
   - Atalhos de teclado diretos (`1` e `2`) visíveis no `Footer` para alternância imediata, além de suporte a clique com o mouse.

4. **Tratamento Elegante de Janelas Vazias (Empty States)**:
   - Em períodos sem execuções medidas (`duration_ms > 0`) ou sem consumo de tokens, exibe-se um banner informativo explicativo em vez de desenhar eixos vazios ou colunas com zeros.

## Opções Consideradas

- **Adicionar bibliotecas externas de plotagem (Plotext, AsciiChart, Matplotlib):** Rejeitado. GitPR é distribuído exclusivamente via PyPI com instalação leve; dependências gráficas adicionais aumentam o tamanho do pacote, tempo de instalação e risco de quebra de compatibilidade em ambientes restritos de terminal.
- **Inserir os gráficos 2D diretamente no fluxo de scroll vertical existente sem abas:** Rejeitado. Gráficos com eixos verticais de 8 a 12 linhas esgotam o espaço útil de tela e empurram a tabela de eventos para fora do campo visual, prejudicando a usabilidade.
- **Renderizador puro em Python desacoplado em `src/ascii_chart.py` com abas na TUI:** **Adotado.** Mantém zero dependências extras, excelente fidelidade visual, separação de responsabilidades (Clean Architecture) e facilidade de manutenção.

## Consequências

- O Dashboard TUI ganha visual moderno e profissional com gráficos 2D legíveis e cards estatísticos integrados.
- A experiência de navegação por teclado ganha atalhos rápidos `1` e `2` no rodapé.
- Novos conceitos ubíquos (`Dashboard chart pane`, `Vertical latency histogram`, `Token time-series chart`) registrados formalmente no `CONTEXT.md`.
- Cobertura de testes unitários dedicada em `tests/test_ascii_chart.py` garantindo que formatações, cálculos de escala e alinhamento de eixos permaneçam estáveis contra regressões.
