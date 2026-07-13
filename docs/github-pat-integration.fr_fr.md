# Documentation technique : Intégration et sécurité du token GitHub (PAT)

Pour que la fonctionnalité de création directe d'Issues (`gitpr --issue`) fonctionne de manière automatisée, GitPR doit communiquer avec l'**API REST de GitHub**. Cette documentation explique comment cette authentification se déroule et comment vos identifiants sont protégés localement.

📖 **Documentation associée :** [Guide de l'option `--issue` (gitpr-issue-option.md)](gitpr-issue-option.md)

## 1. Pourquoi avons-nous besoin d'un token (PAT) ?
La création d'issues dans des dépôts distants de manière programmatique exige une authentification. GitHub recommande l'utilisation d'un **Personal Access Token (PAT)** afin que les outils en ligne de commande (CLI) puissent interagir avec votre compte de développeur en toute sécurité.

## 2. Portée nécessaire (`repo`)
GitPR n'a besoin que de la portée **`repo`** activée au moment de la création de votre PAT. Cela garantit la permission de lire les métadonnées et de créer l'Issue dans le bon projet (qu'il soit privé ou public).
Pour accélérer ce processus, le CLI lui-même génère une URL de configuration dynamique. Il extrait le nom de votre dépôt local et construit un lien qui s'ouvre dans votre navigateur avec les bonnes options déjà présélectionnées.

## 3. Sécurité et chiffrement local (Design Patterns)
La sécurité de vos identifiants est traitée avec le plus grand sérieux. GitPR n'envoie **jamais** votre clé à des serveurs tiers autres que l'API de GitHub elle-même.

* **Chiffrement symétrique (Fernet) :** Dès que vous collez votre token dans le terminal, GitPR utilise la bibliothèque native `cryptography` pour chiffrer la chaîne en temps réel.
* **Stockage sécurisé :** Le token chiffré est enregistré de manière permanente dans le fichier global `~/.gitpr/.env` (dans le dossier racine de votre utilisateur, inaccessible aux autres utilisateurs du système d'exploitation).
* **Clé maîtresse de déchiffrement :** La clé maîtresse nécessaire pour inverser ce chiffrement reste isolée sur votre machine locale (`~/.gitpr/secret.key`).

Grâce à cette architecture, en cas de fuite locale et si un script malveillant lit votre fichier `.env`, votre token GitHub restera absolument illisible et protégé.
