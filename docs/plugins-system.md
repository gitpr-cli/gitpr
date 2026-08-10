# 🧩 GitPR Plugin System

The GitPR plugin system allows you to extend the tool's capabilities globally across **all your projects** without duplicating configuration files.

## 📂 Directory Structure

Plugins are stored in your global GitPR configuration folder:

```
~/.gitpr/plugins/
├── linter/          # Global linter rule packs (.yml / .yaml)
│   ├── security.yml
│   ├── no-debug.yml
│   └── php-psr.yml
└── prompts/         # Custom AI prompt templates (.md)
    ├── audit_security.md
    ├── generate_tests.md
    └── explain_to_business.md
```

> **Tip:** These directories are automatically created when you run any GitPR command. You can also run `gitpr --plugins` to check if they exist and list all active plugins.

---

## 🔍 Linter Plugins (`plugins/linter/`)

### What they are

Linter plugins are YAML files containing rules in the same format as `.gitpr.linter.yml`, but applied **globally** — across every project on your machine.

### Difference between Local and Global

| Aspect | Local (`.gitpr.linter.yml`) | Global (`~/.gitpr/plugins/linter/*.yml`) |
|--------|---------------------------|----------------------------------------|
| **Scope** | Project-specific | All projects on the machine |
| **Versioning** | Committed with the project | Personal — not versioned per project |
| **Use case** | Team conventions for one repo | Personal standards, security checks |

### How it works

When GitPR runs the linter (via `-l`, `-r`, `-f`, or pre-commit hooks), it:

1. Loads rules from the local `.gitpr.skill/.gitpr.linter.yml` (if it exists)
2. Iterates over all `.yml` and `.yaml` files in `~/.gitpr/plugins/linter/`
3. Merges both sets into a single rule list
4. Runs the combined rules against the diff

If a global plugin has invalid YAML, GitPR shows a **yellow warning** and continues — your workflow is never blocked by a broken plugin.

### Example: Security Pack

Create `~/.gitpr/plugins/linter/security.yml`:

```yaml
rules:
  - name: "AWS Access Key leak"
    regex: "AKIA[0-9A-Z]{16}"
    severity: error
    message: "AWS Access Key ID found — this should never be committed."

  - name: "Generic password assignment"
    regex: "(?i)(password|passwd|senha)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: warning
    message: "Hardcoded password detected. Use environment variables."
```

### Example: No-Debug Pack

Create `~/.gitpr/plugins/linter/no-debug.yml`:

```yaml
rules:
  - name: "console.log left behind"
    regex: "console\\.log\\("
    severity: error
    extensions: [".js", ".ts", ".jsx", ".tsx"]
    message: "Remove console.log() before committing."

  - name: "var_dump left behind"
    regex: "var_dump\\("
    severity: error
    extensions: [".php"]
    message: "Remove var_dump() before committing."
```

---

## 💬 Prompt Plugins (`plugins/prompts/`)

### What they are

Prompt plugins are Markdown (`.md`) files that define custom AI prompts. Each file becomes available as:

- An **MCP Resource** at `prompt://plugin/<filename>`
- An **MCP Prompt** named `Plugin: <filename>`

This allows AI-powered editors (VS Code, Cursor, Claude Desktop, Zed) to use your custom workflows.

### How it works

On MCP server startup (`gitpr --mcp`), GitPR:

1. Scans `~/.gitpr/plugins/prompts/` for `.md` files
2. Registers each one as an MCP resource and prompt
3. Lists them alongside built-in prompts in `prompt://list`

### Example: Security Auditor

Create `~/.gitpr/plugins/prompts/audit_security.md`:

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

### Example: PHPUnit Test Generator

Create `~/.gitpr/plugins/prompts/generate_tests.md`:

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

## 🖥️ CLI: Listing Active Plugins

Run `gitpr --plugins` to see all installed plugins:

```
🧩 GitPR Plugin System

🔍 Linter Packs (2):
  - security.yml
  - no-debug.yml

💬 Custom Prompts (1):
  - audit_security.md

💡 Plugin directory: ~/.gitpr/plugins/
```

Use `gitpr -h --plugins` for contextual help about the plugin system.

---

## 🔄 Execution Order and Precedence

| Layer | Priority | Override behavior |
|-------|----------|-------------------|
| Local `.gitpr.linter.yml` | Loaded first | — |
| Global `plugins/linter/*.yml` | Appended after local | Same rule name = both run (no dedup) |

Rules are **additive** — global plugins never replace local rules; they are added alongside them.

---

## 🛡️ Error Handling

- **Malformed global YAML** → Yellow warning, plugin skipped. Main flow continues.
- **Missing plugin directory** → Silently ignored. No warnings.
- **Empty plugin file** → Skipped with no message.
- **MCP server startup** → Plugin registration failures are silently caught. MCP boots normally.

---

## 📚 See Also

- [Custom Linter Rules](linter-regras-customizadas.md) — How to write `.gitpr.linter.yml` rules
- [Skills and Templates](skill-template.md) — Project-local AI prompts and rules
- [MCP Integration](https://gitpr.natanfiuza.dev.br/docs/mcp) — Using GitPR with AI editors
