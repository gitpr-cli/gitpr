## Completion Report — Co-Author Trailer Hidden in TUI Until Commit Confirmation

### What was done
- Removed the `Co-Authored-By: Gitpr-cli <gitpr@natanfiuza.dev.br>` trailer from the commit message shown in the PR Publisher TUI edit screen (`CommitMessageScreen`).
- The trailer is now injected at commit execution time (right before `execute_git_commit()`), only after the user confirms the commit — so the TUI never displays it, but the final commit still carries it.
- Console flows unchanged: `gitpr -c` (`--commit`), `--hook` mode, `--no-edit` auto-commit and the MCP `generate_commit_message` tool keep appending the trailer at generation time.
- `self._pending_commit_msg` stays clean (no trailer), preserving the pure AI phrase in the PR title fallback and the "Recommended Commit Message" block of the saved/published PR description.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| src/ui/pr_publish_app.py | fix | `_generate_commit_msg()` passes the raw AI message to the edit screen; `_start_commit_and_publish()` appends the trailer to a local variable only when the message is non-empty, immediately before `execute_git_commit()` |
| docs/pull-request-publication.md | docs | New "Co-author signature" note in section 5 documenting the injection moment per flow (TUI: at commit execution; `--no-edit`: at generation) |
| docs/pull-request-publication.pt_br.md | docs | Localized note (pt-BR) |
| docs/pull-request-publication.pt_pt.md | docs | Localized note (pt-PT) |
| docs/pull-request-publication.es_es.md | docs | Localized note (es-ES) |
| docs/pull-request-publication.fr_fr.md | docs | Localized note (fr-FR) |

### Impact
- **Functionality:** TUI users no longer see the trailer in the commit message edit screen; it is added to the final commit after confirmation. All other flows (console, hook, auto-commit, MCP) behave exactly as before.
- **Performance:** No impact — `append_coauthor_trailer()` is idempotent and runs once per commit; the MD5 cache is untouched.
- **Compatibility:** No breaking changes. Edge paths where `_pending_commit_msg` is empty (F3 without uncommitted changes, auto-commit declined) keep their previous behavior — no trailer-only commit is ever created.

### Next steps (if applicable)
- Note: `tests/test_external_linters.py` has 2 pre-existing failures on this machine (assertions expect English, environment is pt-BR) — unrelated to this change.
- The MCP tool `run_linter` of gitpr was reported as hanging during this session; validation was done with `py_compile` + `pytest` (244 passed) instead.
