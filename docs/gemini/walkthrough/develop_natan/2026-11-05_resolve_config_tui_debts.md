# Walkthrough: Resolving Config TUI Technical Debts

This walkthrough details the resolution of the four technical debts inherited from the Config TUI feature (`docs/reports/relatorio_estado_v0.0.22.md`).

## 1. Unified `DEFAULT_CONFIG` with Schema as SSOT

### Problem
`DEFAULT_CONFIG` was manually defined twice: once in `src/config.py` (a 90+ line dictionary) and once in `src/config_schema.py` (individual `ConfigField` instances). Any new default field had to be maintained in two places.

### Solution
- Added `seeded: bool = False` to `ConfigField` in `src/config_schema.py`.
- Marked all 58 core initial settings with `seeded=True`.
- Derived `DEFAULT_CONFIG` automatically:
  ```python
  DEFAULT_CONFIG = {field.key: field.default for field in FIELDS if field.seeded}
  ```
- In `src/config.py`, replaced the hardcoded dictionary with:
  ```python
  from src.config_schema import DEFAULT_CONFIG
  ```

---

## 2. Updated Main Banner Flags

### Problem
The opening CLI banner in `src/main.py` did not display `--init` and `--base`.

### Solution
- Updated the banner options line:
  ```python
  "  Options: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | --install | --init | -is,--issue | --no-publish | --no-edit | --base | --plugins | -h,--help (use -h --flag for contextual help)\n"
  ```
- Synchronized translation entries across all 6 locale files (`pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, `fr.json`).

---

## 3. Disabled Command Palette in `LinterApp`

### Problem
`LinterApp` in `src/ui/linter_app.py` was the only Textual app without `ENABLE_COMMAND_PALETTE = False`, allowing the command palette to pop up unexpectedly.

### Solution
- Added class attribute `ENABLE_COMMAND_PALETTE = False` to `LinterApp`.

---

## 4. Added CI Check Category & Schema for 9 `GITPR_CHECK_*` Keys

### Problem
The 9 environment variables consumed by `gitpr check` (`GITPR_CHECK_BASE`, `GITPR_CHECK_FORMAT`, `GITPR_CHECK_OUTPUT`, `GITPR_CHECK_FAIL_ON`, `GITPR_CHECK_NO_IA`, `GITPR_CHECK_IA_ONLY_HIGH_RISK`, `GITPR_CHECK_BASELINE_PATH`, `GITPR_CHECK_POLICY`, `GITPR_CHECK_TIMEOUT_SECONDS`) were missing from `src/config_schema.py` and had no category.

### Solution
- Declared the `"check"` category with documentation link `"check-ci.md"`:
  ```python
  Category("check", __("CI Check"), __("Unified pipeline checks, output formats, thresholds, and execution limits."), doc="check-ci.md")
  ```
- Added field definitions for all 9 `GITPR_CHECK_*` variables under `"check"`, with `seeded=False` so they remain optional in `.env`.
- Translated all descriptions and labels in `langs/*.json`.

---

## Verification Results

- `pytest tests/test_config_schema.py`: 52 passed.
- `pytest tests/test_i18n.py`: 22 passed.
- `pytest tests/test_config_app.py`: 92 passed.
