# MCP Tool Annotations — IDE Integration Hints

GitPR's MCP tools include **annotations** (`readOnlyHint`, `destructiveHint`,
`idempotentHint`) that help IDEs and AI agents understand tool behavior at a
glance. These annotations enable smarter UI decisions — like showing confirmation
dialogs for destructive operations or caching results of idempotent calls.

## ✨ What Are Tool Annotations?

In the Model Context Protocol, every tool can declare behavioral **hints** via a
`ToolAnnotations` object. These hints are not enforced by the server — they are
advisory metadata that the IDE/client can use to improve the user experience.

The standard annotation fields are:

| Field | Type | Meaning |
|-------|------|---------|
| `readOnlyHint` | `bool` | If `true`, the tool does **not** modify its environment |
| `destructiveHint` | `bool` | If `true`, the tool may perform destructive updates (only meaningful when `readOnlyHint` is `false`) |
| `idempotentHint` | `bool` | If `true`, calling the tool repeatedly with the same arguments has no additional side effects |

## 📋 GitPR Tool Annotations

### Read-Only Tools (no side effects)

These tools only read local state — safe to call anytime, no confirmation needed:

| Tool | `readOnlyHint` | `idempotentHint` |
|------|:---:|:---:|
| `get_git_context` | ✅ | ✅ |
| `analyze_diff` | ✅ | ✅ |
| `run_linter` | ✅ | ✅ |

### Tools with Side Effects (network calls)

These tools make network calls (AI APIs, git fetch) but do **not** write or
delete files. They are safe to invoke without a destructive-operation warning:

| Tool | `readOnlyHint` | `destructiveHint` | `idempotentHint` |
|------|:---:|:---:|:---:|
| `get_full_diff` | ❌ | ❌ | ❌ |
| `generate_commit_message` | ❌ | ❌ | ❌ |
| `review_code` | ❌ | ❌ | ❌ |
| `full_review` | ❌ | ❌ | ❌ |
| `generate_pr_description` | ❌ | ❌ | ❌ |
| `analyze_blame` | ❌ | ❌ | ❌ |
| `generate_issue` | ❌ | ❌ | ❌ |

> **Note:** `destructiveHint` is `false` for all GitPR tools because none of
> them modify, delete, or overwrite files. The "side effects" are limited to
> network API calls.

## 🚀 Benefits for IDE Integration

Annotations enable editors to:

- **VS Code / Cursor:** Show a shield icon for read-only tools, warn before
  running tools marked `destructiveHint=true`
- **Claude Desktop:** Organize tools into safe/unsafe groups in the UI
- **Claude Code:** Cache results of idempotent tools to avoid redundant calls
- **Zed:** Display tool safety level in the inline assistant

## 🔧 Implementation

Annotations are set via the `ToolAnnotations` class in `src/mcp_server.py`:

```python
from mcp.types import ToolAnnotations

@mcp.tool(
    description=__("Get the current git branch, repository name, and remote origin URL."),
    annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True),
)
def get_git_context() -> str:
    ...
```

Each tool's annotation is chosen based on its actual behavior:
- **Read-only + idempotent** for tools that only inspect local state
- **Non-read-only + non-destructive** for tools that make network calls
- No tool is marked `destructiveHint=true` since GitPR never writes files

## 📚 Related Documentation

- [MCP Integration](mcp-integration.md) — How to set up MCP for your editor
- [MCP Prompts](mcp-prompts.md) — Pre-built message templates for common flows

---
**Pro tip:** Tool annotations are hints, not guarantees. Configure API keys in
`~/.gitpr/.env` before using any tool. Run `gitpr --install` to set everything
up in one go.
