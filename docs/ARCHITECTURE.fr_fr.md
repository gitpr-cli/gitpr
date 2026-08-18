# **🚀 GitPR - Automatisation Intelligente de Code Review et Pull Requests**

**GitPR** est un outil d'Interface de Ligne de Commande (CLI) développé en Python qui agit comme un assistant d'ingénierie logicielle directement dans le terminal. Il combine la rapidité des validations statiques locales avec la puissance analytique d'Intelligences Artificielles (**Google Gemini**, **DeepSeek** et **Ollama** — local) pour automatiser et élever la qualité des Commits, Code Reviews, Issues et Pull Requests.

Au-delà de la CLI, GitPR fonctionne également comme **serveur MCP (Model Context Protocol)** — exposant toutes ses capacités d'IA aux éditeurs tels que VS Code, Cursor, Claude Desktop, Zed et Claude Code — et offre des interfaces TUI (Textual) pour la publication de PRs, la création d'Issues, le chat de programmation en binôme et un tableau de bord de métriques.

## **🎯 À quoi ça sert ?**

L'objectif principal de GitPR est d'éliminer le travail répétitif et de garantir un haut standard de qualité (*Quality Gate*) dans le cycle de vie du développement logiciel. Il résout trois problèmes principaux :

1. **Historique Git Pollué :** Impose l'utilisation de *Conventional Commits* et génère automatiquement des messages sémantiques — y compris via des git hooks installés dans le dépôt.  
2. **Pull Requests Vides ou Pauvres :** Rédige des descriptions détaillées basées sur le diff, en séparant les changements techniques de l'impact métier, et publie la PR directement sur GitHub via la TUI.  
3. **Dette Technique et Bugs :** Réalise des Code Reviews sémantiques et des validations de règles (Regex) avant même que le code ne quitte la machine du développeur (approche *Shift-Left*), plus une archéologie de code avec `git blame` pour retracer l'origine des règles métier.

---

## **✨ Fonctionnalités Principales**

* **📝 Auto-Commit (`-c` / `--commit`):** Lit les changements *staged* (git diff) et génère un message de commit concis au format impératif (Conventional Commits). En mode hook (`--hook`), injecte le message directement dans le fichier temporaire de Git ; ignore les merges, squashes et amends. Les commits portent le trailer `Co-Authored-By`, ajouté uniquement au moment de l'exécution — les écrans d'édition de la TUI ne l'affichent jamais.  
* **📖 Génération de Pull Request → Éditeur de PR (Par défaut):** Analyse le diff entre la branche courante et la branche principale, générant un .md avec résumé, impact et détails techniques. Ouvre ensuite une TUI (Textual) pour réviser, éditer et publier la PR directement sur GitHub — avec auto-commit validé par le linter, push automatique, mise à jour de la PR existante et merge optionnel. Modificateurs : `--no-publish` (enregistre en local uniquement), `--no-edit` (publie directement, sans TUI) et `--base <branch>` (branche cible).  
* **🕵️ Code Review Intelligent (`-r` / `--review`):** Inspecte le code modifié à la recherche de mauvaises pratiques d'architecture, de violations de SOLID et de vulnérabilités de sécurité.  
* **🔬 Audit de Fichier Complet (`-i` / `--input`):** Permet de pointer GitPR vers un fichier spécifique (ex. : du code legacy) pour que l'IA réalise une analyse architecturale de haut en bas, en suggérant des refactorisations pour l'ensemble du fichier.  
* **⚡ Linter Statique Local (`-l` / `--linter`):** Un moteur d'Expressions Régulières (Regex) ultra-rapide qui s'exécute localement pour détecter les erreurs évidentes (ex. : console.log, clés en dur) sans dépenser de tokens d'IA. Prend également en charge les **linters externes** (ESLint, PHPCS, Stylelint) via un pont Checkstyle — configurés par un assistant interactif (`--linter-setup`).  
* **🪝 Intégration aux Git Hooks (`-ih` / `--installhooks`):** Injecte GitPR dans le cycle naturel de Git, en exécutant le Linter lors d'un pre-commit ou en suggérant des messages lors d'un prepare-commit-msg. Installe **5 hooks** (pre-commit, prepare-commit-msg, pre-push, post-checkout, post-merge) avec **auto-sync versionné et localisé** (EN, PT-BR, PT-PT, ES, FR).  
* **🗿 Archéologie de Code (`-b` / `--blame`):** Retrace l'origine d'une règle métier avec `git blame` + IA (profondeur maximale de 4 commits parents), en classant chaque commit comme **ORIGIN** ou **REFACTORING** et en générant une chronologie avec résumé exécutif.  
* **📋 Issues Standardisées (`-is` / `--issue`):** Génère un brouillon d'Issue au format **What / Why / Where / How** et ouvre une TUI pour l'édition ou la publication via l'API REST de GitHub. Dispose de **3 moteurs de contexte** : diff (par défaut), historique de la branche (`-ht`) et blame (`-b file:lines`).  
* **💬 Chat de Programmation en Binôme (`-ch` / `--chat`):** TUI interactive où l'IA voit le diff actuel et maintient une conversation contextuelle, avec mémoire par branche, slash commands (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patch et export de session.  
* **🔌 Serveur MCP (`--mcp` / `gitpr-mcp`):** Expose toutes les capacités d'IA sous forme de **12 tools**, **resources** et **7 prompts** pour les éditeurs compatibles MCP (VS Code, Cursor, Claude Desktop, Zed, Claude Code). Installation automatique via `gitpr-mcp --install <editor|auto>`. Invocation directe sans serveur persistant : `gitpr-mcp --tool <name> --tool-args '{...}'` — JSON sur stdout, diagnostic sur stderr (sûr pour les pipes, scripts et CI).  
* **📊 Métriques et Télémétrie Locale (`--metrics` / `--dashboard`):** Collecte hors ligne d'événements (commande, statut, fournisseur, tokens, durée) avec export CSV/JSON et tableau de bord TUI à portée par dépôt, enrichi de tokens réels lus depuis le cache de prompts.  
* **🧙 Assistant de Configuration (`--install`):** Configuration guidée en 4 étapes — modèles de skills, git hooks, configuration MCP dans les éditeurs détectés et vérification de la clé API du fournisseur d'IA.  
* **🔎 Statut des Fichiers (`--status`):** Liste les fichiers non commités, catégorisés (new / modified / deleted) — rapide, sans IA et sans réseau.  
* **🧩 Système de Plugins (`--plugins`):** Packs globaux de règles de linter (`~/.gitpr/plugins/linter/*.yml`) et de prompts MCP (`~/.gitpr/plugins/prompts/*.md`) appliqués de manière additive à tous les projets.  
* **🔄 Multi-Model (Agnostique de l'IA):** Permet de choisir entre **Google Gemini**, **DeepSeek** ou **Ollama** (local, sans réseau) comme moteur de raisonnement, en basculant dynamiquement via le .env ou le flag `--provider`, avec bascule automatique entre les fournisseurs.  
* **🌐 Internationalisation (`--lang`):** Interface en 5 langues avec détection automatique du système d'exploitation, repli vers l'anglais et override temporaire par flag.  
* **🗜️ Optimisation des Tokens (Map-Reduce + Smart Excludes):** Les diffs au-dessus de ~90k tokens sont découpés en chunks par fichier et résumés (Map) avant la consolidation finale (Reduce). Les lockfiles, fichiers minifiés et la documentation sont exclus du diff automatiquement (listes distantes + configuration locale par projet).  
* **🔄 Auto-Update (`-u` / `--update`):** Consulte les Releases de GitHub (binaire) ou PyPI (pip) et remplace son propre exécutable (*hot-swap*) avec rollback en cas d'échec.  

---

## **🛠️ Détails de Développement et d'Architecture**

GitPR a été conçu en mettant l'accent sur la **Performance**, la **Sécurité** et l'**Extensibilité**.

### **1. Facade/Mediator (core.py)**

Le module `core.py` orchestre tout : opérations git, assemblage des prompts, cache, skills, hooks, smart excludes et sortie des fichiers. La CLI (`main.py`) ne fait que router les flags ; les modules spécialisés (IA, linter, blame, issues, MCP, métriques, TUI) sont coordonnés par le core. Les composants visuels restent isolés dans le sous-package `src/ui/`.

### **2. Système de "Skills" (Prompt Engineering Découplé)**

Au lieu d'avoir les *prompts* de l'IA codés en dur dans le code Python, GitPR utilise un système de fichiers .md locaux (Skills) qui agissent comme des *System Instructions*.

* .gitpr.commit.md  
* .gitpr.pr.md  
* .gitpr.review.md  
* .gitpr.filereview.md  
* .gitpr.issue.md  
* .gitpr.blame.md  

Cela permet à chaque équipe d'adapter la « personnalité » et les règles métier de l'IA sans modifier une seule ligne du code source de l'outil. Les fichiers vivent dans `.gitpr/skill/` (avec migration automatique des chemins legacy depuis la racine du projet).

### **3. Strategy Pattern pour les Fournisseurs d'IA**

Le module `ai_providers.py` isole la communication avec les APIs externes. Le moteur (Core) ne demande qu'un JSON, et ce module décide comment formater la requête en utilisant le SDK de Google (Gemini) ou le SDK d'OpenAI (DeepSeek et Ollama — 100% compatibles avec l'API OpenAI). Caractéristiques :

* **Retry Automatique** (3 tentatives, intervalle de 2s) pour les instabilités réseau.  
* **Bascule automatique** vers l'autre fournisseur en cas d'échec du fournisseur configuré.  
* **JSON structuré obligatoire** et temperature 0.0 pour une sortie déterministe.  
* **Hiérarchisation des modèles par complexité :** les tâches simples (commit) utilisent le modèle secondaire/économique ; les tâches avancées (review, PR, issue) utilisent le modèle primaire.

### **4. Sécurité des Clés (Cryptography)**

Les clés API (API_KEYS) ne sont jamais enregistrées en clair. Le module `security.py` utilise la bibliothèque cryptography (Fernet) pour générer une clé maîtresse locale et stocker les identifiants chiffrés dans le fichier `~/.gitpr/.env`. Le **GitHub PAT** suit le même schéma et est validé contre `api.github.com/user` avant toute utilisation, avec une boucle de ré-authentification (max. 3 tentatives) en cas d'expiration.

### **5. Système de Cache MD5**

Pour économiser la consommation de Tokens d'IA (argent) et le temps (latence), GitPR crée un hash MD5 du *prompt* généré à partir du *diff*. Si le développeur demande un Code Review du même code deux fois, le système récupère la réponse du répertoire `~/.gitpr/cache/prompts/` instantanément. Chaque entrée stocke **repo + branch** — le double filtre évite les collisions entre projets portant le même nom de branche, et l'historique des PRs en cache alimente le contexte des issues d'historique (`-ht`).

### **6. Triple « Quality Gate » (Performance)**

L'outil a été conçu pour équilibrer la consommation de ressources :

* **Couche 1 (Linter Local) :** Rapide (<100ms), hors ligne, axée sur la syntaxe (via linter_engine.py et .gitpr.linter.yml).  
* **Couche 2 (Linters Externes) :** Pont Checkstyle — exécute ESLint/PHPCS/Stylelint et filtre les erreurs uniquement pour les lignes modifiées dans le diff.  
* **Couche 3 (IA Cloud) :** Profonde (2s-8s), en ligne, axée sur la sémantique et l'intention.

### **7. Map-Reduce pour les Diffs Géants**

Lorsque le diff dépasse ~90k tokens estimés, GitPR le découpe en chunks par fichier (en préservant les en-têtes `diff --git`), demande à l'IA un résumé technique de chaque partie (Map) et unifie le tout dans le message final de commit, review, PR ou issue (Reduce). Activation automatique, sans flags — avec progression dans la console et métrique dédiée.

### **8. Smart Excludes (Optimisation des Tokens)**

Les fichiers non-code sont retirés du diff avant son envoi à l'IA, avec deux couches contrôlées à distance : lockfiles/générés (`.lock`, `*.min.js`, `*.map`, `*.svg`…) et prose de documentation (`*.md`, `*.txt`, `*.rst`…). La documentation modifiée est tout de même communiquée à l'IA sous forme de **métadonnées** (uniquement les chemins, sans contenu). Chaque projet peut ajouter des exclusions locales dans `.gitpr/conf/gitpr.smart-excludes.json`, fusionnées avec la liste globale à l'exécution. Overrides via env : `GITPR_SKIP_SMART_EXCLUDES`.

### **9. Vérification des Fichiers Unstaged**

Avant toute commande d'IA, GitPR liste les fichiers non commités (new/modified/deleted) et propose une TUI de sélection de staging — ou un auto-stage lorsque `GITPR_AUTO_STAGE=true`. Le comportement est adapté par commande (PR/issue exigent le staging, review informe seulement) et peut être désactivé avec `--no-unstaged-check`.

### **10. Sortie Centralisée (.gitpr/reports/)**

Tous les artefacts générés (PR, review, full review, file review, blame, issue, linter) sont enregistrés dans `.gitpr/reports/<type>/` via `resolve_output_path()`. Les chemins personnalisés du `.env` (avec séparateur de répertoires) sont respectés — seuls les noms de fichiers « nus » sont redirigés (rétrocompatible). Le rapport du linter n'est généré que lorsque des violations sont trouvées.

### **11. Télémétrie Hors Ligne (Fire-and-Forget)**

Le module `metrics.py` enregistre les événements sur des threads daemon — la télémétrie ne peut jamais casser la CLI. Chaque événement stocke la commande, le statut, le fournisseur, les tokens, la durée (via `time.perf_counter()`), le repo et la branche. Le tableau de bord enrichit les événements avec des **tokens réels** lus depuis le cache de prompts et fusionne de manière incrémentale avec le cache.

### **12. Système de Plugins Globaux**

`~/.gitpr/plugins/` contient des packs de règles de linter (`linter/*.yml`) et des modèles de prompts MCP (`prompts/*.md`). Les règles sont fusionnées **de manière additive** avec le `.gitpr.linter.yml` du projet ; les prompts deviennent des resources et prompts MCP dynamiques via des factory closures (évitant le late-binding dans les boucles). Les plugins malformés génèrent un avertissement, sans jamais casser l'exécution.

### **13. Serveur MCP (Isolation de stdout)**

Le `mcp_server.py` s'exécute sur stdio et expose 12 tools annotées (`get_git_context`, `analyze_diff`, `analyze_unstaged_diff`, `get_full_diff`, `list_unstaged_files`, `generate_commit_message`, `review_code`, `full_review`, `generate_pr_description`, `run_linter`, `analyze_blame`, `generate_issue`), des resources (skills, linter, prompts) et 7 prompts préconstruits. L'architecture isole le JSON-RPC via un **monkey-patching de stdout** (chaque print est redirigé vers stderr, n'exposant que le buffer réel au transport MCP) — appliqué avant tout import interne. Le mode `--tool` permet d'invoquer n'importe quel outil directement depuis la ligne de commande sans serveur persistant. Comme le SDK exécute les handlers synchrones en ligne sur l'event loop, les 12 handlers sont enveloppés dans un décorateur `_offload` (threads de travail anyio) afin que le travail bloquant (sous-processus git, téléchargements, appels IA) ne fige jamais le serveur stdio.

### **14. Écosystème TUI (Textual)**

Les interfaces visuelles vivent dans `src/ui/` et suivent des schémas communs : retour d'état via `final_action`/`final_message` (permettant des boucles de ré-authentification dans main), appels à l'IA sur des threads d'arrière-plan, modales d'aide (F1) avec URLs localisées, et le wrapper `_with_real_stdout()` qui contourne le conflit Textual×click sous Windows. Applications : `PrPublishApp` (publication de PR avec écrans de staging, commit, linter et erreur), `IssueApp`, `ChatApp`, `MetricsApp` et `LinterApp`.

### **15. Moteur d'Internationalisation (__())**

`src/i18n.py` implémente un moteur inspiré du helper `__()` de Laravel : clés en anglais dans le code, traductions en JSON (`~/.gitpr/langs/{lang}.json`) téléchargées OTA lorsque la langue change, repli vers le texte anglais lui-même et prise en charge des placeholders nommés. Langues : EN, PT-BR, PT-PT, ES, FR.

### **16. Version Markers (Ressources OTA)**

Les ressources distantes (traductions, thinking words, smart excludes, presets de linter, scripts de hooks) sont re-téléchargées en bloc lorsque les marqueurs de version (`__lang_version__`, `__scripts_version__` dans `updater.py`) changent. Les hooks installés sont comparés à `SCRIPTS_VERSION` + `SCRIPTS_LANG` dans `.env` et **auto-synchronisés silencieusement** à chaque exécution (en respectant la langue de l'utilisateur).

### **17. Système d'Auto-Update**

Construit avec l'empaquetage PyInstaller, le module `updater.py` consulte les *Releases* du dépôt sur GitHub. Si une nouvelle version existe, l'exécutable télécharge le nouveau binaire, se remplace lui-même (*hot-swap*) et relance la commande sans interruption — avec rollback automatique en cas d'échec. Vérification quotidienne en cache (`~/.gitpr/update_cache.json`) et garde de connexion (socket `8.8.8.8:53`) avant toute opération réseau.

### **18. Spinner Adaptatif**

Pendant les appels à l'IA, le `spinner.py` s'exécute sur un thread d'arrière-plan avec des caractères braille, des « mots de réflexion » découverts lettre par lettre (liste contrôlée à distance, avec cache par version) et une vitesse adaptative à la longueur de la phrase.

---

## **💻 Stack Technologique**

| Composant | Technologie |
| --- | --- |
| CLI framework | click >= 8.0.0 |
| TUI (issues, PRs, chat, dashboard) | Textual (ModalScreen, App, bindings) |
| IA (Gemini) | `google-genai` SDK |
| IA (DeepSeek / Ollama) | `openai` SDK (API compatible) |
| MCP Server | `mcp` (SDK Python officiel) |
| GitHub API | `requests` (REST, PAT via header) |
| i18n | Moteur propre `__()` inspiré de Laravel |
| Config/Build | `pyproject.toml` + setuptools >= 61 |
| Chiffrement | `cryptography.fernet` (symétrique) |
| Linter | `pyyaml` (règles) + regex |
| Tests | pytest + unittest.mock |
| Empaquetage | PyInstaller (exécutable standalone) |

---

## **🗂️ Structure du Projet**

```text
src/
├── main.py           # CLI (Click) — routage des commandes et flags
├── core.py           # Orchestration — git ops, prompts d'IA, cache, skills, hooks
├── config.py         # Configuration, .env, clés API, modèles, plugins
├── security.py       # Chiffrement Fernet (clés API au repos)
├── cache.py          # Cache local des réponses d'IA (MD5, repo+branch)
├── ai_providers.py   # Couche unifiée d'appels IA (Gemini + DeepSeek + Ollama)
├── spinner.py        # Spinner braille animé avec mots de réflexion
├── i18n.py           # Moteur d'internationalisation (__())
├── linter_engine.py  # Analyse statique avec regex (règles YAML) + linters externes
├── linter_wizard.py  # Assistant de configuration des linters externes (pont Checkstyle)
├── blame_engine.py   # Archéologie de code avec git blame + IA
├── issue_engine.py   # Génération d'issues par IA (3 moteurs de contexte)
├── chat_memory.py    # Persistance des sessions de chat (repo+branch, historique des diffs)
├── tui_issue.py      # Validation du token GitHub et point d'entrée de la TUI
├── metrics.py        # Télémétrie hors ligne (fire-and-forget, enrichissement via cache)
├── github_api.py     # Appels centralisés à l'API REST de GitHub (PRs)
├── mcp_server.py     # Serveur MCP (stdio) + tools/resources/prompts + mode --tool
├── updater.py        # Vérification de version (PyPI + GitHub), hot-swap et version markers
└── ui/               # Sous-package : composants TUI (Textual)
    ├── __init__.py       # Marqueur de package (découverte setuptools)
    ├── issue_app.py      # TUI d'édition et de publication d'Issues
    ├── pr_publish_app.py # TUI d'édition de PRs + sélection de staging + écrans de commit
    ├── chat_app.py       # TUI du chat de programmation en binôme
    ├── metrics_app.py    # Tableau de bord TUI des métriques
    ├── linter_app.py     # Affichage des violations du linter
    ├── help_screen.py    # Modale d'aide (F1) — raccourcis et instructions
    └── pr_publish_help.py # Modale d'aide de l'éditeur de PR

scripts/            # Modèles de git hooks localisés (5 langues)
templates/          # Modèles distants servis depuis GitHub (--skill)
langs/              # Fichiers de traduction (pt_br, pt_pt, es, fr)
tests/              # Tests unitaires (unittest + mock)
docs/               # Documentation technique (EN canonique + suffixes de langue)
```

---

## **📚 Documentation Détaillée**

Chaque fonctionnalité dispose d'un guide dédié dans `docs/` (anglais canonique + `.pt_br` / `.pt_pt` / `.es_es` / `.fr_fr`) :

* [pull-request-publication.md](pull-request-publication.md) — Éditeur de PR (TUI, auto-commit, merge)  
* [pr-descricao-padrao.md](pr-descricao-padrao.md) — Mode de description de PR par défaut  
* [understanding_chat_functionality.md](understanding_chat_functionality.md) — Chat de programmation en binôme  
* [mcp-integration.md](mcp-integration.md) — Intégration MCP avec les éditeurs  
* [mcp-annotations.md](mcp-annotations.md) — Annotations des tools MCP  
* [mcp-prompts.md](mcp-prompts.md) — Prompts prédéfinis du MCP  
* [metricas-telemetria.md](metricas-telemetria.md) — Métriques et télémétrie locale  
* [plugins-system.md](plugins-system.md) — Système de plugins globaux  
* [map-reduce-diff.md](map-reduce-diff.md) — Map-reduce pour les diffs géants  
* [smart-excludes.md](smart-excludes.md) — Optimisation des tokens  
* [hooks-versioning.md](hooks-versioning.md) — Versionnage et auto-sync des hooks  
* [git-hooks-locais.md](git-hooks-locais.md) — Guide des git hooks locaux  
* [linter-regras-customizadas.md](linter-regras-customizadas.md) — Règles de linter et linters externes  
* [guia-regex-gitpr.md](guia-regex-gitpr.md) — Guide regex pour les règles du linter  
* [github-ci-linter.md](github-ci-linter.md) — Intégration du linter avec la CI  
* [blame-arqueologo.md](blame-arqueologo.md) — Archéologie de code (git blame)  
* [issue-tui-help.md](issue-tui-help.md) — Issues standardisées et TUI  
* [gitpr-issue-option.md](gitpr-issue-option.md) — Options de génération d'issues  
* [commit-message-ia.md](commit-message-ia.md) — Messages de commit par IA  
* [code-review-ia.md](code-review-ia.md) — Code review par IA  
* [install-wizard.md](install-wizard.md) — Assistant de configuration  
* [i18n_explanation.md](i18n_explanation.md) — Moteur i18n  
* [github-pat-integration.md](github-pat-integration.md) — Sécurité du GitHub PAT  
* [git-status.md](git-status.md) — Liste du statut des fichiers non commités  
* [untracked-files.md](untracked-files.md) — Explication des fichiers untracked  
* [auto-update.md](auto-update.md) — Auto-updateur (hot-swap)  
* [providers-ia.md](providers-ia.md) — Fournisseurs d'IA (Gemini, DeepSeek, Ollama)  
* [skill-template.md](skill-template.md) — Système de skills et modèles  

Tutoriels (en portugais uniquement) :

* [github-issue-prompt-com-gh.md](github-issue-prompt-com-gh.md) — Formater et mettre à jour des issues via la gh CLI  
* [como_reverter_commit_git_localmente.md](como_reverter_commit_git_localmente.md) — Annuler des commits localement  
* [testar_sem_usar_pypi.md](testar_sem_usar_pypi.md) — Tester sans dépenser une version sur PyPI  
* [otimizacao-de-tokens.md](otimizacao-de-tokens.md) — Optimisation des tokens dans les fichiers de contexte (.gitpr.*.md)  

---
