# Métricas e Analytics — Dashboard de Uso para Times

## Visão Geral

Adicionar ao GitPR uma camada de **telemetria e inteligência de uso** voltada
para times e líderes técnicos, sem depender de serviços externos. A coleta é
100% local e anônima, com exportação opcional para consolidação em equipe.

## O que seria medido

Com o GitPR integrado localmente em cada máquina (CLI + MCP + Git Hooks), seria
possível coletar métricas anônimas e agregadas como:

| Métrica | O que revela |
|---------|-------------|
| **Frequência de Code Reviews** | Quantas revisões por dia/semana o time executa |
| **Taxa de aprovação do linter** | % de commits que passam no linter estático direto vs. os que precisam de ajustes |
| **Uso de IA por funcionalidade** | Quais comandos mais usados: `--commit`, `--review`, `--fullreview`, `--issue`, `--blame` |
| **Provedores mais usados** | Gemini vs. DeepSeek vs. Ollama — ajuda a decidir qual provedor contratar |
| **Tempo médio entre commit e PR** | Latência do ciclo de desenvolvimento |
| **Tokens consumidos por sprint** | Estimativa de custo com APIs de IA |
| **Dívida técnica rastreada** | Quantas issues de `--blame` foram abertas por módulo |
| **Map-Reduce ativado** | % de diffs que dispararam o chunking automático — sinaliza PRs muito grandes |

## Como funcionaria

```
Máquina A ──┐
Máquina B ──┤   (dados anônimos, via Git Hooks + CLI)
Máquina C ──┘
              │
              ▼
    ~/.gitpr/metrics/  (arquivos JSON locais)
              │
              ▼
    gitpr --metrics --export  →  relatorio.json / CSV
              │
              ▼
    Dashboard HTML local (Textual TUI ou página estática)
```

1. **Coleta local:** Cada execução do GitPR geraria um evento JSON mínimo em
   `~/.gitpr/metrics/` (timestamp, comando, status, provider, tokens estimados,
   duração). Nada sairia da máquina automaticamente.

2. **Agregação via Git:** Um comando como `gitpr --metrics --export` geraria um
   relatório consolidado a partir dos arquivos de métricas de todo o histórico
   da branch/repositório. Times poderiam versionar esses dados no próprio
   repositório.

3. **Dashboard TUI:** Uma tela no estilo Textual (como o chat e o issue editor
   já fazem) exibiria gráficos ASCII de tendências — uso diário, taxa de erros,
   distribuição por provider, top arquivos mais revisados.

## Estrutura do evento JSON

```json
{
  "timestamp": "2026-07-26T14:30:00",
  "command": "review",
  "status": "success",
  "provider": "gemini",
  "tokens_estimated": 4500,
  "duration_ms": 3200,
  "repo": "owner/repo",
  "branch": "feature/xyz",
  "cache_hit": false,
  "map_reduce_triggered": false,
  "linter_errors": 0,
  "linter_warnings": 2
}
```

## Por que isso seria útil

- **Tech Lead / EM:** Saber se o time está realmente usando as revisões de IA
  ou ignorando os hooks
- **Finanças/Cloud:** Decidir entre manter Gemini (pago) ou migrar para Ollama
  (local) com base no custo real por sprint
- **Qualidade:** Identificar quais módulos do código mais acionam o linter ou
  o blame — focar refactors onde dói mais
- **Produtividade:** Medir se o Map-Reduce está sendo acionado com frequência
  (sinal de PRs muito grandes — problema de processo)

## Escopo sugerido

| Fase | Entregável |
|------|-----------|
| **Fase 1** | `src/metrics.py` — módulo de coleta local (evento JSON por execução) |
| **Fase 2** | Flag `--metrics` com subcomandos: `--export`, `--summary`, `--reset` |
| **Fase 3** | Dashboard TUI (`src/ui/metrics_app.py`) com gráficos ASCII e tabelas |
| **Fase 4** | Integração com Git Hooks para métricas de pre-commit/prepare-commit-msg |
| **Fase 5** | Documentação em 5 idiomas + entrada nos READMEs |

## Dependências

- Nenhuma dependência externa nova prevista
- Reutilizar `src/cache.py` para padrão de arquivos JSON locais
- Reutilizar `src/ui/` (Textual) para o dashboard TUI
- Reutilizar `src/i18n.py` (`__()`) para mensagens multilíngues
