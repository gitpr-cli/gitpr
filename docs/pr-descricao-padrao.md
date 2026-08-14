# Technical Documentation: Pull Request Generation (Default Mode)

When run **without flags**, GitPR generates a complete Pull Request description in Markdown with AI — ready to be pasted into GitHub, GitLab, or Bitbucket — and opens an interactive panel (TUI) to review, edit, and publish the PR directly to GitHub without leaving the terminal.

---

## 1. Usage

```bash
gitpr
```

| Mode | Command | Behavior |
|---|---|---|
| Interactive (default) | `gitpr` | Generates the PR and opens the TUI to review and publish |
| Save only | `gitpr --no-publish` | Generates the PR and saves the `.md` file locally |
| Direct publish | `gitpr --no-edit` | Generates the PR, auto-commits, pushes, and publishes without the TUI |

---

## 2. Execution Flow

```
unstaged files check → git fetch → diff against origin/main → AI → .md → TUI → publish
```

1. **Unstaged files check** — Detects uncommitted files and offers staging (stage, skip, or cancel)
2. **`git fetch`** — Syncs with the remote repository
3. **Diff** — Compares all changes on the current branch against `origin/main`
4. **AI** — Generates the commit message (Conventional Commits) and the PR description
5. **Output** — Saves a `.md` file in `.gitpr/reports/pr_desc/`
6. **Publish** — Opens the TUI (`F3` = publish) or publishes directly with `--no-edit`

---

## 3. Output

The generated file (`{branch}_{datetime}_PR_DESC.md`) is saved in `.gitpr/reports/pr_desc/` and contains:

```markdown
# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
feat: short description of the change

---

## Description
...
## Changes
...
## Impact
...
```

---

## 4. Publishing the Pull Request

The publisher is available in 3 modes:

### 4.1 Interactive Mode (Default)

Running `gitpr` opens the TUI after generating the description. Shortcuts:

| Key | Action |
|---|---|
| **`F1`** | Help |
| **`F2`** | Save the `.md` file locally |
| **`F3`** | Publish the PR (auto-commit → push → create/update PR on GitHub) |
| **`Esc`** | Exit without publishing |

### 4.2 Save Only

```bash
gitpr --no-publish
```

Generates the description and saves the `.md` file without opening the TUI.

### 4.3 Direct Publish

```bash
gitpr --no-edit
```

Skips the TUI: auto-commits pending changes (linter + AI commit message), pushes, and publishes directly. Use with care — the content is not reviewed before publishing.

To publish, GitPR requires a GitHub **Personal Access Token (PAT)** with `repo` scope, stored encrypted in `~/.gitpr/.env`. The target branch is resolved via the `--base` flag → `PR_DEFAULT_BASE` env → auto-detection.

> **Note:** See the [complete publishing guide](pull-request-publication.md) for the detailed flow (unstaged check, auto-commit, merge, error handling).

---

## 5. Customization

### 5.1 PR Template

The AI behavior can be customized through the `.gitpr.pr.md` file:

```bash
gitpr -s          # Downloads the template
# Edit .gitpr.pr.md with your team's required sections
gitpr             # The AI will follow your template
```

### 5.2 Output File Name

Set the `OUTPUT_FILE_NAME` environment variable in the `~/.gitpr/.env` file:

```ini
OUTPUT_FILE_NAME=PR_{branch}_{datetime}.md
```

Available variables: `{branch}` (current branch name) and `{datetime}` (`YYYYMMDDHHMMSS` timestamp).

---

## 6. AI Provider Selection

```bash
gitpr -p gemini       # Forces Google Gemini
gitpr -p deepseek     # Forces DeepSeek
```

If no provider is specified, GitPR uses the default defined in the `DEFAULT_AI_PROVIDER` variable of `~/.gitpr/.env`.

---

## 7. Response Cache

GitPR generates an MD5 hash of the diff + AI instructions. If you run `gitpr` again **without changing the code**, the response is returned from the local cache in milliseconds, without consuming API quotas.

> **Note:** See also the [main documentation (README.md)](../README.md) for an overview of all features.
