# Plan — `gitpr split`: atomic commits by hunk

## Context

`docs/plans/20260918_skill_gitpr_split_command_spec.md` specifies a `gitpr split` command: read a working tree holding several unrelated concerns, group the hunks by logical intent with AI, and propose (or create) N atomic commits, each with a message generated for that subset alone.

A grilling session settled every open decision before implementation. Three of the spec's own premises did not survive contact with the code, and one originally-settled decision was found to be flawed — both are corrected below. The design tree is exhausted; nothing is left assumed.

**Intended outcome:** `gitpr split` turns a messy working tree into clean, ordered, atomic commits, without ever writing to the working tree — the final file contents are byte-identical to the state before the command, only distributed across commits.

---

## Spec premises that are false

| Spec claim                                                    | Reality                                                                                                                                                                                                                                                                                                                                                                                     |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| §0.1 — reuse the hunk parser already in the map-reduce engine | There is no hunk parser. Map-reduce splits at *file* granularity: `re.split(r"(^diff --git a/)", ...)` at [core.py:737](src/core.py#L737) → `list[str]`. No `unidiff`/`whatthepatch`/any diff library is declared. `_HUNK_HEADER_RE` ([diff_parser.py:17](src/diff_parser.py#L17)) captures only the new-side start/count and is load-bearing for `summarize_patch` — it cannot be widened. |
| §5 — confirm whether selective staging already exists         | It does not. The only index write in the project is file-level `git add` ([core.py:2031](src/core.py#L2031)). No `--cached`, no `update-index`, no `add -p`, no `git reset` anywhere in `src/`.                                                                                                                                                                                             |
| §0.4 / §4.6 — reuse the commit-message pipeline               | True and clean: [core.py:762](src/core.py#L762) `generate_pr_content("commit", "commit", diff_text, provider)` takes a **raw diff string** and returns `{"commit_message": ...}`, pulling in the commit skill, the MD5 cache and the map-reduce path.                                                                                                                                       |

---

## Settled decisions

**Structure**
1. `src/split/` sub-package (`split_plan.py`, `hunk_parser.py`, `hunk_grouper.py`, `generate_split_plan.py`, `apply_split_plan.py`) + `src/infrastructure/git/selective_stager.py`.
2. `src/fix/patch_applier.py` **moves** to `src/infrastructure/git/patch_applier.py`; the old path becomes a silent re-export shim (precedent: [github_api.py](src/github_api.py) shims `github_provider.py`). `tests/fix/**` must stay green. `selective_stager` imports `_apply` — never re-implements it, because the byte-stdin CRLF defence at [patch_applier.py:62](src/fix/patch_applier.py#L62) is the project's single most important Windows protection.

**Diff capture**
3. New `get_split_diff(quiet=False)` in `core.py`, beside `get_git_diff`: `SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")`, `git diff <args> HEAD`, **no pathspec**. Deliberately not `get_git_diff()`: `-w` renders whitespace-only differences as context, producing a patch `git apply` must refuse or must apply as content differing from the working tree — which breaks the byte-identical guarantee. `-U1` leaves too little context to anchor. `-B` splits rewrites into delete+add. `-M` is **kept** so renames stay whole; `--binary` is a no-op for text diffs and makes binary changes applicable.
4. **No smart excludes in split.** Excluding a lockfile while committing its manifest produces a broken intermediate commit. The AI prompt is bounded by per-unit truncation instead.
5. **Capture first, unstage last.** The diff is captured against whatever index state exists — staged new files and renames only appear in `git diff HEAD` because the index tracks them, and `git reset` would drop them out of scope. Hunks carry HEAD-based pre-images regardless of what is staged, and after the unstage the index *is* HEAD, so they apply cleanly. No re-diff, no abort, no plan silently re-shaped. `--dry-run` never mutates in any index state.
6. Untracked files are out of scope; the warning names them explicitly.

**Domain model**
7. `ChangeUnit` is a **PEP 604 union alias** — `ChangeUnit = Hunk | OpaqueSection`, both `@dataclass(frozen=True)`, dispatch by `isinstance`. No ABC, no inheritance.
8. `HunkGroup.units: list[ChangeUnit]` replaces the spec's `hunks`; `SplitPlan.ungrouped_units` / `total_units` follow. `group_id` is `G1..Gn` assigned by gitpr in the model's returned order — never by the model.
9. `Hunk` keeps the spec's six fields and adds `file_header`, `old_count`, `new_count`, `ordinal`. The file header is **not** reconstructible from a path: `new file mode`, `deleted file mode`, `old mode`/`new mode`, and git's quoted form for non-ASCII/spaced paths are all unrecoverable, and synthesizing them breaks `git apply`.
10. Non-hunk sections (binary, pure rename, mode-only, malformed) become `OpaqueSection` and then forced atomic single groups. The AI never sees them.

**AI**
11. Grouping is **one call, no batching**. Batch A cannot see batch B's hunks, so hunks belonging to one concern that straddle batches can never be reunited — batching buys coverage on huge diffs at the price of wrong answers.
12. `Hunk.id` = `f"{ordinal:04d}-{md5(file_path + hunk_header + content)[:8]}"`. Deterministic (fixed traversal) *and* collision-safe: a bare content hash — the spec's own suggestion — collides on two byte-identical hunks in one file.
13. Overflow past `GITPR_SPLIT_MAX_HUNKS` (or past the prompt budget) goes to `ungrouped_units` with a warning naming the ids. Largest-first when trimming for budget, so a long diff does not systematically starve its last files.
14. The grouping prompt is a **fixed system instruction** embedded in `hunk_grouper.py`. `get_skill_context("split")` would silently return the *review* skill (`DEFAULT_SKILL_TYPE = "review"`); registering a real skill would drag in `config.py`, `SKILL_LABELS` (order-asserted), `mcp_server.py` `SKILL_FILES`, six templates and their translations.
15. Every id returned by the model is validated against the real units: unknown ids are discarded with a warning, duplicates kept once, unmentioned units forced into `ungrouped_units`. No ghost unit ever enters a group; no unit is ever silently dropped.
16. AI failure (no key, unreachable, three failed retries) → `SplitError` with **zero mutation**.

**Config**
17. `GITPR_SPLIT_MAX_GROUPS` (int, 5), `GITPR_SPLIT_REQUIRE_CONFIRMATION` (bool, true), `GITPR_SPLIT_MAX_HUNKS` (int, 50) — declared as `ConfigField`s in `config_schema.py` with literal `__()` labels, `DEFAULT_CONFIG` entries and a `get_split_settings()` getter. Spec §6's `min_confidence_to_group` and both `include_staged/unstaged` keys are dropped as dead.

**CLI**
18. `gitpr split [--dry-run] [--apply] [--yes] [--max-groups N] [--provider NAME]`. Bare → print the plan, then offer to apply. `--dry-run` → print and stop, never prompts. `--apply` → print, confirm once (unstage folded in), execute. `--interactive` is **absent**, not stubbed.

**Safety**
19. Mid-sequence failure stops cleanly with **no rollback** of commits already created (spec §1 puts automatic undo out of scope). Index handling differs per failure site: a staging failure triggers `unstage_all`; a commit failure leaves the group staged and says so verbatim rather than hiding which units were in flight.
20. **Terminal fallback** (added here; the spec has no exit for it): when forcing a whole file into one group still fails `git apply --cached --check` — a CRLF file, a binary unit — the units go to `ungrouped_units` with a warning. The conflict loop is bounded and always terminates.

**Accepted, not fixed**
- CRLF repos: capturing with `text=True` plus `split_patch_sections`' `rstrip("\r")` strips CRs, so `--check` refuses those files. Loud failure, never a corrupt apply. Documented, regression-tested, and only worth revisiting (byte capture + a CR-preserving parser, abandoning the one-parser rule) if it bites a real user.
- `generate_pr_content` prints a banner per call → N banners for N groups. Accepted as progress output.
- `execute_git_commit` returns no hash, so `commits_created` comes from `patch_applier.current_head()` after each commit.

---

## Files

**Create**

| Path                                         | Responsibility                                                                                                               |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `src/split/__init__.py`                      | Package docstring; re-exports nothing (precedent: `src/fix/__init__.py`)                                                     |
| `src/split/split_plan.py`                    | The data contract only: `SplitError`, `ChangeUnit`, `Hunk`, `OpaqueSection`, `HunkGroup`, `SplitPlan`. No I/O                |
| `src/split/hunk_parser.py`                   | `parse_units()`, `build_patch()`, `make_unit_id()`, `_FULL_HUNK_RE`. Pure text↔model, never runs git                         |
| `src/split/hunk_grouper.py`                  | Prompt rendering, truncation/budget, `call_ai_model`, cache, response validation                                             |
| `src/split/generate_split_plan.py`           | Use case: diff → units → opaque groups → AI grouping → conflict pre-validation → per-group messages → `SplitPlan`. Read-only |
| `src/split/apply_split_plan.py`              | Use case + `ApplySplitResult`. The only split module that mutates git                                                        |
| `src/infrastructure/git/__init__.py`         | Package docstring                                                                                                            |
| `src/infrastructure/git/patch_applier.py`    | The moved module, verbatim, plus `check_patch_cached()` / `apply_patch_cached()`                                             |
| `src/infrastructure/git/selective_stager.py` | `stage_hunks`, `check_units`, `unstage_all`, `index_is_clean`, `HunkConflictError`                                           |
| `tests/split/**`                             | See Tests below                                                                                                              |
| `docs/split-command.md` + `.pt_br.md`        | Feature page (matches `fix-command.md` / `review-pr.md`)                                                                     |
| `docs/plans/glossary-gitpr-split.md`         | Vocabulary + the recorded deviations from spec §3                                                                            |
| `docs/plans/ADR-006-split-apply-safety.md`   | Why split departs from every other flow: own diff capture, clean-index precondition, no smart excludes                       |

**Modify**

| Path                                         | Change                                                                                           |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `src/fix/patch_applier.py`                   | Becomes a re-export shim over `src.infrastructure.git.patch_applier`                             |
| `src/core.py`                                | `SPLIT_DIFF_ARGS` + `get_split_diff()`. Nothing else                                             |
| `src/main.py`                                | The `split` subcommand, modelled on `fix` (:2073) and `review-pr` (:2347)                        |
| `src/config.py`                              | Three `DEFAULT_CONFIG` keys + `get_split_settings()` (mirrors `get_fix_settings()` at :724)      |
| `src/config_schema.py`                       | `Category("split", ...)` + three `ConfigField`s (the `fix` category at :635–686 is the template) |
| `langs/{pt_br,pt_pt,es,es_es,fr,fr_fr}.json` | Every new `__()` key — full pass across all six                                                  |
| `README.md` + 4 translations                 | One bullet beside the `fix` bullet                                                               |

**Not touched:** `src/mcp_server.py`, the skill registry, `tests/fix/**` (green required), `scripts/fix_mangled_i18n_keys.py` (asserts `CLEAN_KEYS == 49`).

---

## Key algorithms

**Hunk parsing** — `parse_units()` reuses `diff_parser.split_patch_sections()` ([diff_parser.py:256](src/diff_parser.py#L256)) for the file-level split, then owns a local regex capturing **both** sides:

```
^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@
```

A hunk ends when its **declared counts are exhausted**, not at the next `@@` — the only safe rule, since `--- ` and `+++ ` at column 0 inside a hunk are indistinguishable from headers, while a context line always carries a leading space. Count-driven consumption doubles as the malformed-input validator: any mismatch degrades the *whole section* to one `OpaqueSection` — never a partial hunk list, because half a malformed section is not something to hand to `git apply`. `\ No newline at end of file` is consumed unconditionally. A missing count means 1, except an explicit `0`.

**Patch rebuild** — `build_patch(units)` groups units by file, emits `Hunk.file_header` once per file followed by its hunks, sorted by `ordinal` (never caller order — hunks re-emitted out of ascending order apply at the wrong offsets), and appends opaque sections verbatim. `_normalize_header` drops the `index <old>..<new>` line for hunk-bearing sections so a later group's patch no longer asserts a preimage blob the index has moved past — but **keeps** it for hunk-less ones, because a `GIT binary patch` requires the full index line.

**Staging** — `stage_hunks(units, repo_path)` builds the patch, runs `git apply --cached --check -` first, raises `HunkConflictError(units, error)` on refusal, then `git apply --cached -`. Both go through the moved `_apply`, inheriting the byte-stdin CRLF defence.

**Conflict response at plan time** — a failing group triggers `_force_whole_files`: every unit of every file that group touches, from every group and from `ungrouped_units`, merges into it; emptied groups are dropped; the merged group's commit message is **regenerated** for the merged patch (a message describing a subgroup would be a lie about the commit). Bounded loop; on exhaustion, decision 20's terminal fallback.

**Verification while applying** — `index_is_clean()` before staging group N and after group N's commit makes cross-group leakage structurally impossible. After staging, the path set from `git diff --cached -M --name-status` must equal the group's file set, and per-file `(added, removed)` from `--numstat` must equal the counts computed from the units' `+`/`-` lines. Numstat is invariant under context shifts, unlike hunk headers, which would false-alarm whenever a neighbouring commit moved the context.

---

## Ordering

Each step leaves the suite green before the next begins.

1. `src/infrastructure/git/` + move `patch_applier` + `--cached` wrappers + the `fix` shim → `tests/fix/**` green **first**. Pure refactor, and nothing mocks `src.fix.patch_applier.<name>`, so a re-export suffices.
2. `split_plan.py` (contract).
3. `hunk_parser.py` + acceptance 1.
4. `selective_stager.py` + acceptance 4/5 — highest risk, validated standalone before any consumer.
5. Config (`DEFAULT_CONFIG`, getter, schema category, **and `docs/split-command.md`**, which the schema's `doc=` link requires to exist).
6. `hunk_grouper.py` + acceptance 2.
7. `core.get_split_diff()` + `generate_split_plan.py` + acceptance 2c/6/7.
8. `apply_split_plan.py` + acceptance 3/8/9.
9. `src/main.py` split command + CLI tests.
10. i18n across all six `langs/*.json`.
11. Docs, READMEs, glossary, ADR-006.
12. Full suite + the mandatory completion report at `docs/claude-code/reports/develop_natan/2026-09-19_gitpr_split_command.md`.

**Step 0 (before everything):** write the survey at `docs/survey/20260919_gitpr_split_command_surveyfacts.md` — plan mode permits only the plan file this turn, so the skill's mandated survey is deferred to execution, carrying the round-by-round decisions and the §0 fact report.

---

## Verification

- `tests/split/git_fixture.py` extends `tests/fix/git_fixture.py`'s `GitRepoTestCase` unchanged (it already pins `core.autocrlf=false`, `commit.gpgsign=false`, and provides `write/read/commit/patch_for/status_porcelain/seed`), adding `seed_multi()`, `diff_now()` and a `stubbed(...)` context manager over `call_ai_model` / `generate_pr_content` / the cache.
- Spec §7's ten acceptance tests map onto `tests/split/`; the interactive one (#10) is deferred. The load-bearing four: **#1** exact hunks and deterministic, collision-safe ids; **#3** byte-identical final tree via a `copytree` snapshot and an empty `status_porcelain()`; **#4** `stage_hunks` on 3 of 5 hunks leaves exactly those staged; **#8** `git show --stat` per commit matches its group.
- **#9** mid-sequence failure uses a real `pre-commit` hook that rejects the second commit, asserting commits 1..N-1 survive and the report is accurate.
- **Performance:** the acceptance criterion is one AI grouping call plus one commit-message call per group — no batching, no map-reduce.
- **Compatibility:** no migration, no API break, no version bump (releases are cut through `gitpr release` per ADR-002).
- **End-to-end, read-only:** `gitpr split --dry-run` against this repo's own dirty working tree (~20 modified files) — the ideal real-world subject, and safe by contract since dry-run never touches the index or working tree. `--apply` runs **only** against scratch repos built by the test fixture; the user's uncommitted work is never committed as a test.
