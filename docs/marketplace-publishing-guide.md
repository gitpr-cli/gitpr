# Marketplace Publishing & Setup Guide (VS Code & Cursor)

This guide provides step-by-step instructions for publishing the **GitPR Editor Extension** to the **Visual Studio Marketplace** (for VS Code) and the **Open VSX Registry** (for Cursor and other open-source editors).

---

## Overview

The publication is fully automated via GitHub Actions (`.github/workflows/extension.yml`). When an official release tag (`ext-v*`) is pushed, the workflow:
1. Validates that the git tag version strictly matches `extensions/vscode/package.json`.
2. Compiles TypeScript and runs mocha integration tests.
3. Packages the extension into a `.vsix` bundle containing the official icon and license.
4. **Creates an official GitHub Release** with the `.vsix` bundle permanently attached for direct download.
5. Evaluates `VSCE_PAT` and `OVSX_PAT` independently (**Granular Marketplace Gate**):
   - If `VSCE_PAT` is configured, publishes to Visual Studio Marketplace.
   - If `OVSX_PAT` is configured, publishes to Open VSX Registry.
   - If either secret is missing, logs an informative notice and summary table in the workflow without blocking the GitHub Release.

---

## 1. Visual Studio Marketplace Setup (Microsoft / VS Code)

### Step 1.1: Azure DevOps Organization
1. Sign in to [Azure DevOps](https://dev.azure.com) with the Microsoft account managing the GitPR extension.
2. If you don't already have an organization, create one (e.g., `natanfiuza` or your chosen dev organization name).

### Step 1.2: Generate Personal Access Token (PAT)
1. In Azure DevOps, click the **User Settings** gear icon (top right, next to your profile photo) and select **Personal access tokens**.
2. Click **+ New Token**.
3. Fill in the details:
   - **Name**: `gitpr-marketplace-publish`
   - **Organization**: Select **All accessible organizations**. *(Crucial: vsce requires a multi-organization PAT).*
   - **Expiration**: Select 1 year (or 90 days, depending on security requirements).
   - **Scopes**: Click **Show all scopes** at the bottom, scroll down to **Marketplace**, and select:
     - `Acquire`
     - `Manage` (allows publishing extensions)
4. Click **Create** and **copy the PAT immediately**.

### Step 1.3: Create Visual Studio Marketplace Publisher
1. Go to the [Visual Studio Marketplace Management Portal](https://marketplace.visualstudio.com/manage).
2. Click **Create publisher**.
3. Enter the details:
   - **ID**: `natanfiuza` *(must match `"publisher": "natanfiuza"` in `package.json`)*.
   - **Name**: `Natan Fiuza`
   - **Email**: `contato@natanfiuza.dev.br`
4. Confirm creation.

### Step 1.4: Add Secret to GitHub
1. In the GitHub repository, navigate to **Settings > Secrets and variables > Actions**.
2. Click **New repository secret**.
3. Name: `VSCE_PAT`
4. Value: Paste your Azure DevOps Personal Access Token.

---

## 2. Open VSX Registry Setup (Eclipse Foundation / Cursor)

The Open VSX Registry powers extension search in Cursor, VSCodium, Gitpod, and other open IDEs.

### Step 2.1: Create Account
1. Go to [open-vsx.org](https://open-vsx.org) and sign in using your GitHub account (`natanfiuza`).

### Step 2.2: Register the Namespace
1. Go to the [Open VSX Namespaces](https://open-vsx.org/user-settings/namespaces) section or request creation of the `natanfiuza` namespace.
2. If self-service creation is available under your user settings, create namespace `natanfiuza` *(must match `"publisher": "natanfiuza"` in `package.json`)*.
3. If namespace ownership requires verification, link your GitHub organization or personal profile as instructed by Open VSX.

### Step 2.3: Generate Access Token
1. Go to your [User Settings > Access Tokens](https://open-vsx.org/user-settings/tokens) on open-vsx.org.
2. Create a new token (e.g. `gitpr-ovsx-token`).
3. Copy the generated token string.

### Step 2.4: Add Secret to GitHub
1. In the GitHub repository, navigate to **Settings > Secrets and variables > Actions**.
2. Click **New repository secret**.
3. Name: `OVSX_PAT`
4. Value: Paste your Open VSX Access Token.

---

## 3. Local Verification & Dry-Run (Optional)

Before triggering the public release, you can test authentication and packaging locally:

### Verify PATs with CLIs
```bash
cd extensions/vscode

# Test Visual Studio Marketplace PAT
npx @vscode/vsce verify-pat natanfiuza -p "<YOUR_VSCE_PAT>"

# Test Open VSX PAT
npx ovsx verify-pat -p "<YOUR_OVSX_PAT>"
```

### Local Packaging Test
```bash
npm run compile
npm test
npm run package
```
This produces `gitpr-0.1.0.vsix` containing `images/icon.png`, `LICENSE.txt`, compiled bundles, and manifest files.

---

## 4. Triggering the Automated Release

When you are ready to publish a new release:

1. Ensure `extensions/vscode/package.json` has the version you want to release (e.g., `"version": "0.1.0"`).
2. Commit any pending changes to `main` or your release branch.
3. Create and push an annotated git tag matching `ext-v<version>`:
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
4. GitHub Actions will run the **Editor Extension** workflow:
   - Validates that `ext-v0.1.0` matches `0.1.0`.
   - Runs tests and builds the VSIX.
   - **Creates the GitHub Release** with `gitpr-0.1.0.vsix` attached as an asset.
   - Automatically publishes to Visual Studio Marketplace and/or Open VSX Registry if their respective secrets (`VSCE_PAT`, `OVSX_PAT`) are configured. If not yet configured, the VSIX remains available on GitHub Releases and marketplace publication will activate once secrets are added.

---

## 5. Maintenance & Future Releases

- **Bumping version**: Update `"version"` in `extensions/vscode/package.json` and push the corresponding tag (e.g., `ext-v0.1.1`).
- **Token expiration**: Azure DevOps PATs expire after at most 1 year. Remember to regenerate `VSCE_PAT` and update the repository secret before expiration.
