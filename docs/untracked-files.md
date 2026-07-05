# ⚠️ Why did GitPR ignore my new files?

If you ran GitPR and received a warning that **untracked files** were detected, don't worry! This is a safety and optimization behavior native to the system.

## 🔍 What does "Untracked" mean?

When you create a new file in your project, Git does not automatically track it. It remains in the *Untracked* state. The command GitPR uses to read your code (`git diff HEAD`) analyzes only files that Git already knows about or that have been prepared for commit (*Staged*).

## 🛡️ Why doesn't GitPR read these files automatically?

We designed GitPR with three pillars in mind:
1. **Security (Leak Prevention):** Imagine you create a `.env.local` file with production database passwords and forget to add it to `.gitignore`. If GitPR read everything automatically, it would send your passwords to the AI API.
2. **Token Economy (Cost):** Some frameworks generate giant cache folders or compiled files. Sending garbage to the AI would consume your tokens unnecessarily and make the response extremely slow.
3. **Git Standard:** GitPR respects the official Git lifecycle. The AI only analyzes what you, as a developer, decide has value.

## ✅ How to fix it?

The solution is very simple. You just need to tell Git which new files are part of your next commit using the `add` command:

```bash
# To add a specific file:
git add src/my_new_file.py

# OR to add all new files at once:
git add .

```

After running `git add`, simply run the **GitPR** command again. The AI will now see your new additions and generate the analysis perfectly! 🚀
