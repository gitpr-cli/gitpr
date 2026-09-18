"""Compose and write the review artefact — shared by both review flows.

Extracted verbatim from the block both ``gitpr -r`` and ``gitpr -f`` already
ran, so a remote-PR review produces the same file, with the same linter header
and the same terminal messages, as a local one. The point of extracting it is
that the two flows cannot drift: an installed user sees one tool with two diff
origins, not two tools.
"""

import click

from src.i18n import __


def compose_review_content(content, linter_results):
    """Return *content* with the linter alert block prepended.

    Errors and warnings go into the same block, errors first — the report has
    never distinguished them visually. With no alerts the review is returned
    untouched, so the file of a clean run has no header at all.

    Kept separate from ``render_review_result`` because the published comment
    (src/review/remote_pr.py) must read exactly like the file: same alerts, same
    order, one implementation.
    """
    all_alerts = linter_results["errors"] + linter_results["warnings"]
    if not all_alerts:
        return content

    header = __("## 🚨 Local Static Analysis Alerts (YAML Rules)\n\n")
    for alert in all_alerts:
        header += f"- {alert}\n"
    header += __("\n---\n\n## 🤖 AI Code Review\n\n")
    return header + content


def render_review_result(content, linter_results, output_filename):
    """Report the linter verdict, then write the composed review to disk.

    Returns the path written, or None when the write failed — the caller
    decides whether a failure is fatal. ``linter_results`` is the dict
    ``parse_diff_and_lint`` returns ({"errors": [...], "warnings": [...]}).
    """
    all_alerts = linter_results["errors"] + linter_results["warnings"]

    if all_alerts:
        click.secho(
            __(
                "⚠️ Attention! Found {count} alerts in the Linter rules.",
                count=len(all_alerts),
            ),
            fg="yellow",
        )
    else:
        click.secho(
            __("✅ Local Linter passed with no rule violations!"), fg="green"
        )

    content = compose_review_content(content, linter_results)

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(content)
        click.secho(
            __(
                "\n✅ Code Review successfully generated: '{output_filename}'",
                output_filename=output_filename,
            ),
            fg="green",
            bold=True,
        )
        return output_filename
    except Exception as e:
        click.secho(__("\n❌ Error saving review: {error}", error=str(e)), fg="red")
        return None
