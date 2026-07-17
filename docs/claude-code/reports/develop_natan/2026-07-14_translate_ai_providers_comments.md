## Completion Report — Translate ai_providers.py comments and sync i18n keys

### What was done
- Translated all Portuguese comments and docblocks to English in `src/ai_providers.py`, starting from line 86 (`load_chat_commands`, `process_chat_command`, `call_ai_chat`).
- Audited the `__()` translatable strings in that region:
  - `"❌ Unknown AI provider: {provider}"` — already present in all language files (no change).
  - `"\r❌ Critical error in Chat API ({provider}): {error}"` — **new**; added to all language files.
- Added the new key to `langs/pt_br.json`, `langs/pt_pt.json`, `langs/fr_fr.json`, `langs/es_es.json`.
- Bumped `__lang_version__` from `v0.0.3` to `v0.0.4` in `src/updater.py` (new key added).
- Validated all four JSON dictionaries parse successfully.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/ai_providers.py | docs | Translated comments/docblocks (from line 86) to English |
| langs/pt_br.json | feat | Added `"\r❌ Critical error in Chat API ({provider}): {error}"` translation |
| langs/pt_pt.json | feat | Added same key (PT-PT translation) |
| langs/fr_fr.json | feat | Added same key (FR translation) |
| langs/es_es.json | feat | Added same key (ES translation) |
| src/updater.py | chore | `__lang_version__` bumped to `v0.0.4` |

### Impact
- **Functionality:** No behavior change. The chat-API critical-error message is now translatable instead of falling back to the raw English key.
- **Performance:** None.
- **Compatibility:** Non-breaking. Language version bump signals clients to refresh cached dictionaries via the existing updater flow.

### Next steps (if applicable)
- Remote `langs/*.json` on GitHub main should be updated so downloaded dictionaries match the new `v0.0.4`.
