import * as vscode from "vscode";
import { SessionManager } from "./session_manager";
import { GitPrStatusBar } from "./ui/status_bar";
import { runCommitCommand } from "./commands/commit";
import { runReviewCommand } from "./commands/review";
import {
  runGeneratePrCommand,
  runPublishPrCommand,
} from "./commands/publish_pr";
import { runCheckCommand } from "./commands/check";

export const REGISTERED_COMMANDS: ReadonlyArray<string> = [
  "gitpr.commit",
  "gitpr.review",
  "gitpr.fullReview",
  "gitpr.reviewMentor",
  "gitpr.generatePr",
  "gitpr.generatePrExplain",
  "gitpr.publishPr",
  "gitpr.check",
];

let activeSessions: SessionManager | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const outputChannel = vscode.window.createOutputChannel("GitPR");
  const diagnostics = vscode.languages.createDiagnosticCollection("gitpr");
  const statusBar = new GitPrStatusBar();
  const sessions = new SessionManager(outputChannel);
  activeSessions = sessions;

  sessions.onStatusChange((connected) => {
    statusBar.setConnected(connected);
  });

  context.subscriptions.push(
    outputChannel,
    diagnostics,
    statusBar,
    sessions,
    vscode.commands.registerCommand("gitpr.commit", () =>
      runCommitCommand(sessions)
    ),
    vscode.commands.registerCommand("gitpr.review", () =>
      runReviewCommand(sessions, { full: false, mentor: false })
    ),
    vscode.commands.registerCommand("gitpr.fullReview", () =>
      runReviewCommand(sessions, { full: true, mentor: false })
    ),
    vscode.commands.registerCommand("gitpr.reviewMentor", () =>
      runReviewCommand(sessions, { full: false, mentor: true })
    ),
    vscode.commands.registerCommand("gitpr.generatePr", () =>
      runGeneratePrCommand(sessions, { explain: false })
    ),
    vscode.commands.registerCommand("gitpr.generatePrExplain", () =>
      runGeneratePrCommand(sessions, { explain: true })
    ),
    vscode.commands.registerCommand("gitpr.publishPr", () =>
      runPublishPrCommand(sessions)
    ),
    vscode.commands.registerCommand("gitpr.check", () =>
      runCheckCommand(sessions, diagnostics)
    )
  );
}

export async function deactivate(): Promise<void> {
  if (activeSessions) {
    await activeSessions.disposeAsync();
    activeSessions = undefined;
  }
}
