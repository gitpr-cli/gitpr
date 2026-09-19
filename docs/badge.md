# Technical Documentation: Pull Request Badge

Every pull request GitPR publishes carries a small badge at the foot of the body: `GitPR` and the linter counts for the change. It is built from a measurement GitPR actually made — the local static linter, over the diff being published — and it is a Markdown image that shields.io renders in the reader's browser, so nothing is fetched while the pull request is being written.

There is a second, static badge for a project's own README. `gitpr badge --readme` prints the snippet and writes nothing.

---

## 1. Overview

The badge is an opt-out feature. It is on by default, it never asks anything — no prompt, no first-run confirmation — and it is announced twice: once when `gitpr --init` configures a forge, which is where publishing becomes possible, and once on a publish that attaches it without you having seen the body first.

### 1.1 Command Reference — `gitpr badge`

All options of the subcommand, as shown by `gitpr badge -h` (or `--help`):

```bash
gitpr badge                          # what it is, plus the snippet
gitpr badge --readme                 # only the snippet, ready to pipe
gitpr badge --style for-the-badge    # another shields.io style
```

| Option | Description |
| --- | --- |
| **`--readme`** | Prints only the snippet, with nothing around it — safe for `>>` and for piping |
| **`--style <style>`** | `flat` (default), `flat-square` or `for-the-badge`. An unknown value warns on stderr and falls back to `flat` |
| **`-h` / `--help`** | Help plus the documentation link for the current language |

| Characteristic | Description |
| --- | --- |
| **Files written** | None. The command prints; it never edits your README |
| **Network** | None. The URL is assembled, never requested |
| **Configuration** | None is read: the snippet does not depend on your provider, your forge or your language |
| **Exit code** | 0. An unknown `--style` is a warning, not a failure |

---

## 2. What the Badge Says

The counts come from the local static linter's YAML rules, run over the same diff the pull request is about. Only the rules are used — the external linter bridge is skipped, because it runs binaries against the working tree rather than the revision being published.

| errors | warnings | Colour | Message |
| --- | --- | --- | --- |
| **> 0** | any | `red` | `N errors · M warnings` |
| **0** | **> 0** | `yellow` | `0 errors · M warnings` |
| **0** | **0** | `brightgreen` | `no issues` |

Two rules shape the text:

- **A zero is shown next to a non-zero count.** `0 errors · 2 warnings` says what was measured; hiding the zero would read as if errors were never counted. Each count pluralises on its own, so `1 error · 1 warning` is written that way.
- **The badge never claims a review.** It reports what the linter counted, in the linter's vocabulary. A green badge means *no rule violation was found*, not *this code was reviewed and approved* — the AI review is a different step with no part in this.

What you see on the pull request is a single image. `GitPR | 0 errors · 2 warnings` is how shields.io draws it, not a second line of text in the body, and the image is a link to [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/).

The badge text is **fixed English**, whatever the interface language is. Like the pull request body it sits in, it is a public artefact that outlives the machine that wrote it, and it lands in a repository whose readers may not share your language.

---

## 3. Where It Is Attached

The badge is added in one place, after the pull request body is complete and before either publisher reads it:

| Path | The badge |
| --- | --- |
| **`gitpr`** (TUI) | **Yes** — seeded into the editable body, so you can change or delete it before publishing |
| **`gitpr --no-edit`** | **Yes** — composed into the request that is sent |
| **`gitpr --no-publish`** | **No** — the `.md` written locally is the AI output, before the badge is built |
| **`gitpr review-pr`** | **No** — a review comment is a different artefact, and GitPR does not sign it |
| **MCP tools** | **No** — the tools return what the model produced |

The TUI is the reason the badge is seeded rather than injected at send time: it is on screen, in the text area you are already editing, and you have the last word on it. Updating an existing pull request re-sends the body currently on screen — including the badge, if you kept it.

Attachment is idempotent. A body that already carries a badge is left alone, so republishing never stacks two.

---

## 4. When There Is No Badge

**No linter rules, no badge.** An empty `.gitpr/skill/.gitpr.linter.yml` — the state of anyone who never ran `gitpr --skill` — means the linter has nothing to run, and its empty result is indistinguishable from a clean diff. A green badge on a diff nobody checked would be a claim GitPR cannot back, so it is left out entirely.

**The opt-out is `GITPR_BADGE=false`.** As with the co-author trailer, `false`, `0`, `no`, `off` and `n` all turn it off, case-insensitively and ignoring surrounding spaces; anything else — or the variable being absent — leaves it on. It is never written to `.env` on your behalf.

With the flag off, no badge is built and no notice is printed: the pull request goes out exactly as it did before this feature existed.

---

## 5. The README Badge

The badge you can put on your own project is a different one: static, always the same, and it says what the tool does rather than what it measured.

```markdown
[![GitPR](https://img.shields.io/badge/GitPR-quality--checked-blue)](https://gitpr.natanfiuza.dev.br/)
```

`gitpr badge` prints it with a short explanation; `gitpr badge --readme` prints the line alone, which is what you want for `gitpr badge --readme >> README.md`. Either way the command only prints — placing it is your call, because only you know where it belongs in your README.

---

## 6. Configuration

| Where | Name | Notes |
| --- | --- | --- |
| `~/.gitpr/.env` | `GITPR_BADGE` | On by default; `false` turns the badge off. Read-only — GitPR never writes it |
| Configuration screen | **Pull Request Badge** | General section, same switch, with the default spelled out in the description |
| `gitpr --init` | Notice | Shown once the forge is configured, together with the switch that disables it |
| `gitpr --no-edit` | Notice | Shown when a badge was attached to a body you did not see |

---

## 7. Environment Variables

| Variable | Purpose |
| --- | --- |
| `GITPR_BADGE` | `false` (or `0`, `no`, `off`, `n`) publishes pull request bodies without the badge |
| `GITPR_LANG` | Interface language. The badge itself is always English |

> **Note:** See also the [PR Publication documentation](pull-request-publication.md) for the flow the badge is attached to, and the [Customizable Static Linter documentation](linter-regras-customizadas.md) for the rules the counts come from — the badge has nothing to report until those rules exist.
