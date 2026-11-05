# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: harden extension release workflow and marketplace metadata
```

---

## 🎯 Summary

Prepares the VS Code extension for public distribution on the Visual Studio Marketplace and Open VSX Registry. The release pipeline is hardened so that a mis-tagged build or missing credential fails fast and loudly instead of publishing a broken or unversioned artifact, and the package now carries the metadata (icon, license, homepage, issue tracker) required for a credible marketplace listing.

## 🛠️ Technical Changes

- Add `workflow_dispatch` trigger with a `dry_run` boolean input, allowing manual packaging/testing runs without publishing.
- Add a pre-build guard that verifies the Git tag (`ext-v<version>`) matches `extensions/vscode/package.json` version, aborting the release on mismatch.
- Add a credential validation step in the publish job that fails with `::error::` annotations when `VSCE_PAT` or `OVSX_PAT` is missing.
- Move `VSCE_PAT`/`OVSX_PAT` from individual step-level `env` blocks to job-level `env` so both validation and publish steps can read them.
- Extend the publish job condition to also run on `workflow_dispatch` when `dry_run` is false.
- Add `extensions/vscode/LICENSE` (LGPL-2.1) so the packaged extension ships its license text.
- Add `extensions/vscode/images/icon.png` and reference it via the new `icon` field in `package.json`.
- Add `homepage` and `bugs.url` fields to `package.json` pointing to the upstream GitHub repository.
- Raise the MCP client integration test timeout from 20s to 60s to accommodate slower cold starts of the real Python `gitpr-mcp` process.
- Update marketplace publishing documentation and editor-extension guides (EN, ES, FR, PT-BR, PT-PT) to reflect the new release process.

## ⚠️ Impact/Warnings

- **Secrets required:** `VSCE_PAT` and `OVSX_PAT` must exist in GitHub repository secrets; releases now hard-fail without them.
- **Release discipline:** tags must follow `ext-v<package.json version>` exactly, otherwise the workflow aborts.
- **No database or dependency changes.**
- The new license file and icon are packaging artifacts only and do not affect runtime behavior.

close #269

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)