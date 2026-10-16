import * as vscode from "vscode";
import { SessionManager } from "../session_manager";
import { maskSensitiveText } from "../masking";
import {
  formatPrDraftDocument,
  parsePrDraftDocument,
  ParsedPrDraft,
} from "../draft_and_diagnostics";

export { formatPrDraftDocument, parsePrDraftDocument, ParsedPrDraft };

interface GeneratePrResponse {
  status?: string;
  commit_message?: string;
  pr_description?: string;
  message?: string;
}

interface GitContextResponse {
  branch?: string;
  repository?: string;
}

export interface PublishPrResponse {
  status?: "success" | "needs_push" | "already_exists" | "auth_required" | "error";
  url?: string;
  number?: number;
  provider?: string;
  source_branch?: string;
  target_branch?: string;
  message?: string;
}

export async function runGeneratePrCommand(
  sessions: SessionManager,
  options: { explain: boolean }
): Promise<void> {
  const folder = await sessions.resolveWorkspaceFolder();
  if (!folder) {
    return;
  }

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: vscode.l10n.t("Generating Pull Request draft..."),
      cancellable: false,
    },
    async () => {
      try {
        const client = await sessions.getClientForFolder(folder);
        const provider = sessions.getConfiguredProvider(folder);
        const args: Record<string, unknown> = {
          explain: Boolean(options.explain),
        };
        if (provider) {
          args.provider = provider;
        }

        const result = await client.callTool<GeneratePrResponse>(
          "generate_pr_description",
          args
        );

        if (result.status === "success") {
          const draftContent = formatPrDraftDocument(
            result.commit_message ?? "",
            result.pr_description ?? ""
          );
          const doc = await vscode.workspace.openTextDocument({
            language: "markdown",
            content: maskSensitiveText(draftContent),
          });
          await vscode.window.showTextDocument(doc, { preview: false });

          const publishLabel = vscode.l10n.t("Publish");
          const choice = await vscode.window.showInformationMessage(
            vscode.l10n.t(
              "PR draft opened. Review or edit the first line (title) and body, then click 'Publish PR'."
            ),
            publishLabel
          );
          if (choice === publishLabel) {
            await runPublishPrCommand(sessions);
          }
          return;
        }

        if (result.status === "no_changes") {
          vscode.window.showInformationMessage(
            maskSensitiveText(
              result.message ?? "No changes against the base branch."
            )
          );
          return;
        }

        await sessions.handleToolErrorMessage(
          result.message ?? "Failed to generate Pull Request draft."
        );
      } catch (err) {
        await sessions.handleToolErrorMessage((err as Error).message);
      }
    }
  );
}

export async function runPublishPrCommand(
  sessions: SessionManager
): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== "markdown") {
    vscode.window.showWarningMessage(
      vscode.l10n.t(
        "Open a GitPR PR draft Markdown document before publishing."
      )
    );
    return;
  }

  const parsed = parsePrDraftDocument(editor.document.getText());
  if (!parsed.title || !parsed.body) {
    vscode.window.showWarningMessage(
      vscode.l10n.t(
        "Open a GitPR PR draft Markdown document before publishing."
      )
    );
    return;
  }

  const folder = await sessions.resolveWorkspaceFolder();
  if (!folder) {
    return;
  }

  try {
    const client = await sessions.getClientForFolder(folder);
    const gitCtx = await client
      .callTool<GitContextResponse>("get_git_context", {})
      .catch(() => ({ branch: "current", repository: "" }));

    const headBranch = gitCtx.branch ?? "HEAD";
    const baseBranch = "main";

    const publishBtn = vscode.l10n.t("Publish");
    const draftBtn = vscode.l10n.t("Publish as Draft");
    const confirm = await vscode.window.showInformationMessage(
      vscode.l10n.t(
        "Publish Pull Request '{0}' ({1} -> {2})?",
        parsed.title,
        headBranch,
        baseBranch
      ),
      { modal: true },
      publishBtn,
      draftBtn
    );
    if (!confirm) {
      return;
    }

    const isDraft = confirm === draftBtn;
    await executePublishCall(sessions, folder, parsed.title, parsed.body, isDraft);
  } catch (err) {
    await sessions.handleToolErrorMessage((err as Error).message);
  }
}

async function executePublishCall(
  sessions: SessionManager,
  folder: vscode.WorkspaceFolder,
  title: string,
  body: string,
  draft: boolean
): Promise<void> {
  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: vscode.l10n.t("Publishing Pull Request..."),
      cancellable: false,
    },
    async () => {
      const client = await sessions.getClientForFolder(folder);
      const outcome = await client.callTool<PublishPrResponse>(
        "publish_pull_request",
        {
          title,
          body,
          draft,
        }
      );

      if (outcome.status === "success" && outcome.url) {
        const openLabel = vscode.l10n.t("Open in Browser");
        const choice = await vscode.window.showInformationMessage(
          vscode.l10n.t("Pull Request created: {0}", outcome.url),
          openLabel
        );
        if (choice === openLabel) {
          await vscode.env.openExternal(vscode.Uri.parse(outcome.url));
        }
        return;
      }

      if (outcome.status === "already_exists") {
        const openLabel = vscode.l10n.t("Open in Browser");
        const url = outcome.url ?? "";
        const choice = await vscode.window.showInformationMessage(
          vscode.l10n.t(
            "An open Pull Request already exists: {0}",
            url || maskSensitiveText(outcome.message)
          ),
          ...(url ? [openLabel] : [])
        );
        if (choice === openLabel && url) {
          await vscode.env.openExternal(vscode.Uri.parse(url));
        }
        return;
      }

      if (outcome.status === "needs_push") {
        const pushLabel = vscode.l10n.t("Push & Publish");
        const branch = outcome.source_branch ?? "HEAD";
        const choice = await vscode.window.showWarningMessage(
          vscode.l10n.t(
            "Branch '{0}' needs to be pushed before publishing.",
            branch
          ),
          pushLabel
        );
        if (choice === pushLabel) {
          await vscode.commands.executeCommand("git.push");
          await executePublishCall(sessions, folder, title, body, draft);
        }
        return;
      }

      if (outcome.status === "auth_required") {
        const termLabel = vscode.l10n.t("Open Terminal");
        const choice = await vscode.window.showErrorMessage(
          vscode.l10n.t(
            "Authentication required on {0}. Run 'gitpr' in a terminal to configure your token.",
            outcome.provider ?? "SCM"
          ),
          termLabel
        );
        if (choice === termLabel) {
          const terminal = vscode.window.createTerminal("GitPR Auth");
          terminal.show();
          terminal.sendText("gitpr");
        }
        return;
      }

      await sessions.handleToolErrorMessage(
        outcome.message ?? "Failed to publish Pull Request."
      );
    }
  );
}
