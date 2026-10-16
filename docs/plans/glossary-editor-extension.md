# Glossary — GitPR Editor Extension

- **Editor extension** — the VS Code-compatible package (one VSIX, installed in VS Code and Cursor) that exposes GitPR commands inside the editor. It holds no business logic.
- **Thin client** — the rule that the editor extension only calls MCP tools and renders their results; every decision about diffs, prompts, findings and publishing lives in the Python server.
- **Server session** — one long-lived `gitpr-mcp` process bound to one workspace folder, started on the first command and restarted if it dies.
- **Workspace folder** — the folder whose root is the server session's working directory; in a multi-root workspace the user picks one per command.
- **Commit draft** — the AI-generated commit message placed in the Source Control input box for the user to review; the extension never commits.
- **Review document** — the Markdown result of a review, full review or PR description, opened as a preview; it never produces diagnostics.
- **Check diagnostics** — the findings of a check run shown in the Problems panel with file, line and severity; the only source of diagnostics.

- **PR draft** — the editable Markdown document produced by `Generate PR`: first line is the title, the rest is the body. Only a PR draft can be published from the editor.
- **Publish outcome** — the structured answer of a publish attempt: `success`, `needs_push`, `already_exists`, `auth_required` or `error`.
- **Required tools** — the MCP tool names the extension needs; a server missing any of them is too old and the extension asks for an upgrade instead of running.
