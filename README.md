# **GitPR CLI 🚀**

GitPR CLI é uma ferramenta de automação de linha de comando que utiliza a inteligência artificial do **Google Gemini** e do **DeepSeek** para analisar as suas alterações de código (git diff) ou ficheiros completos. A ferramenta gera automaticamente mensagens de commit no padrão *Conventional Commits*, descrições detalhadas para Pull Requests e Code Reviews profundos visando a redução de dívida técnica.

## **🛠️ Tecnologias e Bibliotecas Utilizadas**

Este projeto foi desenvolvido em Python e utiliza as seguintes bibliotecas principais:

* [**Click**](https://click.palletsprojects.com/): Para criar uma interface de linha de comando (CLI) robusta e amigável.  
* [**Google GenAI**](https://pypi.org/project/google-genai/): SDK oficial para integração direta com a API do Gemini.  
* [**OpenAI**](https://pypi.org/project/openai/): Biblioteca utilizada devido à sua total compatibilidade com a poderosa API do **DeepSeek**.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): Para a gestão segura de variáveis de ambiente.
* [**Pytest**](https://docs.pytest.org/): Para execução de testes unitários de forma simples, colorida e legível no console.
* [**Cryptography**](https://cryptography.io/): Para garantir que sua `GEMINI_API_KEY` seja armazenada de forma encriptada e segura no disco.
* [**PyYAML**](https://pyyaml.org/): Utilizado para ler e processar as regras customizadas de análise estática do arquivo `.gitpr.linter.yml`.
* [**Textual**](https://textual.textualize.io/): Biblioteca poderosa para a criação de Interfaces Gráficas de Terminal (TUI), utilizada no painel interativo de geração e edição de Issues.
* [**Requests**](https://pypi.org/project/requests/): Biblioteca elegante e robusta para requisições HTTP, utilizada para a comunicação com a API REST do GitHub.

----

## 📦 Como Compilar o Executável Localmente

Se você deseja gerar o seu próprio binário a partir do código-fonte, utilizamos o **PyInstaller**. Certifique-se de estar no diretório raiz do projeto e com o ambiente virtual configurado.

1. Instale as dependências de desenvolvimento (caso ainda não tenha feito):
   ```bash
   pipenv install --dev
   ```

2. Execute o comando de build apontando para o nosso ponto de entrada (`run.py`):
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Nota técnica:** A flag `--onefile` garante que todo o Python, bibliotecas e dependências ficam comprimidos num único binário, enquanto `--paths src` ajuda o compilador a encontrar os nossos arquivos `core.py` e `config.py`. 🛠️

Após a execução deste comando, o PyInstaller vai criar algumas pastas (`build` e `dist`). 
O seu arquivo final e pronto a usar estará dentro da pasta **`dist/`** com o nome `gitpr` (ou `gitpr.exe` no Windows). 


----

## 🧪 Executando Testes

Para garantir que a lógica de captura do Git e a integração com a IA estejam funcionando corretamente, utilizamos testes unitários.

1. Instale as dependências de teste (caso ainda não tenha feito):
   ```bash
   pipenv install --dev pytest
   ```

2. Execute os testes com o comando:
   ```bash
   pipenv run pytest -v
   ```
O Pytest irá detectar automaticamente os arquivos dentro da pasta `tests/` e apresentará um relatório detalhado da execução.

----
## **⚙️ Instalação e Configuração**

### **Usando o Executável (Recomendado)**

1. Faça o download do arquivo executável gitpr na aba "Releases" do GitHub.  
2. Mova o executável para uma pasta que esteja no seu PATH (ex: /usr/local/bin no Linux/Mac ou na pasta do seu utilizador no Windows).  
3. Na primeira execução, o assistente irá guiá-lo:  
   $ gitpr
```bash
🚀 Automação Inteligente de PRs com IA

🔧 Primeira execução detetada! Vamos configurar o GitPR CLI.

🔑 Insira sua GEMINI_API_KEY:

📄 Padrão do nome do arquivo de saída [{branch}_{datetime}_PR_DESC.md]:
```` 
*Nota: A sua configuração será guardada em segurança no arquivo `~/.gitpr/.env`.*

> **🔒 Nota sobre Segurança:** O GitPR CLI utiliza criptografia simétrica (Fernet). Sua chave de API é armazenada como um hash no arquivo `.env`, e a chave mestra para desencriptação é gerada automaticamente em `~/.gitpr/secret.key`. **Nunca compartilhe seu arquivo secret.key.**

### A partir do Código-Fonte

1. Clone o repositório: `git clone https://github.com/natanfiuza/gitpr.git`

2. Entre na pasta: `cd gitpr`

3. Atualize o ambiente:  
```bash  
pipenv install google-genai openai python-dotenv click cryptography
``` 
4. Execute: pipenv run python src/main.py

## **💻 Como Usar**

O GitPR possui um comportamento padrão poderoso e diversas opções avançadas para auxiliar no seu dia a dia como desenvolvedor.

### **Comportamento Padrão (Pull Request)**
Basta executar o comando puro no seu terminal:
```bash
gitpr
```
A ferramenta irá sincronizar com o remoto (`git fetch`), comparar as suas alterações com a branch principal remota (ex: `origin/main`), e gerar um arquivo Markdown (ex: `feature-login_20260421110134_PR_DESC.md`) na raiz do seu projeto com a sugestão completa para o seu Pull Request.

### **Opções e Comandos Avançados**
Você pode passar as seguintes *flags* para ações específicas:

* `-c` ou `--commit`: Executa um `git diff` local e exibe **apenas a mensagem de commit** sugerida.
* `-r` ou `--review`: Realiza um **Code Review** detalhado das alterações locais.
* `-f` ou `--fullreview`: Realiza um **Code Review completo** analisando todas as alterações desde a branch remota.
* `-i <arquivo>` ou `--input <arquivo>`: **Auditoria de Ficheiro Completo.** Usado obrigatoriamente em conjunto com `-r` ou `-f`, ele ignora o histórico do git e faz um Code Review do ficheiro inteiro. Excelente para atuar como consultor em refatoração de código legado.
* `--provider <gemini|deepseek>`: Força a utilização de uma IA específica apenas para esta execução, ignorando o seu padrão guardado no `.env`.
* `-l` ou `--linter`: Roda **apenas o linter estático local** (sem chamadas de IA). Ideal para usar em pipelines de CI/CD para bloquear código fora do padrão.
* `-ih` ou `--installhooks`: Instala automaticamente os **Git Hooks locais** (`pre-commit` e `prepare-commit-msg`) no seu repositório.
* `-s` ou `--skill`: Cria os arquivos de template de contexto da IA (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) e do Linter (`.gitpr.linter.yml`) na raiz do projeto.
* `-is` ou `--issue`: Gera automaticamente o rascunho de uma **Issue padronizada** e abre uma interface interativa (TUI) para edição ou envio direto via API REST. Esta funcionalidade possui **3 motores de contexto** dependendo da combinação de comandos:
  * **Issue de Código Novo (`gitpr -is`):** Lê o `git diff` atual. **Por que usar:** Ideal para documentar rapidamente a tarefa que você acabou de programar, antes de commitar.
  * **Issue de Épico/Release (`gitpr -is -ht`):** Lê o histórico completo da branch atual (Git Log + Cache de PRs). **Por que usar:** Ideal para gerar uma documentação consolidada de uma release inteira ou de uma *feature* grande que levou vários dias/commits para ser concluída.
  * **Issue Arqueológica/Dívida Técnica (`gitpr -is -b arquivo:linhas`):** Lê a linha do tempo de uma regra específica. **Por que usar:** Ideal para documentar dívidas técnicas, explicando como um bloco de código legado evoluiu e por que precisa ser refatorado.
* `-h` ou `--help`: Mostra a ajuda geral com todas as opções. Use em conjunto com outra flag para **ajuda contextual** (ex: `gitpr -h --issue`, `gitpr -h --linter`) com link direto para a documentação detalhada de cada funcionalidade.
* `-u` ou `--update`: Verifica e instala a versão mais recente do GitPR (Auto-Updater).
* `-h` ou `--help`: Exibe o menu de ajuda.

> **⚙️ Nota Técnica (--hook):** O GitPR possui uma flag oculta `--hook <arquivo>` que é acionada exclusivamente pelo sistema de Git Hooks em background. Ela permite que a IA injete a mensagem sugerida diretamente no arquivo temporário do Git, sem poluir o seu terminal.

## 🛡️ Linter Local (Análise Estática)

O GitPR CLI permite que você defina regras rígidas que serão validadas instantaneamente durante o `--review` ou `--fullreview`, sem depender da IA. Isso é ideal para evitar que erros comuns (como `console.log` ou IPs de teste) cheguem ao repositório.

### Como configurar o `.gitpr.linter.yml`:
Ao rodar `gitpr --skill`, um modelo será gerado. Você pode configurar regras usando Expressões Regulares (Regex):

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensões que serão validadas
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # O que procurar
    message: "🚨 Uso de localhost detectado no arquivo {file_name}"
    ignore_comments: true # Ignora se a linha estiver comentada
    ignore_paths: # Pastas ou arquivos ignorados (aceita *)
      - "vendor/*"
      - "node_modules/*"
```

O Linter analisa apenas as **linhas adicionadas** no seu `git diff`, garantindo uma execução focada e extremamente rápida. Se houver violações, elas aparecerão com destaque no topo do seu arquivo de revisão.

## 🧠 Arquitetura Multi-Model (Agnóstico de IA)

O GitPR não está preso a uma única Inteligência Artificial. Durante a configuração inicial, o utilizador pode escolher o seu motor padrão. Atualmente suportamos:
* **Google Gemini** (Padrão: `gemini-2.5-flash`)
* **DeepSeek** (Padrão: `deepseek-chat`)

Pode alternar dinamicamente os modelos configurando as variáveis `GEMINI_API_MODEL` ou `DEEPSEEK_API_MODEL` no seu arquivo `~/.gitpr/.env`, ou alternar em tempo real usando a flag `--provider`.

## 🎯 Sistema de "Skills" Customizáveis (Prompt Engineering)

Em vez de esconder as instruções da IA no código fonte, o GitPR utiliza arquivos Markdown locais que atuam como *System Instructions*. Ao rodar `gitpr -s`, os seguintes arquivos são gerados na raiz do seu projeto para poder customizar a "persona" da IA de acordo com as regras de negócio da sua empresa:

* `.gitpr.commit.md`: Regras para geração das mensagens curtas de commit.
* `.gitpr.pr.md`: Estrutura de tópicos exigida para a descrição do Pull Request.
* `.gitpr.review.md`: Define o foco de arquitetura (ex: SOLID, Clean Code) para a análise de diffs.
* `.gitpr.filereview.md`: Define regras rígidas de coesão e acoplamento para auditoria de um ficheiro completo (usado com `--input`).
* `.gitpr.issue.md`: Define a estrutura e o nível de detalhe exigido para a geração de Issues padronizadas (usado com `--issue`).
* `.gitpr.blame.md`: Define o foco da análise arqueológica para o rastreamento de código legado (usado com `--blame`).

## 📚 Documentação Técnica e Guias Avançados

Para manter este README conciso, detalhamos as implementações mais avançadas e focadas em **DevOps** e **Integração Contínua** em documentos separados. 

Se você deseja implementar o GitPR como uma barreira de qualidade automatizada na sua equipe, consulte os guias abaixo:

* [**Git Hooks Locais (Shift-Left)**](docs/git-hooks-locais.md): Como usar o `gitpr --installhooks` para criar travas na máquina do desenvolvedor e usar a IA para escrever mensagens de commit automaticamente.
* [**Linter Estático Customizável**](docs/linter-regras-customizadas.md): Como criar regras de validação no `.gitpr.linter.yml` para CI/CD e hooks de pre-commit.
* [**Geração de Issues e Interface TUI**](docs/issue-tui-help.md): Como utilizar a interface gráfica de terminal (TUI) e os 3 motores de contexto para gerir Issues estruturadas.
* [**Code Review com IA**](docs/code-review-ia.md): Guia dos modos de revisão (`--review`, `--fullreview`) e auditoria de arquivo (`--input`).
* [**Mensagens de Commit com IA**](docs/commit-message-ia.md): Como gerar mensagens no padrão Conventional Commits e integrar com Git Hooks.
* [**Arqueólogo de Código (Git Blame)**](docs/blame-arqueologo.md): Como rastrear a origem de regras de negócio com `git blame` e IA.
* [**Sistema de Skills e Templates**](docs/skill-template.md): Como customizar o comportamento da IA com arquivos `.gitpr.*.md`.
* [**Auto-Updater**](docs/auto-update.md): Como funciona a atualização automática (hot-swap) do GitPR.
* [**Provedores de IA**](docs/providers-ia.md): Configuração e seleção entre Google Gemini e DeepSeek.
* [**Pull Request (Modo Padrão)**](docs/pr-descricao-padrao.md): Fluxo completo de geração de descrição de PR sem flags.
* [**Integração com CI/CD (GitHub Actions)**](docs/github-ci-linter.md): Como rodar o GitPR no pipeline para travar o "Merge" de PRs com violações.
* [**Integração e Segurança do Token GitHub (PAT)**](docs/github-pat-integration.md): Entenda como o GitPR gera issues diretamente no repositório de forma autenticada.

## ⚡ Sistema de Cache Local (Economia de Quota)

O GitPR possui um motor inteligente de cache baseado em **MD5**. Sempre que você rodar um comando (`--review`, `--commit`, etc.), a ferramenta gera um hash exato do seu código atual (diff) e das instruções. 
Se você rodar o mesmo comando novamente sem ter alterado o código, o GitPR intercepta a requisição e devolve o resultado instantaneamente (em milissegundos) a partir da pasta `~/.gitpr/cache/prompts/`, poupando seu tempo e suas cotas da API do Gemini!

## 🔄 Auto-Updater (Atualização Over-The-Air)

Nunca mais se preocupe em baixar novas versões manualmente. O GitPR possui um Guardião de Conexão e um atualizador embutido:
* Ele verifica a disponibilidade de rede antes de iniciar para não travar seu fluxo offline.
* Em cada execução, ele verifica silenciosamente se há um novo release oficial na API do GitHub.
* Você pode forçar a busca e instalação rodando `gitpr --update` ou `gitpr -u`.
* A ferramenta utiliza a técnica de *Hot-Swap*, baixando o novo `.exe` e substituindo a versão antiga de forma transparente.

## Publicar no PyPi

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 Como Contribuir**

Contribuições são muito bem-vindas! Para contribuir:

1. Faça um Fork do projeto.  
2. Crie uma branch para a sua *feature* (git checkout \-b feature/NovaFuncionalidade).  
3. Faça o commit das suas alterações (git commit \-m 'feat: adiciona nova funcionalidade'). Sugestão: Use o próprio GitPR para gerar esta mensagem! 😄  
4. Faça o Push para a branch (git push origin feature/NovaFuncionalidade).  
5. Abra um Pull Request.

## **✨ Agradecimentos e Autoria**

Projeto idealizado e desenvolvido por:

**Natan Fiuza** \- [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 Licença**

Este projeto está licenciado sob a **GNU Lesser General Public License v2.1 (LGPL-2.1)**. Consulte o arquivo LICENSE para mais detalhes.