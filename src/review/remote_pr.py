"""Review a pull request that is already open on the forge.

The use case behind ``gitpr review-pr <n>``: resolve the pull request, fetch its
diff over the API, run the very same review engine the local flows use, and
optionally publish the result as a comment. Nothing here re-implements review
logic — ``core.generate_pr_content``, ``linter_engine.parse_diff_and_lint`` and
``review.render`` are the local flow's own pieces, fed with a diff that came
from somewhere else.

Two deviations from the spec this was built against, both deliberate:

  * ``provider`` is the AI provider *name* ("gemini"/"deepseek"), not an
    instance. No provider object exists anywhere in this codebase —
    ``ai_providers.call_ai_model`` builds what it needs from the name and the
    configured key — so accepting an instance would have meant inventing a type
    to satisfy a signature.
  * the result carries no ``comment_url``. ``ScmProvider.add_comment`` returns
    None by contract and no forge here reads back the created comment, so the
    field could only ever hold a guess.
"""

from dataclasses import dataclass, field

from src.i18n import __
from src.infrastructure.scm.base import RepoRef, ScmProvider, ScmProviderError
from src.review.diff_normalizer import (
    filter_excluded_sections,
    is_reviewable_diff,
    normalize_newlines,
)
from src.review.diff_source import DiffOrigin, DiffSource

# The states in which a forge still accepts changes, across all four:
# GitHub "open", GitLab "opened", Azure "active", Bitbucket "OPEN". Compared
# case-folded, so one list covers them. A provider that reports no state at all
# is let through rather than blocked on a field it never promised.
_OPEN_STATES = ("open", "opened", "active")


class ReviewPrError(Exception):
    """A pull request that cannot be reviewed, with a message fit for the user.

    Every failure that is the user's to act on — a forge without diffs, a PR
    that does not exist or is closed, an empty or unreviewable diff — arrives
    as this rather than as a provider error or a traceback. The point is that it
    is raised *before* any AI call, so a bad PR number costs nothing.
    """


@dataclass
class ReviewRemotePrResult:
    """What a remote review produced.

    ``review`` is the AI's markdown, the same string the local flows write to
    ``.txt``: the spec called for a ``ReviewResult`` type shared with the local
    review, but the local review has never had one — it has a dict with a
    "review" key — so this field is that string and nothing more is invented.

    ``warnings`` collects what the user should know but that did not stop the
    run: files dropped by the smart excludes, a diff large enough to trigger
    map-reduce.
    """

    pr_number: int
    pr_url: str
    review: str
    diff_source: DiffSource
    linter_results: dict
    warnings: list = field(default_factory=list)
    comment_posted: bool = False


def _ai_provider_label(provider):
    """Human-readable AI provider name for messages ("gemini" -> "Gemini")."""
    return (provider or "").capitalize()


def build_comment_body(review, linter_results, provider="gemini"):
    """The markdown published on the pull request.

    The review exactly as the local flow would file it — linter alerts included,
    through the same ``compose_review_content`` — followed by a footer naming
    what produced it. The footer says AI-generated on purpose: the comment
    lands on someone else's pull request, where a reader who did not run the
    command has no other way to know a model wrote it.

    No commit SHA appears: ``PullRequestResult`` carries none and no provider
    reads ``head.sha``, so any revision marker here would be fabricated.
    """
    from src.review.render import compose_review_content
    from src.updater import __version__

    try:
        body = compose_review_content(review, linter_results)
    except Exception:
        body = review

    footer = __(
        "*Automated review by GitPR {version} — AI provider: {provider}. "
        "AI-generated content: verify before acting on it.*",
        version=__version__,
        provider=_ai_provider_label(provider),
    )
    return f"{body}\n\n---\n\n{footer}\n"


def review_remote_pr(
    pr_number,
    scm_provider: ScmProvider,
    repo_ref: RepoRef,
    ai_provider="gemini",
    post_comment=False,
):
    """Review the open pull request *pr_number* and return the result.

    ``ai_provider`` is the AI engine's name and ``scm_provider`` the forge: two
    different things that would both answer to "provider" sitting in one
    signature, so only the AI one is spelled out.

    Raises ``ReviewPrError`` for anything the caller can fix, always before the
    AI is called. Network and HTTP failures from the forge surface as
    ``ScmProviderError`` only when this module cannot say something more useful
    about them.
    """
    from src.core import generate_pr_content, get_smart_exclude_patterns
    from src.linter_engine import parse_diff_and_lint

    provider_label = getattr(scm_provider, "name", "") or "This forge"

    # 1. Capability gate — the cheapest possible rejection, before the network.
    if not getattr(scm_provider, "supports_reviewable_diff", False):
        raise ReviewPrError(
            __(
                "{provider} does not serve a reviewable diff: its API returns a "
                "list of changed files instead of a unified diff. Review this "
                "pull request locally, or use a forge that serves diffs.",
                provider=provider_label,
            )
        )

    # 2. The pull request itself. A 404 here is the "does not exist" answer —
    #    which is why this call exists instead of filtering a listing that only
    #    ever returns open PRs, one page of them.
    try:
        pr = scm_provider.get_pull_request(repo_ref, pr_number)
    except ScmProviderError as exc:
        if exc.http_status == 404:
            raise ReviewPrError(
                __(
                    "Pull request #{pr_number} was not found in {repo}.",
                    pr_number=pr_number,
                    repo=repo_ref.display,
                )
            ) from exc
        if exc.http_status in (401, 403):
            raise ReviewPrError(
                __(
                    "No permission to read pull request #{pr_number} in {repo}. "
                    "Check the token configured for {provider} (gitpr --init).",
                    pr_number=pr_number,
                    repo=repo_ref.display,
                    provider=provider_label,
                )
            ) from exc
        raise ReviewPrError(
            __(
                "Could not read pull request #{pr_number}: {error}",
                pr_number=pr_number,
                error=exc.message,
            )
        ) from exc

    # 3. A closed or merged PR has no review to publish — refusing here is what
    #    keeps a stale number from spending tokens.
    state = (pr.state or "").strip().lower()
    if state and state not in _OPEN_STATES:
        raise ReviewPrError(
            __(
                "Pull request #{pr_number} is not open (state: {state}). "
                "Only open pull requests can be reviewed.",
                pr_number=pr_number,
                state=pr.state,
            )
        )

    # 4. The diff.
    try:
        raw_diff = scm_provider.get_pull_request_diff(repo_ref, pr_number)
    except ScmProviderError as exc:
        raise ReviewPrError(
            __(
                "Could not fetch the diff of pull request #{pr_number}: {error}",
                pr_number=pr_number,
                error=exc.message,
            )
        ) from exc

    raw_diff = normalize_newlines(raw_diff or "")
    if not raw_diff.strip():
        raise ReviewPrError(
            __(
                "Pull request #{pr_number} has no diff to review.",
                pr_number=pr_number,
            )
        )

    # Safety net behind the capability flag: a provider that claims to serve
    # diffs but answers with prose (Azure's summary lines) stops here.
    if not is_reviewable_diff(raw_diff):
        raise ReviewPrError(
            __(
                "{provider} returned a file summary instead of a diff for pull "
                "request #{pr_number}. It cannot be reviewed.",
                provider=provider_label,
                pr_number=pr_number,
            )
        )

    # 5. Smart excludes. git applies these as pathspecs on every local diff; a
    #    diff from the API never passes through git, so they run here instead.
    warnings = []
    diff_text, dropped = filter_excluded_sections(
        raw_diff, get_smart_exclude_patterns()
    )
    if dropped:
        warnings.append(
            __(
                "{count} file(s) skipped by the smart excludes: {files}",
                count=len(dropped),
                files=", ".join(dropped),
            )
        )
    if not diff_text.strip():
        raise ReviewPrError(
            __(
                "Every file of pull request #{pr_number} matches the smart "
                "excludes — nothing left to review.",
                pr_number=pr_number,
            )
        )

    # 6. Provenance. The identifier is what scopes the cache, so a review of
    #    this PR can never be answered by a review of an identical local diff.
    source = DiffSource(
        origin=DiffOrigin.REMOTE_PR,
        content=diff_text,
        identifier=f"pr-{pr_number}",
        pr_number=pr_number,
        repo_ref=repo_ref,
        base_branch=pr.target_branch,
        head_branch=pr.source_branch,
    )

    # 7. The engine — unchanged, and unaware of where the diff came from.
    data = generate_pr_content(
        "review",
        "review",
        diff_text,
        ai_provider,
        cache_scope=source.cache_scope,
        store_diff=True,
    )
    review = (data or {}).get("review", "")
    if not review.strip():
        raise ReviewPrError(
            __(
                "The AI returned no review for pull request #{pr_number}.",
                pr_number=pr_number,
            )
        )

    # 8. Linter. The external bridge runs binaries against files on disk, which
    #    here would be whatever the user has checked out — not this PR.
    linter_results = parse_diff_and_lint(diff_text, skip_external=True)

    chunk_count = _chunk_count(diff_text)
    if chunk_count > 1:
        warnings.append(
            __(
                "Large diff: processed in {count} batches (map-reduce).",
                count=chunk_count,
            )
        )

    # 9. Publication, only when asked and only now that a review exists.
    comment_posted = False
    if post_comment:
        body = build_comment_body(review, linter_results, ai_provider)
        scm_provider.add_comment(repo_ref, pr_number, body)
        comment_posted = True
        warnings.append(
            __("Review published as a comment on pull request #{pr_number}.",
               pr_number=pr_number)
        )

    return ReviewRemotePrResult(
        pr_number=pr_number,
        pr_url=pr.url,
        review=review,
        diff_source=source,
        linter_results=linter_results,
        warnings=warnings,
        comment_posted=comment_posted,
    )


def _chunk_count(diff_text):
    """How many batches the engine will split *diff_text* into.

    Asked rather than observed: the engine does not report its chunk count
    back, and the callers that need it (the MCP tool especially) have no
    terminal to read the "processing in N batches" line from.
    """
    from src.core import split_diff_into_chunks

    try:
        return len(split_diff_into_chunks(diff_text, max_tokens=90000))
    except Exception:
        return 1
