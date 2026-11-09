## Completion Report — Document Interactive Commit (`-c`) Migration Note

### What was done
- Documented the behavioral breaking change of `gitpr -c` (`--commit`) introduced in v1.4.4 and guarded by TTY in v1.6.0 as an explicit Migration Note (`> [!WARNING]`) in Section 1 and supplemented in Section 3 across all 5 localized technical documentation files (`docs/commit-message-ia.*.md`).
- Explicitly clarified that before v1.4.4, `gitpr -c` was a silent/console-only command that did not stage files or execute `git commit`. Starting in v1.4.4, in interactive terminals (`may_ask == True`), it opens the 4-step TUI workflow and executes the commit upon user confirmation.
- Added explicit guidance for CI/CD pipelines, headless scripts, and git hooks: always use `gitpr --commit --hook <file-path>` to inject the commit message without interactive prompts, or note that in headless runs without a TTY, GitPR falls back to displaying the suggested message on console without creating a commit.
- Refined the `Commit flow` glossary definition in `CONTEXT.md` to reinforce that commit creation belongs strictly to an `Interactive run`.
- Maintained 100% translation and structural parity across English, Brazilian Portuguese, European Portuguese, Spanish, and French.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `CONTEXT.md` | docs | Refined `Commit flow` glossary definition |
| `docs/commit-message-ia.md` | docs | Added Migration Note callout in §1 and CI guidance in §3 (English) |
| `docs/commit-message-ia.pt_br.md` | docs | Added Migration Note callout in §1 and CI guidance in §3 (pt-BR) |
| `docs/commit-message-ia.pt_pt.md` | docs | Added Migration Note callout in §1 and CI guidance in §3 (pt-PT) |
| `docs/commit-message-ia.es_es.md` | docs | Added Migration Note callout in §1 and CI guidance in §3 (Spanish) |
| `docs/commit-message-ia.fr_fr.md` | docs | Added Migration Note callout in §1 and CI guidance in §3 (French) |
| `docs/survey/20261109_document_interactive_commit_migration_note_surveyfacts.md` | docs | Survey facts artifact from grill-with-docs |
| `docs/plans/develop_natan/20261109_document_interactive_commit_migration_note_plansfacts.md` | docs | Plan facts artifact from grill-with-docs |
| `docs/gemini/plans/develop_natan/2026-11-09_develop_natan_document_interactive_commit_migration_note.md` | docs | Implementation plan artifact per GEMINI.md |

### Impact
- **Functionality:** Users reviewing the `--commit` (`-c`) documentation are now immediately warned about the breaking behavioral difference between legacy silent console output (< v1.4.4) and the interactive TUI flow, preventing confusion in automated CI/CD scripts and git hooks.
- **Performance:** Zero runtime overhead (documentation and domain model only).
- **Compatibility:** Strictly backward-compatible; clarifies usage of `--hook <file>` and non-interactive console fallbacks.

### Next steps (if applicable)
- Consider referencing the migration note in upcoming release notes or `CHANGELOG.md` when cutting the next version tag.
