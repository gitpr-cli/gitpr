# ADR-015 — Project-local pull request target base

**Status:** Accepted (2026-10-30)
**Spec:** `docs/plans/develop_natan/20261030_project_pr_base_plansfacts.md`
**Survey:** `docs/survey/20261030_project_pr_base_surveyfacts.md`

## Context

The target branch of a pull request was resolved from `--base` → `PR_DEFAULT_BASE` → `origin/HEAD` → `main`
(`src/main.py`). `PR_DEFAULT_BASE` lives in `~/.gitpr/.env`, so it is machine-wide: a developer who
contributes to a repository that merges into `develop` and one that merges into `main` had to pass
`--base develop` on every run of the first, or change the default for every project on the machine.

The choice also has to travel with the repository: a new contributor has no way of knowing that this
project does not merge into `main`, and nothing in the checkout said so. The CLI already keeps a
repository-local directory (`./.gitpr/skill/`, `./.gitpr.linter.yml`, `./.gitpr/` artifacts), but no
repository-local *configuration* store.

## Decisions

1. **A versioned file at `.gitpr/conf/gitpr.config.yml`,** anchored at `git rev-parse --show-toplevel`
   (falling back to the working directory outside a repository). Worktrees get their own copy, since
   `--show-toplevel` reports the worktree root.

2. **Nested YAML, one commented key:**

   ```yaml
   # Project configuration for GitPR — versioned with the repository.
   # The pull request target base branch for this repository.
   pull_request:
     base_branch: develop
   ```

   The nesting leaves room for later project-local settings without a format change.

3. **Precedence: `--base` > project file > `PR_DEFAULT_BASE` > auto-detected `origin/HEAD` > `main`.**
   One resolver (`resolve_pull_request_base`) serves the CLI default flow, `--no-edit`, the publish TUI and
   the MCP `publish_pull_request` tool. The auto-detection itself is not reimplemented — the resolver calls
   `core.get_base_branch()`, imported inside the function so the module stays importable without the AI SDKs.

4. **Seeded on every invocation inside a repository,** subcommands included, and in `--install`. Seeded with
   `PR_DEFAULT_BASE` when set, literal `main` otherwise. **Never overwritten** once it exists. GitPR never runs
   `git add`: the seed prints one line telling the user to version the file, and warns when the user's own
   `.gitignore` excludes it. Help and `-h` never write; the announcement is suppressed for subcommands,
   `--quiet`, `--hook` and `--mcp`, so `gitpr config` and the stdio server keep a clean stdout.
   `GITPR_SKIP_PROJECT_CONFIG_SEED` disables it (used by the test suite).

5. **A broken file is reported, never repaired.** Unreadable YAML, a non-mapping document or a non-string
   value produce a warning and the resolution continues down the chain. Writing refuses to overwrite a file it
   could not parse, so hand-written content is never destroyed. A missing key or an empty value is not an
   error — it means "fall through".

6. **The target is verified against `origin` before publishing.** Whatever the source, the branch must exist as
   a remote-tracking ref; otherwise the publication aborts with the branch name and the
   `git fetch origin <branch>` command to run. The check runs after the diff is built, so a branch fetched by
   this very run counts. `--no-publish` never reaches it. The TUI warns on the same missing ref but **saves
   anyway**, because the branch may be about to be pushed.

7. **The screen gains a Project category** (read-only path, editable branch, read-only effective value), backed
   by a `ConfigField.store` attribute that names the file a value belongs to (`STORE_ENV` or `STORE_PROJECT`).
   The branch is a picker (`KIND_BRANCH`) fed by `list_branches()` — the local branches plus the ones that
   exist on `origin`, read once when the screen opens. A value the checkout does not have yet is kept as an
   option instead of being dropped by the widget, and the explicit empty choice means "fall through".
   `F2` writes the project YAML first, then the `.env`: if the YAML write fails, nothing is written anywhere
   and every edit stays pending. Reset drops the key from the YAML instead of writing a value.

8. **The project file controls the PR target only.** The AI description is still produced from a diff against
   the detected default branch. Local full review (`-f`), the MCP diff tools and the flag-based `check` path
   keep their own base. This is deliberate debt, not an oversight: making the diff base project-local changes
   what every AI prompt sees, and is a separate decision.

9. **`PR_DEFAULT_BASE` survives** as the machine-wide fallback and was relabelled **Global Default Base Branch**,
   because "the default base branch" no longer has a single answer. The seed and the resolver read it from the
   process environment first and from `~/.gitpr/.env` when it is absent, because both run before
   `load_dotenv()` — and the `config` subcommand never calls it. A variable that is present but empty means
   "no global default": it overrides the file, the same rule `load_dotenv(override=False)` gives everywhere
   else.

10. **The target may not be the branch checked out.** `verify_remote_base()` checks it before the remote ref, raising
    `CurrentBranchError` — a narrower `BaseBranchError` — so the CLI can tell "this pull request would target itself"
    apart from "the ref is missing". The pickers never offer the current branch: `gitpr config` filters it out of
    `list_branches()` and refuses an edit that would write it, while keeping a stored value that already names it
    visible and labelled, because being on the target branch is a normal state of a checkout and blocking unrelated
    saves over it would make the screen unusable. The publish path is the hard stop: after resolving the target and
    before publishing, an interactive run (`not --quiet`, stdin a tty) with no `--base` opens `BaseBranchPromptApp`,
    writes the chosen branch to the project file and resolves again. Anything else — `--quiet`, a non-interactive
    stdin, an explicit `--base` — keeps the error. `--base` is deliberately not rewritten: it is a choice for this
    run, not stale configuration, and silently changing the repository's file to satisfy a flag would hide the
    mistake for every later run.

## Consequences

- A team versions one file and every clone, CI job and agent targets the same branch.
- A repository whose default is `master` gets `main` in its seeded file (Q9), so the first publish fails until
  the file is edited — accepted, mitigated by the fail-fast message and the versioning hint. Seeding with the
  detected default instead was rejected: it would silently pin `master` into a file the user never asked for.
- One more file appears in `git status` on the first run. Teams that do not want it can ignore it or delete it;
  the resolver simply falls through, and the seed re-creates it on the next run.
- The `ConfigApp` is now a two-store editor. `_build_plan` splits its output by `ConfigField.store`; adding a
  third store later would repeat that split, which is the point at which a per-store save backend is worth
  extracting.

## Alternatives rejected

- **Only `PR_DEFAULT_BASE`.** It is exactly the global default that caused the problem, and it cannot be
  versioned with the project.
- **`.gitpr/skill/`-style discovery or a file at the repository root.** Root-level clutter, and the skill folder
  is a download target with different ownership rules.
- **`GITPR_CONFIG` pointing at an arbitrary path.** Two users of the same checkout would have different targets,
  and the file would not be the repository's.
- **Seeding on `--install` only.** A user who never runs `--install` would never see the file.
- **Blocking the TUI save on a missing remote branch.** It would make the screen unusable on a branch that is
  about to be pushed; the CLI already refuses at publish time.
- **Falling back silently to `origin/HEAD` when the target is the current branch.** It would publish to a branch
  nobody chose, and the project file would keep the wrong value, so the next run would fail the same way.
