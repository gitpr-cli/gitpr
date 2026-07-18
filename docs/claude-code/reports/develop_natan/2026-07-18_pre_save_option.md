# Completion Report — Hidden `--pre-save` option (AI payload dump)

## What was done

Added a hidden CLI flag `--pre-save` that, when enabled, dumps the **full AI payload** (system instruction + user prompt + provider/model info + character counts) to a JSON file in the current working directory **before** the request is sent to the model. The call then proceeds normally (save-and-continue, not a dry-run). Motivation: the author needed to inspect exactly what is sent to the AI to debug a problem with very large prompts.

- File naming: `_{action}-{datetime}.json` — e.g. `_pr_desc-20260718150334633166.json`. `action` ∈ `pr_desc`, `commit`, `review`, `misc`, `issue`, `blame`, `blame_summary`, `chat`. Datetime format `%Y%m%d%H%M%S%f` (microseconds prevent collisions when the blame engine fires several calls in a loop).
- Interception happens at the single choke point in `src/ai_providers.py`, covering **all** engines: PR description, commit, review/fullreview/filereview, issue, blame (classification + executive summary) and the interactive chat TUI.
- The flag is toggled once from `main.py` via a new module-level setter (`set_pre_save()`), avoiding threading a new parameter through `generate_pr_content`/`run_blame_analysis`/`generate_issue_content`/`ChatApp` signatures.
- A confirmation message (`📝 Pre-save: AI payload saved to {filename}`) is printed via `__()` before the spinner starts; it is suppressed in quiet mode (the chat TUI calls with `quiet=True`, so the Textual interface is never corrupted).
- A failure to write the dump file is silent (helper returns `None`) — a debug tool must never break the main pipeline.

## Changed files

| File | Change type | Description |
| ---- | ----------- | ----------- |
| src/ai_providers.py | feat | `PRE_SAVE_ENABLED` module flag, `set_pre_save()` setter, `_save_pre_save_payload()` helper; interception blocks in `call_ai_model()` (new `action="ai_call"` kwarg) and `call_ai_chat()` (action fixed as `"chat"`); added `datetime` import |
| src/main.py | feat | Hidden `@click.option('--pre-save', is_flag=True, hidden=True, ...)` after `--quiet`; `pre_save` param in `cli()`; wiring block calling `set_pre_save(True)` before all AI code paths |
| src/core.py | feat | Pass `action=action_folder` at the `call_ai_model()` call site (line 218) |
| src/blame_engine.py | feat | Pass `action="blame"` (commit classification) and `action="blame_summary"` (executive summary) |
| src/issue_engine.py | feat | Pass `action="issue"` at the `call_ai_model()` call site |
| langs/pt_br.json | feat | 2 new translation keys (flag help text + saved-file message) |
| tests/test_pre_save.py | test | New file: toggle test + payload dump tests (model call and chat call variants) |
| README.md | docs | Technical note documenting the `--pre-save` debug flag (same pattern as the existing `--hook` note) |
| README.pt_br.md | docs | Same technical note in Portuguese |

## JSON dump schema

Standard calls: `datetime`, `action`, `provider`, `model`, `system_instruction`, `system_instruction_chars`, `prompt`, `prompt_chars`, `total_chars`.
Chat calls: replaces `prompt`/`prompt_chars` with `chat_history`, `new_message`, `chat_history_chars`, `new_message_chars`. Character counters were included specifically to help diagnose the large-prompt problem. Written with `ensure_ascii=False, indent=2, encoding="utf-8"`.

## Impact

- **Functionality:** No behavior change when the flag is absent (default `False`). With `--pre-save`, one JSON file per AI call is written to CWD. The flag does not appear in `gitpr -h` (hidden, like `--hook`/`--quiet`).
- **Performance:** Negligible — one small file write per AI call, only when the flag is enabled.
- **Compatibility:** `call_ai_model()` gained an optional trailing kwarg (`action="ai_call"`); all existing positional call signatures remain valid. No API breaks, no cache-key impact (prompts are unchanged, so MD5 cache entries stay valid).

## Known caveats (by design)

- **Cache hit:** `core.py` and `issue_engine.py` check the MD5 cache *before* calling `call_ai_model()`. On a cache hit, nothing is sent to the AI, so no dump file is generated (correct: there is no outgoing payload to inspect). To force a dump, clear `~/.gitpr/cache/prompts/` or change the diff.
- The dump happens once, before the retry loop (retries resend the identical payload).

## Verification performed

1. `python -m pytest tests/ -v` → **26 passed** (23 pre-existing + 3 new).
2. Choke-point exercise (no API key needed, unknown provider): `set_pre_save(True)` + `call_ai_model(...)` + `call_ai_chat(...)` in a temp dir → `_commit-<ts>.json` and `_chat-<ts>.json` created with the correct schema and counters; both functions continued into normal flow.
3. `python run.py -h` → `--pre-save` not listed (hidden), exit code 0 (identical to the pre-change code, verified via stash roundtrip); `python run.py --pre-save -h` → flag accepted by Click, standard help shown.

## Next steps (suggestions)

- If the large-prompt investigation confirms a size limit, a follow-up could add a warning threshold based on `total_chars`.
