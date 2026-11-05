# GitPR

GitPR is a Python CLI that automates pull requests, commits, code reviews and
issues with AI. It is distributed only through PyPI, so an installed release
must not keep running once a newer one has been published.

## Language

**Update gate**:
The rule that an installed GitPR refuses to run while a newer release is
published on PyPI.
_Avoid_: version check, version lock, auto-update

**Update check**:
The act of asking PyPI which release is currently published. It can be muted by
configuration, and a check that gets no answer never blocks.
_Avoid_: version verification, ping

**Release cache**:
The remembered answer of the update check together with the moment it was
obtained.
_Avoid_: update file, daily cache

**Freshness window**:
The rolling period during which a remembered release answer may be reused
instead of asking PyPI again.
_Avoid_: cache day, TTL

**Interactive run**:
A run attached to a terminal at both ends that is allowed to stop and ask the
user. Scripts, pipes, hooks and the MCP server are never interactive.
_Avoid_: CLI mode, TTY run

**Stage selector**:
The modal screen (`StageFilesScreen`) that presents files outside the Git staging
area and allows the user to selectively add them (`git add`) to the index before
generating a commit or pull request.
_Avoid_: file picker, stage chooser, unstaged dialog

**Commit flow**:
The interactive sequence triggered by `gitpr -c` (or during PR publication) that
coordinates unstaged file selection, AI commit message generation, review/editing
in a modal, and commit execution with animated progress.
_Avoid_: commit wizard, auto-commit script, commit generator

**PR target base**:
The branch the forge is asked to merge the pull request into — resolved from
`--base`, the project configuration file, `PR_DEFAULT_BASE`, the detected
`origin/HEAD` or `main`. It must exist on `origin` and must differ from the branch
checked out.
_Avoid_: base branch, merge target, default branch

**Release workflow**:
The GitHub Actions workflow triggered by version tags (`v*`) that validates,
builds, publishes the Python package distribution to PyPI and creates the
corresponding GitHub Release.
_Avoid_: deploy script, publish job, release action

**Trusted publishing**:
The OpenID Connect (OIDC) authentication mechanism between GitHub Actions and
PyPI that exchanges short-lived cryptographic tokens without storing long-lived
API tokens or passwords in repository secrets.
_Avoid_: PyPI token, secretless auth

**Diff base**:
The branch the current branch is compared against to build the diff sent to the
AI. It is a different value from the PR target base and today is still the
detected default branch.
_Avoid_: base branch

**Project configuration file**:
`.gitpr/conf/gitpr.config.yml` at the repository root, versioned with the project.
It holds settings that belong to the team, starting with the PR target base, as
opposed to the machine-wide `~/.gitpr/.env`.
_Avoid_: config file, .env

**Self-target**:
A PR target base equal to the branch checked out. It is refused before any
publication, and an interactive run offers to replace it in the project
configuration file.
_Avoid_: same branch, self-PR

**Embedded security ruleset**:
The immutable secret-scanning rule catalogue (`sec-*`) shipped inside the GitPR
Python package, executed by the static linter across all diff lines regardless
of file extension.
_Avoid_: security plugin, secret scanner, linter pack

**Read-back**:
The list of reviewer logins the forge reports as actually attached to a pull
request after a reviewer request. An empty read-back means the request was
accepted but nobody was attached. A forge that cannot report it means the
attachment cannot be verified, which is never a failure.
_Avoid_: attach result, confirmation, ack

**Unusable baseline**:
The baseline file a flow that enforces the baseline cannot apply: missing when
required, tampered with, ill-formed, or carrying a checksum that diverges while
the checksum guard is on. Such a flow stops rather than classify every legacy
finding as new.
_Avoid_: broken baseline, corrupt baseline, invalid baseline

**Package version**:
The semantic release identifier (PEP 440) of the GitPR distribution on PyPI,
defined exclusively in `src/updater.py::__version__` as the canonical single
source of truth. It is surfaced by `gitpr --version`, checked by the update
gate, and enforced by release workflows and agent guidelines.
_Avoid_: tool version, code version, script version

**Language asset version**:
The schema and revision identifier (`__lang_version__`) of the localized dictionary
files under `langs/` and remote templates, versioned independently of the package version.
_Avoid_: lang version, translation release, dictionary version

**Hook script version**:
The version identifier (`__scripts_version__`) of the Git hook shell scripts
installed into `.git/hooks/`, versioned independently of the package version.
_Avoid_: hook version, git script version

**Issue registry**:
The local, unversioned record of the last issue created with `gitpr -is`, kept at
`.gitpr/conf/github.yml`, so the next pull request can offer to close it. It is
state of the machine, not project content, and holds no credentials.
_Avoid_: issue cache, issue log, github.yml state

**Closing line**:
The pull request body line (`close #N` on GitHub) that tells the forge to close
the tracked issue when the pull request is merged. It is forge syntax, not a
label: the issue is named by the line itself.
_Avoid_: auto-close keyword, issue reference, fix line

**Close issue decision**:
The in-memory outcome of offering to close the tracked issue: the closing line
and the issue it names, present only when the issue is still open and the user
accepted. It is not the pull request body itself — the line becomes part of the
description only when the body is assembled.
_Avoid_: close prompt result, autoclose flag


**Smart Excludes**:
The pathspec-based filtering engine that automatically excludes noise (lockfiles,
minified assets, generated artifacts, binary assets) and documentation prose from the git diff
before it is sent to the AI. Composed of three layers: Core Exclusions (global),
Documentation Exclusions (global), and Project-Local Exclusions (`.gitpr/conf/gitpr.smart-excludes.json`).
_Avoid_: diff ignore, ignore patterns, gitignore filter

**Binary hunk guard**:
The post-diff safeguard that detects patch sections whose hunks carry binary byte
streams decoded as `U+FFFD` replacement characters and collapses their hunks into
a standard binary-diff marker before analysis, while preserving legitimate
non-UTF-8 legacy text.
_Avoid_: replacement stripper, U+FFFD filter, binary sanitizer

**Seeded configuration field**:
A configuration variable declared in the schema that is auto-written to `~/.gitpr/.env`
on first run with its default value if absent from the environment.
_Avoid_: default env entry, auto-populated key, config constant

**CI Check**:
The unified pipeline command (`gitpr check`) that orchestrates static analysis,
secrets scanning, risk evaluation, baseline suppressions, and optional AI review
to produce standard machine-readable artifacts and deterministic exit codes.
_Avoid_: check mode, CI runner, CI linter

**Legacy CI action contract**:
The previous GitHub Action workflow contract where `action.yml` sequentially executed
discrete commands (gitpr --linter followed by gitpr --fullreview), generated an
unclassified *_PR_FULLREVIEW.txt text artifact in the workspace, and required manual
step-summary concatenation. Replaced by the unified CI Check pipeline producing
SARIF/JSON/JUnit artifacts and deterministic exit codes.
_Avoid_: old action, linter action, legacy review runner

**Marketplace publication workflow**:
The GitHub Actions workflow (`.github/workflows/extension.yml`) triggered by `ext-v*`
tags or manual dispatch that tests, packages, and publishes the GitPR editor extension
to the Visual Studio Marketplace and Open VSX Registry.
_Avoid_: extension deploy script, marketplace action, vsce pipeline

**Extension release tag**:
The semantic version tag prefixed with `ext-v` (such as `ext-v0.1.0`) that triggers
the marketplace publication workflow and must strictly match `version` in
`extensions/vscode/package.json`.
_Avoid_: extension tag, vsix tag, marketplace version

**Fail-fast secret check**:
The strict gate inside the marketplace publication workflow that halts execution
immediately with a fatal error if either `VSCE_PAT` or `OVSX_PAT` is missing on a
release tag run, preventing phantom releases.
_Avoid_: secret check, env fallback, optional token skip
