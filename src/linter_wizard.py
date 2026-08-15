import os
import json
import yaml
import click
import urllib.request
from pathlib import Path
from dotenv import load_dotenv, set_key
from src.config import resolve_skill_path
from src.core import get_doc_url
from src.i18n import __
from src.updater import __lang_version__

# Remote template that controls the available linter presets (editable without a release)
_LINTER_PRESETS_URL = "https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/gitpr.linter-presets.json"

# Built-in fallback presets (used when the remote template is unreachable)
_LINTER_PRESETS = [
    {
        "name": "PHP_CodeSniffer (PHPCS)",
        "extensions": ["php"],
        "command": "vendor/bin/phpcs --report=checkstyle",
        "install_msg": "composer require --dev squizlabs/php_codesniffer",
    },
    {
        "name": "ESLint (JavaScript/TypeScript)",
        "extensions": ["js", "ts", "vue", "jsx", "tsx"],
        "command": "npx eslint --format checkstyle",
        "install_msg": "npm install --save-dev eslint",
    },
    {
        "name": "Stylelint (CSS/SCSS)",
        "extensions": ["css", "scss", "sass", "less", "vue"],
        "command": "npx stylelint --custom-formatter=node_modules/stylelint-checkstyle-formatter",
        "install_msg": "npm install --save-dev stylelint stylelint-checkstyle-formatter",
    },
]


def load_linter_presets():
    """
    Loads the external linter presets used by the setup wizard.

    Resolution order (same chain as the smart-excludes list):
    1. Local copy at ~/.gitpr/conf/gitpr.linter-presets.json when its version
       marker (LINTER_PRESETS_VERSION in ~/.gitpr/.env) matches __lang_version__.
    2. Fresh download from the remote template (saved locally + marker updated).
    3. Stale local copy when the download fails.
    4. Built-in _LINTER_PRESETS as last resort.

    Silent on failure — the wizard must never break because of this list.
    """
    env_file = Path.home() / ".gitpr" / ".env"
    load_dotenv(env_file)

    conf_dir = Path.home() / ".gitpr" / "conf"
    local_file = conf_dir / "gitpr.linter-presets.json"
    needs_update = os.getenv("LINTER_PRESETS_VERSION") != __lang_version__

    def _extract(data):
        presets = data.get("linters", [])
        return presets if isinstance(presets, list) else []

    # 1. Local copy is present and up to date
    if local_file.exists() and not needs_update:
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                presets = _extract(json.load(f))
                if presets:
                    return presets
        except Exception:
            pass

    # 2. Download the updated list from the remote template
    try:
        with urllib.request.urlopen(_LINTER_PRESETS_URL, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        conf_dir.mkdir(parents=True, exist_ok=True)
        with open(local_file, "w", encoding="utf-8", errors="replace") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        set_key(str(env_file), "LINTER_PRESETS_VERSION", __lang_version__)
        presets = _extract(data)
        if presets:
            return presets
    except Exception:
        pass

    # 3. Offline fallback: reuse the local copy even if outdated
    if local_file.exists():
        try:
            with open(local_file, "r", encoding="utf-8", errors="replace") as f:
                presets = _extract(json.load(f))
                if presets:
                    return presets
        except Exception:
            pass

    # 4. Last resort: built-in defaults
    return _LINTER_PRESETS


def run_linter_setup_wizard():
    """
    Executes the interactive wizard to configure external linters via CLI.
    """
    presets = load_linter_presets()

    click.secho(__("\n🔌 GitPR External Linter Setup"), fg="cyan", bold=True)
    click.echo(
        __(
            "Choose an external linter to configure as a bridge (Checkstyle XML format):"
        )
    )

    for i, data in enumerate(presets, start=1):
        click.echo(f"  [{i}] {data.get('name', '')}")

    click.echo(__("  [0] Cancel"))

    choices = [str(i) for i in range(len(presets) + 1)]
    choice = click.prompt(__("Select an option"), type=click.Choice(choices))
    choice_index = int(choice)

    if choice_index == 0:
        click.secho(__("❌ Setup cancelled."), fg="yellow")
        return

    selected_linter = presets[choice_index - 1]
    linter_name = selected_linter.get("name", "")

    # Shows the native install instruction
    click.secho(
        __("\n🛠️  Step 1: Install the linter in your project"), fg="yellow", bold=True
    )
    click.echo(
        __(
            "Run the following command in your terminal if you haven't installed it yet:"
        )
    )
    click.secho(f"  {selected_linter.get('install_msg', '')}\n", fg="green")

    # Updates the YAML file
    click.secho(__("⚙️  Step 2: Configuring .gitpr.linter.yml"), fg="yellow", bold=True)
    local_path = resolve_skill_path(".gitpr.linter.yml")

    config = {}
    if os.path.exists(local_path):
        try:
            with open(local_path, "r", encoding="utf-8", errors="replace") as f:
                config = yaml.safe_load(f) or {}
        except Exception as e:
            click.secho(
                __("❌ Error reading current linter config: {error}", error=str(e)),
                fg="red",
            )
            return

    if "external_linters" not in config:
        config["external_linters"] = []

    # Avoid duplicate entries
    already_exists = any(
        l.get("name") == linter_name for l in config["external_linters"]
    )

    if already_exists:
        click.secho(
            __("⚠️  The linter '{name}' is already configured.", name=linter_name),
            fg="yellow",
        )
    else:
        new_entry = {
            "name": linter_name,
            "command": selected_linter.get("command", ""),
            "extensions": selected_linter.get("extensions", []),
        }
        config["external_linters"].append(new_entry)

        try:
            # The .gitpr/skill/ folder may not exist yet on fresh projects
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "w", encoding="utf-8", errors="replace") as f:
                yaml.dump(
                    config,
                    f,
                    allow_unicode=True,
                    default_flow_style=False,
                    sort_keys=False,
                )
            click.secho(
                __(
                    "✅ Successfully added '{name}' to your configuration!",
                    name=linter_name,
                ),
                fg="green",
                bold=True,
            )
        except Exception as e:
            click.secho(
                __("❌ Error saving configuration: {error}", error=str(e)), fg="red"
            )

    # Full documentation link
    click.echo(__("For more details, see the full documentation:"))
    click.secho(
        f"  {get_doc_url('linter-regras-customizadas.md')}", fg="blue", underline=True
    )
