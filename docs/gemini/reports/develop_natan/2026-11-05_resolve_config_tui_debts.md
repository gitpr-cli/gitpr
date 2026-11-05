## Completion Report — Resolve Config TUI Debts

### What was done
- Resolved all four technical debts inherited from the Config TUI feature (`docs/reports/relatorio_estado_v0.0.22.md`):
  1. Eliminated redundant `DEFAULT_CONFIG` dictionary in `src/config.py`: Made `src/config_schema.py` the Single Source of Truth (SSOT) by adding a `seeded: bool = False` flag to `ConfigField`. Marked the 58 core default fields with `seeded=True`, derived `DEFAULT_CONFIG = {field.key: field.default for field in FIELDS if field.seeded}`, and imported it into `src/config.py`.
  2. Updated the opening ASCII banner in `src/main.py` (`print_banner()`) to list `--init` and `--base` alongside `--plugins`.
  3. Disabled the command palette in `LinterApp` (`src/ui/linter_app.py`) via `ENABLE_COMMAND_PALETTE = False`, making it consistent with all other Textual apps in the project.
  4. Added the 9 `GITPR_CHECK_*` configuration keys under a newly declared category `"check"` (`Category("check", __("CI Check"), __("Unified pipeline checks, output formats, thresholds, and execution limits."), doc="check-ci.md")`) in `src/config_schema.py`, with `seeded=False` so they remain optional environment variables rather than forced entries in `~/.gitpr/.env`.
- Synchronized and translated all new i18n keys across all 6 language files (`langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`, `langs/es.json`, `langs/fr_fr.json`, `langs/fr.json`).
- Documented "Seeded configuration field" and "CI Check" in `CONTEXT.md`.
- Expanded the test suite in `tests/test_config_schema.py` with tests for seeded field derivation, check category presence, `LinterApp` command palette disabling, and banner text verification. Verified with 52 tests passing in `test_config_schema.py`, 22 in `test_i18n.py`, and 92 in `test_config_app.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/config_schema.py` | refactor / feat | Added `seeded` field to `ConfigField`, marked 58 fields as seeded, added `"check"` category with 9 `GITPR_CHECK_*` fields, derived `DEFAULT_CONFIG`. |
| `src/config.py` | refactor | Replaced 90+ lines of duplicate `DEFAULT_CONFIG = { ... }` with `from src.config_schema import DEFAULT_CONFIG`. |
| `src/ui/linter_app.py` | fix | Added `ENABLE_COMMAND_PALETTE = False` to `LinterApp`. |
| `src/main.py` | fix | Added `--init` and `--base` to the banner options string. |
| `CONTEXT.md` | docs | Added domain definitions for "Seeded configuration field" and "CI Check". |
| `langs/pt_br.json` | feat | Added Portuguese (Brazil) translations for banner and 9 check fields. |
| `langs/pt_pt.json` | feat | Added Portuguese (Portugal) translations for banner and 9 check fields. |
| `langs/es_es.json` | feat | Added Spanish (Spain) translations for banner and 9 check fields. |
| `langs/es.json` | feat | Added Spanish translations for banner and 9 check fields. |
| `langs/fr_fr.json` | feat | Added French (France) translations for banner and 9 check fields. |
| `langs/fr.json` | feat | Added French translations for banner and 9 check fields. |
| `tests/test_config_schema.py` | test | Added unit tests verifying `DEFAULT_CONFIG` SSOT derivation, check category, and regression assertions for banner and `LinterApp`. |

### Impact
- **Functionality:**
  - `gitpr check` configuration options (`GITPR_CHECK_*`) are now fully inspectable and editable from the Config TUI under the "CI Check" category.
  - The CLI banner now accurately reflects `--init` and `--base`.
  - The `LinterApp` now prevents accidental opening of Textual's default command palette, aligning its UX with other screens.
- **Performance:** Zero negative impact. Dynamic dictionary comprehension executes once on import and maintains the exact 58 seeded configuration keys.
- **Compatibility:** Full backward compatibility. `DEFAULT_CONFIG` remains importable from `src.config` with the exact same keys and values.

### Next steps (if applicable)
- All technical debts specified in `docs/reports/relatorio_estado_v0.0.22.md` for the Config TUI are now resolved.
