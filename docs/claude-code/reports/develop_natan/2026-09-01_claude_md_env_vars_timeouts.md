## Completion Report — Add timeout env vars to CLAUDE.md env-var list

### What was done
- **Added `GITPR_AI_TIMEOUT` and `GITPR_LINTER_TIMEOUT`** to the "Environment variables" list in [CLAUDE.md:280](CLAUDE.md#L280) (after `PR_AUTO_PUBLISH`), completing the documentation chain for the two timeout variables (AI call timeout, 180s default; external linter subprocess timeout, 120s default).
- **Verified the list against `src/config.py` `DEFAULT_CONFIG`** before editing (per the project memory: CLAUDE.md/GEMINI.md age silently and must be cross-checked with `src/`).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| CLAUDE.md | docs | Added `GITPR_AI_TIMEOUT`, `GITPR_LINTER_TIMEOUT` to the env-var list |

### Impact
- **Functionality:** none — documentation-only change.
- **Performance:** none.
- **Compatibility:** the auto-loaded instruction file now lists the two timeout vars, matching `src/config.py`.

### Next steps (if applicable)
- **Findings from the cross-check (not fixed — outside the approved scope):**
  1. **GEMINI.md:313** has a parallel env-var list that is already divergent: it includes `OLLAMA_API_MODEL_*` (absent from CLAUDE.md) but lacks `PR_DEFAULT_BASE`/`PR_AUTO_PUBLISH` and the two timeouts. Syncing it is a possible future task.
  2. Both lists still omit vars present in `DEFAULT_CONFIG`: `OLLAMA_API_MODEL_PRIMARY`/`SECONDARY` (in GEMINI only), `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SHOW_LOGS`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`, `GITPR_AUTO_MERGE`, `OUTPUT_FILE_NAME_LINTER`, plus the read-only opt-out `GITPR_COAUTHOR` (`src/config.py:coauthor_enabled()`). A full enumeration sync of both files is a possible future task.
