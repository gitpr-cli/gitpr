from dataclasses import dataclass, field
from enum import Enum


class TestFramework(str, Enum):
    __test__ = False
    PEST = "pest"
    PHPUNIT = "phpunit"
    JEST = "jest"
    VITEST = "vitest"
    PYTEST = "pytest"
    UNKNOWN = "unknown"


@dataclass
class TestGenerationTarget:
    """Target context to generate tests for (full diff, single file, or specific finding)."""

    __test__ = False
    source_type: str  # "diff" | "file" | "finding"
    file_path: str | None = None
    finding_id: str | None = None
    diff_content: str = ""


@dataclass
class TestScaffold:
    """Target test location and configuration according to framework conventions."""

    __test__ = False
    framework: TestFramework
    target_test_path: str
    already_exists: bool = False


@dataclass
class GeneratedTest:
    """Complete output of test generation."""

    scaffold: TestScaffold
    content: str
    covered_scenarios: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
