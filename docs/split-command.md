# Technical Documentation: Split Command (gitpr split)

`gitpr split` reads a working tree holding several unrelated concerns, groups the hunks by logical intent with AI, and proposes one atomic commit per concern — each with a message generated for that subset of the changes alone. Reading is the default and writing is opt-in: with no arguments the command prints the plan and offers to apply it, `--dry-run` prints and stops without ever asking, and `--apply` confirms once and then stages and commits group by group.

The problem it solves is the one every developer recognises: a bug fix, a refactor and a configuration tweak that grew in the same afternoon, now inseparable in a single `git diff`, where the only ways out are `git add -p` by hand or a commit message that lists three unrelated things.

---

## 1. Overview

The subcommand is an addition to the CLI, not a change to it: every legacy option keeps its meaning, and the whole flow is local — no `git commit` is created until `--apply` is confirmed, nothing is pushed, and no branch is created.

### 1.1 Command Reference — `gitpr split`

All options of the subcommand, as shown by `gitpr split -h` (or `--help`):

```bash
gitpr split                    # prints the plan, then offers to apply it
gitpr split --dry-run          # prints the plan and stops — never prompts
gitpr split --apply            # prints the plan, confirms once, stages and commits
gitpr split --apply --yes      # same, without the confirmation prompt
gitpr split --max-groups 3     # at most three atomic commits
```

| Option | Description |
| --- | --- |
| **`--dry-run`** | Prints the plan and stops. Never prompts, never touches the index or the working tree, in any index state |
| **`--apply`** | Executes the plan: selective staging and one commit per group, in order |
| **`--yes`** | Skips the confirmation prompt. It never bypasses the per-group `--check` |
| **`--max-groups <n>`** | Upper limit on how many commits the plan may propose, overriding the configuration |
| **`--provider <name>`** | Forces the AI provider for this run (`gemini`, `deepseek`, `ollama`) |

| Characteristic | Description |
| --- | --- |
| **Data source** | The working tree's uncommitted changes — staged, unstaged and both together, as one diff against HEAD |
| **AI calls** | One call to group the hunks, plus one call per group to write its commit message |
| **Files written** | Nothing by default. `--apply` writes to the Git index and creates commits; the working tree is never written to |
| **Index** | Left clean before the run. `--apply` asks once for permission to unstage everything |
| **Undo** | None. The result is ordinary commits — `git reset`/`git reflog` are the tools |
| **Exit code 1** | Not a Git repository, `--dry-run` combined with `--apply`, an empty working tree, no API key or an unreachable provider, a repository with no commits to build on, or a plan with no groups |

### 1.1.1 When the Command Asks

`--apply` states an intent, so `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` may legitimately skip the question. No flag at all states no intent, so in that mode the question **is** the command and it is always asked — a bare `gitpr split` must not commit on its own just because a configuration value says confirmations are off. `--yes` is the user saying so explicitly, and it skips the question in both modes.

### 1.2 What "Atomic" Means Here

An atomic commit is a commit holding every change one concern needs and no change belonging to another. The unit of division is the **hunk** — one `@@` block of one file — and never a smaller piece: dividing a single hunk into sub-hunk fragments is out of scope, and so is splitting a pull request that is already published on the forge.

The unit is the hunk and not the file because the case worth solving is precisely the one where a single file holds two concerns. A file whose every hunk belongs to the same concern is not a special case of that: it is the same machinery arriving at the obvious answer.

### 1.3 What Is Out of Scope

- Files git does not track. They carry no hunks, and `git diff HEAD` does not describe them, so they take no part in a plan. They are named in a warning, never silently ignored.
- Splitting a hunk further.
- Undoing a split. The result is normal commits and normal Git reverses them; no dedicated rollback was built, unlike `gitpr fix`, where a written patch has no commit to reset.
- Interactive reordering, merging and unticking of groups. A later delivery.

---

## 2. Capturing the Diff

### 2.1 Its Own Diff Capture, and Why

Split does not use `get_git_diff()`, the diff every other flow reads:

```python
SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")
```

The difference is `-w`, which the other flows pass and split must not. With `-w`, a difference that is *only* whitespace is rendered as context — and the context line emitted may not match the file byte for byte. A patch built from such a diff is either refused by `git apply` or, worse, applies content that differs from the working tree. That would break the guarantee this command is built on: the files on disk at the end are byte-identical to the files on disk at the start.

`-U1` is also dropped: one line of context leaves `git apply --check` too little to anchor a hunk on. `-B`, which decomposes rewrites into delete-plus-add, is dropped for the same reason it is bad here as anywhere — it turns one applicable hunk into two that must be applied in lockstep.

`-M` is **kept**, and it is load-bearing. Without rename detection a rename arrives as a deletion plus an addition, and the addition is an untracked file — out of scope. Split would then commit a bare deletion of the old path while the new file sat untracked beside it, which reads as data loss.

`--binary` is a no-op for text and the only thing that makes a changed binary file applicable at all.

### 2.2 No Smart Excludes

The review flows drop lockfiles, generated files and binaries before sending a diff to the AI. Split drops nothing.

The reason is that the exclusion is not free here, it is *wrong*. A lockfile and its manifest describe one change; excluding the lockfile commits the manifest alone and leaves a tree in which the two disagree — a broken intermediate commit, which is exactly what this command exists to prevent. Noise is bounded instead by truncating each unit in the prompt and by capping how many units are sent at all.

### 2.3 Capture First, Unstage Last

`--apply` needs an index it can stage against, and the index may already hold work: a staged new file, a staged rename. That state is not an accident to be cleared away before reading the diff — it is what makes those changes *visible*. A new file only appears in `git diff HEAD` because the index tracks it; unstage it first and it becomes untracked, out of scope, and gone from the plan.

So the order is fixed: the diff is captured against whatever index state exists, and everything is unstaged immediately before the first `git apply --cached`. This is sound because every hunk in a `git diff HEAD` carries a preimage taken from HEAD, whatever the index happens to hold. After the unstage the index *is* HEAD, so those same preimages apply cleanly. There is no re-diff, no abort on divergence, and no plan that quietly re-shapes itself between being shown and being applied.

### 2.4 Untracked Files

They are out of scope and they are reported: the plan carries a warning naming them. "Nothing to do here" and "there was something here and I skipped it" must never look alike.

---

## 3. The Plan

### 3.1 Units

A unit is one of two things, and the difference matters throughout:

| Unit | What it is |
| --- | --- |
| **`Hunk`** | One `@@` block of one file, with its content verbatim, the file header that precedes it, both sides' start and count, and its position in the original traversal |
| **`OpaqueSection`** | A section of the diff that has no hunks — a binary change, a pure rename, a mode-only change, an empty file creation — kept whole and verbatim |

Opaque sections are never sent to the AI. There is no grouping decision to ask of it, and a unit the model cannot reason about is a unit it invents a plausible id for. Each becomes its own single-unit group: an atomic commit of one indivisible change.

The file header is **stored, not reconstructed**. `new file mode`, `deleted file mode`, `old mode`/`new mode`, and git's quoted form for paths holding spaces or non-ASCII bytes are all unrecoverable from a path, and synthesizing them produces a patch git refuses.

### 3.2 Hunk Boundaries Are Decided by Counting

A hunk ends when the counts in its header are exhausted — never at the next `@@`. Inside a hunk, a removed line reading `--- something` and an added line reading `+++ something` sit at column 0 and are indistinguishable from a file-header pair, while a context line always carries its leading space. Counting is the only rule that is correct.

Counting doubles as the malformed-input validator. A section whose counts cannot be reconciled with its body degrades **whole** to one `OpaqueSection`: never a partial hunk list, because half of an unparseable section is not something to hand to `git apply`, and a patch that applies most of a file is worse than one that refuses it.

### 3.3 Unit Identity

A unit's id is `0007-1a2b3c4d` — the traversal position, then the first eight hex digits of an MD5 over the file path, hunk header and body.

Both halves are load-bearing. The position depends only on traversal order, which the diff text fixes, so the same working tree always yields the same ids and a repeated `--dry-run` prints what it printed before. The hash is what separates two files changed *identically* — a vendored copy and its original produce the same header and the same body and differ in nothing but their path.

### 3.4 Grouping

The grouping is **one AI call, with no batching**. Batching is the obvious way to cover a diff too large for one prompt, and it is wrong for this task: hunks of one concern that fall on opposite sides of a batch boundary can never be reunited, because neither batch can see the other's hunks. The model then answers confidently about the half it can see. Split would rather degrade honestly — units that do not fit stay ungrouped and uncommitted — than produce a plan that looks complete and is not.

Every id the model returns is validated against the units actually sent. Unknown ids are discarded with a warning; duplicates are kept once; units the model never mentioned become ungrouped units. No invented unit ever enters a group, and no real unit is ever silently dropped.

When more units exist than `GITPR_SPLIT_MAX_HUNKS` allows, the largest are kept and the rest go to the ungrouped list with a warning naming their ids. Largest-first rather than first-N: trimming in file order would systematically starve the last files in the diff.

### 3.5 Conflict Pre-validation

Before the plan is shown, every group is run through `git apply --cached --check` against a clean index. A group that fails has every unit of every file it touches — from every group, and from the ungrouped list — merged into it, and its commit message is regenerated for the merged patch, because a message describing a subgroup would be a lie about the commit it labels.

The loop is bounded and always terminates. When forcing whole files still fails — a CRLF file, a binary unit — those units go to `ungrouped_units` with a warning. Nothing is dropped and nothing is half-applied.

A conflict out of a real `-U3` diff is rarer than it sounds. Git merges any two changes closer than seven lines apart into a single hunk, which leaves three lines of untouched context between the hunks it does emit, so any subset of them applies cleanly to an index that is at HEAD. The two ways a group is genuinely refused are a newline mismatch and two hunks covering the same lines.

### 3.6 Commit Messages

Each group's message comes from `generate_pr_content()` — the same function the default commit flow uses, receiving only that group's patch instead of the whole diff. Nothing in the message pipeline is duplicated: the `.gitpr.commit.md` skill, the MD5 prompt cache and the map-reduce path for oversized patches are inherited as they are.

A patch holding three of a file's nine hunks is built by rebuilding the file header and those three hunks, not by slicing the original diff text. A slice carries offsets that were correct in the whole-file diff and are wrong in the smaller one.

---

## 4. Applying

### 4.1 The Sequence

For each group, in the order the plan fixes:

1. Confirm the index is clean — nothing staged. Checked before every group, so a group that leaked past its own commit cannot be staged on top of the next one and surface later as a commit holding somebody else's work.
2. Rebuild the group's patch and run `git apply --cached --check`, then `git apply --cached`. Both go through the same `patch_applier` as `gitpr fix`, so the patch is fed to git as **bytes on stdin** — the defence against Windows's text-mode newline translation, which would otherwise turn every `\n` into `\r\n` and make git reject the whole patch, silently, and only there.
3. Verify that what reached the index is exactly the group: the path set from `git diff --cached --name-only -M` must equal the group's file set, and the per-file `(added, removed)` counts from `--numstat` must equal the counts read off the units' `+` and `-` lines. Numstat and not the hunk headers: a header's numbers describe the region it covers, context included, and they shift when a neighbouring commit moves the surrounding lines, so a header-based check would raise a false alarm on a plan that is perfectly correct.
4. Commit, with the group's generated message.
5. Confirm the index is clean again.

The working tree is never written to. Every file on disk keeps every change it had, staged or not; at the end, `git status` shows a clean tree and the commits hold the work.

### 4.2 What Is Left Behind

Units in `ungrouped_units` remain uncommitted and unstaged at the end. That is the honest outcome for a hunk the model would not classify, a group that could not be staged, or a unit trimmed away for exceeding the budget. They are listed in the report; the user commits them or runs `gitpr split` again over what is left.

### 4.3 When Something Fails Mid-sequence

There is **no automatic rollback**. A split produces ordinary commits, and undoing them is `git reset`, which the user already has. What the command guarantees instead is that it stops cleanly and says exactly what happened:

| Failure | What the index holds afterwards |
| --- | --- |
| Staging a group | Everything staged for that group is unstaged again, and the report says the run stopped at that group |
| Committing a group | The group stays staged, and the report says so verbatim — rather than hiding which units were in flight |
| Commits 1..N-1 | Untouched. They are real commits and they stay |

---

## 5. Skill Template

Split has **no skill template**, and reads none.

`.gitpr.split.md` would be the obvious shape, and it would be wrong. `get_skill_context()` answers an unregistered action type with the *review* skill — `DEFAULT_SKILL_TYPE = "review"` — so a call made before the type is registered everywhere would quietly hand the grouping prompt a code-review persona. Registering it properly means a new entry in `SKILL_FILES_BY_TYPE`, a new label in the configuration screen's order-asserted list, a new resource in the MCP server, a template per language and their translations: a large surface, for a prompt that describes a fixed response schema and should not be edited by hand.

The grouping instruction is therefore embedded in `hunk_grouper.py`, where it sits beside the code that parses its output.

---

## 6. Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `GITPR_SPLIT_MAX_GROUPS` | `5` | Upper limit on how many atomic commits a plan may propose |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | `true` | Shows the plan and asks before the first commit is created |
| `GITPR_SPLIT_MAX_HUNKS` | `50` | Upper limit on how many units are sent to the grouping call |

All three are editable in the configuration screen, under **Split**.

A non-positive or unparseable value for either ceiling falls back to the default rather than being honoured: a ceiling of zero would silently turn "split this" into "split nothing" instead of into an error anyone could see.
