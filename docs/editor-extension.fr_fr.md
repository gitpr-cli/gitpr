# Extension d'Éditeur GitPR (VS Code & Cursor)

L'**Extension d'Éditeur GitPR** intègre la génération de messages Conventional Commits par IA, les revues de code, la création et la publication de Pull Requests ainsi que les diagnostics unifiés `gitpr check` directement dans **VS Code** et **Cursor** sous forme de **client léger (thin client) MCP**.

---

## Architecture : Véritable Thin Client via MCP

Au lieu de dupliquer les modèles de prompts, l'analyseur de diff ou la gestion des identifiants en TypeScript, l'extension communique via `stdio` avec votre serveur local `gitpr-mcp` (`@modelcontextprotocol/sdk`) :

- **Une Session par Dossier de Workspace** : L'extension lance `gitpr-mcp` à la demande (lazy) lors de la première commande (avec `cwd` défini sur la racine du dossier) et maintient la session persistante, en se reconnectant automatiquement si le processus s'arrête.
- **Vérification du Contrat (Handshake)** : À la connexion, l'extension appelle `listTools` et vérifie que tous les outils requis (`get_git_context`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_check`, `publish_pull_request`) sont présents. Si votre `gitpr-cli` est obsolète, elle affiche une invite de mise à jour (`pip install --upgrade gitpr-cli`).
- **Zéro Configuration Parallèle** : Les clés API, les jetons SCM et les préférences restent dans `~/.gitpr/.env` chiffrés avec Fernet. L'extension ne demande ni ne stocke jamais de secrets.
- **Masquage des Secrets en Profondeur** : Le serveur MCP Python (`mask_sensitive_text`) et l'extension TypeScript (`maskSensitiveText`) masquent tous deux les jetons (`ghp_*`, `glpat-*`, `sk-*`, `AIza*`, `Bearer *`, clés privées) avant d'afficher des notifications ou d'écrire dans l'OutputChannel `GitPR`.

---

## Installation

### 1. Prérequis : `gitpr-cli`

Assurez-vous que `gitpr-cli` est installé et configuré sur votre machine :

```bash
pip install --upgrade gitpr-cli
gitpr --install
```

### 2. Installer l'Extension (VS Code & Cursor)

VS Code et Cursor partagent le même paquet VSIX (`natanfiuza.gitpr`) :

- **VS Code Marketplace** : Recherchez `GitPR` (`natanfiuza.gitpr`).
- **Cursor / Open VSX** : Recherchez `GitPR` ou installez depuis le fichier `.vsix`.
- **Depuis les Sources (VSIX Local)** :
  ```bash
  cd extensions/vscode
  npm install
  npm run compile
  npm run package
  code --install-extension gitpr-0.1.0.vsix
  ```

---

## Commandes et Flux de Travail

Toutes les commandes sont accessibles depuis la **Palette de Commandes** (`Ctrl+Shift+P` / `Cmd+Shift+P`), et les 4 actions principales (**Commit**, **Review**, **PR**, **Check**) sont épinglées dans la **Barre d'État**.

| Commande | Outil MCP Appelé | Comportement |
|---|---|---|
| `GitPR: Commit (Générer le Message)` | `generate_commit_message` | Génère un brouillon Conventional Commits et remplit le champ **Contrôle de code source** (avec copie dans le presse-papiers en secours). Ne valide jamais automatiquement. |
| `GitPR: Review (Modifications Locales)` | `review_code(mentor=false)` | Examine les modifications locales (`git diff HEAD`) et ouvre un aperçu Markdown côte à côte. |
| `GitPR: Full Review (Contre la Branche de Base)` | `full_review(mentor=false)` | Exécute `git fetch` et examine toute la branche contre `origin/main`, en ouvrant un aperçu Markdown. |
| `GitPR: Review (Mode Mentor Junior)` | `review_code(mentor=true)` | Ajoute des explications pédagogiques du Mode Mentor Junior à l'aperçu de revue de code. |
| `GitPR: Générer un Brouillon de PR` | `generate_pr_description(explain=false)` | Ouvre un document Markdown modifiable de brouillon de PR (`ligne 1` = titre, reste = corps). |
| `GitPR: Générer un Brouillon de PR (avec Guide du Relecteur)` | `generate_pr_description(explain=true)` | Génère le brouillon modifiable de PR incluant la section **Explain my PR** (Guide du Relecteur). |
| `GitPR: Publier la PR depuis le Brouillon Actif` | `publish_pull_request` | Lit le brouillon Markdown modifié actif, demande une confirmation modale (`Publier` ou `Publier comme Brouillon`) et crée la PR sur la forge configurée (GitHub, GitLab, Bitbucket, Azure DevOps). |
| `GitPR: Check (Diagnostics Unifiés Linter et Sécurité)` | `run_check` | Exécute le pipeline de vérification unifié et alimente le panneau **Problèmes** avec des diagnostics cliquables par fichier, ligne et sévérité. |

### Publication de Pull Request en Deux Étapes

La publication ne se fait jamais à l'aveugle :
1. Exécutez **`GitPR: Générer un Brouillon de PR`** (ou **`Générer un Brouillon de PR (avec Guide du Relecteur)`**).
2. Relisez et modifiez le document Markdown ouvert. La première ligne non vide sert de titre à la Pull Request et le reste constitue le corps.
3. Cliquez sur le bouton **`Publier la PR`** dans la barre de titre de l'éditeur (ou exécutez **`GitPR: Publier la PR depuis le Brouillon Actif`**).
4. Confirmez dans la boîte de dialogue modale. Le serveur renvoie des états structurés :
   - `needs_push` → propose le bouton **Pousser et Publier** via `vscode.git`.
   - `already_exists` → propose d'ouvrir la PR existante dans le navigateur.
   - `auth_required` → propose d'ouvrir un terminal exécutant `gitpr` pour s'authentifier.
   - `success` → propose d'ouvrir la PR nouvellement créée dans le navigateur.

---

## Paramètres de l'Extension

Configurez dans `settings.json` de VS Code / Cursor :

```json
{
  "gitpr.mcpCommand": "gitpr-mcp",
  "gitpr.mcpArgs": [],
  "gitpr.provider": "",
  "gitpr.check.useAI": false
}
```

| Paramètre | Type | Défaut | Description |
|---|---|---|---|
| `gitpr.mcpCommand` | `string` | `"gitpr-mcp"` | Exécutable utilisé pour lancer le serveur MCP GitPR. |
| `gitpr.mcpArgs` | `string[]` | `[]` | Arguments supplémentaires passés à l'exécutable du serveur MCP. |
| `gitpr.provider` | `string` | `""` | Fournisseur d'IA optionnel (`gemini`, `deepseek`, `ollama`). Vide hérite de `~/.gitpr/.env`. |
| `gitpr.check.useAI` | `boolean` | `false` | Active la revue IA dans `GitPR: Check`. Désactivé par défaut pour garder des vérifications rapides et sans jetons dans l'éditeur. |

---

## Internationalisation (i18n) et Télémétrie

- **Langues de l'Interface** : Empaquetée avec les traductions `en`, `pt-br`, `es` et `fr` (`package.nls.*.json` et `l10n/bundle.l10n.*.json`).
- **Télémétrie Locale Uniquement** : L'extension n'émet aucune télémétrie externe et n'ouvre aucune connexion réseau. Le serveur MCP local enregistre les événements `mcp:check` et `mcp:publish_pr` dans le registre SQLite local (`~/.gitpr/metrics/telemetry.db`).
