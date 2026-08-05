# **Guide Pratique : Expressions Régulières Performantes dans GitPR**

Le Linter Statique de GitPR traite le `git diff` ligne par ligne à l'aide du moteur natif `re` de Python (NFA - *Nondeterministic Finite Automaton*). Les moteurs NFA sont puissants, mais ils ont un angle mort dangereux : le **Retour en Arrière Catastrophique (Catastrophic Backtracking)**.

Ce guide explique comment rédiger des règles pour le `.gitpr.linter.yml` tout en garantissant que le temps de validation du commit reste de l'ordre de quelques millisecondes.

---

## **1. Qu'est-ce que le Catastrophic Backtracking ?**

Il se produit lorsqu'une Regex utilise des **quantificateurs gourmands** `(*, +)` proches les uns des autres ou imbriqués, et que la chaîne testée correspond presque, mais échoue à la fin.

Pour tenter de trouver une correspondance valide, le moteur "revient en arrière" (backtrack) et essaie toutes les permutations possibles. Le temps de traitement croît de manière exponentielle ($O(2^n)$).

**L'Exemple Classique (Le Code de la Mort) :**

* **Regex :** `(a+)+$`  
* **Texte :** `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaX`  
* *Résultat :* Le terminal plante. Le moteur essaiera plus de 700 millions de combinaisons avant de réaliser que le `X` à la fin empêche la correspondance.

---

## **2. Règles d'Or pour une Haute Performance**

### **Règle 1 : "Échouer Rapidement" avec les Ancres**

Le meilleur moyen d'économiser du CPU est d'amener la Regex à renoncer à la ligne le plus rapidement possible.

Si le mot interdit doit être un mot isolé, utilisez la frontière de mot `\b` (Word Boundary). Cela empêche la Regex d'analyser inutilement l'intérieur de longues chaînes de caractères.

* ❌ **Lent :** `dd\(` *(Cherche les caractères 'd', 'd', '(' à toutes les positions de la ligne)*  
* ✅ **Rapide :** `\bdd\(` *(Ne commence la recherche qu'au début d'un mot. Si la ligne contient `add()`, il renonce dès le premier caractère)*

### **Règle 2 : Remplacez `.*` par des Classes Négatives `[^...]`**

Le `.*` (n'importe quoi, zéro ou plusieurs fois) est la principale cause de backtracking. Il est gourmand : il va jusqu'à la fin de la ligne, puis commence à revenir en arrière de droite à gauche pour trouver le reste de votre règle.

Si vous cherchez quelque chose entre guillemets ou entre parenthèses, indiquez exactement où il doit s'arrêter.

* ❌ **Lent :** `console\.log\(.*\)` *(Va jusqu'à la fin de la ligne avant de revenir en arrière pour trouver la parenthèse fermante)*  
* ✅ **Rapide :** `console\.log\([^)]*\)` *(La classe `[^)]` signifie : "Capturez tout, tant qu'il ne s'agit PAS d'une parenthèse fermante". Il s'arrête à la milliseconde exacte où il rencontre la limite)*

### **Règle 3 : Évitez les Quantificateurs Optionnels Imbriqués**

Ne placez jamais un quantificateur optionnel (`*` ou `?`) juste après un autre quantificateur optionnel, ou à l'intérieur d'un groupe qui se répète également.

* ❌ **Lent :** `(localhost\s*)*`  
* ✅ **Rapide :** `localhost(\s+localhost)*`

### **Règle 4 : Désactivez la Capture dans les Groupes `(?:...)`**

Par défaut, lorsque vous utilisez des parenthèses `(get|post)` comme dans notre règle de routage, Python conserve ces informations en mémoire pour une extraction ultérieure. GitPR n'a pas besoin d'extraire le mot, il doit seulement savoir s'il existe (`True` ou `False`).

Utilisez des groupes non-capturants `(?:...)` pour économiser la mémoire.

* ❌ **Lent :** `Route::(get|post)\(`  
* ✅ **Rapide :** `Route::(?:get|post)\(`

---

## **3. Comparatif Pratique pour `.gitpr.linter.yml`**

Voici comment transformer des règles naïves en règles blindées :

| Objectif | ❌ Regex Naïve (Dangereuse) | ✅ Regex Performante (GitPR) | Pourquoi est-ce meilleur ? |
| :---- | :---- | :---- | :---- |
| Bloquer une IP Fixe | `[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+` | `\b(?:\d{1,3}\.){3}\d{1,3}\b` | Utilise `\b` et `(?:)` pour éviter l'allocation de mémoire supplémentaire et limite la taille à 3 chiffres. |
| Trouver les TODOs | `.*TODO.*` | `\bTODO\b:` | Élimine le `.*` inutile. L'ancre `\b` résout la recherche sur toute la ligne. |
| Routes (Verbes) | `Route::.*\('get.*` | `Route::[A-Za-z]+(\s*['"](?:get\|post)` | Utilise des classes de caractères et une alternance rapide sans capture. |

**Conseil de Prévention :** Comme GitPR traite des lignes avec des fichiers minifiés (ex : `app.min.js`), une seule ligne peut contenir des milliers de caractères. Appliquer la **Règle 2 (Classes Négatives)** est votre meilleure garantie contre le blocage du terminal.

---
