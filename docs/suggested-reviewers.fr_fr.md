# Documentation Technique : Relecteurs Suggérés pour les Pull Requests

Lorsque vous publiez une pull request via l'éditeur interactif de GitPR (le mode `gitpr` par défaut), GitPR suggère qui devrait la relire : il identifie les personnes qui ont travaillé sur le code que vous modifiez et propose jusqu'à `GITPR_REVIEWER_SUGGESTION_TOP_N` candidats (3 par défaut). Les suggestions apparaissent dans un champ modifiable de l'Éditeur de PR (TUI) et, sur GitHub, elles sont soumises à la nouvelle pull request juste après sa création.

Le calcul est activé par défaut et ne s'exécute que dans le flux de l'éditeur interactif — jamais avec `--no-edit` ni `--no-publish`. Il est purement consultatif et totalement non bloquant : tout échec ou situation non prise en charge se réduit à un avertissement et le flux de publication se poursuit sans changement.

---

## 1. Comment Ça Fonctionne

GitPR ne devine pas : il attribue une paternité réelle avec `git blame`, exécuté sur les lignes exactes que votre diff a ajoutées, en comparant la branche de base avec votre working tree.

### 1.1 Paternité sur les Lignes Ajoutées

- L'entrée est le même diff que GitPR a déjà calculé pour la PR : branche de base vs. working tree (modifications staged incluses), avec les smart-excludes appliqués. Le parseur consomme ce texte de diff et ne ré-exécute jamais `git diff`.
- Seules les **lignes ajoutées** (`+`) comptent pour la paternité. Les lignes supprimées et de contexte sont ignorées.
- Les lignes pas encore commitées — « Not Committed Yet », hash de blame `0000…` — sont ignorées : c'est votre propre travail en cours.
- Le blame s'exécute sur la working tree (sans révision), donc il correspond exactement au diff, fichiers staged et nouveaux compris.
- Les fichiers sans historique exploitable (nouveaux, binaires, clones shallow) ne produisent aucun candidat : un avertissement est affiché et l'analyse continue.

### 1.2 Classement et Exclusions

Chaque auteur trouvé est agrégé par fichier et par ligne et reçoit un score :

| Facteur | Poids | Signification |
| --- | --- | --- |
| Lignes touchées | 50 % | Part des lignes ajoutées du diff écrites par la personne |
| Fichiers touchés | 30 % | Part des fichiers modifiés dans lesquels la personne a une paternité |
| Récence | 20 % | `1 / (1 + days / 90)` — une demi-vie de 90 jours depuis le dernier touché |

L'auteur de la PR est toujours exclu, même lorsqu'il domine le diff. Les **bots** sont également exclus : toute identité dont le nom ou la partie locale de l'e-mail se termine par `[bot]`, ou dont l'e-mail figure dans la liste des bots connus (Dependabot, GitHub Actions, etc.). Le domaine `users.noreply.github.com` n'est jamais traité comme un bot — c'est l'e-mail standard des vrais utilisateurs GitHub. Des personnes supplémentaires peuvent être exclues via `GITPR_REVIEWER_SUGGESTION_EXCLUDED`. Les égalités sont départagées par les lignes touchées et le résultat est tronqué au `top_n` configuré (3 par défaut).

---

## 2. Configuration

La fonctionnalité est activée par défaut. Désactivez-la par exécution avec la flag, ou globalement via l'environnement :

```bash
gitpr --no-suggest-reviewers        # Désactive le calcul pour cette exécution
```

```bash
# ~/.gitpr/.env — désactive globalement et ajuste le classement
GITPR_SUGGEST_REVIEWERS=false
GITPR_REVIEWER_SUGGESTION_TOP_N=5
GITPR_REVIEWER_SUGGESTION_EXCLUDED=renovate[bot],qa@example.com
```

| Variable | Défaut | Description |
| --- | --- | --- |
| `GITPR_SUGGEST_REVIEWERS` | `true` | Interrupteur général. Valeurs falsy : `false`, `0`, `no`, `off`, `n` |
| `GITPR_REVIEWER_SUGGESTION_TOP_N` | `3` | Combien de candidats suggérer ; invalide ou ≤ 0 revient à 3 |
| `GITPR_REVIEWER_SUGGESTION_EXCLUDED` | *(vide)* | CSV facultatif d'e-mails ou de noms à exclure, en plus de l'auteur de la PR et des bots |

Les clés sont lues dans `~/.gitpr/.env` et ne sont jamais écrites automatiquement. `--no-edit` et `--no-publish` ne calculent jamais de suggestions, quelle que soit la configuration.

---

## 3. Relecteurs Suggérés dans l'Éditeur de PR (TUI)

### 3.1 La Section des Relecteurs Suggérés

Dans le flux interactif par défaut, GitPR affiche la ligne `🔍 Recherche de relecteurs suggérés...` pendant que l'analyse s'exécute, avant l'ouverture de l'Éditeur de PR. Lorsqu'il s'ouvre, une section modifiable **👥 Relecteurs Suggérés** est affichée :

- Un champ de saisie pré-rempli avec les utilisateurs GitHub suggérés, séparés par des virgules. Supprimez un relecteur en vidant le champ ; ajoutez-en un en saisissant.
- Une indication en lecture seule sous le champ, expliquant chaque suggestion (lignes et fichiers touchés, dernière activité).
- Laisser le champ vide ne soumet aucun relecteur.

### 3.2 Publication

Après confirmation avec F3, GitPR crée la pull request puis demande les relecteurs acceptés sur GitHub via le point d'accès `requested_reviewers` (`POST .../pulls/{number}/requested_reviewers`). L'attache se produit à la fois lors de la création et lors de la mise à jour, et elle **n'est jamais fatale** : si GitHub rejette la demande — par exemple un handle invalide saisi à la main, répondant avec HTTP 422 — la PR reste publiée et la TUI affiche un avertissement (`⚠️ PR publiée, mais les relecteurs n'ont pas pu être demandés : {error}`).

### 3.3 Aide Contextuelle

La flag participe au système d'aide contextuelle :

```bash
gitpr -h --no-suggest-reviewers
```

---

## 4. Prise en Charge et Limitations par Forge

| Forge | Suggestion | Soumission |
| --- | --- | --- |
| GitHub | Affichée et modifiable | Oui — demandée via `requested_reviewers` après la création ou la mise à jour de la PR |
| GitLab | Affichée localement uniquement | Non — aucun point d'accès équivalent |
| Bitbucket Cloud | Affichée localement uniquement | Non — aucun point d'accès équivalent |
| Azure DevOps | Affichée localement uniquement | Non — aucun point d'accès équivalent |

Sur les forges autres que GitHub, le champ de saisie n'est pas affiché ; la section présente les candidats avec une note indiquant que la suggestion est uniquement locale. Pour transformer les e-mails GitHub en noms d'utilisateur, GitPR résout chaque candidat au mieux et ne bloque jamais : les e-mails du domaine `users.noreply.github.com` sont directement convertis en handle et tout autre e-mail retombe sur `/search/users in:email` de GitHub. Les candidats dont l'e-mail n'est pas reconnu par GitHub apparaissent avec leur nom et leur e-mail et ne sont simplement pas pré-remplis — vous pouvez toujours saisir leur handle.

Obtenir moins de suggestions que `top_n` est normal : fichiers sans historique, fichiers binaires, diff sans lignes ajoutées ou dépôt tout nouveau produisent des résultats vides ou partiels avec un avertissement — jamais une erreur. L'analyse ne s'exécute jamais dans les flux `--no-edit`/`--no-publish`, donc les pipelines automatisés ne sont pas affectés.

---

## 5. Pour les Développeurs et les Plugins

Le use case vit dans quatre modules plats dans `src/` : `reviewer_suggestion.py` contient le domaine pur (dataclasses, poids, liste de bots, `rank_reviewers()` — sans git, sans réseau), `diff_parser.py` implémente `parse_added_lines()` sur le texte du diff, `blame_engine.py` a gagné la fine `get_blame_for_range()` (le flux de l'archéologie n'a pas été refactorisé) et `suggest_reviewers.py` orchestre le tout avec `compute_reviewer_suggestions()`, qui **ne lève jamais d'exception**. Les trois clés `GITPR_*` ci-dessus sont déclarées dans `DEFAULT_CONFIG` dans `src/config.py`, avec `suggest_reviewers_enabled()` et `get_reviewer_suggestion_settings()`.

Côté SCM, le contrat de base `ScmProvider` a gagné une méthode **non abstraite** `request_pull_request_reviewers(repo, pr_id, reviewers)` dont le défaut lève `ScmNotSupportedError` ; seul `github_provider.py` l'implémente, avec `email_to_handle()`, propre à GitHub. `main.py` limite le calcul au flux TUI par défaut et remet à l'application un dict de vue `{"handles", "lines", "submittable", "note"}`. Tout le texte visible passe par des clés i18n `__()`, donc les 5 packs de langue doivent rester synchronisés lorsque les messages changent.

Registre de décision d'architecture et vocabulaire canonique : [ADR-002 Suggestion de Relecteurs](plans/ADR-002-reviewer-suggestion.md) et [Glossaire de la Suggestion de Relecteurs](plans/glossary-reviewer-suggestion.md).

> **Remarque :** Voir aussi la [documentation de publication des pull requests](pull-request-publication.md) pour le flux complet de publication, ses modes et ses flags.
