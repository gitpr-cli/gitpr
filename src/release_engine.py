"""Release flow orchestration for the ``gitpr release`` subcommand.

Connects the pure modules (``commit_classifier``, ``version_bump``,
``changelog_builder``) to the real environment, mirroring how
``issue_engine.py`` orchestrates git + AI + output:

- resolves the commit range from ``--since`` (default: the latest tag) to HEAD;
- classifies every commit of the range by Conventional Commits;
- decides the target version (``--version`` override or semver suggestion);
- asks the AI for an executive summary (optional, degrades with a warning);
- assembles the changelog section (Markdown) and prepends it to the changelog
  file, idempotently (aborts when the version section exists, ``--force``
  regenerates);
- publishes the release on the configured forge when requested.

Read-only by design (grill Q3): the flow never edits version files and never
creates local tags — the tag is created by the forge API on publish.
"""

import re
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime

import click

from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.changelog_builder import (
    ReleaseNotesResult,
    build_release_section,
    normalize_contributors,
    organize_commits,
    release_body,
)
from src.commit_classifier import classify_commits
from src.config import get_api_key, get_api_model, get_ai_provider
from src.core import get_skill_context
from src.i18n import CURRENT_LANG, __
from src.version_bump import parse_semver_tag, suggest_next_version

# Commits per AI batch: beyond this, the summary goes through Map-Reduce
# batches to stay safely inside the token window (same philosophy as the
# diff map-reduce used by the other engines).
_SUMMARY_BATCH_SIZE = 200

# git log placeholder record/field separators: subjects and bodies almost never
# contain ASCII control characters, so parsing is unambiguous.
_LOG_SEP_RECORD = "\x1e"
_LOG_SEP_FIELD = "\x1f"
_LOG_FORMAT = (
    "%x1e%H" + "%x1f%an" + "%x1f%ae" + "%x1f%aI" + "%x1f%s" + "%x1f%b"
)

# Existing changelog version-section header, ex.: "## [1.2.0] - 2026-09-07".
_SECTION_HEADER_RE = re.compile(r"(?m)^#{1,6}\s")
_VERSION_SECTION_PREFIX = re.compile(r"(?m)^##\s*\[")


class ReleaseNotesError(Exception):
    """Raised when the release flow cannot proceed (user-facing message)."""


def _say(quiet, text, **kwargs):
    """Terminal message, suppressed when stdout must stay clean (--format json)."""
    if not quiet:
        click.secho(text, **kwargs)


def _run_git(root, args):
    """Runs a git command inside ``root`` with the project UTF-8 convention."""
    return subprocess.run(
        ["git", "-C", root, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def get_repo_root(repo_path):
    """Resolves ``repo_path`` to the repository top-level directory."""
    completed = _run_git(repo_path, ["rev-parse", "--show-toplevel"])
    if completed.returncode != 0:
        raise ReleaseNotesError(
            __("❌ '{path}' is not inside a git repository.", path=repo_path)
        )
    return completed.stdout.strip()


def _ensure_ref_exists(root, ref):
    """Fails fast when the user-supplied --since reference does not exist."""
    completed = _run_git(root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    if completed.returncode != 0:
        raise ReleaseNotesError(
            __("❌ Tag or reference '{ref}' not found in this repository.", ref=ref)
        )


def _latest_tag(root):
    """Returns the latest reachable tag (git describe), or None on a first release."""
    completed = _run_git(root, ["describe", "--tags", "--abbrev=0"])
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _latest_semver_tag(root):
    """Returns the highest semver tag reachable from HEAD, or None."""
    completed = _run_git(root, ["tag", "--merged", "HEAD"])
    if completed.returncode != 0:
        return None
    candidates = [
        (parse_semver_tag(tag), tag)
        for tag in completed.stdout.splitlines()
        if parse_semver_tag(tag) is not None
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0][1:])[1]


def _collect_raw_commits(root, since_used):
    """Returns the raw commits of the ``since..HEAD`` range as dicts.

    Newest first (native git log order). With ``since_used=None`` the whole
    history is used (first release). Merge commits are skipped so squash-merged
    PR lines are not double counted.
    """
    args = ["log", "--no-merges", f"--pretty=format:{_LOG_FORMAT}"]
    args.append(f"{since_used}..HEAD" if since_used else "HEAD")
    completed = _run_git(root, args)
    if completed.returncode != 0:
        raise ReleaseNotesError(
            __("❌ Failed to read the git history: {error}", error=completed.stderr.strip())
        )

    raw_commits = []
    for record in completed.stdout.split(_LOG_SEP_RECORD):
        record = record.strip("\n\x1e")
        if not record:
            continue
        fields = record.split(_LOG_SEP_FIELD)
        if len(fields) < 6:
            continue  # corrupt record — never crash the whole release on it
        commit_hash, author_name, author_email, date, subject, body = fields[:6]
        raw_commits.append(
            {
                "hash": commit_hash,
                "short_hash": commit_hash[:7],
                "author_name": author_name,
                "author_email": author_email,
                "date": date,
                "subject": subject,
                "body": body,
            }
        )
    return raw_commits


def _language_for_prompt():
    """Maps the interface language code to a spoken language name."""
    names = {
        "pt_br": "Brazilian Portuguese",
        "pt_pt": "European Portuguese",
        "es_es": "Spanish",
        "fr_fr": "French",
        "en_us": "English",
    }
    return names.get(CURRENT_LANG.lower(), "English")


def _summarize_batch(provider, api_key, api_model, commits, system_instruction, quiet=False):
    """Summarizes a batch of commits with the AI, using the response cache."""
    lines = [
        "- {subject} ({short_hash})".format(subject=c.subject, short_hash=c.short_hash)
        for c in commits
    ]
    prompt = (
        __(
            "Generate ONLY a JSON object in the format {json_format} containing an executive summary in {language} of what changed in this release. Highlight the user-facing impact for changelog readers, never list code identifiers:\n",
            json_format='{"summary": "..."}',
            language=_language_for_prompt(),
        )
        + "\n".join(lines)
    )

    cached = get_cached_response("release_summary", prompt)
    if cached and cached.get("summary"):
        _say(quiet, __("⚡ Release summary retrieved from local cache."), fg="green", dim=True)
        return cached["summary"]

    response = call_ai_model(
        provider, api_key, api_model, prompt, system_instruction, action="release_summary"
    )
    if not response:
        return None
    summary = response.get("summary")
    if summary:
        save_cached_response(
            "release_summary", "release_summary", prompt, {"summary": summary}
        )
    return summary


def _generate_summary(provider, api_key, api_model, commits, quiet=False):
    """Executive summary with Map-Reduce for very long ranges. None on failure."""
    # Skill-first: the user's .gitpr.release.md overrides the summary persona
    # (same consumption rule as the other engines). "quiet" keeps the skill
    # loading messages off stdout (mandatory for --format json).
    system_instruction = get_skill_context("release", quiet=quiet) or __(
        "You are a Release Manager. Write the release summary for the changelog of a software project."
    )
    if len(commits) <= _SUMMARY_BATCH_SIZE:
        return _summarize_batch(
            provider, api_key, api_model, commits, system_instruction, quiet=quiet
        )

    _say(
        quiet,
        __(
            "📦 Large commit range detected! Summarizing in {count} batches (Map-Reduce)...",
            count=(len(commits) + _SUMMARY_BATCH_SIZE - 1) // _SUMMARY_BATCH_SIZE,
        ),
        fg="yellow",
        bold=True,
    )
    partials = []
    for start in range(0, len(commits), _SUMMARY_BATCH_SIZE):
        _say(
            quiet,
            __("⏳ Summarizing batch {current}...", current=(start // _SUMMARY_BATCH_SIZE) + 1),
            fg="cyan",
            dim=True,
        )
        partial = _summarize_batch(
            provider,
            api_key,
            api_model,
            commits[start : start + _SUMMARY_BATCH_SIZE],
            system_instruction,
            quiet=quiet,
        )
        if partial:
            partials.append(partial)

    if not partials:
        return None
    if len(partials) == 1:
        return partials[0]

    # Reduce: merge the partial summaries into a single executive paragraph.
    merge_prompt = (
        __(
            "Generate ONLY a JSON object in the format {json_format} merging the partial release summaries below into one single executive summary paragraph in {language}:\n",
            json_format='{"summary": "..."}',
            language=_language_for_prompt(),
        )
        + "\n\n".join(f"### Batch {i}\n{p}" for i, p in enumerate(partials, 1))
    )
    cached = get_cached_response("release_summary", merge_prompt)
    if cached and cached.get("summary"):
        return cached["summary"]
    response = call_ai_model(
        provider, api_key, api_model, merge_prompt, system_instruction, action="release_summary"
    )
    if response and response.get("summary"):
        save_cached_response(
            "release_summary", "release_summary", merge_prompt, {"summary": response["summary"]}
        )
        return response["summary"]
    # Degrade gracefully: joined partials beat an empty summary.
    return "\n\n".join(partials)


def _stdin_is_interactive():
    """True when stdin is a TTY (interactive prompt allowed).

    Non-interactive callers (--format json consumers, CI, MCP tool calls)
    must never block on a version question.
    """
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _ask_about_suggested_version(suggestion):
    """Lets the user accept the suggested version or type another one.

    Interactive only: accept by default; declining loops until a valid semver
    is typed (validation mirrors the explicit --version rule).
    """
    if click.confirm(
        __("❓ Use the suggested version {version}?", version=suggestion),
        default=True,
        show_default=False,
    ):
        return suggestion
    while True:
        answer = click.prompt(
            __("✏️ Type another version (semantic versioning, ex.: 1.2.3)")
        ).strip()
        if parse_semver_tag(answer) is not None:
            return answer
        click.secho(
            __(
                "❌ Invalid target version '{version}'. Use semantic versioning, ex.: 1.2.3",
                version=answer,
            ),
            fg="red",
            err=True,
        )


def generate_release_notes(
    repo_path=".",
    since_tag=None,
    target_version=None,
    ai_summary=True,
    auto_bump=True,
    provider=None,
    quiet=False,
    ask_version=False,
):
    """Runs the full local pipeline (range → classify → version → summary → markdown).

    Performs no file writes and never publishes: the caller decides where the
    resulting ``ReleaseNotesResult.markdown`` goes (see ``upsert_changelog``)
    and whether to call ``publish_release``.

    Args:
        repo_path: path to the repository (default: current directory).
        since_tag: range origin; default is the latest reachable tag, or the
            first commit when no tag exists (first release).
        target_version: explicit ``x.y.z`` override. When omitted, the semver
            suggestion is used (requires ``auto_bump`` and a previous semver
            tag, otherwise ``ReleaseNotesError``).
        ai_summary: generate the AI executive summary when True.
        auto_bump: allow the automatic semver suggestion when True.
        provider: AI provider name override (default: configured provider).
        quiet: suppress terminal messages (mandatory for --format json).
        ask_version: when the version comes from the automatic suggestion and
            stdin is interactive, ask the user to accept it or type another
            (default False keeps the flow non-interactive).

    Returns:
        The assembled ``ReleaseNotesResult``.
    """
    root = get_repo_root(repo_path)

    since_used = since_tag
    if since_used:
        _ensure_ref_exists(root, since_used)
    else:
        since_used = _latest_tag(root)  # None = first release, whole history

    raw_commits = _collect_raw_commits(root, since_used)
    if not raw_commits:
        if since_used:
            raise ReleaseNotesError(
                __("❌ No commits found since '{since}'. Nothing to release.", since=since_used)
            )
        raise ReleaseNotesError(__("❌ This repository has no commits yet."))

    commits = classify_commits(raw_commits)

    warnings = []
    non_conventional = sum(1 for commit in commits if not commit.raw_type)
    if non_conventional:
        warnings.append(
            __(
                "{count} commit(s) without Conventional Commits, categorized as OTHER.",
                count=non_conventional,
            )
        )

    # ── Version: explicit override or semver suggestion ─────────────────────
    if target_version:
        if parse_semver_tag(target_version) is None:
            raise ReleaseNotesError(
                __(
                    "❌ Invalid target version '{version}'. Use semantic versioning, ex.: 1.2.3",
                    version=target_version,
                )
            )
    else:
        # Baseline: the range anchor itself when it is a version tag, otherwise
        # the highest semver tag reachable from HEAD.
        baseline = since_used
        if parse_semver_tag(baseline) is None:
            baseline = _latest_semver_tag(root)
        suggestion = suggest_next_version(commits, baseline) if baseline else None

        if suggestion and auto_bump:
            target_version = suggestion
            _say(
                quiet,
                __("📈 Suggested version: {version} (semantic bump)", version=suggestion),
                fg="cyan",
                dim=True,
            )
            if ask_version and not quiet and _stdin_is_interactive():
                target_version = _ask_about_suggested_version(suggestion)
        elif not auto_bump:
            raise ReleaseNotesError(
                __(
                    "❌ Automatic version bump is disabled. Pass --version x.y.z explicitly."
                )
            )
        else:
            raise ReleaseNotesError(
                __(
                    "❌ No previous semantic version tag found to suggest a bump. Pass --version x.y.z explicitly."
                )
            )

    # ── AI executive summary (optional, graceful degradation) ───────────────
    summary = ""
    if ai_summary:
        resolved_provider = provider or get_ai_provider()
        api_key = get_api_key(resolved_provider)
        api_model = get_api_model(resolved_provider, task_complexity="advanced")
        if not api_key:
            warnings.append(
                __(
                    "AI summary skipped: no API key configured for {provider}. Generate one with --install.",
                    provider=resolved_provider,
                )
            )
        else:
            _say(
                quiet,
                __(
                    "🤖 Generating executive summary using {provider} ({api_model})...",
                    provider=resolved_provider.capitalize(),
                    api_model=api_model,
                ),
                fg="cyan",
                dim=True,
            )
            summary = _generate_summary(
                resolved_provider, api_key, api_model, commits, quiet=quiet
            ) or ""
            if not summary:
                warnings.append(
                    __("AI summary failed: changelog generated without a summary.")
                )

    # ── Assemble the result ──────────────────────────────────────────────────
    generated_at = datetime.now().isoformat(timespec="seconds")
    sections, breaking_changes = organize_commits(commits)
    contributors = normalize_contributors(commits)
    markdown = build_release_section(
        target_version,
        generated_at,
        summary,
        sections,
        breaking_changes,
        contributors,
    )
    return ReleaseNotesResult(
        version=target_version,
        previous_tag=since_used,
        generated_at=generated_at,
        summary=summary,
        sections=sections,
        breaking_changes=breaking_changes,
        contributors=contributors,
        markdown=markdown,
        warnings=warnings,
    )


def _find_version_section(content, version):
    """Returns ``(start, end)`` of the existing section for ``version`` or None."""
    pattern = re.compile(
        r"(?m)^##\s*\[" + re.escape(version) + r"\]"
    )
    match = pattern.search(content)
    if not match:
        return None
    start = match.start()
    next_header = _SECTION_HEADER_RE.search(content, match.end())
    return (start, next_header.start()) if next_header else (start, len(content))


def _insert_new_section(content, block):
    """Prepends ``block`` under a leading H1 title (when present), never overwriting."""
    block = block.rstrip("\n")
    if not content:
        return block + "\n"
    if content.startswith("# "):
        # Keep the "# Title" first line on top; drop blank padding after it.
        after_title = content.split("\n", 1)[1]
        rest = after_title.lstrip("\n")
        return "# {title}\n\n{block}\n\n{rest}".format(
            title=content.split("\n", 1)[0][2:], block=block, rest=rest
        )
    return block + "\n\n" + content


def upsert_changelog(changelog_path, version, markdown, force=False):
    """Writes or prepends the version section to the changelog (idempotent).

    Args:
        changelog_path: file path of the changelog (relative to the repo root
            or absolute).
        version: target version whose section is being written.
        markdown: the section Markdown produced by the builder.
        force: when True, an existing section for ``version`` is replaced.

    Returns:
        "created" when the file was new, "replaced" when an existing section
        was regenerated.

    Raises:
        ReleaseNotesError: the version section already exists and ``force`` is
            False (the caller surfaces the --force escape hatch).
    """
    try:
        with open(changelog_path, "r", encoding="utf-8", errors="replace") as f:
            existing = f.read()
    except FileNotFoundError:
        existing = None

    status = "created"
    if existing is not None:
        span = _find_version_section(existing, version)
        if span is not None:
            if not force:
                raise ReleaseNotesError(
                    __(
                        "❌ Version {version} already has a section in {path}. Pass --force to regenerate it.",
                        version=version,
                        path=changelog_path,
                    )
                )
            start, end = span
            # Drop the old block, keeping whatever precedes/follows it.
            existing = existing[:start] + existing[end:]
            status = "replaced"
        content = _insert_new_section(existing, markdown)
    else:
        content = _insert_new_section("", markdown)

    with open(changelog_path, "w", encoding="utf-8", errors="replace") as f:
        f.write(content)
    return status


def publish_release(release_result, provider, repo, draft=False):
    """Publishes the release on the forge via ``provider.create_release``.

    Args:
        release_result: the ``ReleaseNotesResult`` being published.
        provider: a resolved ``ScmProvider`` instance.
        repo: the ``RepoRef`` of the repository on the forge.
        draft: create a forge draft. GitLab has no native draft: a warning is
            shown and the release is published directly.

    Returns:
        The URL of the created release.

    Raises:
        ScmProviderError: the forge refused the operation; the local changelog
            flow is unaffected.
    """
    target_draft = bool(draft)
    if draft and getattr(provider, "name", "") == "gitlab":
        click.secho(
            __("⚠️ GitLab has no native draft: publishing the release directly."),
            fg="yellow",
        )
        target_draft = False

    return provider.create_release(
        repo,
        tag=release_result.version,
        title=release_result.version,
        body=release_body(release_result.markdown),
        draft=target_draft,
    )


def result_to_json(release_result):
    """Serializes a ReleaseNotesResult for ``--format json`` (stdout only)."""
    return asdict(release_result)
