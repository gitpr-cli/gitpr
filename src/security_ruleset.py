"""Embedded secret-scanning rules for the static linter.

The rules live in the package, not in the user's .gitpr.linter.yml, because a
secret gate has to be identical on every machine and in every CI run: the local
catalogue is never overwritten by the download, the --linter-setup wizard
rewrites it through yaml.dump (comments and all), and a global plugin is
per-machine. Shipping them inside the wheel is what makes "the same seven checks
everywhere" true without a download. See
docs/plans/ADR-007-secret-ruleset-location-and-severity.md.

Each entry uses the schema the engine actually reads: name, level, regex,
message, extensions. `extensions: ["*"]` means every file — without it the
suffix match would leave out exactly the files secrets leak from: .env, id_rsa,
credentials, Dockerfile.

`error` is reserved for the five patterns that are proof by themselves (a value
only a credential looks like, plus the private-key header). The two formats that
also appear legitimately in fixtures, docs and examples are `warning`: they
report without blocking. A third level between the two would add a word without
adding behaviour, which is why this ruleset uses the engine's two levels.

No message interpolates the matched value. The engine only knows {file_name} and
{line_number}, so an alert names the category and the location and never echoes
the secret it found; tests/test_security_ruleset.py holds that invariant.

Escape hatches (both in ~/.gitpr/.env): GITPR_LINTER_SECURITY=false turns the
whole set off, GITPR_LINTER_SECURITY_DISABLED_RULES="name;name" drops single
rules by name.
"""

from src.i18n import __

SECURITY_RULES = [
    {
        "name": "sec-aws-access-key",
        "level": "error",
        "extensions": ["*"],
        "regex": r"AKIA[0-9A-Z]{16}",
        "message": __(
            "Possible AWS Access Key ID hardcoded in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-github-token",
        "level": "error",
        "extensions": ["*"],
        "regex": r"gh[pousr]_[A-Za-z0-9]{36,}",
        "message": __(
            "Possible GitHub token hardcoded in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-slack-token",
        "level": "error",
        "extensions": ["*"],
        "regex": r"xox[baprs]-[A-Za-z0-9-]{10,}",
        "message": __(
            "Possible Slack token hardcoded in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-google-api-key",
        "level": "error",
        "extensions": ["*"],
        "regex": r"AIza[0-9A-Za-z\-_]{35}",
        "message": __(
            "Possible Google API key hardcoded in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-private-key-block",
        "level": "error",
        "extensions": ["*"],
        # Only the header line: the engine matches line by line, and the header
        # is already definitive on its own. The base64 body is never read.
        "regex": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        "message": __(
            "Private key block committed in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-db-connection-string",
        "level": "warning",
        "extensions": ["*"],
        "regex": r"(mysql|postgres|postgresql|mongodb(\+srv)?)://[^:\s]+:[^@\s]+@",
        "message": __(
            "Database connection string with credentials in {file_name} (Line {line_number})."
        ),
    },
    {
        "name": "sec-generic-credential-assignment",
        "level": "warning",
        "extensions": ["*"],
        # Case-insensitivity is scoped per group: a global (?i) is only legal at
        # the very start of the pattern, so wrapping the regex later would raise.
        # The negative lookahead sits right after the opening quote and runs
        # before any value character is read, which is what filters placeholders.
        "regex": (
            r"(?i:password|senha|secret|api[_-]?key|token)\s*[:=]\s*['\"]"
            r"(?!(?i:changeme|xxx+|your[_-]?(?:key|password|secret|token)[_-]?here"
            r"|placeholder|examples?|dummy|sample|sua[_-]?senha)['\"])"
            r"[^'\"]{6,}['\"]"
        ),
        "message": __(
            "Possible hardcoded credential in {file_name} (Line {line_number})."
        ),
    },
]
