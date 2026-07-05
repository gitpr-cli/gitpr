### 🛠️ Mapa de Substituição (`help_screen.py`)

Abaixo está a lista exata das linhas que devem ser alteradas no arquivo:

| Linha Aprox. | Linha Original (Português)                                             | Nova Linha (Inglês com `__()`)                                                 |
| ------------ | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `25`         | `yield Static("💡 Ajuda do GitPR Issue", classes="help_title")`         | `yield Static(__("💡 GitPR Issue Help"), classes="help_title")`                 |
| `27`         | `"• F1 (Ajuda): Exibe este modal de instruções.\n"`                    | `__("• F1 (Help): Displays this instruction modal.\n") +`                      |
| `28`         | `"• F2 (Salvar Local): Gera um arquivo Markdown (.md) com a issue.\n"` | `__("• F2 (Save Local): Generates a Markdown (.md) file with the issue.\n") +` |
| `29`         | `"• F3 (Criar no GitHub): Cria a issue remotamente via API.\n"`        | `__("• F3 (Create on GitHub): Creates the issue remotely via API.\n") +`       |
| `30`         | `"• Esc (Sair): Fecha o aplicativo sem salvar.\n\n"`                   | `__("• Esc (Exit): Closes the application without saving.\n\n") +`             |
| `31`         | `"📚 Leia o guia completo de utilização da interface TUI:\n"`           | `__("📚 Read the complete TUI interface usage guide:\n") +`                     |
| `32`         | `+ help_url,`                                                          | `help_url,` *(Mantém igual, é apenas a variável concatenada ao bloco acima)*   |
| `34`         | `yield Button("Entendi", variant="primary", id="close_help")`          | `yield Button(__("Got it"), variant="primary", id="close_help")`               |
