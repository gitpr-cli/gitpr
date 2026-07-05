# Technical Documentation: Local Git Hooks Integration (GitPR)

This documentation details the architecture and usage of GitPR CLI's automatic Git Hooks functionality. The implementation adopts the **Shift Left** practice, bringing code validation and message generation (AI) to the exact moment of commit, before any integration with the remote server.

---

## 1. Automated Installation

To install the hooks in your local repository, navigate to the project root (where the hidden `.git` folder resides) and run:

```bash
gitpr --installhooks
# or
gitpr -ih
```

**What this command does under the hood:**

1. Checks the integrity of the .git/hooks directory.
2. Downloads the latest version of the pre-commit and prepare-commit-msg scripts directly from the official GitPR repository.
3. Automatically applies POSIX execution permissions (chmod +x) to the files, ensuring compatibility across Linux, macOS, and Git Bash environments on Windows.

---

## **2. Hook: pre-commit (Static Linter)**

The pre-commit hook acts as a local "bodyguard". It is triggered instantly when running git commit, before the commit message is requested.

### **How it works:**

* The script invokes the gitpr --linter command.
* GitPR analyzes the current diff (staged files) against the rules defined in the .gitpr.linter.yml file.
* **Exit Code 0:** If there are no violations, the Git flow continues normally.
* **Exit Code 1:** If forbidden strings (e.g.: console.log, passwords, localhost) are detected, the script intercepts the action, displays the alerts in the terminal, and **aborts the commit**.

### **Bypass Route**

If there is a strict need to bypass the local Linter validation (for example, when uploading temporary debug code on an isolated branch), use the native Git flag:

```bash
git commit --no-verify -m "Your message here"
```

---

## **3. Hook: prepare-commit-msg (AI Auto-Commit)**

This hook eliminates the need to manually write commit messages. It integrates Gemini's artificial intelligence directly into the Git lifecycle, generating messages in the *Conventional Commits* standard based on your code.

### **How it works:**

1. Add your files to stage (git add .).
2. Run only the base commit command, without passing the message:
   ```bash
   git commit
   ```

3. The hook kicks in displaying the message: 🤖 GitPR: Requesting commit suggestion from AI...
4. GitPR runs the hidden --hook flag, sending your *diff* to Gemini.
5. The AI generates the message and the script cleanly injects the result into the first line of Git's temporary file.
6. Your default text editor (Vim, Nano, VS Code) will open with the message already filled in. Just save and close to confirm the commit.

### **Preserving Manual Flow**

The script is smart enough not to overwrite your intention. If you run the commit passing the explicit message flag (-m), the hook recognizes the source as "message" and **silently disables AI processing**:

```bash
# The AI will NOT be triggered in this case, respecting your message.
git commit -m "fix: resolves API concurrency issue"
```

---

## **4. Troubleshooting**

* **Hook does not run (Linux/macOS):** Make sure the files in .git/hooks have execution permission. You can force it with chmod +x .git/hooks/pre-commit.
* **Command not found:** The hook scripts are configured to search for both the global installation (gitpr) and local execution via virtual environment (pipenv run python run.py). If you are using a different dependency manager (such as Poetry), you may need to edit the scripts inside the .git/hooks folder to reflect your environment.
