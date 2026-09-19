"""Scenario registry — the example diff and the recorded answers the tour replays.

Scenarios are Python modules, not JSON data files, because the package ships
zero non-``.py`` files: ``pyproject.toml`` collects ``src`` and ``src.*`` through
``packages.find`` and there is no ``package_data``, so a ``.json`` fixture would
be missing from the wheel with nothing failing at build time.

Each scenario module exposes ``NAME``, ``DIFF`` and ``TEXT``. ``DIFF`` is
repository code and stays in English in every language; ``TEXT`` holds the
prose the tour narrates, keyed by language code, with ``en`` always present as
the fallback.

One deviation from a byte-exact unified diff: blank lines inside ``DIFF`` are
stored empty instead of carrying the single space a real diff uses as its
context marker — no editor in the toolchain preserves trailing whitespace, so
it cannot be kept in source. Hunk headers must still add up under the rule that
an empty line counts as context, which ``tests/demo/test_demo_scenarios.py``
enforces. Nothing parses or applies ``DIFF``: the tour renders it.
"""

from dataclasses import dataclass

from src.i18n import __

from src.demo.scenarios import laravel_bug_fix, security_issue


class DemoScenarioError(Exception):
    """The requested scenario name is not in the registry."""


@dataclass(frozen=True)
class DemoScenario:
    """One example diff together with the answers generated for it.

    ``lang`` reports the language actually used, which is not necessarily the
    one requested — a scenario whose translation is not written yet falls back
    to English.
    """

    name: str
    lang: str
    title: str
    description: str
    diff: str
    commit_message: str
    review: str
    linter: dict
    pr_description: str
    other_scenarios: tuple


_LANG_ALIASES = {
    "en": "en",
    "en_us": "en",
    "en_gb": "en",
    "pt": "pt_br",
    "pt_br": "pt_br",
    "pt_pt": "pt_pt",
    "es": "es_es",
    "es_es": "es_es",
    "fr": "fr_fr",
    "fr_fr": "fr_fr",
}

FALLBACK_LANG = "en"

_MODULES = {
    laravel_bug_fix.NAME: laravel_bug_fix,
    security_issue.NAME: security_issue,
}

SCENARIO_NAMES = tuple(_MODULES)
DEFAULT_SCENARIO = SCENARIO_NAMES[0]


def _current_lang():
    """The interface language as it is right now.

    Read at call time: ``i18n.set_lang()`` — the one ``--lang`` calls — rebinds
    the module global instead of mutating it, so a module-level import would
    keep the value detected at start-up forever.
    """
    from src.i18n import CURRENT_LANG

    return CURRENT_LANG or FALLBACK_LANG


def _resolve_lang(lang):
    """Map an interface language code onto a scenario text key."""
    code = (lang or "").strip().lower().replace("-", "_")
    return _LANG_ALIASES.get(code, FALLBACK_LANG)


def load_scenario(name=None, lang=None):
    """Return the scenario ``name`` with its prose resolved to ``lang``.

    ``name`` defaults to the first registered scenario, ``lang`` to the current
    interface language. Raises ``DemoScenarioError`` for an unknown name.
    """
    resolved = (name or DEFAULT_SCENARIO).strip().lower()
    module = _MODULES.get(resolved)

    if module is None:
        raise DemoScenarioError(
            __(
                "Unknown scenario: '{name}'. Available scenarios: {available}.",
                name=name,
                available=", ".join(SCENARIO_NAMES),
            )
        )

    requested = _resolve_lang(lang if lang is not None else _current_lang())
    text = module.TEXT.get(requested) or module.TEXT[FALLBACK_LANG]
    used = requested if requested in module.TEXT else FALLBACK_LANG

    return DemoScenario(
        name=module.NAME,
        lang=used,
        title=text["title"],
        description=text["description"],
        diff=module.DIFF,
        commit_message=text["commit_message"],
        review=text["review"],
        linter=text["linter"],
        pr_description=text["pr_description"],
        other_scenarios=tuple(n for n in SCENARIO_NAMES if n != module.NAME),
    )
