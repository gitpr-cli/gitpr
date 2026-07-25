# Assistente de Configuração Interativo do GitPR (`--install`)

O comando `gitpr --install` executa um assistente guiado interativo que prepara o ambiente do teu projeto com todas as configurações essenciais do GitPR num único fluxo. Consolida vários passos de configuração manual numa experiência única e contínua.

## ✨ O Que Faz

O assistente guia-te por **4 etapas**, pedindo confirmação antes de cada uma:

| Etapa | O que configura | Comando equivalente |
|-------|----------------|---------------------|
| 1. Skill Templates | Descarrega ficheiros template `.gitpr.*.md` e `.gitpr.linter.yml` | `gitpr --skill` |
| 2. Git Hooks | Instala hooks `pre-commit` e `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 3. Configuração MCP | Auto-deteta e configura editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 4. Verificação da Chave de API | Verifica ou solicita a chave de API do teu fornecedor de IA | Assistente de primeira execução |

No final, é exibida uma ligação para esta documentação como referência.

## 🚀 Como Utilizar

```bash
gitpr --install
```

O assistente irá:
1. Exibir um cabeçalho de boas-vindas
2. Para cada etapa: explicar o que faz → pedir confirmação (`[Y/n]`) → executar ou saltar
3. Mostrar os resultados e o URL da documentação quando terminar

Cada etapa pode ser **saltada** respondendo `n` (não) quando solicitado. As etapas saltadas podem ser executadas posteriormente de forma individual usando os seus comandos equivalentes.

## 📋 Pré-requisitos

- **Ligação à internet:** Necessária para descarregar templates, hooks e verificar actualizações.
- **Repositório Git:** O comando deve ser executado dentro de um projeto git (necessário para hooks e análise de diff).
- **Ambiente Python:** O GitPR deve estar instalado e acessível no teu PATH.

## 📖 Detalhes Passo a Passo

### Etapa 1 — Skill Templates

Descarrega ficheiros template de contexto de IA para a pasta `.gitpr/skill/` do teu projeto:

- `.gitpr.commit.md` — Regras para geração de mensagens de commit
- `.gitpr.pr.md` — Estrutura necessária para descrições de PR
- `.gitpr.review.md` — Foco arquitetural para code reviews
- `.gitpr.filereview.md` — Regras de coesão e acoplamento para auditorias de ficheiros
- `.gitpr.issue.md` — Estrutura para geração padronizada de issues
- `.gitpr.blame.md` — Foco para rastreio de código legado
- `.gitpr.linter.yml` — Regras personalizadas de análise estática

Estes ficheiros **nunca são sobrescritos** se já existirem. Edita-os livremente para personalizar o comportamento da IA para as convenções da tua equipa.

📚 Ver também: [Sistema de Skills e Templates](skill-template.md)

### Etapa 2 — Git Hooks

Instala dois hooks Git locais em `.git/hooks/`:

- **`pre-commit`** — Executa o linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando código que viole as tuas regras.
- **`prepare-commit-msg`** — Usa IA para gerar uma mensagem no formato Conventional Commits e injeta-a no teu editor de commit.

Isto permite a prática **Shift-Left** — detetar problemas na máquina do programador antes de chegarem ao CI/CD ou à revisão de código.

📚 Ver também: [Git Hooks Locais](git-hooks-locais.md)

### Etapa 3 — Configuração MCP

Auto-deteta quais os editores com IA que utilizas e cria os ficheiros de configuração necessários:

| Editor | Ficheiro de configuração criado |
|--------|-------------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Uma vez configurado, podes usar linguagem natural no chat de IA do teu editor para invocar ferramentas GitPR: "Review my changes", "Generate a commit message", "Create a PR description", etc.

Os ficheiros de configuração existentes são **fundidos** — outros servidores MCP nunca são sobrescritos.

📚 Ver também: [Integração MCP](mcp-integration.md)

### Etapa 4 — Configuração da Chave de API

Verifica se a chave de API do teu fornecedor de IA já está configurada:

- **Se configurada:** Exibe uma mensagem de sucesso — estás pronto a usar.
- **Se ausente:** Oferece a possibilidade de configurá-la interativamente. A chave é encriptada com Fernet (encriptação simétrica) e armazenada de forma segura em `~/.gitpr/.env`.

Podes saltar esta etapa e configurá-la mais tarde executando `gitpr` (que aciona o assistente de primeira execução) ou editando `~/.gitpr/.env` diretamente.

📚 Ver também: [Fornecedores de IA](providers-ia.md)

## 🔄 Executar Etapas Individuais Mais Tarde

Se saltaste uma etapa, podes sempre executar o seu comando equivalente mais tarde:

```bash
gitpr --skill              # Etapa 1: Descarregar templates
gitpr --installhooks    # Etapa 2: Instalar Git hooks
gitpr-mcp --install auto   # Etapa 3: Configurar MCP
gitpr                      # Etapa 4: Chave de API (assistente de primeira execução)
```

## ⚙️ Ambientes CI/CD

Em pipelines CI/CD (detetados pelas variáveis de ambiente `CI` ou `GITHUB_ACTIONS`), o GitPR **não** solicitará chaves de API interativamente. Configura a tua chave antecipadamente usando variáveis de ambiente ou GitHub Secrets.

---
**Dica profissional:** Executa `gitpr --install` em cada novo clone para obter a experiência completa do GitPR configurada em segundos.
