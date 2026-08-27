# Manual E2E — PR Publisher with a linter-breaking diff

This runbook covers a path the automated suite **cannot** reach. The headless tests
(`tests/test_pr_publish_app.py`, `tests/test_pr_publish_linter_modal.py`) mock Git,
the AI provider and the GitHub API, so they verify the *wiring* of the linter modal
but never the real thing: a real `git diff`, a real linter run, a real TUI render and
a real decision to publish or not.

Run this before any release that touches the PR publisher, the linter engine or the
commit flow.

* **Time:** ~15 minutes
* **Prerequisites knowledge:** none — every step is literal
* **Never run this against a repository you care about.** Scenario D pushes a real
  branch; use a scratch repo you own.

---

## 0. Pre-conditions

Complete every item before starting. A skipped pre-condition invalidates the run.

| # | Pre-condition | How to verify |
| --- | --- | --- |
| 0.1 | GitPR installed and runnable | `gitpr --status` exits 0 |
| 0.2 | An AI provider configured with a working key | `gitpr --status` shows a provider and a valid key |
| 0.3 | A GitHub PAT with `repo` scope stored | `gitpr --status` shows the GitHub token as valid |
| 0.4 | A **scratch** GitHub repository you own, cloned locally | `git remote -v` points at the scratch repo |
| 0.5 | `main` exists on the remote | `git ls-remote --heads origin main` returns a ref |
| 0.6 | Linter is **not** globally disabled | `GITPR_SKIP_LINT` is unset or `false` in `~/.gitpr/.env` |
| 0.7 | Auto-commit prompts are **not** suppressed | `GITPR_AUTO_COMMIT` is unset or `false` in `~/.gitpr/.env` |

> **0.6 matters most.** `GITPR_SKIP_LINT=true` makes `_run_linter_and_commit` skip the
> linter entirely and every scenario below silently "passes" while testing nothing.

### Reference linter configuration

Fixed so results are identical for every tester. Create **exactly** this file at
`.gitpr/skill/.gitpr.linter.yml` in the scratch repo:

```yaml
rules:
  - name: "e2e-no-console-log"
    level: "error"
    extensions: ["js"]
    regex: 'console\.(log|debug|info)\s*\('
    message: "🚨 console.log not allowed in {file_name} (Line {line_number})."
    ignore_comments: true

  - name: "e2e-todo-warning"
    level: "warning"
    extensions: ["js"]
    regex: 'TODO'
    message: "⚠️ TODO left in {file_name} (Line {line_number})."
    ignore_comments: false
```

Verify it is picked up before continuing:

```bash
echo "console.log('x')" > probe.js
git add probe.js
gitpr --linter          # must report 1 error for probe.js
git rm -f --cached probe.js && rm probe.js
```

**PASS:** one `e2e-no-console-log` error is reported.
**FAIL:** no error → the config is in the wrong place; check `.gitpr/skill/`.

### Starting state for every scenario

```bash
git checkout main && git pull
git checkout -b e2e/linter-check-$(date +%s)
```

---

## Scenario A — Violation in a tracked file

**Goal:** the linter error modal appears in the real TUI and blocks publication.

### Steps

1. Create and commit a clean tracked file:
   ```bash
   echo "export const ok = 1;" > app.js
   git add app.js && git commit -m "chore: add app.js"
   ```
2. Introduce a violation **and stage it** (`git diff HEAD` only sees tracked changes):
   ```bash
   echo "console.log('debug');" >> app.js
   git add app.js
   ```
3. Run the publisher: `gitpr`
4. Wait for the TUI with the PR title and body.
5. Press **F3**.
6. At *"Uncommitted changes detected. Auto-commit before publishing?"*, choose **Yes**.
7. Observe the progress screen, then the modal.

### Expected result

| Step | Expected | PASS criterion |
| --- | --- | --- |
| 3–4 | TUI opens, title and body populated by the AI | Both fields non-empty; header shows `branch → main` |
| 5–6 | Commit confirmation modal appears | Modal is readable, buttons not overlapping |
| 7 | Progress screen logs `🔍 Running linter...` then `🚨 …console.log not allowed…` | The violation text names `app.js` and the correct line |
| 7 | **Linter error modal** replaces the progress screen | Both buttons — *Commit with --no-verify* and *Abort* — visible, side by side, fully rendered, not overlapping |

**FAIL if:** the modal never appears; the flow commits anyway; the buttons overlap or
are cut off; the error text names the wrong file or line.

> Leave this modal open — Scenario B continues from here.

---

## Scenario B — Abort is non-destructive

**Goal:** aborting leaves the repository untouched. This is the most important
scenario: a false "success" here means data loss risk in production.

### Steps

1. From Scenario A's open modal, click **Abort**.
2. The TUI returns to the PR edit screen.
3. Press **Esc** to exit.
4. Inspect the repository:
   ```bash
   git log --oneline -3
   git status --short
   git ls-remote --heads origin | grep e2e/
   ```

### Expected result

| Check | Expected | PASS criterion |
| --- | --- | --- |
| Modal | Dismisses, returns to the PR TUI | No crash, no traceback |
| `git log` | **No new commit** beyond `chore: add app.js` | Top commit unchanged |
| `git status` | `app.js` still staged and modified | The change was neither committed nor discarded |
| `git ls-remote` | Branch **not** pushed | No `e2e/` ref on the remote |
| GitHub UI | **No pull request created** | PR list unchanged |

**FAIL if:** a commit was created, the branch was pushed, a PR exists, or the staged
change was silently discarded.

---

## Scenario C — Violation in a new (previously untracked) file

**Goal:** document and confirm the untracked-file behavior, which surprises users.

### Steps

1. Continue on the same branch. Create a **new, untracked** file with a violation:
   ```bash
   echo "console.log('new file');" > brand-new.js
   ```
   Do **not** `git add` it yet.
2. Run `gitpr` and press **F3**, choose **Yes**.
3. Observe whether the violation in `brand-new.js` is reported.
4. Exit (**Esc**). Now stage the file and repeat:
   ```bash
   git add brand-new.js
   gitpr    # F3 → Yes
   ```

### Expected result

| Step | Expected | PASS criterion |
| --- | --- | --- |
| 2–3 | `brand-new.js` is **not** linted while untracked | The linter does not report `brand-new.js` |
| 2–3 | GitPR surfaces the untracked file to the user | A staging prompt or an untracked-files warning names `brand-new.js` |
| 4 | After `git add`, the violation **is** reported | Linter error modal appears naming `brand-new.js` |

> **This is expected behavior, not a bug.** The linter runs on `git diff HEAD`
> ([`core.py` `get_git_diff`](../../src/core.py)), which by definition excludes
> untracked files. Staging is what makes a new file visible to the analysis.

**FAIL if:** step 4 does **not** report the violation after staging (that would be a
real detection bug), or if the untracked file is never surfaced to the user at all.

Abort the modal before continuing.

---

## Scenario D — Publication succeeds after the violation is fixed

**Goal:** the publisher proceeds normally once the code is clean.

### Steps

1. Remove every violation, keep a warning to prove warnings do not block:
   ```bash
   git checkout -- . 2>/dev/null; rm -f brand-new.js
   printf "export const ok = 1;\n// TODO: refine later\n" > app.js
   git add app.js
   ```
2. Run `gitpr`, press **F3**, choose **Yes**.
3. On the commit-message modal, edit the message to `feat: e2e verified message`
   and click **Confirm**.
4. Let the flow push and create the PR.
5. Open the PR on GitHub.

### Expected result

| Step | Expected | PASS criterion |
| --- | --- | --- |
| 2 | Progress logs `⚠️ …TODO…` then `✅ Linter passed with warnings.` | Warning shown, flow **not** blocked |
| 2 | **No** linter error modal | Flow proceeds to the commit message |
| 3 | Commit-message modal is editable | Edited text is accepted |
| 4 | Branch pushed, PR created, URL reported | TUI reports success with a PR URL |
| 5 | PR exists with the edited title | `git log -1 --pretty=%s` equals `feat: e2e verified message` |

**FAIL if:** the warning blocks the flow; the edited commit message is discarded and
the original AI text is used; the PR is created with the wrong title or body.

---

## Scenario E — `--no-verify` resumes without re-running the linter

**Goal:** confirm the historical infinite-loop bug stays fixed (choosing
`--no-verify` used to re-run the linter and bounce straight back into the modal).

### Steps

1. New branch, reintroduce a violation, stage it:
   ```bash
   git checkout main && git checkout -b e2e/no-verify-$(date +%s)
   echo "console.log('loop check');" >> app.js && git add app.js
   ```
2. Run `gitpr`, **F3**, **Yes**, wait for the linter error modal.
3. Click **Commit with --no-verify**.

### Expected result

| Check | Expected | PASS criterion |
| --- | --- | --- |
| After click | Flow **resumes**; progress screen shows `📝 Generating commit message...` | The linter does **not** run again |
| Modal | The linter error modal does **not** reappear | Appears exactly once for the whole run |
| Commit | Commit is created despite the violation | `git log -1` shows the new commit |

**FAIL if:** the modal reappears, the flow stalls on a dead progress screen, or
nothing happens at all.

---

## Cleanup

```bash
git checkout main
git branch -D $(git branch --list 'e2e/*' | tr -d ' *')
git push origin --delete <any e2e/* branch that was pushed>
```
Close any PR opened by Scenario D, and delete `.gitpr/skill/.gitpr.linter.yml` if the
scratch repo is reused for other testing.

---

## Result sheet

| Scenario | PASS / FAIL | Tester | Date | Notes |
| --- | --- | --- | --- | --- |
| A — Violation in tracked file | | | | |
| B — Abort is non-destructive | | | | |
| C — New/untracked file | | | | |
| D — Publish after fix | | | | |
| E — `--no-verify` resumes | | | | |

**Environment recorded for this run:** GitPR version (`gitpr --status`), OS + terminal,
AI provider, and whether any external linter was configured.

---

## Related

* [tests/test_pr_publish_linter_modal.py](../../tests/test_pr_publish_linter_modal.py) — headless coverage of the modal
* [tests/test_pr_publish_app.py](../../tests/test_pr_publish_app.py) — headless coverage of the surrounding flow
* [linter-regras-customizadas.md](../linter-regras-customizadas.md) — linter rule reference
* [pull-request-publication.md](../pull-request-publication.md) — PR publisher documentation
* [untracked-files.md](../untracked-files.md) — why untracked files are excluded
