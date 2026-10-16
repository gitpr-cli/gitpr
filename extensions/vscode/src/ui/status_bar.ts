import * as vscode from "vscode";

export class GitPrStatusBar implements vscode.Disposable {
  private readonly connectionItem: vscode.StatusBarItem;
  private readonly commitItem: vscode.StatusBarItem;
  private readonly reviewItem: vscode.StatusBarItem;
  private readonly prItem: vscode.StatusBarItem;
  private readonly checkItem: vscode.StatusBarItem;

  constructor() {
    this.connectionItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      105
    );
    this.commitItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      104
    );
    this.reviewItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      103
    );
    this.prItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      102
    );
    this.checkItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      101
    );

    this.setConnected(false);

    this.commitItem.text = "$(git-commit) Commit";
    this.commitItem.tooltip = "GitPR: Commit (Generate Conventional Commit)";
    this.commitItem.command = "gitpr.commit";
    this.commitItem.show();

    this.reviewItem.text = "$(eye) Review";
    this.reviewItem.tooltip = "GitPR: Review Local Diff";
    this.reviewItem.command = "gitpr.review";
    this.reviewItem.show();

    this.prItem.text = "$(git-pull-request) PR";
    this.prItem.tooltip = "GitPR: Generate Pull Request Draft";
    this.prItem.command = "gitpr.generatePr";
    this.prItem.show();

    this.checkItem.text = "$(shield) Check";
    this.checkItem.tooltip = "GitPR: Run Unified Check Diagnostics";
    this.checkItem.command = "gitpr.check";
    this.checkItem.show();
  }

  public setConnected(connected: boolean): void {
    if (connected) {
      this.connectionItem.text = "$(plug) GitPR MCP: Connected";
      this.connectionItem.tooltip = "GitPR MCP server is active";
    } else {
      this.connectionItem.text = "$(debug-disconnect) GitPR MCP: Idle";
      this.connectionItem.tooltip = "GitPR MCP server will connect on first command";
    }
    this.connectionItem.show();
  }

  public dispose(): void {
    this.connectionItem.dispose();
    this.commitItem.dispose();
    this.reviewItem.dispose();
    this.prItem.dispose();
    this.checkItem.dispose();
  }
}
