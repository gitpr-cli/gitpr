# Métricas e Telemetria — Analytics Local Offline

O GitPR inclui um **sistema de telemetria local e offline** que coleta eventos
anônimos de uso (comandos CLI, chamadas de IA, execuções do linter, git hooks)
para analytics da equipe. Nada sai da sua máquina — todos os dados ficam em
`~/.gitpr/metrics/`.

## ✨ O Que Faz

Cada comando do GitPR gera um pequeno arquivo JSON de evento registrando:

| Campo | Descrição |
|-------|-----------|
| `timestamp` | Quando o evento ocorreu (ISO 8601) |
| `command` | Qual comando foi executado (`commit`, `review`, `fullreview`, `linter`, `blame`, etc.) |
| `status` | Resultado (`success`, `error`, `triggered`, `no_changes`) |
| `provider` | Provedor de IA usado (`gemini`, `deepseek`, `ollama`, `local`) |
| `tokens_estimated` | Contagem de tokens dos metadados de uso da IA |
| `duration_ms` | Duração do comando em milissegundos |
| `repo` | Nome do repositório (`dono/repo`) |
| `branch` | Nome da branch atual |

Campos adicionais como `linter_errors`, `linter_warnings`, `cache_hit` e
`map_reduce_triggered` fornecem contexto mais profundo para tipos específicos
de comando.

## 📁 Onde os Dados Ficam Armazenados

```
~/.gitpr/metrics/
├── {owner}/{branch}/
│   ├── XXXX-XXXXX-XXXX_20260726.json   ← arquivo de evento
│   └── YYYY-YYYYY-YYYY_20260726.json
├── config.json                          ← estado de exportação
└── export/
    ├── gitpr_metrics_2026-07-26.csv     ← CSV consolidado
    └── gitpr_metrics_2026-07-26.json    ← JSON consolidado
```

Cada arquivo de evento é nomeado com um UUID único e data para evitar colisões.

## 🚀 Comandos CLI

### Mostrar Resumo

```bash
gitpr --metrics
```

Exibe total de arquivos, uso em disco e o caminho do diretório de métricas.

### Exportar Dados

```bash
gitpr --metrics --export
```

Varre todos os arquivos de evento não exportados, consolida em relatórios CSV
e JSON em `~/.gitpr/metrics/export/` e rastreia quais arquivos já foram processados.

- **Colunas CSV:** timestamp, command, status, provider, tokens_estimated,
  duration_ms, repo, branch
- **JSON:** array completo dos payloads de eventos
- **Barra de progresso:** feedback visual via `click.progressbar()`

### Limpar Dados

```bash
gitpr --metrics --purge
```

Remove todos os arquivos de métrica locais após confirmação. Preserva
`config.json` para controle futuro de exportação.

### Dashboard Interativo

```bash
gitpr --metrics --dashboard
```

Abre um **dashboard TUI** (Textual) mostrando:

- **Barra de resumo:** total de eventos, erros, total de tokens, top comandos, top providers
- **Tabela de eventos:** últimos 100 eventos com timestamp, comando, status, provider, tokens, duração
- **Atalhos:** `F5` para atualizar, `Esc` para sair

## 🔧 Git Hooks (Coleta Automática)

Quando instalados via `gitpr --installhooks`, três hooks adicionais coletam
telemetria comportamental:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Trocas de branch (mudanças de contexto) |
| `pre-push` | Eventos de push (frequência de entrega) |
| `post-merge` | Eventos de pull/merge (frequência de integração) |

Esses hooks usam `gitpr --hook-event <nome> --quiet` — uma flag oculta que
registra o evento silenciosamente sem output.

## 📊 Casos de Uso

- **Tech Lead:** Saber se o time está realmente usando revisões de IA ou ignorando os hooks
- **Finanças:** Comparar uso de Gemini vs. DeepSeek vs. Ollama para otimizar custos de API
- **Qualidade:** Identificar quais módulos mais acionam o linter ou a análise de blame
- **Processo:** Detectar se o map-reduce está sendo disparado com frequência (PRs grandes — possível problema de processo)

## 🔒 Privacidade

- **100% local** — nenhum dado é enviado para servidores externos
- **Anônimo** — eventos contêm repo/branch mas nenhum conteúdo de arquivos ou diffs
- **Controle do usuário** — exportação e limpeza são manuais; nada é auto-deletado
- **Hooks opcionais** — git hooks só instalam se você executar `gitpr --installhooks`

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Configuração do servidor MCP
- [MCP Prompts](mcp-prompts.md) — Templates de mensagem pré-definidos
- [MCP Tool Annotations](mcp-annotations.md) — Dicas de integração com IDEs

---
**Dica profissional:** Combine as exportações de métricas com o pipeline de CI
da sua equipe executando `gitpr --metrics --export` agendado e versionando o
CSV no seu repositório.
