# Documentation technique : Badge de Pull Request

Chaque pull request publiée par GitPR porte un petit badge au bas du corps : `GitPR` et les compteurs du linter pour la modification. Il est construit à partir d'une mesure que GitPR a réellement faite — le linter statique local, sur le diff en cours de publication — et c'est une image Markdown que shields.io affiche dans le navigateur du lecteur, donc rien n'est demandé au réseau pendant que le pull request est écrit.

Il existe un second badge, statique, pour le README de votre projet. `gitpr badge --readme` affiche l'extrait et n'écrit rien.

---

## 1. Vue d'ensemble

Le badge est une fonctionnalité avec opt-out. Il est activé par défaut, ne demande jamais rien — ni invite, ni confirmation à la première exécution — et il est annoncé deux fois : une fois quand `gitpr --init` configure une forge, qui est le moment où publier devient possible, et une fois lors d'une publication qui l'ajoute sans que vous ayez vu le corps auparavant.

### 1.1 Référence de la Commande — `gitpr badge`

Toutes les options du sous-commande, telles qu'affichées par `gitpr badge -h` (ou `--help`) :

```bash
gitpr badge                          # ce que c'est, plus l'extrait
gitpr badge --readme                 # seulement l'extrait, prêt à être redirigé
gitpr badge --style for-the-badge    # un autre style shields.io
```

| Option | Description |
| --- | --- |
| **`--readme`** | Affiche uniquement l'extrait, sans rien autour — sûr pour `>>` et pour un pipe |
| **`--style <style>`** | `flat` (par défaut), `flat-square` ou `for-the-badge`. Une valeur inconnue avertit sur stderr et retombe sur `flat` |
| **`-h` / `--help`** | L'aide plus le lien de la documentation dans la langue courante |

| Caractéristique | Description |
| --- | --- |
| **Fichiers écrits** | Aucun. La commande affiche ; elle ne modifie jamais votre README |
| **Réseau** | Aucun. L'URL est assemblée, jamais demandée |
| **Configuration** | Aucune n'est lue : l'extrait ne dépend ni de votre fournisseur, ni de votre forge, ni de votre langue |
| **Code de sortie** | 0. Un `--style` inconnu est un avertissement, pas un échec |

---

## 2. Ce Que Dit le Badge

Les compteurs viennent des règles YAML du linter statique local, exécutées sur le même diff que le pull request. Seules les règles sont utilisées — le pont vers les linters externes est ignoré, parce qu'il exécute des binaires contre l'arbre de travail, et non contre la révision en cours de publication.

| errors | warnings | Couleur | Message |
| --- | --- | --- | --- |
| **> 0** | quelconque | `red` | `N errors · M warnings` |
| **0** | **> 0** | `yellow` | `0 errors · M warnings` |
| **0** | **0** | `brightgreen` | `no issues` |

Deux règles façonnent le texte :

- **Un zéro apparaît à côté d'un compteur non nul.** `0 errors · 2 warnings` dit ce qui a été mesuré ; masquer le zéro laisserait croire que les erreurs n'ont jamais été comptées. Chaque compteur s'accorde tout seul, donc `1 error · 1 warning` s'écrit ainsi.
- **Le badge ne prétend jamais à une revue.** Il rapporte ce que le linter a compté, dans le vocabulaire du linter. Un badge vert signifie *aucune violation de règle n'a été trouvée*, pas *ce code a été relu et approuvé* — la revue par IA est une autre étape, sans aucune part à cela.

Ce que vous voyez sur le pull request est une seule image. `GitPR | 0 errors · 2 warnings` est la façon dont shields.io la dessine, et non une seconde ligne de texte dans le corps, et l'image est un lien vers [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/).

Le texte du badge est **en anglais fixe**, quelle que soit la langue de l'interface. Comme le corps du pull request dans lequel il se trouve, c'est un artefact public qui survit à la machine qui l'a écrit, et il atterrit dans un dépôt dont les lecteurs peuvent ne pas parler votre langue.

---

## 3. Où Il Est Ajouté

Le badge est ajouté à un seul endroit, une fois le corps du pull request complet et avant que l'un ou l'autre des publieurs ne le lise :

| Chemin | Le badge |
| --- | --- |
| **`gitpr`** (TUI) | **Oui** — injecté dans le corps éditable, donc vous pouvez le modifier ou le supprimer avant de publier |
| **`gitpr --no-edit`** | **Oui** — composé dans la requête qui est envoyée |
| **`gitpr --no-publish`** | **Non** — le `.md` écrit localement est la sortie de l'IA, avant que le badge ne soit construit |
| **`gitpr review-pr`** | **Non** — un commentaire de revue est un autre artefact, et GitPR ne le signe pas |
| **Outils MCP** | **Non** — les outils renvoient ce que le modèle a produit |

La TUI est la raison pour laquelle le badge est injecté plutôt qu'ajouté au moment de l'envoi : il est à l'écran, dans la zone de texte que vous êtes déjà en train de modifier, et vous avez le dernier mot. Mettre à jour un pull request existant renvoie le corps actuellement à l'écran — y compris le badge, si vous l'avez gardé.

L'ajout est idempotent. Un corps qui porte déjà un badge est laissé tel quel, donc republier n'en empile jamais deux.

---

## 4. Quand Il N'y a Pas de Badge

**Pas de règles de linter, pas de badge.** Un `.gitpr/skill/.gitpr.linter.yml` vide — l'état de quiconque n'a jamais exécuté `gitpr --skill` — signifie que le linter n'a rien à exécuter, et son résultat vide est indiscernable d'un diff propre. Un badge vert sur un diff que personne n'a vérifié serait une affirmation que GitPR ne peut pas soutenir, donc il est entièrement omis.

**L'opt-out est `GITPR_BADGE=false`.** Comme pour le trailer de co-autorat, `false`, `0`, `no`, `off` et `n` le désactivent, sans distinguer la casse et en ignorant les espaces autour ; toute autre valeur — ou la variable absente — le laisse activé. Elle n'est jamais écrite dans le `.env` à votre place.

Avec la flag désactivée, aucun badge n'est construit et aucun avis n'est affiché : le pull request part exactement comme avant l'existence de cette fonctionnalité.

---

## 5. Le Badge du README

Le badge que vous pouvez mettre sur votre propre projet est un autre : statique, toujours le même, et il dit ce que fait l'outil, et non ce qu'il a mesuré.

```markdown
[![GitPR](https://img.shields.io/badge/GitPR-quality--checked-blue)](https://gitpr.natanfiuza.dev.br/)
```

`gitpr badge` l'affiche avec une courte explication ; `gitpr badge --readme` affiche la ligne seule, ce que vous voulez pour `gitpr badge --readme >> README.md`. Dans un cas comme dans l'autre la commande se contente d'afficher — le placer est votre décision, parce que vous seul savez où il est à sa place dans votre README.

---

## 6. Configuration

| Où | Nom | Remarques |
| --- | --- | --- |
| `~/.gitpr/.env` | `GITPR_BADGE` | Activé par défaut ; `false` désactive le badge. En lecture seule — GitPR ne l'écrit jamais |
| Écran de configuration | **Badge de pull request** | Section Général, le même interrupteur, avec la valeur par défaut explicite dans la description |
| `gitpr --init` | Avis | Affiché une fois la forge configurée, avec l'interrupteur qui le désactive |
| `gitpr --no-edit` | Avis | Affiché lorsqu'un badge a été ajouté à un corps que vous n'avez pas vu |

---

## 7. Variables d'Environnement

| Variable | À quoi elle sert |
| --- | --- |
| `GITPR_BADGE` | `false` (ou `0`, `no`, `off`, `n`) publie les corps de pull request sans le badge |
| `GITPR_LANG` | Langue de l'interface. Le badge lui-même est toujours en anglais |

> **Note :** Voir aussi la [documentation de Publication de PR sur GitHub](pull-request-publication.fr_fr.md) pour le flux auquel le badge est ajouté, et la [documentation du Linter Statique Personnalisable](linter-regras-customizadas.fr_fr.md) pour les règles d'où viennent les compteurs — le badge n'a rien à rapporter tant que ces règles n'existent pas.
