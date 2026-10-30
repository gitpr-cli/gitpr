# Documentation Technique : Écran de Configuration Interactif (`gitpr config`)

GitPR se configure via `~/.gitpr/.env`, un fichier dotenv d'environ cinquante variables. Jusqu'ici, en modifier une exigeait de connaître son nom exact, d'ouvrir le fichier à la main et de deviner si la valeur est `true`, `1` ou `yes` — et une valeur que le lecteur ne comprend pas est avalée en silence, donc une faute de frappe ne se manifeste jamais comme une erreur.

`gitpr config` ouvre un écran master-detail sur ce même fichier : les catégories à gauche, les réglages de celle qui est sélectionnée à droite, modifiés sur place. C'est une fine couche au-dessus du fichier que vous avez déjà — pas une seconde source de configuration.

```bash
gitpr config
```

---

## 1. L'Écran

```text
┌ Header ──────────────────────────────────────────────┐
│ Configuration      [/ rechercher…] ● 2 non enreg.    │
├──────────────┬───────────────────────────────────────┤
│ Général      │  Langue de l'interface                │
│ Fournisseurs │  [ fr_fr            ▾ ]                 │
│ Pull Request │                                       │
│ …            │  Co-auteur                            │
│              │  [ ●] activé                          │
├──────────────┴───────────────────────────────────────┤
│ F1 Aide · F2 Enregistrer · ^R Rétablir · / Rechercher│
└──────────────────────────────────────────────────────┘
```

| Touche | Action |
| --- | --- |
| `F1` | Aide — la liste des raccourcis et la façon dont les valeurs sont lues |
| `F2` | Valide et enregistre les modifications en attente |
| `Ctrl+R` | Rétablit la valeur par défaut du champ sélectionné (supprime la ligne) |
| `/` | Recherche un nom de variable ou un libellé dans toutes les catégories |
| `Échap` | Quitte — ou efface d'abord la recherche ; demande avant d'abandonner |

### 1.1 Catégories

Le menu latéral reflète les commandes et les flags de la CLI, donc le réglage que vous cherchez se trouve là où se trouve la fonctionnalité que vous utilisez. La première entrée est toujours **Général** :

| Catégorie | Contient |
| --- | --- |
| **Général** | Langue de l'interface, ligne de co-auteur, journal général |
| **Fournisseurs d'IA** | Moteur par défaut, délai de l'IA, les deux clés d'API, et les modèles de chaque fournisseur — sous une sous-section par fournisseur, affichée une à la fois |
| **Pull Request** | `OUTPUT_FILE_NAME`, branche de base, auto commit/stage/merge, ignorer le linter, journal de publication, suggestion de relecteurs |
| **Projet** | Le fichier versionné du projet : son chemin, la branche de base cible de la PR et la branche qui sera réellement utilisée (§1.8) |
| **Révision de Code** | `OUTPUT_FILE_NAME_REVIEW`, `_FULLREVIEW`, `_FILEREVIEW` |
| **Issue** | `OUTPUT_FILE_NAME_ISSUE` |
| **Blame** | `OUTPUT_FILE_NAME_BLAME` |
| **Linter** | `OUTPUT_FILE_NAME_LINTER`, `GITPR_LINTER_TIMEOUT` |
| **Release** | Chemin du changelog, résumé par IA, incrément automatique, brouillon par défaut, `OUTPUT_FILE_NAME_RELEASE` |
| **SCM / Forge** | Fournisseur, token de CI/CD, token de la forge, URL de base ; sous-sections **GitHub**, **Bitbucket** et **Azure DevOps** avec ce dont chaque forge a besoin |
| **Filtres de Diff** | Interrupteur des smart excludes et les deux chemins de liste de filtres |
| **Skills** | Les sept fichiers de skill de ce projet — une entrée par skill, modifiés sur place (§1.7) |
| **Avancé** | Trois sous-sections — **Spinner**, **Git Hooks**, **Téléchargements** — masquées jusqu'à l'activation de **Afficher les options avancées** |
| **Inconnues** | Clés du fichier que le schema ne déclare pas — n'apparaît que lorsqu'elles existent |

Chacune des treize catégories a un lien vers sa propre documentation technique (§1.5).

### 1.2 Contrôles

Chaque champ reçoit le contrôle que son type mérite, afin qu'une valeur invalide soit difficile à produire dès le départ :

| Type | Contrôle |
| --- | --- |
| Booléen | Switch |
| Énumération | Select |
| Entier | Champ texte, validé |
| Modèle de nom de fichier | Champ texte, validé contre les placeholders |
| Chemin, texte libre | Champ texte |
| Secret | Champ masqué |
| Liste de mots | Champ en lecture seule qui défile de lui-même, avec le nombre d'entrées au-dessus et un bouton de téléchargement (§1.4) |

### 1.3 Filtré par la Valeur Sélectionnée

Deux réglages décident quels autres réglages sont à l'écran, et le panneau suit la sélection **immédiatement** — avant tout enregistrement :

| Quand vous sélectionnez | Vous voyez |
| --- | --- |
| Un **Fournisseur par défaut** | Uniquement les modèles de ce fournisseur. Sans rien de sélectionné, aucune section de fournisseur n'est affichée du tout |
| Un **Fournisseur de la forge** | Uniquement la sous-section de cette forge, plus les champs que toutes les forges partagent |

La recherche ignore le filtre à dessein : chercher `deepseek` avec Gemini sélectionné trouve quand même les modèles DeepSeek, ce qui vous permet de pré-remplir un fournisseur vers lequel vous allez basculer. Un champ masqué avec une modification en attente est quand même enregistré — la visibilité est une vue, pas une permission.

### 1.4 Boutons de Téléchargement

Quatre listes sont servies depuis le dépôt GitPR et actualisées lorsque leur marqueur de version change. **📥 Forcer le téléchargement** à côté d'un marqueur de version le retélécharge à la demande, et **📥 Télécharger la liste de mots** fait de même pour les mots du spinner. C'est la sortie de secours manuelle pour le cas que la vérification automatique ne peut pas voir : la liste est présente, à jour, et ce n'est toujours pas celle que vous voulez.

Le bouton rapporte le résultat honnêtement, car un téléchargement peut échouer et retomber sur la copie déjà présente sur le disque sans qu'aucun signe extérieur ne permette de distinguer les deux :

| Retour | Signification |
| --- | --- |
| `✔ v0.0.24` et *"{name} est à jour ({version})."* | Le fichier porte désormais la version actuelle — soit fraîchement téléchargée, soit une copie qui était déjà à jour |
| `✖ non mis à jour` et *"Téléchargement de {name} impossible. La copie précédente reste utilisée."* | Le téléchargement a échoué. Rien n'a été perdu : la copie précédente est intacte et toujours utilisée |
| *"L'anglais n'a pas besoin de pack de traduction — il n'y a rien à télécharger."* | Le pack de traduction n'a pas d'édition anglaise à récupérer, puisque l'anglais est intégré |

Le verdict vient d'une relecture de `~/.gitpr/.env` après le téléchargement, jamais de `os.getenv()` : `load_dotenv()` s'exécute avec `override=False`, donc le processus détient encore la valeur avec laquelle il a démarré.

### 1.5 Lien vers la Documentation

**📚 Documentation** en haut du panneau de droite ouvre la documentation technique de la catégorie que vous regardez, et l'URL est imprimée à côté du bouton pour que vous puissiez la lire ou la copier d'abord.

| Catégorie | Document |
| --- | --- |
| Général | `config-tui.md` |
| Fournisseurs d'IA | `providers-ia.md` |
| Pull Request | `pull-request-publication.md` |
| Projet | `pull-request-publication.md` |
| Révision de Code | `code-review-ia.md` |
| Issue | `gitpr-issue-option.md` |
| Blame | `blame-arqueologo.md` |
| Linter | `linter-regras-customizadas.md` |
| Release | `release-notes.md` |
| SCM / Forge | `scm-multiforge.md` |
| Filtres de Diff | `smart-excludes.md` |
| Skills | `skill-template.md` |
| Avancé | `version-markers.md` |

Le lien suit la langue de l'interface (`?lang=fr_fr`), et la ligne disparaît dans la vue de recherche et dans **Inconnues**, qui n'est pas une catégorie que GitPR possède.

### 1.6 Le Basculement des Options Avancées

**Afficher les options avancées** dans la barre d'outils révèle la catégorie `Avancé` et tout champ marqué comme interne. Ce sont des marqueurs de version que GitPR tient lui-même lors du téléchargement des traductions, des presets de linter, des mots du spinner et des listes de filtres ; ils sont affichés par transparence, pas pour être modifiés. Le basculement est désactivé à chaque ouverture.

Deux de ces champs ne sont pas des marqueurs et méritent d'être connus :

- **Langue des hooks** (`SCRIPTS_LANG`) — la langue dans laquelle les Git Hooks sont installés. Vide signifie « suivre la langue de l'interface », ce que la plupart des utilisateurs souhaitent ; en choisir une installe les hooks dans cette langue à l'exécution suivante. **Langue des hooks installés** juste à côté est en lecture seule et enregistre ce qui se trouve réellement sur le disque, de sorte que les deux ne soient jamais confondus.
- **Mots du spinner** — la liste elle-même, en lecture seule, dans le champ décrit au §1.2.

### 1.7 La Section Skills

Partout ailleurs, l'écran modifie `~/.gitpr/.env`. **Skills** est la seule section qui ne le fait pas : elle modifie les fichiers de skill du projet lui-même — les instructions IA lues depuis `./.gitpr/skill/` ([Système de Skills et Templates](skill-template.fr_fr.md)).

La liste contient une entrée par skill prise en charge par GitPR : **Commit**, **Pull Request**, **Code Review**, **File Review**, **Issue**, **Blame**, **Release**. C'est la liste des skills que les commandes chargent, et non un miroir du dossier — un fichier dans `.gitpr/skill/` qu'aucune commande ne lit n'est pas proposé ici.

| L'entrée affiche | Signification |
| --- | --- |
| rien | Le fichier est présent et accessible en écriture — modifiez-le dans le champ à droite et appuyez sur `F2` |
| **● modifié** | Une de vos modifications n'est pas encore enregistrée |
| **absent de ce projet** | Le fichier n'existe pas. Le champ affiche *"Ce projet n'a pas encore le fichier {name}."* et l'éditeur est désactivé — un champ vide se lirait comme « ce skill est vide », soit le contraire de la vérité |
| **lecture seule** | Le fichier existe mais ne peut pas être écrit. Il est affiché, verrouillé, et n'a rien à enregistrer |

**📥 Télécharger le template** apparaît pour un skill absent et récupère le template publié pour votre langue d'interface, comme les boutons de téléchargement du §1.4. Quand même cela ne peut pas être écrit — un dossier `.gitpr/skill/` en lecture seule — le bouton reste désactivé avec la raison à côté.

`F2` enregistre les champs du `.env` **et** les fichiers de skill en une seule passe, et le compteur de modifications en attente couvre les deux. Dans le panneau, `Ctrl+R` abandonne la modification et remet le texte du disque — ce qu'un fichier a de plus proche d'une valeur par défaut — et `Esc` demande confirmation avant de l'abandonner, comme partout ailleurs.

Chaque fichier conserve ses fins de ligne d'origine : un fichier `CRLF` reste en `CRLF` et votre diff n'affiche que les lignes que vous avez modifiées.

### 1.8 La Section Projet

Le second stockage. Contrairement à toutes les autres catégories, ces valeurs ne viennent pas de `~/.gitpr/.env` — elles vivent dans `.gitpr/conf/gitpr.config.yml`, à la racine du dépôt, et GitPR versionne ce fichier avec le projet pour que toute l'équipe cible la même branche de base ([Publication de Pull Request](pull-request-publication.fr_fr.md)).

| Ligne | Modifiable | Affiche |
| --- | --- | --- |
| **Fichier de Configuration** | non | Le chemin absolu du fichier, qui est aussi ce qui est écrit |
| **Branche de Base Cible de la PR** | oui | La valeur du fichier, choisie parmi les branches locales du dépôt et celles qui existent sur `origin` — sauf la branche extraite. *(automatique)* supprime la clé et le dépôt retombe dans la chaîne de priorité ; une branche que le checkout ne possède pas encore reste visible |
| **Branche de Base Effective** | non | La branche qu'une pull request ciblerait maintenant, et d'où elle vient : `--base`, le fichier du projet, `PR_DEFAULT_BASE` ou `origin/HEAD` |

Le fichier est créé à la première invocation dans un dépôt (et par `--install`), prérempli avec `PR_DEFAULT_BASE` lorsqu'il est défini et `main` sinon. Le seed n'écrase jamais un fichier existant. Si le fichier ne peut pas être lu — YAML cassé, une valeur qui n'est pas du texte — l'écran affiche le fallback qui serait utilisé et l'enregistrement *refuse d'écraser le fichier*, afin qu'un contenu écrit à la main ne soit jamais détruit par un `F2` accidentel.

`F2` écrit cette section dans le YAML et le reste de l'écran dans le `.env`, dans le même enregistrement. Une branche qui n'existe pas sur `origin` est **enregistrée avec un avertissement** : elle est peut-être sur le point d'être poussée. La CLI et le serveur MCP échouent sur la même référence absente, ce dont l'avertissement avertit.

Une pull request ne peut pas cibler la branche dont elle part : la branche sur laquelle vous êtes maintenant n'est donc pas proposée dans le sélecteur, et la choisir est refusé à l'enregistrement. Un fichier qui la nomme déjà n'est pas une erreur tant que vous ne modifiez autre chose — être sur la branche cible est un état normal d'un checkout — mais la valeur s'affiche comme **{branch} (branche actuelle)** pour rendre le problème visible, et la publication suivante demande un remplacement.

---

## 2. Comment les Valeurs Sont Lues

**L'écran affiche ce qui est dans le fichier, pas ce que le processus utilise.** La différence compte, car `load_dotenv()` s'exécute avec `override=False` partout dans GitPR : quand une variable est aussi exportée dans votre shell, l'environnement l'emporte et le fichier est ignoré à l'exécution.

Un champ dans cette situation est signalé par **⚠ dans l'environnement**, et la valeur affichée reste celle du fichier. La modifier est permis — elle ne prendra simplement pas effet tant que la variable n'est pas retirée de l'environnement. C'est délibéré : sans ce signal vous verriez une valeur qui, en silence, n'est pas celle qui est utilisée, ce qui est l'échec le plus déroutant que ce fichier puisse produire.

Les valeurs sont lues avec un parser qui ne regarde que le fichier, jamais avec `os.getenv()`, donc rien du processus courant ne fuit vers l'écran.

---

## 3. Édition et Enregistrement

Rien n'est écrit avant que vous appuyiez sur `F2`. Pendant l'édition, `F2` affiche un compteur de modifications en attente et `Échap` demande confirmation avant de quitter :

- **Enregistrer** n'écrit que les champs que vous avez réellement modifiés, donc les lignes sans rapport conservent leurs commentaires et leur position dans le fichier.
- **Fichiers de skill** sont écrits par le même enregistrement : un `F2` couvre les champs `.env` en attente et les skills modifiés (§1.7). Un skill qui ne peut pas être écrit est signalé par son nom et garde sa modification en attente — les autres fichiers sont enregistrés quand même.
- **Les champs du projet** vont dans `.gitpr/conf/gitpr.config.yml`, pas dans le `.env` (§1.8). Le fichier du projet est écrit en premier : s'il échoue, rien n'est écrit nulle part et toutes les modifications restent en attente.
- **`Ctrl+R`** sur un champ **ne** réécrit **pas** la valeur par défaut intégrée — il marque la ligne pour **suppression**, afin que la valeur revienne à ce que le code définit par défaut. Le champ affiche `— sera supprimé —` et un nouveau `Ctrl+R` annule la marque. C'est la réinitialisation honnête : écrire la valeur par défaut actuelle la figerait dans le fichier et interromprait le suivi des changements futurs.
- **Vider un champ** efface la surcharge.
- Après un enregistrement réussi, l'écran reste ouvert, relit le fichier et indique combien de paramètres ont été enregistrés.

### 3.1 Validation

`F2` valide avant d'écrire quoi que ce soit. Un champ qui échoue reçoit une bordure rouge et un message en ligne, rien n'est enregistré, et l'écran saute au premier champ fautif — en changeant de catégorie et en activant **Afficher les options avancées** si c'est là qu'il se trouve.

| Règle | Pourquoi |
| --- | --- |
| Uniquement `true` / `false`, plus `1`/`0`, `yes`/`no`, `y`/`n`, `off` | GitPR a deux lecteurs de booléens qui divergent en dehors de cet ensemble. `on` semble symétrique de `off`, mais l'un le lit **false** et l'autre **true** |
| Les entiers doivent être supérieurs à zéro | Un délai illisible est remplacé en silence par la valeur par défaut, donc une faute de frappe ne se manifeste jamais comme une erreur |
| Les énumérations doivent être l'un des choix déclarés | Un nom de fournisseur inconnu n'est pas rejeté au démarrage, il ne fonctionne simplement pas |
| Les modèles doivent utiliser des placeholders connus et conserver `{datetime}` | Un placeholder inconnu provoque un `KeyError` à la commande suivante ; sans `{datetime}` chaque exécution résout vers le même nom de fichier et écrase le rapport précédent |
| La branche de base du projet ne peut pas être la branche courante | Une Pull Request ne peut pas se cibler elle-même : la forge la refuse, et GitPR la refuse plus tôt avec la même règle (§1.8) |

### 3.2 Validation des Identifiants

Un secret (clé d'API, token de forge) est validé auprès de son fournisseur avant d'être enregistré, car un identifiant erroné ne se découvre qu'ensuite, au milieu d'une vraie commande. La validation s'exécute en arrière-plan pour que l'écran ne se fige jamais, et le résultat décide :

| Résultat | Comportement |
| --- | --- |
| Accepté | Enregistré |
| Refusé (HTTP 401/403, ou une réponse « invalid API key ») | **Bloque** — l'identifiant est faux et le stocker n'aide personne |
| Panne réseau, délai dépassé, fournisseur injoignable | **Enregistré avec un avertissement** — une clé correcte saisie derrière un proxy ne peut pas être refusée |

Seuls les secrets que vous avez modifiés durant cette session sont revalidés. Une clé déjà présente dans le fichier et laissée intacte n'est pas sondée à chaque enregistrement.

Les valeurs de secret **ne sont jamais réaffichées**. Le champ reste vide quand rien n'est stocké, et affiche un placeholder fixe (`•••••••• (défini — saisissez pour remplacer)`) quand une valeur existe — le même masque quel que soit le secret, car la valeur réelle n'est jamais lue vers l'écran. Elle n'entre dans l'enregistrement que si vous y saisissez quelque chose. Les secrets sont chiffrés au repos avec la clé Fernet locale dans `~/.gitpr/secret.key` ; l'écran chiffre au moment d'écrire et ne déchiffre jamais pour remplir un champ.

---

## 4. Recherche et Clés Hors du Schema

Saisir dans la zone de recherche filtre par nom de variable **et** par libellé, dans toutes les catégories à la fois — `timeout` trouve les délais de l'IA et du linter sans que vous sachiez dans quelle catégorie ils se trouvent. Tant qu'une recherche est active, la zone principale affiche les résultats sous forme de liste plate, avec un compteur, au lieu des champs de la catégorie sélectionnée ; le menu latéral reste où il est. `Échap` efface la recherche — et rend le focus au menu latéral — avant de pouvoir quitter l'écran.

Les variables présentes dans le fichier que GitPR ne déclare pas tombent dans une catégorie **Inconnues** qui n'apparaît que lorsque de telles clés existent. Elles sont en lecture seule : l'écran n'écrit jamais une clé qui ne lui appartient pas. En modifier une signifie éditer le fichier à la main.

---

## 5. Délibérément Non Éditables

Ces clés ne reçoivent aucun champ éditable. L'écran ne masque jamais une clé présente dans votre fichier — il refuse seulement d'**écrire** dans une clé qui ne lui appartient pas — donc toutes sauf la dernière apparaissent encore, en lecture seule, sous **Inconnues** (voir §4).

| Variable | Pourquoi |
| --- | --- |
| `GITPR_SCM_TOKEN` | Le token brut de CI/CD prime sur le token chiffré et est stocké en clair. Il a une ligne dans **SCM / Forge** — en lecture seule et jamais affichée — pointant vers `gitpr --init`, qui est la seule chose qui devrait l'écrire ; un champ modifiable inviterait à masquer le token que vous y avez configuré |
| `PR_AUTO_PUBLISH` | Un vestige d'avant que la publication devienne le flux par défaut. Lue nulle part : ce qui l'a remplacée est la flag `--no-edit`. Une installation ancienne peut encore porter sa ligne dans le `.env`, et c'est pourquoi elle apparaît sous **Inconnues** |
| `CI`, `GITHUB_ACTIONS` | Marqueurs d'environnement du processus, jamais écrits dans ce fichier, donc ils n'apparaissent jamais |

---

## 6. Pour les Développeurs

L'écran est construit à partir d'un schema déclaratif, donc ajouter un réglage est un changement de données et non d'interface.

| Fichier | Rôle |
| --- | --- |
| `src/config_schema.py` | Données pures : `ConfigField`, `Category`, `Group`, `CATEGORIES`, `GROUPS`, `FIELDS` (83 champs), plus `fields_of()`, `validate_field_value()` et les aides de recherche. Source unique de vérité pour le menu, les widgets, les valeurs par défaut, les sous-sections, la visibilité et la validation |
| `src/project_config.py` | Le stockage du projet : résolution du chemin, le seed, lecture/écriture YAML et le résolveur de la base de la PR (§1.8). Maintenu hors de `core.py` pour que l'écran, le serveur MCP et `--install` l'utilisent sans charger les SDK d'IA — `core.get_base_branch()` est importé dans le résolveur |
| `src/doc_links.py` | `doc_url(filename)` — l'URL de base de la documentation et la règle du `?lang=`. Séparé de `core.py` parce que l'écran ne peut pas importer `src.core`, qui charge les SDK d'IA à chaque ouverture |
| `src/ui/config_app.py` | `ConfigApp` plus les modales d'aide et de confirmation. Layout master-detail, dirty state, recherche, le basculement des options avancées, le filtre de visibilité, les workers de téléchargement, le panneau Skills (§1.7) et le pipeline d'enregistrement |
| `src/config.py` | Quatre fonctions ajoutées : `read_env_file_values()`, `save_config_values()`, `remove_config_value()`, `validate_ai_key()`. Il contient aussi le registre des skills (`SKILL_FILES_BY_TYPE`, `SKILL_TYPES`) et les aides de fichier (`read_skill_file()`, `write_skill_file()`, `skill_file_status()`) que lisent à la fois `get_skill_context()` et la section Skills (§1.7) |
| `src/main.py` | La sous-commande `config` — sans `setup_environment()`, pour que rien ne puisse demander une saisie sur stdin dans l'application plein écran |

Trois attributs d'un `ConfigField` portent la mise en page : `group` place le champ sous un sous-titre, `show_if` le masque à moins qu'un autre champ ne porte l'une des valeurs listées, et `action` attache un bouton de téléchargement. `version_source` indique quelle constante afficher lorsqu'un marqueur de version n'est pas encore dans le fichier — un `LINTER_PRESETS_VERSION` vide affiche la version livrée dans le code au lieu d'un champ vide.

**Ajouter un réglage :** déclarez un `ConfigField` avec un libellé et une description littéraux `__("…")`, ajoutez la clé à `DEFAULT_CONFIG` s'il s'agit d'une nouvelle valeur par défaut de semis, et traduisez les nouvelles clés dans les six `langs/*.json`. `tests/test_config_schema.py` échoue tant que le schema et `DEFAULT_CONFIG` ne concordent pas — et tant qu'un nouveau `group`, `show_if` ou `action` ne pointe pas vers quelque chose qui existe — et `tests/test_i18n.py` échoue tant que chaque fichier de langue ne porte pas les nouvelles clés.

**Modèle d'état :** les modifications en attente vivent dans un dictionnaire indexé par le nom de la variable, pas dans les widgets. L'ensemble des lignes visibles change selon la navigation ou la recherche, et une valeur relue depuis un contrôle masqué serait fragile — c'est pourquoi `F2` est indépendant de ce qui est affiché à cet instant.

**Les écritures sur disque** passent par `set_key()`/`unset_key()` de `python-dotenv`, qui écrivent un fichier temporaire puis le renomment, en préservant les commentaires et l'ordre. L'écran ne réécrit jamais le fichier en entier.

Vocabulaire d'architecture : [Glossaire de la Configuration](plans/glossary-config-tui.md).

> **Note :** `gitpr -h config` ouvre l'écran et ignore le `-h`, car le callback racine retourne immédiatement pour toute sous-commande. Utilisez `gitpr config -h` pour le texte d'aide.
