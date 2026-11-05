# Walkthrough — Project-Local Configuration Seed (`gitpr seed`)

The pending item from `docs/reports/relatorio_estado_v0.0.22.md` regarding project-local configuration seeding has been implemented and verified.

## Summary of Changes

1. **Project Configuration Seeding Engine (`src/core.py` & `src/project_config.py`):**
   - Refactored `_seed_local_smart_excludes(project_root=None, force=False)` to support idempotent file creation, returning a structured result dict.
   - Enhanced `ensure_project_config(..., force=False)` in `src/project_config.py` to support overwriting on `--force`.
   - Enhanced `download_skill_file(..., force=False)` in `src/core.py` to support force-downloading templates.
   - Implemented `seed_project_configuration(force=False, include_all_skills=False, quiet=False, project_root=None)` which orchestrates:
     - `.gitpr/conf/gitpr.config.yml` (PR base branch)
     - `.gitpr/conf/gitpr.smart-excludes.json` (Project-specific Smart Excludes)
     - `.gitpr/skill/.gitpr.linter.yml` (Local static linter rules)
   - Integrated `_seed_local_smart_excludes()` into `generate_skill_template()` (`gitpr --skill`).

2. **CLI Entry Points & Telemetry (`src/main.py`):**
   - Created standalone Click subcommand: `gitpr seed [--force] [--all]`.
   - Added root option flag: `gitpr --seed` / `-sd`.
   - Added contextual help entry for `seed` in `FEATURE_HELP`.
   - Logged execution metric to SQLite telemetry ledger (`command="seed"`, `provider="local"`).

3. **Expanded Interactive Setup Wizard (`src/core.py`):**
   - Reorganized `run_install_wizard()` into **5 structured steps**:
     - **Step 1 of 5:** Project Local Configuration (`.gitpr/conf/`)
     - **Step 2 of 5:** Skill Templates & Linter (`.gitpr/skill/`) with optional external linter prompt
     - **Step 3 of 5:** Git Hooks (`.git/hooks/`)
     - **Step 4 of 5:** MCP Configuration
     - **Step 5 of 5:** API Key Configuration

4. **Resilience & Internationalization:**
   - Wrapped `load_dotenv` calls in `src/i18n.py` and `src/spinner.py` with try/except to ensure stability in sandboxed and read-only environments.
   - Updated language assets (`langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`, `langs/es.json`, `langs/fr_fr.json`, `langs/fr.json`).
   - Bumped `__lang_version__` to `v0.0.40` in `src/updater.py`.

5. **Updated Documentation:**
   - Updated `docs/install-wizard.*.md` (EN, PT-BR, PT-PT, ES-ES, FR-FR) to reflect the 5 wizard steps and explain `gitpr seed`.

---

## Verification Results

### Automated Tests
Ran the full suite of related tests:
```bash
python -m pytest tests/test_seed_command.py tests/test_install_wizard.py tests/test_skill_command.py tests/test_smart_excludes.py tests/test_i18n.py -v
```
**Result:** **60 passed in 12.16s** (100% green).
- `tests/test_seed_command.py`: 8 passed
- `tests/test_install_wizard.py`: 3 passed
- `tests/test_skill_command.py`: 10 passed
- `tests/test_smart_excludes.py`: 17 passed
- `tests/test_i18n.py`: 22 passed
