# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add review-pr command to review open pull requests
```

---

## 🎯 Summary

Reviewing a pull request authored by someone else used to require checking the branch out and losing the local context. This change adds `gitpr review-pr <number>`, which fetches the diff straight from the forge over the API and runs it through the exact review engine the local flows already use — same report, same linter rules, same `.txt` artefact. The command is read-only by default: nothing is published on the forge unless `--post-comment` is passed explicitly. The same capability is exposed as the read-only MCP tool `review_remote_pr` and, alongside it, the SCM layer gains the primitives (fetch a single PR, GitLab's diff reconstruction, a capability flag) needed to support reviewing a revision that is not on disk.

## 🛠️ Technical Changes

- Add the `src/review/` package: `diff_source.py` (provenance contract), `diff_normalizer.py` (smart excludes for a diff git never saw), `render.py` (review artefact composer, extracted from `main.py`), `remote_pr.py` (the use case).
- Add the `gitpr review-pr` CLI subcommand with `--provider` and `--post-comment`, reusing `_resolve_scm_context` and rejecting the PR before any AI call on capability, existence, state, empty/unreviewable diff, and smart-exclude exhaustion.
- Add the `review_remote_pr` MCP tool (read-only, never posts a comment, never writes a file) and ship the stdio/HTTP server registry and tool catalog accordingly.
- Add `ScmProvider.get_pull_request` to the base class and all four providers (GitHub, GitLab, Bitbucket, Azure DevOps) to distinguish "does not exist" from "merged/closed" — `list_open_pull_requests` cannot.
- Add the `supports_reviewable_diff` capability flag; Azure DevOps declares `False` because its REST API serves a file summary rather than a unified diff.
- Rebuild GitLab diffs from `old_path`/`new_path` since its `diff` field carries hunk bodies alone, honoring `/dev/null` for added/deleted files and raising `ScmProviderError` when GitLab flags `overflow` instead of silently reviewing a truncated MR.
- Add `diff_parser.split_patch_sections` to hand back each file's path beside its own text, used by the remote smart-excludes filter and the GitLab header synthesis.
- Extend `generate_pr_content` with `cache_scope` (appended to the cache key only, never to the prompt) and `store_diff`; default `""` leaves every existing local review's MD5 untouched.
- Extend `parse_diff_and_lint` with `skip_external` so a remote review never lints the user's working tree and publishes it against someone else's branch.
- Store the reviewed diff in the cache (`cache.save_cached_response`) and prefer it in `fix/apply_fix.reviewed_diff`, so `gitpr fix` patches the revision that was reviewed rather than the tree of the day it runs; older records fall back to re-derivation.
- Update the `es`, `fr`, `pt_br`, `pt_pt` and `es_es` dictionaries for the new strings, bump `__lang_version__` to `v0.0.28`, and add `docs/review-pr.md` plus its translations, plan, ADR and glossary.
- Add tests for the normalizer, `DiffSource`, `remote_pr`, the CLI, the MCP tool, and the GitLab provider's new diff reconstruction.

## ⚠️ Impact/Warnings

- **New CLI subcommand:** `gitpr review-pr <number> [--provider <name>] [--post-comment]`. Requires a repository whose remote is resolvable and a forge token set with `gitpr --init`; `--post-comment` is the only path that writes to the forge.
- **New MCP tool:** the tool registry grows from 13 to 14 tools (`review_remote_pr`), reflected in `_build_tools_catalog` and its tests.
- **Changed behaviour:** `gitpr fix` now prefers the diff recorded with the review when present, which is the only way to correct a patch derived from a remote PR or a full-branch diff; pre-existing cache records keep working via re-derivation.
- **Changed behaviour:** GitLab MRs whose diff overflows the API size limit now fail with a clear error instead of silently reviewing a truncated payload.
- **Changed behaviour:** `generate_pr_content` defaults keep existing cache keys byte-identical; remote reviews are scoped by `::diff-source::pr-<n>` and cannot be answered by a matching local review.
- **No database, no dependency and no environment-variable changes.**


close #173