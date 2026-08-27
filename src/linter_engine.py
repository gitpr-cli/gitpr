import re
import fnmatch
import shlex
import shutil
import subprocess
import os
import xml.etree.ElementTree as ET
from src.config import load_linter_rules, load_external_linters, get_linter_timeout
from src.i18n import __
from src.metrics import log_local_metric


def _is_rule_applicable(rule, current_file, file_extension):
    """Checks whether the rule applies to the current file based on extension and paths."""
    # Check extension
    if file_extension not in rule.get("extensions", []):
        return False

    # Check require_paths (if present, the file MUST match at least one)
    require_paths = rule.get("require_paths", [])
    if require_paths:
        match_required = any(
            re.search(p.replace("*", ".*"), current_file) for p in require_paths
        )
        if not match_required:
            return False

    # Check ignore_paths (if it matches any, the rule does not apply)
    ignore_paths = rule.get("ignore_paths", [])
    if ignore_paths:
        should_ignore = any(
            re.search(p.replace("*", ".*"), current_file) for p in ignore_paths
        )
        if should_ignore:
            return False

    return True


def _apply_rule(rule, code_line, line_number, current_file, alerts):
    """Applies the rule's regex on the code line and records the alert if needed."""
    # Logic to ignore comments in code
    if rule.get("ignore_comments", False):
        comment_patterns = [r"^//", r"^#", r"^/\*", r"^\*"]
        if any(re.match(cp, code_line.strip()) for cp in comment_patterns):
            return

    # Validate rule regex
    try:
        if re.search(rule["regex"], code_line):
            message = (
                rule["message"]
                .replace("{file_name}", current_file)
                .replace("{line_number}", str(line_number))
            )

            # Extract severity (default is error)
            level = rule.get("level", "error").lower()

            if level == "warning":
                alerts["warnings"].append(message)
            else:
                alerts["errors"].append(message)
    except re.error as e:
        alerts["errors"].append(
            __(
                "Rule '{rule_name}' contains invalid Regex: {error}",
                rule_name=rule.get("name"),
                error=str(e),
            )
        )


def _split_command(command):
    """Splits a configured linter command string into an argv list.

    Uses POSIX quoting rules (so "--report=checkstyle" loses its quotes and
    quoted paths stay whole) but with backslash escaping DISABLED, otherwise
    Windows paths like C:\\tools\\lint.exe would be mangled into C:toolslint.exe.
    """
    lexer = shlex.shlex(command, posix=True)
    lexer.whitespace_split = True
    lexer.escape = ""
    return list(lexer)


def _run_external_linter(command, file_path, timeout=None):
    """Executes an external linter command and returns its stdout (Checkstyle XML).

    The command runs as an argv list WITHOUT a shell, so metacharacters in the
    configured command or in the target path are never interpreted (a file named
    'a; rm -rf ~' is passed as one literal argument).  Because CreateProcess only
    auto-appends .exe, the executable is resolved through shutil.which() so
    PATHEXT shims such as npx.cmd keep working on Windows without shell=True.
    """
    try:
        argv = _split_command(command)
        if not argv:
            return ""

        resolved = shutil.which(argv[0])
        if resolved:
            argv[0] = resolved

        argv.append(file_path)

        result = subprocess.run(
            argv,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout if timeout is not None else get_linter_timeout(),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        # Return stdout regardless of the exit code (linters exit > 0 when they find problems)
        return result.stdout
    except Exception:
        return ""


def _parse_checkstyle_xml(xml_content):
    """Extracts errors from Checkstyle XML into a dictionary list.

    Each entry carries the owning <file name=...> so callers can attribute a
    violation to its source file instead of matching on line number alone.
    """
    results = []
    if not xml_content or not xml_content.strip():
        return results

    try:
        root = ET.fromstring(xml_content)
        for file_node in root.findall("file"):
            source_file = file_node.get("name", "")
            for error_node in file_node.findall("error"):
                try:
                    line = int(error_node.get("line", 0))
                except (TypeError, ValueError):
                    continue
                results.append(
                    {
                        "file": source_file,
                        "line": line,
                        "severity": error_node.get("severity", "error").lower(),
                        "message": error_node.get("message", ""),
                    }
                )
    except ET.ParseError:
        pass
    return results


def _checkstyle_file_matches(reported_path, target_path):
    """True when a Checkstyle <file name=...> refers to *target_path*.

    Checkstyle reports absolute paths while the diff yields repo-relative ones,
    so the comparison is suffix-based over normalized separators.  A report with
    no name attribute cannot be discriminated and is accepted, so a linter that
    omits it never silently loses every violation.
    """
    if not reported_path:
        return True

    reported = os.path.normpath(reported_path).replace("\\", "/").lower()
    target = os.path.normpath(target_path).replace("\\", "/").lower()

    return (
        reported == target
        or reported.endswith("/" + target)
        or target.endswith("/" + reported)
    )


def _collect_external_alerts(
    external_linters, file_path, file_extension, alerts, allowed_lines=None
):
    """Runs every external linter matching *file_extension* against *file_path*.

    Violations are attributed by file AND line: the file guard drops results a
    linter reports for OTHER files (project-wide configs, followed imports),
    which previously leaked in whenever their line number happened to collide
    with an added line.  When *allowed_lines* is None (full-file mode) every
    line of the target file counts; otherwise only the diff's added lines do.
    """
    for ext_linter in external_linters:
        if file_extension not in ext_linter.get("extensions", []):
            continue

        command = ext_linter.get("command")
        if not command:
            continue

        xml_output = _run_external_linter(command, file_path)

        for err in _parse_checkstyle_xml(xml_output):
            if not _checkstyle_file_matches(err["file"], file_path):
                continue
            if allowed_lines is not None and err["line"] not in allowed_lines:
                continue

            msg = f"🚨 [{ext_linter.get('name', 'External linter')}] {err['message']} ({file_path}, Line {err['line']})"
            if err["severity"] == "warning":
                alerts["warnings"].append(msg)
            else:
                alerts["errors"].append(msg)


def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):
    """
    Analyzes the git diff OR a full file and applies the rules defined in .gitpr.linter.yml.
    In diff mode, also bridges external linters (Checkstyle XML) filtered by added lines.
    Returns a dictionary with two lists: 'errors' (critical) and 'warnings' (alerts).
    """
    rules = load_linter_rules()
    external_linters = load_external_linters()
    if not rules and not external_linters:
        return {"errors": [], "warnings": []}

    alerts = {"errors": [], "warnings": []}

    lines = diff_text.split("\n")

    # ==========================================
    # FULL FILE MODE (--input)
    # ==========================================
    if is_full_file:
        if not file_path:
            return alerts

        # Normalize path to ensure Windows and Linux compatibility in Regex
        current_file = file_path.replace("\\", "/")
        file_extension = current_file.split(".")[-1] if "." in current_file else ""

        for i, line in enumerate(lines, start=1):
            code_line = line.strip()
            if not code_line:
                continue

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, i, current_file, alerts)

        # External linters audit the whole file here: with no diff to intersect,
        # every violation the linter reports for this file is in scope.
        if external_linters:
            _collect_external_alerts(
                external_linters,
                current_file,
                file_extension,
                alerts,
                allowed_lines=None,
            )

        log_local_metric(
            command="linter",
            status="success",
            linter_errors=len(alerts["errors"]),
            linter_warnings=len(alerts["warnings"]),
            mode="full_file",
        )
        return alerts

    # ==========================================
    # STANDARD GIT DIFF MODE
    # ==========================================
    modified_files = {}
    current_file = None
    file_extension = None
    line_number = 0

    for line in lines:
        if line.startswith("+++ b/"):
            current_file = line[6:]
            file_extension = current_file.split(".")[-1] if "." in current_file else ""
            line_number = 0
            if current_file not in modified_files:
                modified_files[current_file] = []
            continue

        if line.startswith("@@"):
            match = re.search(r"\+(\d+)", line)
            if match:
                line_number = int(match.group(1)) - 1
            continue

        if line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            code_line = line[1:].strip()

            if not current_file or not code_line:
                continue

            modified_files[current_file].append(line_number)

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    # Cross-reference with External Linters (only lines added in the current diff)
    if external_linters and modified_files:
        for f_path, modified_lines in modified_files.items():
            f_ext = f_path.split(".")[-1] if "." in f_path else ""

            _collect_external_alerts(
                external_linters,
                f_path,
                f_ext,
                alerts,
                allowed_lines=set(modified_lines),
            )

    log_local_metric(
        command="linter",
        status="success",
        linter_errors=len(alerts["errors"]),
        linter_warnings=len(alerts["warnings"]),
        mode="diff",
    )
    return alerts


def generate_linter_report_content(alerts):
    """Generates the Markdown content for the linter report."""
    content = __("# 🚨 GitPR Linter Report\n\n")
    if not alerts["errors"] and not alerts["warnings"]:
        content += __("✅ No violations found.\n")
        return content

    if alerts["errors"]:
        content += __("## ❌ Errors\n\n")
        for err in alerts["errors"]:
            content += f"- {err}\n"
        content += "\n"

    if alerts["warnings"]:
        content += __("## ⚠️ Warnings\n\n")
        for warn in alerts["warnings"]:
            content += f"- {warn}\n"

    return content
