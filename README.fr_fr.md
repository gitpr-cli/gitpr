# **GitPR CLI 🚀** — Français

<p align="center">
  <img src="https://raw.githubusercontent.com/natanfiuza/gitpr/main/docs/logo.png" alt="GitPR Logo" width="150">
</p>

GitPR CLI est un outil d'automatisation en ligne de commande qui utilise l'intelligence artificielle de **Google Gemini** et **DeepSeek** pour analyser vos modifications de code (git diff) ou des fichiers entiers. L'outil génère automatiquement des messages de commit au standard *Conventional Commits*, des descriptions détaillées de Pull Request et des revues de code approfondies visant à réduire la dette technique.

🌐 **Site web :** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/) · 📂 **Dépôt :** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)

----

## ⚡ **Démarrage Rapide**

### **1. Installation via PyPI**

Installez GitPR CLI avec `pip` :

```bash
pip install gitpr-cli
```

### **2. Initialisation dans un Nouveau Dépôt**

Pour initialiser GitPR dans le dossier d'un nouveau dépôt, exécutez :

```bash
gitpr --install
```

> **Configuration Guidée :** Configuration guidée qui télécharge des modèles de skills, installe des Git Hooks, configure MCP pour vos éditeurs et vérifie la clé d'API de votre fournisseur d'IA.  
> 📖 **Documentation complète :** [https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=fr_fr](https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=fr_fr)

## **🛠️ Technologies et Bibliothèques Utilisées**

Ce projet a été développé en Python et utilise les bibliothèques principales suivantes :

* [**Click**](https://click.palletsprojects.com/) : Pour créer une interface en ligne de commande (CLI) robuste et conviviale.
* [**Google GenAI**](https://pypi.org/project/google-genai/) : SDK officiel pour l'intégration directe avec l'API Gemini.
* [**OpenAI**](https://pypi.org/project/openai/) : Bibliothèque utilisée en raison de sa compatibilité totale avec la puissante API **DeepSeek**.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/) : Pour la gestion sécurisée des variables d'environnement.
* [**Pytest**](https://docs.pytest.org/) : Pour exécuter des tests unitaires de manière simple, colorée et lisible dans la console.
* [**Cryptography**](https://cryptography.io/) : Pour garantir que votre `GEMINI_API_KEY` est stockée de manière chiffrée et sécurisée sur le disque.
* [**PyYAML**](https://pyyaml.org/) : Utilisé pour lire et traiter les règles personnalisées d'analyse statique du fichier `.gitpr.linter.yml`.
* [**Textual**](https://textual.textualize.io/) : Puissante bibliothèque pour créer des Interfaces Graphiques de Terminal (TUI), utilisée dans le panneau interactif de génération et d'édition d'issues.
* [**Requests**](https://pypi.org/project/requests/) : Bibliothèque élégante et robuste pour les requêtes HTTP, utilisée pour communiquer avec l'API REST de GitHub.
* [**MCP**](https://pypi.org/project/mcp/) : SDK Python officiel pour le Model Context Protocol, permettant à GitPR de s'intégrer directement avec les éditeurs et IDE dotés d'IA.

----

## 📦 Comment Compiler l'Exécutable Localement

Si vous souhaitez générer votre propre binaire à partir du code source, nous utilisons **PyInstaller**. Assurez-vous d'être dans le répertoire racine du projet avec l'environnement virtuel configuré.

1. Installez les dépendances de développement (si ce n'est pas déjà fait) :
   ```bash
   pipenv install --dev
   ```

2. Exécutez la commande de build en pointant vers notre point d'entrée (`run.py`) :
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Note technique :** Le flag `--onefile` garantit que tout Python, les bibliothèques et les dépendances sont compressés en un seul binaire. 🛠️

Après avoir exécuté cette commande, PyInstaller créera quelques dossiers (`build` et `dist`).
Votre fichier final prêt à l'emploi se trouvera dans le dossier **`dist/`** sous le nom `gitpr` (ou `gitpr.exe` sur Windows).


----

## 🧪 Exécution des Tests

Pour garantir que la logique de capture Git et l'intégration avec l'IA fonctionnent correctement, nous utilisons des tests unitaires.

1. Installez les dépendances de test (si ce n'est pas déjà fait) :
   ```bash
   pipenv install --dev pytest
   ```

2. Exécutez les tests avec la commande :
   ```bash
   pipenv run pytest -v
   ```
Pytest détectera automatiquement les fichiers dans le dossier `tests/` et affichera un rapport détaillé de l'exécution.

----
## **⚙️ Installation et Configuration**

### **Utilisation de l'Exécutable (Recommandé)**

1. Téléchargez l'exécutable GitPR depuis l'onglet "Releases" sur GitHub.
2. Déplacez l'exécutable vers un dossier qui se trouve dans votre PATH (ex. : /usr/local/bin sur Linux/Mac ou votre dossier utilisateur sur Windows).
3. Lors de la première exécution, l'assistant vous guidera :
   ```bash
   $ gitpr
   ```
```bash
🚀 Intelligent PR Automation with AI

🔧 First run detected! Let's configure GitPR CLI.

🔑 Enter your GEMINI_API_KEY:

📄 Default output filename pattern [{branch}_{datetime}_PR_DESC.md]:
```
*Note : Votre configuration sera enregistrée en toute sécurité dans le fichier `~/.gitpr/.env`.*

> **🔒 Note de Sécurité :** GitPR CLI utilise le chiffrement symétrique (Fernet). Votre clé API est stockée sous forme de hash dans le fichier `.env`, et la clé maîtresse pour le déchiffrement est générée automatiquement dans `~/.gitpr/secret.key`. **Ne partagez jamais votre fichier secret.key.**

### À Partir du Code Source

1. Clonez le dépôt : `git clone https://github.com/natanfiuza/gitpr.git`

2. Entrez dans le dossier : `cd gitpr`

3. Configurez l'environnement :
```bash
pipenv install google-genai openai python-dotenv click cryptography
```
4. Exécutez : pipenv run python src/main.py

## **💻 Comment Utiliser**

GitPR dispose d'un comportement par défaut puissant et de plusieurs options avancées pour vous assister dans votre quotidien de développeur.

### **Comportement par Défaut (Pull Request)**
Exécutez simplement la commande nue dans votre terminal :
```bash
gitpr
```
L'outil se synchronisera avec le dépôt distant (`git fetch`), comparera vos modifications avec la branche principale distante (ex. : `origin/main`) et générera un fichier Markdown (ex. : `feature-login_20260421110134_PR_DESC.md`) à la racine de votre projet avec la suggestion complète pour votre Pull Request.

### **Options et Commandes Avancées**
Vous pouvez passer les *flags* suivants pour des actions spécifiques :

* `-c` ou `--commit` : Exécute un `git diff` local et affiche **uniquement le message de commit suggéré**.
* `-r` ou `--review` : Effectue un **Code Review** détaillé des modifications locales.
* `-f` ou `--fullreview` : Effectue un **Code Review Complet** analysant toutes les modifications depuis la branche distante.
* `-i <fichier>` ou `--input <fichier>` : **Audit Complet de Fichier.** Doit être utilisé avec `-r` ou `-f` ; ignore l'historique git et fait un Code Review du fichier entier. Excellent pour agir comme consultant en refactorisation de code legacy.
* `--provider <gemini|deepseek|ollama>` : Force l'utilisation d'une IA spécifique uniquement pour cette exécution, en ignorant celle par défaut enregistrée dans `.env`.
* `--lang <code>` : Force la langue de l'interface pour cette exécution (ex. : `en_us`, `fr_fr`). Remplace `GITPR_LANG` du `.env` sans persister le changement.
* `-ch` ou `--chat` : Ouvre le **Chat Interactif de Pair Programming** — un terminal TUI où l'IA voit votre diff actuel et maintient une conversation contextuelle. Dispose d'une mémoire par branche, de commandes slash (`/explain`, `/tests`, `/optimize`, `/clear`), d'auto-patching (F5), de rafraîchissement de diff (F2) et d'exportation de session (F6).
* `-l` ou `--linter` : Exécute **uniquement le linter statique local** (sans appels à l'IA). Idéal pour une utilisation dans les pipelines CI/CD afin de bloquer le code non conforme.
* `--mcp` : Démarre GitPR en tant que **serveur MCP** (Model Context Protocol) sur le transport stdio. Permet l'intégration avec VS Code, Cursor, Claude Desktop et d'autres éditeurs compatibles MCP — exposant toutes les capacités IA de GitPR comme outils directement dans votre IDE. Également disponible en tant que commande autonome `gitpr-mcp`.
* `--install` : **Assistant de Configuration Interactif.** Exécute une configuration guidée en 4 étapes : télécharge les skill templates, installe les Git Hooks, configure MCP pour les éditeurs détectés et vérifie/demande votre clé API du fournisseur d'IA. Chaque étape demande confirmation avant de continuer.
* `-ih` ou `--installhooks` : Installe automatiquement les **Git Hooks locaux** (`pre-commit` et `prepare-commit-msg`) dans votre dépôt.
* `-s` ou `--skill` : Crée les fichiers de template de contexte IA (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) et le Linter (`.gitpr.linter.yml`) à la racine du projet.
* `-is` ou `--issue` : Génère automatiquement un brouillon d'une **Issue standardisée** et ouvre une interface interactive (TUI) pour l'édition ou l'envoi direct via l'API REST. Cette fonctionnalité dispose de **3 moteurs de contexte** selon la combinaison de commandes :
  * **Issue de Nouveau Code (`gitpr -is`) :** Lit le `git diff` actuel. **Pourquoi utiliser :** Idéal pour documenter rapidement la tâche que vous venez de programmer, avant de commiter.
  * **Issue d'Épique/Release (`gitpr -is -ht`) :** Lit l'historique complet de la branche actuelle (Git Log + Cache PR). **Pourquoi utiliser :** Idéal pour générer une documentation consolidée d'une release entière ou d'une *feature* importante qui a pris plusieurs jours/commits à terminer.
  * **Issue de Dette Technique/Archéologique (`gitpr -is -b fichier:lignes`) :** Lit la chronologie d'une règle métier spécifique. **Pourquoi utiliser :** Idéal pour documenter la dette technique, en expliquant comment un bloc de code legacy a évolué et pourquoi il doit être refactorisé.
* `-h` ou `--help` : Affiche l'aide générale avec toutes les options. Utilisez-le avec un autre flag pour une **aide contextuelle** (ex. : `gitpr -h --issue`, `gitpr -h --linter`) avec un lien direct vers la documentation détaillée de chaque fonctionnalité.
* `-u` ou `--update` : Vérifie et installe la version la plus récente de GitPR (Auto-Updater).

> **⚙️ Note Technique (--hook) :** GitPR possède un flag caché `--hook <fichier>` qui est déclenché exclusivement par le système de Git Hooks en arrière-plan. Il permet à l'IA d'injecter le message suggéré directement dans le fichier temporaire de Git, sans encombrer votre terminal.
>
> **⚙️ Note Technique (--pre-save) :** GitPR possède un flag caché de debug `--pre-save` qui peut être combiné avec n'importe quelle commande IA (ex. : `gitpr -c --pre-save`). Avant chaque appel à l'IA, il enregistre le payload complet qui sera envoyé au modèle (system instruction + prompt + compteurs de caractères) dans un fichier `_{action}-{dateheure}.json` dans le dossier actuel, puis poursuit normalement. Utile pour inspecter les prompts très volumineux. Note : lorsque la réponse provient du cache local, aucun appel n'est effectué et aucun fichier n'est généré.

### 📦 Diffs Volumineux (Map-Reduce)

Lorsque le diff est trop volumineux pour un seul appel à l'IA (au-dessus d'environ 90 000 tokens estimés), GitPR le divise automatiquement en lots par fichier, demande à l'IA un résumé technique de chaque partie (Map) et unifie le tout dans le message de commit, la review ou la description de PR finale (Reduce). Aucun flag nécessaire — s'active à la demande et affiche la progression dans la console.

📚 Documentation complète : [docs/map-reduce-diff.md](https://github.com/natanfiuza/gitpr/blob/main/docs/map-reduce-diff.md)

## 🛡️ Linter Local (Analyse Statique)

GitPR CLI vous permet de définir des règles strictes qui seront validées instantanément pendant `--review` ou `--fullreview`, sans dépendre de l'IA. C'est idéal pour empêcher les erreurs courantes (comme `console.log` ou les IP de test) d'atteindre le dépôt.

### Comment configurer `.gitpr.linter.yml` :
En exécutant `gitpr --skill`, un template sera généré. Vous pouvez configurer des règles en utilisant des Expressions Régulières (Regex) :

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensions à valider
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # Ce qu'il faut rechercher
    message: "🚨 Localhost usage detected in file {file_name}"
    ignore_comments: true # Ignore si la ligne est commentée
    ignore_paths: # Dossiers ou fichiers ignorés (accepte *)
      - "vendor/*"
      - "node_modules/*"
```

Le Linter analyse uniquement les **lignes ajoutées** dans votre `git diff`, garantissant une exécution ciblée et extrêmement rapide. S'il y a des violations, elles apparaîtront en évidence en haut de votre fichier de review.

## 🧠 Architecture Multi-Modèle (IA Agnostic)

GitPR n'est pas lié à une seule Intelligence Artificielle. Lors de la configuration initiale, l'utilisateur peut choisir son moteur par défaut. Nous prenons actuellement en charge :
* **Google Gemini** (Par défaut : `gemini-2.5-flash`)
* **DeepSeek** (Par défaut : `deepseek-chat`)
* **Ollama** (Local) — exécutez des modèles localement sans Internet, entièrement compatible avec le format de l'API OpenAI

Vous pouvez changer dynamiquement de modèles en configurant les variables `GEMINI_API_MODEL` ou `DEEPSEEK_API_MODEL` dans votre fichier `~/.gitpr/.env`, ou basculer en temps réel en utilisant le flag `--provider`.

## 🎯 Système de "Skills" Personnalisables (Prompt Engineering)

Au lieu de cacher les instructions d'IA dans le code source, GitPR utilise des fichiers Markdown locaux qui agissent comme des *System Instructions*. En exécutant `gitpr -s`, les fichiers suivants sont générés à la racine de votre projet pour personnaliser la "persona" de l'IA selon les règles métier de votre entreprise :

* `.gitpr.commit.md` : Règles pour générer des messages de commit courts.
* `.gitpr.pr.md` : Structure de rubriques obligatoire pour la description du Pull Request.
* `.gitpr.review.md` : Définit le focus architectural (ex. : SOLID, Clean Code) pour l'analyse du diff.
* `.gitpr.filereview.md` : Définit des règles strictes de cohésion et de couplage pour l'audit complet de fichier (utilisé avec `--input`).
* `.gitpr.issue.md` : Définit la structure et le niveau de détail requis pour générer des Issues standardisées (utilisé avec `--issue`).
* `.gitpr.blame.md` : Définit le focus de l'analyse archéologique pour le traçage de code legacy (utilisé avec `--blame`).

## 🌐 Internationalisation (i18n)

GitPR détecte automatiquement la langue de votre système et affiche les messages dans votre langue maternelle. Le système i18n est inspiré du **helper `__()` de Laravel** :

* **Détection automatique :** Lors de la première exécution, GitPR détecte la langue du système d'exploitation et l'enregistre dans `~/.gitpr/.env` (`GITPR_LANG`).
* **Fichiers de traduction :** Les packs de langue sont téléchargés automatiquement depuis le dépôt officiel vers `~/.gitpr/langs/`.
* **Fallback en anglais :** Si une traduction est manquante, le texte en anglais est affiché directement.
* **API développeur :** Utilisez `from src.i18n import __` et enveloppez toutes les chaînes d'interface avec `__("Votre texte ici")`.
* **Placeholders :** Prend en charge les paramètres nommés — `__("Téléchargement de {file}...", file="template.md")`.

Pour forcer une langue spécifique, définissez `GITPR_LANG=fr_fr` ou `GITPR_LANG=en` dans `~/.gitpr/.env`.

> 📖 **Guide complet du développeur :** [docs/i18n_explanation.md](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — architecture, modèles d'utilisation, précautions contre les imports circulaires et comment ajouter de nouvelles langues.

## 🔄 Versionnement et Synchronisation Automatique des Scripts de Hooks

GitPR inclut un système automatique de versionnement pour les scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Chaque fois que vous exécutez `gitpr`, le système vérifie silencieusement si vos hooks installés correspondent à la dernière version et les met à jour automatiquement si nécessaire — tout en respectant votre préférence linguistique.

**Fonctionnement :**
1. Lit `SCRIPTS_VERSION` et `SCRIPTS_LANG` depuis `~/.gitpr/.env`
2. Compare avec la dernière version (`__scripts_version__`) livrée avec votre version de GitPR
3. Si les versions ou la langue diffèrent → télécharge et met à jour les hooks automatiquement
4. Si tout correspond → ignore complètement (simple lecture du `.env`, zéro E/S réseau)

**Exemple :**
```bash
# Première exécution — aucun hook installé
$ gitpr --installhooks
📥 Téléchargement de pre-commit...
📥 Téléchargement de prepare-commit-msg...
✅ Scripts synchronisés avec succès !

# Exécutions suivantes — vérifications silencieuses
$ gitpr  # (aucune sortie = hooks à jour)
```

Le système prend en charge **5 langues** : Anglais (défaut), Portugais (Brésil), Portugais (Portugal), Français et Espagnol. Les scripts sont des thin shims — la logique réelle réside dans le CLI, donc même des hooks légèrement obsolètes continuent de fonctionner correctement.

📚 [Documentation Complète](https://gitpr.natanfiuza.dev.br/docs/hooks-versioning?lang=fr_fr)

## 🔌 Intégration MCP (Model Context Protocol)

GitPR peut s'exécuter en tant que **serveur MCP**, exposant ses capacités d'IA comme des outils que l'assistant IA de votre éditeur peut invoquer directement — sans avoir besoin du terminal. Cela permet un flux de travail totalement intégré où vous pouvez générer des messages de commit, réviser du code, exécuter des linters, tracer les origines du code et créer des issues sans quitter votre IDE.

### Éditeurs Compatibles

| Éditeur | Fichier de Configuration |
| ------- | ------------------------ |
| **VS Code** | `.vscode/mcp.json` |
| **Cursor** | `.cursor/mcp.json` |
| **Claude Code** | `.mcp.json` |
| **Claude Desktop** | `claude_desktop_config.json` |
| **Zed** | `settings.json` |

### Configuration Rapide

Utilisez l'installateur intégré pour configurer votre éditeur automatiquement :

```bash
gitpr-mcp --install vscode    # Crée .vscode/mcp.json
gitpr-mcp --install cursor      # Crée .cursor/mcp.json
gitpr-mcp --install claude-code # Crée .mcp.json
gitpr-mcp --install claude      # Met à jour la config de Claude Desktop
gitpr-mcp --install zed         # Met à jour la config de Zed
gitpr-mcp --install auto      # Auto-détecter et installer pour tous
```

L'installateur crée le répertoire de config si nécessaire, fusionne avec toute
config existante (ne remplace jamais les autres serveurs) et peut être exécuté
plusieurs fois en toute sécurité.

> La configuration manuelle est également prise en charge — voir [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md)
> pour le format JSON de chaque éditeur.

Une fois configuré, utilisez le langage naturel dans le chat IA de votre éditeur :

   * *"Révise mes modifications actuelles"* → appelle `review_code`
   * *"Génère un message de commit"* → appelle `generate_commit_message`
   * *"Crée une description de PR"* → appelle `generate_pr_description`
   * *"Exécute le linter sur mon diff"* → appelle `run_linter`

### Outils MCP Disponibles

| Outil | Description |
| ----- | ----------- |
| `get_git_context` | Branche actuelle, nom du dépôt et URL du remote |
| `analyze_diff` | Diff git des modifications non commitées |
| `get_full_diff` | Diff complet par rapport à origin/main |
| `generate_commit_message` | Message Conventional Commits généré par IA |
| `review_code` | Code review IA des modifications locales |
| `full_review` | Code review IA de toutes les modifications depuis origin/main |
| `generate_pr_description` | Description complète de PR (titre + corps) |
| `run_linter` | Linter statique basé sur `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + classification par IA |
| `generate_issue` | Issue structurée à partir du diff, de l'historique ou du blame |

📖 **Documentation complète :** [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — disponible en 5 langues (EN, PT-BR, PT-PT, ES, FR).

> 💬 **MCP Prompts** — GitPR expose également 7 modèles de message prédéfinis (prompts) pour les flux courants comme « Réviser la PR », « Générer un Message de Commit » et « Créer une Issue depuis le Diff ». Consultez le [guide MCP Prompts](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) pour la liste complète.

## 🎯 Smart Excludes (Optimisation des Tokens)

GitPR supprime automatiquement les fichiers non-code de votre `git diff` avant de les envoyer à l'IA — réduisant la consommation de tokens et les coûts d'API sans aucune configuration requise.

**Deux couches d'exclusions :**
- **Lockfiles et fichiers générés :** `package-lock.json`, `*.min.js`, `*.map`, `*.pyc`, `*.svg` et plus de 30 autres motifs définis dans [`gitpr.smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.smart-excludes.json)
- **Documentation en prose :** `*.md`, `*.txt`, `*.rst`, `*.adoc`, `*.tex` et plus de 20 autres extensions définies dans [`gitpr.docs-smart-excludes.json`](https://github.com/natanfiuza/gitpr/blob/main/templates/gitpr.docs-smart-excludes.json)

**Suivi de la documentation :** Même si le contenu de la documentation est exclu du diff, GitPR indique toujours à l'IA _quels_ fichiers de documentation ont été modifiés en injectant leurs chemins comme métadonnées dans les instructions système. L'IA dispose ainsi du contexte complet sur les mises à jour de documentation sans consommer de tokens sur leur prose.

**Avantages :**
- ✅ Jusqu'à **98 % de réduction de tokens** sur les branches riches en documentation
- ✅ **Réponses plus rapides de l'IA** — moins de texte à traiter par appel API
- ✅ **Analyse de meilleure qualité** — l'IA se concentre sur le code, pas sur le balisage
- ✅ **Zéro configuration** — fonctionne automatiquement à chaque exécution, géré à distance

> 📖 **Documentation complète :** [docs/smart-excludes.md](https://github.com/natanfiuza/gitpr/blob/main/docs/smart-excludes.md) — disponible en 5 langues (EN, PT-BR, PT-PT, FR, ES).

## 📚 Documentation Technique et Guides Avancés

Pour garder ce README concis, nous détaillons les implémentations les plus avancées axées sur le **DevOps** et l'**Intégration Continue** dans des documents séparés.

Si vous souhaitez implémenter GitPR comme une barrière de qualité automatisée dans votre équipe, consultez les guides ci-dessous.

> 🌐 Chaque guide est disponible en **5 langues** — ajoutez `.pt_br`, `.pt_pt`, `.fr_fr` ou `.es_es` avant l'extension `.md` pour les versions traduites (ex. : `docs/understanding_chat_functionality.fr_fr.md`). L'anglais est la langue par défaut sans suffixe.

### Chat et Fonctionnalités Interactives

* [**🧠 Chat Interactif (Pair Programming)**](https://github.com/natanfiuza/gitpr/blob/main/docs/understanding_chat_functionality.md) — Comment utiliser le chat IA avec mémoire, commandes slash, auto-patch et exportation de session.

### DevOps & CI/CD

* [**Git Hooks Locaux (Shift-Left)**](https://github.com/natanfiuza/gitpr/blob/main/docs/git-hooks-locais.md) — Comment utiliser `gitpr --installhooks` pour créer des barrières de qualité sur la machine du développeur et utiliser l'IA pour générer automatiquement des messages de commit.
* [**Versionnement et Synchronisation des Scripts de Hooks**](https://github.com/natanfiuza/gitpr/blob/main/docs/hooks-versioning.md) — Comment le système de versionnement automatique et de synchronisation avec support i18n maintient vos Git hooks à jour.
* [**Linter Statique Personnalisable**](https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md) — Comment créer des règles de validation dans `.gitpr.linter.yml` pour le CI/CD et les hooks de pre-commit.
* [**Intégration CI/CD (GitHub Actions)**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-ci-linter.md) — Comment exécuter GitPR dans le pipeline pour bloquer le "Merge" des PR avec des violations.

### Fonctionnalités Principales

* [**Pull Request (Mode par Défaut)**](https://github.com/natanfiuza/gitpr/blob/main/docs/pr-descricao-padrao.md) — Flux complet pour générer des descriptions de PR sans flags.
* [**Code Review avec IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/code-review-ia.md) — Guide des modes de review (`--review`, `--fullreview`) et d'audit de fichiers (`--input`).
* [**Messages de Commit avec IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/commit-message-ia.md) — Comment générer des messages au standard Conventional Commits et les intégrer avec Git Hooks.
* [**Génération d'Issues et Interface TUI**](https://github.com/natanfiuza/gitpr/blob/main/docs/issue-tui-help.md) — Comment utiliser l'interface graphique de terminal (TUI) et les 3 moteurs de contexte pour gérer des Issues structurées.
* [**Archéologue de Code (Git Blame)**](https://github.com/natanfiuza/gitpr/blob/main/docs/blame-arqueologo.md) — Comment tracer l'origine des règles métier avec `git blame` et l'IA.
* [**Système de Skills et Templates**](https://github.com/natanfiuza/gitpr/blob/main/docs/skill-template.md) — Comment personnaliser le comportement de l'IA avec les fichiers `.gitpr.*.md`.

### Configuration et Infrastructure

* [**Assistant d'Installation**](https://github.com/natanfiuza/gitpr/blob/main/docs/install-wizard.md) — Configuration guidée étape par étape pour installer GitPR dans un nouveau projet.
* [**Fournisseurs d'IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/providers-ia.md) — Configuration et sélection entre Google Gemini, DeepSeek et Ollama.
* [**Auto-Updater**](https://github.com/natanfiuza/gitpr/blob/main/docs/auto-update.md) — Comment fonctionne la mise à jour automatique (hot-swap) de GitPR.
* [**Token GitHub (PAT) — Intégration et Sécurité**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration.md) — Comprenez comment GitPR crée des issues directement dans le dépôt avec authentification.
* [**Internationalisation (i18n)**](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — Architecture, modèles d'utilisation et comment ajouter de nouvelles langues.
* [**Intégration MCP**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — Connectez GitPR à VS Code, Cursor et Claude Desktop via le Model Context Protocol.
* [**MCP Prompts**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) — Modèles de message prédéfinis (7 prompts, 35 variantes linguistiques) pour les flux courants dans le chat IA de votre éditeur.
* [**MCP Tool Annotations**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-annotations.md) — Conseils d'intégration avec les IDEs (`readOnlyHint`, `destructiveHint`) pour un comportement UI plus intelligent et une exécution sécurisée des outils.
* [**Métriques et Télémétrie**](https://github.com/natanfiuza/gitpr/blob/main/docs/metricas-telemetria.md) — Analytics local hors ligne pour les métriques d'utilisation d'équipe, rapports CSV exportables et tableau de bord TUI interactif.

## ⚡ Système de Cache Local (Économie de Quota)

GitPR dispose d'un moteur de cache intelligent basé sur **MD5**. Chaque fois que vous exécutez une commande (`--review`, `--commit`, etc.), l'outil génère un hash exact de votre code actuel (diff) et des instructions.
Si vous exécutez à nouveau la même commande sans modifier le code, GitPR intercepte la requête et renvoie le résultat instantanément (en millisecondes) depuis le dossier `~/.gitpr/cache/prompts/`, vous faisant gagner du temps et économisant vos quotas d'API Gemini !

## 🔄 Auto-Updater (Mise à Jour Over-The-Air)

Ne vous souciez plus jamais de télécharger manuellement les nouvelles versions. GitPR dispose d'un Gardien de Connexion et d'un outil de mise à jour intégré :
* Il vérifie la disponibilité du réseau avant de démarrer pour ne pas bloquer votre flux de travail hors ligne.
* À chaque exécution, il vérifie silencieusement s'il existe une nouvelle release officielle sur l'API GitHub.
* Vous pouvez forcer la vérification et l'installation en exécutant `gitpr --update` ou `gitpr -u`.
* L'outil utilise la technique de *Hot-Swap*, en téléchargeant le nouveau `.exe` et en remplaçant l'ancienne version de manière transparente.

## Publication sur PyPI

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 Comment Contribuer**

Les contributions sont les bienvenues ! Pour contribuer :

1. Faites un fork du projet.
2. Créez une branche pour votre *feature* (git checkout -b feature/NouvelleFonctionnalite).
3. Faites commit de vos modifications (git commit -m 'feat: ajoute nouvelle fonctionnalité'). Astuce : Utilisez GitPR lui-même pour générer ce message ! 😄
4. Faites push vers la branche (git push origin feature/NouvelleFonctionnalite).
5. Ouvrez un Pull Request.

## **✨ Remerciements et Paternité**

Projet conçu et développé par :

**Natan Fiuza** - [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 Licence**

Ce projet est sous licence **GNU Lesser General Public License v2.1 (LGPL-2.1)**. Consultez le fichier LICENSE pour plus de détails.
