## Completion Report — Document the dashboard Charts tab, translate it, guard docs parity

### What was done

The task arrived as "translate `docs/metricas-telemetria.*` — the new charts only reached the English
version". The repository disproved that premise, and the work was retargeted at the gap that
actually exists.

- **Premise check.** `0b3b899` (2026-11-12) already synced the `📈 Token Trend` / `📊 Latency` rows
  into all four translations (+4/−1 lines each). All five files were in full parity: 18 headings,
  34 table rows, 22 fenced code lines, and the same 106 inline-code spans in the same order.
- **The real gap.** `07822f7` (2026-11-10) added a second dashboard tab — `Events` (key `1`) and
  `Charts & Trends` (key `2`) — plus `src/ascii_chart.py` rendering a vertical latency histogram and
  a daily token time series. No language documented it, English included.
- **Documented it in English**, then carried the same two bullets and the extended shortcuts bullet
  into `pt_br`, `pt_pt`, `es_es` and `fr_fr`, quoting the tab names the TUI actually renders
  (`langs/*.json`): `Eventos` / `Gráficos e Tendências`, `Eventos` / `Gráficos y Tendencias`,
  `Événements` / `Graphiques et Tendances`.
- **Added the parity guard** the repo lacked: every top-level `docs/*.md` must have four non-empty
  translations and share the English structural signature (heading levels, table rows, bullets,
  fenced blocks), with a documented baseline of known divergences.
- **Audited every doc pair.** 8 docs diverge structurally; 1 has no translations by design.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `docs/metricas-telemetria.md` | docs | `Two tabs` and `Charts tab` bullets; `1` / `2` added to the shortcuts bullet |
| `docs/metricas-telemetria.pt_br.md` | docs | Same, with `Duas abas`, `Aba de gráficos` |
| `docs/metricas-telemetria.pt_pt.md` | docs | Same, with `Dois separadores`, `Separador de gráficos` |
| `docs/metricas-telemetria.es_es.md` | docs | Same, with `Dos pestañas`, `Pestaña de gráficos` |
| `docs/metricas-telemetria.fr_fr.md` | docs | Same, with `Deux onglets`, `Onglet graphiques` |
| `tests/unit/test_docs_translation_parity.py` | test | New guard: language coverage, structural parity, and an anti-staleness check on the exception baseline |
| `docs/plans/develop_natan/20261114_translate_metricas_telemetria_charts_plansfacts.md` | docs | Session plan |
| `docs/survey/20261114_translate_metricas_telemetria_charts_surveyfacts.md` | docs | Survey, decisions and the drift audit |

### Drift audit — all top-level `docs/*.md`

Signature counted **outside** fenced code blocks; English → translations.

| Doc | Divergence |
|-----|------------|
| `ARCHITECTURE` | headings 27 → 26; bullets 77 → 69; fences 4 → 2 |
| `check-ci` | fences 12 → 10 |
| `git-hooks-locais` | headings 10 → 10 (pt_br) / 9; fences 10 → 8 (pt_br) / 4 |
| `git-status` | fences 14 → 14 (pt_br) / 8 |
| `linter-regras-customizadas` | headings 16 → 14 (pt_br) / 10; bullets 8 → 9 (pt_br) / 6; fences 10 → 6 / 4; table rows 9 → 0 in three languages |
| `mentor-mode` | headings 6 → 4; table rows 11 → 4; bullets 3 → 0 (pt_pt/es_es/fr_fr; pt_br matches) |
| `pull-request-publication` | headings 54 → 47; table rows 99 → 91; bullets 16 → 13; fences 58 → 46 |
| `skill-template` | table rows 20 → 18 |
| `github-issue-prompt-com-gh` | no translations, English-only by design |

Every other top-level doc pair is in parity, `metricas-telemetria` included.

### Verification

- `python -m pytest tests/unit/test_docs_translation_parity.py -v` → 3 passed.
- Negative control: removing the new `Aba de gráficos` bullet from `pt_br` failed the guard
  (`bullets 26 vs 27`); restoring it returned green. The check catches exactly the drift this task
  was named after.
- Structural equality of the five metrics docs after the edit: 18 headings, 34 table rows,
  26 bullets, 22 fenced lines in every file.
- `python -m pytest tests/test_doc_links.py -q` → 11 passed.

### Impact

- **Functionality:** none in code. The dashboard has documented tabs, keys and charts for the first
  time.
- **Performance:** none — the new test reads 256 short markdown files and runs in ~0.2 s.
- **Compatibility:** no API or doc-link changes; translation filenames, anchors and cross-links
  are untouched.

### Deviations from the approved plan

- The plan predicted 27 bullets per metrics doc; the actual count is 26 — two bullets were added and
  the shortcuts bullet was edited in place.
- The plan listed 9 drifted docs; the accurate fence-aware count is 8. `plugins-system` appeared
  divergent only because lines inside its code fences were counted as headings and bullets.
  The test's `_PARITY_EXCEPTIONS` carries the corrected eight, and
  `test_parity_exceptions_are_still_real` now fails if an entry stops diverging, so the baseline
  cannot rot silently.

### Next steps

- `src/ascii_chart.py` hardcodes its labels in English — `Latency Histogram`, `Timed runs`,
  `Average`, `Median (P50)`, `P95`, `Total`, `Peak`, `Daily Avg`, `Sparkline`, and both empty-state
  cards — while the tab titles are localized. Wrap them in `__()` and add the four `langs/*.json`
  keys.
- Repair the eight structurally divergent docs, then delete their `_PARITY_EXCEPTIONS` entries; the
  anti-staleness test will demand the deletion.
