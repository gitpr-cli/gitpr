## Completion Report — Project-Local Configuration Seed (`gitpr seed`)

### What was done
- Implemented `seed_project_configuration` in `src/core.py` to seed `.gitpr/conf/gitpr.config.yml`, `.gitpr/conf/gitpr.smart-excludes.json`, and `.gitpr/skill/.gitpr.linter.yml`.
- Refactored `_seed_local_smart_excludes(project_root=None, force=False)` with structured return status.
- Added support for `--force` in `ensure_project_config()` (`src/project_config.py`) and `download_skill_file()` (`src/core.py`).
- Integrated automatic seeding of `.gitpr/conf/gitpr.smart-excludes.json` into `generate_skill_template()` (`gitpr --skill`).
- Reorganized `run_install_wizard()` in `src/core.py` to 5 steps, establishing Step 1 as *Project Local Configuration* and offering an optional external linter prompt in Step 2.
- Created `gitpr seed` Click subcommand and `--seed` / `-sd` CLI flag with `--force` and `--all` options in `src/main.py`.
- Connected command execution metric logging (`command="seed"`, `provider="local"`) to the SQLite telemetry ledger.
- Added domain glossary entry `Project configuration seed` to `CONTEXT.md`.
- Updated i18n dictionaries across 6 files (`pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr`) and bumped `__lang_version__` to `v0.0.40`.
- Hardened `load_dotenv` calls in `src/i18n.py` and `src/spinner.py` against sandboxed or read-only filesystem environments.
- Created unit and CLI integration tests in `tests/test_seed_command.py` (8 test scenarios).
- Updated documentation in `docs/install-wizard.*.md` across 5 languages.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat/refactor | Added `seed_project_configuration`, updated `_seed_local_smart_excludes`, `download_skill_file`, `generate_skill_template`, and 5-step `run_install_wizard` |
| `src/project_config.py` | feat | Added `force=False` parameter to `ensure_project_config` |
| `src/main.py` | feat | Added `seed` subcommand, `--seed` / `-sd` flag, contextual help, and ledger telemetry |
| `src/i18n.py` | fix | Made `load_dotenv` resilient against permission errors |
| `src/spinner.py` | fix | Made `load_dotenv` resilient against permission errors |
| `src/updater.py` | chore | Bumped `__lang_version__` to `v0.0.40` |
| `CONTEXT.md` | docs | Added `Project configuration seed` domain term |
| `langs/*.json` | feat | Added and translated 20 new localization keys (PT-BR, PT-PT, ES, FR) |
| `tests/test_seed_command.py` | test | New dedicated unit and CLI tests for seed command |
| `tests/test_install_wizard.py` | test | Adapted test mocks for the 5-step wizard |
| `docs/install-wizard.*.md` | docs | Documented the 5-step wizard and `gitpr seed` command in 5 languages |

### Impact
- **Functionality:** Resolves the pending `.gitpr/conf/` seeding task, giving developers both automated (wizard/skill) and manual (`gitpr seed`) controls to initialize project configuration files.
- **Performance:** Local seed runs instantaneously without network overhead (unless `--all` or initial remote linter download is requested).
- **Compatibility:** Strictly backward-compatible; existing configurations are never overwritten unless `--force` is explicitly provided.

### Next steps (if applicable)
- Verify `gitpr seed` in live multi-project environments.
