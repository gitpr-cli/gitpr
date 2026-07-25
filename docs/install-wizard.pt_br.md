# Assistente de Configuração Interativo do GitPR (`--install`)

O comando `gitpr --install` executa um assistente guiado interativo que prepara o ambiente do seu projeto com todas as configurações essenciais do GitPR em um único fluxo. Ele consolida várias etapas manuais de configuração em uma experiência integrada.

## ✨ O Que Ele Faz

O assistente guia você por **4 etapas**, solicitando confirmação antes de cada uma:

| Etapa | O que configura | Comando equivalente |
|------|----------------|--------------------|
| 1. Skill Templates | Baixa arquivos de template `.gitpr.*.md` e `.gitpr.linter.yml` | `gitpr --skill` |
| 2. Git Hooks | Instala hooks `pre-commit` e `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 3. Configuração MCP | Auto-deteta e configura editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 4. Verificação de Chave de API | Verifica ou solicita a chave de API do seu provedor de IA | Assistente de primeira execução |

Ao final, um link para esta documentação é exibido para referência.

## 🚀 Como Usar

```bash
gitpr --install
```

O assistente irá:
1. Exibir um cabeçalho de boas-vindas
2. Para cada etapa: explicar o que faz → solicitar confirmação (`[Y/n]`) → executar ou pular
3. Mostrar resultados e a URL da documentação ao finalizar

Cada etapa pode ser **pulada** respondendo `n` (não) quando solicitado. Etapas puladas podem ser executadas posteriormente individualmente usando seus comandos equivalentes.

## 📋 Pré-requisitos

- **Conexão com internet:** Necessária para baixar templates, hooks e verificar atualizações.
- **Repositório Git:** O comando deve ser executado dentro de um projeto git (necessário para hooks e análise de diff).
- **Ambiente Python:** O GitPR deve estar instalado e acessível no seu PATH.

## 📖 Detalhamento das Etapas

### Etapa 1 — Skill Templates

Baixa os arquivos de template de contexto de IA para a pasta `.gitpr/skill/` do seu projeto:

- `.gitpr.commit.md` — Regras para geração de mensagens de commit
- `.gitpr.pr.md` — Estrutura necessária para descrições de PR
- `.gitpr.review.md` — Foco arquitetural para code reviews
- `.gitpr.filereview.md` — Regras de coesão e acoplamento para auditorias de arquivo
- `.gitpr.issue.md` — Estrutura para geração padronizada de issues
- `.gitpr.blame.md` — Foco para rastreamento de código legado
- `.gitpr.linter.yml` — Regras personalizadas de análise estática

Estes arquivos **nunca são sobrescritos** se já existirem. Edite-os livremente para personalizar o comportamento da IA para as convenções da sua equipe.

📚 Veja também: [Sistema de Skills e Templates](skill-template.md)

### Etapa 2 — Git Hooks

Instala dois hooks Git locais em `.git/hooks/`:

- **`pre-commit`** — Executa o linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando código que viola suas regras.
- **`prepare-commit-msg`** — Usa IA para gerar uma mensagem no formato Conventional Commits e a injeta no seu editor de commit.

Isso habilita a prática **Shift-Left** — detectando problemas na máquina do desenvolvedor antes que cheguem ao CI/CD ou ao code review.

📚 Veja também: [Git Hooks Locais](git-hooks-locais.md)

### Etapa 3 — Configuração MCP

Auto-deteta quais editores com IA você usa e cria os arquivos de configuração necessários:

| Editor | Arquivo de configuração criado |
|--------|-------------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Uma vez configurado, você pode usar linguagem natural no chat de IA do seu editor para invocar as ferramentas do GitPR: "Revise minhas alterações", "Gere uma mensagem de commit", "Crie uma descrição de PR", etc.

Arquivos de configuração existentes são **mesclados** — outros servidores MCP nunca são sobrescritos.

📚 Veja também: [Integração MCP](mcp-integration.md)

### Etapa 4 — Configuração da Chave de API

Verifica se a chave de API do seu provedor de IA já está configurada:

- **Se configurada:** Exibe uma mensagem de sucesso — você está pronto para usar.
- **Se ausente:** Oferece a opção de configurá-la interativamente. A chave é criptografada com Fernet (criptografia simétrica) e armazenada com segurança em `~/.gitpr/.env`.

Você pode pular esta etapa e configurá-la depois executando `gitpr` (que aciona o assistente de primeira execução) ou editando `~/.gitpr/.env` diretamente.

📚 Veja também: [Provedores de IA](providers-ia.md)

## 🔄 Executando Etapas Individuais Depois

Se você pulou uma etapa, pode sempre executar seu comando equivalente posteriormente:

```bash
gitpr --skill              # Etapa 1: Baixar templates
gitpr --installhooks       # Etapa 2: Instalar Git hooks
gitpr-mcp --install auto   # Etapa 3: Configurar MCP
gitpr                      # Etapa 4: Chave de API (assistente de primeira execução)
```

## ⚙️ Ambientes CI/CD

Em pipelines CI/CD (detectados pelas variáveis de ambiente `CI` ou `GITHUB_ACTIONS`), o GitPR **não** solicitará chaves de API interativamente. Configure sua chave antecipadamente usando variáveis de ambiente ou GitHub Secrets.

---
**Dica profissional:** Execute `gitpr --install` em cada novo clone para obter a experiência completa do GitPR configurada em segundos.
