# Implementation Plan — Publish GitPR Extension to Marketplaces

## Goal Description
Prepare, harden, and document the automated publication pipeline for the GitPR VS Code & Cursor extension to the **Visual Studio Marketplace** and **Open VSX Registry**, closing the inherited open backlog item. This involves adding visual identity (icon) and metadata to `package.json`, fixing and strengthening `.github/workflows/extension.yml` with fail-fast secret checks and tag-vs-version validation, creating a comprehensive step-by-step publisher setup guide (`docs/marketplace-publishing-guide.md`), and verifying VSIX packaging.

---

## User Review Required

> [!IMPORTANT]
> **GitHub Secrets Configuration Required Before Triggering Tag:**
> In order for the workflow to publish to the marketplaces, two repository secrets must be configured in GitHub (`Settings > Secrets and variables > Actions`):
> 1. `VSCE_PAT` — Azure DevOps Personal Access Token with scope `Marketplace (Manage)` for publisher `natanfiuza`.
> 2. `OVSX_PAT` — Open VSX Personal Access Token for namespace `natanfiuza`.
> A dedicated guide (`docs/marketplace-publishing-guide.md`) will detail the exact setup steps.

> [!NOTE]
> The workflow will now be guarded with a **fail-fast secret check**: if an official release tag (`ext-v*`) is pushed without these secrets configured, the job will fail immediately with a descriptive error instead of silently passing without publishing.

---

## Open Questions
None. All design questions were resolved during the grilling interview rounds:
- **Q1 (Objective):** Full hardening and preparation of pipeline + provisioning guide.
- **Q2 (Publishers):** Include full account and namespace creation instructions for `natanfiuza`.
- **Q3 (Icon):** Generate and package `images/icon.png` from `docs/assets/logo.png`.
- **Q4 (Secrets):** Fail-fast behavior on release tags if secrets are missing.
- **Q5 (Tag Validation):** Enforce strict tag match against `package.json` version (`ext-v` + `version`).
- **Q6 (Trigger):** Add `workflow_dispatch` for manual testing and verification.
- **Q7 (Documentation):** Create dedicated `docs/marketplace-publishing-guide.md`.

---

## Proposed Changes

```
gitpr/
├── .github/workflows/
│   └── extension.yml                     # [MODIFY] Add workflow_dispatch, tag check, fail-fast secrets check
├── extensions/vscode/
│   ├── images/
│   │   └── icon.png                      # [NEW] Extension icon (256x256) derived from docs/assets/logo.png
│   ├── package.json                      # [MODIFY] Add icon field and marketplace metadata
│   └── .vscodeignore                     # [MODIFY] Ensure images/icon.png is packaged into VSIX
├── docs/
│   ├── marketplace-publishing-guide.md   # [NEW] Step-by-step setup guide for Azure DevOps & Open VSX PATs
│   └── editor-extension.md               # [MODIFY] Link to publishing guide
└── CONTEXT.md                            # [ALREADY UPDATED] Added canonical domain terms
```

---

### Component: Visual Identity & Package Manifest (`extensions/vscode/`)

#### [NEW] `extensions/vscode/images/icon.png`
- Generate an optimized 256x256 PNG icon from `docs/assets/logo.png`.

#### [MODIFY] `extensions/vscode/package.json`
- Add `"icon": "images/icon.png"`.
- Ensure repository, bugs, homepage, and gallery metadata are properly configured for marketplace display.

#### [MODIFY] `extensions/vscode/.vscodeignore`
- Ensure `!images/icon.png` or `!images/**` is explicitly un-ignored so the icon is included in the `.vsix` bundle.

---

### Component: CI/CD Workflow (`.github/workflows/extension.yml`)

#### [MODIFY] `.github/workflows/extension.yml`
- Add `workflow_dispatch` trigger:
  ```yaml
  on:
    pull_request:
      paths:
        - "extensions/**"
        - ".github/workflows/extension.yml"
    push:
      tags:
        - "ext-v*"
    workflow_dispatch:
      inputs:
        dry_run:
          description: "Package and test only, skip publishing even if secrets exist"
          type: boolean
          default: false
  ```
- In `build-and-test` job:
  - Add tag vs `package.json` version validation step:
    ```yaml
    - name: Verify Git Tag matches package.json version
      if: startsWith(github.ref, 'refs/tags/ext-v')
      run: |
        python -c "
        import json, os, sys
        with open('extensions/vscode/package.json', 'r', encoding='utf-8') as f:
            pkg = json.load(f)
        ref = os.environ.get('GITHUB_REF_NAME', '')
        expected = f'ext-v{pkg[\"version\"]}'
        if ref != expected:
            sys.exit(f'FATAL: Tag mismatch! Git tag is \"{ref}\" but package.json version is \"{pkg[\"version\"]}\" (expected \"{expected}\").')
        print(f'OK: Tag {ref} matches package.json version {pkg[\"version\"]}')
        "
    ```
- In `publish` job:
  - Update trigger condition:
    ```yaml
    if: startsWith(github.ref, 'refs/tags/ext-v') || (github.event_name == 'workflow_dispatch' && !inputs.dry_run)
    ```
  - Add **Fail-Fast Secret Check** step:
    ```yaml
    - name: Validate Publishing Credentials
      if: startsWith(github.ref, 'refs/tags/ext-v')
      env:
        VSCE_PAT: ${{ secrets.VSCE_PAT }}
        OVSX_PAT: ${{ secrets.OVSX_PAT }}
      run: |
        missing=0
        if [ -z "$VSCE_PAT" ]; then
          echo "::error::Missing repository secret VSCE_PAT! Cannot publish to Visual Studio Marketplace."
          missing=1
        fi
        if [ -z "$OVSX_PAT" ]; then
          echo "::error::Missing repository secret OVSX_PAT! Cannot publish to Open VSX Registry."
          missing=1
        fi
        if [ $missing -eq 1 ]; then
          echo "FATAL: Required publishing secrets are missing from GitHub repository settings. Aborting release."
          exit 1
        fi
        echo "OK: All publishing secrets are configured."
    ```
  - Fix step execution for VS Code Marketplace and Open VSX:
    ```yaml
    - name: Publish to VS Code Marketplace
      if: env.VSCE_PAT != ''
      working-directory: extensions/vscode
      env:
        VSCE_PAT: ${{ secrets.VSCE_PAT }}
      run: npx @vscode/vsce publish --packagePath *.vsix -p "$VSCE_PAT"

    - name: Publish to Open VSX (Cursor)
      if: env.OVSX_PAT != ''
      working-directory: extensions/vscode
      env:
        OVSX_PAT: ${{ secrets.OVSX_PAT }}
      run: npx ovsx publish *.vsix -p "$OVSX_PAT"
    ```

---

### Component: Documentation (`docs/`)

#### [NEW] `docs/marketplace-publishing-guide.md`
Detailed guide containing:
1. **Visual Studio Marketplace (Microsoft):**
   - Microsoft/GitHub login.
   - Creating/linking Azure DevOps Organization.
   - Creating Personal Access Token (PAT) with `Marketplace (Manage)` scope.
   - Creating Publisher ID (`natanfiuza`) at `https://marketplace.visualstudio.com/manage`.
   - Adding `VSCE_PAT` to GitHub repository secrets.
2. **Open VSX Registry (Eclipse Foundation):**
   - Creating account on `https://open-vsx.org`.
   - Claiming/registering namespace `natanfiuza`.
   - Generating Personal Access Token.
   - Adding `OVSX_PAT` to GitHub repository secrets.
3. **Local Testing & Verification:**
   - Testing tokens locally via CLI (`npx @vscode/vsce verify-pat`, `npx ovsx verify-pat`).
   - Testing packaging locally (`npm run package`).
4. **Triggering the Official Release:**
   - Tag format: `ext-v0.1.0`.
   - Command: `git tag ext-v0.1.0 && git push origin ext-v0.1.0`.

#### [MODIFY] `docs/editor-extension.md`
- Add a reference link in the **Publishing** / **Marketplace** section pointing to `docs/marketplace-publishing-guide.md`.

---

## Verification Plan

### Automated Tests
1. **Python test suite:**
   ```bash
   pytest tests/ -v
   ```
2. **Extension compilation and test suite:**
   ```bash
   cd extensions/vscode && npm run compile && npm test
   ```
3. **VSIX packaging test:**
   ```bash
   cd extensions/vscode && npm run package
   ```
   Verify that `gitpr-0.1.0.vsix` is created, contains `images/icon.png`, and has no packaging warnings.

### Manual Verification
1. Inspect the generated VSIX archive contents:
   - Confirm `extension/images/icon.png` is present inside the archive.
   - Confirm `package.json` contains `"icon": "images/icon.png"` and `"publisher": "natanfiuza"`.
2. Inspect GitHub Actions workflow YAML syntax:
   - Verify valid syntax and step sequencing.
3. Review `docs/marketplace-publishing-guide.md`:
   - Verify all URLs, Azure DevOps permission scopes, and Open VSX instructions are accurate.
