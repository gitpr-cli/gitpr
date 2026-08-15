import urllib.request
import json
import os
import sys
import shutil
import click
from datetime import datetime

# Current version of your local executable (Update this on every new build!)
# ── Must stay ABOVE the i18n import: i18n.py lazily imports __lang_version__
#     from here, and pyproject.toml reads __version__ via setuptools attr:.
__version__ = "0.0.36"  # GitPR current version
__lang_version__ = "v0.0.15"  # Language dictionary version control
__scripts_version__ = "v0.0.3"  # Git Hook scripts version control (independent from __lang_version__)

from src.i18n import __
GITHUB_API_URL = "https://api.github.com/repos/natanfiuza/gitpr/releases/latest"
PYPI_API_URL = "https://pypi.org/pypi/gitpr-cli/json"

def get_gitpr_dir():
    """Returns the ~/.gitpr/ directory path."""
    return os.path.join(os.path.expanduser("~"), ".gitpr")

def get_update_cache_file():
    """Returns the path to the update cache file."""
    return os.path.join(get_gitpr_dir(), "update_cache.json")

def parse_version(version_str):
    """Converts 'v0.1.0' or '0.1.0' into a tuple (0, 1, 0) for version math."""
    clean_version = version_str.lower().replace("v", "")
    try:
        return tuple(map(int, clean_version.split(".")))
    except ValueError:
        return (0, 0, 0)

def get_latest_remote_version(is_compiled):
    """Fetches the latest version from the correct API (PyPI or GitHub) with daily cache."""
    cache_file = get_update_cache_file()
    today = datetime.now().strftime("%Y-%m-%d")

    # Try to read from cache to avoid slowing down the user's terminal
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
            if cache_data.get("date") == today:
                return cache_data.get("version"), cache_data.get("download_url")
        except Exception:
            pass

    # Fetch from Web if cache expired
    latest_version = ""
    download_url = ""

    try:
        if is_compiled:
            # Fetch from GitHub (For standalone executable)
            req = urllib.request.Request(GITHUB_API_URL, headers={'User-Agent': 'GitPR-Updater'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "").replace("v", "")
            
            assets = data.get("assets", [])
            exe_asset = next((a for a in assets if a.get("name") == "gitpr.exe"), None)
            if exe_asset:
                download_url = exe_asset.get("browser_download_url")
        else:
            # Fetch from PyPI (For PIP installation)
            req = urllib.request.Request(PYPI_API_URL, headers={'User-Agent': 'GitPR-Updater'})
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
            latest_version = data.get("info", {}).get("version", "")
            
        # 3. Save to cache
        if latest_version:
            os.makedirs(get_gitpr_dir(), exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump({"date": today, "version": latest_version, "download_url": download_url}, f)
                
    except Exception:
        pass  # Silent failure in case of no internet
        
    return latest_version, download_url

def print_update_notice():
    """Prints the PIP-style update notice block at the end of execution."""
    is_compiled = getattr(sys, 'frozen', False)
    latest_version, _ = get_latest_remote_version(is_compiled)

    if not latest_version:
        return

    current_v = parse_version(__version__)
    latest_v = parse_version(latest_version)

    if latest_v > current_v:
        click.echo("")        
        click.secho(__("[notice] A new release of gitpr is available: {current_version} -> {latest_version}", current_version=__version__, latest_version=latest_version), fg="yellow", dim=True)
        if is_compiled:
            click.secho(__("[notice] To update, run: gitpr --update"), fg="yellow", dim=True)
        else:
            click.secho(__("[notice] To update, run: pip install --upgrade gitpr-cli"), fg="yellow", dim=True)
        click.echo("")

def check_and_update():
    """Function triggered only when the user forces the --update flag."""
    is_compiled = getattr(sys, 'frozen', False)
    
    if not is_compiled:
        
        click.secho(__("💡 Since you installed via PIP, update by running: pip install --upgrade gitpr-cli"), fg="cyan", bold=True)
        return

    latest_version, download_url = get_latest_remote_version(is_compiled=True)
    
    if not latest_version or not download_url:
        
        click.secho(__("❌ Could not check for updates at this moment."), fg="red")
        return

    current_v = parse_version(__version__)
    latest_v = parse_version(latest_version)

    if latest_v > current_v:
        
        click.secho(__("\n🚀 New GitPR version found (v{latest_version})!", latest_version=latest_version), fg="green", bold=True)
        click.secho(__("Downloading update in background..."), fg="cyan")
        _perform_hot_swap(download_url)
    else:
        click.secho(__("✅ You are already using the latest version of GitPR."), fg="green")

def _perform_hot_swap(download_url):
    """Downloads and replaces the current executable (Hot-Swap)."""
    current_exe = sys.executable
    old_exe = current_exe + ".old"
    
    try:
        if os.path.exists(old_exe):
            os.remove(old_exe)
        os.rename(current_exe, old_exe)
        urllib.request.urlretrieve(download_url, current_exe)
        
        click.secho(__("✅ Update successfully completed! You will use the new version on the next run.\n"), fg="green", bold=True)
    except Exception as e:
        click.secho(__("❌ Failed to apply update: {error}", error=str(e)), fg="red")
        if os.path.exists(old_exe) and not os.path.exists(current_exe):
            os.rename(old_exe, current_exe)