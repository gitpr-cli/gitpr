# Technical Documentation: Policy Packs (`gitpr policy`)

A **Policy Pack** is a versioned YAML manifest that carries a team's whole quality policy — review skills, linter rules, severity overrides, critical paths, risk weights and the PR/commit conventions — as one file a repository can adopt, review and version alongside its code. `gitpr policy` records *which* pack a repository follows and is the only thing that decides *what* that pack changes.

Until now each of those surfaces was configured somewhere else: `.gitpr/skill/.gitpr.review.md`, `.gitpr/skill/.gitpr.linter.yml`, `.gitpr/skill/gitpr.risk.yml`, `~/.gitpr/.env`. Nothing tied them together, so "we follow the Acme policy" was a convention rather than something the tool could check. With a pack it is a line in a file under version control.

---

## 1. Overview

Policy Packs operate across three surfaces:

1. **The `gitpr policy` group**: seven commands to list, validate, show, adopt, install, scaffold and drop a policy. `list`, `validate` and `show` only read; `use`, `install`, `init` and `off` write and ask before they do.
2. **Every later command in the repository**: once a pack is active, `gitpr -r`, `gitpr -f`, `gitpr -c`, `gitpr` (PR description), `gitpr -l` and `gitpr risk` all run under it, without any of them taking a new argument.
3. **`.gitpr/policy.lock.yml`**: the file that records the decision. It names the pack, its version, its source and a checksum per pack, so a teammate gets the same policy from the same commit.

### 1.1 Command Reference

```bash
gitpr policy list                        # The packs on this machine and the one in force
gitpr policy validate gitpr/laravel-quality   # Schema, compatibility, skills, rules, dependencies
gitpr policy show                        # The effective policy, with the origin of every value
gitpr policy use acme/team-policy@1.0.0  # Pins a pack, writing .gitpr/policy.lock.yml
gitpr policy init --stack laravel        # Suggests and activates the official pack for the stack
gitpr policy install ./our-policy        # Copies a local directory into ~/.gitpr/policies
gitpr policy off                         # Stops following the pack
```

| Command | Writes | Description |
|---|---|---|
| **`list`** | — | The active pack (with its dependency graph) and every pack found on this machine |
| **`validate <path\|name[@range]>`** | — | Validates a pack and reports what it does. Non-zero exit when the pack is invalid, so CI can gate on it |
| **`show`** | — | The effective policy in force, with the provenance of every field and the precedence order that produced it |
| **`use <name>[@<version>]`** | `.gitpr/policy.lock.yml` | Pins a pack for this repository. Replaces whichever pack was active |
| **`init [--stack laravel\|vue\|php\|node]`** | `.gitpr/policy.lock.yml` | Detects the stack from the project and activates the matching official pack |
| **`install <path> [--force]`** | `~/.gitpr/policies/` | Validates a pack in a local directory and copies it into the user's pack store. There is no registry and no download |
| **`off`** | removes `.gitpr/policy.lock.yml` | Stops following the pack. The pack and the overrides file are kept |

Every writing command accepts `--yes`, which skips the confirmation prompt but **not** the checks behind it. Without a terminal and without `--yes`, a writing command fails with the instruction instead of blocking on a prompt nobody will read — which is what makes the group safe to call from a hook or a CI job that forgot the flag.

### 1.2 Where a pack may come from

Three sources, searched in this order:

| Order | Source | Location | `source` in the lockfile |
|---:|---|---|---|
| 1 | The repository itself | `<repo>/.gitpr/policies/<name>/` | `local_path` |
| 2 | The user's store | `~/.gitpr/policies/<flat-name>/` | `installed` |
| 3 | What GitPR ships | `src/policy_packs/<name>/` | `bundled` |

An installed pack lives in a **flat** directory — `acme/team-policy` is stored as `acme__team-policy` — because a namespace is part of a pack's identity, not of the filesystem's layout. A pack versioned inside the repository is found by path instead, which is what lets a team adopt a policy no one has installed.

Nothing is downloaded. A pack is text on disk; resolution reads it, hashes it and composes it.

---

## 2. The Manifest

A pack is a directory holding `policy.yml` and whatever assets the manifest declares:

```
acme__team-policy/
├── policy.yml          # the manifest — the only required file
├── linter.yml          # declared by linter.rules_file
├── README.md           # carried along; part of the pack, read by nobody
└── CHANGELOG.md
```

### 2.1 Schema

The schema is **closed**: an unknown key is an error, not a warning. A typo like `test:` instead of `tests:` has to fail loudly, because the alternative is a policy that silently does nothing while its name still appears in the output.

| Key | Required | Type | Meaning |
|---|---|---|---|
| `schema_version` | ✅ | int | Manifest schema version. Currently `1` |
| `name` | ✅ | str | `namespace/name`. Path traversal is refused |
| `version` | ✅ | str | The pack's own version |
| `min_gitpr_version` | ✅ | str | `SpecifierSet` range, e.g. `">=1.3.0"`. Validated against the running GitPR |
| `description` | — | str | Free text, shown by `policy list` |
| `license` | — | str | Free text |
| `authors` | — | list[str] | Free text |
| `extends` | — | list | Dependencies: `[{name, version}]`. `version` is a range |
| `skills` | — | map | `skills.<type>.additional_context` — text prepended to that skill's prompt |
| `linter` | — | map | `rules_file`, `severity_overrides` |
| `risk` | — | map | `critical_paths`, `test_patterns`, `weights`, `thresholds` |
| `pr` | — | map | `required_sections` |
| `commit` | — | map | `allowed_types` |
| `protected_paths` | — | list[str] | Declared for the prompt, not enforced by an engine |

### 2.2 A complete example

```yaml
schema_version: 1
name: acme/team-policy
version: 1.0.0
description: The Acme house rules for PHP services.
min_gitpr_version: ">=1.3.0"
license: MIT
authors:
  - Acme Platform

extends:
  - name: acme/base-policy
    version: ">=1.0.0 <2.0.0"

skills:
  review:
    additional_context: |
      Money is an integer in minor units. A float in a monetary field is a bug
      regardless of how it got there.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  critical_paths:
    - app/Services/**
  test_patterns:
    - spec/**
  weights:
    database_migration: 25

pr:
  required_sections:
    - Business impact
    - Rollback plan

commit:
  allowed_types:
    - feat
    - fix
    - chore

protected_paths:
  - config/**
```

### 2.3 The sections

**`skills`** — one block per skill type. The valid types are the ones GitPR knows: `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `release`, `fix`, `tests`, `explain`, `mentor`. An unknown type is refused at parse time; a pack cannot invent a skill, because nothing would read it. The text is concatenated with the other packs' contributions and attached to the prompt as system instructions, which is why it also travels into the cache key — see §4.3.

**`linter.rules_file`** — the name of a YAML rules file **inside the pack directory**. A path that escapes the directory is refused, so a pack cannot point at `/etc/passwd` or at a file above itself. The rules are merged into the catalogue by `name`, with the project's own rules winning over the pack's.

**`linter.severity_overrides`** — changes the level of a rule that already exists, after every catalogue has been merged. `level` is `error` or `warning`. **Lowering a rule from `error` to `warning` requires a `reason`** — an override that weakens the gate is a decision somebody made on purpose, and the reason travels with it into `policy validate`, `policy show` and the review report. Hardening a rule needs no justification. An override naming a rule that does not exist anywhere in the final catalogue is an **error**: silently doing nothing would leave the team believing a rule was relaxed when it was not.

**`risk.critical_paths` / `risk.test_patterns`** — unioned across packs, in precedence order. `test_patterns` teaches the risk engine which files count as tests in *this* project's layout (`spec/**`, `**/*Cest.php`), which is what makes `TEST_PRESENT` fire for a repository whose test directory is not called `test/` or `tests/`.

**`risk.weights` / `risk.thresholds`** — a single value, not a list. Two packs that are not related by `extends` disagreeing on the same weight is a **validation error** naming both of them; a dependency and its dependent disagreeing is refinement, and the dependent wins.

**`pr.required_sections`, `commit.allowed_types`, `protected_paths`** — nothing in the code reads these. They exist to be *said* to the model, which is why they are rendered into the `pr` and `commit` skill contexts as prompt text rather than left as data.

### 2.4 `extends`

A pack may depend on other packs. The graph is resolved in **topological order** — dependencies first, root pack last — so a dependency's values are applied before the pack that builds on them. A cycle is refused with the chain in the message, because "there is a cycle" without the path is not actionable.

One root pack per repository. `gitpr policy use` **replaces** the previous choice rather than adding to it; the graph below the root is reached through `extends`, which keeps the precedence ladder a line rather than a lattice.

---

## 3. Precedence

Lowest to highest. A value with a higher number overrides one with a lower number.

| # | Layer | Written by |
|---:|---|---|
| 1 | GitPR internal defaults | the code |
| 2 | Dependency packs | `extends`, in topological order |
| 3 | The root pack | `.gitpr/policy.lock.yml` |
| 4 | `.gitpr/policy.overrides.yml` | the repository |
| 5 | Local project configuration | `.gitpr/skill/*`, `.gitpr.linter.yml` |
| 6 | CLI flags | `--base`, `--provider`, … |
| 7 | Environment variables | `GITPR_*` |

The linter catalogue is merged in its own order, because its layers are not the same ones:

**embedded security ruleset → pack rules → project rules → global plugins → severity overrides**

Severity overrides are applied **last**, against the final catalogue, because only there is the set of known rule names complete — which is what lets an override naming a typo fail instead of quietly doing nothing.

### 3.1 The lockfile

`gitpr policy use acme/team-policy@1.0.0` writes:

```yaml
schema_version: 1
root:
  name: acme/team-policy
  version: 1.0.0
  source: installed
  checksum: 4f449708ac83901bffb4275e8d6d7c880154022bca0382962519c2270cb1842f
packs:
  - name: acme/base-policy
    version: 1.0.0
    source: installed
    checksum: 9c1f…
  - name: acme/team-policy
    version: 1.0.0
    source: installed
    checksum: 4f44…
```

The file is meant to be **committed**. A pack inside the repository is recorded by a repository-relative POSIX `path` as well, so a teammate reads it from the same place instead of from a copy of their own; a pack from the user's store is recorded by name only, because where it lives is a machine-specific detail.

### 3.2 Overrides

`.gitpr/policy.overrides.yml` is the repository speaking about itself, one level below the CLI flags. It takes the `{add, remove}` form for lists, so dropping a protected path or a required section is a line in a diff rather than an absence:

```yaml
protected_paths:
  add:
    - legacy/**
  remove:
    - .env.example

risk:
  weights:
    large_diff: 10
```

---

## 4. Integrity & Failure Behaviour

### 4.1 The checksum

Each pack's checksum is SHA-256 over `policy.yml` plus every asset the manifest declares, computed when the pack is activated and re-verified on every run. An edited asset is a different policy, and a different policy was not the one the team agreed to.

Note that the checksum is byte-exact: a pack versioned inside the repository and rewritten by `core.autocrlf` on checkout will abort with a mismatch. `gitpr policy use` on a pack with an LF-normalised working copy — or `.gitattributes` pinning the pack directory — settles it.

### 4.2 The three aborts

Resolution **aborts** rather than degrading in exactly three cases:

| Failure | Why it aborts |
|---|---|
| A pack is no longer on disk | Its rules are gone; the output would still carry the policy's label |
| A pinned version vanished (after an upgrade, or a `use` elsewhere) | The version the team agreed to is not the one that would run |
| A checksum no longer matches | The content changed since activation |

Half-keeping a promise is worse than not keeping it, because the review, the linter output and the risk score would all still claim to be running under the policy. Each abort names the pack, what happened, and the command that repairs it.

`strict=False` is the one escape hatch, and only the `gitpr policy` commands use it — they are the tool that repairs a broken lockfile, so they have to be able to run while one is broken.

### 4.3 Cache scope

GitPR caches AI answers by MD5 over the prompt. The skill context is a **separate argument** (`instrucao_sistema`) and is not part of that hash — so without a fix, activating a pack over an already-cached diff would change nothing at all, and the label would be a lie.

The fix is the cache scope. When a pack is active, `::policy::<name>@<version>::<checksum>` is appended to the cache key, which means an activated pack invalidates the affected cache entries and two different packs never share an answer. Without a pack the scope is the empty string, so nothing changes.

### 4.4 Guarantees

- **No network, ever**: a pack is local by design. Resolution reads a lockfile, hashes files and composes text.
- **No arbitrary execution**: `policy validate` runs no subprocess, and validation is offline and side-effect free. A pack is text somebody else wrote, and the command that inspects it runs nothing it contains.
- **No secrets in a manifest**: a manifest matching one of the embedded secret-scanning rules is refused at parse time, using the same ruleset the linter runs rather than a second scanner that could drift from it.

---

## 5. Configuration

| Key | Type | Default | Description |
|---|---|---|---|
| `GITPR_POLICY_ENABLED` | bool | `true` | Reads and applies the lockfile. Turning it off makes every command behave as if the repository had no pack, without touching the lockfile |
| `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` | int | `12000` | Ceiling on how much context a pack may add to one prompt. Beyond it, contributions are dropped from the lowest-precedence pack first and the drop is reported as a warning |

Which pack is active is deliberately **not** a configuration key: it belongs to the repository, not to the machine, so it lives in the lockfile where it can be reviewed and versioned with the code it applies to.

---

## 6. Bundled Packs

| Pack | Chain rules | What it is for |
|---|---:|---|
| `gitpr/php-security` | 8 | PHP security baseline: SQL interpolation, `eval`, weak password hashes, foreign `unserialize`, dynamic includes, `extract()` from input, wildcard CORS, insecure session cookies |
| `gitpr/laravel-quality` | 7 (+8) | Laravel quality gate: authorisation, mass assignment, transactions, N+1, reversible migrations, queues, personal data. **Extends `gitpr/php-security`** |
| `gitpr/node-quality` | 7 | Node services: floating promises, input validation, unhandled states, dependency hygiene, configuration and secrets |
| `gitpr/vue-quality` | 6 | Vue 3 components: props and emits, reactivity, side-effect cleanup, async states, accessibility, component size |

Each one carries review context that a general-purpose reviewer does not have (what a `down()` that does not reverse its `up()` costs, why a job dispatched inside a transaction can run before the row is committed), critical paths and test patterns for its layout, and PR/commit conventions. They are deliberately small and opinionated: they add what the defaults do not already cover, rather than restating them.

`gitpr policy init` picks one from the project's own markers — `composer.json` + `artisan` for Laravel, `package.json` + Vue for Vue, and so on — most specific first.

---

## 7. Adopting a Policy in a Team

```bash
# One person, once: validate and install the pack
gitpr policy install ./our-policy --yes

# In the repository: pin it and commit the decision
gitpr policy use acme/team-policy@1.0.0
git add .gitpr/policy.lock.yml && git commit -m "chore: adopt the Acme quality policy"

# Everyone else: nothing to install if the pack is committed with the repo
gitpr policy show
```

Three ways to share a policy, depending on how much the team wants to depend on a machine:

- **A pack inside the repository** (`.gitpr/policies/<name>/`) — versioned with the code, no install step, and the lockfile records the relative path. The best fit for a policy that is the repository's own.
- **An installed pack** (`~/.gitpr/policies/`) — one copy for every repository on the machine. Each teammate installs it from the same source; the lockfile records the name and version.
- **A bundled pack** — read straight from what GitPR ships. Nothing to distribute, and a new GitPR release can carry a new version of it.

The pack's own lifecycle is separate from GitPR's: bump `version` in the manifest and the checksum changes, which is a diff in the lockfile, which is a review. That is the whole point of pinning.
