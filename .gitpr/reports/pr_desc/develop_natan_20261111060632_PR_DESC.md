# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: add interactive marketplace setup wizard script
```

---

## 🎯 Summary

Publishing the GitPR editor extension requires two sets of marketplace credentials — an Azure DevOps Personal Access Token (`VSCE_PAT`) for the Visual Studio Marketplace and an Open VSX access token (`OVSX_PAT`) for Cursor/VSCodium — plus the correct GitHub Actions secrets that consume them. Doing this by hand is error-prone: the PAT must be scoped to "All accessible organizations", the publisher/namespace must already exist, and a mistyped token is only discovered much later when the release pipeline fails.

This PR introduces a guided, idempotent setup wizard that walks a maintainer through the exact browser steps, validates each token against the real marketplace APIs before storing it, provisions the corresponding GitHub secrets, and optionally triggers the release tag.

## 🛠️ Technical Changes

- Add `scripts/marketplace-setup-wizard.sh`, a 5-stage interactive CLI wizard:
  - Stage 1: verifies local prerequisites (`gh` authentication, `npx` availability) and degrades gracefully with warnings instead of aborting.
  - Stage 2: guides creation of the Azure DevOps PAT, explicitly calling out the required "All accessible organizations" organization scope and the Marketplace → Acquire/Manage scopes.
  - Stage 3: validates `VSCE_PAT` via `npx @vscode/vsce verify-pat` before writing it, then stores it as a GitHub Actions secret.
  - Stage 4: guides Open VSX namespace registration and access-token generation.
  - Stage 5: validates `OVSX_PAT` via `npx ovsx verify-pat`, stores the secret, and offers to create and push the annotated `ext-v0.1.0` release tag.
- Embed a shared, reusable wizard library (colored banners, stage progress, `ask`/`ask_secret` prompts, `write_env` upsert, `set_secret`/`set_var` wrappers, and a closing summary listing anything still to be done manually).
- Make the flow re-runnable: existing `.env` values are offered as defaults (Enter keeps current), and `write_env` upserts keys idempotently.
- Cross-platform URL opening via `wslview`, `explorer.exe`, `xdg-open`, or `open`.
- Add `tests/unit/test_marketplace_wizard_syntax.py` covering file presence/shebang, required wizard markers and stage count, and static `bash -n` syntax validation (preferring Git Bash on Windows to avoid blocking WSL calls, and skipping when no bash is available).
- Register the new script in `tests/unit/test_marketplace_publishing_guide_docs_parity.py` so its documented tokens are covered by the documentation parity check.

## ⚠️ Impact/Warnings

- **Filesystem:** the wizard writes/updates `KEY=VALUE` entries in `.env` (path overridable via the `ENV_FILE` environment variable). Ensure `.env` remains git-ignored.
- **GitHub configuration:** running the wizard mutates repository settings — it creates the Actions secrets `VSCE_PAT` and `OVSX_PAT` (and may set repository variables) through the `gh` CLI when authenticated. If `gh` is missing or unauthenticated, it records the items as manual follow-ups instead of failing.
- **Git history:** Stage 5 can create and push the annotated tag `ext-v0.1.0` to `origin`, which triggers the release workflow. This requires an explicit `y` confirmation.
- **Hardcoded configuration:** `PUBLISHER_ID` is pinned to `natanfiuza` and the release tag to `ext-v0.1.0`; forks must edit these values before use.
- **Dependencies:** no new runtime dependencies for the project itself, but the wizard's validation steps rely on `npx` and the `@vscode/vsce` / `ovsx` packages being fetchable at run time (verification is skipped when unavailable).
- **Database:** no schema or migration changes.

close #313

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)