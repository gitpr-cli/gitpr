# Assistant de Configuration Interactif GitPR (`--install`)

La commande `gitpr --install` exécute un assistant interactif guidé qui prépare l'environnement de votre projet avec toutes les configurations GitPR essentielles en un seul flux. Elle consolide plusieurs étapes de configuration manuelle en une expérience fluide.

## ✨ Ce Qu'il Fait

L'assistant vous guide à travers **4 étapes**, en demandant une confirmation avant chacune d'elles :

| Étape | Ce qu'elle configure | Commande équivalente |
|-------|---------------------|----------------------|
| 1. Skill Templates | Télécharge les fichiers template `.gitpr.*.md` et `.gitpr.linter.yml` | `gitpr --skill` |
| 2. Git Hooks | Installe les hooks `pre-commit` et `prepare-commit-msg` localement | `gitpr --installhooks` |
| 3. Configuration MCP | Détecte et configure automatiquement les éditeurs (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 4. Vérification de la Clé API | Vérifie ou demande la clé API de votre fournisseur d'IA | Assistant de premier lancement |

À la fin, un lien vers cette documentation est affiché pour référence.

## 🚀 Comment Utiliser

```bash
gitpr --install
```

L'assistant va :
1. Afficher un en-tête de bienvenue
2. Pour chaque étape : expliquer ce qu'elle fait → demander une confirmation (`[Y/n]`) → exécuter ou ignorer
3. Afficher les résultats et l'URL de la documentation une fois terminé

Chaque étape peut être **ignorée** en répondant `n` (non) lorsque vous y êtes invité. Les étapes ignorées peuvent être exécutées ultérieurement individuellement en utilisant leurs commandes équivalentes.

## 📋 Prérequis

- **Connexion internet :** Nécessaire pour télécharger les templates, les hooks et vérifier les mises à jour.
- **Dépôt Git :** La commande doit être exécutée dans un projet git (nécessaire pour les hooks et l'analyse de diff).
- **Environnement Python :** GitPR doit être installé et accessible dans votre PATH.

## 📖 Détails Étape par Étape

### Étape 1 — Skill Templates

Télécharge les fichiers template de contexte IA dans le dossier `.gitpr/skill/` de votre projet :

- `.gitpr.commit.md` — Règles pour la génération de messages de commit
- `.gitpr.pr.md` — Structure requise pour les descriptions de PR
- `.gitpr.review.md` — Axe architectural pour les revues de code
- `.gitpr.filereview.md` — Règles de cohésion et couplage pour les audits de fichiers
- `.gitpr.issue.md` — Structure pour la génération standardisée d'issues
- `.gitpr.blame.md` — Axe pour le traçage de code legacy
- `.gitpr.linter.yml` — Règles personnalisées d'analyse statique

Ces fichiers ne sont **jamais écrasés** s'ils existent déjà. Modifiez-les librement pour personnaliser le comportement de l'IA selon les conventions de votre équipe.

📚 Voir aussi : [Système de Skills et Templates](skill-template.md)

### Étape 2 — Git Hooks

Installe deux hooks Git locaux dans `.git/hooks/` :

- **`pre-commit`** — Exécute le linter statique (`.gitpr.linter.yml`) avant chaque commit, bloquant le code qui enfreint vos règles.
- **`prepare-commit-msg`** — Utilise l'IA pour générer un message au format Conventional Commits et l'injecte dans votre éditeur de commit.

Cela permet la pratique **Shift-Left** — détecter les problèmes sur la machine du développeur avant qu'ils n'atteignent le CI/CD ou la revue de code.

📚 Voir aussi : [Git Hooks Locaux](git-hooks-locais.md)

### Étape 3 — Configuration MCP

Détecte automatiquement quels éditeurs avec IA vous utilisez et crée les fichiers de configuration nécessaires :

| Éditeur | Fichier de configuration créé |
|---------|-------------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Une fois configuré, vous pouvez utiliser le langage naturel dans le chat IA de votre éditeur pour invoquer les outils GitPR : "Revise mes modifications", "Génère un message de commit", "Crée une description de PR", etc.

Les fichiers de configuration existants sont **fusionnés** — les autres serveurs MCP ne sont jamais écrasés.

📚 Voir aussi : [Intégration MCP](mcp-integration.md)

### Étape 4 — Configuration de la Clé API

Vérifie si la clé API de votre fournisseur d'IA est déjà configurée :

- **Si configurée :** Affiche un message de succès — vous êtes prêt à partir.
- **Si manquante :** Propose de la configurer interactivement. La clé est chiffrée avec Fernet (chiffrement symétrique) et stockée de manière sécurisée dans `~/.gitpr/.env`.

Vous pouvez ignorer cette étape et la configurer plus tard en exécutant `gitpr` (qui déclenche l'assistant de premier lancement) ou en modifiant `~/.gitpr/.env` directement.

📚 Voir aussi : [Fournisseurs d'IA](providers-ia.md)

## 🔄 Exécuter des Étapes Individuelles Plus Tard

Si vous avez ignoré une étape, vous pouvez toujours exécuter sa commande équivalente plus tard :

```bash
gitpr --skill              # Étape 1 : Télécharger les templates
gitpr --installhooks    # Étape 2 : Installer les Git hooks
gitpr-mcp --install auto   # Étape 3 : Configurer MCP
gitpr                      # Étape 4 : Clé API (assistant de premier lancement)
```

## ⚙️ Environnements CI/CD

Dans les pipelines CI/CD (détectés par les variables d'environnement `CI` ou `GITHUB_ACTIONS`), GitPR **ne** demandera **pas** de clés API de manière interactive. Configurez votre clé à l'avance en utilisant des variables d'environnement ou GitHub Secrets.

---
**Pro tip :** Exécutez `gitpr --install` sur chaque nouveau clone pour obtenir l'expérience GitPR complète configurée en quelques secondes.
