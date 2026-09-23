"""Release flow orchestration for the ``gitpr release`` subcommand.

Connects the pure modules (``commit_classifier``, ``version_bump``,
``changelog_builder``) to the real environment, mirroring how
``issue_engine.py`` orchestrates git + AI + output:

- resolves the commit range from ``--since``, or from the previous version
  section of the changelog (default), falling back to the latest tag;
- classifies every commit of the range by Conventional Commits;
- drops what a previous section already listed, so each version shows its delta;
- decides the target version (``--version`` override or semver suggestion);
- asks the AI for an executive summary (optional, degrades with a warning);
- assembles the changelog section (Markdown, with commit/PR/profile links) and
  prepends it to the changelog file, idempotently (aborts when the version
  section exists, ``--force`` regenerates);
- publishes the release on the configured forge when requested.

Read-only by design (grill Q3): the flow never edits version files and never
creates local tags — the tag is created by the forge API on publish.
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import click

from src.ai_providers import call_ai_model
from src.cache import get_cached_response, save_cached_response
from src.changelog_builder import (
    LinkContext,
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
from src.infrastructure.scm import detect_provider_from_remote, repo_web_base
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

# Header of a changelog block, ex.: "## [1.2.0] - 2026-09-07" or "## Unreleased".
# Level 2 only: the "###" subsections of a release (Summary, Features, ...) are
# part of the block, so a section ends at the next level-2 header, never sooner.
_BLOCK_HEADER_RE = re.compile(r"(?m)^##\s")
_VERSION_SECTION_PREFIX = re.compile(r"(?m)^##\s*\[")

# Short hash of a bullet, in both shapes the section writer ever emitted: the
# current "([a799664](…/commit/a799664…))" and the older "(a799664)".
_HASH_RE = re.compile(r"[\(\[]([0-9a-f]{7,40})[\)\]]")

# Contributor login cache (~/.gitpr/cache): e-mail -> forge login.
_CONTRIBUTORS_CACHE_NAME = "contributors.json"


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


# ── Changelog as the range boundary (anti-duplicate) ────────────────────────


def _read_changelog(changelog_path):
    """Returns the changelog content, or None when it cannot be read."""
    if not changelog_path:
        return None
    try:
        with open(changelog_path, "r", encoding="utf-8", errors="replace") as handle:
            return handle.read()
    except OSError:
        return None


def _version_blocks(content):
    """Splits a changelog into ``[(version, body)]``, in file order (newest first).

    Headings whose version does not parse as semver ("Unreleased", free prose)
    are skipped: only a real release can anchor the next range.
    """
    text = content or ""
    headings = list(_VERSION_SECTION_PREFIX.finditer(text))
    blocks = []
    for index, heading in enumerate(headings):
        closing = text.find("]", heading.end())
        if closing == -1:
            continue
        version = text[heading.end():closing].strip()
        if parse_semver_tag(version) is None:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        blocks.append((version, text[heading.start():end]))
    return blocks


def _previous_block(content, target_version):
    """First released section that is not ``target_version``.

    Skipping the target matters for --force: regenerating a section must anchor
    on the release *before* it, never on the section being rewritten.
    """
    target = parse_semver_tag(target_version) if target_version else None
    for version, body in _version_blocks(content):
        if target is not None and parse_semver_tag(version) == target:
            continue
        return version, body
    return None, None


def _hashes_in(text):
    """Short hashes referenced by the bullets of one section."""
    return {match.group(1)[:7] for match in _HASH_RE.finditer(text or "")}


def _ref_exists(root, ref):
    """True when ``ref`` resolves to a commit of the repository."""
    completed = _run_git(root, ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"])
    return completed.returncode == 0


def _is_ancestor(root, ref):
    """True when ``ref`` is reachable from HEAD, so it can start a range."""
    return _run_git(root, ["merge-base", "--is-ancestor", ref, "HEAD"]).returncode == 0


def _newest_commit_of(root, hashes):
    """Full sha of the most recent commit among ``hashes``, or None.

    One ``git log --no-walk`` resolves them all; the newest of them is the tip
    of the previous release, which is exactly where the new range starts.
    """
    if not hashes:
        return None
    completed = _run_git(
        root,
        ["log", "--no-walk", f"--pretty=format:%H{_LOG_SEP_FIELD}%at", *sorted(hashes)],
    )
    if completed.returncode != 0:
        return None
    newest_hash, newest_time = None, -1
    for line in completed.stdout.splitlines():
        commit_hash, _, timestamp = line.partition(_LOG_SEP_FIELD)
        # Epoch seconds, not the ISO date: ordering must survive mixed timezones.
        if commit_hash and timestamp.lstrip("-").isdigit() and int(timestamp) > newest_time:
            newest_hash, newest_time = commit_hash, int(timestamp)
    return newest_hash


def _range_origin(root, since_tag, target_version, changelog_path, warnings):
    """Decides where the release range starts.

    Returns ``(origin, previous_version, source)``. The previous section of the
    changelog is the source of truth: its newest bullet hash is the tip of the
    last release and its version tag the fallback for sections written by hand
    (the 0.0.x era carries no hashes). ``git describe`` is the last resort and
    is announced, because its range can list commits that already shipped.
    """
    content = _read_changelog(changelog_path)
    previous_version, previous_body = _previous_block(content, target_version)

    if since_tag:
        _ensure_ref_exists(root, since_tag)
        return since_tag, previous_version, "explicit"

    anchor = _newest_commit_of(root, _hashes_in(previous_body))
    if anchor and _is_ancestor(root, anchor):
        return anchor, previous_version, "changelog"

    for candidate in (previous_version, f"v{previous_version}" if previous_version else None):
        if candidate and _ref_exists(root, candidate) and _is_ancestor(root, candidate):
            return candidate, previous_version, "changelog"

    # No previous release to anchor on (first release, empty changelog): the
    # latest tag is the documented default and there is nothing to duplicate.
    if previous_version:
        warnings.append(
            __(
                "⚠️ Could not locate the previous release in {path}; using the latest tag, so already released commits may appear again.",
                path=changelog_path,
            )
        )
    return _latest_tag(root), previous_version, "fallback"


def _drop_released(commits, content, target_version):
    """Drops the commits another release section already listed.

    The range anchor makes this redundant when it works. It is kept because a
    changelog can be edited by hand, and because sections generated with a
    wider range overlap the following one exactly like the 1.3.0 did.
    """
    target = parse_semver_tag(target_version) if target_version else None
    released = set()
    for version, body in _version_blocks(content):
        if target is not None and parse_semver_tag(version) == target:
            continue  # the section being (re)generated is not "already released"
        released |= _hashes_in(body)
    if not released:
        return commits, 0
    kept = [commit for commit in commits if commit.short_hash not in released]
    return kept, len(commits) - len(kept)


# ── Links (commit / pull request / contributor profile) ─────────────────────


def _origin_remote(root):
    """Origin remote URL, or None when the repository has no origin."""
    completed = _run_git(root, ["remote", "get-url", "origin"])
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def _contributors_cache_path():
    """Path of the shared ``email -> login`` cache."""
    return Path.home() / ".gitpr" / "cache" / _CONTRIBUTORS_CACHE_NAME


def _load_contributor_logins():
    """Cached ``email -> login`` map; {} when missing or unreadable."""
    try:
        with open(
            _contributors_cache_path(), "r", encoding="utf-8", errors="replace"
        ) as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_contributor_logins(logins):
    """Best-effort cache write: a release never fails on it."""
    try:
        path = _contributors_cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", errors="replace") as handle:
            json.dump(logins, handle, indent=2, ensure_ascii=False, sort_keys=True)
    except OSError:
        pass


def _newest_commit_per_email(commits):
    """``email -> full hash`` of the newest commit each author has in the range.

    ``commits`` comes out of ``git log`` newest first, so the first commit seen
    for an email is the one most likely to already exist on the forge.
    """
    newest = {}
    for commit in commits or ():
        email = (commit.author_email or "").lower()
        if email and email not in newest:
            newest[email] = commit.hash
    return newest


def _lookup_contributor_login(provider, repo_ref, email, sha):
    """Login for one author: the commit first, the email search second.

    Same ladder as the reviewer resolution (``reviewer_resolution.py``): the
    commit lookup is the reliable one — it sees corporate addresses that the
    user search API cannot. The email fallback covers commits the forge does
    not know (never pushed, shallow clone) and any failure of the first step.
    """
    get_commit_author_login = getattr(provider, "get_commit_author_login", None)
    if callable(get_commit_author_login) and repo_ref is not None and sha:
        try:
            login = get_commit_author_login(repo_ref, sha)
        except Exception:
            login = None
        if login:
            return login
    email_to_handle = getattr(provider, "email_to_handle", None)
    if callable(email_to_handle):
        try:
            return email_to_handle(email)
        except Exception:
            return None
    return None


def _resolve_contributor_logins(commits, remote):
    """Best-effort ``email -> login`` map for the authors of the range.

    Never raises: without a token, offline, or on a forge with no handle
    lookup, contributors keep their display name. Only successful lookups are
    cached, so a rate-limited run retries on the next release instead of
    freezing the failure forever.
    """
    newest = _newest_commit_per_email(commits)
    if not newest:
        return {}
    cache = _load_contributor_logins()
    missing = sorted(email for email in newest if email not in cache)
    if missing:
        provider = repo_ref = None
        try:
            from src.config import get_scm_settings
            from src.infrastructure.scm.factory import resolve_scm_provider

            provider = resolve_scm_provider(get_scm_settings())
            if remote:
                repo_ref = provider.parse_repo_ref(remote)
        except Exception:
            repo_ref = None  # unusable provider: emails keep their display name
        if provider is not None:
            resolved_any = False
            for email in missing:
                login = _lookup_contributor_login(
                    provider, repo_ref, email, newest[email]
                )
                if login:
                    cache[email] = login
                    resolved_any = True
            if resolved_any:
                _save_contributor_logins(cache)
    return {email: cache[email] for email in newest if cache.get(email)}


def _build_link_context(root, commits):
    """Link targets for the bullets and the contributor footer of one section.

    ``None`` (no origin remote, or a remote we cannot parse) makes the builder
    render plain text — a valid section, only without links.
    """
    remote = _origin_remote(root)
    base = repo_web_base(remote)
    if not base:
        return None
    logins = {}
    by_email = _resolve_contributor_logins(commits, remote)
    if by_email:
        for commit in commits:
            login = by_email.get((commit.author_email or "").lower())
            if login and commit.author_name:
                logins.setdefault(commit.author_name, login)
    return LinkContext(
        provider=detect_provider_from_remote(base), base=base, logins=logins
    )


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
        provider,
        api_key,
        api_model,
        prompt,
        system_instruction,
        quiet=quiet,
        action="release_summary",
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
        provider,
        api_key,
        api_model,
        merge_prompt,
        system_instruction,
        quiet=quiet,
        action="release_summary",
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
    changelog_path="CHANGELOG.md",
):
    """Runs the full local pipeline (range → classify → version → summary → markdown).

    Performs no file writes and never publishes: the caller decides where the
    resulting ``ReleaseNotesResult.markdown`` goes (see ``upsert_changelog``)
    and whether to call ``publish_release``.

    Args:
        repo_path: path to the repository (default: current directory).
        since_tag: explicit range origin; when omitted, the previous version
            section of the changelog is used (see ``_range_origin``).
        target_version: explicit ``x.y.z`` override. When omitted, the semver
            suggestion is used (requires ``auto_bump`` and a previous semantic
            version, otherwise ``ReleaseNotesError``).
        ai_summary: generate the AI executive summary when True.
        auto_bump: allow the automatic semver suggestion when True.
        provider: AI provider name override (default: configured provider).
        quiet: suppress terminal messages (mandatory for --format json).
        ask_version: when the version comes from the automatic suggestion and
            stdin is interactive, ask the user to accept it or type another
            (default False keeps the flow non-interactive).
        changelog_path: changelog file whose previous section bounds the range
            and whose hashes filter the already released commits (relative to
            the repository root or absolute).

    Returns:
        The assembled ``ReleaseNotesResult``.
    """
    root = get_repo_root(repo_path)

    resolved_changelog = changelog_path
    if resolved_changelog and not os.path.isabs(resolved_changelog):
        resolved_changelog = os.path.join(root, resolved_changelog)

    warnings = []
    since_used, previous_version, _origin_source = _range_origin(
        root, since_tag, target_version, resolved_changelog, warnings
    )

    raw_commits = _collect_raw_commits(root, since_used)
    if not raw_commits:
        if since_used:
            raise ReleaseNotesError(
                __("❌ No commits found since '{since}'. Nothing to release.", since=since_used)
            )
        raise ReleaseNotesError(__("❌ This repository has no commits yet."))

    commits = classify_commits(raw_commits)

    commits, already_released = _drop_released(
        commits, _read_changelog(resolved_changelog), target_version
    )
    if already_released:
        warnings.append(
            __(
                "{count} commit(s) already released in a previous version were skipped.",
                count=already_released,
            )
        )
    if not commits:
        raise ReleaseNotesError(
            __(
                "❌ Nothing new to release: every commit of the range is already in {path}.",
                path=resolved_changelog,
            )
        )

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
        # Baseline: the version of the previous changelog section (the release
        # the user actually shipped), then the range anchor when it is a tag,
        # and only then the highest semver tag reachable from HEAD.
        baseline = previous_version or since_used
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
        links=_build_link_context(root, commits),
    )
    return ReleaseNotesResult(
        version=target_version,
        previous_tag=since_used,
        previous_version=previous_version,
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
    next_header = _BLOCK_HEADER_RE.search(content, match.end())
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
