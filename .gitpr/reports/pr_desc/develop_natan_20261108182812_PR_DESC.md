# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add configurable model pricing and currency settings
```

---

## 🎯 Summary

Cost reporting relied on a fixed, built-in price table, so operators had no way to align telemetry costs with their actual provider contracts or to report in a currency other than USD. This change introduces a first-class `float` config field type and exposes per-model input/output pricing (Gemini and DeepSeek, advanced and fast models) plus a metrics currency setting, while extending the built-in price table with the `gemini-pro-latest` and `gemini-flash-lite-latest` aliases so those models are no longer reported as unpriced.

## 🛠️ Technical Changes

- Add `KIND_FLOAT` to the config schema kinds and wire it into `src/ui/config_app.py`, with validation that accepts empty values and rejects negative or non-numeric input ("Use a number greater than or equal to zero.").
- Add `GITPR_METRICS_CURRENCY` config field (string, category `ai`) to control the currency code used in telemetry and cost reports, defaulting to USD.
- Add per-model price fields (`*_INPUT` / `*_OUTPUT`) for Gemini Pro latest, Gemini Flash Lite latest, DeepSeek V4 Pro and DeepSeek V4 Flash, shown only when the corresponding `DEFAULT_AI_PROVIDER` is selected.
- Extend `DEFAULT_MODEL_PRICES` with `gemini-pro-latest` (1.25 / 10.00) and `gemini-flash-lite-latest` (0.10 / 0.40) so built-in aliases resolve to list prices.
- Add unit tests covering float validation (valid, empty, negative, malformed) and asserting built-in pricing for the new Gemini aliases with an empty `unpriced` list.
- Update `es`, `es_es`, `fr`, `fr_fr`, `pt_br` and `pt_pt` translation catalogs with the new labels, descriptions and validation message.

## ⚠️ Impact/Warnings

- **Environment variables:** new optional keys `GITPR_METRICS_CURRENCY` and `GITPR_METRICS_PRICE_{GEMINI_PRO_LATEST,GEMINI_FLASH_LITE_LATEST,DEEPSEEK_V4_PRO,DEEPSEEK_V4_FLASH}_{INPUT,OUTPUT}`. All default to empty, so existing behavior is preserved unless set.
- **Cost figures:** configuring a price for a model overrides the built-in rate; report values will change wherever overrides are applied.
- **Database:** no schema or migration changes.
- **Dependencies:** none added.

close #294

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)