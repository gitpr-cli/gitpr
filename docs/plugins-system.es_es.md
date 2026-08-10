# 🧩 Sistema de Plugins de GitPR

El sistema de plugins de GitPR te permite ampliar las capacidades de la herramienta de forma global en **todos tus proyectos** sin duplicar archivos de configuración.

## 📂 Estructura de directorios

Los plugins se almacenan en tu carpeta de configuración global de GitPR:

```
~/.gitpr/plugins/
├── linter/          # Paquetes globales de reglas de linter (.yml / .yaml)
│   ├── security.yml
│   ├── no-debug.yml
│   └── php-psr.yml
└── prompts/         # Plantillas de prompts de IA personalizadas (.md)
    ├── audit_security.md
    ├── generate_tests.md
    └── explain_to_business.md
```

> **Consejo:** Estos directorios se crean automáticamente al ejecutar cualquier comando de GitPR. También puedes ejecutar `gitpr --plugins` para comprobar si existen y listar todos los plugins activos.

---

## 🔍 Plugins de Linter (`plugins/linter/`)

### Qué son

Los plugins de linter son archivos YAML que contienen reglas en el mismo formato que `.gitpr.linter.yml`, pero aplicadas **globalmente** — en todos los proyectos de tu máquina.

### Diferencia entre Local y Global

| Aspecto | Local (`.gitpr.linter.yml`) | Global (`~/.gitpr/plugins/linter/*.yml`) |
|---------|---------------------------|----------------------------------------|
| **Alcance** | Específico del proyecto | Todos los proyectos de la máquina |
| **Versionado** | Commiteado con el proyecto | Personal — no versionado por proyecto |
| **Uso típico** | Convenciones del equipo para un repo | Estándares personales, verificaciones de seguridad |

### Cómo funciona

Cuando GitPR ejecuta el linter (mediante `-l`, `-r`, `-f` o hooks de pre-commit):

1. Carga las reglas del archivo local `.gitpr.skill/.gitpr.linter.yml` (si existe)
2. Itera sobre todos los archivos `.yml` e `.yaml` en `~/.gitpr/plugins/linter/`
3. Fusiona ambos conjuntos en una sola lista de reglas
4. Ejecuta las reglas combinadas contra el diff

Si un plugin global tiene YAML inválido, GitPR muestra un **aviso amarillo** y continúa — tu flujo de trabajo nunca se bloquea por un plugin defectuoso.

### Ejemplo: Paquete de Seguridad

Crea `~/.gitpr/plugins/linter/security.yml`:

```yaml
rules:
  - name: "Fuga de Access Key de AWS"
    regex: "AKIA[0-9A-Z]{16}"
    severity: error
    message: "Clave de acceso AWS encontrada — esto nunca debe ser commiteado."

  - name: "Contraseña hardcodeada"
    regex: "(?i)(password|passwd|senha)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: warning
    message: "Contraseña hardcodeada detectada. Usa variables de entorno."
```

### Ejemplo: Paquete Anti-Debug

Crea `~/.gitpr/plugins/linter/no-debug.yml`:

```yaml
rules:
  - name: "console.log olvidado"
    regex: "console\\.log\\("
    severity: error
    extensions: [".js", ".ts", ".jsx", ".tsx"]
    message: "Elimina console.log() antes de committear."

  - name: "var_dump olvidado"
    regex: "var_dump\\("
    severity: error
    extensions: [".php"]
    message: "Elimina var_dump() antes de committear."
```

---

## 💬 Plugins de Prompt (`plugins/prompts/`)

### Qué son

Los plugins de prompt son archivos Markdown (`.md`) que definen prompts de IA personalizados. Cada archivo está disponible como:

- Un **Recurso MCP** en `prompt://plugin/<nombredelarchivo>`
- Un **Prompt MCP** llamado `Plugin: <nombredelarchivo>`

Esto permite que los editores con IA (VS Code, Cursor, Claude Desktop, Zed) usen tus flujos de trabajo personalizados.

### Cómo funciona

Al iniciar el servidor MCP (`gitpr --mcp`), GitPR:

1. Escanea `~/.gitpr/plugins/prompts/` en busca de archivos `.md`
2. Registra cada uno como recurso y prompt MCP
3. Los lista junto con los prompts nativos en `prompt://list`

### Ejemplo: Auditor de Seguridad

Crea `~/.gitpr/plugins/prompts/audit_security.md`:

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

### Ejemplo: Generador de Tests PHPUnit

Crea `~/.gitpr/plugins/prompts/generate_tests.md`:

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

## 🖥️ CLI: Listando Plugins Activos

Ejecuta `gitpr --plugins` para ver todos los plugins instalados:

```
🧩 GitPR Plugin System

🔍 Linter Packs (2):
  - security.yml
  - no-debug.yml

💬 Custom Prompts (1):
  - audit_security.md

💡 Plugin directory: ~/.gitpr/plugins/
```

Usa `gitpr -h --plugins` para ayuda contextual sobre el sistema de plugins.

---

## 🔄 Orden de Ejecución y Precedencia

| Capa | Prioridad | Comportamiento |
|------|-----------|----------------|
| Local `.gitpr.linter.yml` | Cargado primero | — |
| Global `plugins/linter/*.yml` | Agregado después | Misma regla = ambas se ejecutan (sin dedup) |

Las reglas son **aditivas** — los plugins globales nunca reemplazan las reglas locales; se añaden junto a ellas.

---

## 🛡️ Manejo de Errores

- **YAML global con errores** → Aviso amarillo, plugin omitido. El flujo principal continúa.
- **Directorio de plugin ausente** → Ignorado silenciosamente. Sin avisos.
- **Archivo de plugin vacío** → Omitido sin mensaje.
- **Inicio del servidor MCP** → Los fallos de registro de plugins se capturan silenciosamente. MCP arranca normalmente.

---

## 📚 Ver También

- [Reglas de Linter Personalizadas](linter-regras-customizadas.md) — Cómo escribir reglas `.gitpr.linter.yml`
- [Sistema de Skills y Templates](skill-template.md) — Prompts y reglas de IA locales del proyecto
- [Integración MCP](https://gitpr.natanfiuza.dev.br/docs/mcp) — Usando GitPR con editores de IA
