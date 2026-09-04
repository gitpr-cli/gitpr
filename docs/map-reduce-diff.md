# 📦 How GitPR Handles Huge Diffs (Map-Reduce)

If GitPR showed you the message **"📦 Huge diff detected! Processing in N batches (Map-Reduce)..."**, your changes were too large to be analyzed by the AI in a single call. Don't worry — nothing is lost. This page explains what happens behind the scenes.

## 🔍 Why is there a size limit?

AI models have a limited context window. GitPR estimates the size of your diff using the safe rule of **4 characters per token**. When the estimate exceeds **90,000 tokens** (roughly 360,000 characters), a single API call could fail, truncate the analysis, or produce low-quality results.

## ⚙️ How does the Map-Reduce pipeline work?

1. **Split:** the diff is divided into batches, always respecting file boundaries (the `diff --git` headers). A file is never cut in half.
2. **Map:** each batch is sent to the AI, which returns a technical summary of what changed in that part. The console shows the progress:

   ```text
   📦 Huge diff detected! Processing in 4 batches (Map-Reduce)...
   ⏳ Analyzing batch 1/4...
   ⏳ Analyzing batch 2/4...
   ```

3. **Reduce:** the partial summaries are unified and sent in a final call that generates the actual output — the commit message (`-c`), the code review (`-r`/`-f`), or the Pull Request description (default command).

## 💡 Good to know

- **Fully automatic:** there is no flag to enable it. Chunking only activates when the diff exceeds the limit; smaller diffs keep using a single AI call.
- **Same provider and model:** the batches use the AI engine you configured (Gemini, DeepSeek, or Ollama), with a 1-second pause between calls to respect rate limits.
- **Smart excludes come first:** lock files, minified assets, and other noise are removed from the diff before the size estimate — which often avoids chunking entirely.
- **Quality trade-off:** the final result is generated from technical summaries instead of the raw diff, so very fine-grained details may be condensed. For giant branches, splitting the work into smaller PRs still gives the AI the best material to work with.

🔗 Repository: [https://github.com/gitpr-cli/gitpr.git](https://github.com/gitpr-cli/gitpr.git)
