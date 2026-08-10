# 🧩 Sistema de Plugins do GitPR

O sistema de plugins do GitPR permite-lhe estender as capacidades da ferramenta globalmente em **todos os seus projetos** sem duplicar ficheiros de configuração.

## 📂 Estrutura de Diretórios

Os plugins são armazenados na pasta global de configuração do GitPR:

```
~/.gitpr/plugins/
├── linter/          # Pacotes globais de regras de linter (.yml / .yaml)
│   ├── security.yml
│   ├── no-debug.yml
│   └── php-psr.yml
└── prompts/         # Modelos de prompts de IA personalizados (.md)
    ├── audit_security.md
    ├── generate_tests.md
    └── explain_to_business.md
```

> **Dica:** Estes diretórios são criados automaticamente quando executa qualquer comando do GitPR. Também pode executar `gitpr --plugins` para verificar se existem e listar todos os plugins ativos.

---

## 🔍 Plugins de Linter (`plugins/linter/`)

### O que são

Plugins de linter são ficheiros YAML contendo regras no mesmo formato do `.gitpr.linter.yml`, mas aplicadas **globalmente** — em todos os projetos da sua máquina.

### Diferença entre Local e Global

| Aspeto | Local (`.gitpr.linter.yml`) | Global (`~/.gitpr/plugins/linter/*.yml`) |
|--------|---------------------------|----------------------------------------|
| **Âmbito** | Específico do projeto | Todos os projetos na máquina |
| **Versionamento** | Commitado com o projeto | Pessoal — não versionado por projeto |
| **Uso típico** | Convenções da equipa para um repo | Padrões pessoais, verificações de segurança |

### Como funciona

Quando o GitPR executa o linter (via `-l`, `-r`, `-f` ou hooks de pre-commit), ele:

1. Carrega as regras do ficheiro local `.gitpr.skill/.gitpr.linter.yml` (se existir)
2. Itera sobre todos os ficheiros `.yml` e `.yaml` em `~/.gitpr/plugins/linter/`
3. Une ambos os conjuntos numa única lista de regras
4. Executa as regras combinadas contra o diff

Se um plugin global tiver YAML inválido, o GitPR mostra um **aviso amarelo** e continua — o seu fluxo nunca é bloqueado por um plugin corrompido.

### Exemplo: Pacote de Segurança

Crie `~/.gitpr/plugins/linter/security.yml`:

```yaml
rules:
  - name: "Fuga de Access Key da AWS"
    regex: "AKIA[0-9A-Z]{16}"
    severity: error
    message: "Chave de acesso AWS encontrada — isto nunca deve ser commitado."

  - name: "Password hardcoded"
    regex: "(?i)(password|passwd|senha)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: warning
    message: "Password hardcoded detetada. Utilize variáveis de ambiente."
```

### Exemplo: Pacote Anti-Debug

Crie `~/.gitpr/plugins/linter/no-debug.yml`:

```yaml
rules:
  - name: "console.log esquecido"
    regex: "console\\.log\\("
    severity: error
    extensions: [".js", ".ts", ".jsx", ".tsx"]
    message: "Remova console.log() antes de commitar."

  - name: "var_dump esquecido"
    regex: "var_dump\\("
    severity: error
    extensions: [".php"]
    message: "Remova var_dump() antes de commitar."
```

---

## 💬 Plugins de Prompt (`plugins/prompts/`)

### O que são

Plugins de prompt são ficheiros Markdown (`.md`) que definem prompts de IA personalizados. Cada ficheiro fica disponível como:

- Um **Recurso MCP** em `prompt://plugin/<nomedoficheiro>`
- Um **Prompt MCP** chamado `Plugin: <nomedoficheiro>`

Isto permite que editores com IA (VS Code, Cursor, Claude Desktop, Zed) utilizem os seus fluxos de trabalho personalizados.

### Como funciona

No arranque do servidor MCP (`gitpr --mcp`), o GitPR:

1. Examina `~/.gitpr/plugins/prompts/` em busca de ficheiros `.md`
2. Regista cada um como recurso e prompt MCP
3. Lista-os juntamente com os prompts nativos em `prompt://list`

### Exemplo: Auditor de Segurança

Crie `~/.gitpr/plugins/prompts/audit_security.md`:

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

### Exemplo: Gerador de Testes PHPUnit

Crie `~/.gitpr/plugins/prompts/generate_tests.md`:

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

## 🖥️ CLI: Listando Plugins Ativos

Execute `gitpr --plugins` para ver todos os plugins instalados:

```
🧩 GitPR Plugin System

🔍 Linter Packs (2):
  - security.yml
  - no-debug.yml

💬 Custom Prompts (1):
  - audit_security.md

💡 Plugin directory: ~/.gitpr/plugins/
```

Utilize `gitpr -h --plugins` para ajuda contextual sobre o sistema de plugins.

---

## 🔄 Ordem de Execução e Precedência

| Camada | Prioridade | Comportamento |
|--------|-----------|---------------|
| Local `.gitpr.linter.yml` | Carregado primeiro | — |
| Global `plugins/linter/*.yml` | Adicionado depois | Mesma regra = ambas executam (sem dedup) |

As regras são **aditivas** — plugins globais nunca substituem regras locais; são adicionadas juntamente com elas.

---

## 🛡️ Tratamento de Erros

- **YAML global mal formatado** → Aviso amarelo, plugin ignorado. Fluxo principal continua.
- **Diretório de plugin ausente** → Ignorado silenciosamente. Sem avisos.
- **Ficheiro de plugin vazio** → Ignorado sem mensagem.
- **Arranque do servidor MCP** → Falhas no registo de plugins são capturadas silenciosamente. MCP inicia normalmente.

---

## 📚 Veja Também

- [Regras de Linter Personalizadas](linter-regras-customizadas.md) — Como escrever regras `.gitpr.linter.yml`
- [Sistema de Skills e Templates](skill-template.md) — Prompts e regras de IA locais do projeto
- [Integração MCP](https://gitpr.natanfiuza.dev.br/docs/mcp) — Usando GitPR com editores de IA
