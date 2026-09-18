# Documentation technique : Code Review avec l'IA (--review / --fullreview / --input)

GitPR CLI offre quatre modes de code review utilisant l'intelligence artificielle, chacun adapté à un moment différent du cycle de développement. Tous les modes s'intègrent automatiquement avec le **Linter statique** (`.gitpr.linter.yml`), qui ajoute des alertes de regex en haut du rapport.

---

## 1. Modes de Review

### 1.1 Review local — `gitpr -r` (ou `--review`)

Analyse uniquement les modifications **non committées** dans le working tree (`git diff HEAD`).

```bash
gitpr -r
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | `git diff HEAD` (modifications locales) |
| **Quand l'utiliser** | Avant de committer, pour valider la qualité du code |
| **Sortie** | `{branch}_{datetime}_PR_REVIEW.txt` |
| **Idéal pour** | Revue rapide, validation pré-commit |

### 1.2 Full Review — `gitpr -f` (ou `--fullreview`)

Compare **toutes** les modifications de la branche actuelle par rapport à la branche principale distante (`origin/main`).

```bash
gitpr -f
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Diff complet par rapport à `origin/main` (fait un `git fetch` avant) |
| **Quand l'utiliser** | Avant d'ouvrir une Pull Request |
| **Sortie** | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| **Idéal pour** | Revue approfondie de toute la branche de fonctionnalité |

### 1.3 Audit de fichier — `gitpr -r -i <arquivo>` (ou `--review --input`)

Analyse un **fichier entier**, en ignorant le git diff. Utile pour le code legacy ou les refactorisations.

```bash
gitpr -r -i src/legacy/parser.py
gitpr -f -i src/core.py
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Contenu intégral du fichier sur le disque |
| **Quand l'utiliser** | Refactorisation de code legacy, audit de fichiers critiques |
| **Sortie** | `{branch}_{datetime}_FILE_REVIEW.txt` |
| **Nécessite** | `--review` (`-r`) ou `--fullreview` (`-f`) |

### 1.4 Revue de pull request distante — `gitpr review-pr <number>`

Révise une pull request **déjà ouverte sur la forge**, en récupérant son diff directement depuis l'API. La branche n'a pas besoin d'être locale : rien n'est récupéré ni ramené dans votre arbre de travail. C'est le mode pour relire la pull request de quelqu'un d'autre.

```bash
gitpr review-pr 123
gitpr review-pr 123 --provider deepseek
gitpr review-pr 123 --post-comment
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Le diff servi par l'API de la forge pour cette pull request |
| **Quand l'utiliser** | Relire une pull request à laquelle vous avez été invité, sans faire de checkout de la branche |
| **Sortie** | `{branch}_{datetime}_PR_REVIEW.txt`, nommé d'après la branche source de la pull request |
| **Publication** | Rien, sauf si `--post-comment` est fourni ; la revue est alors publiée en commentaire |
| **Nécessite** | Une forge configurée par `gitpr --init` qui serve un diff unifié — Azure DevOps ne le fait pas |
| **Idéal pour** | La revue de code de contributions tierces, et pour les dépôts que vous ne clonez jamais |

Il exécute le même moteur, la même skill et le même cache que `gitpr -r` : son rapport se lit donc comme une revue locale du même diff. Voir la [documentation de la Revue de pull request distante](review-pr.md) pour le contrat complet — les refus qui ne coûtent aucun token, le filtre smart excludes, la portée de cache et le pied du commentaire.

---

## 2. Intégration avec le Linter statique

Dans tous les modes de review, le **Linter statique** est exécuté automatiquement. S'il y a des violations des règles définies dans le `.gitpr.linter.yml`, les alertes apparaissent en haut du rapport, avant l'analyse de l'IA :

```
## 🚨 Alertes d'analyse statique locale (Règles YAML)
- 🚨 Utilisation de console.log détectée dans app.js (Ligne 42)
- ⚠️ Utilisation de localhost détectée dans config.php (Ligne 15)

---

## 🤖 Code Review de l'IA
...
```


Dans une revue de pull request distant (`gitpr review-pr`), seules les règles YAML s'exécutent : le pont du linter externe lance des binaires contre des fichiers **sur le disque**, qui dans ce mode seraient ce que vous avez en checkout et non la pull request en revue. Revoir la mauvaise révision et publier les alertes en commentaire est pire que de ne pas les exécuter.

---

## 3. Personnalisation via Skills

Le comportement de l'IA pendant la review peut être personnalisé à travers les fichiers de template :

| Fichier | Mode | Fonction |
| --- | --- | --- |
| `.gitpr.review.md` | `--review` / `--fullreview` | Définit le focus de l'analyse (ex : SOLID, Clean Code, sécurité) |
| `.gitpr.filereview.md` | `--input` (+ review) | Définit les règles de cohésion et de couplage pour un fichier complet |

Téléchargez les templates avec `gitpr -s` et éditez-les selon les règles métier de votre équipe.

---

## 4. Sélection du fournisseur d'IA

```bash
gitpr -r -p deepseek        # Review local avec DeepSeek
gitpr -f -p gemini          # Full review avec Gemini
gitpr -r -i arquivo.py -p deepseek  # Audit avec DeepSeek
gitpr review-pr 123 --provider deepseek  # Revue distante avec DeepSeek
```

Le `-p` / `--provider` du groupe racine n'est pas hérité par les sous-commandes : `gitpr review-pr` écrit donc la même option `--provider`.

---

## 5. Variables d'environnement

| Variable | Mode | Valeur par défaut |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r`, `review-pr` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Note :** Consultez également la [documentation du Linter](linter-regras-customizadas.md) pour créer des règles de validation statique.
