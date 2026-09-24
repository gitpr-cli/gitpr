# Documentation Technique : Commande Split (gitpr split)

`gitpr split` analyse un arbre de travail contenant plusieurs préoccupations non liées, regroupe les hunks (tronçons de diff) par intention logique grâce à l'IA et propose un commit atomique par préoccupation — chacun accompagné d'un message généré exclusivement pour ce sous-ensemble de modifications. La lecture constitue le comportement par défaut et l'écriture est soumise à confirmation explicite (*opt-in*) : sans argument, la commande affiche le plan et propose de l'appliquer, `--dry-run` affiche le plan et s'arrête sans jamais solliciter l'utilisateur, et `--apply` demande une confirmation unique avant d'indexer et de commiter groupe par groupe.

Le problème résolu est familier à tout développeur : un correctif de bug, un refactoring et un ajustement de configuration réalisés au cours du même après-midi, désormais indissociables dans un unique `git diff`, où les seules issues seraient un fastidieux `git add -p` manuel ou un message de commit énumérant trois sujets sans rapport.

---

## 1. Vue d'Ensemble

La sous-commande constitue un ajout à la CLI et non une modification de son comportement de base : toutes les options existantes conservent leur sémantique et l'ensemble du flux est strictement local — aucun `git commit` n'est créé avant la confirmation de `--apply`, rien n'est poussé sur le dépôt distant et aucune branche n'est créée.

### 1.1 Référence de la Commande — `gitpr split`

Toutes les options de la sous-commande, telles qu'affichées par `gitpr split -h` (ou `--help`) :

```bash
gitpr split                    # affiche le plan, puis propose de l'appliquer
gitpr split --dry-run          # affiche le plan et s'arrête — ne sollicite jamais
gitpr split --apply            # affiche le plan, confirme une fois, indexe et commite
gitpr split --apply --yes      # identique, sans message de confirmation
gitpr split --max-groups 3     # au maximum trois commits atomiques
```

| Option | Description |
| --- | --- |
| **`--dry-run`** | Affiche le plan et s'arrête. Ne pose aucune question, ne modifie jamais l'index ni l'arbre de travail, quel que soit l'état de l'index |
| **`--apply`** | Exécute le plan : indexation sélective et création d'un commit par groupe, dans l'ordre défini |
| **`--yes`** | Ignore la demande de confirmation. Ne contourne jamais la validation `--check` propre à chaque groupe |
| **`--max-groups <n>`** | Limite supérieure du nombre de commits proposés par le plan, outrepassant la configuration |
| **`--provider <name>`** | Force le fournisseur d'IA pour cette exécution (`gemini`, `deepseek`, `ollama`) |

| Caractéristique | Description |
| --- | --- |
| **Source des données** | Les modifications non commitées de l'arbre de travail — indexées (*staged*), non indexées (*unstaged*) ou les deux combinées, sous la forme d'un diff unique par rapport à HEAD |
| **Appels IA** | Un appel pour regrouper les hunks, puis un appel par groupe pour rédiger son message de commit |
| **Fichiers écrits** | Aucun par défaut. `--apply` écrit dans l'index Git et crée des commits ; l'arbre de travail physique n'est jamais modifié |
| **Index** | Laissé vierge avant l'exécution. `--apply` sollicite une autorisation unique pour désindexer l'ensemble des fichiers |
| **Annulation** | Aucune commande intégrée. Le résultat consiste en commits ordinaires — `git reset`/`git reflog` sont les outils prévus |
| **Code de sortie 1** | Répertoire non Git, combinaison de `--dry-run` et `--apply`, arbre de travail vide, clé API absente ou fournisseur inaccessible, dépôt sans commits préalables, ou plan sans groupes |

### 1.1.1 Quand la Commande Sollicite l'Utilisateur

`--apply` exprimant une intention formelle, la variable `GITPR_SPLIT_REQUIRE_CONFIRMATION=false` peut légitimement désactiver la question. Sans aucun drapeau, aucune intention n'est déclarée : la question **est** alors l'essence même de la commande et est systématiquement posée — un simple `gitpr split` ne doit pas créer de commits de manière autonome simplement parce qu'une configuration désactive les confirmations. Le drapeau `--yes` matérialise l'accord explicite de l'utilisateur et désactive la demande dans les deux cas.

### 1.2 Ce Que Signifie "Atomique" Ici

Un commit atomique est un commit regroupant l'intégralité des modifications requises par une seule préoccupation, et aucune modification relevant d'une autre. L'unité élémentaire de division est le **hunk** — un bloc `@@` d'un fichier — et jamais un fragment plus petit : subdiviser un hunk en sous-hunks est hors de portée, tout comme découper une pull request déjà publiée sur une forge logicielle.

L'unité retenue est le hunk et non le fichier, car le cas essentiel à résoudre est précisément celui où un unique fichier porte deux préoccupations distinctes. Un fichier dont tous les hunks appartiennent à la même préoccupation n'est pas un cas particulier : c'est le même mécanisme aboutissant à l'évidence.

### 1.3 Hors de Portée

- Fichiers non suivis par Git (*untracked*). Ils ne contiennent pas de hunks et `git diff HEAD` ne les décrit pas ; ils ne prennent part à aucun plan. Ils sont signalés dans un avertissement et ne sont jamais ignorés silencieusement.
- Découpage interne d'un hunk.
- Annulation automatisée d'un split. Le résultat prend la forme de commits standards que Git classique permet d'annuler ; aucun rollback dédié n'a été implémenté, contrairement à `gitpr fix` où un patch appliqué ne possède pas de commit à réinitialiser.
- Réorganisation interactive, fusion et désélection de groupes. Prévu pour une version ultérieure.

---

## 2. Capture du Diff

### 2.1 Une Capture de Diff Dédiée et ses Justifications

Split n'emploie pas `get_git_diff()`, le diff exploité par l'ensemble des autres flux :

```python
SPLIT_DIFF_ARGS = ("--binary", "-M", "-U3")
```

La différence clé réside dans le paramètre `-w`, transmis par les autres flux mais proscrit pour le split. Avec `-w`, une différence constituée *uniquement* d'espaces est rendue comme du simple contexte — et la ligne de contexte émise peut ne pas correspondre byte par byte au fichier réel. Un patch conçu à partir d'un tel diff serait rejeté par `git apply` ou, pire encore, appliquerait un contenu divergent de l'arbre de travail. Cela romprait la garantie fondamentale de la commande : les fichiers sur disque à la fin sont strictement identiques, byte par byte, aux fichiers sur disque au début.

Le paramètre `-U1` est également écarté : une seule ligne de contexte offre trop peu d'ancrage pour `git apply --check`. Le paramètre `-B`, qui décompose les réécritures en suppression suivie d'ajout, est abandonné pour le même motif : il transformerait un hunk applicable en deux éléments interdépendants devant impérativement être appliqués simultanément.

Le paramètre `-M` est **conservé** et s'avère structurel. Sans détection des renommages, un renommage apparaît sous la forme d'une suppression plus un ajout, et l'ajout est assimilé à un fichier non suivi — hors de portée. Split enregistrerait alors une suppression pure de l'ancien chemin tandis que le nouveau fichier resterait abandonné hors suivi, ce qui s'apparenterait à une perte de données.

`--binary` est sans effet sur le texte brut et constitue le seul moyen de rendre applicable un fichier binaire modifié.

### 2.2 Absence d'Exclusions Intelligentes (*Smart Excludes*)

Les flux de revue standard excluent les fichiers de verrouillage (*lockfiles*), fichiers générés et binaires avant d'envoyer un diff à l'IA. Split ne filtre absolument rien.

La raison est qu'une telle exclusion n'est pas neutre ici, elle est *incorrecte*. Un lockfile et son manifeste décrivent une modification indissociable ; exclure le lockfile reviendrait à commiter le seul manifeste en laissant un arbre où les deux divergent — créant un commit intermédiaire corrompu, ce que cette commande vise précisément à empêcher. Le bruit est contenu en tronquant chaque unité dans le prompt et en plafonnant le nombre total d'unités transmises.

### 2.3 Capturer d'Abord, Désindexer à la Fin

`--apply` nécessite un index propre pour indexer sélectivement, or l'index peut déjà contenir des éléments préparés : un nouveau fichier indexé, un renommage indexé. Cet état n'est pas un accident à purger avant la lecture du diff — c'est ce qui rend ces modifications *visibles*. Un nouveau fichier n'apparaît dans `git diff HEAD` que parce que l'index le prend en compte ; le désindexer au préalable le rendrait non suivi, hors de portée, et il disparaîtrait du plan.

L'ordre est donc immuable : le diff est capturé par rapport à l'état réel de l'index, puis l'ensemble est désindexé immédiatement avant le premier `git apply --cached`. Cette méthode est fiable car chaque hunk d'un `git diff HEAD` intègre une pré-image issue de HEAD, quel que soit le contenu de l'index. Après désindexation totale, l'index coïncide avec HEAD, permettant l'application propre de ces mêmes pré-images. Il n'y a aucun recalcul de diff, aucun échec pour divergence et aucun plan ne subit de mutation silencieuse entre son affichage et son exécution.

### 2.4 Fichiers Non Suivis (*Untracked*)

Ils sont hors de portée et clairement signalés : le plan contient un avertissement listant leurs noms. "Rien à traiter" et "Il y avait des éléments et ils ont été ignorés" ne doivent jamais prêter à confusion.

---

## 3. Le Plan

### 3.1 Unités

Une unité correspond à l'une de deux natures, dont la distinction est primordiale tout au long de la chaîne :

| Unité | Description |
| --- | --- |
| **`Hunk`** | Un bloc `@@` d'un fichier, avec son contenu littéral, l'en-tête de fichier qui le précède, les coordonnées de départ et compteurs des deux côtés, et sa position dans le parcours initial |
| **`OpaqueSection`** | Une section du diff dépourvue de hunks — modification binaire, renommage pur, simple changement de permissions/mode, création de fichier vide — conservée intégrale et littérale |

Les sections opaques ne sont jamais transmises à l'IA. Aucune décision sémantique de regroupement n'est à lui demander, et une unité sur laquelle le modèle ne peut raisonner l'amènerait à forger un identifiant arbitraire. Chacune devient son propre groupe unitaire : un commit atomique pour une modification indivisible.

L'en-tête de fichier est **conservé, jamais reconstruit**. `new file mode`, `deleted file mode`, `old mode`/`new mode` et la syntaxe entre guillemets utilisée par Git pour les chemins comprenant des espaces ou des caractères non-ASCII sont impossibles à déduire d'un chemin brut ; tenter de les synthétiser générerait un patch rejeté par Git.

### 3.2 Limites de Hunk Déterminées par Comptage

Un hunk s'achève rigoureusement lorsque les compteurs de son en-tête sont épuisés — jamais à l'apparition du prochain `@@`. Au sein d'un hunk, une ligne supprimée débutant par `--- quelquechose` et une ligne ajoutée débutant par `+++ quelquechose` figurent en colonne 0 et seraient indiscernables d'un en-tête de fichier, tandis qu'une ligne de contexte comporte toujours son espace initial. Le comptage est la seule règle exacte.

Le comptage sert également de validateur pour les entrées corrompues. Une section dont les compteurs ne concordent pas avec le corps est dégradée **intégralement** en une `OpaqueSection` : jamais en une liste partielle de hunks, car la moitié d'une section illisible ne doit pas être soumise à `git apply`, et un patch appliquant partiellement un fichier est pire qu'un patch rejeté en bloc.

### 3.3 Identité de l'Unité

L'identifiant d'une unité prend la forme `0007-1a2b3c4d` — sa position ordinale de parcours, suivie des huit premiers caractères hexadécimaux d'un condensé MD5 calculé sur le chemin du fichier, l'en-tête du hunk et son corps.

Ces deux éléments sont indispensables. La position dépend exclusivement de l'ordre de parcours fixé par le texte du diff, garantissant que le même arbre de travail produit toujours les mêmes identifiants et qu'un `--dry-run` répété restitue un affichage identique. Le hash permet de distinguer deux fichiers modifiés de *manière identique* — une copie tierce vendorisée et son fichier d'origine génèrent le même en-tête et le même corps, ne différant que par leur chemin d'accès.

### 3.4 Regroupement

Le regroupement repose sur **un appel d'IA unique, sans traitement par lots**. Le traitement par lots (*batching*) serait la solution évidente pour couvrir un diff trop vaste pour un seul prompt, mais il est inadapté à cette tâche : les hunks d'une même préoccupation séparés par une frontière de lot ne pourraient jamais être réunis, aucun lot ne voyant les hunks de l'autre. Le modèle répondrait avec assurance sur la seule portion visible. Split privilégie une dégradation transparente — les unités qui ne rentrent pas demeurent non regroupées et non commitées — plutôt que de fabriquer un plan d'apparence complète mais erroné.

Chaque identifiant retourné par le modèle est validé par rapport aux unités réellement transmises. Les identifiants inconnus sont écartés avec avertissement ; les doublons sont dédupliqués ; les unités omises par le modèle rejoignent les unités non groupées. Aucune unité inventée n'intègre un groupe, et aucune unité réelle n'est silencieusement omise.

Lorsque le nombre d'unités excède la limite fixée par `GITPR_SPLIT_MAX_HUNKS`, les plus volumineuses sont conservées et le surplus est basculé dans la liste non groupée avec un avertissement indiquant leurs identifiants. La sélection par taille plutôt que par ordre séquentiel évite de pénaliser systématiquement les derniers fichiers du diff.

### 3.5 Pré-validation des Conflits

Avant d'afficher le plan, chaque groupe est testé au moyen de `git apply --cached --check` sur un index propre. En cas d'échec, toutes les unités de l'ensemble des fichiers touchés par ce groupe — issues de n'importe quel groupe et de la liste non groupée — y sont fusionnées, et le message de commit est régénéré pour le patch consolidé, évitant qu'un message décrivant un sous-groupe ne travestisse la réalité du commit.

La boucle de rattrapage est bornée et termine systématiquement. Si même en intégrant les fichiers complets l'application échoue (par exemple, problème de fins de ligne CRLF ou unité binaire), ces unités sont basculées dans `ungrouped_units` avec un avertissement. Rien n'est perdu et rien n'est appliqué à moitié.

Un conflit issu d'un véritable diff avec contexte `-U3` est plus rare qu'il n'y paraît. Git fusionne automatiquement deux modifications distantes de moins de sept lignes en un seul hunk, garantissant trois lignes de contexte préservé entre les hunks émis ; tout sous-ensemble s'applique donc sans accroc sur un index calé sur HEAD. Les deux seules causes réelles de rejet sont une incohérence de fins de ligne (*newlines*) et le chevauchement de deux hunks sur les mêmes lignes.

### 3.6 Messages de Commit

Le message associé à chaque groupe provient de `generate_pr_content()` — la fonction exploitée par le flux de commit standard, qui reçoit ici le patch exclusif du groupe plutôt que le diff global. Aucun rouage de génération n'est dupliqué : la skill `.gitpr.commit.md`, le cache de prompts MD5 et le traitement map-reduce pour les volumineux patches sont réutilisés tels quels.

Un patch regroupant trois des neuf hunks d'un fichier est constitué en reconstruisant l'en-tête du fichier et ces trois hunks spécifiques, et non en découpant le texte du diff d'origine. Un découpage brut conserverait des décalages (*offsets*) valables pour le fichier complet mais erronés pour l'extrait réduit.

---

## 4. Application du Plan

### 4.1 La Séquence

Pour chaque groupe, selon l'ordre établi par le plan :

1. Vérifier la propreté de l'index — aucun fichier préparé en stage. Vérifié avant chaque groupe afin d'éviter que des résidus d'un groupe précédent ne polluent le commit suivant.
2. Reconstruire le patch du groupe et exécuter `git apply --cached --check`, puis `git apply --cached`. Les deux étapes transitent par `patch_applier` (identique à `gitpr fix`), le patch étant transmis à Git sous la forme d'un **flux d'octets sur stdin** — rempart contre la conversion automatique des fins de ligne sous Windows (`\n` vers `\r\n`), qui provoquerait le rejet silencieux du patch.
3. Vérifier que le contenu parvenu à l'index correspond fidèlement au groupe : la liste des chemins issus de `git diff --cached --name-only -M` doit coïncider avec l'ensemble des fichiers du groupe, et les compteurs `(ajoutées, supprimées)` par fichier obtenus par `--numstat` doivent égaler les lignes `+` et `-` des unités. L'usage de numstat prévaut sur les en-têtes de hunks, car les lignes indiquées dans un en-tête se décalent lors de l'application de commits adjacents préalables, ce qui générerait de fausses alertes sur un plan parfaitement valide.
4. Créer le commit avec le message généré pour le groupe.
5. Vérifier à nouveau la propreté de l'index.

L'arbre de travail physique n'est jamais altéré. Chaque fichier sur disque conserve l'ensemble de ses modifications, indexées ou non ; à l'issue du processus, `git status` indique un arbre propre et les commits enregistrent le travail accompli.

### 4.2 Les Éléments Restants

Les unités figurant dans `ungrouped_units` restent non indexées et non commitées au terme de l'exécution. C'est l'issue logique pour un hunk non classé par le modèle, un groupe impossible à indexer ou une unité écartée pour respecter le quota de tokens. Elles sont récapitulées dans le rapport final ; l'utilisateur peut les commiter manuellement ou relancer `gitpr split` sur les modifications résiduelles.

### 4.3 En Cas d'Échec en Cours de Séquence

**Il n'y a aucun rollback automatique.** Split produit des commits classiques dont l'annulation relève de `git reset`, outil standard à disposition de l'utilisateur. La commande garantit en revanche un arrêt propre accompagné d'un diagnostic clair :

| Échec | État consécutif de l'index |
| --- | --- |
| Lors de l'indexation d'un groupe (*staging*) | Tout ce qui a été indexé pour ce groupe est désindexé, et le rapport indique l'interruption à ce niveau |
| Lors de la création du commit du groupe | Le groupe demeure indexé dans le stage, et le rapport le signale explicitement — plutôt que de masquer les unités en cours |
| Commits 1..N-1 | Intacts. Il s'agit de commits réels et pérennes |

---

## 5. Modèle de Skill (*Skill Template*)

Split **ne dispose d'aucun modèle de skill et n'en consulte aucun**.

Un fichier `.gitpr.split.md` semblerait une structure intuitive, mais s'avérerait inadapté. `get_skill_context()` attribue par défaut la skill de *review* (`DEFAULT_SKILL_TYPE = "review"`) à toute action non répertoriée ; un appel survenant avant l'enregistrement global du type doterait ainsi le prompt de regroupement d'une personnalité de code review. L'enregistrer formellement exigerait une entrée supplémentaire dans `SKILL_FILES_BY_TYPE`, un nouvel intitulé validé par des tests d'ordonnancement dans l'interface de configuration, une ressource additionnelle sur le serveur MCP et des modèles traduits pour chaque langue : une surface disproportionnée pour un prompt obéissant à un schéma de réponse rigide qui ne doit pas être édité manuellement.

L'instruction de regroupement est par conséquent directement intégrée dans `hunk_grouper.py`, au plus près du code chargé d'en analyser la réponse.

---

## 6. Variables d'Environnement

| Variable | Valeur par Défaut | Description |
| --- | --- | --- |
| `GITPR_SPLIT_MAX_GROUPS` | `5` | Limite supérieure du nombre de commits atomiques proposés par un plan |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | `true` | Affiche le plan et sollicite une confirmation avant la création du premier commit |
| `GITPR_SPLIT_MAX_HUNKS` | `50` | Limite supérieure du nombre d'unités transmises à l'appel de regroupement |

Ces trois variables sont paramétrables dans l'écran de configuration, sous la rubrique **Split**.

Toute valeur négative, nulle ou invalide est automatiquement remplacée par la valeur par défaut : fixer une limite à zéro transformerait silencieusement l'ordre "découper ces modifications" en "ne rien découper", au lieu de générer une erreur explicite.
