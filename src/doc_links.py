"""Builds the public URLs of the GitPR documentation website.

Kept out of src/core.py on purpose: the configuration screen links to the
technical documentation of every section, and src/ui/config_app.py must not
import src.core (it pulls google.genai into every screen launch). The mapping
from a section to its page lives in src/config_schema.py, next to the labels.
"""

from src import i18n

DOCS_BASE_URL = "https://gitpr.natanfiuza.dev.br/docs/"

# Maps internal locale codes (src/i18n.py) to the documentation site's ?lang=
# query parameter contract (Spanish and French use two-letter codes on the site).
DOC_LANG_PARAMS = {
    "pt_br": "pt_br",
    "pt_pt": "pt_pt",
    "es_es": "es",
    "es": "es",
    "fr_fr": "fr",
    "fr": "fr",
}

KNOWN_LOCALE_SUFFIXES = (".pt_br", ".pt_pt", ".es_es", ".fr_fr", ".en_us")


def doc_url(filename):
    """Returns the complete URL for the official GitPR documentation website.

    Transforms a docs/ filename like 'commit-message-ia.md' into a clean website
    URL with language query parameter. English is the site default (no ?lang=).

    Examples:
        doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files"
        doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files?lang=pt_br"  (when CURRENT_LANG is pt_br)
        doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files?lang=es"     (when CURRENT_LANG is es_es)
    """
    base = (
        filename[:-3]
        if filename.endswith(".md")
        else (filename.rsplit(".", 1)[0] if "." in filename else filename)
    )
    for suffix in KNOWN_LOCALE_SUFFIXES:
        if base.endswith(suffix):
            base = base[: -len(suffix)]
            break

    url = f"{DOCS_BASE_URL}{base}"
    current_lang = (i18n.CURRENT_LANG or "en_us").lower()
    if not current_lang.startswith("en"):
        lang_param = DOC_LANG_PARAMS.get(current_lang, current_lang)
        url += f"?lang={lang_param}"
    return url
