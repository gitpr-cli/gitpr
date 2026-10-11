# Documentation Technique : Baseline et suppressions auditables (`gitpr baseline`)

Adopter GitPR dans un dépôt legacy, c'est le moment où l'outil est le moins utile : le linter signale quatre cents problèmes préexistants, le ruleset de secrets repère une clé synthétique dans un fixture de test, et la première pull request de la migration échoue sur un portail qui n'a rien à voir avec le changement qu'elle contient. L'équipe a deux options, et les deux sont mauvaises — éteindre le portail, ou passer un sprint à corriger du code que personne ne touche.

Un **baseline** est la troisième option. C'est un fichier, commité dans Git, qui enregistre les constats que le dépôt a déjà. À partir de là, une exécution classe chaque constat qu'elle rencontre : ceux qui sont dans le fichier sont **existing**, ceux qui y étaient et ont disparu sont **resolved**, et seul ce que *ce changement* a introduit est **new** — et seul `new` bloque. Le portail devient une affirmation sur le diff au lieu d'une affirmation sur l'histoire du dépôt.

Avec le registre vient la piste d'audit : une suppression n'est pas un filtre silencieux, c'est une décision avec un **motif**, un auteur et une date ; la dette acceptée a un **responsable** et, en option, une **échéance** ; et un checksum sur le fichier entier attrape une modification faite hors de GitPR. Tout ce que l'outil décide au sujet d'un constat peut être relu et contesté.

Sans fichier de baseline, chaque commande se comporte exactement comme avant l'existence de cette fonctionnalité — même sortie, mêmes exit codes, mêmes clés de cache.

---

## 1. Vue d'ensemble

```bash
gitpr baseline create                    # Enregistre le diff actuel comme baseline
gitpr baseline show                      # Les constats, les décisions et les décomptes
gitpr baseline validate                  # Chaque défaut du fichier, exit 1 sur n'importe lequel
gitpr baseline update                    # Enregistre ce que le diff montre aujourd'hui, en gardant les décisions
gitpr baseline suppress <id> --reason "…"    # Une décision au sujet d'un constat
gitpr baseline unsuppress <id>           # Retire une décision
```

| Commande | Écrit | Description |
|---|---|---|
| **`create`** | `.gitpr/baseline.json` | Enregistre les constats du diff actuel comme point de départ. `--base <ref>` enregistre le diff contre une ref au lieu de l'arbre de travail ; `--refresh` relance la revue IA au lieu de réutiliser celle en cache ; `--format json` pour la CI |
| **`show`** | — | Décomptes par état et liste de chaque constat qui porte une décision, avec son motif, sa portée et son origine. `--status`, `--rule`, `--file` filtrent ; `--format json` émet les entrées |
| **`validate`** | — | Chaque problème que le fichier et les overrides peuvent avoir : schéma, version de fingerprint, compatibilité, checksum, fingerprints dupliqués, champs inconnus, dette échue. Exit 1 sur n'importe lequel |
| **`update`** | `.gitpr/baseline.json` | Réenregistre ce que le diff montre aujourd'hui, en marquant ce qui a disparu comme `resolved` et en gardant chaque décision. Refuse un fichier dont le checksum diverge, sauf si `--recompute` est donné |
| **`suppress`** | l'entrée, ou `.gitpr/baseline.overrides.yml` | Enregistre une décision au sujet d'un constat. `--reason` est obligatoire ; `--scope finding\|line\|file\|rule` ; `--debt --owner <qui> [--due-date YYYY-MM-DD]` enregistre une dette au lieu d'une suppression |
| **`unsuppress`** | l'entrée, ou le fichier d'overrides | Retire une décision. Une décision plus large que ce constat-là est *signalée*, jamais supprimée — elle se modifie là où elle vit |

Toute commande qui écrit accepte `--yes`, qui répond à la confirmation sans sauter les vérifications derrière. Sans terminal et sans `--yes`, la commande échoue avec l'instruction au lieu de se bloquer sur une invite que personne ne lira.

### 1.1 Ids de constat

Un constat se nomme sur la ligne de commande par un **préfixe unique de son fingerprint**, que `show` imprime et que `suppress` accepte :

```
sha256:ab12cd34ef56…
```

Un id qui ne correspond à aucun constat, ou à deux, est refusé — et le refus dit lequel des deux cas, parce que l'id est la seule prise que l'utilisateur a sur le constat.

---

## 2. Les cinq états

| État | Signification | Persisté |
|---|---|---|
| **`new`** | Le constat n'est pas dans le baseline. C'est tout l'objet de la fonctionnalité, et le seul état qui bloque | **jamais** |
| **`existing`** | Le constat est enregistré et toujours là. Rien n'est dit sur sa qualité — il est connu | oui |
| **`resolved`** | Le constat était enregistré et n'apparaît plus, dans un fichier que le diff actuel touche | oui |
| **`ignored`** | Un humain l'a regardé et a décidé qu'il reste, avec un motif | oui |
| **`accepted_debt`** | Un humain a décidé qu'il sera corrigé, avec un responsable et un motif énoncé — et en option une échéance | oui |

`new` n'est jamais écrit dans le fichier : une entrée enregistrée comme « new » serait périmée dès l'exécution suivante, et un fichier qui enregistre sa propre comparaison est un fichier qui ment.

`resolved` ne s'applique qu'aux entrées dont le **fichier apparaît dans le diff actuel**. Un fichier hors du diff peut être intact pour des raisons qui n'ont rien à voir avec le constat — le diff ne l'atteint simplement pas — et appeler cela « resolved » serait une affirmation fausse au seul endroit que l'équipe lit comme un registre. La règle plus étroite fait qu'un diff qui rétrécit n'invente jamais une résolution.

---

## 3. Ce qui bloque, et ce que ça coûte

| Surface | Effet du baseline |
|---|---|
| `gitpr -l` / `--linter` | Sort avec 1 seulement quand un constat de niveau **error** est `new`. Les constats existing, ignored et accepted sont affichés avec leur état et leur motif, et l'exécution continue |
| `gitpr -r`, `-f`, `-i` | La revue annote chaque constat avec son état. La revue n'a jamais été un portail, donc aucun exit code ne change |
| `gitpr risk` | Seuls les constats `new` comptent. Tout le reste est attaché comme preuve informative valant **zéro point**, avec son état dans `details`, pour que le chiffre de risque décrive le changement plutôt que le dépôt |
| `gitpr review-pr` | Résout la politique et le baseline par elle-même, en annotant les constats du linter, la section de risque et le commentaire de la PR |
| Tout le reste (`-c`, description de PR, blame, issue, chat, release, split, fix) | Le baseline n'est pas consulté du tout |

Un avertissement destructif, une alerte ignorée ou une échéance dépassée ne font jamais échouer une exécution à eux seuls : une échéance dépassée est un avertissement, imprimé à côté du rapport.

---

## 4. Configuration

Quatre variables dans `~/.gitpr/.env`, également modifiables via `gitpr config` dans la section **Baseline** :

| Clé | Défaut | Effet |
|---|---|---|
| `GITPR_BASELINE_ENABLED` | `true` | `false` → aucune exécution ne lit le baseline ; le comportement d'avant la fonctionnalité, octet pour octet |
| `GITPR_BASELINE_PATH` | *(vide)* | `.gitpr/baseline.json` par défaut. Un chemin relatif se résout depuis la racine du dépôt — c'est ainsi qu'on pointe vers un monorepo ou un baseline partagé ailleurs |
| `GITPR_BASELINE_REQUIRE_LOCKFILE_CHECKSUM_MATCH` | `true` | Un checksum divergent rend le baseline inutilisable : l'exécution refuse, imprime l'instruction et sort avec un code non nul dans les flux qui bloquent. Désactivé, le fichier est appliqué et la divergence est quand même signalée comme avertissement |
| `GITPR_BASELINE_ALLOW_LOCAL_OVERRIDES` | `true` | `false` → `.gitpr/baseline.overrides.yml` n'est pas lu, avec un avertissement. Les décisions écrites dans le fichier de baseline restent seules |

L'interrupteur maître échoue en ouvert — seuls `false`, `0`, `no`, `off` ou `n` le désactivent.

---

## 5. Le fichier

`.gitpr/baseline.json`, commité avec le code :

```json
{
  "schema_version": 1,
  "fingerprint_version": "1",
  "policy_name": "acme/team-policy",
  "policy_version": "1.0.0",
  "gitpr_version": "0.0.37",
  "created_at": "2026-10-10T09:12:44+00:00",
  "updated_at": "2026-10-10T09:12:44+00:00",
  "checksum": "sha256:…",
  "entries": [
    {
      "fingerprint": "sha256:…",
      "rule_id": "sec-aws-key",
      "category": "security",
      "file_path": "tests/fixtures/keys.py",
      "line_start": 18,
      "line_end": 18,
      "severity": "error",
      "source": "linter",
      "status": "ignored",
      "low_confidence": false,
      "first_seen_commit": "a1b2c3d",
      "last_seen_commit": "a1b2c3d",
      "first_seen_date": "2026-10-10",
      "last_seen_date": "2026-10-10",
      "resolved_at": null,
      "suppressed": true,
      "suppression_reason": "Synthetic key in a fixture; never used to reach a service.",
      "suppression_scope": "finding",
      "suppressed_by": "alice",
      "suppressed_at": "2026-10-10",
      "accepted_debt_owner": null,
      "accepted_debt_due_date": null,
      "accepted_debt_reason": null,
      "provenance": {"origin": "local", "command": "baseline suppress", "policy": null}
    }
  ]
}
```

Trois propriétés du format comptent :

1. **Aucune entrée ne porte de message, et aucune ne porte de code.** La prose qu'émet une règle appartient à la règle — la reformuler ressemblerait à un changement de baseline — et le baseline est commité dans Git, donc persister la ligne fautive mettrait dans le dépôt précisément le secret que le ruleset a signalé. Seul un *digest* de cette ligne est stocké.
2. **Les entrées sont écrites dans l'ordre des fingerprints.** Le fichier est commité, et deux exécutions sur les mêmes constats, sur deux machines, doivent produire le même diff.
3. **Le checksum ne se couvre pas lui-même.** C'est le SHA-256 du JSON canonique (clés triées, sans espaces, entrées ordonnées) de tous les autres champs. Modifier une entrée à la main dans un éditeur — changer un numéro de ligne, inverser un état — le casse, et `gitpr baseline validate` nomme la divergence au lieu d'appliquer le fichier.

`gitpr baseline update --recompute` est la façon sanctionnée d'accepter un fichier modifié à la main : il réécrit le checksum sur le contenu qu'il trouve, pour que la modification devienne un changement dans l'histoire Git avec un commit derrière, plutôt qu'une divergence silencieuse.

---

## 6. Le fingerprint

Un constat est identifié par un SHA-256 sur huit lignes, dans cet ordre :

```
1  FINGERPRINT_VERSION      ("1")
2  rule_identity            le rule id, ou "category:<catégorie>" quand il n'y en a pas
3  category                 en minuscules
4  normalize_path           relatif au dépôt, barres obliques, minuscules
5  source                   linter | ai | external | …
6  line_start
7  line_end
8  snippet_hash             digest de la ligne fautive, espaces réduits
```

Délibérément **absents** du payload : le message, le timestamp, le provider et le modèle, la branche, le chemin absolu du checkout. Deux exécutions sur la même révision produisent le même fingerprint sur n'importe quelle machine, et un build sur un chemin différent ne change rien.

Ce que cela signifie en pratique :

| Changement | Effet |
|---|---|
| Le message de la règle est reformulé | Même fingerprint — un message n'est pas une identité |
| La ligne est réindentée ou espacée autrement | Même fingerprint — les espaces sont réduits avant le hachage |
| Le contenu de la ligne change | **Nouveau fingerprint** — une ligne différente est un constat différent |
| Une ligne est insérée au-dessus du constat, le décalant | **Nouveau fingerprint** — les numéros de ligne font partie de l'identité |
| Le fichier est renommé | **Nouveau fingerprint** — le chemin fait partie de l'identité |
| L'analyse tourne sur une autre machine, une autre branche, un autre provider | Même fingerprint |
| Le constat vient de l'IA et ne porte pas de rule id | L'identité retombe sur la catégorie, et `low_confidence` est mis à `true` sur l'entrée |

Le biais vers `new` est délibéré. Un faux `new` est visible dans le rapport et se corrige en une commande (`gitpr baseline update`) ; un faux `existing` ferait taire un constat qui n'est pas du tout le même constat — et celui qu'il ferait taire pourrait être un vrai secret. Les numéros de ligne sont dans le payload pour la même raison.

`FINGERPRINT_VERSION` est la **première** ligne du payload, donc changer l'algorithme change tous les fingerprints d'un coup, invalidation de tout baseline comprise — une migration, pas une réinterprétation silencieuse. Le manifeste enregistre la version avec laquelle il a été écrit, et un fichier écrit sous une autre version est refusé avec l'instruction.

---

## 7. Décisions : suppressions et dette acceptée

Une décision s'enregistre à l'un de deux endroits, du plus étroit au plus large :

1. **Sur l'entrée** — une suppression de portée `finding`, ou une dette acceptée. Un fingerprint, un constat.
2. **Dans `.gitpr/baseline.overrides.yml`** — tout ce qui est plus large : une règle, un fichier, une plage de lignes. Ce fichier est additif et modifiable à la main, et c'est là qu'une équipe énonce une politique sur une *classe* de constats.

```yaml
overrides:
  suppressions:
    - fingerprint: "sha256:…"
      scope: finding
      reason: "Clé synthétique dans un fixture ; jamais utilisée pour atteindre un service."
      by: "alice"
      date: "2026-10-10"
    - scope: rule
      rule_id: "warning-todo-fixme"
      reason: "La règle est une aide à la décision, pas un portail, dans cet arbre legacy."
    - scope: file
      rule_id: "php-tabs"
      file_path: "app/Legacy/*"
      reason: "Fichiers générés, réécrits à chaque migration."
    - scope: line
      rule_id: "php-tabs"
      file_path: "app/Old.php"
      line_start: 100
      line_end: 120
      reason: "Bloc legacy en cours de migration ce trimestre."
  accepted_debt:
    - fingerprint: "sha256:…"
      owner: "time-backend"
      reason: "Migration prévue pour le trimestre prochain."
      due_date: "2026-12-31"
```

| Portée | Atteint | Notes |
|---|---|---|
| `finding` | Un fingerprint exact | La plus étroite, et la seule enregistrée sur l'entrée elle-même |
| `line` | Une règle, dans un fichier, à l'intérieur d'une plage de lignes qui **contient** celle du constat | Ignore le digest de contenu, donc elle survit aux modifications à l'intérieur du bloc — c'est pourquoi elle exige toujours un motif |
| `file` | Une règle, dans un fichier ou un glob de chemin | La même idée que le linter a déjà dans `ignore_paths` |
| `rule` | Une règle, partout dans le dépôt | La plus large |

La correspondance la plus spécifique l'emporte et fournit le motif montré au lecteur. Deux invariants sont garantis dans le code, et non par la configuration :

- Une suppression a un **motif** non vide. Une décision que personne n'a expliquée n'est pas une décision ; c'est un filtre.
- La dette acceptée a un **responsable**. Une dette que personne n'assume n'est pas acceptée, elle est oubliée.

Une échéance est optionnelle. Une échéance **dépassée** est un avertissement imprimé à côté du rapport et un problème pour `gitpr baseline validate` — jamais un échec de l'exécution elle-même.

Il existe une troisième couche que le dépôt n'écrit pas : un **Policy Pack** actif peut porter son propre bloc `baseline:` (voir `docs/policy-packs.md`). Ces décisions sont appliquées en mémoire pendant la classification, affichées avec l'origine `policy:<nom>@<version>`, et jamais écrites dans `.gitpr/baseline.json` — le pack est une opinion partagée, le fichier est le registre propre du dépôt. `gitpr baseline unsuppress` n'en supprime aucune : il dit quel pack la porte.

---

## 8. Le flux sur un dépôt legacy

```bash
# 1. Sur la branche de migration, enregistrez ce qui est déjà là.
gitpr baseline create --yes

# 2. Commitez le registre avec le code qu'il décrit.
git add .gitpr/baseline.json && git commit -m "chore: record the baseline"

# 3. Travaillez. Seul ce que le changement introduit est nouveau.
gitpr -l
gitpr -r
gitpr risk
```

Le registre se relit comme n'importe quel autre fichier. Ce qu'un relecteur cherche :

| Dans le diff | Lecture |
|---|---|
| Une nouvelle entrée avec `status: "existing"` et aucune décision | L'auteur a reconnu un constat préexistant. Normal, mais si le décompte grimpe de plusieurs centaines en un seul commit, le baseline a probablement été enregistré contre la mauvaise ref |
| Une nouvelle entrée avec `suppressed: true` et un `suppression_reason` | Une décision. Le motif est ce qui est sous revue — un motif qui répète la règle (« c'est bruyant ») n'explique rien ; un motif qui énonce la situation (« fichier généré, réécrit par la migration ») est auditable |
| Une nouvelle entrée avec `accepted_debt_owner` | Une dette que quelqu'un assume, avec une échéance que `gitpr baseline validate` ira réclamer |
| `.gitpr/baseline.overrides.yml` ajoutant une portée `rule` ou `file` | Le type de changement le plus large dans la posture du dépôt. Il fait taire une classe de constats, pas un seul |
| Des entrées passant à `status: "resolved"` | Une bonne nouvelle, et peu coûteuse à vérifier : le constat a disparu d'un fichier que le diff touche |
| Le `checksum` qui change sans rien d'autre | Rien d'autre n'a été touché — mais une modification à côté aurait été attrapée |

Les chemins `.gitpr/baseline.json` et `.gitpr/baseline.overrides.yml` sont dans `templates/gitpr.smart-excludes.json` : ce sont des registres, pas du code, et ils ne sont jamais envoyés à l'IA comme partie d'un diff.

`create` n'a pas de dry run : il écrit le registre et `gitpr baseline show` le relit, voilà l'aperçu. Pour enregistrer un diff contre une autre ref, `create --base <ref>` et `risk --base <ref>` sont la paire qui doit s'accorder — un baseline enregistré depuis `HEAD` classe presque tout comme `new` quand l'exécution de risque interroge une branche.

---

## 9. Le lire depuis un agent d'IDE (MCP)

Le serveur MCP expose le registre en lecture seule, pour qu'un agent puisse demander ce que le dépôt sait déjà avant de lire un rapport :

| Surface | Ce qu'elle répond |
|---|---|
| Tool `get_baseline_status` | Le résumé en JSON : entrées par état, règles les plus bruyantes, décisions par origine et portée, dette acceptée avec responsable et échéance, dette échue, et l'état du checksum |
| Resource `baseline://summary` | Le même résumé, comme resource |

Les deux renvoient `baseline_summary()`, qui ouvre le fichier, compte ce qu'il contient et s'arrête : aucun linter, aucun appel IA, aucune résolution de politique, aucune écriture. Un fichier qui ne peut pas être appliqué est *signalé* — `usable: false` avec les `problems` qui l'expliquent — jamais levé en exception, parce que « le registre est là et le portail le refuserait » est une des réponses que l'appelant est venu chercher. Le résumé lit les mêmes couches que le portail, donc `.gitpr/baseline.overrides.yml` et le bloc `baseline:` du pack actif apparaissent dans ses décomptes.

`counts.new` vaut toujours `0`, et la réponse dit pourquoi dans `counts_note` : `new` est le résultat de la comparaison d'une exécution avec le registre, pas quelque chose qu'un fichier peut contenir.

---

## 10. Limites, dites sans détour

- **Une ligne déplacée est un nouveau constat.** Délibéré, et expliqué plus haut. `gitpr baseline update` le réenregistre ; le registre garde la `first_seen_date` de ce qu'il reconnaît.
- **Un constat rapporté par l'IA est de faible confiance.** Il n'a pas de rule id, donc son identité est sa catégorie et son emplacement — deux problèmes différents sur la même ligne, rapportés par deux exécutions de revue différentes, ne font qu'une identité pour le baseline. L'entrée dit `low_confidence: true` pour que le lecteur puisse peser.
- **Le chemin map-reduce n'a pas de constats.** Pour un diff trop grand pour un seul appel, l'IA répond en prose, et la prose n'a pas de constat à enregistrer ; `create` dit combien viennent de la revue IA, pour que la différence soit visible.
- **`create` ne lit la revue en cache que si le diff correspond.** Le cache indexe une revue par son prompt, donc `create` compare le `diff` à partir duquel la revue a été faite avec l'actuel ; une divergence est signalée et la revue n'est pas consultée.
- **Il n'y a pas de `gitpr check`, ni d'export SARIF.** Le baseline est du JSON et se consomme par tout ce qui lit du JSON ; un portail de CI de première classe et une surface SARIF ne font pas partie de cette fonctionnalité.
- **Le baseline n'est jamais envoyé à l'IA.** La classification a lieu après que le modèle a répondu, sur sa sortie structurée. Rien au sujet du registre n'atteint un prompt.

---

## 11. Lectures liées

- `docs/policy-packs.md` — le bloc `baseline:` qu'un pack peut porter, et comment les décisions d'un pack de dépendance lui sont attribuées
- `docs/mcp-integration.md` — le serveur MCP, la tool `get_baseline_status` et la resource `baseline://summary`
- `docs/linter-regras-customizadas.md` — les règles de linter à partir desquelles un constat est fingerprinté
- `docs/config-tui.md` — l'écran de configuration où vivent les quatre variables
- `docs/plans/ADR-012-baseline-suppressions.md` — pourquoi le fingerprint hache le contenu de la ligne, pourquoi `new` n'est jamais persisté, et pourquoi la couche d'un pack reste en mémoire
