## Completion Report — Document GITPR_SKIP_UPDATE_CHECK Semantic Change as Migration Note

### What was done
- Documented the semantic change of `GITPR_SKIP_UPDATE_CHECK` (introduced in v1.4.3 with the strict boolean parser) as a migration note across reference documentation and tutorials in all 5 supported languages (EN, PT-BR, PT-PT, ES-ES, FR-FR).
- Added the dedicated sub-section `Escape Switch for Local Development (GITPR_SKIP_UPDATE_CHECK)` with a `> [!WARNING]` migration note in `docs/auto-update.*.md`.
- Added a `> [!WARNING]` migration note callout in Section 5 of `docs/tutorial/install-from-source.*.md` explicitly highlighting that legacy scripts setting `=false` or `=0` expecting to mute the check now leave it enabled and execute the update gate.
- Formalized the canonical domain term `Update check switch` in `CONTEXT.md`.
- Maintained documentation parity across all 5 official languages of the project.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CONTEXT.md` | docs / domain-modeling | Added canonical term `Update check switch` |
| `docs/auto-update.md` | docs | Added escape switch sub-section and migration note (EN) |
| `docs/auto-update.pt_br.md` | docs | Added escape switch sub-section and migration note (PT-BR) |
| `docs/auto-update.pt_pt.md` | docs | Added escape switch sub-section and migration note (PT-PT) |
| `docs/auto-update.es_es.md` | docs | Added escape switch sub-section and migration note (ES-ES) |
| `docs/auto-update.fr_fr.md` | docs | Added escape switch sub-section and migration note (FR-FR) |
| `docs/tutorial/install-from-source.md` | docs | Added strict boolean parser migration note callout in Section 5 (EN) |
| `docs/tutorial/install-from-source.pt_br.md` | docs | Added strict boolean parser migration note callout in Section 5 (PT-BR) |
| `docs/tutorial/install-from-source.pt_pt.md` | docs | Added strict boolean parser migration note callout in Section 5 (PT-PT) |
| `docs/tutorial/install-from-source.es_es.md` | docs | Added strict boolean parser migration note callout in Section 5 (ES-ES) |
| `docs/tutorial/install-from-source.fr_fr.md` | docs | Added strict boolean parser migration note callout in Section 5 (FR-FR) |

### Impact
- **Functionality:** Prevents confusion and unexpected execution blocks for developers and CI maintainers migrating legacy automation scripts that previously set `GITPR_SKIP_UPDATE_CHECK=false` or `=0`.
- **Performance:** Zero runtime performance impact (documentation and domain glossary changes only).
- **Compatibility:** Backward compatible. Clarifies breaking changes introduced in version 1.4.3.

### Next steps (if applicable)
- None. The inherited open item is now fully resolved and closed across all documentation surfaces.
