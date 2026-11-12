# Survey Facts — Tradução de `docs/metricas-telemetria.*` (`translate_metrics_telemetry_docs`)

- **Data:** 2026-11-12
- **Branch:** `develop_natan`
- **Autor:** Antigravity (Google DeepMind)

## 1. Contexto da Tarefa

O usuário solicitou sincronizar a documentação de métricas e telemetria:
`Traduzir docs/metricas-telemetria.*: a janela deu gráficos novos ao tópico, mas só a versão em inglês foi atualizada — PT-BR, PT-PT, ES e FR ficaram para trás.`

## 2. Levantamento de Fatos no Repositório

- **Commit de origem dos gráficos:** `67a9e77d1a388dad9ce297beeb69422382144a98` ("feat: add token trend and latency histogram charts").
- **Alterações feitas na documentação em inglês (`docs/metricas-telemetria.md`):**
  1. Inclusão das linhas de `Token Trend` e `Latency` na tabela de seções do relatório.
  2. Inclusão de `token trend` e `latency histogram` na lista de seções desenhadas pelo dashboard TUI (`gitpr metrics dashboard`).
- **Estado dos arquivos traduzidos:**
  - `docs/metricas-telemetria.pt_br.md`: linhas 81 e 83 ausentes da tabela; linha 255 desatualizada.
  - `docs/metricas-telemetria.pt_pt.md`: linhas 81 e 83 ausentes da tabela; linha 256 desatualizada.
  - `docs/metricas-telemetria.es_es.md`: linhas 81 e 83 ausentes da tabela; linha 261 desatualizada.
  - `docs/metricas-telemetria.fr_fr.md`: linhas 84 e 86 ausentes da tabela; linha 267 desatualizada.
- **Dicionários de i18n (`langs/*.json`):**
  Já continham as chaves correspondentes aos gráficos:
  - `pt_br`: `"Token Trend": "Tendência de Tokens"`, `"Latency": "Latência"`
  - `pt_pt`: `"Token Trend": "Tendência de Tokens"`, `"Latency": "Latência"`
  - `es_es`: `"Token Trend": "Tendencia de Tokens"`, `"Latency": "Latencia"`
  - `fr_fr`: `"Token Trend": "Tendance des Tokens"`, `"Latency": "Latence"`
- **Glossário de Domínio (`CONTEXT.md`):**
  Já definia `Token trend` e `Latency histogram`.

## 3. Decisões do Grill

- Paridade terminológica completa com `langs/*.json` e `CONTEXT.md`.
- Escolha da tradução idiomática para "buckets" (`faixas` em PT-BR, `intervalos` em PT-PT, `rangos` em ES-ES e `tranches` em FR-FR).
- Escopo focado exclusivamente nos 4 arquivos documentais de idiomas estrangeiros.
