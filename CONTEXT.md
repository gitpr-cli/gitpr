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

**Update check switch**:
The environment switch (`GITPR_SKIP_UPDATE_CHECK`) that mutes the update check
during local checkout development and offline automation. Parsed strictly as a
boolean, only explicit truthy values (`1`, `true`, `yes`, `on`, `y`) disable the
check, while falsey values such as `0` or `false` leave it enabled.
_Avoid_: skip flag, update bypass, disable check, bypass switch

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
The interactive sequence triggered by `gitpr -c` (or during PR publication) in an
interactive run that coordinates unstaged file selection, AI commit message
generation, review/editing in a modal, and commit execution with animated
progress. Non-interactive runs fall back to displaying the suggested message or
injecting it via hook mode without executing a commit.
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

**Runtime project configuration seed**:
The automated runtime creation of `.gitpr/conf/gitpr.config.yml` upon first execution
inside a Git repository, pre-populating it exclusively with the PR target base
branch (`PR_DEFAULT_BASE` or `main`). It is never overwritten once created.
_Avoid_: auto-config, auto-init, wizard file, project seed

**Project configuration seed opt-out**:
The explicit suppression of the runtime project configuration seed via setting the
environment variable `GITPR_SKIP_PROJECT_CONFIG_SEED=true` (or `1`), essential
for CI/CD pipelines enforcing pristine working tree checks and monorepos where
the root file is omitted or managed externally.
_Avoid_: disable-config, skip-init

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
`.gitpr/conf/issue.yml` (with transparent legacy fallback from `.gitpr/conf/github.yml`), so the next pull request can offer to close it across supported forges (GitHub, GitLab, Bitbucket). It is
state of the machine, not project content, and holds no credentials.
_Avoid_: issue cache, issue log, github.yml state

**Closing line**:
The pull request body line (`close #N` on GitHub/Bitbucket, `Closes #N` on GitLab) that tells the forge to close
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

**Granular marketplace gate**:
The non-blocking credential evaluation mechanism in the marketplace publication workflow
that checks each marketplace secret (VSCE_PAT, OVSX_PAT) independently. It publishes to
services with active tokens while emitting informative step notices and summary status
for missing credentials, ensuring official VSIX GitHub Releases are never obstructed by
absent third-party marketplace tokens.
_Avoid_: fail-fast secret check, all-or-nothing check, blocking token validation

**Documentation link**:
A canonical public URL pointing to `https://gitpr.natanfiuza.dev.br/docs/<slug>`
without a `.md` extension or locale suffix in the path. English links carry no
query string; localized links append `?lang=pt_br`, `?lang=pt_pt`, `?lang=es`,
or `?lang=fr` matching the documentation site's language parameter contract.
_Avoid_: raw GitHub doc URL, blob link, localized doc filename URL

**Documentation site fallback**:
The graceful degradation contract of the official documentation website (`https://gitpr.natanfiuza.dev.br/docs/`)
where requests carrying localized query parameters (`?lang=es`, `?lang=fr`, `?lang=pt_br`, `?lang=pt_pt`)
return HTTP 200 with canonical English content whenever a specific localized translation is pending or not
yet published, preventing 404 HTTP errors for users following CLI and README links.
_Avoid_: 404 fallback, missing doc error, broken link


**Latency histogram**:
The distribution of timed ledger executions (`duration_ms > 0`) across fixed
duration buckets, paired with mean, median, and 95th-percentile latency over the
active window.
_Avoid_: time chart, speed graph, duration table

**Token trend**:
The continuous daily time series of token consumption from ledger executions
over the active window, with zero-consumption days explicitly preserved.
_Avoid_: token history, usage sparkline, token graph

**Dashboard chart pane**:
The tab pane in the metrics dashboard dedicated to 2D ASCII visualization of
latency distribution and token consumption time series.
_Avoid_: graph tab, metrics chart screen, visual dashboard tab

**Vertical latency histogram**:
The two-dimensional column chart depicting execution frequency on the vertical
axis against discrete latency buckets on the horizontal axis.
_Avoid_: vertical time chart, bar latency plot, latency graph

**Token time-series chart**:
The two-dimensional grid chart rendering daily token consumption volume against
continuous date intervals.
_Avoid_: token graph, token curve, usage chart


**Project configuration seed**:
The explicit action of initializing repository-level configuration files
(`.gitpr/conf/gitpr.config.yml`, `.gitpr/conf/gitpr.smart-excludes.json`,
and `.gitpr/skill/.gitpr.linter.yml`) with baseline templates via `gitpr seed` or
the setup wizard (`gitpr --install`), idempotently without overwriting existing files
unless explicitly forced. Distinct from machine-wide configuration seeding in
`~/.gitpr/.env` and runtime project configuration seeding.
_Avoid_: init repo, template copy, conf generator

**Blame summary**:
The aggregated count of files with and without blame history during reviewer suggestion
computation (`files_with_blame` and `files_without_blame`), displayed as a single informative
console line when unblamable files (new or binary) are present, replacing per-file warnings.
_Avoid_: blame report, blame log, unblamable list

**Token price rate**:
The cost in currency units per million input or completion tokens configured via
`GITPR_METRICS_PRICE_<MODEL>_INPUT` or `GITPR_METRICS_PRICE_<MODEL>_OUTPUT` in `~/.gitpr/.env`.
_Avoid_: token fee, model cost, pricing multiplier

**Metrics currency**:
The currency code or symbol (`GITPR_METRICS_CURRENCY`, default `USD`) used to label and
calculate financial cost estimates across telemetry surfaces.
_Avoid_: cost unit, price currency, billing symbol
