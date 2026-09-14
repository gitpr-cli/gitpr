# Documentation technique : Commande Fix (gitpr fix)

`gitpr fix` transforme les constats de la dernière revue de code en patches que vous lisez avant qu'ils ne touchent à votre arbre de travail. Une seule invocation résout la revue la plus récente du dépôt et de la branche courants, demande à l'IA le plus petit diff unifié qui corrige chaque problème signalé par la revue, classe chaque patch selon la confiance qu'il mérite et — uniquement sur demande — l'écrit dans l'arbre de travail et l'enregistre pour qu'il puisse être annulé. La lecture est le comportement par défaut : sans argument, la commande liste les candidats et n'écrit rien, un constat unique est présenté en dry-run, et l'écriture exige `--apply`.

---

## 1. Vue d'ensemble

La sous-commande est un ajout au CLI, pas une réécriture : chaque option héritée conserve sa signification, et `--force` s'applique ici sous `gitpr fix` (dans `gitpr release`, il signifie « régénérer une section de version existante »). Tout le flux est local — rien n'est commité, rien n'est poussé, aucune branche n'est créée avant qu'une écriture ne soit confirmée.

### 1.1 Référence de la commande — `gitpr fix`

Toutes les options de la sous-commande, telles qu'affichées par `gitpr fix -h` (ou `--help`) :

```bash
gitpr fix                      # liste les candidats de la dernière revue
gitpr fix FIX-001              # dry-run : le diff d'un constat, rien n'est écrit
gitpr fix FIX-001 --apply      # l'écrit, après une confirmation
gitpr fix --all-safe --apply   # écrit chaque patch sûr, sur une nouvelle branche par défaut
gitpr fix --rollback FIX-001-1a2b3c4d
```

| Option | Description |
| --- | --- |
| **`[<finding-id>]`** | Constat visé par l'exécution (`FIX-001`). Sans `--apply`, c'est un dry-run ; sans id et sans `--all-safe`, la commande liste à la place |
| **`--list`** | Liste les candidats de correction de la dernière revue — c'est ce que fait la commande sans argument |
| **`--apply`** | Écrit le patch dans l'arbre de travail. Sans cette option, l'exécution est un dry-run qui ne touche à rien |
| **`--all-safe`** | Sélectionne tous les patches classés comme sûrs. Les écrire nécessite encore `--apply` |
| **`--create-branch <name>`** | Crée et bascule sur cette branche avant d'appliquer les patches |
| **`--no-branch`** | Applique sur la branche courante même quand la configuration en créerait une |
| **`--yes`** | Ignore la confirmation. Ne dispense jamais de `--force` |
| **`--force`** | Applique un patch qui n'est pas sûr, après avoir saisi une phrase de confirmation |
| **`--rollback <patch-id>`** | Annule un patch appliqué auparavant, en lisant son diff dans l'historique local |

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Revue en cache la plus récente du dépôt et de la branche courants — `gitpr -r` ou `gitpr -f`, jamais l'audit de fichier (`-i`) |
| **Appel d'IA** | Un appel par revue, sur le modèle avancé du fournisseur configuré, mis en cache sous `fix/` comme tout autre appel GitPR |
| **Fichiers écrits** | Rien par défaut. `--apply` écrit dans l'arbre de travail et ajoute une entrée à `.gitpr/fix_history.json` |
| **Branche** | Uniquement un lot `--all-safe --apply`, et seulement quand la configuration le demande |
| **Annulation** | `--rollback <patch-id>` — pas de commit, pas de stash, pas de reset |
| **Code de sortie 1** | Aucune revue, aucune modification à corriger, pas de clé d'API, id de constat inconnu, patch non sûr sans `--force`, branche impossible à créer |

---

## 2. De la revue aux constats

### 2.1 La revue qu'il lit

`gitpr fix` ne réalise lui-même aucune revue : il consomme la dernière revue du dépôt et de la branche courants depuis le cache de prompts (`~/.gitpr/cache/prompts/review/`). Parmi les enregistrements en cache, il prend le plus récent dont le `repo` et la `branch` correspondent et dont l'`action_type` est `review` ou `fullreview` — les trois modes de revue partagent ce dossier, et un `filereview` (audit de fichier, `-i`) est exclu à dessein, car l'audit d'un seul fichier n'a pas de diff de branche à corriger.

Sans revue enregistrée, la commande s'arrête avec `❌ No review found for {repo} on branch '{branch}'. Run 'gitpr -r' first.` — « il n'y a pas de revue » et « la revue n'a rien trouvé » ne doivent jamais se ressembler.

### 2.2 Le diff est recalculé

Le *texte* de la revue vient du cache ; le *diff* est recalculé maintenant, avec la fonction même qui a produit la revue : `get_git_diff()` pour `review`, `get_git_full_diff()` pour `fullreview`, sélectionnée par l'`action_type` enregistré. C'est ce qui ancre le patch à l'arbre qui se trouve devant vous aujourd'hui plutôt qu'à celui du jour où la revue a été exécutée. Un arbre de travail sans aucune modification abandonne avec `❌ The working tree has no changes to apply fixes to. Make the changes and run 'gitpr -r' again.`

### 2.3 Un seul appel d'IA, et les ids qu'il produit

Un seul appel demande au modèle le plus petit diff unifié par constat de la revue, en renvoyant un objet JSON par constat. Il passe par l'infrastructure standard de GitPR (fournisseur configuré, modèle avancé, sortie JSON, nouvelle tentative) et par le cache MD5 standard dans `~/.gitpr/cache/prompts/fix/` — consultez la [documentation des Fournisseurs d'IA](providers-ia.md).

Les ids sont attribués par gitpr, jamais par le modèle : `FIX-001`, `FIX-002`, ... dans l'ordre de retour des constats. Comme le prompt est construit à partir de la même revue et du même diff, la réponse en cache est réutilisée et **les ids restent stables d'une exécution à l'autre** — l'id affiché par une liste est celui que `--apply` cible. Relancer `gitpr -r` produit une nouvelle revue, donc un nouveau prompt, de nouveaux constats et de nouveaux ids.

Un modèle qui répond en prose au lieu de l'enveloppe attendue est un résultat ordinaire, pas un plantage : l'exécution signale `ℹ️ The review raised no fixable findings.` et n'écrit rien.

| Champ | Signification |
| --- | --- |
| **`finding_id`** | `FIX-001` — attribué par gitpr, dans l'ordre de retour des constats |
| **`file_path`** | Le chemin que le patch touche. Le patch fait foi ; le `file_path` du modèle lui-même sert de repli pour un constat qui n'a aucun patch |
| **`line_start` / `line_end`** | La plage de lignes visée par la revue (0 quand le modèle n'en a signalé aucune) |
| **`severity` / `category`** | Tels que déclarés par la revue (`critical`, `major`, `minor`, `info` / `bug`, `security`, ...) — enregistrés, jamais recalculés |
| **`message`** | Le constat, dans la langue de l'interface |
| **`confidence`** | `high` / `medium` / `low` tels que déclarés par le modèle ; `low` force la classe `experimental` |
| **`diff`** | Le diff unifié qui corrige le constat — le patch lui-même |
| **`suggested_test`** | Ce que le modèle suggère pour couvrir la correction |
| **`patch_id`** | `FIX-001-1a2b3c4d` — l'id du constat suivi des 8 premiers chiffres hexadécimaux du MD5 du diff ; ce que `--rollback` cible |

---

## 3. Classification de sécurité

La classification est déterministe et n'implique aucune IA : le même résumé de patch et les mêmes paramètres donnent toujours le même verdict, donc un patch classé `safe` lors d'un dry-run reste `safe` quand `--apply` s'exécute. `git apply --check` est évalué en premier — un patch qui ne s'applique pas à l'arbre courant n'est jamais autre chose.

| Classe | Critères | Ce que cela ouvre |
| --- | --- | --- |
| **`safe`** | S'applique proprement, un fichier, un hunk, dans la limite de lignes modifiées, hors des chemins sensibles, et ne supprime aucune ligne qui ressemble à un appel | `--all-safe --apply` peut l'inclure dans un lot |
| **`review_required`** | S'applique proprement, mais au moins une condition de `safe` a échoué | `--apply` sur ce constat, avec une confirmation |
| **`experimental`** | Ne s'applique pas à cet arbre, couvre plus d'un fichier, ou le modèle a déclaré une faible confiance | Jamais inclus dans un lot. `--force` avec une phrase saisie est la seule porte |

### 3.1 Codes de raison

Le verdict porte toujours une raison — la première condition déclenchée, dans cet ordre :

| Code de raison | Signification |
| --- | --- |
| `apply_check_failed` | Il ne s'applique pas à l'arbre actuel |
| `multi_file` | Il modifie plus d'un fichier |
| `low_confidence` | L'IA a déclaré une faible confiance |
| `excluded_path` | Il touche un chemin sensible configuré |
| `multiple_hunks` | Il couvre plus d'un hunk |
| `too_many_lines` | Il modifie plus de lignes que la limite configurée |
| `removes_call` | Il supprime une ligne qui ressemble à un appel |
| `safe` | Aucune condition n'a échoué |

Le terminal transforme chaque code en une phrase traduite ; l'outil MCP rapporte le code lui-même, afin que ses appelants puissent s'appuyer sur une chaîne stable.

### 3.2 Remarques sur les critères

Un constat auquel le modèle a répondu sans patch utilisable devient quand même un candidat, classé `experimental` avec un diff vide. L'écarter masquerait un problème signalé par la revue, et le diff vide est la vérité — git le refuse, il ne peut donc jamais être appliqué par accident.

L'heuristique d'appel est délibérément grossière : toute ligne supprimée correspondant à `\w+` suivi d'une parenthèse ouvrante la déclenche, y compris un commentaire supprimé qui ne fait que mentionner `foo()`. Elle penche vers `review_required`, ce qui est la bonne direction pour se tromper.

Les chemins sensibles relèvent du *risque* (migrations, workflows, docker, terraform), pas du bruit dans le diff — c'est pourquoi ils constituent une configuration à part et ne sont pas partagés avec la liste smart-excludes.

---

## 4. Lire avant d'écrire

### 4.1 Lister les candidats

Sans id de constat, `gitpr fix` (ou `gitpr fix --list`) affiche chaque candidat de la dernière revue — classe, emplacement, message et id de patch — et n'écrit rien :

```text
🔎 Fix candidates from the last review:
  FIX-001  [safe]  src/core.py:210
     The retry loop swallows the exception.
     ↳ FIX-001-1a2b3c4d
  FIX-002  [review_required]  src/config.py:88
     The default timeout is duplicated.
     ↳ FIX-002-9f8e7d6c — it changes more lines than the configured limit
ℹ️ Apply one with 'gitpr fix <id> --apply'; the safe ones can be batched with '--all-safe --apply'.
```

La classe est colorée en vert (`safe`), jaune (`review_required`) ou rouge (`experimental`), et la phrase de raison n'apparaît que pour les deux classes non sûres.

### 4.2 Dry-run — `gitpr fix <id>`

Avec un id de constat et sans `--apply`, l'exécution affiche le bloc du candidat, tout le diff unifié dans les couleurs de terminal utilisées dans le projet, chaque avertissement, et se termine par `ℹ️ Dry run — nothing was written. Add --apply to write it.` Rien n'est touché dans l'arbre. Quand une branche serait créée, l'exécution le dit (`ℹ️ Branch '{branch}' would be created before the patches are applied.`), et un dry-run `--all-safe` liste en plus les candidats qu'il a laissés de côté, chacun avec l'id qui permet de le reprendre.

### 4.3 Écrire — `--apply`

Un patch qui n'est pas classé `safe` n'est jamais écrit par un simple `--apply` : l'exécution affiche le constat, sa classe et sa raison, puis se termine avec le code 1 (`❌ {finding_id} is {safety} ({reason}) — re-run with --force to apply it anyway.`).

```bash
gitpr fix FIX-001 --apply
gitpr fix --all-safe --apply
gitpr fix FIX-002 --apply --force
```

Pour un patch `safe`, l'exécution demande `❓ Apply FIX-001 to the working tree?` (refuser est le choix par défaut) ; refuser affiche `❌ Operation cancelled by user.` et laisse l'arbre intact. `--yes` ou `GITPR_FIX_REQUIRE_CONFIRMATION=false` ignore cette invite.

`--force` s'ouvre sur une phrase à saisir plutôt qu'un o/n : l'exécution affiche la classe et la raison, puis demande que la phrase `apply FIX-001` soit saisie exactement (espaces superflus ignorés, insensible à la casse). Une non-concordance interrompt avec `❌ The confirmation phrase does not match. Nothing was applied.` et le code de sortie 1 — `--yes` ne dispense pas de cette invite. `--force` combiné à `--all-safe` avertit seulement qu'il est sans effet, puisque seuls les patches sûrs sont sélectionnés. `gitpr fix --apply` sans id de constat et sans `--all-safe` avertit (`⚠️ Nothing was selected: name a finding id or add --all-safe.`) et liste les candidats à la place.

Un patch que git refuse est signalé comme un échec avec le message de git lui-même et le lot continue — l'échec d'un candidat ne dit rien du suivant. Rien n'est enregistré dans l'historique pour lui : l'enregistrement existe pour annuler ce qui a été appliqué, et rien ne l'a été. Chaque patch écrit est signalé par `✅ Patch applied: FIX-001-1a2b3c4d (src/core.py)`.

### 4.4 Gestion des branches

| Situation | Comportement |
| --- | --- |
| `--all-safe --apply` avec `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE=true` | Crée `GITPR_FIX_BRANCH_NAME_TEMPLATE` (par défaut `fix/gitpr-{datetime}`) depuis le `HEAD` courant et y applique le lot ; la branche d'origine reste intacte |
| `--create-branch <name>` | Crée cette branche à la place (toute exécution) |
| `--no-branch` | Applique sur la branche courante même quand la configuration en créerait une |
| Constat unique ou dry-run | Ne crée jamais de branche |

La branche est créée une seule fois, avant le premier patch, et uniquement lors d'une exécution réelle. Une branche qui ne peut pas être créée interrompt le lot — continuer appliquerait les patches à la branche que l'utilisateur cherchait à quitter.

### 4.5 Un fichier déjà modifié

Quand un patch cible un fichier qui a déjà des modifications non commitées, l'exécution avertit précisément sur ces fichiers (`⚠️ These files already have uncommitted changes: ...`) avant d'écrire. Avertir sur chaque fichier modifié du dépôt se déclencherait à presque chaque exécution réelle ; seul le recoupement entre le patch et les modifications en attente est le cas où l'application peut surprendre l'utilisateur.

---

## 5. Historique et annulation

### 5.1 `.gitpr/fix_history.json`

Chaque patch appliqué est enregistré dans `<root>/.gitpr/fix_history.json`, **suivi par git** — le diff complet y est stocké précisément pour que le patch puisse être annulé sans commit. Le fichier est écrit de façon atomique (un fichier voisin temporaire renommé à sa place), de sorte qu'une écriture interrompue ne laisse jamais un historique à moitié écrit. La conséquence de ce suivi est délibérée et connue : appliquer une correction modifie un fichier suivi, qui apparaît donc dans `gitpr -c` et dans les descriptions de PR jusqu'à ce qu'il soit commité — c'est pourquoi `.gitpr/fix_history.json` figure dans la liste smart-excludes et reste hors des diffs envoyés à l'IA.

| Champ | Signification |
| --- | --- |
| **`patch_id`** | `FIX-001-1a2b3c4d` — ce que `--rollback` cible |
| **`finding_id`** | `FIX-001` |
| **`file_path`** | Le fichier visé par la revue |
| **`files_changed`** | Chaque chemin que le diff touche |
| **`safety`** | `safe` / `review_required` / `experimental` au moment de son application |
| **`branch`** | La branche sur laquelle le patch a été appliqué (`null` quand il a été appliqué sur place) |
| **`applied_at`** | Horodatage, dans le format de cache du projet |
| **`diff`** | Le diff unifié complet, verbatim |
| **`provenance`** | Fournisseur, modèle, version du prompt, version de gitpr, horodatage de génération |
| **`rolled_back_at`** | Horodatage une fois annulé, sinon `null` |

### 5.2 `--rollback <patch-id>`

L'annulation lit le diff stocké et le rejoue avec `git apply --reverse` — pas de commit, pas de stash, pas de reset, et aucune dépendance à ce que l'arbre de travail corresponde encore à ce qui a été appliqué. Git lui-même vérifie l'inversion par rapport au fichier : si l'arbre a évolué, l'inversion échoue, l'erreur est signalée et aucun fichier n'est laissé à moitié écrit. En cas de succès, l'exécution affiche `ℹ️ Undone patch {patch_id}: {files} restored.` et marque l'entrée comme annulée.

| Refus | Message |
| --- | --- |
| Aucun id de patch de ce type dans ce dépôt | `❌ No applied patch with id '{patch_id}' was recorded here.` |
| Déjà annulé | `❌ Patch '{patch_id}' was already rolled back at {when}.` — annuler deux fois est une erreur, pas une opération sans effet |
| Appliqué sur une autre branche | `❌ Patch '{patch_id}' was applied on branch '{branch}': switch back to it to undo the patch.` — le fichier à restaurer n'est pas ici |
| L'arbre a évolué de façon incompatible | `❌ Could not undo patch '{patch_id}': {error}` — le message de git lui-même, sans fichier laissé à moitié écrit |

`--rollback` n'accepte pas d'id de constat et ne se combine ni avec `--apply` ni avec `--all-safe`.

---

## 6. Template Skill — `.gitpr.fix.md`

L'appel des constats utilise le fichier `.gitpr.fix.md` comme system instruction de l'IA (persona : **Senior Software Engineer**, normalisant la revue en patches minimaux). Le template est téléchargé par `gitpr --skill` — selon la langue (`gitpr.fix.md` pour l'anglais, `gitpr.fix.pt_br.md` pour le PT-BR) et sans jamais écraser un fichier local existant. Sans lui, la persona intégrée est utilisée.

Le template énonce le contrat dont dépend le pipeline : le patch est la source de vérité, un hunk dans un fichier, ne jamais reformater du code non touché, ne jamais supprimer un appel ou une garde existants, déclarer une `confidence` honnête, et laisser le `diff` vide quand le constat nécessite une décision humaine. Modifiez-le localement pour changer la façon dont les patches sont écrits ; le prompt est construit à partir de lui, donc une modification produit un nouveau prompt et un nouvel appel d'IA. Consultez la [documentation de Skills et Templates](skill-template.md) pour le mécanisme général.

---

## 7. Intégration MCP

`list_fix_candidates` est le 13e outil MCP et est **en lecture seule** : il rapporte ce que `gitpr fix` pourrait appliquer, patch inclus, et n'écrit jamais dans l'arbre de travail. L'argument optionnel `finding_id` restreint la réponse à un seul constat.

```json
{"status": "success", "finding_count": 2, "candidates": [ ... ]}
```

Chaque candidat porte `finding_id`, `patch_id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`, `safety`, `safety_reason` (le code stable, pas une phrase), `confidence`, `suggested_test` et `diff`. Le statut est `no_data` quand la revue n'a rien signalé qui puisse devenir un patch, et `error` avec un `message` quand il n'y a aucune revue à lire ou que le pipeline ne peut pas s'exécuter du tout. Consultez la [documentation d'Intégration MCP](mcp-integration.md).

---

## 8. Variables d'environnement

La configuration de la correction est lue depuis le fichier global `~/.gitpr/.env` (format dotenv). Les deux booléens suivent la convention « false désactive » : non défini ou toute valeur autre que `false` / `0` / `no` / `off` / `n` signifie activé — les valeurs par défaut du tableau s'appliquent quand la variable n'est pas définie.

| Variable | Valeur par défaut | Objet |
| --- | --- | --- |
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | `5` | Lignes ajoutées plus supprimées qu'un patch peut comporter et rester `safe` ; une valeur non positive ou illisible retombe à `5` |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | `database/migrations/**;**/*.ci.yml;docker/**;terraform/**;.github/workflows/**` | Chemins sensibles, séparés par des `;`. Un patch qui en touche un s'applique quand même, mais n'est jamais `safe` |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | `true` | Demande une confirmation avant d'écrire un patch sûr ; `false` l'ignore (`--yes` fait de même pour une exécution) |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `true` | `--all-safe --apply` crée une branche avant d'écrire ; `--no-branch` la remplace pour une exécution |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | `fix/gitpr-{datetime}` | Nom de cette branche. Espaces réservés : `{branch}` (branche courante) et `{datetime}` |

> **Note :** Consultez également la [documentation de Skills et Templates](skill-template.md) pour personnaliser les fichiers de modèles d'IA de GitPR.
