# Implementation Plan — Add Token Cost Rates and Currency to GitPR Config

## Context & Objectives
In `gitpr metrics dashboard`, telemetry displays token costs. However, when using standard Gemini models (`gemini-pro-latest` / `gemini-flash-lite-latest`), users saw a notice:
`As taxas vêm de GITPR_METRICS_PRICE_<MODEL>_INPUT / _OUTPUT em ~/.gitpr/.env.`
because no pricing rates were configured for those models in `src/config.py::DEFAULT_MODEL_PRICES`, and `gitpr config` did not expose the token rate configuration variables in its TUI.

This plan integrates token pricing configurations (`GITPR_METRICS_PRICE_<MODEL>_INPUT` and `_OUTPUT`) and currency configuration (`GITPR_METRICS_CURRENCY`) directly into `gitpr config` dynamically gated by `DEFAULT_AI_PROVIDER`.

## Architecture & Proposed Changes

### 1. `src/config.py`
- Add `"gemini-pro-latest": (1.25, 10.00)` and `"gemini-flash-lite-latest": (0.10, 0.40)` to `DEFAULT_MODEL_PRICES`.

### 2. `src/config_schema.py`
- Define `KIND_FLOAT = "float"` and add to `KINDS`.
- Update `validate_field_value` to support `KIND_FLOAT`:
  - Validate that non-empty values parse to `float` and are `>= 0.0`.
  - Return localized error `__("Use a number greater than or equal to zero.")` if invalid.
- Add new `ConfigField` declarations in `FIELDS` within category `"ai"`:
  - `GITPR_METRICS_CURRENCY`:
    - kind: `KIND_STR`
    - default: `"USD"`
    - seeded: `True`
  - For Gemini (`show_if=(("DEFAULT_AI_PROVIDER", ("gemini",)),)`):
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_INPUT` (`KIND_FLOAT`, default `"1.25"`, seeded `True`)
    - `GITPR_METRICS_PRICE_GEMINI_PRO_LATEST_OUTPUT` (`KIND_FLOAT`, default `"10.00"`, seeded `True`)
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_INPUT` (`KIND_FLOAT`, default `"0.10"`, seeded `True`)
    - `GITPR_METRICS_PRICE_GEMINI_FLASH_LITE_LATEST_OUTPUT` (`KIND_FLOAT`, default `"0.40"`, seeded `True`)
  - For DeepSeek (`show_if=(("DEFAULT_AI_PROVIDER", ("deepseek",)),)`):
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT` (`KIND_FLOAT`, default `"0.435"`, seeded `True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT` (`KIND_FLOAT`, default `"0.87"`, seeded `True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_INPUT` (`KIND_FLOAT`, default `"0.14"`, seeded `True`)
    - `GITPR_METRICS_PRICE_DEEPSEEK_V4_FLASH_OUTPUT` (`KIND_FLOAT`, default `"0.28"`, seeded `True`)

### 3. `src/ui/config_app.py`
- Import `KIND_FLOAT` from `src.config_schema`.
- Ensure `KIND_FLOAT` maps to `Input` control in `FieldRow._build_control()`.

### 4. `langs/*.json`
- Add localized translations across `pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, `fr.json`.

### 5. Automated Tests
- In `tests/test_config_schema.py`:
  - Test `KIND_FLOAT` validation for valid decimals, zero, negative numbers, and invalid strings.
  - Verify schema seeding and consistency across all new fields.
- In `tests/test_i18n.py`:
  - Verify that all static keys in `__("...")` are present in all language dictionaries.
- In `tests/test_metrics.py`:
  - Verify that `cost_report` correctly calculates Gemini token rates with the updated default prices.

## Verification Plan
- Run `pytest tests/test_config_schema.py`
- Run `pytest tests/test_metrics.py`
- Run `pytest tests/test_i18n.py`
