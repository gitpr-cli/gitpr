import * as vscode from "vscode";
import { SessionManager } from "../session_manager";
import { maskSensitiveText } from "../masking";

interface CommitToolResponse {
  status?: string;
  commit_message?: string;
  message?: string;
}

interface GitExtensionApi {
  getAPI(version: number): {
    repositories: Array<{
      rootUri: vscode.Uri;
      inputBox: { value: string };
    }>;
  };
}

export function tryPopulateGitScmInputBox(
  workspaceRoot: string,
  commitMessage: string
): boolean {
  try {
    const gitExt = vscode.extensions.getExtension<GitExtensionApi>("vscode.git");
    if (!gitExt || !gitExt.isActive) {
      return false;
    }
    const api = gitExt.exports?.getAPI?.(1);
    if (!api || !Array.isArray(api.repositories) || api.repositories.length === 0) {
      return false;
    }
    const matchingRepo =
      api.repositories.find(
        (r) =>
          r.rootUri.fsPath.toLowerCase() === workspaceRoot.toLowerCase()
      ) ?? api.repositories[0];

    if (matchingRepo?.inputBox) {
      matchingRepo.inputBox.value = commitMessage;
      return true;
    }
  } catch {
    // Fallback to clipboard notification
  }
  return false;
}

export async function runCommitCommand(
  sessions: SessionManager
): Promise<void> {
  const folder = await sessions.resolveWorkspaceFolder();
  if (!folder) {
    return;
  }

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: vscode.l10n.t("Generating commit message with GitPR..."),
      cancellable: false,
    },
    async () => {
      try {
        const client = await sessions.getClientForFolder(folder);
        const provider = sessions.getConfiguredProvider(folder);
        const args: Record<string, unknown> = {};
        if (provider) {
          args.provider = provider;
        }

        const result = await client.callTool<CommitToolResponse>(
          "generate_commit_message",
          args
        );

        if (result.status === "success" && result.commit_message) {
          const msg = result.commit_message;
          const populated = tryPopulateGitScmInputBox(folder.uri.fsPath, msg);
          if (populated) {
            vscode.window.showInformationMessage(
              vscode.l10n.t(
                "Commit message populated in Source Control input box."
              )
            );
          } else {
            const copyLabel = vscode.l10n.t("Copy");
            const choice = await vscode.window.showInformationMessage(
              vscode.l10n.t("Commit message generated. Copy to clipboard?"),
              copyLabel
            );
            if (choice === copyLabel) {
              await vscode.env.clipboard.writeText(msg);
            }
          }
          return;
        }

        if (result.status === "no_changes") {
          vscode.window.showInformationMessage(
            maskSensitiveText(result.message ?? "No diff to analyze.")
          );
          return;
        }

        await sessions.handleToolErrorMessage(
          result.message ?? "Failed to generate commit message."
        );
      } catch (err) {
        await sessions.handleToolErrorMessage((err as Error).message);
      }
    }
  );
}
