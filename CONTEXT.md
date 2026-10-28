# GitPR

GitPR is a Python CLI that automates pull requests, commits, code reviews and
issues with AI. It is distributed only through PyPI, so an installed release
must not keep running once a newer one has been published.

## Language

**Update gate**:
The rule that an installed GitPR refuses to run while a newer release is
published on PyPI.
_Avoid_: version check, version lock, auto-update

**Update check**:
The act of asking PyPI which release is currently published. It can be muted by
configuration, and a check that gets no answer never blocks.
_Avoid_: version verification, ping

**Release cache**:
The remembered answer of the update check together with the moment it was
obtained.
_Avoid_: update file, daily cache

**Freshness window**:
The rolling period during which a remembered release answer may be reused
instead of asking PyPI again.
_Avoid_: cache day, TTL

**Interactive run**:
A run attached to a terminal at both ends that is allowed to stop and ask the
user. Scripts, pipes, hooks and the MCP server are never interactive.
_Avoid_: CLI mode, TTY run
