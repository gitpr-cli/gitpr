## Completion Report — Publish GitPR Extension (VSIX Distribution & Granular Marketplaces)

### What was done
- Conducted the decision interview (grilling) and aligned on decoupling the official `.vsix` distribution from third-party marketplace accounts.
- Updated `.github/workflows/extension.yml`:
  - Added dedicated `github-release` job that triggers on `ext-v*` tags, creates an official GitHub Release with `softprops/action-gh-release@v2`, and attaches the compiled `gitpr-0.1.0.vsix` as a permanent asset with `contents: write` permissions.
  - Replaced the rigid fail-fast check (`missing=1; exit 1`) in `publish-marketplaces` with an independent, non-blocking **Granular Marketplace Gate** that evaluates `VSCE_PAT` and `OVSX_PAT` separately.
  - Implemented automatic `$GITHUB_STEP_SUMMARY` markdown reporting in CI showing publication status per marketplace.
- Updated `CONTEXT.md` to retire the deprecated `Fail-fast secret check` term in favor of the canonical domain term `Granular marketplace gate`.
- Updated documentation across all 5 supported languages (`docs/editor-extension.md`, `.pt_br.md`, `.pt_pt.md`, `.es_es.md`, `.fr_fr.md`) with 1-click terminal install commands (`code --install-extension gitpr-0.1.0.vsix`, `cursor --install-extension gitpr-0.1.0.vsix`) and GUI installation steps.
- Updated `README.md` to highlight the direct VSIX download from GitHub Releases.
- Updated `docs/marketplace-publishing-guide.md` to describe progressive marketplace token enablement.
- Verified test suite: 117 tests passing in `tests/test_mcp_server.py`, 7 tests passing in `extensions/vscode` mocha suite (including live stdio MCP handshake), and clean packaging of `gitpr-0.1.0.vsix` (34 files, 90.34 KB).

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `.github/workflows/extension.yml` | feat | Added `github-release` job and non-blocking `publish-marketplaces` granular gate |
| `CONTEXT.md` | docs | Replaced `Fail-fast secret check` with `Granular marketplace gate` |
| `docs/marketplace-publishing-guide.md` | docs | Updated setup and release instructions for granular token evaluation |
| `docs/editor-extension.md` | docs | Added 1-click terminal & GUI VSIX installation instructions (EN) |
| `docs/editor-extension.pt_br.md` | docs | Added 1-click terminal & GUI VSIX installation instructions (PT-BR) |
| `docs/editor-extension.pt_pt.md` | docs | Added 1-click terminal & GUI VSIX installation instructions (PT-PT) |
| `docs/editor-extension.es_es.md` | docs | Added 1-click terminal & GUI VSIX installation instructions (ES-ES) |
| `docs/editor-extension.fr_fr.md` | docs | Added 1-click terminal & GUI VSIX installation instructions (FR-FR) |
| `README.md` | docs | Updated extension section with direct GitHub Releases VSIX download link |
| `docs/survey/20261109_publish_extension_marketplaces_surveyfacts.md` | docs | Fact survey artifact from grilling session |
| `docs/plans/develop_natan/20261109_publish_extension_marketplaces_plansfacts.md` | docs | Execution plan artifact from grilling session |
| `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_publish_extension_marketplaces.md` | docs | Task implementation plan |
| `docs/gemini/walkthrough/develop_natan/2026-11-09_publish_extension_marketplaces.md` | docs | Task walkthrough with sequence diagram |

### Impact
- **Functionality:** Users can now immediately install and update the GitPR Editor Extension in VS Code and Cursor via `.vsix` attached directly to GitHub Releases upon pushing any `ext-v*` tag. When `VSCE_PAT` and/or `OVSX_PAT` are added to repository secrets, marketplace publication activates automatically without disrupting VSIX releases.
- **Performance:** Zero runtime overhead. The packaged `.vsix` is compact (~90 KB) and self-contained.
- **Compatibility:** Fully compatible with VS Code ^1.85.0, Cursor, VSCodium, and all GitPR MCP server tools.

### Next steps (if applicable)
- Create tag `ext-v0.1.0` (`git tag ext-v0.1.0 && git push origin ext-v0.1.0`) to trigger the first automated GitHub Release of the extension.
- When ready to publish to official stores, follow `docs/marketplace-publishing-guide.md` to add `VSCE_PAT` and `OVSX_PAT` to GitHub repository secrets.
