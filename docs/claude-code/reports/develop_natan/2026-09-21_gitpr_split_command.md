## Completion Report — Split Command (`gitpr split`)

### What was done

Implemented `gitpr split`: it reads a working tree holding several unrelated concerns, groups the hunks by logical intent with AI, and proposes — or creates — one atomic commit per concern, each with a message generated for that subset of the changes alone. The constraint that shaped the whole design is that the command **never writes to the working tree**: the files on disk at the end are byte-identical to the files on disk at the start. Reading is the default and writing is opt-in (`--apply`).

Three of the spec's own premises did not survive contact with the code, and the grilling session corrected them before implementation began:

- **§0.1 assumed a hunk parser existed to reuse.** It does not. Map-reduce splits at *file* granularity (`re.split(r"(^diff --git a/)", …)`) and `_HUNK_HEADER_RE` in `diff_parser.py` captures only the new-side start/count and is load-bearing for `summarize_patch`, so it cannot be widened. `hunk_parser.py` is new code.
- **§5 asked to confirm whether selective staging already existed.** It did not: `--cached`, `update-index`, `add -p` and `git reset` appear nowhere in `src/` before this feature. Only file-level `git add` did.
- **The settled "clean index precondition" was wrong, and was reversed.** Refusing a dirty index (or unstaging before reading) destroys the plan: a staged new file or rename appears in `git diff HEAD` *because the index tracks it*, so unstaging first turns it into an untracked file — out of scope — and silently drops work the user had. The order is therefore fixed as **capture first, unstage last**.

- **Own diff capture, not `get_git_diff()`** — `SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")` and `get_split_diff()` in `core.py`. The difference is `-w`, which every other flow passes and split must not: with `-w` a whitespace-only difference is rendered as *context*, the emitted context line need not match the file byte for byte, and the patch built from it is either refused by `git apply` or applies content that differs from the working tree. The first is a loud failure; the second breaks the byte-identical guarantee in silence. `-U1` leaves too little to anchor on, `-B` decomposes one applicable hunk into two that must move in lockstep, and `-M` is **kept** because without rename detection a rename becomes a deletion plus an untracked addition, which reads as data loss.
- **No smart excludes** — excluding a lockfile while committing its manifest produces an intermediate commit in which the two disagree, which is exactly the defect the command exists to prevent. Noise is bounded by per-unit truncation and `GITPR_SPLIT_MAX_HUNKS` instead.
- **`src/split/`** — six modules, flat, following `src/fix/` and `src/review/`. `split_plan.py` is the data contract with no I/O; `hunk_parser.py` is pure text↔model and never runs git; `hunk_grouper.py` owns the prompt, the budget and the response validation; `generate_split_plan.py` is the read-only use case; `apply_split_plan.py` is the only module that mutates git.
- **Hunk boundaries decided by counting** — a hunk ends when the counts in its header are exhausted, never at the next `@@`. Inside a hunk, `--- something` and `+++ something` at column 0 are indistinguishable from a file-header pair, while a context line always carries its leading space. Counting doubles as the malformed-input validator: a section whose counts do not reconcile degrades **whole** to one `OpaqueSection`, never to a partial hunk list.
- **Unit identity** — `0007-1a2b3c4d`: traversal position plus the first eight hex digits of an MD5 over path, header and body. Both halves are load-bearing; the hash is what separates two files changed identically (a vendored copy and its original) that differ only in path.
- **One AI grouping call, no batching** — hunks of one concern straddling a batch boundary can never be reunited, because neither batch sees the other's hunks, and the model then answers confidently about the half it can see. Every id the model returns is validated against the real units: unknown ids discarded with a warning, duplicates kept once, unmentioned units forced into `ungrouped_units`. No invented unit enters a group; no real unit is silently dropped.
- **Conflict pre-validation at plan time** — each group runs through `git apply --cached --check` against a temporary `GIT_INDEX_FILE`, so building a plan touches nothing. A refused group absorbs every unit of every file it touches, and its message is **regenerated** for the merged patch. The loop is bounded and has a terminal fallback: a CRLF file or a binary unit that still fails goes to `ungrouped_units` with a warning.
- **`src/infrastructure/git/`** — `patch_applier.py` moved verbatim plus `check_patch_cached()` / `apply_patch_cached()`, alongside `selective_stager.py`. `src/fix/patch_applier.py` is now a re-export shim. `selective_stager` imports `_apply` rather than re-implementing it, so selective staging inherits the byte-stdin CRLF defence — the project's most important Windows protection.
- **No skill template** — `get_skill_context()` answers an unregistered type with the *review* skill (`DEFAULT_SKILL_TYPE = "review"`), so `.gitpr.split.md` would hand the grouping prompt a code-review persona. The instruction is embedded in `hunk_grouper.py` instead.
- **`__lang_version__` → `v0.0.31`** — see deviation 3; without this the 50 new keys never reach an existing install.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/split/split_plan.py` | feat | `SplitError`, `ChangeUnit` (PEP 604 union), `Hunk`, `OpaqueSection`, `HunkGroup`, `SplitPlan`. No I/O |
| `src/split/hunk_parser.py` | feat | `parse_units()`, `build_patch()`, `make_unit_id()`, count-driven `_FULL_HUNK_RE` |
| `src/split/hunk_grouper.py` | feat | Prompt rendering, budget trimming, response validation, embedded system instruction |
| `src/split/generate_split_plan.py` | feat | Diff → units → opaque groups → AI grouping → pre-validation → per-group messages. Read-only |
| `src/split/apply_split_plan.py` | feat | The only mutating module: selective staging, per-group verification, commits |
| `src/infrastructure/git/patch_applier.py` | refactor | Moved verbatim + `check_patch_cached()` / `apply_patch_cached()` |
| `src/infrastructure/git/selective_stager.py` | feat | `stage_hunks`, `check_units`, `unstage_all`, `index_is_clean`, `HunkConflictError` |
| `src/fix/patch_applier.py` | refactor | Becomes a re-export shim (168 deletions are the move, not a change) |
| `src/fix/__init__.py` | docs | Shim note |
| `src/core.py` | feat | `SPLIT_DIFF_ARGS` + `get_split_diff()` only — nothing else |
| `src/main.py` | feat | The `split` subcommand, modelled on `fix` and `review-pr` |
| `src/config.py` | feat | Three `DEFAULT_CONFIG` keys + `get_split_settings()` |
| `src/config_schema.py` | feat | `Category("split", …)` + three `ConfigField`s |
| `src/updater.py` | chore | `__lang_version__` `v0.0.30` → `v0.0.31` |
| `langs/*.json` (6) | feat | 50 keys each, sorted into position, `50 insertions / 0 deletions` per file |
| `CLAUDE.md` | docs | Architecture tree, subcommand table, config-variable list |
| `README.md` + 4 variants | docs | One bullet beside the `fix` bullet |
| `tests/split/` (9 files) | test | 101 tests |
| `docs/split-command.md` + `.pt_br.md` | docs | Feature page (198 lines each) |
| `docs/plans/glossary-gitpr-split.md` | docs | Canonical vocabulary |
| `docs/plans/ADR-006-split-apply-safety.md` | docs | Why split departs from every other flow |
| `docs/plans/20260919_split_atomic_commits_hunk.md` | docs | The approved plan |
| `docs/survey/20260919_gitpr_split_command_surveyfacts.md` | docs | The grill survey behind it |

### Impact

- **Functionality:** a new `gitpr split [--dry-run] [--apply] [--yes] [--max-groups N] [--provider NAME]` subcommand. Additive: no existing flag, output file or environment variable changed meaning. `--dry-run` never touches the index or the working tree in any index state; `--apply` asks once for permission to unstage everything, then stages and commits group by group. The working tree is never written to.
- **Performance:** one grouping call plus one message call per group — the real run against this repository's own tree made six calls, and a repeat run was served entirely from the MD5 cache. No batching and no map-reduce on the grouping path.
- **Compatibility:** no migration and no API break. `src/fix/patch_applier.py`'s public names are unchanged (re-exported), so `tests/fix/**` is untouched and green. `__lang_version__` moving to `v0.0.31` makes existing installs re-download their language pack, smart-excludes and thinking words once on the next run — the same step every preceding feature took.

#### Deviations from the approved plan

1. **Nothing was committed.** The repo's rules forbid `git add`/`commit`/`push`, so the plan's per-step commit structure cannot be honoured. Everything is in the working tree for you to review.
2. **The report filename is dated 2026-09-21, not 2026-09-19.** The plan named `2026-09-19_gitpr_split_command.md`; CLAUDE.md requires `{current_date}`, which is today.
3. **`__lang_version__` was bumped to `v0.0.31` — a defect found in this task's own work.** The plan's step 10 covered the six `langs/*.json` files but not the marker that delivers them. `origin/main` already carries `v0.0.30`, so any user who ran GitPR after the badge release has `LANG_VERSION=v0.0.30` stored, and the gate at [i18n.py:69](../../../../src/i18n.py#L69) (`needs_update = force or current_env_version != __lang_version__`) would have been **permanently False**: all 50 split strings would have stayed English for every `pt_br`/`pt_pt`/`es`/`es_es`/`fr`/`fr_fr` user, with nothing failing anywhere to say so. Verified against `origin/main` before and after the change.
4. **The 50 keys were sorted into position rather than appended at the end of the file.** The first pass appended them as one block; the file's convention is code-point order with the `⚠️` clusters sitting beside the text they warn about (pt_br has exactly 4 descents, the others 5), and the badge commit inserted each key in its sorted neighbourhood. The keys were moved into place with the descent profile preserved and a JSON key/value round-trip asserted before writing. **Measured side effect:** scattering the keys turns the six langs files from 6 hunks into **84** — 14 per file instead of 1 — and those 84 are what carry this repository's own dry run past the `GITPR_SPLIT_MAX_HUNKS` ceiling of 50 (104 units in total, 84 of them in `langs/`; see Verification). It is a one-time artefact of this diff: once committed, a future key is one hunk again.
5. **`--interactive` is absent, not stubbed**, and spec §6's `min_confidence_to_group` plus both `include_staged`/`include_unstaged` keys were dropped as dead — both as the plan settled them.

### Verification

```
python -m pytest tests/split -q                              # 101 passed
GITPR_LANG=en_us python -m pytest tests/split -q             # 101 passed
GITPR_LANG=pt_br python -m pytest tests/split -q             # 101 passed
GITPR_LANG=en_us python -m pytest tests/ -q                  # 3 failed, 1773 passed, 2 skipped, 81 subtests passed
```

The new tests are immune to the ambient language because `tests/split/conftest.py` pins `CURRENT_LANG` to `en_us` and clears `TRANSLATIONS` — 101 passed under both settings, which the rest of the suite does not manage.

**The 3 failures are pre-existing, and the comparison is against the code at `HEAD`.** A `git worktree add --detach` at `69f41ec` ran the full suite with the same command and produced **3 failed, 1672 passed, 2 skipped, 81 subtests** — a `diff` of the two sorted `FAILED` lists is empty, three against three, and the pass count grows by exactly **+101**, the size of `tests/split`:

| | failures | passed |
|---|---|---|
| `69f41ec` (clean worktree) | 3 | 1672 |
| working tree | 3 | 1773 |

The three are `tests/test_core.py::TestHooksLanguage::test_the_language_chosen_with_the_lang_flag_is_honoured` and two in `tests/test_net_timeouts.py::TestTimeoutConfig`. None is in a file this change touches. The two timeout ones are a committed mismatch: `_DEFAULT_AI_TIMEOUT = 180.0` at `HEAD` while the tests assert `600.0`.

**A caveat that matters more than the failures themselves.** Those counts are under `GITPR_LANG=en_us`. Under this developer's ambient `pt_br` the same tree reports **25 failed, 1751 passed, 2 skipped, 81 subtests**. Comparing the two `FAILED` sets:

| | tests |
|---|---|
| Fail under **both** settings — the two timeouts, language-independent | 2 |
| Fail under `pt_br` **only** — assert English text without pinning the language | 23 |
| Fail under `en_us` **only** — assert the ambient default *is* `pt_br` (`TestHooksLanguage`) | 1 |

So 24 tests are coupled to the ambient language in one direction or the other, and the count goes up or down depending on who runs it. Under `pt_br` the families are `test_config_app` (13), `test_suggest_reviewers` (5), `test_net_timeouts` (2), and one each in `test_chat_backend`, `test_mcp_server`, `test_reviewer_resolution`, `test_main_suggest_reviewers` and `fix/test_rollback_fix` — the same families, name for name, that the badge report recorded at `da162d0`. This is a pre-existing test-isolation defect, not something this change introduced — proven by the identical failure set at `69f41ec` — but it means "the suite is green" is not currently a statement this repository can make, and the language-pinning fixture in `tests/split/conftest.py` is the shape of the fix.

End to end, read-only, against this repository's own dirty tree (20 modified files, index verified clean before and after):

```
python run.py split --dry-run
```

produced a real plan — **5 groups**, each with a semantic label, a rationale and a Conventional Commits message:

| Group | Units | Files | Message |
|---|---|---|---|
| G1 | 7 | CLAUDE.md, README ×5 | `docs: add gitpr split subcommand to READMEs and CLAUDE.md` |
| G2 | 38 | langs/*.json ×6 | `feat: add i18n strings for split commits feature` |
| G3 | 2 | src/config.py, src/config_schema.py | `feat: add split configuration settings` |
| G4 | 2 | src/core.py, src/main.py | `feat: add split command to create atomic commits` |
| G5 | 1 | src/fix/patch_applier.py | `refactor: move patch_applier to infrastructure with shim` |

The grouping separated documentation, translations, configuration, implementation and the refactor without being told which was which — including keeping the `patch_applier` move out of the implementation commit. 54 units exceeded the budget and were reported in `ungrouped_units`, naming every id; 12 untracked files were named and excluded. **The run mutated nothing**: `git diff --cached` stayed empty, `HEAD` stayed at `69f41ec`, and the working tree's `736 insertions / 177 deletions` were identical before and after.

`--apply` was exercised only against scratch repositories built by the test fixture, never against this tree, by contract.

### Next steps

- **The ambient-language coupling is the highest-value fix here.** 24 tests pass or fail depending on an environment variable, which makes the suite's result unreproducible across machines. The `monkeypatch` fixture already written for `tests/split/conftest.py` generalises to the rest.
- **The two timeout tests are a one-line disagreement** — `_DEFAULT_AI_TIMEOUT` is `180.0` and the tests want `600.0`. One of the two is stale; which one is a decision, not a lookup.
- **`gitpr -h --split` has no `HELP_MAP` entry**, following the `demo` and `badge` precedent. Its help is `gitpr split --help`.
- **The budget ceiling is reachable in ordinary use.** This repository's own diff hit it after a routine translation-key edit; a user with a large uncommitted tree will meet `ungrouped_units` often. Raising the default or summarising trimmed units rather than only naming their ids are both worth considering.
- **Untracked residue left alone:** `.gitpr/metrics/export/gitpr_metrics_2026-09-21.{csv,json}` and `.gitpr/reports/pr_desc/develop_natan_20260919101657_PR_DESC.md` are not gitignored and not part of this change. `docs/plans/20260918_skill_gitpr_split_command_spec.md` carries a one-word working-tree edit (the checklist said "seção nova Demo", corrected to "Split") that predates this task and is left as it is.
