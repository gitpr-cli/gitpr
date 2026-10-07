# Technical Documentation: Junior Mentor Mode (gitpr mentor / --mentor)

`gitpr mentor` transforms code review findings into pedagogical, actionable, and didactic feedback. Designed especially for junior engineers and software apprentices, it focuses on explaining **what** is happening, **why** it matters in practice, everyday **analogies**, and key engineering concepts **to learn more**.

The feature is strictly **additive and opt-in**: the original technical analysis of the code review is never modified or removed.

---

## 1. Overview

Junior Mentor Mode operates in two complementary surfaces:

1. **Flag `-r --mentor` / `-f --mentor`**: Executes the standard code review and automatically appends a formatted `## 🎓 Mentor (Junior Guidance)` section at the end of the review output file (`*_PR_REVIEW.txt` or `*_PR_FULLREVIEW.txt`).
2. **Standalone Command `gitpr mentor [--finding <id>]`**: Reads the findings from the most recent code review and outputs pedagogical guidance directly in the terminal without rerunning the review or writing files to disk.

### 1.1 Command Reference

```bash
gitpr -r --mentor              # Runs local review and appends Mentor section to the report
gitpr -f --mentor              # Runs full branch review and appends Mentor section
gitpr mentor                   # Explains findings of the last review in the terminal
gitpr mentor --finding FIX-002 # Explains a single finding by its ID
gitpr mentor --provider gemini # Forces specific AI provider
```

| Option | Description |
|---|---|
| **`-r --mentor`** | Appends pedagogical guidance to local code review report |
| **`-f --mentor`** | Appends pedagogical guidance to full review against origin/main |
| **`gitpr mentor`** | Displays guidance in the terminal for all findings of the last review (up to cap) |
| **`--finding <id>`** | Focuses explanation on a single finding ID (e.g., `FIX-002`) |
| **`--provider <name>`** | Overrides configured AI provider (`gemini`, `deepseek`, or `ollama`) |

---

## 2. Explanation Structure

For each analyzed finding, the mentor output contains:

1. **Original Technical Finding**: Kept verbatim as a blockquote reference.
2. **What is happening**: A straightforward, plain-language breakdown of the code pattern.
3. **Why it matters**: Practical consequences if unaddressed (security vulnerabilities, resource leaks, edge case crashes) rather than vague "bad practice" statements.
4. **Analogy (optional)**: Grounded in everyday life or introductory programming to reinforce the concept.
5. **To learn more**: Concrete architectural principles or patterns to research (e.g. *Single Responsibility Principle*, *OWASP SQL Injection Prevention*). Never contains hallucinated links or URLs.

---

## 3. Configuration (`~/.gitpr/.env`)

| Key | Type | Default | Description |
|---|---|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | boolean | `false` | When `true`, automatically enables Mentor mode on every `-r` and `-f` without requiring the `--mentor` flag. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | boolean | `true` | When `false`, instructs the AI to omit analogies and return a more direct explanation. |

---

## 4. Performance, Caching & Cap Limit

- **Batch Processing**: Explanations are generated in a single batch AI request, rather than one request per finding.
- **Safety Cap (10 findings)**: If a review generates more than 10 findings, the top 10 by severity (`blocker` > `critical` > `high` > `medium` > `low`) are expanded. Remaining findings are listed at the bottom and can be inspected with `gitpr mentor --finding <id>`.
- **Local Cache**: Responses are cached locally under `~/.gitpr/cache/prompts/mentor/<md5>.json`. Re-running the command for the same findings incurs zero API cost and minimal latency.

