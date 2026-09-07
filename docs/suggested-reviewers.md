# Technical Documentation: Suggested Reviewers for Pull Requests

When you publish a Pull Request through GitPR's interactive publisher (the default `gitpr` mode), GitPR suggests who should review it: it looks at the people who worked on the code you are changing and proposes up to `GITPR_REVIEWER_SUGGESTION_TOP_N` candidates (3 by default). The suggestions are shown in an editable field of the PR Publisher (TUI) and, on GitHub, they are submitted to the new pull request right after it is created.

The computation is enabled by default and runs only in the interactive publisher flow — never with `--no-edit` or `--no-publish`. It is purely advisory and fully non-blocking: any failure or unsupported situation degrades to a warning and the publishing flow continues unchanged.

---

## 1. How It Works

GitPR does not guess: it attributes real authorship with `git blame`, running over the exact lines your diff added and comparing the base branch with your working tree.

### 1.1 Authorship over the Added Lines

- The input is the same diff GitPR already computed for the PR: base branch vs. working tree (staged changes included), with the smart-excludes applied. The parser consumes that diff text and never re-runs `git diff`.
- Only **added lines** (`+`) count for authorship. Removed lines and context lines are ignored.
- Lines not committed yet — "Not Committed Yet", blame hash `0000…` — are skipped: they are your own work in progress.
- The blame runs on the working tree (no revision), so it matches the diff exactly, staged and new files included.
- Files without usable history (brand new, binary, shallow clones) produce no candidates: a warning is shown and the analysis moves on.

### 1.2 Ranking and Exclusions

Every author found is aggregated per file and line and receives a score:

| Factor | Weight | Meaning |
| --- | --- | --- |
| Lines touched | 50% | Share of the diff's added lines authored by the person |
| Files touched | 30% | Share of the changed files where the person has authorship |
| Recency | 20% | `1 / (1 + days / 90)` — a half-life of 90 days since the last touch |

The author of the PR is always excluded, even when they dominate the diff. **Bots** are excluded too: any identity whose name or email local-part ends in `[bot]` or whose email is on the known-bots list (Dependabot, GitHub Actions, etc.). The `users.noreply.github.com` domain is never treated as a bot — it is the standard email of real GitHub users. Additional people can be excluded through `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. Ties are broken by lines touched, and the result is truncated to the configured `top_n` (default 3).

---

## 2. Configuration

The feature is enabled by default. Disable it per run with the flag, or globally through the environment:

```bash
gitpr --no-suggest-reviewers        # Disables the computation for this run
```

```bash
# ~/.gitpr/.env — disable globally and tune the ranking
GITPR_SUGGEST_REVIEWERS=false
GITPR_REVIEWER_SUGGESTION_TOP_N=5
GITPR_REVIEWER_SUGGESTION_EXCLUDED=renovate[bot],qa@example.com
```

| Variable | Default | Description |
| --- | --- | --- |
| `GITPR_SUGGEST_REVIEWERS` | `true` | Master switch. Falsy values: `false`, `0`, `no`, `off`, `n` |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | `3` | How many candidates to suggest; invalid or ≤ 0 falls back to 3 |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | *(empty)* | Optional CSV of emails or names to exclude, besides the PR author and bots |

The keys are read from `~/.gitpr/.env` and are never auto-written. `--no-edit` and `--no-publish` never compute suggestions, regardless of the configuration.

---

## 3. Suggested Reviewers in the PR Publisher (TUI)

### 3.1 The Suggested Reviewers Section

In the default interactive flow, GitPR prints a `🔍 Searching for suggested reviewers...` line while the analysis runs, before the PR Publisher opens. When it does, an editable **👥 Suggested Reviewers** section is shown:

- An input field pre-filled with the suggested GitHub usernames, comma-separated. Remove a reviewer by clearing the field; add one by typing.
- A read-only hint below the field explaining each suggestion (lines and files touched, last activity).
- Leaving the field empty submits no reviewers at all.

### 3.2 Publishing

After you confirm with F3, GitPR creates the pull request and then requests the accepted reviewers on GitHub through the `requested_reviewers` endpoint (`POST .../pulls/{number}/requested_reviewers`). The attach happens on the create path and on the update path, and it is **never fatal**: if GitHub rejects the request — for example an invalid handle typed by hand, answered with HTTP 422 — the PR stays published and the TUI shows a warning (`⚠️ PR published, but the reviewers could not be requested: {error}`).

### 3.3 Contextual Help

The flag participates in the contextual help system:

```bash
gitpr -h --no-suggest-reviewers
```

---

## 4. Forge Support and Limitations

| Forge | Suggestion | Submission |
| --- | --- | --- |
| GitHub | Shown and editable | Yes — requested via `requested_reviewers` after the PR is created or updated |
| GitLab | Shown locally only | No — no equivalent endpoint |
| Bitbucket Cloud | Shown locally only | No — no equivalent endpoint |
| Azure DevOps | Shown locally only | No — no equivalent endpoint |

On non-GitHub forges the input field is not shown; the section displays the candidates with a note that the suggestion is local only. To turn GitHub emails into usernames, GitPR resolves each candidate best-effort and never blocks on it: emails in the `users.noreply.github.com` domain are parsed directly into a handle, and any other email falls back to GitHub's `/search/users in:email`. Candidates whose email GitHub does not recognize are shown by name and email and are simply not pre-filled — you can still type their handle.

Fewer suggestions than `top_n` are normal: files without history, binary files, a diff with no added lines or a brand-new repository all yield empty or partial results with a warning — never an error. The analysis never runs in `--no-edit`/`--no-publish` flows, so automated pipelines are unaffected.

---

## 5. For Developers and Plugins

The use case lives in four flat modules in `src/`: `reviewer_suggestion.py` holds the pure domain (dataclasses, weights, bot list, `rank_reviewers()` — no git, no network), `diff_parser.py` implements `parse_added_lines()` over the diff text, `blame_engine.py` gained the thin `get_blame_for_range()` (the archaeology flow was not refactored), and `suggest_reviewers.py` orchestrates with `compute_reviewer_suggestions()`, which **never raises**. The three `GITPR_*` keys above are declared in `DEFAULT_CONFIG` in `src/config.py`, with `suggest_reviewers_enabled()` and `get_reviewer_suggestion_settings()`.

On the SCM side, the base `ScmProvider` contract gained a **non-abstract** `request_pull_request_reviewers(repo, pr_id, reviewers)` whose default raises `ScmNotSupportedError`; only `github_provider.py` implements it, together with the GitHub-only `email_to_handle()`. `main.py` gates the computation to the default TUI flow and hands the app a view dict `{"handles", "lines", "submittable", "note"}`. All user-facing text goes through `__()` i18n keys, so the 5 language packs must stay in sync when messages change.

Architecture decision record and canonical vocabulary: [ADR-002 Reviewer Suggestion](plans/ADR-002-reviewer-suggestion.md) and [Reviewer Suggestion glossary](plans/glossary-reviewer-suggestion.md).

> **Note:** See also the [pull request publication documentation](pull-request-publication.md) for the full publishing flow, its modes and its flags.
