"""Bandit Python SAST bridge."""

import json
import os
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
    NormalizedFinding,
)


class BanditBridge(ExternalLinterBridge):
    """Bridge for Bandit Python static security testing tool."""

    tool_name = "bandit"
    binary_name = "bandit"

    def run(
        self,
        target_files: list[str],
        repo_path: str = ".",
        diff_only: bool = False,
        timeout: int = 45,
    ) -> ExternalLinterResult:
        binary = self.resolve_binary_path()
        if not binary:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=False,
                warnings=["Binary 'bandit' not found in PATH"],
            )

        # Bandit only applies to Python files (.py)
        py_files = [
            f for f in target_files
            if f.endswith(".py") and os.path.exists(f if os.path.isabs(f) else os.path.join(repo_path, f))
        ]
        if not py_files:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=True,
                findings=[],
            )

        argv = [
            binary,
            "-f",
            "json",
        ] + py_files

        stdout, stderr, code, err = self._execute_subprocess(
            argv, cwd=repo_path, timeout=timeout
        )

        warnings: list[str] = []
        if err:
            warnings.append(f"Bandit execution warning: {err}")
        if stderr and "error" in stderr.lower():
            warnings.append(f"Bandit stderr: {stderr.strip()[:200]}")

        findings = self.parse_output(stdout, repo_path=repo_path)

        return ExternalLinterResult(
            tool_name=self.tool_name,
            available=True,
            findings=findings,
            raw_output=stdout,
            exit_code=code,
            warnings=warnings,
        )

    def parse_output(self, raw_output: str, repo_path: str = ".") -> list[NormalizedFinding]:
        if not raw_output or not raw_output.strip():
            return []

        findings: list[NormalizedFinding] = []
        try:
            data = json.loads(raw_output)
            results = data.get("results", []) if isinstance(data, dict) else []

            for item in results:
                test_id = item.get("test_id", "bandit-test")
                raw_filename = item.get("filename", "")

                # Normalize path
                if os.path.isabs(raw_filename) and repo_path:
                    try:
                        rel_filename = os.path.relpath(raw_filename, repo_path)
                    except ValueError:
                        rel_filename = raw_filename
                else:
                    rel_filename = raw_filename
                rel_filename = rel_filename.replace("\\", "/")

                line_number = int(item.get("line_number", 1))
                line_range = item.get("line_range", [line_number])
                line_end = line_range[-1] if line_range else line_number

                issue_text = item.get("issue_text", "").strip() or f"Bandit issue {test_id}"
                raw_severity = item.get("issue_severity", "MEDIUM").upper()
                raw_confidence = item.get("issue_confidence", "MEDIUM").upper()

                # Severity mapping: HIGH severity + HIGH confidence = error (blocker)
                if raw_severity == "HIGH" and raw_confidence == "HIGH":
                    severity = "error"
                elif raw_severity in ("HIGH", "MEDIUM"):
                    severity = "warning"
                else:
                    severity = "info"

                findings.append(
                    NormalizedFinding(
                        severity=severity,
                        category="security/python",
                        file_path=rel_filename,
                        line_start=line_number,
                        line_end=line_end,
                        message=f"{issue_text} (confidence: {raw_confidence})",
                        source="bandit",
                        rule_id=test_id,
                    )
                )
        except json.JSONDecodeError:
            pass

        return findings

