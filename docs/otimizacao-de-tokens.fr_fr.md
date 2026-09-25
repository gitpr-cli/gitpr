# Documentation technique : Optimisation des tokens dans les fichiers de contexte (.md)

Les fichiers `.gitpr.pr.md` et `.gitpr.review.md` agissent comme le « cerveau » des requêtes de GitPR. Ils sont injectés en tant que `system_instruction` dans les API d'IA.

L'objectif de cette documentation est d'établir des normes rigoureuses pour maintenir la consommation en dessous de **150 tokens par fichier**, garantissant des réponses quasi instantanées (faible TTFT - *Time to First Token*) et éliminant les hallucinations.

---

## 1. Principes de Prompting Efficace (Anti-Patterns)

Pour économiser des tokens, évitez les erreurs courantes suivantes :

* **N'enseignez pas ce que l'IA sait déjà :** Les modèles fondateurs ont été entraînés sur des milliers de livres d'ingénierie et de bases de code.
  * ❌ *Mauvais (consomme des tokens) :* « SOLID est un ensemble de 5 principes. Le S signifie Single Responsibility... »
  * ✅ *Bon (économique) :* « Évaluez l'architecture en utilisant les principes SOLID et le Clean Code. »
* **Éliminez le « bruit syntaxique » (politesse) :** L'IA n'a pas d'émotions.
  * ❌ *Mauvais :* « S'il vous plaît, pourriez-vous générer une description... »
  * ✅ *Bon :* « Générez la description. »
* **Attention au formatage Markdown excessif dans le Prompt :** Les symboles tels que `###` et les listes imbriquées dans votre fichier `.md` consomment des tokens individuels. Utilisez les **MAJUSCULES (CAPS LOCK)** pour définir la hiérarchie dans le prompt ; l'IA comprend parfaitement la sémantique.

---

## 2. Modèle Optimisé : .gitpr.pr.md (Focus sur la Livraison)

Ce fichier est utilisé par les commandes `--commit` et `--pr` (par défaut). Son but est de dicter la manière dont l'IA doit analyser le Diff et le traduire en valeur métier et en historique Git.

**Template de base (Copier et Coller) :**

```plaintext
CONTEXTE DU PROJET
[Insérez 1 ou 2 phrases sur le projet. Ex. : ERP Financier Laravel/Vue. Haute sécurité et auditabilité sont critiques.]

ROLE
Ingénieur Logiciel Senior. Résumez le git diff en vous concentrant sur l'impact métier et la clarté technique.

REGLES DE COMMIT
1. STANDARD : Utilisez Conventional Commits (feat, fix, refactor, chore).
2. VERBE : Utilisez l'impératif en français (ex. : "feat: ajoute un filtre", JAMAIS "ajoutant").
3. TAILLE : Max 72 caractères, sans point final.

REGLES DE PULL REQUEST
1. FOCUS : Expliquez le « pourquoi » du changement, ne traduisez pas le code.
2. STRUCTURE EXIGEE (Markdown) :
- 🎯 Résumé
- 🛠️ Changements Techniques (liste)
- ⚠️ Impact/Avertissements (Mettez en évidence envs, dépendances ou base de données)

FORMAT DE SORTIE
ZERO salutations ou compliments.
```

**Pourquoi est-ce efficace ?** Nous regroupons les règles logiques par blocs (Commits et PR). L'utilisation de « ZERO salutations » comme consigne négative finale est la technique la plus économique pour empêcher l'IA de gaspiller 20 tokens en disant *« Voici votre description de Pull Request : »* avant d'envoyer le JSON.

---

## 3. Modèle Optimisé : .gitpr.review.md (Focus sur la Qualité)

Ce fichier est déclenché exclusivement par `--review` et `--fullreview`. Ici, l'IA ignore l'historique Git et agit comme un contrôleur de qualité du code (*Quality Gate*).

**Template de base (Copier et Coller) :**

```plaintext
CONTEXTE DU PROJET
[Insérez 1 ou 2 phrases sur le projet. Ex. : ERP Financier Laravel/Vue. Haute sécurité e auditabilité sont critiques.]

ROLE
Architecte Logiciel Senior. Révisez le git diff en vous concentrant sur la maintenabilité et la prévention des bugs.

REGLES DE REVISION
1. DOCBLOCK : Chaque nouvelle fonction/méthode DOIT comporter une documentation standard (DocBlock/Docstring). Signalez l'absence comme erreur critique.
2. ARCHITECTURE : Signalez les violations de SOLID, requêtes N+1, nombres magiques et couplage fort. Ne définissez pas les concepts, indiquez seulement l'erreur.
3. SECURITE : Alertez sur SQLi, XSS ou données sensibles dans les logs.

STRUCTURE DE SORTIE EXIGEE (Markdown)
- RESUME DE LA MODIFICATION (1 phrase)
- POINTS CRITIQUES (Bugs, sécurité ou absence de DocBlock. Omettre si aucun)
- SUGGESTIONS D'AMELIORATION (Refactorisations. Utilisez des blocs de code pour Avant/Après)
- VERDICT (Approuvé / Approuvé avec Réserves / Rejeté)

FORMAT DE SORTIE
ZERO salutations ou compliments. Droit au but technique.
```

**Pourquoi est-ce efficace ?** La règle *Omettre si aucun* dans la section Points Critiques permet d'économiser des dizaines de tokens de sortie. Au lieu de générer un bloc inutile disant *« Points Critiques : Aucun point critique trouvé dans cette analyse »*, l'IA saute simplement la section et fait gagner du temps de lecture dans le terminal.

---
