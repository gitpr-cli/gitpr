# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add split command to turn uncommitted changes into atomic commits
```

---

## 🎯 Summary

GitPR could describe a branch, review it and fix it, but a working tree holding several unrelated concerns still landed as a single blob commit. `gitpr split` closes that gap: it reads the uncommitted diff, has the AI partition its hunks by logical intent, and proposes one atomic commit per concern — each with a message generated from that group's rebuilt patch alone. The tree is never rewritten: the files on disk end byte-identical to how they started, only the history changes.

## 🛠️ Technical Changes

- New `split` CLI command (`src/main.py`) with `--dry-run`, `--apply`, `--yes`, `--max-groups` and `--provider`; bare invocation prints the plan and asks before committing anything.
- New `src/split/` package, layered bottom-up: `split_plan.py` (Hunk / OpaqueSection / HunkGroup / SplitPlan contract), `hunk_parser.py` (count-driven hunk parsing and patch rebuilding), `hunk_grouper.py` (prompt construction plus validation of the AI answer), `generate_split_plan.py` (read-only use case), `apply_split_plan.py` (the only module that commits).
- New `src/infrastructure/git/` package: `patch_applier.py` moved out of `src/fix/` and extended with `--cached` check/apply and an `env` parameter so a throwaway `GIT_INDEX_FILE` can be used. `src/fix/patch_applier.py` is now a re-export shim, so existing imports keep working.
- New `selective_stager.py` stages an arbitrary subset of hunks, pre-validating every group against a temporary HEAD index so a plan is never applied unchecked and the user's index is never read or moved during planning.
- New `core.get_split_diff()` with dedicated `SPLIT_DIFF_ARGS` (`--binary -M -U3`), deliberately not reusing `get_git_diff()`; `-w` and the smart excludes would both break the byte-identical guarantee.
- New settings `GITPR_SPLIT_MAX_GROUPS`, `GITPR_SPLIT_MAX_HUNKS` and `GITPR_SPLIT_REQUIRE_CONFIRMATION`, registered as a new "Split" category in `config_schema.py`, plus a positive-integer parser that falls back on unparseable values.
- Localization entries added for es, es_es, fr, fr_fr, pt_br and pt_pt; `__lang_version__` bumped to `v0.0.31`.
- New test suite under `tests/split/` (plan generation, apply, parser, grouper, selective stager, CLI) running against real throwaway repositories with the network blocked.

## ⚠️ Impact/Warnings

- **New environment variables / config keys**: `GITPR_SPLIT_MAX_GROUPS` (default `5`), `GITPR_SPLIT_MAX_HUNKS` (default `50`), `GITPR_SPLIT_REQUIRE_CONFIRMATION` (default `true`). Zero or negative values are ignored in favour of the defaults rather than silently disabling a ceiling.
- **Destructive to the index, not to the tree**: `gitpr split --apply` resets the index to HEAD before staging, so anything the user had already staged is unstaged. File contents are preserved, but the staging must be redone.
- **Internal module move**: new code should import `src.infrastructure.git.patch_applier` / `selective_stager`. The old `src/fix/patch_applier.py` path remains as a shim and no public API is broken.
- **Language dictionary version bumped**: the shipped `langs/*.json` files and `src/updater.py` must be released together, or users will be offered an update whose keys are missing.
- **AI dependency**: grouping and commit messages require a configured provider and API key; responses are cached as elsewhere in the project.
- **Review artifacts**: the sample metrics files under `.gitpr/metrics/export/` look like generated local data and probably should not be versioned.
- No database changes.


close #181

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)