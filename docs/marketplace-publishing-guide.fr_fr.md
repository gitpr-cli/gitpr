# Guide de Publication et de Configuration sur les Marketplaces (VS Code & Cursor)

Ce guide fournit des instructions pas à pas pour publier l'**Extension d'Éditeur GitPR** sur le **Visual Studio Marketplace** (pour VS Code) et sur l'**Open VSX Registry** (pour Cursor et d'autres éditeurs open source).

---

## Vue d'Ensemble

La publication est entièrement automatisée via GitHub Actions (`.github/workflows/extension.yml`). Lorsqu'un tag de release officiel (`ext-v*`) est poussé, le workflow :
1. Valide que la version du tag git correspond strictement au champ `"version"` dans `extensions/vscode/package.json`.
2. Compile le TypeScript et exécute les tests d'intégration Mocha.
3. Empaquette l'extension dans une archive `.vsix` contenant l'icône officielle et la licence.
4. **Crée une GitHub Release officielle** avec l'archive `.vsix` attachée en permanence pour un téléchargement direct.
5. Évalue `VSCE_PAT` et `OVSX_PAT` de manière indépendante (**Granular Marketplace Gate**) :
   - Si `VSCE_PAT` est configuré, publie sur le Visual Studio Marketplace.
   - Si `OVSX_PAT` est configuré, publie sur l'Open VSX Registry.
   - Si l'un des secrets est absent, consigne un avertissement informatif et un tableau récapitulatif dans le workflow sans bloquer la GitHub Release.

---

## Configuration Rapide avec l'Assistant Marketplace (Recommandé)

Pour accélérer la génération des jetons, la validation locale via CLI et l'approvisionnement des secrets dans le dépôt, exécutez l'assistant interactif :

```bash
chmod +x scripts/marketplace-setup-wizard.sh
./scripts/marketplace-setup-wizard.sh
```

L'assistant vous guide lors de l'enregistrement sur Azure DevOps et Open VSX, ouvre les pages de configuration dans le navigateur, valide les jetons localement (`vsce verify-pat`, `ovsx verify-pat`), approvisionne `VSCE_PAT` et `OVSX_PAT` dans les secrets GitHub via `gh secret set`, et propose éventuellement la création et l'envoi du tag de release `ext-v0.1.0`.

Pour des instructions manuelles détaillées, suivez les sections ci-dessous.

---

## 1. Configuration du Visual Studio Marketplace (Microsoft / VS Code)

### Étape 1.1 : Organisation Azure DevOps
1. Connectez-vous à [Azure DevOps](https://dev.azure.com) avec le compte Microsoft gérant l'extension GitPR.
2. Si vous n'avez pas encore d'organisation, créez-en une (par exemple `natanfiuza` ou le nom d'organisation de développement de votre choix).

### Étape 1.2 : Générer un Personal Access Token (PAT)
1. Dans Azure DevOps, cliquez sur l'icône d'engrenage **User Settings** (en haut à droite, à côté de votre photo de profil) et sélectionnez **Personal access tokens**.
2. Cliquez sur **+ New Token**.
3. Renseignez les informations :
   - **Name** : `gitpr-marketplace-publish`
   - **Organization** : Sélectionnez **All accessible organizations**. *(Crucial : vsce requiert un PAT multi-organisation).*
   - **Expiration** : Sélectionnez 1 an (ou 90 jours, selon vos exigences de sécurité).
   - **Scopes** : Cliquez sur **Show all scopes** en bas, faites défiler jusqu'à **Marketplace**, puis sélectionnez :
     - `Acquire`
     - `Manage` (permet de publier des extensions)
4. Cliquez sur **Create** et **copiez le PAT immédiatement**.

### Étape 1.3 : Créer l'Éditeur sur le Visual Studio Marketplace
1. Accédez au [Portail de Gestion du Visual Studio Marketplace](https://marketplace.visualstudio.com/manage).
2. Cliquez sur **Create publisher**.
3. Saisissez les informations :
   - **ID** : `natanfiuza` *(doit correspondre à `"publisher": "natanfiuza"` dans `package.json`)*.
   - **Name** : `Natan Fiuza`
   - **Email** : `contato@natanfiuza.dev.br`
4. Confirmez la création.

### Étape 1.4 : Ajouter le Secret sur GitHub
1. Dans le dépôt GitHub, accédez à **Settings > Secrets and variables > Actions**.
2. Cliquez sur **New repository secret**.
3. Nom : `VSCE_PAT`
4. Valeur : Collez votre Personal Access Token d'Azure DevOps.

---

## 2. Configuration de l'Open VSX Registry (Eclipse Foundation / Cursor)

L'Open VSX Registry alimente la recherche d'extensions dans Cursor, VSCodium, Gitpod et d'autres IDE open source.

### Étape 2.1 : Créer un Compte
1. Accédez à [open-vsx.org](https://open-vsx.org) et connectez-vous avec votre compte GitHub (`natanfiuza`).

### Étape 2.2 : Enregistrer le Namespace
1. Rendez-vous dans la section [Open VSX Namespaces](https://open-vsx.org/user-settings/namespaces) ou demandez la création du namespace `natanfiuza`.
2. Si la création en libre-service est disponible dans vos paramètres utilisateur, créez le namespace `natanfiuza` *(doit correspondre à `"publisher": "natanfiuza"` dans `package.json`)*.
3. Si la propriété du namespace requiert une vérification, liez votre organisation GitHub ou votre profil personnel comme indiqué par Open VSX.

### Étape 2.3 : Générer un Access Token
1. Accédez à vos [User Settings > Access Tokens](https://open-vsx.org/user-settings/tokens) sur open-vsx.org.
2. Créez un nouveau jeton (par exemple `gitpr-ovsx-token`).
3. Copiez la chaîne du jeton généré.

### Étape 2.4 : Ajouter le Secret sur GitHub
1. Dans le dépôt GitHub, accédez à **Settings > Secrets and variables > Actions**.
2. Cliquez sur **New repository secret**.
3. Nom : `OVSX_PAT`
4. Valeur : Collez votre Access Token Open VSX.

---

## 3. Vérification Locale et Simulation (Facultatif)

Avant de déclencher la publication publique, vous pouvez tester l'authentification et l'empaquetage localement :

### Vérifier les PATs avec les CLIs
```bash
cd extensions/vscode

# Tester le PAT du Visual Studio Marketplace
npx @vscode/vsce verify-pat natanfiuza -p "<VOTRE_VSCE_PAT>"

# Tester le PAT d'Open VSX
npx ovsx verify-pat -p "<VOTRE_OVSX_PAT>"
```

### Test Local d'Empaquetage
```bash
npm run compile
npm test
npm run package
```
Cela produit `gitpr-0.1.0.vsix` contenant `images/icon.png`, `LICENSE.txt`, les bundles compilés et les fichiers manifestes.

---

## 4. Déclencher la Publication Automatisée

Lorsque vous êtes prêt à publier une nouvelle version :

1. Assurez-vous que `extensions/vscode/package.json` contient la version que vous souhaitez publier (par exemple, `"version": "0.1.0"`).
2. Committez tous les changements en attente sur `main` ou votre branche de release.
3. Créez et poussez un tag git annoté correspondant à `ext-v<version>` :
   ```bash
   git tag ext-v0.1.0
   git push origin ext-v0.1.0
   ```
4. GitHub Actions exécutera le workflow **Editor Extension** :
   - Valide que `ext-v0.1.0` correspond à `0.1.0`.
   - Exécute les tests et compile le VSIX.
   - **Crée la GitHub Release** avec `gitpr-0.1.0.vsix` attaché en tant qu'actif (asset).
   - Publie automatiquement sur le Visual Studio Marketplace et/ou l'Open VSX Registry si leurs secrets respectifs (`VSCE_PAT`, `OVSX_PAT`) sont configurés. S'ils ne sont pas encore configurés, le VSIX reste accessible sur GitHub Releases et la publication sur les marketplaces s'activera dès que les secrets seront ajoutés.

---

## 5. Maintenance et Versions Futures

- **Montée de version** : Mettez à jour `"version"` dans `extensions/vscode/package.json` et poussez le tag correspondant (par exemple, `ext-v0.1.1`).
- **Expiration des jetons** : Les PATs Azure DevOps expirent au bout d'un an au maximum. Pensez à régénérer `VSCE_PAT` et à mettre à jour le secret du dépôt avant l'échéance.
