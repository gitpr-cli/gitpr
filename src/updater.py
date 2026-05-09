import urllib.request
import json
import os
import sys
import shutil
import click

# Versão atual do seu executável local (Atualize isso a cada novo build!)
__version__ = "0.0.11"
GITHUB_API_URL = "https://api.github.com/repos/natanfiuza/gitpr/releases/latest"

def get_gitpr_dir():
    """Retorna o diretório ~/.gitpr/"""
    return os.path.join(os.path.expanduser("~"), ".gitpr")

def check_and_update():
    """Verifica na API do GitHub se há um novo release com um hash diferente."""
    try:
        # Timeout curto para não travar a CLI se a API do GitHub estiver lenta
        req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'GitPR-Updater'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
        
        # Pega a versão remota (apenas para log/exibição)
        remote_version = data.get("tag_name", "").replace("v", "")
        
        # Procura o executável nos assets
        assets = data.get("assets", [])
        exe_asset = next((a for a in assets if a.get("name") == "gitpr.exe"), None)
        
        if not exe_asset:
            return # Nenhum executável encontrado no release mais recente

        remote_digest = exe_asset.get("digest", "").replace("sha256:", "")
        download_url = exe_asset.get("browser_download_url")

        if not remote_digest or not download_url:
            return

        # Compara com o hash local
        gitpr_dir = get_gitpr_dir()
        sha_file = os.path.join(gitpr_dir, ".sha256")
        local_digest = ""
        
        if os.path.exists(sha_file):
            with open(sha_file, "r") as f:
                local_digest = f.read().strip()

        # Se os hashes forem diferentes, dispara o update!
        if remote_digest != local_digest:
            click.secho(f"\n🚀 Nova versão do GitPR encontrada (v{remote_version})!", fg="green", bold=True)
            click.secho("Baixando atualização em segundo plano...", fg="cyan")
            _perform_hot_swap(download_url, remote_digest, sha_file)

    except Exception as e:
        # Silencia erros de timeout ou rede para não atrapalhar o fluxo do usuário
        click.secho(f"Debug Updater: {e}", fg="red") # Descomente para debugar
        pass

def _perform_hot_swap(download_url, new_digest, sha_file):
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