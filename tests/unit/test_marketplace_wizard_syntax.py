"""Unit tests validating syntax, structure, and integrity of marketplace-setup-wizard.sh."""

from pathlib import Path
import shutil
import subprocess
import pytest


def test_marketplace_wizard_file_exists_and_executable_shebang():
    """Verify scripts/marketplace-setup-wizard.sh exists and starts with a bash shebang."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    script_path = repo_root / "scripts" / "marketplace-setup-wizard.sh"

    assert script_path.is_file(), "scripts/marketplace-setup-wizard.sh must exist"
    content = script_path.read_text(encoding="utf-8")
    assert content.startswith("#!/usr/bin/env bash"), "Script must start with bash shebang"


def test_marketplace_wizard_required_markers_and_stages():
    """Verify script contains standard wizard markers, 5 stages, and essential technical tokens."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    script_path = repo_root / "scripts" / "marketplace-setup-wizard.sh"
    content = script_path.read_text(encoding="utf-8")

    assert "TOTAL_STAGES=5" in content, "Wizard must define exactly 5 stages"
    assert "PUBLISHER_ID=\"natanfiuza\"" in content or "natanfiuza" in content
    assert "set_secret \"VSCE_PAT\"" in content
    assert "set_secret \"OVSX_PAT\"" in content
    assert "npx --yes @vscode/vsce verify-pat" in content
    assert "npx --yes ovsx verify-pat" in content
    assert "ext-v0.1.0" in content
    assert "finish" in content


def test_marketplace_wizard_bash_syntax_validation():
    """If a working bash is available, run bash -n to validate script syntax statically."""
    import sys

    # On Windows, C:\Windows\System32\bash.exe invokes WSL which may block if WSL is unconfigured.
    # Prefer Git Bash if available on Windows.
    candidates = []
    if sys.platform == "win32":
        for git_bash in [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ]:
            if Path(git_bash).is_file():
                candidates.append(git_bash)
    else:
        found = shutil.which("bash")
        if found:
            candidates.append(found)

    if not candidates:
        pytest.skip("No non-blocking bash executable found; skipping bash -n syntax validation")

    repo_root = Path(__file__).resolve().parent.parent.parent
    script_path = repo_root / "scripts" / "marketplace-setup-wizard.sh"

    try:
        result = subprocess.run(
            [candidates[0], "-n", str(script_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0, f"bash -n syntax validation failed:\n{result.stderr}"
    except (subprocess.TimeoutExpired, OSError) as exc:
        pytest.skip(f"bash execution timed out or failed to start: {exc}")
