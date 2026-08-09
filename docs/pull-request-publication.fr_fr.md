# Documentation technique : publication de PR sur GitHub

Cette documentation décrit le flux de publication de Pull Requests via l'interface interactive en terminal (TUI), qui vous permet de consulter, modifier et publier des Pull Requests directement sur GitHub sans quitter le terminal.

---

## 1. Qu'est-ce que le Publisher de PR ?

Lorsque vous exécutez la commande `gitpr` (comportement par défaut), GitPR génère la description de la PR avec l'IA, enregistre le fichier `.md` localement et ouvre un panneau interactif directement dans le terminal. Cela vous permet de consulter, modifier et publier la Pull Request générée par l'intelligence artificielle avant de l'envoyer au dépôt distant via l'API REST.

---

## 2. Modes d'exécution

Le Publisher de PR dispose de **3 modes d'exécution**, déclenchés par les options (ou leur absence).

### 2.1 Mode interactif (par défaut) — `gitpr`

Exécuter `gitpr` sans aucune option génère la description de la PR et ouvre la TUI pour consultation et modification avant publication.

```bash
gitpr
```

| Caractéristique | Description |
|---|---|
| **Flux** | `git fetch` → l'IA génère la PR → `.md` enregistré → la TUI s'ouvre → l'utilisateur modifie → POST vers GitHub |
| **Quand l'utiliser** | Flux de travail standard — contrôle total sur ce qui est publié |
| **Résultat** | Pull Request créée sur GitHub avec le contenu modifié |
| **Idéal pour** | Développement quotidien — consulter et ajuster le contenu de la PR avant publication |

> **Astuce :** Le fichier `.md` local est enregistré avant l'ouverture de la TUI et ré-enregistré avec toutes les modifications avant publication. Vous disposez toujours d'une sauvegarde.

---

### 2.2 Ignorer le Publisher — `gitpr --no-publish`

Génère la PR et l'enregistre localement sans ouvrir l'éditeur interactif.

```bash
gitpr --no-publish
```

| Caractéristique | Description |
|---|---|
| **Flux** | `git fetch` → l'IA génère la PR → `.md` enregistré → fin du processus |
| **Quand l'utiliser** | Lorsque vous n'avez besoin que du fichier de description de la PR pour la documentation ou une consultation ultérieure |
| **Résultat** | Fichier Markdown enregistré localement ; aucune TUI ne s'ouvre |
| **Idéal pour** | Documentation, consultation hors ligne, enregistrement de brouillons de PR pour plus tard |

---

### 2.3 Publication directe — `gitpr --no-edit`

Ignore l'éditeur interactif, fait le commit automatique (auto-commit) des modifications en attente avec validation du linter, puis publie directement sur GitHub.

```bash
gitpr --no-edit
```

| Caractéristique | Description |
|---|---|
| **Flux** | `git fetch` → l'IA génère la PR → `.md` enregistré → auto-commit (linter + message de commit avec l'IA) → POST direct vers GitHub |
| **Quand l'utiliser** | Lorsque vous faites confiance au résultat de l'IA et souhaitez publier immédiatement |
| **Résultat** | Pull Request créée sur GitHub sans ouvrir la TUI |
| **Idéal pour** | Pipelines CI/CD, corrections rapides, flux de travail automatisés |

> **Attention :** À utiliser avec précaution — vous n'aurez pas la possibilité de consulter ni de modifier le contenu avant publication.

---

## 3. Flux d'auto-commit (--no-edit et F3 de la TUI)

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
   └─ Display message, request confirmation
   
4. Execute: git commit -m "<message>" [--no-verify]
   └─ Proceed with PR publication
```

### Organigramme de décision du linter

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

---

## 4. Configuration de la branche de base

La branche cible de la Pull Request est déterminée dans l'ordre de priorité suivant :

| Priorité | Source | Comment configurer |
|---|---|---|
| **1 (la plus élevée)** | option `--base` | `gitpr --base develop` |
| **2** | variable d'environnement `PR_DEFAULT_BASE` | `PR_DEFAULT_BASE=develop` dans `~/.gitpr/.env` |
| **3 (par défaut)** | Détection automatique | `git symbolic-ref refs/remotes/origin/HEAD` (généralement `main` ou `master`) |

---

## 5. Raccourcis et navigation de la TUI

L'interface a été conçue pour être rapide et ne pas nécessiter une utilisation constante de la souris. Vous pouvez naviguer entre les champs avec la touche `Tab` et utiliser les raccourcis suivants :

| Touche | Action | Description |
|---|---|---|
| **`F1`** | Aide | Ouvre un modal flottant avec des instructions rapides d'utilisation de l'interface |
| **`F2`** | Enregistrer `.md` local | Enregistre le contenu mis à jour dans le fichier de description de la PR du projet actuel. Idéal lorsque vous souhaitez affiner le contenu plus tard |
| **`F3`** | Publier la PR | Exécute l'auto-commit (linter + message IA) s'il y a des modifications en attente, puis crée la Pull Request sur GitHub via l'API. Le lien direct vers la PR nouvellement créée sera affiché dans le terminal |
| **`Esc`** | Quitter | Annule l'opération et ferme l'interface sans publier |
| **`Tab`** | Naviguer | Alterne le focus entre les champs de l'interface |

---

## 6. Intégration GitHub (token PAT)

Pour créer des Pull Requests directement dans le dépôt distant (`F3`), GitPR a besoin d'un **Personal Access Token (PAT)** GitHub avec le scope `repo`.

### 6.1 Configuration du token

La première fois que vous utilisez `F3` ou `--no-edit`, GitPR :

1. Détecter qu'aucun token n'est configuré
2. Afficher l'URL de génération du token avec les paramètres pré-remplis (scope `repo`)
3. Vous demander de coller le token généré
4. Le stocker chiffré (Fernet) dans le fichier `~/.gitpr/.env`

> **Remarque :** La TUI Issues (`gitpr -is`) partage le même token. Si vous avez déjà configuré un token pour Issues, il sera réutilisé automatiquement.

### 6.2 Sécurité

- Le token est stocké sous forme de hash chiffré — jamais en clair
- La clé maîtresse de déchiffrement se trouve dans `~/.gitpr/secret.key`
- Le token est validé via `GET /user` avant l'ouverture de la TUI
- Consultez le guide complet dans [github-pat-integration.md](github-pat-integration.md)

---

## 7. API GitHub — création de la PR

La PR est créée via `POST https://api.github.com/repos/{owner}/{repo}/pulls` avec le payload suivant :

```json
{
  "title": "PR title (editable in TUI)",
  "body": "Full markdown PR description with commit message",
  "head": "Current branch (source)",
  "base": "Target branch (main, develop, etc.)"
}
```

---

## 8. Gestion des erreurs

| Erreur | Comportement |
|---|---|
| Token invalide/expiré (401) | Demande un nouveau token (jusqu'à 3 tentatives) |
| Branche introuvable (422) | Affiche le message d'erreur de GitHub avec les détails |
| Aucun commit à fusionner (422) | Affiche une erreur de validation suggérant d'apporter d'abord des modifications |
| La PR existe déjà (422) | Affiche le conflit spécifique |
| Erreurs du linter | Demande à l'utilisateur : faire le commit avec `--no-verify` ou annuler |
| Échec du commit | Affiche l'erreur et permet de réessayer ou d'annuler |
| Échec réseau | Affiche le message d'erreur de connexion |
| Remote manquant | Erreur avant l'ouverture de la TUI — aucun appel API n'est tenté |

---

## 9. Variables d'environnement

| Variable | Défaut | Description |
|---|---|---|
| `GITHUB_TOKEN_ENCRYPTED` | *(aucun)* | Token d'accès personnel GitHub chiffré |
| `PR_DEFAULT_BASE` | *(vide)* | Branche cible par défaut (utilise la détection automatique lorsqu'elle est vide) |
| `GITPR_AUTO_COMMIT` | `false` | Définissez sur `true` pour exécuter les commits sans demander de confirmation |
| `GITPR_SKIP_LINT` | `false` | Définissez sur `true` pour ignorer la validation du linter pendant l'auto-commit |
| `GITPR_AUTO_STAGE` | `false` | Définir à `true` pour faire le stage automatique de tous les fichiers unstaged sans afficher le modal de sélection |
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Définir à `true` pour ignorer complètement la vérification des fichiers unstaged au démarrage |

---

## 10. Exemples pratiques

### Exemple 1 : Flux de travail standard — consulter et publier

```bash
# You finished developing on the feature/login branch
gitpr
# → AI generates the PR description and opens the TUI
# → Review the title, body, and base branch
# → Press F3 to auto-commit and create the PR on GitHub
```

### Exemple 2 : Publication rapide sans modification

```bash
gitpr --no-edit
# → AI generates PR, auto-commits changes, and publishes immediately
# → The PR URL is displayed in the terminal
```

### Exemple 3 : Enregistrer uniquement le fichier de la PR localement

```bash
gitpr --no-publish
# → AI generates PR description, saves .md file, exits
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
# → Auto-commit skips lint, generates message, commits, and publishes
```

### Exemple 6 : Auto-commit sans confirmation

```bash
GITPR_AUTO_COMMIT=true gitpr --no-edit
# → Commit message is generated and executed without asking for confirmation
```

---

## 11. Fichiers associés

| Fichier | Fonction |
|---|---|
| `.gitpr.pr.md` | Template local avec des règles personnalisées pour la génération de la description de la PR (téléchargez-le avec `gitpr -s`) |
| `~/.gitpr/.env` | Configuration globale : clés API, paramètres par défaut de la PR et token GitHub chiffré |
| `~/.gitpr/secret.key` | Clé maîtresse Fernet pour le déchiffrement des identifiants |

> **Remarque :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités de GitPR et le [guide de description de PR](pr-descricao-padrao.md) pour le flux par défaut de génération de la PR.
