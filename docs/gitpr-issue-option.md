# 🚀 Issue Creation and Management with GitPR CLI

The `--issue` (or `-is`) feature turns GitPR into an advanced documentation assistant. Instead of writing Issues from scratch, Artificial Intelligence reads your work context, structures the issue in the **What / Why / Where / How** standard, and opens a visual interface directly in your terminal for review before submitting.

---

## 1. The Triple Context Engine (Which to use and why?)

GitPR's AI can read three different "languages" depending on the flag combination you use. Each engine was designed for a specific day-to-day developer scenario:

### 🆕 New Code Issue (The Default)
**Command:** `gitpr --issue` or `gitpr -is`
* **How it works:** GitPR reads your current `git diff` (uncommitted changes you just made).
* **Why use it:** Ideal for quickly documenting a small feature or bugfix you just coded, ensuring issue tracking is recorded on GitHub before you push the code.

### 📦 Release / Epic Issue
**Command:** `gitpr -is -ht` (Issue + History)
* **How it works:** GitPR compiles the entire `git log` of the current branch and combines it with the AI's own memory bank (fetching descriptions of old PRs for this branch from local cache).
* **Why use it:** If you've been working on a branch for several days, this command generates a mega-issue summarizing the entire feature. Excellent for delivering consolidated Release documentation to QA or Product teams.

### 🕰️ Archaeological / Technical Debt Issue
**Command:** `gitpr -is -b src/file.py:10-20` (Issue + Blame)
* **How it works:** GitPR doesn't look at new code. It triggers the Archaeological Engine to read the timeline and historical evolution of those specific lines.
* **Why use it:** Ideal for documenting technical debt. The AI structures an issue explaining how a legacy business rule evolved over time, why it became a problem, and the justification for a future refactoring.

---

## 2. Authentication and the PAT Token

For GitPR to create the Issue directly in your remote repository, it needs to communicate with the **GitHub REST API**.

1. The first time you run the command, the tool will request a **Personal Access Token (PAT)**.
2. GitPR generates a smart link and displays it in the terminal. Simply click it: your browser will open directly to GitHub's token creation page with the correct scope (`repo`) pre-selected.
3. Paste the token in the terminal.

**Security:** Your token is never transmitted in plain text. As soon as you paste it, GitPR uses the `cryptography` library to symmetrically encrypt the key, saving only the secure hash in the hidden file `~/.gitpr/.env` on your machine.

---

## 3. Terminal User Interface (TUI)

After the AI processes the context and structures the Issue, GitPR does not send data blindly. It will open an interactive interface built with the `textual` library.

On this sleek blue screen, you can freely edit the Title and Body of the issue. When satisfied, use quick keyboard shortcuts (no mouse needed):

* **`F4` (Help):** Opens a modal with quick explanations about the interface.
* **`F2` (Save Local):** Exports screen content to a Markdown (`.md`) file in your current folder. Useful if you just want the draft to refine later.
* **`F3` (Create on GitHub):** Triggers the official request. In seconds, GitPR closes the screen and displays the green link to your newly published issue in the terminal.
* **`Esc` (Exit):** Safely aborts the operation without saving anything.