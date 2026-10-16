import * as path from "path";
import * as vscode from "vscode";
import { SessionManager } from "../session_manager";
import {
  CheckEnvelopeResponse,
  CheckFindingPayload,
  normalizeCheckFindings,
} from "../draft_and_diagnostics";

export { CheckEnvelopeResponse, CheckFindingPayload };

export function mapSeverityToVscode(
  severity: string
): vscode.DiagnosticSeverity {
  switch (severity.toLowerCase()) {
    case "error":
      return vscode.DiagnosticSeverity.Error;
    case "warning":
      return vscode.DiagnosticSeverity.Warning;
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

export function applyCheckFindingsToDiagnostics(
  workspaceRoot: string,
  findings: CheckFindingPayload[],
  collection: vscode.DiagnosticCollection
): number {
  collection.clear();

  const normalized = normalizeCheckFindings(findings);
  const grouped = new Map<string, vscode.Diagnostic[]>();

  for (const item of normalized) {
    const absPath = path.isAbsolute(item.filePath)
      ? item.filePath
      : path.join(workspaceRoot, item.filePath);

    const range = new vscode.Range(
      item.startLineZeroBased,
      0,
      item.endLineZeroBased,
      200
    );
    const diag = new vscode.Diagnostic(
      range,
      item.message,
      mapSeverityToVscode(item.severity)
    );
    diag.source = item.source;
    diag.code = item.code;

    const list = grouped.get(absPath) ?? [];
    list.push(diag);
    grouped.set(absPath, list);
  }

  for (const [filePath, diags] of grouped.entries()) {
    collection.set(vscode.Uri.file(filePath), diags);
  }

  return normalized.length;
}

export async function runCheckCommand(
  sessions: SessionManager,
  diagnostics: vscode.DiagnosticCollection
): Promise<void> {
  const folder = await sessions.resolveWorkspaceFolder();
  if (!folder) {
    return;
  }

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: vscode.l10n.t("Running GitPR Check..."),
      cancellable: false,
    },
    async () => {
      try {
        const client = await sessions.getClientForFolder(folder);
        const useAI = sessions.getCheckUseAI(folder);
        const result = await client.callTool<CheckEnvelopeResponse>(
          "run_check",
          {
            no_ia: !useAI,
          }
        );

        if (result.status === "error" && result.exit_code === 2 && !result.findings?.length) {
          await sessions.handleToolErrorMessage(
            result.message ?? "GitPR Check failed with an internal error."
          );
          return;
        }

        const findings = result.findings ?? [];
        const count = applyCheckFindingsToDiagnostics(
          folder.uri.fsPath,
          findings,
          diagnostics
        );

        const openProblemsLabel = "Problems";
        const choice = await vscode.window.showInformationMessage(
          vscode.l10n.t(
            "GitPR Check completed: {0} finding(s) reported in Problems panel.",
            String(count)
          ),
          openProblemsLabel
        );
        if (choice === openProblemsLabel) {
          await vscode.commands.executeCommand("workbench.actions.view.problems");
        }
      } catch (err) {
        await sessions.handleToolErrorMessage((err as Error).message);
      }
    }
  );
}
