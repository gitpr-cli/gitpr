# Documentation Technique : Guide du Relecteur (`gitpr explain` / `--explain`)

Le Guide du Relecteur explique un ensemble de changements du point de vue de la personne qui va relire. Au lieu de décrire l'apparence du diff (la description de la Pull Request le fait déjà), il répond aux quatre questions que se pose un relecteur avant d'approuver : **ce qui change**, **pourquoi cela change**, **où concentrer la relecture** et **quel risque de régression cela comporte**.

Il est disponible en tant que commande autonome, en tant que section optionnelle du flux de Pull Request, et via le serveur MCP et l'extension VS Code.

---

## 1. Aperçu

```bash
# Explique les modifications non commitées du dépôt courant
gitpr explain

# Force un fournisseur d'IA précis pour cette exécution
gitpr explain --provider deepseek

# Ajoute le Guide du Relecteur à la description de la Pull Request (flux PR standard)
gitpr --explain

# Idem, en enregistrant la description localement sans ouvrir la TUI de publication
gitpr --explain --no-publish

# L'inclure systématiquement, sans passer le drapeau à chaque exécution
# (~/.gitpr/.env)
GITPR_EXPLAIN_BY_DEFAULT=true

# Aide contextuelle avec le lien vers la documentation
gitpr -h --explain
```

---

## 2. Référence des Commandes

| Invocation | Portée | Écrit sur le disque | Publie |
|---|---|---|---|
| `gitpr explain [--provider <name>]` | Diff de l'arborescence de travail (`git diff HEAD`) | Non | Non |
| `gitpr --explain` | Diff complet de la branche par rapport à la base distante | Oui (fichier `.md` de la PR) | Oui, lorsque la PR est publiée |
| `gitpr --explain --no-publish` | Diff complet de la branche par rapport à la base distante | Oui (fichier `.md` de la PR) | Non |
| `gitpr --explain --no-edit` | Diff complet de la branche par rapport à la base distante | Oui | Oui, directement |

### `gitpr explain`

| Option | Valeur par défaut | Description |
|---|---|---|
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Force le fournisseur d'IA pour cette exécution (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Aide Click plus le lien vers cette page. |

La commande autonome imprime le guide dans le terminal et se termine. Elle ne crée jamais de fichier, n'ouvre jamais l'éditeur et ne communique jamais avec le forge.

### Drapeau racine `--explain`

| Drapeau | Variable d'environnement | Valeur par défaut | Description |
|---|---|---|---|
| `--explain` | `GITPR_EXPLAIN_BY_DEFAULT` | `false` | Ajoute la section du Guide du Relecteur à la description de Pull Request générée. |

Valeurs acceptées par `GITPR_EXPLAIN_BY_DEFAULT` (insensibles à la casse) : `true`, `1`, `yes`, `y`. Toute autre valeur — y compris la variable absente — laisse la section désactivée. La clé est modifiable dans l'écran de configuration (`gitpr config`), dans la catégorie **PR**, et peut être définie manuellement dans `~/.gitpr/.env`.

Le drapeau ne participe qu'au **flux de Pull Request standard**. Les modes qui se terminent avant ce flux (`--commit`, `--review`, `--fullreview`, `--issue`, `--blame`, `--chat`, `gitpr tests generate` et les autres sous-commandes) l'ignorent.

---

## 3. Sources du Diff

Les deux points d'entrée n'expliquent pas la même chose :

| Point d'entrée | Commande sous-jacente | Couvre |
|---|---|---|
| `gitpr explain` | `git diff -U1 -w -M -B HEAD -- <smart excludes>` | Modifications indexées et non indexées des fichiers suivis, comparées à `HEAD`. Les fichiers non suivis sont signalés et **ne font pas** partie du prompt. |
| `--explain` (flux PR) | `git fetch origin` → `git merge-base origin/<base> HEAD` → `git diff -U1 -w -M -B <merge-base> -- <smart excludes>` | Tout ce que la branche modifie par rapport au point où elle a divergé de la branche de base, y compris l'état de l'arborescence de travail. |

Dans les deux cas, le diff est capturé avec `-U1` (une ligne de contexte), `-w` (insensible aux espaces), `-M` (détection des renommages), `-B` (paires cassées) et les **smart excludes** résolues (lockfiles, artefacts générés et autres chemins qui noieraient le signal). Le même fichier auxiliaire peut être remplacé par `GITPR_SKIP_SMART_EXCLUDES`, `GITPR_SMART_EXCLUDES_GLOBAL` et `GITPR_SMART_EXCLUDES_LOCAL`.

Comme le diff est rogné pour la lecture, ce n'est pas un patch : il ne doit pas être utilisé avec `git apply`. Les commandes qui ont besoin d'un patch applicable (`gitpr fix`, `gitpr split`) capturent leur propre diff.

---

## 4. Pipeline de Génération

1. **Vérification du diff vide.** Un diff vide ou composé uniquement d'espaces renvoie immédiatement une explication vide ; la commande autonome imprime `⚠️ No diff found...` et sort avec le code `1`.
2. **Fournisseur et clé.** Le fournisseur vient de `--provider` ou de `DEFAULT_AI_PROVIDER`. Si aucune clé n'est configurée, la commande imprime `❌ No API key configured for <provider>. Generate one with --install.` sur **stderr** et renvoie une explication vide. `ollama` n'a pas besoin de clé.
3. **Sélection du modèle.** Le modèle avancé/principal est utilisé (`get_api_model(provider, task_complexity="advanced")`) : `GEMINI_API_MODEL_PRIMARY` ou `DEEPSEEK_API_MODEL_PRIMARY`, avec la valeur par défaut intégrée correspondante.
4. **Résolution de la skill.** L'instruction système est `get_skill_context("explain", quiet=True)` — `.gitpr/skill/.gitpr.explain.md` lorsqu'il existe, un `.gitpr.md` hérité en repli, sinon une instruction intégrée équivalente au modèle anglais. Le flux PR passe `quiet=True` afin que le message « skill chargée » ne pollue jamais la description générée.
5. **Prompt.** Le diff complet et les règles d'explication sont envoyés dans un seul prompt. La sortie doit être un objet JSON (la couche fournisseurs est configurée pour les réponses JSON).
6. **Appel à l'IA.** `call_ai_model(..., action="explain")` utilise une température de `0.0` et réessaie jusqu'à **3** fois avec un intervalle de **2 s**. En cas d'échec, il renvoie `None` et la commande signale que le guide n'a pas pu être généré.
7. **Analyse.** `parse_explain_payload` accepte le **dict** déjà analysé du fournisseur et, par compatibilité, une chaîne JSON. Une chaîne qui n'est pas du JSON valide est traitée comme de la prose : elle remplit `what_changes`, le champ `why_it_changes` reçoit un placeholder `[FILL: ...]` et `has_sufficient_evidence` passe à `False`.
8. **Rendu.** `build_explain_markdown` assemble la section Markdown utilisée par le flux PR ; la commande autonome rend les mêmes données dans un rapport coloré au terminal.

Le flux **n'utilise pas** le cache local de réponses IA et **n'écrit pas** de ligne dans le ledger de métriques. Chaque exécution appelle le fournisseur.

---

## 5. Contrat de Sortie

Le modèle renvoie un objet JSON à quatre champs :

| Champ | Type | Signification |
|---|---|---|
| `what_changes` | string | 2 à 4 phrases en langage simple décrivant le changement fonctionnel, sans jargon. |
| `why_it_changes` | string | La motivation déduite. Lorsque le diff ne soutient pas une conclusion, le modèle doit utiliser `[FILL: What is the primary business motivation for this change?]` au lieu d'en inventer une. |
| `reviewer_focus_points` | tableau d'objets | 2 à 5 points concrets à inspecter. Chaque objet possède `description` (obligatoire), `file_path` (optionnel) et `related_line` (entier optionnel). |
| `regression_risk` | string | Surfaces de risque objectives : code partagé critique, migrations de schéma, changements d'authentification, tests manquants, interfaces cassantes. |

La couche fournisseurs ajoute `_telemetry_meta` au dict ; l'analyseur l'ignore.

### Section Markdown

```markdown
## 🧐 Reviewer Guide (Explain My PR)

### 🔍 What changes
...

### 💡 Why it changes
...

### 🎯 Where to focus review
- **Validate token expiration** (`src/auth/tokens.py:45`)
- **Check backward compatibility of the refresh endpoint**

### ⚠️ Regression Risk
...
```

`Where to focus review` n'est émis que lorsqu'au moins un point d'attention existe, et `Regression Risk` que lorsque le champ n'est pas vide.

### Indicateur de preuve

`has_sufficient_evidence` vaut `False` lorsque le diff est vide, lorsqu'aucune clé d'API n'est disponible, ou lorsque `what_changes` / `why_it_changes` contiennent un marqueur de placeholder (`[PREENCHER`, `[FILL`, `[TODO`, `[REQUIRED`). La commande autonome imprime un avertissement sous le rapport ; la section de la PR n'est pas supprimée — les placeholders restent visibles pour que l'auteur les complète.

---

## 6. Où Apparaît le Guide

### Flux PR (`--explain`)

Une fois le titre et le corps de la PR générés, le Guide du Relecteur est ajouté au corps sous forme de bloc séparé :

```text
<description de la PR>

---

## 🧐 Reviewer Guide (Explain My PR)
...
```

Le corps combiné est écrit dans le fichier `.md` de la PR et c'est ce qui est publié lors de la création de la Pull Request. Activer `GITPR_EXPLAIN_BY_DEFAULT=true` produit le même résultat sans le drapeau.

### Serveur MCP

L'outil `generate_pr_description` accepte `explain: bool = false` et ajoute la même section au `pr_description` renvoyé. L'outil calcule lui-même le diff complet de la branche ; le guide est omis si le modèle ne renvoie pas de Markdown.

### Extension VS Code

La commande `gitpr.generatePrExplain` exécute la génération de PR avec `explain: true`. La commande simple `gitpr.generatePr` laisse la section désactivée.

---

## 7. Personnaliser le Guide avec une Skill

Les règles d'explication sont une **skill**, et non un texte de prompt figé :

- Emplacement par défaut : `.gitpr/skill/.gitpr.explain.md` dans le dépôt.
- Téléchargez-la avec `gitpr --skill` (également disponible dans l'assistant d'installation). Des variantes existent pour `en`, `pt_br`, `pt_pt`, `es_es` et `fr_fr` ; le fichier est téléchargé dans la langue d'interface active et n'est **jamais écrasé** s'il existe déjà.
- Un `.gitpr.md` hérité dans `.gitpr/skill/` sert de repli lorsque le fichier spécifique est absent.
- Lorsqu'aucun des deux n'existe, l'instruction intégrée est utilisée ; elle est équivalente au modèle anglais et exige également du JSON strict.
- La langue du texte généré suit la skill chargée, et non la langue d'interface de `--lang`. Pour obtenir le guide en français, par exemple, téléchargez ou rédigez le `.gitpr.explain.md` en français.

Le modèle demande à l'IA d'écrire pour un relecteur qui n'a pas écrit le code, de ne jamais inventer la motivation, de lister 2 à 5 points d'attention et de renvoyer uniquement l'objet JSON.

---

## 8. Erreurs et Codes de Sortie

| Situation | Comportement | Code de sortie |
|---|---|---|
| Guide généré | Rapport au terminal (autonome) ou section ajoutée (flux PR) | `0` |
| Aucun diff / aucun contenu | `⚠️ No diff found...` sur stdout | `1` |
| Aucune clé d'API | Erreur localisée sur stderr ; la commande autonome imprime aussi `❌ Failed to generate PR explanation.` | `1` |
| Le modèle n'a rien renvoyé d'utilisable | `❌ Failed to generate PR explanation.` | `1` |
| Flux PR, le modèle n'a rien renvoyé | La section est silencieusement omise de la description ; le reste de la PR est produit normalement | `0` |
| Nom de fournisseur invalide | La couche fournisseurs signale le fournisseur inconnu ; aucun guide n'est produit | `1` (autonome) |

---

## 9. Exemple

```text
$ gitpr explain

🧐 Analyzing diff from reviewer perspective...

============================================================
  REVIEWER GUIDE (Explain My PR)
============================================================

🔍 What changes:
  Adds a Redis-backed rate limiter to the login route and wires it
  into the authentication middleware.

💡 Why it changes:
  Mitigates brute-force credential stuffing without changing the
  login response contract.

🎯 Where to focus review:
  • Verify the key expiration strategy [src/auth/limiter.py:25]
  • Confirm legitimate shared-IP users are not locked out [src/auth/middleware.py]

⚠️ Regression Risk:
  Users behind shared NATs may be throttled together; no test covers
  the limit boundary yet.

⚠️ Notice: Inferred with partial context. Some fields contain placeholders to complete.
```

---

## 10. Limites

- **La sortie autonome se limite au terminal.** `gitpr explain` n'écrit aucun fichier et ne publie rien ; pour joindre la section à une PR, utilisez `--explain` dans le flux PR.
- **`--explain` est réservé au flux PR standard.** Le combiner avec des modes qui se terminent plus tôt n'a aucun effet.
- **Pas de cache, pas de ledger.** Les exécutions répétées rappellent le modèle, et l'exécution n'est pas enregistrée dans `gitpr metrics`.
- **Les fichiers non suivis ne sont pas expliqués.** Les deux sources de diff ne voient que les fichiers suivis. La commande autonome signale les fichiers non suivis mais ne les inclut pas ; ajoutez-les d'abord avec `git add`.
- **Pas de découpage.** Le diff entier part dans un seul prompt. Les changements très volumineux peuvent atteindre la limite de contexte du fournisseur ; découpez le travail ou relisez une plage plus petite.
- **Pas de sémantique de patch.** Le diff est capturé avec `-w` et `-U1` pour la lecture. Ne le réutilisez pas pour `git apply`.
- **La motivation est déduite.** L'IA a l'interdiction d'inventer une justification ; lorsque le diff n'apporte pas de preuve, elle émet un placeholder `[FILL: ...]`.
- **La langue dépend de la skill.** La seule langue de l'interface ne traduit pas le guide généré.

---

## 11. Documentation Associée

- [Publication de Pull Request](pull-request-publication.fr_fr.md) — où la section est ajoutée et comment la PR est publiée.
- [Modèles de Skill](skill-template.fr_fr.md) — comment les fichiers `.gitpr.*.md` sont résolus, téléchargés et remplacés.
- [Fournisseurs d'IA](providers-ia.fr_fr.md) — fournisseurs, modèles, tentatives et configuration des clés.
- [TUI de Configuration](config-tui.fr_fr.md) — comment modifier `GITPR_EXPLAIN_BY_DEFAULT` depuis `gitpr config`.
- [Génération de Tests](tests-generate.fr_fr.md) — l'autre commande de génération par IA.
- [Mode Mentor](mentor-mode.fr_fr.md) — les explications pédagogiques ajoutées aux revues de code.
