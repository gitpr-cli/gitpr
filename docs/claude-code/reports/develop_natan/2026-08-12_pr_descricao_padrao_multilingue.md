## Completion Report — Default PR Description Docs: Publishing Update + Multilingual Set

### What was done
- Updated `docs/pr-descricao-padrao.md` with the new PR publishing functionality: 3 execution modes (`gitpr`, `--no-publish`, `--no-edit`), unstaged files check in the flow, TUI shortcuts (F1/F2/F3/Esc), PAT requirement, and base branch resolution
- Corrected the output location from "project root" to `.gitpr/reports/pr_desc/` (per centralized output paths)
- Converted the canonical file to English, per the docs convention (EN canonical + locale suffixes)
- Created the 4 locale files: `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`
- Added cross-links to the complete publishing guide (`pull-request-publication.md`)

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/pr-descricao-padrao.md | docs | Canonical rewritten in English with publishing section (modes, TUI shortcuts, PAT, base branch) and updated flow/output |
| docs/pr-descricao-padrao.pt_br.md | docs | New Brazilian Portuguese localization |
| docs/pr-descricao-padrao.pt_pt.md | docs | New European Portuguese localization (preserves previous content, extended with publishing section) |
| docs/pr-descricao-padrao.es_es.md | docs | New Spanish localization |
| docs/pr-descricao-padrao.fr_fr.md | docs | New French localization |
| docs/claude-code/reports/develop_natan/2026-08-12_pr_descricao_padrao_multilingue.md | docs | This report |

### Impact
- **Functionality:** None — documentation only. The doc set now matches the current default behavior (TUI publisher after PR generation) and the existing README links (all 5 READMEs link to `pr-descricao-padrao.md`).
- **Performance:** No impact.
- **Compatibility:** Filename unchanged, so existing links (README, `pull-request-publication` docs, `mcp-prompts` docs) keep working. Canonical file language changed from pt-pt to English per the project's docs convention (EN canonical + locale suffixes).

### Next steps
- None required. The canonical content is the reference for future updates; locales should be updated in sync.
