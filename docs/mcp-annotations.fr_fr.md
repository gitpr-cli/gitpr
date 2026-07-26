# Annotations des Outils MCP — Conseils pour l'Intégration avec les IDEs

Les outils MCP de GitPR incluent des **annotations** (`readOnlyHint`, `destructiveHint`,
`idempotentHint`) qui aident les IDEs et les agents IA à comprendre rapidement le
comportement de l'outil. Ces annotations permettent des décisions d'interface plus
intelligentes — comme afficher des dialogues de confirmation pour les opérations
destructives ou mettre en cache les résultats des appels idempotents.

## ✨ Que Sont les Annotations d'Outils ?

Dans le Model Context Protocol, chaque outil peut déclarer des **conseils**
comportementaux via un objet `ToolAnnotations`. Ces conseils ne sont pas imposés
par le serveur — ce sont des métadonnées consultatives que l'IDE/client peut
utiliser pour améliorer l'expérience utilisateur.

Les champs d'annotation standard sont :

| Champ | Type | Signification |
|-------|------|---------------|
| `readOnlyHint` | `bool` | Si `true`, l'outil **ne** modifie **pas** son environnement |
| `destructiveHint` | `bool` | Si `true`, l'outil peut effectuer des mises à jour destructives (pertinent uniquement lorsque `readOnlyHint` est `false`) |
| `idempotentHint` | `bool` | Si `true`, appeler l'outil de manière répétée avec les mêmes arguments n'a pas d'effets secondaires supplémentaires |

## 📋 Annotations des Outils GitPR

### Outils en Lecture Seule (sans effets secondaires)

Ces outils lisent uniquement l'état local — sûrs à appeler à tout moment, sans
confirmation nécessaire :

| Outil | `readOnlyHint` | `idempotentHint` |
|------|:---:|:---:|
| `get_git_context` | ✅ | ✅ |
| `analyze_diff` | ✅ | ✅ |
| `run_linter` | ✅ | ✅ |

### Outils avec Effets Secondaires (appels réseau)

Ces outils effectuent des appels réseau (APIs IA, git fetch) mais **n'écrivent
ni ne suppriment** de fichiers. Ils peuvent être invoqués sans avertissement
d'opération destructive :

| Outil | `readOnlyHint` | `destructiveHint` | `idempotentHint` |
|------|:---:|:---:|:---:|
| `get_full_diff` | ❌ | ❌ | ❌ |
| `generate_commit_message` | ❌ | ❌ | ❌ |
| `review_code` | ❌ | ❌ | ❌ |
| `full_review` | ❌ | ❌ | ❌ |
| `generate_pr_description` | ❌ | ❌ | ❌ |
| `analyze_blame` | ❌ | ❌ | ❌ |
| `generate_issue` | ❌ | ❌ | ❌ |

> **Note :** `destructiveHint` est `false` pour tous les outils GitPR car aucun
> d'entre eux ne modifie, supprime ou écrase des fichiers. Les « effets
> secondaires » se limitent aux appels API réseau.

## 🚀 Avantages pour l'Intégration avec les IDEs

Les annotations permettent aux éditeurs de :

- **VS Code / Cursor :** Afficher une icône de bouclier pour les outils en
  lecture seule, avertir avant d'exécuter des outils marqués `destructiveHint=true`
- **Claude Desktop :** Organiser les outils en groupes sûr/dangereux dans l'interface
- **Claude Code :** Mettre en cache les résultats des outils idempotents pour
  éviter les appels redondants
- **Zed :** Afficher le niveau de sécurité de l'outil dans l'assistant inline

## 🔧 Implémentation

Les annotations sont définies via la classe `ToolAnnotations` dans `src/mcp_server.py` :

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    description=__("Obtient la branche git actuelle, le nom du dépôt et l'URL du remote origin."),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def get_git_context() -> str:
    ...
```

L'annotation de chaque outil est choisie en fonction de son comportement réel :
- **Lecture seule + idempotent** pour les outils qui inspectent uniquement l'état local
- **Non lecture seule + non destructif** pour les outils qui effectuent des appels réseau
- Aucun outil n'est marqué `destructiveHint=true` car GitPR n'écrit jamais de fichiers

## 📚 Documentation Connexe

- [Intégration MCP](mcp-integration.md) — Comment configurer MCP pour votre éditeur
- [MCP Prompts](mcp-prompts.md) — Modèles de message prédéfinis pour les flux courants

---
**Conseil de pro :** Les annotations d'outils sont des conseils, pas des garanties.
Configurez les clés API dans `~/.gitpr/.env` avant d'utiliser un outil. Exécutez
`gitpr --install` pour tout configurer en une seule fois.
