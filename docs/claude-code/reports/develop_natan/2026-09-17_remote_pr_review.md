## Completion Report — Remote Pull Request Review (`gitpr review-pr`)

### What was done

Implemented `gitpr review-pr <n>`: review a pull request that is **already open on the forge**, fetching its diff from the API, without checking out its branch. The audience expansion the spec asked for — from "who is about to open a PR" to "who was invited to review someone else's PR".

The feature is orchestration, not a second review engine. The existing engine (`generate_pr_content`), the linter (`parse_diff_and_lint`) and the renderer are the local flow's own pieces, fed with a diff that came from somewhere else; a `.txt` from a remote review and one from a local review of the same diff differ only in the file name.

- **SCM contract** — `get_pull_request(repo, pr_id)` added as a **concrete** ABC method (default raises `ScmNotSupportedError`, `create_release` pattern) and implemented in all four providers; `supports_reviewable_diff` class attribute added (`False` on Azure DevOps), checked before any network call.
- **Two latent defects fixed**, both of which this feature would have exposed: GitLab's `get_pull_request_diff` dropped the file path (`changes[].diff` is a bare hunk, `old_path`/`new_path` were ignored — the AI would have reviewed orphan hunks and neither the chunker nor the exclude filter could work) and ignored `overflow: true` (a truncated diff would have been reviewed halfway and published as if whole). Headers are now synthesized and truncation raises.
- **`split_patch_sections`** added to `src/diff_parser.py` (pure parsing, where ADR-004 put it) as the basis of the Python-side smart-excludes filter.
- **`src/review/`** — four single-responsibility modules: `diff_source.py` (pure data), `diff_normalizer.py` (newline normalization, diff validation, Python-side excludes), `render.py` (the artefact, extracted from `main.py` and now **shared** with the local flows) and `remote_pr.py` (the orchestration).
- **Review engine, additive only** — `generate_pr_content` gained `cache_scope=""` and `store_diff=False`, with defaults that keep the local path byte-identical (`cache_scope` is appended to the **cache key only**, never to the prompt; the empty default means zero cache invalidation).
- **`gitpr fix`** now prefers the diff recorded in the cache record and falls back to re-deriving it for older records, so it can patch the revision that was actually reviewed — the only correct source when the review came from a pull request.
- **Linter** — `parse_diff_and_lint(..., skip_external=False)`; the remote flow passes `True`, because the external bridge runs binaries against files on disk (the user's tree, not the PR) and those alerts would be published as a public comment.
- **CLI subcommand** `gitpr review-pr <n>` with `--provider` and `--post-comment`; read-only by default, never calls `check_unstaged_files`, writes `{branch}_{datetime}_PR_REVIEW.txt` named after the PR's source branch.
- **MCP tool** `review_remote_pr` — the 14th tool, read-only, no `post_comment` argument, no `.txt` written, resolves the forge itself.
- **i18n** — 20 new keys translated into all six `langs/*.json`; `__lang_version__` bumped to `v0.0.28`.
- **Docs** — new `docs/review-pr.md` + `.pt_br`, the remote mode added to `docs/code-review-ia` in all five locales, the now-false §2.2 of `docs/fix-command` rewritten in all five locales, `README.md` / `README.pt_br.md`, `CLAUDE.md` (command table, MCP tools 13 → 14, `src/review/` in the tree), plus the glossary and ADR-005.

### Changed files

| File | Change type | Description |
|------|-------------|-------------|
| `src/review/diff_source.py` | feat | `DiffOrigin` + `DiffSource` (provenance, `cache_scope`, `is_remote`) |
| `src/review/diff_normalizer.py` | feat | newline normalization, `is_reviewable_diff`, `filter_excluded_sections` |
| `src/review/render.py` | refactor | `compose_review_content` + `render_review_result`, extracted from `main.py` and shared |
| `src/review/remote_pr.py` | feat | the orchestrator: gate → PR → diff → normalise → excludes → engine → linter → comment |
| `src/review/__init__.py` | feat | package marker (setuptools discovery) |
| `src/infrastructure/scm/base.py` | feat | concrete `get_pull_request`, `supports_reviewable_diff` |
| `src/infrastructure/scm/{github,gitlab,bitbucket,azure}_provider.py` | feat/fix | `get_pull_request` in the four forges; GitLab headers + `overflow`; Azure declares no reviewable diff |
| `src/diff_parser.py` | feat | `PatchSection` + `split_patch_sections` |
| `src/core.py` | feat | `cache_scope` / `store_diff` optional parameters in `generate_pr_content` |
| `src/cache.py` | feat | `reviewed_diff` field at the top level of the record |
| `src/fix/apply_fix.py` | fix | `reviewed_diff()` prefers the recorded diff |
| `src/linter_engine.py` | feat | `skip_external` gates the two external-bridge call sites |
| `src/main.py` | feat | `review-pr` subcommand |
| `src/mcp_server.py` | feat | `review_remote_pr` tool (14th) + catalog + `_TOOL_FUNCS` |
| `src/updater.py` | chore | `__lang_version__` → `v0.0.28` |
| `langs/*.json` (6) | feat | 20 keys translated per file |
| `tests/review/` (4 files) | test | 97 new tests |
| `tests/scm/test_gitlab_provider.py` | test | fixtures that exercise the synthesized headers and `overflow` |
| `tests/test_mcp_server.py` | test | 11 tests for the tool, catalog 13 → 14 |
| `docs/review-pr.md`, `docs/review-pr.pt_br.md` | docs | new feature documentation |
| `docs/code-review-ia.*` (5) | docs | remote mode as §1.4 + the external-linter caveat |
| `docs/fix-command.*` (5) | docs | §2.2 rewritten: the diff now comes from the record |
| `README.md`, `README.pt_br.md`, `CLAUDE.md` | docs | command, MCP tools table, architecture tree |
| `docs/plans/glossary-review-pr.md`, `docs/plans/ADR-005-review-pr-subcommand.md` | docs | vocabulary + decisions |
| `docs/survey/20260917_skill_gitpr_review_pr_surveyfacts.md` | docs | grill fact-finding record |

### Impact

- **Functionality:** new command and new MCP tool. The forge is only **read** unless `--post-comment` is passed. Every rejection the user can act on (unreviewable forge, missing/closed PR, empty or fully excluded diff, no permission) happens **before** the AI call, so a bad PR number costs no tokens.
- **Compatibility:** no breaking change. `generate_pr_content`'s new parameters are optional with local-preserving defaults, so existing cache keys are byte-identical and no installed user's cache is invalidated. `parse_diff_and_lint`'s `skip_external` defaults to `False` (current behaviour). Older cache records simply lack the `diff` field and `gitpr fix` falls back to re-deriving the diff exactly as before.
- **Cache:** a remote review is scoped `::diff-source::pr-<n>` in the **key only**, so an identical local diff can never answer a remote review or vice versa.
- **Performance:** one AI call per review, same as the local flow; the metadata call to the forge is one extra GET.

#### Test results

```
tests/review/ + tests/scm/ : 377 passed, 2 skipped
  test_diff_source.py      12 passed
  test_diff_normalizer.py  20 passed
  test_remote_pr.py        40 passed
  test_review_pr_cli.py    25 passed
full suite                 : 25 failed, 1410 passed, 2 skipped
```

### Disclosures

**(a) `tests/sync_i18n.py` is destructive and was not used.** Its `PATTERN` regex captures only the first literal of an implicitly concatenated `__("a " "b")` call, so running it removed 25 legitimate full keys and added 46 truncated fragments. The file's own comment documents this as a "Known limitation (accepted)" and `tests/test_i18n.py::_extract_keys_ast` folds the concatenation correctly — the two disagree by design. The 20 keys were inserted by hand at their sorted positions instead (a one-shot script, deleted afterwards; it asserted sortedness the way the file is *actually* sorted — the committed files carry 4–5 emoji-key inversions, so a full re-sort would have produced a huge unrelated diff).

**(b) 25 pre-existing suite failures, none of them caused by this work.** The suite is red on this machine before the change: the baseline was established by running the pristine `HEAD` tree in a throwaway `git worktree` (`25 failed`, the same 25). They are ambient-locale failures (`tests/test_config_app.py`, `tests/test_suggest_reviewers.py`, `tests/test_net_timeouts.py`, `tests/fix/test_rollback_fix.py::test_undoing_twice_is_refused`, `tests/test_mcp_server.py::TestFixCandidatesTool::test_a_review_without_findings_says_so`, among others) — tests that assert English strings without pinning the language, against a pt-BR environment. Fixing them is out of scope for this feature; the new `tests/review/` files pin `set_lang("en_us")` in `setUpClass` for exactly this reason.

**(c) Known limitation — local documentation metadata in a remote prompt.** `generate_pr_content` injects the locally changed-docs list (`get_changed_docs_list()`) into the prompt it builds. On a remote review that list describes the **user's working tree**, not the pull request under review: harmless context noise, not an incorrect review, but it is information about the wrong revision. Removing it requires a prompt path that knows the diff's origin — which is precisely the coupling that ADR-005 decided against, so it was left as-is and recorded here.

**(d) Deliberate deviations from the spec**, both documented in `src/review/remote_pr.py`'s module docstring and in ADR-005:

- `provider` is the AI provider **name** (`"gemini"`), not an instance. No provider object exists in this codebase — `ai_providers.call_ai_model` builds what it needs from the name and the configured key — so accepting an instance would have meant inventing a type to satisfy a signature. Because `scm_provider` sits beside it, the AI parameter is spelled `ai_provider` on the public function.
- the result carries **no `comment_url`**. `ScmProvider.add_comment` returns `None` by contract and no forge here reads back the created comment, so the field could only ever hold a guess. For the same reason the published comment claims **no commit SHA**.

### Next steps (if applicable)

- **A stale `ADR-002` numbering collision** already exists in `docs/plans/` (`ADR-002-gitpr-release-subcommand.md` and `ADR-002-reviewer-suggestion.md`); this ADR took **005** to avoid joining it. One of the two should eventually be renumbered.
- **`list_open_pull_requests` and `check_existing_pull_request` still paginate a single page** in all four providers. The second is reachable in production — the PR Publisher calls it before pushing (`src/ui/pr_publish_app.py:1209`), so on a busy repository it fails to find an open PR and the user creates a **duplicate**. Left out of scope and registered here.
- **GitLab could migrate to the `/diffs` endpoint**, which would remove the need for the synthesized headers at the source. Rejected for this delivery (it swaps the endpoint of a provider in production); the current fix works with what the API already returns.
- **Translations of `docs/review-pr.md`** exist for EN and PT-BR only, as the plan decided; `pt_pt`, `es_es` and `fr_fr` link to the English original for now.
