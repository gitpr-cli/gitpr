## Completion Report — Document GITPR_AI_TIMEOUT in providers-ia.md

### What was done
- **Documented `GITPR_AI_TIMEOUT`** (the next step suggested in the MCP docs audit report) in the AI Providers technical doc — the natural home for it, since the doc already documented generation parameters (temperature, top_p, retry, cache).
- Added a **Timeout row** to the "Generation Parameters" table in section 6 of `docs/providers-ia.md`: `180s per call (configurable via GITPR_AI_TIMEOUT in ~/.gitpr/.env)`.
- Added a short **explanatory paragraph** stating the semantics: each model call is bounded by 180s so a hung provider fails fast with a visible error instead of freezing the CLI; invalid or non-positive values fall back to the 180s default.
- **Mirrored the change in all 4 localized variants** (`.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr`), preserving the multilingual convention's parity (canonical English + suffix localizations).
- Scope kept surgical: only the timeout variable documented; the sibling `GITPR_LINTER_TIMEOUT` was not touched (not requested).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/providers-ia.md | docs | Timeout row + explanation paragraph in section 6 (Generation Parameters) |
| docs/providers-ia.pt_br.md | docs | Mirrored addition (PT-BR) |
| docs/providers-ia.pt_pt.md | docs | Mirrored addition (PT-PT) |
| docs/providers-ia.es_es.md | docs | Mirrored addition (ES) |
| docs/providers-ia.fr_fr.md | docs | Mirrored addition (FR) |

### Impact
- **Functionality:** none — documentation-only change; no code or behavior touched.
- **Performance:** none.
- **Compatibility:** docs now state the real default (180s, shipped in commit `681a7fa`); previously no live doc mentioned `GITPR_AI_TIMEOUT` (grep matched only historical reports).

### Next steps (if applicable)
- None required. Optional for a future task: `GITPR_LINTER_TIMEOUT` (120s default) could get the same treatment in the linter docs (`linter-regras-customizadas.md`), if desired.
