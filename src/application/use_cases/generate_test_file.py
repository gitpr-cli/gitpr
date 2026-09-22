import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from src.ai_providers import call_ai_model
from src.config import get_ai_provider, get_api_key, get_api_model
from src.core import get_skill_context, resolve_skill_path
from src.domain.tests_generation.framework_detector import detect_test_framework
from src.domain.tests_generation.test_content_types import (
    GeneratedTest,
    TestFramework,
    TestGenerationTarget,
    TestScaffold,
)
from src.domain.tests_generation.test_scaffold_builder import build_test_scaffold
from src.i18n import __


def validate_test_syntax(content: str, framework: TestFramework) -> tuple[bool, str | None]:
    """Validates the syntax of the generated test file using local tools if present.
    
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    if not content or not content.strip():
        return False, "Generated test content is empty."

    if framework in (TestFramework.PEST, TestFramework.PHPUNIT):
        php_bin = shutil.which("php")
        if php_bin:
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".php", delete=False, encoding="utf-8") as tf:
                    tf.write(content)
                    temp_name = tf.name
                
                try:
                    res = subprocess.run(
                        [php_bin, "-l", temp_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if res.returncode != 0:
                        return False, res.stderr.strip() or res.stdout.strip()
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
            except Exception as e:
                return True, f"Syntax validation skipped: {e}"

    elif framework in (TestFramework.JEST, TestFramework.VITEST):
        node_bin = shutil.which("node")
        if node_bin:
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as tf:
                    tf.write(content)
                    temp_name = tf.name
                try:
                    res = subprocess.run(
                        [node_bin, "--check", temp_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if res.returncode != 0:
                        return False, res.stderr.strip() or res.stdout.strip()
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
            except Exception as e:
                return True, f"Syntax validation skipped: {e}"

    elif framework == TestFramework.PYTEST:
        python_bin = shutil.which("python") or shutil.which("python3")
        if python_bin:
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
                    tf.write(content)
                    temp_name = tf.name
                try:
                    res = subprocess.run(
                        [python_bin, "-m", "py_compile", temp_name],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    if res.returncode != 0:
                        return False, res.stderr.strip() or res.stdout.strip()
                finally:
                    if os.path.exists(temp_name):
                        os.unlink(temp_name)
            except Exception as e:
                return True, f"Syntax validation skipped: {e}"

    return True, None


def generate_test_file(
    target: TestGenerationTarget,
    repo_path: str = ".",
    ai_provider: str | None = None,
    framework_override: TestFramework | str | None = None,
    apply: bool = False,
    quiet: bool = False,
) -> GeneratedTest:
    """Orchestrates test generation from a target diff/file/finding."""
    warnings: list[str] = []

    # 1. Detect Framework
    detected_fw, fw_warnings = detect_test_framework(repo_path, framework_override)
    warnings.extend(fw_warnings)

    # 2. Build Scaffold
    scaffold = build_test_scaffold(target.file_path, detected_fw, repo_path)

    # 3. Setup AI provider & system instruction
    provider = ai_provider or get_ai_provider()
    api_key = get_api_key(provider)
    if not api_key:
        warnings.append(f"No API key configured for {provider}. Generate one with --install.")
        return GeneratedTest(
            scaffold=scaffold,
            content="",
            covered_scenarios=[],
            warnings=warnings,
        )

    api_model = get_api_model(provider, task_complexity="advanced")

    # Load skill context or use built-in instruction
    skill_content = get_skill_context("tests", quiet=True)
    if not skill_content:
        skill_content = (
            "You are an expert QA and Test Automation Engineer. "
            "Generate a complete, executable, clean test file adhering strictly to the requested test framework and conventions. "
            "You MUST ONLY return a valid JSON object matching this schema:\n"
            '{"content": "complete test file source code as a string", "covered_scenarios": ["scenario 1", "scenario 2"], "warnings": []}'
        )

    # 4. Construct Prompt
    target_info = f"Target Type: {target.source_type}\n"
    if target.file_path:
        target_info += f"Target File: {target.file_path}\n"
    if target.finding_id:
        target_info += f"Target Finding ID: {target.finding_id}\n"

    user_prompt = (
        f"Generate a comprehensive test file for the following changes:\n\n"
        f"Framework: {detected_fw.value}\n"
        f"Target Test Path: {scaffold.target_test_path}\n"
        f"{target_info}\n"
        f"Diff Context:\n```diff\n{target.diff_content}\n```\n\n"
        "Requirements:\n"
        "1. Write complete, ready-to-run test code (imports, test cases, assertions).\n"
        "2. Include Happy Path scenarios covering main changes.\n"
        "3. Include Edge Cases and Regression scenarios where applicable.\n"
        "4. Follow the idiomatic conventions of the detected framework.\n"
        "5. Return strictly JSON with 'content', 'covered_scenarios', and 'warnings'."
    )

    # 5. Call AI
    ai_raw = call_ai_model(
        provider=provider,
        api_key=api_key,
        api_model=api_model,
        prompt=user_prompt,
        system_instruction=skill_content,
        quiet=quiet,
        action="tests",
    )

    if not ai_raw:
        warnings.append("AI model did not return a response.")
        return GeneratedTest(
            scaffold=scaffold,
            content="",
            covered_scenarios=[],
            warnings=warnings,
        )

    # 6. Parse AI JSON
    test_code = ""
    covered_scenarios = []
    try:
        data = json.loads(ai_raw)
        test_code = data.get("content", "")
        covered_scenarios = data.get("covered_scenarios", [])
        if "warnings" in data and isinstance(data["warnings"], list):
            warnings.extend(data["warnings"])
    except Exception:
        # If response wasn't strict JSON, use clean raw text
        test_code = ai_raw.strip()
        if test_code.startswith("```"):
            lines = test_code.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            test_code = "\n".join(lines).strip()
        covered_scenarios.append("Generated from raw model output")

    # 7. Validate Syntax
    is_valid, syn_err = validate_test_syntax(test_code, detected_fw)
    if not is_valid:
        warnings.append(f"Syntax validation failed ({syn_err}). Marked as EXPERIMENTAL / low confidence.")

    # 8. Apply if requested
    if apply and test_code:
        full_dest_path = Path(repo_path) / scaffold.target_test_path
        full_dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_dest_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(test_code)

    return GeneratedTest(
        scaffold=scaffold,
        content=test_code,
        covered_scenarios=covered_scenarios,
        warnings=warnings,
    )

