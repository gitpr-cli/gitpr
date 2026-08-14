# Intégration MCP — GitPR

GitPR prend en charge le **Model Context Protocol (MCP)**, permettant l'intégration
directe avec les éditeurs et outils d'IA compatibles MCP comme **VS Code**, **Cursor**
et **Claude Desktop**.

Une fois connecté, GitPR expose ses capacités d'IA sous forme d'outils que
l'assistant IA de votre éditeur peut invoquer — sans quitter l'éditeur ni ouvrir
un terminal.

## Installation Rapide

Le moyen le plus simple de configurer MCP est d'utiliser l'installateur intégré :

```bash
# Installer pour un éditeur spécifique
gitpr-mcp --install vscode      # Crée .vscode/mcp.json
gitpr-mcp --install cursor      # Crée .cursor/mcp.json
gitpr-mcp --install claude-code # Crée .mcp.json
gitpr-mcp --install claude      # Met à jour la config de Claude Desktop
gitpr-mcp --install zed         # Met à jour la config de Zed

# Auto-détecter les éditeurs et installer pour tous ceux trouvés
gitpr-mcp --install auto
gitpr-mcp --install              # Identique à --install auto
```

L'installateur :

* Crée le répertoire de config de l'éditeur s'il n'existe pas
* Fusionne avec la config existante — ne remplace jamais les autres serveurs
* Affiche les éditeurs qui ont été configurés
* Est idempotent — peut être exécuté plusieurs fois sans risque

## Invocation Directe par CLI

Vous pouvez invoquer n'importe quel outil MCP directement depuis le terminal sans démarrer le serveur.
C'est utile pour le débogage, les scripts et les tests d'outils sans client MCP.

```bash
# Outils sans paramètres
gitpr-mcp --tool get_git_context
gitpr-mcp --tool analyze_diff
gitpr-mcp --tool run_linter

# Outils avec paramètres (JSON)
gitpr-mcp --tool analyze_blame --tool-args '{"file_path":"src/main.py","start_line":"10","end_line":"20"}'
gitpr-mcp --tool generate_commit_message --tool-args '{"provider":"gemini"}'
gitpr-mcp --tool generate_issue --tool-args '{"context_type":"history"}'

# Lister tous les outils disponibles et leurs paramètres
gitpr-mcp --tool
```

La sortie JSON va vers stdout ; tous les messages de diagnostic (spinners, bannières, logs)
vont vers stderr. La configuration `.env` est chargée automatiquement, donc les clés API
fonctionnent sans invites interactives.

> **Note :** Sur Windows Command Prompt, utilisez des guillemets doubles pour `--tool-args` et
> échappez les guillemets internes : `"{\"file_path\":\"src/main.py\",\"start_line\":\"10\"}"`.
> PowerShell et les shells Unix acceptent les guillemets simples comme montré ci-dessus.

## Outils Disponibles

| Outil | Description |
|-------|-------------|
| `get_git_context` | Branche actuelle, nom du dépôt et URL du remote |
| `analyze_diff` | Diff git des modifications non commitées (`git diff HEAD`) |
| `list_unstaged_files` | Fichiers non commités regroupés en nouveaux, modifiés ou supprimés (JSON structuré) |
| `analyze_unstaged_diff` | Uniquement les modifications non stagées (`git diff` — index vs arbre de travail) |
| `get_full_diff` | Diff complet par rapport à origin/main (`git fetch` + diff) |
| `generate_commit_message` | Message de commit au format Conventional Commits généré par IA |
| `review_code` | Revue de code IA des modifications locales (non commitées) |
| `full_review` | Revue de code IA de toutes les modifications depuis origin/main |
| `generate_pr_description` | Description complète de PR (titre + corps) |
| `run_linter` | Linter statique basé sur les règles du `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + classification IA (ORIGIN vs REFACTORING) |
| `generate_issue` | Issue structurée à partir du diff, de l'historique ou du contexte blame |

## Ressources Disponibles

| URI | Contenu |
|-----|---------|
| `skill://list` | Liste de tous les URIs de templates de skill disponibles |
| `skill://pr` | Instructions IA personnalisées pour les descriptions de PR |
| `skill://commit` | Instructions IA personnalisées pour les messages de commit |
| `skill://review` | Instructions IA personnalisées pour les revues de code |
| `skill://filereview` | Instructions IA personnalisées pour les audits de fichiers |
| `skill://issue` | Instructions IA personnalisées pour la génération d'issues |
| `skill://blame` | Instructions IA personnalisées pour l'analyse de blame |
| `linter://config` | Règles YAML du linter (`.gitpr.linter.yml`) |

### Templates de Prompt

Ces templates de prompt sont également exposés comme ressources — et comme
prompts sélectionnables dans le chat IA de votre éditeur :

| URI | Contenu |
|-----|---------|
| `prompt://list` | Liste de tous les URIs de templates de prompt disponibles |
| `prompt://review` | Revue de code complète de la branche actuelle |
| `prompt://commit` | Génération de message Conventional Commits |
| `prompt://pr` | Génération de description de Pull Request |
| `prompt://linter` | Exécution du linter statique sur les modifications |
| `prompt://issue` | Génération d'issue structurée à partir des modifications |
| `prompt://blame` | Traçage de l'origine du code avec git blame + IA |
| `prompt://explore` | Exploration du contexte du projet et des skills disponibles |

Les prompts personnalisés installés dans `~/.gitpr/plugins/` sont enregistrés
automatiquement comme `prompt://plugin/<nom>`.

Le serveur expose également ces **prompts** intégrés (messages initiaux
sélectionnables dans le chat IA de l'éditeur) : *Review PR*, *Generate Commit
Message*, *Create PR Description*, *Run Code Linter*, *Create Issue from Diff*,
*Trace Code Origin* et *Explore Project Context*.

## Configuration des Éditeurs

### VS Code

Créez `.vscode/mcp.json` à la racine de votre projet :

```json
{
  "servers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

Ou installez globalement via les paramètres de VS Code.

### Cursor

Créez `.cursor/mcp.json` à la racine de votre projet :

```json
{
  "mcpServers": {
    "gitpr": {
      "type": "stdio",
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Claude Code

Créez `.mcp.json` à la racine de votre projet :

```json
{
  "mcpServers": {
    "gitpr": {
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Claude Desktop

Ajoutez à `claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "gitpr": {
      "command": "gitpr-mcp",
      "args": []
    }
  }
}
```

### Zed

Ajoutez à `settings.json` :

```json
{
  "context_servers": {
    "gitpr": {
      "command": {
        "path": "gitpr-mcp",
        "args": []
      }
    }
  }
}
```

## Exemples d'Utilisation

Après avoir connecté GitPR via MCP, vous pouvez utiliser le langage naturel dans
le chat IA de votre éditeur :

- **"Révise mes modifications actuelles"** → appelle `review_code`
- **"Génère un message de commit pour ces modifications"** → appelle `generate_commit_message`
- **"Crée une description de PR à partir de ma branche"** → appelle `generate_pr_description`
- **"Exécute le linter sur mon diff"** → appelle `run_linter`
- **"Trace l'origine des lignes 10-20 dans src/main.py"** → appelle `analyze_blame`
- **"Génère une issue à partir de mes modifications"** → appelle `generate_issue`
- **"Sur quelle branche suis-je ?"** → appelle `get_git_context`

## Prérequis

1. **GitPR installé :** `pip install gitpr-cli` ou le binaire standalone
2. **Clés API configurées :** Exécutez `gitpr` une fois en mode interactif pour
   configurer les clés API, ou créez `~/.gitpr/.env` manuellement avec vos clés chiffrées
3. **Un éditeur compatible MCP :** VS Code, Cursor, Zed, Claude Desktop, etc.

## Fonctionnement

La commande `gitpr-mcp` démarre un serveur MCP via le **transport stdio** (entrée/sortie
standard). L'éditeur l'exécute comme un processus enfant et communique via des
messages JSON-RPC 2.0.

Pour garder le canal JSON-RPC propre, la sortie terminal de GitPR (bannières,
spinners, messages colorés) est automatiquement redirigée vers stderr lors de
l'exécution en mode MCP. Cela ne nécessite aucune configuration — tout se fait
de manière transparente.

## Dépannage

### L'éditeur ne découvre pas les outils GitPR
- Vérifiez que `gitpr-mcp` est dans votre PATH : `which gitpr-mcp` (Linux/macOS) ou `where gitpr-mcp` (Windows)
- Exécutez `pip install -e .` depuis le répertoire source de GitPR si vous développez localement
- Consultez les logs de l'éditeur pour les erreurs de connexion MCP

### Les outils retournent des erreurs
- Assurez-vous que les clés API sont configurées dans `~/.gitpr/.env`
- Consultez la sortie stderr du serveur MCP (visible dans les logs de l'éditeur)
- Exécutez `gitpr --help` normalement pour vérifier que la CLI fonctionne

### Erreur "L'invite interactive n'est pas disponible"
- Vous devez préconfigurer les clés API dans `~/.gitpr/.env` — le mode MCP ne peut pas demander interactivement
- Exécutez `gitpr` une fois dans un terminal pour terminer la configuration initiale
