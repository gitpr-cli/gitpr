# 📋 Plano de Desenvolvimento: Bridge para Linters Externos (Checkstyle)

* [ ] **Fase 1: Configuração e Infraestrutura (`src/config.py`)**
* Adicionar a variável `OUTPUT_FILE_NAME_LINTER` com valor padrão `{branch}_{datetime}_LINTER.md` no dicionário `DEFAULT_CONFIG`.
* Mapear a nova variável no `_OUTPUT_FOLDER_MAP` do `src/core.py` para a pasta `linter`.


* [ ] **Fase 2: Extensão do YAML e Execução Segura (`src/linter_engine.py`)**
* Atualizar a leitura do `.gitpr.linter.yml` para suportar o nó `external_linters` (esperando chaves como `name`, `command`, `extensions`).
* Implementar uma função que execute o `command` via `subprocess` em background, capturando o `stdout` contendo o XML (mesmo que o exit code seja 1).


* [ ] **Fase 3: Parser Checkstyle e Mapeamento de Diff (`src/linter_engine.py`)**
* Criar um parser de XML (`xml.etree.ElementTree`) para extrair os erros do padrão Checkstyle.
* Implementar a matemática de cruzamento: garantir que os erros extraídos do XML só sejam contabilizados se a linha e o arquivo coincidirem com as linhas adicionadas (`+`) no git diff atual.


* [ ] **Fase 4: Geração de Relatórios e TUI (`src/main.py` e `src/linter_engine.py`)**
* Unificar os erros do regex interno com os do linter externo em uma única lista de `errors` e `warnings`.
* Sempre gerar e salvar o relatório formatado em Markdown na pasta `.gitpr/reports/linter/`.
* Exibir a TUI de erro apenas se houver *errors* impeditivos E o comando estiver rodando fora de hooks (ex: via flag explícita manual).


* [ ] **Fase 5: Assistente Interativo de Instalação (`src/main.py` ou novo `src/ui/linter_wizard.py`)**
* Criar um comando CLI (ex: `gitpr --linter-setup`) que pergunta qual linter configurar (PHPCS, ESLint, Stylelint).
* Exibir as instruções de instalação nativa para o usuário (ex: `npm install -g eslint`) e gerar automaticamente o bloco no `.gitpr.linter.yml` do projeto.


* [ ] **Fase 6: Atualização da Documentação (`docs/linter-regras-customizadas.md`)**
* Adicionar exemplos de como plugar ESLint, PHPCS e outros.
* Explicar a nova variável de ambiente `OUTPUT_FILE_NAME_LINTER` e como usar o assistente interativo.
* Sincronize com os outros idiomas suportados

* [ ]  **Fase 7: Aplicar o i18n** 
* Aplique a função i18n.__() em todos os textos que são exibidos para o usuário
* Adicione os textos como chaves nos arquivos json dos idiomas devidamente traduzidos

* [ ] **Fase 8: relatório da tarefa**
* Implemente a regra do relatorio final

---

## Fase 1 


Concluir a Fase 1 , injetando as configurações que vão definir onde nossos relatórios serão salvos. Faça as alterações abaixo para criarmos a rota segura para a pasta `linter`.

**1. Atualizando as configurações padrão:**

```python
# Arquivo: src/config.py
# Onde alterar: Dentro do dicionário DEFAULT_CONFIG, adicione a nova chave no final[cite: 10].

# DE:
    "GITPR_SKIP_UNSTAGED_CHECK": "false",
    "PR_PUBLISH_LOG": "true",
    "GITPR_AUTO_MERGE": "false"
}

def get_skill_dir():

# PARA:
    "GITPR_SKIP_UNSTAGED_CHECK": "false",
    "PR_PUBLISH_LOG": "true",
    "GITPR_AUTO_MERGE": "false",
    "OUTPUT_FILE_NAME_LINTER": "{branch}_{datetime}_LINTER.md"
}

def get_skill_dir():

```

**2. Mapeando a pasta de saída:**

```python
# Arquivo: src/core.py
# Onde alterar: Adicione a chave no dicionário _OUTPUT_FOLDER_MAP[cite: 11].

# DE:
_OUTPUT_FOLDER_MAP = {
    "OUTPUT_FILE_NAME": "pr_desc",
    "OUTPUT_FILE_NAME_REVIEW": "review",
    "OUTPUT_FILE_NAME_FULLREVIEW": "full_review",
    "OUTPUT_FILE_NAME_FILEREVIEW": "file_review",
    "OUTPUT_FILE_NAME_BLAME": "blame",
    "OUTPUT_FILE_NAME_ISSUE": "issue",
}

def resolve_output_path(env_var, default_pattern, safe_branch_name, current_time):

# PARA:
_OUTPUT_FOLDER_MAP = {
    "OUTPUT_FILE_NAME": "pr_desc",
    "OUTPUT_FILE_NAME_REVIEW": "review",
    "OUTPUT_FILE_NAME_FULLREVIEW": "full_review",
    "OUTPUT_FILE_NAME_FILEREVIEW": "file_review",
    "OUTPUT_FILE_NAME_BLAME": "blame",
    "OUTPUT_FILE_NAME_ISSUE": "issue",
    "OUTPUT_FILE_NAME_LINTER": "linter",
}

def resolve_output_path(env_var, default_pattern, safe_branch_name, current_time):

```

Com essas duas adições simples, nosso motor `resolve_output_path` já sabe automaticamente que, ao usarmos a chave do linter, ele deve criar a pasta `.gitpr/reports/linter/` e salvar o Markdown lá dentro.

## Fase 2


Prepare a base no motor atual injetando a função de subprocessos que executará o comando do linter externo em background, capturando a saída XML de forma segura (Fase 2). 

Aplique estas alterações cirúrgicas no seu arquivo `src/linter_engine.py`:

**1. Adicione as bibliotecas nativas de sistema nos imports:**

```python
# DE:
import re
import fnmatch
from src.config import load_linter_rules

# PARA:
import re
import fnmatch
import subprocess
import os
from src.config import load_linter_rules

```

**2. Crie a função executora logo acima de `parse_diff_and_lint`:**

```python
# DE:
    except re.error as e:
        alerts["errors"].append(__("Rule '{rule_name}' contains invalid Regex: {error}", rule_name=rule.get('name'), error=str(e)))

def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):

# PARA:
    except re.error as e:
        alerts["errors"].append(__("Rule '{rule_name}' contains invalid Regex: {error}", rule_name=rule.get('name'), error=str(e)))

def _run_external_linter(command, file_path):
    """Executes an external linter command and returns its stdout (Checkstyle XML)."""
    try:
        # Resolve o comando injetando o arquivo alvo
        full_command = f"{command} \"{file_path}\""
        
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        # Retornamos o stdout independente do exit code (linters retornam > 0 quando acham erros)
        return result.stdout
    except Exception as e:
        return ""

def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):

```

A estratégia de não travar a aplicação baseada no *exit code* (já que o linter retorna erro nativamente quando detecta problemas).

---

## Fase 3

Para a Fase 3, vamos implementar o parser de XML e a matemática de diff para garantir que apenas as linhas que você alterou no commit gerem alertas. Para isso, extrairemos a configuração dos linters externos do YAML e injetaremos a validação cruzada no final da varredura do motor.

Faça as seguintes alterações cirúrgicas nos arquivos:

**1. Extraindo as configurações externas (`src/config.py`):**
Adicione esta nova função logo abaixo da função `load_linter_rules()`.

```python
# Onde alterar: Logo após o return rules da load_linter_rules()

# INCLUIR:
def load_external_linters():
    """
    Loads external linter configurations (name, command, extensions) 
    from local project and global plugins.
    """
    external_linters = []

    # 1. Load Local Project External Linters
    local_path = resolve_skill_path(".gitpr.linter.yml")
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "external_linters" in config:
                    external_linters.extend(config.get("external_linters", []))
        except Exception:
            pass

    # 2. Load Global Plugin External Linters
    for plugin_file in get_linter_plugins():
        try:
            with open(plugin_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "external_linters" in config:
                    external_linters.extend(config.get("external_linters", []))
        except Exception:
            pass

    return external_linters

```

**2. Importando as novas dependências (`src/linter_engine.py`):**

```python
# DE:
import re
import fnmatch
import subprocess
import os
from src.config import load_linter_rules

# PARA:
import re
import fnmatch
import subprocess
import os
import xml.etree.ElementTree as ET
from src.config import load_linter_rules, load_external_linters

```

**3. Criando o Parser XML e preparando o mapeamento (`src/linter_engine.py`):**
Adicione a função de parser de Checkstyle logo após `_run_external_linter`.

```python
# DE:
        # Retornamos o stdout independente do exit code (linters retornam > 0 quando acham erros)
        return result.stdout
    except Exception as e:
        return ""

def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):

# PARA:
        # Retornamos o stdout independente do exit code (linters retornam > 0 quando acham erros)
        return result.stdout
    except Exception as e:
        return ""

def _parse_checkstyle_xml(xml_content):
    """Extracts errors from Checkstyle XML into a dictionary list."""
    results = []
    if not xml_content or not xml_content.strip():
        return results

    try:
        root = ET.fromstring(xml_content)
        for file_node in root.findall('file'):
            for error_node in file_node.findall('error'):
                results.append({
                    'line': int(error_node.get('line', 0)),
                    'severity': error_node.get('severity', 'error').lower(),
                    'message': error_node.get('message', '')
                })
    except ET.ParseError:
        pass
    return results

def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):

```

**4. Mapeando as linhas alteradas e rodando o Linter Externo (`src/linter_engine.py`):**
Vamos modificar o `STANDARD GIT DIFF MODE` para guardar as linhas adicionadas e cruzar com os erros do XML ao final do loop.

```python
# DE:
    # ==========================================
    # STANDARD GIT DIFF MODE
    # ==========================================
    current_file = None
    file_extension = None
    line_number = 0
    
    for line in lines:
        if line.startswith('+++ b/'):
            current_file = line[6:]
            file_extension = current_file.split('.')[-1] if '.' in current_file else ''
            line_number = 0 
            continue

        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                line_number = int(match.group(1)) - 1
            continue

        if line.startswith('+') and not line.startswith('+++'):
            line_number += 1
            code_line = line[1:].strip()

            if not current_file or not code_line:
                continue

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="diff")
    return alerts

# PARA:
    # ==========================================
    # STANDARD GIT DIFF MODE
    # ==========================================
    modified_files = {}
    current_file = None
    file_extension = None
    line_number = 0
    
    for line in lines:
        if line.startswith('+++ b/'):
            current_file = line[6:]
            file_extension = current_file.split('.')[-1] if '.' in current_file else ''
            line_number = 0 
            if current_file not in modified_files:
                modified_files[current_file] = []
            continue

        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                line_number = int(match.group(1)) - 1
            continue

        if line.startswith('+') and not line.startswith('+++'):
            line_number += 1
            code_line = line[1:].strip()

            if not current_file or not code_line:
                continue

            modified_files[current_file].append(line_number)

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    # Cross-reference with External Linters
    external_configs = load_external_linters()
    if external_configs and modified_files:
        for f_path, modified_lines in modified_files.items():
            f_ext = f_path.split('.')[-1] if '.' in f_path else ''
            
            for ext_linter in external_configs:
                if f_ext not in ext_linter.get('extensions', []):
                    continue
                
                xml_output = _run_external_linter(ext_linter['command'], f_path)
                ext_errors = _parse_checkstyle_xml(xml_output)
                
                for err in ext_errors:
                    if err['line'] in modified_lines:
                        msg = f"🚨 [{ext_linter['name']}] {err['message']} ({f_path}, Linha {err['line']})"
                        if err['severity'] == 'warning':
                            alerts["warnings"].append(msg)
                        else:
                            alerts["errors"].append(msg)

    log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="diff")
    return alerts

```

Usando o dicionário `modified_files`, guardamos apenas as linhas que estão sendo manipuladas no commit atual, e o laço final ignora solenemente qualquer erro legado que o Checkstyle cuspir de outras linhas! 


## Fase 5

Chegamos na Fase 4! Nossa missão agora é gerar o relatório consolidado em Markdown e exibir a nossa nova TUI estritamente quando rodarmos o comando fora de ambientes *headless* (como os hooks).

Vamos fazer as implementações cirúrgicas abaixo para não quebrarmos a estabilidade do fluxo de *auto-commit*. 🚀

**1. Crie o novo arquivo da TUI (`src/ui/linter_app.py`):**

Este aplicativo Textual cuidará de exibir os erros críticos na tela caso a flag manual seja acionada.

```python
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Horizontal
from textual.widgets import Header, Footer, Label, Button
from src.i18n import __

class LinterApp(App):
    """TUI for displaying Linter errors."""
    CSS = """
    Screen { background: $surface; }
    .alert-container { margin: 1 2; }
    .error-text { color: red; text-style: bold; }
    .warning-text { color: yellow; }
    #btn-container { align: center bottom; margin-top: 2; height: 3; }
    """
    
    BINDINGS = [
        ("q", "quit", __("Quit")),
    ]

    def __init__(self, alerts):
        super().__init__()
        self.alerts = alerts

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(classes="alert-container"):
            if self.alerts["errors"]:
                yield Label(__("❌ Critical Errors:"), classes="error-text")
                for err in self.alerts["errors"]:
                    yield Label(f"  - {err}", classes="error-text")
                yield Label("")
            
            if self.alerts["warnings"]:
                yield Label(__("⚠️ Warnings:"), classes="warning-text")
                for warn in self.alerts["warnings"]:
                    yield Label(f"  - {warn}", classes="warning-text")
                    
        with Horizontal(id="btn-container"):
            yield Button(__("Acknowledge & Exit"), variant="error", id="btn_exit")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_exit":
            self.exit(1)

```

**2. Adicione o gerador de Markdown no final de `src/linter_engine.py`:**

```python
# Onde alterar: Adicione no final do arquivo src/linter_engine.py

def generate_linter_report_content(alerts):
    """Generates the Markdown content for the linter report."""
    content = __("# 🚨 GitPR Linter Report\n\n")
    if not alerts["errors"] and not alerts["warnings"]:
        content += __("✅ No violations found.\n")
        return content
    
    if alerts["errors"]:
        content += __("## ❌ Errors\n\n")
        for err in alerts["errors"]:
            content += f"- {err}\n"
        content += "\n"
        
    if alerts["warnings"]:
        content += __("## ⚠️ Warnings\n\n")
        for warn in alerts["warnings"]:
            content += f"- {warn}\n"
            
    return content

```

**3. Atualize o fluxo CLI principal (`src/main.py`):**
Vamos plugar a lógica de salvamento e proteção de hook substituindo apenas o bloco responsável pela flag `--linter`.

```python
# Onde alterar: Arquivo src/main.py, substituindo TODO o bloco `if linter:`

# DE:
    if linter:
        diff_text = get_git_diff()
        
        if not diff_text or not diff_text.strip():
            if not quiet: click.secho(__("✅ Nothing to validate (empty diff)."), fg="green")
            return

        linter_results = parse_diff_and_lint(diff_text)
        
        has_warnings = len(linter_results["warnings"]) > 0
        has_errors = len(linter_results["errors"]) > 0
        
        # ... (código existente de print e saída) ...
        
        # Fire-and-forget linter metric
        from src.metrics import log_command_metric
        log_command_metric(
            command="linter",
            status="error" if has_errors else "success",
            linter_errors=len(linter_results.get("errors", [])),
            linter_warnings=len(linter_results.get("warnings", [])),
        )
        return

# PARA:
    if linter:
        diff_text = get_git_diff()
        
        if not diff_text or not diff_text.strip():
            if not quiet: click.secho(__("✅ Nothing to validate (empty diff)."), fg="green")
            return

        linter_results = parse_diff_and_lint(diff_text)
        has_warnings = len(linter_results["warnings"]) > 0
        has_errors = len(linter_results["errors"]) > 0

        # 1. Generate and save the Markdown report
        from src.linter_engine import generate_linter_report_content
        branch_name = get_current_branch()
        safe_branch_name = branch_name.replace("/", "-").replace("\\", "-")
        current_time = datetime.now().strftime("%Y%m%d%H%M%S")
        
        report_path = resolve_output_path(
            "OUTPUT_FILE_NAME_LINTER",
            "{branch}_{datetime}_LINTER.md",
            safe_branch_name,
            current_time
        )
        
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(generate_linter_report_content(linter_results))
            if not quiet:
                click.secho(__("📄 Linter report saved to: {path}", path=report_path), fg="blue", dim=True)
        except Exception as e:
            click.secho(__("❌ Error saving linter report: {error}", error=str(e)), fg="red")

        from src.metrics import log_command_metric
        log_command_metric(
            command="linter",
            status="error" if has_errors else "success",
            linter_errors=len(linter_results.get("errors", [])),
            linter_warnings=len(linter_results.get("warnings", [])),
        )

        # 2. Display TUI if there are blocking errors and NOT in a hook/quiet mode
        if has_errors:
            if not quiet and not hook:
                from src.ui.linter_app import LinterApp
                app = LinterApp(alerts=linter_results)
                app.run()
            else:
                # Segurança para hooks: apenas print no terminal
                click.secho(__("\n🚨 Validation failed! Found {count} critical error(s):", count=len(linter_results['errors'])), fg="red", bold=True)
                for alert in linter_results["errors"]:
                    click.echo(f"  - {alert}")
            sys.exit(1)

        # 3. Warning processing
        if has_warnings and not quiet:
            click.secho(__("\n⚠️ The Linter generated {count} best practice warning(s):", count=len(linter_results['warnings'])), fg="yellow", bold=True)
            for alert in linter_results["warnings"]:
                click.echo(f"  - {alert}")
            click.secho(__("\n✅ Code approved with warnings. The commit will proceed."), fg="green")
        elif not quiet: 
            click.secho(__("\n✅ Clean code! No violations found by the local Linter."), fg="green", bold=True)

        return

```

## Fase 5


Chegamos à Fase 5, onde vamos criar o assistente interativo para plugar linters externos (como PHPCS e ESLint) com facilidade. Para mantermos a arquitetura limpa e seguirmos o Princípio de Responsabilidade Única (SOLID), proponho criarmos um novo arquivo dedicado que fará as perguntas ao desenvolvedor e injetará a configuração automaticamente no arquivo `.gitpr.linter.yml`.

Crie o novo arquivo abaixo na sua estrutura:

**1. Novo arquivo: `src/linter_wizard.py**`

```python
import os
import yaml
import click
from src.config import resolve_skill_path
from src.i18n import __

# Dicionário com os presets dos linters mais comuns
_LINTER_PRESETS = {
    "1": {
        "name": "PHP_CodeSniffer (PHPCS)",
        "extensions": ["php"],
        "command": "vendor/bin/phpcs --report=checkstyle",
        "install_msg": "composer require --dev squizlabs/php_codesniffer"
    },
    "2": {
        "name": "ESLint (JavaScript/TypeScript)",
        "extensions": ["js", "ts", "vue", "jsx", "tsx"],
        "command": "npx eslint --format checkstyle",
        "install_msg": "npm install --save-dev eslint"
    },
    "3": {
        "name": "Stylelint (CSS/SCSS)",
        "extensions": ["css", "scss", "sass", "less", "vue"],
        "command": "npx stylelint --custom-formatter=node_modules/stylelint-checkstyle-formatter",
        "install_msg": "npm install --save-dev stylelint stylelint-checkstyle-formatter"
    }
}

def run_linter_setup_wizard():
    """
    Executa o assistente interativo para configurar linters externos via CLI.
    """
    click.secho(__("\n🔌 GitPR External Linter Setup"), fg="cyan", bold=True)
    click.echo(__("Choose an external linter to configure as a bridge (Checkstyle XML format):"))
    
    for key, data in _LINTER_PRESETS.items():
        click.echo(f"  [{key}] {data['name']}")
        
    click.echo(__("  [0] Cancel"))
    
    choice = click.prompt(__("Select an option"), type=click.Choice(["0", "1", "2", "3"]))
    
    if choice == "0":
        click.secho(__("❌ Setup cancelled."), fg="yellow")
        return
        
    selected_linter = _LINTER_PRESETS[choice]
    
    # Exibe instrução de instalação nativa
    click.secho(__("\n🛠️  Step 1: Install the linter in your project"), fg="yellow", bold=True)
    click.echo(__("Run the following command in your terminal if you haven't installed it yet:"))
    click.secho(f"  {selected_linter['install_msg']}\n", fg="green")
    
    # Atualiza o arquivo YAML
    click.secho(__("⚙️  Step 2: Configuring .gitpr.linter.yml"), fg="yellow", bold=True)
    local_path = resolve_skill_path(".gitpr.linter.yml")
    
    config = {}
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            click.secho(__("❌ Error reading current linter config: {error}", error=str(e)), fg="red")
            return
            
    if "external_linters" not in config:
        config["external_linters"] = []
        
    # Verifica se já existe para evitar duplicatas
    already_exists = any(l.get("name") == selected_linter["name"] for l in config["external_linters"])
    
    if already_exists:
        click.secho(__("⚠️  The linter '{name}' is already configured.", name=selected_linter["name"]), fg="yellow")
    else:
        new_entry = {
            "name": selected_linter["name"],
            "command": selected_linter["command"],
            "extensions": selected_linter["extensions"]
        }
        config["external_linters"].append(new_entry)
        
        try:
            with open(local_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            click.secho(__("✅ Successfully added '{name}' to your configuration!", name=selected_linter["name"]), fg="green", bold=True)
        except Exception as e:
            click.secho(__("❌ Error saving configuration: {error}", error=str(e)), fg="red")

```

Esse novo arquivo gerencia as opções de forma clara, exibe o comando nativo que o usuário deve rodar (`npm`, `composer`, etc.) e faz o *merge* da configuração dentro da chave `external_linters` do nosso YAML.

### Atenção nova implemantação nesta etapa

- [ ] Utilize _LINTER_PRESETS como fallbacks, crie o arquivo em templates/ para que sejam importados do repositorio e salvos em ~/.gitpr/conf  implemente esta funcionalidade com isso sera possivel implementar novos linters externos quando quisermos ou quando o usuario queser, anote isso para adicionar a documentação.


### Plugar o assitente interativo

Vamos plugar o nosso assistente interativo diretamente na artéria principal do CLI, facilitando a vida de quem for configurar essas ferramentas externas. Para isso, vamos injetar a nova flag `--linter-setup` no arquivo `src/main.py`.

Faça as alterações cirúrgicas abaixo no seu `src/main.py`:

**1. Adicione a flag no mapa de ajuda e nas prioridades:**

```python
# Onde alterar: No final dos dicionários HELP_MAP e HELP_PRIORITY

# DE:
    'no-unstaged-check': {
        'url': get_doc_url('git-status.md'),
        'title': __('Skip Unstaged Check (--no-unstaged-check)'),
        'description': __('Skips the unstaged-files verification that runs before PR, commit, review, full review and issue generation. Equivalent to GITPR_SKIP_UNSTAGED_CHECK=true for one run.'),
    },
}

# Priority for contextual help when multiple flags are used with -h
# Lower value = higher priority
HELP_PRIORITY: dict[str, int] = {
    # ... (linhas anteriores)
    'plugins': 18,
    'status': 19,
    'no-unstaged-check': 20,
}

# PARA:
    'no-unstaged-check': {
        'url': get_doc_url('git-status.md'),
        'title': __('Skip Unstaged Check (--no-unstaged-check)'),
        'description': __('Skips the unstaged-files verification that runs before PR, commit, review, full review and issue generation. Equivalent to GITPR_SKIP_UNSTAGED_CHECK=true for one run.'),
    },
    'linter-setup': {
        'url': get_doc_url('linter-regras-customizadas.md'),
        'title': __('External Linter Wizard (--linter-setup)'),
        'description': __('Interactive wizard to configure external linters (ESLint, PHPCS, etc.) via Checkstyle XML integration.'),
    },
}

# Priority for contextual help when multiple flags are used with -h
# Lower value = higher priority
HELP_PRIORITY: dict[str, int] = {
    # ... (linhas anteriores)
    'plugins': 18,
    'status': 19,
    'no-unstaged-check': 20,
    'linter-setup': 21,
}

```

**2. Adicione a opção no decorador Click e na assinatura da função:**

```python
# Onde alterar: Nas definições do @click.option acima da função def cli(...)

# DE:
@click.option('--no-unstaged-check', is_flag=True, help=__("Skips the unstaged files verification before AI processing."))
@click.option('-h', '--help', 'help_flag', is_flag=True, help=__("Shows this message and exits. Use with another flag for contextual help (e.g., -h --issue)."))
def cli(commit, review, fullreview, linter, skill, update, installhooks, install, hook, quiet, pre_save, provider, input, blame, history, issue, chat, help_flag, lang, mcp, metrics, export, purge, hook_event, show_dashboard, base, no_publish, no_edit, plugins, status, no_unstaged_check):

# PARA:
@click.option('--no-unstaged-check', is_flag=True, help=__("Skips the unstaged files verification before AI processing."))
@click.option('--linter-setup', is_flag=True, help=__("Interactive wizard to configure external linters (ESLint, PHPCS, etc)."))
@click.option('-h', '--help', 'help_flag', is_flag=True, help=__("Shows this message and exits. Use with another flag for contextual help (e.g., -h --issue)."))
def cli(commit, review, fullreview, linter, skill, update, installhooks, install, hook, quiet, pre_save, provider, input, blame, history, issue, chat, help_flag, lang, mcp, metrics, export, purge, hook_event, show_dashboard, base, no_publish, no_edit, plugins, status, no_unstaged_check, linter_setup):

```

**3. Injete a lógica de execução:**

```python
# Onde alterar: Logo após o bloco do assistente de instalação (`if install:`) e antes do `--skill`

# DE:
    # --install option: Interactive setup wizard
    if install:
        run_install_wizard()
        from src.metrics import log_command_metric
        log_command_metric(command="install", status="success", provider="git")
        return

    # --skill option: Generate template and exit
    if skill:

# PARA:
    # --install option: Interactive setup wizard
    if install:
        run_install_wizard()
        from src.metrics import log_command_metric
        log_command_metric(command="install", status="success", provider="git")
        return

    # --linter-setup option: External linter wizard
    if linter_setup:
        from src.linter_wizard import run_linter_setup_wizard
        run_linter_setup_wizard()
        return

    # --skill option: Generate template and exit
    if skill:

```

Pronto! Nossa CLI já entende e despacha a configuração. 


## Fase 6

Vamos fechar nossa implementação com chave de ouro nesta Fase 6, atualizando a documentação técnica para a comunidade. Assim, todos saberão como plugar o ESLint ou PHPCS de forma nativa e como gerenciar os relatórios gerados.

Faça as inclusões cirúrgicas abaixo no seu arquivo `docs/linter-regras-customizadas.pt_br.md`:

**1. Atualize a Seção 2 (Estrutura do Arquivo .gitpr.linter.yml):**
Substitua o bloco de código YAML da Seção 2 para incluir a nova chave `external_linters`.

```markdown
# DE:
    ignore_paths: # Opcional: Pastas onde esta regra NÃO deve rodar  
      - "vendor/*"  
    require_paths: # Opcional: Pastas exclusivas onde esta regra DEVE rodar  
      - "routes/*"

# PARA:
    ignore_paths: # Opcional: Pastas onde esta regra NÃO deve rodar  
      - "vendor/*"  
    require_paths: # Opcional: Pastas exclusivas onde esta regra DEVE rodar  
      - "routes/*"

external_linters:
  - name: "ESLint (JavaScript/TypeScript)"
    extensions: ["js", "ts", "vue", "jsx", "tsx"]
    command: "npx eslint --format checkstyle"

```

**2. Adicione as novas seções de Linters Externos e Relatórios no final do arquivo:**
Vá até o final do documento (logo após a Seção 4) e adicione:

```markdown
# ADICIONAR NO FINAL DO ARQUIVO:

## **5. Integração com Linters Externos (Bridge via Checkstyle)**

O GitPR CLI não precisa reinventar a roda. Se o seu projeto já usa ferramentas como PHP_CodeSniffer, ESLint ou Stylelint, o GitPR pode atuar como uma ponte, executando essas ferramentas em background e filtrando os erros **apenas para as linhas que você alterou no seu Pull Request atual**.

Para isso, o linter externo precisa suportar a saída de relatórios no formato `checkstyle` (padrão universal em CI/CD).

### **Como Configurar Rapidamente (--linter-setup)**
Em vez de configurar o YAML manualmente, você pode usar nosso assistente interativo:
Execute no terminal:
`gitpr --linter-setup`

O assistente exibirá opções pré-configuradas, orientará você sobre o comando de instalação no seu projeto (ex: `npm install --save-dev eslint`) e injetará a configuração correta automaticamente no seu `.gitpr.linter.yml`.

---

## **6. Relatórios de Análise (Markdown)**

Toda vez que o linter rodar (seja manualmente via `--linter` ou automaticamente antes do commit via `--no-edit`), ele irá consolidar os erros gerados pelas Regras de Regex e pelos Linters Externos em um relatório único.

Este relatório formatado em Markdown será salvo automaticamente, mantendo um histórico das suas auditorias locais. 

**Localização Padrão:** `.gitpr/reports/linter/`

**Customização:** Você pode alterar o nome e a pasta deste arquivo definindo a variável `OUTPUT_FILE_NAME_LINTER` no seu arquivo `~/.gitpr/.env`.

```

E com isso, o nosso motor de ponte para linters externos (Bridge) + Assistente Interativo + Geração de Relatórios está oficialmente concluído! O que achou do resultado final dessa nossa jornada arquitetural? Tem mais alguma nova funcionalidade que gostaria de atacar agora? 🚀


