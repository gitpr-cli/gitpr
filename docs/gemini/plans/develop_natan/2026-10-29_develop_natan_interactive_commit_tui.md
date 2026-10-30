# Implementation Plan: Interactive Commit TUI Flow (`gitpr -c`, `--commit`)

## Goal Description
Enhance `gitpr -c` / `gitpr --commit` from a simple console prompt/suggestion tool into a complete, interactive Textual TUI workflow (`CommitApp`).
When invoked, `gitpr -c` will:
1. Detect files outside the staging area and display the interactive Stage Selector (`StageFilesScreen`).
2. Add only the user-selected files to the Git stage via `stage_files()`.
3. Generate the commit message using AI based on the staged diff (`git diff --cached`).
4. Display the Commit Message Screen (`CommitMessageScreen`) allowing the user to review and edit the suggested Conventional Commit message.
5. Upon confirmation, display the animated progress modal (`CommitProgressScreen`), execute the actual `git commit`, log the outcome, and provide a clean close action.
6. Preserve strictly non-interactive behavior when executed via Git hook (`--hook`).

---

## User Review Required

> [!IMPORTANT]
> **Behavioral Change for `gitpr -c`**:
> Previously, `gitpr -c` in the console only printed the generated commit message to `stdout` and did not execute `git commit`. With this change, running `gitpr -c` launches an interactive TUI that **executes** the commit upon confirmation in the modal.
> Hook mode (`gitpr -c --hook <path>`) remains purely non-interactive, writing directly to the hook file without launching any UI.

---

## Proposed Changes

### 1. Core Utilities (`src/core.py`)

#### [MODIFY] `src/core.py`
- Add `get_git_staged_diff()` to retrieve the diff of staged changes (`git diff --cached`) filtered with `SMART_EXCLUDES`.
- This ensures the AI model generates the commit message specifically for the changes that will be committed, even if other untracked or unstaged modifications exist in the working directory.

```python
def get_git_staged_diff():
    """Runs 'git diff --cached' and returns the output filtered by SMART_EXCLUDES."""
    try:
        cmd = ["git", "diff", "--cached", "-U1", "-w", "-M", "-B", "--"] + SMART_EXCLUDES
        result = subprocess.run(
            cmd,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout
    except Exception:
        return ""
```

---

### 2. Interactive Commit TUI (`src/ui/commit_app.py`)

#### [NEW] `src/ui/commit_app.py`
Create a dedicated `CommitApp(App)` leveraging the existing modal screens from `src/ui/pr_publish_app.py`:
- `StageFilesScreen`
- `CommitMessageScreen`
- `CommitProgressScreen`
- `LinterErrorScreen`

**Workflow Steps within `CommitApp`**:
1. **On Mount**:
   - Inspect unstaged files via `get_unstaged_files()`.
   - If unstaged files exist and not skipped:
     - Push `StageFilesScreen(unstaged)`.
     - On `"stage"`: call `stage_files(selected_files)` and proceed to Step 2.
     - On `"skip"`: proceed to Step 2 with existing staged files.
     - On `"cancel"`: exit app immediately.
   - If no unstaged files exist:
     - Check if there are staged changes (`get_git_staged_diff()`).
     - If no staged changes exist, verify if working tree has untracked/modified changes. If clean: show notice or exit.
2. **Commit Message Generation**:
   - Push `CommitProgressScreen` with title `__("📝 Generating commit message...")` and bouncing bar animation.
   - Run AI generation in a worker thread (`generate_pr_content("commit", "commit", staged_diff, provider)`).
   - Once AI returns: pop progress screen, push `CommitMessageScreen(commit_msg)`.
3. **Commit Message Review**:
   - User reviews / edits commit message.
   - On `"cancel"`: exit app without committing.
   - On `"confirm"`: retrieve edited message, proceed to Step 4.
4. **Execution & Animation Modal**:
   - Push `CommitProgressScreen` with title `__("📦 Executing commit...")` and animated gradient bar.
   - Worker thread runs:
     - `append_coauthor_trailer(message)`
     - `execute_git_commit(message)`
     - Update log on screen: `add_log(__("✅ Commit successfully created!"))` or error.
     - Call `mark_finished(show_close=True)` allowing user to dismiss and exit.

---

### 3. CLI Entry Point Routing (`src/main.py`)

#### [MODIFY] `src/main.py`
- In `cli()` when `commit` is True:
  - If `hook`: retain current hook behavior (inject into file and exit).
  - If not `hook`:
    - Check if working tree has any changes at all before launching TUI; if completely clean, report with `click.secho` and exit cleanly.
    - Otherwise, import and instantiate `CommitApp(provider=active_provider, skip_unstaged=no_unstaged_check)`.
    - Run `app.run()`.
    - Return gracefully.

---

### 4. Automated Tests (`tests/test_commit_app.py`)

#### [NEW] `tests/test_commit_app.py`
Create a comprehensive test suite for `CommitApp` using Textual's test runner (`app.run_test()`):
- `test_commit_app_stages_files_and_executes_commit`: tests full flow from stage selection to commit execution.
- `test_commit_app_skips_stage_selector_when_no_unstaged_files`: tests direct message generation when files are already staged.
- `test_commit_app_cancel_at_stage_selector_aborts`: ensures cancelling stage selector exits cleanly.
- `test_commit_app_cancel_at_commit_message_modal_aborts`: ensures cancelling at message review does not commit.
- `test_commit_app_shows_animated_progress_modal_during_commit`: asserts `CommitProgressScreen` is displayed during commit execution.

---

## Verification Plan

### Automated Tests
Run the entire unit and TUI test suite via:
```bash
pipenv run pytest tests/test_commit_app.py -v
pipenv run pytest tests/test_pr_publish_app.py -v
```

### Manual Verification
1. Run `gitpr -c` with unstaged files:
   - Verify that `StageFilesScreen` is shown with checkboxes for unstaged files.
   - Select a subset of files and click "Stage Selected".
   - Verify that the commit message generation starts with status animation.
   - Verify that `CommitMessageScreen` appears with the editable message.
   - Click "Confirm".
   - Verify that `CommitProgressScreen` with animated bar opens, executes the commit, logs the commit message/SHA, and presents a "Close" button.
2. Run `gitpr -c` with only already staged files:
   - Verify `StageFilesScreen` is skipped and it proceeds directly to message generation.
3. Run `gitpr -c --hook <test_file>`:
   - Verify it runs without any UI and injects the message into `<test_file>`.
