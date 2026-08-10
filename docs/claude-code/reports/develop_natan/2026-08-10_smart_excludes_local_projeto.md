## Completion Report — Smart Excludes Local por Projeto

### What was done
- Implemented project-local Smart Excludes file support that merges with the global list at runtime
- Added a `_seed_local_smart_excludes()` function that creates a template `.gitpr/conf/gitpr.smart-excludes.json` file in the project root (idempotent, never overwrites existing files)
- Modified `_load_smart_excludes()` to load and merge project-local excludes with global ones (union, deduplicated)
- Modified `_load_docs_smart_excludes()` to respect the `GITPR_SKIP_SMART_EXCLUDES` env var
- Added env var support: `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, `GITPR_SMART_EXCLUDES_LOCAL`
- Updated technical documentation in all 5 languages (EN, PT-BR, PT-PT, ES, FR)

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| src/core.py | feat | Added `_seed_local_smart_excludes()` function; refactored `_load_smart_excludes()` to support project-local file merge, env overrides, and skip flag; added skip flag to `_load_docs_smart_excludes()` |
| docs/smart-excludes.md | docs | Added project-local file to configuration table; updated resolution chain (5 steps); replaced "Local Override (Temporary)" and "Disabling Specific Extensions" with "Project-Local Configuration", "Temporary Override", and "Disabling Smart Excludes" sections; updated FAQ |
| docs/smart-excludes.pt_br.md | docs | Same updates in Brazilian Portuguese |
| docs/smart-excludes.es_es.md | docs | Same updates in Spanish |
| docs/smart-excludes.fr_fr.md | docs | Same updates in French |
| docs/smart-excludes.pt_pt.md | docs | Same updates in European Portuguese |

### Impact
- **Functionality:** Users can now define project-specific exclusions at `.gitpr/conf/gitpr.smart-excludes.json` that are merged with the global list. The file is auto-seeded on first download. Global exclusion updates no longer wipe project-specific settings.
- **Performance:** No impact — local file is only loaded if present; merge uses set operations (O(n+m)).
- **Compatibility:** Fully backward-compatible. Projects without the local file work exactly as before. All 171 existing tests pass without modification.

### New environment variables

| Variable | Purpose |
|----------|---------|
| `GITPR_SKIP_SMART_EXCLUDES` | Set to `"1"`/`"true"` to disable all Smart Excludes filtering |
| `GITPR_SMART_EXCLUDES_GLOBAL` | Override path to the global excludes file |
| `GITPR_SMART_EXCLUDES_LOCAL` | Override path to the project-local excludes file |

### Next steps
- Consider adding a `gitpr --init` or `gitpr --local-config` command to seed `.gitpr/conf/` with local config templates
- The `--skill` command could be extended to download the local smart-excludes template explicitly
