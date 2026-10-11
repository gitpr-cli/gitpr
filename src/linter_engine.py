import re
import fnmatch
import shlex
import shutil
import subprocess
import os
import xml.etree.ElementTree as ET
from src.config import (
    load_linter_rules,
    load_external_linters,
    load_sast_config,
    get_linter_timeout,
)
from src.domain.baseline.baseline_fingerprint import snippet_hash
from src.domain.finding.finding_types import NormalizedFinding
from src.domain.linter.sast_finding_mapper import (
    format_finding_message,
    deduplicate_secret_findings,
)
from src.infrastructure.linter.external.semgrep_bridge import SemgrepBridge
from src.infrastructure.linter.external.gitleaks_bridge import GitleaksBridge
from src.infrastructure.linter.external.bandit_bridge import BanditBridge
from src.i18n import __
from src.metrics import log_local_metric



def _is_rule_applicable(rule, current_file, file_extension):
    """Checks whether the rule applies to the current file based on extension and paths."""
    # Check extension ("*" means every file, including the ones with no suffix)
    extensions = rule.get("extensions", [])
    if "*" not in extensions and file_extension not in extensions:
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


def _apply_rule(rule, code_line, line_number, current_file, alerts, findings=None):
    """Applies the rule's regex on the code line and records the alert if needed.

    ``findings`` is the structured side channel a baseline is built from: the
    alert strings carry only what the rule's message template renders, and never
    the rule's name, so a finding has to be recorded as data. The parameter is
    optional and the alert lists are untouched by it, which is what keeps every
    existing caller byte-for-byte identical.
    """
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

            if findings is not None:
                findings.append(
                    NormalizedFinding(
                        severity="warning" if level == "warning" else "error",
                        category=rule.get("category") or "lint",
                        file_path=current_file,
                        line_start=line_number,
                        line_end=line_number,
                        message=message,
                        source="linter",
                        rule_id=rule.get("name"),
                        snippet_hash=snippet_hash(code_line),
                    )
                )
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


def external_alert_message(tool_name, message, file_path, line_number):
    """The alert line an external linter's violation is reported as.

    The template lives here and only here: the baseline reads a bridge finding
    back into the alert it came from (a Checkstyle report names no rule, so the
    rendered line is the only thing tying the two together), and a second copy
    of this string would turn a cosmetic edit into a silent mismatch.
    """
    return f"🚨 [{tool_name}] {message} ({file_path}, Line {line_number})"


def _collect_external_alerts(
    external_linters,
    file_path,
    file_extension,
    alerts,
    allowed_lines=None,
    findings=None,
    line_texts=None,
):
    """Runs every external linter matching *file_extension* against *file_path*.

    Violations are attributed by file AND line: the file guard drops results a
    linter reports for OTHER files (project-wide configs, followed imports),
    which previously leaked in whenever their line number happened to collide
    with an added line.  When *allowed_lines* is None (full-file mode) every
    line of the target file counts; otherwise only the diff's added lines do.

    ``findings`` and ``line_texts`` are the baseline's side channel: a Checkstyle
    report names no rule, only the message, so the linter's own name is what
    identifies a finding here, and the line's digest comes from the text the
    engine already parsed (the tool reports locations, never content).
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

            msg = external_alert_message(
                ext_linter.get("name", "External linter"),
                err["message"],
                file_path,
                err["line"],
            )
            if err["severity"] == "warning":
                alerts["warnings"].append(msg)
            else:
                alerts["errors"].append(msg)

            if findings is not None:
                # Line 0 is what Checkstyle reports for a file-level violation
                # (file length, header missing) — kept as it arrived rather than
                # bent into line 1, which would name a line nobody violated.
                findings.append(
                    NormalizedFinding(
                        severity="warning" if err["severity"] == "warning" else "error",
                        category="lint",
                        file_path=file_path,
                        line_start=err["line"],
                        line_end=err["line"],
                        message=err["message"],
                        source="external",
                        rule_id=ext_linter.get("name"),
                        snippet_hash=_line_snippet(line_texts, file_path, err["line"]),
                    )
                )


def _normalize_lint_path(file_path):
    """The key *file_path* is looked up under, in the baseline's own spelling."""
    return (file_path or "").replace("\\", "/").lower()


def _line_snippet(line_texts, file_path, line_number):
    """The digest of the offending line, or None when the text is not at hand.

    Only the digest is ever kept: the line may hold a credential, and a baseline
    is a file meant to be committed.
    """
    if not line_texts:
        return None
    text = line_texts.get((_normalize_lint_path(file_path), line_number))
    return snippet_hash(text) if text is not None else None


def _fill_snippet_hashes(findings, line_texts):
    """Gives each bridge finding the digest of the line it points at.

    The bridges run a tool against files on disk and hand back locations, never
    content, so the digest comes from the diff this module already parsed. It is
    what makes editing a secret in place a new finding instead of the same one.
    """
    for finding in findings:
        if finding.snippet_hash is None:
            finding.snippet_hash = _line_snippet(
                line_texts, finding.file_path, finding.line_start
            )


def _drop_merged_findings(findings, alerts):
    """Removes the rule findings whose alert a SAST merge consumed.

    A merge means one detection that two tools agree on, so it has to leave one
    finding behind. The regex side is dropped because its alert is gone from the
    report: keeping it would put the same line twice in a baseline, and the
    second entry would point at an alert nobody can see.

    Only ``source="linter"`` findings are candidates — their ``message`` *is* the
    alert string. A bridge finding is not alert-backed (its alert is a decorated
    rendering), so it is never matched here and never dropped by accident.
    """
    surviving = set(alerts["errors"]) | set(alerts["warnings"])
    findings[:] = [
        finding
        for finding in findings
        if finding.source != "linter" or finding.message in surviving
    ]


def _run_sast_bridges(target_files, repo_path=".", diff_only=True, allowed_lines_by_file=None):
    """Executes enabled SAST tool bridges (Semgrep, Gitleaks, Bandit) and returns findings."""
    sast_config = load_sast_config()
    all_findings = []
    warnings = []

    # Map of tool bridges
    bridges = {
        "semgrep": SemgrepBridge(),
        "gitleaks": GitleaksBridge(),
        "bandit": BanditBridge(),
    }

    for tool_name, bridge in bridges.items():
        conf = sast_config.get(tool_name, {})
        if not conf.get("enabled", False):
            continue

        if not bridge.is_available():
            warnings.append(
                __(
                    "⚠️ SAST tool '{tool}' is enabled in config but was not found in PATH.",
                    tool=tool_name,
                )
            )
            continue

        timeout = conf.get("timeout_seconds", 60)
        result = bridge.run(
            target_files=target_files,
            repo_path=repo_path,
            diff_only=diff_only,
            timeout=timeout,
        )

        for w in result.warnings:
            warnings.append(f"⚠️ [{tool_name}] {w}")

        # Filter findings by added lines if diff-only / allowed_lines provided
        for f in result.findings:
            if allowed_lines_by_file is not None:
                norm_fpath = f.file_path.replace("\\", "/").lower()
                allowed_lines = allowed_lines_by_file.get(norm_fpath)
                if allowed_lines is not None and f.line_start not in allowed_lines:
                    # In diff mode, only alert if line_start is within added lines
                    # (Unless tool is Gitleaks or Semgrep detecting across lines)
                    continue

            all_findings.append(f)

    return all_findings, warnings


def parse_diff_and_lint(
    diff_text,
    is_full_file=False,
    file_path=None,
    skip_external=False,
    repo_path=".",
    findings_out=None,
):
    """
    Analyzes the git diff OR a full file and applies the rules defined in .gitpr.linter.yml.
    In diff mode, also bridges external linters (Checkstyle XML) and SAST bridges (Semgrep, Gitleaks, Bandit).
    Returns a dictionary with two lists: 'errors' (critical) and 'warnings' (alerts).

    ``skip_external`` runs the YAML rules only. The external bridge executes a
    linter binary against files on disk, so it can only speak about the working
    tree — a review of a pull request fetched over the API would be checking
    whatever the user happens to have checked out, and publishing that as a
    comment about someone else's branch. Callers reviewing anything other than
    the local tree pass True.

    ``findings_out``, when given a list, is filled with the same alerts as
    structured findings — rule name, file, line, digest of the line — which is
    what a baseline fingerprints. The returned dictionary does not depend on it:
    a caller that passes nothing gets exactly the alerts it got before.
    """
    from src.domain.policy import get_active_policy

    rules = load_linter_rules(get_active_policy())
    external_linters = [] if skip_external else load_external_linters()
    sast_config = {} if skip_external else load_sast_config()
    has_sast = any(c.get("enabled", False) for c in sast_config.values())

    if not rules and not external_linters and not has_sast:
        return {"errors": [], "warnings": []}

    alerts = {"errors": [], "warnings": []}
    # (normalized path, line) -> the line's text, kept only for the digest of a
    # finding: the alert strings never carry the content, and the SAST bridges
    # report locations for files they read themselves.
    line_texts = {}

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

            line_texts[(_normalize_lint_path(current_file), i)] = code_line

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, i, current_file, alerts, findings_out)

        # External linters audit the whole file here: with no diff to intersect,
        # every violation the linter reports for this file is in scope.
        if external_linters:
            _collect_external_alerts(
                external_linters,
                current_file,
                file_extension,
                alerts,
                allowed_lines=None,
                findings=findings_out,
                line_texts=line_texts,
            )

        # SAST Bridges full-file execution
        if not skip_external and has_sast:
            sast_findings, sast_warnings = _run_sast_bridges(
                target_files=[current_file],
                repo_path=repo_path,
                diff_only=False,
                allowed_lines_by_file=None,
            )
            alerts["warnings"].extend(sast_warnings)

            if findings_out is not None:
                _fill_snippet_hashes(sast_findings, line_texts)

            # Deduplicate regex secret alerts vs SAST findings
            cleaned_alerts, merged_findings = deduplicate_secret_findings(alerts, sast_findings)
            alerts["errors"] = cleaned_alerts["errors"]
            alerts["warnings"] = cleaned_alerts["warnings"]

            if findings_out is not None:
                _drop_merged_findings(findings_out, alerts)

            for finding in merged_findings:
                msg = format_finding_message(finding)
                if finding.severity == "error":
                    alerts["errors"].append(msg)
                else:
                    alerts["warnings"].append(msg)

            if findings_out is not None:
                findings_out.extend(merged_findings)

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

        if line.startswith(" "):
            # Context exists on both sides, so the new-side counter moves over it.
            # Only additions used to advance the counter, which reported every
            # addition after the first context line with a number below its real
            # one — and the report, the review and the diff's own numbering all
            # disagreed with it. (A removed line is the old side: it moves nothing,
            # which is why '-' needs no branch here.)
            line_number += 1
            continue

        if line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            code_line = line[1:].strip()

            if not current_file or not code_line:
                continue

            modified_files[current_file].append(line_number)
            line_texts[(_normalize_lint_path(current_file), line_number)] = code_line

            for rule in rules:
                if not _is_rule_applicable(rule, current_file, file_extension):
                    continue
                _apply_rule(rule, code_line, line_number, current_file, alerts, findings_out)

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
                findings=findings_out,
                line_texts=line_texts,
            )

    # SAST Bridges diff execution
    if not skip_external and has_sast and modified_files:
        allowed_lines_by_file = {
            f.replace("\\", "/").lower(): set(lines_list)
            for f, lines_list in modified_files.items()
        }
        sast_findings, sast_warnings = _run_sast_bridges(
            target_files=list(modified_files.keys()),
            repo_path=repo_path,
            diff_only=True,
            allowed_lines_by_file=allowed_lines_by_file,
        )
        alerts["warnings"].extend(sast_warnings)

        if findings_out is not None:
            _fill_snippet_hashes(sast_findings, line_texts)

        # Deduplicate regex secret alerts vs SAST findings
        cleaned_alerts, merged_findings = deduplicate_secret_findings(alerts, sast_findings)
        alerts["errors"] = cleaned_alerts["errors"]
        alerts["warnings"] = cleaned_alerts["warnings"]

        if findings_out is not None:
            _drop_merged_findings(findings_out, alerts)

        for finding in merged_findings:
            msg = format_finding_message(finding)
            if finding.severity == "error":
                alerts["errors"].append(msg)
            else:
                alerts["warnings"].append(msg)

        if findings_out is not None:
            findings_out.extend(merged_findings)

    log_local_metric(
        command="linter",
        status="success",
        linter_errors=len(alerts["errors"]),
        linter_warnings=len(alerts["warnings"]),
        mode="diff",
    )
    return alerts


def lint_findings(diff_text, **kwargs):
    """The structured findings of a lint run — what a baseline fingerprints.

    A thin wrapper over ``parse_diff_and_lint``: it opens the findings channel and
    returns it, dropping the alert strings the report is built from. Both views
    come from one run, so a call site that needs the alerts as well passes
    ``findings_out`` to the linter directly instead of linting twice.
    """
    findings = []
    parse_diff_and_lint(diff_text, findings_out=findings, **kwargs)
    return findings


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

