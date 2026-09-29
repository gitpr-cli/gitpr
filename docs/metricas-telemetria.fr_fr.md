# Métriques et Télémétrie — Analytics Local Hors Ligne

GitPR tient un **registre local et hors ligne de l'utilisation** : une ligne par
commande exécutée, ce qu'elle a coûté et combien de temps elle a pris. Rien ne
quitte votre machine — le registre est un fichier SQLite dans
`~/.gitpr/metrics/telemetry.db`.

## ✨ Ce Que Cela Fait

Chaque commande exécutée ajoute une ligne au registre, avec :

| Champ | Description |
|-------|-------------|
| `timestamp` | Quand la commande s'est terminée (ISO 8601) |
| `command` | Quelle commande a tourné (`commit`, `review`, `fullreview`, `linter`, `blame`, `hook:post-checkout`, etc.) |
| `status` | Résultat (`success`, `error`, `fired`, `no_changes`) |
| `provider` | Fournisseur d'IA qui a répondu (`gemini`, `deepseek`, `ollama`) |
| `model` | Modèle avec lequel le fournisseur a répondu |
| `prompt_tokens` / `completion_tokens` | Nombre de tokens rapporté par le fournisseur |
| `tokens_actual` / `tokens_estimated` | Le compte qui fait foi : mesuré quand le fournisseur le rapporte, estimé sinon |
| `duration_ms` | Durée de la commande en millisecondes |
| `repo` | Dépôt sous la forme `propriétaire/nom`, résolu par le même parseur multi-forge que le reste de la CLI |
| `branch` | Nom de la branche actuelle |
| `author_name` | Auteur Git local de l'exécution |
| `modules` | Modules touchés par le diff, normalisés aux deux premiers segments du chemin (`src/fix`, `(root)` pour un fichier à la racine du dépôt) |
| `source` | `execution` pour une commande qui a tourné, `cache_backfill` pour une ligne reconstruite depuis le cache d'IA |

Les lignes portent aussi `cache_hit`, `map_reduce`, `chunks_count`,
`linter_errors` et `linter_warnings`, qui ont du sens pour certaines commandes et
restent à zéro pour les autres. `modules` est **vide** pour les commandes qui
n'ont jamais eu de diff en main — le linter, le moteur de blame et les hooks
enregistrent des exécutions sans diff, et la section des modules les
additionne sous `(sans module)` au lieu de les faire passer pour un module
qui ne porte aucun nom.

## 📁 Où les Données Sont Stockées

```
~/.gitpr/metrics/
├── telemetry.db         ← le registre : une ligne par commande exécutée (SQLite)
└── .migration_declined  ← écrit uniquement si vous avez refusé l'importation

~/.gitpr/metrics_legacy/    ← les fichiers d'événements antérieurs au registre, déplacés ici après l'importation
~/.gitpr/cache/prompts/     ← cache de réponses de l'IA, source d'une reconstruction
```

Les exportations vont dans le dépôt où vous lancez la commande, jamais dans votre
répertoire personnel :

```
./.gitpr/metrics/export/
├── gitpr_metrics_2026-09-28.csv    ← CSV consolidé
├── gitpr_metrics_2026-09-28.json   ← JSON consolidé
└── gitpr_metrics_2026-09-28.db     ← bundle écrit par `gitpr metrics bundle`
```

Le registre a remplacé des fichiers JSON d'événement nommés
`{uuid}_{AAAAMMJJ}.json` dans `~/.gitpr/metrics/{propriétaire}/{branch}/`. Ces
fichiers sont importés une fois puis **déplacés, jamais supprimés** — ils
finissent dans `~/.gitpr/metrics_legacy/`, en dehors du répertoire que compte le
résumé.

## 🚀 Commandes CLI

### Afficher le Résumé

```bash
gitpr metrics
```

Compte des lignes, pas des fichiers : le chemin du registre, combien d'exécutions
il contient, combien de lignes ont été reconstruites depuis le cache et la taille
sur disque. Un avertissement apparaît tant que des fichiers d'événements
antérieurs au registre attendent d'être importés.

Sous l'en-tête viennent les sections, dans l'ordre où elles sont lues :

| Section | Ce qu'elle répond |
|---------|-------------------|
| 💰 Coût | Combien de tokens, et ce qu'ils ont coûté par modèle |
| 🧪 Qualité | Taux de réussite du linter et fréquence de déclenchement du chemin map-reduce |
| 🧩 Modules | Quels modules les exécutions ont touchés, et combien de tokens chacun a pris |
| 🤖 Fournisseurs | Exécutions et tokens par fournisseur — y compris ceux qui n'appellent jamais d'IA |
| ⏱ Cycle | Combien de temps ont pris les pull requests fusionnées de ce dépôt, lues depuis la forge |

Une section qui n'a rien à dire est omise plutôt qu'imprimée vide. Le tableau de
bord dessine ces mêmes lignes depuis le même moteur de rendu : le terminal et la
TUI ne peuvent donc pas raconter deux histoires sur un même registre.

### La Fenêtre

Une fenêtre, une signification — les mêmes flags limitent le résumé, le tableau de
bord, l'export, le bundle et l'outil MCP :

```bash
gitpr metrics --days 30
gitpr metrics --since 2026-01-01 --until 2026-03-31
```

La fenêtre est **inclusive aux deux bornes** et porte sur la date à laquelle la
ligne se rapporte. Sans aucune flag, les sections du registre lisent le registre
entier — sauf le cycle, qui demande sa réponse au réseau et prend donc par défaut
les 30 derniers jours, en le disant dans son propre en-tête plutôt qu'en
restreignant en silence.

### Coût et Tarifs

La section de coût convertit les tokens en argent avec deux couches, la seconde
primant sur la première par modèle :

1. **Une table intégrée** des prix catalogue publiés par les fournisseurs pour les
   IDs de modèle fixes que GitPR accompagne (`deepseek-v4-flash`,
   `deepseek-v4-pro`, `gemini-2.5-pro`, `gemini-2.5-flash-lite`), pour que la
   section dise quelque chose sur une machine que personne n'a configurée.
2. **L'environnement**, par modèle :

```ini
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_INPUT=0.435
GITPR_METRICS_PRICE_DEEPSEEK_V4_PRO_OUTPUT=0.87
GITPR_METRICS_CURRENCY=USD
```

`<MODEL>` est le nom du modèle en majuscules, chaque suite de caractères qui n'est
ni lettre ni chiffre étant réduite à un `_`. Les deux tarifs sont obligatoires : un
modèle qui n'en a qu'un est reporté en tokens seuls, car tarifer l'autre moitié à
un zéro non configuré sous-estimerait la facture.

- **La devise par défaut est USD**, la devise dans laquelle la table intégrée est
  cotée. Configurez des tarifs dans une autre devise et pointez
  `GITPR_METRICS_CURRENCY` dessus — la table intégrée s'efface alors, car un tarif
  en dollars imprimé sous l'étiquette d'une autre devise est un nombre faux, pas
  un nombre manquant.
- **Les fournisseurs qui tournent sur cette machine** (`ollama`, `local`) coûtent
  zéro par définition et n'ont pas besoin de tarif.
- **Les tarifs bougent.** Convertir des tokens dépensés l'an dernier au prix
  d'aujourd'hui est une approximation, et la section le dit sur la ligne sous le
  total.
- **Un total qui laisse des modèles de côté le dit** — `Total (partiel)` — au lieu
  de laisser une somme des lignes tarifées passer pour la facture entière.

### La Métrique de Cycle

La section ⏱ est la seule métrique ici qui ne vient pas du registre, et elle ne
peut pas en venir : le registre note ce que GitPR a exécuté sur cette machine,
alors qu'une pull request est fusionnée sur la forge, par des personnes qui n'ont
jamais exécuté GitPR. C'est pourquoi celle-ci a besoin d'un jeton et du réseau, et
c'est la seule section qui peut revenir vide pour une raison qui n'est pas « rien
ne s'est passé ».

Elle mesure `created_at → merged_at` des pull requests que la forge signale comme
fusionnées dans la fenêtre — **le cycle de la pull request elle-même**, de
l'ouverture à la fusion. Ce n'est pas le temps du premier commit d'une branche
jusqu'à sa pull request : le contrat de listage ne porte pas les commits de
branche, cet intervalle n'est donc pas disponible ici, et il n'est pas non plus
inventé à partir du registre.

L'en-tête nomme le dépôt et la fenêtre — `⏱ Cycle · propriétaire/dépôt · 30
derniers jours` — car c'est la seule section dont la portée n'est pas celle du
registre : lue à côté d'un résumé qui dit « Tous les dépôts », une valeur nue
semblerait les couvrir tous.

Toute défaillance se dégrade en une ligne, jamais en stack trace :

| Ce qui s'est passé | Ce que la section affiche |
|--------------------|---------------------------|
| Pas de remote origin, pas de forge utilisable, pas de jeton, pas de réseau | `Non lu : <la raison>` |
| La forge ne publie pas de date de fusion (Bitbucket) | Le dit, sans dépenser d'appel réseau |
| La fenêtre ne contient aucune pull request fusionnée | `Aucune pull request n'a été fusionnée dans cette fenêtre.` |

Une fusion dont la date précède sa propre création est une horloge que la forge
s'est trompée, pas un cycle négatif : cette ligne est écartée plutôt que
moyennée.

### Exporter les Données

```bash
gitpr metrics export
```

Écrit en CSV et JSON les lignes qui n'ont jamais été exportées, dans
`./.gitpr/metrics/export/`, puis les marque comme exportées — c'est pourquoi une
seconde exécution répond « Aucune nouvelle métrique à exporter. » au lieu de se
répéter. L'exportation couvre le dépôt de la copie de travail.

- **Colonnes CSV :** timestamp, day, command, status, provider, model,
  prompt_tokens, completion_tokens, tokens_actual, tokens_estimated, duration_ms,
  repo, branch, author_name, modules, cache_hit, map_reduce, linter_errors,
  linter_warnings, chunks_count, source
- **JSON :** les mêmes lignes sous forme d'objets, prêtes à être lues par un script

### Bundle et Merge (Consolidation d'Équipe)

`export` est ce qu'une personne lit ; un **bundle** est ce qu'une autre machine
lit — la même tranche du registre sous forme de fichier `.db` autonome :

```bash
gitpr metrics bundle --days 30
gitpr metrics bundle --since 2026-07-01 --until 2026-09-30 -o ./passation/
gitpr metrics merge ./passation/gitpr_metrics_2026-09-29.db ./passation/autre.db
```

`bundle` copie les lignes de la fenêtre dans un fichier SQLite autonome, schéma et
`PRAGMA user_version` inclus, et écrit dans `./.gitpr/metrics/export/` sauf si
`-o` dit autre chose. `merge` attache chaque bundle et insère les lignes qu'il n'a
pas déjà — l'UUID est la clé primaire, donc fusionner deux fois le même fichier,
ou deux bundles qui se chevauchent, ne compte jamais une exécution deux fois.

Les versions de schéma sont traitées dans **un seul sens** : un bundle plus ancien
est migré vers le haut à l'attachement, et un plus récent est refusé *avant* toute
écriture, avec la version qu'il porte et celle que ce GitPR comprend — le registre
local n'est jamais laissé à moitié importé. Mettez GitPR à jour pour lire un
bundle plus récent.

C'est la réponse à « combien l'équipe a dépensé ce trimestre » sans serveur :
chaque machine emballe sa fenêtre, et qui a besoin du total fusionne les fichiers
dans un registre à lui.

### Importer les Données Antérieures au Registre

```bash
gitpr metrics migrate
```

Lit les fichiers d'événements écrits avant l'existence du registre, les insère et
déplace les originaux vers `~/.gitpr/metrics_legacy/`. Avec un terminal, ouvre un
assistant qui propose aussi de reconstruire l'historique depuis le cache de
réponses de l'IA. Ces lignes sont marquées `source: cache_backfill` parce que le
cache indexe une réponse par son prompt et compte donc **des prompts distincts,
pas des exécutions**.

### Supprimer les Anciens Enregistrements

```bash
gitpr metrics prune --before 2026-01-01
```

Supprime les lignes écrites avant une date, après confirmation, et récupère
l'espace avec `VACUUM`. `--source cache_backfill` limite la suppression aux lignes
reconstruites. Il n'y a **aucune expiration automatique** : le registre répond
« combien avons-nous dépensé cette année », et un calendrier qui supprime tout
seul changerait cette réponse sans que personne ne le demande.

### Purger les Données

```bash
gitpr metrics purge
```

Le chemin destructeur : supprime toutes les lignes et tous les fichiers
d'événements encore en attente d'importation, après confirmation.

### Tableau de Bord Interactif

```bash
gitpr metrics dashboard
```

Ouvre un **tableau de bord TUI** (Textual) limité au dépôt de la copie de
travail :

- **Barre de résumé :** total d'entrées, lignes reconstruites, total de tokens, durée totale, commandes principales
- **Tableau d'événements :** horodatage, commande, statut, fournisseur, tokens, durée
- **Sections :** coût, qualité, modules, fournisseurs et le cycle — les mêmes lignes
  que `gitpr metrics` imprime, dessinées avec le markup Textual au lieu des couleurs
  de click
- **Barre d'état :** la plage de temps couverte par le tableau et son nombre d'entrées
- **Raccourcis :** `F5` pour actualiser, `Esc` pour quitter

Tant que le registre n'existe pas encore, le tableau de bord lit le cache et les
fichiers d'événements, affiche une barre de progression pendant l'analyse et
l'indique dans la barre d'état.

La section de cycle est dessinée dans tous les cas : elle n'a jamais lu le
registre.

## 🔧 Git Hooks (Collecte Automatique)

Lorsqu'ils sont installés via `gitpr --installhooks`, trois hooks supplémentaires
collectent la télémétrie comportementale :

| Hook | Événement capturé |
|------|------------------|
| `post-checkout` | Changements de branche (changements de contexte) — ne se déclenche que si la branche a réellement changé |
| `pre-push` | Événements de push (fréquence de livraison) |
| `post-merge` | Événements de pull/merge (fréquence d'intégration) |

Les trois lancent `gitpr --quiet metrics hook-event <nom>`, une action cachée dont
l'unique tâche est d'écrire une ligne et de sortir. Le dépôt est résolu par le
hook lui-même, avec le même parseur que le reste de la CLI : GitLab, Bitbucket et
Azure DevOps enregistrent donc le même `propriétaire/nom` que GitHub. Une garde
autour de l'appel — `command -v gitpr`, plus un `|| true` final — empêche une
machine sans GitPR, ou avec un GitPR en échec, de casser votre commande Git.

## 📊 Cas d'Usage

- **Tech Lead :** Voir quels dépôts, branches et auteurs utilisent réellement les révisions IA, et quels hooks se déclenchent
- **Finance :** Lire la section de coût pour la facture par modèle, ou `gitpr metrics --since 2026-07-01` pour le trimestre
- **Qualité :** Lire `linter_errors`, `linter_warnings` et `modules` pour trouver quelle partie du projet génère le plus de constats
- **Processus :** Surveiller `map_reduce` et `chunks_count` — des PRs volumineuses qui déclenchent le chemin map-reduce signalent un problème de processus
- **Livraison :** Lire la section de cycle pour voir combien de temps ont pris les pull requests fusionnées de ce dépôt, et lesquelles ont pris le plus

## 🔒 Confidentialité

- **100% local** — le registre est un fichier sur votre machine ; rien de ce qu'il contient n'est jamais envoyé à des serveurs externes
- **La seule exception est la section de cycle** — elle demande à la forge configurée les pull requests fusionnées du dépôt où vous vous trouvez. Elle n'envoie aucune ligne du registre, aucun décompte de tokens et aucun diff : la question est « quelles pull requests ont été fusionnées dans cette fenêtre », et la réponse est en lecture seule
- **Pas anonyme** — chaque ligne porte le dépôt, la branche et le nom de l'auteur Git local. Elle ne porte aucun contenu de fichier ni diff : `modules` garde les segments de chemin touchés par une exécution, jamais les noms de fichiers, et l'e-mail de l'auteur reste dans le cache d'IA
- **Contrôlé par l'utilisateur** — `prune` et `purge` sont manuels et confirmés ; rien n'expire tout seul
- **Hooks optionnels** — les git hooks ne s'installent que si vous exécutez `gitpr --installhooks`

## 📚 Documentation Connexe

- [Intégration MCP](mcp-integration.md) — Configuration du serveur MCP
- [MCP Prompts](mcp-prompts.md) — Modèles de message prédéfinis
- [MCP Tool Annotations](mcp-annotations.md) — Conseils d'intégration avec les IDEs

---
**Conseil de pro :** Les exportations atterrissent dans `./.gitpr/metrics/export/`,
dans le dépôt où vous êtes — ce répertoire appartient à votre machine, pas au
projet, et c'est ce que l'entrée `.gitignore` de GitPR lui-même garde hors de
l'arbre. Pour répondre à « combien cette machine a-t-elle dépensé ce trimestre »
sans tableur, interrogez le registre : `gitpr metrics --since 2026-07-01`.
