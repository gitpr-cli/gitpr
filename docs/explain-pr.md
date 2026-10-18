# Technical Documentation: Reviewer Guide (`gitpr explain` / `--explain`)

The Reviewer Guide explains a change set from the reviewer's point of view. Instead of describing what the diff looks like (the PR description already does that), it answers the four questions a reviewer asks before approving: **what changes**, **why it changes**, **where to focus the review**, and **what regression risk it carries**.

It is available as a standalone command, as an opt-in section of the Pull Request flow, and through the MCP server and the VS Code extension.

---

## 1. Overview

```bash
# Explain the uncommitted changes in the current repository
gitpr explain

# Force a specific AI provider for this run
gitpr explain --provider deepseek

# Include the Reviewer Guide in the Pull Request description (default PR flow)
gitpr --explain

# Same, saving the description locally without opening the publisher TUI
gitpr --explain --no-publish

# Always include it, without passing the flag on every run
# (~/.gitpr/.env)
GITPR_EXPLAIN_BY_DEFAULT=true

# Contextual help with the documentation link
gitpr -h --explain
```

---

## 2. Command Reference

| Invocation | Scope | Writes to disk | Publishes |
|---|---|---|---|
| `gitpr explain [--provider <name>]` | Working tree diff (`git diff HEAD`) | No | No |
| `gitpr --explain` | Full branch diff against the remote base | Yes (PR `.md` file) | Yes, when the PR is published |
| `gitpr --explain --no-publish` | Full branch diff against the remote base | Yes (PR `.md` file) | No |
| `gitpr --explain --no-edit` | Full branch diff against the remote base | Yes | Yes, directly |

### `gitpr explain`

| Option | Default | Description |
|---|---|---|
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Forces the AI provider for this run (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Click help plus the link to this page. |

The standalone command prints the guide to the terminal and exits. It never creates a file, never opens the editor, and never talks to the forge.

### Root flag `--explain`

| Flag | Environment variable | Default | Description |
|---|---|---|---|
| `--explain` | `GITPR_EXPLAIN_BY_DEFAULT` | `false` | Appends the Reviewer Guide section to the generated Pull Request description. |

Values accepted by `GITPR_EXPLAIN_BY_DEFAULT` (case-insensitive): `true`, `1`, `yes`, `y`. Anything else — including an unset variable — keeps the section off. The key is editable from the configuration screen (`gitpr config`) under the **PR** category, and it can be set by hand in `~/.gitpr/.env`.

The flag only participates in the **default Pull Request flow**. Modes that exit before that flow (`--commit`, `--review`, `--fullreview`, `--issue`, `--blame`, `--chat`, `gitpr tests generate`, and the other subcommands) ignore it.

---

## 3. Diff Sources

The two entry points do not explain the same thing:

| Entry point | Command behind it | Covers |
|---|---|---|
| `gitpr explain` | `git diff -U1 -w -M -B HEAD -- <smart excludes>` | Staged and unstaged changes of tracked files, compared with `HEAD`. Untracked files are reported as a warning and are **not** part of the prompt. |
| `--explain` (PR flow) | `git fetch origin` → `git merge-base origin/<base> HEAD` → `git diff -U1 -w -M -B <merge-base> -- <smart excludes>` | Everything the branch changes relative to the point where it diverged from the base branch, including the working tree state. |

In both cases the diff is captured with `-U1` (one line of context), `-w` (whitespace-insensitive), `-M` (rename detection), `-B` (broken pairs), and the resolved **smart excludes** (lockfiles, generated artifacts, and other paths that would drown the signal). The same helper file can be overridden with `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL`, and `GITPR_SMART_EXCLUDES_LOCAL`.

Because the diff is trimmed for reading, it is not a patch: it must not be used with `git apply`. Commands that need an applicable patch (`gitpr fix`, `gitpr split`) capture their own diff.

---

## 4. Generation Pipeline

1. **Empty diff check.** An empty or whitespace-only diff returns an empty explanation immediately; the standalone command prints `⚠️ No diff found...` and exits with code `1`.
2. **Provider and key.** The provider comes from `--provider` or `DEFAULT_AI_PROVIDER`. If no key is configured, the command prints `❌ No API key configured for <provider>. Generate one with --install.` to **stderr** and returns an empty explanation. `ollama` needs no key.
3. **Model selection.** The advanced/primary model is used (`get_api_model(provider, task_complexity="advanced")`): `GEMINI_API_MODEL_PRIMARY` or `DEEPSEEK_API_MODEL_PRIMARY`, with the corresponding built-in default.
4. **Skill resolution.** The system instruction is `get_skill_context("explain", quiet=True)` — `.gitpr/skill/.gitpr.explain.md` when it exists, a legacy `.gitpr.md` as fallback, otherwise a built-in instruction equivalent to the English template. The PR flow passes `quiet=True` so the "skill loaded" message never pollutes the generated description.
5. **Prompt.** The full diff and the explanation rules are sent in a single prompt. The output must be one JSON object (the provider layer is configured for JSON responses).
6. **AI call.** `call_ai_model(..., action="explain")` uses temperature `0.0` and retries up to **3** times with a **2 s** interval. On failure it returns `None`, and the command reports that the guide could not be generated.
7. **Parsing.** `parse_explain_payload` accepts the provider's parsed **dict** and, for compatibility, a raw JSON string. A string that is not valid JSON is treated as prose: it fills `what_changes`, the `why_it_changes` field receives a `[FILL: ...]` placeholder, and `has_sufficient_evidence` becomes `False`.
8. **Rendering.** `build_explain_markdown` assembles the Markdown section used by the PR flow; the standalone command renders the same data in a coloured terminal report.

The flow does **not** use the local AI response cache and does **not** write a row to the metrics ledger. Every run calls the provider.

---

## 5. Output Contract

The model returns a JSON object with four fields:

| Field | Type | Meaning |
|---|---|---|
| `what_changes` | string | 2–4 plain-language sentences describing the functional change, without jargon. |
| `why_it_changes` | string | The inferred motivation. When the diff does not support a conclusion, the model must use `[FILL: What is the primary business motivation for this change?]` instead of inventing one. |
| `reviewer_focus_points` | array of objects | 2–5 concrete points to inspect. Each object has `description` (required), `file_path` (optional), and `related_line` (optional integer). |
| `regression_risk` | string | Objective risk surfaces: critical shared code, schema migrations, auth changes, missing tests, breaking interfaces. |

The provider layer adds `_telemetry_meta` to the dict; the parser ignores it.

### Markdown section

```markdown
## 🧐 Reviewer Guide (Explain My PR)

### 🔍 What changes
...

### 💡 Why it changes
...

### 🎯 Where to focus review
- **Validate token expiration** (`src/auth/tokens.py:45`)
- **Check backward compatibility of the refresh endpoint**

### ⚠️ Regression Risk
...
```

`Where to focus review` is emitted only when at least one focus point exists, and `Regression Risk` only when the field is non-empty.

### Evidence flag

`has_sufficient_evidence` is `False` when the diff is empty, when no API key is available, or when `what_changes` / `why_it_changes` contain a placeholder marker (`[PREENCHER`, `[FILL`, `[TODO`, `[REQUIRED`). The standalone command prints a notice below the report; the PR section itself is not suppressed — the placeholders remain visible so the author can complete them.

---

## 6. Where the Guide Appears

### PR flow (`--explain`)

After the PR title and body are generated, the Reviewer Guide is appended to the body as a separate block:

```text
<PR description>

---

## 🧐 Reviewer Guide (Explain My PR)
...
```

The combined body is written to the PR `.md` file and is what gets published when the Pull Request is created. Enabling `GITPR_EXPLAIN_BY_DEFAULT=true` produces the same result without the flag.

### MCP server

The `generate_pr_description` tool accepts `explain: bool = false` and appends the same section to the returned `pr_description`. The tool computes the full branch diff itself; the guide is omitted if the model returns no Markdown.

### VS Code extension

The `gitpr.generatePrExplain` command runs the PR generation with `explain: true`. The plain `gitpr.generatePr` command leaves the section off.

---

## 7. Customizing the Guide with a Skill

The explanation rules are a **skill**, not hard-coded prompt text:

- Default location: `.gitpr/skill/.gitpr.explain.md` in the repository.
- Download it with `gitpr --skill` (also available in the install wizard). Language variants exist for `en`, `pt_br`, `pt_pt`, `es_es`, and `fr_fr`; the file is downloaded in the active interface language and is **never overwritten** if it already exists.
- A legacy `.gitpr.md` at `.gitpr/skill/` is used as a fallback when the specific file is absent.
- When neither exists, the built-in instruction is used; it is equivalent to the English template and still requires strict JSON.
- The language of the generated text follows the loaded skill, not the `--lang` interface language. To get the guide in Portuguese, for example, download or write the Portuguese `.gitpr.explain.md`.

The template instructs the model to write for a reviewer who did not author the code, to never invent motivation, to list 2–5 focus points, and to return only the JSON object.

---

## 8. Errors and Exit Codes

| Situation | Behaviour | Exit code |
|---|---|---|
| Guide generated | Terminal report (standalone) or section appended (PR flow) | `0` |
| No diff / no content | `⚠️ No diff found...` on stdout | `1` |
| No API key | Localized error on stderr; standalone also prints `❌ Failed to generate PR explanation.` | `1` |
| Model returned nothing usable | `❌ Failed to generate PR explanation.` | `1` |
| PR flow, model returned nothing | Section is silently omitted from the description; the rest of the PR is still produced | `0` |
| Invalid provider name | Provider layer reports the unknown provider; no guide is produced | `1` (standalone) |

---

## 9. Example

```text
$ gitpr explain

🧐 Analyzing diff from reviewer perspective...

============================================================
  REVIEWER GUIDE (Explain My PR)
============================================================

🔍 What changes:
  Adds a Redis-backed rate limiter to the login route and wires it
  into the authentication middleware.

💡 Why it changes:
  Mitigates brute-force credential stuffing without changing the
  login response contract.

🎯 Where to focus review:
  • Verify the key expiration strategy [src/auth/limiter.py:25]
  • Confirm legitimate shared-IP users are not locked out [src/auth/middleware.py]

⚠️ Regression Risk:
  Users behind shared NATs may be throttled together; no test covers
  the limit boundary yet.

⚠️ Notice: Inferred with partial context. Some fields contain placeholders to complete.
```

---

## 10. Limitations

- **Standalone output is terminal-only.** `gitpr explain` does not write a file and does not publish anything; to attach the section to a PR, use `--explain` in the PR flow.
- **`--explain` is exclusive to the default PR flow.** Combining it with modes that exit earlier has no effect.
- **No cache, no ledger.** Repeated runs call the model again, and the run is not recorded in `gitpr metrics`.
- **Untracked files are not explained.** Both diff sources only see tracked files. The standalone command warns about untracked files but does not include them; add them with `git add` first.
- **No chunking.** The whole diff goes into one prompt. Very large changes can hit the provider's context limit; split the work or review a smaller range.
- **No patch semantics.** The diff is captured with `-w` and `-U1` for readability. Do not reuse it for `git apply`.
- **Motivation is inferred.** The model is prohibited from inventing a rationale; when the diff lacks evidence it emits a `[FILL: ...]` placeholder instead.
- **Language depends on the skill.** The interface language alone does not translate the generated guide.

---

## 11. Related Documentation

- [Pull Request Publication](pull-request-publication.md) — where the section is attached and how the PR is published.
- [Skill Templates](skill-template.md) — how `.gitpr.*.md` files are resolved, downloaded, and overridden.
- [AI Providers](providers-ia.md) — providers, models, retries, and key configuration.
- [Configuration TUI](config-tui.md) — editing `GITPR_EXPLAIN_BY_DEFAULT` from `gitpr config`.
- [Test Generation](tests-generate.md) — the other AI generation command.
- [Mentor Mode](mentor-mode.md) — the pedagogical explanations added to code reviews.
