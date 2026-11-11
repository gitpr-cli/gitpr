# Implementation Plan — Marketplace Setup Wizard & Extension Publishing

**Date:** 2026-11-10  
**Branch:** `develop_natan`  
**Task:** `publish_extension_marketplaces`  

---

## 1. Goal Description

Provide a streamlined, interactive onboarding tool (`scripts/marketplace-setup-wizard.sh`) that assists the human maintainer in obtaining and validating credentials (`VSCE_PAT` and `OVSX_PAT`) for both Visual Studio Marketplace and Open VSX Registry, provisions them securely to GitHub repository secrets, updates project domain documentation in 5 languages, and prompts the official `ext-v0.1.0` release.

---

## 2. User Review Required

> [!IMPORTANT]
> The wizard requires user interaction to open portal URLs, complete third-party web registrations, and paste generated PAT tokens into masked prompts. It does **not** persist any token to disk. It uses GitHub CLI (`gh secret set`) to configure GitHub Actions secrets directly.

---

## 3. Proposed Changes

### Scripts
#### [NEW] `scripts/marketplace-setup-wizard.sh`
Interactive bash wizard built on the standardized wizard library (`template.sh`):
- Stage 1: Prerequisites check (`git`, `gh auth`, `node`/`npx`).
- Stage 2: Azure DevOps PAT configuration (`Marketplace: Acquire, Manage`), publisher verification (`natanfiuza`), masked capture of `VSCE_PAT`.
- Stage 3: Local verification via `npx @vscode/vsce verify-pat natanfiuza -p "$VSCE_PAT"` and secret upload to GitHub (`set_secret VSCE_PAT`).
- Stage 4: Open VSX Registry namespace verification (`natanfiuza`), Access Token generation, masked capture of `OVSX_PAT`.
- Stage 5: Local verification via `npx ovsx verify-pat -p "$OVSX_PAT"` and secret upload to GitHub (`set_secret OVSX_PAT`), followed by release trigger prompt for tag `ext-v0.1.0`.

### Domain Model
#### [MODIFY] `CONTEXT.md`
- Add canonical domain term: `Marketplace setup wizard`.

### Documentation
#### [MODIFY] `docs/marketplace-publishing-guide.md`
#### [MODIFY] `docs/marketplace-publishing-guide.pt_br.md`
#### [MODIFY] `docs/marketplace-publishing-guide.pt_pt.md`
#### [MODIFY] `docs/marketplace-publishing-guide.es_es.md`
#### [MODIFY] `docs/marketplace-publishing-guide.fr_fr.md`
- Add "Quick Setup with the Marketplace Setup Wizard" section before manual steps.

#### [MODIFY] `README.md`
- Reference the new setup wizard in the Extension section.

### Automated Tests
#### [MODIFY] `tests/unit/test_marketplace_publishing_guide_docs_parity.py`
- Add assertions verifying that `marketplace-setup-wizard.sh` is referenced across all 5 localized guides.

#### [NEW] `tests/unit/test_marketplace_wizard_syntax.py`
- Verify bash script syntax (`bash -n scripts/marketplace-setup-wizard.sh`) and required markers (`TOTAL_STAGES`, `VSCE_PAT`, `OVSX_PAT`, `set_secret`).

---

## 4. Verification Plan

### Automated Tests
- Run `pytest tests/unit/test_marketplace_wizard_syntax.py`
- Run `pytest tests/unit/test_marketplace_publishing_guide_docs_parity.py`
- Run full pytest test suite: `pytest tests/`

### Manual Verification
- Verify executable permissions: `chmod +x scripts/marketplace-setup-wizard.sh`
- Perform dry-run tracing of wizard stages.
