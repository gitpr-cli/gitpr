import urllib.request
import json
import os
import sys
import shutil
import click
from datetime import datetime

# Versão atual do seu executável local (Atualize isso a cada novo build!)
__version__ = "0.0.14"
GITHUB_API_URL = "https://api.github.com/repos/natanfiuza/gitpr/releases/latest"
PYPI_API_URL = "https://pypi.org/pypi/gitpr-cli/json"

def get_gitpr_dir():
    """Retorna o diretório ~/.gitpr/"""
    return os.path.join(os.path.expanduser("~"), ".gitpr")

def get_update_cache_file():
    """Retorna o caminho do arquivo de cache de atualizações."""
    return os.path.join(get_gitpr_dir(), "update_cache.json")

def parse_version(version_str):
    """Converte 'v0.1.0' ou '0.1.0' em uma tupla (0, 1, 0) para matemática de versões."""
    clean_version = version_str.lower().replace("v", "")
    try:
        return tuple(map(int, clean_version.split(".")))
    except ValueError:
        return (0, 0, 0)

def get_latest_remote_version(is_compiled):
    """Busca a última versão na API correta (PyPI ou GitHub) com cache diário."""
    cache_file = get_update_cache_file()
    today = datetime.now().strftime("%Y-%m-%d")

    # 1. Tenta ler do cache para não atrasar o terminal do usuário
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            if cache_data.get("date") == today:
                return cache_data.get("version"), cache_data.get("download_url")
        except Exception:
            pass

    # 2. Busca na Web se o cache expirou
    latest_version = ""
    download_url = ""

    try:
        if is_compiled:
            # Busca no GitHub (Para executável)
            req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'GitPR-Updater'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").replace("v", "")
            
            assets = data.get("assets", [])
            exe_asset = next((a for a in assets if a.get("name") == "gitpr.exe"), None)
            if exe_asset:
                download_url = exe_asset.get("browser_download_url")
        else:
            # Busca no PyPI (Para instalação via PIP)
            req = urllib.request.Request(PYPI_API_URL, headers={'User-Agent': 'GitPR-Updater'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
            latest_version = data.get("info", {}).get("version", "")
            
        # 3. Salva no cache
        if latest_version:
            os.makedirs(get_gitpr_dir(), exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump({"date": today, "version": latest_version, "download_url": download_url}, f)
                
    except Exception:
        pass # Falha silenciosa em caso de falta de internet
        
    return latest_version, download_url

def print_update_notice():
    """Imprime o bloco de aviso estilo PIP no fim da execução."""
    is_compiled = getattr(sys, 'frozen', False)
    latest_version, _ = get_latest_remote_version(is_compiled)

    if not latest_version:
        return

    current_v = parse_version(__version__)
    latest_v = parse_version(latest_version)

    if latest_v > current_v:
        click.echo("")
        click.secho(f"[notice] A new release of gitpr is available: {__version__} -> {latest_version}", fg="yellow", dim=True)
        if is_compiled:
            click.secho(f"[notice] To update, run: gitpr --update", fg="yellow", dim=True)
        else:
            click.secho(f"[notice] To update, run: pip install --upgrade gitpr-cli", fg="yellow", dim=True)
        click.echo("")

def check_and_update():
    """Função disparada apenas quando o usuário força a flag --update."""
    is_compiled = getattr(sys, 'frozen', False)
    
    if not is_compiled:
        click.secho("💡 Como você instalou via PIP, atualize rodando: pip install --upgrade gitpr-cli", fg="cyan", bold=True)
        return

    latest_version, download_url = get_latest_remote_version(is_compiled=True)
    
    if not latest_version or not download_url:
        click.secho("❌ Não foi possível verificar atualizações no momento.", fg="red")
        return

    current_v = parse_version(__version__)
    latest_v = parse_version(latest_version)

    if latest_v > current_v:
        click.secho(f"\n🚀 Nova versão do GitPR encontrada (v{latest_version})!", fg="green", bold=True)
        click.secho("Baixando atualização em segundo plano...", fg="cyan")
        _perform_hot_swap(download_url)
    else:
        click.secho("✅ Você já está usando a versão mais recente do GitPR.", fg="green")

def _perform_hot_swap(download_url):
    """Faz o download e substitui o executável atual."""
    current_exe = sys.executable
    old_exe = current_exe + ".old"
    
    try:
        if os.path.exists(old_exe):
            os.remove(old_exe)
        os.rename(current_exe, old_exe)
        urllib.request.urlretrieve(download_url, current_exe)
        click.secho(f"✅ Atualização concluída com sucesso! Na próxima execução você já usará a nova versão.\n", fg="green", bold=True)
    except Exception as e:
        click.secho(f"❌ Falha ao aplicar atualização: {e}", fg="red")
        if os.path.exists(old_exe) and not os.path.exists(current_exe):
            os.rename(old_exe, current_exe)
    """Faz o download e substitui o executável atual (Hot-Swap)."""
    current_exe = sys.executable
    
    # Se não estiver rodando como executável compilado (PyInstaller), aborta o update
    if not getattr(sys, 'frozen', False):
        click.secho("⚠️ Aviso: Rodando via script Python. O Auto-Update funciona apenas no executável compilado.", fg="yellow")
        return

    old_exe = current_exe + ".old"
    
    try:
        # 1. Renomeia o executável atual que está em uso
        if os.path.exists(old_exe):
            os.remove(old_exe) # Remove restos antigos se existirem
        os.rename(current_exe, old_exe)
        
        # 2. Faz o download direto para o caminho original
        urllib.request.urlretrieve(download_url, current_exe)
        
        # 3. Salva o novo hash
        with open(sha_file, "w") as f:
            f.write(new_digest)
            
        click.secho(f"✅ Atualização concluída com sucesso! Na próxima execução você já usará a nova versão.\n", fg="green", bold=True)
        
    except Exception as e:
        # Se algo falhar na renomeação/download, tenta desfazer a bagunça
        click.secho(f"❌ Falha ao aplicar atualização: {e}", fg="red")
        if os.path.exists(old_exe) and not os.path.exists(current_exe):
            os.rename(old_exe, current_exe)