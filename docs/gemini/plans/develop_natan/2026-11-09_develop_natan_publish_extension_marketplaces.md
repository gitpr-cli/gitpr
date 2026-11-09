# Implementation Plan — Publish GitPR Extension (VSIX Distribution & Granular Marketplaces)

**Date:** 2026-11-09  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  
**Artifact Plan Reference:** `publish_extension_marketplaces.md`

---

## 1. Goal Description

Unblock and modernize the GitPR Editor Extension release pipeline. The inherited backlog item depended on external `VSCE_PAT` and `OVSX_PAT` tokens which blocked the release workflow via a rigid fail-fast check.

This plan decouples official `.vsix` distribution by introducing an automated GitHub Release job for extension tags (`ext-v*`), refactors marketplace publication into a resilient, non-blocking **Granular Marketplace Gate**, updates the domain model in `CONTEXT.md`, and documents local VSIX installation for both VS Code and Cursor across all 5 supported documentation languages.

---

## 2. User Review Required

> [!IMPORTANT]
> **Decoupled VSIX Distribution:**
> Pushing an official tag such as `ext-v0.1.0` will now automatically generate a GitHub Release containing `gitpr-0.1.0.vsix` as a permanent asset, allowing users to install the extension in 1-click via terminal or editor GUI without needing marketplace accounts.

> [!NOTE]
> **Progressive Marketplace Deployment:**
> Marketplaces are now published independently. Adding `VSCE_PAT` to GitHub secrets enables VS Code Marketplace publishing, and adding `OVSX_PAT` enables Open VSX publishing, without either blocking the other or failing the GitHub Release.

---

## 3. Proposed Changes

```
.github/workflows/
└── extension.yml                           # [MODIFY] Decouple github-release and granular publish-marketplaces jobs
CONTEXT.md                                  # [MODIFY] Replace Fail-fast secret check with Granular marketplace gate
docs/
├── marketplace-publishing-guide.md         # [MODIFY] Update token configuration guide for granular behavior
├── editor-extension.md                     # [MODIFY] Add GitHub Releases VSIX download & 1-click install (EN)
├── editor-extension.pt_br.md               # [MODIFY] Add GitHub Releases VSIX download & 1-click install (PT-BR)
├── editor-extension.pt_pt.md               # [MODIFY] Add GitHub Releases VSIX download & 1-click install (PT-PT)
├── editor-extension.es_es.md               # [MODIFY] Add GitHub Releases VSIX download & 1-click install (ES-ES)
└── editor-extension.fr_fr.md               # [MODIFY] Add GitHub Releases VSIX download & 1-click install (FR-FR)
README.md                                   # [MODIFY] Add extension VSIX installation section
```

---

## 4. Verification Plan

### Automated Verification
```bash
# Verify Python test suite & MCP server tests
pytest tests/test_mcp_server.py -v

# Verify extension TypeScript build, test suite & packaging
cd extensions/vscode
npm run compile
npm test
npm run package
```

### Manual Verification
1. Inspect `.github/workflows/extension.yml` YAML syntax and job dependencies.
2. Confirm `extensions/vscode/gitpr-0.1.0.vsix` is created cleanly.
3. Review `CONTEXT.md` glossary consistency and documentation links in all 5 languages.
