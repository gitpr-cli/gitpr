# 🧩 Sistema de Plugins do GitPR

O sistema de plugins do GitPR permite que você estenda as capacidades da ferramenta globalmente em **todos os seus projetos** sem duplicar arquivos de configuração.

## 📂 Estrutura de Diretórios

Os plugins são armazenados na pasta global de configuração do GitPR:

```
~/.gitpr/plugins/
├── linter/          # Pacotes globais de regras de linter (.yml / .yaml)
│   ├── security.yml
│   ├── no-debug.yml
│   └── php-psr.yml
└── prompts/         # Templates de prompts de IA customizados (.md)
    ├── audit_security.md
    ├── generate_tests.md
    └── explain_to_business.md
```

> **Dica:** Estes diretórios são criados automaticamente quando você executa qualquer comando do GitPR. Execute `gitpr --plugins` para verificar se existem e listar todos os plugins ativos.

---

## 🔍 Plugins de Linter (`plugins/linter/`)

### O que são

Plugins de linter são arquivos YAML contendo regras no mesmo formato do `.gitpr.linter.yml`, mas aplicadas **globalmente** — em todos os projetos da sua máquina.

### Diferença entre Local e Global

| Aspecto | Local (`.gitpr.linter.yml`) | Global (`~/.gitpr/plugins/linter/*.yml`) |
|---------|---------------------------|----------------------------------------|
| **Escopo** | Específico do projeto | Todos os projetos na máquina |
| **Versionamento** | Commitado com o projeto | Pessoal — não versionado por projeto |
| **Uso típico** | Convenções da equipe para um repo | Padrões pessoais, verificações de segurança |

### Como funciona

Quando o GitPR executa o linter (via `-l`, `-r`, `-f` ou hooks de pre-commit), ele:

1. Carrega as regras do arquivo local `.gitpr.skill/.gitpr.linter.yml` (se existir)
2. Itera sobre todos os arquivos `.yml` e `.yaml` em `~/.gitpr/plugins/linter/`
3. Une ambos os conjuntos em uma única lista de regras
4. Executa as regras combinadas contra o diff

Se um plugin global tiver YAML inválido, o GitPR mostra um **aviso amarelo** e continua — seu fluxo nunca é bloqueado por um plugin quebrado.

### Exemplo: Pacote de Segurança

Crie `~/.gitpr/plugins/linter/security.yml`:

```yaml
rules:
  - name: "Vazamento de Access Key da AWS"
    regex: "AKIA[0-9A-Z]{16}"
    severity: error
    message: "Chave de acesso AWS encontrada — isto nunca deve ser commitado."

  - name: "Senha hardcoded"
    regex: "(?i)(password|passwd|senha)\\s*=\\s*['\"][^'\"]+['\"]"
    severity: warning
    message: "Senha hardcoded detectada. Use variáveis de ambiente."
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

Plugins de prompt são arquivos Markdown (`.md`) que definem prompts de IA personalizados. Cada arquivo fica disponível como:

- Um **Recurso MCP** em `prompt://plugin/<nomedoarquivo>`
- Um **Prompt MCP** chamado `Plugin: <nomedoarquivo>`

Isso permite que editores com IA (VS Code, Cursor, Claude Desktop, Zed) usem seus fluxos de trabalho customizados.

### Como funciona

Na inicialização do servidor MCP (`gitpr --mcp`), o GitPR:

1. Escaneia `~/.gitpr/plugins/prompts/` em busca de arquivos `.md`
2. Registra cada um como um recurso e prompt MCP
3. Lista-os junto com os prompts nativos em `prompt://list`

### Exemplo: Auditor de Segurança

Crie `~/.gitpr/plugins/prompts/audit_security.md`:

```markdown
Você é um Engenheiro de Segurança Sênior. Realize uma revisão completa de segurança do diff atual.

Foque em:
1. **Vulnerabilidades de injeção** (SQL, NoSQL, Comando, XPath)
2. **Vetores de XSS / Cross-Site Scripting**
3. **Exposição de dados sensíveis** (chaves, tokens, PII em logs)
4. **Falhas de Autenticação / Autorização**
5. **Desserialização insegura**
6. **Riscos de path traversal**

Para cada achado, forneça:
- **Severidade**: Crítico / Alto / Médio / Baixo
- **Arquivo e Linha**: Onde está o problema
- **Descrição**: Qual é a vulnerabilidade
- **Correção**: Sugestão concreta de código
```

### Exemplo: Gerador de Testes PHPUnit

Crie `~/.gitpr/plugins/prompts/generate_tests.md`:

```markdown
Você é um Desenvolvedor PHP Sênior especializado em TDD.

Para as alterações neste diff, gere testes PHPUnit abrangentes seguindo:

1. **Cobertura de 100%** — cubra todos os métodos novos/alterados
2. **Siga PSR-12** para padrões de código
3. **Use data providers** para múltiplos cenários de entrada
4. **Mock de dependências externas** (APIs, bancos, sistemas de arquivos)
5. **Teste casos limite**: null, vazio, valores de fronteira, exceções
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

Use `gitpr -h --plugins` para ajuda contextual sobre o sistema de plugins.

---

## 🔄 Ordem de Execução e Precedência

| Camada | Prioridade | Comportamento |
|--------|-----------|---------------|
| Local `.gitpr.linter.yml` | Carregado primeiro | — |
| Global `plugins/linter/*.yml` | Adicionado depois | Mesma regra = ambas executam (sem dedup) |

As regras são **aditivas** — plugins globais nunca substituem regras locais; são adicionados junto com elas.

---

## 🛡️ Tratamento de Erros

- **YAML global mal formatado** → Aviso amarelo, plugin ignorado. Fluxo principal continua.
- **Diretório de plugin ausente** → Ignorado silenciosamente. Sem avisos.
- **Arquivo de plugin vazio** → Ignorado sem mensagem.
- **Inicialização do servidor MCP** → Falhas no registro de plugins são capturadas silenciosamente. MCP inicia normalmente.

---

## 📚 Veja Também

- [Regras de Linter Customizadas](linter-regras-customizadas.md) — Como escrever regras `.gitpr.linter.yml`
- [Sistema de Skills e Templates](skill-template.md) — Prompts e regras de IA locais do projeto
- [Integração MCP](https://gitpr.natanfiuza.dev.br/docs/mcp) — Usando GitPR com editores de IA
