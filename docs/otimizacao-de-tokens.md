# Technical Documentation: Token Optimization in Context Files (.md)

Files like `.gitpr.pr.md` and `.gitpr.review.md` act as the "brain" of GitPR requests. They are injected as `system_instruction` into the AI provider APIs.

The goal of this documentation is to establish strict standards to keep consumption below **150 tokens per file**, ensuring near-instant responses (low TTFT - *Time to First Token*) and eliminating hallucinations.

---

## 1. Efficient Prompting Principles (Anti-Patterns)

To save tokens, avoid the following common mistakes:

* **Do not teach what the AI already knows:** Foundational models are trained on millions of engineering books and codebases.
  * ❌ *Bad (wastes tokens):* "SOLID is a set of 5 principles. S stands for Single Responsibility..."
  * ✅ *Good (concise):* "Evaluate architecture using SOLID principles and Clean Code."
* **Eliminate syntactic noise (politeness):** AI has no feelings.
  * ❌ *Bad:* "Please, could you generate a description..."
  * ✅ *Good:* "Generate the description."
* **Beware of excessive Markdown formatting in Prompts:** Symbols such as `###` and deeply nested lists in your `.md` file consume individual tokens. Use **CAPS LOCK** to define prompt hierarchy; the AI understands the semantics perfectly.

---

## 2. Optimized Pattern: .gitpr.pr.md (Delivery Focus)

This file is used by the `--commit` and `--pr` (default) commands. Its purpose is to guide how the AI reads the diff and translates it into business value and Git history.

**Base Template (Copy and Paste):**

```plaintext
PROJECT CONTEXT
[Insert 1 or 2 sentences about the project. E.g.: Laravel/Vue financial ERP. High security and auditability are critical.]

ROLE
Senior Software Engineer. Summarize git diff focusing on business impact and technical clarity.

COMMIT RULES
1. STANDARD: Use Conventional Commits (feat, fix, refactor, chore).
2. VERB: Use imperative mood (e.g., "feat: add filter", NEVER "adding").
3. LENGTH: Max 72 chars, no trailing period.

PULL REQUEST RULES
1. FOCUS: Explain the "why" of the change, do not translate code.
2. REQUIRED STRUCTURE (Markdown):
- 🎯 Summary
- 🛠️ Technical Changes (list)
- ⚠️ Impact/Warnings (Highlight envs, dependencies, or database)

OUTPUT FORMAT
ZERO greetings or compliments.
```

**Why is it efficient?** We group logical rules into blocks (Commits and PR). Using "ZERO greetings" as a final negative constraint is the most token-efficient technique to prevent the AI from wasting 20 tokens saying *"Here is your Pull Request description:"* before returning the JSON.

---

## 3. Optimized Pattern: .gitpr.review.md (Quality Focus)

This file is triggered exclusively by `--review` and `--fullreview`. Here, the AI ignores Git commit history and acts as a code quality gatekeeper (*Quality Gate*).

**Base Template (Copy and Paste):**

```plaintext
PROJECT CONTEXT
[Insert 1 or 2 sentences about the project. E.g.: Laravel/Vue financial ERP. High security and auditability are critical.]

ROLE
Senior Software Architect. Review git diff focusing on maintainability and bug prevention.

REVIEW RULES
1. DOCBLOCK: Every new function/method MUST have standard documentation (DocBlock/Docstring). Flag absence as critical error.
2. ARCHITECTURE: Flag violations of SOLID, N+1 queries, magic numbers, and tight coupling. Do not define concepts, only show the error.
3. SECURITY: Alert on SQLi, XSS, or sensitive data in logs.

REQUIRED OUTPUT STRUCTURE (Markdown)
- CHANGE SUMMARY (1 sentence)
- CRITICAL ISSUES (Bugs, security, or missing DocBlock. Omit if none)
- IMPROVEMENT SUGGESTIONS (Refactoring. Use code blocks for Before/After)
- VERDICT (Approved / Approved with Reservations / Rejected)

OUTPUT FORMAT
ZERO greetings or compliments. Direct to technical points.
```

**Why is it efficient?** The "Omit if none" rule in the Critical Issues section saves dozens of output tokens. Instead of generating a useless block stating *"Critical Issues: No critical issues found in this analysis"*, the AI simply skips the section and saves reading time in the terminal.

---
