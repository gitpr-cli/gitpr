You are designing an implementation plan for the gitpr CLI repo at c:\Users\nataniel\projetos\python\gitpr. Do NOT write any files — return the plan as your final report.

## Feature
Hidden Click flag `--pre-save` on the main `cli` command. When enabled, every AI call must FIRST dump the full payload (system instruction + user prompt + provider/model info) to a JSON file in the current working directory, then proceed with the call normally (save-and-continue, NOT dry-run). Purpose: the user needs to inspect prompts before they hit the model because very large prompts cause problems.

## Decisions already made with the user (fixed requirements)
- Filename: `_{action}-{datetime}.json` where action ∈ {pr_desc, commit, review, issue, blame, blame_summary, chat, ...} and datetime uses format `%Y%m%d%H%M%S` (same as other gitpr output files). Written to CWD, `encoding='utf-8'`.
- Behavior: save then continue (the AI call proceeds).
- Scope: BOTH `call_ai_model()` (src/ai_providers.py:13) and `call_ai_chat()` (src/ai_providers.py:139).

## Known facts from exploration (verify exact line numbers yourself by reading the files)
- src/main.py: options stacked as decorators on `cli()` (lines ~136-153); `--hook` (line 144) and `--quiet` (line 145) already use `hidden=True`. `cli()` signature at line 154 takes plain args; no Click context/config object. Provider string threads to `generate_pr_content(action_type, action_type, diff_text, active_provider)` at line ~559. Issue/blame/chat resolve provider internally via `get_ai_provider()`.
- src/ai_providers.py: `call_ai_model(provider, api_key, api_model, prompt, system_instruction, quiet=False)` is the single choke point for PR/commit/review/issue/blame. Gemini: prompt→`contents`, system→`config["system_instruction"]`. DeepSeek/Ollama: `messages=[{role:system},{role:user}]`. Retry loop with Spinner started at ~line 20-21. `call_ai_chat(provider, api_key, api_model, system_instruction, chat_history, new_message, quiet=False)` at line 139 is the chat path (Textual TUI, quiet=True).
- call_ai_model call sites: src/core.py:218 (action_folder already computed in core.py:165-170 as "pr_desc"/"commit"/"review"/"issue"), src/blame_engine.py:86 (commit classification), src/blame_engine.py:213 (final summary), src/issue_engine.py:81.
- i18n: `__()` from src/i18n.py; translation keys are the full English sentence; pt-BR values in langs/pt_br.json.
- Spinner writes \r to stdout continuously; any console message must be printed BEFORE spinner.start() or after stop. In quiet mode spinner is a no-op.
- CLAUDE.md rules: all code/comments in English; `open()` with encoding='utf-8'; surgical changes; user-facing text through `__()`; conventional commits.

## Design constraints to respect
1. Minimal diff. Preferred mechanism: a module-level flag in src/ai_providers.py (e.g. `PRE_SAVE_ENABLED` + `set_pre_save(enabled)` setter) toggled once from main.py — this avoids threading a new parameter through generate_pr_content/run_blame_analysis/generate_issue_content/ChatApp signatures. Validate this is sound (single-process CLI, no concurrency concerns except the chat TUI worker thread — check how ChatApp calls call_ai_chat, src/ui/chat_app.py:483-520).
2. The filename needs an `action` label at the choke point. call_ai_model currently doesn't receive one. Evaluate: add optional kwarg `action=None` (default e.g. "ai_call") to call_ai_model and pass it from the 4 call sites (core.py has action_folder; blame_engine → "blame" / "blame_summary"; issue_engine → "issue"). For call_ai_chat, hardcode "chat". Confirm each call site's surrounding code and what minimal edit is needed.
3. JSON dump content: propose exact schema. Should include datetime, provider, model, action, system_instruction, prompt (or chat_history + new_message for chat), and character counts (system_instruction_chars, prompt_chars, total_chars) since the user is debugging prompt-size problems. `ensure_ascii=False, indent=2`.
4. Save must happen ONCE before the retry loop, before spinner starts. A short confirmation message via `__()` + click.secho, suppressed when quiet=True (chat TUI passes quiet=True so it won't corrupt the TUI).
5. Cache caveat: core.py checks MD5 cache BEFORE calling call_ai_model — on cache hit no AI call happens, so no file is written. Confirm where the cache check happens in core.py and state this caveat in the plan (correct behavior: nothing is sent). 
6. Where exactly in main.py to declare the option (which decorator position / after which existing option), the exact new parameter in the `cli()` signature (note: main.py line ~169 uses `locals().get(param_name)` for contextual help — check whether adding a param breaks anything there), and where to call `set_pre_save()` (early, before any engine dispatch — find the right spot, e.g., near where quiet/provider are handled after setup_environment()).
7. i18n: exact English message string to use as key + suggested pt_br.json addition.
8. Tests: look at tests/test_core.py patterns (unittest + mock) and propose 1-2 minimal unit tests for the save helper (e.g., tmp dir, assert file created with expected keys, assert not created when disabled).

## Deliverable
A step-by-step implementation plan: ordered list of edits per file with exact anchor points (function names + line numbers you verified), the new helper function code shape (signature + behavior description, not necessarily full code), test plan, and a short verification checklist (commands to run: e.g. `pipenv run python run.py -c --pre-save` in a repo with changes; check file `_commit-<ts>.json` appears; run pytest). Flag any risk you see (e.g., ChatApp thread, Windows console encoding, filename collisions when blame makes many rapid calls — decide if seconds-resolution timestamp suffices or a counter/microseconds is needed).

----

# Opção oculta `--pre-save` — dump do payload de IA antes do envio

## Contexto

O usuário identificou um problema quando o prompt enviado à IA é muito grande e precisa inspecionar **exatamente** o que será enviado ao modelo (system message + prompt) antes do envio. Solução: uma flag oculta `--pre-save` que, ativada, salva o payload completo em um arquivo JSON no diretório atual e **continua a execução normalmente** (salvar e continuar, não é dry-run).

Decisões confirmadas com o usuário:
- **Nome do arquivo:** `_{acao}-{datahora}.json` (ex.: `_pr_desc-20260718143210123456.json`) — datahora no formato `%Y%m%d%H%M%S` + microssegundos (`%f`) para evitar colisão quando o blame faz várias chamadas seguidas.
- **Comportamento:** salvar e continuar (a chamada de IA prossegue).
- **Escopo:** todas as chamadas — `call_ai_model()` (PR, commit, review, fullreview, filereview, issue, blame) **e** `call_ai_chat()` (chat TUI).

Ponto de estrangulamento único já existente: `src/ai_providers.py` — todos os engines passam por `call_ai_model()` (linha 13) ou `call_ai_chat()` (linha 139). Interceptar ali cobre tudo sem duplicação.

## Alterações

### 1. `src/ai_providers.py` — flag de módulo + helper + interceptação

- Adicionar `from datetime import datetime` aos imports do topo.
- Após os imports (linha ~11), adicionar:
  - `PRE_SAVE_ENABLED = False` (flag de módulo)
  - `def set_pre_save(enabled):` — setter que faz `global PRE_SAVE_ENABLED`.
  - `def _save_pre_save_payload(action, provider, api_model, system_instruction, prompt=None, chat_history=None, new_message=None):`
    - Gera `filename = f"_{action}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"` no CWD.
    - Conteúdo do JSON (`ensure_ascii=False, indent=2`, `encoding="utf-8"`):
      - Sempre: `datetime` (legível), `action`, `provider`, `model`, `system_instruction`, `system_instruction_chars`.
      - Chamada normal: `prompt`, `prompt_chars`, `total_chars`.
      - Chat: `chat_history`, `new_message`, `chat_history_chars`, `new_message_chars`, `total_chars`.
      - Os contadores de caracteres existem porque o problema investigado é tamanho de prompt.
    - `try/except` retornando o filename ou `None` — ferramenta de debug **nunca** pode quebrar o fluxo principal.
- `call_ai_model()` (linha 13): adicionar kwarg `action="ai_call"` à assinatura. Antes de `spinner = Spinner(quiet=quiet)` (linha 20) — ou seja, uma única vez, antes do loop de retry e antes do spinner iniciar:
  ```python
  if PRE_SAVE_ENABLED:
      saved_file = _save_pre_save_payload(action, provider, api_model, system_instruction, prompt=prompt)
      if saved_file and not quiet:
          click.secho(__("📝 Pre-save: AI payload saved to {filename}", filename=saved_file), fg="yellow", dim=True)
  ```
- `call_ai_chat()` (linha 139): mesmo bloco antes do spinner (linha 144), com `action` fixo `"chat"` e `chat_history=chat_history, new_message=new_message`. O TUI chama com `quiet=True`, então a mensagem não corrompe a interface Textual.

### 2. Propagar o rótulo `action` nos call sites (1 palavra por linha)

| Arquivo:linha                                       | Alteração                                                                                                                                   |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| [src/core.py:218](src/core.py#L218)                 | `call_ai_model(..., instrucao_sistema, action=action_folder)` — `action_folder` já existe na linha 171 (`pr_desc`/`commit`/`review`/`misc`) |
| [src/blame_engine.py:86](src/blame_engine.py#L86)   | `action="blame"`                                                                                                                            |
| [src/blame_engine.py:213](src/blame_engine.py#L213) | `action="blame_summary"`                                                                                                                    |
| [src/issue_engine.py:81](src/issue_engine.py#L81)   | `action="issue"`                                                                                                                            |

### 3. `src/main.py` — opção oculta + wiring

- Novo decorator após `--quiet` (linha 145), seguindo o padrão dos hidden existentes:
  ```python
  @click.option('--pre-save', is_flag=True, hidden=True, help=__("Saves the full AI payload (system + prompt) to a JSON file before each AI call (debug)."))
  ```
- Adicionar `pre_save` à assinatura de `cli()` (linha 154), após `quiet`.
- Após o bloco de hot-swap cleanup (linha 231-237) e antes de `if linter:` (linha 239) — ponto que antecede todos os caminhos que chamam IA (blame, issue, chat, fluxo principal):
  ```python
  # Enable AI payload dump for inspection (hidden debug flag)
  if pre_save:
      from src.ai_providers import set_pre_save
      set_pre_save(True)
  ```
  (import local segue o estilo existente do arquivo, ex. `from src.i18n import set_lang` na linha 218.)
- Segurança verificada: o help contextual (linhas 165-214) itera `HELP_MAP`, que não contém `pre_save` — nada quebra.

### 4. `langs/pt_br.json` — 2 novas chaves

```json
"Saves the full AI payload (system + prompt) to a JSON file before each AI call (debug).": "Salva o payload completo da IA (system + prompt) em um arquivo JSON antes de cada chamada (debug).",
"📝 Pre-save: AI payload saved to {filename}": "📝 Pre-save: payload da IA salvo em {filename}"
```

### 5. `tests/test_pre_save.py` — novo arquivo (padrão pytest de `tests/test_chat_backend.py`)

- **Teste 1 — toggle:** usar `import src.ai_providers as ai_providers` e ler `ai_providers.PRE_SAVE_ENABLED` (não `from ... import PRE_SAVE_ENABLED`, que copiaria o valor no import). Resetar para `False` em `finally`.
- **Teste 2 — criação do arquivo:** `monkeypatch.chdir(tmp_path)`, chamar `_save_pre_save_payload(action="commit", provider="gemini", api_model="...", system_instruction="...", prompt="...")`, verificar que o arquivo `_commit-*.json` existe e contém as chaves `action`, `provider`, `model`, `system_instruction`, `prompt`, `total_chars` com valores corretos (utf-8).

### 6. Relatório obrigatório (regra do CLAUDE.md)

Criar `docs/claude-code/reports/develop_natan/2026-07-18_pre_save_option.md` com o formato de Completion Report padrão.

## Ressalvas (comportamento esperado, documentar no relatório)

- **Cache hit:** `core.py:197-200` (e issue engine) consultam o cache MD5 **antes** de chamar `call_ai_model` — com cache hit nada é enviado à IA e nenhum arquivo é gerado (correto: não há envio a inspecionar). Para forçar o dump, limpe `~/.gitpr/cache/prompts/` ou altere o diff.
- O dump ocorre 1× antes do loop de retry (retries reenviam o mesmo payload).
- Falha ao gravar o arquivo é silenciosa (retorna `None`) — debug não pode derrubar o pipeline.
- `templates/gitpr.thinking-words.md` está modificado no working tree por causa alheia a esta task — não tocar.

## Verificação

1. `python -m pytest tests/ -v` — suite completa passa, incluindo os 2 novos testes.
2. Manual, em um repo com mudanças não commitadas:
   - `pipenv run python run.py -c --pre-save` → fluxo de commit normal **+** `_commit-<ts>.json` no CWD; abrir o JSON e conferir que `system_instruction` + `prompt` batem com o esperado e que `total_chars` reflete o tamanho.
   - `pipenv run python run.py -c` (sem a flag) → nenhum `_*.json` criado.
   - `pipenv run python run.py --pre-save` → `_pr_desc-<ts>.json`.
   - `pipenv run python run.py -c --pre-save --lang pt_br` → mensagem traduzida.
3. `pipenv run python run.py -h` → `--pre-save` **não** aparece no help (hidden).
