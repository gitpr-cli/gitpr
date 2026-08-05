import os
import json
import locale
import urllib.request
from pathlib import Path
from dotenv import load_dotenv, set_key

# Global path to the .env file
env_path = Path.home() / ".gitpr" / ".env"
load_dotenv(env_path)

def get_system_language():
    """Detects the system language or forces the language configured in .env.
    On first run, saves the detected language to .env for persistence."""
    lang_env = os.getenv("GITPR_LANG")
    if lang_env:
        return lang_env.lower()

    # No GITPR_LANG set yet — detect from OS and save to .env
    try:
        loc, _ = locale.getdefaultlocale()
        if loc:
            lang = loc.lower()  # e.g.: pt_br, es_es, en_us
        else:
            lang = "en_us"
    except Exception:
        lang = "en_us"

    # Persist the detected language so it survives restarts
    set_key(env_path, "GITPR_LANG", lang)

    # Reload .env so the new variable is available immediately
    load_dotenv(env_path, override=True)

    return lang

def get_translations(lang_code):
    """Loads the translation JSON. If outdated or missing, downloads remotely (OTA)."""
    if lang_code.startswith("en"):
        return {}

    from src.updater import __lang_version__

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


def set_lang(lang: str) -> None:
    """
    Override the session language at runtime.
    Updates CURRENT_LANG and TRANSLATIONS. Does NOT persist to .env.
    Called by the --lang CLI flag before any command logic.
    """
    global CURRENT_LANG, TRANSLATIONS
    lang = lang.lower().replace("-", "_")  # normalize pt-BR -> pt_br
    CURRENT_LANG = lang
    TRANSLATIONS = get_translations(lang)


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


# ==========================================
# IN-MEMORY INITIALIZATION (SESSION CACHE)
# ==========================================
CURRENT_LANG = get_system_language()
TRANSLATIONS = get_translations(CURRENT_LANG)