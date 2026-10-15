"""Sensitive data masking for CI artifacts (SARIF, JSON, JUnit).

Ensures credentials, private keys, API keys, and sensitive tokens never leak into
CI logs or static analysis reports in plaintext.
"""

import re
from typing import Pattern

# Common secret regexes to sanitize before serialization
SECRET_PATTERNS: list[tuple[Pattern[str], str]] = [
    # Private keys
    (
        re.compile(
            r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----[\s\S]*?-----END (?:[A-Z0-9_-]+ )?PRIVATE KEY-----",
            re.MULTILINE,
        ),
        "-----BEGIN PRIVATE KEY-----\n***\n-----END PRIVATE KEY-----",
    ),
    # AWS Access Key ID
    (re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "***"),
    # AWS Secret Key (approximate 40-char base64 in assignments)
    (
        re.compile(
            r"""(?i)(aws_secret_access_key|aws_secret_key|secret_key)\s*[:=]\s*['"]?([A-Za-z0-9/+=]{40})['"]?"""
        ),
        r"\1: '***'",
    ),
    # GitHub Tokens
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b"), "***"),
    (re.compile(r"\b(github_pat_[A-Za-z0-9_]{82})\b"), "***"),
    # Google API Key / Gemini
    (re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,45})\b"), "***"),
    # OpenAI API Key
    (re.compile(r"\b(sk-[A-Za-z0-9_-]{20,})\b"), "***"),
    # Slack Token
    (re.compile(r"\b(xox[baprs]-[0-9A-Za-z]{10,48})\b"), "***"),
    # Bearer tokens
    (
        re.compile(r"(?i)\bBearer\s+([A-Za-z0-9\-_\.]{20,})\b"),
        "Bearer ***",
    ),
    # Basic auth passwords in URLs (e.g. https://user:pass@host)
    (
        re.compile(r"(https?://[^:/@\s]+):([^/@\s]+)@"),
        r"\1:***@",
    ),
    # Generic password assignments in findings (password = 'secret')
    (
        re.compile(
            r"""(?i)(password|passwd|pwd|secret|api_key|apikey|token)\s*[:=]\s*['"]([^'"]{6,})['"]"""
        ),
        r"\1 = '***'",
    ),
]


def mask_sensitive_text(text: str | None) -> str:
    """Replaces known credentials and secrets with masked placeholders."""
    if not text:
        return ""
    result = text
    for pattern, replacement in SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
