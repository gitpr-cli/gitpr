## Completion Report — Add Token Pricing Rates and Currency to GitPR Config

### What was done
- Identified that `DEFAULT_MODEL_PRICES` lacked entries for Gemini default aliases (`gemini-pro-latest` and `gemini-flash-lite-latest`), causing telemetry dashboard to report that rates were missing.
- Added default list prices for `"gemini-pro-latest": (1.25, 10.00)` and `"gemini-flash-lite-latest": (0.10, 0.40)` in `src/config.py::DEFAULT_MODEL_PRICES`.
- Introduced `KIND_FLOAT = "float"` into `src/config_schema.py` (`KINDS`) and added validation logic for non-negative floating-point values in `validate_field_value`.
- Declared `GITPR_METRICS_CURRENCY` in category `"ai"` of `src/config_schema.py`.
- Declared input and output token pricing configuration fields for Gemini and DeepSeek models under category `"ai"`, conditionally visible via `show_if=(("DEFAULT_AI_PROVIDER", ("<provider>",)),)`.
- Updated `src/ui/config_app.py` to import and support `KIND_FLOAT`.
- Added localized strings to all six language dictionaries: `langs/pt_br.json`, `langs/pt_pt.json`, `langs/es_es.json`, `langs/es.json`, `langs/fr_fr.json`, and `langs/fr.json`.
- Added unit tests for `KIND_FLOAT` validation in `tests/test_config_schema.py`.
- Added unit test in `tests/test_metrics.py` verifying built-in list prices for Gemini model aliases.
- Verified all tests in `test_config_schema.py`, `test_i18n.py`, and `test_metrics.py`.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/config.py` | feat | Added built-in list prices for `gemini-pro-latest` and `gemini-flash-lite-latest`. |
| `src/config_schema.py` | feat | Added `KIND_FLOAT`, validation for floats $\ge 0$, `GITPR_METRICS_CURRENCY`, and provider-gated `GITPR_METRICS_PRICE_*` fields. |
| `src/ui/config_app.py` | feat | Imported `KIND_FLOAT` for TUI configuration row rendering. |
| `CONTEXT.md` | docs | Documented domain terms `Token price rate` and `Metrics currency`. |
| `langs/*.json` | feat | Localized translations for labels and descriptions in PT-BR, PT-PT, ES, and FR. |
| `tests/test_config_schema.py` | test | Added unit tests for float validation and verified schema integrity. |
| `tests/test_metrics.py` | test | Added unit test verifying Gemini model pricing resolution. |

### Impact
- **Functionality:** Users can now view and customize token pricing rates (`GITPR_METRICS_PRICE_<MODEL>_INPUT / _OUTPUT`) and telemetry currency (`GITPR_METRICS_CURRENCY`) directly in the `gitpr config` TUI under the selected AI provider. Gemini models now calculate costs automatically on fresh installs without displaying missing rate warnings.
- **Performance:** Zero overhead; schema validation is performed offline during user interaction.
- **Compatibility:** Backward compatible. Existing configurations without custom overrides fall back gracefully to vendor list prices.

### Next steps (if applicable)
- None. All requirements and regression tests are passing.
