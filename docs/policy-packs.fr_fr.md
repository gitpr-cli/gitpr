# Documentation Technique : Policy Packs (`gitpr policy`)

Un **Policy Pack** est un manifeste YAML versionnable qui transporte toute la politique qualité d'une équipe — skills de revue, règles de linter, overrides de sévérité, chemins critiques, poids de risque et conventions de PR/commit — dans un seul fichier qu'un dépôt peut adopter, relire et versionner avec son propre code. `gitpr policy` enregistre *quel* pack le dépôt suit et c'est la seule chose qui décide *ce que* ce pack change.

Jusqu'ici chacune de ces surfaces se configurait ailleurs : `.gitpr/skill/.gitpr.review.md`, `.gitpr/skill/.gitpr.linter.yml`, `.gitpr/skill/gitpr.risk.yml`, `~/.gitpr/.env`. Rien ne reliait l'ensemble, donc « nous suivons la politique Acme » était une convention, pas quelque chose que l'outil pouvait vérifier. Avec un pack, c'est une ligne dans un fichier sous contrôle de version.

---

## 1. Vue d'ensemble

Les Policy Packs agissent sur trois surfaces :

1. **Le groupe `gitpr policy`** : sept commandes pour lister, valider, afficher, adopter, installer, créer et abandonner une politique. `list`, `validate` et `show` ne font que lire ; `use`, `install`, `init` et `off` écrivent et demandent avant de le faire.
2. **Toutes les commandes suivantes dans le dépôt** : avec un pack actif, `gitpr -r`, `gitpr -f`, `gitpr -c`, `gitpr` (description de PR), `gitpr -l` et `gitpr risk` s'exécutent sous lui, sans qu'aucune n'accepte un nouvel argument.
3. **`.gitpr/policy.lock.yml`** : le fichier qui enregistre la décision. Il nomme le pack, sa version, sa source et une somme de contrôle par pack, afin qu'un collègue obtienne la même politique depuis le même commit.

### 1.1 Référence des commandes

```bash
gitpr policy list                        # Les packs de cette machine et celui en vigueur
gitpr policy validate gitpr/laravel-quality   # Schema, compatibilité, skills, règles, dépendances
gitpr policy show                        # La politique effective, avec l'origine de chaque valeur
gitpr policy use acme/team-policy@1.0.0  # Épingle un pack, en écrivant .gitpr/policy.lock.yml
gitpr policy init --stack laravel        # Suggère et active le pack officiel de la stack
gitpr policy install ./our-policy        # Copie un répertoire local vers ~/.gitpr/policies
gitpr policy off                         # Cesse de suivre le pack
```

| Commande | Écrit | Description |
|---|---|---|
| **`list`** | — | Le pack actif (avec son graphe de dépendances) et tous les packs trouvés sur cette machine |
| **`validate <chemin\|nom[@plage]>`** | — | Valide un pack et rapporte ce qu'il fait. Sortie non nulle quand le pack est invalide, pour que la CI puisse bloquer |
| **`show`** | — | La politique effective en vigueur, avec la provenance de chaque champ et l'ordre de précédence qui l'a produite |
| **`use <nom>[@<version>]`** | `.gitpr/policy.lock.yml` | Épingle un pack pour ce dépôt. Remplace le pack qui était actif |
| **`init [--stack laravel\|vue\|php\|node]`** | `.gitpr/policy.lock.yml` | Détecte la stack à partir du projet et active le pack officiel correspondant |
| **`install <chemin> [--force]`** | `~/.gitpr/policies/` | Valide un pack dans un répertoire local et le copie dans le magasin de packs de l'utilisateur. Aucun registry, aucun téléchargement |
| **`off`** | supprime `.gitpr/policy.lock.yml` | Cesse de suivre le pack. Le pack et le fichier d'overrides sont conservés |

Toutes les commandes qui écrivent acceptent `--yes`, qui saute la confirmation mais **pas** les vérifications derrière. Sans terminal et sans `--yes`, une commande d'écriture échoue avec l'instruction au lieu de se bloquer sur une invite que personne ne lira — c'est ce qui rend le groupe sûr à appeler depuis un hook ou un job de CI qui a oublié le flag.

### 1.2 D'où peut venir un pack

Trois sources, cherchées dans cet ordre :

| Ordre | Source | Emplacement | `source` dans le lockfile |
|---:|---|---|---|
| 1 | Le dépôt lui-même | `<repo>/.gitpr/policies/<nom>/` | `local_path` |
| 2 | Le magasin de l'utilisateur | `~/.gitpr/policies/<nom-aplati>/` | `installed` |
| 3 | Ce que GitPR livre | `src/policy_packs/<nom>/` | `bundled` |

Un pack installé vit dans un répertoire **aplati** — `acme/team-policy` est stocké sous `acme__team-policy` — parce que le namespace fait partie de l'identité du pack, pas de l'arborescence du système de fichiers. Un pack versionné dans le dépôt se trouve par chemin, et c'est ce qui permet à une équipe d'adopter une politique que personne n'a installée.

Rien n'est téléchargé. Un pack est du texte sur disque ; la résolution le lit, le hache et le compose.

---

## 2. Le manifeste

Un pack est un répertoire contenant `policy.yml` et les assets déclarés par le manifeste :

```
acme__team-policy/
├── policy.yml          # le manifeste — le seul fichier obligatoire
├── linter.yml          # déclaré par linter.rules_file
├── README.md           # voyage avec lui ; fait partie du pack, n'est lu par personne
└── CHANGELOG.md
```

### 2.1 Schema

Le schema est **fermé** : une clé inconnue est une erreur, pas un avertissement. Une faute de frappe comme `test:` au lieu de `tests:` doit échouer bruyamment, car l'alternative est une politique qui ne fait silencieusement rien pendant que son nom continue d'apparaître dans la sortie.

| Clé | Obligatoire | Type | Signification |
|---|---|---|---|
| `schema_version` | ✅ | int | Version du schema du manifeste. Actuellement `1` |
| `name` | ✅ | str | `namespace/nom`. Le path traversal est refusé |
| `version` | ✅ | str | La version du pack lui-même |
| `min_gitpr_version` | ✅ | str | Plage `SpecifierSet`, ex. : `">=1.3.0"`. Validée contre le GitPR en cours d'exécution |
| `description` | — | str | Texte libre, affiché par `policy list` |
| `license` | — | str | Texte libre |
| `authors` | — | list[str] | Texte libre |
| `extends` | — | list | Dépendances : `[{name, version}]`. `version` est une plage |
| `baseline` | — | map | `suppressions`, `accepted_debt` — les décisions que le pack apporte au baseline, en mémoire seulement |
| `skills` | — | map | `skills.<type>.additional_context` — texte attaché au prompt de cette skill |
| `linter` | — | map | `rules_file`, `severity_overrides` |
| `risk` | — | map | `critical_paths`, `test_patterns`, `weights`, `thresholds` |
| `pr` | — | map | `required_sections` |
| `commit` | — | map | `allowed_types` |
| `protected_paths` | — | list[str] | Déclaré pour le prompt, imposé par aucun moteur |

### 2.2 Un exemple complet

```yaml
schema_version: 1
name: acme/team-policy
version: 1.0.0
description: The Acme house rules for PHP services.
min_gitpr_version: ">=1.3.0"
license: MIT
authors:
  - Acme Platform

extends:
  - name: acme/base-policy
    version: ">=1.0.0 <2.0.0"

skills:
  review:
    additional_context: |
      Money is an integer in minor units. A float in a monetary field is a bug
      regardless of how it got there.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  critical_paths:
    - app/Services/**
  test_patterns:
    - spec/**
  weights:
    database_migration: 25

pr:
  required_sections:
    - Business impact
    - Rollback plan

commit:
  allowed_types:
    - feat
    - fix
    - chore

baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31

protected_paths:
  - config/**
```

### 2.3 Les sections

**`skills`** — un bloc par type de skill. Les types valides sont ceux que GitPR connaît : `commit`, `pr`, `review`, `filereview`, `blame`, `issue`, `release`, `fix`, `tests`, `explain`, `mentor`. Un type inconnu est refusé au parsing ; un pack ne peut pas inventer une skill, puisque rien ne la lirait. Le texte est concaténé avec les contributions des autres packs et attaché au prompt comme instructions système, et c'est pourquoi il entre aussi dans la clé de cache — voir §4.3.

**`linter.rules_file`** — le nom d'un fichier YAML de règles **à l'intérieur du répertoire du pack**. Un chemin qui s'échappe du répertoire est refusé, donc un pack ne peut pas pointer vers `/etc/passwd` ni vers un fichier au-dessus de lui-même. Les règles rejoignent le catalogue par `name`, celles du projet l'emportant sur celles du pack.

**`linter.severity_overrides`** — change le niveau d'une règle qui existe déjà, après que tout catalogue a été fusionné. `level` vaut `error` ou `warning`. **Abaisser une règle de `error` à `warning` exige un `reason`** — un override qui affaiblit la porte est une décision que quelqu'un a prise exprès, et la raison voyage avec lui dans `policy validate`, `policy show` et le rapport de revue. Durcir une règle n'a pas besoin de justification. Un override nommant une règle inexistante nulle part dans le catalogue final est une **erreur** : ne rien faire en silence laisserait l'équipe croire qu'une règle a été assouplie alors que ce n'est pas le cas.

**`risk.critical_paths` / `risk.test_patterns`** — réunis entre packs, dans l'ordre de précédence. `test_patterns` apprend au moteur de risque quels fichiers comptent comme tests dans l'arborescence *de ce* projet (`spec/**`, `**/*Cest.php`), ce qui fait déclencher `TEST_PRESENT` dans un dépôt dont le répertoire de tests ne s'appelle ni `test/` ni `tests/`.

**`risk.weights` / `risk.thresholds`** — une valeur unique, pas une liste. Deux packs non reliés par `extends` en désaccord sur le même poids est une **erreur de validation**, nommant les deux ; une dépendance et son dépendant en désaccord est un raffinement, et le dépendant l'emporte.

**`pr.required_sections`, `commit.allowed_types`, `protected_paths`** — rien dans le code ne lit ces trois-là. Ils existent pour être *dits* au modèle, et c'est pourquoi ils sont rendus dans les contextes des skills `pr` et `commit` comme texte de prompt, plutôt que laissés comme données.

### 2.4 `extends`

Un pack peut dépendre d'autres packs. Le graphe est résolu en **ordre topologique** — dépendances d'abord, pack racine en dernier — donc les valeurs d'une dépendance sont appliquées avant celles du pack qui s'appuie sur elles. Un cycle est refusé avec la chaîne dans le message, car « il y a un cycle » sans le chemin n'est pas actionnable.

Un pack racine par dépôt. `gitpr policy use` **remplace** le choix précédent au lieu de s'y ajouter ; le graphe sous la racine s'atteint par `extends`, ce qui garde l'échelle de précédence linéaire plutôt qu'en réseau.

### 2.5 `baseline`

Un pack peut porter les suppressions et la dette acceptée que sa stack connaît déjà, pour qu'adopter le pack et adopter le baseline soient une seule décision au lieu de deux :

```yaml
baseline:
  suppressions:
    - scope: rule
      rule_id: acme-no-float-money
      reason: The float check is advisory while the migration is in flight.
  accepted_debt:
    - fingerprint: "sha256:9f2c…"
      owner: acme-platform
      reason: Scheduled for the payments rewrite.
      due_date: 2026-12-31
```

Les deux moitiés ont la **même forme et les mêmes quatre portées** que `.gitpr/baseline.overrides.yml` — `finding`, `line`, `file`, `rule` — et passent par les **mêmes validateurs** : un pack qui déclarerait une suppression sans motif, ou une dette acceptée que personne n'assume, serait un moyen de contourner l'auditabilité pour laquelle le baseline existe. Un pack n'achète pas une règle plus faible en la déclarant dans un autre fichier. Le bloc est fermé comme le reste du manifeste : une clé inconnue est une erreur, et un échec nomme le pack, la moitié et l'index de l'entrée, parce que c'est ce que `gitpr policy validate` imprime.

Trois propriétés séparent cette couche des fichiers du dépôt lui-même :

| | Bloc du pack | `.gitpr/baseline.json` / `.overrides.yml` |
|---|---|---|
| **Où il vit** | En mémoire, pendant la classification | Sur disque, commité |
| **Origine affichée** | `policy:<nom>@<version>`, par entrée — la décision d'une dépendance nomme la dépendance, pas la racine | `local` |
| **Écrit par une exécution** | Jamais. Rien d'un pack n'atteint le fichier de baseline | `baseline create`, `update`, `suppress` |

`gitpr baseline unsuppress` ne peut donc pas en retirer une : il dit quel pack la porte, et la réponse est une modification du pack, pas du dépôt. Rien n'est téléchargé pour lire le bloc — le pack est déjà du texte sur disque, couvert par le checksum du lockfile comme tout autre champ qu'il déclare, donc le baseline d'un pack ne peut pas être modifié sans que le checksum s'en aperçoive.

Un pack qui utilise ce bloc devrait déclarer un `min_gitpr_version` incluant la version avec laquelle il a été écrit : un GitPR plus ancien lit le manifeste, ne connaît pas la clé et refuse le pack entier, au lieu d'appliquer une politique à moitié silencieusement absente.

---

## 3. Précédence

Du plus faible au plus fort. Une valeur avec un numéro plus élevé l'emporte sur une avec un numéro plus faible.

| # | Couche | Écrite par |
|---:|---|---|
| 1 | Défauts internes de GitPR | le code |
| 2 | Packs de dépendance | `extends`, en ordre topologique |
| 3 | Le pack racine | `.gitpr/policy.lock.yml` |
| 4 | `.gitpr/policy.overrides.yml` | le dépôt |
| 5 | Configuration locale du projet | `.gitpr/skill/*`, `.gitpr.linter.yml` |
| 6 | Flags de CLI | `--base`, `--provider`, … |
| 7 | Variables d'environnement | `GITPR_*` |

Le catalogue du linter est fusionné dans son propre ordre, car ses couches ne sont pas les mêmes :

**ruleset de sécurité embarqué → règles des packs → règles du projet → plugins globaux → overrides de sévérité**

Les overrides de sévérité sont appliqués **en dernier**, contre le catalogue final, car c'est seulement là que l'ensemble des noms de règles connus est complet — et c'est ce qui permet à un override comportant une faute de frappe d'échouer au lieu de ne silencieusement rien faire.

### 3.1 Le lockfile

`gitpr policy use acme/team-policy@1.0.0` écrit :

```yaml
schema_version: 1
root:
  name: acme/team-policy
  version: 1.0.0
  source: installed
  checksum: 4f449708ac83901bffb4275e8d6d7c880154022bca0382962519c2270cb1842f
packs:
  - name: acme/base-policy
    version: 1.0.0
    source: installed
    checksum: 9c1f…
  - name: acme/team-policy
    version: 1.0.0
    source: installed
    checksum: 4f44…
```

Le fichier est destiné à être **commité**. Un pack à l'intérieur du dépôt est aussi enregistré par un `path` relatif au dépôt, en POSIX, afin qu'un collègue le lise au même endroit plutôt que depuis une copie personnelle ; un pack du magasin de l'utilisateur n'est enregistré que par son nom, car l'endroit où il vit est un détail de machine.

### 3.2 Overrides

`.gitpr/policy.overrides.yml` est le dépôt parlant de lui-même, un niveau sous les flags de CLI. Il utilise la forme `{add, remove}` pour les listes, donc retirer un chemin protégé ou une section obligatoire est une ligne dans un diff plutôt qu'une absence :

```yaml
protected_paths:
  add:
    - legacy/**
  remove:
    - .env.example

risk:
  weights:
    large_diff: 10
```

---

## 4. Intégrité et comportement en cas d'échec

### 4.1 La somme de contrôle

La somme de contrôle de chaque pack est un SHA-256 sur `policy.yml` plus tous les assets déclarés par le manifeste, calculée à l'activation du pack et revérifiée à chaque exécution. Un asset modifié est une politique différente, et une politique différente n'est pas celle que l'équipe a validée.

Notez que la somme est exacte au byte près : un pack versionné dans le dépôt et réécrit par `core.autocrlf` au checkout échouera avec un mismatch. Un `gitpr policy use` sur un pack dont la copie de travail est normalisée en LF — ou un `.gitattributes` épinglant le répertoire du pack — règle la question.

### 4.2 Les trois abandons

La résolution **abandonne** au lieu de dégrader dans exactement trois cas :

| Échec | Pourquoi il abandonne |
|---|---|
| Un pack n'est plus sur le disque | Ses règles ont disparu ; la sortie porterait toujours l'étiquette de la politique |
| Une version épinglée a disparu (après une mise à jour, ou un `use` ailleurs) | La version validée par l'équipe n'est pas celle qui s'exécuterait |
| Une somme de contrôle ne correspond plus | Le contenu a changé depuis l'activation |

Tenir la moitié de la promesse est pire que ne pas la tenir, car la revue, la sortie du linter et le score de risque prétendraient tous s'exécuter sous la politique. Chaque abandon nomme le pack, ce qui s'est passé et la commande qui répare.

`strict=False` est la seule échappatoire, et seules les commandes `gitpr policy` l'utilisent — elles sont l'outil qui répare un lockfile cassé, donc elles doivent pouvoir s'exécuter pendant qu'un lockfile est cassé.

### 4.3 Portée du cache

GitPR met en cache les réponses de l'IA par MD5 sur le prompt. Le contexte de skill est un **argument séparé** (`instrucao_sistema`) et ne fait pas partie de ce hash — donc, sans correctif, activer un pack sur un diff déjà en cache ne changerait absolument rien, et l'étiquette serait un mensonge.

Le correctif est la portée du cache. Avec un pack actif, `::policy::<nom>@<version>::<checksum>` est ajouté à la clé de cache, ce qui signifie qu'un pack activé invalide les entrées concernées et que deux packs différents ne partagent jamais une réponse. Sans pack, la portée est la chaîne vide, donc rien ne change.

### 4.4 Garanties

- **Aucun réseau, jamais** : un pack est local par conception. La résolution lit un lockfile, hache des fichiers et compose du texte.
- **Aucune exécution arbitraire** : `policy validate` ne lance aucun sous-processus, et la validation est hors ligne et sans effet de bord. Un pack est du texte écrit par quelqu'un d'autre, et la commande qui l'inspecte n'exécute rien de ce qu'il contient.
- **Aucun secret dans un manifeste** : un manifeste correspondant à l'une des règles embarquées de détection de secrets est refusé au parsing, en utilisant le même ruleset que le linter plutôt qu'un second scanner qui pourrait diverger.

---

## 5. Configuration

| Clé | Type | Défaut | Description |
|---|---|---|---|
| `GITPR_POLICY_ENABLED` | bool | `true` | Lit et applique le lockfile. La désactiver fait que chaque commande se comporte comme si le dépôt n'avait pas de pack, sans toucher au lockfile |
| `GITPR_POLICY_CONTEXT_MAX_CHARACTERS` | int | `12000` | Plafond de contexte qu'un pack peut ajouter à un prompt. Au-delà, les contributions sont retirées d'abord du pack de plus faible précédence et le retrait est signalé comme avertissement |

Quel pack est actif n'est délibérément **pas** une clé de configuration : il appartient au dépôt, pas à la machine, donc il vit dans le lockfile où il peut être relu et versionné avec le code auquel il s'applique.

---

## 6. Packs officiels

| Pack | Règles en chaîne | À quoi il sert |
|---|---:|---|
| `gitpr/php-security` | 8 | Socle de sécurité PHP : interpolation SQL, `eval`, hachages de mot de passe faibles, `unserialize` étranger, includes dynamiques, `extract()` depuis l'input, CORS avec joker, cookies de session non sécurisés |
| `gitpr/laravel-quality` | 7 (+8) | Porte qualité Laravel : autorisation, mass assignment, transactions, N+1, migrations réversibles, files d'attente, données personnelles. **Étend `gitpr/php-security`** |
| `gitpr/node-quality` | 7 | Services Node : promesses flottantes, validation d'entrée, états non gérés, hygiène des dépendances, configuration et secrets |
| `gitpr/vue-quality` | 6 | Composants Vue 3 : props et emits, réactivité, nettoyage des effets de bord, états asynchrones, accessibilité, taille du composant |

Chacun porte un contexte de revue qu'un relecteur générique n'a pas (ce que coûte un `down()` qui ne défait pas son `up()`, pourquoi un job déclenché dans une transaction peut s'exécuter avant que la ligne soit commitée), des chemins critiques et des motifs de test pour son arborescence, et des conventions de PR/commit. Ils sont délibérément petits et opinionnés : ils ajoutent ce que les défauts ne couvrent pas déjà, plutôt que de les répéter.

`gitpr policy init` en choisit un à partir des marqueurs du projet lui-même — `composer.json` + `artisan` pour Laravel, `package.json` + Vue pour Vue, et ainsi de suite — du plus spécifique au plus générique.

---

## 7. Adopter une politique en équipe

```bash
# Une personne, une fois : valide et installe le pack
gitpr policy install ./our-policy --yes

# Dans le dépôt : épingle et commite la décision
gitpr policy use acme/team-policy@1.0.0
git add .gitpr/policy.lock.yml && git commit -m "chore: adopt the Acme quality policy"

# Tout le monde : rien à installer si le pack est commité avec le dépôt
gitpr policy show
```

Trois façons de partager une politique, selon la dépendance à une machine que l'équipe accepte :

- **Un pack dans le dépôt** (`.gitpr/policies/<nom>/`) — versionné avec le code, aucune étape d'installation, et le lockfile enregistre le chemin relatif. Le meilleur choix pour une politique qui appartient au dépôt.
- **Un pack installé** (`~/.gitpr/policies/`) — une copie pour tous les dépôts de la machine. Chaque collègue l'installe depuis la même source ; le lockfile enregistre nom et version.
- **Un pack officiel** — lu directement depuis ce que GitPR livre. Rien à distribuer, et une nouvelle version de GitPR peut en apporter une nouvelle version.

Le cycle de vie du pack est distinct de celui de GitPR : montez la `version` dans le manifeste et la somme de contrôle change, ce qui est un diff dans le lockfile, ce qui est une revue. C'est tout l'intérêt d'épingler.
