# Documentation Technique : Génération de Pull Request (Mode par Défaut)

Lorsqu'il est exécuté **sans flags**, GitPR génère une description complète de Pull Request en Markdown avec l'IA — prête à être collée sur GitHub, GitLab ou Bitbucket — et ouvre un panneau interactif (TUI) pour consulter, modifier et publier la PR directement sur GitHub sans quitter le terminal.

---

## 1. Utilisation

```bash
gitpr
```

| Mode | Commande | Comportement |
|---|---|---|
| Interactif (par défaut) | `gitpr` | Génère la PR et ouvre la TUI pour la consulter et la publier |
| Enregistrer seulement | `gitpr --no-publish` | Génère la PR et enregistre le fichier `.md` localement |
| Publication directe | `gitpr --no-edit` | Génère la PR, effectue auto-commit, push et publie sans ouvrir la TUI |

---

## 2. Flux d'Exécution

```
vérification des fichiers unstaged → git fetch → diff par rapport à origin/main → IA → .md → TUI → publier
```

1. **Vérification des fichiers unstaged** — Détecte les fichiers non commités et propose de les stager (stage, ignorer ou annuler)
2. **`git fetch`** — Synchronise avec le dépôt distant
3. **Diff** — Compare toutes les modifications de la branche actuelle par rapport à `origin/main`
4. **IA** — Génère le message de commit (Conventional Commits) et la description de la PR
5. **Output** — Enregistre un fichier `.md` dans `.gitpr/reports/pr_desc/`
6. **Publier** — Ouvre la TUI (`F3` = publier) ou publie directement avec `--no-edit`

---

## 3. Output

Le fichier généré (`{branch}_{datetime}_PR_DESC.md`) est enregistré dans `.gitpr/reports/pr_desc/` et contient :

```markdown
# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
feat: short description of the change

---

## Description
...
## Changes
...
## Impact
...
```

---

## 4. Publication de la Pull Request

Le publicateur est disponible en 3 modes :

### 4.1 Mode Interactif (par Défaut)

Exécuter `gitpr` ouvre la TUI après la génération de la description. Raccourcis :

| Touche | Action |
|---|---|
| **`F1`** | Aide |
| **`F2`** | Enregistre le fichier `.md` localement |
| **`F3`** | Publie la PR (auto-commit → push → crée/met à jour la PR sur GitHub) |
| **`Esc`** | Quitte sans publier |

### 4.2 Enregistrer Seulement

```bash
gitpr --no-publish
```

Génère la description et enregistre le fichier `.md` sans ouvrir la TUI.

### 4.3 Publication Directe

```bash
gitpr --no-edit
```

Ignore la TUI : effectue l'auto-commit des modifications en attente (linter + message de commit par IA), pousse et publie directement. À utiliser avec prudence — le contenu n'est pas relu avant la publication.

Pour publier, GitPR nécessite un **Personal Access Token (PAT)** GitHub avec le scope `repo`, stocké chiffré dans `~/.gitpr/.env`. La branche cible est résolue via la flag `--base` → env `PR_DEFAULT_BASE` → détection automatique.

> **Remarque :** Consultez le [guide complet de publication](pull-request-publication.md) pour le flux détaillé (vérification des unstaged, auto-commit, merge, gestion des erreurs).

---

## 5. Personnalisation

### 5.1 Template de PR

Le comportement de l'IA peut être personnalisé via le fichier `.gitpr.pr.md` :

```bash
gitpr -s          # Downloads the template
# Edit .gitpr.pr.md with your team's required sections
gitpr             # The AI will follow your template
```

### 5.2 Nom du Fichier de Sortie

Configurez la variable d'environnement `OUTPUT_FILE_NAME` dans le fichier `~/.gitpr/.env` :

```ini
OUTPUT_FILE_NAME=PR_{branch}_{datetime}.md
```

Variables disponibles : `{branch}` (nom de la branche actuelle) et `{datetime}` (horodatage `YYYYMMDDHHMMSS`).

---

## 6. Sélection du Fournisseur d'IA

```bash
gitpr -p gemini       # Forces Google Gemini
gitpr -p deepseek     # Forces DeepSeek
```

Si aucun fournisseur n'est spécifié, GitPR utilise la valeur par défaut définie dans la variable `DEFAULT_AI_PROVIDER` de `~/.gitpr/.env`.

---

## 7. Cache des Réponses

GitPR génère un hash MD5 du diff + des instructions de l'IA. Si vous exécutez `gitpr` à nouveau **sans modifier le code**, la réponse est renvoyée depuis le cache local en quelques millisecondes, sans consommer de quota API.

> **Remarque :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités.
