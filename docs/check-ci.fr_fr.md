# Documentation Technique : Vérification Unifiée pour CI (`gitpr check`)

La commande `gitpr check` fournit un point d'entrée unique conçu pour les pipelines d'Intégration Continue (CI) tels que GitHub Actions, GitLab CI et Jenkins. Elle orchestre l'analyse statique, les bridges SAST externes, la détection des secrets, la revue de code par IA optionnelle, l'évaluation des risques et la baseline en une seule commande produisant des artefacts standardisés (**SARIF 2.1.0**, **JSON** ou **JUnit XML**) et des codes de sortie déterministes.

---

## 1. Vue d'ensemble

```bash
# Exécute la vérification unifiée et écrit le SARIF sur stdout
gitpr check

# Génère un fichier SARIF pour GitHub Code Scanning
gitpr check --format sarif --output gitpr-results.sarif

# Vérification rapide à coût zéro sans appel à l'IA
gitpr check --no-ia

# Échoue en cas d'avertissement ou d'erreur
gitpr check --fail-on warning

# Restreint la revue d'IA uniquement aux fichiers à haut risque
gitpr check --ia-only-high-risk

# Évalue les résultats par rapport à une baseline spécifique
gitpr check --baseline .gitpr/baseline.json

# Applique un Policy Pack spécifique
gitpr check --policy security-strict@1.0.0
```

---

## 2. Options CLI et Variables d'Environnement

| Option | Variable d'Environnement | Par Défaut | Description |
|---|---|---|---|
| `--base <ref>` | `GITPR_CHECK_BASE` | Auto-détecté | Référence git pour la comparaison (`GITHUB_BASE_REF`, `origin/main` ou `HEAD`). |
| `--format {sarif\|json\|junit}` | `GITPR_CHECK_FORMAT` | `sarif` | Format de l'artefact produit. |
| `-o`, `--output <path>` | `GITPR_CHECK_OUTPUT` | `None` (stdout) | Chemin du fichier de sortie. Si omis, écrit sur `stdout`. |
| `--fail-on <severity>` | `GITPR_CHECK_FAIL_ON` | `error` | Sévérité minimale provoquant le code de sortie 1. |
| `--no-ia` | `GITPR_CHECK_NO_IA` | `false` | Désactive la revue d'IA. |
| `--ia-only-high-risk` | `GITPR_CHECK_IA_ONLY_HIGH_RISK` | `false` | Analyse IA uniquement pour les fichiers à risque élevé ou critique. |
| `--baseline <path>` | `GITPR_CHECK_BASELINE_PATH` | `.gitpr/baseline.json` | Chemin vers le manifeste JSON de baseline. |
| `--policy <name>@<ver>` | `GITPR_CHECK_POLICY` | Lockfile actif | Applique un Policy Pack spécifique. |
| — | `GITPR_CHECK_TIMEOUT_SECONDS` | `300` | Délai limite global en secondes. |

---

## 3. Codes de Sortie

| Code | Statut | Signification |
|---|---|---|
| **`0`** | Succès | Aucun résultat comptabilisable n'a atteint le seuil `--fail-on`. |
| **`1`** | Échec | Un ou plusieurs résultats comptabilisables ont atteint le seuil `--fail-on`. |
| **`2`** | Erreur | Exécution interrompue par une erreur de configuration, une politique introuvable, une baseline corrompue ou un délai dépassé. |

> Les autres flux qui exigent le baseline (`-l`, `-r`, `-f`, `-i`, `risk`, `review-pr`) sortent avec **1** face à un baseline inutilisable. Voir [Baseline : exit codes par flux](baseline-suppressions.fr_fr.md#baseline-inutilisable-exit-codes-par-flux).

