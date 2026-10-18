# Documentation Technique : Génération de Tests par IA (`gitpr tests generate`)

`gitpr tests generate` transforme un ensemble de changements en un fichier de test complet. Il détecte le framework de test du projet, calcule le chemin de destination conventionnel, demande à l'IA une suite prête à exécuter, valide la syntaxe avec la chaîne d'outils locale lorsqu'elle est disponible et — uniquement avec `--apply` — écrit le fichier sur le disque.

La commande n'exécute jamais les tests générés et ne fait jamais de stage ni de commit.

---

## 1. Aperçu

```bash
# Génère des tests pour le diff complet de l'arborescence de travail (dry run)
gitpr tests generate

# Génère des tests pour un fichier
gitpr tests generate --file src/auth/limiter.py

# Cible un constat de la dernière revue de code
gitpr tests generate --finding FIX-001

# Force le framework au lieu de le détecter automatiquement
gitpr tests generate --framework vitest

# Écrit le fichier généré sur le disque (demande confirmation)
gitpr tests generate --file src/auth/limiter.py --apply

# Aide contextuelle avec le lien vers la documentation
gitpr tests generate -h
```

---

## 2. Référence des Commandes

```text
gitpr tests generate [--file PATH] [--finding ID] [--framework NAME] [--apply] [--provider NAME]
```

| Option | Valeur par défaut | Description |
|---|---|---|
| `--file PATH` | — | Génère des tests pour ce fichier au lieu du diff complet. |
| `--finding ID` | — | Génère des tests pour un constat précis de la dernière revue de code (par exemple `FIX-001`). |
| `--framework NAME` | Détecté automatiquement | Force le framework : `pest`, `phpunit`, `jest`, `vitest`, `pytest`. |
| `--apply` | `false` | Écrit le fichier généré sur le disque après le dry run et les confirmations. |
| `--provider <name>` | `DEFAULT_AI_PROVIDER` | Force le fournisseur d'IA pour cette exécution (`gemini`, `deepseek`, `ollama`). |
| `-h`, `--help` | — | Aide Click plus le lien vers cette page. |

`--file` et `--finding` sont mutuellement exclusifs en pratique : `--finding` a la priorité, et `--file` est alors remplacé par le chemin du fichier du constat.

---

## 3. Résolution de la Cible

La commande décide de ce qu'elle envoie au modèle avant de générer quoi que ce soit :

| Invocation | Contenu de la cible |
|---|---|
| *(sans drapeau de cible)* | Diff de l'arborescence de travail : `git diff HEAD` avec les smart excludes. |
| `--file PATH` | `git diff HEAD -- PATH`. Si ce diff est vide et que le fichier existe, le **contenu complet du fichier** est utilisé à la place. |
| `--finding ID` | La dernière revue est chargée (`resolve_review` → `collect_candidates` → `find_candidate`), et le prompt reçoit les métadonnées du constat, son `suggested_test` et son patch `diff_unified`. Le scaffold utilise le `file_path` du constat. |

Si le contenu résolu est vide, la commande imprime `❌ No changes or target content found to generate tests.` et sort avec le code `1`.

Pour `--finding`, la revue doit exister et être lisible. Si la résolution de la candidature échoue, la commande imprime un avertissement et se replie sur un contexte minimal contenant seulement `Finding ID: <id>` ; dans ce cas, le test généré a très peu d'éléments pour travailler.

---

## 4. Détection du Framework

La détection s'exécute uniquement à la **racine du dépôt**. La première correspondance gagne, dans cet ordre :

| Ordre | Framework | Indicateurs |
|---|---|---|
| 1 | `pest` | `pest.php`, `tests/Pest.php` ou `pestphp/pest` dans `composer.json` (`require` / `require-dev`). |
| 2 | `phpunit` | `phpunit.xml`, `phpunit.dist.xml`, `phpunit.xml.dist` ou `phpunit/phpunit` dans `composer.json`. |
| 3 | `vitest` | `vitest.config.{ts,js,mjs,mts}`, `vite.config.{ts,js}` ou `vitest` dans les dépendances ou scripts de `package.json`. |
| 4 | `jest` | `jest.config.{js,ts,mjs,cjs,json}` ou `jest` dans les dépendances ou scripts de `package.json`. |
| 5 | `pytest` | `pytest.ini`, `conftest.py`, `tox.ini`, `setup.cfg`, un `pyproject.toml` mentionnant pytest, ou `tests/test_*.py` / `tests/*_test.py`. |
| — | `unknown` | Aucun indicateur trouvé. Un avertissement invite à utiliser `--framework`. |

`--framework` est appliqué en premier. La valeur est comparée sans tenir compte de la casse aux cinq noms connus ; une valeur inconnue produit un avertissement et se replie sur la détection automatique au lieu d'échouer.

---

## 5. Conventions de Chemin du Scaffold

Le chemin de destination est calculé avant l'appel à l'IA, et le prompt le reçoit comme cible obligatoire.

### Pest / PHPUnit

- `app/` est retiré du début du chemin.
- La suite est **Feature** lorsque le premier segment restant est `Http`, `Controllers`, `Livewire` ou `Filament` ; sinon elle est **Unit**.
- Le nom du fichier reçoit le suffixe `Test.php` sauf si le stem se termine déjà par `Test`.

| Source | Destination |
|---|---|
| `app/Http/Controllers/Api/UserController.php` | `tests/Feature/Http/Controllers/Api/UserControllerTest.php` |
| `app/Services/UserService.php` | `tests/Unit/Services/UserServiceTest.php` |
| *(sans fichier source, Pest)* | `tests/Feature/GeneratedTest.php` |
| *(sans fichier source, PHPUnit)* | `tests/Unit/GeneratedTest.php` |

### Jest / Vitest

- `src/` est retiré du début du chemin.
- `.ts` / `.tsx` → `.test.ts` ; `.vue` → `.spec.js` ; tout le reste → `.test.js`.

| Source | Destination |
|---|---|
| `src/components/Button.vue` | `tests/components/Button.spec.js` |
| `src/utils/date.ts` | `tests/utils/date.test.ts` |
| `src/lib/api.js` | `tests/lib/api.test.js` |
| *(sans fichier source, Vitest)* | `tests/generated.test.ts` |
| *(sans fichier source, Jest)* | `tests/generated.test.js` |

### pytest

- `src/` ou `app/` est retiré du début du chemin.
- `test_` est préfixé sauf si le stem commence déjà par lui.

| Source | Destination |
|---|---|
| `src/core.py` | `tests/test_core.py` |
| `app/services/auth.py` | `tests/services/test_auth.py` |
| *(sans fichier source)* | `tests/test_generated.py` |

### Inconnu

| Source | Destination |
|---|---|
| `src/model.py` | `tests/test_model.py` |
| *(sans fichier source)* | `tests/test_generated.txt` |

Le scaffold enregistre aussi `already_exists`, qui contrôle la confirmation d'écrasement dans `--apply`.

---

## 6. Pipeline de Génération

1. **Détection du framework** — override ou indicateurs du dépôt (section 4).
2. **Scaffold** — chemin de destination conventionnel (section 5).
3. **Fournisseur et clé** — `--provider` ou `DEFAULT_AI_PROVIDER`. Sans clé, la commande ajoute un avertissement (`No API key configured for <provider>...`), renvoie un contenu vide et sort avec le code `1`. `ollama` n'a pas besoin de clé.
4. **Modèle** — le modèle avancé/principal est utilisé (`task_complexity="advanced"`).
5. **Skill** — `get_skill_context("tests", quiet=True)` lit `.gitpr/skill/.gitpr.tests.md` ; à défaut, une instruction intégrée équivalente au modèle anglais est utilisée. La skill définit la persona QA et l'enveloppe JSON.
6. **Prompt** — framework, chemin de destination, type de cible, métadonnées de fichier/constat et le diff complet.
7. **Appel à l'IA** — `call_ai_model(..., action="tests")`, température `0.0`, jusqu'à **3** tentatives avec un intervalle de **2 s**.
8. **Analyse** — le fournisseur renvoie un **dict** déjà analysé ; une chaîne JSON est également acceptée. Une chaîne qui n'est pas du JSON est traitée comme un bloc de code : les balises sont retirées et tout le texte devient le fichier de test, avec le scénario `Generated from raw model output`.
9. **Validation de la syntaxe** — la chaîne d'outils locale vérifie le code généré lorsqu'elle est disponible (section 7).
10. **Écriture facultative** — uniquement lorsque `--apply` est passé (section 8).

Il n'y a pas de cache de prompt ni d'enregistrement dans le ledger de métriques : chaque exécution appelle le fournisseur.

---

## 7. Validation de la Syntaxe

La validation est faite au mieux et ne bloque jamais la génération :

| Framework | Outil | Commande | Remarques |
|---|---|---|---|
| Pest / PHPUnit | `php` | `php -l <temp>.php` | Ignorée lorsque PHP n'est pas dans le `PATH`. |
| Jest / Vitest | `node` | `node --check <temp>.js` | Le fichier temporaire utilise toujours le suffixe `.js`, y compris pour les sources TypeScript. Elle détecte les erreurs de syntaxe grossières, pas les erreurs de type. |
| pytest | `python` / `python3` | `python -m py_compile <temp>.py` | Ignorée lorsque aucun des binaires n'est dans le `PATH`. |
| inconnu | — | — | Aucune validation. |

Une validation en échec ajoute un avertissement (`Syntax validation failed ... Marked as EXPERIMENTAL / low confidence.`), mais le contenu généré est quand même renvoyé et peut toujours être écrit avec `--apply`. Un contenu généré vide est signalé comme invalide.

---

## 8. Écriture avec `--apply`

La commande **imprime toujours** le dry run en premier : framework, chemin de destination, scénarios couverts et le code généré complet. L'écriture n'a lieu qu'ensuite et uniquement lorsque `--apply` est présent.

| Étape | Condition | Réponse par défaut |
|---|---|---|
| Confirmation d'écrasement | Le chemin de destination existe déjà (`already_exists`) | **Non** |
| Confirmation d'écriture | Toujours | **Oui** |

Si l'une des confirmations est refusée, la commande imprime un message d'annulation et revient sans écrire. Lorsqu'elle est acceptée, elle crée les répertoires parents et écrit le fichier en UTF-8 avec `errors='replace'`, relativement au **répertoire de travail courant**.

Elle **n'exécute pas** `git add`, ne fait pas de commit et n'exécute pas les tests générés.

---

## 9. Exemple de Sortie

```text
$ gitpr tests generate --file src/auth/limiter.py

🧪 Analyzing diff and generating test file...

📋 Target Framework: PYTEST
📂 Target Test Path: tests/test_limiter.py

🧪 Covered Scenarios:
  • Happy path: request under the limit is allowed
  • Boundary: request exactly at the limit
  • Regression: counter expiration resets the window

--- Generated Test Code ---
def test_request_under_limit_is_allowed():
    ...
---

ℹ️ Dry-run mode. Run with --apply to write to disk.
```

Avec `--apply`, le même rapport est suivi des confirmations et de `✅ Test file successfully created at '<path>'!`.

---

## 10. Erreurs et Codes de Sortie

| Situation | Comportement | Code de sortie |
|---|---|---|
| Tests générés (dry run ou appliqués) | Rapport et, avec `--apply`, le fichier | `0` |
| Aucun diff / aucun contenu de fichier | `❌ No changes or target content found to generate tests.` | `1` |
| Aucune clé d'API | Avertissement plus `❌ Test generation failed.` (contenu vide) | `1` |
| Le modèle n'a rien renvoyé d'utilisable | Avertissement plus `❌ Test generation failed.` | `1` |
| La validation de syntaxe a échoué | Avertissement seulement ; le contenu est quand même affiché/appliqué | `0` |
| L'utilisateur refuse une confirmation | Message d'annulation | `0` |
| Utilisation CLI invalide | Erreur d'utilisation Click | `2` |

---

## 11. Limites

- **Détection à la racine uniquement.** Les indicateurs de framework sont recherchés à la racine du dépôt. Les monorepos avec des configurations par paquet ne sont pas pris en charge ; utilisez `--framework`.
- **La première correspondance gagne.** Un dépôt contenant à la fois des indicateurs PHP et JS est détecté comme PHP, car PHP est vérifié en premier.
- **Le test généré n'est pas exécuté.** Seule la syntaxe est vérifiée, et uniquement lorsque le binaire correspondant est installé. Un test syntaxiquement valide peut échouer à l'exécution.
- **La validation TypeScript est superficielle.** `node --check` analyse le fichier comme du JavaScript ; les erreurs de type et de nombreuses constructions propres à TS ne sont pas validées.
- **Un framework inconnu produit un fichier `.txt`.** Sans framework, il n'y a ni convention ni vérification de syntaxe, et la destination est `tests/test_generated.txt` (ou `tests/test_<stem><ext>`).
- **`--file` sans diff envoie le fichier entier.** Pour un fichier volumineux et inchangé, cela peut consommer une partie importante de la fenêtre de contexte ; la commande ne fait pas de découpage.
- **`--finding` dépend de la dernière revue.** Elle lit l'artefact de revue produit par `gitpr -r` / `gitpr -f` via la machinerie `fix`. Sans revue, le contexte se dégrade en ID de constat.
- **Les chemins sont relatifs au répertoire courant.** L'exécution depuis un sous-répertoire écrit le test relativement à ce sous-répertoire, et non à la racine du dépôt.
- **Pas de cache, pas de ledger.** Les exécutions répétées rappellent le fournisseur, et l'exécution n'est pas enregistrée dans `gitpr metrics`.
- **Aucune intégration git.** Le nouveau fichier reste non suivi ; `git add` et le commit sont à votre charge.
- **La commande `/tests` du chat est séparée.** Elle ne délègue pas à ce moteur ; utilisez `gitpr tests generate` pour une génération structurée.
- **Le texte généré suit la langue de la skill**, et non la langue d'interface de `--lang`.

---

## 12. Documentation Associée

- [Revue de Code par IA](code-review-ia.fr_fr.md) — d'où viennent les constats consommés par `--finding`.
- [Commande Fix](fix-command.fr_fr.md) — les constats de revue et la machinerie de patch partagée avec `--finding`.
- [Modèles de Skill](skill-template.fr_fr.md) — comment `.gitpr.tests.md` est résolu, téléchargé et remplacé.
- [Fournisseurs d'IA](providers-ia.fr_fr.md) — fournisseurs, modèles, tentatives et configuration des clés.
- [Guide du Relecteur](explain-pr.fr_fr.md) — l'autre commande de génération par IA.
- [Vérification Unifiée de CI](check-ci.fr_fr.md) — quelles validations s'exécutent plutôt en CI.
