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

- An input field pre-filled with the handles GitPR resolved for the suggested people, comma-separated. It accepts a GitHub login, a name or an email — whatever you type is resolved to a login before being submitted (§4). Remove a reviewer by clearing the field; add one by typing.
- A read-only hint below the field explaining each suggestion (lines and files touched, last activity). A suggestion shown under a plain name, with no `@handle`, carries the note `No GitHub login found for this person — type one below.` — there is no account to pre-fill, so type the login yourself if you know it.
- Leaving the field empty submits no reviewers at all.

### 3.2 Publishing

After you confirm with F3, GitPR creates the pull request and then requests the accepted reviewers on GitHub through the `requested_reviewers` endpoint (`POST .../pulls/{number}/requested_reviewers`). The attach happens on the create path and on the update path, and it is **never fatal**: the PR stays published whatever happens to the reviewers.

Every value of the field is resolved to a real login before being submitted; a value that resolves to nothing is **not sent** and is reported instead. Once submitted, GitPR reads back the reviewers GitHub actually attached: the forge answers `201` to a login it does not know and attaches nobody, so the response body is the only proof that the request landed. A batch rejected with HTTP 422 — a known login that is not eligible, such as the PR author — is retried one login at a time, so a single bad handle does not take the good ones down with it.

Whatever did not end up on the pull request — a name with no account, a login the forge ignored, a rejection with its reason — is listed in a modal that must be closed before the flow reaches the merge prompt, and the same list is appended to the final message:

```text
⚠️ Reviewers not requested
The pull request was published, but these reviewers were not requested:
⚠️ Eduarda Leal: no GitHub account found.
⚠️ ghost: GitHub did not attach this reviewer.
```

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

On non-GitHub forges the input field is not shown; the section displays the candidates with a note that the suggestion is local only.

On GitHub, every suggested person is resolved to a login before the TUI opens — best-effort, never blocking:

1. The commit of the blame hit: `GET /repos/{owner}/{repo}/commits/{sha}` returns the account linked to the commit author email. This is the reliable path, and the only one that also sees corporate addresses.
2. The `users.noreply.github.com` parse, which costs no request.
3. The fallback `GET /search/users?q={email} in:email`, which only finds **public** emails.

A person that resolves to nothing is still shown, by name and email, with the hint that no login was found — and is never submitted as typed: a name is not a login, and the forge answers `201` to a login it does not know while attaching nobody. Typing the name of a person that did resolve (shown as `Suggested @handle:`) attaches that handle.

Fewer suggestions than `top_n` are normal: files without history, binary files, a diff with no added lines or a brand-new repository all yield empty or partial results with a warning — never an error. The analysis never runs in `--no-edit`/`--no-publish` flows, so automated pipelines are unaffected.

---

## 5. For Developers and Plugins

The use case lives in five flat modules in `src/`: `reviewer_suggestion.py` holds the pure domain (dataclasses, weights, bot list, `rank_reviewers()`, `identity_key()`/`normalize_identity()` — no git, no network), `diff_parser.py` implements `parse_added_lines()` over the diff text, `blame_engine.py` gained the thin `get_blame_for_range()` (the archaeology flow was not refactored), `suggest_reviewers.py` orchestrates with `compute_reviewer_suggestions()`, which **never raises**, and `reviewer_resolution.py` turns identities into logins — `resolve_candidates()` before the TUI, `resolve_typed_reviewers()` at attach time; nothing there raises either, and what cannot be resolved comes back as a `dropped` entry with its reason. The three `GITPR_*` keys above are declared in `DEFAULT_CONFIG` in `src/config.py`, with `suggest_reviewers_enabled()` and `get_reviewer_suggestion_settings()`.

On the SCM side, the base `ScmProvider` contract gained a **non-abstract** `request_pull_request_reviewers(repo, pr_id, reviewers)` whose default raises `ScmNotSupportedError`; only `github_provider.py` implements it, together with the GitHub-only `email_to_handle()`, `get_commit_author_login()` and `get_user_login()`. The method returns the logins the forge **actually attached**, read back from the `201` body — an empty list is how the caller detects a request that was accepted and silently ignored. `main.py` gates the computation to the default TUI flow and hands the app a view dict `{"handles", "lines", "submittable", "note", "resolutions"}`. All user-facing text goes through `__()` i18n keys, so the 5 language packs must stay in sync when messages change.

Architecture decision record and canonical vocabulary: [ADR-002 Reviewer Suggestion](plans/ADR-002-reviewer-suggestion.md) and [Reviewer Suggestion glossary](plans/glossary-reviewer-suggestion.md).

> **Note:** See also the [pull request publication documentation](pull-request-publication.md) for the full publishing flow, its modes and its flags.
