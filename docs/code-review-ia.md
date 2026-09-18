# Technical Documentation: AI Code Review (--review / --fullreview / --input)

GitPR CLI offers four code review modes using artificial intelligence, each suited to a different moment in the development cycle. All modes automatically integrate with the **Static Linter** (`.gitpr.linter.yml`), which adds regex alerts to the top of the report.

---

## 1. Review Modes

### 1.1 Local Review — `gitpr -r` (or `--review`)

Analyzes only **uncommitted** changes in the working tree (`git diff HEAD`).

```bash
gitpr -r
```

| Characteristic | Description |
| --- | --- |
| **Data source** | `git diff HEAD` (local changes) |
| **When to use** | Before committing, to validate code quality |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt` |
| **Ideal for** | Quick review, pre-commit validation |

### 1.2 Full Review — `gitpr -f` (or `--fullreview`)

Compares **all** changes in the current branch against the remote main branch (`origin/main`).

```bash
gitpr -f
```

| Characteristic | Description |
| --- | --- |
| **Data source** | Full diff against `origin/main` (runs `git fetch` first) |
| **When to use** | Before opening a Pull Request |
| **Output** | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| **Ideal for** | Deep review of the entire feature branch |

### 1.3 File Audit — `gitpr -r -i <file>` (or `--review --input`)

Analyzes an **entire file**, ignoring the git diff. Useful for legacy code or refactoring.

```bash
gitpr -r -i src/legacy/parser.py
gitpr -f -i src/core.py
```

| Characteristic | Description |
| --- | --- |
| **Data source** | Full file content on disk |
| **When to use** | Legacy code refactoring, critical file auditing |
| **Output** | `{branch}_{datetime}_FILE_REVIEW.txt` |
| **Requires** | `--review` (`-r`) or `--fullreview` (`-f`) |

### 1.4 Remote Pull Request Review — `gitpr review-pr <number>`

Reviews a pull request that is **already open on the forge**, fetching its diff straight from the API. The branch does not have to be local: nothing is checked out, nothing is fetched into your tree. It is the mode for reviewing someone else's pull request.

```bash
gitpr review-pr 123
gitpr review-pr 123 --provider deepseek
gitpr review-pr 123 --post-comment
```

| Characteristic | Description |
| --- | --- |
| **Data source** | The diff served by the forge API for that pull request |
| **When to use** | Reviewing a pull request you were invited to, without checking out its branch |
| **Output** | `{branch}_{datetime}_PR_REVIEW.txt`, named after the pull request's source branch |
| **Publishing** | Nothing unless `--post-comment` is given; the review is then posted as a comment |
| **Requires** | A forge configured by `gitpr --init` that serves a unified diff — Azure DevOps does not |
| **Ideal for** | Code review of third-party contributions, and for repositories you never clone |

It runs the same engine, the same skill and the same cache as `gitpr -r`, so its report reads like a local review of the same diff. See the [Remote Pull Request Review documentation](review-pr.md) for the full contract — the rejections that cost no tokens, the smart-excludes filter, the cache scope and the comment footer.

---

## 2. Static Linter Integration

In all review modes, the **Static Linter** runs automatically. If there are violations of the rules defined in `.gitpr.linter.yml`, the alerts appear at the top of the report, before the AI analysis:

```
## 🚨 Local Static Analysis Alerts (YAML Rules)
- 🚨 console.log usage detected in app.js (Line 42)
- ⚠️ localhost usage detected in config.php (Line 15)

---

## 🤖 AI Code Review
...
```

In a remote pull request review (`gitpr review-pr`), only the YAML rules run: the external linter bridge executes binaries against files **on disk**, which in that mode would be whatever you have checked out rather than the pull request under review. Reviewing the wrong revision and publishing the alerts as a comment is worse than not running them.

---

## 3. Customization via Skills

The AI behavior during review can be customized through template files:

| File | Mode | Function |
| --- | --- | --- |
| `.gitpr.review.md` | `--review` / `--fullreview` | Defines the analysis focus (e.g.: SOLID, Clean Code, security) |
| `.gitpr.filereview.md` | `--input` (+ review) | Defines cohesion and coupling rules for full file auditing |

Download the templates with `gitpr -s` and edit them according to your team's business rules.

---

## 4. AI Provider Selection

```bash
gitpr -r -p deepseek        # Local review with DeepSeek
gitpr -f -p gemini          # Full review with Gemini
gitpr -r -i file.py -p deepseek  # Audit with DeepSeek
gitpr review-pr 123 --provider deepseek  # Remote review with DeepSeek
```

The root group's `-p` / `--provider` is not inherited by subcommands, so `gitpr review-pr` spells the same option `--provider`.

---

## 5. Environment Variables

| Variable | Mode | Default value |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r`, `review-pr` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Note:** See also the [Linter documentation](linter-regras-customizadas.md) for creating static validation rules.
