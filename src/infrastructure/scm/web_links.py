"""Web (browser) URLs for commits, pull requests and user profiles.

The SCM providers speak API URLs only: ``base_url`` is an API root and every
web URL GitPR has ever used came back inside an API payload (``html_url`` /
``web_url``). The release notes are the first artifact that has to *build* an
HTML link locally, from nothing but the origin remote, so the patterns live
here rather than on the provider ABC — this is a formatting concern, and a
link-less bullet is still perfectly valid output.

Pure module: string in, string out, no I/O and no network. ``None`` means
"this forge has no such page", and callers degrade to plain text instead of
emitting a broken link.
"""

# {base} is the repository web root (no trailing slash), {host} its origin.
# A None entry disables that kind for the forge.
_PATTERNS = {
    "github": {
        "commit": "{base}/commit/{sha}",
        "pull": "{base}/pull/{number}",
        "user": "{host}/{login}",
    },
    "gitlab": {
        "commit": "{base}/-/commit/{sha}",
        "pull": "{base}/-/merge_requests/{number}",
        "user": "{host}/{login}",
    },
    "bitbucket": {
        "commit": "{base}/commits/{sha}",
        "pull": "{base}/pull-requests/{number}",
        "user": "{host}/{login}",
    },
    "azure_devops": {
        "commit": "{base}/commit/{sha}",
        "pull": "{base}/pullrequest/{number}",
        # Azure DevOps has no stable public profile page, so contributors stay
        # as plain names there.
        "user": None,
    },
}


def repo_web_base(remote_url):
    """Returns the repository web root for a git remote URL, or None.

    Accepts every shape a remote can take — ``https://host/path.git``,
    ``ssh://git@host/path``, ``git://host/path`` and the scp-like
    ``git@host:path`` — and always answers with ``https``, because the result
    is a link meant for a browser, not for git.
    """
    url = (remote_url or "").strip()
    if not url:
        return None

    if "://" in url:
        _, _, rest = url.partition("://")
        # Credentials ("git@" and "user:pass@") are never part of a web URL.
        authority, _, path = rest.partition("/")
        if "@" in authority:
            authority = authority.rsplit("@", 1)[1]
        host = authority
    else:
        # scp-like syntax has no scheme: git@github.com:owner/repo.git
        head, separator, path = url.partition(":")
        if not separator:
            return None
        host = head.rsplit("@", 1)[-1]

    path = path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]

    if not host or not path:
        return None
    return f"https://{host}/{path}"


def _host_of(base):
    """Origin part of a web base, ex.: "https://github.com"."""
    return "/".join(base.split("/")[:3])


def _render(kind, provider, base, **values):
    """Applies the forge pattern for ``kind``; None when unknown or disabled."""
    pattern = _PATTERNS.get((provider or "").strip().lower(), {}).get(kind)
    if not base or not pattern:
        return None
    return pattern.format(base=base, host=_host_of(base), **values)


def commit_url(provider, base, sha):
    """Web URL of one commit, or None when the forge has no known pattern."""
    return _render("commit", provider, base, sha=sha)


def pull_request_url(provider, base, number):
    """Web URL of one pull/merge request, or None when unknown."""
    return _render("pull", provider, base, number=number)


def user_url(provider, base, login):
    """Web URL of a user profile, or None when the forge has no such page."""
    return _render("user", provider, base, login=login)
