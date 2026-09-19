# Documentation Technique : Visite Guidée (gitpr demo)

`gitpr demo` parcourt les trois choses que GitPR fait d'une modification — le message de commit, la revue de code et la description de pull request — sur un diff d'exemple embarqué dans le paquet. Rien n'est généré et rien n'est envoyé où que ce soit : les réponses ont été enregistrées une fois et sont rejouées, donc la visite fonctionne **sans clé d'API, sans dépôt Git et sans connexion**.

Elle existe pour raccourcir la distance entre le `pip install gitpr-cli` et le « je comprends à quoi sert cet outil ». Toute autre fonctionnalité exige de la configuration avant de vous montrer quoi que ce soit : un fournisseur, une clé, un jeton de forge, un dépôt avec un diff dedans. La visite n'en a besoin d'aucun, ce qui en fait la seule commande qui fonctionne sur une machine où GitPR n'a jamais tourné.

---

## 1. Vue d'ensemble

La visite est un sous-commande, pas un flag : `gitpr demo` n'atteint jamais la configuration de la clé d'API, le blocage de mise à jour PyPI ni la vérification de connexion, parce que rien en aval n'a besoin d'un environnement configuré.

### 1.1 Référence de la Commande — `gitpr demo`

Toutes les options du sous-commande, telles que les affiche `gitpr demo -h` (ou `--help`) :

```bash
gitpr demo                                  # le scénario par défaut, à l'écran
gitpr demo --scenario security-issue        # l'autre exemple fourni
gitpr demo --no-tui                         # texte brut, sans écran
gitpr demo --lang fr_fr --no-tui            # la visite en français
```

| Option | Description |
| --- | --- |
| **`--scenario <name>`** | Quel exemple parcourir. Sans lui, le premier scénario enregistré est utilisé. Un nom inconnu sort avec le code 1 et liste ceux qui existent |
| **`--lang <code>`** | Langue de l'interface pour cette exécution (`en_us`, `pt_br`, `pt_pt`, `es_es`, `fr_fr`). Remplace `GITPR_LANG` pour cette exécution et n'est pas persisté |
| **`--no-tui`** | Affiche la visite en texte brut au lieu d'ouvrir l'écran. Pour la CI, les terminaux limités et les enregistrements |
| **`-h` / `--help`** | L'aide plus le lien de la documentation dans la langue courante |

| Caractéristique | Description |
| --- | --- |
| **Contenu** | Réponses enregistrées une fois par GitPR et embarquées comme code dans le paquet — rejouées, jamais régénérées |
| **Fournisseur d'IA** | Aucun n'est instancié et aucune clé n'est lue. Le pipeline s'exécute réellement, avec l'appel au modèle remplacé |
| **Réseau** | Aucun. Aucune requête HTTPS, aucun DNS, aucun socket |
| **Git** | Aucun. Aucun dépôt n'est nécessaire ; la visite ne lance pas une seule commande `git` qui lui soit propre |
| **Fichiers écrits** | Aucun. Aucun `.md`, aucun `.txt`, aucune entrée de cache, aucune métrique |
| **Écran** | Une app Textual, ou du texte brut avec `--no-tui` (contenu identique dans les deux cas) |
| **Code de sortie 1** | Un nom de `--scenario` inconnu |

---

## 2. Les Six Étapes

La visite est linéaire : six écrans, dans cet ordre, chacun avec un titre, une ligne de texte de cadrage et l'artefact dont il parle.

| # | Étape | Ce qu'elle montre |
| --- | --- | --- |
| 1 | **Bienvenue dans GitPR** | Ce que fait l'outil et la promesse de la visite : un exemple enregistré, sans clé, sans dépôt, sans connexion |
| 2 | **L'exemple de modification** | Le diff unifié — du code, en anglais, dans toutes les langues |
| 3 | **Message de commit** | Ce que `gitpr -c` écrit pour ce diff : un sujet au format Conventional Commits plus le raisonnement qui n'y tient pas |
| 4 | **Revue de code** | Ce que `gitpr -r` rapporte, composé exactement comme la revue locale : les alertes du linter d'abord, la revue en dessous |
| 5 | **Description de la pull request** | Ce que `gitpr` écrit pour la branche : ce qui a changé, pourquoi, et ce que le relecteur doit regarder |
| 6 | **Étapes suivantes** | `gitpr --init` pour la vraie chose, le lien de la documentation et comment relancer la visite |

### 2.1 Touches

| Touche | Action |
| --- | --- |
| `n`, `→`, `Entrée` | Étape suivante. Sur la dernière étape, quitte la visite |
| `p`, `←` | Étape précédente. Sur la première étape, ne fait rien (un bip, pas une sortie) |
| `F1` | Fenêtre d'aide : les touches et ce sur quoi la visite tourne |
| `Échap` | Quitte la visite, depuis n'importe quelle étape — et depuis l'intérieur de la fenêtre d'aide |

Revenir est gratuit : les trois artefacts sont générés une fois, avant le premier écran, donc revenir ne régénère jamais rien et la visite ne peut pas montrer une réponse différente la seconde fois. Une étape compte comme vue quand vous la quittez vers l'avant, donc relire une précédente ne la décoche pas.

---

## 3. D'où Viennent les Réponses

La visite n'est pas un diaporama d'écrans figés : elle appelle le même `generate_pr_content()` que `gitpr -c`, `gitpr -r` et `gitpr`, et le même `compose_review_content()` qui rend la revue locale. Seul l'appel au modèle est remplacé — par un fake qui renvoie la réponse enregistrée du scénario — et c'est ce qui empêche la visite de s'éloigner de ce qu'affichent les commandes réelles.

Tout ce que le pipeline irait chercher à l'extérieur est neutralisé pendant la visite :

| Remplacé | Pourquoi |
| --- | --- |
| **`call_ai_model`** | La source des données : un fake qui rejoue la réponse enregistrée et journalise l'appel |
| **`get_cached_response` / `save_cached_response`** | Une lecture du cache rejouerait *votre* ancienne revue d'une vraie branche, et une écriture classerait la réponse de la démo sous un vrai prompt — la visite ne lit ni n'écrit rien |
| **`log_command_metric` / `log_local_metric`** | La télémétrie écrit dans `~/.gitpr/metrics/` sans interrupteur, et une visite n'est pas un usage d'une fonctionnalité |
| **`get_api_key` / `get_api_model`** | Le pipeline de PR abandonne *avant* d'appeler le modèle quand la clé ou le modèle manque, il faut donc répondre à cet appel |
| **`get_skill_context`** | Déterminisme : un fichier local dans `.gitpr/skill/` changerait ce que montre la visite, et imprimerait sa ligne « template chargé » au milieu |

Le diff lui-même est du code du dépôt et reste en anglais dans toutes les langues — traduire `Rule::unique()` déformerait ce que l'outil lit. La prose autour, les revues et les descriptions de PR sont traduites.

Un scénario qui ne parvient pas à produire l'un des trois artefacts lève une erreur au lieu de rendre un écran vide : une visite vide donne l'impression que l'outil n'a rien trouvé, alors que la cause réelle est que le pipeline n'a jamais atteint le fournisseur.

---

## 4. Les Scénarios Fournis

| Scénario | Stack | La modification |
| --- | --- | --- |
| **`laravel-bug-fix`** (par défaut) | PHP / Laravel | Une mise à jour de profil qui rejette la propre adresse e-mail de l'utilisateur — `unique:users,email` sans `ignore()`, où le correctif ajoute la règle d'ignore |
| **`security-issue`** | TypeScript / Express | Un IDOR dans le téléchargement de factures : la ligne est résolue par la seule clé primaire, donc tout utilisateur authentifié télécharge la facture d'une autre organisation |

Chacun est un module Python dans `src/demo/scenarios/` qui expose trois noms :

```python
NAME = "laravel-bug-fix"   # la valeur que reçoit --scenario
DIFF = """..."""           # le diff unifié — du code, jamais traduit
TEXT = {"en": {...}, "pt_br": {...}, ...}   # la prose et les réponses enregistrées
```

Les scénarios sont des modules et non des fichiers de données JSON parce que le paquet n'embarque aucun fichier qui ne soit pas `.py` : `pyproject.toml` collecte `src` et `src.*` via `packages.find` et n'a pas de `package_data`, donc un fichier de données manquerait à la wheel sans que rien n'échoue à la construction.

Pour en ajouter un, déposez un module dans ce répertoire, enregistrez-le dans `src/demo/scenarios/__init__.py` et copiez la forme ci-dessus. `TEXT["en"]` est obligatoire et sert de repli pour toutes les autres langues ; les tests exigent que chaque langue présente porte `title`, `description`, `commit_message`, `review`, `linter` et `pr_description`, non vides, avec les en-têtes de hunk du `DIFF` qui tombent juste.

---

## 5. Langues

La visite a deux moitiés et elles sont traduites séparément :

| Moitié | Où elle vit | Langues |
| --- | --- | --- |
| **Chrome** — titres des étapes, prose de cadrage, fenêtre d'aide, étapes suivantes | `langs/*.json`, comme toute autre chaîne de l'outil | `pt_br`, `pt_pt`, `es_es`, `es`, `fr_fr`, `fr` |
| **Prose des scénarios** — titre de l'exemple, revue, message de commit, description de PR | Dans chaque module de scénario, sous `TEXT` | `en`, `pt_br`, `pt_pt`, `es_es`, `fr_fr` |

Un scénario dont la langue n'a pas d'entrée `TEXT` retombe sur l'anglais pour cette moitié, plutôt que d'échouer ou de mélanger — une langue partiellement traduite se dégrade au lieu de casser. Le scénario indique la langue dans laquelle il a réellement tourné.

`--lang` est déclaré par le sous-commande lui-même, parce que le callback racine retourne avant son propre gestionnaire de `--lang` pour n'importe quel sous-commande. Sans le flag, la visite suit `GITPR_LANG` / la langue détectée du système, la même que l'interface qui l'entoure, donc les deux moitiés s'accordent toujours.

---

## 6. Ce Que la Visite Ne Touche Pas

| Ne touche pas | Parce que |
| --- | --- |
| Votre fournisseur d'IA et vos clés | L'appel au modèle est remplacé ; aucune clé n'est lue, et aucune n'a besoin d'exister |
| `~/.gitpr/cache/prompts/` | Les deux appels de cache sont remplacés, donc la visite ne lit pas une vraie revue en cache et n'empoisonne pas le cache avec une revue enregistrée |
| `~/.gitpr/metrics/` | Les deux appels de métrique sont remplacés |
| Votre arbre de travail et votre dépôt | Aucune commande `git` propre à la visite ne s'exécute, et aucun fichier n'est écrit — aucun rapport, aucun `.md`, aucun `.txt` |
| `.gitpr/skill/` | La recherche de skill est remplacée, donc un template local ne change jamais ce que montre la visite |
| La forge | Aucun jeton, aucun appel d'API, aucun dépôt |

**Une ligne est tout de même écrite.** Le journal d'invocations (`~/.gitpr/logs/`) enregistre l'exécution comme n'importe quelle autre commande, depuis le callback racine de la CLI par lequel passent toutes les commandes et tous les `-h`, avec l'unique appel à `git config` qui étiquette la ligne avec le dépôt et l'auteur. Il est local et best-effort — un home en lecture seule ou un `git` absent ne devient jamais une commande en échec — et `GITPR_SHOW_LOGS=false` le désactive. Rien d'autre de la visite ne laisse de trace.

---

## 7. Variables d'Environnement

La visite n'introduit **aucune configuration nouvelle**. Elle lit ce que le reste de l'outil lit déjà :

| Variable | Rôle |
| --- | --- |
| `GITPR_LANG` | Langue de l'interface, quand `--lang` n'est pas donné |
| `GITPR_SHOW_LOGS` | Désactive le journal d'invocations (`false`), pour n'importe quelle commande |

Aucune variable de clé, de jeton, de modèle ou de chemin n'est lue : sur une machine au `~/.gitpr/` vide, `gitpr demo` est la seule commande qui fonctionne encore.

> **Note :** Voir aussi la [documentation de Revue de Code](code-review-ia.fr_fr.md) pour ce que prévisualise la quatrième étape, et celle des [Messages de Commit](commit-message-ia.fr_fr.md) pour la troisième.
