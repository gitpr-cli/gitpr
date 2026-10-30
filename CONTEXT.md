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
