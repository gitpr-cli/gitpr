import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
def get_cache_base_dir():
    """Retorna o caminho ~/.gitpr/cache/prompts/"""
    path = Path.home() / ".gitpr" / "cache" / "prompts"
    return path

def generate_md5(text):
    """Gera o hash MD5 de uma string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_cached_response(action_folder, prompt_text):
    """Verifica se existe um cache válido para o prompt e retorna o conteúdo."""
    md5_hash = generate_md5(prompt_text)
    cache_file = get_cache_base_dir() / action_folder / f"{md5_hash}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("response")
        except (json.JSONDecodeError, IOError):
            return None
    return None

def save_cached_response(action_folder, action_type, prompt_text, response_dict):
    """Salva a resposta da IA no cache local."""
    md5_hash = generate_md5(prompt_text)
    folder_path = get_cache_base_dir() / action_folder
    folder_path.mkdir(parents=True, exist_ok=True)
    
    cache_file = folder_path / f"{md5_hash}.json"
    from src.core import get_current_branch, get_repo_name
    current_branch = get_current_branch()
    repo_name = get_repo_name()

    cache_data = {
        "md5": md5_hash,
        "repo": repo_name,
        "branch": current_branch,
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action_type": action_type,
        "prompt": prompt_text,
        "response": response_dict
    }

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
    except IOError:
        pass # Falha silenciosa no cache para não travar a ferramenta
    
def get_cached_pr_descriptions(repo_name, branch_name):
    """Busca no cache todos os PRs gerados historicamente para este repositorio e branch."""
    pr_cache_folder = get_cache_base_dir() / "pr_desc"
    history_texts = []

    if not pr_cache_folder.exists():
        return ""

    for cache_file in pr_cache_folder.glob("*.json"):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Filtra por repositorio E branch (evita misturar projetos diferentes)
                if data.get("repo") == repo_name and data.get("branch") == branch_name:
                    response_dict = data.get("response", {})
                    pr_desc = response_dict.get("pr_description")
                    if pr_desc:
                        date_str = data.get("datetime", "Data desconhecida")
                        history_texts.append(f"[{date_str}]\n{pr_desc}\n")
        except (json.JSONDecodeError, IOError):
            continue

    if history_texts:
        # Ordena cronologicamente (usando a data extraida no colchete)
        history_texts.sort()
        return "=== HISTÓRICO DE PRs DA IA ===\n" + "\n".join(history_texts)

    return ""