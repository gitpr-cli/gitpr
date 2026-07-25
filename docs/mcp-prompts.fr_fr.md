# MCP Prompts — Modèles de Message pour les Flux Courants

Le serveur MCP de GitPR expose des **prompts** (modèles de message prédéfinis) qui
vous aident à composer des tâches courantes de GitPR dans le chat IA de votre éditeur. Au lieu de taper
des instructions complètes à chaque fois, sélectionnez un prompt et laissez l'IA remplir les détails.

## Que Sont les MCP Prompts?

Dans le Model Context Protocol, les **prompts** sont des modèles de message définis par le serveur.
Contrairement aux outils (qui exécutent du code automatiquement), les prompts sont des **messages de départ**
que l'utilisateur peut sélectionner dans une liste dans son éditeur. L'IA utilise ensuite le
modèle pour invoquer les outils GitPR appropriés afin de répondre à la demande.

## Prompts Disponibles

| Prompt | Ce qu'il fait | Outils utilisés |
|--------|---------------|-----------------|
| **Review PR** | Révision complète du code de toutes les modifications dans la branche actuelle | `full_review` |
| **Generate Commit Message** | Génère un message au format Conventional Commits à partir des modifications non commitées | `generate_commit_message` |
| **Create PR Description** | Génère un titre et un corps pour un Pull Request | `generate_pr_description` |
| **Run Code Linter** | Vérifie les modifications non commitées par rapport aux règles de `.gitpr.linter.yml` | `run_linter` |
| **Create Issue from Diff** | Génère une issue structurée à partir des modifications actuelles | `generate_issue` |
| **Trace Code Origin** | Enquête sur l'historique d'une région spécifique du code | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Obtient les informations de la branche actuelle et liste les skills/templates disponibles | `get_git_context`, `skill://list` |

## Comment Utiliser

Une fois le serveur MCP configuré dans votre éditeur, les prompts apparaissent dans la liste
des prompts aux côtés des autres prompts des serveurs MCP. L'emplacement exact varie selon l'éditeur :

- **VS Code / Cursor :** Dans le panneau de chat IA, recherchez le sélecteur "Prompts"
- **Claude Desktop :** Les prompts apparaissent comme des options sélectionnables dans l'interface de chat
- **Claude Code :** Utilisez la liste des prompts dans le panneau de chat
- **Zed :** Disponible dans la liste des prompts de l'assistant inline

Sélectionnez un prompt et l'IA invoquera automatiquement les outils GitPR appropriés
pour répondre à la demande.

## Comment ça Fonctionne

Chaque prompt est défini comme une fonction décorée avec `@mcp.prompt()` dans
`src/mcp_server.py`. La fonction retourne une chaîne de message que l'agent IA de l'éditeur
envoie au modèle, lui demandant d'appeler des outils GitPR spécifiques avec les
paramètres appropriés.

Exemple — le prompt "Review PR" :

```python
@mcp.prompt()
def review_pr_prompt() -> str:
    return (
        "Review all changes in my current branch. "
        "Run a full review against origin/main, "
        "check the linter, and suggest improvements."
    )
```

L'agent IA qui reçoit ce message appellera alors `full_review`, `run_linter`,
et composera une réponse de révision complète basée sur les résultats.

## Documentation Connexe

- [Intégration MCP](mcp-integration.md) — Comment configurer MCP pour votre éditeur
- [Code Review avec IA](code-review-ia.md) — Guide des modes de révision de code
- [Messages de Commit avec IA](commit-message-ia.md) — Guide des Conventional Commits
- [Mode de Description de PR](pr-descricao-padrao.md) — Flux de génération de PR

---
**Conseil pratique :** Combinez les prompts avec des skills (fichiers `.gitpr.*.md`) pour personnaliser
le comportement de l'IA selon les conventions de votre équipe. Exécutez `gitpr --install` pour tout
configurer en une seule fois.
