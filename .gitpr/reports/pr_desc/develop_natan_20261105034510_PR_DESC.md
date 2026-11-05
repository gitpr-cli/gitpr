# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
refactor: derive DEFAULT_CONFIG from config schema as SSOT
```

---

## 🎯 Summary

This change eliminates a hand-maintained duplication between `src/config.py` and `src/config_schema.py` by making the schema the single source of truth (SSOT) for the default environment configuration. Previously, `DEFAULT_CONFIG` was a standalone dictionary in `config.py` that had to be kept manually in sync with the schema; any drift could silently leave new keys missing from the seeded `~/.gitpr/.env`. By deriving `DEFAULT_CONFIG` from a new `seeded=True` flag on schema fields, the two lists can no longer diverge, and the tests that previously guarded against drift are simplified to assert the derivation invariant.

Alongside this refactor, the change introduces a new `check` configuration category (unified CI pipeline checks, output formats, thresholds, and execution limits) and resolves outstanding TUI technical debts (disabled command palette in `LinterApp`, updated banner to advertise `--init` and `--base`), with translations aligned across all supported languages.

## 🛠️ Technical Changes

- Add a `seeded: bool = False` flag to `ConfigField`; fields set to `seeded=True` are automatically included in `DEFAULT_CONFIG`.
- Replace the hardcoded `DEFAULT_CONFIG` dictionary in `src/config.py` with an import from `src.config_schema` to preserve backward compatibility.
- Derive `DEFAULT_CONFIG = {field.key: field.default for field in FIELDS if field.seeded}` in `src/config_schema.py` as the single source of truth.
- Mark all pre-existing default fields with `seeded=True` to retain the exact prior behavior of the seeded `.env` file.
- Introduce a new `check` category (`check-ci.md`) with nine new fields: `GITPR_CHECK_BASE`, `GITPR_CHECK_FORMAT`, `GITPR_CHECK_OUTPUT`, `GITPR_CHECK_FAIL_ON`, `GITPR_CHECK_NO_IA`, `GITPR_CHECK_IA_ONLY_HIGH_RISK`, `GITPR_CHECK_BASELINE_PATH`, `GITPR_CHECK_POLICY`, and `GITPR_CHECK_TIMEOUT_SECONDS`.
- Update the CLI banner in `src/main.py` to list the `--init` and `--base` options.
- Disable the command palette in `src/ui/linter_app.py` via `ENABLE_COMMAND_PALETTE = False`.
- Refresh `tests/test_config_schema.py`: assert `DEFAULT_CONFIG` equals the seeded field set, verify the `check` category and fields are present and not seeded, and add regression tests for the banner options and command palette debt.
- Reorder and extend translation keys in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, and `pt_pt` locale files to match the new schema entries and banner text.

## ⚠️ Impact/Warnings

- **Configuration behavior:** `DEFAULT_CONFIG` is now generated from schema fields where `seeded=True`. Any future default that must be written to `.env` on first run requires setting `seeded=True`; omitting it silently drops the key from seeding.
- **Environment variables:** Nine new `GITPR_CHECK_*` configuration keys are introduced. They are intentionally **not** seeded (`seeded=False`) and default to values at runtime rather than being persisted to `~/.gitpr/.env`.
- **No database changes.**
- **Backward compatibility:** `from src.config import DEFAULT_CONFIG` continues to work via re-export from the schema.
- **UI:** The `LinterApp` command palette is disabled, which changes the discoverable keyboard shortcuts available to users of that screen.

close #265

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)