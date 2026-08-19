# 🚀 Pull Request Suggestion

**Recommended Commit Message:**
```text
feat: add external linter bridge and setup wizard
```

---

## 🎯 Summary

This change introduces support for integrating external linters (ESLint, PHPCS, Stylelint, etc.) into GitPR's local linter process. It adds a configuration wizard (`--linter-setup`) to easily set up these tools, runs them on changed lines of code, parses their Checkstyle XML output, and presents violations through a terminal UI and a generated Markdown report. The goal is to leverage mature linters and provide a richer local validation experience alongside GitPR's existing custom rules.

## 🛠️ Technical Changes

- Load external linter configurations from local `.gitpr.linter.yml` and global plugin files.
- Execute external linter commands via subprocess and parse Checkstyle XML output.
- Cross-reference linter findings with lines added in the current diff to ignore pre-existing issues.
- Introduced interactive wizard (`--linter-setup`) with remote presets and local caching.
- Generate a Markdown linter report (configurable output filename) after linting.
- Added Textual-based TUI (`LinterApp`) for displaying critical errors and warnings.
- Added translations for new UI strings in Spanish, French, and Portuguese.
- Bumped language and scripts version numbers (v0.0.13→v0.0.15, v0.0.2→v0.0.3).
- Added unit tests for XML parsing, external command execution, diff filtering, and report generation.

## ⚠️ Impact/Warnings

- External linters must be installed in the project (e.g., `composer require --dev squizlabs/php_codesniffer` or `npm install --save-dev eslint`) as instructed by the wizard.
- A new configuration file `.gitpr.linter.yml` may be created; the wizard handles this automatically.
- Linter report output file name can now be customized via `OUTPUT_FILE_NAME_LINTER` environment variable.
- Running external linters adds overhead to the commit/review process, especially on large codebases.
- TUI requires the Textual library, which is already a dependency of GitPR.

close #119