## Completion Report — Document GITPR_LINTER_TIMEOUT in linter-regras-customizadas.md

### What was done
- **Documented `GITPR_LINTER_TIMEOUT`** (the optional next step suggested in the `GITPR_AI_TIMEOUT` report) in the custom linter technical doc — the natural home, since the timeout bounds the **external linter subprocesses** (section 5, "Integration with External Linters").
- Added a new subsection **"External Linter Timeout"** to section 5 of `docs/linter-regras-customizadas.md`, right before "Quick Setup (--linter-setup)": each external linter subprocess is bounded by a 120-second timeout (configurable via `GITPR_LINTER_TIMEOUT` in `~/.gitpr/.env`); if a linter exceeds the bound it is skipped — its violations are not included in the report — instead of blocking the whole review; invalid or non-positive values fall back to the 120s default.
- Semantics verified against the code before writing: [src/linter_engine.py:111](src/linter_engine.py#L111) passes `get_linter_timeout()` as `subprocess.run(timeout=...)`; on timeout (or any error) `_run_external_linter` returns `""` — the linter is skipped, not blocking the review. The doc text reflects that, not a hypothetical "visible error".
- **Mirrored the change in all 4 localized variants** (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`), preserving the multilingual convention's parity.
- Scope kept surgical: only the new subsection added; no other content touched (existing markdownlint warnings in the files are pre-existing).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/linter-regras-customizadas.md | docs | New subsection "External Linter Timeout" in section 5 |
| docs/linter-regras-customizadas.pt_br.md | docs | Mirrored addition (PT-BR) |
| docs/linter-regras-customizadas.pt_pt.md | docs | Mirrored addition (PT-PT) |
| docs/linter-regras-customizadas.es_es.md | docs | Mirrored addition (ES) |
| docs/linter-regras-customizadas.fr_fr.md | docs | Mirrored addition (FR) |

### Impact
- **Functionality:** none — documentation-only change; no code or behavior touched.
- **Performance:** none.
- **Compatibility:** docs now document the real default (120s); previously `GITPR_LINTER_TIMEOUT` was absent from every live doc.

### Next steps (if applicable)
- None required. The two timeout variables (`GITPR_AI_TIMEOUT`, `GITPR_LINTER_TIMEOUT`) are now both documented; `CLAUDE.md`'s env-var list still omits both — a possible future task if that list should enumerate all configurable variables.
