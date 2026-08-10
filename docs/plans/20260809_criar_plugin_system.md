# 📋 Plano de Desenvolvimento: Sistema de Plugins (Linter e Prompts)

* [ ] **Fase 1: Infraestrutura e Descoberta (`src/config.py`)**
* **Objetivo:** Preparar o ambiente para suportar diretórios de plugins.
* **Ações:**
* Modificar `setup_environment` ou criar função dedicada para garantir a existência de `~/.gitpr/plugins/linter/` e `~/.gitpr/plugins/prompts/`.
* Criar funções de leitura de diretório (`get_linter_plugins()`, `get_prompt_plugins()`) que retornem as rotas dos arquivos `.yml` e `.md` encontrados.




* [ ] **Fase 2: Extensibilidade do Linter (`src/config.py` ou `src/linter_engine.py`)**
* **Objetivo:** Unificar as regras do projeto local com as regras globais dos plugins.
* **Ações:**
* Alterar a função `load_linter_rules()` para ler o arquivo local e, em seguida, iterar sobre todos os arquivos `.yml` de `plugins/linter/`.
* Concatenar as listas de regras em tempo de execução, garantindo um bloco `try/except` silencioso para ignorar YAMLs mal formatados sem quebrar o CLI.




* [ ] **Fase 3: Extensibilidade de Prompts no MCP (`src/mcp_server.py`)**
* **Objetivo:** Registrar os prompts customizados para que IDEs (Cursor, VS Code) possam utilizá-los.
* **Ações:**
* No bloco de inicialização do MCP, varrer `plugins/prompts/*.md`.
* Registrar dinamicamente cada arquivo como um recurso (ex: `prompt://plugin/nome_do_arquivo`) e como uma Tool MCP, estendendo os hardcoded que já temos.




* [ ] **Fase 4: Gerenciamento via CLI (`src/main.py`)**
* **Objetivo:** Dar visibilidade ao usuário sobre o que está carregado.
* **Ações:**
* Adicionar um subcomando ou flag `--plugins` para listar os plugins ativos (ex: "3 pacotes de linter carregados, 2 prompts customizados").

---

## Explicação e possiveis usos

### 1. Diferença entre `.gitpr.linter.yml` (Local) e `~/.gitpr/plugins/linter/` (Global/Plugin)

O arquivo `.gitpr.linter.yml` é **específico do projeto**, ideal para regras que só fazem sentido naquele repositório (ex: padrões de nomenclatura daquele cliente) e que devem ser versionadas junto com o código.
Já a pasta `~/.gitpr/plugins/linter/` é **global na máquina do desenvolvedor**. Ela permite que você crie pacotes de regras que se aplicarão automaticamente a *todos* os repositórios que você auditar, sem precisar copiar o arquivo `.yml` para cada projeto.

### 2. Possíveis Usos para Plugins de Linter

Ao usar plugins globais, você pode criar "Packs" de validação separados por arquivo:

* **Security Pack (`security.yml`):** Bloquear globalmente chaves da AWS (`AKIA...`), tokens JWT, ou senhas hardcoded em qualquer projeto.
* **Debug Preventer (`no-debug.yml`):** Regras que impedem commits com `console.log`, `var_dump()`, `dd()` ou `print()` esquecidos.
* **Language Packs (`php-psr.yml`, `vue-rules.yml`):** Regras específicas de sintaxe que você carrega apenas se trabalhar com essas linguagens, garantindo que todo projeto seu siga a PSR ou o Vue Style Guide.

### 3. Possíveis Usos para Plugins de Prompts

Permite que o desenvolvedor crie novos comandos para a IA ler o código com objetivos muito específicos:

* **Auditoria de Segurança (`prompt://audit_security`):** Um prompt focado exclusivamente em caçar vulnerabilidades (SQL Injection, XSS) no diff.
* **Gerador de Testes (`prompt://generate_phpunit`):** Um template rigoroso que instrui a IA a gerar testes unitários no padrão da sua equipe.
* **Tradução para Negócios (`prompt://explain_to_business`):** Transforma o diff em um resumo não-técnico para enviar a Product Managers.
* **Revisor de Arquitetura SOLID (`prompt://solid_check`):** Força a IA a focar apenas em acoplamento, coesão e ferimento de princípios SOLID no código.

## Fase 2 e 3

Vamos implementar a **Fase 1** (Infraestrutura) e a **Fase 2** (Linter Global) diretamente no seu `src/config.py`. As alterações vão criar a estrutura de pastas na máquina do usuário e consolidar as regras locais e globais em tempo de execução de forma segura.

Abaixo estão as alterações cirúrgicas necessárias:

**1. Adicione a criação das pastas na função `setup_environment`:**

```python
# Localize a função setup_environment() e adicione a criação dos diretórios globais de plugins:

# DE:
def setup_environment():
    """Ensures that encryption keys, the default provider, and the API key are configured."""
    # Ensure the global folder exists
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)

    # Call the existing function in security.py to ensure the master key exists

# PARA:
def setup_environment():
    """Ensures that encryption keys, the default provider, and the API key are configured."""
    # Ensure the global folder exists
    os.makedirs(os.path.dirname(ENV_FILE), exist_ok=True)
    
    # Create global plugin directories
    os.makedirs(os.path.join(os.path.dirname(ENV_FILE), "plugins", "linter"), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(ENV_FILE), "plugins", "prompts"), exist_ok=True)

    # Call the existing function in security.py to ensure the master key exists

```

**2. Crie as funções de descoberta de plugins antes do `load_linter_rules`:**

```python
# Adicione este bloco inteiro LOGO ACIMA da função load_linter_rules():

def get_plugin_dir(plugin_type):
    """Returns the absolute path to the global plugin directory."""
    return os.path.join(os.path.dirname(ENV_FILE), "plugins", plugin_type)

def get_linter_plugins():
    """Returns a list of all global linter plugin .yml files."""
    linter_dir = get_plugin_dir("linter")
    if not os.path.exists(linter_dir):
        return []
    return [os.path.join(linter_dir, f) for f in os.listdir(linter_dir) if f.endswith(('.yml', '.yaml'))]

def get_prompt_plugins():
    """Returns a list of all global prompt plugin .md files."""
    prompt_dir = get_plugin_dir("prompts")
    if not os.path.exists(prompt_dir):
        return []
    return [os.path.join(prompt_dir, f) for f in os.listdir(prompt_dir) if f.endswith('.md')]

```

**3. Refatore a função `load_linter_rules` para concatenar os plugins globais:**

```python
# Substitua a função load_linter_rules() inteira pela nova versão que agrega plugins:

# DE:
def load_linter_rules():
    """
    Loads the static linter rules from the .gitpr.linter.yml file.
    Returns a list of rules or an empty list if the file does not exist.
    """
    file_path = resolve_skill_path(".gitpr.linter.yml")

    # If the file does not exist in the project, it's not an error. There are simply no rules to apply.
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Return the list of rules or empty if the file is blank
        if not config or "rules" not in config:
            return []

        return config.get("rules", [])

    except yaml.YAMLError as e:
        # If the user makes an indentation or quote error, warn without crashing the terminal
        click.secho(__("\n❌ Syntax error in .gitpr.linter.yml file:\n{error}", error=str(e)), fg="red")
        return []
    except Exception as e:
        click.secho(__("\n❌ Unexpected error reading linter rules: {error}", error=str(e)), fg="red")
        return []

# PARA:
def load_linter_rules():
    """
    Loads the static linter rules from the local project and global plugins.
    Returns a combined list of rules.
    """
    rules = []

    # 1. Load Local Project Rules
    local_path = resolve_skill_path(".gitpr.linter.yml")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "rules" in config:
                    rules.extend(config.get("rules", []))
        except yaml.YAMLError as e:
            click.secho(__("\n❌ Syntax error in local .gitpr.linter.yml file:\n{error}", error=str(e)), fg="red")
        except Exception as e:
            click.secho(__("\n❌ Unexpected error reading local linter rules: {error}", error=str(e)), fg="red")

    # 2. Load Global Plugin Rules
    for plugin_file in get_linter_plugins():
        try:
            with open(plugin_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "rules" in config:
                    rules.extend(config.get("rules", []))
        except Exception as e:
            # Silently skip malformed global plugins so we don't break the main flow
            click.secho(__("⚠️ Warning: Could not load linter plugin {file} ({error})", file=os.path.basename(plugin_file), error=str(e)), fg="yellow")

    return rules

```

Observe que mantive a resiliência no carregamento: se um plugin global tiver um erro de formatação, exibimos apenas um `Warning` amarelo e o processo de commit/review continua rodando normalmente. 🛡️


---

## Fase 3

A mágica aqui é fazer o SDK do MCP (FastMCP) reconhecer dinamicamente os plugins sem precisarmos dar *hardcode* em cada um deles. Para isso, vamos alterar a listagem nativa de prompts e criar um laço de repetição (factory) que carrega e anota os `.md` dos plugins no servidor no momento da inicialização.

Aplique as duas modificações abaixo no seu `src/mcp_server.py`:

**1. Localize a função `list_prompts` e modifique-a para incluir os plugins na listagem:**

```python
# DE:
@mcp.resource(
    uri="prompt://list",
    name=__("Available Prompt Templates"),
    description=__("Lists all available MCP prompt template URIs."),
    mime_type="application/json",
)
def list_prompts() -> str:
    """Return a JSON list of available prompt resource URIs."""
    return json.dumps({
        "prompts": [f"prompt://{name}" for name in PROMPT_FILES],
    })

# PARA:
@mcp.resource(
    uri="prompt://list",
    name=__("Available Prompt Templates"),
    description=__("Lists all available MCP prompt template URIs."),
    mime_type="application/json",
)
def list_prompts() -> str:
    """Return a JSON list of available prompt resource URIs."""
    prompts = [f"prompt://{name}" for name in PROMPT_FILES]
    
    try:
        from src.config import get_prompt_plugins
        import os
        for plugin_path in get_prompt_plugins():
            plugin_name = os.path.basename(plugin_path).replace('.md', '')
            prompts.append(f"prompt://plugin/{plugin_name}")
    except Exception:
        pass

    return json.dumps({
        "prompts": prompts,
    })

```

**2. Vá até o final da sessão de Prompts (logo após a função `explore_project_prompt` e ANTES do bloco `MCP Config Installer`) e adicione o registrador dinâmico:**

```python
# DE:
@mcp.prompt(
    name=__("Explore Project Context"),
    description=__("Get current branch info, repository name, and list available "
                    "skill templates for the project."),
)
def explore_project_prompt() -> str:
    """Prompt: explore the current git context and available skills."""
    return _read_prompt_file("explore")


# =============================================================================
# MCP Config Installer (gitpr-mcp --install <editor>)
# =============================================================================

# PARA:
@mcp.prompt(
    name=__("Explore Project Context"),
    description=__("Get current branch info, repository name, and list available "
                    "skill templates for the project."),
)
def explore_project_prompt() -> str:
    """Prompt: explore the current git context and available skills."""
    return _read_prompt_file("explore")


def _register_plugin_prompts():
    """Dynamically registers custom user prompts from plugins folder as MCP resources and prompts."""
    try:
        from src.config import get_prompt_plugins
        import os
        
        for plugin_path in get_prompt_plugins():
            plugin_name = os.path.basename(plugin_path).replace('.md', '')
            uri_string = f"prompt://plugin/{plugin_name}"
            
            # Using closures to prevent late-binding issues in loops
            def make_resource_handler(path, uri, name):
                @mcp.resource(
                    uri=uri,
                    name=f"Plugin: {name}",
                    description=f"Custom plugin prompt: {name}",
                    mime_type="text/markdown",
                )
                def resource_handler() -> str:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception:
                        return ""
                return resource_handler
            
            def make_prompt_handler(path, name):
                @mcp.prompt(
                    name=f"Plugin: {name}",
                    description=f"Custom AI prompt loaded from plugins: {name}",
                )
                def prompt_handler() -> str:
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except Exception:
                        return ""
                return prompt_handler
                
            make_resource_handler(plugin_path, uri_string, plugin_name)
            make_prompt_handler(plugin_path, plugin_name)
            
    except Exception:
        pass  # Silently skip if plugins fail to load so the MCP server boots normally

# Fire the dynamic registration immediately
_register_plugin_prompts()


# =============================================================================
# MCP Config Installer (gitpr-mcp --install <editor>)
# =============================================================================

```

> 🧠 **Por que a Factory Function (`make_resource_handler`)?**
> Em Python, se colocarmos os decoradores diretamente dentro do loop `for`, devido ao escopo e *late-binding*, todas as funções MCP criadas acabariam apontando para o *último* arquivo do loop. Ao isolar a criação numa função `make_...`, congelamos o contexto e garantimos que cada plugin aponte exatamente para o seu arquivo correspondente.

Faça a implementação e verifique se as IDEs já conseguem enxergar os arquivos colocados na pasta `~/.gitpr/plugins/prompts/`. 

---

## Fase 4

Olá, Natan! Aqui é o Seu Zé. Chegamos na reta final da nossa implementação do sistema de plugins. 🚀

Vamos adicionar a flag `--plugins` no nosso `src/main.py` para que os desenvolvedores possam auditar facilmente quais extensões globais estão ativas.

Faça as seguintes alterações cirúrgicas no seu arquivo `src/main.py`:

**1. Adicione a flag no mapa de ajuda contextual (`HELP_MAP`) e nas prioridades (`HELP_PRIORITY`):**

```python
# Localize o dicionário HELP_MAP e adicione a chave 'plugins' no final:

# DE:
    'no-edit': {
        'url': get_doc_url('pull-request-publication.md'),
        'title': __('Direct Publish with Auto-Commit (--no-edit)'),
        'description': __('Generates the PR, auto-commits pending changes (with lint validation), and publishes directly to GitHub without opening the TUI.'),
    },
}

# Priority for contextual help when multiple flags are used with -h

# PARA:
    'no-edit': {
        'url': get_doc_url('pull-request-publication.md'),
        'title': __('Direct Publish with Auto-Commit (--no-edit)'),
        'description': __('Generates the PR, auto-commits pending changes (with lint validation), and publishes directly to GitHub without opening the TUI.'),
    },
    'plugins': {
        'url': get_doc_url('plugins-system.md'),
        'title': __('Plugin System (--plugins)'),
        'description': __('Lists all globally installed custom linter packs and MCP prompts loaded from ~/.gitpr/plugins/.'),
    },
}

# Priority for contextual help when multiple flags are used with -h

```

```python
# Localize o dicionário HELP_PRIORITY e adicione a prioridade para 'plugins':

# DE:
    'metrics': 15,
    'no-publish': 16,
    'no-edit': 17,
}

# PARA:
    'metrics': 15,
    'no-publish': 16,
    'no-edit': 17,
    'plugins': 18,
}

```

**2. Adicione a flag no decorador do Click e na assinatura da função `cli`:**

```python
# Localize as marcações @click.option antes de 'def cli(...):'

# DE:
@click.option('--no-publish', is_flag=True, help=__("Saves the PR file locally without opening the interactive publisher."))
@click.option('--no-edit', is_flag=True, help=__("Skips the interactive editor and publishes the Pull Request directly (with auto-commit)."))
@click.option('-h', '--help', 'help_flag', is_flag=True, help=__("Shows this message and exits. Use with another flag for contextual help (e.g., -h --issue)."))
def cli(commit, review, fullreview, linter, skill, update, installhooks, install, hook, quiet, pre_save, provider, input, blame, history, issue, chat, help_flag, lang, mcp, metrics, export, purge, hook_event, show_dashboard, base, no_publish, no_edit):

# PARA:
@click.option('--no-publish', is_flag=True, help=__("Saves the PR file locally without opening the interactive publisher."))
@click.option('--no-edit', is_flag=True, help=__("Skips the interactive editor and publishes the Pull Request directly (with auto-commit)."))
@click.option('--plugins', is_flag=True, help=__("Lists all active global plugins (linters and prompts)."))
@click.option('-h', '--help', 'help_flag', is_flag=True, help=__("Shows this message and exits. Use with another flag for contextual help (e.g., -h --issue)."))
def cli(commit, review, fullreview, linter, skill, update, installhooks, install, hook, quiet, pre_save, provider, input, blame, history, issue, chat, help_flag, lang, mcp, metrics, export, purge, hook_event, show_dashboard, base, no_publish, no_edit, plugins):

```

**3. Injete a lógica de execução logo após o bloco do servidor MCP (`if mcp:`):**

```python
# Localize o final do bloco do MCP (linha ~262) e adicione o manipulador de plugins:

# DE:
    if mcp:
        from src.mcp_server import main as mcp_main
        mcp_main()
        return

    # Silencia o banner se estiver no modo quiet ou via hook
    if not quiet and not hook:
        print_banner()

# PARA:
    if mcp:
        from src.mcp_server import main as mcp_main
        mcp_main()
        return

    if plugins:
        from src.config import get_linter_plugins, get_prompt_plugins
        linter_plugins = get_linter_plugins()
        prompt_plugins = get_prompt_plugins()

        click.secho(__("\n🧩 GitPR Plugin System"), fg="cyan", bold=True)
        
        click.secho(__("\n🔍 Linter Packs ({count}):", count=len(linter_plugins)), fg="yellow", bold=True)
        if linter_plugins:
            for p in linter_plugins:
                click.echo(f"  - {os.path.basename(p)}")
        else:
            click.echo(__("  No global linter plugins installed."))

        click.secho(__("\n💬 Custom Prompts ({count}):", count=len(prompt_plugins)), fg="yellow", bold=True)
        if prompt_plugins:
            for p in prompt_plugins:
                click.echo(f"  - {os.path.basename(p)}")
        else:
            click.echo(__("  No global prompt plugins installed."))
        
        click.secho(f"\n💡 {__('Plugin directory:')} ~/.gitpr/plugins/", dim=True)
        return

    # Silencia o banner se estiver no modo quiet ou via hook
    if not quiet and not hook:
        print_banner()

```

*(Não se esqueça de adicionar as novas traduções ao seu arquivo `langs/pt_br.json` caso queira manter a interface 100% traduzida!)*

E com isso finalizamos o nosso sistema de Plugins Globais (Fase 4 concluída com sucesso)! Comandos desacoplados, limpos e prontos para uso. 

## Testes

Crie testes para esta nova implementação

## Documentação

Crie um arquivo em docs/ para esta nova funcionalidade de plugins. ( lembre-se dos outros idiomas )
Adicione ao README.md esta nova funcionalidade, lembrando de criar para os outros idiomas. 