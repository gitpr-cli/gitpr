# Documentation technique : Interface graphique de terminal (TUI) — Issues

Cette documentation décrit le fonctionnement de l'interface graphique interactive (TUI) de GitPR pour la génération et la gestion des Issues, construite avec la bibliothèque Python `textual`.

---

## 1. Qu'est-ce que la TUI d'Issues ?

Lorsque vous exécutez la commande `gitpr --issue` (ou `-is`), GitPR analyse votre code et ouvre un panneau interactif directement dans le terminal. Cela vous permet de réviser, d'éditer et d'améliorer l'issue générée par l'Intelligence Artificielle avant de l'enregistrer ou de l'envoyer vers le dépôt distant.

---

## 2. Moteurs de contexte (3 modes de génération)

La fonctionnalité d'Issues possède **3 moteurs de contexte** distincts, déclenchés selon les flags combinés avec `--issue`. Chaque moteur alimente l'IA avec un ensemble différent d'informations, adapté au moment du cycle de développement.

### 2.1 Issue de code nouveau — `gitpr -is`

**Contexte :** `git diff` actuel (modifications non committées).

```bash
gitpr -is
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | Diff local (`git diff HEAD`) |
| **Quand l'utiliser** | Avant de committer — vous venez de programmer et voulez documenter la tâche |
| **Résultat** | Issue décrivant exactement ce qui se trouve dans votre working tree |
| **Idéal pour** | Documentation rapide de features, corrections et refactorisations récemment implémentées |

> **Astuce :** C'est le mode le plus rapide. L'IA ne lit que les lignes que vous avez modifiées et génère une issue ciblée et objective.

---

### 2.2 Issue d'Épopée / Release — `gitpr -is -ht`

**Contexte :** Historique complet de la branche actuelle (Git Log + Cache des PRs précédentes).

```bash
gitpr -is -ht
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | `git log` de la branche + cache local des PRs générés par GitPR |
| **Quand l'utiliser** | À la fin d'une branche de fonctionnalité avec plusieurs commits ou lors de la clôture d'une release |
| **Résultat** | Issue consolidée avec le panorama complet de tout ce qui a été développé |
| **Idéal pour** | Épopées, releases, grandes fonctionnalités qui ont pris plusieurs jours/commits à finaliser |

> **Astuce :** GitPR parcourt l'historique des commits exclusifs de votre branche et les rapports de PR déjà générés pour construire une vision de haut niveau. S'il n'y a pas de commits exclusifs ou de PRs précédentes, la commande affichera un avertissement et s'interrompra.

---

### 2.3 Issue archéologique / Dette technique — `gitpr -is -b arquivo:linhas`

**Contexte :** Chronologie d'un bloc de code spécifique via `git blame`.

```bash
gitpr -is -b src/core.py:140-195
```

| Caractéristique | Description |
| --- | --- |
| **Source de données** | `git blame` (historique des modifications ligne par ligne) + traçage des commits parents (jusqu'à 4 niveaux) |
| **Quand l'utiliser** | En identifiant du code legacy qui a besoin de refactorisation ou pour documenter une dette technique |
| **Résultat** | Issue contenant la chronologie du bloc : quand il est apparu, qui l'a modifié, comment il a évolué et pourquoi il doit être refactorisé |
| **Idéal pour** | Documenter des dettes techniques, justifier des refactorisations, comprendre l'évolution de code critique |

> **Astuce :** Vous pouvez aussi utiliser le format interactif : `gitpr -is -b arquivo` (sans spécifier de lignes). GitPR demandera quelles lignes investiguer.

---

## 3. Structure de l'Issue (Quoi / Pourquoi / Où / Comment)

L'IA de GitPR est instruite de générer le brouillon de l'issue en suivant un standard rigoureux d'ingénierie logicielle pour faciliter la communication de l'équipe :

| Section | Description |
| --- | --- |
| **Quoi (What)** | Checklists directes sur les fonctionnalités créées ou les problèmes identifiés |
| **Pourquoi (Why)** | Le contexte et la motivation technique derrière l'implémentation |
| **Où (Where)** | Spécification des routes, modules, pages ou ressources affectés |
| **Comment (How)** | Détail technique divisé en Backend/Moteur, Base de données/Données et Frontend/CLI/Interface |

> **Personnalisation :** Vous pouvez personnaliser le template utilisé par l'IA via le fichier `.gitpr.issue.md` à la racine du projet (téléchargez-le avec `gitpr -s`).

---

## 4. Raccourcis et navigation de la TUI

L'interface a été conçue pour être rapide et éviter l'utilisation constante de la souris. Vous pouvez naviguer entre les champs à l'aide de la touche `Tab` et utiliser les raccourcis suivants :

| Touche | Action | Description |
| --- | --- | --- |
| **`F1`** | Aide | Ouvre un modal flottant avec des instructions rapides d'utilisation de l'interface |
| **`F2`** | Enregistrer `.md` local | Exporte le contenu de l'écran vers un fichier Markdown dans le dossier actuel du projet. Idéal lorsque vous ne voulez que le brouillon pour l'affiner ultérieurement |
| **`F3`** | Créer sur GitHub | Se connecte à l'API REST de GitHub et crée automatiquement l'issue dans le dépôt distant. Le lien direct vers l'issue nouvellement créée sera affiché dans le terminal |
| **`F4`** | Aide (alternatif) | Raccourci alternatif pour ouvrir les instructions de la TUI |
| **`Esc`** | Quitter | Interrompt l'opération et ferme l'interface sans enregistrer aucune modification |
| **`Tab`** | Naviguer | Alterne le focus entre les champs de titre et de corps de l'issue |

---

## 5. Intégration avec GitHub (Token PAT)

Pour créer des issues directement dans le dépôt distant (`F3`), GitPR a besoin d'un **Personal Access Token (PAT)** de GitHub avec la portée `repo`.

### 5.1 Configuration du token

La première fois que vous utilisez `F3`, GitPR va :

1. Détecter qu'aucun token n'est configuré
2. Afficher l'URL de génération du token avec les paramètres pré-remplis (portée `repo`)
3. Demander que vous colliez le token généré
4. Le stocker chiffré (Fernet) dans le fichier `~/.gitpr/.env`

### 5.2 Sécurité

- Le token est stocké sous forme de hash chiffré — jamais en texte clair
- La clé maîtresse de déchiffrement reste dans `~/.gitpr/secret.key`
- Consultez le guide complet dans [github-pat-integration.md](github-pat-integration.md)

---

## 6. Exemples pratiques

### Exemple 1 : Documenter une feature avant de committer

```bash
# Você acabou de implementar um sistema de login
gitpr -is
# → A IA lê o diff, gera o rascunho e abre a TUI
# → Revise, ajuste o texto se necessário
# → Pressione F3 para criar a issue no GitHub
```

### Exemple 2 : Générer une issue de release

```bash
# Sua branch feature/payment tem 15 commits ao longo de 3 dias
git checkout feature/payment
gitpr -is -ht
# → A IA consolida todo o histórico em uma issue de épico
```

### Exemple 3 : Documenter une dette technique

```bash
# Você encontrou um bloco de código confuso no arquivo legado
gitpr -is -b src/legacy/parser.py:200-350
# → A IA rastreia a evolução do bloco desde o commit original
# → Gera uma issue explicando a dívida técnica e sugerindo refatoração
```

---

## 7. Fichiers associés

| Fichier | Fonction |
| --- | --- |
| `.gitpr.issue.md` | Template local avec règles personnalisées pour la génération d'issues (téléchargez-le avec `gitpr -s`) |
| `~/.gitpr/.env` | Configuration globale : clés d'API et token GitHub chiffré |
| `~/.gitpr/secret.key` | Clé maîtresse Fernet pour le déchiffrement des identifiants |

> **Note :** Consultez également la [documentation principale (README.md)](../README.md) pour un aperçu de toutes les fonctionnalités de GitPR.
