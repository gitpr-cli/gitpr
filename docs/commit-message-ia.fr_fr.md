# Documentation technique : Génération de messages de commit avec l'IA (--commit)

La commande `--commit` (`-c`) de GitPR génère automatiquement des messages de commit au format **Conventional Commits** en utilisant l'intelligence artificielle pour analyser vos modifications locales.

---

## 1. Utilisation de base

```bash
gitpr -c
```

L'outil analyse le `git diff HEAD` et affiche le message suggéré directement dans la console :

```
📝 Suggestion de commit :

feat: ajoute la validation d'email dans le formulaire d'inscription

- Implemente la regex de validation RFC 5322
- Ajoute des messages d'erreur localises (pt-BR)
- Corrige l'edge case des emails avec domaines internationaux


Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

---

## 2. Format Conventional Commits

L'IA est instruite de générer des messages selon le standard :

```
type: description courte

Corps optionnel avec détails supplémentaires
```

**Types utilisés :** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Intégration avec les Git Hooks

La commande `--commit` est utilisée en interne par le hook `prepare-commit-msg`. Lorsqu'il est installé via `gitpr -ih`, le hook exécute :

```bash
gitpr --commit --hook <caminho-do-arquivo-temporario>
```

Le flag `--hook` (interne/caché) fait que le message suggéré est injecté directement dans l'éditeur de Git, au lieu d'être affiché dans la console.

---

## 4. Personnalisation via Skill

Le comportement de l'IA peut être personnalisé à travers le fichier `.gitpr.commit.md` à la racine du projet :

```bash
gitpr -s          # Télécharge le template .gitpr.commit.md
# Éditez le fichier selon les conventions de votre équipe
gitpr -c          # L'IA utilisera vos règles personnalisées
```

---

## 5. Sélection du fournisseur d'IA

```bash
gitpr -c -p gemini       # Force Google Gemini
gitpr -c -p deepseek     # Force DeepSeek
```

---

## 6. Cache de réponses

GitPR génère un hash MD5 de votre diff + instructions. Si vous exécutez `gitpr -c` à nouveau **sans modifier le code**, la réponse est renvoyée instantanément depuis le cache local, économisant les quotas de l'API.

---

## 7. Signature de co-auteur

Chaque message de commit généré par GitPR porte automatiquement le trailer de co-auteur :

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

Le trailer est ajouté programmatiquement (jamais par l'IA) dans tous les flux : suggestion dans la console, hook `prepare-commit-msg`, auto-commit, TUI de publication de PR et l'outil MCP `generate_commit_message`. Il est séparé du message par des lignes vides supplémentaires pour ne pas apparaître au premier coup d'œil dans les aperçus de commits de GitHub, et n'est jamais dupliqué lorsque le message le contient déjà.

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités.
