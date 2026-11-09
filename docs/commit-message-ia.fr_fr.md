# Documentation technique : Génération de messages de commit avec l'IA (--commit)

La commande `--commit` (`-c`) de GitPR génère automatiquement des messages de commit au format **Conventional Commits** en utilisant l'intelligence artificielle pour analyser vos modifications locales et propose un flux TUI interactif complet pour sélectionner les fichiers, réviser le message et exécuter le commit.

---

## 1. Flux interactif de commit

```bash
gitpr -c
```

Lorsqu'il est exécuté dans un terminal interactif, GitPR vous guide à travers un flux en 4 étapes :

1. **Sélecteur de stage ("Fichiers hors du stage")** :
   - S'il y a des fichiers unstaged ou untracked, GitPR ouvre la modale `StageFilesScreen` avec des cases à cocher.
   - Vous pouvez sélectionner avec précision les fichiers à ajouter au stage (`git add`).
   - Utilisez **"Tout sélectionner"**, **"Tout désélectionner"**, **"Stage Selected"** (Ajouter la sélection), **"Skip Staging"** (Ignorer le stage) ou **"Annuler"**.
   - Si toutes les modifications sont déjà dans le stage, cet écran est automatiquement ignoré.

2. **Génération du message avec l'IA** :
   - Analyse le diff du stage (`git diff --cached`) en appliquant les exclusions intelligentes (`SMART_EXCLUDES`).
   - Génère le message au format Conventional Commits en arrière-plan tout en affichant une modale animée de progression (`CommitProgressScreen`).

3. **Révision et édition du message** :
   - Affiche le message généré dans la modale `CommitMessageScreen`.
   - Vous pouvez réviser et modifier le texte directement avant de confirmer.
   - Cliquez sur **"Confirmer"** pour continuer ou **"Annuler"** pour abandonner sans commiter.

4. **Exécution animée du commit** :
   - Lors de la confirmation, affiche la modale `CommitProgressScreen` avec la barre animée en dégradé.
   - Exécute le commit (`git commit -m "..."`) en incluant la signature de co-auteur.
   - Affiche les journaux en temps réel et le hash du commit généré, avec le bouton **"Fermer"** pour terminer.

> [!WARNING]
> **Note de Migration (Flux Interactif vs. Silencieux Legacy) :**  
> Avant la version v1.4.4, la commande `gitpr -c` (`--commit`) était strictement une commande de console non interactive et silencieuse : elle générait le message et l'affichait sur `stdout` sans ajouter de fichiers au stage ni exécuter `git commit`. À partir de la v1.4.4, l'exécution de `gitpr -c` dans un terminal interactif lance le flux TUI en 4 étapes et exécute le commit après confirmation.
> 
> Dans les pipelines CI, les environnements headless ou les scripts d'automatisation :
> - **Dans les Git hooks et l'injection dans un fichier de commit :** Utilisez toujours `--hook <chemin-du-fichier>` (`gitpr --commit --hook <fichier>`). Cela garantit une exécution strictement non interactive et écrit directement le message dans le fichier cible sans invites ni modales TUI.
> - **Dans les scripts automatisés sans TTY :** GitPR détecte les exécutions non interactives (`may_ask == False`) et bascule vers l'affichage de la suggestion sur la console sans ouvrir de modales et **sans créer de commit**. Si votre automatisation dépend du commit automatique des modifications en attente lors de la publication de PR, utilisez `gitpr --no-edit`.

---

## 2. Format Conventional Commits

L'IA est instruite de générer des messages selon le standard :

```
type: description courte

Corps optionnel avec détails supplémentaires
```

**Types utilisés :** `feat`, `fix`, `refactor`, `test`, `chore`, `docs`

---

## 3. Intégration avec les Git Hooks (Non interactif)

La commande `--commit` est utilisée en interne par le hook `prepare-commit-msg`. Lorsqu'il est installé via `gitpr -ih`, le hook exécute :

```bash
gitpr --commit --hook <chemin-du-fichier-temporaire>
```

Le flag `--hook` maintient l'exécution strictement non interactive : aucun écran TUI ni modale n'est ouvert, et le message suggéré est injecté directement dans l'éditeur de Git.

> [!TIP]
> **Bonnes pratiques pour la CI et l'automatisation headless :**  
> Lorsque vous appelez GitPR depuis des jobs CI/CD automatisés, des git hooks ou des scripts shell où les invites interactives ne doivent jamais bloquer, utilisez toujours `gitpr --commit --hook <fichier>`. Pour une inspection ponctuelle sur la console sans commiter, assurez-vous que l'exécution s'exécute dans un pipe non interactif ou passez `--no-unstaged-check` et `--quiet` selon vos besoins.

---

## 4. Configuration du staging et automatisation

Vous pouvez configurer le comportement de staging via des variables d'environnement dans `~/.gitpr/.env` :

- `GITPR_AUTO_STAGE=true` : Ajoute automatiquement tous les fichiers non stagés au stage sans ouvrir le sélecteur.
- `GITPR_SKIP_UNSTAGED_CHECK=true` : Ignore la vérification des fichiers hors du stage.
- `--no-unstaged-check` : Flag en ligne de commande pour ignorer la vérification des fichiers hors du stage pour une seule exécution.

---

## 5. Personnalisation via Skill

Le comportement de l'IA peut être personnalisé à travers le fichier `.gitpr.commit.md` dans `.gitpr/skill/` :

```bash
gitpr -s          # Télécharge le template .gitpr.commit.md
# Éditez le fichier selon les conventions de votre équipe
gitpr -c          # L'IA utilisera vos règles personnalisées
```

---

## 6. Sélection du fournisseur d'IA

```bash
gitpr -c -p gemini       # Force Google Gemini
gitpr -c -p deepseek     # Force DeepSeek
gitpr -c -p ollama       # Force Ollama local
```

---

## 7. Cache de réponses

GitPR génère un hash MD5 de votre diff du stage + instructions. Si vous exécutez `gitpr -c` à nouveau **sans modifier le code stagé**, la réponse est renvoyée instantanément depuis le cache local, économisant les quotas de l'API.

---

## 8. Signature de co-auteur

Chaque message de commit généré par GitPR porte automatiquement le trailer de co-auteur :

```text
Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>
```

Le trailer est ajouté programmatiquement (jamais par l'IA) dans tous les flux : TUI interactive de commit, hook `prepare-commit-msg`, auto-commit lors de la publication de PR et l'outil MCP `generate_commit_message`. Il est séparé du message par des lignes vides supplémentaires pour ne pas apparaître au premier coup d'œil dans les aperçus de commits de GitHub, et n'est jamais dupliqué lorsque le message le contient déjà.

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités.
