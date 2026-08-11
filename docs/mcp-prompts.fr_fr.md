# MCP Prompts — Modèles de Message pour les Flux Courants

Le serveur MCP de GitPR expose des **prompts** (modèles de message prédéfinis) qui
vous aident à composer des tâches GitPR courantes dans le chat IA de votre éditeur.
Au lieu de taper des instructions complètes à chaque fois, sélectionnez un prompt
et laissez l'IA remplir les détails.

## ✨ Que Sont les MCP Prompts ?

Dans le Model Context Protocol, les **prompts** sont des modèles de message définis
par le serveur. Contrairement aux outils (qui exécutent du code automatiquement),
les prompts sont des **messages de démarrage** que l'utilisateur peut sélectionner
dans une liste de son éditeur. L'IA utilise ensuite le modèle pour invoquer les
outils GitPR appropriés afin de répondre à la demande.

## 📋 Prompts Disponibles

| Prompt | Ce qu'il fait | Outils utilisés |
|--------|---------------|-----------------|
| **Review PR** | Revue de code complète de tous les changements de la branche actuelle | `full_review` |
| **Generate Commit Message** | Génère un message Conventional Commits à partir des modifications non validées | `generate_commit_message` |
| **Create PR Description** | Génère un titre et un corps pour une Pull Request | `generate_pr_description` |
| **Run Code Linter** | Vérifie les modifications non validées par rapport aux règles `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Génère une issue structurée à partir des modifications actuelles | `generate_issue` |
| **Trace Code Origin** | Enquête sur l'historique d'une région spécifique du code | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtient les informations de la branche actuelle et liste les skills/modèles disponibles | `get_git_context`, `skill://list` |

## 🚀 Comment Utiliser

Une fois le serveur MCP configuré dans votre éditeur, les prompts apparaissent dans
la liste des prompts aux côtés des autres prompts de serveurs MCP. L'emplacement
exact varie selon l'éditeur :

- **VS Code / Cursor :** Dans le panneau de chat IA, cherchez le sélecteur "Prompts"
- **Claude Desktop :** Les prompts apparaissent comme des options sélectionnables dans l'interface de chat
- **Claude Code :** Utilisez la liste de prompts dans le panneau de chat
- **Zed :** Disponible dans la liste de prompts de l'assistant inline

Sélectionnez un prompt et l'IA invoquera automatiquement les outils GitPR appropriés
pour répondre à la demande.

## 🔧 Comment Ça Fonctionne

Chaque prompt est défini comme une fonction décorée avec `@mcp.prompt()` dans
`src/mcp_server.py`. Le contenu du prompt est chargé depuis des **fichiers modèles**
stockés dans le répertoire `templates/` :

```
templates/gitpr.prompt.review.md       (Anglais)
templates/gitpr.prompt.review.pt_br.md  (Portugais Brésilien)
templates/gitpr.prompt.review.pt_pt.md  (Portugais Européen)
templates/gitpr.prompt.review.es_es.md  (Espagnol)
templates/gitpr.prompt.review.fr_fr.md  (Français)
```

Cette conception basée sur des modèles signifie que les messages des prompts peuvent
être mis à jour et traduits indépendamment du code Python. Le serveur MCP charge la
variante linguistique appropriée en fonction du paramètre `GITPR_LANG` de
l'utilisateur, avec repli vers l'anglais.

Exemple — le modèle du prompt "Review PR" (`gitpr.prompt.review.fr_fr.md`) :

```
Veuillez examiner toutes les modifications de ma branche actuelle en effectuant
une révision complète du code par rapport à origin/main. Exécutez également le
linter statique pour vérifier les problèmes de qualité du code. Combinez les
résultats en un seul rapport complet avec : 1) résumé des modifications,
2) problèmes critiques trouvés, 3) violations du linter, et 4) améliorations
suggérées.
```

L'agent IA recevant ce message appellera alors `full_review`, `run_linter`,
et composera une réponse de révision complète basée sur les résultats.

### Ressources de Prompt

Les modèles de prompt sont également exposés en tant que **ressources** MCP sous
le schéma URI `prompt://`, afin que les agents IA puissent lire le contenu brut
du modèle :

| URI | Contenu |
|-----|---------|
| `prompt://list` | Liste JSON de toutes les URIs de prompt disponibles |
| `prompt://review` | Modèle du prompt de révision de PR |
| `prompt://commit` | Modèle du prompt de message de commit |
| `prompt://pr` | Modèle du prompt de description de PR |
| `prompt://linter` | Modèle du prompt du linter |
| `prompt://issue` | Modèle du prompt d'issue |
| `prompt://blame` | Modèle du prompt d'origine de code |
| `prompt://explore` | Modèle du prompt de contexte du projet |

## 🔧 Équivalents par CLI

Alors que les prompts MCP sont des modèles de messages pour le chat IA de l'éditeur,
vous pouvez obtenir les mêmes résultats depuis le terminal en utilisant `--tool` :

| Prompt | Équivalent CLI |
| ------ | -------------- |
| Réviser la PR | `gitpr-mcp --tool full_review` |
| Générer un message de commit | `gitpr-mcp --tool generate_commit_message` |
| Créer une description de PR | `gitpr-mcp --tool generate_pr_description` |
| Exécuter le linter | `gitpr-mcp --tool run_linter` |
| Créer une issue depuis le diff | `gitpr-mcp --tool generate_issue` |
| Tracer l'origine du code | `gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"...","start_line":"...","end_line":"..."}'` |
| Explorer le contexte du projet | `gitpr-mcp --tool get_git_context` |

> **Note :** `--tool` invoque uniquement des outils — les prompts (modèles de messages)
> ne sont pas exécutables. Utilisez `gitpr-mcp --list` pour voir toutes les ressources
> et prompts, puis exécutez l'outil sous-jacent avec `--tool`. Voir
> [Intégration MCP — Invocation Directe par CLI](mcp-integration.md#invocation-directe-par-cli)
> pour les détails.

## 📚 Documentation Connexe

- [Intégration MCP](mcp-integration.md) — Comment configurer MCP pour votre éditeur
- [Revue de Code avec IA](code-review-ia.md) — Guide des modes de revue de code
- [Messages de Commit avec IA](commit-message-ia.md) — Guide des Conventional Commits
- [Mode Description de PR](pr-descricao-padrao.md) — Flux de génération de PR

---
**Conseil de pro :** Combinez les prompts avec les skills (fichiers `.gitpr.*.md`)
pour personnaliser le comportement de l'IA selon les conventions de votre équipe.
Exécutez `gitpr --install` pour tout configurer en une seule fois.
