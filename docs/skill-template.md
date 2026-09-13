# Technical Documentation: Skills and Templates System (--skill)

GitPR uses a **Skills** (Prompt Engineering) system that allows customizing the artificial intelligence behavior according to your company's business rules. The template files act as the AI's *System Instructions*.

---

## 1. Downloading Templates

```bash
gitpr -s
# or
gitpr --skill
```

This command creates the following files in the project's `.gitpr/skill/` folder:

| File | Function |
| --- | --- |
| `.gitpr.commit.md` | Rules for commit message generation |
| `.gitpr.pr.md` | Required structure for Pull Request description |
| `.gitpr.review.md` | Architecture focus for diff code review |
| `.gitpr.filereview.md` | Cohesion rules for full file auditing |
| `.gitpr.issue.md` | Structure and detail for Issue generation |
| `.gitpr.blame.md` | Focus of archaeological code analysis |
| `.gitpr.release.md` | Rules for the AI executive summary of `gitpr release` |
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
| `gitpr release` | `.gitpr.release.md` |
| `gitpr -l` / `gitpr -r` | `.gitpr.linter.yml` |

If the skill file does not exist, GitPR uses a default internal template.

**Release skill auto-download:** unlike the other skills (downloaded only via `gitpr -s`), `.gitpr.release.md` is also downloaded automatically on the **first** `gitpr release` run, respecting the interface language (EN + `pt_br`, `pt_pt`, `es_es`, `fr_fr` variants). It is never downloaded in `--format json` mode (stdout-only contract), never overwrites an existing file, and a network failure is non-fatal (the built-in persona is used instead). The file acts as the *system instruction* of the AI executive summary — edit it to customize the summary wording.

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

---

## 5. Editing from the `gitpr config` Screen

`gitpr config` has a **Skills** section that lists these same files and opens each one in an editor, so a rule can be adjusted without leaving the terminal ([Interactive Configuration Screen](config-tui.md), §1.7).

- One entry per skill GitPR supports — the seven `.gitpr.*.md` files of section 1 above.
- A skill the project does not have yet is listed as **not in this project**, with a **📥 Download the template** button that fetches the published template for your interface language.
- `F2` writes the edited skills together with the `.env` settings; `Ctrl+R` inside the pane drops the edit and restores the text on disk.
- Each file keeps the line endings it already had, so saving never turns an untouched line into a change.

Two things stay out of that list on purpose: `.gitpr.linter.yml`, which no command loads through this mechanism ([Custom Linter Rules](linter-regras-customizadas.md)), and any other file you keep in `.gitpr/skill/` — the screen offers the skills the commands read, not everything the folder holds.
