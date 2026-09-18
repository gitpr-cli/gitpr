# Technical Documentation: Remote Pull Request Review (gitpr review-pr)

`gitpr review-pr <number>` reviews a pull request that is already open on the forge, fetching its diff straight from the API. The branch under review does not have to exist on your machine — you never check it out, never fetch it, and never touch your working tree. It is the mode for the reviewer who was invited to someone else's pull request, where the code to read lives on the other side of the network.

The review itself is not a second engine: it is `gitpr -r` with the diff coming from somewhere else. The same AI call, the same `.gitpr.review.md` skill, the same linter rules, the same report file and the same cache — which is why a remote review and a local one of the same diff read identically.

---

## 1. Overview

The subcommand is an addition to the CLI, not a change to it: every legacy option keeps its meaning, and the local flows (`gitpr -r`, `gitpr -f`, `gitpr fix`) are untouched by it. Reading is the default — with no flags the forge is only ever *read*, and nothing is published anywhere.

### 1.1 Command Reference — `gitpr review-pr`

All options of the subcommand, as shown by `gitpr review-pr -h` (or `--help`):

```bash
gitpr review-pr 123                    # review the pull request and save the .txt
gitpr review-pr 123 --provider deepseek  # review with a specific AI engine
gitpr review-pr 123 --post-comment     # also publish the review on the pull request
```

| Option | Description |
| --- | --- |
| **`<number>`** | The pull request number as shown on the forge (`123`). Required, and an integer — a non-numeric argument is a usage error |
| **`--provider <name>`** | Forces the AI engine for this run (`gemini`, `deepseek` or `ollama`). Without it the configured default is used |
| **`--post-comment`** | Publishes the review as a comment on the pull request. **Without it the forge is never written to** |

| Characteristic | Description |
| --- | --- |
| **Data source** | The diff served by the forge API for that pull request — never your working tree |
| **Forge** | Whatever `gitpr --init` configured (GitHub, GitLab, Bitbucket). Azure DevOps is refused — see §3 |
| **AI call** | One call, on the advanced model of the configured provider, cached under `review/` like every other GitPR call |
| **Files written** | `{branch}_{datetime}_PR_REVIEW.txt` in the reports folder (`OUTPUT_FILE_NAME_REVIEW`) |
| **Published** | Nothing, unless `--post-comment` is given |
| **Local tree** | Never read, never checked for unstaged files, never modified — no checkout, no fetch, no branch switch |
| **Exit code 1** | No forge configured, an unreviewable forge, a pull request that does not exist or is not open, an empty or filtered-out diff, an unreachable API, no AI key |

---

## 2. What a Remote Review Is

### 2.1 The Diff Comes from the API

The forge is asked for the pull request metadata first, then for its diff:

| Step | What it establishes |
| --- | --- |
| `get_pull_request` | That the number exists, what state it is in, and which branches it joins |
| `get_pull_request_diff` | The unified diff to review |

Resolving the number directly is what makes "does not exist" distinguishable from "was merged last week": listing open pull requests returns only open ones, so a number missing from that list could be either. The metadata also supplies the two branches the report needs to name.

The metadata request is not decoration — it is what keeps a stale number from spending tokens (§4.2).

### 2.2 The Diff Is Normalized

A diff that never passed through git arrives in whatever shape the forge chose to send. Three things are settled before the AI sees it:

| Step | Why |
| --- | --- |
| **Line endings unified to LF** | GitLab and Bitbucket serve CRLF on Windows-authored branches, and the chunker splits on `^diff --git a/`, which a stray `\r` throws off |
| **The content is confirmed to be a diff** | A provider that claims to serve diffs but answers with prose stops here instead of being reviewed as if it were code |
| **Smart excludes applied** | The lockfiles and minified assets are filtered out of the *reviewed* diff, not out of a local one (§2.3) |

### 2.3 Smart Excludes Run in Python Here

Every local diff gets its smart-excludes applied by git itself, as `:(exclude)` pathspecs. A diff that arrives over the API never passes through git, so the same patterns are applied in Python, one file section at a time, and the files that were dropped are named in a warning:

```text
⚠️  3 file(s) skipped by the smart excludes: package-lock.json, poetry.lock, dist/app.min.js
```

The pattern list is the same one the local flows use (`~/.gitpr/conf/gitpr.smart-excludes.json`), and `GITPR_SKIP_SMART_EXCLUDES` disables it here too. A pull request whose every file is a lockfile has nothing left to review, and says so rather than sending an empty diff to the model.

### 2.4 It Is Cached Apart from the Local Review

The MD5 cache key is built from the prompt, and a prompt is built from the diff — so a remote review of a branch that happens to be checked out locally would produce a byte-identical prompt and be answered by the cached local review. The remote flow therefore appends a scope to the cache key:

```text
::diff-source::pr-123
```

The scope is added to the cache key **only** — never to the text sent to the AI. The consequence for an installed user is zero: the local flows pass an empty scope, so their keys are byte-identical to the ones they have always had, and no existing cache entry is invalidated.

### 2.5 The Reviewed Diff Is Recorded

The review is stored in the cache with the diff it was produced from, which is what lets `gitpr fix` patch the revision that was actually reviewed instead of re-deriving a diff from your tree. For a remote review this is not a convenience but the only correct source: the branch may not exist locally at all. See the [Fix Command documentation](fix-command.md) for what reads it back.

The record is filed under the repository and the branch **you are on** — the same fields every cached review carries, because that is what `gitpr fix` resolves to find it. The pull request's own branches are recorded inside the entry (as the `{branch}` of the report name and in the diff source), but they do not address it: reviewing PR #123 while on `develop` files the review under `develop`.

---

## 3. Which Forges Can Be Reviewed

A review needs a unified diff, and not every forge serves one.

| Forge | Remote review | Why |
| --- | --- | --- |
| **GitHub** | Yes | `GET /repos/{owner}/{repo}/pulls/{n}/files` with `Accept: application/vnd.github.diff` |
| **GitLab** | Yes | `changes[].diff` per file, with the file headers synthesized (§3.1) |
| **Bitbucket** | Yes | `GET .../pullrequests/{n}/diff` |
| **Azure DevOps** | **No** | Its API returns a list of changed files with line counts, not a unified diff. Refused before any network call, with a message pointing to the local review |

The capability is declared by the provider itself (`supports_reviewable_diff` on the `ScmProvider`), so a forge added later states its own answer rather than being guessed at. Behind that flag sits a second, cheaper net: the fetched content is checked for actual diff structure, so a provider that declares the capability and then answers with a file summary is caught anyway (§2.2).

### 3.1 GitLab: The File Headers Are Synthesized

The GitLab API returns each changed file's `diff` field as a bare hunk, with the file's identity in separate `old_path` / `new_path` fields. Read as-is, the review would have been handed anonymous hunks — the AI could not say which file a change belonged to, and neither the smart-excludes filter nor the chunker could work, since both key off the `diff --git a/…` line. The provider rebuilds that header before each hunk:

```diff
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
```

GitLab also flags when it truncated a diff for being over the API's size limit (`overflow: true`). A truncated diff is not a diff, so it is refused outright with a message telling the reviewer to review that merge request locally, rather than being reviewed halfway and the result published as if it were whole.

---

## 4. The Report, Warnings and Failures

### 4.1 The Report

The output is the same file the local review writes, through the same rendering code — linter block on top, AI review below — with one difference in the name: the `{branch}` slot carries the pull request's **source** branch, sanitized for the filesystem (`feature/login` becomes `feature-login`), because the report belongs to the revision being reviewed and not to whatever branch you happen to have checked out. A pull request whose branch is unnamed falls back to `pr-123`.

```text
✅ Code Review successfully generated: 'feature-login_20260917143210_PR_REVIEW.txt'
```

Nothing else is printed: the review is never echoed to the terminal, exactly as in the local flows. The report path is configured by `OUTPUT_FILE_NAME_REVIEW`, the same variable the local review uses — the remote mode introduces no new configuration.

### 4.2 Rejections That Cost Nothing

Everything the user can act on is refused **before** the AI is called, so a bad number, a closed pull request or a forge with the wrong token costs no tokens:

| Situation | Message |
| --- | --- |
| The forge does not serve a reviewable diff | `{provider} does not serve a reviewable diff: … Review this pull request locally, or use a forge that serves diffs.` |
| The number does not exist | `Pull request #123 was not found in {repo}.` |
| The token cannot read it (401/403) | `No permission to read pull request #123 in {repo}. Check the token configured for {provider} (gitpr --init).` |
| It is closed or merged | `Pull request #123 is not open (state: closed). Only open pull requests can be reviewed.` |
| The diff came back empty | `Pull request #123 has no diff to review.` |
| It came back as a file summary | `{provider} returned a file summary instead of a diff for pull request #123. It cannot be reviewed.` |
| Every file matched the smart excludes | `Every file of pull request #123 matches the smart excludes — nothing left to review.` |
| The model returned nothing usable | `The AI returned no review for pull request #123.` |

The four open states across the supported forges — GitHub `open`, GitLab `opened`, Azure `active`, Bitbucket `OPEN` — are compared case-folded, so one check covers them all. A provider that reports no state at all is let through rather than refused over a field it never promised.

### 4.3 Warnings

Warnings are things the user should know that did not stop the run. They are printed before the report and, with `--post-comment`, published inside the comment — a reader on the pull request deserves to know the review skipped three lockfiles.

| Warning | When |
| --- | --- |
| `{count} file(s) skipped by the smart excludes: {files}` | The filter dropped at least one file |
| `Large diff: processed in {count} batches (map-reduce).` | The diff is big enough for the engine to split it |

The batch count is asked of the chunker rather than observed from the engine's terminal line, because the MCP tool has no terminal to read it from. A chunker that fails to answer is not a failure: the warning is a courtesy and never the reason a run dies.

### 4.4 A Failed Run Writes Nothing

Any failure exits with code 1, prints the reason to stderr, and writes **no report** — a `.txt` on disk means a review exists, and "the review failed" is never allowed to look like "the review found nothing". The command also never retries: the pipeline raises before the engine, so there is no second call to pay for.

---

## 5. Publishing — `--post-comment`

With `--post-comment`, the review is posted as a comment on the pull request itself. It is one comment, created after the review succeeded and the linter has run, and it is **always a new comment** — an earlier review by the same tool is left where it is, because overwriting a comment somebody may have replied to is not this command's decision to make.

The body is the report body plus a footer:

```markdown
## 🚨 Local Static Analysis Alerts (YAML Rules)

- 🚨 console.log usage detected in app.js (Line 42)

---

## 🤖 AI Code Review

…

---

*Automated review by GitPR 1.1.0 — AI provider: Gemini. AI-generated content: verify before acting on it.*
```

The footer is there because the comment lands on **someone else's** pull request: a reader who never ran the command has no other way to know a model wrote it. The alerts are composed by the very same function that composes the `.txt`, so the file and the comment can never read differently.

No commit SHA appears anywhere in it. The forge result carries none, and inventing one on a public comment would be worse than omitting it.

If the review fails, nothing is posted — the comment exists only downstream of a review that produced something. If the *comment* fails (a token that can read but not write), the error surfaces as a forge error and the run exits 1: the review was produced, but it was not published.

---

## 6. Skill Template — `.gitpr.review.md`

The remote review uses the same system instruction as the local one: `.gitpr.review.md` (persona and review focus), downloaded by `gitpr --skill` — language-aware and never overwriting an existing file. There is no remote-specific skill type; a review that read differently depending on where the diff came from would defeat the point of sharing the engine.

---

## 7. MCP Integration

`review_remote_pr` is the 14th MCP tool and is **read-only**: it reviews an open pull request and returns the review and the linter alerts, and it has no way to publish anything. There is no `post_comment` argument, on purpose — a tool an agent calls on its own must not be able to write to somebody's pull request.

```json
{"status": "success", "pr_number": 123, "pr_url": "…", "head_branch": "feature/login",
 "base_branch": "main", "origin": "remote_pr", "linter": {…}, "warnings": [], "review": "…"}
```

Unlike the CLI it writes no `.txt` — MCP tools do not write artefacts — and it resolves the forge itself, so a repository with no forge configured answers with a JSON error naming `gitpr --init` instead of a terminal message. The status is `error` with a `message` for every rejection in §4.2. See the [MCP Integration documentation](mcp-integration.md).

---

## 8. Environment Variables

The remote review introduces **no new configuration**. It reads what the local review already reads:

| Variable | Purpose |
| --- | --- |
| `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN` / `GITPR_SCM_TOKEN_ENCRYPTED` | The forge and its token, configured by `gitpr --init` |
| `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` | Forge extras (self-hosted GitLab, Azure, Bitbucket) |
| `OUTPUT_FILE_NAME_REVIEW` | Name of the report (default `{branch}_{datetime}_PR_REVIEW.txt`) |
| `DEFAULT_AI_PROVIDER` | AI engine used when `--provider` is not given |
| `GITPR_SKIP_SMART_EXCLUDES` | Disables the smart-excludes filter, local or remote |

> **Note:** See also the [AI Code Review documentation](code-review-ia.md) for the review modes and the [Fix Command documentation](fix-command.md) for what consumes the recorded diff.
