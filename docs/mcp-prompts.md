# MCP Prompts — Message Templates for Common Flows

GitPR's MCP server exposes **prompts** (pre-defined message templates) that help
you compose common GitPR tasks in your editor's AI chat. Instead of typing full
instructions each time, select a prompt and let the AI fill in the details.

## ✨ What Are MCP Prompts?

In the Model Context Protocol, **prompts** are server-defined message templates.
Unlike tools (which execute code automatically), prompts are **starter messages**
that the user can select from a list in their editor. The AI then uses the
template to invoke the appropriate GitPR tools to fulfill the request.

## 📋 Available Prompts

| Prompt | What it does | Tools used |
|--------|-------------|------------|
| **Review PR** | Full code review of all changes in the current branch | `full_review` |
| **Generate Commit Message** | Generate a Conventional Commits message from uncommitted changes | `generate_commit_message` |
| **Create PR Description** | Generate a title and body for a Pull Request | `generate_pr_description` |
| **Run Code Linter** | Check uncommitted changes against `.gitpr.linter.yml` rules | `run_linter` |
| **Create Issue from Diff** | Generate a structured issue from current changes | `generate_issue` |
| **Trace Code Origin** | Investigate the history of a specific code region | `analyze_blame`, `get_git_context` |
| **Explore Project Context** | Get current branch info and list available skills/templates | `get_git_context`, `skill://list` |

## 🚀 How to Use

Once the MCP server is configured in your editor, prompts appear in the prompt
list alongside any other MCP server prompts. The exact location varies by editor:

- **VS Code / Cursor:** In the AI chat panel, look for the "Prompts" selector
- **Claude Desktop:** Prompts appear as selectable options in the chat interface
- **Claude Code:** Use the prompts list in the chat panel
- **Zed:** Available in the inline assistant prompt list

Select a prompt and the AI will automatically invoke the appropriate GitPR tools
to fulfill the request.

## 🔧 How It Works

Each prompt is defined as a function decorated with `@mcp.prompt()` in
`src/mcp_server.py`. The prompt content is loaded from **template files** stored
in the `templates/` directory:

```
templates/gitpr.prompt.review.md       (English)
templates/gitpr.prompt.review.pt_br.md  (Brazilian Portuguese)
templates/gitpr.prompt.review.pt_pt.md  (European Portuguese)
templates/gitpr.prompt.review.es_es.md  (Spanish)
templates/gitpr.prompt.review.fr_fr.md  (French)
```

This template-based design means prompt messages can be updated and translated
independently of the Python code. The MCP server loads the appropriate language
variant based on the user's `GITPR_LANG` setting, falling back to English.

Example — the "Review PR" prompt template (`gitpr.prompt.review.md`):

```
Please review all changes in my current branch by running a full code
review against origin/main. Also run the static linter to check for
code quality issues. Combine the results into a single comprehensive
review report with: 1) summary of changes, 2) critical issues found,
3) linter violations, and 4) suggested improvements.
```

The AI agent receiving this message will call `full_review`, `run_linter`,
and compose a comprehensive review response based on the results.

### Prompt Resources

Prompt templates are also exposed as MCP **resources** under the `prompt://`
URI scheme, so AI agents can read the raw template content:

| URI | Content |
|-----|---------|
| `prompt://list` | JSON list of all available prompt URIs |
| `prompt://review` | Review PR prompt template |
| `prompt://commit` | Commit message prompt template |
| `prompt://pr` | PR description prompt template |
| `prompt://linter` | Linter prompt template |
| `prompt://issue` | Issue prompt template |
| `prompt://blame` | Code origin prompt template |
| `prompt://explore` | Project context prompt template |

## 📚 Related Documentation

- [MCP Integration](mcp-integration.md) — How to set up MCP for your editor
- [AI Code Review](code-review-ia.md) — Guide to code review modes
- [AI Commit Messages](commit-message-ia.md) — Conventional Commits guide
- [PR Description Mode](pr-descricao-padrao.md) — PR generation flow

---
**Pro tip:** Combine prompts with skills (`.gitpr.*.md` files) to customize
the AI's behavior for your team's conventions. Run `gitpr --install` to set
everything up in one go.
