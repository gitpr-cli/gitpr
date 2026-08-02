# Metrics Dashboard & Export — Repo-Scoped Fixes

## Context

5 problemas reportados no dashboard e export de métricas:

1. **Totalizador não conta commits** — dashboard só mostra `pr` e `map_reduce`. Precisa escanear `~/.gitpr/cache/prompts/` (todas as subpastas) e extrair `response.meta_raw` para computar tokens reais.
2. **F5 Refresh quebra colunas** — ao pressionar F5, as colunas se repetem (são readicionadas sem `clear()` efetivo) e dados não atualizam.
3. **Dashboard não filtra por repo** — mostra eventos de TODOS os repositórios, deve filtrar pelo `core.get_repo_name()` atual.
4. **Dashboard não exibe nome do repo** — usuário não sabe de qual repo são as estatísticas.
5. **Export não filtra por repo e salva no local errado** — exporta todos os repos e salva em `~/.gitpr/metrics/export/`, mas deve filtrar pelo repo atual e salvar em `./.gitpr/metrics/export/` (diretório do projeto).

## Plano

### 1. `src/metrics.py` — Nova função `load_cache_token_summary(repo_name)`

Varre `~/.gitpr/cache/prompts/*/` recursivamente, abre cada `*.json`, extrai `response.meta_raw` (ou `response._telemetry_meta`), filtra por `data.get("repo") == repo_name` e retorna um dict com:
- `total_prompt_tokens`, `total_completion_tokens`, `total_tokens` (soma de todas as entradas)
- `by_action`: Counter de `action_type` com contagem e tokens

Se `repo_name` for None, agrega todos os repos.

Lógica de fallback: se `meta_raw` não existir, usa `response._telemetry_meta` (padrão do issue_engine antigo).

### 2. `src/ui/metrics_app.py` — Dashboard refactor

**2a. Filtrar por repo atual:**
- `__init__` recebe `repo_filter` (opcional, default = `get_repo_name()`)
- `_load_metrics()`: após carregar eventos, filtra por `e.get("repo") == self.repo_filter`
- `_load_metrics()`: também chama `load_cache_token_summary(self.repo_filter)` para complementar o totalizador com dados do cache

**2b. F5 Refresh (bug raiz):**
- O problema: `_populate_table()` chama `table.clear()` mas depois `table.add_column()` é chamado novamente **dentro do mesmo método**, adicionando colunas duplicadas a cada refresh
- Solução: extrair `_setup_columns()` chamado apenas no `on_mount`, e `_populate_table()` apenas adiciona/limpa linhas
- Ou: verificar `if not table.columns:` antes de adicionar colunas, e apenas limpar as linhas

**2c. Exibir repo no dashboard:**
- Adicionar um `Static` widget `#repo_label` no compose que mostra `f"Repository: {self.repo_filter}"`
- Incluir no summary: `f"📁 Repository: {self.repo_filter}"`

**2d. Totalizador enriquecido:**
- `_update_summary()`: além dos eventos, soma os tokens do cache via `self.cache_summary`
- Mostrar `Total tokens (cache): X,XXX` e `Total tokens (events): X,XXX` ou combinado

### 3. `src/metrics.py` — `export_metrics()` com filtro de repo

**3a. Filtrar eventos por `repo_name`:**
- `export_metrics()` recebe novo parâmetro `repo_filter=None`
- Após coletar eventos (linha ~242), filtra: `[e for e in events if e.get("repo") == repo_filter]`
- Se `repo_filter` é None, comportamento atual (todos os repos)

**3b. Output dir local:**
- Quando `output_dir` é None, usar `os.path.join(os.getcwd(), ".gitpr", "metrics", "export")` em vez de `~/.gitpr/metrics/export/`

### 4. `src/main.py` — Passar repo_filter

- `launch_metrics_dashboard()` recebe `repo_filter=get_repo_name()`
- `export_metrics()` chamado com `repo_filter=get_repo_name()`

### 5. `tests/test_metrics.py` — Atualizar testes

- Testes de export: mockar `os.getcwd()` para tmp_path, verificar output em `.gitpr/metrics/export/`
- Testes de filtro: criar eventos de 2 repos diferentes, verificar que só o repo filtrado aparece
- Testes de `load_cache_token_summary`: criar cache files mockados, verificar soma

## Arquivos modificados

| Arquivo                 | Mudanças                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| `src/metrics.py`        | Nova `load_cache_token_summary(repo_name)`, `export_metrics(repo_filter)`, output dir local |
| `src/ui/metrics_app.py` | `repo_filter`, `_setup_columns()`, repo label, cache summary no totalizador                 |
| `src/main.py`           | Passar `get_repo_name()` para dashboard e export                                            |
| `tests/test_metrics.py` | Atualizar/expandir testes                                                                   |

## Verificação

1. `python -m pytest tests/test_metrics.py -v` — todos passam
2. `python -m pytest tests/ -v` — sem regressões (exceto pre-existing)
3. `python run.py --metrics --dashboard` — abre TUI com repo visível, apenas dados do repo atual
4. Pressionar F5 — colunas não duplicam, dados atualizam
5. `python run.py --metrics --export` — exporta apenas repo atual em `./.gitpr/metrics/export/`
