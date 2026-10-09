# Documentation technique : Évaluation locale des risques (gitpr risk)

`gitpr risk` calcule un score de risque local, déterministe et explicable pour chaque fichier modifié ainsi que pour l'ensemble de la Pull Request ou du diff. Il exploite les signaux du dépôt et de Git (chemins critiques, absence de tests, migrations de base de données, historique de bugs et de réversions, volume du diff et constats statiques) afin d'orienter l'attention des réviseurs humains et de guider la revue par IA, sans nécessiter d'accès réseau, sans consommer de jetons d'IA et sans bloquer le flux de travail.

---

## 1. Vue d'ensemble

L'évaluation locale des risques s'articule autour de trois points de contact :

1. **CLI autonome (`gitpr risk`)** : Évalue le répertoire de travail ou le diff de branche par rapport à une référence de base et affiche une ventilation détaillée des niveaux de risque, des scores et des facteurs contributifs.
2. **Inspection ciblée par fichier (`gitpr risk --file <chemin>`)** : Isole le calcul de risque pour un fichier spécifique, en détaillant ses signaux individuels et sa corrélation avec les tests.
3. **Contexte additif pour la revue de code (`gitpr -r` / `gitpr -f` / `gitpr --review-pr`)** : Lorsqu'activé (`GITPR_RISK_INCLUDE_IN_REVIEW=true`), ajoute automatiquement une section `## ⚡ Évaluation des risques` aux fichiers de revue de code générés et injecte un résumé structuré dans le prompt IA pour concentrer l'analyse sur les fichiers critiques.

### 1.1 Référence des commandes

```bash
gitpr risk                        # Calcule le score de risque pour le diff courant non commité (ou le diff de branche)
gitpr risk --file src/auth.py     # Décompose les facteurs de risque pour un fichier spécifique
gitpr risk --format json          # Produit un JSON structuré pour l'intégration CI/CD et l'automatisation
gitpr risk --base main            # Évalue le risque par rapport à une référence git explicite
gitpr risk --no-history           # Désactive l'extraction de l'historique git log pour un calcul local plus rapide
```

| Option | Description |
|---|---|
| **`--file <chemin>`** | Calcule les facteurs de risque détaillés pour un fichier spécifique |
| **`--format {text\|json}`** | Sélectionne la sortie terminal lisible (par défaut) ou du JSON structuré |
| **`--base <ref>`** | Calcule le diff par rapport à une branche ou un commit git explicite |
| **`--no-history`** | Ignore la lecture de l'historique des commits pour optimiser la vitesse d'exécution |

---

## 2. Modèle de notation et formule d'agrégation

Tous les scores sont strictement normalisés dans l'intervalle **`0.0 – 100.0`**.

### 2.1 Niveaux de risque et seuils

| Niveau de risque | Plage de score | Badge | Signification |
|---|---|---|---|
| **LOW** | 0.0 – 24.0 | `LOW 🟢` | Modifications de routine avec faible probabilité de régression |
| **MEDIUM** | 25.0 – 49.0 | `MEDIUM 🟡` | Changements modérés nécessitant une vigilance normale en revue |
| **HIGH** | 50.0 – 79.0 | `HIGH 🟠` | Modifications importantes touchant des zones critiques ou manquant de tests |
| **CRITICAL** | 80.0 – 100.0 | `CRITICAL 🔴` | Risque élevé de régression, bloqueurs ou impacts architecturaux sensibles |

### 2.2 Table des poids des signaux

| Signal | Points par défaut | Condition / Motif |
|---|---:|---|
| **`CRITICAL_PATH`** | +25 | Authentification, autorisation, permissions, paiements, politiques, facturation |
| **`SECURITY_SENSITIVE`** | +25 | Configurations de sécurité, cryptographie, sessions, gestion des jetons |
| **`DATABASE_MIGRATION`** | +20 | Modifications de schéma, migrations de base de données, SQL structurel |
| **`INFRASTRUCTURE`** | +20 | Workflows CI/CD, Dockerfiles, Terraform, configurations Kubernetes |
| **`NO_TEST_CHANGE`** | +15 | Code de production modifié sans modification correspondante de tests dans le diff |
| **`LARGE_DIFF`** | +5 à +15 | Volume de diff : >= 50 lignes (+5), >= 100 lignes (+10), >= 300 lignes (+15) |
| **`HISTORICAL_BUGS`** | +10 à +20 | Fichier associé à des commits de correction de bugs récents (90 jours / 50 commits) |
| **`HISTORICAL_REVERTS`** | +10 | Fichier touché par des commits de réversion ou rollback |
| **`HIGH_CHURN`** | +15 | Fichier avec fréquence de commit élevée (>= 20 commits dans la fenêtre) |
| **`FINDING_BLOCKER`** | +25 | Constat de sécurité bloquant signalé par le linter local ou le scanner de secrets |
| **`FINDING_CRITICAL`** | +15 | Constat d'erreur critique signalé par le linter statique |
| **`FINDING_WARNING`** | +3 | Avertissement non bloquant signalé par le linter statique |
| **`TEST_PRESENT`** | -10 | Signal atténuant : fichier de test correspondant modifié ou ajouté aux côtés du code |
| **`NEW_FILE`** | 0 | Informatif : fichier nouvellement créé sans historique de commit antérieur |

### 2.3 Formule d'agrégation (50 / 30 / 20)

Le score agrégé de la pull request combine les scores individuels des fichiers :
- **50%** : Score maximal d'un fichier individuel (`max_file_score`)
- **30%** : Moyenne pondérée des scores par lignes modifiées (`weighted_avg_lines`)
- **20%** : Score de criticité des constats agrégés (`critical_evidence_score`)

### 2.4 Règles d'élévation obligatoires

1. **Plancher High** : Si un seul fichier obtient un score **>= 80.0**, le niveau global de la PR ne peut être inférieur à `HIGH`.
2. **Plancher Critical** : Si un constat bloquant (`FINDING_BLOCKER`) est présent ou si un fichier individuel atteint **>= 90.0**, le niveau global est automatiquement élevé à `CRITICAL`.
3. **Saturation** : Les scores sont limités entre `0.0` et `100.0`. Les points négatifs sont réservés aux signaux atténuants explicites (`TEST_PRESENT`).

---

## 3. Configuration et personnalisation

### 3.1 Configuration globale (`~/.gitpr/.env` ou `gitpr config`)

| Clé | Type | Défaut | Description |
|---|---|---|---|
| `GITPR_RISK_INCLUDE_IN_REVIEW` | booléen | `true` | Ajoute automatiquement la section Évaluation des risques aux revues de code (`-r`, `-f`, `--review-pr`). |

### 3.2 Règles personnalisées via YAML (`.gitpr/skill/gitpr.risk.yml`)

Vous pouvez définir des chemins, des poids et des seuils spécifiques au projet dans `.gitpr/skill/gitpr.risk.yml` ou `.gitpr.risk.yml` :

```yaml
risk:
  enabled: true
  include_in_review: true
  analysis_version: "1.0"
  thresholds:
    low_max: 24
    medium_max: 49
    high_max: 79
  weights:
    critical_path: 25
    security_sensitive: 25
    database_migration: 20
    infrastructure: 20
    no_test_change: 15
    test_present: -10
  critical_paths:
    - "app/Http/Middleware/**"
    - "app/Policies/**"
    - "database/migrations/**"
    - ".github/workflows/**"
```

---

## 4. Garanties de performance et de confidentialité

- **100% Hors-ligne et déterministe** : S'exécute entièrement sur les diffs locaux et les métadonnées Git. N'effectue aucun appel réseau ni transmission de code.
- **Exécution en sous-seconde** : Évalue les diffs en quelques millisecondes, idéal pour les hooks pre-commit et les pipelines CI.
- **Honnêteté épistémique** : Si l'historique git est indisponible (par exemple clone superficiel en CI), le signal est marqué `SIGNAL_UNAVAILABLE` avec un avertissement non bloquant sans inventer de points de risque synthétiques.

