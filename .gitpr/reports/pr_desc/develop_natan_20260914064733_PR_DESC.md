# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add gitpr fix subcommand with safe patch apply and rollback
```

---

## 🎯 Summary

This PR introduces `gitpr fix`, a new GitPR subcommand that turns code-review findings into the smallest applicable unified diff and applies it to the working tree under an explicit safety model. The goal is to close the loop between automated code review and remediation: instead of re-prompting an LLM and hand-editing the result, developers can list concrete fix candidates derived from the latest cached review and apply only the patches that pass deterministic safety checks.

All writes are opt-in: the command is dry-run by default and any mutation requires `--apply` (or an explicit typed confirmation phrase with `--force`). The remainder of the diff is unrelated vendored/build noise that should not be part of this change.

## 🛠️ Technical Changes

- **New `src/fix/` package** with a layered design: data contract (`patch_provenance`), a shared code/diff extractor, a deterministic `SAFE` / `REVIEW_REQUIRED` / `EXPERIMENTAL` classifier, a git-writing wrapper (check/apply/reverse + branch creation), an atomically written `.gitpr/fix_history.json` ledger, and the apply/rollback use cases.
- **`src/cache.py`**: adds `REVIEW_ACTION_TYPES` and `resolve_last_review()`, selecting the newest cached `review`/`fullreview` record for a repo+branch while excluding file-scoped reviews.
- **`src/config.py` / `src/config_schema.py`**: adds five `GITPR_FIX_*` settings (max added+removed lines, sensitive path globs, confirmation requirement, branch-on-all-safe, branch name template) exposed as a new `fix` configuration category.
- **`src/diff_parser.py`**: adds pure `summarize_patch()` / `PatchSummary` used by the safety classifier (file count, hunk count, line delta, deleted-call detection).
- **CLI (`src/main.py`)**: registers `gitpr fix` with `--list`, `--apply`, `--all-safe`, `--create-branch`, `--no-branch`, `--yes`, `--force` (typed confirmation phrase) and `--rollback`.
- **MCP (`src/mcp_server.py`)**: adds a read-only `list_fix_candidates` tool and a `skill://fix` resource.
- **Templating / hygiene**: adds `.gitpr/fix_history.json` to the smart-excludes template, bumps the language dictionary version, and replaces the duplicated regex in `chat_app.py` with the shared `extract_code_blocks` extractor.
- **Tests**: a full `unittest` suite under `tests/fix/` covering the classifier matrix, patch applier, history ledger, CLI routing, rollback and the MCP tool, using git-backed fixtures.
- **Unrelated in the same diff (do not commit / add to `.gitignore`)**: pip HTTP cache entries under `pypa/virtualenv/wheel/3.13/image/1/CopyPipInstall/pip-25.2-py3-none-any/**` and `pip/cache/http-v2/**` — a complete auto-vendored pip 25.2 payload (`_internal`, `_vendor`, `pip-26.2.1` metadata, `pip.json` discovery marker). Pure third-party build byproducts with no relation to this feature.

## ⚠️ Impact/Warnings

- **New environment variables**: `GITPR_FIX_SAFE_MAX_LINES`, `GITPR_FIX_SENSITIVE_PATHS`, `GITPR_FIX_REQUIRE_CONFIRMATION`, `GITPR_FIX_BRANCH_ON_ALL_SAFE`, `GITPR_FIX_BRANCH_NAME_TEMPLATE`. Defaults preserve the conservative behavior (dry-run, no branch).
- **New tracked state file**: `.gitpr/fix_history.json`. It is written atomically and is required for `--rollback`; it is added to the smart-excludes template and should be committed intentionally.
- **Write safety**: the patch classifier rejects fixes spanning more than one file or hunk, touching configured sensitive paths, exceeding the added+removed line budget, deleting a line that looks like a call, declared low-confidence by the AI, or failing `git apply --check` against the current tree. `--force` never bypasses the applicability check.
- **No database changes** and no new third-party runtime dependencies are introduced by the feature itself.
- **Repository hygiene**: the vendored pip 25.2 tree included in this diff is third-party code that must never be edited in place (update only by re-vendoring) and inflates repository size significantly. Recommend excluding it from the commit or adding it to `.gitignore` before merging.

close #167