import * as vscode from "vscode";
import { SessionManager } from "../session_manager";
import { maskSensitiveText } from "../masking";

interface ReviewToolResponse {
  status?: string;
  review?: string;
  message?: string;
}

export async function runReviewCommand(
  sessions: SessionManager,
  options: { full: boolean; mentor: boolean }
): Promise<void> {
  const folder = await sessions.resolveWorkspaceFolder();
  if (!folder) {
    return;
  }

  const progressTitle = options.full
    ? vscode.l10n.t("Running GitPR full branch review...")
    : vscode.l10n.t("Running GitPR code review...");

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: progressTitle,
      cancellable: false,
    },
    async () => {
      try {
        const client = await sessions.getClientForFolder(folder);
        const provider = sessions.getConfiguredProvider(folder);
        const toolName = options.full ? "full_review" : "review_code";
        const args: Record<string, unknown> = {
          mentor: Boolean(options.mentor),
        };
        if (provider) {
          args.provider = provider;
        }

        const result = await client.callTool<ReviewToolResponse>(
          toolName,
          args
        );

        if (result.status === "success" && result.review) {
          const doc = await vscode.workspace.openTextDocument({
            language: "markdown",
            content: maskSensitiveText(result.review),
          });
          await vscode.window.showTextDocument(doc, { preview: false });
          await vscode.commands.executeCommand("markdown.showPreviewToSide", doc.uri);
          return;
        }

        if (result.status === "no_changes") {
          vscode.window.showInformationMessage(
            maskSensitiveText(result.message ?? "No diff to review.")
          );
          return;
        }

        await sessions.handleToolErrorMessage(
          result.message ?? "Failed to run code review."
        );
      } catch (err) {
        await sessions.handleToolErrorMessage((err as Error).message);
      }
    }
  );
}
