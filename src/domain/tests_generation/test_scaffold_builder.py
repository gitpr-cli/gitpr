import os
from pathlib import Path
from src.domain.tests_generation.test_content_types import TestFramework, TestScaffold


def build_test_scaffold(
    file_path: str | None,
    framework: TestFramework,
    repo_path: str = ".",
) -> TestScaffold:
    """Computes the conventional test file path for a given source file and test framework."""
    root = Path(repo_path)
    
    if not file_path:
        # Default test target paths when no specific source file is provided (e.g. general diff)
        fallback_map = {
            TestFramework.PEST: "tests/Feature/GeneratedTest.php",
            TestFramework.PHPUNIT: "tests/Unit/GeneratedTest.php",
            TestFramework.VITEST: "tests/generated.test.ts",
            TestFramework.JEST: "tests/generated.test.js",
            TestFramework.PYTEST: "tests/test_generated.py",
            TestFramework.UNKNOWN: "tests/test_generated.txt",
        }
        rel_test_path = fallback_map.get(framework, "tests/test_generated.txt")
        full_path = root / rel_test_path
        return TestScaffold(
            framework=framework,
            target_test_path=rel_test_path.replace("\\", "/"),
            already_exists=full_path.exists(),
        )

    # Normalize file path
    clean_path = file_path.replace("\\", "/")
    path_obj = Path(clean_path)
    stem = path_obj.stem
    ext = path_obj.suffix.lower()

    if framework in (TestFramework.PEST, TestFramework.PHPUNIT):
        # Handle PHP / Laravel conventions
        # app/Services/UserService.php -> tests/Feature/Services/UserServiceTest.php
        # app/Http/Controllers/Api/UserController.php -> tests/Feature/Http/Controllers/Api/UserControllerTest.php
        parts = list(path_obj.parts)
        if parts and parts[0] == "app":
            parts = parts[1:]  # remove app/
        
        # Decide Feature vs Unit (Controllers, Livewire, Http -> Feature; Services, Actions, Models -> Unit/Feature)
        first_segment = parts[0] if parts else ""
        suite_folder = "Feature" if first_segment in ("Http", "Controllers", "Livewire", "Filament") else "Unit"
        
        sub_dirs = parts[:-1]
        test_file_name = f"{stem}Test.php" if not stem.endswith("Test") else f"{stem}.php"
        rel_test_path = str(Path("tests") / suite_folder / Path(*sub_dirs) / test_file_name)

    elif framework in (TestFramework.VITEST, TestFramework.JEST):
        # Handle JS / TS / Vue / React conventions
        # src/components/Button.vue -> tests/unit/components/Button.spec.js or src/components/Button.test.ts
        is_ts = ext in (".ts", ".tsx")
        test_ext = ".test.ts" if is_ts else (".spec.js" if ext == ".vue" else ".test.js")
        
        parts = list(path_obj.parts)
        if parts and parts[0] == "src":
            parts = parts[1:]
        
        sub_dirs = parts[:-1]
        test_file_name = f"{stem}{test_ext}"
        rel_test_path = str(Path("tests") / Path(*sub_dirs) / test_file_name)

    elif framework == TestFramework.PYTEST:
        # Handle Python / Pytest conventions
        # src/core.py -> tests/test_core.py
        # app/services/auth.py -> tests/services/test_auth.py
        parts = list(path_obj.parts)
        if parts and parts[0] in ("src", "app"):
            parts = parts[1:]
        
        sub_dirs = parts[:-1]
        test_file_name = f"test_{stem}.py" if not stem.startswith("test_") else f"{stem}.py"
        rel_test_path = str(Path("tests") / Path(*sub_dirs) / test_file_name)

    else:
        # Unknown fallback
        rel_test_path = f"tests/test_{stem}{ext}"

    rel_test_path = rel_test_path.replace("\\", "/")
    full_path = root / rel_test_path

    return TestScaffold(
        framework=framework,
        target_test_path=rel_test_path,
        already_exists=full_path.exists(),
    )

