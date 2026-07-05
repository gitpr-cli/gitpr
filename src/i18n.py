import os
import json
import locale
import urllib.request
from pathlib import Path
from dotenv import load_dotenv, set_key

# Import the current language version defined in the code
from src.updater import __lang_version__

# Global path to the .env file
env_path = Path.home() / ".gitpr" / ".env"
load_dotenv(env_path)

def get_system_language():
    """Detects the system language or forces the language configured in .env"""
    lang_env = os.getenv("GITPR_LANG")
    if lang_env:
        return lang_env.lower()

    try:
        loc, _ = locale.getdefaultlocale()
        if loc:
            return loc.lower()  # e.g.: pt_br, es_es, en_us
    except Exception:
        pass

    return "en_us"  # Global fallback

def get_translations(lang_code):
    """Loads the translation JSON. If outdated or missing, downloads remotely (OTA)."""
    if lang_code.startswith("en"):
        return {}

    langs_dir = Path.home() / ".gitpr" / "langs"
    langs_dir.mkdir(parents=True, exist_ok=True)

    local_file = langs_dir / f"{lang_code}.json"

    # Version Control Logic (Forces update if the code version is newer)
    current_env_version = os.getenv("LANG_VERSION")
    needs_update = current_env_version != __lang_version__

    if not local_file.exists() or needs_update:
        remote_url = f"https://raw.githubusercontent.com/natanfiuza/gitpr/main/langs/{lang_code}.json"
        try:
            with urllib.request.urlopen(remote_url, timeout=3) as response:
                content = response.read().decode('utf-8')

            with open(local_file, "w", encoding="utf-8") as f:
                f.write(content)

            # Update .env with the new version after successful download
            set_key(env_path, "LANG_VERSION", __lang_version__)
        except Exception:
            # In case of failure (e.g.: offline), if the old file exists, use it
            if not local_file.exists():
                return {}

    if local_file.exists():
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    return {}

# ==========================================
# IN-MEMORY INITIALIZATION (SESSION CACHE)
# ==========================================
CURRENT_LANG = get_system_language()
TRANSLATIONS = get_translations(CURRENT_LANG)

def __(key, **kwargs):
    """
    Translation Engine inspired by Laravel.
    Tries to find the key in the dictionary. If not found, returns the key itself (English).
    """
    text = TRANSLATIONS.get(key, key)
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
            
    return text