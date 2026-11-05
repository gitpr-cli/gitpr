# Assistente de Configuração Interativo do GitPR (`--install`)

O comando `gitpr --install` executa um assistente guiado interativo que prepara o ambiente do seu projeto com todas as configurações essenciais do GitPR em um único fluxo. Ele consolida várias etapas manuais de configuração em uma experiência integrada.

## ✨ O Que Ele Faz

O assistente guia você por **5 etapas**, solicitando confirmação antes de cada uma:

| Etapa | O que configura | Comando equivalente |
|------|----------------|--------------------|
| 1. Configuração Local do Projeto | Inicializa `.gitpr/conf/` (`gitpr.config.yml`, `gitpr.smart-excludes.json`) | `gitpr seed` |
| 2. Skill Templates & Linter | Baixa arquivos `.gitpr.*.md` e `.gitpr.linter.yml` em `.gitpr/skill/` (com opção de linters externos) | `gitpr --skill` / `gitpr --linter-setup` |
| 3. Git Hooks | Instala hooks `pre-commit` e `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 4. Configuração MCP | Auto-deteta e configura editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 5. Verificação de Chave de API | Verifica ou solicita a chave de API do seu provedor de IA | Assistente de primeira execução |

Ao final, um link para esta documentação é exibido para referência.

O arquivo de configuração do projeto `.gitpr/conf/gitpr.config.yml` define a branch que os pull requests deste repositório devem mirar — `PR_DEFAULT_BASE` quando definido, `main` caso contrário. Arquivos existentes nunca são sobrescritos por padrão. Versione-o para que o time inteiro aponte para a mesma branch ([Publicação de Pull Request](pull-request-publication.pt_br.md#91-o-arquivo-do-projeto)).

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

### Etapa 1 — Configuração Local do Projeto

Inicializa os arquivos de configuração locais em `.gitpr/conf/`:
- **`gitpr.config.yml`** — Configuração da branch base de PR para o repositório.
- **`gitpr.smart-excludes.json`** — Regras específicas do projeto de exclusão de arquivos e pastas para diffs de IA, unificadas com a lista global em runtime.

### Etapa 2 — Skill Templates & Linter

Baixa os arquivos de template de contexto de IA para a pasta `.gitpr/skill/` do seu projeto:

- `.gitpr.commit.md` — Regras para geração de mensagens de commit
- `.gitpr.pr.md` — Estrutura necessária para descrições de PR
- `.gitpr.review.md` — Foco arquitetural para code reviews
- `.gitpr.filereview.md` — Regras de coesão e acoplamento para auditorias de arquivo
- `.gitpr.issue.md` — Estrutura para geração padronizada de issues
- `.gitpr.blame.md` — Foco para rastreamento de código legado
- `.gitpr.linter.yml` — Regras customizadas de análise estática local

Estes arquivos **nunca são sobrescritos** se já existirem. Edite-os livremente para customizar o comportamento da IA para as convenções do seu time.

Ao baixar os templates, o assistente oferece opcionalmente configurar pontes para linters externos (ESLint, PHPCS, Stylelint).

📚 Veja também: [Sistema de Skills e Templates](skill-template.pt_br.md)

### Etapa 3 — Git Hooks

Instala dois Git hooks locais em `.git/hooks/`:

- **`pre-commit`** — Executa o linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando código que viole suas regras.
- **`prepare-commit-msg`** — Usa IA para gerar uma mensagem no padrão Conventional Commits e a injeta no seu editor de commit.

Isso viabiliza a prática de **Shift-Left** — detectando problemas na máquina do desenvolvedor antes que cheguem ao CI/CD ou code review.

📚 Veja também: [Git Hooks Locais](git-hooks-locais.pt_br.md)

### Etapa 4 — Configuração MCP

Auto-deteta quais editores com IA você usa e cria os arquivos de configuração necessários:

| Editor | Arquivo de config criado |
|--------|--------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Uma vez configurado, você pode usar linguagem natural no chat de IA do seu editor para invocar ferramentas do GitPR: "Revise minhas alterações", "Gere uma mensagem de commit", "Crie uma descrição de PR", etc.

Arquivos de config existentes são **mesclados** — outros servidores MCP nunca são sobrescritos.

📚 Veja também: [Integração MCP](mcp-integration.pt_br.md)

### Etapa 5 — Configuração da Chave de API

Verifica se a chave de API do seu provedor de IA já está configurada:

- **Se configurada:** Exibe uma mensagem de sucesso — você está pronto para usar.
- **Se ausente:** Oferece para configurá-la interativamente. A chave é criptografada com Fernet (criptografia simétrica) e armazenada com segurança em `~/.gitpr/.env`.

Você pode pular esta etapa e configurá-la posteriormente executando `gitpr` (que aciona o assistente de primeira execução) ou editando `~/.gitpr/.env` diretamente.

📚 Veja também: [Provedores de IA](providers-ia.pt_br.md)

---

## ⚡ Semeadura Direta de Configurações (`gitpr seed`)

Para semear os arquivos de configuração do projeto diretamente, sem passar por todo o assistente interativo:

```bash
gitpr seed
```

Ou usando a flag raiz:
```bash
gitpr --seed
```

### Opções:
- `--force` / `-f`: Sobrescreve os arquivos existentes com os templates padrão.
- `--all` / `-a`: Também baixa todos os 12 templates de prompt de IA em `.gitpr/skill/`.

## 🔄 Executando Etapas Individuais Posteriormente

Se você pulou uma etapa, pode sempre executar seu comando equivalente posteriormente:

```bash
gitpr seed                 # Etapa 1: Configuração do projeto
gitpr --skill              # Etapa 2: Baixar templates
gitpr --linter-setup       # Etapa 2 (opcional): Linters externos
gitpr --installhooks       # Etapa 3: Instalar Git hooks
gitpr-mcp --install auto   # Etapa 4: Configurar MCP
gitpr                      # Etapa 5: Chave de API (primeira execução)
```

## ⚙️ Ambientes CI/CD

Em pipelines de CI/CD (detetados pelas variáveis de ambiente `CI` ou `GITHUB_ACTIONS`), o GitPR **não** solicitará chaves de API interativamente. Configure sua chave antecipadamente usando variáveis de ambiente ou GitHub Secrets.

---
**Dica:** Execute `gitpr --install` ou `gitpr seed` em cada novo clone para configurar o repositório em segundos.
