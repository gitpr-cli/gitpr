# 🚀 Sugestão de Pull Request

**Commit Message Recomendada:**
```text
docs: add memory index and project knowledge files
```

---

## 🎯 Summary

Establishes a structured project knowledge base (memory index) to document design patterns, architectural decisions, and fixes discovered across 36 reports. This centralizes tribal knowledge for future development and onboarding.

## 🛠️ Technical Changes

- Add `.claude/memory/MEMORY.md` as a generated index with categorized links (Project, Reference, Feedback).
- Add 16 individual memory files:
  - **Project patterns:** help-contextual, cache-filter-repo-branch, ui-subpackage-packaging, spinner-config, skill-folder-auto-migration, smart-excludes-remote-control, version-marker, mcp-server-isolation, spinner-adaptive-speed, metrics-telemetry-architecture, github-token-reauth-flow, metrics-cache-enrichment, dashboard-repo-scope, ai-call-duration-tracking.
  - **Reference:** pre-save-debug-flag.
  - **Feedback:** windows-utf8-encoding-fix.
- Each memory file contains structured metadata (type, source, date, branch) and sections for "Why" and "How to apply".

## ⚠️ Impact/Warnings

- No production code changes; purely documentation.
- No database migrations, environment variables, or dependency changes.
- The memory files are for internal reference and do not affect runtime behavior.

close #78