# Implementation Plan — Paying Remaining i18n Technical Debts

## Goal Description
Resolve all remaining internationalization (i18n) technical debts across the codebase:
1. **Unwrapped UI & CLI strings**: Wrap user-facing strings in `src/ui/chat_app.py` (Chat Help modal titles and keyboard shortcuts, including fixing the `Ctrlhift+S`/`Ctrlhift+E` typo) and `src/mcp_server.py` (CLI help/description) in `__()`.
2. **Untranslated identity keys**: Provide accurate and idiomatic translations for ~45 user-facing strings currently stored identically to English (`key == value`) across all six dictionary files (`pt_br.json`, `pt_pt.json`, `es.json`, `es_es.json`, `fr.json`, `fr_fr.json`).
3. **AI prompt prefix registration**: Register the business rule timeline blame prompt in `AI_PROMPT_PREFIXES` in `tests/test_i18n.py`.
4. **Test suite hardening**: Enhance `tests/test_i18n.py` to audit all identity keys against an explicit whitelist of universal technical terms/acronyms and AI prompts, preventing future untranslated English strings from passing silently.
5. **OTA version bump**: Increment `__lang_version__` in `src/updater.py` from `v0.0.36` to `v0.0.37` so client installations receive updated translations via OTA.

## User Review Required
- All six language dictionaries will remain in 100% key parity (1677 keys each after adding the newly wrapped strings).
- Translations for all ~45 identity keys + new chat help & MCP CLI keys will be added to PT-BR, PT-PT, ES, ES-ES, FR, and FR-FR.
- The chat keyboard shortcut text fix (`Ctrlhift+S` -> `Ctrl+Shift+S`) corrects an existing UI typo.

## Proposed Changes

### UI Components

#### [MODIFY] `src/ui/chat_app.py`
- Enclose Help modal title, section headers, and keyboard shortcut lines in `__()`:
  - `__("💡 Chat Help")`
  - `__("⌨️ Keyboard Shortcuts")`
  - `__("⚡ Slash Commands")`
  - Shortcut items:
    - `__("• [bold]F1[/bold] Help — Shows this help modal\n")`
    - `__("• [bold]F2[/bold] Refresh Diff — Updates the chat context with the latest code changes\n")`
    - `__("• [bold]F5[/bold] Auto-Patch — Extracts code blocks from the last AI response\n")`
    - `__("• [bold]F6[/bold] Export — Saves the full conversation to a Markdown file\n")`
    - `__("• [bold]F7/F8[/bold] — Navigate focus between AI messages\n")`
    - `__("• [bold]Ctrl+Shift+S[/bold] — Auto-Patch the focused AI message\n")`
    - `__("• [bold]Ctrl+Shift+E[/bold] — Export the focused AI message\n")`
    - `__("• [bold]Esc[/bold] Exit — Closes the chat")`

---

### MCP Server CLI

#### [MODIFY] `src/mcp_server.py`
- Enclose `argparse.ArgumentParser` description and argument `help=` strings in `__()` in `run_cli()`:
  - `__("GitPR MCP Server — integrate GitPR with AI-powered editors.")`
  - `__("Print the complete tools catalog as JSON (tools, resources, and prompts). Use this to discover available capabilities without starting the server.")`
  - `__("Install MCP configuration for an editor (vscode, cursor, claude-code, claude, zed, or auto-detect).")`
  - `__("Invoke a single MCP tool directly and print its JSON result to stdout. Use --tool-args to pass parameters as a JSON object. Use '--tool' alone (no NAME) to list available tools.")`
  - `__('JSON object with tool parameters, e.g. \'{"file_path": "src/main.py", "start_line": "10", "end_line": "20"}\'. Only meaningful with --tool.')`

---

### Internationalization Dictionaries

#### [MODIFY] `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es.json`, `langs/es_es.json`, `langs/fr.json`, `langs/fr_fr.json`
- Add translations for the 12 newly wrapped strings from `chat_app.py` and `mcp_server.py`.
- Provide natural and context-accurate translations for the ~45 identity keys:
  - Geração de testes (`gitpr tests`): `"Analyzing diff and generating test file..."`, `"Writes the generated test file directly to disk."`, `"Forces the test framework (pest, phpunit, jest, vitest, pytest)."`, `"Covered Scenarios:"`, `"Generated Test Code"`, `"Suggested Path:"`, `"Target Finding:"`, `"Target Framework:"`, `"Target Test Path:"`, `"❌ Test generation failed."`, etc.
  - Reviewer Guide / Explain PR (`gitpr explain`): `"Analyzing diff from reviewer perspective..."`, `"Generating Reviewer Guide (Explain my PR)..."`, `"REVIEWER GUIDE (Explain My PR)"`, `"Reviewer Guide (Explain My PR)"`, `"Reviewer Guide (--explain / gitpr explain)"`, `"Explain PR by Default"`, `"What changes"`, `"What changes:"`, `"Why it changes"`, `"Why it changes:"`, `"Where to focus review"`, `"Where to focus review:"`, `"Regression Risk"`, `"Regression Risk:"`, etc.
  - PR History & Commits: `"=== AI PR HISTORY ===\n"`, `"=== AI PR HISTORY ===\nNo previous AI-generated PR found in cache for this branch.\n"`, `"=== REGISTERED COMMITS ===\n"`, `"No exclusive commits found in this branch.\n\n"`.
  - Prompts e avisos: `"ℹ️ Dry-run mode. Run with --apply to write to disk."`, `"⚠️ Notice: Inferred with partial context. Some fields contain placeholders to complete."`, `"❓ Overwrite existing test file?"`, `"❓ Write test file to disk?"`, `"❌ Overwrite cancelled by user."`, `"[FILL: Please explain the motivation for these changes]"`.

---

### Versioning & Updater

#### [MODIFY] `src/updater.py`
- Bump `__lang_version__` from `"v0.0.36"` to `"v0.0.37"`.

---

### Test Suite Hardening

#### [MODIFY] `tests/test_i18n.py`
- Add `"Based on the following commit timeline of a business rule"` to `AI_PROMPT_PREFIXES`.
- Update `test_identity_keys_with_braces_allowlist` (or replace with a comprehensive `test_identity_keys_allowlist`) to check all keys in the dictionary where `k == v`, ensuring only explicitly allowed technical terms (e.g. `"Tokens"`, `"SCM / Forge"`, `"Semgrep SAST"`, `"Auto-Patch"`, `"id:"`, categories like `"Baseline"`, `"Commit"`, `"Issue"`, `"Linter"`, status markers `"[OK]"`, `"[FAIL]"`, `"✔ {version}"`, and `AI_PROMPT_PREFIXES`) can remain untranslated.

---

## Verification Plan

### Automated Tests
Run the i18n test suite:
```bash
pytest tests/test_i18n.py -v
```
Verify:
1. `test_json_valid_and_str_values` passes.
2. `test_no_mangled_keys` passes.
3. `test_key_parity_and_count` passes with 100% parity across all 6 files.
4. `test_no_missing_keys` passes (every `__()` call in code has an entry).
5. `test_no_orphan_keys` passes (no dead keys).
6. `test_identity_keys_allowlist` passes (no rogue untranslated English strings).

### Manual Verification
1. Run `gitpr-mcp --help` with `GITPR_LANG=pt_br` and observe translated CLI options.
2. Verify that `langs/*.json` are valid JSON with UTF-8 encoding.
