"""Base classes and data models for external linter & SAST bridges."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
import shutil
import subprocess


@dataclass
class NormalizedFinding:
    """Standardized finding model used across all GitPR SAST & linter tools."""

    severity: str  # "error" | "warning" | "info"
    category: str
    file_path: str
    line_start: int
    line_end: int
    message: str
    source: str  # "semgrep" | "gitleaks" | "bandit" | etc.
    rule_id: str | None = None


@dataclass
class ExternalLinterResult:
    """Execution result returned by an external linter or SAST bridge."""

    tool_name: str
    available: bool
    findings: list[NormalizedFinding] = field(default_factory=list)
    raw_output: str = ""
    exit_code: int | None = None
    warnings: list[str] = field(default_factory=list)


class ExternalLinterBridge(ABC):
    """Abstract base class for running external linters and SAST tools securely."""

    tool_name: str = "base"
    binary_name: str = "base"

    def is_available(self) -> bool:
        """Checks if the external binary exists in PATH without invoking it."""
        try:
            return shutil.which(self.binary_name) is not None
        except Exception:
            return False

    def resolve_binary_path(self) -> str | None:
        """Resolves the executable path via shutil.which for safe invocation on Windows and Unix."""
        try:
            return shutil.which(self.binary_name)
        except Exception:
            return None

    def _execute_subprocess(
        self,
        argv: list[str],
        cwd: str | None = None,
        timeout: int = 60,
    ) -> tuple[str, str, int | None, str | None]:
        """Runs a subprocess with security hardening invariants.

        Invariants enforced:
        1. shell=False (list of args).
        2. Strict timeout.
        3. Capture stdout & stderr with encoding='utf-8' and errors='replace'.
        4. DEVNULL stdin.
        """
        try:
            result = subprocess.run(
                argv,
                cwd=cwd,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            return result.stdout, result.stderr, result.returncode, None
        except subprocess.TimeoutExpired:
            return "", "", None, f"Execution timed out after {timeout} seconds"
        except FileNotFoundError:
            return "", "", None, f"Binary '{argv[0]}' not found"
        except Exception as e:
            return "", "", None, str(e)

    @abstractmethod
    def run(
        self,
        target_files: list[str],
        repo_path: str = ".",
        diff_only: bool = True,
        timeout: int = 60,
    ) -> ExternalLinterResult:
        """Executes the bridge on target files within repo_path."""
        ...

    @abstractmethod
    def parse_output(self, raw_output: str, repo_path: str = ".") -> list[NormalizedFinding]:
        """Parses the raw JSON or text output into NormalizedFindings."""
        ...

