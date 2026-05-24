import os
import json
import stat
import click
import subprocess
import urllib.request
import urllib.error
from google import genai
from src.security import decrypt_data
from src.cache import get_cached_response, save_cached_response
from src.config import get_api_key, get_api_model
from src.ai_providers import call_ai_model


def get_git_diff():
    """Executa 'git diff HEAD' e retorna a saída, alertando sobre arquivos não monitorados (untracked)."""
    try:
        # 1. Verifica se existem arquivos novos não monitorados (untracked)
        untracked_process = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"], 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            errors="replace"  # <--- CORREÇÃO AQUI (Evita crash com acentos)
        )
        untracked_files = untracked_process.stdout.strip()
        
        # Se houver arquivos novos, exibe um alerta educativo no console
        if untracked_files:
            click.secho("⚠️ Aviso: O Git detectou novos arquivos que não estão sendo monitorados:", fg="yellow")
            for file in untracked_files.split('\n'):
                click.secho(f"  - {file}", fg="yellow", dim=True)
            click.secho("💡 Dica: Use 'git add <arquivo>' para que eles sejam incluídos na análise do GitPR.", fg="cyan")
            click.secho("📚 Entenda o motivo: https://github.com/natanfiuza/gitpr/blob/main/docs/untracked-files.md\n", fg="blue", underline=True)

        # 2. Executa o diff normal que captura arquivos monitorados e em staging
        result = subprocess.run(
            ["git", "diff", "HEAD"], 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            errors="replace",  # <--- CORREÇÃO AQUI (Evita crash com acentos)
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Erro ao executar o Git: {e.stderr}", fg="red")
        return None
    except FileNotFoundError:
        click.secho("❌ Git não encontrado. Certifique-se de que está instalado e no PATH.", fg="red")
        return None


def get_current_branch():
    """Retorna o nome da branch atual."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "main" # Fallback


def get_skill_context(action_type="pr"):
    """Lê o arquivo de contexto correto baseado na ação (PR/Commit ou Review)."""
    
    # Define qual arquivo procurar
    if action_type == "commit":
        target_file = ".gitpr.commit.md"
    elif action_type == "pr":
        target_file = ".gitpr.pr.md"
    elif action_type == "filereview": # NOVO!
        target_file = ".gitpr.filereview.md"        
    else: # review ou fullreview
        target_file = ".gitpr.review.md"

    skill_file = os.path.join(os.getcwd(), target_file)
    
    # Fallback para o arquivo antigo (para retrocompatibilidade com usuários da versão anterior)
    legacy_file = os.path.join(os.getcwd(), ".gitpr.md")

    # Verifica o novo primeiro; se não achar, tenta o antigo
    file_to_load = skill_file if os.path.exists(skill_file) else (legacy_file if os.path.exists(legacy_file) else None)
    
    if file_to_load:
        try:
            with open(file_to_load, "r", encoding="utf-8") as f:
                conteudo = f.read()
                nome_arquivo = os.path.basename(file_to_load)
                click.secho(f"🧠 Arquivo {nome_arquivo} (Skill) encontrado e carregado!", fg="blue")
                return conteudo
        except Exception as e:
            click.secho(f"⚠️ Aviso: Falha ao ler o arquivo {nome_arquivo} ({e})", fg="yellow")
    
    # Retorna vazio se não existir
    return ""


def generate_pr_content(action_folder, action_type, diff_text, provider="gemini"):
    """Envia o diff para a IA usando System Instruction e retorna um JSON parseado."""
    if not diff_text or not diff_text.strip():
        click.secho("⚠️ Nenhum diff encontrado. Faça alguma alteração antes de rodar o comando.", fg="yellow")
        return None

    # Configuração de pastas para o Cache
    action_folder_map = {
        "pr": "pr_desc",
        "commit": "commit",
        "review": "review",
        "fullreview": "review",
        "filereview": "review",
    }
    action_folder = action_folder_map.get(action_type, "misc")

    # Busca o contexto do arquivo correspondente à ação (PR, Commit ou Review)
    skill_context = get_skill_context(action_type)

    # Definição da Complexidade da Tarefa (NOVO)
    # Commits usam modelos mais rápidos/baratos. Reviews e PRs usam modelos avançados.
    task_complexity = "simple" if action_type == "commit" else "advanced"

    # Definição da Instrução de Sistema (Persona e Regras)
    if action_type == "commit":
        instrucao_sistema = skill_context if skill_context else "Você é um especialista em Git. Gere mensagens de commit concisas."
        prompt = f"Gere APENAS um objeto JSON no formato {{\"commit_message\": \"...\"}} para este diff:\n{diff_text}"
        
    elif action_type in ["review", "fullreview", "filereview"]:
        instrucao_sistema = skill_context if skill_context else "Você é um Arquiteto de Software Sênior. Foque em apontar melhorias."
        
        if action_type == "filereview":
            prompt = f"Gere APENAS um objeto JSON no formato {{\"review\": \"...\"}} com a análise e melhorias para o código integral deste arquivo:\n{diff_text}"
        else:
            prompt = f"Gere APENAS um objeto JSON no formato {{\"review\": \"...\"}} apontando erros e melhorias para este diff:\n{diff_text}"       
    else: # pr
        instrucao_sistema = skill_context if skill_context else "Você é um Tech Lead redigindo descrições de PR limpas e técnicas."
        prompt = f"Gere APENAS um objeto JSON no formato {{\"commit_message\": \"...\", \"pr_description\": \"...\"}} para este diff:\n{diff_text}"

    # TENTA RECUPERAR DO CACHE
    cached_data = get_cached_response(action_folder, prompt)
    if cached_data:
        click.secho("⚡ Resposta recuperada do cache local.", fg="green", dim=True)
        return cached_data

    # Preparação das Chaves (Agora dinâmico por Provedor)
    api_key = get_api_key(provider)
    if not api_key:
        click.secho(f"❌ Erro: Chave de API para o provedor '{provider.capitalize()}' não encontrada.", fg="red")
        return None
    
    # Busca o Modelo Inteligente (NOVO)
    # Envia a complexidade para o config.py devolver o modelo primário ou secundário
    api_model = get_api_model(provider, task_complexity)
    if not api_model:
        click.secho(f"❌ Erro: Não foi possível determinar o modelo para o provedor '{provider}'.", fg="red")
        return None

    # CHAMADA À API
    click.secho(f"🤖 O GitPR está analisando o seu código usando {provider.capitalize()} ({api_model})...\n", fg="cyan")
    
    result_json = call_ai_model(provider, api_key, api_model, prompt, instrucao_sistema)

    # SALVA NO CACHE E RETORNA
    if result_json:
        save_cached_response(action_folder, action_type, prompt, result_json)
        return result_json
    
    return None


def generate_skill_template():
    """
    Faz o download dos templates .gitpr.pr.md, .gitpr.review.md 
    e .gitpr.linter.yml diretamente do repositório oficial.
    """
    click.secho("\n📥 Iniciando a configuração dos templates do GitPR...", fg="cyan", bold=True)
    
    base_url = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/"
    
    # Atualizado para contemplar os 3 arquivos
    files_to_download = {
        ".gitpr.commit.md": "gitpr.commit.md",
        ".gitpr.pr.md": "gitpr.pr.md",
        ".gitpr.review.md": "gitpr.review.md",
        ".gitpr.linter.yml": "gitpr.linter.yml",
        ".gitpr.filereview.md": "gitpr.filereview.md", 
        ".gitpr.blame.md": "gitpr.blame.md", 
    }
    
    success_count = 0
    
    for local_name, remote_name in files_to_download.items():
        file_path = os.path.join(os.getcwd(), local_name)
        url = base_url + remote_name
        
        if os.path.exists(file_path):
            click.secho(f"⚠️ O arquivo {local_name} já existe neste diretório. Ele não será sobrescrito.", fg="yellow")
            continue
            
        try:
            click.echo(f"A descarregar {local_name}...")
            with urllib.request.urlopen(url, timeout=5) as response:
                content = response.read().decode('utf-8')
                
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            success_count += 1
            
        except urllib.error.URLError as e:
            click.secho(f"❌ Erro de rede ao baixar {local_name}: {e.reason}", fg="red")
        except Exception as e:
            click.secho(f"❌ Falha ao processar {local_name}: {e}", fg="red")

    if success_count > 0:
        click.secho("\n✅ Templates base configurados com sucesso!", fg="green", bold=True)
        click.echo("Você pode agora abrir os arquivos gerados e personalizar o comportamento da ferramenta para o seu projeto:\n")       
        click.echo("  1. As regras de arquitetura para a IA no arquivo '.gitpr.pr.md' e '.gitpr.review.md'\n")
        click.echo("  2. As regras de regex locais no arquivo '.gitpr.linter.yml'\n")
    else:
        click.echo("\nNenhum arquivo novo foi baixado.")


def get_base_branch():
    """Descobre a branch principal remota (ex: main ou master)."""
    try:
        # Busca a referência da branch default do remote
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True, text=True, check=True
        )
        # O retorno é algo como 'refs/remotes/origin/main', então pegamos a última parte
        return result.stdout.strip().split('/')[-1]
    except subprocess.CalledProcessError:
        click.secho("⚠️ Aviso: Branch principal remota não detectada. Assumindo 'main' como fallback padrão.", fg="yellow")
        return "main" # Fallback padrão caso não encontre


def get_git_full_diff():
    """Faz o fetch e captura o diff entre a branch principal remota e o estado atual."""
    click.secho("🔄 Sincronizando com o repositório remoto (git fetch)...", fg="cyan")
    try:
        # Faz o fetch para garantir que sabemos onde a origin/main está
        subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
        
        base_branch = get_base_branch()
        
        # Encontra o HASH do commit onde a sua branch nasceu (o ancestral comum)
        merge_base_res = subprocess.run(
            ["git", "merge-base", f"origin/{base_branch}", "HEAD"],
            capture_output=True, text=True, check=True
        )
        ancestor_hash = merge_base_res.stdout.strip()

        # Faz o diff entre esse HASH e o seu WORKSPACE ATUAL (sem usar HEAD)
        # Ao passar apenas o hash, o Git compara esse commit com os arquivos no seu disco.
        result = subprocess.run(
            ["git", "diff", ancestor_hash], 
            capture_output=True, 
            text=True, 
            encoding="utf-8",
            check=True
        )
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Erro ao calcular o diff: {e.stderr}", fg="red")
        return None
    
def install_git_hooks():
    """Faz o download e instala os scripts de pre-commit e prepare-commit-msg."""
    hooks_dir = os.path.join(os.getcwd(), ".git", "hooks")
    
    if not os.path.exists(hooks_dir):
        click.secho("❌ Erro: Pasta .git não encontrada. Execute na raiz do projeto.", fg="red")
        return False

    # Mapeamento: Nome do Hook no Git -> Nome do Template no seu GitHub
    hooks_to_install = {
        "pre-commit": "pre-commit-template.sh",
        "prepare-commit-msg": "prepare-commit-msg-template.sh"
    }

    base_url = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/scripts/"
    success_count = 0

    for hook_name, template_name in hooks_to_install.items():
        hook_path = os.path.join(hooks_dir, hook_name)
        url = base_url + template_name

        try:
            click.secho(f"📥 A descarregar {hook_name}...", fg="cyan")
            
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                
            with open(hook_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Atribui permissão de execução (chmod +x)
            st = os.stat(hook_path)
            os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
            
            success_count += 1
        except Exception as e:
            click.secho(f"⚠️ Falha ao instalar {hook_name}: {e}", fg="yellow")

    return success_count == len(hooks_to_install)