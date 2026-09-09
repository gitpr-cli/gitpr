# Technical Documentation: Release Notes & Changelog (gitpr release)

`gitpr release` is the first subcommand of the GitPR CLI and generates the changelog / release notes of the current repository ("release notes" and "changelog" name the same flow). One invocation scans the commits collected between an origin tag and `HEAD`, classifies them by Conventional Commits, suggests a semantic version bump, optionally adds an AI executive summary, and prepends a new version section to the repository changelog. Generation is purely local by default — nothing is published and no local tags or version files are touched; `--publish` goes further and creates the release on the configured forge after an explicit confirmation.

---

## 1. Overview

The root command keeps all its legacy options unchanged (`-r`, `-c`, `-is`, `-l`, ...) — the subcommand is an addition, not a rewrite. Run without flags, `gitpr release` performs the local flow: collect the commit range, classify, suggest the version, generate the section (optionally with an AI summary), write `CHANGELOG.md`, save the per-run artifact and print a terminal preview capped at 40 lines (`… and N more lines` when longer — v1 has no interactive TUI preview). If a version section already exists in the changelog, the command aborts instead of duplicating it (see Section 6, JSON Mode and Idempotency).

### 1.1 Command Reference — `gitpr release`

All options of the subcommand, as shown by `gitpr release -h` (or `--help`):

```bash
gitpr release
gitpr release --version 2.0.0
gitpr release --publish
```

| Option | Description |
| --- | --- |
| **`--since <tag>`** | Range origin: tag or reference from where commits are collected (default: the latest reachable tag, or the first commit when no tag exists) |
| **`--version <x.y.z>`** | Target version of the release (default: automatic semantic bump suggestion) |
| **`--publish`** | After generating, publish the release on the configured forge (asks for confirmation) |
| **`--draft`** | Create the release as a draft on the forge (GitHub). Only applies together with `--publish`; GitLab has no draft concept |
| **`--format {markdown\|json}`** | `json` prints the full result to stdout without touching files or publishing (default: `markdown`) |
| **`--force`** | Regenerate the version section when it already exists in the changelog (idempotency override) |

| Characteristic | Description |
| --- | --- |
| **Data source** | Commits of the range `since..HEAD`, merge commits excluded |
| **AI summary** | Automatic when an API key is configured (disable with `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Files written** | New section in `CHANGELOG.md` + `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` artifact |
| **Published** | Nothing — local generation is the default |
| **Local tags / version files** | Never touched (read-only: version suggestions come from git tags only) |

---

## 2. Release Range and Version Suggestion

### 2.1 Commit Range — `--since <tag>`

A release always covers the commits from an origin up to `HEAD`. The origin defaults to the latest reachable tag, and the end of the range is always `HEAD` — generating between two older tags is not supported in v1. Merge commits never reach the changelog: they are excluded at collection time.

```bash
# Default: from the latest reachable tag to HEAD
gitpr release

# Explicit origin: everything since v1.0.0
gitpr release --since v1.0.0
```

| Characteristic | Description |
| --- | --- |
| **Default origin** | Latest reachable tag (`git describe --tags --abbrev=0`) |
| **No tag in the repository** | First release: the range starts at the repository's first commit |
| **Merge commits** | Excluded from the collection |
| **Range end** | Always `HEAD` |

### 2.2 Semantic Version Suggestion

Without `--version`, the engine suggests a bump from the classified commits, following semantic versioning:

| Commits in the range | Suggested bump |
| --- | --- |
| Any **breaking** commit | **MAJOR** |
| No breaking commit, at least one **feature** | **MINOR** |
| Only fixes, chores or other changes | **PATCH** |

The suggestion is read-only: it comes exclusively from git tags — the engine never reads version files (such as `pyproject.toml`) and never creates local tags. A `v` prefix on the last tag is preserved (`v1.2.3` suggests `v1.2.4`, written as `## [v1.2.4]`). When there is no previous semantic version tag, no suggestion exists — for a first release, `--version` becomes mandatory to publish.

When the version comes from the suggestion, the command asks for confirmation before the AI call: `❓ Use the suggested version {version}?` (accepting is the default). The prompt is skipped with an explicit `--version`, in `--format json`, in quiet or non-interactive terminals, and with `GITPR_RELEASE_AUTO_BUMP=false` (which forces an explicit `--version` on every run).

### 2.3 Explicit Version — `--version <x.y.z>`

`--version` overrides the suggestion (no confirmation prompt) and is the only source of the tag published on the forge. Pass a plain `x.y.z` — the `v` prefix is not required.

```bash
gitpr release --version 2.0.0
gitpr release --since v1.0.0 --version 1.1.0
```

---

## 3. Changelog Structure and Files

### 3.1 Commit Classification

Every commit of the range is parsed by Conventional Commits rules: `type`, optional `scope`, breaking markers (`!` after the type/scope or a `BREAKING CHANGE:` line in the body) and the squash-merge PR tail `(#123)`. Commits that do not follow the convention are never rejected — they land in **OTHER** with a warning, and duplicates of the same PR are recognized and deduplicated.

| Category | Trigger | Heading (English fallback) |
| --- | --- | --- |
| **BREAKING** | Breaking marker on any type (`feat!`, `refactor!`, `BREAKING CHANGE:` ...) | `⚠️ Breaking Changes` |
| **FEATURE** | `feat:` | `✨ Features` |
| **FIX** | `fix:` | `🐛 Fixes` |
| **PERFORMANCE** | `perf:` | `⚡ Performance` |
| **DOCS** | `docs:` | `📚 Docs` |
| **REFACTOR** | `refactor:` | `♻️ Refactoring` |
| **CHORE** | `chore:` | `🔧 Chores` |
| **OTHER** | Anything else (non-conforming or unknown types) | `📦 Other Changes` |

The category blocks follow the fixed order FEATURE, FIX, PERFORMANCE, DOCS, REFACTOR, CHORE, OTHER (empty blocks are skipped). Breaking commits appear only under `⚠️ Breaking Changes`, never duplicated inside their own category. Heading labels go through the GitPR localization engine, so the generated file follows the interface language, with English as fallback.

### 3.2 Version Section Anatomy

One release produces one version section: the header `## [x.y.z] - date`, an optional `### Summary`, one block per present category, and a `**Contributors:**` footer with the unique author names (deduplicated by e-mail, sorted). Each entry is rendered as `subject (short hash)`, with the commit scope appended when present:

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 (b2c3d4e) — core

### ✨ Features
- add the gitpr release subcommand (a1b2c3d) — cli
- publish releases on GitLab (#567) (d4e5f6g) — scm

### 🐛 Fixes
- handle repositories without tags (f6a7b8c) — release

**Contributors:** Ana Souza, Bob Smith
```

The section is prepended to `CHANGELOG.md` — the file is never rewritten from scratch and previous sections are preserved. When a `## [x.y.z]` section for the same version already exists, the command aborts with exit code 1 (see Section 6, JSON Mode and Idempotency); it never duplicates and never overwrites silently.

### 3.3 Files Written

| Artifact | Path | Notes |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Repository root by default — the deliberate exception to the `.gitpr/reports/` convention, because it is a public, committable file. Override with `GITPR_RELEASE_CHANGELOG_PATH` (relative paths resolved against the repository root) |
| **Release notes artifact** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Written on every markdown run, best-effort: a save failure only warns and never fails the command. Name template via `OUTPUT_FILE_NAME_RELEASE` |
| **Terminal preview** | — | Printed after saving, up to 40 lines |

---

## 4. AI Executive Summary

The optional `### Summary` paragraph is generated by the AI from the classified commits of the range, and written in the current interface language.

### 4.1 First-Run Skill Template — `.gitpr.release.md`

```bash
# First run in markdown mode downloads the template (language-aware, never overwriting)
gitpr release
```

On the first run in markdown mode, the CLI downloads the `.gitpr.release.md` skill template from the project templates. The download respects the current interface language (remote variants such as `gitpr.release.pt_br.md` are stored locally as `.gitpr.release.md`), never overwrites an existing local file and never fails on a network error — the run proceeds with the built-in persona. The download is skipped entirely in `--format json`, which is stdout-only. The file is loaded as the AI's system instruction (persona: **Release Manager**, strict JSON contract) — edit it locally to customize the executive summary. See the [Skills and Templates documentation](skill-template.md) for the general mechanism.

### 4.2 Generation and Graceful Degradation

Ranges with more than 200 commits are summarized in batches (Map-Reduce, with a notice such as `📦 Large commit range detected!`), and responses go through the standard GitPR MD5 cache, so unchanged runs do not repeat AI calls. Two notes: the cache is keyed on the prompt — editing `.gitpr.release.md` does not invalidate cached summaries — and the summary always uses the same AI infrastructure as the other GitPR commands (configured provider, JSON output, automatic retry). See the [AI Providers documentation](providers-ia.md).

The summary never blocks the command: with no API key configured, or when the AI call fails, the command warns (`AI summary failed: changelog generated without a summary.`) and generates the section with the classified lists only. `GITPR_RELEASE_AI_SUMMARY=false` disables the summary entirely.

---

## 5. Publishing to the Forge

### 5.1 Confirmation and Guardrails — `--publish`

Publishing only happens in the markdown flow, after the local generation and preview, behind an explicit confirmation: `❓ Publish release {version} on {provider}?` — declining (the default) keeps the changelog and prints `⏭️ Publication skipped — the changelog was generated locally.` The release body sent to the forge is the generated section without the `## [x.y.z] - date` heading (the release title carries the version).

```bash
gitpr release --publish
gitpr release --since v1.0.0 --version 1.2.0 --publish
```

Guardrails: without a git `origin` remote the command refuses to publish (`❌ No git remote 'origin' found. Cannot publish the release.`, exit code 1); combined with `--format json`, `--publish` only warns that it is ignored (`⚠️ --format json is stdout-only: --publish is ignored.`) — JSON mode never publishes; after a plain local run, the CLI hints `ℹ️ To publish this release on the forge, run again with --publish.`

### 5.2 Supported Forges

Publishing targets the forge configured through the SCM settings (`gitpr --init` or `GITPR_SCM_PROVIDER`). See the [Multi-Forge SCM documentation](scm-multiforge.md) for the provider setup.

| Forge | Release | Notes |
| --- | --- | --- |
| **GitHub** | Yes | A missing tag is auto-created by the API, pointing at the repository's default branch (not local `HEAD`); drafts honored |
| **GitLab** | Yes | The tag must already exist on the forge; no native draft concept |
| **Bitbucket Cloud** | No | No release API — the command warns and keeps the changelog local for manual publishing |
| **Azure DevOps** | No | No release API — the command warns and keeps the changelog local for manual publishing |

When publishing is not supported, the warning is `⚠️ Release publishing is not supported on {provider}. The changelog was generated locally — publish it manually.`

### 5.3 Drafts — `--draft`

`--draft` only matters together with `--publish` (alone, it warns `⚠️ --draft only applies together with --publish: generating the changelog locally.`). GitHub is the only forge with a draft concept, and by default a GitHub `--publish` already creates a **draft** (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`); pass `--draft` to force a draft when that default was turned off. GitLab has no drafts: a draft request only warns and publishes directly.

```bash
gitpr release --publish --draft
```

---

## 6. JSON Mode and Idempotency

### 6.1 Pure JSON Output — `--format json`

`--format json` is stdout-only, ideal for scripts and CI: it writes nothing (no `CHANGELOG.md` update, no per-run artifact, no skill template download), publishes nothing and never prompts (the version confirmation is skipped). The stdout stream stays clean — warnings travel inside the JSON payload. The output follows the release result: `version`, `previous_tag`, `generated_at`, `summary`, `sections` (one list of classified commits per category), `breaking_changes`, `contributors`, `markdown` and `warnings`.

```bash
gitpr release --format json
```

### 6.2 Existing Section and `--force`

The changelog write is idempotent per version: when the `## [x.y.z]` section of the target version already exists, the command aborts with exit code 1 without changing the file — it never duplicates content and never silently overwrites it. `--force` regenerates and replaces that section (`🔄 Existing section for version {version} regenerated.`); with no existing section, `--force` is a plain addition.

```bash
gitpr release --force
gitpr release --since v1.0.0 --version 1.2.0 --force
```

---

## 7. Environment Variables

The release configuration is read from the global `~/.gitpr/.env` file (dotenv format). Booleans follow the "false disables" convention: unset or any value other than `false` / `0` / `no` / `off` / `n` means enabled — the defaults in the table are active when the variable is not set.

| Variable | Default value | Purpose |
| --- | --- | --- |
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Changelog file; relative paths resolved against the repository root, absolute paths honored |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Enables the AI executive summary; `false` generates the classified lists only |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Enables the automatic semantic bump; `false` requires an explicit `--version` |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | GitHub: `--publish` creates the release as a draft by default |
| `OUTPUT_FILE_NAME_RELEASE` | `{branch}_{datetime}_RELEASE.md` | Name template of the per-run artifact in `.gitpr/reports/release/` |

> **Note:** See also the [Skills and Templates documentation](skill-template.md) for customizing the GitPR AI template files.
