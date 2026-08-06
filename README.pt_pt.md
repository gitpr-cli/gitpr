# **GitPR CLI 🚀** — Português (Portugal)

<p align="center">
  <img src="https://raw.githubusercontent.com/natanfiuza/gitpr/main/docs/logo.png" alt="GitPR Logo" width="150">
</p>

O GitPR CLI é uma ferramenta de automação via linha de comandos que utiliza inteligência artificial do **Google Gemini** e **DeepSeek** para analisar as suas alterações de código (git diff) ou ficheiros inteiros. A ferramenta gera automaticamente mensagens de commit no padrão *Conventional Commits*, descrições detalhadas de Pull Request e revisões profundas de código com foco na redução da dívida técnica.

🌐 **Site:** [gitpr.natanfiuza.dev.br](https://gitpr.natanfiuza.dev.br/) · 📂 **Repositório:** [github.com/natanfiuza/gitpr](https://github.com/natanfiuza/gitpr)

----

## ⚡ **Início Rápido**

### **1. Instalação via PyPI**

Instale o GitPR CLI utilizando o `pip`:

```bash
pip install gitpr-cli
```

### **2. Inicializar num Novo Repositório**

Para inicializar o GitPR na pasta de um novo repositório, execute:

```bash
gitpr --install
```

> **Configuração Guiada:** Configuração guiada que descarrega templates de skill, instala Git Hooks, configura MCP para os seus editores e verifica a chave de API do seu provedor de IA.  
> 📖 **Documentação completa:** [https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=pt_pt](https://gitpr.natanfiuza.dev.br/docs/install-wizard?lang=pt_pt)

## **🛠️ Tecnologias e Bibliotecas Utilizadas**

Este projeto foi desenvolvido em Python e utiliza as seguintes bibliotecas principais:

* [**Click**](https://click.palletsprojects.com/): Para criar uma interface de linha de comandos (CLI) robusta e amigável.
* [**Google GenAI**](https://pypi.org/project/google-genai/): SDK oficial para integração direta com a API do Gemini.
* [**OpenAI**](https://pypi.org/project/openai/): Biblioteca utilizada devido à sua total compatibilidade com a poderosa API da **DeepSeek**.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): Para a gestão segura de variáveis de ambiente.
* [**Pytest**](https://docs.pytest.org/): Para executar testes unitários de forma simples, colorida e legível na consola.
* [**Cryptography**](https://cryptography.io/): Para garantir que a sua `GEMINI_API_KEY` seja armazenada de forma encriptada e segura em disco.
* [**PyYAML**](https://pyyaml.org/): Usado para ler e processar as regras personalizadas de análise estática do ficheiro `.gitpr.linter.yml`.
* [**Textual**](https://textual.textualize.io/): Biblioteca poderosa para criação de Interfaces Gráficas de Terminal (TUI), usada no painel interativo de geração e edição de issues.
* [**Requests**](https://pypi.org/project/requests/): Biblioteca elegante e robusta para requisições HTTP, usada para comunicação com a API REST do GitHub.
* [**MCP**](https://pypi.org/project/mcp/): SDK oficial Python para o Model Context Protocol, permitindo que o GitPR se integre diretamente com editores e IDEs com tecnologia de IA.

----

## 📦 Como Compilar o Executável Localmente

Se deseja gerar o seu próprio binário a partir do código fonte, utilizamos o **PyInstaller**. Certifique-se de que está no diretório raiz do projeto com o ambiente virtual configurado.

1. Instale as dependências de desenvolvimento (se ainda não o fez):
   ```bash
   pipenv install --dev
   ```

2. Execute o comando de build apontando para o nosso ponto de entrada (`run.py`):
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Nota técnica:** A flag `--onefile` garante que todo o Python, bibliotecas e dependências sejam comprimidos num único binário. 🛠️

Após executar este comando, o PyInstaller criará algumas pastas (`build` e `dist`).
O seu ficheiro final pronto para uso estará dentro da pasta **`dist/`** com o nome `gitpr` (ou `gitpr.exe` no Windows).


----

## 🧪 Executando Testes

Para garantir que a lógica de captura do Git e a integração com a IA estão a funcionar corretamente, utilizamos testes unitários.

1. Instale as dependências de teste (se ainda não o fez):
   ```bash
   pipenv install --dev pytest
   ```

2. Execute os testes com o comando:
   ```bash
   pipenv run pytest -v
   ```
O Pytest detetará automaticamente os ficheiros dentro da pasta `tests/` e exibirá um relatório detalhado da execução.

----
## **⚙️ Instalação e Configuração**

### **Usando o Executável (Recomendado)**

1. Descarregue o executável do GitPR no separador "Releases" do GitHub.
2. Mova o executável para uma pasta que esteja no seu PATH (ex.: /usr/local/bin no Linux/Mac ou a sua pasta de utilizador no Windows).
3. Na primeira execução, o assistente irá guiá-lo:
   ```bash
   $ gitpr
   ```
```bash
🚀 Intelligent PR Automation with AI

🔧 First run detected! Let's configure GitPR CLI.

🔑 Enter your GEMINI_API_KEY:

📄 Default output filename pattern [{branch}_{datetime}_PR_DESC.md]:
```
*Nota: A sua configuração será guardada com segurança no ficheiro `~/.gitpr/.env`.*

> **🔒 Nota de Segurança:** O GitPR CLI usa encriptação simétrica (Fernet). A sua chave de API é armazenada como um hash no ficheiro `.env`, e a chave mestra para desencriptação é gerada automaticamente em `~/.gitpr/secret.key`. **Nunca partilhe o seu ficheiro secret.key.**

### A Partir do Código Fonte

1. Clone o repositório: `git clone https://github.com/natanfiuza/gitpr.git`

2. Entre na pasta: `cd gitpr`

3. Configure o ambiente:
```bash
pipenv install google-genai openai python-dotenv click cryptography
```
4. Execute: pipenv run python src/main.py

## **💻 Como Usar**

O GitPR possui um comportamento padrão poderoso e várias opções avançadas para auxiliá-lo no seu dia a dia como programador.

### **Comportamento Padrão (Pull Request)**
Simplesmente execute o comando puro no seu terminal:
```bash
gitpr
```
A ferramenta irá sincronizar com o remoto (`git fetch`), comparar as suas alterações com o ramo principal remoto (ex.: `origin/main`) e gerar um ficheiro Markdown (ex.: `feature-login_20260421110134_PR_DESC.md`) na raiz do seu projeto com a sugestão completa para o seu Pull Request.

### **Opções e Comandos Avançados**
Pode passar as seguintes *flags* para ações específicas:

* `-c` ou `--commit`: Executa um `git diff` local e exibe **apenas a mensagem de commit sugerida**.
* `-r` ou `--review`: Realiza um **Code Review** detalhado das alterações locais.
* `-f` ou `--fullreview`: Realiza um **Code Review Completo** analisando todas as alterações desde o ramo remoto.
* `-i <ficheiro>` ou `--input <ficheiro>`: **Auditoria Completa de Ficheiro.** Deve ser usado juntamente com `-r` ou `-f`; ignora o histórico git e faz um Code Review do ficheiro inteiro. Excelente para atuar como consultor em refatoração de código legado.
* `--provider <gemini|deepseek|ollama>`: Força o uso de uma IA específica apenas para esta execução, ignorando a predefinição guardada no `.env`.
* `--lang <código>`: Força o idioma da interface para esta execução (ex.: `en_us`, `pt_pt`). Sobrescreve o `GITPR_LANG` do `.env` sem persistir a alteração.
* `-ch` ou `--chat`: Abre o **Chat Interativo de Pair Programming** — um terminal TUI onde a IA vê o seu diff atual e mantém uma conversa contextual. Possui memória por ramo, comandos slash (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patching (F5), atualização de diff (F2) e exportação de sessão (F6).
* `-l` ou `--linter`: Executa **apenas o linter estático local** (sem chamadas de IA). Ideal para uso em pipelines de CI/CD para bloquear código fora de conformidade.
* `--mcp`: Inicia o GitPR como um **servidor MCP** (Model Context Protocol) no transporte stdio. Permite integração com VS Code, Cursor, Claude Desktop e outros editores compatíveis com MCP — expondo todas as capacidades de IA do GitPR como ferramentas diretamente dentro do seu IDE. Também disponível como comando standalone `gitpr-mcp`.
* `--install`: **Assistente de Configuração Interativo.** Executa uma configuração guiada em 4 etapas: descarrega skill templates, instala Git Hooks, configura MCP para editores detetados e verifica/solicita a sua chave de API do fornecedor de IA. Cada etapa pede confirmação antes de prosseguir.
* `-ih` ou `--installhooks`: Instala automaticamente **Git Hooks locais** (`pre-commit` e `prepare-commit-msg`) no seu repositório.
* `-s` ou `--skill`: Cria os ficheiros de template de contexto da IA (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) e o Linter (`.gitpr.linter.yml`) na raiz do projeto.
* `-is` ou `--issue`: Gera automaticamente um rascunho de uma **Issue padronizada** e abre uma interface interativa (TUI) para edição ou envio direto via API REST. Esta funcionalidade possui **3 motores de contexto** dependendo da combinação de comandos:
  * **Issue de Código Novo (`gitpr -is`):** Lê o `git diff` atual. **Porquê usar:** Ideal para documentar rapidamente a tarefa que acabou de programar, antes de fazer commit.
  * **Issue de Épico/Release (`gitpr -is -ht`):** Lê o histórico completo do ramo atual (Git Log + Cache de PR). **Porquê usar:** Ideal para gerar documentação consolidada de uma release inteira ou de uma *feature* grande que levou vários dias/commits para ser concluída.
  * **Issue de Dívida Técnica/Arqueológica (`gitpr -is -b ficheiro:linhas`):** Lê a linha do tempo de uma regra de negócio específica. **Porquê usar:** Ideal para documentar dívida técnica, explicando como um bloco de código legado evoluiu e porque precisa de ser refatorado.
* `-h` ou `--help`: Mostra a ajuda geral com todas as opções. Use juntamente com outra flag para **ajuda contextual** (ex.: `gitpr -h --issue`, `gitpr -h --linter`) com um link direto para a documentação detalhada de cada funcionalidade.
* `-u` ou `--update`: Verifica e instala a versão mais recente do GitPR (Auto-Updater).

> **⚙️ Nota Técnica (--hook):** O GitPR possui uma flag oculta `--hook <ficheiro>` que é acionada exclusivamente pelo sistema de Git Hooks em segundo plano. Permite que a IA injete a mensagem sugerida diretamente no ficheiro temporário do Git, sem poluir o seu terminal.
>
> **⚙️ Nota Técnica (--pre-save):** O GitPR possui uma flag oculta de debug `--pre-save` que pode ser combinada com qualquer comando de IA (ex.: `gitpr -c --pre-save`). Antes de cada chamada à IA, guarda o payload completo que será enviado ao modelo (system instruction + prompt + contadores de caracteres) num ficheiro `_{acao}-{datahora}.json` na pasta atual, e depois prossegue normalmente. Útil para inspecionar prompts muito grandes. Obs.: quando a resposta vem da cache local, nenhuma chamada é feita e nenhum ficheiro é gerado.

### 📦 Diffs Gigantes (Map-Reduce)

Quando o diff é demasiado grande para uma única chamada de IA (acima de ~90 mil tokens estimados), o GitPR divide-o automaticamente em lotes por ficheiro, pede à IA um resumo técnico de cada parte (Map) e unifica tudo na mensagem de commit, review ou descrição de PR final (Reduce). Sem flags — ativa sob demanda e mostra o progresso na consola.

📚 Documentação completa: [docs/map-reduce-diff.md](https://github.com/natanfiuza/gitpr/blob/main/docs/map-reduce-diff.md)

## 🛡️ Linter Local (Análise Estática)

O GitPR CLI permite que defina regras rigorosas que serão validadas instantaneamente durante o `--review` ou `--fullreview`, sem depender de IA. Isto é ideal para impedir que erros comuns (como `console.log` ou IPs de teste) cheguem ao repositório.

### Como configurar o `.gitpr.linter.yml`:
Ao executar `gitpr --skill`, um template será gerado. Pode configurar regras usando Expressões Regulares (Regex):

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensões a serem validadas
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # O que procurar
    message: "🚨 Localhost usage detected in file {file_name}"
    ignore_comments: true # Ignora se a linha estiver comentada
    ignore_paths: # Pastas ou ficheiros ignorados (aceita *)
      - "vendor/*"
      - "node_modules/*"
```

O Linter analisa apenas as **linhas adicionadas** no seu `git diff`, garantindo uma execução focada e extremamente rápida. Se houver violações, estas aparecerão destacadas no topo do seu ficheiro de review.

## 🧠 Arquitetura Multi-Modelo (IA Agnóstica)

O GitPR não está preso a uma única Inteligência Artificial. Durante a configuração inicial, o utilizador pode escolher o seu motor padrão. Atualmente oferecemos suporte a:
* **Google Gemini** (Padrão: `gemini-2.5-flash`)
* **DeepSeek** (Padrão: `deepseek-chat`)
* **Ollama** (Local) — execute modelos localmente sem internet, totalmente compatível com o formato da API OpenAI

Pode alternar dinamicamente os modelos configurando as variáveis `GEMINI_API_MODEL` ou `DEEPSEEK_API_MODEL` no seu ficheiro `~/.gitpr/.env`, ou alternar em tempo real usando a flag `--provider`.

## 🎯 Sistema de "Skills" Personalizáveis (Prompt Engineering)

Em vez de esconder instruções de IA no código fonte, o GitPR usa ficheiros Markdown locais que atuam como *System Instructions*. Ao executar `gitpr -s`, os seguintes ficheiros são gerados na raiz do seu projeto para personalizar a "persona" da IA de acordo com as regras de negócio da sua empresa:

* `.gitpr.commit.md`: Regras para gerar mensagens de commit curtas.
* `.gitpr.pr.md`: Estrutura de tópicos obrigatória para a descrição do Pull Request.
* `.gitpr.review.md`: Define o foco arquitetural (ex.: SOLID, Clean Code) para análise do diff.
* `.gitpr.filereview.md`: Define regras rigorosas de coesão e acoplamento para auditoria completa de ficheiro (usado com `--input`).
* `.gitpr.issue.md`: Define a estrutura e o nível de detalhe necessários para gerar Issues padronizadas (usado com `--issue`).
* `.gitpr.blame.md`: Define o foco da análise arqueológica para rastreamento de código legado (usado com `--blame`).

## 🌐 Internacionalização (i18n)

O GitPR deteta automaticamente o idioma do seu sistema e exibe as mensagens no seu idioma nativo. O sistema i18n é inspirado no **helper `__()` do Laravel**:

* **Deteção automática:** Na primeira execução, o GitPR deteta o idioma do SO e guarda em `~/.gitpr/.env` (`GITPR_LANG`).
* **Ficheiros de tradução:** Os pacotes de idioma são descarregados automaticamente do repositório oficial para `~/.gitpr/langs/`.
* **Fallback em inglês:** Se uma tradução estiver em falta, o texto em inglês é exibido diretamente.
* **API do programador:** Use `from src.i18n import __` e envolva todas as strings de interface com `__("O seu texto aqui")`.
* **Placeholders:** Suporta parâmetros nomeados — `__("A descarregar {file}...", file="template.md")`.

Para forçar um idioma específico, defina `GITPR_LANG=pt_pt` ou `GITPR_LANG=en` no `~/.gitpr/.env`.

> 📖 **Guia completo do programador:** [docs/i18n_explanation.md](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — arquitetura, padrões de uso, precauções com import circular e como adicionar novos idiomas.

## 🔄 Versionamento e Sincronização Automática de Scripts de Hooks

O GitPR inclui um sistema automático de versionamento para scripts de Git hooks (`pre-commit`, `prepare-commit-msg`, `pre-push`, `post-checkout`, `post-merge`). Sempre que executa `gitpr`, o sistema verifica silenciosamente se os seus hooks instalados correspondem à versão mais recente e atualiza-os automaticamente se necessário — tudo respeitando a sua preferência de idioma.

**Como funciona:**
1. Lê `SCRIPTS_VERSION` e `SCRIPTS_LANG` do `~/.gitpr/.env`
2. Compara com a versão mais recente (`__scripts_version__`) enviada com a sua release do GitPR
3. Se as versões ou o idioma diferirem → descarrega e atualiza os hooks automaticamente
4. Se tudo corresponder → ignora completamente (leitura única do `.env`, zero I/O de rede)

**Exemplo:**
```bash
# Primeira execução — sem hooks instalados ainda
$ gitpr --installhooks
📥 A descarregar pre-commit...
📥 A descarregar prepare-commit-msg...
✅ Scripts sincronizados com sucesso!

# Execuções seguintes — verificações silenciosas
$ gitpr  # (sem saída = hooks estão atualizados)
```

O sistema suporta **5 idiomas**: Inglês (padrão), Português (Brasil), Português (Portugal), Francês e Espanhol. Os scripts são thin shims — a lógica real reside no CLI, pelo que mesmo hooks ligeiramente desatualizados continuam a funcionar corretamente.

📚 [Documentação Completa](https://gitpr.natanfiuza.dev.br/docs/hooks-versioning?lang=pt_pt)

## 🔌 Integração MCP (Model Context Protocol)

O GitPR pode ser executado como um **servidor MCP**, expondo as suas capacidades com IA como ferramentas que o assistente de IA do seu editor pode invocar diretamente — sem precisar de terminal. Isto permite um fluxo de trabalho totalmente integrado onde pode gerar mensagens de commit, rever código, executar linters, rastrear origens de código e criar issues sem sair do seu IDE.

### Editores Compatíveis

| Editor | Ficheiro de Configuração |
| ------ | ------------------------ |
| **VS Code** | `.vscode/mcp.json` |
| **Cursor** | `.cursor/mcp.json` |
| **Claude Code** | `.mcp.json` |
| **Claude Desktop** | `claude_desktop_config.json` |
| **Zed** | `settings.json` |

### Configuração Rápida

Use o instalador integrado para configurar o seu editor automaticamente:

```bash
gitpr-mcp --install vscode    # Cria .vscode/mcp.json
gitpr-mcp --install cursor      # Cria .cursor/mcp.json
gitpr-mcp --install claude-code # Cria .mcp.json
gitpr-mcp --install claude      # Atualiza config do Claude Desktop
gitpr-mcp --install zed         # Atualiza config do Zed
gitpr-mcp --install auto      # Auto-detectar e instalar para todos
```

O instalador cria o diretório de config se necessário, funde com qualquer
config existente (nunca sobrescreve outros servidores) e é seguro executar
múltiplas vezes.

> Configuração manual também é suportada — veja [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md)
> para o formato JSON de cada editor.

Uma vez configurado, use linguagem natural no chat de IA do seu editor:

   * *"Revise as minhas alterações atuais"* → chama `review_code`
   * *"Gere uma mensagem de commit"* → chama `generate_commit_message`
   * *"Crie uma descrição de PR"* → chama `generate_pr_description`
   * *"Execute o linter no meu diff"* → chama `run_linter`

### Ferramentas MCP Disponíveis

| Ferramenta | Descrição |
| ---------- | --------- |
| `get_git_context` | Ramo atual, nome do repositório e URL do remote |
| `analyze_diff` | Diff git das alterações não commitadas |
| `get_full_diff` | Diff completo contra origin/main |
| `generate_commit_message` | Mensagem Conventional Commits gerada por IA |
| `review_code` | Code review com IA das alterações locais |
| `full_review` | Code review com IA de todas as alterações desde origin/main |
| `generate_pr_description` | Descrição completa de PR (título + corpo) |
| `run_linter` | Linter estático baseado no `.gitpr.linter.yml` |
| `analyze_blame` | Git blame + classificação por IA |
| `generate_issue` | Issue estruturada a partir de diff, histórico ou blame |

📖 **Documentação completa:** [docs/mcp-integration.md](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — disponível em 5 idiomas (EN, PT-BR, PT-PT, ES, FR).

> 💬 **MCP Prompts** — O GitPR também expõe 7 modelos de mensagem predefinidos (prompts) para fluxos comuns como "Rever PR", "Gerar Mensagem de Commit" e "Criar Issue a partir do Diff". Consulte o [guia de MCP Prompts](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) para a lista completa.

## 📚 Documentação Técnica e Guias Avançados

Para manter este README conciso, detalhamos as implementações mais avançadas focadas em **DevOps** e **Integração Contínua** em documentos separados.

Se deseja implementar o GitPR como uma barreira de qualidade automatizada na sua equipa, confira os guias abaixo.

> 🌐 Cada guia está disponível em **5 idiomas** — adicione `.pt_br`, `.pt_pt`, `.fr_fr` ou `.es_es` antes da extensão `.md` para versões traduzidas (ex.: `docs/understanding_chat_functionality.pt_pt.md`). Inglês é o padrão sem sufixo.

### Chat e Recursos Interativos

* [**🧠 Chat Interativo (Pair Programming)**](https://github.com/natanfiuza/gitpr/blob/main/docs/understanding_chat_functionality.md) — Como usar o chat com IA com memória, comandos slash, auto-patch e exportação de sessão.

### DevOps & CI/CD

* [**Git Hooks Locais (Shift-Left)**](https://github.com/natanfiuza/gitpr/blob/main/docs/git-hooks-locais.md) — Como usar `gitpr --installhooks` para criar barreiras de qualidade na máquina do programador e usar IA para gerar mensagens de commit automaticamente.
* [**Versionamento e Sincronização de Scripts de Hooks**](https://github.com/natanfiuza/gitpr/blob/main/docs/hooks-versioning.md) — Como o sistema de versionamento automático e sincronização com suporte a i18n mantém os seus Git hooks sempre atualizados.
* [**Linter Estático Personalizável**](https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md) — Como criar regras de validação no `.gitpr.linter.yml` para CI/CD e hooks de pre-commit.
* [**Integração CI/CD (GitHub Actions)**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-ci-linter.md) — Como executar o GitPR no pipeline para bloquear "Merge" de PRs com violações.

### Funcionalidades Principais

* [**Pull Request (Modo Padrão)**](https://github.com/natanfiuza/gitpr/blob/main/docs/pr-descricao-padrao.md) — Fluxo completo para gerar descrições de PR sem flags.
* [**Code Review com IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/code-review-ia.md) — Guia dos modos de review (`--review`, `--fullreview`) e auditoria de ficheiros (`--input`).
* [**Mensagens de Commit com IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/commit-message-ia.md) — Como gerar mensagens no padrão Conventional Commits e integrar com Git Hooks.
* [**Geração de Issues e Interface TUI**](https://github.com/natanfiuza/gitpr/blob/main/docs/issue-tui-help.md) — Como usar a interface gráfica de terminal (TUI) e os 3 motores de contexto para gerir Issues estruturadas.
* [**Arqueólogo de Código (Git Blame)**](https://github.com/natanfiuza/gitpr/blob/main/docs/blame-arqueologo.md) — Como rastrear a origem de regras de negócio com `git blame` e IA.
* [**Sistema de Skills e Templates**](https://github.com/natanfiuza/gitpr/blob/main/docs/skill-template.md) — Como personalizar o comportamento da IA com ficheiros `.gitpr.*.md`.

### Configuração e Infraestrutura

* [**Assistente de Instalação**](https://github.com/natanfiuza/gitpr/blob/main/docs/install-wizard.md) — Configuração guiada passo a passo para configurar o GitPR num novo projeto.
* [**Provedores de IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/providers-ia.md) — Configuração e seleção entre Google Gemini, DeepSeek e Ollama.
* [**Auto-Updater**](https://github.com/natanfiuza/gitpr/blob/main/docs/auto-update.md) — Como funciona a atualização automática (hot-swap) do GitPR.
* [**Token GitHub (PAT) — Integração e Segurança**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration.md) — Entenda como o GitPR cria issues diretamente no repositório com autenticação.
* [**Internacionalização (i18n)**](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — Arquitetura, padrões de uso e como adicionar novos idiomas.
* [**Integração MCP**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-integration.md) — Conecte o GitPR ao VS Code, Cursor e Claude Desktop via Model Context Protocol.
* [**MCP Prompts**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-prompts.md) — Modelos de mensagem predefinidos (7 prompts, 35 variantes de idioma) para fluxos comuns no chat de IA do seu editor.
* [**MCP Tool Annotations**](https://github.com/natanfiuza/gitpr/blob/main/docs/mcp-annotations.md) — Dicas de integração com IDEs (`readOnlyHint`, `destructiveHint`) para comportamento de IU mais inteligente e execução segura de ferramentas.
* [**Métricas e Telemetria**](https://github.com/natanfiuza/gitpr/blob/main/docs/metricas-telemetria.md) — Analytics local offline para métricas de utilização da equipa, relatórios CSV exportáveis e dashboard TUI interativo.

## ⚡ Sistema de Cache Local (Poupança de Cota)

O GitPR possui um motor de cache inteligente baseado em **MD5**. Sempre que executa um comando (`--review`, `--commit`, etc.), a ferramenta gera um hash exato do seu código atual (diff) e das instruções.
Se executar o mesmo comando novamente sem alterar o código, o GitPR interceta o pedido e devolve o resultado instantaneamente (em milissegundos) da pasta `~/.gitpr/cache/prompts/`, poupando o seu tempo e as suas quotas da API!

## 🔄 Auto-Updater (Atualização Over-The-Air)

Nunca mais se preocupe em descarregar novas versões manualmente. O GitPR possui um Guardião de Conexão e um atualizador integrado:
* Verifica a disponibilidade de rede antes de iniciar para não bloquear o seu fluxo de trabalho offline.
* A cada execução, verifica silenciosamente se há uma nova release oficial na API do GitHub.
* Pode forçar a verificação e instalação executando `gitpr --update` ou `gitpr -u`.
* A ferramenta usa a técnica de *Hot-Swap*, descarregando o novo `.exe` e substituindo a versão antiga de forma transparente.

## Publicação no PyPI

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 Como Contribuir**

Contribuições são muito bem-vindas! Para contribuir:

1. Faça um fork do projeto.
2. Crie um ramo para a sua *feature* (git checkout -b feature/NovaFuncionalidade).
3. Faça commit das suas alterações (git commit -m 'feat: adiciona nova funcionalidade'). Dica: Use o próprio GitPR para gerar esta mensagem! 😄
4. Faça push para o ramo (git push origin feature/NovaFuncionalidade).
5. Abra um Pull Request.

## **✨ Agradecimentos e Autoria**

Projeto idealizado e desenvolvido por:

**Natan Fiuza** - [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 Licença**

Este projeto está licenciado sob a **GNU Lesser General Public License v2.1 (LGPL-2.1)**. Veja o ficheiro LICENSE para mais detalhes.
