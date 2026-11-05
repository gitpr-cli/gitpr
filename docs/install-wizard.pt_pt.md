# Assistente de Configuração Interativo do GitPR (`--install`)

O comando `gitpr --install` executa um assistente guiado interativo que prepara o ambiente do teu projeto com todas as configurações essenciais do GitPR num único fluxo. Consolida vários passos de configuração manual numa experiência única e contínua.

## ✨ O Que Faz

O assistente guia-te por **5 etapas**, pedindo confirmação antes de cada uma:

| Etapa | O que configura | Comando equivalente |
|-------|----------------|---------------------|
| 1. Configuração Local do Projeto | Inicializa `.gitpr/conf/` (`gitpr.config.yml`, `gitpr.smart-excludes.json`) | `gitpr seed` |
| 2. Modelos de Skill & Linter | Descarrega ficheiros `.gitpr.*.md` e `.gitpr.linter.yml` em `.gitpr/skill/` (com opção de linters externos) | `gitpr --skill` / `gitpr --linter-setup` |
| 3. Git Hooks | Instala hooks `pre-commit` e `prepare-commit-msg` localmente | `gitpr --installhooks` |
| 4. Configuração MCP | Auto-deteta e configura editores (VS Code, Cursor, Claude, Zed) | `gitpr-mcp --install auto` |
| 5. Verificação da Chave de API | Verifica ou solicita a chave de API do teu fornecedor de IA | Assistente de primeira execução |

No final, é exibida uma ligação para esta documentação como referência.

O ficheiro de configuração do projeto `.gitpr/conf/gitpr.config.yml` define o ramo que os pull requests deste repositório devem apontar — `PR_DEFAULT_BASE` quando definido, `main` caso contrário. Ficheiros existentes nunca são sobrescritos por predefinição. Versione-o para que toda a equipa aponte para o mesmo ramo ([Publicação de Pull Request](pull-request-publication.pt_pt.md#91-o-ficheiro-do-projeto)).

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

### Passo 1 — Configuração Local do Projeto

Inicializa os ficheiros de configuração locais em `.gitpr/conf/`:
- **`gitpr.config.yml`** — Configuração do ramo base de PR para o repositório.
- **`gitpr.smart-excludes.json`** — Regras específicas do projeto de exclusão de ficheiros e pastas para diffs de IA, unificadas com a lista global em runtime.

### Passo 2 — Modelos de Skill & Linter

Descarrega os ficheiros de modelo de contexto de IA para a pasta `.gitpr/skill/` do teu projeto:

- `.gitpr.commit.md` — Regras para geração de mensagens de commit
- `.gitpr.pr.md` — Estrutura necessária para descrições de PR
- `.gitpr.review.md` — Foco arquitetural para revisões de código
- `.gitpr.filereview.md` — Regras de coesão e acoplamento para auditorias de ficheiro
- `.gitpr.issue.md` — Estrutura para geração padronizada de issues
- `.gitpr.blame.md` — Foco para rastreio de código legado
- `.gitpr.linter.yml` — Regras personalizadas de análise estática local

Estes ficheiros **nunca são sobrescritos** se já existirem. Edita-os livremente para personalizar o comportamento da IA para as convenções da tua equipa.

Ao descarregar os modelos, o assistente oferece opcionalmente configurar pontes para linters externos (ESLint, PHPCS, Stylelint).

📚 Consulta também: [Sistema de Skills e Modelos](skill-template.pt_pt.md)

### Passo 3 — Git Hooks

Instala dois Git hooks locais em `.git/hooks/`:

- **`pre-commit`** — Executa o linter estático (`.gitpr.linter.yml`) antes de cada commit, bloqueando código que viole as tuas regras.
- **`prepare-commit-msg`** — Usa IA para gerar uma mensagem no padrão Conventional Commits e injeta-a no teu editor de commit.

Isto viabiliza a prática de **Shift-Left** — detetando problemas na máquina do programador antes que cheguem ao CI/CD ou à revisão de código.

📚 Consulta também: [Git Hooks Locais](git-hooks-locais.pt_pt.md)

### Passo 4 — Configuração MCP

Auto-deteta quais os editores com IA que usas e cria os ficheiros de configuração necessários:

| Editor | Ficheiro de config criado |
|--------|---------------------------|
| VS Code | `.vscode/mcp.json` |
| Cursor | `.cursor/mcp.json` |
| Claude Code | `.mcp.json` |
| Claude Desktop | `claude_desktop_config.json` |
| Zed | `settings.json` |

Uma vez configurado, podes usar linguagem natural no chat de IA do teu editor para invocar ferramentas do GitPR: "Revê as minhas alterações", "Gera uma mensagem de commit", "Cria uma descrição de PR", etc.

Ficheiros de config existentes são **fundidos** — outros servidores MCP nunca são sobrescritos.

📚 Consulta também: [Integração MCP](mcp-integration.pt_pt.md)

### Passo 5 — Configuração da Chave de API

Verifica se a chave de API do teu fornecedor de IA já está configurada:

- **Se configurada:** Exibe uma mensagem de sucesso — estás pronto a utilizar.
- **Se ausente:** Oferece para configurá-la interativamente. A chave é encriptada com Fernet (encriptação simétrica) e armazenada com segurança em `~/.gitpr/.env`.

Podes saltar este passo e configurá-la posteriormente executando `gitpr` (que aciona o assistente de primeira execução) ou editando `~/.gitpr/.env` diretamente.

📚 Consulta também: [Fornecedores de IA](providers-ia.pt_pt.md)

---

## ⚡ Inicialização Direta de Configurações (`gitpr seed`)

Para inicializar os ficheiros de configuração do projeto diretamente, sem passar por todo o assistente interativo:

```bash
gitpr seed
```

Ou usando a flag raiz:
```bash
gitpr --seed
```

### Opções:
- `--force` / `-f`: Sobrescreve os ficheiros existentes com os modelos predefinidos.
- `--all` / `-a`: Também descarrega todos os 12 modelos de prompt de IA em `.gitpr/skill/`.

## 🔄 Executar Passos Individuais Posteriormente

Se saltaste um passo, podes sempre executar o seu comando equivalente mais tarde:

```bash
gitpr seed                 # Passo 1: Configuração do projeto
gitpr --skill              # Passo 2: Descarregar modelos
gitpr --linter-setup       # Passo 2 (opcional): Linters externos
gitpr --installhooks       # Passo 3: Instalar Git hooks
gitpr-mcp --install auto   # Passo 4: Configurar MCP
gitpr                      # Passo 5: Chave de API (primeira execução)
```

## ⚙️ Ambientes CI/CD

Em pipelines de CI/CD (detetados pelas variáveis de ambiente `CI` ou `GITHUB_ACTIONS`), o GitPR **não** solicitará chaves de API interativamente. Configura a tua chave antecipadamente usando variáveis de ambiente ou GitHub Secrets.

---
**Dica:** Executa `gitpr --install` ou `gitpr seed` em cada novo clone para configurar o repositório em segundos.
