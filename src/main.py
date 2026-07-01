import os
from datetime import datetime
import click
import sys

# Importações dos nossos módulos internos atualizadas
from src.config import setup_environment, check_internet_connection, get_ai_provider
from src.updater import check_and_update, __version__, print_update_notice
from src.core import (
    get_git_diff, 
    get_git_full_diff,
    get_current_branch, 
    generate_pr_content,  
    generate_skill_template,
    install_git_hooks,
    get_branch_history_text
)
from src.linter_engine import parse_diff_and_lint


def print_banner():
    """Exibe a assinatura ASCII Art do projeto"""
    banner = """
 ,----.   ,--.  ,--.  ,------. ,------.  
'  .-./   `--',-'  '-.|  .--. '|  .--. ' 
|  | .---.,--.'-.  .-'|  '--' ||  '--'.' 
'  '--'  ||  |  |  |  |  | --' |  |\  \  
 `------' `--'  `--'  `--'     `--' '--' 
                                         
"""
    click.secho(banner, fg="cyan", bold=True)
    click.secho(f"  🚀 Automação Inteligente de PRs com IA (v{__version__})", fg="yellow", bold=True)
    click.secho("  Opções: -c,--commit | -r,--review | -f,--fullreview | -l,--linter | -s,--skill | -u,--update | -ih,--installhooks | -is,--issue | -h ou --help\n", fg="white", dim=True)


# Configuração nativa do Click para aceitar -h além de --help
@click.command()
@click.help_option('-h', '--help', help='Mostra esta mensagem e sai.')
@click.option('-c', '--commit', is_flag=True, help="Gera apenas a mensagem de commit e exibe no console.")
@click.option('-r', '--review', is_flag=True, help="Faz um code review das alterações locais (git diff).")
@click.option('-f', '--fullreview', is_flag=True, help="Faz um code review de todas as alterações desde a branch principal (origin/main).")
@click.option('-l', '--linter', is_flag=True, help="Roda apenas o linter estático local (ideal para CI/CD).")
@click.option('-s', '--skill', is_flag=True, help="Gera o arquivo de template .gitpr.md na pasta atual.")
@click.option('-u', '--update', is_flag=True, help="Verifica e instala a versão mais recente do GitPR.")
@click.option('-ih', '--installhooks', is_flag=True, help="Instala automaticamente os Git Hooks de validação no projeto.")
@click.option('--hook', type=click.Path(), hidden=True, help="Caminho do arquivo de commit (uso interno dos hooks).")
@click.option('-q', '--quiet', is_flag=True, hidden=True, help="Oculta o banner e logs não essenciais (uso interno).")
@click.option('-i', '--input', type=click.Path(exists=True), help="Caminho de um arquivo específico para análise completa.")
@click.option('-b', '--blame', type=str, help="Analisa a origem de uma regra de negócio (ex: arquivo.py:10-20 ou apenas arquivo.py).")
@click.option('-ht', '--history', is_flag=True, help="Usa todo o histórico da branch (Git Log + Cache de PR) como contexto para gerar a issue.")
@click.option('-is', '--issue', is_flag=True, help="Gera uma Issue padronizada das alterações atuais e abre a interface interativa.")
@click.option('-p', '--provider', type=click.Choice(['gemini', 'deepseek']), help="Força a utilização de um provedor de IA específico nesta execução.")
def cli(commit, review, fullreview, linter, skill, update, installhooks, hook, quiet, provider, input, blame,history, issue):
    """
    GitPR CLI - Automação de PRs e Code Review com IA.

    COMPORTAMENTO PADRÃO (Sem opções):
    Faz o fetch, compara com a branch principal remota e gera um arquivo Markdown (.md) com a descrição completa para o Pull Request.
    """
    # Silencia o banner se estiver no modo quiet ou via hook
    if not quiet and not hook:
        print_banner()

    # Identifica se a ferramenta está rodando como binário (PyInstaller) ou via PIP
    is_compiled = getattr(sys, 'frozen', False)

    # Limpeza do Hot-Swap (Apenas no modo Binário)
    if is_compiled:
        old_exe = sys.executable + ".old"
        if os.path.exists(old_exe):
            try:
                os.remove(old_exe)
            except OSError:
                pass

    if linter:
        diff_text = get_git_diff()
        
        if not diff_text or not diff_text.strip():
            if not quiet: click.secho("✅ Nada para validar (diff vazio).", fg="green")
            return

        linter_results = parse_diff_and_lint(diff_text)
        
        has_warnings = len(linter_results["warnings"]) > 0
        has_errors = len(linter_results["errors"]) > 0

        # Processamento de Warnings (Apenas Avisos)
        if has_warnings:
            # Os avisos DEVEM aparecer sempre, mesmo no modo quiet
            click.secho(f"\n⚠️ O Linter gerou {len(linter_results['warnings'])} aviso(s) de boas práticas:", fg="yellow", bold=True)
            for alert in linter_results["warnings"]:
                click.echo(f"  - {alert}")

        # Processamento de Erros (Críticos, Bloqueiam o Commit)
        if has_errors:
            # Os erros DEVEM aparecer sempre, mesmo no modo quiet
            click.secho(f"\n🚨 Falha na validação! Encontrados {len(linter_results['errors'])} erro(s) críticos:", fg="red", bold=True)
            for alert in linter_results["errors"]:
                click.echo(f"  - {alert}")
            # Trava o Git apenas se houver erros críticos
            sys.exit(1)
        
        # Sucesso silencioso (Nenhum erro crítico encontrado)
        if not quiet: 
            if has_warnings:
                click.secho("\n✅ Código aprovado com avisos. O commit prosseguirá.", fg="green")
            else:
                click.secho("\n✅ Código limpo! Nenhuma violação encontrada pelo Linter local.", fg="green", bold=True)
        return

    # Guardião de Conexão (Failing Fast)
    check_internet_connection()

    # Módulo de Atualização (Pip-Aware)
    if update:    
        click.secho("🔍 Verificando atualizações...", fg="cyan")
        check_and_update()
        return

    # Opção --skill: Gera o template e encerra
    if skill:
        generate_skill_template()
        return
    
    if installhooks:
        if install_git_hooks():
            click.secho("\n✅ Git Hooks instalados com sucesso!", fg="green", bold=True)
            click.echo("O Linter será agora executado automaticamente antes de cada commit.")
            
            click.echo("\n---")
            click.echo("📚 Guias de Utilização:")
            
            # Link da documentação geral de Hooks
            click.echo("• Como utilizar Git Hooks:")
            click.secho("  https://github.com/natanfiuza/gitpr/blob/main/docs/git-hooks-locais.md", fg="blue")
            
            # Novo link: Documentação de Regras Customizadas
            click.echo("• Como criar novas regras de Linter (.gitpr.linter.yml):")
            click.secho("  https://github.com/natanfiuza/gitpr/blob/main/docs/linter-regras-customizadas.md", fg="blue")
            click.echo("---\n")
        return
    
    # Módulo Arqueólogo (--blame)
    if blame and not issue:
        # Parser para separar o arquivo das linhas
        if ":" in blame:
            # Modo Direto: gitpr --blame arquivo:10-20
            file_path, lines = blame.split(":", 1)
            try:
                if "-" in lines:
                    start_line, end_line = lines.split("-")
                else:
                    start_line = end_line = lines
            except ValueError:
                click.secho("❌ Formato de linhas inválido. Use inicio-fim (ex: 10-20).", fg="red")
                return
        else:
            # Modo Interativo: gitpr --blame arquivo
            file_path = blame
            if not os.path.exists(file_path):
                click.secho(f"❌ O arquivo '{file_path}' não foi encontrado.", fg="red")
                return
            
            click.secho(f"📂 Arquivo selecionado: {file_path}", fg="cyan", bold=True)
            lines_input = click.prompt("Quais linhas você deseja investigar? (Ex: 10-20 ou apenas 45)")
            
            if "-" in lines_input:
                start_line, end_line = lines_input.split("-")
            else:
                start_line = end_line = lines_input
        
        # Validação final do arquivo
        if not os.path.exists(file_path):
            click.secho(f"❌ O arquivo '{file_path}' não foi encontrado.", fg="red")
            return
            
        # Aciona o motor
        from src.blame_engine import run_blame_analysis
        run_blame_analysis(file_path.strip(), start_line.strip(), end_line.strip())
        return 

# Módulo Issue (Híbrido)
    if issue:
        from src.issue_engine import generate_issue_content, get_github_repo_info
        from src.tui_issue import validate_or_request_github_token, IssueApp
        
        setup_environment()
        
        context_text = ""
        context_type = "diff"
        
        # 1. Roteador de Contexto Inteligente
        if history:
            context_type = "history"
            context_text = get_branch_history_text()
            if not context_text or ("Nenhum commit exclusivo" in context_text and "Nenhum PR anterior" in context_text):
                click.secho("\n⚠️ Nenhum histórico encontrado para esta branch.\n", fg="yellow")
                return
                
        elif blame:
            context_type = "blame"
            # Reaproveita o parser de arquivo/linhas da opção blame
            if ":" in blame:
                file_path, lines = blame.split(":", 1)
                try:
                    start_line, end_line = lines.split("-") if "-" in lines else (lines, lines)
                except ValueError:
                    click.secho("❌ Formato de linhas inválido. Use inicio-fim (ex: 10-20).", fg="red")
                    return
            else:
                file_path = blame
                if not os.path.exists(file_path):
                    click.secho(f"❌ O arquivo '{file_path}' não foi encontrado.", fg="red")
                    return
                click.secho(f"📂 Arquivo selecionado: {file_path}", fg="cyan", bold=True)
                lines_input = click.prompt("Quais linhas você deseja investigar? (Ex: 10-20)")
                start_line, end_line = lines_input.split("-") if "-" in lines_input else (lines_input, lines_input)
                    
            if not os.path.exists(file_path.strip()):
                click.secho(f"❌ O arquivo '{file_path}' não foi encontrado.", fg="red")
                return
                
            from src.blame_engine import run_blame_analysis
            click.secho("🔍 Extraindo linha do tempo arqueológica em background...", fg="cyan")
            
            # Aciona o arqueólogo no modo silencioso
            timeline = run_blame_analysis(file_path.strip(), start_line.strip(), end_line.strip(), return_data=True)
            
            if not timeline:
                click.secho("\n⚠️ Nenhum histórico rastreável para alimentar a issue.\n", fg="yellow")
                return
            
            # Traduz a lista de dicionários para um texto legível para a IA
            formatted_timeline = []
            for item in timeline:
                formatted_timeline.append(
                    f"[{item['raw_date']}] Commit {item['hash']} por {item['info']['author']}:\n"
                    f"Ação: {item['status']}\n"
                    f"Motivo IA: {item['motivo']}\n"
                )
            context_text = "\n".join(formatted_timeline)

        else:
            context_type = "diff"
            context_text = get_git_diff()
            if not context_text or not context_text.strip():
                click.secho("\n⚠️ Nenhum código novo encontrado. Faça alguma alteração antes de gerar a issue.\n", fg="yellow")
                return

        # 2. Gera o conteúdo com a IA enviando o idioma correto
        issue_data = generate_issue_content(context_text, context_type=context_type)
        if not issue_data:
            return
            
        # 3. Pega informações do repositório
        repo_info = get_github_repo_info()
        
        # 4. Valida ou solicita o Token PAT
        github_token = validate_or_request_github_token(repo_info)
        
        if not github_token:
            click.secho("❌ Acesso cancelado. O Token do GitHub é obrigatório para esta ação.", fg="red")
            return
            
        # 5. Roda a Interface Gráfica do Terminal
        app = IssueApp(issue_data=issue_data, repo_info=repo_info, github_token=github_token)
        app.run()
        
        # 6. Exibe a mensagem de retorno após fechar a TUI
        if app.final_message:
            cor = "green" if app.final_action in ["saved", "created"] else "red"
            click.secho(f"\n{app.final_message}\n", fg=cor, bold=True)
            
        return 

    # Validação do Modo Input
    if input and not (review or fullreview):
        click.secho("\n❌ Erro: A opção --input (-i) só pode ser utilizada em conjunto com --review (-r) ou --fullreview (-f).", fg="red", bold=True)
        return
    
    # Garante que o ambiente e as chaves estão configurados
    setup_environment()

    # Determina o provedor de IA a ser usado (opção de linha de comando tem prioridade)
    active_provider = provider if provider else get_ai_provider()
    
    # Determina o tipo de ação e qual diff capturar
    action_type = "pr"
    diff_text = ""
    
    if input:
        # MODO FILE REVIEW: Lê o arquivo físico em vez do git diff
        action_type = "filereview"
        try:
            with open(input, "r", encoding="utf-8") as f:
                diff_text = f.read()
            click.secho(f"📄 Modo Arquivo: Analisando conteúdo integral de '{input}'...", fg="blue")
        except Exception as e:
            click.secho(f"❌ Erro ao ler o arquivo: {e}", fg="red")
            return
    elif commit:
        action_type = "commit"
        diff_text = get_git_diff()
    elif review:
        action_type = "review"
        diff_text = get_git_diff()
    elif fullreview:
        action_type = "fullreview" 
        diff_text = get_git_full_diff()
    else:
        # Padrão: Descrição de PR usando o Full Diff contra a main remota
        action_type = "pr"
        diff_text = get_git_full_diff()
   
    # CRÍTICO: Avisa o usuário antes de sair se não houver alterações
    if not diff_text or not diff_text.strip():
        click.secho("\n⚠️ Nenhum código novo encontrado. Faça alguma alteração ou verifique sua branch antes de rodar o comando.\n", fg="yellow")
        return

    # Chama a IA de acordo com active_provider utilizando a nova assinatura da função
    # A assinatura requer: action_folder, action_type, diff_text, provider
    # Usamos o próprio action_type como action_folder, pois a função lida com isso internamente.
    data = generate_pr_content(action_type, action_type, diff_text, active_provider)
    if not data:
        return

    # Processamento da Saída
    branch_name = get_current_branch()
    safe_branch_name = branch_name.replace("/", "-").replace("\\", "-")
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")

    # Apenas Commit no console
    if action_type == "commit":
        msg = data.get('commit_message', 'Atualização de código')

        if hook:
            # MODO HOOK: Injeta a mensagem direto no arquivo do Git
            try:
                with open(hook, "r", encoding="utf-8") as f:
                    original_content = f.read()
                
                # Coloca a sugestão no topo, mantendo os comentários originais do Git abaixo
                with open(hook, "w", encoding="utf-8") as f:
                    f.write(f"{msg}\n\n{original_content}")
                
                click.secho(f"✅ Mensagem injetada com sucesso no editor!", fg="green")
            except Exception as e:
                click.secho(f"❌ Erro ao injetar no hook: {e}", fg="red")
        else:
            # MODO CONSOLE: O comportamento original que já existia
            click.secho("\n💡 Dica: Use sem --commit para gerar o PR completo.\n", fg="yellow")
            click.secho("\n📝 Sugestão de Commit:\n", fg="green", bold=True)
            click.echo(msg)
            click.echo("\n")
        return

    # Code Review e File Review (Arquivo)  
    if action_type in ["review", "fullreview", "filereview"]:
        
        if fullreview:
            pattern = os.getenv("OUTPUT_FILE_NAME_FULLREVIEW", "{branch}_{datetime}_PR_FULLREVIEW.txt")
        elif action_type == "filereview":
            pattern = os.getenv("OUTPUT_FILE_NAME_FILEREVIEW", "{branch}_{datetime}_FILE_REVIEW.txt")
        else:
            pattern = os.getenv("OUTPUT_FILE_NAME_REVIEW", "{branch}_{datetime}_PR_REVIEW.txt")            

        output_filename = pattern.format(
            branch=safe_branch_name,
            datetime=current_time
        )
        content = data.get('review', 'Nenhuma análise gerada.')
        
        # Chama o Linter. Se for "filereview", ativa o modo de arquivo completo.
        if action_type == "filereview":
            linter_results = parse_diff_and_lint(diff_text, is_full_file=True, file_path=input)
        else:
            linter_results = parse_diff_and_lint(diff_text)
            
        all_alerts = linter_results["errors"] + linter_results["warnings"]
        
        if all_alerts:
            
            click.secho(f"⚠️ Atenção! Encontrados {len(all_alerts)} alertas nas regras do Linter.", fg="yellow")
            
            # Monta o cabeçalho com os erros do linter
            linter_header = "## 🚨 Alertas de Análise Estática Local (Regras YAML)\n\n"
            for alert in all_alerts:
                linter_header += f"- {alert}\n"
            linter_header += "\n---\n\n## 🤖 Code Review da IA\n\n"
            
            # Injeta o cabeçalho no topo do conteúdo gerado pela IA
            content = linter_header + content
        else:
            click.secho("✅ Linter Local passou sem violações de regras!", fg="green")

        try:
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(content)
            click.secho(f"\n✅ Code Review gerado com sucesso: '{output_filename}'", fg="green", bold=True)
        except Exception as e:
            click.secho(f"\n❌ Erro ao salvar o review: {e}", fg="red")
        return

    # Pull Request Padrão (Arquivo .md)
    filename_pattern = os.getenv("OUTPUT_FILE_NAME", "{branch}_{datetime}_PR_DESC.md")
    output_filename = filename_pattern.format(branch=safe_branch_name, datetime=current_time)

    markdown_content = f"""# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
{data.get('commit_message', 'Atualização de código')}
```

---

{data.get('pr_description', 'Sem descrição detalhada.')}
"""

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        click.secho(f"\n✅ Sucesso! O arquivo '{output_filename}' foi gerado na pasta atual.", fg="green", bold=True)
    except Exception as e:
        click.secho(f"\n❌ Erro ao guardar o arquivo: {e}", fg="red")
    
    if not quiet:
        print_update_notice()    
        
if __name__ == "__main__":
    cli()