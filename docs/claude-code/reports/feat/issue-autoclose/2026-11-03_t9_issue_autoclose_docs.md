## Completion Report — T9: Documentation for issue autoclose

### What was done

- **Contextual CLI help.** Added two `HELP_MAP` entries in
  `src/main.py` (`close_issue`, `no_close_issue`) so `gitpr -h --close-issue`
  and `gitpr -h --no-close-issue` print the behavior, the forge check and what
  the opt-out skips, with a link to the Issue TUI documentation.
- **i18n.** Four new English keys for those titles/descriptions, translated in
  all six `langs/*.json` files (1694 → 1698 keys per file, parity preserved,
  `es.json`/`fr.json` mirrored from `es_es`/`fr_fr`).
- **README ×5.** One bullet before the PR Publisher bullet describing the
  automatic issue closure, both flags, `GITPR_ISSUE_AUTOCLOSE`,
  `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`, the record at `.gitpr/conf/github.yml`
  (auto-added to `.gitignore`) and a language-aware docs link.
- **`docs/issue-tui-help.md` ×5.** New subsection **5.3 "Automatic Issue
  Closure with the Pull Request"**: where the record lives, what the question
  does, the exact `close #N` insertion rule, a flag/configuration table and the
  four operational notes (GitHub only, no question without a terminal, the
  record survives a failed publish, and it self-cleans). A Related Files row for
  `.gitpr/conf/github.yml` was added in each language.
- **CHANGELOG.** `## [Unreleased]` section with the feature bullet.
- **Metrics docs ×5.** `issue_autoclose` added to the `command` examples and a
  paragraph stating that its rows carry `asked`, `accepted` and
  `skipped_reason` in the row payload — visible in the JSON export, absent from
  the CSV columns.
- **Config TUI docs ×5.** The Issue category row now lists the three fields it
  holds (`OUTPUT_FILE_NAME_ISSUE`, `GITPR_ISSUE_AUTOCLOSE`,
  `GITPR_ISSUE_AUTOCLOSE_TIMEOUT`) and `FIELDS` went from 83 to 85. The
  "thirteen categories" sentence was left unchanged — the schema grew inside
  existing categories, so the category count is still 13.
- **Regression test.** `tests/test_cli_help.py::test_contextual_help_flag_close_issue`
  pins the new help entry (`-h --close-issue` exits 0, shows the title and the
  docs URL).

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/main.py` | docs | `HELP_MAP` entries for `close_issue` and `no_close_issue` |
| `langs/{pt_br,pt_pt,es,es_es,fr,fr_fr}.json` | docs | 4 new keys each (1694 → 1698) |
| `README.md`, `README.pt_br.md`, `README.pt_pt.md`, `README.es_es.md`, `README.fr_fr.md` | docs | Feature bullet with flags, env vars, record file and docs link |
| `docs/issue-tui-help.md` + 4 translations | docs | New §5.3 and `.gitpr/conf/github.yml` in Related Files |
| `docs/metricas-telemetria.md` + 4 translations | docs | `issue_autoclose` command example + payload-fields paragraph |
| `docs/config-tui.md` + 4 translations | docs | Issue category row and 83 → 85 fields |
| `CHANGELOG.md` | docs | `## [Unreleased]` note |
| `tests/test_cli_help.py` | test | Contextual help test for `--close-issue` |

29 files changed, 197 insertions, 15 deletions.

### Impact

- **Functionality:** No behavior change. The only runtime touch is the two
  `HELP_MAP` entries — `gitpr -h --close-issue` / `-h --no-close-issue` now
  answer with feature-specific help instead of falling back to the root help.
- **Performance:** None.
- **Compatibility:** None. No flag, env var or config field was added or
  renamed in this task; the documentation describes what T1–T8 shipped.

### Verification

| Command | Result |
|---------|--------|
| `python -m pytest tests/test_cli_help.py tests/test_i18n.py -q` | **31 passed** (9 help + 22 i18n audit) |
| `python -m pytest tests/issue_autoclose tests/test_metrics.py -q` | **284 passed, 56 subtests passed** |
| Broad suite (same recipe as T1–T8) | **3163 passed, 8 failed, 2 skipped, 1 deselected, 227 subtests passed** in 342.88 s |

The 8 failures are all in `tests/test_plugins.py` and are the known
pre-existing leak (`load_dotenv(ENV_FILE, override=True)` injects
`GITPR_LINTER_SECURITY='true'` only in broad runs; the file passes 17/17 in
isolation). No new failure.

`git status` shows only the 29 files above (plus this untracked report) —
`langs/` carries exactly the four new keys per file, no file under
`~/.gitpr/metrics/` and no behavior file in `src/` besides `HELP_MAP`.

### Next steps

- **T9 is the last task of the SPEC.** With it merged, the issue-autoclose
  feature is complete: record → decision → closing line → PR wiring → config →
  metric → docs.
- Optional follow-ups left out of scope: a metrics funnel for the helper's
  short-circuits (`no-record`, `flag-disabled`, `disabled`) and a documented
  pointer to `docs/metricas-telemetria*.md` from §5.3.

### Suggested commit

```
docs: document issue autoclose
```
