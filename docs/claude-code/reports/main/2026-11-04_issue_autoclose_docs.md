## Completion Report — Automatic Issue Closure Documentation

### What was done

- Verified that the `--close-issue` / `--no-close-issue` feature had **no
  standalone technical document**: it existed only as §5.3 of
  `docs/issue-tui-help.*`, one row of `docs/config-tui.*`, two mentions in
  `docs/metricas-telemetria.*`, one README bullet, the CHANGELOG and the
  `CONTEXT.md` terms.
- Created `docs/issue-autoclose.md` plus its four translations
  (`.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) — 259 lines each, the
  same 16 headings in the same order and 7 tables, following the house
  pattern of `docs/policy-packs.md`, `docs/baseline-suppressions.md` and
  `docs/risk-scoring.md`.
- Added a cross-link paragraph to §5.3 of the five `docs/issue-tui-help.*`
  files, pointing at the new document.
- Added an H2 section (`## 🔗 … (--close-issue)`) to the five READMEs,
  between the badge section and the multi-model section, with a 4-row
  flag/setting table, a limits paragraph and the `📖 documentation` link
  (`?lang=` in the translations).
- Added the feature to the `### Core Features` index of the five READMEs,
  right after the Issues entry.
- Retargeted the existing `--close-issue`/`--no-close-issue` bullet in the
  five READMEs from `docs/issue-tui-help` to `docs/issue-autoclose`.
- Repointed `close_issue` and `no_close_issue` in `HELP_MAP` to
  `issue-autoclose.md` and updated the contextual-help test accordingly.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `docs/issue-autoclose.md` | docs | New EN technical document (10 sections, 2 subsections) |
| `docs/issue-autoclose.pt_br.md` | docs | PT-BR translation, identical structure |
| `docs/issue-autoclose.pt_pt.md` | docs | PT-PT translation ("registo", "ficheiro", "utilizador") |
| `docs/issue-autoclose.es_es.md` | docs | ES-ES translation ("registro", "archivo") |
| `docs/issue-autoclose.fr_fr.md` | docs | FR-FR translation ("enregistrement", "dépôt") |
| `docs/issue-tui-help.md` (+4) | docs | One cross-link paragraph at the end of §5.3 |
| `README.md` (+4) | docs | New H2, index entry, bullet retarget — CRLF preserved |
| `src/main.py` | refactor | `HELP_MAP` URLs for `close_issue` and `no_close_issue` |
| `tests/test_cli_help.py` | test | Contextual-help assertion now expects `docs/issue-autoclose` |
| `docs/plans/main/20261104_issue_autoclose_docs_plansfacts.md` | docs | Session plan |
| `docs/survey/20261104_issue_autoclose_docs_surveyfacts.md` | docs | Session survey and fact report |

### Impact

- **Functionality:** none in the CLI behaviour. `gitpr -h --close-issue` and
  `gitpr -h --no-close-issue` now print links to `docs/issue-autoclose`
  instead of `docs/issue-tui-help` — the behavior they describe is unchanged.
- **Performance:** none.
- **Compatibility:** no API or configuration change; no migration needed. The
  READMEs keep their original CRLF line endings (verified after the edit).

### Verification

| Check | Result |
|---|---|
| `python -m pytest tests/test_cli_help.py -q` | 9 passed |
| `python -m pytest tests/issue_autoclose tests/test_config_issue_autoclose.py -q` | 130 passed, 86 subtests |
| Full suite with the known hanging integration test deselected | 3273 passed, 2 skipped, 1 deselected, 227 subtests (12m13s), no failures |
| `doc_url('issue-autoclose.md')` | `https://gitpr.natanfiuza.dev.br/docs/issue-autoclose?lang=pt_br` |
| Doc parity across the 5 files | identical heading sequence (16), 7 tables, 259 lines each |
| Cross-link in `issue-tui-help.*` | exactly 1 line per file |
| READMEs | one `^## 🔗` per file, slug present in H2, index and bullet, all lines CRLF |
| README local slug resolution | only the pre-existing `i18n` and `understanding` slugs have no local file |

### Next steps

- Publish the docs site with the new `issue-autoclose` topic so the README and
  `HELP_MAP` links resolve.
- `docs/ARCHITECTURE.*` still carries an outdated feature catalogue, and the
  translated READMEs still miss the `gitpr mentor` bullet — both were left out
  of scope for this task.

### Suggested commit

```
docs: add standalone issue autoclose documentation
```
