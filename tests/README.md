# Tests — GitPR

## Required libraries

Tests use the same dependencies as the project plus `pytest`:

```bash
pipenv install --dev
# or
pip install -e . && pip install pytest
```

## Running tests

```bash
# All tests
pipenv run pytest -v
# or
python -m pytest tests/ -v

# A single test file
python -m pytest tests/test_chat_backend.py -v

# A single test class
python -m pytest tests/test_chat_backend.py::TestCallAiChat -v

# A single test method
python -m pytest tests/test_chat_backend.py::TestCallAiChat::test_gemini_success -v
```

## Writing a new test

### 1. File naming

Place your file in `tests/` with the prefix `test_`:

```
tests/
├── test_chat_backend.py
├── test_skill_command.py
└── test_core.py
```

### 2. Structure

Every test file should follow this pattern:

```python
import pytest
from unittest.mock import patch, MagicMock

from src.module_name import function_under_test


class TestFeatureName:
    """Tests for the feature / function."""

    def test_happy_path(self):
        """The normal, expected case."""
        result = function_under_test("valid input")
        assert result is not None

    def test_edge_case(self):
        """What happens with empty / None / boundary inputs."""
        result = function_under_test("")
        assert result == ""

    def test_error_handling(self, capsys):
        """Function should not crash on unexpected errors."""
        with patch("module.dependency", side_effect=Exception("boom")):
            result = function_under_test("input")
        assert result is None
        assert "Error" in capsys.readouterr().out
```

### 3. Mocking external dependencies

All tests must run **offline** — never call real APIs or touch the network.

| What to mock | How |
|---|---|
| HTTP requests | `patch("urllib.request.urlopen", return_value=mock_response)` |
| AI / SDK calls | `patch("src.ai_providers.genai.Client")` or `patch("src.ai_providers.OpenAI")` |
| File system (redirect to tmp) | `monkeypatch.setattr("src.module.Path.home", lambda: tmp_path)` |
| Working directory | `monkeypatch.setattr("src.module.os.getcwd", lambda: str(tmp_path))` |
| Language / locale | `monkeypatch.setattr("src.module.CURRENT_LANG", "en")` |

### 4. Context manager mocks

When the code uses `with urlopen(...) as response:`, the mock needs `__enter__`:

```python
mock_response = MagicMock()
mock_response.read.return_value = b'{"key": "value"}'
mock_response.__enter__.return_value = mock_response  # <-- required for "with" blocks
```

### 5. Asserting console output

Use the `capsys` fixture to capture what `click.secho` / `click.echo` prints:

```python
def test_output(self, capsys):
    function_under_test()
    captured = capsys.readouterr()
    assert "Expected message" in captured.out
```

### 6. Checking translated strings

When a function uses `__()` (i18n), the assertion must account for the current locale:

```python
from src.i18n import __

def test_error_message(self, capsys):
    function_under_test("bad")
    expected = __("❌ Error: {reason}", reason="bad")
    assert expected in capsys.readouterr().out
```

### 7. Temp directories

Use `tmp_path` (built-in pytest fixture) for any file I/O:

```python
def test_file_creation(self, tmp_path):
    output = tmp_path / "output.txt"
    function_that_writes(output)
    assert output.read_text() == "expected content"
```

### 8. Fixtures with autouse

Use `autouse=True` when every test in the class needs the same setup:

```python
class TestSomething:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.module.Path.home", lambda: tmp_path)
        (tmp_path / ".gitpr" / "cache").mkdir(parents=True)
```
