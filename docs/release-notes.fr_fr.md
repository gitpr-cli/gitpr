# Documentation technique : Notes de version et changelog (gitpr release)

`gitpr release` est le premier sous-commande du GitPR CLI et génère le changelog / les notes de version du dépôt courant (« release notes » et « changelog » désignent le même flux). Une seule invocation parcourt les commits recueillis entre une tag d'origine et le `HEAD`, les classe selon Conventional Commits, suggère un bump sémantique de version, ajoute éventuellement un résumé exécutif d'IA et insère une nouvelle section de version en tête du changelog du dépôt. La génération est purement locale par défaut — rien n'est publié et aucune tag locale ni aucun fichier de version n'est touché ; `--publish` va plus loin et crée la release sur la forge configurée après une confirmation explicite.

---

## 1. Vue d'ensemble

La commande racine conserve toutes ses options héritées sans changement (`-r`, `-c`, `-is`, `-l`, ...) — le sous-commande est un ajout, pas une réécriture. Exécuté sans drapeau, `gitpr release` réalise le flux local : il recueille la plage de commits, classe, suggère la version, génère la section (éventuellement avec un résumé d'IA), écrit le `CHANGELOG.md`, enregistre l'artefact de l'exécution et affiche un aperçu dans le terminal limité à 40 lignes (`… and N more lines` quand il est plus long — v1 n'a pas d'aperçu interactif en TUI). Si une section de version existe déjà dans le changelog, la commande s'interrompt au lieu de la dupliquer (voir la section 6, Mode JSON et idempotence).

### 1.1 Référence de la commande — `gitpr release`

Toutes les options du sous-commande, telles qu'affichées par `gitpr release -h` (ou `--help`) :

```bash
gitpr release
gitpr release --version 2.0.0
gitpr release --publish
```

| Option | Description |
| --- | --- |
| **`--since <tag>`** | Origine de la plage : tag ou référence à partir de laquelle les commits sont recueillis (par défaut : la dernière tag atteignable, ou le premier commit quand aucune tag n'existe) |
| **`--version <x.y.z>`** | Version cible de la release (par défaut : suggestion automatique de bump sémantique) |
| **`--publish`** | Après la génération, publie la release sur la forge configurée (demande confirmation) |
| **`--draft`** | Crée la release comme brouillon sur la forge (GitHub). Ne s'applique qu'avec `--publish` ; GitLab n'a pas de concept de brouillon |
| **`--format {markdown\|json}`** | `json` affiche le résultat complet sur stdout sans toucher aux fichiers ni publier (par défaut : `markdown`) |
| **`--force`** | Régénère la section de version quand elle existe déjà dans le changelog (annulation de l'idempotence) |

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Commits de la plage `since..HEAD`, merges exclus |
| **Résumé d'IA** | Automatique quand une clé d'API est configurée (désactivez-le avec `GITPR_RELEASE_AI_SUMMARY=false`) |
| **Fichiers écrits** | Nouvelle section dans `CHANGELOG.md` + artefact `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` |
| **Publié** | Rien — la génération locale est le comportement par défaut |
| **Tags locales / fichiers de version** | Jamais touchés (read-only : les suggestions de version proviennent uniquement des tags git) |

---

## 2. Plage de la release et suggestion de version

### 2.1 Plage de commits — `--since <tag>`

Une release couvre toujours les commits d'une origine jusqu'au `HEAD`. L'origine est, par défaut, la dernière tag atteignable, et la fin de la plage est toujours `HEAD` — générer entre deux anciennes tags n'est pas pris en charge en v1. Les commits de fusion (merge) n'atteignent jamais le changelog : ils sont exclus au moment de la collecte.

```bash
# Par défaut : de la dernière tag atteignable au HEAD
gitpr release

# Origine explicite : tout depuis v1.0.0
gitpr release --since v1.0.0
```

| Caractéristique | Description |
| --- | --- |
| **Origine par défaut** | Dernière tag atteignable (`git describe --tags --abbrev=0`) |
| **Aucune tag dans le dépôt** | Première release : la plage commence au premier commit du dépôt |
| **Commits de fusion (merge)** | Exclus de la collecte |
| **Fin de la plage** | Toujours `HEAD` |

### 2.2 Suggestion de version sémantique

Sans `--version`, le moteur suggère un bump à partir des commits classés, en suivant le versionnage sémantique :

| Commits de la plage | Bump suggéré |
| --- | --- |
| Tout commit **breaking** (changement cassant) | **MAJOR** |
| Aucun commit breaking, au moins une **fonctionnalité** | **MINOR** |
| Uniquement des fixes, chores ou autres changements | **PATCH** |

La suggestion est read-only : elle provient exclusivement des tags git — le moteur ne lit jamais les fichiers de version (comme `pyproject.toml`) et ne crée jamais de tags locales. Le préfixe `v` de la dernière tag est conservé (`v1.2.3` suggère `v1.2.4`, écrit comme `## [v1.2.4]`). Quand aucune tag de version sémantique antérieure n'existe, il n'y a pas de suggestion — pour une première release, `--version` devient obligatoire pour publier.

Quand la version provient de la suggestion, la commande demande confirmation avant l'appel d'IA : `❓ Use the suggested version {version}?` (accepter est le choix par défaut). L'invite est ignorée avec un `--version` explicite, en `--format json`, dans les terminaux silencieux ou non interactifs, et avec `GITPR_RELEASE_AUTO_BUMP=false` (qui exige un `--version` explicite à chaque exécution).

### 2.3 Version explicite — `--version <x.y.z>`

Le `--version` remplace la suggestion (sans invite de confirmation) et est la seule source de la tag publiée sur la forge. Passez un `x.y.z` simple — le préfixe `v` n'est pas requis.

```bash
gitpr release --version 2.0.0
gitpr release --since v1.0.0 --version 1.1.0
```

---

## 3. Structure du changelog et fichiers

### 3.1 Classification des commits

Chaque commit de la plage est analysé selon les règles de Conventional Commits : `type`, `scope` optionnel, marqueurs de breaking (`!` après le type/scope ou une ligne `BREAKING CHANGE:` dans le corps) et la queue de squash-merge de PR `(#123)`. Les commits qui ne suivent pas la convention ne sont jamais rejetés — ils tombent dans **OTHER** avec un avertissement, et les doublons d'un même PR sont reconnus et dédupliqués.

| Catégorie | Déclencheur | Titre (repli en anglais) |
| --- | --- | --- |
| **BREAKING** | Marqueur de breaking sur tout type (`feat!`, `refactor!`, `BREAKING CHANGE:` ...) | `⚠️ Breaking Changes` |
| **FEATURE** | `feat:` | `✨ Features` |
| **FIX** | `fix:` | `🐛 Fixes` |
| **PERFORMANCE** | `perf:` | `⚡ Performance` |
| **DOCS** | `docs:` | `📚 Docs` |
| **REFACTOR** | `refactor:` | `♻️ Refactoring` |
| **CHORE** | `chore:` | `🔧 Chores` |
| **OTHER** | Tout le reste (non conformes ou types inconnus) | `📦 Other Changes` |

Les blocs de catégorie suivent l'ordre fixe FEATURE, FIX, PERFORMANCE, DOCS, REFACTOR, CHORE, OTHER (les blocs vides sont ignorés). Les commits breaking n'apparaissent que sous `⚠️ Breaking Changes`, jamais dupliqués dans leur propre catégorie. Les titres passent par le moteur de localisation de GitPR : le fichier généré suit donc la langue de l'interface, avec l'anglais en repli.

### 3.2 Anatomie d'une section de version

Une release produit une section de version : l'en-tête `## [x.y.z] - date`, un `### Summary` optionnel, un bloc par catégorie présente et un pied `**Contributors:**` avec les noms uniques d'auteurs (dédupliqués par e-mail, triés). Chaque entrée est rendue comme `subject (short hash)`, avec le scope du commit ajouté lorsqu'il est présent :

```markdown
## [1.2.0] - 2026-09-08

### Summary
Release highlights generated by the AI executive summary.

### ⚠️ Breaking Changes
- drop support for Python 3.9 (b2c3d4e) — core

### ✨ Features
- add the gitpr release subcommand (a1b2c3d) — cli
- publish releases on GitLab (#567) (d4e5f6g) — scm

### 🐛 Fixes
- handle repositories without tags (f6a7b8c) — release

**Contributors:** Ana Souza, Bob Smith
```

La section est insérée en tête du `CHANGELOG.md` — le fichier n'est jamais réécrit de zéro et les sections précédentes sont conservées. Quand une section `## [x.y.z]` existe déjà pour la même version, la commande s'interrompt avec le code de sortie 1 (voir la section 6, Mode JSON et idempotence) ; elle ne duplique jamais et ne remplace jamais silencieusement.

### 3.3 Fichiers écrits

| Artefact | Chemin | Notes |
| --- | --- | --- |
| **Changelog** | `CHANGELOG.md` | Racine du dépôt par défaut — l'exception délibérée à la convention de `.gitpr/reports/`, car c'est un fichier public et commitable. Remplacez avec `GITPR_RELEASE_CHANGELOG_PATH` (les chemins relatifs sont résolus par rapport à la racine du dépôt) |
| **Artefact des notes de version** | `.gitpr/reports/release/{branch}_{datetime}_RELEASE.md` | Écrit à chaque exécution markdown, best-effort : un échec d'écriture ne fait qu'avertir et ne fait jamais échouer la commande. Modèle de nom via `OUTPUT_FILE_NAME_RELEASE` |
| **Aperçu dans le terminal** | — | Affiché après l'enregistrement, jusqu'à 40 lignes |

---

## 4. Résumé exécutif de l'IA

Le paragraphe `### Summary` optionnel est généré par l'IA à partir des commits classés de la plage et écrit dans la langue actuelle de l'interface.

### 4.1 Template Skill au premier usage — `.gitpr.release.md`

```bash
# La première exécution en mode markdown télécharge le modèle (language-aware, ne remplace jamais)
gitpr release
```

Lors de la première exécution en mode markdown, le CLI télécharge le template Skill `.gitpr.release.md` depuis les modèles du projet. Le téléchargement respecte la langue actuelle de l'interface (les variantes distantes comme `gitpr.release.fr_fr.md` sont enregistrées localement comme `.gitpr.release.md`), ne remplace jamais un fichier local existant et n'échoue jamais sur une erreur réseau — l'exécution continue avec la persona intégrée. Le téléchargement est entièrement ignoré en `--format json`, qui est stdout-only. Le fichier est chargé comme system instruction de l'IA (persona : **Release Manager**, contrat JSON strict) — modifiez-le localement pour personnaliser le résumé exécutif. Consultez la [documentation de Skills et Templates](skill-template.md) pour le mécanisme général.

### 4.2 Génération et dégradation contrôlée

Les plages de plus de 200 commits sont résumées par lots (Map-Reduce, avec un avis comme `📦 Large commit range detected!`), et les réponses passent par le cache MD5 standard de GitPR : des exécutions inchangées ne répètent donc pas les appels d'IA. Deux remarques : le cache est indexé par le prompt — modifier `.gitpr.release.md` n'invalide pas les résumés en cache — et le résumé utilise toujours la même infrastructure d'IA que les autres commandes de GitPR (fournisseur configuré, sortie JSON, nouvelle tentative automatique). Consultez la [documentation des Fournisseurs d'IA](providers-ia.md).

Le résumé ne bloque jamais la commande : sans clé d'API configurée, ou quand l'appel d'IA échoue, la commande avertit (`AI summary failed: changelog generated without a summary.`) et génère la section avec les listes classées uniquement. `GITPR_RELEASE_AI_SUMMARY=false` désactive complètement le résumé.

---

## 5. Publication sur la forge

### 5.1 Confirmation et garde-fous — `--publish`

La publication n'a lieu que dans le flux markdown, après la génération locale et l'aperçu, derrière une confirmation explicite : `❓ Publish release {version} on {provider}?` — refuser (le choix par défaut) conserve le changelog et affiche `⏭️ Publication skipped — the changelog was generated locally.` Le corps de la release envoyé à la forge est la section générée sans l'en-tête `## [x.y.z] - date` (le titre de la release porte la version).

```bash
gitpr release --publish
gitpr release --since v1.0.0 --version 1.2.0 --publish
```

Garde-fous : sans remote git `origin`, la commande refuse de publier (`❌ No git remote 'origin' found. Cannot publish the release.`, code de sortie 1) ; combiné avec `--format json`, le `--publish` avertit seulement qu'il est ignoré (`⚠️ --format json is stdout-only: --publish is ignored.`) — le mode JSON ne publie jamais ; après une exécution locale simple, le CLI suggère `ℹ️ To publish this release on the forge, run again with --publish.`

### 5.2 Forges prises en charge

La publication cible la forge configurée dans les paramètres SCM (`gitpr --init` ou `GITPR_SCM_PROVIDER`). Consultez la [documentation Multi-Forge SCM](scm-multiforge.md) pour la configuration du fournisseur.

| Forge | Release | Notes |
| --- | --- | --- |
| **GitHub** | Oui | Une tag manquante est créée automatiquement par l'API, pointant vers la branche par défaut du dépôt (pas le `HEAD` local) ; les brouillons sont respectés |
| **GitLab** | Oui | La tag doit déjà exister sur la forge ; pas de concept natif de brouillon |
| **Bitbucket Cloud** | Non | Pas d'API de release — la commande avertit et garde le changelog local pour une publication manuelle |
| **Azure DevOps** | Non | Pas d'API de release — la commande avertit et garde le changelog local pour une publication manuelle |

Quand la publication n'est pas prise en charge, l'avertissement est `⚠️ Release publishing is not supported on {provider}. The changelog was generated locally — publish it manually.`

### 5.3 Brouillons — `--draft`

Le `--draft` n'a d'importance qu'avec `--publish` (isolé, il avertit `⚠️ --draft only applies together with --publish: generating the changelog locally.`). GitHub est la seule forge avec un concept de brouillon et, par défaut, un `--publish` sur GitHub crée déjà un **brouillon** (`GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT=true`) ; passez `--draft` pour forcer un brouillon quand cette valeur par défaut est désactivée. GitLab n'a pas de brouillons : une demande de brouillon ne fait qu'avertir et publie directement.

```bash
gitpr release --publish --draft
```

---

## 6. Mode JSON et idempotence

### 6.1 Sortie JSON pure — `--format json`

Le `--format json` est stdout-only, idéal pour les scripts et le CI : il n'écrit rien (pas de mise à jour du `CHANGELOG.md`, pas d'artefact d'exécution, pas de téléchargement de Skill), ne publie rien et ne pose jamais de question (la confirmation de version est ignorée). Le flux stdout reste propre — les avertissements voyagent dans le payload JSON. La sortie suit le résultat de la release : `version`, `previous_tag`, `generated_at`, `summary`, `sections` (une liste de commits classés par catégorie), `breaking_changes`, `contributors`, `markdown` et `warnings`.

```bash
gitpr release --format json
```

### 6.2 Section existante et `--force`

L'écriture du changelog est idempotente par version : quand la section `## [x.y.z]` de la version cible existe déjà, la commande s'interrompt avec le code de sortie 1 sans modifier le fichier — elle ne duplique jamais le contenu et ne le remplace jamais silencieusement. Le `--force` régénère et remplace cette section (`🔄 Existing section for version {version} regenerated.`) ; sans section existante, le `--force` est une simple addition.

```bash
gitpr release --force
gitpr release --since v1.0.0 --version 1.2.0 --force
```

---

## 7. Variables d'environnement

La configuration de la release est lue depuis le fichier global `~/.gitpr/.env` (format dotenv). Les booléens suivent la convention « false désactive » : non défini ou toute valeur autre que `false` / `0` / `no` / `off` / `n` signifie activé — les valeurs par défaut du tableau s'appliquent quand la variable n'est pas définie.

| Variable | Valeur par défaut | Objet |
| --- | --- | --- |
| `GITPR_RELEASE_CHANGELOG_PATH` | `CHANGELOG.md` | Fichier du changelog ; chemins relatifs résolus par rapport à la racine du dépôt, chemins absolus respectés |
| `GITPR_RELEASE_AI_SUMMARY` | `true` | Active le résumé exécutif d'IA ; `false` ne génère que les listes classées |
| `GITPR_RELEASE_AUTO_BUMP` | `true` | Active le bump sémantique automatique ; `false` exige un `--version` explicite |
| `GITPR_RELEASE_PUBLISH_DRAFT_BY_DEFAULT` | `true` | GitHub : `--publish` crée la release comme brouillon par défaut |
| `OUTPUT_FILE_NAME_RELEASE` | `{branch}_{datetime}_RELEASE.md` | Modèle de nom de l'artefact d'exécution dans `.gitpr/reports/release/` |

> **Note :** Consultez également la [documentation de Skills et Templates](skill-template.md) pour personnaliser les fichiers de modèles d'IA de GitPR.
