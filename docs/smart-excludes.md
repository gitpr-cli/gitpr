# 🎯 Smart Excludes — Token Optimization

If you've ever seen GitPR automatically reduce your diff before sending it to the AI, that's **Smart Excludes** at work. This page explains what it is, how it works, and how you can customize it for your project.

## 🔍 What is Smart Excludes?

Smart Excludes is a token-optimization system that **automatically removes non-code files** from your `git diff` before it is sent to the AI for analysis. By stripping out lockfiles, minified assets, binary files, and documentation prose, the AI receives a cleaner, more relevant diff — which means:

- **Lower token consumption** (and lower API costs)
- **Faster AI responses** (less text to process)
- **Higher-quality analysis** (the AI focuses on code, not noise)

## ⚙️ How It Works

GitPR uses Git's native **pathspec exclusion** syntax (`:(exclude)*.md`) to filter files out of the diff. This happens at the `git diff` command level before any text reaches the AI — so excluded files never consume a single token.

The system has **two layers** of exclusions:

### 1. Core Exclusions (Noise)
Controlled by [`templates/gitpr.smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.smart-excludes.json):

- **Lockfiles:** `package-lock.json`, `yarn.lock`, `Cargo.lock`, `Pipfile.lock`, `uv.lock`, etc.
- **Minified assets:** `*.min.js`, `*.min.css`, `*.bundle.js`
- **Generated files:** `*.map`, `*.pyc`, `*.log`
- **OS files:** `.DS_Store`, `Thumbs.db`

### 2. Documentation Exclusions (Prose)
Controlled by [`templates/gitpr.docs-smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.docs-smart-excludes.json):

- **Markup/prose:** `.md`, `.txt`, `.rst`, `.adoc`, `.asciidoc`, `.org`, `.textile`, `.wiki`
- **Academic/tech writing:** `.tex`, `.rtf`, `.pod`, `.rdoc`
- **Extended Markdown:** `.mdx`, `.markdown`, `.rest`
- **Man pages:** `.man`, `.1`–`.8`

The two lists are **merged at runtime** into a single `SMART_EXCLUDES` variable, which is appended to every `git diff` command executed by GitPR.

## 📋 Documentation Metadata (Changed Docs Without Content)

Excluding documentation from the diff saves tokens, but you still want to know _which_ docs were modified. GitPR solves this by running a separate lightweight command:

```bash
git diff --name-only <ref> -- <doc-paths>
```

It filters the output by the documentation extensions above and **injects the file list as metadata** into the AI's system instructions:

```
Changed documentation (content excluded from diff):
- docs/README.md
- CHANGELOG.md
- guides/setup.rst
```

This way the AI knows which documents changed — which is useful context for commit messages and PR descriptions — without consuming tokens on their full prose content.

## 📁 Configuration Files

| File | Purpose | Managed |
|------|---------|---------|
| `templates/gitpr.smart-excludes.json` | Core exclusions (lockfiles, binaries, minified) | Remote (GitHub) |
| `templates/gitpr.docs-smart-excludes.json` | Documentation extensions | Remote (GitHub) |
| `~/.gitpr/conf/gitpr.smart-excludes.json` | Local cache of core exclusions | Auto-downloaded |
| `~/.gitpr/conf/gitpr.docs-smart-excludes.json` | Local cache of doc exclusions | Auto-downloaded |
| `./.gitpr/conf/gitpr.smart-excludes.json` | **Project-specific** exclusions (optional) | User-created (versionable) |

Both remote templates are **version-controlled** — GitPR automatically re-downloads them when a new version is published (triggered by the `__lang_version__` marker). You never need to manually update these files.

### Resolution Chain

When GitPR starts, each exclusion list is loaded through a fallback chain:

1. **Global cache** — `~/.gitpr/conf/` (fastest, zero network)
2. **Remote download** — from the official GitHub repository (timeout: 3 seconds)
3. **Stale global copy** — used when the network is unavailable
4. **Built-in fallback** — hardcoded defaults (guarantees functionality offline)
5. **Project-local merge** — `.gitpr/conf/gitpr.smart-excludes.json` at the project root is loaded and **merged** (union) with the global list. Items in the local file are additive — they add extra exclusions specific to your project

## 📊 Usage Example

Consider a branch where you changed `src/auth.py`, `docs/README.md`, and `package-lock.json`:

**Without Smart Excludes** (all files in the diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
diff --git a/docs/README.md b/docs/README.md
+ ## New Section
+ This is a long documentation update with many paragraphs...
diff --git a/package-lock.json b/package-lock.json
+ 500 lines of dependency tree changes
```
→ ~600+ lines sent to the AI (~15,000 tokens)

**With Smart Excludes** (only code in the diff):
```diff
diff --git a/src/auth.py b/src/auth.py
+ def validate_token(token): ...
```
→ ~10 lines sent to the AI (~250 tokens)

**Plus metadata** injected into the system instruction:
```
Changed documentation (content excluded from diff):
- docs/README.md
```

> **Result:** ~98% token reduction for this scenario, with the AI still aware that documentation was updated.

## 🎨 Customization

### Adding New Extensions

To permanently add new patterns, edit the template files on the [GitPR repository](https://github.com/natanfiuza/gitpr):

1. Edit `templates/gitpr.smart-excludes.json` for non-code noise
2. Edit `templates/gitpr.docs-smart-excludes.json` for documentation extensions
3. Bump `__lang_version__` in `src/updater.py`
4. The new patterns propagate to all users on their next run

### Project-Local Configuration (Recommended)

Each project can have its own Smart Excludes file at `.gitpr/conf/gitpr.smart-excludes.json`. This file is **merged** with the global list at runtime — it adds extra exclusions that only apply to your project (e.g., `dist/`, `node_modules/`, framework-specific build artifacts).

**Creating the file:**

The file is auto-seeded the first time GitPR downloads the global Smart Excludes list. You can also create it manually:

```json
{
  "_comment": "Project-specific Smart Excludes. Merged with the global list at runtime.",
  "excludes": [
    "dist/",
    "*.pyc",
    "build/"
  ]
}
```

**Why use the local file instead of editing the global cache?**

- The global cache (`~/.gitpr/conf/`) is overwritten on every version update
- The local file persists independently and can be **version-controlled** in your repository
- Team members get the same project-specific exclusions when they clone the repo

### Temporary Override

You can edit the cached files in `~/.gitpr/conf/` directly. These changes persist until the next `__lang_version__` bump, when the remote version overwrites them. Prefer the project-local file for permanent exclusions.

### Disabling Smart Excludes

Set the environment variable `GITPR_SKIP_SMART_EXCLUDES=1` to disable all Smart Excludes filtering for the current session. Use this sparingly — it removes both global and project-local exclusions.

## ❓ FAQ

### Why are documentation files excluded from the diff?

Documentation prose (READMEs, guides, CHANGELOGs) can be thousands of words long. Including them in the AI prompt consumes tokens that are better spent on analyzing code changes. The AI still receives the file _names_ as metadata, so it knows which docs changed.

### How do I know which documentation files were changed?

GitPR automatically injects the list of changed documentation files into the AI's context. You can also run `git diff --name-only` yourself and filter by the extensions listed above.

### Can I disable Smart Excludes entirely?

Smart Excludes is a core optimization but can be disabled by setting `GITPR_SKIP_SMART_EXCLUDES=1` in your environment. For more granular control, use the project-local configuration file (`.gitpr/conf/gitpr.smart-excludes.json`) to add or adjust exclusions for your project without disabling the system globally.

### Does this affect the actual git repository?

No. Smart Excludes only affects what GitPR _reads_ from your repository. Your actual `git diff`, commits, and working tree are completely unchanged.

### What happens to the Linter?

The static linter (`.gitpr.linter.yml`) runs on the diff **after** Smart Excludes filtering. Documentation files are not linted.

---

📂 **Repository:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)
🌐 **Website:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/)
