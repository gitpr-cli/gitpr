"""Semgrep multi-language SAST bridge."""

import json
import os
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
    NormalizedFinding,
)


class SemgrepBridge(ExternalLinterBridge):
    """Bridge for Semgrep multi-language static analysis."""

    tool_name = "semgrep"
    binary_name = "semgrep"

    def run(
        self,
        target_files: list[str],
        repo_path: str = ".",
        diff_only: bool = False,
        timeout: int = 60,
    ) -> ExternalLinterResult:
        binary = self.resolve_binary_path()
        if not binary:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=False,
                warnings=["Binary 'semgrep' not found in PATH"],
            )

        if not target_files:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=True,
                findings=[],
            )

        # Semgrep runs on target files or directory
        # semgrep --config auto --json --timeout <timeout> <files...>
        valid_files = [
            f for f in target_files
            if os.path.exists(f if os.path.isabs(f) else os.path.join(repo_path, f))
        ]
        if not valid_files:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=True,
                findings=[],
            )

        argv = [
            binary,
            "--config",
            "auto",
            "--json",
            "--timeout",
            str(timeout),
        ] + valid_files

        stdout, stderr, code, err = self._execute_subprocess(
            argv, cwd=repo_path, timeout=timeout + 15
        )

        warnings: list[str] = []
        if err:
            warnings.append(f"Semgrep execution warning: {err}")
        if stderr and "error" in stderr.lower():
            warnings.append(f"Semgrep stderr: {stderr.strip()[:200]}")

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
                check_id = item.get("check_id", "semgrep-rule")
                raw_path = item.get("path", "")
                
                # Normalize path
                if os.path.isabs(raw_path) and repo_path:
                    try:
                        rel_path = os.path.relpath(raw_path, repo_path)
                    except ValueError:
                        rel_path = raw_path
                else:
                    rel_path = raw_path
                rel_path = rel_path.replace("\\", "/")

                start = item.get("start", {})
                end = item.get("end", {})
                line_start = int(start.get("line", 1))
                line_end = int(end.get("line", line_start))

                extra = item.get("extra", {})
                message = extra.get("message", "").strip() or f"Semgrep issue {check_id}"
                raw_severity = extra.get("severity", "WARNING").upper()

                # Map severity
                if raw_severity in ("ERROR", "CRITICAL", "BLOCKER"):
                    severity = "error"
                elif raw_severity in ("WARNING", "WARN"):
                    severity = "warning"
                else:
                    severity = "info"

                findings.append(
                    NormalizedFinding(
                        severity=severity,
                        category="security/sast",
                        file_path=rel_path,
                        line_start=line_start,
                        line_end=line_end,
                        message=message,
                        source="semgrep",
                        rule_id=check_id,
                    )
                )
        except json.JSONDecodeError:
            pass

        return findings

