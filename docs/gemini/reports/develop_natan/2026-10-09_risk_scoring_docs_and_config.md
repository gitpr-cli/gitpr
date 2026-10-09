## Completion Report — Local Risk Scoring Documentation & Config Integration

### What was done
- **Created dedicated technical documentation** in 5 languages for Local Risk Scoring (`gitpr risk`):
  - English: `docs/risk-scoring.md`
  - Portuguese (Brazil): `docs/risk-scoring.pt_br.md`
  - Portuguese (Portugal): `docs/risk-scoring.pt_pt.md`
  - Spanish: `docs/risk-scoring.es_es.md`
  - French: `docs/risk-scoring.fr_fr.md`
- **Updated all 5 README documentation surfaces**:
  - `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, and `README.fr_fr.md`
  - Added `gitpr risk` to the advanced options and commands quick-reference list.
  - Added a dedicated feature section covering signal weights, risk thresholds, badges (`LOW 🟢`, `MEDIUM 🟡`, `HIGH 🟠`, `CRITICAL 🔴`), aggregation formula (50/30/20), and review integration.
  - Added documentation links under Core Features.
- **Config TUI Integration**:
  - Registered `GITPR_RISK_INCLUDE_IN_REVIEW` under the `review` category in `src/config_schema.py` (`KIND_BOOL`, default `true`, label `__("Include Risk Assessment")`, with localized helper descriptions).
- **i18n Translation Sync**:
  - Synchronized and verified translations for the new config schema setting across `pt_br.json`, `pt_pt.json`, `es_es.json`, `es.json`, `fr_fr.json`, and `fr.json`.
- **Validation**:
  - Executed full test suite covering `tests/test_i18n.py`, `tests/test_config_schema.py`, `tests/test_config_app.py`, `tests/test_config_cli.py`, `tests/domain/risk/`, and `tests/test_risk_cli.py` (163 tests passed, 0 failures).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `docs/risk-scoring.md` | feat/docs | English technical specification and documentation for `gitpr risk` |
| `docs/risk-scoring.pt_br.md` | feat/docs | Brazilian Portuguese technical documentation for `gitpr risk` |
| `docs/risk-scoring.pt_pt.md` | feat/docs | European Portuguese technical documentation for `gitpr risk` |
| `docs/risk-scoring.es_es.md` | feat/docs | Spanish technical documentation for `gitpr risk` |
| `docs/risk-scoring.fr_fr.md` | feat/docs | French technical documentation for `gitpr risk` |
| `README.md` | docs | Added `gitpr risk` to command list, dedicated section, and docs index |
| `README.pt_br.md` | docs | Added `gitpr risk` to command list, dedicated section, and docs index |
| `README.pt_pt.md` | docs | Added `gitpr risk` to command list, dedicated section, and docs index |
| `README.es_es.md` | docs | Added `gitpr risk` to command list, dedicated section, and docs index |
| `README.fr_fr.md` | docs | Added `gitpr risk` to command list, dedicated section, and docs index |
| `src/config_schema.py` | feat | Added `GITPR_RISK_INCLUDE_IN_REVIEW` boolean field to `review` settings |
| `langs/pt_br.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |
| `langs/pt_pt.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |
| `langs/es_es.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |
| `langs/es.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |
| `langs/fr_fr.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |
| `langs/fr.json` | i18n | Localized strings for `GITPR_RISK_INCLUDE_IN_REVIEW` |

### Impact
- **Functionality:** Users can now configure whether Risk Assessment is included in reviews via the interactive `gitpr config` screen or `.env`. The documentation fully covers all aspects of deterministic local risk calculation.
- **Performance:** Zero overhead; config schema loads lazily and doc changes add no runtime penalty.
- **Compatibility:** 100% backward compatible. Defaults to `true` (current behavior), non-breaking.

### Next steps (if applicable)
- Ready for user review and commit.

