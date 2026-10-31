# Documentation technique : Revue de Pull Request Distante (gitpr review-pr)

`gitpr review-pr <number>` passe en revue une pull request déjà ouverte sur la forge, en extrayant son diff directement depuis l'API. La branche sous revue n'a pas besoin d'exister sur votre machine — vous n'avez jamais besoin d'en faire l'extraction (`checkout`), de la télécharger (`fetch`) ou de toucher à votre arbre de travail. C'est le mode dédié au relecteur invité sur la pull request d'un pair, où le code à inspecter réside de l'autre côté du réseau.

La revue elle-même n'est pas un second moteur : c'est `gitpr -r` alimenté par un diff venu d'ailleurs. Le même appel d'IA, la même skill `.gitpr.review.md`, les mêmes règles de linter, le même fichier de rapport et le même cache — raison pour laquelle une revue distante et une revue locale portant sur un diff identique produisent un résultat rigoureusement semblable.

---

## 1. Vue d'ensemble

Cette sous-commande est un ajout à la CLI, non une modification : chaque option héritée conserve sa signification et les flux locaux (`gitpr -r`, `gitpr -f`, `gitpr fix`) ne sont aucunement altérés. La lecture constitue le comportement par défaut — sans aucune option, la forge est exclusivement consultée en *lecture*, et rien n'est publié nulle part.

### 1.1 Référence des Commandes — `gitpr review-pr`

Toutes les options de la sous-commande, telles qu'affichées par `gitpr review-pr -h` (ou `--help`) :

```bash
gitpr review-pr 123                    # passer en revue la pull request et enregistrer le .txt
gitpr review-pr 123 --provider deepseek  # passer en revue avec un moteur d'IA spécifique
gitpr review-pr 123 --post-comment     # publier également la revue sous forme de commentaire
```

| Option | Description |
| --- | --- |
| **`<number>`** | Le numéro de la pull request tel qu'affiché sur la forge (`123`). Obligatoire et entier — un argument non numérique constitue une erreur d'utilisation |
| **`--provider <name>`** | Force le moteur d'IA pour cette exécution (`gemini`, `deepseek` ou `ollama`). Sans cette option, la valeur par défaut configurée est utilisée |
| **`--post-comment`** | Publie la revue sous forme de commentaire sur la pull request. **Sans cette option, la forge n'est jamais modifiée** |

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Le diff servi par l'API de la forge pour cette pull request — jamais votre arbre de travail |
| **Forge** | Celle configurée via `gitpr --init` (GitHub, GitLab, Bitbucket). Azure DevOps est refusé — voir §3 |
| **Appel d'IA** | Un seul appel, sur le modèle avancé du fournisseur configuré, mis en cache sous `review/` comme tout autre appel GitPR |
| **Fichiers enregistrés** | `{branch}_{datetime}_PR_REVIEW.txt` dans le dossier des rapports (`OUTPUT_FILE_NAME_REVIEW`) |
| **Publication** | Rien, à moins que `--post-comment` ne soit spécifié |
| **Arbre local** | Jamais lu, jamais inspecté pour des fichiers non indexés et jamais modifié — sans checkout, sans fetch, sans changement de branche |
| **Code de sortie 1** | Aucune forge configurée, forge sans diff relisible, pull request inexistante ou fermée, diff vide ou entièrement filtré, API inaccessible, clé d'IA absente |

---

## 2. Ce Qu'est une Revue Distante

### 2.1 Le Diff Provient de l'API

La forge est d'abord interrogée pour obtenir les métadonnées de la pull request, puis son diff :

| Étape | Ce qu'elle établit |
| --- | --- |
| `get_pull_request` | Confirme que le numéro existe, son état actuel et les branches qu'elle relie |
| `get_pull_request_diff` | Le diff unifié à passer en revue |

Résoudre directement le numéro permet de distinguer un élément inexistant d'un élément fusionné la semaine dernière : lister les pull requests ouvertes ne renvoie que celles qui sont ouvertes, de sorte qu'un numéro absent pourrait correspondre à l'un ou l'autre cas. Les métadonnées fournissent également le nom des deux branches requis par le rapport.

La requête de métadonnées n'est pas décorative — c'est elle qui empêche un numéro obsolète de consommer inutilement des tokens (§4.2).

### 2.2 Le Diff Est Normalisé

Un diff qui n'est jamais passé par git arrive dans la forme exacte choisie par la forge. Trois étapes sont exécutées avant transmission à l'IA :

| Étape | Raison |
| --- | --- |
| **Fins de ligne unifiées en LF** | GitLab et Bitbucket renvoient des CRLF pour les branches créées sous Windows, et le découpeur scinde sur `^diff --git a/`, ce qu'un `\r` résiduel fausse |
| **Validation du contenu comme diff réel** | Un fournisseur prétendant servir des diffs mais répondant avec du texte brut s'arrête ici, évitant d'être analysé comme du code |
| **Application des smart excludes** | Les fichiers de verrouillage (lockfiles) et ressources minifiées sont filtrés du diff *relu*, et non d'un diff local (§2.3) |

### 2.3 Exécution des Smart Excludes en Python

Chaque diff local reçoit ses exclusions intelligentes directement via git avec les pathspecs `:(exclude)`. Un diff parvenant par l'API ne transite jamais par git ; les mêmes motifs sont donc appliqués en Python, section de fichier par section de fichier, et les fichiers écartés sont signalés dans un avertissement :

```text
⚠️  3 file(s) skipped by the smart excludes: package-lock.json, poetry.lock, dist/app.min.js
```

La liste de motifs est identique à celle des flux locaux (`~/.gitpr/conf/gitpr.smart-excludes.json`), et la variable `GITPR_SKIP_SMART_EXCLUDES` la désactive également ici. Une pull request dont tous les fichiers seraient des lockfiles n'a rien à relire, et le signale explicitement au lieu de transmettre un diff vide au modèle.

### 2.4 Isolation en Cache Distincte de la Revue Locale

La clé de cache MD5 est calculée à partir du prompt, et le prompt provient du diff. Ainsi, une revue distante d'une branche se trouvant par hasard extraite localement générerait un prompt identique en octets et serait servie par le cache local préexistant. Le flux distant ajoute donc une portée distincte à la clé de cache :

```text
::diff-source::pr-123
```

Cette portée est ajoutée **uniquement** à la clé de cache — jamais au texte transmis à l'IA. L'impact pour les utilisateurs existants est nul : les flux locaux transmettent une portée vide, conservant des clés strictement identiques à celles d'origine et préservant les entrées de cache existantes.

### 2.5 Le Diff Relu Est Enregistré

La revue est stockée en cache avec le diff dont elle est issue, ce qui permet à `gitpr fix` d'appliquer des correctifs sur la révision exacte qui a été inspectée plutôt que de recalculer un diff depuis votre arbre. Pour une revue distante, c'est indispensable : la branche peut ne pas exister du tout localement. Consultez la [documentation de la commande Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=fr) pour comprendre sa restitution.

L'enregistrement est classé sous le dépôt et la branche **sur laquelle vous vous trouvez** — les mêmes champs que porte chaque revue en cache, puisque c'est ce que `gitpr fix` résout pour la retrouver. Les branches propres à la pull request sont notées à l'intérieur de l'entrée (dans le `{branch}` du nom de rapport et dans la source de diff), mais ne servent pas de clé de recherche : relire la PR #123 tout en étant sur `develop` classe la revue sous `develop`.

---

## 3. Forges Prises en Charge pour la Revue

Une revue nécessite un diff unifié, ce que toutes les forges ne fournissent pas.

| Forge | Revue Distante | Raison |
| --- | --- | --- |
| **GitHub** | Oui | `GET /repos/{owner}/{repo}/pulls/{n}/files` avec en-tête `Accept: application/vnd.github.diff` |
| **GitLab** | Oui | `changes[].diff` par fichier, avec en-têtes de fichier synthétisés (§3.1) |
| **Bitbucket** | Oui | `GET .../pullrequests/{n}/diff` |
| **Azure DevOps** | **Non** | Son API renvoie une liste de fichiers modifiés avec décompte de lignes, pas un diff unifié. Refusé avant tout appel réseau, avec un message renvoyant à la revue locale |

Cette capacité est déclarée par le fournisseur lui-même (`supports_reviewable_diff` sur le `ScmProvider`), de sorte qu'une nouvelle forge ajoutée ultérieurement affirme explicitement son support. Derrière cet indicateur opère une seconde vérification : le contenu téléchargé est contrôlé pour valider sa structure de diff, interceptant les fournisseurs qui déclareraient la capacité mais répondraient avec un résumé de fichiers (§2.2).

### 3.1 GitLab : Synthèse des En-têtes de Fichier

L'API de GitLab renvoie le champ `diff` de chaque fichier modifié sous la forme d'un hunk isolé, avec l'identité du fichier dans des champs séparés `old_path` / `new_path`. Sans retraitement, la revue recevrait des blocs anonymes — l'IA ne pourrait identifier à quel fichier se rattache une modification, et ni le filtre d'exclusions ni le découpage par lots ne pourraient fonctionner, ceux-ci dépendant de la ligne `diff --git a/…`. Le fournisseur reconstruit cet en-tête avant chaque bloc :

```diff
diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,2 @@
```

GitLab signale également lorsqu'il a tronqué un diff pour dépassement de taille maximale d'API (`overflow: true`). Un diff tronqué est incomplet et se trouve donc immédiatement refusé avec une instruction invitant à relire la merge request localement, évitant un examen partiel publié comme s'il était intégral.

---

## 4. Le Rapport, Avertissements et Échecs

### 4.1 Le Rapport

La sortie génère le même fichier que la revue locale, via le même moteur de rendu — bloc de linter en haut, revue par IA en bas — avec une nuance dans le nom : l'emplacement `{branch}` reprend la branche **source** de la pull request, nettoyée pour le système de fichiers (`feature/login` devient `feature-login`), car le rapport appartient à la révision examinée et non à votre branche courante. Une pull request sans nom de branche explicite se rabat sur `pr-123`.

```text
✅ Code Review successfully generated: 'feature-login_20260917143210_PR_REVIEW.txt'
```

Rien d'autre n'est affiché : la revue n'est jamais reproduite sur le terminal, à l'identique des flux locaux. Le chemin du rapport est configuré par `OUTPUT_FILE_NAME_REVIEW`, la même variable que celle de la revue locale — le mode distant n'introduit aucune nouvelle configuration.

### 4.2 Rejets Sans Coût de Quota

Tout ce sur quoi l'utilisateur peut intervenir est refusé **avant** tout appel à l'IA, garantissant qu'un mauvais numéro, une pull request fermée ou un token invalide ne consomment aucun token :

| Situation | Message |
| --- | --- |
| La forge ne fournit pas de diff relisible | `{provider} does not serve a reviewable diff: … Review this pull request locally, or use a forge that serves diffs.` |
| Le numéro n'existe pas | `Pull request #123 was not found in {repo}.` |
| Le token ne dispose pas des droits de lecture (401/403) | `No permission to read pull request #123 in {repo}. Check the token configured for {provider} (gitpr --init).` |
| Elle est fermée ou fusionnée | `Pull request #123 is not open (state: closed). Only open pull requests can be reviewed.` |
| Le diff est revenu vide | `Pull request #123 has no diff to review.` |
| Le résultat est revenu sous forme de résumé de fichiers | `{provider} returned a file summary instead of a diff for pull request #123. It cannot be reviewed.` |
| Tous les fichiers correspondent aux smart excludes | `Every file of pull request #123 matches the smart excludes — nothing left to review.` |
| Le modèle n'a rien renvoyé d'exploitable | `The AI returned no review for pull request #123.` |

Les quatre états ouverts parmi les forges prises en charge — GitHub `open`, GitLab `opened`, Azure `active`, Bitbucket `OPEN` — sont comparés sans distinction de casse. Un fournisseur qui ne renseigne aucun état est accepté, évitant un blocage sur un champ non garanti.

### 4.3 Avertissements

Les avertissements signalent des événements notables qui n'ont pas interrompu l'exécution. Ils sont affichés avant le rapport et, avec `--post-comment`, intégrés au commentaire publié — tout lecteur de la pull request a le droit de savoir si la revue a écarté des lockfiles.

| Avertissement | Circonstance |
| --- | --- |
| `{count} file(s) skipped by the smart excludes: {files}` | Le filtre a écarté au moins un fichier |
| `Large diff: processed in {count} batches (map-reduce).` | Le diff est suffisamment volumineux pour que le moteur le divise en lots |

Le nombre de lots est demandé au découpeur plutôt qu'extrait de la sortie terminal, assurant la compatibilité avec les outils MCP. Si le découpeur ne renvoie pas cette donnée, l'exécution se poursuit : l'avertissement est informatif et ne provoque jamais l'arrêt de la commande.

### 4.4 Une Exécution Échouée N'écrit Rien

Tout échec quitte avec le code de sortie 1, imprime la raison sur stderr et **n'écrit aucun rapport** — la présence d'un `.txt` sur le disque atteste d'une revue valide, empêchant qu'un échec ne soit confondu avec une revue sans problème. La commande n'effectue aucun nouvel essai : les exceptions sont levées en amont du moteur d'IA, évitant toute facturation secondaire.

---

## 5. Publication — `--post-comment`

Avec `--post-comment`, la revue est publiée sous la forme d'un commentaire sur la pull request elle-même. Il s'agit d'un commentaire unique, créé après le succès de la revue et l'exécution du linter, et constitue **toujours un nouveau commentaire** — une revue antérieure déposée par le même outil reste intacte, car écraser un commentaire auquel un tiers a pu répondre n'appartient pas à cette commande.

Le corps reprend le texte du rapport accompagné d'un pied de page :

```markdown
## 🚨 Local Static Analysis Alerts (YAML Rules)

- 🚨 console.log usage detected in app.js (Line 42)

---

## 🤖 AI Code Review

…

---

*Automated review by GitPR 1.1.0 — AI provider: Gemini. AI-generated content: verify before acting on it.*
```

Le pied de page assure la transparence sur la pull request d'un **tiers** : un lecteur n'ayant pas exécuté la CLI dispose ainsi de l'information selon laquelle le texte a été produit par un modèle. Les alertes sont composées par la fonction exacte qui élabore le `.txt`, garantissant une concordance totale entre le fichier et le commentaire.

Aucun SHA de commit n'y figure. La forge ne le mentionne pas dans la réponse du diff, et en inventer un dans un commentaire public serait moins fiable que de l'omettre.

Si la revue échoue, rien n'est publié — le commentaire n'existe qu'en aval d'une revue productive. Si la publication du commentaire échoue (par exemple, un token autorisé en lecture mais non en écriture), l'erreur remonte en tant qu'anomalie de forge et la commande se termine avec le code 1 : la revue a été générée, mais n'a pas pu être publiée.

---

## 6. Modèle de Skill — `.gitpr.review.md`

La revue distante utilise la même instruction système que la revue locale : `.gitpr.review.md` (persona et orientation de la revue), téléchargée via `gitpr --skill` — en respectant la langue active et sans écraser de fichier préexistant. Il n'existe pas de type de skill spécifique au mode distant ; si la lecture variait selon la provenance du diff, cela trahirait le principe d'un moteur unifié.

---

## 7. Intégration MCP

`review_remote_pr` est le 14e outil MCP et opère en mode de **lecture seule** : il passe en revue une pull request ouverte et renvoie la revue ainsi que les alertes du linter, sans possibilité de publier quoi que ce soit. Il ne propose pas d'argument `post_comment`, à dessein — un outil qu'un agent déclenche de façon autonome ne doit pas pouvoir écrire sur la pull request d'un utilisateur.

```json
{"status": "success", "pr_number": 123, "pr_url": "…", "head_branch": "feature/login",
 "base_branch": "main", "origin": "remote_pr", "linter": {…}, "warnings": [], "review": "…"}
```

Contrairement à la CLI, il n'écrit aucun fichier `.txt` — les outils MCP ne génèrent pas d'artefacts sur disque — et résout lui-même la forge, de sorte qu'un dépôt sans forge configurée répond par une erreur JSON invitant à exécuter `gitpr --init` plutôt que par un message de terminal. Le statut renvoyé est `error` avec le champ `message` pour chacun des rejets décrits au §4.2. Consultez la [documentation d'Intégration MCP](https://gitpr.natanfiuza.dev.br/docs/mcp-integration?lang=fr).

---

## 8. Variables d'Environnement

La revue distante **n'introduit aucune configuration nouvelle**. Elle exploite les variables déjà lues par la revue locale :

| Variable | Usage |
| --- | --- |
| `GITPR_SCM_PROVIDER` / `GITPR_SCM_TOKEN` / `GITPR_SCM_TOKEN_ENCRYPTED` | La forge et son token, configurés par `gitpr --init` |
| `GITPR_SCM_BASE_URL`, `GITPR_SCM_ORGANIZATION`, `GITPR_SCM_PROJECT`, `GITPR_SCM_USERNAME` | Paramètres complémentaires de forge (GitLab auto-hébergé, Azure, Bitbucket) |
| `OUTPUT_FILE_NAME_REVIEW` | Nom du rapport (par défaut `{branch}_{datetime}_PR_REVIEW.txt`) |
| `DEFAULT_AI_PROVIDER` | Moteur d'IA utilisé lorsque `--provider` n'est pas précisé |
| `GITPR_SKIP_SMART_EXCLUDES` | Désactive le filtre des smart excludes, en local comme à distance |

> **Remarque :** Consultez également la [documentation de Code Review avec l'IA](https://gitpr.natanfiuza.dev.br/docs/code-review-ia?lang=fr) pour découvrir les autres modes de revue et la [documentation de la commande Fix](https://gitpr.natanfiuza.dev.br/docs/fix-command?lang=fr) pour comprendre l'utilisation du diff enregistré.
