# 🚀 Sugestão de Pull Request

**Mensagem de Commit Recomendada:**
```text
feat: support github enterprise domains in parse_repo_ref
```

---

## 🎯 Summary

`GitHubProvider.parse_repo_ref` previously hardcoded the `github.com` host in its regex, which caused remote URLs from GitHub Enterprise Server instances (e.g. `github.acme.com`) to fail parsing. This change replaces the host-specific pattern with a generic remote-URL parser, so the provider can resolve repository references across both github.com and self-hosted Enterprise domains without breaking the existing owner/repo contract.

## 🛠️ Technical Changes

- Add a module-level compiled regex `_REMOTE_RE` that matches a generic git remote URL: optional `user@` prefix, host with optional port, a `:` (SSH) or `/` (HTTPS) separator, and the repository path.
- Strip the URL scheme (`://`) before matching so both `https://` and `ssh://` forms are handled uniformly.
- Trim trailing slashes from the captured path, split it into segments, and enforce exactly two non-empty segments (`workspace`/`name`), raising `ValueError` otherwise.
- Preserve `raw`, `workspace`, `name`, and `provider` fields in the returned `RepoRef`, keeping the public contract unchanged.
- Add `TestParseRepoRef` unit tests covering github.com HTTPS/SSH variants, Enterprise custom domains (HTTP, SSH, custom port, embedded `user:token` credentials), and rejection of malformed or over-nested URLs.

## ⚠️ Impact/Warnings

- **Behavior change:** GitHub Enterprise Server remote URLs are now accepted; previously they raised `ValueError`. Malformed URLs and paths with depth other than exactly two segments (e.g. nested subgroups) still raise `ValueError`.
- **No database, environment variable, or dependency changes.**
- Callers that relied on the old regex being host-anchored to `github.com` should be aware that arbitrary hosts now parse successfully as long as the path resolves to two segments.

close #332

---

[![GitPR](https://img.shields.io/badge/GitPR-no_issues-brightgreen)](https://gitpr.natanfiuza.dev.br/)