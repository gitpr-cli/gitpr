# 🚀 Création et Gestion des Issues avec GitPR CLI

La fonctionnalité `--issue` (ou `-is`) transforme GitPR en un assistant de documentation avancé. Au lieu d'écrire des Issues à partir de zéro, l'Intelligence Artificielle lit votre contexte de travail, structure l'issue selon le standard **Quoi / Pourquoi / Où / Comment** et ouvre une interface visuelle directement dans votre terminal pour que vous puissiez la réviser avant l'envoi.

---

## 1. Le Triple Moteur de Contexte (Lequel utiliser et pourquoi ?)

L'IA de GitPR peut lire trois « langages » différents selon la combinaison de flags que vous utilisez. Chaque moteur a été conçu pour un scénario spécifique du quotidien du développeur :

### 🆕 Issue de Nouveau Code (Le Par Défaut)
**Commande :** `gitpr --issue` ou `gitpr -is`
* **Comment ça fonctionne :** GitPR lit votre `git diff` actuel (les modifications que vous venez de faire et qui ne sont pas encore commitées).
* **Pourquoi l'utiliser :** Idéal pour documenter rapidement une petite *feature* ou un *bugfix* que vous venez de coder, garantissant que le suivi du problème est enregistré sur GitHub avant d'envoyer le code.

### 📦 Issue de Release / Épique
**Commande :** `gitpr -is -ht` (Issue + History)
* **Comment ça fonctionne :** GitPR compile tout le `git log` de la branche actuelle et le combine avec la banque de mémoire de l'IA (en cherchant les descriptions des anciens PRs de cette branche dans le cache local).
* **Pourquoi l'utiliser :** Si vous avez travaillé pendant plusieurs jours sur une branche, cette commande génère une super issue résumant l'ensemble de la *feature*. Excellent pour fournir une documentation consolidée de Release aux équipes QA ou Produit.

### 🕰️ Issue Archéologique / Dette Technique
**Commande :** `gitpr -is -b src/fichier.py:10-20` (Issue + Blame)
* **Comment ça fonctionne :** GitPR ne regarde pas le nouveau code. Il déclenche le Moteur Archéologique pour lire la chronologie et l'évolution historique de ces lignes spécifiques.
* **Pourquoi l'utiliser :** Idéal pour documenter la dette technique. L'IA structure une issue expliquant comment une règle métier héritée a évolué au fil du temps, pourquoi elle est devenue un problème et la justification d'une future refactorisation.

---

## 2. Authentification et Jeton PAT

Pour que GitPR puisse créer l'Issue directement dans votre dépôt distant, il doit communiquer avec l'**API REST de GitHub**.

1. La première fois que vous exécutez la commande, l'outil vous demandera un **Personal Access Token (PAT)**.
2. GitPR génère un lien intelligent et l'affiche dans le terminal. Il suffit de cliquer dessus : votre navigateur s'ouvrira directement sur la page de création de jetons de GitHub avec la permission appropriée (`repo`) pré-sélectionnée.
3. Collez le jeton dans le terminal.

**Sécurité :** Votre jeton ne circule jamais en texte clair. Dès que vous le collez, GitPR utilise la bibliothèque `cryptography` pour chiffrer la clé de manière symétrique, ne sauvegardant que le hash sécurisé dans le fichier caché `~/.gitpr/.env` de votre machine.

---

## 3. Interface Graphique de Terminal (TUI)

Une fois que l'IA a traité le contexte et structuré l'Issue, GitPR n'envoie pas les données aveuglément. Il ouvrira une interface interactive basée sur la bibliothèque `textual`.

Sur cet élégant écran bleu, vous pouvez modifier librement le Titre et le Corps de l'issue. Lorsque vous êtes satisfait, utilisez des raccourcis clavier rapides (sans avoir besoin de la souris) :

* **`F4` (Aide) :** Ouvre une modale avec des explications rapides sur l'interface.
* **`F2` (Enregistrer Localement) :** Exporte le contenu de l'écran vers un fichier Markdown (`.md`) dans votre dossier actuel. Utile si vous souhaitez simplement le brouillon pour le peaufiner plus tard.
* **`F3` (Créer sur GitHub) :** Déclenche la requête officielle. En quelques secondes, GitPR ferme l'écran et affiche dans le terminal le lien vert de votre nouvelle issue créée et publiée sur le dépôt.
* **`Esc` (Quitter) :** Annule l'opération en toute sécurité sans rien enregistrer.
