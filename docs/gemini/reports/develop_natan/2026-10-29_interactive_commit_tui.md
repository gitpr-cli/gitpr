## Completion Report — Interactive Commit TUI Flow (`gitpr -c`, `--commit`)

### What was done
- Transformed the `gitpr -c` / `gitpr --commit` command from a terminal-only suggestion printer into a complete, interactive Textual TUI workflow (`CommitApp`).
- Integrated the Stage Selector modal (`StageFilesScreen`) to detect files outside stage, allowing selective staging of changes.
- Added `get_git_staged_diff()` to `src/core.py` to ensure AI commit message generation focuses strictly on staged changes (`git diff --cached`).
- Implemented the full commit lifecycle:
  1. Unstaged file selection (`StageFilesScreen`) with selective `git add`.
  2. Background AI generation with status animation.
  3. Commit message review and editing modal (`CommitMessageScreen`).
  4. Animated commit execution modal (`CommitProgressScreen`) that runs `execute_git_commit()`, logs the commit SHA/result, and presents a Close button.
- Preserved strictly non-interactive behavior when executed via Git hook (`--hook`).
- Updated `CONTEXT.md` with the domain terms `Stage selector` and `Commit flow`.
- Created comprehensive unit and headless integration test suite in `tests/test_commit_app.py` (13 tests, all passing).
- Updated the technical documentation `commit-message-ia.md` in all 5 supported languages (EN, PT-BR, PT-PT, ES-ES, FR-FR) detailing the 4-step interactive flow, configuration options, and hook behavior.

### Changed files
| File | Change type | Description |
|------|-------------|-------------|
| `src/core.py` | feat | Added `get_git_staged_diff()` to query cached diff with `SMART_EXCLUDES`. |
| `src/ui/commit_app.py` | feat | Created `CommitApp` orchestrating the Stage Selector, message review, and animated commit execution. |
| `src/main.py` | feat | Routed `gitpr -c` interactive mode to `CommitApp`, while keeping `--hook` non-interactive. |
| `CONTEXT.md` | docs | Added canonical domain terms `Stage selector` and `Commit flow`. |
| `docs/commit-message-ia.md` | docs | Updated English technical documentation with interactive TUI flow. |
| `docs/commit-message-ia.pt_br.md` | docs | Updated Portuguese (BR) technical documentation with interactive TUI flow. |
| `docs/commit-message-ia.pt_pt.md` | docs | Updated Portuguese (PT) technical documentation with interactive TUI flow. |
| `docs/commit-message-ia.es_es.md` | docs | Updated Spanish technical documentation with interactive TUI flow. |
| `docs/commit-message-ia.fr_fr.md` | docs | Updated French technical documentation with interactive TUI flow. |
| `tests/test_commit_app.py` | test | Added 13 unit and headless integration tests covering all states, transitions, and callbacks. |

### Impact
- **Functionality:** `gitpr -c` now provides an interactive UI to select unstaged files, generate commit message based on staged diff, review/edit the message, and execute `git commit` with animated feedback.
- **Performance:** Highly responsive Textual TUI with background threads for AI calls and git commit execution, keeping the animated bar smooth.
- **Compatibility:** 100% backward compatible. `--hook` continues to inject commit message suggestions without launching any TUI.

### Next steps (if applicable)
- Continue monitoring user feedback during interactive commits across repositories with large staged diffs.
