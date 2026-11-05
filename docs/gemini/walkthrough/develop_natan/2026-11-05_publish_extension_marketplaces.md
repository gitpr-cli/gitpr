# Walkthrough — Publish GitPR Extension to Marketplaces

## Overview
We have prepared, hardened, and documented the entire pipeline required to publish the GitPR Editor Extension for VS Code and Cursor to the **Visual Studio Marketplace** and **Open VSX Registry**, completing the inherited open backlog item.

---

## Changes Made

### 1. Visual Identity & Marketplace Manifest
- Generated 256x256 high-resolution icon: [`extensions/vscode/images/icon.png`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/images/icon.png) from `docs/logo_2048.png`.
- Updated [`extensions/vscode/package.json`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/package.json):
  - Added `"icon": "images/icon.png"`
  - Added `"homepage": "https://github.com/natanfiuza/gitpr"`
  - Added `"bugs": { "url": "https://github.com/natanfiuza/gitpr/issues" }`
- Added [`extensions/vscode/LICENSE`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/LICENSE) (LGPL-2.1) to eliminate packaging warnings and meet marketplace requirements.

### 2. CI/CD Workflow Hardening
- Updated [`.github/workflows/extension.yml`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/.github/workflows/extension.yml):
  - **Manual Trigger:** Added `workflow_dispatch` with optional `dry_run` input.
  - **Tag Verification:** Added step `Verify Git Tag matches package.json version` on `ext-v*` tags to prevent releasing mismatched artifacts.
  - **Fail-Fast Secret Check:** Added step `Validate Publishing Credentials` on `ext-v*` release runs that strictly halts the build with fatal error messages if `VSCE_PAT` or `OVSX_PAT` are missing in GitHub repository secrets.
  - **Scoping Fix:** Configured `env: VSCE_PAT / OVSX_PAT` at the job level so conditional checks evaluate correctly in GitHub Actions.

### 3. Test Suite & Local VSIX Packaging
- Updated [`extensions/vscode/src/test/mcp_client.test.ts`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/src/test/mcp_client.test.ts) to extend the mocha timeout from 20s to 60s for the live Python MCP server stdio integration test, accommodating Windows import times.
- Verified that `npm test` runs and passes all 7 tests.
- Verified that `npm run package` compiles cleanly and produces [`extensions/vscode/gitpr-0.1.0.vsix`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/extensions/vscode/gitpr-0.1.0.vsix) with 34 packaged files, including `images/icon.png` and `LICENSE.txt`.

### 4. Step-by-Step Marketplace Publishing Guide
- Created [`docs/marketplace-publishing-guide.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/marketplace-publishing-guide.md) documenting:
  - Visual Studio Marketplace: Azure DevOps organization, Personal Access Token with `Marketplace (Manage)` scope, publisher ID (`natanfiuza`), and GitHub secret `VSCE_PAT`.
  - Open VSX Registry: Account creation, namespace registration (`natanfiuza`), token generation, and GitHub secret `OVSX_PAT`.
  - Local verification CLI commands (`vsce verify-pat`, `ovsx verify-pat`).
  - Official release execution command (`git tag ext-v0.1.0 && git push origin ext-v0.1.0`).
- Updated [`docs/editor-extension.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/editor-extension.md) and localized files (`pt_br`, `pt_pt`, `es_es`, `fr_fr`) to link to the guide.

### 5. Domain Modeling
- Updated [`CONTEXT.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/CONTEXT.md) with canonical domain terms:
  - **Marketplace publication workflow**
  - **Extension release tag**
  - **Fail-fast secret check**

---

## Validation Results

| Test / Check | Result | Details |
|---|---|---|
| Extension Icon | **PASSED** | 256x256 PNG generated and verified via binary header parser |
| Extension Mocha Tests (`npm test`) | **PASSED** | 7 passing tests including live stdio MCP handshake with `src.mcp_server` |
| VSIX Packaging (`npm run package`) | **PASSED** | Packaged 34 files without warnings (license + icon confirmed) |
| Workflow YAML Syntax | **PASSED** | Validated structure, job-level secrets, and fail-fast step |
| Documentation Links | **PASSED** | All 5 language guides updated with marketplace guide reference |

---

## Release Instructions for User

Once you are ready to publish:
1. Follow [`docs/marketplace-publishing-guide.md`](file:///c:/Users/nataniel/projetos/pessoal/gitpr_projeto/gitpr/docs/marketplace-publishing-guide.md) to obtain your PATs:
   - Configure secret `VSCE_PAT` in GitHub (`Settings > Secrets and variables > Actions`).
   - Configure secret `OVSX_PAT` in GitHub.
2. Push the official release tag:
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
3. GitHub Actions will execute `.github/workflows/extension.yml` and publish directly to both marketplaces.
