"""Builds the public URLs of the GitPR documentation website.

Kept out of src/core.py on purpose: the configuration screen links to the
technical documentation of every section, and src/ui/config_app.py must not
import src.core (it pulls google.genai into every screen launch). The mapping
from a section to its page lives in src/config_schema.py, next to the labels.
"""

from src.i18n import CURRENT_LANG

DOCS_BASE_URL = "https://gitpr.natanfiuza.dev.br/docs/"


def doc_url(filename):
    """Returns the complete URL for the official GitPR documentation website.

    Transforms a docs/ filename like 'commit-message-ia.md' into a clean website
    URL with language query parameter. English is the site default (no ?lang=).

    Examples:
        doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files"
        doc_url("untracked-files.md")  -> "https://gitpr.natanfiuza.dev.br/docs/untracked-files?lang=pt_br"  (when CURRENT_LANG is pt_br)
    """
    base, _ = filename.rsplit(".", 1)
    url = f"{DOCS_BASE_URL}{base}"
    if not CURRENT_LANG.startswith("en"):
        url += f"?lang={CURRENT_LANG}"
    return url
