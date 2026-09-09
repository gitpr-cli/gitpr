# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add gitpr release changelog subcommand
```

---

🎯 Summary

Introduces `gitpr release`, a command-line flow that automatically generates changelog/release notes from a repository's git history. It classifies commits by Conventional Commits, suggests or validates semantic version bumps, creates localized Markdown sections, optionally adds an AI executive summary, and can publish the release to GitHub/GitLab.

🛠️ Technical Changes

- Adds a first Click subcommand `release` with options `--since`, `--version`, `--publish`, `--draft`, `--format`, and `--force`; legacy flag dispatch remains intact when no subcommand is invoked.
- Adds pure modules for Conventional Commits classification, semver bump logic, and changelog Markdown rendering with localized section headings.
- Introduces `release_engine.py` to orchestrate range resolution, git log collection, classification, version decision, AI Map-Reduce summaries, idempotent changelog upsert, and forge publishing.
- Extends GitHub/GitLab providers with `create_release`; Bitbucket/Azure inherit an explicit not-supported default.
- Adds first-use auto-download of `.gitpr.release.md` skill template and a `skill://release` MCP resource.
- Adds localized strings for all release flow messages and new `GITPR_RELEASE_*` configuration defaults; updates version to 1.0.0.

⚠️ Impact/Warnings

- New CLI path wired as a Click group: existing `gitpr` flags keep the current behavior, but any custom wrapper relying on the root being a plain command should be revalidated.
- Default changelog file is `CHANGELOG.md` at the repository root; an existing `## [version]` section aborts unless `--force` is supplied.
- AI summaries require an API key configured through `--install`; when unavailable the changelog is still generated without a summary and a warning is shown.
- Publishing requires forge credentials: GitHub creates the tag on its default branch, GitLab requires the tag to be present beforehand, and Bitbucket/Azure release publishing is unsupported.
- New optional environment variables: `GITPR_RELEASE_CHANGELOG_PATH`, `GITPR_RELEASE_AI_SUMMARY`, `GITPR_RELEASE_AUTO_BUMP`, and `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT`.

close #159