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

---

## 4. Ordre d'Exécution du Pipeline

1. **Résolution de la Politique** : Charge la politique active ou demandée via `--policy`. Échoue avec le code 2 si elle est invalide.
2. **Extraction du Diff** : Obtient le diff normalisé par rapport à la branche de base ou HEAD avec exclusions intelligentes.
3. **Linter Statique et Secrets** : Exécute les règles regex, le scanner de secrets et les bridges SAST (Semgrep, Gitleaks, Bandit).
4. **Scoring de Risque Préliminaire** : Identifie les métriques de risque par fichier et agrégées de la PR.
5. **Revue par IA (Optionnelle)** : Fait appel au fournisseur d'IA si configuré (dégrade gracieusement en l'absence de clé).
6. **Classification contre Baseline** : Compare les anomalies avec la baseline (statut : `new`, `existing`, `ignored`, `accepted_debt`, `resolved`). Sans baseline, toutes les anomalies sont comptabilisables.
7. **Évaluation du Seuil** : Compare les anomalies comptabilisables par rapport à `--fail-on`.
8. **Masquage et Génération de l'Artefact** : Assainit les données sensibles et sérialise en SARIF, JSON ou JUnit XML.

---

## 5. Formats d'Artefacts

### SARIF 2.1.0 (`--format sarif`)
- Compatible nativement avec **GitHub Code Scanning**, **GitLab SAST** et Azure DevOps.
- Remplit `tool.driver.rules` dynamiquement à partir des anomalies détectées.
- Mappe les niveaux (`error` $	o$ `error`, `warning` $	o$ `warning`, `info` $	o$ `note`).
- Insère `fingerprint`, `baseline_status` et `risk_score` dans `properties`.

### Enveloppe JSON (`--format json`)
JSON structuré contenant le statut, le résumé, les métriques de risque et les anomalies détaillées avec masquage.

### JUnit XML (`--format junit`)
Rapport XML standard pris en charge par Jenkins, le résumé de tests de GitLab CI et Azure Pipelines.
- Les anomalies bloquantes génèrent des balises `<failure>`.
- Les anomalies informatives sont enregistrées dans des balises `<system-out>`.

---

## 6. Intégration avec GitHub Actions

Utilisez la composite action officielle dans `.github/workflows/ci.yml` :

```yaml
name: CI Check

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Requis pour le téléversement SARIF vers GitHub Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Exécuter GitPR Check
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }}
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Téléverser SARIF vers GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

---

## 7. Guide de Migration : Mise à Niveau depuis le Workflow Hérité d'Action

Avant l'introduction de `gitpr check`, la composite action officielle (`action.yml`) exécutait deux commandes séquentielles discrètes :
1. `gitpr --linter` (échouait immédiatement en cas d'erreurs statiques).
2. `gitpr --fullreview` (générait sur le disque un fichier texte non classifié `*_PR_FULLREVIEW.txt`, facultativement concaténé dans `$GITHUB_STEP_SUMMARY`).

Cette refonte architecturale a introduit une rupture de contrat lors de la mise à niveau vers les versions modernes de GitPR :
- **Absence de `*_PR_FULLREVIEW.txt` sur le disque** : La commande `gitpr check` ne crée pas ce fichier texte. Les workflows hérités qui dépendaient de `cat *_PR_FULLREVIEW.txt >> $GITHUB_STEP_SUMMARY` échoueront ou produiront des résumés vides.
- **SARIF et Code Scanning Natif** : La sortie standard est désormais SARIF 2.1.0 (`gitpr-results.sarif`), JSON ou JUnit XML, s'intégrant directement dans l'onglet **Security > Code scanning alerts** de GitHub via `github/codeql-action/upload-sarif@v3`.
- **Clé d'API Optionnelle et CI à Coût Zéro** : L'entrée `api-key` n'est plus obligatoire (`required: false`). Les workflows peuvent s'exécuter sans frais ou hors ligne avec `no-ia: "true"`.
- **Codes de Sortie Déterministes et Suppression par Baseline** : Au lieu d'échecs inconditionnels sur n'importe quelle anomalie, les codes de sortie sont strictement contrôlés par `--fail-on` (par défaut `error`). Les anomalies enregistrées dans `.gitpr/baseline.json` sont supprimées et n'interrompent pas le pipeline.

### Comparatif Contractuel : Avant vs. Après

| Caractéristique | Workflow Hérité (`v0.0.12` – `v0.0.36`) | Vérification Unifiée Moderne (`v0.0.37+`) |
|---|---|---|
| **Commande Sous-jacente** | `gitpr --linter` puis `gitpr --fullreview` | `gitpr check` |
| **Artefact Généré** | `*_PR_FULLREVIEW.txt` (fichier texte brut) | `gitpr-results.sarif` (SARIF 2.1.0), JSON ou JUnit XML |
| **Intégration UI GitHub** | Concaténation manuelle dans `$GITHUB_STEP_SUMMARY` | Annotations inline natives dans la PR et alertes dans **Code Scanning** |
| **Exigence de Clé IA** | Obligatoire (`required: true`) | Optionnelle (`required: false`) ; supporte `no-ia: "true"` |
| **Critère d'Échec** | Échec du linter en cas d'erreur ; revue non filtrée | Configurable via `--fail-on` (`info`, `warning`, `error`) |
| **Support Baseline** | Aucune suppression dans le CI | Suppressions complètes via `.gitpr/baseline.json` |
| **Codes de Sortie** | Non standardisés par sous-étape | Normalisés : `0` (propre), `1` (seuil dépassé), `2` (erreur d'exécution) |

### Exemples de Workflow : Avant et Après

#### ❌ Avant (Workflow Hérité)

```yaml
name: CI Code Review (Hérité)

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # Invocation héritée de la composite action
      - name: Exécuter GitPR Review
        uses: natanfiuza/gitpr@v0.0.36
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # était obligatoire

      # Étape dépendante qui échoue sur les versions modernes :
      - name: Publier le Résumé de l'Étape
        if: always()
        run: |
          REVIEW_FILE=$(ls *_PR_FULLREVIEW.txt 2>/dev/null | head -n 1)
          if [ -f "$REVIEW_FILE" ]; then
            cat "$REVIEW_FILE" >> $GITHUB_STEP_SUMMARY
          fi
```

#### ✅ Après (Vérification Unifiée Moderne)

```yaml
name: CI Check (Moderne)

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write # Requis pour le téléversement SARIF vers Code Scanning
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Exécuter GitPR Check Unifié
        uses: natanfiuza/gitpr@main
        with:
          provider: gemini
          api-key: ${{ secrets.GEMINI_API_KEY }} # optionnel si no-ia est true
          format: sarif
          output: gitpr-results.sarif
          fail-on: error

      - name: Téléverser SARIF vers GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: gitpr-results.sarif
```

### Préserver les Revues Textuelles Autonomes

Si votre flux de travail exige strictement le fichier `*_PR_FULLREVIEW.txt` sous forme de texte brut (par ex. pour l'archivage ou des outils d'analyse tiers hérités), exécutez `gitpr --fullreview` comme une étape de script autonome au lieu d'utiliser `action.yml` :

```yaml
      - name: Exécuter Full Review Autonome (Sortie Héritée)
        env:
          DEFAULT_AI_PROVIDER: gemini
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          pip install gitpr-cli
          gitpr --fullreview
```
