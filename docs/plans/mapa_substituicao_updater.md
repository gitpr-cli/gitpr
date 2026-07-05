
### 🛠️ Mapa de Substituição (`src/updater.py`)

Abaixo estão as substituições. Substituí as *f-strings* originais pelo formato seguro do `__()`.

| Linha Aprox. | Linha Original (Português/Inglês fixo) | Nova Linha (Inglês com `__()`) |
| --- | --- | --- |
| `92` | `click.secho(f"[notice] A new release of gitpr is available: {__version__} -> {latest_version}", fg="yellow", dim=True)` | `click.secho(__("[notice] A new release of gitpr is available: {current_version} -> {latest_version}", current_version=__version__, latest_version=latest_version), fg="yellow", dim=True)` |
| `94` | `click.secho(f"[notice] To update, run: gitpr --update", fg="yellow", dim=True)` | `click.secho(__("[notice] To update, run: gitpr --update"), fg="yellow", dim=True)` |
| `96` | `click.secho(f"[notice] To update, run: pip install --upgrade gitpr-cli", fg="yellow", dim=True)` | `click.secho(__("[notice] To update, run: pip install --upgrade gitpr-cli"), fg="yellow", dim=True)` |
| `104` | `click.secho("💡 Como você instalou via PIP, atualize rodando: pip install --upgrade gitpr-cli", fg="cyan", bold=True)` | `click.secho(__("💡 Since you installed via PIP, update by running: pip install --upgrade gitpr-cli"), fg="cyan", bold=True)` |
| `110` | `click.secho("❌ Não foi possível verificar atualizações no momento.", fg="red")` | `click.secho(__("❌ Could not check for updates at this moment."), fg="red")` |
| `117` | `click.secho(f"\n🚀 Nova versão do GitPR encontrada (v{latest_version})!", fg="green", bold=True)` | `click.secho(__("\n🚀 New GitPR version found (v{latest_version})!", latest_version=latest_version), fg="green", bold=True)` |
| `118` | `click.secho("Baixando atualização em segundo plano...", fg="cyan")` | `click.secho(__("Downloading update in background..."), fg="cyan")` |
| `121` | `click.secho("✅ Você já está usando a versão mais recente do GitPR.", fg="green")` | `click.secho(__("✅ You are already using the latest version of GitPR."), fg="green")` |
| `132` / `159` | `click.secho(f"✅ Atualização concluída com sucesso! Na próxima execução você já usará a nova versão.\n", fg="green", bold=True)` | `click.secho(__("✅ Update successfully completed! You will use the new version on the next run.\n"), fg="green", bold=True)` |
| `134` / `163` | `click.secho(f"❌ Falha ao aplicar atualização: {e}", fg="red")` | `click.secho(__("❌ Failed to apply update: {error}", error=str(e)), fg="red")` |
| `143` | `click.secho("⚠️ Aviso: Rodando via script Python. O Auto-Update funciona apenas no executável compilado.", fg="yellow")` | `click.secho(__("⚠️ Warning: Running via Python script. Auto-Update only works on the compiled executable."), fg="yellow")` |
