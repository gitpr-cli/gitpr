# Métricas e Telemetria — Analytics Local Offline

O GitPR inclui um **sistema de telemetria local e offline** que recolhe eventos
anónimos de utilização (comandos CLI, chamadas de IA, execuções do linter, git
hooks) para analytics da equipa. Nada sai da sua máquina — todos os dados ficam
em `~/.gitpr/metrics/`.

## ✨ O Que Faz

Cada comando do GitPR gera um pequeno ficheiro JSON de evento que regista:

| Campo | Descrição |
|-------|-----------|
| `timestamp` | Quando o evento ocorreu (ISO 8601) |
| `command` | Qual comando foi executado (`commit`, `review`, `fullreview`, `linter`, `blame`, etc.) |
| `status` | Resultado (`success`, `error`, `triggered`, `no_changes`) |
| `provider` | Provedor de IA utilizado (`gemini`, `deepseek`, `ollama`, `local`) |
| `tokens_estimated` | Contagem de tokens dos metadados de utilização da IA |
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
│   ├── XXXX-XXXXX-XXXX_20260726.json   ← ficheiro de evento
│   └── YYYY-YYYYY-YYYY_20260726.json
├── config.json                          ← estado de exportação
└── export/
    ├── gitpr_metrics_2026-07-26.csv     ← CSV consolidado
    └── gitpr_metrics_2026-07-26.json    ← JSON consolidado
```

Cada ficheiro de evento é nomeado com um UUID único e data para evitar colisões.

## 🚀 Comandos CLI

### Mostrar Resumo

```bash
gitpr --metrics
```

Exibe o total de ficheiros, uso em disco e o caminho do diretório de métricas.

### Exportar Dados

```bash
gitpr --metrics --export
```

Percorre todos os ficheiros de evento não exportados, consolida em relatórios
CSV e JSON em `~/.gitpr/metrics/export/` e regista quais ficheiros já foram
processados.

- **Colunas CSV:** timestamp, command, status, provider, tokens_estimated,
  duration_ms, repo, branch
- **JSON:** array completo dos payloads de eventos
- **Barra de progresso:** feedback visual via `click.progressbar()`

### Limpar Dados

```bash
gitpr --metrics --purge
```

Remove todos os ficheiros de métrica locais após confirmação. Preserva
`config.json` para controlo futuro de exportação.

### Dashboard Interativo

```bash
gitpr --metrics --dashboard
```

Abre um **dashboard TUI** (Textual) mostrando:

- **Barra de resumo:** total de eventos, erros, total de tokens, top comandos, top providers
- **Tabela de eventos:** últimos 100 eventos com timestamp, comando, estado, provider, tokens, duração
- **Atalhos:** `F5` para atualizar, `Esc` para sair

## 🔧 Git Hooks (Recolha Automática)

Quando instalados via `gitpr --installhooks`, três hooks adicionais recolhem
telemetria comportamental:

| Hook | Evento capturado |
|------|-----------------|
| `post-checkout` | Trocas de branch (mudanças de contexto) |
| `pre-push` | Eventos de push (frequência de entrega) |
| `post-merge` | Eventos de pull/merge (frequência de integração) |

Estes hooks usam `gitpr --hook-event <nome> --quiet` — uma flag oculta que
regista o evento silenciosamente sem output.

## 📊 Casos de Uso

- **Tech Lead:** Saber se a equipa está realmente a usar revisões de IA ou a ignorar os hooks
- **Finanças:** Comparar uso de Gemini vs. DeepSeek vs. Ollama para otimizar custos de API
- **Qualidade:** Identificar quais módulos mais acionam o linter ou a análise de blame
- **Processo:** Detetar se o map-reduce está a ser disparado com frequência (PRs grandes — possível problema de processo)

## 🔒 Privacidade

- **100% local** — nenhum dado é enviado para servidores externos
- **Anónimo** — eventos contêm repo/branch mas nenhum conteúdo de ficheiros ou diffs
- **Controlo do utilizador** — exportação e limpeza são manuais; nada é auto-eliminado
- **Hooks opcionais** — git hooks só instalam se executar `gitpr --installhooks`

## 📚 Documentação Relacionada

- [Integração MCP](mcp-integration.md) — Configuração do servidor MCP
- [MCP Prompts](mcp-prompts.md) — Modelos de mensagem pré-definidos
- [MCP Tool Annotations](mcp-annotations.md) — Dicas de integração com IDEs

---
**Dica profissional:** Combine as exportações de métricas com o pipeline de CI
da sua equipa executando `gitpr --metrics --export` de forma agendada e
versionando o CSV no seu repositório.
