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

def generate_issue_content(context_text, context_type="diff"):
    """Envia o contexto (diff, blame ou history) para a IA e retorna um dicionário da issue."""
    if not context_text or not str(context_text).strip():
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

    # Cérebro Adaptativo (Prompt Dinâmico)
    if context_type == "blame":
        target_action = "documentar a evolução arquitetural, refatorações e a dívida técnica desta regra de negócio baseando-se no histórico de commits."
        data_label = "LINHA DO TEMPO DA REGRA (DO MAIS ANTIGO PARA O MAIS NOVO):"
    elif context_type == "history":
        target_action = "documentar o Épico/Release detalhando todas as funcionalidades implementadas baseando-se no histórico integral da branch."
        data_label = "HISTÓRICO CONSOLIDADO DA BRANCH (COMMITS + PRS ANTIGOS):"
    else:
        target_action = "documentar a seguinte alteração de código recém introduzida."
        data_label = "DIFF PARA ANÁLISE:"

    prompt = (
        f"Gere o objeto JSON solicitado seguindo as instruções de sistema para {target_action}\n\n"
        f"{data_label}\n{context_text}"
    )
    
    # Tenta recuperar do Cache
    cached_data = get_cached_response("issue", prompt)
    if cached_data:
        click.secho("⚡ Resposta da Issue recuperada do cache local.", fg="green", dim=True)
        return cached_data

    click.secho(f"🤖 Estruturando a Issue usando {provider.capitalize()} ({api_model})...", fg="cyan", dim=True)
    
    result_json = call_ai_model(provider, api_key, api_model, prompt, sys_inst)
    
    if result_json and "titulo" in result_json and "corpo" in result_json:
        # Salva no Cache 
        save_cached_response("issue", "issue", prompt, result_json)
        return result_json
        
    return {"titulo": "Erro ao gerar título", "corpo": "Não foi possível gerar o corpo da issue pela IA."}