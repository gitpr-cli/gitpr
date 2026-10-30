# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add project-local pull request base branch config
```

---

## 🎯 Summary

Until now the pull request target branch lived only in the machine-wide `~/.gitpr/.env` (`PR_DEFAULT_BASE`) or was guessed from `origin/HEAD`, so a repository could not declare where its PRs should land. Teams targeting `develop` had to rely on every developer setting the same variable by hand, and the failure mode (a PR opened against the wrong branch) was only discovered on the forge.

This change introduces a repository-versioned configuration file — `.gitpr/conf/gitpr.config.yml` — that carries the PR target base branch with the code. The value travels with the project, is edited from the existing `gitpr config` screen, and is validated before anything is committed or pushed. A single resolver now serves the CLI and the MCP server, so all entry points agree on the precedence chain and on the same failure rules.

A pull request also can no longer target the branch it is opened from. That case is detected and, in an interactive run, repaired by a dedicated picker that writes the new value into the project file.

## 🛠️ Technical Changes

- Add `src/project_config.py`: path resolution anchored at the repository root, YAML read/write that preserves unrelated keys, idempotent seeding of the file, branch listing, current-branch detection, and remote verification.
- Implement a single precedence chain via `resolve_pull_request_base()`: `--base` → project file → `PR_DEFAULT_BASE` → `origin/HEAD` detection → `main`.
- Add `BaseBranchError` / `CurrentBranchError` and validate the resolved base against `origin/<branch>` before publishing; a missing ref or absent `origin` remote fails fast with an actionable hint instead of opening a doomed PR.
- Add the `project` category to `config_schema.py` with a `store` attribute (`env` vs `project`), the `KIND_BRANCH` widget kind, and three fields: the file path (read-only), the editable target branch, and the effective branch with its source (read-only).
- Extend `src/ui/config_app.py` to dispatch writes per store: project values never reach `save_config_values()`, are written first, support removal-on-empty, refuse the current branch, and never overwrite unparsable YAML. Add an in-place refresh of the effective-base row after saving.
- Add `src/ui/pr_base_app.py`, a focused modal that asks for a replacement target branch and is driven headless in tests.
- `src/main.py`: seed the project file on every invocation inside a repository (except help paths), announce creation only on the interactive root path, and route `--base` through `_resolve_pr_target()`, which repairs a stale project value when interactive and otherwise reports the refusal.
- `src/mcp_server.py`: `publish_pull_request` uses the shared resolver, returns an error envelope on `BaseBranchError`, and exposes resolver `warnings` in the payload and tool catalog.
- `src/core.py`: `get_base_branch()` gains `quiet` so the TUI and JSON-RPC streams are not polluted by the fallback warning.
- Add translations for all new strings in `es`, `es_es`, `fr`, `fr_fr`, `pt_br`, `pt_pt`, and update the configuration/install documentation.
- Tests: new suites for the config module, the picker, its CLI wiring, and the schema store split; existing config, MCP and CLI tests updated.

## ⚠️ Impact/Warnings

- **Repository side effect:** running `gitpr` inside a git repository now creates `.gitpr/conf/gitpr.config.yml` on first use. Existing files are never overwritten, and the creation is skipped for help paths. If `.gitignore` excludes the file, a warning is printed because the value will not be versioned.
- **New environment variable:** `GITPR_SKIP_PROJECT_CONFIG_SEED` disables the seed. It is set to `true` in `tests/conftest.py` so the test suite never writes into a developer checkout.
- **Behavior change:** the PR base branch is now validated against `origin`. A branch that does not exist on the remote, a repository without an `origin` remote, or a target equal to the current branch now aborts with an error instead of attempting the publication.
- **MCP contract change:** `publish_pull_request` may now return `{"status": "error"}` for an invalid base branch and includes an optional `warnings` array in the success payload. Consumers ignoring unknown keys are unaffected; the target-branch documentation was updated.
- **Renamed strings:** `Default Base Branch` became `Global Default Base Branch`, and its description and the `--base` help text were rewritten. Any external tooling matching on those labels must be reviewed.
- **Precedence change:** `--base` now overrides the project file and `PR_DEFAULT_BASE`; `PR_DEFAULT_BASE` acts as a machine-wide fallback only when the repository declares no target.
- No database, dependency, or migration changes; YAML is read through the already present `PyYAML` dependency.

close #234

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)