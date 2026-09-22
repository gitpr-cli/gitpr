from pathlib import Path
from src.domain.tests_generation.test_scaffold_builder import build_test_scaffold
from src.domain.tests_generation.test_content_types import TestFramework


def test_scaffold_pest_laravel_service(tmp_path):
    scaffold = build_test_scaffold("app/Services/UserService.php", TestFramework.PEST, str(tmp_path))
    assert scaffold.framework == TestFramework.PEST
    assert scaffold.target_test_path == "tests/Unit/Services/UserServiceTest.php"
    assert scaffold.already_exists is False


def test_scaffold_pest_laravel_controller(tmp_path):
    scaffold = build_test_scaffold("app/Http/Controllers/OrderController.php", TestFramework.PEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/Feature/Http/Controllers/OrderControllerTest.php"


def test_scaffold_pytest_python_source(tmp_path):
    scaffold = build_test_scaffold("src/application/service.py", TestFramework.PYTEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/application/test_service.py"


def test_scaffold_vitest_vue_component(tmp_path):
    scaffold = build_test_scaffold("src/components/Modal.vue", TestFramework.VITEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/components/Modal.spec.js"


def test_scaffold_jest_ts_file(tmp_path):
    scaffold = build_test_scaffold("src/utils/format.ts", TestFramework.JEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/utils/format.test.ts"


def test_scaffold_already_exists(tmp_path):
    test_file = tmp_path / "tests" / "test_core.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("# existing test", encoding="utf-8")

    scaffold = build_test_scaffold("src/core.py", TestFramework.PYTEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/test_core.py"
    assert scaffold.already_exists is True


def test_scaffold_fallback_no_file(tmp_path):
    scaffold = build_test_scaffold(None, TestFramework.PYTEST, str(tmp_path))
    assert scaffold.target_test_path == "tests/test_generated.py"

