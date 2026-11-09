# Walkthrough - Documenting Project Configuration Seed Workflow Change

## Overview
Documented the workflow change introduced by the runtime creation of `.gitpr/conf/gitpr.config.yml` on the first execution within a Git repository. Specifically, guided CI/CD pipeline maintainers and monorepo engineers on how to manage this behavior, prevent clean working tree check failures, and use `GITPR_SKIP_PROJECT_CONFIG_SEED`.

## Changes Made

### 1. Pull Request Publication Guide
- **File:** [docs/pull-request-publication.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/pull-request-publication.md)
  - Updated Section 9.1 with an alert highlighting the runtime creation behavior and deep-linking to Section 9.4.
  - Added new Section 9.4: *Migration & Workflow Note: CI/CD, Monorepos and Clean Trees*, covering:
    - Clean working tree verification checks in CI/CD (`git status --porcelain`, `git diff --exit-code`).
    - The `GITPR_SKIP_PROJECT_CONFIG_SEED` opt-out switch with practical GitHub Actions and GitLab CI configurations.
    - Monorepo dynamics: root repository anchoring (`git rev-parse --show-toplevel`) and root versioning vs opt-out.
  - Updated Section 14 (Environment Variables) table with `GITPR_SKIP_PROJECT_CONFIG_SEED`.

### 2. Interactive Configuration Guide
- **File:** [docs/config-tui.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/config-tui.md)
  - Updated Section 1.8 with details on automatic runtime seeding and `GITPR_SKIP_PROJECT_CONFIG_SEED` for automated scripts, CI, and monorepos.

### 3. Domain Model
- **File:** [CONTEXT.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md)
  - Added formal domain terms under `## Language`:
    - **`Project configuration seed`**
    - **`Project configuration seed opt-out`**

### 4. Project Development Reference
- **File:** [GEMINI.md](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/GEMINI.md)
  - Added `GITPR_SKIP_PROJECT_CONFIG_SEED` to the environment variables reference list under `User configuration`.

## Verification Results
- All updated documents follow GitHub markdown standards and formatting rules.
- Internal links verified: anchor link `#94-migration--workflow-note-cicd-monorepos-and-clean-trees` properly references the newly added section.
- Terminology aligned with `CONTEXT.md`.
