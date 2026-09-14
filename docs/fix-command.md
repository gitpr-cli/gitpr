# Technical Documentation: Fix Command (gitpr fix)

`gitpr fix` turns the findings of the last code review into patches you read before they touch your tree. One invocation resolves the most recent review of the current repository and branch, asks the AI for the smallest unified diff that fixes each problem the review raised, classifies every patch by how much it can be trusted, and — only when told to — writes it into the working tree and records it so it can be undone. Reading is the default: with no arguments the command lists the candidates and writes nothing, a single finding is shown as a dry run, and writing requires `--apply`.

---

## 1. Overview

The subcommand is an addition to the CLI, not a change to it: every legacy option keeps its meaning and `--force` here namespaces under `gitpr fix` (in `gitpr release` it means "regenerate an existing version section"). The whole flow is local — nothing is committed, nothing is pushed, no branch is created before a write is confirmed.

### 1.1 Command Reference — `gitpr fix`

All options of the subcommand, as shown by `gitpr fix -h` (or `--help`):

```bash
gitpr fix                      # lists the candidates of the last review
gitpr fix FIX-001              # dry run: the diff of one finding, nothing written
gitpr fix FIX-001 --apply      # writes it, after a confirmation
gitpr fix --all-safe --apply   # writes every safe patch, on a new branch by default
gitpr fix --rollback FIX-001-1a2b3c4d
```

| Option | Description |
| --- | --- |
| **`[<finding-id>]`** | Finding addressed by the run (`FIX-001`). With no `--apply` it is a dry run; with no id and no `--all-safe` the command lists instead |
| **`--list`** | Lists the fix candidates of the last review — what the command does with no arguments |
| **`--apply`** | Writes the patch into the working tree. Without it the run is a dry run that touches nothing |
| **`--all-safe`** | Selects every patch classified as safe. Writing them still requires `--apply` |
| **`--create-branch <name>`** | Creates and switches to this branch before applying the patches |
| **`--no-branch`** | Applies on the current branch even when the configuration would create one |
| **`--yes`** | Skips the confirmation prompt. It never bypasses `--force` |
| **`--force`** | Applies a patch that is not safe, after a typed confirmation phrase |
| **`--rollback <patch-id>`** | Undoes a patch applied earlier, reading its diff from the local history |

| Characteristic | Description |
| --- | --- |
| **Data source** | Most recent cached review of the current repository and branch — `gitpr -r` or `gitpr -f`, never the file audit (`-i`) |
| **AI call** | One call per review, on the advanced model of the configured provider, cached under `fix/` like every other GitPR call |
| **Files written** | Nothing by default. `--apply` writes the working tree and appends to `.gitpr/fix_history.json` |
| **Branch** | Only a `--all-safe --apply` batch, and only when the configuration asks for it |
| **Undo** | `--rollback <patch-id>` — no commit, no stash, no reset |
| **Exit code 1** | No review, no changes to patch, no API key, unknown finding id, unsafe patch without `--force`, a branch that cannot be created |

---

## 2. From Review to Findings

### 2.1 The Review It Reads

`gitpr fix` never reviews anything itself: it consumes the last review of the current repository and branch from the prompt cache (`~/.gitpr/cache/prompts/review/`). Among the cached records it takes the most recent one whose `repo` and `branch` match and whose `action_type` is `review` or `fullreview` — the three review modes share that folder, and a `filereview` (file audit, `-i`) is excluded on purpose, because an audit of a single file has no branch diff to patch.

With no review recorded, the command stops with `❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.` — "there is no review" and "the review found nothing" are never allowed to look alike.

### 2.2 The Diff Is Re-Derived

The review *text* comes from the cache; the *diff* is re-derived now, with the very function that produced the review: `get_git_diff()` for `review`, `get_git_full_diff()` for `fullreview`, selected by the recorded `action_type`. That is what anchors the patch to the tree in front of you today instead of the tree of the day the review ran. A working tree with no changes at all aborts with `❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again.`

### 2.3 One AI Call, and the Ids It Produces

A single call asks the model for the smallest unified diff per finding of the review, returning one JSON object per finding. It runs through the standard GitPR infrastructure (configured provider, advanced model, JSON output, retry) and the standard MD5 cache in `~/.gitpr/cache/prompts/fix/` — see the [AI Providers documentation](providers-ia.md).

The ids are assigned by gitpr, never by the model: `FIX-001`, `FIX-002`, ... in the order the findings came back. Because the prompt is built from the same review and the same diff, the cached answer is reused and **the ids stay put between runs** — the id a listing showed is the id `--apply` addresses. Running `gitpr -r` again produces a new review, hence a new prompt, new findings and new ids.

A model that answers with prose instead of the expected envelope is an ordinary outcome, not a crash: the run reports `ℹ️ The review raised no fixable findings.` and writes nothing.

| Field | Meaning |
| --- | --- |
| **`finding_id`** | `FIX-001` — assigned by gitpr, in the order the findings came back |
| **`file_path`** | The path the patch touches. The patch is authoritative; the model's own `file_path` is the fallback for a finding that has no patch at all |
| **`line_start` / `line_end`** | The line range the review pointed at (0 when the model reported none) |
| **`severity` / `category`** | As the review declared them (`critical`, `major`, `minor`, `info` / `bug`, `security`, ...) — recorded, never re-derived |
| **`message`** | The finding, in the interface language |
| **`confidence`** | `high` / `medium` / `low` as declared by the model; `low` forces the `experimental` class |
| **`diff`** | The unified diff that fixes the finding — the patch itself |
| **`suggested_test`** | What the model suggests to cover the fix |
| **`patch_id`** | `FIX-001-1a2b3c4d` — the finding id plus the first 8 hex digits of the diff's MD5; what `--rollback` addresses |

---

## 3. Safety Classification

The classification is deterministic and involves no AI: the same patch summary and the same settings always yield the same verdict, so a patch classified `safe` in a dry run is still `safe` when `--apply` runs. `git apply --check` is evaluated first — a patch that does not apply to the current tree is never anything else.

| Class | Criteria | What it opens |
| --- | --- | --- |
| **`safe`** | Applies cleanly, one file, one hunk, within the changed-lines limit, outside the sensitive paths, and deletes no line that looks like a call | `--all-safe --apply` may batch it |
| **`review_required`** | Applies cleanly, but at least one `safe` condition failed | `--apply` on that finding, with a confirmation |
| **`experimental`** | Does not apply to this tree, spans more than one file, or the model declared low confidence | Never batched. `--force` with a typed phrase is the only door |

### 3.1 Reason Codes

The verdict always carries a reason — the first condition that tripped, in this order:

| Reason code | Meaning |
| --- | --- |
| `apply_check_failed` | It does not apply to the current tree |
| `multi_file` | It changes more than one file |
| `low_confidence` | The AI declared low confidence in it |
| `excluded_path` | It touches a configured sensitive path |
| `multiple_hunks` | It spans more than one hunk |
| `too_many_lines` | It changes more lines than the configured limit |
| `removes_call` | It deletes a line that looks like a call |
| `safe` | No condition failed |

The terminal turns each code into a translated sentence; the MCP tool reports the code itself, so its callers can match on a stable string.

### 3.2 Notes on the Criteria

A finding the model answered without a usable patch still becomes a candidate, classified `experimental` with an empty diff. Dropping it would hide an issue the review raised, and the empty diff is the truth — git refuses it, so it can never be applied by accident.

The call heuristic is deliberately crude: any removed line matching `\w+` followed by an open parenthesis trips it, including a deleted comment that merely mentions `foo()`. It errs toward `review_required`, which is the safe direction to be wrong in.

The sensitive paths are about *risk* (migrations, workflows, docker, terraform), not about diff noise — which is why they are a configuration of their own and not shared with the smart-excludes list.

---

## 4. Reading Before Writing

### 4.1 Listing Candidates

With no finding id, `gitpr fix` (or `gitpr fix --list`) prints every candidate of the last review — class, location, message and patch id — and writes nothing:

```text
🔎 Fix candidates from the last review:
  FIX-001  [safe]  src/core.py:210
     The retry loop swallows the exception.
     ↳ FIX-001-1a2b3c4d
  FIX-002  [review_required]  src/config.py:88
     The default timeout is duplicated.
     ↳ FIX-002-9f8e7d6c — it changes more lines than the configured limit
ℹ️ Apply one with 'gitpr fix <id> --apply'; the safe ones can be batched with '--all-safe --apply'.
```

The class is coloured green (`safe`), yellow (`review_required`) or red (`experimental`), and the reason sentence only appears for the two non-safe classes.

### 4.2 Dry Run — `gitpr fix <id>`

With a finding id and no `--apply`, the run prints the candidate block, the whole unified diff in the terminal colours used across the project, every warning, and closes with `ℹ️ Dry run — nothing was written. Add --apply to write it.` Nothing in the tree is touched. When a branch would be created, the run says so (`ℹ️ Branch '{branch}' would be created before the patches are applied.`), and a `--all-safe` dry run additionally lists the candidates it left out, each with the id that brings it back.

### 4.3 Writing — `--apply`

A patch that is not classified `safe` is never written by a plain `--apply`: the run prints the finding, its class and its reason, and exits with code 1 (`❌ {finding_id} is {safety} ({reason}) — re-run with --force to apply it anyway.`).

```bash
gitpr fix FIX-001 --apply
gitpr fix --all-safe --apply
gitpr fix FIX-002 --apply --force
```

For a `safe` patch the run asks `❓ Apply FIX-001 to the working tree?` (declining is the default); declining prints `❌ Operation cancelled by user.` and leaves the tree untouched. `--yes` or `GITPR_FIX_REQUIRE_CONFIRMATION=false` skips that prompt.

`--force` opens on a typed phrase rather than a y/n: the run prints the class and the reason and asks for the phrase `apply FIX-001` to be typed exactly (trimmed, case-insensitive). A mismatch aborts with `❌ The confirmation phrase does not match. Nothing was applied.` and exit code 1 — `--yes` does not bypass this prompt. `--force` together with `--all-safe` only warns that it has no effect, since only safe patches are selected. `gitpr fix --apply` with no finding id and no `--all-safe` warns (`⚠️ Nothing was selected: name a finding id or add --all-safe.`) and lists the candidates instead.

A patch git refuses is reported as a failure with git's own message and the batch continues — one candidate failing to apply says nothing about the next. Nothing is recorded in the history for it: the record exists to undo what was applied, and nothing was. Each written patch is reported as `✅ Patch applied: FIX-001-1a2b3c4d (src/core.py)`.

### 4.4 Branch Handling

| Situation | Behaviour |
| --- | --- |
| `--all-safe --apply` with `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE=true` | Creates `GITPR_FIX_BRANCH_NAME_TEMPLATE` (default `fix/gitpr-{datetime}`) from the current `HEAD` and applies the batch there; the original branch is left intact |
| `--create-branch <name>` | Creates that branch instead (any run) |
| `--no-branch` | Applies on the current branch even when the configuration would create one |
| Single finding, or a dry run | Never creates a branch |

The branch is created once, before the first patch, and only on a real run. A branch that cannot be created aborts the batch — carrying on would apply the patches to the branch the user was trying to leave.

### 4.5 A File That Is Already Dirty

When a patch targets a file that already has uncommitted changes, the run warns about exactly those files (`⚠️ These files already have uncommitted changes: ...`) before writing. Warning about every dirty file in the repository would fire on nearly every real run; only the overlap between the patch and the pending changes is the case where applying can surprise the user.

---

## 5. History and Rollback

### 5.1 `.gitpr/fix_history.json`

Every applied patch is recorded in `<root>/.gitpr/fix_history.json`, **tracked in git** — the whole diff is stored there precisely so the patch can be undone without a commit. The file is written atomically (a temporary sibling renamed over it), so an interrupted write never leaves a half-written history. The consequence of tracking it is deliberate and known: applying a fix dirties a tracked file, so it appears in `gitpr -c` and in PR descriptions until it is committed — which is why `.gitpr/fix_history.json` ships in the smart-excludes list and stays out of the AI diffs.

| Field | Meaning |
| --- | --- |
| **`patch_id`** | `FIX-001-1a2b3c4d` — what `--rollback` addresses |
| **`finding_id`** | `FIX-001` |
| **`file_path`** | The file the review pointed at |
| **`files_changed`** | Every path the diff touches |
| **`safety`** | `safe` / `review_required` / `experimental` at the moment it was applied |
| **`branch`** | The branch the patch was applied on (`null` when it was applied in place) |
| **`applied_at`** | Timestamp, in the project's cache format |
| **`diff`** | The complete unified diff, verbatim |
| **`provenance`** | Provider, model, prompt version, gitpr version, generation timestamp |
| **`rolled_back_at`** | Timestamp once undone, otherwise `null` |

### 5.2 `--rollback <patch-id>`

The rollback reads the stored diff and replays it with `git apply --reverse` — no commit, no stash, no reset, and no dependence on the working tree still matching what was applied. Git itself verifies the reversal against the file: if the tree moved on, the reverse fails, the error is reported and no file is left half-written. On success the run prints `ℹ️ Undone patch {patch_id}: {files} restored.` and stamps the entry as rolled back.

| Refusal | Message |
| --- | --- |
| No such patch id in this repository | `❌ No applied patch with id '{patch_id}' was recorded here.` |
| Already rolled back | `❌ Patch '{patch_id}' was already rolled back at {when}.` — undoing twice is a mistake, not a no-op |
| Applied on another branch | `❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.` — the file to restore is not here |
| The tree moved on incompatibly | `❌ Could not undo patch '{patch_id}': {error}` — git's own message, with no file left half-written |

`--rollback` takes no finding id and cannot be combined with `--apply` or `--all-safe`.

---

## 6. Skill Template — `.gitpr.fix.md`

The findings call uses the `.gitpr.fix.md` file as the AI's system instruction (persona: **Senior Software Engineer**, normalizing the review into minimal patches). The template is downloaded by `gitpr --skill` — language-aware (`gitpr.fix.md` for English, `gitpr.fix.pt_br.md` for PT-BR) and never overwriting an existing local file. Without it, the built-in persona is used.

The template states the contract the pipeline depends on: the patch is the source of truth, one hunk in one file, never reformat untouched code, never delete an existing call or guard, declare an honest `confidence`, and leave the `diff` empty when the finding needs a human decision. Edit it locally to change how patches are written; the prompt is built from it, so a change produces a new prompt and a new AI call. See the [Skills and Templates documentation](skill-template.md) for the general mechanism.

---

## 7. MCP Integration

`list_fix_candidates` is the 13th MCP tool and is **read-only**: it reports what `gitpr fix` could apply, patch included, and never writes to the working tree. The optional `finding_id` argument narrows the answer to one finding.

```json
{"status": "success", "finding_count": 2, "candidates": [ ... ]}
```

Each candidate carries `finding_id`, `patch_id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`, `safety`, `safety_reason` (the stable code, not a sentence), `confidence`, `suggested_test` and `diff`. The status is `no_data` when the review raised nothing that could become a patch, and `error` with a `message` when there is no review to read or the pipeline cannot run at all. See the [MCP Integration documentation](mcp-integration.md).

---

## 8. Environment Variables

The fix configuration is read from the global `~/.gitpr/.env` file (dotenv format). The two booleans follow the "false disables" convention: unset or any value other than `false` / `0` / `no` / `off` / `n` means enabled — the defaults in the table are active when the variable is not set.

| Variable | Default value | Purpose |
| --- | --- | --- |
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | Added + removed lines a patch may carry and still be `safe`; a non-positive or unparsable value falls back to `5` |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | Sensitive paths, separated by `;`. A patch touching one still applies, but is never `safe` |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | Asks for a confirmation before writing a safe patch; `false` skips it (`--yes` does the same for one run) |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | `--all-safe --apply` creates a branch before writing; `--no-branch` overrides it for one run |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | Name of that branch. Placeholders: `{branch}` (current branch) and `{datetime}` |

> **Note:** See also the [Skills and Templates documentation](skill-template.md) for customizing the GitPR AI template files.
