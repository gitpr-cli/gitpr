import re
import fnmatch
from src.config import load_linter_rules
from src.i18n import __
from src.metrics import log_local_metric

def _is_rule_applicable(rule, current_file, file_extension):
    """Checks whether the rule applies to the current file based on extension and paths."""
    # Check extension
    if file_extension not in rule.get('extensions', []):
        return False

    # Check require_paths (if present, the file MUST match at least one)
    require_paths = rule.get('require_paths', [])
    if require_paths:
        match_required = any(re.search(p.replace('*', '.*'), current_file) for p in require_paths)
        if not match_required:
            return False

    # Check ignore_paths (if it matches any, the rule does not apply)
    ignore_paths = rule.get('ignore_paths', [])
    if ignore_paths:
        should_ignore = any(re.search(p.replace('*', '.*'), current_file) for p in ignore_paths)
        if should_ignore:
            return False

    return True

def _apply_rule(rule, code_line, line_number, current_file, alerts):
    """Applies the rule's regex on the code line and records the alert if needed."""
    # Logic to ignore comments in code
    if rule.get('ignore_comments', False):
        comment_patterns = [r'^//', r'^#', r'^/\*', r'^\*']
        if any(re.match(cp, code_line.strip()) for cp in comment_patterns):
            return

    # Validate rule regex
    try:
        if re.search(rule['regex'], code_line):
            message = rule['message'].replace('{file_name}', current_file).replace('{line_number}', str(line_number))

            # Extract severity (default is error)
            level = rule.get('level', 'error').lower()

            if level == 'warning':
                alerts["warnings"].append(message)
            else:
                alerts["errors"].append(message)
    except re.error as e:
        alerts["errors"].append(__("Rule '{rule_name}' contains invalid Regex: {error}", rule_name=rule.get('name'), error=str(e)))

def parse_diff_and_lint(diff_text, is_full_file=False, file_path=None):
    """
    Analyzes the git diff OR a full file and applies the rules defined in .gitpr.linter.yml.
    Returns a dictionary with two lists: 'errors' (critical) and 'warnings' (alerts).
    """
    rules = load_linter_rules()
    if not rules:
        return {"errors": [], "warnings": []}

    alerts = {
        "errors": [],
        "warnings": []
    }

    lines = diff_text.split('\n')
    
    # ==========================================
    # FULL FILE MODE (--input)
    # ==========================================
    if is_full_file:
        if not file_path:
            return alerts

        # Normalize path to ensure Windows and Linux compatibility in Regex
        current_file = file_path.replace('\\', '/')
        file_extension = current_file.split('.')[-1] if '.' in current_file else ''

        for i, line in enumerate(lines, start=1):
            code_line = line.strip()
            if not code_line:
                continue

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, i, current_file, alerts)

        log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="full_file")
        return alerts

    # ==========================================
    # STANDARD GIT DIFF MODE
    # ==========================================
    current_file = None
    file_extension = None
    line_number = 0
    
    for line in lines:
        if line.startswith('+++ b/'):
            current_file = line[6:]
            file_extension = current_file.split('.')[-1] if '.' in current_file else ''
            line_number = 0 
            continue

        if line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                line_number = int(match.group(1)) - 1
            continue

        if line.startswith('+') and not line.startswith('+++'):
            line_number += 1
            code_line = line[1:].strip()

            if not current_file or not code_line:
                continue

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts)

    log_local_metric(command="linter", status="success", linter_errors=len(alerts["errors"]), linter_warnings=len(alerts["warnings"]), mode="diff")
    return alerts