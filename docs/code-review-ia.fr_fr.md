# Documentation technique : Code Review avec l'IA (--review / --fullreview / --input)

GitPR CLI offre trois modes de code review utilisant l'intelligence artificielle, chacun adapté à un moment différent du cycle de développement. Tous les modes s'intègrent automatiquement avec le **Linter statique** (`.gitpr.linter.yml`), qui ajoute des alertes de regex en haut du rapport.

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

---

## 2. Intégration avec le Linter statique

Dans tous les modes de review, le **Linter statique** est exécuté automatiquement. S'il y a des violations des règles définies dans le `.gitpr.linter.yml`, les alertes apparaissent en haut du rapport, avant l'analyse de l'IA :

```
## 🚨 Alertas de Análise Estática Local (Regras YAML)
- 🚨 Uso de console.log detectado em app.js (Linha 42)
- ⚠️ Uso de localhost detectado em config.php (Linha 15)

---

## 🤖 Code Review da IA
...
```

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
gitpr -r -p deepseek        # Review local com DeepSeek
gitpr -f -p gemini          # Full review com Gemini
gitpr -r -i arquivo.py -p deepseek  # Auditoria com DeepSeek
```

---

## 5. Variables d'environnement

| Variable | Mode | Valeur par défaut |
| --- | --- | --- |
| `OUTPUT_FILE_NAME_REVIEW` | `-r` | `{branch}_{datetime}_PR_REVIEW.txt` |
| `OUTPUT_FILE_NAME_FULLREVIEW` | `-f` | `{branch}_{datetime}_PR_FULLREVIEW.txt` |
| `OUTPUT_FILE_NAME_FILEREVIEW` | `-i` | `{branch}_{datetime}_FILE_REVIEW.txt` |

> **Note :** Consultez également la [documentation du Linter](linter-regras-customizadas.md) pour créer des règles de validation statique.
