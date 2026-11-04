# Technical Documentation: Automatic Issue Closure (`--close-issue`)

The Issues TUI creates an issue and then closes; the number it received is otherwise lost, and the next pull request is the first place that could close it. The automatic issue closure is the bridge between those two moments: a local record carries the number forward, and the pull request flow offers one line — `close #N` — that makes the forge close the issue when the merge lands.

It is not an issue manager. It does not edit, list, reopen or label anything, and it never speaks to the forge on its own schedule: nothing is recorded until an issue is created through the TUI, and nothing is decided until a pull request run finds a record to read.

---

## 1. Overview

The feature acts on three surfaces:

1. **Creation.** `gitpr -is` opens the Issues TUI; `F3` creates the issue on the forge, and the same answer is written to `.gitpr/conf/github.yml`.
2. **The pull request run.** The default `gitpr` flow reads the record before generating anything, asks the forge whether the issue is still open, and — at most once — offers to add the closing line to the description.
3. **Contextual help.** `gitpr -h --close-issue` and `gitpr -h --no-close-issue` describe the two flags and link to this document.

### 1.1 Command Reference

```bash
gitpr -is                      # Create an issue; F3 on GitHub records it
gitpr                          # The PR flow reads the record and may offer close #N
gitpr --close-issue            # Accepts the line without asking (the issue is still checked)
gitpr --no-close-issue         # Skips the feature entirely for this run
gitpr -h --close-issue         # The same summary, with a link to this document
```

| Command | Writes | What it does |
|---|---|---|
| `gitpr -is` → `F3` | `.gitpr/conf/github.yml`, `.gitignore` | Creates the issue on GitHub and records its number, title, URL, creation time and branch. `F2` (save locally) records nothing |
| `gitpr` (default) | The pull request body, only when the line is accepted | Reads the record, checks the issue, asks at most once |
| `--close-issue` | Same as above | Accepts the line without the question; the issue is still verified |
| `--no-close-issue` | Nothing | No record is read and no forge call is made |
| `-h --close-issue` | Nothing | Prints the contextual help |

The two flags answer the same question, so passing both is a usage error: the command prints `❌ --close-issue and --no-close-issue cannot be used together.` and exits `1`. The rejection happens before the ledger migration prompt and the project-file seed, because a usage error must not ask anything or write a file. `-h` wins over the error, so a help invocation that carries both flags still shows both entries.

---

## 2. The Flow, End to End

Six steps, in the order the run takes them:

1. **Record.** `F3` in the Issues TUI calls the forge, receives the new issue, and hands the result to `register_created_issue` (`src/ui/issue_app.py`). Only GitHub is recorded; a failure here is swallowed, because the issue already exists on the forge and local bookkeeping must never turn a successful creation into an error.
2. **Early gate.** `_prepare_close_issue` (`src/main.py`) runs at the start of the default pull request branch — **before** the unstaged-files check, before the diff is read and before any AI call. It returns immediately for `--no-close-issue`, for `GITPR_ISSUE_AUTOCLOSE=false`, and when the file holds neither a record nor an error. Only past those gates does it construct the registry — and constructing it runs `git rev-parse` — then resolve the SCM provider.
3. **Decision.** `resolve_close_issue` (`src/issue_autoclose/resolve_close_issue.py`) reads the record once, asks the forge once, and asks the user at most once. The gates are listed in section 4.
4. **Assembly.** `insert_close_line` (`src/issue_autoclose/insert_close_line.py`) runs at the single point where the description is built — after the reviewer guide and before both the local `.md` file and `pr_data`. The TUI publisher and the direct `--no-edit` publisher therefore receive exactly the same body.
5. **Publication.** The TUI (`PrPublishApp`) or `_publish_pr_directly` sends the body to the forge.
6. **Clearing.** The record is removed only when the body actually reached the forge: `app.body_published` for the TUI, or `_publish_pr_directly` returning `True`. A declined question, `Esc`, a failed publish, or merely opening an existing pull request keep the record for the next run.

The decision is made before the description exists on purpose. Asking once, at the start, keeps the question away from the publisher screen and lets the same answer flow into the file, the TUI and the direct publisher without a second prompt.

### 2.1 What Each Step Costs

| Step | Disk | Network | AI | Skipped when |
|---|---|---|---|---|
| 1. Record | Record write, plus one `.gitignore` line on the first write | The `create_issue` call that was already happening | — | Issue created outside the TUI, local save (`F2`), or a non-GitHub forge |
| 2. Early gate | One record read | `git rev-parse` only once the feature is on | — | `--no-close-issue`, `GITPR_ISSUE_AUTOCLOSE=false`, no record |
| 3. Decision | One record read | One `get_issue`; a second call for the default branch only on the question path | — | Any of the gates in section 4 |
| 4. Assembly | — | — | — | No decision produced |
| 5. Publication | The usual PR artifacts | The usual publish call | The usual PR generation | — |
| 6. Clearing | One unlink | — | — | Nothing was published |

With no record, the run is the flow of every earlier version, byte for byte. The only extra work is one file read.

---

## 3. The Registry File

The record lives at `.gitpr/conf/github.yml`, anchored at the repository root. It is local state, not project content: the file is not meant to be committed, and the first write adds exactly one line to the repository's `.gitignore`.

The folder itself is not ignored wholesale. `gitpr.config.yml` lives in the same `.gitpr/conf/` and is versioned on purpose (ADR-015), so the ignore entry names the record file specifically.

The record holds **one issue at a time — the last one wins.** A single pull request workflow needs nothing more: the issue being documented is the one just created. Creating a second issue replaces the first, and there is no history to consult. This is also why the file is not a cache of issues: it is a bookmark.

### 3.1 The Format

```yaml
schema_version: 1
last_issue:
  repo: owner/name
  number: 42
  title: "Add login rate limit"
  url: https://github.com/owner/name/issues/42
  created_at: '2026-11-03T14:22:07'
  branch: feat/login-rate-limit
```

`schema_version: 1` is the only version this module reads and the only one it writes. A file carrying any other version is reported as unreadable rather than guessed at.

`load()` validates every field before returning it:

- `repo`, `title`, `url` and `created_at` must be non-empty text;
- `number` must be a positive integer, and a boolean is rejected even though Python treats it as an integer;
- `branch` is optional and may be empty.

A **missing file is not an error** — it means "no issue recorded". An unreadable file is an error, returned as data (`RegistryLoad.error`) so the command that owns the screen decides how to report it. The module never prints.

### 3.2 Writes, Corruption and `.gitignore`

`record()` writes to a sibling temporary file and moves it into place with `os.replace`, so an interrupted run can never leave a truncated record. A file that `load()` reported as corrupt is simply replaced by the next `record()`: a broken bookmark is worth less than a new one.

Before the first write, `record()` asks `git check-ignore -q .gitpr/conf/github.yml`. Only when git does not already ignore the file does it append the entry to `.gitignore`, and only once. Outside a git repository, or when `.gitignore` cannot be written, nothing changes and the record is still valid — the user can add the line by hand.

`clear()` removes the file and returns `False` when there was nothing to remove, so a caller never has to distinguish "removed" from "was not there". Any genuine I/O failure becomes `IssueRegistryError`; the callers that run inside the pull request flow catch it and move on, because local state must not break a publication.

---

## 4. The Decision: Gates in Order

The order is part of the contract. Every gate that costs nothing runs before any disk or network access, and only a still-open issue reaches the question. `skipped_reason` is the vocabulary the `issue_autoclose` metric reports (section 8).

| # | Gate | `skipped_reason` | Cost | Clears the record |
|---:|---|---|---|---|
| 1 | `--no-close-issue` was passed | `flag-disabled` | None | No |
| 2 | `GITPR_ISSUE_AUTOCLOSE=false` | `disabled` | None — the PR flow returns before calling the use case; the check remains as defence in depth for callers that own the switch | No |
| 3 | The forge is not GitHub | `not-github` | None | No |
| 4 | The record exists but cannot be read | `registry-error` | One file read, one warning | No |
| 5 | No record at all | `no-record` | One file read | No |
| 6 | The record belongs to another repository | `other-repo` | One file read | No (ADR-007) |
| 7 | `get_issue` answers 404 | `issue-missing` | One HTTP call | **Yes** |
| 8 | `get_issue` fails for another reason | `verify-failed` | One HTTP call, one warning | No — kept for the next run |
| 9 | The number is a pull request | `issue-is-pr` | One HTTP call | **Yes** |
| 10 | The issue is not `open` | `issue-not-open` | One HTTP call | **Yes** |
| 11 | There is no terminal and `--close-issue` was not passed | `no-tty` | One HTTP call | No |
| 12 | `--close-issue` was passed | — (a decision is made) | One HTTP call, no question | No |
| 13 | The user answers the question | `declined` when the answer is no | A second HTTP call for the default branch, only on this path | No on decline |

Two details matter more than the table:

- **The pull-request check comes before the state check.** GitHub's issue endpoint answers pull request numbers too, so `is_pull_request` is examined first. A number that turns out to be a pull request is not an issue that was closed — it is a record that can never be used, and it is forgotten.
- **Repository comparison is case-insensitive.** GitHub owner and repository names are case-insensitive, so `matches_repo()` compares them with `casefold()`. A record from another repository is none of this flow's business, and it is deliberately kept rather than cleared.

### 4.1 The Question and the Target-Branch Warning

The question reads:

```text
Issue #42 – Add login rate limit is open. Add "close #42" to the end of the pull request description?
```

It defaults to yes. `ask` is called outside every `try` block: `click`'s `Abort` is a `RuntimeError`, and `Ctrl+C` must leave the flow exactly like any other prompt instead of being swallowed as a skipped feature.

On the question path — and only there — the flow also fetches the repository's default branch. When the configured target differs from the default, the question carries an extra line:

> Warning: the pull request targets `"develop"` but the default branch is `"main"`. GitHub only closes the issue when the merge lands on the default branch.

A failed or empty default-branch lookup degrades in silence. The forge only says "unknown", and a warning the caller cannot phrase correctly is worse than no warning at all.

### 4.2 What the Outcome Carries

`CloseIssueOutcome` has five fields, and every one of them is safe to ignore:

| Field | Meaning |
|---|---|
| `decision` | The number, title and exact line to insert — `None` when nothing was offered or the user declined |
| `warning` | A one-line message to print; never set when a question was asked |
| `skipped_reason` | The gate that ended the decision; empty when a decision was made |
| `asked` | Whether the user was actually shown a question |
| `accepted` | Whether the line will be inserted |

A decision never clears the record — clearing belongs to the caller, once the pull request exists (ADR-007), because a failed publish must keep the record for the next run. `target_branch_warning` is repeated on the decision only so the caller can keep it alongside the line; it was already part of the question and must not be printed again.

---

## 5. Insertion and Idempotency

The body is assembled once. `insert_close_line` is called from that point and nowhere else, so no publisher can receive a body without the line or with it added twice.

A `None` decision returns the body unchanged. Otherwise the line is appended as its own paragraph:

```text

close #42
```

The function is idempotent across keyword spellings. GitHub accepts `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` and `resolved`, case-insensitively, and the same issue may be named as `owner/repo#42`. If the body already mentions **the same issue number** with any of those forms, nothing is added — the forge will close the issue either way, and a second reference would only be noise.

The badge is attached later and always at the end of the body, so appending here is what leaves the closing line immediately before it. This module never has to look for a badge.

---

## 6. The SCM Contract and the Other Forges

Three methods on `ScmProvider` exist for this feature:

| Method | GitHub | Base class |
|---|---|---|
| `get_issue(repo, number, timeout=5)` | `GET /repos/{owner}/{repo}/issues/{n}` | Raises `ScmNotSupportedError` |
| `get_default_branch(repo, timeout=5)` | `GET /repos/{owner}/{repo}` → `default_branch` | Raises `ScmNotSupportedError` |
| `closing_line(number)` | `close #N` | Raises `ScmNotSupportedError` |

None of the three is abstract. That is deliberate: GitLab, Bitbucket and Azure DevOps keep compiling and keep working for every other feature, and the automatic closure is GitHub-only (ADR-003). The caller reads `ScmNotSupportedError` as "feature inactive", never as a crash.

`closing_line` is forge syntax rather than a generic string. GitHub reads `close #N`; a line built anywhere else could be spelled correctly and still mean nothing to the forge. The short five-second default timeout is also part of the contract: the answer only decides whether one question is asked, and a slow forge must not hold up the pull request flow.

`provider_is_github()` is checked before any of this, so the other forges skip the feature without a disk read and without a warning.

---

## 7. Configuration

Two variables in `~/.gitpr/.env`, also editable in `gitpr config` under the **Issue** section. Neither is ever written automatically.

| Key | Default | Effect |
|---|---|---|
| `GITPR_ISSUE_AUTOCLOSE` | `true` | Only `false`, `0`, `no`, `off` or `n` turns the feature off; any other value — including an unparseable one — leaves it on |
| `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` | `5` | Seconds to wait for the forge while reading the issue. Zero, a negative number or a non-integer falls back to `5` |

The precedence is:

```text
--no-close-issue  >  GITPR_ISSUE_AUTOCLOSE=false  >  --close-issue
```

`--close-issue` **does not override** `GITPR_ISSUE_AUTOCLOSE=false`. The switch is the user's decision about the machine, and a per-run flag that silently reversed it would make the setting untrustworthy. There is no per-repository configuration for this feature.

---

## 8. Metrics

Every decision the use case reaches is reported once to the local ledger (`gitpr metrics`) as an `issue_autoclose` row:

| Payload field | Value |
|---|---|
| `command` | `issue_autoclose` |
| `asked` | Whether the question was shown |
| `accepted` | Whether the line will be inserted |
| `skipped_reason` | The gate from section 4, or empty when a decision was made |

The helper's own short-circuits — flag off, config off, no record, no provider — never engaged the feature and stay out of the ledger. They are not decisions; they are runs in which there was nothing to decide.

The fields travel in the JSON payload. The CSV export carries the columns the ledger defines for every command, not a per-feature shape.

---

## 9. Limits, Stated Plainly

- **One issue at a time.** Creating a second issue replaces the first record; the first can no longer be closed by this feature.
- **Recording happens only in the TUI.** An issue created with `gh`, through the API, or by any other path is invisible to the feature.
- **GitHub only.** The other forges skip the feature silently, with no warning and no record.
- **The record is per clone.** It is local state and is not committed, so a teammate's clone does not inherit it, and a fresh clone starts with nothing to close.
- **Deleting the line in the editor does not keep the record.** If the body was published, the record is cleared because the publication carried the body — even if the line itself was edited out before sending.
- **Updating an existing pull request also clears the record.** The TUI reports "created" for that path too; what decides the clearing is that the body reached the forge.
- **The keywords are English only.** `close`, `fix` and `resolve` and their inflections are what GitHub reads; a body that says `fecha #42` is not a closing reference and the line will be added next to it.
- **The state check trusts the forge.** An issue closed between the read and the merge cannot be detected here; the closing line simply has nothing left to close.

---

## 10. Related Reading

- `docs/issue-tui-help.md` — the Issues TUI, `F2`/`F3`, and the short user-facing summary of this feature.
- `docs/config-tui.md` — the configuration screen, including the **Issue** section.
- `docs/metricas-telemetria.md` — the local ledger and the `issue_autoclose` metric.
- `docs/scm-multiforge.md` — the provider abstraction and why only GitHub implements the closure.
- `docs/github-pat-integration.md` — the token `F3` needs to create the issue.
- `docs/pull-request-publication.md` — the publisher that receives the assembled body.
- `docs/specs/issue-autoclose/adrs/ADR-001` through `ADR-007` — the decisions behind the record, the gates, the insertion and the clearing.
- `CONTEXT.md` — the glossary terms *Issue registry*, *Closing line* and *Close issue decision*.
