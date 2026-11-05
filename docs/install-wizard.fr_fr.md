# Assistant de Configuration Interactif de GitPR (`--install`)

La commande `gitpr --install` lance un assistant interactif guidé qui prépare l'environnement de votre projet avec toutes les configurations essentielles de GitPR en un seul flux. Il consolide plusieurs étapes de configuration manuelle en une expérience intégrée.

## ✨ Ce Qu'il Fait

L'assistant vous guide à travers **5 étapes**, en demandant confirmation avant chacune d'elles :

| Étape | Ce qu'il configure | Commande équivalente |
|-------|--------------------|----------------------|
| 1. Configuration Locale du Projet | Initialise `.gitpr/conf/` (`gitpr.config.yml`, `gitpr.smart-excludes.json`) | `gitpr seed` |
| 2. Modèles de Skill & Linter | Télécharge `.gitpr.*.md` et `.gitpr.linter.yml` dans `.gitpr/skill/` (avec option de linters externes) | `gitpr --skill` / `gitpr --linter-setup` |
| 3. Git Hooks | Installe les hooks `pre-commit` et `prepare-commit-msg` localement | `gitpr --installhooks` |
| 4. Configuration MCP | Détecte automatiquement et configure vos éditeurs (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 5. Vérification de la Clé API | Vérifie ou demande la clé API de votre fournisseur d'IA | Assistant de premier lancement |

À la fin, un lien vers cette documentation est affiché pour référence.

Le fichier de configuration du projet `.gitpr/conf/gitpr.config.yml` définit la branche que les pull requests de ce dépôt doivent cibler — `PR_DEFAULT_BASE` lorsqu'elle est définie, `main` sinon. Les fichiers existants ne sont jamais écrasés par défaut. Versionnez-le pour que toute l'équipe cible la même branche ([Publication de Pull Request](pull-request-publication.fr_fr.md#91-le-fichier-du-projet)).

## 🚀 Comment l'Utiliser

```bash
gitpr --install
```

L'assistant va :
1. Afficher un en-tête de bienvenue
2. Pour chaque étape : expliquer son rôle → demander confirmation (`[Y/n]`) → exécuter ou ignorer
3. Afficher les résultats et l'URL de documentation à la fin

Chaque étape peut être **ignorée** en répondant `n` (non). Les étapes ignorées peuvent être exécutées plus tard individuellement avec leurs commandes équivalentes.

## 📋 Prérequis

- **Connexion Internet :** Nécessaire pour télécharger les modèles, les hooks et vérifier les mises à jour.
- **Dépôt Git :** La commande doit être exécutée dans un projet git (requis pour les hooks et l'analyse de diff).
- **Environnement Python :** GitPR doit être installé et accessible dans votre PATH.

## 📖 Détails Étape par Étape

### Étape 1 — Configuration Locale du Projet

Initialise les fichiers de configuration locaux dans `.gitpr/conf/` :
- **`gitpr.config.yml`** — Configuration de la branche cible PR pour le dépôt.
- **`gitpr.smart-excludes.json`** — Règles spécifiques au projet pour exclure des fichiers et dossiers des diffs IA, fusionnées avec la liste globale à l'exécution.

### Étape 2 — Modèles de Skill & Linter

Télécharge les fichiers modèles de contexte IA dans le dossier `.gitpr/skill/` de votre projet :

- `.gitpr.commit.md` — Règles de génération des messages de commit
- `.gitpr.pr.md` — Structure requise pour les descriptions de PR
- `.gitpr.review.md` — Orientation architecturale pour les revues de code
- `.gitpr.filereview.md` — Règles de cohésion et couplage pour les audits de fichiers
- `.gitpr.issue.md` — Structure pour la génération standardisée d'issues
- `.gitpr.blame.md` — Orientation pour l'analyse de code historique
- `.gitpr.linter.yml` — Règles personnalisées d'analyse statique locale

Ces fichiers ne sont **jamais écrasés** s'ils existent déjà. Modifiez-les librement pour adapter le comportement de l'IA aux conventions de votre équipe.

Lors du téléchargement des modèles, l'assistant propose facultativement de configurer des ponts vers des linters externes (ESLint, PHPCS, Stylelint).

📚 Voir aussi : [Système de Skills et Modèles](skill-template.fr_fr.md)

### Étape 3 — Git Hooks

Installe deux Git hooks locaux dans `.git/hooks/` :

- **`pre-commit`** — Exécute le linter statique (`.gitpr.linter.yml`) avant chaque commit, bloquant le code non conforme.
- **`prepare-commit-msg`** — Utilise l'IA pour générer un message Conventional Commits et l'injecter dans votre éditeur.

Cela permet la pratique du **Shift-Left** — détecter les problèmes sur le poste du développeur avant qu'ils n'atteignent le CI/CD ou la revue de code.

📚 Voir aussi : [Git Hooks Locaux](git-hooks-locais.fr_fr.md)

### Étape 4 — Configuration MCP

Détecte automatiquement les éditeurs IA installés et crée les fichiers de configuration nécessaires :

| Éditeur | Fichier de configuration créé |
|---------|-------------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Une fois configuré, vous pouvez utiliser le langage naturel dans le chat IA de votre éditeur pour invoquer les outils GitPR.

Les fichiers existants sont **fusionnés** — les autres serveurs MCP ne sont jamais écrasés.

📚 Voir aussi : [Intégration MCP](mcp-integration.fr_fr.md)

### Étape 5 — Configuration de la Clé API

Vérifie si la clé API de votre fournisseur d'IA est déjà configurée :

- **Si configurée :** Affiche un message de succès — vous êtes prêt.
- **Si manquante :** Propose de la configurer de manière interactive. La clé est chiffrée avec Fernet (chiffrement symétrique) et enregistrée dans `~/.gitpr/.env`.

Vous pouvez ignorer cette étape et la configurer ultérieurement en exécutant `gitpr` ou en modifiant `~/.gitpr/.env` directement.

📚 Voir aussi : [Fournisseurs d'IA](providers-ia.fr_fr.md)

---

## ⚡ Initialisation Directe des Configurations (`gitpr seed`)

Pour initialiser directement les fichiers de configuration du projet sans passer par l'assistant interactif complet :

```bash
gitpr seed
```

Ou en utilisant l'option racine :
```bash
gitpr --seed
```

### Options :
- `--force` / `-f` : Écrase les fichiers de configuration existants avec les modèles par défaut.
- `--all` / `-a` : Télécharge également tous les 12 modèles d'instructions IA dans `.gitpr/skill/`.

## 🔄 Exécuter les Étapes Individuellement Plus Tard

Si vous avez ignoré une étape, vous pouvez toujours exécuter sa commande équivalente plus tard :

```bash
gitpr seed                 # Étape 1 : Configuration du projet
gitpr --skill              # Étape 2 : Télécharger les modèles
gitpr --linter-setup       # Étape 2 (optionnel) : Linters externes
gitpr --installhooks       # Étape 3 : Installer les Git hooks
gitpr-mcp --install auto   # Étape 4 : Configurer MCP
gitpr                      # Étape 5 : Clé API (premier lancement)
```

## ⚙️ Environnements CI/CD

Dans les pipelines CI/CD (détectés via `CI` ou `GITHUB_ACTIONS`), GitPR **ne demandera pas** de clé API de manière interactive. Définissez vos clés au préalable via des variables d'environnement ou GitHub Secrets.

---
**Conseil :** Exécutez `gitpr --install` ou `gitpr seed` sur chaque nouveau clone pour configurer le dépôt en quelques secondes.
