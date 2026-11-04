# Documentation Technique : Fermeture Automatique de l'Issue (`--close-issue`)

La TUI des Issues crée une issue puis se ferme ; le numéro qu'elle a reçu est perdu, et la prochaine Pull Request est le premier endroit où elle pourrait être fermée. La fermeture automatique de l'issue est le pont entre ces deux moments : un registre local transporte le numéro, et le flux de Pull Request propose une ligne — `close #N` — qui fait fermer l'issue par le forge lorsque le merge atterrit.

Ce n'est pas un gestionnaire d'issues. Il ne modifie, ne liste, ne rouvre et n'étiquette rien, et il ne parle jamais au forge de sa propre initiative : rien n'est enregistré tant qu'une issue n'est pas créée depuis la TUI, et rien n'est décidé tant qu'une exécution de Pull Request ne trouve pas un registre à lire.

---

## 1. Vue d'ensemble

La fonctionnalité agit sur trois surfaces :

1. **Création.** `gitpr -is` ouvre la TUI des Issues ; `F3` crée l'issue sur le forge, et la même réponse est écrite dans `.gitpr/conf/github.yml`.
2. **L'exécution de la Pull Request.** Le flux standard `gitpr` lit le registre avant de générer quoi que ce soit, demande au forge si l'issue est toujours ouverte et — au plus une fois — propose d'ajouter la ligne de fermeture à la description.
3. **Aide contextuelle.** `gitpr -h --close-issue` et `gitpr -h --no-close-issue` décrivent les deux flags et renvoient à ce document.

### 1.1 Référence des Commandes

```bash
gitpr -is                      # Crée une issue ; F3 sur GitHub l'enregistre
gitpr                          # Le flux de PR lit le registre et peut proposer close #N
gitpr --close-issue            # Accepte la ligne sans demander (l'issue est quand même vérifiée)
gitpr --no-close-issue         # Ignore la fonctionnalité pour cette exécution
gitpr -h --close-issue         # Le même résumé, avec un lien vers ce document
```

| Commande | Écrit | Ce qu'elle fait |
|---|---|---|
| `gitpr -is` → `F3` | `.gitpr/conf/github.yml`, `.gitignore` | Crée l'issue sur GitHub et enregistre numéro, titre, URL, date de création et branche. `F2` (sauvegarde locale) n'enregistre rien |
| `gitpr` (standard) | Le corps de la Pull Request, uniquement lorsque la ligne est acceptée | Lit le registre, vérifie l'issue, demande au plus une fois |
| `--close-issue` | Idem ci-dessus | Accepte la ligne sans la question ; l'issue est quand même vérifiée |
| `--no-close-issue` | Rien | Aucun registre n'est lu et aucun appel au forge n'est effectué |
| `-h --close-issue` | Rien | Affiche l'aide contextuelle |

Les deux flags répondent à la même question : les passer tous les deux est une erreur d'utilisation. L'exécution indique qu'ils ne peuvent pas être utilisés ensemble et sort avec le code `1`. Le rejet intervient avant l'invite de migration du ledger et la création du fichier de projet, car une erreur d'utilisation ne doit rien demander ni écrire de fichier. `-h` l'emporte sur l'erreur : une invocation d'aide portant les deux flags affiche donc encore les deux entrées.

---

## 2. Le Flux, de Bout en Bout

Six étapes, dans l'ordre où l'exécution les parcourt :

1. **Enregistrement.** `F3` dans la TUI des Issues appelle le forge, reçoit la nouvelle issue et confie le résultat à `register_created_issue` (`src/ui/issue_app.py`). Seul GitHub est enregistré ; un échec ici est étouffé, car l'issue existe déjà sur le forge et la comptabilité locale ne doit jamais transformer une création réussie en erreur.
2. **Porte initiale.** `_prepare_close_issue` (`src/main.py`) s'exécute au début du flux standard de Pull Request — **avant** la vérification des fichiers non commités, avant la lecture du diff et avant tout appel à l'IA. Elle revient immédiatement pour `--no-close-issue`, pour `GITPR_ISSUE_AUTOCLOSE=false` et lorsque le fichier ne contient ni registre ni erreur. Ce n'est qu'après ces portes qu'elle construit le registre — et le construire exécute `git rev-parse` — puis résout le provider SCM.
3. **Décision.** `resolve_close_issue` (`src/issue_autoclose/resolve_close_issue.py`) lit le registre une fois, interroge le forge une fois et demande à l'utilisateur au plus une fois. Les portes sont listées à la section 4.
4. **Assemblage.** `insert_close_line` (`src/issue_autoclose/insert_close_line.py`) s'exécute au seul point où la description est construite — après le guide du relecteur et avant le fichier `.md` local et `pr_data`. Le publieur de la TUI et le publieur direct de `--no-edit` reçoivent donc exactement le même corps.
5. **Publication.** La TUI (`PrPublishApp`) ou `_publish_pr_directly` envoie le corps au forge.
6. **Nettoyage.** Le registre n'est supprimé que lorsque le corps a réellement atteint le forge : `app.body_published` pour la TUI, ou `_publish_pr_directly` renvoyant `True`. Une question refusée, `Esc`, une publication en échec ou la simple ouverture d'une Pull Request existante conservent le registre pour l'exécution suivante.

La décision est prise avant que la description n'existe pour une raison précise : demander une fois, au début, garde la question loin de l'écran du publieur et laisse la même réponse alimenter le fichier, la TUI et le publieur direct sans seconde invite.

### 2.1 Ce que Coûte Chaque Étape

| Étape | Disque | Réseau | IA | Ignorée quand |
|---|---|---|---|---|
| 1. Enregistrement | Écriture du registre, plus une ligne dans `.gitignore` à la première écriture | L'appel `create_issue` qui avait déjà lieu | — | Issue créée hors de la TUI, sauvegarde locale (`F2`) ou forge autre que GitHub |
| 2. Porte initiale | Une lecture du registre | `git rev-parse` seulement lorsque la fonctionnalité est active | — | `--no-close-issue`, `GITPR_ISSUE_AUTOCLOSE=false`, aucun registre |
| 3. Décision | Une lecture du registre | Un `get_issue` ; un second appel pour la branche par défaut, uniquement sur le chemin de la question | — | N'importe laquelle des portes de la section 4 |
| 4. Assemblage | — | — | — | Aucune décision produite |
| 5. Publication | Les artefacts habituels de la PR | L'appel habituel de publication | La génération habituelle de la PR | — |
| 6. Nettoyage | Une suppression de fichier | — | — | Rien n'a été publié |

Sans registre, l'exécution est le flux de toutes les versions précédentes, octet pour octet. Le seul travail supplémentaire est une lecture de fichier.

---

## 3. Le Fichier de Registre

Le registre se trouve dans `.gitpr/conf/github.yml`, ancré à la racine du dépôt. C'est un état local, pas un contenu du projet : le fichier n'est pas destiné à être commité, et la première écriture ajoute exactement une ligne au `.gitignore` du dépôt.

Le dossier lui-même n'est pas ignoré en bloc. `gitpr.config.yml` vit dans le même `.gitpr/conf/` et est versionné à dessein (ADR-015), donc l'entrée d'ignore nomme spécifiquement le fichier de registre.

Le registre conserve **une issue à la fois — la dernière gagne.** Un flux de Pull Request unique n'a pas besoin de plus : l'issue documentée est celle qui vient d'être créée. Créer une seconde issue remplace la première, et il n'y a aucun historique à consulter. C'est aussi pourquoi le fichier n'est pas un cache d'issues : c'est un marque-page.

### 3.1 Le Format

```yaml
schema_version: 1
last_issue:
  repo: owner/name
  number: 42
  title: "Add login rate limit"
  url: https://github.com/owner/name/issues/42
  created_at: '2026-11-03T14:22:07'
  branch: feat/login-rate-limit
```

`schema_version: 1` est la seule version que ce module lit et la seule qu'il écrit. Un fichier portant une autre version est signalé comme illisible plutôt que deviné.

`load()` valide chaque champ avant de le renvoyer :

- `repo`, `title`, `url` et `created_at` doivent être du texte non vide ;
- `number` doit être un entier positif, et un booléen est rejeté même si Python le traite comme un entier ;
- `branch` est facultatif et peut être vide.

Un **fichier absent n'est pas une erreur** — il signifie « aucune issue enregistrée ». Un fichier illisible est une erreur, renvoyée comme donnée (`RegistryLoad.error`) afin que la commande maîtresse de l'écran décide comment la signaler. Le module n'imprime jamais.

### 3.2 Écritures, Corruption et `.gitignore`

`record()` écrit dans un fichier temporaire voisin et le déplace en place avec `os.replace`, si bien qu'une exécution interrompue ne peut jamais laisser un registre tronqué. Un fichier que `load()` a signalé comme corrompu est simplement remplacé par le `record()` suivant : un marque-page cassé vaut moins qu'un neuf.

Avant la première écriture, `record()` interroge `git check-ignore -q .gitpr/conf/github.yml`. Ce n'est que lorsque git n'ignore pas encore le fichier qu'il ajoute l'entrée au `.gitignore`, et une seule fois. Hors d'un dépôt git, ou lorsque le `.gitignore` ne peut pas être écrit, rien ne change et le registre reste valide — l'utilisateur peut ajouter la ligne à la main.

`clear()` supprime le fichier et renvoie `False` lorsqu'il n'y avait rien à supprimer, si bien que l'appelant n'a jamais à distinguer « supprimé » de « n'existait pas ». Toute véritable défaillance d'E/S devient `IssueRegistryError` ; les appelants qui s'exécutent dans le flux de Pull Request la capturent et poursuivent, car l'état local ne doit pas casser une publication.

---

## 4. La Décision : les Portes dans l'Ordre

L'ordre fait partie du contrat. Toute porte qui ne coûte rien s'exécute avant tout accès au disque ou au réseau, et seule une issue encore ouverte atteint la question. `skipped_reason` est le vocabulaire que rapporte la métrique `issue_autoclose` (section 8).

| # | Porte | `skipped_reason` | Coût | Efface le registre |
|---:|---|---|---|---|
| 1 | `--no-close-issue` a été passé | `flag-disabled` | Aucun | Non |
| 2 | `GITPR_ISSUE_AUTOCLOSE=false` | `disabled` | Aucun — le flux de PR revient avant d'appeler le cas d'usage ; la vérification reste comme défense en profondeur pour les appelants qui contrôlent l'interrupteur | Non |
| 3 | Le forge n'est pas GitHub | `not-github` | Aucun | Non |
| 4 | Le registre existe mais ne peut pas être lu | `registry-error` | Une lecture de fichier, un avertissement | Non |
| 5 | Aucun registre | `no-record` | Une lecture de fichier | Non |
| 6 | Le registre appartient à un autre dépôt | `other-repo` | Une lecture de fichier | Non (ADR-007) |
| 7 | `get_issue` répond 404 | `issue-missing` | Un appel HTTP | **Oui** |
| 8 | `get_issue` échoue pour une autre raison | `verify-failed` | Un appel HTTP, un avertissement | Non — conservé pour l'exécution suivante |
| 9 | Le numéro est une Pull Request | `issue-is-pr` | Un appel HTTP | **Oui** |
| 10 | L'issue n'est pas `open` | `issue-not-open` | Un appel HTTP | **Oui** |
| 11 | Aucun terminal et `--close-issue` n'a pas été passé | `no-tty` | Un appel HTTP | Non |
| 12 | `--close-issue` a été passé | — (une décision est prise) | Un appel HTTP, sans question | Non |
| 13 | L'utilisateur répond à la question | `declined` lorsque la réponse est non | Un second appel HTTP pour la branche par défaut, uniquement sur ce chemin | Non en cas de refus |

Deux détails comptent plus que le tableau :

- **La vérification de Pull Request précède celle de l'état.** Le point de terminaison des issues de GitHub répond aussi aux numéros de Pull Request, donc `is_pull_request` est examiné en premier. Un numéro qui s'avère être une Pull Request n'est pas une issue qui a été fermée — c'est un registre qui ne pourra jamais servir, et il est oublié.
- **La comparaison de dépôt ignore la casse.** Les noms d'owner et de dépôt sur GitHub ne distinguent pas les majuscules des minuscules, donc `matches_repo()` les compare avec `casefold()`. Un registre d'un autre dépôt ne regarde pas ce flux, et il est délibérément conservé plutôt qu'effacé.

### 4.1 La Question et l'Avertissement de Branche Cible

La question est :

```text
Issue #42 – Add login rate limit is open. Add "close #42" to the end of the pull request description?
```

La réponse par défaut est oui. `ask` est appelé en dehors de tout bloc `try` : l'`Abort` de `click` est un `RuntimeError`, et `Ctrl+C` doit laisser le flux exactement comme n'importe quelle autre invite, au lieu d'être avalé comme fonctionnalité ignorée.

Sur le chemin de la question — et seulement là — le flux récupère aussi la branche par défaut du dépôt. Lorsque la cible configurée diffère de la branche par défaut, la question porte une ligne supplémentaire :

> Warning: the pull request targets `"develop"` but the default branch is `"main"`. GitHub only closes the issue when the merge lands on the default branch.

Une recherche de branche par défaut qui échoue ou revient vide dégrade en silence. Le forge dit seulement « inconnu », et un avertissement que l'appelant ne sait pas formuler correctement est pire qu'aucun avertissement.

### 4.2 Ce que le Résultat Transporte

`CloseIssueOutcome` a cinq champs, et tous peuvent être ignorés sans risque :

| Champ | Signification |
|---|---|
| `decision` | Le numéro, le titre et la ligne exacte à insérer — `None` lorsque rien n'a été proposé ou que l'utilisateur a refusé |
| `warning` | Un message d'une ligne à imprimer ; jamais défini lorsqu'une question a été posée |
| `skipped_reason` | La porte qui a terminé la décision ; vide lorsqu'une décision a été prise |
| `asked` | Si l'utilisateur a réellement vu une question |
| `accepted` | Si la ligne sera insérée |

Une décision n'efface jamais le registre — l'effacement appartient à l'appelant, une fois la Pull Request existante (ADR-007), car une publication en échec doit conserver le registre pour l'exécution suivante. `target_branch_warning` est répété sur la décision uniquement pour que l'appelant le garde à côté de la ligne ; il faisait déjà partie de la question et ne doit pas être imprimé de nouveau.

---

## 5. Insertion et Idempotence

Le corps est assemblé une seule fois. `insert_close_line` est appelé depuis ce point et nulle part ailleurs, donc aucun publieur ne peut recevoir un corps sans la ligne ou avec la ligne ajoutée deux fois.

Une décision `None` renvoie le corps inchangé. Sinon, la ligne est ajoutée comme paragraphe distinct :

```text

close #42
```

La fonction est idempotente entre les graphies des mots-clés. GitHub accepte `close`, `closes`, `closed`, `fix`, `fixes`, `fixed`, `resolve`, `resolves` et `resolved`, sans distinction de casse, et la même issue peut être nommée `owner/repo#42`. Si le corps mentionne déjà **le même numéro d'issue** sous l'une de ces formes, rien n'est ajouté — le forge fermera l'issue de toute façon, et une seconde référence ne serait que du bruit.

Le badge est attaché plus tard et toujours à la fin du corps, donc ajouter ici est ce qui laisse la ligne de fermeture immédiatement avant lui. Ce module n'a jamais à chercher un badge.

---

## 6. Le Contrat SCM et les Autres Forges

Trois méthodes de `ScmProvider` existent pour cette fonctionnalité :

| Méthode | GitHub | Classe de base |
|---|---|---|
| `get_issue(repo, number, timeout=5)` | `GET /repos/{owner}/{repo}/issues/{n}` | Lève `ScmNotSupportedError` |
| `get_default_branch(repo, timeout=5)` | `GET /repos/{owner}/{repo}` → `default_branch` | Lève `ScmNotSupportedError` |
| `closing_line(number)` | `close #N` | Lève `ScmNotSupportedError` |

Aucune des trois n'est abstraite. C'est délibéré : GitLab, Bitbucket et Azure DevOps continuent de compiler et de fonctionner pour toutes les autres fonctionnalités, et la fermeture automatique est réservée à GitHub (ADR-003). L'appelant lit `ScmNotSupportedError` comme « fonctionnalité inactive », jamais comme un plantage.

`closing_line` est la syntaxe du forge, pas une chaîne générique. GitHub lit `close #N` ; une ligne construite ailleurs pourrait être correctement orthographiée et ne rien signifier pour le forge. Le délai court de cinq secondes fait aussi partie du contrat : la réponse ne décide que si une question sera posée, et un forge lent ne doit pas retenir le flux de Pull Request.

`provider_is_github()` est vérifié avant tout cela, donc les autres forges ignorent la fonctionnalité sans lecture disque et sans avertissement.

---

## 7. Configuration

Deux variables dans `~/.gitpr/.env`, également modifiables dans `gitpr config`, section **Issue**. Aucune n'est écrite automatiquement.

| Clé | Défaut | Effet |
|---|---|---|
| `GITPR_ISSUE_AUTOCLOSE` | `true` | Seuls `false`, `0`, `no`, `off` ou `n` désactivent la fonctionnalité ; toute autre valeur — y compris une valeur illisible — la laisse active |
| `GITPR_ISSUE_AUTOCLOSE_TIMEOUT` | `5` | Secondes d'attente du forge lors de la lecture de l'issue. Zéro, un nombre négatif ou une valeur non entière reviennent à `5` |

La précédence est :

```text
--no-close-issue  >  GITPR_ISSUE_AUTOCLOSE=false  >  --close-issue
```

`--close-issue` **ne prime pas** sur `GITPR_ISSUE_AUTOCLOSE=false`. L'interrupteur est la décision de l'utilisateur concernant la machine, et un flag par exécution qui l'inverserait en silence rendrait le réglage indigne de confiance. Il n'existe pas de configuration par dépôt pour cette fonctionnalité.

---

## 8. Métriques

Chaque décision atteinte par le cas d'usage est rapportée une fois au ledger local (`gitpr metrics`) sous forme de ligne `issue_autoclose` :

| Champ du payload | Valeur |
|---|---|
| `command` | `issue_autoclose` |
| `asked` | Si la question a été affichée |
| `accepted` | Si la ligne sera insérée |
| `skipped_reason` | La porte de la section 4, ou vide lorsqu'une décision a été prise |

Les courts-circuits du helper lui-même — flag désactivé, configuration désactivée, aucun registre, aucun provider — n'ont jamais engagé la fonctionnalité et restent hors du ledger. Ce ne sont pas des décisions ; ce sont des exécutions où il n'y avait rien à décider.

Les champs voyagent dans le payload JSON. L'export CSV porte les colonnes que le ledger définit pour toutes les commandes, pas un format par fonctionnalité.

---

## 9. Limites, Dites Clairement

- **Une issue à la fois.** Créer une seconde issue remplace le premier registre ; la première ne peut plus être fermée par cette fonctionnalité.
- **L'enregistrement n'a lieu que dans la TUI.** Une issue créée avec `gh`, via l'API ou par tout autre chemin est invisible pour la fonctionnalité.
- **GitHub uniquement.** Les autres forges ignorent la fonctionnalité en silence, sans avertissement et sans registre.
- **Le registre est par clone.** C'est un état local et il n'est pas commité, donc le clone d'un collègue ne l'hérite pas, et un nouveau clone commence sans rien à fermer.
- **Supprimer la ligne dans l'éditeur ne conserve pas le registre.** Si le corps a été publié, le registre est effacé parce que la publication a transporté le corps — même si la ligne a été retirée avant l'envoi.
- **Mettre à jour une Pull Request existante efface aussi le registre.** La TUI rapporte « created » pour ce chemin également ; ce qui décide de l'effacement, c'est que le corps a atteint le forge.
- **Les mots-clés sont uniquement en anglais.** `close`, `fix` et `resolve` et leurs flexions sont ce que lit GitHub ; un corps qui dit `ferme #42` n'est pas une référence de fermeture, et la ligne sera ajoutée à côté.
- **La vérification d'état fait confiance au forge.** Une issue fermée entre la lecture et le merge ne peut pas être détectée ici ; la ligne de fermeture n'a simplement plus rien à fermer.

---

## 10. Lectures Connexes

- `docs/issue-tui-help.md` — la TUI des Issues, `F2`/`F3` et le résumé court de cette fonctionnalité pour l'utilisateur.
- `docs/config-tui.md` — l'écran de configuration, y compris la section **Issue**.
- `docs/metricas-telemetria.md` — le ledger local et la métrique `issue_autoclose`.
- `docs/scm-multiforge.md` — l'abstraction des providers et pourquoi seul GitHub implémente la fermeture.
- `docs/github-pat-integration.md` — le token dont `F3` a besoin pour créer l'issue.
- `docs/pull-request-publication.md` — le publieur qui reçoit le corps assemblé.
- `docs/specs/issue-autoclose/adrs/ADR-001` à `ADR-007` — les décisions derrière le registre, les portes, l'insertion et l'effacement.
- `CONTEXT.md` — les termes du glossaire *Issue registry*, *Closing line* et *Close issue decision*.
