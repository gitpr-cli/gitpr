"""The numbers the badge is allowed to show, measured before it is built.

The badge is a public claim printed on someone else's pull request, so it is
only ever built from a measurement that actually happened. Two consequences
shape this module:

- The only structured number the default ``gitpr pr`` flow can produce offline
  is the static linter's alert lists — the AI call returns prose, with no
  severities and no per-finding structure.
- The linter short-circuits to empty lists when no rules are configured, and
  that is the common case for anyone who never ran ``gitpr --skill``. Empty
  lists there mean "nothing was checked", not "nothing was found", and the
  return value alone cannot tell the two apart. So the rules are inspected
  first, and no badge is produced when there are none.

Nothing here raises: a badge is decoration, and decoration never gets to stop
a pull request from being published.
"""

from dataclasses import dataclass

from src.config import load_linter_rules
from src.linter_engine import parse_diff_and_lint


@dataclass(frozen=True)
class BadgeCounts:
    """What the linter found in a diff: two counts, nothing else."""

    errors: int
    warnings: int


def collect_linter_counts(diff_text):
    """Count the linter alerts for ``diff_text``.

    Returns ``BadgeCounts``, or ``None`` when there is nothing the badge could
    honestly report: no rules configured, or a failure anywhere in the linter.
    ``skip_external`` keeps this to the YAML rules — the external bridge runs
    binaries against the working tree, which is not the revision being reviewed.
    """
    try:
        if not load_linter_rules():
            return None

        alerts = parse_diff_and_lint(diff_text, skip_external=True)
    except Exception:
        return None

    return BadgeCounts(
        errors=len(alerts.get("errors", [])),
        warnings=len(alerts.get("warnings", [])),
    )
