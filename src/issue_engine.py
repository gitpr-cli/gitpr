import subprocess
import re
import os
import click
from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.config import get_api_key, get_api_model, get_ai_provider
from src.ai_providers import call_ai_model

def get_github_repo_info():
    """Extrai o formato owner/repo do comando git remote -v."""
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Busca padrões como git@github.com:owner/repo.git ou https://github.com/owner/repo.git
        match = re.search(r'github\.com[:/](.+?)/(.+?)(\.git)?\s+\(push\)', result.stdout)
        
        if match:
            owner = match.group(1)
            repo = match.group(2).replace('.git', '')
            return f"{owner}/{repo}"
            
        return None
    except subprocess.CalledProcessError:
        return None

def generate_issue_content(diff_text):
    """Envia o diff para a IA e retorna um dicionário com título e corpo da issue."""
    if not diff_text or not diff_text.strip():
        return None

    provider = get_ai_provider()
    api_key = get_api_key(provider)
    
    if not api_key:
        click.secho("❌ Erro: Chave de API não encontrada.", fg="red")
        return None

    # Utilizamos o modelo avançado para garantir a qualidade da estrutura da Issue
    api_model = get_api_model(provider, task_complexity="advanced")

    skill_path = os.path.join(os.getcwd(), ".gitpr.issue.md")
    sys_inst = ""
    
    if os.path.exists(skill_path):
        with open(skill_path, "r", encoding="utf-8") as f:
            sys_inst = f.read()
    else:
        sys_inst = "Você é um Arquiteto de Software. Siga o formato O Que / Por Que / Onde / Como para documentar a Issue."

    prompt = (
        f"Gere o objeto JSON solicitado seguindo as instruções de sistema para documentar a seguinte alteração:\n\n"
        f"DIFF PARA ANÁLISE:\n{diff_text}"
    )

    # --- NOVO: Tenta recuperar do Cache ---
    cached_data = get_cached_response("issue", prompt)
    if cached_data:
        click.secho("⚡ Resposta da Issue recuperada do cache local.", fg="green", dim=True)
        return cached_data

    click.secho(f"🤖 Estruturando a Issue usando {provider.capitalize()} ({api_model})...", fg="cyan", dim=True)
    
    result_json = call_ai_model(provider, api_key, api_model, prompt, sys_inst)
    
    if result_json and "titulo" in result_json and "corpo" in result_json:
        # --- NOVO: Salva no Cache ---
        save_cached_response("issue", "issue", prompt, result_json)
        return result_json
        
    return {"titulo": "Erro ao gerar título", "corpo": "Não foi possível gerar o corpo da issue pela IA."}