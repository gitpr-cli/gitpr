# **Practical Guide: Performant Regular Expressions in GitPR**

GitPR's Static Linter processes `git diff` line by line using Python's native `re` engine (NFA - *Nondeterministic Finite Automaton*). NFA engines are powerful, but they have a dangerous blind spot: **Catastrophic Backtracking**.

This guide explains how to write rules for `.gitpr.linter.yml` to ensure commit validation times remain in the order of milliseconds.

---

## **1. What is Catastrophic Backtracking?**

It occurs when a Regex uses **greedy quantifiers** `(*, +)` close to each other or nested, and the tested string almost matches, but fails at the end.

To try to find a valid match, the engine "backtracks" and tests all possible permutations. Processing time grows exponentially ($O(2^n)$).

**The Classic Example (The Code of Death):**

* **Regex:** `(a+)+$`  
* **Text:** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX`  
* *Result:* The terminal freezes. The engine will attempt over 700 million combinations before realizing that the `X` at the end prevents a match.

---

## **2. Golden Rules for High Performance**

### **Rule 1: "Fail Fast" using Anchors**

The best way to save CPU is to make the Regex give up on the line as quickly as possible.

If the prohibited word should be an isolated word, use word boundary `\b`. This prevents Regex from analyzing the interior of long strings unnecessarily.

* ❌ **Slow:** `dd\(` *(Searches for characters 'd', 'd', '(' at every position in the line)*  
* ✅ **Fast:** `\bdd\(` *(Only starts searching at the beginning of a word. If the line is `add()`, it gives up on the first character)*

### **Rule 2: Replace `.*` with Negated Classes `[^...]`**

`.*` (anything, zero or more times) is the biggest cause of backtracking. It is greedy: it consumes until the end of the line, and then starts backtracking from right to left searching for the rest of your rule.

If you are looking for something inside quotes or parentheses, specify exactly where it should stop.

* ❌ **Slow:** `console\.log\(.*\)` *(Goes to the end of the line before backtracking to find the closing parenthesis)*  
* ✅ **Fast:** `console\.log\([^)]*\)` *(The `[^)]` class means: "Capture everything, as long as it is NOT a closing parenthesis". It stops at the exact millisecond it hits the boundary)*

### **Rule 3: Avoid Nested Optional Quantifiers**

Never place an optional quantifier (`*` or `?`) right after another optional quantifier, or inside a group that also repeats.

* ❌ **Slow:** `(localhost\s*)*`  
* ✅ **Fast:** `localhost(\s+localhost)*`

### **Rule 4: Disable Group Capture `(?:...)`**

By default, when you use parentheses `(get|post)` as in our routing rule, Python saves that information in memory for later extraction. GitPR does not need to extract the word; it only needs to know if it exists (`True` or `False`).

Use non-capturing groups `(?:...)` to save memory allocation.

* ❌ **Slow:** `Route::(get|post)\(`  
* ✅ **Fast:** `Route::(?:get|post)\(`

---

## **3. Practical Comparison for `.gitpr.linter.yml`**

See how to transform naive rules into bulletproof rules:

| Objective | ❌ Naive Regex (Dangerous) | ✅ Performant Regex (GitPR) | Why is it better? |
| :---- | :---- | :---- | :---- |
| Block Fixed IP | `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+` | `\b(?:\d{1,3}\.){3}\d{1,3}\b` | Uses `\b` and `(?:)` to avoid extra memory allocation, and limits length to 3 digits. |
| Find TODOs | `.*TODO.*` | `\bTODO\b:` | Eliminates useless `.*`. The `\b` anchor resolves matching across the entire line. |
| Routes (Verbs) | `Route::.*\('get.*` | `Route::[A-Za-z]+(\s*['"](?:get\|post)` | Uses character classes and fast non-capturing alternation. |

**Prevention Tip:** Since GitPR processes lines in minified files (e.g., `app.min.js`), a single line can contain thousands of characters. Applying **Rule 2 (Negated Classes)** is your best defense against terminal freezes.

---
