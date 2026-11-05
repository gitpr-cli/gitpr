"""Tests for canonical documentation website links (src/doc_links.py),
TUI help modal URLs, README language query invariants, and 5-language
documentation parity in docs/.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src import i18n
from src.config_schema import CATEGORIES
from src.doc_links import DOCS_BASE_URL, DOC_LANG_PARAMS, doc_url

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


@pytest.fixture(autouse=True)
def restore_i18n_lang():
    """Preserve and restore src.i18n.CURRENT_LANG across each test."""
    previous = i18n.CURRENT_LANG
    yield
    i18n.CURRENT_LANG = previous


class TestDocUrlLanguageContract:
    """Verify that doc_url() honors the site's ?lang= parameter contract."""

    def test_english_omits_lang_query_param(self):
        with patch.object(i18n, "CURRENT_LANG", "en_us"):
            assert (
                doc_url("commit-message-ia.md")
                == f"{DOCS_BASE_URL}commit-message-ia"
            )

    @pytest.mark.parametrize(
        "internal_lang,expected_param",
        [
            ("pt_br", "pt_br"),
            ("pt_pt", "pt_pt"),
            ("es_es", "es"),
            ("fr_fr", "fr"),
        ],
    )
    def test_localized_languages_use_site_query_param(
        self, internal_lang, expected_param
    ):
        with patch.object(i18n, "CURRENT_LANG", internal_lang):
            assert (
                doc_url("commit-message-ia.md")
                == f"{DOCS_BASE_URL}commit-message-ia?lang={expected_param}"
            )

    def test_set_lang_dynamically_updates_doc_url(self):
        """Regression guard: doc_url() must read src.i18n.CURRENT_LANG at call time
        rather than holding a frozen module-level import from startup."""
        with patch("src.i18n.get_translations", return_value={}):
            i18n.set_lang("en_us")
            assert doc_url("version-markers.md") == f"{DOCS_BASE_URL}version-markers"

            i18n.set_lang("es_es")
            assert (
                doc_url("version-markers.md")
                == f"{DOCS_BASE_URL}version-markers?lang=es"
            )

            i18n.set_lang("fr_fr")
            assert (
                doc_url("version-markers.md")
                == f"{DOCS_BASE_URL}version-markers?lang=fr"
            )

            i18n.set_lang("pt_br")
            assert (
                doc_url("version-markers.md")
                == f"{DOCS_BASE_URL}version-markers?lang=pt_br"
            )

    def test_strips_md_and_accidental_locale_suffixes(self):
        with patch.object(i18n, "CURRENT_LANG", "es_es"):
            assert (
                doc_url("issue-tui-help.es_es.md")
                == f"{DOCS_BASE_URL}issue-tui-help?lang=es"
            )
            assert (
                doc_url("issue-tui-help")
                == f"{DOCS_BASE_URL}issue-tui-help?lang=es"
            )


class TestTuiHelpModalsUseDocUrl:
    """Ensure HelpScreen and ChatHelpScreen use doc_url() instead of raw GitHub URLs."""

    def test_issue_help_screen_uses_doc_url(self):
        from src.ui.help_screen import HelpScreen

        screen = HelpScreen()
        with patch.object(i18n, "CURRENT_LANG", "fr_fr"):
            # Inspect the source or composed widgets of HelpScreen
            source = Path(REPO_ROOT / "src" / "ui" / "help_screen.py").read_text(
                encoding="utf-8", errors="replace"
            )
            assert "github.com/gitpr-cli/gitpr.git/blob/main/docs" not in source
            assert 'doc_url("issue-tui-help.md")' in source
            assert (
                doc_url("issue-tui-help.md")
                == f"{DOCS_BASE_URL}issue-tui-help?lang=fr"
            )

    def test_chat_help_screen_online_help_opens_canonical_doc_url(self):
        from src.ui.chat_app import ChatHelpScreen

        screen = ChatHelpScreen()
        event = MagicMock()
        event.button.id = "online_help"

        with patch.object(i18n, "CURRENT_LANG", "es_es"), patch(
            "src.ui.chat_app.webbrowser.open"
        ) as mock_open:
            screen.on_button_pressed(event)
            mock_open.assert_called_once_with(
                f"{DOCS_BASE_URL}understanding_chat_functionality?lang=es"
            )


class TestReadmeAndDocsParity:
    """Verify README ES/FR site links and 5-language coverage of config docs."""

    def test_readme_es_and_fr_use_site_lang_params(self):
        readme_es = (REPO_ROOT / "README.es_es.md").read_text(
            encoding="utf-8", errors="replace"
        )
        readme_fr = (REPO_ROOT / "README.fr_fr.md").read_text(
            encoding="utf-8", errors="replace"
        )

        assert "?lang=es_es" not in readme_es
        assert "?lang=es)" in readme_es or "?lang=es#" in readme_es

        assert "?lang=fr_fr" not in readme_fr
        assert "?lang=fr)" in readme_fr or "?lang=fr#" in readme_fr

    def test_every_config_category_doc_has_all_five_language_files(self):
        """Every page linked from src/config_schema.py CATEGORIES (including
        version-markers.md) must have all 5 language variants in docs/."""
        suffixes = ("", ".pt_br", ".pt_pt", ".es_es", ".fr_fr")
        missing = []
        for category in CATEGORIES:
            slug = category.doc[:-3] if category.doc.endswith(".md") else category.doc
            for suffix in suffixes:
                candidate = DOCS_DIR / f"{slug}{suffix}.md"
                if not candidate.is_file() or candidate.stat().st_size == 0:
                    missing.append(candidate.name)
        assert missing == [], f"Missing or empty localized category docs: {missing}"
