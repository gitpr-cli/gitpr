import * as assert from "assert";
import * as fs from "fs";
import * as path from "path";
import {
  GitPrMcpClient,
  MissingMcpToolsError,
  REQUIRED_MCP_TOOLS,
} from "../mcp_client";
import { maskSensitiveText } from "../masking";
import {
  formatPrDraftDocument,
  normalizeCheckFindings,
  parsePrDraftDocument,
} from "../draft_and_diagnostics";

describe("GitPR VS Code Extension — MCP Client & Thin Client Contract", () => {
  it("defines the 7 required MCP tools in REQUIRED_MCP_TOOLS", () => {
    assert.deepStrictEqual(REQUIRED_MCP_TOOLS, [
      "get_git_context",
      "generate_commit_message",
      "review_code",
      "full_review",
      "generate_pr_description",
      "run_check",
      "publish_pull_request",
    ]);
  });

  it("masks secrets across common token formats", () => {
    const raw =
      "Error with ghp_1234567890abcdefghijklmnopqrstuvwxyz and glpat-abcdefghijklmnopqrstuv and Bearer abcdefghijklmnopqrstuvwxyz12345";
    const masked = maskSensitiveText(raw);
    assert.strictEqual(
      masked.includes("ghp_1234567890abcdefghijklmnopqrstuvwxyz"),
      false
    );
    assert.strictEqual(masked.includes("glpat-abcdefghijklmnopqrstuv"), false);
    assert.strictEqual(
      masked.includes("abcdefghijklmnopqrstuvwxyz12345"),
      false
    );
    assert.strictEqual(masked.includes("***"), true);
  });

  it("formats and parses PR draft Markdown documents round-trip", () => {
    const doc = formatPrDraftDocument(
      "feat: add thin client",
      "## Summary\nImplemented MCP thin client."
    );
    const parsed = parsePrDraftDocument(doc);
    assert.strictEqual(parsed.title, "feat: add thin client");
    assert.strictEqual(parsed.body, "## Summary\nImplemented MCP thin client.");
  });

  it("normalizes check findings into 0-based diagnostics and filters ignored/resolved", () => {
    const items = normalizeCheckFindings([
      {
        rule_id: "no-secret",
        file_path: "src/a.py",
        line_start: 10,
        line_end: 12,
        severity: "error",
        source: "linter",
        message: "Leaked ghp_1234567890abcdefghijklmnopqrstuvwxyz",
        suggestion: "Use env var",
        baseline_status: "new",
      },
      {
        rule_id: "ignored-rule",
        file_path: "src/b.py",
        line_start: 3,
        severity: "warning",
        message: "Ignored",
        baseline_status: "ignored",
      },
    ]);
    assert.strictEqual(items.length, 1);
    assert.strictEqual(items[0].filePath, "src/a.py");
    assert.strictEqual(items[0].startLineZeroBased, 9);
    assert.strictEqual(items[0].endLineZeroBased, 11);
    assert.strictEqual(items[0].severity, "error");
    assert.strictEqual(
      items[0].message.includes("ghp_1234567890abcdefghijklmnopqrstuvwxyz"),
      false
    );
  });

  it("registers all 8 commands and 4 settings in package.json without configPath", () => {
    const pkgPath = path.resolve(__dirname, "../../package.json");
    const pkg = JSON.parse(fs.readFileSync(pkgPath, "utf-8"));
    const commands = (pkg.contributes?.commands ?? []).map(
      (c: { command: string }) => c.command
    );
    assert.deepStrictEqual(commands, [
      "gitpr.commit",
      "gitpr.review",
      "gitpr.fullReview",
      "gitpr.reviewMentor",
      "gitpr.generatePr",
      "gitpr.generatePrExplain",
      "gitpr.publishPr",
      "gitpr.check",
    ]);

    const props = Object.keys(pkg.contributes?.configuration?.properties ?? {});
    assert.deepStrictEqual(props, [
      "gitpr.mcpCommand",
      "gitpr.mcpArgs",
      "gitpr.provider",
      "gitpr.check.useAI",
    ]);
    assert.strictEqual(props.includes("gitpr.configPath"), false);
  });

  it("connects to real Python gitpr-mcp over stdio, verifies contract, and calls get_git_context", async function () {
    this.timeout(20000);
    const repoRoot = path.resolve(__dirname, "../../../..");
    const pythonCmd = process.env.PYTHON || "python";
    const client = new GitPrMcpClient(
      pythonCmd,
      ["-m", "src.mcp_server"],
      repoRoot
    );

    try {
      await client.connect();
      assert.strictEqual(client.isConnected(), true);

      const ctx = await client.callTool<{ branch?: string; repository?: string }>(
        "get_git_context",
        {}
      );
      assert.ok(ctx.branch, "Expected branch from get_git_context");
      assert.ok(ctx.repository, "Expected repository from get_git_context");
    } finally {
      await client.disconnect();
      assert.strictEqual(client.isConnected(), false);
    }
  });

  it("constructs MissingMcpToolsError with clear upgrade instructions", () => {
    const err = new MissingMcpToolsError(["run_check", "publish_pull_request"]);
    assert.ok(err.message.includes("pip install --upgrade gitpr-cli"));
    assert.deepStrictEqual(err.missingTools, [
      "run_check",
      "publish_pull_request",
    ]);
  });
});
