# Technical Documentation: AI Commit Message Generation (--commit)

The GitPR `--commit` (`-c`) command automatically generates commit messages in the **Conventional Commits** format using artificial intelligence to analyze your local changes.

---

## 1. Basic Usage

```bash
gitpr -c
```

The tool analyzes `git diff HEAD` and displays the suggested message directly in the console:

```
📝 Commit Suggestion:

feat: add email validation to registration form

- Implement RFC 5322 validation regex
- Add localized error messages (en-US)
- Fix edge case with international domain emails
```

---

## 2. Conventional Commits Format

The AI is instructed to generate messages in the standard:

```
type: short description

Optional body with additional details
```

**Types used:** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Git Hooks Integration

`--commit` is used internally by the `prepare-commit-msg` hook. When installed via `gitpr -ih`, the hook runs:

```bash
gitpr --commit --hook <temporary-file-path>
```

The `--hook` flag (internal/hidden) causes the suggested message to be injected directly into the Git editor, instead of being displayed in the console.

---

## 4. Customization via Skill

The AI behavior can be customized through the `.gitpr.commit.md` file at the project root:

```bash
gitpr -s          # Downloads the .gitpr.commit.md template
# Edit the file according to your team's conventions
gitpr -c          # The AI will use your customized rules
```

---

## 5. AI Provider Selection

```bash
gitpr -c -p gemini       # Force Google Gemini
gitpr -c -p deepseek     # Force DeepSeek
```

---

## 6. Response Cache

GitPR generates an MD5 hash of your diff + instructions. If you run `gitpr -c` again **without changing the code**, the response is returned instantly from the local cache, saving API quotas.

> **Note:** See also the [main documentation (README.md)](../README.md) for an overview of all features.
