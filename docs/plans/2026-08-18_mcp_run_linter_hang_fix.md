# Plano: Corrigir travamento das tools MCP do GitPR no Claude Code (run_linter / todas)

## Contexto

- O usuário relata que a tool MCP `run_linter` trava (nunca retorna) quando o Claude Code a executa; provavelmente afeta todas as tools MCP.
- A memória `mcp-run-linter-hangs` (2026-08-18) registrou o sintoma sem a causa raiz. Esta tarefa: diagnosticar (feito) + corrigir + verificar.

## Diagnóstico confirmado (verificado contra o código)

**Causa raiz — handlers sync rodam inline no event loop MCP.** As 12 tools são funções sync registradas via `@mcp.tool()` em `src/mcp_server.py` (~linhas 282-780). O SDK `mcp` 1.28.1 executa handlers sync diretamente no loop asyncio (`mcp/.../func_metadata.py:93-96` — sem off-load para thread, verificado). Qualquer chamada bloqueante dentro de um handler (subprocess git, download OTA, chamada SDK de IA com timeout padrão de ~600s) congela o servidor stdio inteiro: o leitor de stdin e o escritor de stdout param → o Claude Code nunca recebe resposta → "trava". Bate com "ocorre com todas as tools".

**Gatilho concreto do `run_linter`:** o handler faz `from src.core import ...` de forma lazy (`src/mcp_server.py:673`). O primeiro `import src.core` executa `SMART_EXCLUDES = _load_smart_excludes() + _load_docs_smart_excludes()` em nível de módulo (`src/core.py:287`) → dois downloads `urllib.request.urlopen(timeout=3)` (`src/core.py:184`, `:265`) disparam porque `~/.gitpr/.env` tem `SMART_EXCLUDES_VERSION='v0.0.16'` enquanto `src/updater.py` agora declara `__lang_version__="v0.0.17"` (bump de versão não commitado). O timeout do urllib NÃO limita a resolução DNS no Windows → espera efetivamente ilimitada, inline no loop. Em falha, o `.env` continua desatualizado → repete a cada novo processo do servidor.

**Riscos dormentes (mesma classe):** chamadas `subprocess.run` deixam `stdin=None` → filhos herdam o pipe JSON-RPC (nunca EOF) → um filho que lê stdin (prompt de credencial do git, linter externo interativo) bloqueia para sempre. Locais: `src/core.py:446, 474, 525, 504, 550, 565, 762, 1120, 1143` (git fetch — maior risco), `:1168`; `src/metrics.py:18`; `_run_external_linter` (`src/linter_engine.py:72-89`, shell=True, sem timeout — dormente: `.gitpr/skill/.gitpr.linter.yml` tem apenas 2 regras regex).

**Ambiente:** o `.mcp.json` lança `gitpr-mcp.exe` do venv pipenv — install EDITÁVEL, então correções de código valem no reinício do servidor. O modo CLI `--tool` chama as mesmas funções sync via `_TOOL_FUNCS` (`src/mcp_server.py:1635-1648`) — deve permanecer sync. 246 testes coletados atualmente.

## Mudanças

### 1. Decorator `_offload` + aplicação nas 12 tools — `src/mcp_server.py`

- Imports (linhas 33-38): adicionar `threading`, `from functools import wraps`, `import anyio`.
- Novo decorator após `_safe_call` (~linha 243):

```python
def _offload(fn):
    """Wrap a sync MCP tool handler so it runs on an anyio worker thread."""
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))
    return wrapper
```

(anyio 4.x `run_sync` não aceita `**kwargs` — closure faz o marshaling. `@mcp.tool(...)` deve ficar ACIMA de `@_offload`; `wraps` preserva `__name__`/`__wrapped__`, então a introspecção de assinatura do FastMCP e os nomes das tools não mudam.)
- Inserir `@_offload` entre cada bloco `@mcp.tool(...)` e seu `def` (12 locais: get_git_context:282, analyze_diff:308, list_unstaged_files:338, analyze_unstaged_diff:375, get_full_diff:405, generate_commit_message:441, review_code:501, full_review:558, generate_pr_description:608, run_linter:663, analyze_blame:709, generate_issue:770). Corpos intactos.
- `_TOOL_FUNCS`: valores passam a `fn.__wrapped__` (mantém o modo CLI `--tool` síncrono; adicionar comentário explicando).

### 2. Warm imports no startup — `src/mcp_server.py` `_init_config()` (~209-223)

Thread daemon pré-importa `src.core` para o download OTA nunca atrasar a primeira chamada de tool; um import concorrente bloqueia no import lock dentro da thread de trabalho, nunca no loop.

### 3. Endurecimento de subprocessos

- Adicionar `stdin=subprocess.DEVNULL` nos locais de `subprocess.run` listados acima em `src/core.py` e `src/metrics.py:18`. (Prompts de credencial do git abrem o console, não stdin — fluxos CLI não mudam; em MCP/CI um possível hang vira `CalledProcessError` rápido, já tratado.)
- `src/linter_engine.py` `_run_external_linter` (72-89): adicionar `stdin=subprocess.DEVNULL` **e** `timeout=120` (engolido pelo `except Exception: return ""` existente; corrige a classe de hang infinito tanto no CLI quanto no MCP).

### 4. Limitar o download OTA — `src/core.py`

- Adicionar `import threading`; helper `_download_smart_excludes(url, hard_timeout=10.0)`: thread daemon + `join(10)`; retorna None em stall → cadeia de fallback offline existente assume.
- Substituir os três blocos de download `urlopen` crus: `src/core.py:184`, `:265`, `:314`. (Linha 1070 já tem timeout=5 — intocada.)

## Testes

- `tests/test_mcp_server.py`: helper `_call_tool(fn, *a, **kw)` (`asyncio.run(fn(...))`) e conversão dos call sites sync (run_linter em 143/158/168 e os demais 23).
- Nova classe `TestOffloadDecorator` no mesmo arquivo (7 testes determinísticos): roda em thread de trabalho (thread id difere), retorna valor, propaga exceções, preserva nome/assinatura/`__wrapped__`, as 12 tools registradas no FastMCP são async, `_TOOL_FUNCS` permanece sync, chamadas concorrentes lenta+rápida não bloqueiam o loop.
- Novo `tests/test_mcp_server_e2e.py`: (a) sobe o servidor como subprocesso (bootstrap de sys.path + `GITPR_SKIP_SMART_EXCLUDES=1` para independência de rede), envia JSON-RPC `initialize` + `tools/call run_linter` + `tools/call get_git_context` via stdin, afirma que ambas as respostas chegam em ≤60s (padrão reader-thread — sem `select` em pipes no Windows); (b) `--tool run_linter` como subprocesso retorna 0 + JSON válido no stdout.
- Suíte completa: `pipenv run pytest tests/ -v` (246 existentes + novos).

## Rollout / verificação

1. `taskkill /IM gitpr-mcp.exe /F` para matar servidores travados; reinício da sessão do Claude Code relança via `.mcp.json` (install editável — sem reinstalação).
2. A primeira execução se auto-corrige: o download de smart excludes grava `SMART_EXCLUDES_VERSION` v0.0.17 no `~/.gitpr/.env`; se o DNS ainda estiver parado, a mudança 4 limita a ~10s e a cópia offline é usada.
3. Verificações funcionais no Claude Code: `run_linter`, `get_git_context`, `analyze_diff`, uma tool de IA.
4. Verificação CLI: `gitpr-mcp --tool run_linter`.
5. Commit (Conventional Commits atômico + trailer Co-Authored-By, ex.: `fix: offload MCP tool handlers from the event loop to fix server hangs`).
6. Relatório de conclusão → `docs/claude-code/reports/develop_natan/2026-08-18_mcp_run_linter_hang_fix.md`; cópia deste plano → `docs/plans/2026-08-18_mcp_run_linter_hang_fix.md`.
7. Atualizar memória `mcp-run-linter-hangs` com causa raiz + correção.
8. Nota de uma frase no item 13 do ARCHITECTURE.md (offloading de handlers) nas 5 variantes de idioma.

## Follow-ups (fora de escopo, anotados no relatório)

- Limitar timeouts do SDK de IA em `src/ai_providers.py` (timeout http explícito; padrão do SDK ~600s).
- Injeção de shell em `_run_external_linter` (shlex/argv em vez de f-string + shell=True).
- Mesmo padrão de limitação de DNS para os locais urllib de i18n/ai_providers.
