## Completion Report — Pull Request Badge (`gitpr badge`)

### What was done

Implemented the badge in its two halves: an automatic badge appended to the body of every pull request GitPR **publishes**, and a `gitpr badge` subcommand that prints a static snippet for a project's own README. The declared goal is distribution — every published pull request carries the product name — and the constraint that shaped the whole design is that the badge is a **public claim printed in someone else's repository**.

The spec's central premise does not exist in the code: the default `gitpr pr` flow runs **no review**, produces no severities and measures no duration — `generate_pr_content("pr", …)` returns two strings of prose ([core.py:827](../../../../src/core.py#L827)). The badge is therefore built from the only structured number that flow can actually produce offline: the static linter's alert lists over the very diff being published, via `parse_diff_and_lint(diff_text, skip_external=True)` — no network, no subprocess, and it never raises. No number is invented, and **when no linter rules are configured there is no badge at all** (Q11): the linter short-circuits to empty lists in that case, and empty lists there mean "nothing was checked", not "nothing was found" — indistinguishable from a clean diff by the return value alone. The rules are inspected first (`load_linter_rules()`), and `None` means no badge.

- **`src/branding/`** — flat package, following `src/fix/` and `src/review/`, not the `domain`/`application` layers the spec assumed (Q1). `badge_data.py` holds `BadgeCounts` + `collect_linter_counts()` (never raises: a badge is decoration and decoration never stops a pull request); `badge_builder.py` holds the markdown builders, the shields.io escaping (`-`→`--`, `_`→`__`, space→`_`, then percent-encode, so the middle dot survives as `%C2%B7` and the URL is pure ASCII), `append_badge()`, and `attach_pr_badge()`.
- **One insertion point** (Q2) — `attach_pr_badge(pr_data, diff_text)` at [main.py:1458](../../../../src/main.py#L1458), after `pr_data` is complete and before either publisher reads it. The TUI seeds the body into its `TextArea` (so the badge is **visible and deletable**, Q7) and `--no-edit` sends it in the request. The local `.md` written by `--no-publish` is composed in another branch and stays clean; MCP and review comments are untouched.
- **`append_badge` is idempotent** — it marks on `img.shields.io/badge/GitPR`, so republishing sends the user's edited body with the badge it already had, instead of stacking a second one.
- **Opt-out** — `badge_enabled()` in [config.py:330](../../../../src/config.py#L330) mirrors `coauthor_enabled()`: `false/0/no/off/n` disable, absence means enabled. Not seeded into `DEFAULT_CONFIG`, and never auto-written to `.env`.
- **`gitpr badge`** — subcommand declared with the other subcommands, so it escapes the PyPI gate and `check_internet_connection()`. `--readme` prints only the snippet (pipe-friendly), `--style` selects `flat` / `flat-square` / `for-the-badge`, an unknown style warns on stderr and falls back to `flat`. **Nothing is ever written to the user's README** — it prints.
- **Disclosure** — a line at the end of `--init` (the moment publishing becomes possible) and a line on each publishing run whose body the user never sees (`--no-edit`). Never a prompt. The badge text itself is fixed English, like the PR body it sits next to.
- **The demo shows it** (Q8) — the PR step now ends with the badge a publish would attach, counted from each scenario's **recorded** `linter` block, so the tour lints nothing and reads no rule from disk. A second intro paragraph says where the badge comes from and that it needs rules. The tour deliberately does **not** consult `badge_enabled()`: it is a recording that consults no other configuration either.
- **i18n** — 10 new keys per `langs/*.json` in all six files, inserted surgically and sorted, byte-identical round-trip (`10 insertions / 0 deletions` each, 1089 → 1090 keys); `__lang_version__` bumped `v0.0.29` → `v0.0.30`, which is the mechanism that delivers them to existing installs. `tests/sync_i18n.py` was **not** run (its regex extractor truncates implicitly-concatenated literals); parity is enforced by `tests/test_i18n.py`, which parses with AST.
- **Docs** — new `docs/badge.md` + the four language variants (117 lines each, headings at identical line numbers), the demo doc updated in five languages, and the README dogfooded in five languages: the badge under the logo, a bullet in the options list, a `## 🏷️ …` section, and a docs-index entry.
- **No new dependency** — `pyproject.toml` and `Pipfile` are untouched; shields.io renders the image in the reader's browser and GitPR only builds the URL.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/branding/__init__.py` | feat | package marker (setuptools discovery) |
| `src/branding/badge_data.py` | feat | `BadgeCounts`, `collect_linter_counts()` — `None` when there is nothing honest to report |
| `src/branding/badge_builder.py` | feat | `build_pr_badge` / `build_readme_badge` / `append_badge` / `attach_pr_badge` / `has_badge`, shields escaping |
| `src/main.py` | feat | the single insertion point; `badge` subcommand; the unseen-publish notice |
| `src/config.py` | feat | `badge_enabled()` |
| `src/config_schema.py` | feat | `GITPR_BADGE` `ConfigField` (general, `KIND_BOOL`, default `true`) |
| `src/core.py` | feat | disclosure line at the end of `run_scm_init_wizard()` |
| `src/updater.py` | chore | `__lang_version__` → `v0.0.30` |
| `langs/*.json` (6) | feat | 10 keys each, parity enforced by `tests/test_i18n.py` |
| `src/demo/demo_runner.py` | feat | `_recorded_badge()` + the badge on the PR artifact + a second intro paragraph |
| `docs/badge.md` + 4 variants | docs | new feature documentation |
| `docs/demo.md` + 4 variants | docs | step 5 row and the "See also" note |
| `README.md` + 4 variants | docs | dogfooded badge, `gitpr badge` bullet, section, docs-index entry |
| `tests/badge/` (7 files + `conftest.py`) | test | 83 new tests (the spec's seven obligatory proofs, mapped) |
| `tests/demo/test_demo_runner.py` | test | +6 tests for the badge on the PR step |
| `tests/scm/test_init_wizard.py` | test | +2 tests: disclosed on success, silent on failure |
| `docs/survey/20260919_gitpr_badge_surveyfacts.md` | docs | the grill survey behind the plan |

### Impact

- **Functionality:** published pull request bodies gain a footer (separated by `---`) with a badge built from the linter counts of that diff — red with errors, yellow with warnings only, green with `no issues`; absent without rules or with `GITPR_BADGE=false`. A new `gitpr badge` subcommand prints the README snippet. Nothing existing changed behaviour: the local `.md` of `--no-publish`, the review artefacts, the MCP tools and the review comments are untouched.
- **Performance:** one extra linter pass over a diff that is already in memory, on the two publishing paths only. No network, no subprocess (`skip_external=True`).
- **Compatibility:** additive. No flag, no output file and no environment variable of an existing command changed. `__lang_version__` moving to `v0.0.30` makes existing installs re-download their language pack, smart-excludes and thinking words once on the next run — the same step the previous features took. The demo's PR artifact changed content (the badge is part of it now), which is the point of Q8.

#### Deviations from the approved plan

1. **Nothing was committed.** The repo's rules forbid `git add`/`commit`/`push`, so the spec's §9 ("cada etapa deve ser um commit/PR isolado") cannot be honoured. Everything is in the working tree, split as one logical change per file group.
2. **The Q3 notice is per-publish, not first-publish-only.** The plan called for a one-line notice on the *first* publication, guarded by a marker. The implemented rule is the one the plan named as its fallback and made the honest one: the line appears whenever a body **the user never saw** is published (`--no-edit`), because no reliable first-run marker exists for this and no migration writes one. The TUI gets no line — there the badge is in the text area, which is the disclosure. Consequence: a scripted `--no-edit` user sees the line on every run until they set `GITPR_BADGE=false`.
3. **The badge does not appear on a fresh install.** This is the deliberate consequence of Q11, not an accident: without `.gitpr/skill/.gitpr.linter.yml` there are no rules, so there is nothing the badge may claim. The virality only switches on after the user configures the linter (`gitpr --skill`), which the docs turn into a funnel and the demo's PR step says out loud.
4. **`gitpr -h --badge` still errors** (`No such option: --badge`); the subcommand has no `HELP_MAP` entry, following the `demo` precedent and the plan's explicit scope. Its help is `gitpr badge --help`, with the localized documentation link in the epilog.
5. **Accepted linter side effects on each publishing run that carries a badge:** one JSON line appended under `~/.gitpr/metrics/` by `log_local_metric`, and one `git remote -v` to label it with the repository. Both are pre-existing behaviour of every linter call, and the metric is the price of using the real measurement instead of inventing one.
6. **Cosmetic difference between the two badges:** the dogfooded badge in the five READMEs names the URL without `?style=flat`, while `gitpr badge --readme` appends it. shields.io renders both identically; it is left as is because the README block is HTML (`<p align="center">`) matching the logo above it, not the markdown the command prints.

### Verification

```
python -m pytest tests/badge -q                    # 83 passed
python -m pytest tests/demo tests/test_i18n.py -q  # 175 passed
python -m pytest tests/scm/test_init_wizard.py -q  # 12 passed
python -m pytest tests/ -q                         # 25 failed, 1650 passed, 2 skipped, 81 subtests passed
```

The 25 failures are **pre-existing**, and this time the comparison is against the code at `HEAD`: a `git worktree add --detach` at `da162d0` ran the eight test files that contain every failure and produced the **identical `FAILED` set, name by name** — `diff` of the two sorted lists is empty, 25 against 25. The families are `test_config_app` (13), `test_suggest_reviewers` (5), `test_net_timeouts` (2), and one each in `test_chat_backend`, `test_mcp_server`, `test_reviewer_resolution`, `test_main_suggest_reviewers` and `fix/test_rollback_fix` — no file the change touches. The pass count grows by exactly the new tests: `--collect-only` reports 1586 at `HEAD` against 1677 in the working tree (**+91** = 83 in the new `tests/badge/`, 6 in `tests/demo`, 2 in `tests/scm`), and 1586 − 25 − 2 skipped = **1559**, the figure the previous report recorded at `HEAD`.

End to end, from the repository root:

| Command | Result |
| --- | --- |
| `python run.py badge --readme` | the snippet and nothing else |
| `python run.py badge --style for-the-badge --readme` | the same line with `?style=for-the-badge` |
| `python run.py badge --style nope --readme` | yellow warning on stderr, `flat` used |
| `python run.py badge` | title, snippet, and the one-line explanation of the automatic badge |

The two **publishing** paths are asserted against the real code in `tests/badge/test_badge_paths.py`: the TUI is constructed for real and its editable text area is read back (`test_the_seeded_body_carries_the_badge`, `test_the_badge_is_inside_the_editable_text_area`), and `_publish_pr_directly` runs for real against a provider that captures the request (`test_the_published_body_carries_the_badge`). The third path, `--no-publish`, needs no test: its `return` in `src/main.py` sits **above** the attachment point, and it composes and writes its `.md` from the AI payload before that — the file cannot contain a badge because the code that adds one is never reached. `tests/badge/test_badge_offline.py` arms `socket` and `urllib` to raise for the whole construction and printing of the badge — the URL is built, never fetched. `tests/badge/test_badge_data.py` pins the Q11 boundary: no rules ⇒ `None` ⇒ no badge, as does a linter that raises or rules that cannot be read.

**Untracked residue left alone:** `.gitpr/metrics/export/gitpr_metrics_2026-09-19.{csv,json}` and `.gitpr/reports/pr_desc/develop_natan_20260918215137_PR_DESC.md` are not gitignored and not part of this change. The first two are exports of verification runs; the third predates this session. They are there for you to delete or ignore deliberately.

### Next steps

- **The virality gate is the linter setup.** The single highest-leverage change for the spec's §10 goal is making `gitpr --skill` happen earlier — or offering the linter rules during `--init` — because until rules exist no badge is published at all.
- **A `first_publish` marker** in `~/.gitpr/.env`, written through the same helper as `LANG_VERSION`, would let the `--no-edit` notice thin out to once per install (deviation 2).
- **`HELP_MAP` entry** for `gitpr -h --badge`, for consistency with the other flags (deviation 4).
- **The demo's PR step** could consult `badge_enabled()` if the tour is ever expected to reflect the user's configuration; today it deliberately reflects the product's default.
- **`sync_i18n.py`** still must not be run — its regex extractor should be replaced by the AST approach `tests/test_i18n.py` already uses, so the documented verification step stops being unsafe.
