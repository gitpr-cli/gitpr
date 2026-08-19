# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive PR publisher TUI and auto-commit flow
```

---

## 🎯 Summary

This PR introduces a complete Pull Request publication feature with an interactive Terminal User Interface (TUI), including unstaged file management, linter validation, AI-generated commit messages, and one-click PR creation on GitHub. The new workflow replaces the previous local-only PR description generation, enabling users to review, edit, and publish PRs directly from the CLI.

## 🛠️ Technical Changes

- Add new configuration options: `PR_DEFAULT_BASE`, `GITPR_AUTO_COMMIT`, `GITPR_SKIP_LINT`, `GITPR_AUTO_STAGE`, `GITPR_SKIP_UNSTAGED_CHECK`, `PR_PUBLISH_LOG`.
- Implement core utility functions: `has_uncommitted_changes`, `get_unstaged_files`, `stage_files`, `execute_git_commit`.
- Create `github_api.py` module with `create_pull_request` function (REST API + error handling).
- Integrate new CLI flags: `--base`, `--no-publish`, `--no-edit`; update help texts.
- Implement image-based UI (Textual) with multiple modal screens for unstaged file staging, commit confirmation, message editing, linter errors, and progress animation.
- Add auto-commit flow with linter check and AI commit message generation.
- Add comprehensive i18n translations (es_es, fr_fr, pt_br, pt_pt) for all new UI strings.
- Add sample metric export files for testing.

## ⚠️ Impact/Warnings

- New optional dependencies: `textual` library for the TUI (ensure it's installed).
- Environment variables (`PR_DEFAULT_BASE`, etc.) now influence behavior; may need documentation.
- Updated default CLI behavior: `gitpr` now opens interactive TUI instead of just generating a markdown file (backwards incompatible in default mode).