import urllib.request
import json
import os
import click
from datetime import datetime

# Current version of your local executable (Update this on every new build!)
# ── Must stay ABOVE the i18n import: i18n.py lazily imports __lang_version__
#     from here, and pyproject.toml reads __version__ via setuptools attr:.
__version__ = "1.2.0"  # GitPR current version
__lang_version__ = "v0.0.28"  # Language dictionary version control
__scripts_version__ = (
    "v0.0.3"  # Git Hook scripts version control (independent from __lang_version__)
)

from src.i18n import __

PYPI_API_URL = "https://pypi.org/pypi/gitpr-cli/json"

# Environment switch used to mute the mandatory update check (test harness and
# offline automation). Read as a plain flag: any non-empty value disables it.
SKIP_UPDATE_CHECK_ENV = "GITPR_SKIP_UPDATE_CHECK"


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


def is_update_check_disabled():
    """Returns True when the update check must be muted for this execution."""
    return bool(os.environ.get(SKIP_UPDATE_CHECK_ENV, "").strip())


def get_latest_remote_version():
    """Fetches the latest version published on PyPI, with a daily cache."""
    cache_file = get_update_cache_file()
    today = datetime.now().strftime("%Y-%m-%d")

    # Try to read from cache to avoid slowing down the user's terminal
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
                cache_data = json.load(f)
            if cache_data.get("date") == today:
                return cache_data.get("version", "")
        except Exception:
            pass

    # Fetch from Web if cache expired
    latest_version = ""

    try:
        req = urllib.request.Request(PYPI_API_URL, headers={"User-Agent": "GitPR-Updater"})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
        latest_version = data.get("info", {}).get("version", "")

        if latest_version:
            os.makedirs(get_gitpr_dir(), exist_ok=True)
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump({"date": today, "version": latest_version}, f)

    except Exception:
        pass  # Silent failure in case of no internet

    return latest_version


def enforce_update_required():
    """Blocks execution while a newer GitPR version is published on PyPI.

    Prints the upgrade instructions and returns True when the caller must stop.
    Returns False when the local version is current, when the remote version is
    unknown (offline, so the user could not upgrade anyway) or when the check is
    disabled via GITPR_SKIP_UPDATE_CHECK.
    """
    if is_update_check_disabled():
        return False

    latest_version = get_latest_remote_version()

    if not latest_version:
        return False

    if parse_version(latest_version) <= parse_version(__version__):
        return False

    click.echo("")
    click.secho(
        __(
            "⚠️ A new version of GitPR is available: {current_version} -> {latest_version}",
            current_version=__version__,
            latest_version=latest_version,
        ),
        fg="yellow",
        bold=True,
    )
    click.secho(
        __("GitPR must be updated before it can run: pip install --upgrade gitpr-cli"),
        fg="cyan",
        bold=True,
    )
    click.echo("")
    return True


def check_and_update():
    """Function triggered only when the user forces the --update flag."""
    latest_version = get_latest_remote_version()

    if not latest_version:
        click.secho(__("❌ Could not check for updates at this moment."), fg="red")
        return

    if parse_version(latest_version) > parse_version(__version__):
        click.secho(
            __(
                "\n🚀 New GitPR version found (v{latest_version})!",
                latest_version=latest_version,
            ),
            fg="green",
            bold=True,
        )
        click.secho(
            __("Run to update: pip install --upgrade gitpr-cli"), fg="cyan", bold=True
        )
    else:
        click.secho(
            __("✅ You are already using the latest version of GitPR."), fg="green"
        )
