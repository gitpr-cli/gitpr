# **GitPR CLI 🚀**

GitPR CLI is a command-line automation tool that uses **Google Gemini** and **DeepSeek** artificial intelligence to analyze your code changes (git diff) or entire files. The tool automatically generates commit messages in the *Conventional Commits* standard, detailed Pull Request descriptions, and deep Code Reviews aimed at reducing technical debt.

## **🛠️ Technologies and Libraries Used**

This project was developed in Python and uses the following main libraries:

* [**Click**](https://click.palletsprojects.com/): To create a robust and user-friendly command-line interface (CLI).
* [**Google GenAI**](https://pypi.org/project/google-genai/): Official SDK for direct integration with the Gemini API.
* [**OpenAI**](https://pypi.org/project/openai/): Library used due to its full compatibility with the powerful **DeepSeek** API.
* [**Python-dotenv**](https://pypi.org/project/python-dotenv/): For secure environment variable management.
* [**Pytest**](https://docs.pytest.org/): For running unit tests in a simple, colorful, and readable way in the console.
* [**Cryptography**](https://cryptography.io/): To ensure your `GEMINI_API_KEY` is stored encrypted and securely on disk.
* [**PyYAML**](https://pyyaml.org/): Used to read and process the custom static analysis rules from the `.gitpr.linter.yml` file.
* [**Textual**](https://textual.textualize.io/): Powerful library for creating Terminal Graphical Interfaces (TUI), used in the interactive issue generation and editing panel.
* [**Requests**](https://pypi.org/project/requests/): Elegant and robust library for HTTP requests, used to communicate with the GitHub REST API.

----

## 📦 How to Compile the Executable Locally

If you want to generate your own binary from the source code, we use **PyInstaller**. Make sure you are in the project root directory with the virtual environment configured.

1. Install development dependencies (if you haven't already):
   ```bash
   pipenv install --dev
   ```

2. Run the build command pointing to our entry point (`run.py`):
   ```bash
   pipenv run pyinstaller --noconfirm --onefile --icon=icon.ico --name gitpr run.py
   ```
> **Technical note:** The `--onefile` flag ensures all Python, libraries, and dependencies are compressed into a single binary, while `--paths src` helps the compiler find our `core.py` and `config.py` files. 🛠️

After running this command, PyInstaller will create some folders (`build` and `dist`).
Your final ready-to-use file will be inside the **`dist/`** folder named `gitpr` (or `gitpr.exe` on Windows).


----

## 🧪 Running Tests

To ensure the Git capture logic and AI integration are working correctly, we use unit tests.

1. Install test dependencies (if you haven't already):
   ```bash
   pipenv install --dev pytest
   ```

2. Run the tests with the command:
   ```bash
   pipenv run pytest -v
   ```
Pytest will automatically detect files inside the `tests/` folder and display a detailed execution report.

----
## **⚙️ Installation and Configuration**

### **Using the Executable (Recommended)**

1. Download the gitpr executable file from the "Releases" tab on GitHub.
2. Move the executable to a folder that is in your PATH (e.g.: /usr/local/bin on Linux/Mac or your user folder on Windows).
3. On the first run, the wizard will guide you:
   ```bash
   $ gitpr
   ```
```bash
🚀 Intelligent PR Automation with AI

🔧 First run detected! Let's configure GitPR CLI.

🔑 Enter your GEMINI_API_KEY:

📄 Default output filename pattern [{branch}_{datetime}_PR_DESC.md]:
```
*Note: Your configuration will be securely saved in the `~/.gitpr/.env` file.*

> **🔒 Security Note:** GitPR CLI uses symmetric encryption (Fernet). Your API key is stored as a hash in the `.env` file, and the master key for decryption is automatically generated in `~/.gitpr/secret.key`. **Never share your secret.key file.**

### From Source Code

1. Clone the repository: `git clone https://github.com/natanfiuza/gitpr.git`

2. Enter the folder: `cd gitpr`

3. Set up the environment:
```bash
pipenv install google-genai openai python-dotenv click cryptography
```
4. Run: pipenv run python src/main.py

## **💻 How to Use**

GitPR has a powerful default behavior and several advanced options to assist you in your day-to-day as a developer.

### **Default Behavior (Pull Request)**
Simply run the bare command in your terminal:
```bash
gitpr
```
The tool will sync with the remote (`git fetch`), compare your changes with the remote main branch (e.g.: `origin/main`), and generate a Markdown file (e.g.: `feature-login_20260421110134_PR_DESC.md`) at the root of your project with the complete suggestion for your Pull Request.

### **Advanced Options and Commands**
You can pass the following *flags* for specific actions:

* `-c` or `--commit`: Runs a local `git diff` and displays **only the suggested commit message**.
* `-r` or `--review`: Performs a detailed **Code Review** of local changes.
* `-f` or `--fullreview`: Performs a **Full Code Review** analyzing all changes since the remote branch.
* `-i <file>` or `--input <file>`: **Full File Audit.** Must be used together with `-r` or `-f`; it ignores git history and does a Code Review of the entire file. Excellent for acting as a consultant on legacy code refactoring.
* `--provider <gemini|deepseek|ollama>`: Força o uso de uma IA específica apenas para esta execução, ignorando o padrão salvo no `.env`.
* `--lang <codigo>`: Força o idioma da interface para esta execução (ex.: `en_us`, `pt_br`). Sobrescreve o `GITPR_LANG` do `.env` sem persistir a alteração.
* `-ch` ou `--chat`: Abre o **Chat Interativo de Pair Programming** — um terminal TUI onde a IA enxerga seu diff atual e mantém uma conversa contextual. Possui memória por branch, comandos slash (`/explain`, `/tests`, `/optimize`, `/clear`), auto-patching (F5), atualização de diff (F2) e exportação de sessão (F6).
* `-l` or `--linter`: Runs **only the local static linter** (no AI calls). Ideal for use in CI/CD pipelines to block non-compliant code.
* `-ih` or `--installhooks`: Automatically installs **local Git Hooks** (`pre-commit` and `prepare-commit-msg`) in your repository.
* `-s` or `--skill`: Creates the AI context template files (`.gitpr.commit.md`, `.gitpr.pr.md`, `.gitpr.review.md`, `.gitpr.filereview.md`, `.gitpr.issue.md`, `.gitpr.blame.md`) and the Linter (`.gitpr.linter.yml`) at the project root.
* `-is` or `--issue`: Automatically generates a draft of a **standardized Issue** and opens an interactive interface (TUI) for editing or direct submission via REST API. This feature has **3 context engines** depending on the command combination:
  * **New Code Issue (`gitpr -is`):** Reads the current `git diff`. **Why use:** Ideal for quickly documenting the task you just finished programming, before committing.
  * **Epic/Release Issue (`gitpr -is -ht`):** Reads the full history of the current branch (Git Log + PR Cache). **Why use:** Ideal for generating consolidated documentation of an entire release or a large *feature* that took several days/commits to complete.
  * **Archaeological/Technical Debt Issue (`gitpr -is -b file:lines`):** Reads the timeline of a specific business rule. **Why use:** Ideal for documenting technical debt, explaining how a legacy code block evolved and why it needs to be refactored.
* `-h` or `--help`: Shows the general help with all options. Use together with another flag for **contextual help** (e.g.: `gitpr -h --issue`, `gitpr -h --linter`) with a direct link to the detailed documentation of each feature.
* `-u` or `--update`: Checks and installs the latest version of GitPR (Auto-Updater).

> **⚙️ Technical Note (--hook):** GitPR has a hidden flag `--hook <file>` that is triggered exclusively by the Git Hooks system in the background. It allows the AI to inject the suggested message directly into Git's temporary file, without cluttering your terminal.

## 🛡️ Local Linter (Static Analysis)

GitPR CLI allows you to define strict rules that will be validated instantly during `--review` or `--fullreview`, without depending on AI. This is ideal for preventing common errors (like `console.log` or test IPs) from reaching the repository.

### How to configure `.gitpr.linter.yml`:
When running `gitpr --skill`, a template will be generated. You can configure rules using Regular Expressions (Regex):

```yaml
rules:
  - name: "check-localhost"
    extensions: ["js", "php"] # Extensions to be validated
    regex: 'http(s)?://(localhost|127\.0\.0\.1)' # What to look for
    message: "🚨 Localhost usage detected in file {file_name}"
    ignore_comments: true # Ignores if the line is commented
    ignore_paths: # Folders or files ignored (accepts *)
      - "vendor/*"
      - "node_modules/*"
```

The Linter analyzes only the **added lines** in your `git diff`, ensuring a focused and extremely fast execution. If there are violations, they will appear highlighted at the top of your review file.

## 🧠 Multi-Model Architecture (AI-Agnostic)

GitPR is not tied to a single Artificial Intelligence. During initial setup, the user can choose their default engine. We currently support:
* **Google Gemini** (Default: `gemini-2.5-flash`)
* **DeepSeek** (Default: `deepseek-chat`)
* **Ollama** (Local) — execute modelos localmente sem internet, totalmente compatível com o formato da API OpenAI

You can dynamically switch models by configuring the `GEMINI_API_MODEL` or `DEEPSEEK_API_MODEL` variables in your `~/.gitpr/.env` file, or switch in real-time using the `--provider` flag.

## 🎯 Customizable "Skills" System (Prompt Engineering)

Instead of hiding AI instructions in the source code, GitPR uses local Markdown files that act as *System Instructions*. When running `gitpr -s`, the following files are generated at the root of your project to customize the AI's "persona" according to your company's business rules:

* `.gitpr.commit.md`: Rules for generating short commit messages.
* `.gitpr.pr.md`: Required topic structure for the Pull Request description.
* `.gitpr.review.md`: Defines the architectural focus (e.g.: SOLID, Clean Code) for diff analysis.
* `.gitpr.filereview.md`: Defines strict cohesion and coupling rules for full file auditing (used with `--input`).
* `.gitpr.issue.md`: Defines the structure and level of detail required for generating standardized Issues (used with `--issue`).
* `.gitpr.blame.md`: Defines the focus of archaeological analysis for legacy code tracing (used with `--blame`).

## 🌐 Internacionalização (i18n)

O GitPR detecta automaticamente o idioma do seu sistema e exibe as mensagens no seu idioma nativo. O sistema i18n é inspirado no **helper `__()` do Laravel**:

* **Detecção automática:** Na primeira execução, o GitPR detecta o idioma do SO e salva em `~/.gitpr/.env` (`GITPR_LANG`).
* **Arquivos de tradução:** Os pacotes de idioma são baixados automaticamente do repositório oficial para `~/.gitpr/langs/`.
* **Fallback em inglês:** Se uma tradução estiver faltando, o texto em inglês é exibido diretamente.
* **API do desenvolvedor:** Use `from src.i18n import __` e envolva todas as strings de interface com `__("Seu texto aqui")`.
* **Placeholders:** Suporta parâmetros nomeados — `__("Baixando {file}...", file="template.md")`.

Para forçar um idioma específico, defina `GITPR_LANG=pt_br` ou `GITPR_LANG=en` no `~/.gitpr/.env`.

> 📖 **Guia completo do desenvolvedor:** [docs/i18n_explanation.pt_br.md](docs/i18n_explanation.pt_br.md) — arquitetura, padrões de uso, precauções com import circular e como adicionar novos idiomas.

## 📚 Documentação Técnica e Guias Avançados

Para manter este README conciso, detalhamos as implementações mais avançadas focadas em **DevOps** e **Integração Contínua** em documentos separados.

Se você deseja implementar o GitPR como uma barreira de qualidade automatizada em sua equipe, confira os guias abaixo.

> 🌐 Cada guia está disponível em **5 idiomas** — adicione `.pt_br`, `.pt_pt`, `.fr_fr` ou `.es_es` antes da extensão `.md` para versões traduzidas (ex.: `docs/understanding_chat_functionality.pt_br.md`). Inglês é o padrão sem sufixo.

### Chat e Recursos Interativos

* [**🧠 Chat Interativo (Pair Programming)**](https://github.com/natanfiuza/gitpr/blob/main/docs/understanding_chat_functionality.md) — Como usar o chat com IA com memória, comandos slash, auto-patch e exportação de sessão.

### DevOps & CI/CD

* [**Git Hooks Locais (Shift-Left)**](https://github.com/natanfiuza/gitpr/blob/main/docs/git-hooks-locais.md) — Como usar `gitpr --installhooks` para criar barreiras de qualidade na máquina do desenvolvedor e usar IA para gerar mensagens de commit automaticamente.
* [**Linter Estático Customizável**](https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md) — Como criar regras de validação no `.gitpr.linter.yml` para CI/CD e hooks de pre-commit.
* [**Integração CI/CD (GitHub Actions)**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-ci-linter.md) — Como executar o GitPR no pipeline para bloquear "Merge" de PRs com violações.

### Funcionalidades Principais

* [**Pull Request (Modo Padrão)**](https://github.com/natanfiuza/gitpr/blob/main/docs/pr-descricao-padrao.md) — Fluxo completo para gerar descrições de PR sem flags.
* [**Code Review com IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/code-review-ia.md) — Guia dos modos de review (`--review`, `--fullreview`) e auditoria de arquivos (`--input`).
* [**Mensagens de Commit com IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/commit-message-ia.md) — Como gerar mensagens no padrão Conventional Commits e integrar com Git Hooks.
* [**Geração de Issues e Interface TUI**](https://github.com/natanfiuza/gitpr/blob/main/docs/issue-tui-help.md) — Como usar a interface gráfica de terminal (TUI) e os 3 motores de contexto para gerenciar Issues estruturadas.
* [**Arqueólogo de Código (Git Blame)**](https://github.com/natanfiuza/gitpr/blob/main/docs/blame-arqueologo.md) — Como rastrear a origem de regras de negócio com `git blame` e IA.
* [**Sistema de Skills e Templates**](https://github.com/natanfiuza/gitpr/blob/main/docs/skill-template.md) — Como personalizar o comportamento da IA com arquivos `.gitpr.*.md`.

### Configuração e Infraestrutura

* [**Provedores de IA**](https://github.com/natanfiuza/gitpr/blob/main/docs/providers-ia.md) — Configuração e seleção entre Google Gemini, DeepSeek e Ollama.
* [**Auto-Updater**](https://github.com/natanfiuza/gitpr/blob/main/docs/auto-update.md) — Como funciona a atualização automática (hot-swap) do GitPR.
* [**Token GitHub (PAT) — Integração e Segurança**](https://github.com/natanfiuza/gitpr/blob/main/docs/github-pat-integration.md) — Entenda como o GitPR cria issues diretamente no repositório com autenticação.
* [**Internacionalização (i18n)**](https://github.com/natanfiuza/gitpr/blob/main/docs/i18n_explanation.md) — Arquitetura, padrões de uso e como adicionar novos idiomas.

## ⚡ Local Cache System (Quota Savings)

GitPR has an intelligent **MD5**-based cache engine. Whenever you run a command (`--review`, `--commit`, etc.), the tool generates an exact hash of your current code (diff) and instructions.
If you run the same command again without changing the code, GitPR intercepts the request and returns the result instantly (in milliseconds) from the `~/.gitpr/cache/prompts/` folder, saving you time and your Gemini API quotas!

## 🔄 Auto-Updater (Over-The-Air Update)

Never worry about manually downloading new versions again. GitPR has a Connection Guardian and a built-in updater:
* It checks network availability before starting so it doesn't block your offline workflow.
* On each execution, it silently checks if there is a new official release on the GitHub API.
* You can force the check and installation by running `gitpr --update` or `gitpr -u`.
* The tool uses the *Hot-Swap* technique, downloading the new `.exe` and transparently replacing the old version.

## Publishing to PyPI

```bash
pipenv run python -m build
pipenv run twine upload dist/*
```
## **🤝 How to Contribute**

Contributions are very welcome! To contribute:

1. Fork the project.
2. Create a branch for your *feature* (git checkout -b feature/NewFeature).
3. Commit your changes (git commit -m 'feat: add new feature'). Tip: Use GitPR itself to generate this message! 😄
4. Push to the branch (git push origin feature/NewFeature).
5. Open a Pull Request.

## **✨ Acknowledgments and Authorship**

Project conceived and developed by:

**Natan Fiuza** - [contato@natanfiuza.dev.br](mailto:contato@natanfiuza.dev.br)

## **📄 License**

This project is licensed under the **GNU Lesser General Public License v2.1 (LGPL-2.1)**. See the LICENSE file for more details.
