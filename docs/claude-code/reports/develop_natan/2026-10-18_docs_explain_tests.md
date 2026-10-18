## Completion Report — Documentation topics for `explain` and `tests generate`

### What was done
- Documented the two remaining undocumented features in five languages each: `docs/explain-pr.md` and `docs/tests-generate.md` plus `.pt_br`, `.pt_pt`, `.es_es`, `.fr_fr` translations (10 files).
- Fixed four runtime defects that would have made the documentation untruthful:
  - `parse_explain_payload()` crashed on the provider's parsed dict (`json.loads(dict)` → `TypeError`, then `.strip()` → `AttributeError`); it now accepts `dict | str | None` and normalizes `None` fields.
  - `generate_test_file` had the same dict/string mismatch; it now accepts the parsed dict (with a raw-JSON-string fallback for cached/legacy payloads).
  - `gitpr tests generate --finding` read `cand.finding.suggested_test` and `cand.diff`, attributes that do not exist; the prompt now uses `cand.suggested_test` and `cand.diff_unified`.
  - `gitpr -h --explain` was broken by a dest-name mismatch (`explain_flag` vs the `HELP_MAP` key `explain`); the option now uses the `explain` dest.
- Added the missing no-API-key branch to `generate_pr_explanation`: the standalone command now prints the standard key error and exits 1 instead of crashing.
- Wired documentation entry points: `HELP_MAP["explain"]` URL, `HELP_PRIORITY["explain"]`, the `gitpr explain` epilog, and new epilogs for `gitpr tests` and `gitpr tests generate`.
- Updated all five READMEs: `gitpr explain` and `--explain` now link to `explain-pr.<lang>.md`; `gitpr tests generate` gained a docs link.
- Updated test mocks to the real dict contract and added regressions for dict parsing, raw-string compatibility, no-key behavior, `--finding`, contextual help, and docs-link epilogs.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| docs/explain-pr.md | docs | English canonical Reviewer Guide documentation |
| docs/explain-pr.pt_br.md / .pt_pt.md / .es_es.md / .fr_fr.md | docs | Full translations with localized related-doc links |
| docs/tests-generate.md | docs | English canonical test generation documentation |
| docs/tests-generate.pt_br.md / .pt_pt.md / .es_es.md / .fr_fr.md | docs | Full translations with localized related-doc links |
| README.md + 4 translations | docs | Docs links for `gitpr explain`, `--explain`, `gitpr tests generate` |
| src/domain/pr/explain_section_builder.py | fix | Accept dict/None payloads; normalize non-string fields |
| src/application/use_cases/generate_pr_explanation.py | fix | No-API-key branch returns an empty explanation with the standard error |
| src/application/use_cases/generate_test_file.py | fix | Accept the provider dict; keep raw-string compatibility |
| src/main.py | fix | Docs URLs/epilogs, HELP_PRIORITY, `explain` dest, `--finding` attributes |
| tests/test_explain_command.py | test | Dict mocks; no-key and contextual-help regressions |
| tests/test_tests_command.py | test | Dict mocks; `--finding` and docs-link epilog regressions |
| tests/domain/pr/test_explain_section_builder.py | test | Dict-payload and None-normalization regressions |
| tests/application/use_cases/test_generate_pr_explanation.py | test | Dict mock; no-key regression |
| tests/application/use_cases/test_generate_test_file.py | test | Dict mocks; raw-JSON-string regression |
| docs/plans/develop_natan/20261018_docs_explain_tests_plansfacts.md | docs | Grilling plan |
| docs/survey/20261018_docs_explain_tests_surveyfacts.md | docs | Grilling survey |

### Impact
- **Functionality:** `gitpr explain`, `--explain`, and `gitpr tests generate` now work against the real AI provider contract; `--finding` resolves its prompt fields; `gitpr -h --explain` renders again. Both features now have complete, linked documentation.
- **Performance:** no change.
- **Compatibility:** no public CLI break. `parse_explain_payload` is more permissive; test mocks that returned JSON strings still pass because the string path is preserved. No prompt-cache or skill-template changes.

### Verification
- `python -m pytest tests/test_explain_command.py tests/test_tests_command.py tests/domain/pr/test_explain_section_builder.py tests/application/use_cases/test_generate_pr_explanation.py tests/application/use_cases/test_generate_test_file.py -v` → 22 passed.
- `python -m pytest tests/test_skill_context.py tests/test_config_schema.py -q` → 62 passed.
- All 10 documentation files verified present; every README link verified to point at the language-specific file.

### Next steps (if applicable)
- Run the full suite before release; only the targeted suites were executed for this task.
- The chat `/tests` engine remains separate from `gitpr tests generate`; unifying them is out of scope and documented as a limitation.
