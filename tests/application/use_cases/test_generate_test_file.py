import json
from unittest.mock import patch
from src.application.use_cases.generate_test_file import generate_test_file, validate_test_syntax
from src.domain.tests_generation.test_content_types import TestFramework, TestGenerationTarget


def test_validate_test_syntax_python_valid():
    valid_code = "def test_ok():\n    assert True\n"
    is_valid, err = validate_test_syntax(valid_code, TestFramework.PYTEST)
    assert is_valid is True
    assert err is None


def test_validate_test_syntax_python_invalid():
    invalid_code = "def test_fail(\n"
    is_valid, err = validate_test_syntax(invalid_code, TestFramework.PYTEST)
    assert is_valid is False
    assert err is not None


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="dummy-key")
def test_generate_test_file_dry_run(mock_key, mock_ai, tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
    mock_ai.return_value = json.dumps({
        "content": "def test_example():\n    assert 1 == 1\n",
        "covered_scenarios": ["Scenario 1: Simple calculation"],
        "warnings": [],
    })

    target = TestGenerationTarget(
        source_type="file",
        file_path="src/calculator.py",
        diff_content="@@ -1 +1 @@\n+def add(a, b): return a + b",
    )

    result = generate_test_file(
        target=target,
        repo_path=str(tmp_path),
        apply=False,
    )

    assert result.scaffold.framework == TestFramework.PYTEST
    assert result.scaffold.target_test_path == "tests/test_calculator.py"
    assert "def test_example" in result.content
    assert len(result.covered_scenarios) == 1
    # Dry run should not write to disk
    assert not (tmp_path / "tests" / "test_calculator.py").exists()


@patch("src.application.use_cases.generate_test_file.call_ai_model")
@patch("src.application.use_cases.generate_test_file.get_api_key", return_value="dummy-key")
def test_generate_test_file_apply(mock_key, mock_ai, tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
    mock_ai.return_value = json.dumps({
        "content": "def test_created():\n    assert True\n",
        "covered_scenarios": ["Creation test"],
        "warnings": [],
    })

    target = TestGenerationTarget(
        source_type="file",
        file_path="src/dummy.py",
        diff_content="+dummy",
    )

    result = generate_test_file(
        target=target,
        repo_path=str(tmp_path),
        apply=True,
    )

    dest = tmp_path / "tests" / "test_dummy.py"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "def test_created():\n    assert True\n"

