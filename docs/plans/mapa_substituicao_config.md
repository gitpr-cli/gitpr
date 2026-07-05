### 🛠️ Mapa de Substituição (`src/config.py`)

Abaixo está a lista exata das linhas que devem ser alteradas no arquivo:

| Função      | Linha Original (Português)                                                                                   | Nova Linha (Inglês com `__()`)                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `setup_...` | `click.secho("🤖 Bem-vindo ao GitPR! Vamos configurar o seu motor de IA.", fg="cyan", bold=True)`             | `click.secho(__("🤖 Welcome to GitPR! Let's configure your AI engine."), fg="cyan", bold=True)`                      |
| `setup_...` | `"Qual inteligência artificial deseja utilizar como padrão?",`                                               | `__("Which artificial intelligence do you want to use as default?"),`                                               |
| `setup_...` | `click.secho(f"🔑 Chave de API do {provider.capitalize()} não encontrada.", fg="yellow")`                     | `click.secho(__("🔑 API Key for {provider} not found.", provider=provider.capitalize()), fg="yellow")`               |
| `setup_...` | `raw_key = click.prompt(f"Cole aqui a sua chave de API do {provider.capitalize()}", hide_input=True)`        | `raw_key = click.prompt(__("Paste your {provider} API key here", provider=provider.capitalize()), hide_input=True)` |
| `setup_...` | `click.secho("✅ Chave guardada com segurança em disco (Encriptada)!", fg="green")`                           | `click.secho(__("✅ Key safely stored on disk (Encrypted)!"), fg="green")`                                           |
| `check_...` | `click.secho("\n❌ Erro: Sem conexão com a internet.", fg="red", bold=True)`                                  | `click.secho(__("\n❌ Error: No internet connection."), fg="red", bold=True)`                                        |
| `check_...` | `click.secho("O GitPR precisa de acesso à rede para consultar a IA e verificar atualizações.", fg="yellow")` | `click.secho(__("GitPR needs network access to query the AI and check for updates."), fg="yellow")`                 |
| `check_...` | `click.secho("Verifique sua conexão e tente novamente.\n", fg="white")`                                      | `click.secho(__("Check your connection and try again.\n"), fg="white")`                                             |
| `load_...`  | `click.secho(f"\n❌ Erro de sintaxe no arquivo .gitpr.linter.yml:\n{e}", fg="red")`                           | `click.secho(__("\n❌ Syntax error in .gitpr.linter.yml file:\n{error}", error=str(e)), fg="red")`                   |
| `load_...`  | `click.secho(f"\n❌ Erro inesperado ao ler as regras do linter: {e}", fg="red")`                              | `click.secho(__("\n❌ Unexpected error reading linter rules: {error}", error=str(e)), fg="red")`                     |
