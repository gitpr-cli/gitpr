# Documentation technique : publication de PR sur GitHub

Cette documentation décrit le flux de publication de Pull Requests via l'interface interactive en terminal (TUI), qui vous permet de consulter, modifier et publier des Pull Requests directement sur GitHub sans quitter le terminal.

---

## 1. Qu'est-ce que le Publisher de PR ?

Lorsque vous exécutez la commande `gitpr` (comportement par défaut), GitPR génère la description de la PR avec l'IA, enregistre le fichier `.md` localement et ouvre un panneau interactif directement dans le terminal. Cela vous permet de consulter, modifier et publier la Pull Request générée par l'intelligence artificielle avant de l'envoyer au dépôt distant via l'API REST.

---

## 2. Flux d'exécution complet

```
gitpr
  ├─ Banner
  ├─ Unstaged files check (before PR generation)
  │   ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip
  │   ├─ No unstaged files → proceed
  │   ├─ GITPR_AUTO_STAGE=true → auto git add → proceed
  │   └─ Has unstaged files → StageFilesApp TUI
  │       ├─ Stage Selected → git add → proceed
  │       ├─ Skip → proceed (no staging)
  │       └─ Cancel → abort
  ├─ PR generation (AI) → .md file saved to .gitpr/reports/pr_desc/
  └─ TUI (default) or --no-publish / --no-edit
      └─ F3 Publish PR → auto-commit (no duplicate unstaged check)
          ├─ Commit → git push → PR check
          │   ├─ No existing PR → POST create PR
          │   └─ Existing PR found → PATCH update PR
          └─ Merge prompt (if GITPR_AUTO_MERGE is not set)
```

---

## 3. Modes d'exécution

Le Publisher de PR dispose de **3 modes d'exécution**, déclenchés par les options (ou leur absence).

### 3.1 Mode interactif (par défaut) — `gitpr`

Exécuter `gitpr` sans aucune option génère la description de la PR et ouvre la TUI pour consultation et modification avant publication.

```bash
gitpr
```

| Caractéristique | Description |
|---|---|
| **Flux** | Vérification des fichiers unstaged → `git fetch` → l'IA génère la PR → `.md` enregistré → la TUI s'ouvre → l'utilisateur modifie → POST vers GitHub |
| **Quand l'utiliser** | Flux de travail standard — contrôle total sur ce qui est publié |
| **Résultat** | Pull Request créée sur GitHub avec le contenu modifié |
| **Idéal pour** | Développement quotidien — consulter et ajuster le contenu de la PR avant publication |

> **Astuce :** Le fichier `.md` local est enregistré avant l'ouverture de la TUI et ré-enregistré avec toutes les modifications avant publication. Vous disposez toujours d'une sauvegarde.

---

### 3.2 Ignorer le Publisher — `gitpr --no-publish`

Génère la PR et l'enregistre localement sans ouvrir l'éditeur interactif.

```bash
gitpr --no-publish
```

| Caractéristique | Description |
|---|---|
| **Flux** | Vérification des fichiers unstaged → `git fetch` → l'IA génère la PR → `.md` enregistré → fin du processus |
| **Quand l'utiliser** | Lorsque vous n'avez besoin que du fichier de description de la PR pour la documentation ou une consultation ultérieure |
| **Résultat** | Fichier Markdown enregistré localement ; aucune TUI ne s'ouvre |
| **Idéal pour** | Documentation, consultation hors ligne, enregistrement de brouillons de PR pour plus tard |

---

### 3.3 Publication directe — `gitpr --no-edit`

Ignore l'éditeur interactif, fait le commit automatique (auto-commit) des modifications en attente avec validation du linter, pousse vers le dépôt distant et publie directement sur GitHub.

```bash
gitpr --no-edit
```

| Caractéristique | Description |
|---|---|
| **Flux** | Vérification des fichiers unstaged → `git fetch` → l'IA génère la PR → `.md` enregistré → auto-commit (linter + message de commit avec l'IA) → `git push` → POST direct vers GitHub |
| **Quand l'utiliser** | Lorsque vous faites confiance au résultat de l'IA et souhaitez publier immédiatement |
| **Résultat** | Pull Request créée sur GitHub sans ouvrir la TUI |
| **Idéal pour** | Pipelines CI/CD, corrections rapides, flux de travail automatisés |

> **Attention :** À utiliser avec précaution — vous n'aurez pas la possibilité de consulter ni de modifier le contenu avant publication.

---

## 4. Gestion des fichiers unstaged

Avant le début de la génération de la PR, GitPR vérifie la présence de fichiers unstaged et propose une interface modale pour les gérer. Cette vérification s'exécute tout au début de l'exécution de `gitpr`, avant tout appel à l'IA.

### 4.1 Flux de vérification au démarrage

```
gitpr starts
  ├─ GITPR_SKIP_UNSTAGED_CHECK=true → skip entire check, proceed
  ├─ No unstaged files detected → proceed
  ├─ GITPR_AUTO_STAGE=true → auto git add all → proceed
  └─ Unstaged files found → StageFilesApp TUI opens
      ├─ [Stage Selected] → git add <selected> → proceed
      ├─ [Skip] → proceed without staging
      └─ [Cancel] → abort (exit without generating PR)
```

### 4.2 Détection des fichiers

Les fichiers unstaged sont détectés via `git status --porcelain`, en recherchant :
- `??` — fichiers non suivis (untracked)
- ` M` — modifiés mais non stageés (modifications de l'arbre de travail)
- ` D` — supprimés mais non stageés

### 4.3 Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Définir à `true` pour ignorer complètement la vérification des fichiers unstaged au démarrage |
| `GITPR_AUTO_STAGE` | `false` | Définir à `true` pour faire le stage automatique de tous les fichiers unstaged sans afficher le modal de sélection |

---

## 5. Flux d'auto-commit (--no-edit et F3 de la TUI)

Lorsque vous utilisez `--no-edit` ou appuyez sur `F3` dans la TUI avec des modifications non commitées, GitPR exécute un flux de commit automatique :

```
1. Check for uncommitted changes (git diff HEAD --stat)
   └─ If clean → skip commit, proceed to publish

2. Run static linter (.gitpr.linter.yml rules)
   ├─ ✅ Pass → proceed
   ├─ ⚠️ Warnings → shown, proceed
   └─ 🚨 Errors:
        ├─ [Commit with --no-verify] → proceed
        └─ [Abort] → operation cancelled

3. Generate commit message via AI (Conventional Commits format)
   └─ Display message in editable field, request confirmation
   └─ Option to regenerate the message

4. Execute: git commit -m "<message>" [--no-verify]
   ├─ Success → proceed with git push + PR publication
   └─ "Nothing to commit" → treated as success, proceed to publish
```

> **Remarque — Signature de co-auteur :** le trailer `Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>` est injecté à des moments différents selon le flux :
>
> - **TUI (F3) :** l'écran modifiable `CommitMessageScreen` affiche le message pur de l'IA ; le trailer n'est injecté qu'à l'exécution du commit (étape 4).
> - **`--no-edit` (console) :** le trailer est ajouté à la génération et reste visible dans l'aperçu avant la confirmation.

### 5.1 Gestion du cas « Nothing to Commit »

Lorsque `git commit` renvoie un code de sortie non nul mais que la sortie indique qu'aucun changement réel n'existe, le flux traite cela comme un succès et continue. Les motifs suivants sont reconnus :

- `nothing to commit`
- `nothing added to commit`
- `no changes added to commit`
- `changes not staged`
- `working tree clean`
- `no changes`

### 5.2 Organigramme de décision du linter

```
Has uncommitted changes?
├─ No → Skip commit, publish PR
└─ Yes
   └─ GITPR_SKIP_LINT=true?
      ├─ Yes → Skip to AI commit message
      └─ No
         └─ Run linter
            ├─ No errors → Skip to AI commit message
            └─ Has errors
               └─ User confirms --no-verify?
                  ├─ Yes → Skip to AI commit message (with --no-verify)
                  └─ No → Abort
```

### 5.3 Fenêtres de dialogue de commit dans la TUI

Le flux d'auto-commit dans la TUI utilise une série d'écrans modaux :

| Écran | Rôle |
|---|---|
| `CommitConfirmScreen` | Confirmation avant le lancement du flux de commit. Libellés de boutons personnalisables selon le contexte |
| `StageFilesScreen` | Liste de fichiers à cases à cocher pour sélectionner les fichiers à ajouter au stage avant le commit |
| `CommitProgressScreen` | Modal `RichLog` de type terminal qui isole les journaux de commit de la TUI principale |
| `CommitMessageScreen` | Message de commit modifiable avec un bouton « Regenerate » pour la régénération du message par l'IA |
| `LinterErrorScreen` | Affiche les erreurs du linter avec les options de faire le commit avec `--no-verify` ou d'annuler |
| `ErrorScreen` | Affichage générique des erreurs avec `max-height: 80%` et défilement pour les sorties d'erreur volumineuses |

---

## 6. Git push et gestion des PR existantes

Après un commit réussi, GitPR pousse la branche et vérifie la présence de PR existantes.

### 6.1 Flux de push

```
git push origin <branch>
  ├─ Success → check for existing PRs
  └─ Failure with "upstream" / "no upstream" in error
      └─ Auto-retry: git push --set-upstream origin <branch>
```

### 6.2 Détection des PR existantes

Avant de créer une nouvelle PR, GitPR vérifie si une PR existe déjà pour la branche courante :

```
Check existing PRs (GET /repos/{owner}/{repo}/pulls?head={branch})
  ├─ No existing PR → POST create new PR
  └─ Existing PR found
      ├─ User chooses "Push to existing PR" → PATCH update PR body
      └─ User chooses "Create new PR" → POST create new PR
```

### 6.3 Mise à jour de la PR

Lors de la publication vers une PR existante, GitPR met à jour uniquement le corps (la description) de la PR via `PATCH /repos/{owner}/{repo}/pulls/{number}`. Le titre de la PR reste inchangé. Le contenu envoyé est uniquement le champ PR Body de la TUI — aucun en-tête ni préfixe de message de commit n'est ajouté.

---

## 7. Flux de fusion (merge)

Après la création ou la mise à jour d'une PR, GitPR peut éventuellement la fusionner.

```
PR created/updated successfully
  ├─ GITPR_AUTO_MERGE=true → auto-merge via PUT /repos/{owner}/{repo}/pulls/{number}/merge
  ├─ GITPR_AUTO_MERGE=false → prompt user to merge
  └─ User declines → exit with PR URL displayed
```

| Variable | Défaut | Description |
|---|---|---|
| `GITPR_AUTO_MERGE` | `false` | Définir à `true` pour fusionner automatiquement les PR après leur création/mise à jour sans demander confirmation |

---

## 8. Structure du répertoire de sortie

Par défaut, GitPR enregistre tous les fichiers de sortie dans le répertoire `.gitpr/reports/`, organisé par type d'artefact :

| Variable d'env | Sous-dossier dans `.gitpr/reports/` |
|---|---|
| `OUTPUT_FILE_NAME` | `pr_desc` |
| `OUTPUT_FILE_NAME_REVIEW` | `review` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `full_review` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `file_review` |
| `OUTPUT_FILE_NAME_BLAME` | `blame` |
| `OUTPUT_FILE_NAME_ISSUE` | `issue` |

### 8.1 Règles de résolution des chemins

La fonction `resolve_output_path()` dans `src/core.py` gère trois scénarios :

1. **La variable d'environnement contient un séparateur de répertoire** (`/` ou `\`) → utilisée telle quelle (chemin personnalisé)
2. **La variable d'environnement ne contient qu'un nom de fichier** → enregistré dans `.gitpr/reports/{folder}/`
3. **La variable d'environnement est vide/par défaut** → utilise le modèle par défaut dans `.gitpr/reports/{folder}/`

Les répertoires sont créés automatiquement via `os.makedirs(exist_ok=True)`. Cela garantit une rétrocompatibilité totale — les utilisateurs ayant des chemins de répertoire personnalisés dans leur `.env` conservent leur comportement actuel.

---

## 9. Configuration de la branche de base

La branche cible de la Pull Request est déterminée dans l'ordre de priorité suivant :

| Priorité | Source | Comment configurer |
|---|---|---|
| **1 (la plus élevée)** | option `--base` | `gitpr --base develop` |
| **2** | variable d'environnement `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` dans `~/.gitpr/.env` |
| **3 (par défaut)** | Détection automatique | `git symbolic-ref refs/remotes/origin/HEAD` (généralement `main` ou `master`) |

---

## 10. Raccourcis et navigation de la TUI

L'interface a été conçue pour être rapide et ne pas nécessiter une utilisation constante de la souris. Vous pouvez naviguer entre les champs avec la touche `Tab` et utiliser les raccourcis suivants :

| Touche | Action | Description |
|---|---|---|
| **`F1`** | Aide | Ouvre un modal flottant avec des instructions rapides d'utilisation de l'interface |
| **`F2`** | Enregistrer `.md` local | Enregistre le contenu mis à jour dans le fichier de description de la PR du projet actuel. Idéal lorsque vous souhaitez affiner le contenu plus tard |
| **`F3`** | Publier la PR | Exécute l'auto-commit (linter + message IA + stage des fichiers si nécessaire) s'il y a des modifications en attente, puis crée ou met à jour la Pull Request sur GitHub via l'API. Le lien direct vers la PR sera affiché dans le terminal |
| **`Esc`** | Quitter | Annule l'opération et ferme l'interface sans publier |
| **`Tab`** | Naviguer | Alterne le focus entre les champs de l'interface |

---

## 11. Intégration GitHub (token PAT)

Pour créer des Pull Requests directement dans le dépôt distant (`F3`), GitPR a besoin d'un **Personal Access Token (PAT)** GitHub avec le scope `repo`.

### 11.1 Configuration du token

La première fois que vous utilisez `F3` ou `--no-edit`, GitPR :

1. Détecte qu'aucun token n'est configuré
2. Affiche l'URL de génération du token avec les paramètres pré-remplis (scope `repo`)
3. Vous demande de coller le token généré
4. Le stocke chiffré (Fernet) dans le fichier `~/.gitpr/.env`

> **Remarque :** La TUI Issues (`gitpr -is`) partage le même token. Si vous avez déjà configuré un token pour Issues, il sera réutilisé automatiquement.

### 11.2 Sécurité

- Le token est stocké sous forme de hash chiffré — jamais en clair
- La clé maîtresse de déchiffrement se trouve dans `~/.gitpr/secret.key`
- Le token est validé via `GET /user` avant l'ouverture de la TUI
- Consultez le guide complet dans [github-pat-integration.md](github-pat-integration.md)

---

## 12. Référence de l'API GitHub

### 12.1 Création de la PR

`POST https://api.github.com/repos/{owner}/{repo}/pulls`

```json
{
  "title": "PR title (editable in TUI)",
  "body": "PR body content from the TUI text area",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

> **Remarque :** Seul le contenu du champ PR Body est envoyé comme `body` — aucun en-tête ni préfixe de message de commit n'est inclus.

### 12.2 Mise à jour de la PR (PR existante)

`PATCH https://api.github.com/repos/{owner}/{repo}/pulls/{number}`

```json
{
  "body": "Updated PR body content from the TUI text area"
}
```

### 12.3 Fusion de la PR

`PUT https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge`

```json
{
  "merge_method": "merge"
}
```

---

## 13. Gestion des erreurs

| Erreur | Comportement |
|---|---|
| Token invalide/expiré (401) | Demande un nouveau token (jusqu'à 3 tentatives) |
| Branche introuvable (422) | Affiche le message d'erreur de GitHub avec les détails |
| Aucun commit à fusionner (422) | Affiche une erreur de validation suggérant d'apporter d'abord des modifications |
| La PR existe déjà (422) | Affiche le conflit spécifique ; dans la TUI, propose l'option de publier vers la PR existante |
| Erreurs du linter | Demande à l'utilisateur : faire le commit avec `--no-verify` ou annuler |
| Échec du commit (« nothing to commit ») | Traité comme un succès — le flux continue vers la publication |
| Échec du commit (autre) | Affiche l'erreur et permet de réessayer ou d'annuler |
| Échec du push (pas d'upstream) | Nouvelle tentative automatique avec `--set-upstream origin <branch>` |
| Échec du push (autre) | Affiche le message d'erreur avec les détails |
| Échec réseau | Affiche le message d'erreur de connexion |
| Remote manquant | Erreur avant l'ouverture de la TUI — aucun appel API n'est tenté |

---

## 14. Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(aucun)* | Token d'accès personnel GitHub chiffré |
| `PR_DEFAULT_BASE` | *(vide)* | Branche cible par défaut (utilise la détection automatique lorsqu'elle est vide) |
| `GITPR_AUTO_COMMIT` | `false` | Définissez sur `true` pour exécuter les commits sans demander de confirmation |
| `GITPR_SKIP_LINT` | `false` | Définissez sur `true` pour ignorer la validation du linter pendant l'auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Définir à `true` pour faire le stage automatique de tous les fichiers unstaged sans afficher le modal de sélection |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Définir à `true` pour ignorer complètement la vérification des fichiers unstaged au démarrage |
| `GITPR_SHOW_LOGS` | `true` | Définir à `false` pour masquer les journaux de progression du commit/push dans la TUI |
| `GITPR_AUTO_MERGE` | `false` | Définir à `true` pour fusionner automatiquement les PR après leur création/mise à jour sans demander confirmation |
| `OUTPUT_FILE_NAME` | `{branch}_{datetime}_PR_DESC.md` | Modèle de nom de fichier par défaut pour les descriptions de PR |
| `OUTPUT_FILE_NAME_REVIEW` | `{branch}_{datetime}_PR_REVIEW.txt` | Modèle de nom de fichier par défaut pour les revues de code |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `{branch}_{datetime}_PR_FULLREVIEW.txt` | Modèle de nom de fichier par défaut pour les revues complètes |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `{branch}_{datetime}_FILE_REVIEW.txt` | Modèle de nom de fichier par défaut pour les revues de fichiers |
| `OUTPUT_FILE_NAME_BLAME` | `{branch}_{datetime}_BLAME_REPORT.md` | Modèle de nom de fichier par défaut pour les rapports de blame |
| `OUTPUT_FILE_NAME_ISSUE` | `{branch}_{datetime}_ISSUE.md` | Modèle de nom de fichier par défaut pour les issues |

---

## 15. Exemples pratiques

### Exemple 1 : Flux de travail standard — consulter et publier

```bash
# You finished developing on the feature/login branch
gitpr
# → Unstaged files check (if any)
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Exemple 2 : Publication rapide sans modification

```bash
gitpr --no-edit
# → Unstaged files check (if any)
# → AI generates PR, auto-commits changes, pushes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Exemple 3 : Enregistrer uniquement le fichier de la PR localement

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file to .gitpr/reports/pr_desc/, exits
# → No TUI, no publication
```

### Exemple 4 : Publier vers une branche de base personnalisée

```bash
gitpr --base staging
# → Target branch is set to "staging" instead of "main"
```

### Exemple 5 : Ignorer le linter dans l'auto-commit

```bash
GITPR_SKIP_LINT=true gitpr --no-edit
# → Auto-commit skips lint, generates message, commits, pushes, and publishes
```

### Exemple 6 : Auto-commit sans confirmation

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

### Exemple 7 : Ignorer la vérification des fichiers unstaged

```bash
GITPR_SKIP_UNSTAGED_CHECK=true gitpr --no-edit
# → Skips the startup unstaged files modal entirely
```

### Exemple 8 : Auto-stage et auto-merge

```bash
GITPR_AUTO_STAGE=true GITPR_AUTO_MERGE=true gitpr --no-edit
# → All unstaged files are automatically staged
# → PR is automatically merged after creation
```

### Exemple 9 : Répertoire de sortie personnalisé

```bash
# In ~/.gitpr/.env:
OUTPUT_FILE_NAME=/home/user/prs/my_custom_pr.md
# → PR description saved to /home/user/prs/my_custom_pr.md
# → Directory paths in env vars are used as-is, never redirected to .gitpr/reports/
```

---

## 16. Fichiers associés

| Fichier | Fonction |
|---|---|
| `.gitpr.pr.md` | Template local avec des règles personnalisées pour la génération de la description de la PR (téléchargez-le avec `gitpr -s`) |
| `~/.gitpr/.env` | Configuration globale : clés API, paramètres par défaut de la PR et token GitHub chiffré |
| `~/.gitpr/secret.key` | Clé maîtresse Fernet pour le déchiffrement des identifiants |
| `.gitpr/reports/pr_desc/` | Répertoire de sortie par défaut pour les fichiers de description de PR |
| `.gitpr/reports/review/` | Répertoire de sortie par défaut pour les fichiers de revue de code |
| `.gitpr/reports/full_review/` | Répertoire de sortie par défaut pour les fichiers de revue complète |

> **Remarque :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités de GitPR et le [guide de description de PR](pr-descricao-padrao.md) pour le flux par défaut de génération de la PR.
