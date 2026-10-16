import * as vscode from "vscode";
import { GitPrMcpClient, MissingMcpToolsError } from "./mcp_client";
import { maskSensitiveText } from "./masking";

export class SessionManager implements vscode.Disposable {
  private readonly sessions = new Map<string, GitPrMcpClient>();
  private readonly statusListeners: Array<(connected: boolean) => void> = [];

  constructor(private readonly outputChannel: vscode.OutputChannel) {}

  public onStatusChange(listener: (connected: boolean) => void): void {
    this.statusListeners.push(listener);
  }

  public isAnyConnected(): boolean {
    for (const client of this.sessions.values()) {
      if (client.isConnected()) {
        return true;
      }
    }
    return false;
  }

  private notifyStatus(): void {
    const connected = this.isAnyConnected();
    for (const listener of this.statusListeners) {
      listener(connected);
    }
  }

  public log(message: string): void {
    this.outputChannel.appendLine(maskSensitiveText(message));
  }

  public getConfiguredProvider(folder?: vscode.WorkspaceFolder): string {
    const cfg = vscode.workspace.getConfiguration("gitpr", folder?.uri);
    return (cfg.get<string>("provider") ?? "").trim();
  }

  public getCheckUseAI(folder?: vscode.WorkspaceFolder): boolean {
    const cfg = vscode.workspace.getConfiguration("gitpr", folder?.uri);
    return Boolean(cfg.get<boolean>("check.useAI", false));
  }

  public async resolveWorkspaceFolder(): Promise<vscode.WorkspaceFolder | undefined> {
    const folders = vscode.workspace.workspaceFolders;
    if (!folders || folders.length === 0) {
      vscode.window.showWarningMessage(
        vscode.l10n.t("No workspace folder is open.")
      );
      return undefined;
    }
    if (folders.length === 1) {
      return folders[0];
    }

    const activeUri = vscode.window.activeTextEditor?.document.uri;
    if (activeUri) {
      const activeFolder = vscode.workspace.getWorkspaceFolder(activeUri);
      if (activeFolder) {
        return activeFolder;
      }
    }

    const picked = await vscode.window.showWorkspaceFolderPick({
      placeHolder: vscode.l10n.t("Select a workspace folder for GitPR"),
    });
    return picked;
  }

  public async getClientForFolder(
    folder: vscode.WorkspaceFolder
  ): Promise<GitPrMcpClient> {
    const rootPath = folder.uri.fsPath;
    let client = this.sessions.get(rootPath);
    if (!client) {
      const cfg = vscode.workspace.getConfiguration("gitpr", folder.uri);
      const mcpCommand = (cfg.get<string>("mcpCommand") ?? "gitpr-mcp").trim() || "gitpr-mcp";
      const mcpArgs = cfg.get<string[]>("mcpArgs") ?? [];

      client = new GitPrMcpClient(mcpCommand, mcpArgs, rootPath, {
        onStateChange: () => this.notifyStatus(),
        log: (line) => this.log(line),
      });
      this.sessions.set(rootPath, client);
    }

    try {
      await client.connect();
      this.notifyStatus();
      return client;
    } catch (err) {
      if (err instanceof MissingMcpToolsError) {
        vscode.window.showErrorMessage(
          vscode.l10n.t(
            "Your gitpr-cli version is outdated (missing MCP tools: {0}). Run 'pip install --upgrade gitpr-cli'.",
            err.missingTools.join(", ")
          )
        );
      }
      throw err;
    }
  }

  public async handleToolErrorMessage(rawMessage: string): Promise<void> {
    const msg = maskSensitiveText(rawMessage);
    this.log(`[Error] ${msg}`);
    const lower = msg.toLowerCase();
    if (
      lower.includes(".env") ||
      lower.includes("api key") ||
      lower.includes("install")
    ) {
      const actionLabel = vscode.l10n.t("Run gitpr --install");
      const choice = await vscode.window.showErrorMessage(msg, actionLabel);
      if (choice === actionLabel) {
        const terminal = vscode.window.createTerminal("GitPR Setup");
        terminal.show();
        terminal.sendText("gitpr --install");
      }
      return;
    }
    vscode.window.showErrorMessage(msg);
  }

  public async disposeAsync(): Promise<void> {
    const clients = Array.from(this.sessions.values());
    this.sessions.clear();
    await Promise.all(clients.map((c) => c.disconnect()));
    this.notifyStatus();
  }

  public dispose(): void {
    void this.disposeAsync();
  }
}
