import json
import os
from pathlib import Path
from src.domain.tests_generation.test_content_types import TestFramework


def detect_test_framework(repo_path: str = ".", framework_override: TestFramework | str | None = None) -> tuple[TestFramework, list[str]]:
    """Detects the primary test framework in the repository or uses the explicit override.
    
    Returns:
        tuple[TestFramework, list[str]]: The resolved TestFramework and any warnings.
    """
    warnings: list[str] = []

    if framework_override:
        if isinstance(framework_override, str):
            val = framework_override.strip().lower()
            try:
                return TestFramework(val), warnings
            except ValueError:
                warnings.append(f"Unknown framework override '{framework_override}', falling back to auto-detection.")
        elif isinstance(framework_override, TestFramework):
            return framework_override, warnings

    root = Path(repo_path)

    # 1. PHP Indicators
    if (root / "pest.php").exists() or (root / "tests" / "Pest.php").exists():
        return TestFramework.PEST, warnings
    if (root / "phpunit.xml").exists() or (root / "phpunit.dist.xml").exists() or (root / "phpunit.xml.dist").exists():
        return TestFramework.PHPUNIT, warnings
    
    # Check composer.json for pest/phpunit
    composer_json = root / "composer.json"
    if composer_json.exists():
        try:
            with open(composer_json, "r", encoding="utf-8", errors="replace") as f:
                cdata = json.load(f)
                require_dev = cdata.get("require-dev", {})
                require = cdata.get("require", {})
                all_reqs = {**require, **require_dev}
                if "pestphp/pest" in all_reqs:
                    return TestFramework.PEST, warnings
                if "phpunit/phpunit" in all_reqs:
                    return TestFramework.PHPUNIT, warnings
        except Exception:
            pass

    # 2. JavaScript / TypeScript Indicators
    vitest_configs = [
        "vitest.config.ts",
        "vitest.config.js",
        "vitest.config.mjs",
        "vitest.config.mts",
        "vite.config.ts",
        "vite.config.js",
    ]
    for cfg in vitest_configs:
        if (root / cfg).exists():
            return TestFramework.VITEST, warnings

    jest_configs = [
        "jest.config.js",
        "jest.config.ts",
        "jest.config.mjs",
        "jest.config.cjs",
        "jest.config.json",
    ]
    for cfg in jest_configs:
        if (root / cfg).exists():
            return TestFramework.JEST, warnings

    package_json = root / "package.json"
    if package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8", errors="replace") as f:
                pdata = json.load(f)
                dev_deps = pdata.get("devDependencies", {})
                deps = pdata.get("dependencies", {})
                all_deps = {**deps, **dev_deps}
                scripts = pdata.get("scripts", {})
                
                if "vitest" in all_deps or "vitest" in " ".join(scripts.values()):
                    return TestFramework.VITEST, warnings
                if "jest" in all_deps or "jest" in " ".join(scripts.values()):
                    return TestFramework.JEST, warnings
        except Exception:
            pass

    # 3. Python Indicators
    pytest_files = [
        "pytest.ini",
        "conftest.py",
        "tox.ini",
        "setup.cfg",
    ]
    for p_file in pytest_files:
        if (root / p_file).exists():
            return TestFramework.PYTEST, warnings

    pyproject_toml = root / "pyproject.toml"
    if pyproject_toml.exists():
        try:
            with open(pyproject_toml, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
                if "[tool.pytest" in content or "pytest" in content:
                    return TestFramework.PYTEST, warnings
        except Exception:
            pass

    # Check for tests/ directory containing python test files
    tests_dir = root / "tests"
    if tests_dir.exists() and tests_dir.is_dir():
        py_tests = list(tests_dir.glob("test_*.py")) + list(tests_dir.glob("*_test.py"))
        if py_tests:
            return TestFramework.PYTEST, warnings

    warnings.append("Could not detect test framework automatically. Use --framework to specify one.")
    return TestFramework.UNKNOWN, warnings

