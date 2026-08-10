# 🧩 Système de Plugins GitPR

Le système de plugins GitPR vous permet d'étendre les capacités de l'outil globalement sur **tous vos projets** sans dupliquer les fichiers de configuration.

## 📂 Structure des répertoires

Les plugins sont stockés dans votre dossier de configuration global GitPR :

```
~/.gitpr/plugins/
├── linter/          # Packs globaux de règles de linter (.yml / .yaml)
│   ├── security.yml
│   ├── no-debug.yml
│   └── php-psr.yml
└── prompts/         # Modèles de prompts IA personnalisés (.md)
    ├── audit_security.md
    ├── generate_tests.md
    └── explain_to_business.md
```

> **Astuce :** Ces répertoires sont créés automatiquement lorsque vous exécutez n'importe quelle commande GitPR. Vous pouvez également exécuter `gitpr --plugins` pour vérifier leur existence et lister tous les plugins actifs.

---

## 🔍 Plugins de Linter (`plugins/linter/`)

### Ce qu'ils sont

Les plugins de linter sont des fichiers YAML contenant des règles au même format que `.gitpr.linter.yml`, mais appliquées **globalement** — sur tous les projets de votre machine.

### Différence entre Local et Global

| Aspect | Local (`.gitpr.linter.yml`) | Global (`~/.gitpr/plugins/linter/*.yml`) |
|--------|---------------------------|----------------------------------------|
| **Portée** | Spécifique au projet | Tous les projets de la machine |
| **Versionnage** | Commit avec le projet | Personnel — non versionné par projet |
| **Cas d'usage** | Conventions d'équipe pour un dépôt | Standards personnels, contrôles de sécurité |

### Comment ça fonctionne

Lorsque GitPR exécute le linter (via `-l`, `-r`, `-f` ou les hooks de pre-commit), il :

1. Charge les règles du fichier local `.gitpr.skill/.gitpr.linter.yml` (s'il existe)
2. Parcourt tous les fichiers `.yml` et `.yaml` dans `~/.gitpr/plugins/linter/`
3. Fusionne les deux ensembles en une seule liste de règles
4. Exécute les règles combinées sur le diff

Si un plugin global a un YAML invalide, GitPR affiche un **avertissement jaune** et continue — votre flux n'est jamais bloqué par un plugin défectueux.

### Exemple : Pack Sécurité

Créez `~/.gitpr/plugins/linter/security.yml` :

```yaml
rules:
  - name: "Fuite de clé d'accès AWS"
    regex: "AKIA[0-9A-Z]{16}"
    severity: error
    message: "Clé d'accès AWS trouvée — ceci ne doit jamais être commité."

  - name: "Mot de passe en dur"
    regex: "(?i)(password|passwd|senha)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: warning
    message: "Mot de passe en dur détecté. Utilisez des variables d'environnement."
```

### Exemple : Pack Anti-Debug

Créez `~/.gitpr/plugins/linter/no-debug.yml` :

```yaml
rules:
  - name: "console.log oublié"
    regex: "console\\.log\\("
    severity: error
    extensions: [".js", ".ts", ".jsx", ".tsx"]
    message: "Supprimez console.log() avant de commiter."

  - name: "var_dump oublié"
    regex: "var_dump\\("
    severity: error
    extensions: [".php"]
    message: "Supprimez var_dump() avant de commiter."
```

---

## 💬 Plugins de Prompt (`plugins/prompts/`)

### Ce qu'ils sont

Les plugins de prompt sont des fichiers Markdown (`.md`) qui définissent des prompts IA personnalisés. Chaque fichier devient disponible en tant que :

- **Ressource MCP** à l'URI `prompt://plugin/<nomdufichier>`
- **Prompt MCP** nommé `Plugin: <nomdufichier>`

Cela permet aux éditeurs dotés d'IA (VS Code, Cursor, Claude Desktop, Zed) d'utiliser vos flux de travail personnalisés.

### Comment ça fonctionne

Au démarrage du serveur MCP (`gitpr --mcp`), GitPR :

1. Analyse `~/.gitpr/plugins/prompts/` à la recherche de fichiers `.md`
2. Enregistre chacun comme ressource et prompt MCP
3. Les liste avec les prompts natifs dans `prompt://list`

### Exemple : Auditeur de Sécurité

Créez `~/.gitpr/plugins/prompts/audit_security.md` :

```markdown
You are a Senior Security Engineer. Perform a thorough security review of the current diff.

Focus on:
1. **Injection vulnerabilities** (SQL, NoSQL, Command, XPath)
2. **XSS / Cross-Site Scripting** vectors
3. **Sensitive data exposure** (keys, tokens, PII in logs)
4. **Authentication / Authorization** flaws
5. **Insecure deserialization**
6. **Path traversal** risks

For each finding, provide:
- **Severity**: Critical / High / Medium / Low
- **File & Line**: Where the issue is
- **Description**: What the vulnerability is
- **Fix**: Concrete code suggestion

Use the format:
### [Severity] Vulnerability Name
- **File**: path/to/file:line
- **Description**: ...
- **Fix**: ...
```

### Exemple : Générateur de Tests PHPUnit

Créez `~/.gitpr/plugins/prompts/generate_tests.md` :

```markdown
You are a Senior PHP Developer specialized in Test-Driven Development.

For the code changes in this diff, generate comprehensive PHPUnit tests following these rules:

1. **100% coverage target** — cover all new/changed methods
2. **Follow PSR-12** coding standards
3. **Use data providers** for multiple input scenarios
4. **Mock external dependencies** (APIs, databases, file systems)
5. **Test edge cases**: null, empty, boundary values, exceptions

Output a ready-to-run PHPUnit test class with:
- Class name matching the source + "Test" suffix
- setUp() for shared fixtures
- test methods prefixed with "test"
- @test, @dataProvider, and @covers annotations
```

---

## 🖥️ CLI : Lister les Plugins Actifs

Exécutez `gitpr --plugins` pour voir tous les plugins installés :

```
🧩 GitPR Plugin System

🔍 Linter Packs (2):
  - security.yml
  - no-debug.yml

💬 Custom Prompts (1):
  - audit_security.md

💡 Plugin directory: ~/.gitpr/plugins/
```

Utilisez `gitpr -h --plugins` pour obtenir de l'aide contextuelle sur le système de plugins.

---

## 🔄 Ordre d'Exécution et Priorité

| Couche | Priorité | Comportement |
|--------|----------|--------------|
| Local `.gitpr.linter.yml` | Chargé en premier | — |
| Global `plugins/linter/*.yml` | Ajouté ensuite | Même règle = les deux s'exécutent (pas de dédoublonnage) |

Les règles sont **additives** — les plugins globaux ne remplacent jamais les règles locales ; ils sont ajoutés à celles-ci.

---

## 🛡️ Gestion des Erreurs

- **YAML global mal formaté** → Avertissement jaune, plugin ignoré. Le flux principal continue.
- **Répertoire de plugin absent** → Ignoré silencieusement. Aucun avertissement.
- **Fichier de plugin vide** → Ignoré sans message.
- **Démarrage du serveur MCP** → Les échecs d'enregistrement des plugins sont capturés silencieusement. MCP démarre normalement.

---

## 📚 Voir Aussi

- [Règles de Linter Personnalisées](linter-regras-customizadas.md) — Comment écrire des règles `.gitpr.linter.yml`
- [Système de Skills et Templates](skill-template.md) — Prompts et règles IA locaux du projet
- [Intégration MCP](https://gitpr.natanfiuza.dev.br/docs/mcp) — Utiliser GitPR avec des éditeurs IA
