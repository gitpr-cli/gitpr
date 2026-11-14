# Plan — Document the dashboard Charts tab, translate it, guard docs parity

- **Date:** 2026-11-14
- **Branch:** `develop_natan`
- **Task:** `translate_metricas_telemetria_charts`

## Context

The requested task was "translate `docs/metricas-telemetria.*` because the new charts only reached
the English version". The repository disproves that premise:

- `0b3b899` (2026-11-12) already synced the `📈 Token Trend` / `📊 Latency` rows into all four
  translations. All five files carry 18 headings, 34 table rows, 24 bullets, 22 fenced code lines,
  and the same 106 inline-code spans in the same order.
- The real gap is the dashboard's second tab: `07822f7` (2026-11-10) added `TabbedContent`
  (`Events` / key `1`, `Charts & Trends` / key `2`) and the ASCII chart renderers, and **no
  language** documents it — English included.
- No parity guard exists for these docs; 8 docs diverge structurally and 1 has no translations
  (8, not 9: `plugins-system` looked divergent only when lines inside code fences were counted).

## Decisions (grilling rounds)

1. Document the Charts tab in English, then propagate to the four translations.
2. Bullets inside the existing `### Interactive Dashboard` section (no new `###` heading).
3. Targeted patch per file — no regeneration.
4. Parity test over all top-level `docs/*.md`: heading-level sequence **and** structural counts,
   with a hardcoded exception baseline.
5. Chart-label i18n (`src/ascii_chart.py` hardcodes English) stays out of scope, logged as follow-up.
6. Audit output goes to the completion report and to
   `docs/survey/20261114_translate_metricas_telemetria_charts_surveyfacts.md`.

## Changes

| File | Change |
| --- | --- |
| `docs/metricas-telemetria.md` | Two new bullets (`Two tabs`, `Charts tab`) + `1`/`2` in the shortcuts bullet |
| `docs/metricas-telemetria.pt_br.md` | Same, with `abas`, `Eventos`, `Gráficos e Tendências` |
| `docs/metricas-telemetria.pt_pt.md` | Same, with `separadores`, `Eventos`, `Gráficos e Tendências` |
| `docs/metricas-telemetria.es_es.md` | Same, with `pestañas`, `Eventos`, `Gráficos y Tendencias` |
| `docs/metricas-telemetria.fr_fr.md` | Same, with `onglets`, `Événements`, `Graphiques et Tendances` |
| `tests/unit/test_docs_translation_parity.py` | New parity guard (headings + rows/bullets/fences) |

## Verification

- `python -m pytest tests/unit/test_docs_translation_parity.py -v` green.
- Negative control: remove one new bullet from a translation → test fails on `metricas-telemetria`;
  restore → green.
- `python -m pytest tests/unit/test_doc_links.py tests/test_doc_links.py -v` green.
- Structural counts stay equal across the five metrics docs after the edit.

## Follow-ups

- Wrap the hardcoded labels in `src/ascii_chart.py` in `__()` and add the four `langs/*.json` keys.
- Repair the 8 structurally divergent docs, then delete their `PARITY_EXCEPTIONS` entries.
