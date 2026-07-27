# 📋 Plano de Desenvolvimento: Métricas, Telemetria e Analytics

## Visão Geral

Adicionar ao GitPR uma camada de **telemetria local offline** que coleta
eventos de uso (CLI, AI, linter, blame, git hooks) em arquivos JSON sob
`~/.gitpr/metrics/`, com exportação consolidada via `--metrics --export` e
dashboard TUI opcional. Nada sai da máquina automaticamente — a telemetria
é 100% local e controlada pelo usuário.

**Módulo base já existente:** `src/metrics.py` (57 linhas) com `log_local_metric()`.
**Infraestrutura de metadados:** `call_ai_model()` já injeta `_telemetry_meta`
nas respostas; `save_cached_response()` já grava `meta_raw` no cache.

---

## **Fase 1: Evolução do Sistema de Cache (Telemetria Base)** ✅ CONCLUÍDA

**Objetivo:** Modificar o sistema de cache atual para atuar passivamente como
um banco de dados de telemetria para as requisições de IA, agregando autoria
e metadados.

### 1.1 Injeção de Autoria (`src/cache.py:40`) ✅
- **O que foi feito:** `save_cached_response()` captura `git config user.name`
  e `user.email` via `get_git_user_info()` (linha 17) e os inclui no JSON.
- **Estrutura atual do JSON de cache:**
  ```json
  {
    "md5": "...", "repo": "owner/repo", "branch": "main",
    "author_name": "User", "author_email": "user@example.com",
    "datetime": "2026-07-26 14:30:00", "action_type": "review",
    "prompt": "...", "response": { ... }
  }
  ```

### 1.2 Captura de Metadados Brutos (`src/cache.py:40`) ✅
- **O que foi feito:** Parâmetro `meta_raw` aceito em `save_cached_response()`.
  Se presente, injetado como `response["meta_raw"]` antes da gravação.

### 1.3 Retorno de Metadados da IA (`src/ai_providers.py:137-138`) ✅
- **O que foi feito:** `call_ai_model()` injeta `_telemetry_meta` na resposta:
  ```python
  result_json["_telemetry_meta"] = meta_raw
  ```
- **Estrutura do `meta_raw`:**
  ```json
  { "prompt_tokens": 1500, "completion_tokens": 400, "total_tokens": 1900 }
  ```
- **Fontes:** Gemini → `response.usage_metadata` (`prompt_token_count`,
  `candidates_token_count`, `total_token_count`). DeepSeek → `response.usage`
  (`prompt_tokens`, `completion_tokens`, `total_tokens`).

### 1.4 Repasse de Metadados (`src/core.py:323-374`) ✅
- **O que foi feito:** `generate_pr_content()` faz pop de `_telemetry_meta`,
  agrega com `_aggregate_meta()` (linhas 323-327) e passa `total_meta` para
  `save_cached_response(..., meta_raw=total_meta)` (linha 374).
- **Agregação no Map-Reduce:** tokens de cada chunk são acumulados no
  `total_meta` antes do `save_cached_response()` final.

---

## **Fase 2: Motor de Telemetria Local Offline** 🚧

**Objetivo:** Expandir o uso de `log_local_metric()` para todos os comandos,
não apenas Map-Reduce.

### 2.1 Expansão do Coletor (`src/metrics.py`)
- **Estado atual:** `log_local_metric()` (linha 42) já existe com threading
  fire-and-forget. Salva em `~/.gitpr/metrics/{owner}/{branch}/{uuid}_{date}.json`.
- **O que fazer:**
  1. Adicionar `log_command_metric()` — wrapper de alto nível que recebe o
     nome do comando (`commit`, `review`, `linter`, etc.), status, provider
     e metadados, preenche `tokens_estimated` e `duration_ms`, e chama
     `log_local_metric()`.
  2. Adicionar `get_metrics_dir()` → `~/.gitpr/metrics/` padronizado.
  3. Adicionar `get_metrics_state_file()` → `~/.gitpr/metrics/config.json`
     para controle de arquivos já exportados.
- **Payload do evento:**
  ```json
  {
    "timestamp": "2026-07-26T14:30:00",
    "command": "review", "status": "success", "provider": "gemini",
    "tokens_estimated": 4500, "duration_ms": 3200,
    "repo": "owner/repo", "branch": "feature/xyz",
    "cache_hit": false, "map_reduce_triggered": false,
    "linter_errors": 0, "linter_warnings": 2
  }
  ```

### 2.2 Identificação Única (`src/metrics.py` + `src/chat_memory.py`)
- **Estado atual:** `gerar_uuid_base_15()` já é importado em `src/metrics.py`
  (linha 31) e usado no nome do arquivo.
- **O que fazer:** Nada — já implementado. ✅

### 2.3 Injeção de Rastreadores
- **O que fazer:** Inserir chamadas `log_command_metric()` fire-and-forget em:
  - `src/core.py` → `generate_pr_content()`: ao final de cada ação (commit,
    review, fullreview, pr). Já existe para map_reduce (linha 334). Expandir
    para os fluxos single-chunk.
  - `src/linter_engine.py` → `parse_diff_and_lint()`: registrar erros/warnings
    encontrados.
  - `src/blame_engine.py` → `run_blame_analysis()`: registrar número de commits
    analisados e classificação (ORIGIN/REFACTORING).
  - `src/main.py` → nos handlers de comando (`if commit:`, `if review:`,
    `if linter:`, `if fullreview:`): medir `duration_ms` do início ao fim.

---

## **Fase 3: Git Hooks de Comportamento** 🚧

**Objetivo:** Mapear o fluxo de trabalho do desenvolvedor no Git com scripts
shell mínimos, salvando eventos em `~/.gitpr/metrics/git/`.

### 3.1 Rastreador de Troca de Contexto (`scripts/post-checkout-template.sh`)
- **O que fazer:** Script bash que, ao detectar `git checkout`, grava:
  ```json
  { "timestamp": "...", "hook": "post-checkout", "from_branch": "...",
    "to_branch": "...", "repo": "owner/repo" }
  ```
- **Instalação:** Adicionar `"post-checkout": "post-checkout-template.sh"`
  ao dicionário em `install_git_hooks()` (`src/core.py:494`).

### 3.2 Rastreador de Entregas (`scripts/pre-push-template.sh`)
- **O que fazer:** Script que grava evento de push:
  ```json
  { "timestamp": "...", "hook": "pre-push", "branch": "...", "repo": "owner/repo" }
  ```

### 3.3 Rastreador de Sincronização (`scripts/post-merge-template.sh`)
- **O que fazer:** Script que grava eventos de `git pull` / merge:
  ```json
  { "timestamp": "...", "hook": "post-merge", "branch": "...", "repo": "owner/repo" }
  ```
- **Nota:** O hook `post-merge` dispara tanto em `git pull` quanto em
  `git merge`. Filtrar pelo arquivo `.git/MERGE_MSG` para diferenciar.

### Padrão comum dos hooks:
- Todos usam `gitpr` CLI para gravar a métrica: `gitpr --metrics --hook-event <nome>`
  (flag oculta, sem output visível).
- Ou gravam diretamente via Python: `python -c "from src.metrics import log_local_metric; log_local_metric(...)"`.
  Melhor usar a CLI para não depender do ambiente Python do usuário.

---

## **Fase 4: CLI e Consolidação (Exportação e Limpeza)** 🚧

**Objetivo:** Adicionar flag `--metrics` com sub-opções `--export` e `--purge`.

### 4.1 Algoritmo de Exportação (`src/metrics.py`)
- **Função:** `export_metrics(output_dir=None)`
- **Fluxo:**
  1. Varre `~/.gitpr/metrics/` recursivamente por `*.json`
  2. Checa `config.json` para pular arquivos já exportados (por UUID)
  3. Consolida todos os payloads em uma lista
  4. Gera `gitpr_metrics_YYYY-MM-DD.csv` e `.json` no diretório atual
     (ou em `output_dir` se fornecido)
  5. Atualiza `config.json` com os UUIDs processados
- **CSV colunas:** `timestamp,command,status,provider,tokens_estimated,duration_ms,repo,branch,author`
- **Barra de progresso:** Usar `click.progressbar()` para feedback visual.

### 4.2 Limpeza (`src/metrics.py`)
- **Função:** `purge_metrics()`
- **Fluxo:**
  1. Confirma com o usuário (`click.confirm()`)
  2. Remove todos os `.json` em `~/.gitpr/metrics/` (exceto `config.json`)
  3. Reseta `config.json`
- **Segurança:** Nunca faz purge automático — sempre pede confirmação.

### 4.3 Comandos CLI (`src/main.py`)
- **Flag:** `--metrics` (is_flag=True)
- **Sub-opções:** `--export` (is_flag=True), `--purge` (is_flag=True),
  `--hook-event <name>` (str, hidden=True)
- **HELP_MAP:**
  ```python
  'metrics': {
      'url': get_doc_url('metricas_analytics_dashboard.md'),
      'title': __('Metrics & Analytics (--metrics)'),
      'description': __('Export or purge local telemetry data for team analytics.'),
  }
  ```
- **HELP_PRIORITY:** `'metrics': 15`
- **Handler:**
  ```python
  if metrics and hook_event:
      # Hidden: fire-and-forget hook event logging
      log_local_metric(command=f"hook:{hook_event}", status="fired", provider="git")
      return
  if metrics and export:
      export_metrics()
      return
  if metrics and purge:
      purge_metrics()
      return
  if metrics:
      # Default: show summary
      click.echo(__("Metrics directory: ~/.gitpr/metrics/"))
      click.echo(__("Use --metrics --export to consolidate, --metrics --purge to clean."))
      return
  ```

### 4.4 Chaves i18n (9 novas em cada `langs/*.json`)
```json
{
  "Metrics directory: ~/.gitpr/metrics/": "...",
  "Use --metrics --export to consolidate, --metrics --purge to clean.": "...",
  "Exporting metrics...": "...",
  "✅ Metrics exported to {filename} ({count} events).": "...",
  "No new metrics to export.": "...",
  "⚠ This will permanently delete all local metric files.": "...",
  "✅ Metrics purged ({count} files removed).": "...",
  "Metrics & Analytics (--metrics)": "...",
  "Export or purge local telemetry data for team analytics.": "..."
}
```

---

## **Fase 5: Dashboard TUI** 🚧

**Objetivo:** Exibição interativa via terminal com Textual (mesmo framework
do chat e do issue editor).

### 5.1 TUI Analítica (`src/ui/metrics_app.py`)
- **Classe:** `MetricsApp(App)`
- **Entrada:** Caminho para um arquivo JSON de métricas exportado
- **Widgets:**
  - `Header` com relógio
  - `DataTable` com as últimas N execuções (timestamp, comando, status, provider, tokens, duração)
  - `Static` com resumo: total de execuções, provider mais usado, comandos top-3, tokens totais
  - Gráficos ASCII com `BarChart` ou `RichLog` para tendências diárias
  - `Footer` com bindings: F1=Help, F2=Refresh, Esc=Exit
- **Bindings:** Seguir padrão de `issue_app.py` — `Binding("f1", ...)`, etc.
- **CSS:** Estilo consistente com o tema do GitPR

### 5.2 Dashboard via `--metrics --dashboard`
- Integrar ao handler `--metrics`:
  ```python
  if metrics and dashboard:
      from src.ui.metrics_app import MetricsApp
      app = MetricsApp(metrics_file=latest_export)
      app.run()
      return
  ```

---

## **Resumo de Arquivos**

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `src/metrics.py` | expandir | Adicionar `log_command_metric()`, `export_metrics()`, `purge_metrics()` |
| `src/core.py` | modificar | Injetar `log_command_metric()` nos fluxos single-chunk |
| `src/linter_engine.py` | modificar | Injetar métrica ao final da análise |
| `src/blame_engine.py` | modificar | Injetar métrica ao final da análise |
| `src/main.py` | modificar | Flag `--metrics` + HELP_MAP + HELP_PRIORITY + handler |
| `scripts/post-checkout-template.sh` | novo | Hook de troca de branch |
| `scripts/pre-push-template.sh` | novo | Hook de push |
| `scripts/post-merge-template.sh` | novo | Hook de pull/merge |
| `src/ui/metrics_app.py` | novo | Dashboard TUI com Textual |
| `langs/pt_br.json` | modificar | 9 chaves i18n |
| `langs/pt_pt.json` | modificar | 9 chaves i18n |
| `langs/es_es.json` | modificar | 9 chaves i18n |
| `langs/fr_fr.json` | modificar | 9 chaves i18n |
| `docs/metricas_analytics_dashboard.md` | existente | Documentação de referência |
| `README.md` + 4 variantes | modificar | Link na seção Technical Documentation |

## **Verificação**

1. `python -c "from src.metrics import log_command_metric, export_metrics, purge_metrics"` → importa OK
2. `gitpr --metrics` → mostra diretório e instruções
3. `gitpr --metrics --export` → gera CSV + JSON no diretório atual
4. `gitpr --metrics --purge` → pede confirmação e limpa
5. `gitpr --metrics --dashboard` → abre TUI (se export existir)
6. `pipenv run pytest tests/ -v` → sem regressões
7. Hook scripts instaláveis via `--installhooks` e funcionais
