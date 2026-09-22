"""Gitleaks SAST & secret scanning bridge."""

import json
import os
import tempfile
from src.infrastructure.linter.external.base_bridge import (
    ExternalLinterBridge,
    ExternalLinterResult,
    NormalizedFinding,
)


def mask_secret_value(secret: str) -> str:
    """Masks secret values so they never leak into logs, telemetry, or findings."""
    if not secret:
        return "[MASKED]"
    secret = secret.strip()
    if len(secret) <= 4:
        return "****"
    return secret[:4] + "*" * min(len(secret) - 4, 12)


class GitleaksBridge(ExternalLinterBridge):
    """Bridge for Gitleaks secret detection tool with entropy checks."""

    tool_name = "gitleaks"
    binary_name = "gitleaks"

    def run(
        self,
        target_files: list[str],
        repo_path: str = ".",
        diff_only: bool = True,
        timeout: int = 30,
    ) -> ExternalLinterResult:
        binary = self.resolve_binary_path()
        if not binary:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=False,
                warnings=["Binary 'gitleaks' not found in PATH"],
            )

        if not target_files:
            return ExternalLinterResult(
                tool_name=self.tool_name,
                available=True,
                findings=[],
            )

        # Gitleaks detect with temporary JSON report file
        findings: list[NormalizedFinding] = []
        warnings: list[str] = []
        raw_output_collected: list[str] = []
        exit_codes: list[int | None] = []

        # We scan each target file using --no-git --source <file> to keep diff-only scope
        # and avoid scanning entire repository git history
        with tempfile.TemporaryDirectory() as tmpdir:
            for file_path in target_files:
                full_path = (
                    file_path
                    if os.path.isabs(file_path)
                    else os.path.join(repo_path, file_path)
                )
                if not os.path.exists(full_path):
                    continue

                report_path = os.path.join(tmpdir, "gitleaks_report.json")
                if os.path.exists(report_path):
                    try:
                        os.remove(report_path)
                    except OSError:
                        pass

                argv = [
                    binary,
                    "detect",
                    "--source",
                    full_path,
                    "--no-git",
                    "--report-format",
                    "json",
                    "--report-path",
                    report_path,
                    "--exit-code",
                    "0",
                ]

                stdout, stderr, code, err = self._execute_subprocess(
                    argv, cwd=repo_path, timeout=timeout
                )
                exit_codes.append(code)
                if stdout:
                    raw_output_collected.append(stdout)
                if stderr:
                    raw_output_collected.append(stderr)

                if err:
                    warnings.append(f"Gitleaks error on {file_path}: {err}")
                    continue

                if os.path.exists(report_path):
                    try:
                        with open(report_path, "r", encoding="utf-8", errors="replace") as rf:
                            report_content = rf.read()
                            findings.extend(self.parse_output(report_content, repo_path=repo_path))
                    except Exception as parse_err:
                        warnings.append(f"Failed to read Gitleaks report for {file_path}: {parse_err}")

        return ExternalLinterResult(
            tool_name=self.tool_name,
            available=True,
            findings=findings,
            raw_output="\n".join(raw_output_collected),
            exit_code=max(exit_codes) if exit_codes and any(c is not None for c in exit_codes) else 0,
            warnings=warnings,
        )

    def parse_output(self, raw_output: str, repo_path: str = ".") -> list[NormalizedFinding]:
        if not raw_output or not raw_output.strip():
            return []

        findings: list[NormalizedFinding] = []
        try:
            items = json.loads(raw_output)
            if not isinstance(items, list):
                return []

            for item in items:
                rule_id = item.get("RuleID", "secret")
                desc = item.get("Description", "Secret detected")
                raw_file = item.get("File", "")
                
                # Normalize relative path
                if os.path.isabs(raw_file) and repo_path:
                    try:
                        rel_file = os.path.relpath(raw_file, repo_path)
                    except ValueError:
                        rel_file = raw_file
                else:
                    rel_file = raw_file
                rel_file = rel_file.replace("\\", "/")

                start_line = int(item.get("StartLine", 1))
                end_line = int(item.get("EndLine", start_line))
                secret_raw = item.get("Secret", "")
                masked_val = mask_secret_value(secret_raw)

                msg = f"{desc} [{masked_val}]"

                findings.append(
                    NormalizedFinding(
                        severity="error",  # Secrets are critical/blocker
                        category="security/secret",
                        file_path=rel_file,
                        line_start=start_line,
                        line_end=end_line,
                        message=msg,
                        source="gitleaks",
                        rule_id=rule_id,
                    )
                )
        except json.JSONDecodeError:
            pass

        return findings

