# 📂 Git Status — Liste des Fichiers Non Commit és et Vérification Unstaged

GitPR peut lister les modifications de fichiers non commités sans traitement IA, et vérifie automatiquement les fichiers hors stage avant d'exécuter toute commande IA (commit, review, full review, issue et PR).

---

## 1. Flag `--status` — Liste Rapide des Fichiers (Sans IA)

La flag `--status` liste toutes les modifications de fichiers non commités catégorisées par type — **sans IA, sans réseau, sans git fetch**. Exécution instantanée.

```bash
gitpr --status
```

Exemple de sortie :
```
📂 Uncommitted changes (no AI):
  ➕ New files (2):
    - src/new_module.py
    - tests/test_new_module.py
  ✏️ Modified files (3):
    - src/core.py
    - src/main.py
    - README.md
  🗑️ Deleted files (1):
    - old_deprecated.py
```

### Catégories

| Catégorie | Codes git status | Description |
|-----------|-----------------|-------------|
| **Nouveaux** (`➕`) | `??` | Fichiers non suivis — jamais ajoutés à Git |
| **Modifiés** (`✏️`) | ` M`, `MM`, `AM`, `RM` | Modifications non stagées dans l'arbre de travail |
| **Supprimés** (`🗑️`) | ` D`, `MD`, `AD`, `RD` | Suppressions non stagées dans l'arbre de travail |

> **Note :** Les fichiers stagés (ajoutés via `git add`) mais avec un arbre de travail propre (`M `, `A `, `D `) ne sont **pas** affichés. La flag `--status` montre uniquement les fichiers avec des **modifications dans l'arbre de travail non encore dans la zone de stage**.

---

## 2. Vérification des Fichiers Unstaged (Toutes les Commandes)

Avant de générer toute analyse IA, GitPR vérifie maintenant les fichiers hors stage sur **toutes** les commandes principales :

| Commande | Comportement quand des fichiers unstaged sont trouvés |
|---------|-------------------------------------------------------|
| `gitpr` (PR par défaut) | **Interactif** — ouvre une modale TUI pour stager, ignorer ou annuler |
| `gitpr -c` (commit) | **Avertissement** — alerte que les fichiers unstaged NE seront PAS dans le commit |
| `gitpr -r` (review) | **Informatif** — note que les fichiers unstaged sont toujours inclus dans le diff |
| `gitpr -f` (fullreview) | **Informatif** — note que les fichiers unstaged sont toujours inclus dans le diff |
| `gitpr -is` (issue, mode diff) | **Informatif** — note que les fichiers unstaged sont toujours inclus dans le diff |

### Comportement spécifique au commit

Lors de l'exécution de `gitpr -c`, l'avertissement est plus fort car les fichiers unstaged ne seront **pas** inclus dans le message de commit généré par l'IA.

Si `GITPR_AUTO_STAGE=true` est défini, `-c` fera un auto-stage des fichiers avant de générer le message de commit (même comportement que le PR).

### Comportement Review/FullReview/Issue

Pour `-r`, `-f` et `-is`, le diff inclut déjà les modifications unstaged, donc l'analyse est précise. Le message est uniquement informatif.

> **Note :** `GITPR_AUTO_STAGE` n'est **pas** appliqué pour review/fullreview/issue — faire un auto-stage comme effet secondaire d'une commande d'analyse en lecture seule serait inattendu.

---

## 3. Flag `--no-unstaged-check`

Ignore la vérification unstaged pour une seule exécution :

```bash
gitpr -c --no-unstaged-check
```

Équivalent à définir `GITPR_SKIP_UNSTAGED_CHECK=true` mais uniquement pour cette commande.

---

## 4. Protection en Mode Hook

Quand GitPR s'exécute dans un hook Git (flag `--hook`, utilisé par `prepare-commit-msg`), la vérification unstaged est **complètement ignorée** — tout prompt ou TUI bloquerait le processus de `git commit`.

---

## 5. Variables d'Environnement

| Variable | Défaut | Description |
|----------|--------|-------------|
| `GITPR_SKIP_UNSTAGED_CHECK` | `false` | Définir sur `true` pour ignorer la vérification des fichiers unstaged pour toutes les commandes |
| `GITPR_AUTO_STAGE` | `false` | Définir sur `true` pour stager automatiquement tous les fichiers unstaged (PR et commit uniquement) |

---

## 6. Outils MCP

Deux nouveaux outils MCP sont disponibles pour l'intégration IDE :

### `list_unstaged_files`
Retourne un JSON structuré avec trois listes catégorisées :
```json
{
  "status": "changes_found",
  "new": ["non_suivi.py"],
  "modified": ["modifié.py"],
  "deleted": ["supprimé.py"],
  "total": 3,
  "message": ""
}
```

### `analyze_unstaged_diff`
Retourne uniquement le diff **unstaged** (index vs arbre de travail), excluant les modifications stagées.

> **Note :** Les fichiers non suivis n'apparaissent jamais dans les diffs git. Utilisez `list_unstaged_files` pour les voir.

L'outil existant `analyze_diff` a été clarifié : il retourne le diff **non commité** (`git diff HEAD` — inclut à la fois les modifications stagées et non stagées, mais pas les fichiers non suivis).

---

## 7. Documentation Connexe

- [Pourquoi GitPR a-t-il ignoré mes nouveaux fichiers ?](untracked-files.fr_fr.md)
- [Publication de Pull Request](pull-request-publication.md)
- [Git Hooks Locaux](git-hooks-locais.md)
