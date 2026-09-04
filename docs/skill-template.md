# Technical Documentation: Skills and Templates System (--skill)

GitPR uses a **Skills** (Prompt Engineering) system that allows customizing the artificial intelligence behavior according to your company's business rules. The template files act as the AI's *System Instructions*.

---

## 1. Downloading Templates

```bash
gitpr -s
# or
gitpr --skill
```

This command creates the following files at the root of your project:

| File | Function |
| --- | --- |
| `.gitpr.commit.md` | Rules for commit message generation |
| `.gitpr.pr.md` | Required structure for Pull Request description |
| `.gitpr.review.md` | Architecture focus for diff code review |
| `.gitpr.filereview.md` | Cohesion rules for full file auditing |
| `.gitpr.issue.md` | Structure and detail for Issue generation |
| `.gitpr.blame.md` | Focus of archaeological code analysis |
| `.gitpr.linter.yml` | Regex rules for static validation |

> **Important:** The `--skill` command **never overwrites** existing local files. If a `.gitpr.*.md` already exists, it is preserved.

---

## 2. How It Works

Each GitPR command automatically looks for the corresponding skill file:

| Command | Skill file used |
| --- | --- |
| `gitpr -c` | `.gitpr.commit.md` |
| `gitpr` (default) | `.gitpr.pr.md` |
| `gitpr -r` / `gitpr -f` | `.gitpr.review.md` |
| `gitpr -r -i file` | `.gitpr.filereview.md` |
| `gitpr -is` | `.gitpr.issue.md` |
| `gitpr -b file` | `.gitpr.blame.md` |
| `gitpr -l` / `gitpr -r` | `.gitpr.linter.yml` |

If the skill file does not exist, GitPR uses a default internal template.

---

## 3. Customization Example

**File `.gitpr.commit.md`:**

```markdown
All commit messages MUST:
- Use mandatory JIRA prefix: [PROJ-1234]
- Follow Conventional Commits (feat, fix, refactor...)
- Be written in English
- Not exceed 72 characters in the subject line
```

After creating this file, all `gitpr -c` executions will follow these rules.

---

## 4. Remote Templates

The official templates are available at:
```
https://github.com/gitpr-cli/gitpr.git/tree/main/templates/
```

The `--skill` command downloads the latest version of each template from the official repository.

> **Note:** Skill files can be committed to your team's repository to share the rules with all developers.
