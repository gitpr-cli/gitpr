import json
import os
import tempfile
from datetime import datetime

import click
from packaging.version import InvalidVersion, Version

# Canonical Single Source of Truth (SSOT) for GitPR package version (PyPI distribution)
# ── Must stay ABOVE the i18n import: i18n.py lazily imports __lang_version__
#     from here, and pyproject.toml reads __version__ via setuptools attr:.
__version__ = "1.4.4"  # GitPR current package version (Canonical SSOT)
__lang_version__ = "v0.0.37"  # Language dictionary version control (asset, independent of package version)
__scripts_version__ = (
    "v0.0.4"  # Git Hook scripts version control (independent from __lang_version__)
)

from src.i18n import __
from src.net import bounded_urlopen

PYPI_API_URL = "https://pypi.org/pypi/gitpr-cli/json"

# How long a PyPI answer is trusted before the next check goes back online.
# A rolling window, not the local calendar day: a release published after the
# first run of the day used to stay invisible until midnight.
UPDATE_CACHE_TTL_SECONDS = 3600

# Wall-clock ceiling for the PyPI fetch, DNS resolution included.
UPDATE_FETCH_HARD_TIMEOUT = 3.0

# Environment switch used to mute the mandatory update check (test harness and
# offline automation). Parsed as a strict boolean: only _SKIP_TRUTHY_VALUES
# disable it, so `GITPR_SKIP_UPDATE_CHECK=false` still checks.
SKIP_UPDATE_CHECK_ENV = "GITPR_SKIP_UPDATE_CHECK"
_SKIP_TRUTHY_VALUES = ("1", "true", "yes", "on", "y")


def get_gitpr_dir():
    """Returns the ~/.gitpr/ directory path."""
    return os.path.join(os.path.expanduser("~"), ".gitpr")


def get_update_cache_file():
    """Returns the path to the update cache file."""
    return os.path.join(get_gitpr_dir(), "update_cache.json")


def _coerce_version(value):
    """Parses *value* as a PEP 440 version, or returns None when it is not one."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    # packaging rejects a leading "v"; the old helper stripped every "v" in the
    # string, which corrupted suffixes such as 1.2.3-dev.
    if text[:1] in ("v", "V"):
        text = text[1:]
    if not text:
        return None
    try:
        return Version(text)
    except InvalidVersion:
        return None


def parse_version(version_str):
    """Converts 'v0.1.0' or '0.1.0' into a tuple (0, 1, 0) for version math.

    Kept for compatibility with outside callers. The tuple is lossy for
    pre/post/dev markers, so the update gate itself compares Version objects
    through _is_newer() instead.
    """
    parsed = _coerce_version(version_str)
    return parsed.release if parsed is not None else (0, 0, 0)


def is_update_check_disabled():
    """Returns True when the update check must be muted for this execution."""
    value = os.environ.get(SKIP_UPDATE_CHECK_ENV, "")
    return value.strip().lower() in _SKIP_TRUTHY_VALUES


def _cache_is_fresh(cache_data, now=None):
    """Whether *cache_data* carries a timestamp inside the freshness window.

    A timestamp in the future (the clock moved backwards) counts as stale, so
    a clock jump can never freeze the cache on an old answer indefinitely.
    """
    checked_at = cache_data.get("checked_at")
    if not isinstance(checked_at, str):
        return False
    try:
        written_at = datetime.fromisoformat(checked_at)
        current = datetime.now() if now is None else now
        age = (current - written_at).total_seconds()
    except (TypeError, ValueError):
        # Not a valid timestamp, or a timezone-aware stamp this cache never writes.
        return False
    return 0 <= age < UPDATE_CACHE_TTL_SECONDS


def _read_cached_version(cache_file):
    """Returns the cached PyPI version while it is still fresh, else "".

    Only the current schema is read: a document from the former calendar-day
    cache has no ``checked_at`` and therefore counts as expired.
    """
    try:
        with open(cache_file, "r", encoding="utf-8", errors="replace") as f:
            cache_data = json.load(f)
    except Exception:
        return ""

    if not isinstance(cache_data, dict) or not _cache_is_fresh(cache_data):
        return ""

    version = cache_data.get("version")
    if isinstance(version, str) and version.strip():
        return version.strip()
    return ""


def _write_cached_version(cache_file, version):
    """Writes the cache atomically; the caller treats a failure as non-fatal."""
    folder = os.path.dirname(cache_file)
    if folder:
        os.makedirs(folder, exist_ok=True)

    payload = {"checked_at": datetime.now().isoformat(), "version": version}
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=folder or ".",
        prefix=".update-cache-",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            json.dump(payload, handle)
        os.replace(handle.name, cache_file)
    except Exception:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def _fetch_pypi_version():
    """Returns the version published on PyPI, or "" when it cannot be read."""
    raw = bounded_urlopen(
        PYPI_API_URL,
        timeout=3,
        hard_timeout=UPDATE_FETCH_HARD_TIMEOUT,
        headers={"User-Agent": "GitPR-Updater"},
    )
    if not raw:
        return ""

    try:
        data = json.loads(raw.decode("utf-8", errors="replace"))
        version = data["info"]["version"]
    except Exception:
        return ""

    # Only a parseable version is trusted: a captive portal or a malformed
    # mirror must not poison the cache for a whole hour.
    if _coerce_version(version) is None:
        return ""
    return version.strip()


def get_latest_remote_version(force=False):
    """Fetches the latest version published on PyPI, with a one-hour cache.

    ``force=True`` (the ``--update`` flag) always asks PyPI: that command
    promises an immediate verification, so it must not answer from the cache.
    Returns "" when the remote version is unknown — offline, stalled DNS, or a
    body that is not a version — and the caller then lets the run proceed.
    """
    cache_file = get_update_cache_file()

    if not force:
        cached = _read_cached_version(cache_file)
        if cached:
            return cached

    latest_version = _fetch_pypi_version()
    if latest_version:
        try:
            _write_cached_version(cache_file, latest_version)
        except Exception:
            pass  # A read-only home or a locked file must not hide the answer
    return latest_version


def _is_newer(remote_version, local_version=None):
    """Whether *remote_version* is a version this install should upgrade to.

    PEP 440 ordering instead of a tuple comparison, so 1.4.10 > 1.4.9 and
    pre/post/dev markers follow the standard. A remote pre-release is ignored
    while the local install is stable: pip will not install it without --pre,
    so blocking would tell the user to run a command that does nothing. An
    unparseable version on either side is "unknown", never "newer".
    """
    remote = _coerce_version(remote_version)
    local = _coerce_version(__version__ if local_version is None else local_version)
    if remote is None or local is None:
        return False
    if remote.is_prerelease and not local.is_prerelease:
        return False
    return remote > local


def enforce_update_required():
    """Blocks execution while a newer GitPR version is published on PyPI.

    Prints the upgrade instructions and returns True when the caller must stop.
    Returns False when the local version is current, when the remote version is
    unknown (offline, so the user could not upgrade anyway), when it is a
    pre-release a stable install cannot move to, or when the check is disabled
    via GITPR_SKIP_UPDATE_CHECK.
    """
    if is_update_check_disabled():
        return False

    latest_version = get_latest_remote_version()

    if not _is_newer(latest_version):
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
    latest_version = get_latest_remote_version(force=True)

    if not latest_version:
        click.secho(__("❌ Could not check for updates at this moment."), fg="red")
        return

    if _is_newer(latest_version):
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
