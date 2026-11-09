# Implementation Plan - Documenting Project Configuration Seed Workflow Change (CI & Monorepos)

## Goal Description
Document the workflow change introduced by the runtime creation of `.gitpr/conf/gitpr.config.yml` on the first execution within a Git repository. Specifically, inform developers running GitPR in CI/CD pipelines or monorepos about the automatic seed, its potential impact on clean working tree checks (e.g., `git status --porcelain`, `git diff --exit-code`), and how to disable it using the `GITPR_SKIP_PROJECT_CONFIG_SEED` environment variable.

## User Review Required
> [!NOTE]
> All technical points and documentation locations were aligned during the grill session:
> - Centralizing documentation in `docs/pull-request-publication.md` (§9.1, new §9.4, §14) and `docs/config-tui.md` (§1.8).
> - Updating `CONTEXT.md` with domain terms `Project configuration seed` and `Project configuration seed opt-out`.
> - Updating `GEMINI.md` user configuration environment variable list.

## Proposed Changes

### Documentation Updates

#### [MODIFY] `docs/pull-request-publication.md`
- In **Section 9.1 (The Project File)**:
  - Add an explicit alert explaining that `.gitpr/conf/gitpr.config.yml` is created automatically on the first run inside any Git repository.
- Add **Section 9.4 (Migration & Workflow Note: CI/CD, Monorepos and Clean Trees)**:
  - Detail the impact on CI/CD pipelines that check for dirty working trees (`git diff --exit-code` or `git status --porcelain`).
  - Explain how setting `GITPR_SKIP_PROJECT_CONFIG_SEED=true` (or `1`) completely disables the automatic seed.
  - Detail monorepo behavior: explain that `project_config_path()` anchors the file at the Git repository root (`git rev-parse --show-toplevel`), so sub-projects share the same root config unless opted out.
  - Provide ready-to-use CI snippets for GitHub Actions and GitLab CI.
- In **Section 14 (Environment Variables)**:
  - Add `GITPR_SKIP_PROJECT_CONFIG_SEED` to the reference table.

#### [MODIFY] `docs/config-tui.md`
- In **Section 1.8 (The Project Section)**:
  - Add a note regarding the runtime seed and reference `GITPR_SKIP_PROJECT_CONFIG_SEED` for automated and CI workflows.

#### [MODIFY] `CONTEXT.md`
- In the **Language** glossary:
  - Add **Project configuration seed**: The automatic creation of `.gitpr/conf/gitpr.config.yml` upon first execution in a repository.
  - Add **Project configuration seed opt-out**: Setting `GITPR_SKIP_PROJECT_CONFIG_SEED=true` to prevent file creation in CI/monorepo environments.

#### [MODIFY] `GEMINI.md`
- Add `GITPR_SKIP_PROJECT_CONFIG_SEED` to the Environment variables list under **User configuration**.

## Verification Plan

### Automated Tests
Run the test suite to ensure doc changes and glossary updates do not break any existing tests or i18n checks:
```bash
python -m pytest tests/ -v
```

### Manual Verification
- Review markdown rendering of alerts, tables, and code snippets in `docs/pull-request-publication.md`, `docs/config-tui.md`, `CONTEXT.md`, and `GEMINI.md`.
- Verify internal cross-reference links between docs.
