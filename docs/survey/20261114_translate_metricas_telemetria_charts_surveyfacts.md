# Survey — `docs/metricas-telemetria.*` translation drift

- **Date:** 2026-11-14
- **Branch:** `develop_natan`
- **Task:** `translate_metricas_telemetria_charts`

## Task as stated

"Translate `docs/metricas-telemetria.*`: the recent stretch gave the topic new charts, but only the
English version was updated — PT-BR, PT-PT, ES and FR fell behind."

## Fact check — the premise does not hold

| Claim | Evidence |
| --- | --- |
| Only English received the chart content | `0b3b899` (2026-11-12) added the `📈 Token Trend` and `📊 Latency` table rows and rewrote the dashboard sections bullet in **all four** translations (+4/−1 lines each) |
| Translations are structurally behind | All five files: 18 headings (1 `#`, 7 `##`, 10 `###`), 34 table rows, 24 bullets, 22 fenced code lines, 45 tree lines, 34 bold pairs, 106 inline-code spans in identical order |
| Translations add content English lacks | None; the only differences are line wrapping and one paragraph split in the dashboard's final paragraph (pt_pt L266/L268, es_es L271/L273, fr_fr L277/L279) |

EN source commit: `67a9e77` (2026-11-05). Sync commit: `0b3b899` (2026-11-12).

## The gap that actually exists

`07822f7` (2026-11-10) — "feat: add ASCII charts and tabbed navigation to dashboard":

- `src/ui/metrics_app.py` gained `TabbedContent`: `Events` (key `1`, summary bar + sections + events
  table) and `Charts & Trends` (key `2`, `latency_chart_panel` + `token_chart_panel`); bindings
  `1`, `2`, `f5`, `escape`.
- `src/ascii_chart.py` renders `render_vertical_histogram` (five latency buckets, counts and shares)
  and `render_token_timeseries` (up to 14 days, total/peak/daily average, sparkline).
- **No documentation in any language mentions tabs.** The `### Interactive Dashboard` section still
  lists summary bar, events table, sections, status bar, F5/Esc.

Secondary finding: the tab titles are localized (`__("Events")`, `__("Charts & Trends")`), but every
label inside the charts is hardcoded English in `src/ascii_chart.py:83-89,185-191` and in both
empty-state cards. Out of scope here; recorded as a follow-up.

## Drift audit — all top-level `docs/*.md`

Structural signature = (heading levels, table rows, bullets, fenced blocks), counted **outside**
fenced code blocks, English vs the four translations. Computed 2026-11-14.

| Doc | Divergence | Detail (English → translations) |
| --- | --- | --- |
| `ARCHITECTURE` | headings + structure | headings 27 → 26; bullets 77 → 69; fences 4 → 2 |
| `check-ci` | structure | fences 12 → 10 |
| `git-hooks-locais` | headings + structure | headings 10 → 10 (pt_br) / 9; fences 10 → 8 (pt_br) / 4 |
| `git-status` | structure | fences 14 → 14 (pt_br) / 8 |
| `linter-regras-customizadas` | headings + structure | headings 16 → 14 (pt_br) / 10; bullets 8 → 9 (pt_br) / 6; fences 10 → 6 / 4; table rows 9 → 0 in three languages |
| `mentor-mode` | headings + structure | headings 6 → 4; table rows 11 → 4; bullets 3 → 0 (pt_pt/es_es/fr_fr; pt_br matches) |
| `pull-request-publication` | headings + structure | headings 54 → 47; table rows 99 → 91; bullets 16 → 13; fences 58 → 46 |
| `skill-template` | structure | table rows 20 → 18 |
| `github-issue-prompt-com-gh` | no translations | English only, by design (`docs/plans/2026-08-18_architecture_multilang.md:21`) |

Every other top-level doc pair is in parity.

Correction from the first pass: counting every `|`, `-` and `#` line also counted lines *inside*
code fences, which made `plugins-system` look divergent (headings 18 vs 17, bullets 27 vs 20 in
pt_br). Fence-aware, it matches English exactly and was dropped from the exception list. The eight
entries above survive the stricter count.

## Decisions from the grilling rounds

1. **Scope:** this doc family + a drift audit; the 8 divergent docs are reported, not repaired.
2. **Edit strategy:** targeted patch — regeneration would rewrite correct prose for no gain.
3. **Chart detail:** two bullets inside the existing dashboard section, no new heading.
4. **Parity guard:** all top-level docs, heading sequence + structural counts, hardcoded exceptions.
   A heading-only check was rejected because it would not have caught `67a9e77` (a table row added
   to English alone), which is the exact failure this task was named after.
5. **Chart i18n:** follow-up, not this task.
6. **Audit output:** this file + the completion report; no new permanent docs page.

## Conventions confirmed for the implementation

- Localized docs are `<base>.<lang>.md` with `pt_br`, `pt_pt`, `es_es`, `fr_fr`
  (`.claude/memory/docs-multilingue-convencao.md:15-23`); no language banner or back-link exists.
- Headings, prose, table headers and shell comments are translated; commands, flags, env vars,
  file names and backticked identifiers are not.
- Tab labels per `langs/*.json`: pt_br/pt_pt `Eventos` / `Gráficos e Tendências`, es_es `Eventos` /
  `Gráficos y Tendencias`, fr_fr `Événements` / `Graphiques et Tendances`.
