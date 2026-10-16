import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { maskSensitiveText } from "./masking";

export const REQUIRED_MCP_TOOLS: ReadonlyArray<string> = [
  "get_git_context",
  "generate_commit_message",
  "review_code",
  "full_review",
  "generate_pr_description",
  "run_check",
  "publish_pull_request",
];

export class MissingMcpToolsError extends Error {
  public readonly missingTools: string[];

  constructor(missingTools: string[]) {
    super(
      `Your gitpr-cli version is outdated (missing MCP tools: ${missingTools.join(", ")}). Run 'pip install --upgrade gitpr-cli'.`
    );
    this.name = "MissingMcpToolsError";
    this.missingTools = missingTools;
  }
}

export interface McpTransportFactory {
  create(command: string, args: string[], cwd: string): StdioClientTransport;
}

const defaultTransportFactory: McpTransportFactory = {
  create(command: string, args: string[], cwd: string): StdioClientTransport {
    const env: Record<string, string> = {};
    for (const [key, val] of Object.entries(process.env)) {
      if (typeof val === "string") {
        env[key] = val;
      }
    }
    return new StdioClientTransport({
      command,
      args,
      cwd,
      env,
    });
  },
};

export class GitPrMcpClient {
  private client: Client | null = null;
  private transport: StdioClientTransport | null = null;
  private connected = false;
  private connectingPromise: Promise<void> | null = null;
  private readonly onStateChange?: (connected: boolean) => void;
  private readonly log?: (line: string) => void;
  private readonly transportFactory: McpTransportFactory;

  constructor(
    private readonly command: string,
    private readonly args: string[],
    public readonly workspaceRoot: string,
    options?: {
      onStateChange?: (connected: boolean) => void;
      log?: (line: string) => void;
      transportFactory?: McpTransportFactory;
    }
  ) {
    this.onStateChange = options?.onStateChange;
    this.log = options?.log;
    this.transportFactory = options?.transportFactory ?? defaultTransportFactory;
  }

  public isConnected(): boolean {
    return this.connected;
  }

  private writeLog(msg: string): void {
    if (this.log) {
      this.log(maskSensitiveText(msg));
    }
  }

  private setConnected(state: boolean): void {
    if (this.connected !== state) {
      this.connected = state;
      if (this.onStateChange) {
        this.onStateChange(state);
      }
    }
  }

  public async connect(): Promise<void> {
    if (this.connected && this.client) {
      return;
    }
    if (this.connectingPromise) {
      return this.connectingPromise;
    }

    this.connectingPromise = (async () => {
      try {
        this.writeLog(
          `[MCP] Starting session: ${this.command} ${this.args.join(" ")} (cwd=${this.workspaceRoot})`
        );
        const transport = this.transportFactory.create(
          this.command,
          this.args,
          this.workspaceRoot
        );
        const client = new Client(
          { name: "gitpr-vscode", version: "0.1.0" },
          { capabilities: {} }
        );

        transport.onclose = () => {
          this.writeLog("[MCP] Transport closed.");
          this.client = null;
          this.transport = null;
          this.setConnected(false);
        };

        transport.onerror = (err: Error) => {
          this.writeLog(`[MCP] Transport error: ${err.message}`);
        };

        await client.connect(transport);
        const toolsResponse = await client.listTools();
        const availableNames = new Set(
          (toolsResponse.tools ?? []).map((t) => t.name)
        );
        const missing = REQUIRED_MCP_TOOLS.filter(
          (name) => !availableNames.has(name)
        );
        if (missing.length > 0) {
          await client.close().catch(() => undefined);
          this.setConnected(false);
          throw new MissingMcpToolsError(missing);
        }

        this.client = client;
        this.transport = transport;
        this.setConnected(true);
        this.writeLog("[MCP] Session connected and contract verified.");
      } catch (err) {
        this.client = null;
        this.transport = null;
        this.setConnected(false);
        throw err;
      } finally {
        this.connectingPromise = null;
      }
    })();

    return this.connectingPromise;
  }

  public async callTool<T = Record<string, unknown>>(
    toolName: string,
    args: Record<string, unknown> = {}
  ): Promise<T> {
    if (!this.connected || !this.client) {
      await this.connect();
    }
    if (!this.client) {
      throw new Error("MCP client is not connected.");
    }

    this.writeLog(`[MCP] -> callTool(${toolName})`);
    let response: unknown;
    try {
      response = await this.client.callTool({
        name: toolName,
        arguments: args,
      });
    } catch (err) {
      // Reconnect once if the stdio process died mid-session
      this.writeLog(
        `[MCP] callTool(${toolName}) failed (${(err as Error).message}); attempting reconnect...`
      );
      this.client = null;
      this.transport = null;
      this.setConnected(false);
      await this.connect();
      response = await this.client!.callTool({
        name: toolName,
        arguments: args,
      });
    }

    return this.parseToolPayload<T>(response);
  }

  private parseToolPayload<T>(response: unknown): T {
    const resObj = response as {
      content?: Array<{ type?: string; text?: string }>;
      isError?: boolean;
    };
    const firstText = resObj?.content?.find((c) => typeof c.text === "string")?.text ?? "";
    if (!firstText) {
      return {} as T;
    }
    try {
      return JSON.parse(firstText) as T;
    } catch {
      return { status: resObj?.isError ? "error" : "success", raw: firstText } as unknown as T;
    }
  }

  public async disconnect(): Promise<void> {
    const current = this.client;
    this.client = null;
    this.transport = null;
    this.setConnected(false);
    if (current) {
      await current.close().catch(() => undefined);
    }
  }
}
