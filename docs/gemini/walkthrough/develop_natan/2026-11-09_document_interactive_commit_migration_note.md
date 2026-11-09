# Walkthrough — Document Interactive Commit (`-c`) Migration Note

**Date:** 2026-11-09  
**Branch:** `develop_natan`  
**Task:** `document_interactive_commit_migration_note`  

## Changes Made

### 1. Domain Modeling (`CONTEXT.md`)
Refined the canonical definition of `Commit flow` to explicitly note that commit execution is exclusive to an **Interactive run**:
```markdown
**Commit flow**:
The interactive sequence triggered by `gitpr -c` (or during PR publication) in an
interactive run that coordinates unstaged file selection, AI commit message
generation, review/editing in a modal, and commit execution with animated
progress. Non-interactive runs fall back to displaying the suggested message or
injecting it via hook mode without executing a commit.
_Avoid_: commit wizard, auto-commit script, commit generator
```

### 2. Technical Documentation across 5 Languages
Added an explicit Migration Note (`> [!WARNING]`) in Section 1 and CI guidance in Section 3 across all 5 languages:
- `docs/commit-message-ia.md` (EN)
- `docs/commit-message-ia.pt_br.md` (PT-BR)
- `docs/commit-message-ia.pt_pt.md` (PT-PT)
- `docs/commit-message-ia.es_es.md` (ES-ES)
- `docs/commit-message-ia.fr_fr.md` (FR-FR)

#### Key Information Documented:
1. **Behavioral shift (< v1.4.4 vs. >= v1.4.4):** Legacy `-c` was a silent console utility printing the commit message without touching git staging or committing. Now, in an interactive terminal, `gitpr -c` opens the 4-step Textual TUI (`CommitApp`) and creates the commit.
2. **Git hooks & File injection:** In CI, automated git hooks, or shell scripts requiring message injection, always use `gitpr --commit --hook <file>`.
3. **Headless & Non-TTY runs:** In environments without a TTY (`may_ask == False`), GitPR does not open modals and falls back to console output without committing.

---

## Validation Results

- Executed `pytest tests/test_doc_links.py -v`: 11 passed in 6.00s.
- Verified exact 5-language parity and markdown formatting.
